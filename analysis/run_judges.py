"""Prepare, split, run, and evaluate the Homework 5 LLM judge.

Run from the repository root. The exact prepared input file is the canonical
judge dataset after the first judge run; do not regenerate or edit it during
prompt development.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from analysis.helpers import (
    freeze_judge,
    judge_alignment,
    register_judge,
    run_judge,
    split_labels,
)


ROOT = Path(__file__).resolve().parents[1]
MODE = "overinformative_response"
LABELS_PATH = ROOT / "analysis" / "state" / "hw5_labels" / f"{MODE}.jsonl"
INPUTS_PATH = ROOT / "analysis" / "state" / "hw5_trace_inputs.json"
SPLITS_PATH = ROOT / "analysis" / "state" / "splits.json"
REPORT_DIR = ROOT / "analysis" / "report"
DEFAULT_TRACE_SOURCES = (
    ROOT / "traces" / "support_traces.json",
    ROOT / "tmp" / "hw5" / "overinformative" / "live_traces.json",
)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _load_export(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text())
    records = payload.get("traces") if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise ValueError(f"{path} must contain a trace list or a {{'traces': [...]}} object")
    return records


def _text_parts(parts: Any) -> list[str]:
    if not isinstance(parts, list):
        return []
    texts: list[str] = []
    for part in parts:
        if not isinstance(part, dict):
            continue
        if part.get("type") == "text" and part.get("content"):
            texts.append(str(part["content"]))
        elif isinstance(part.get("parts"), list):
            texts.extend(_text_parts(part["parts"]))
    return texts


def _generation_messages(trace: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the fullest observed model context, without its system prompt."""
    generations = []
    for observation in trace.get("observations") or []:
        if not isinstance(observation, dict) or observation.get("type") != "GENERATION":
            continue
        inp = observation.get("input")
        messages = inp.get("messages") if isinstance(inp, dict) else None
        if isinstance(messages, list):
            generations.append(observation)
    if not generations:
        raise ValueError(f"trace {trace.get('id')} has no generation conversation")
    generations.sort(key=lambda row: row.get("startTime") or row.get("start_time") or "")
    final_generation = generations[-1]
    raw_messages = final_generation["input"]["messages"]

    call_names: dict[str, str] = {}
    pending_names: list[str] = []
    prepared: list[dict[str, Any]] = []
    for message in raw_messages:
        if not isinstance(message, dict):
            continue
        role = str(message.get("role") or "")
        if role == "system":
            continue
        parts = message.get("parts") or []
        texts = _text_parts(parts)
        if texts:
            prepared.append({"role": role, "text": "\n".join(texts)})
        for part in parts if isinstance(parts, list) else []:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "tool_call" or (
                part.get("name") and "arguments" in part
            ):
                call_id = str(part.get("id") or "")
                name = str(part.get("name") or "tool")
                if call_id:
                    call_names[call_id] = name
                pending_names.append(name)
                prepared.append(
                    {
                        "role": "tool_call",
                        "name": name,
                        "arguments": part.get("arguments"),
                    }
                )
            elif "response" in part:
                call_id = str(part.get("id") or "")
                name = call_names.get(call_id)
                if name is None and pending_names:
                    name = pending_names.pop(0)
                elif name in pending_names:
                    pending_names.remove(name)
                prepared.append(
                    {
                        "role": "tool_result",
                        "name": name or "tool",
                        "content": part.get("response"),
                    }
                )

    output_text = "\n".join(_text_parts(final_generation.get("output")))
    if not output_text:
        # Langfuse also keeps the exact final reply at the trace root.
        output_text = "\n".join(_text_parts(trace.get("output")))
    if not output_text:
        raise ValueError(f"trace {trace.get('id')} has no final assistant reply")
    prepared.append({"role": "assistant", "text": output_text})
    return prepared


def _validate_inputs(records: list[dict[str, Any]], eligible_ids: set[str]) -> None:
    if not records:
        raise ValueError("judge input export is empty")
    ids = [str(record.get("trace_id")) for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("judge input export contains duplicate trace IDs")
    if set(ids) != eligible_ids:
        missing = sorted(eligible_ids - set(ids))
        extra = sorted(set(ids) - eligible_ids)
        raise ValueError(f"judge inputs do not match labels; missing={missing[:5]} extra={extra[:5]}")
    for record in records:
        if set(record) != {"trace_id", "trace"}:
            raise ValueError(f"trace {record.get('trace_id')} has leaking top-level fields")
        messages = record["trace"]
        if not isinstance(messages, list) or not messages:
            raise ValueError(f"trace {record['trace_id']} has no messages")
        if any(message.get("role") == "system" for message in messages):
            raise ValueError(f"trace {record['trace_id']} contains the agent system prompt")
        if not any(message.get("role") == "user" for message in messages):
            raise ValueError(f"trace {record['trace_id']} contains no user request")
        if messages[-1].get("role") != "assistant" or not messages[-1].get("text"):
            raise ValueError(f"trace {record['trace_id']} has no final assistant reply")
        serialized = json.dumps(record, ensure_ascii=False)
        for forbidden in (
            '"label"',
            '"verdict"',
            '"evidence"',
            '"expected"',
            '"scenario_id"',
            '"hw5_family"',
            '"reviewer"',
        ):
            if forbidden in serialized:
                raise ValueError(f"trace {record['trace_id']} contains forbidden field {forbidden}")


def prepare_inputs(
    sources: Iterable[Path] = DEFAULT_TRACE_SOURCES,
    output_path: Path = INPUTS_PATH,
) -> list[dict[str, Any]]:
    """Save one leakage-free judge input per accepted human label."""
    labels = _load_jsonl(LABELS_PATH)
    eligible_ids = {str(row["trace_id"]) for row in labels}
    if len(eligible_ids) != len(labels):
        raise ValueError("HW5 label file contains duplicate trace IDs")

    traces: dict[str, dict[str, Any]] = {}
    for source in sources:
        if not source.exists():
            raise FileNotFoundError(f"required trace source does not exist: {source}")
        for trace in _load_export(source):
            trace_id = str(trace.get("id") or trace.get("trace_id") or "")
            if trace_id in eligible_ids:
                traces[trace_id] = trace
    missing = eligible_ids - set(traces)
    if missing:
        raise ValueError(f"could not find {len(missing)} labeled traces: {sorted(missing)[:5]}")

    records = [
        {"trace_id": trace_id, "trace": _generation_messages(traces[trace_id])}
        for trace_id in sorted(eligible_ids)
    ]
    _validate_inputs(records, eligible_ids)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n")
    return records


def _split_counts(assignment: dict[str, list[str]]) -> dict[str, dict[str, int]]:
    labels = {str(row["trace_id"]): int(row["label"]) for row in _load_jsonl(LABELS_PATH)}
    return {
        name: {
            "Pass": sum(labels[trace_id] == 1 for trace_id in ids),
            "Fail": sum(labels[trace_id] == 0 for trace_id in ids),
            "total": len(ids),
        }
        for name, ids in assignment.items()
        if name in {"train", "dev", "test"}
    }


def split_data(mode: str = MODE) -> dict[str, list[str]]:
    """Create the required deterministic 20/40/40 stratified split once."""
    records = json.loads(INPUTS_PATH.read_text())
    eligible_ids = [str(record["trace_id"]) for record in records]
    assignment = split_labels(
        mode,
        fractions=(0.20, 0.40, 0.40),
        seed=7,
        min_per_class=10,
        eligible_trace_ids=eligible_ids,
    )
    print(json.dumps(_split_counts(assignment), indent=2, sort_keys=True))
    return assignment


def run_development(mode: str, prompt_path: Path) -> tuple[dict[str, str], dict[str, Any]]:
    """Register a prompt and evaluate it on development data."""
    record = register_judge(
        mode=mode,
        prompt_text=prompt_path.read_text(),
        judge_model="gpt-4o-mini",
    )
    judge_id = record["judge_id"]
    run_judge(judge_id, split="dev", batch_size=10)
    development = judge_alignment(judge_id, split="dev")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / f"dev-{judge_id}.json").write_text(
        json.dumps(development, indent=2, sort_keys=True) + "\n"
    )
    return record, development


def run_test(judge_id: str) -> dict[str, Any]:
    """Freeze a selected judge, run the held-out test once, and save metrics."""
    freeze_judge(judge_id)
    run_judge(judge_id, split="test", batch_size=10)
    test = judge_alignment(judge_id, split="test")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / f"test-{judge_id}.json").write_text(
        json.dumps(test, indent=2, sort_keys=True) + "\n"
    )
    return test


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("prepare")
    subparsers.add_parser("split")
    dev = subparsers.add_parser("dev")
    dev.add_argument("prompt", type=Path)
    test = subparsers.add_parser("test")
    test.add_argument("judge_id")
    args = parser.parse_args()

    if args.command == "prepare":
        records = prepare_inputs()
        print(json.dumps({"records": len(records), "output": str(INPUTS_PATH)}, indent=2))
    elif args.command == "split":
        split_data()
    elif args.command == "dev":
        print(json.dumps(run_development(MODE, args.prompt), indent=2))
    elif args.command == "test":
        print(json.dumps(run_test(args.judge_id), indent=2))


if __name__ == "__main__":
    main()
