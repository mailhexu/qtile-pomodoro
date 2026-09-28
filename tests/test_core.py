from __future__ import annotations

from qtile_pomodoro.core import DEFAULTS, State, Timer


class _Store:
    def __init__(self) -> None:
        self.saved = False
        self.completed = 0

    def complete_focus(self, seconds: int) -> None:
        self.completed += seconds

    def save(self, state: State) -> None:
        self.saved = True


def test_status_advances_an_expired_focus_session(monkeypatch) -> None:
    timer = Timer.__new__(Timer)
    timer.config = DEFAULTS.copy()
    timer.state = State(status="running", end_at=100, remaining=0)
    timer.store = _Store()
    timer.notify = lambda title, body: None
    monkeypatch.setattr("qtile_pomodoro.core.time.time", lambda: 100)

    result = timer.status()

    assert result["phase"] == "short_break"
    assert result["remaining"] == 5 * 60
    assert result["overlay"] is True
    assert timer.store.completed == 25 * 60
