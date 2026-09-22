from __future__ import annotations

from analysis.review_app.server import build_review_progress, summarize_review_scope


def _session(session_id: str, *trace_ids: str) -> dict:
    return {
        "session_id": session_id,
        "turns": [{"trace_id": trace_id} for trace_id in trace_ids],
    }


def _annotation(trace_id: str, session_id: str, *, note: str = "reviewed") -> dict:
    return {
        "trace_id": trace_id,
        "session_id": session_id,
        "status": "open_code" if note else "no_failure",
        "note": note,
    }


def test_two_trace_session_moves_from_unreviewed_to_partial_to_full() -> None:
    sessions = [_session("s1", "t1", "t2")]

    zero = summarize_review_scope(sessions, [])
    assert zero == {
        "session_count": 1,
        "trace_count": 2,
        "reviewed_trace_count": 0,
        "unreviewed_trace_count": 2,
        "fully_reviewed_session_count": 0,
        "partially_reviewed_session_count": 0,
        "unreviewed_session_count": 1,
    }

    one = summarize_review_scope(sessions, [_annotation("t1", "s1")])
    assert one["reviewed_trace_count"] == 1
    assert one["fully_reviewed_session_count"] == 0
    assert one["partially_reviewed_session_count"] == 1
    assert one["unreviewed_session_count"] == 0

    two = summarize_review_scope(
        sessions, [_annotation("t1", "s1"), _annotation("t2", "s1")]
    )
    assert two["reviewed_trace_count"] == 2
    assert two["fully_reviewed_session_count"] == 1
    assert two["partially_reviewed_session_count"] == 0
    assert two["unreviewed_session_count"] == 0


def test_progress_reports_complete_sample_sessions_and_full_dataset_separately() -> None:
    sessions = [_session("sample", "t1", "t2"), _session("other", "t3")]
    annotations = [
        _annotation("t1", "sample"),
        _annotation("t1", "sample", note="second note"),
        _annotation("t3", "other", note=""),
    ]
    manifest = {
        "selected_session_ids": ["sample"],
        # An anchor trace selects the whole conversation for review context.
        "selected_trace_ids": ["t1"],
    }

    progress = build_review_progress(sessions, annotations, manifest)

    assert progress["sample"] == {
        "session_count": 1,
        "trace_count": 2,
        "reviewed_trace_count": 1,
        "unreviewed_trace_count": 1,
        "fully_reviewed_session_count": 0,
        "partially_reviewed_session_count": 1,
        "unreviewed_session_count": 0,
    }
    assert progress["overall"] == {
        "session_count": 2,
        "trace_count": 3,
        "reviewed_trace_count": 2,
        "unreviewed_trace_count": 1,
        "fully_reviewed_session_count": 1,
        "partially_reviewed_session_count": 1,
        "unreviewed_session_count": 0,
    }

