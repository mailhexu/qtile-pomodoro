"""Unit tests for qtile_pomodoro.tasks (Story 1)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from qtile_pomodoro.tasks import TaskStore


@pytest.fixture()
def store(tmp_path: Path) -> TaskStore:
    return TaskStore(tmp_path / "tasks.json")


def test_add_persists_and_counts(store: TaskStore, tmp_path: Path) -> None:
    store.add("write report", "today")
    store.add("read paper", "inbox")
    path = tmp_path / "tasks.json"
    assert path.exists()
    data = json.loads(path.read_text())
    assert [t["title"] for t in data["today"]] == ["write report"]
    assert [t["title"] for t in data["inbox"]] == ["read paper"]
    assert data["version"] == 1
    assert store.today_count == 1


def test_complete_moves_to_hidden_history(store: TaskStore) -> None:
    task_id = store.add("email bob", "today").id
    store.complete(task_id)
    assert store.today_count == 0
    assert [t.title for t in store.today] == []
    assert [t.title for t in store.completed] == ["email bob"]
    assert store.completed[0].completed_at is not None


def test_move_swaps_lists(store: TaskStore) -> None:
    inbox_id = store.add("later", "inbox").id
    store.move(inbox_id)
    assert [t.title for t in store.today] == ["later"]
    assert store.inbox == []
    store.move(inbox_id)
    assert [t.title for t in store.inbox] == ["later"]
    assert store.today == []


def test_round_trip_preserves_state(tmp_path: Path) -> None:
    path = tmp_path / "tasks.json"
    first = TaskStore(path)
    today_id = first.add("stay", "today").id
    done_id = first.add("done", "today").id
    first.complete(done_id)
    second = TaskStore(path)
    assert [t.id for t in second.today] == [today_id]
    assert [t.id for t in second.completed] == [done_id]
    assert second.completed[0].completed_at is not None
def test_corrupt_but_valid_json_starts_empty(tmp_path: Path) -> None:
    for payload in ("[]", "null", '{"today": "oops"}', '{"inbox": [123]}'):
        path = tmp_path / "tasks.json"
        path.write_text(payload)
        store = TaskStore(path)
        assert store.inbox == [] and store.today == [] and store.completed == []


def test_save_goes_through_temp_replace(monkeypatch, store: TaskStore) -> None:
    calls = []
    real_replace = __import__("os").replace
    monkeypatch.setattr("qtile_pomodoro.tasks.os.replace",
                        lambda src, dst: calls.append((src, dst)) or real_replace(src, dst))
    store.add("atomic", "today")
    assert any(str(src).endswith(".json.tmp") and str(dst).endswith("tasks.json")
               for src, dst in calls)


def test_corrupt_file_starts_empty(tmp_path: Path) -> None:
    path = tmp_path / "tasks.json"
    path.write_text("{not json!!")
    store = TaskStore(path)
    assert store.inbox == [] and store.today == [] and store.completed == []
    backup = tmp_path / "tasks.json.corrupt"
    assert backup.exists()
    store.add("fresh", "today")
    assert json.loads(path.read_text())["today"][0]["title"] == "fresh"


def test_mutations_write_atomically(store: TaskStore) -> None:
    # after each mutation the canonical file parses and matches memory
    store.add("a", "inbox")
    store.add("b", "today")
    store.complete(store.today[0].id)
    data = json.loads(store.path.read_text())
    assert data["today"] == [] and [t["title"] for t in data["inbox"]] == ["a"]
    assert [t["title"] for t in data["completed"]] == ["b"]
