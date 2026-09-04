"""Unit tests for the task overlay interaction model (Story 3)."""
from __future__ import annotations

from pathlib import Path

import pytest

from qtile_pomodoro.task_model import KEY_ENTER, KEY_ESCAPE, KEY_TAB, OverlayModel
from qtile_pomodoro.tasks import TaskStore


@pytest.fixture()
def model(tmp_path: Path) -> OverlayModel:
    store = TaskStore(tmp_path / "tasks.json")
    store.add("alpha", "today")
    store.add("beta", "inbox")
    return OverlayModel(store)


def _type(model: OverlayModel, text: str) -> None:
    for ch in text:
        _, _ = model.key(ord(ch))


def test_enter_input_mode_typing_and_commit(model: OverlayModel) -> None:
    assert model.mode == "nav"
    _, _ = model.key(KEY_ENTER)  # enter input mode
    assert model.mode == "input"
    _type(model, "write docs")
    assert model.input == "write docs"
    _, _ = model.key(KEY_ENTER)  # commit to default target
    assert model.input == ""
    assert model.mode == "nav"
    assert [t.title for t in model.store.today] == ["alpha", "write docs"]


def test_direct_typing_from_nav_mode(model: OverlayModel) -> None:
    # any non-nav printable key starts typing immediately (no i/Enter needed)
    _, _ = model.key(ord("w"))
    _type(model, "rite report")
    assert model.mode == "input" and model.input == "write report"
    _, _ = model.key(KEY_ENTER)
    assert [t.title for t in model.store.today] == ["alpha", "write report"]


def test_tab_switches_add_target(model: OverlayModel) -> None:
    _, _ = model.key(KEY_TAB)
    assert model.target == "inbox"
    _, _ = model.key(KEY_ENTER); _type(model, "x"); _, _ = model.key(KEY_ENTER)
    assert [t.title for t in model.store.inbox] == ["beta", "x"]


def test_nav_select_complete_and_move(model: OverlayModel) -> None:
    # selection 0 = 'alpha' (today)
    _, _ = model.key(ord("j"))  # select 'beta' (inbox)
    assert model.selection == 1
    _, _ = model.key(ord("m"))  # move beta to today
    assert [t.title for t in model.store.today] == ["alpha", "beta"]
    assert model.store.inbox == []
    _, _ = model.key(ord("k"))
    assert model.selection == 0
    _, _ = model.key(ord("d"))  # complete alpha
    assert [t.title for t in model.store.today] == ["beta"]
    assert [t.title for t in model.store.completed] == ["alpha"]


def test_j_reaches_last_combined_row(model: OverlayModel) -> None:
    for _ in range(5):
        _, _ = model.key(ord("j"))
    assert model.selection == 1  # both rows reachable, clamped at last


def test_space_is_not_a_nav_action(model: OverlayModel) -> None:
    _, _ = model.key(ord(" "))
    assert model.mode == "nav"  # space is ignored in nav, never completes
    assert [t.title for t in model.store.today] == ["alpha"]


def test_space_is_literal_in_input_mode(model: OverlayModel) -> None:
    _, _ = model.key(KEY_ENTER); _type(model, "a b")
    assert model.input == "a b"
    assert [t.title for t in model.store.today] == ["alpha"]  # nothing completed


def test_escape_from_input_returns_to_nav_then_closes(model: OverlayModel) -> None:
    _, _ = model.key(KEY_ENTER); _type(model, "draft")
    _, close = model.key(KEY_ESCAPE)
    assert close is False and model.mode == "nav" and model.input == ""
    _, close = model.key(KEY_ESCAPE)
    assert close is True


def test_backspace_edit_input(model: OverlayModel) -> None:
    _, _ = model.key(KEY_ENTER); _type(model, "abc")
    _, _ = model.key(0xFF08)
    assert model.input == "ab"


def test_selection_clamped_to_rows(model: OverlayModel) -> None:
    for _ in range(5):
        _, _ = model.key(ord("j"))
    assert model.selection == 1  # only two rows
    _, _ = model.key(ord("k")); _, _ = model.key(ord("k"))
    assert model.selection == 0


def test_latin1_keysym_accepted(model: OverlayModel) -> None:
    _, _ = model.key(0xE9)  # é
    assert model.mode == "input" and model.input == "é"


def test_selection_clamped_to_visible_rows(model: OverlayModel) -> None:
    model.max_rows = 1  # overlay truncated the list to one visible row
    for _ in range(5):
        _, _ = model.key(ord("j"))
    assert model.selection == 0  # cannot walk onto hidden rows
    _, _ = model.key(ord("d"))   # completes the visible row only
    assert [t.title for t in model.store.today] == []
    assert [t.title for t in model.store.inbox] == ["beta"]
