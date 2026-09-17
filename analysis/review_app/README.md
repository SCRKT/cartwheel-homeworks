# Cartwheel Review Studio

Run from the repository root:

```bash
uv run python analysis/review_app/server.py
```

Then open <http://127.0.0.1:8020>.

The server uses only Python's standard library. It reads the Homework 3 trace
export and scenarios, groups one-turn Langfuse traces by
`cartwheel.session_id`, and serves a session-oriented review interface. Review
state is saved under `analysis/state/`. Accepted binary labels are mirrored to
Langfuse scores when Langfuse is configured; the local JSONL remains the
reproducible copy if synchronization is temporarily unavailable.

The Review page is for open coding. Select text in a user message, assistant
message, or tool card to attach evidence, or use the review panel to record the
first failure or “no failure observed” for a specific trace. Formal modes are
applied later in the Labels page, once the taxonomy has stabilized.

