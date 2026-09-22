"""Offline authentication checks for the Homework 2 server boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import raindrop
from fastapi import HTTPException

from observability import instrument
from server import app as server_app


@pytest.fixture(autouse=True)
def isolated_sessions(
    world: dict[str, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(server_app, "SESSIONS_DB", tmp_path / "sessions.db")
    server_app._SESSIONS.clear()
    yield
    server_app._SESSIONS.clear()


def test_create_session_rejects_role_mismatch() -> None:
    with pytest.raises(HTTPException) as exc_info:
        server_app.create_session(
            server_app.SessionCreate(user_id=9002, role="shopper")
        )

    assert exc_info.value.status_code == 403


def test_token_cannot_authorize_another_session() -> None:
    first = server_app.create_session(
        server_app.SessionCreate(user_id=1, role="shopper")
    )
    second = server_app.create_session(
        server_app.SessionCreate(user_id=2, role="shopper")
    )

    with pytest.raises(HTTPException) as exc_info:
        server_app._authorize(
            second["session_id"],
            f"Bearer {first['token']}",
        )

    assert exc_info.value.status_code == 403


def test_workshop_uses_manual_events_without_otel_ownership(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configured: dict[str, Any] = {}

    class FakeRaindrop:
        def __init__(self, **kwargs: Any) -> None:
            configured.update(kwargs)

        def shutdown(self) -> None:
            configured["shutdown"] = True

    monkeypatch.setenv("RAINDROP_LOCAL_DEBUGGER", "http://localhost:5899/v1/")
    monkeypatch.setattr(raindrop, "Raindrop", FakeRaindrop)
    monkeypatch.setattr(instrument, "_workshop_client", None)

    client = instrument.setup_workshop()

    assert isinstance(client, FakeRaindrop)
    assert configured == {
        "local_workshop_url": "http://localhost:5899/v1/",
        "tracing_enabled": False,
        "auto_instrument": False,
        "project_id": "cartwheel-homeworks",
    }

    instrument.shutdown_workshop()
    assert configured["shutdown"] is True
    assert instrument.workshop_client() is None
