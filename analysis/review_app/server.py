"""Session-oriented Homework 4 trace-review application.

The app groups Cartwheel's one-trace-per-user-turn Langfuse records by
``cartwheel.session_id`` and joins them to the Homework 3 scenario metadata.
Langfuse remains canonical for structured labels; files under
``analysis/state`` are the committed, reproducible mirror.

Run from the repository root:

    uv run python analysis/review_app/server.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


HERE = Path(__file__).resolve().parent
ANALYSIS_DIR = HERE.parent
ROOT = ANALYSIS_DIR.parent
STATE_DIR = ANALYSIS_DIR / "state"
TRACE_EXPORT = ROOT / "traces" / "support_traces.json"
SCENARIOS = ROOT / "scenarios" / "support_scenarios.jsonl"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

STATE_FILES = {
    "manifest": STATE_DIR / "sample_manifest.json",
    "annotations": STATE_DIR / "annotations.json",
    "patterns": STATE_DIR / "patterns.json",
    "suggestions": STATE_DIR / "suggestions.json",
}
DEFAULTS: dict[str, Any] = {
    "manifest": {"batches": [], "selected_trace_ids": []},
    "annotations": [],
    "patterns": {"modes": [], "revision_history": []},
    "suggestions": [],
}


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def text_content(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if not isinstance(item, dict):
                continue
            for part in item.get("parts") or []:
                if isinstance(part, dict) and part.get("content"):
                    parts.append(str(part["content"]))
        if parts:
            return "\n".join(parts)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def metadata_attributes(trace: dict[str, Any]) -> dict[str, Any]:
    metadata = trace.get("metadata") or {}
    attributes = metadata.get("attributes") if isinstance(metadata, dict) else {}
    if isinstance(attributes, str):
        try:
            attributes = json.loads(attributes)
        except json.JSONDecodeError:
            attributes = {}
    return attributes if isinstance(attributes, dict) else {}


def generation_texts(observation: dict[str, Any]) -> list[str]:
    output = observation.get("output")
    if not isinstance(output, list):
        return []
    texts: list[str] = []
    for item in output:
        if not isinstance(item, dict) or item.get("role") != "assistant":
            continue
        for part in item.get("parts") or []:
            if isinstance(part, dict) and part.get("type") == "text":
                content = str(part.get("content") or "").strip()
                if content:
                    texts.append(content)
    return texts


def system_prompt(observations: list[dict[str, Any]]) -> str:
    for observation in observations:
        if observation.get("type") != "GENERATION":
            continue
        payload = observation.get("input") or {}
        messages = payload.get("messages") if isinstance(payload, dict) else None
        if not isinstance(messages, list):
            continue
        for message in messages:
            if isinstance(message, dict) and message.get("role") == "system":
                return text_content([message])
    return ""


def observation_time(observation: dict[str, Any]) -> str:
    return str(observation.get("startTime") or observation.get("start_time") or "")


def turn_record(trace: dict[str, Any]) -> dict[str, Any]:
    observations = sorted(trace.get("observations") or [], key=observation_time)
    final_output = text_content(trace.get("output")).strip()
    events: list[dict[str, Any]] = []
    seen_text: set[str] = set()
    models: set[str] = set()
    total_cost = 0.0
    input_tokens = output_tokens = 0

    for observation in observations:
        model = observation.get("model")
        if model:
            models.add(str(model))
        usage = observation.get("usageDetails") or observation.get("usage_details") or {}
        if isinstance(usage, dict):
            input_tokens += int(usage.get("input") or 0)
            output_tokens += int(usage.get("output") or 0)
        total_cost += float(observation.get("calculatedTotalCost") or observation.get("totalCost") or 0)

        if observation.get("type") == "GENERATION":
            for content in generation_texts(observation):
                if content == final_output or content in seen_text:
                    continue
                seen_text.add(content)
                events.append({
                    "kind": "assistant_step",
                    "id": observation.get("id"),
                    "timestamp": observation_time(observation),
                    "text": content,
                })
        elif observation.get("type") == "TOOL":
            events.append({
                "kind": "tool",
                "id": observation.get("id"),
                "timestamp": observation_time(observation),
                "name": observation.get("name") or "tool",
                "input": observation.get("input"),
                "output": observation.get("output"),
                "error": observation.get("level") == "ERROR",
            })

    attrs = metadata_attributes(trace)
    trace_id = str(trace.get("id") or "")
    return {
        "trace_id": trace_id,
        "timestamp": trace.get("timestamp"),
        "input": text_content(trace.get("input")),
        "output": final_output,
        "events": events,
        "models": sorted(models),
        "system_prompt": system_prompt(observations),
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(total_cost, 8),
            "latency_seconds": trace.get("latency"),
        },
        "langfuse_url": f"http://localhost:3000/project/cartwheel-dev/traces/{trace_id}",
        "prompt_version": attrs.get("cartwheel.prompt_version"),
    }


def load_scenarios() -> dict[str, dict[str, Any]]:
    if not SCENARIOS.exists():
        return {}
    return {
        record["id"]: record
        for record in (json.loads(line) for line in SCENARIOS.read_text().splitlines() if line.strip())
    }


def load_sessions() -> list[dict[str, Any]]:
    exported = read_json(TRACE_EXPORT, {"traces": []})
    traces = exported.get("traces", []) if isinstance(exported, dict) else exported
    scenarios = load_scenarios()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for trace in traces if isinstance(traces, list) else []:
        if not isinstance(trace, dict):
            continue
        attrs = metadata_attributes(trace)
        session_id = attrs.get("cartwheel.session_id") or trace.get("sessionId") or trace.get("id")
        grouped[str(session_id)].append(trace)

    sessions: list[dict[str, Any]] = []
    for session_id, members in grouped.items():
        members.sort(key=lambda item: str(item.get("timestamp") or ""))
        scenario_id = str(members[0].get("cartwheel_scenario_id") or "")
        scenario = scenarios.get(scenario_id, {})
        tuple_ = scenario.get("tuple") or {}
        turns = [turn_record(member) for member in members]
        tools = [event["name"] for turn in turns for event in turn["events"] if event["kind"] == "tool"]
        generations = sum(
            1
            for member in members
            for observation in member.get("observations") or []
            if observation.get("type") == "GENERATION"
        )
        sessions.append({
            "session_id": session_id,
            "scenario_id": scenario_id,
            "scenario_group": scenario.get("scenario_group"),
            "role": tuple_.get("role"),
            "user_id": tuple_.get("user_id"),
            "intent": tuple_.get("intent"),
            "difficulty": tuple_.get("difficulty"),
            "style": tuple_.get("user_style"),
            "expected": scenario.get("expected"),
            "data_quality_case_id": scenario.get("data_quality_case_id"),
            "turns": turns,
            "features": {
                "turn_count": len(turns),
                "trace_count": len(members),
                "tool_call_count": len(tools),
                "distinct_tools": len(set(tools)),
                "generation_count": generations,
                "tokens": sum(t["usage"]["input_tokens"] + t["usage"]["output_tokens"] for t in turns),
            },
            "tools": tools,
        })

    sessions.sort(key=lambda item: item["scenario_id"])
    add_outlier_flags(sessions)
    return sessions


def add_outlier_flags(sessions: list[dict[str, Any]]) -> None:
    for field in ("tool_call_count", "generation_count", "tokens"):
        ordered = sorted(session["features"][field] for session in sessions)
        if not ordered:
            continue
        threshold = ordered[max(0, int(len(ordered) * 0.9) - 1)]
        for session in sessions:
            session.setdefault("flags", [])
            if session["features"][field] > threshold:
                labels = {
                    "tool_call_count": "many tool calls",
                    "generation_count": "many model steps",
                    "tokens": "high token count",
                }
                session["flags"].append(labels[field])


def label_files() -> dict[str, list[dict[str, Any]]]:
    directory = STATE_DIR / "labels"
    result: dict[str, list[dict[str, Any]]] = {}
    if not directory.exists():
        return result
    for path in sorted(directory.glob("*.jsonl")):
        records = []
        for line in path.read_text().splitlines():
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        result[path.stem] = records
    return result


def save_labels(payload: dict[str, Any]) -> dict[str, Any]:
    mode = str(payload.get("mode") or "")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", mode):
        raise ValueError("mode must be snake_case")
    judgments = payload.get("judgments")
    if not isinstance(judgments, list):
        raise ValueError("judgments must be a list")
    normalized = []
    for item in judgments:
        if not isinstance(item, dict) or item.get("label") not in (0, 1):
            raise ValueError("each judgment needs trace_id and label 0 or 1")
        normalized.append({
            "trace_id": str(item.get("trace_id") or ""),
            "session_id": item.get("session_id"),
            "scenario_id": item.get("scenario_id"),
            "mode": mode,
            "label": int(item["label"]),
            "evidence": item.get("evidence") or "",
            "reviewer": "human",
        })
    directory = STATE_DIR / "labels"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{mode}.jsonl"
    temporary = target.with_suffix(".jsonl.tmp")
    temporary.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in normalized))
    temporary.replace(target)
    synced = sync_label_scores(normalized)
    return {"ok": True, "count": len(normalized), "langfuse_scores_written": synced}


def sync_label_scores(records: list[dict[str, Any]]) -> int:
    try:
        from observability.instrument import load_env
        load_env()
        from analysis.helpers import langfuse_io
        if not langfuse_io.is_configured():
            return 0
        client = langfuse_io._client()
        written = 0
        for record in records:
            langfuse_io.write_label_score(
                trace_id=record["trace_id"],
                mode=record["mode"],
                label=record["label"],
                comment=record.get("evidence"),
                client=client,
            )
            written += 1
        return written
    except Exception as exc:  # local mirror remains recoverable
        print(f"[labels] Langfuse synchronization deferred: {exc}")
        return 0


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def send_json(self, value: Any, status: int = 200) -> None:
        data = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self.send_json({"error": "not found"}, 404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def body(self) -> Any:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return None
        try:
            return json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            return None

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self.send_file(HERE / "index.html", "text/html; charset=utf-8")
        elif path == "/api/sessions":
            self.send_json(load_sessions())
        elif path == "/api/labels":
            self.send_json(label_files())
        elif path.startswith("/api/") and path[5:] in STATE_FILES:
            name = path[5:]
            self.send_json(read_json(STATE_FILES[name], DEFAULTS[name]))
        else:
            self.send_json({"error": f"unknown path: {path}"}, 404)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        payload = self.body()
        if payload is None:
            self.send_json({"error": "expected JSON body"}, 400)
            return
        try:
            if path == "/api/labels":
                self.send_json(save_labels(payload))
            elif path.startswith("/api/") and path[5:] in STATE_FILES:
                name = path[5:]
                write_json(STATE_FILES[name], payload)
                count = len(payload) if isinstance(payload, (list, dict)) else 0
                self.send_json({"ok": True, "count": count})
            else:
                self.send_json({"error": f"unknown path: {path}"}, 404)
        except ValueError as exc:
            self.send_json({"error": str(exc)}, 400)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8020)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Cartwheel HW4 review app: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
