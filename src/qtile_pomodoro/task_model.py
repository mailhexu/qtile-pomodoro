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


NAV_KEYS = {"j", "k", "m", "d", "i", " "}

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

    def _rows(self) -> list[tuple[str, Any]]:
        return [("today", t) for t in self.store.today] + \
               [("inbox", t) for t in self.store.inbox]

    def clamp_selection(self) -> None:
        limit = len(self._rows())
        if self.max_rows is not None:
            limit = min(limit, self.max_rows)
        self.selection = max(0, min(self.selection, max(0, limit - 1)))

    def key(self, keysym: int) -> tuple[bool, bool]:
        """Feed one keysym. Returns (redraw, close)."""
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
            self.store.complete(task.id)
        elif char == "m":
            self.store.move(task.id)
        else:
            return False, False
        self.clamp_selection()
        return True, False
