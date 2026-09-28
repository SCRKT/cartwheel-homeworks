"""Run the Homework 7 post-deployment monitor."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from analysis.helpers.langfuse_io import fetch_traces
from monitoring.chart import prevalence_chart
from monitoring.correct import corrected_mode_prevalence
from monitoring.run_judges import judge_sample, judge_test_data
from monitoring.sample import DEFAULT_RISK_GROUPS, select_traces
from monitoring.write_scores import build_score_records, post_scores
from observability.instrument import load_env

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "monitoring" / "config.json"
SCENARIOS_PATH = ROOT / "scenarios" / "monitoring_scenarios.jsonl"
HISTORY_PATH = ROOT / "monitoring" / "history.jsonl"
CHART_PATH = ROOT / "monitoring" / "prevalence.svg"
LATEST_PATH = ROOT / "monitoring" / "latest.json"


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _scenario_ids() -> set[str]:
    return set(_scenario_turn_counts())


def _scenario_turn_counts() -> dict[str, int]:
    scenarios = [
        json.loads(line)
        for line in SCENARIOS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return {
        str(scenario["id"]): 1 + len(scenario.get("followups") or [])
        for scenario in scenarios
    }


def _message_text(message: dict[str, Any]) -> str:
    role = str(message.get("role") or "step")
    name = str(message.get("name") or message.get("label") or "").strip()
    value = message.get(
        "arguments", message.get("text", message.get("content"))
    )
    if isinstance(value, str):
        content = value
    else:
        content = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    prefix = f"{role} {name}" if name else role
    return f"{prefix}: {content}" if content else ""


def build_conversations(
    traces: list[dict[str, Any]], group_field: str
) -> list[dict[str, Any]]:
    """Group ordered traces and retain the final trace ID for score writes."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trace in traces:
        group_id = trace.get("meta", {}).get(group_field)
        if group_id:
            grouped[str(group_id)].append(trace)

    conversations: list[dict[str, Any]] = []
    for group_id, members in grouped.items():
        members.sort(key=lambda trace: trace.get("timestamp") or "")
        messages = [
            message
            for trace in members
            for message in trace.get("trace", [])
            if isinstance(message, dict)
        ]
        tools = list(
            dict.fromkeys(
                str(message["name"])
                for message in messages
                if message.get("role") == "tool_call" and message.get("name")
            )
        )
        text = "\n".join(
            rendered for message in messages if (rendered := _message_text(message))
        )
        conversations.append(
            {
                "id": str(members[-1]["trace_id"]),
                "group_id": group_id,
                "scenario_id": members[0].get("meta", {}).get("scenario_id"),
                "session_id": members[0].get("meta", {}).get("session_id"),
                "session_ids": sorted(
                    {
                        str(trace.get("meta", {}).get("session_id"))
                        for trace in members
                        if trace.get("meta", {}).get("session_id")
                    }
                ),
                "trace_count": len(members),
                "text": text,
                "tools": tools,
                "turn_count": sum(message.get("role") == "user" for message in messages),
                "models": sorted(
                    {
                        model
                        for trace in members
                        for model in trace.get("models", [])
                        if model
                    }
                ),
            }
        )
    conversations.sort(key=lambda record: record["group_id"])
    return conversations


def _validate_period(
    conversations: list[dict[str, Any]], expected_ids: set[str], model: str
) -> None:
    actual_ids = {str(record["scenario_id"]) for record in conversations}
    missing = sorted(expected_ids - actual_ids)
    extra = sorted(actual_ids - expected_ids)
    if missing or extra or len(conversations) != len(expected_ids):
        raise ValueError(
            f"period must contain exactly {len(expected_ids)} scenarios; "
            f"missing={missing[:5]}, extra={extra[:5]}"
        )
    expected_turns = _scenario_turn_counts()
    combined_retries = [
        record["group_id"]
        for record in conversations
        if len(record["session_ids"]) != 1
        or record["turn_count"] != expected_turns[record["group_id"]]
        or record["trace_count"] != expected_turns[record["group_id"]]
    ]
    if combined_retries:
        raise ValueError(
            "period combines retries or has incomplete turns for scenarios: "
            f"{combined_retries[:5]}"
        )
    mismatches = [
        record["group_id"]
        for record in conversations
        if set(record["models"]) != {model}
    ]
    if mismatches:
        raise ValueError(
            f"period contains conversations outside model {model}: {mismatches[:5]}"
        )


def _windowed_traces(
    traces: list[dict[str, Any]], start: datetime, end: datetime
) -> list[dict[str, Any]]:
    return [
        trace
        for trace in traces
        if trace.get("timestamp")
        and start <= _timestamp(str(trace["timestamp"])) <= end
    ]


def _write_history(record: dict[str, Any]) -> None:
    existing = []
    if HISTORY_PATH.exists():
        existing = [
            json.loads(line)
            for line in HISTORY_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    by_label = {str(row["period"]): row for row in existing}
    by_label[str(record["period"])] = record
    HISTORY_PATH.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in by_label.values()),
        encoding="utf-8",
    )
    points = [
        {
            "label": row["period"],
            "corrected": row["corrected_rate"],
            "ci_low": row["ci_low"],
            "ci_high": row["ci_high"],
        }
        for row in by_label.values()
        if row.get("corrected_rate") is not None
    ]
    if points:
        config = _load_json(CONFIG_PATH)
        CHART_PATH.write_text(
            prevalence_chart(points, config["threshold"], config["judge_mode"]),
            encoding="utf-8",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    window = parser.add_mutually_exclusive_group(required=True)
    window.add_argument("--period", help="named period from monitoring/config.json")
    window.add_argument("--last-hours", type=float, help="monitor a rolling UTC window")
    parser.add_argument(
        "--prepare-only",
        action="store_true",
        help="validate and print sample counts without calling the judge or writing scores",
    )
    args = parser.parse_args()

    load_env()
    config = _load_json(CONFIG_PATH)
    now = datetime.now(timezone.utc)
    if args.period:
        try:
            period = next(
                item for item in config["periods"] if item["label"] == args.period
            )
        except StopIteration as exc:
            raise SystemExit(f"unknown period: {args.period}") from exc
        label = str(period["label"])
        start, end = _timestamp(period["from"]), _timestamp(period["to"])
        group_field = "scenario_id"
    else:
        end = now
        start = end - timedelta(hours=args.last_hours)
        label = f"last-{args.last_hours:g}h-{end.strftime('%Y%m%dT%H%M%SZ')}"
        group_field = "session_id"

    traces = _windowed_traces(fetch_traces(limit=5000), start, end)
    if args.period:
        expected_ids = _scenario_ids()
        traces = [
            trace
            for trace in traces
            if str(trace.get("meta", {}).get("scenario_id")) in expected_ids
        ]
    conversations = build_conversations(traces, group_field)
    if args.period:
        _validate_period(conversations, expected_ids, config["model"])
    else:
        conversations = [
            record for record in conversations if set(record["models"]) == {config["model"]}
        ]
        if not conversations:
            empty = {
                "period": label,
                "judge_id": config["judge_id"],
                "model": config["model"],
                "langfuse_trace_count": len(traces),
                "conversation_count": 0,
                "random_sample_count": 0,
                "risk_sample_count": 0,
                "judge_call_count": 0,
                "random_flag_count": 0,
                "risk_flag_count": 0,
                "risk_raw_rate": None,
                "raw_rate": None,
                "corrected_rate": None,
                "ci_low": None,
                "ci_high": None,
                "failure_sensitivity": None,
                "pass_specificity": None,
            }
            _write_history(empty)
            LATEST_PATH.write_text(json.dumps(empty, indent=2) + "\n", encoding="utf-8")
            print("No eligible conversations; recorded zero counts without calling the judge.")
            return

    unknown_groups = sorted(set(config["risk_groups"]) - set(DEFAULT_RISK_GROUPS))
    if unknown_groups:
        raise ValueError(f"unknown risk groups: {unknown_groups}")
    risk_groups = {name: DEFAULT_RISK_GROUPS[name] for name in config["risk_groups"]}
    plan = select_traces(conversations, config["random_rate"], risk_groups)
    risk_ids = {
        str(record["id"])
        for records in plan["risk_groups"].values()
        for record in records
    }
    print(
        f"{label}: {len(traces)} traces, {len(conversations)} conversations, "
        f"{len(plan['random'])} random, {len(risk_ids)} risk, "
        f"{len(plan['to_judge'])} judge calls"
    )
    if args.prepare_only:
        return

    verdicts = judge_sample(config["judge_id"], plan["to_judge"])
    random_verdicts = {str(row["id"]): verdicts[str(row["id"])] for row in plan["random"]}
    risk_verdicts = {trace_id: verdicts[trace_id] for trace_id in risk_ids}
    test_labels, test_predictions = judge_test_data(config["judge_id"])
    estimate = corrected_mode_prevalence(
        list(random_verdicts.values()), test_labels, test_predictions
    )
    records = build_score_records(
        config["judge_mode"], random_verdicts, risk_verdicts, estimate, label
    )
    score_count = post_scores(records)
    result = {
        "period": label,
        "judge_id": config["judge_id"],
        "model": config["model"],
        "from": start.isoformat(),
        "to": end.isoformat(),
        "langfuse_trace_count": len(traces),
        "conversation_count": len(conversations),
        "random_sample_count": len(plan["random"]),
        "risk_sample_count": len(risk_ids),
        "judge_call_count": len(plan["to_judge"]),
        "random_flag_count": sum(random_verdicts.values()),
        "risk_flag_count": sum(risk_verdicts.values()),
        "risk_raw_rate": round(
            sum(risk_verdicts.values()) / len(risk_verdicts), 4
        )
        if risk_verdicts
        else None,
        "risk_group_counts": {
            name: len(rows) for name, rows in plan["risk_groups"].items()
        },
        "raw_rate": estimate["raw"],
        "corrected_rate": estimate["corrected"],
        "ci_low": estimate["ci_low"],
        "ci_high": estimate["ci_high"],
        "failure_sensitivity": estimate["failure_sensitivity"],
        "pass_specificity": estimate["pass_specificity"],
        "scores_written": score_count,
    }
    _write_history(result)
    LATEST_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
