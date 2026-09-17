"""Create Homework 4's initial 15-uniform + 15-cluster trace sample."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import random
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.helpers.normalization import normalize_trace  # noqa: E402
from analysis.helpers.selection import (  # noqa: E402
    _FEATURES,
    _kmeans,
    _standardize,
)


def attributes(trace: dict[str, Any]) -> dict[str, Any]:
    metadata = trace.get("metadata") or {}
    value = metadata.get("attributes") if isinstance(metadata, dict) else {}
    return value if isinstance(value, dict) else {}


def record(trace: dict[str, Any], reason: str) -> dict[str, Any]:
    attrs = attributes(trace)
    return {
        "trace_id": str(trace["id"]),
        "session_id": attrs.get("cartwheel.session_id"),
        "scenario_id": trace.get("cartwheel_scenario_id")
        or attrs.get("cartwheel.scenario_id"),
        "role": attrs.get("cartwheel.user_role"),
        "reason": reason,
    }


def cluster_medoids(
    traces: list[dict[str, Any]], count: int, seed: int
) -> list[tuple[dict[str, Any], str]]:
    normalized = [normalize_trace(trace) for trace in traces]
    vectors = _standardize(
        [[float(item["features"].get(name, 0)) for name in _FEATURES] for item in normalized]
    )
    assignments = _kmeans(vectors, k=count, seed=seed)
    selected: list[tuple[dict[str, Any], str]] = []
    for cluster in range(count):
        members = [index for index, value in enumerate(assignments) if value == cluster]
        if not members:
            continue
        centroid = [
            sum(vectors[index][dimension] for index in members) / len(members)
            for dimension in range(len(_FEATURES))
        ]
        medoid = min(
            members,
            key=lambda index: (
                sum((a - b) ** 2 for a, b in zip(vectors[index], centroid)),
                normalized[index]["trace_id"],
            ),
        )
        features = normalized[medoid]["features"]
        summary = ", ".join(f"{name}={features[name]}" for name in _FEATURES)
        selected.append(
            (
                traces[medoid],
                f"cluster {cluster + 1} medoid of {len(members)} traces ({summary})",
            )
        )
    if len(selected) != count:
        raise RuntimeError(f"expected {count} nonempty clusters, found {len(selected)}")
    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=ROOT / "traces/support_traces.json")
    parser.add_argument(
        "--output", type=Path, default=ROOT / "analysis/state/sample_manifest.json"
    )
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    payload = json.loads(args.source.read_text())
    traces = payload["traces"] if isinstance(payload, dict) else payload
    if len({trace["id"] for trace in traces}) != len(traces):
        raise ValueError("trace identifiers must be unique")

    uniform = random.Random(args.seed).sample(traces, 15)
    uniform_ids = {trace["id"] for trace in uniform}
    remaining = [trace for trace in traces if trace["id"] not in uniform_ids]
    clustered = cluster_medoids(remaining, count=15, seed=args.seed)

    uniform_records = [record(trace, "uniform random pick") for trace in uniform]
    cluster_records = [record(trace, reason) for trace, reason in clustered]
    all_records = uniform_records + cluster_records
    trace_ids = [item["trace_id"] for item in all_records]
    if len(trace_ids) != 30 or len(set(trace_ids)) != 30:
        raise RuntimeError("initial sample must contain 30 distinct trace identifiers")

    manifest = {
        "schema_version": 1,
        "source": str(args.source.resolve()),
        "selection_unit": "langfuse_trace",
        "seed": args.seed,
        "selected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "batches": [
            {
                "name": "initial_uniform",
                "method": "uniform_random_without_replacement",
                "target_count": 15,
                "records": uniform_records,
            },
            {
                "name": "initial_cluster_representatives",
                "method": "kmeans_medoid_on_standardized_features",
                "features": list(_FEATURES),
                "target_count": 15,
                "excluded_prior_trace_ids": sorted(uniform_ids),
                "records": cluster_records,
            },
        ],
        "selected_trace_ids": trace_ids,
        "selected_session_ids": sorted(
            {item["session_id"] for item in all_records if item.get("session_id")}
        ),
        "counts": {
            "source_traces": len(traces),
            "selected_traces": len(trace_ids),
            "selected_sessions": len(
                {item["session_id"] for item in all_records if item.get("session_id")}
            ),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(args.output)
    print(
        f"selected {manifest['counts']['selected_traces']} traces across "
        f"{manifest['counts']['selected_sessions']} sessions"
    )


if __name__ == "__main__":
    main()
