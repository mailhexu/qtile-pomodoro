"""Qtile bar counter and popup overlay for task management.

Import from config.py::

    from qtile_pomodoro.task_widget import TaskCount, TaskOverlay
"""
from __future__ import annotations

from typing import Any

from libqtile.popup import Popup
from libqtile.widget import base

from .tasks import TaskStore
from .task_model import (HINT_COLOUR, INBOX_COLOUR, OverlayModel, TEXT_COLOUR,
                         TODAY_COLOUR, format_count)

# ------------------------------------------------------------- bar widget

_STORE: TaskStore | None = None


def get_store() -> TaskStore:
    global _STORE
    if _STORE is None:
        _STORE = TaskStore()
    return _STORE


class TaskCount(base.InLoopPollText):
    """Shows ``Tasks:N`` (incomplete Today count); click toggles the overlay."""

    defaults = [("update_interval", 1.0, "Polling interval in seconds")]

    def __init__(self, **config: Any):
        super().__init__(format_count(0), **config)
        self.add_defaults(TaskCount.defaults)
        self._mtime: float | None = None

    def poll(self) -> str:
        store = get_store()
        try:
            mtime = store.path.stat().st_mtime
        except OSError:
            mtime = None
        if mtime != self._mtime:
            store.reload()
            self._mtime = mtime
        return format_count(store.today_count)

    def button_press(self, x: int, y: int, button: int) -> None:
        if button == 1:
            TaskOverlay.toggle(self.qtile)
        super().button_press(x, y, button)


# ---------------------------------------------------------- popup overlay

class TaskOverlay:
    """Centered popup listing Today/Inbox with a keyboard line editor."""

    _current: "TaskOverlay | None" = None
    WIDTH, HEIGHT = 700, 520
    LINE_HEIGHT = 22
    HEADER_Y = 16
    DONE_SHOWN = 5
    def __init__(self, qtile: Any):
        self.qtile = qtile
        self.store = get_store()
        self.model = OverlayModel(self.store)
        screen = qtile.current_screen
        self.popup = Popup(
            qtile,
            x=screen.x + (screen.width - self.WIDTH) // 2,
            y=screen.y + (screen.height - self.HEIGHT) // 2,
            width=self.WIDTH,
            height=self.HEIGHT,
            background="#111111",
            border="#5fafff",
            border_width=2,
        )
        self.popup.win.process_key_press = self._on_key
        self.popup.win.process_button_click = self._on_click
        # Dedicated layouts created once and redrawn each pass — the pattern
        # proven by the Break Overlay; mutating a shared layout per line does
        # not render reliably.
        def _layout(colour: str) -> Any:
            return self.popup.drawer.textlayout(
                text="", colour=colour, font_family="sans", font_size=16,
                font_shadow=None, wrap=False, markup=False)

        self.today_header = _layout("#5fafff")
        self.inbox_header = _layout("#d75f5f")
        self.done_header = _layout("#808080")
        self.done_items = _layout("#808080")
        self.today_items = _layout("#ffffff")
        self.inbox_items = _layout("#ffffff")
        self.input_line = _layout("#ffffff")
        self.hint = _layout("#808080")
        self._draw()

    @classmethod
    def toggle(cls, qtile: Any) -> None:
        if cls._current is not None:
            cls._current.close()
        else:
            cls._current = cls(qtile)

    def close(self) -> None:
        type(self)._current = None
        try:
            self.popup.kill()
        except Exception:
            pass

    def _on_key(self, keysym: int) -> None:
        redraw, close = self.model.key(keysym)
        if close:
            self.close()
        elif redraw:
            self._draw()

    def _visible_rows(self) -> list[dict[str, Any]]:
        """Single source of geometry for both drawing and click hit-testing.

        The model's selection is clamped to the VISIBLE rows: navigation,
        completion, and moving can never act on a hidden truncated row.
        """
        rows: list[dict[str, Any]] = []
        y = self.HEADER_Y
        rows.append({"kind": "header", "y": y})
        y += self.LINE_HEIGHT
        tasks: list[tuple[str, Any]] = \
            [("today", t) for t in self.store.today] + \
            [("inbox", t) for t in self.store.inbox]
        max_rows = (self.HEIGHT - 110 - 2 * self.LINE_HEIGHT
                    - self.DONE_SHOWN * self.LINE_HEIGHT) // self.LINE_HEIGHT
        shown = tasks[:max_rows]
        # keep the Inbox section header visible even when its items are cut
        today_shown = sum(1 for name, _ in shown if name == "today")
        inbox_shown = len(shown) - today_shown
        self.model.max_rows = len(shown)
        self.model.clamp_selection()
        index = 0
        for list_name, task in shown[:today_shown]:
            rows.append({"kind": "task", "task": task, "index": index,
                         "selected": index == self.model.selection, "y": y})
            index += 1
            y += self.LINE_HEIGHT
        rows.append({"kind": "inbox_header", "y": y})
        y += self.LINE_HEIGHT
        for list_name, task in shown[today_shown:]:
            rows.append({"kind": "task", "task": task, "index": index,
                         "selected": index == self.model.selection, "y": y})
            index += 1
            y += self.LINE_HEIGHT
        if len(tasks) > max_rows:
            rows.append({"kind": "more", "count": len(tasks) - max_rows, "y": y})
            y += self.LINE_HEIGHT
        done = list(reversed(self.store.completed))[:self.DONE_SHOWN]
        rows.append({"kind": "done_header", "count": len(self.store.completed), "y": y})
        y += self.LINE_HEIGHT
        for task in done:
            rows.append({"kind": "done", "task": task, "y": y})
            y += self.LINE_HEIGHT
        if len(self.store.completed) > self.DONE_SHOWN:
            rows.append({"kind": "done_more",
                         "count": len(self.store.completed) - self.DONE_SHOWN, "y": y})
        return rows

    def _on_click(self, x: int, y: int, button: int) -> None:
        if button != 1:
            return
        for row in self._visible_rows():
            if row["kind"] != "task":
                continue
            if row["y"] <= y < row["y"] + self.LINE_HEIGHT:
                self.store.complete(row["task"].id)
                self._draw()
                return

    def _draw(self) -> None:
        popup = self.popup
        popup.clear()
        today_titles: list[str] = []
        inbox_titles: list[str] = []
        done_titles: list[str] = []
        selected_y: int | None = None
        for row in self._visible_rows():
            if row["kind"] == "header":
                self.today_header.text = f"Today ({len(self.store.today)})"
                self.today_header.draw(20, row["y"])
            elif row["kind"] == "inbox_header":
                self.inbox_header.text = f"Inbox ({len(self.store.inbox)})"
                self.inbox_header.draw(20, row["y"])
            elif row["kind"] == "more":
                self.hint.text = f"… {row['count']} more"
                self.hint.draw(20, row["y"])
            elif row["kind"] == "done_header":
                self.done_header.text = f"Done ({row['count']})"
                self.done_header.draw(20, row["y"])
            elif row["kind"] == "done":
                done_titles.append(f"  ✓ {row['task'].title}")
            elif row["kind"] == "done_more":
                self.hint.text = f"… {row['count']} more done"
                self.hint.draw(20, row["y"])
            else:
                (today_titles if row["task"] in self.store.today else inbox_titles)\
                    .append(f"  {row['task'].title}")
                if row["selected"]:
                    selected_y = row["y"]

        # selection highlight bar behind the selected row, drawn first
        if selected_y is not None:
            ctx = popup.drawer.ctx
            ctx.set_source_rgb(0.16, 0.24, 0.40)
            ctx.rectangle(8, selected_y - 3, self.WIDTH - 16, self.LINE_HEIGHT)
            ctx.fill()

        for block, titles in ((self.today_items, today_titles),
                              (self.inbox_items, inbox_titles)):
            if titles:
                block.text = "\n".join(titles)
        if done_titles:
            self.done_items.text = "\n".join(done_titles)
            done_y = next(r["y"] for r in self._visible_rows() if r["kind"] == "done")
            self.done_items.draw(20, done_y)

        today_y = next((r["y"] for r in self._visible_rows()
                        if r["kind"] == "task" and r["task"] in self.store.today), None)
        inbox_y = next((r["y"] for r in self._visible_rows()
                        if r["kind"] == "task" and r["task"] in self.store.inbox), None)
        if today_y is not None:
            self.today_items.draw(20, today_y)
        if inbox_y is not None:
            self.inbox_items.draw(20, inbox_y)

        if self.model.mode == "input":
            prefix = f"+ [{self.model.target}] "
        else:
            prefix = "[NAV] "
        self.input_line.text = f"{prefix}{self.model.input}_"
        self.input_line.draw(20, self.HEIGHT - 56)
        self.hint.text = "type to add  Tab:target  j/k:select  d:done  m:move  Esc:close/back"
        self.hint.draw(20, self.HEIGHT - 32)

        popup.draw()
        popup.place()
        popup.unhide()
        popup.win.focus()
