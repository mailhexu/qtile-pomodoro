"""Pure interaction model for the task overlay: no Qtile imports."""
from __future__ import annotations

from typing import Any

from .tasks import TaskStore

KEY_BACKSPACE = 0xFF08
KEY_TAB = 0xFF09
KEY_ENTER = 0xFF0D
KEY_ESCAPE = 0xFF1B

TODAY_COLOUR = (0.376, 0.686, 1.0)     # #5fafff
INBOX_COLOUR = (0.843, 0.373, 0.373)   # #d75f5f
TEXT_COLOUR = (1.0, 1.0, 1.0)
HINT_COLOUR = (0.5, 0.5, 0.5)


NAV_KEYS = {"j", "k", "m", "d", "i", "u", " "}

def format_count(count: int) -> str:
    return f"Tasks:{count}"


def keysym_to_char(keysym: int) -> str | None:
    """X11 Latin-1 printable keysyms map directly to Unicode characters."""
    if 0x20 <= keysym <= 0xFF and not (0x7F <= keysym <= 0xA0) and keysym != 0xAD:
        return chr(keysym)
    return None

class OverlayModel:
    """Pure interaction state: nav mode for list actions, input mode for typing."""

    def __init__(self, store: TaskStore, max_rows: int | None = None):
        self.store = store
        self.mode = "nav"
        self.input = ""
        self.target = "today"
        self.selection = 0
        self.max_rows = max_rows  # set by the overlay to the visible row count
        self._undo_action = None  # latest local mutation (Story 7)
        self.undo_status = ""     # brief feedback for the overlay hint

    def _rows(self) -> list[tuple[str, Any]]:
        return [("today", t) for t in self.store.today] + \
               [("inbox", t) for t in self.store.inbox]

    def clamp_selection(self) -> None:
        limit = len(self._rows())
        if self.max_rows is not None:
            limit = min(limit, self.max_rows)
        self.selection = max(0, min(self.selection, max(0, limit - 1)))

    def apply_complete(self, task_id: str) -> None:
        """Complete by id from any caller (keyboard or mouse); records undo."""
        self._undo_action = self.store.complete(task_id)

    def apply_move(self, task_id: str) -> None:
        """Move by id from any caller; records undo."""
        self._undo_action = self.store.move(task_id)
    def apply_undo(self) -> None:
        """Reverse the latest local action; safe no-op when none retained."""
        if self.store.engine is not None:
            self._undo_action = None  # sync became active: drop local undo
            self.undo_status = "undo off (sync)"
            return
        if self._undo_action is None:
            self.undo_status = "nothing to undo"
            return
        rows = self._rows()
        selected_id = rows[self.selection][1].id if rows else None
        if self.store.undo(self._undo_action):
            self._undo_action = None
            self.undo_status = "undone"
        else:
            self._undo_action = None  # stale: state moved on
            self.undo_status = "nothing to undo"
        if selected_id is not None:
            for i, (_, task) in enumerate(self._rows()):
                if task.id == selected_id:
                    self.selection = i
                    break
            self.clamp_selection()

    def key(self, keysym: int) -> tuple[bool, bool]:
        """Feed one keysym. Returns (redraw, close)."""
        self.undo_status = ""  # status shows only until the next key
        if keysym == KEY_TAB:
            self.target = "inbox" if self.target == "today" else "today"
            return True, False

        if self.mode == "input":
            if keysym == KEY_ESCAPE:
                self.mode, self.input = "nav", ""
                return True, False
            if keysym == KEY_ENTER:
                if self.input.strip():
                    self.store.add(self.input.strip(), self.target)
                self.mode, self.input = "nav", ""
                return True, False
            if keysym == KEY_BACKSPACE:
                self.input = self.input[:-1]
                return True, False
            char = keysym_to_char(keysym)
            if char is not None:
                self.input += char
                return True, False
            return False, False

        # nav mode
        if keysym == KEY_ESCAPE:
            return False, True
        char = keysym_to_char(keysym)
        rows = self._rows()
        if not rows:
            if char == "u":  # undo must work with every task completed
                self.apply_undo()
                return True, False
            if char is not None and char not in NAV_KEYS:
                self.mode, self.input = "input", char
                return True, False
            return False, False
        if char is not None and char not in NAV_KEYS:
            # any other printable key starts typing immediately
            self.mode, self.input = "input", char
            return True, False
        if keysym == KEY_ENTER or char == "i":
            self.mode = "input"
            return True, False
        self.clamp_selection()
        _, task = rows[self.selection]
        if char == "j":
            self.selection += 1
        elif char == "k":
            self.selection -= 1
        elif char == "d":
            self.apply_complete(task.id)
        elif char == "m":
            self.apply_move(task.id)
        elif char == "u":
            self.apply_undo()
        else:
            return False, False
        self.clamp_selection()
        return True, False
