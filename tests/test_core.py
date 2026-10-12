from __future__ import annotations

from pathlib import Path

import pytest

from qtile_pomodoro.core import DEFAULTS, State, Store, Timer


@pytest.fixture()
def timer_store(tmp_path: Path, monkeypatch):
    path = tmp_path / "timer.sqlite3"
    now = [1_000_000.0]
    monkeypatch.setattr("qtile_pomodoro.core.config_path", lambda: tmp_path / "config.toml")
    monkeypatch.setattr("qtile_pomodoro.core.data_path", lambda: path)
    monkeypatch.setattr("qtile_pomodoro.core.time.time", lambda: now[0])
    monkeypatch.setattr(Timer, "notify", lambda self, title, body: None)
    store = Store(path)
    yield store, now
    store.db.close()


def test_status_advances_an_expired_focus_session(timer_store) -> None:
    store, now = timer_store
    timer = Timer()
    try:
        deadline = timer.command("start")["end_at"]
        now[0] = deadline

        # No daemon or ticker is running: the status read must finish focus.
        result = timer.status()

        assert result["phase"] == "short_break"
        assert result["status"] == "running"
        assert result["remaining"] == DEFAULTS["short_break_minutes"] * 60
        assert result["end_at"] == deadline + DEFAULTS["short_break_minutes"] * 60
        assert result["completed_in_cycle"] == 1
        assert result["overlay"] is True
        assert store.load(DEFAULTS) == timer.state
        history = store.report()["history"]
        assert len(history) == 1
        assert history[0]["minutes"] == DEFAULTS["focus_minutes"]

        assert timer.status() == result
        now[0] += 1
        next_status = timer.status()
        assert next_status["remaining"] == result["remaining"] - 1
        assert next_status["end_at"] == result["end_at"]
        assert next_status["completed_in_cycle"] == 1
        assert store.report()["history"] == history
    finally:
        timer.store.db.close()


def test_replacing_timer_preserves_an_unexpired_focus(timer_store) -> None:
    store, now = timer_store
    store.complete_focus(DEFAULTS["focus_minutes"] * 60)
    store.save(State(completed_in_cycle=1))
    history = store.report()["history"]
    timer = Timer()
    try:
        started = timer.command("start")
        deadline = started["end_at"]
        now[0] += 90
        assert timer.status()["remaining"] == DEFAULTS["focus_minutes"] * 60 - 90
    finally:
        timer.store.db.close()

    replacement = Timer()
    try:
        result = replacement.status()
        assert result["phase"] == "focus"
        assert result["status"] == "running"
        assert result["end_at"] == deadline
        assert result["remaining"] == DEFAULTS["focus_minutes"] * 60 - 90
        assert result["completed_in_cycle"] == 1
        assert result["overlay"] is False
        assert store.load(DEFAULTS) == replacement.state
        assert store.report()["history"] == history
    finally:
        replacement.store.db.close()


def test_replacing_timer_recovers_one_overdue_focus_to_a_fresh_break(timer_store) -> None:
    store, now = timer_store
    store.complete_focus(DEFAULTS["focus_minutes"] * 60)
    history = store.report()["history"]
    # Downtime exceeds even a long break: recovery must not skip more phases.
    store.save(State(status="running", end_at=now[0] - 10_000, completed_in_cycle=1))

    replacement = Timer()
    try:
        result = replacement.status()
        assert result["phase"] == "short_break"
        assert result["status"] == "running"
        assert result["remaining"] == DEFAULTS["short_break_minutes"] * 60
        assert result["end_at"] == now[0] + DEFAULTS["short_break_minutes"] * 60
        assert result["completed_in_cycle"] == 2
        assert result["overlay"] is True
        assert store.load(DEFAULTS) == replacement.state
        recovered_history = store.report()["history"]
        assert len(recovered_history) == len(history) + 1
        assert all(row["minutes"] == DEFAULTS["focus_minutes"] for row in recovered_history)
        assert all(row in recovered_history for row in history)
        assert replacement.status() == result
        assert store.report()["history"] == recovered_history
    finally:
        replacement.store.db.close()

    now[0] += 60
    another_replacement = Timer()
    try:
        restored = another_replacement.status()
        assert restored["phase"] == "short_break"
        assert restored["status"] == "running"
        assert restored["end_at"] == result["end_at"]
        assert restored["remaining"] == result["remaining"] - 60
        assert restored["completed_in_cycle"] == 2
        assert restored["overlay"] is True
        assert store.load(DEFAULTS) == another_replacement.state
        assert store.report()["history"] == recovered_history
    finally:
        another_replacement.store.db.close()
