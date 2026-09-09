"""Unit tests for local one-step undo (Story 7)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from qtile_pomodoro.tasks import TaskStore, UndoAction


@pytest.fixture()
def store(tmp_path: Path) -> TaskStore:
    return TaskStore(tmp_path / "tasks.json")


# ---------------------------------------------------------------- store

def test_complete_returns_undo_action(store: TaskStore) -> None:
    task_id = store.add("email bob", "today").id
    action = store.complete(task_id)
    assert action is not None
    assert action.kind == "complete" and action.task_id == task_id
    assert action.source == "today"


def test_undo_completion_restores_task(store: TaskStore) -> None:
    task_id = store.add("email bob", "today").id
    action = store.complete(task_id)
    assert action is not None
    assert store.undo(action) is True
    assert [t.id for t in store.today] == [task_id]
    assert store.today[0].completed_at is None
    assert store.completed == []


def test_undo_move_restores_source_list(store: TaskStore) -> None:
    task_id = store.add("later", "inbox").id
    action = store.move(task_id)
    assert action is not None and action.source == "inbox"
    assert store.undo(action) is True
    assert [t.id for t in store.inbox] == [task_id]
    assert store.today == []


def test_undo_stale_action_fails_without_mutation(store: TaskStore) -> None:
    store.add("keep", "today")
    before = json.loads(store.path.read_text())
    stale = UndoAction("complete", "does-not-exist", "today")
    assert store.undo(stale) is False
    assert json.loads(store.path.read_text()) == before


def test_undo_persists_restored_state(store: TaskStore, tmp_path: Path) -> None:
    task_id = store.add("keep", "today").id
    action = store.complete(task_id)
    assert action is not None
    store.undo(action)
    data = json.loads((tmp_path / "tasks.json").read_text())
    assert [t["id"] for t in data["today"]] == [task_id]
    assert data["today"][0]["completed_at"] is None
    assert data["completed"] == []


def test_unknown_id_returns_none(store: TaskStore) -> None:
    assert store.complete("nope") is None
    assert store.move("nope") is None


class _LocalApplyEngine:
    """Minimal SyncEngine stand-in: applies locally, queues nothing."""
    def enqueue(self, cmd, args, local_apply, temp_id=None):
        local_apply()


def test_engine_mutations_return_no_action(store: TaskStore) -> None:
    task_id = store.add("synced", "today").id
    store.engine = _LocalApplyEngine()
    assert store.complete(task_id) is None
    assert [t.title for t in store.completed] == ["synced"]
    assert store.move(task_id) is None


# ---------------------------------------------------------------- model

@pytest.fixture()
def model(tmp_path: Path):
    from qtile_pomodoro.task_model import OverlayModel
    m_store = TaskStore(tmp_path / "tasks.json")
    m_store.add("alpha", "today")
    m_store.add("beta", "inbox")
    return OverlayModel(m_store)


def test_u_undoes_completion(model) -> None:
    _, _ = model.key(ord("d"))  # complete 'alpha'
    assert [t.title for t in model.store.completed] == ["alpha"]
    _, _ = model.key(ord("u"))
    assert [t.title for t in model.store.today] == ["alpha"]
    assert model.store.completed == []


def test_u_undoes_move(model) -> None:
    _, _ = model.key(ord("m"))  # move 'alpha' today -> inbox
    assert [t.title for t in model.store.inbox] == ["beta", "alpha"]
    _, _ = model.key(ord("u"))
    assert [t.title for t in model.store.today] == ["alpha"]
    assert [t.title for t in model.store.inbox] == ["beta"]


def test_u_twice_is_inert_after_one_undo(model) -> None:
    _, _ = model.key(ord("d"))
    _, _ = model.key(ord("u"))
    _, _ = model.key(ord("u"))  # no action retained: safe no-op
    assert [t.title for t in model.store.today] == ["alpha"]


def test_new_mutation_replaces_undo_action(model) -> None:
    _, _ = model.key(ord("d"))       # complete 'alpha'
    _, _ = model.key(ord("j"))       # select 'beta'
    _, _ = model.key(ord("d"))       # complete 'beta' — replaces action
    _, _ = model.key(ord("u"))
    assert [t.title for t in model.store.inbox] == ["beta"]  # beta restored
    assert [t.title for t in model.store.completed] == ["alpha"]


def test_u_inert_with_no_action(model) -> None:
    redraw, _ = model.key(ord("u"))
    assert model.mode == "nav"
    assert [t.title for t in model.store.today] == ["alpha"]


def test_u_inert_when_sync_enabled(model) -> None:
    model.store.engine = _LocalApplyEngine()
    _, _ = model.key(ord("d"))
    assert model._undo_action is None
    _, _ = model.key(ord("u"))
    assert [t.title for t in model.store.completed] == ["alpha"]


def test_u_is_nav_key_not_input_trigger(model) -> None:
    _, _ = model.key(ord("u"))
    assert model.mode == "nav"


def test_click_completion_records_undo(model) -> None:
    # the model method the overlay routes mouse clicks through
    model.apply_complete(model.store.today[0].id)
    assert [t.title for t in model.store.completed] == ["alpha"]
    _, _ = model.key(ord("u"))
    assert [t.title for t in model.store.today] == ["alpha"]
