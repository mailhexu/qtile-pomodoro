"""Qtile bar counter and popup overlay for task management.

Import from config.py::

    from qtile_pomodoro.task_widget import TaskCount, TaskOverlay
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from libqtile import pangocffi
from libqtile.popup import Popup
from libqtile.widget import base

from .tasks import TaskStore
from .task_model import (HINT_COLOUR, INBOX_COLOUR, OverlayModel, TEXT_COLOUR,
                         TODAY_COLOUR, format_count, keysym_to_char)


def _todoist_token() -> str | None:
    """Token source: env var, config.toml, or the user's interactive shell.

    Qtile does not inherit ~/.bashrc exports, so as a last resort we ask an
    interactive bash once (the token never touches disk).
    """
    token = os.environ.get("TODOIST_API_TOKEN")
    if token:
        return token
    try:
        import tomllib
        path = (Path(os.environ.get("XDG_CONFIG_HOME",
                                    Path.home() / ".config"))
                / "qtile-pomodoro" / "config.toml")
        with open(path, "rb") as fh:
            token = tomllib.load(fh).get("tasks", {}).get("todoist_api_token")
        if token:
            return token
    except (OSError, ValueError):
        pass
    import subprocess
    try:
        out = subprocess.run(
            ["bash", "-ic", 'printf %s "$TODOIST_API_TOKEN"'],
            capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


# ------------------------------------------------------------- bar widget

_STORE: TaskStore | None = None


def get_store() -> TaskStore:
    global _STORE
    if _STORE is None:
        _STORE = TaskStore()
        token = _todoist_token()
        if token:
            from .todoist import SyncEngine, TodoistClient
            _STORE.engine = SyncEngine(_STORE, TodoistClient(token))
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
        if store.engine is not None:
            # engine keeps this store object authoritative in memory;
            # file reloads here would race the worker's queue edits
            return format_count(store.today_count)
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
    TASK_TEXT_WIDTH = WIDTH - 40
    MAX_TASK_LINES = 2
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
            layout = self.popup.drawer.textlayout(
                text="", colour=colour, font_family="sans", font_size=16,
                font_shadow=None, wrap=False, markup=False)
            layout.layout.set_alignment(pangocffi.ALIGNMENTS["left"])
            return layout

        self.today_header = _layout("#5fafff")
        self.inbox_header = _layout("#d75f5f")
        self.done_header = _layout("#808080")
        self.done_items = _layout("#808080")
        self.today_items = _layout("#ffffff")
        self.inbox_items = _layout("#ffffff")
        self._measure_items = _layout("#ffffff")
        self.input_line = _layout("#ffffff")
        self.hint = _layout("#808080")
        self._alive = True
        self._draw()
        self._refresh_async()

    @classmethod
    def toggle(cls, qtile: Any) -> None:
        if cls._current is not None:
            cls._current.close()
        else:
            cls._current = cls(qtile)

    def close(self) -> None:
        self._alive = False
        type(self)._current = None
        try:
            self.popup.kill()
        except Exception:
            pass

    def _refresh_async(self) -> None:
        """Kick a background refresh; redraw on completion if still open."""
        engine = self.store.engine
        if engine is None:
            return
        seen = self.store.sync["revision"]

        def done() -> None:
            if self._alive and self.store.sync["revision"] != seen:
                self._draw()

        engine.refresh_async(done, self.qtile)  # single-flight worker

    def _on_key(self, keysym: int) -> None:
        # 'r' force-refresh must be intercepted in nav mode BEFORE the
        # model routes any non-nav printable into input mode; keysym_to_char
        # range-checks (media keysyms exceed chr()'s domain)
        if (keysym_to_char(keysym) == "r" and self.model.mode == "nav"
                and not self.model.input):
            self._refresh_async()
            return
        redraw, close = self.model.key(keysym)
        if close:
            self.close()
        elif redraw:
            self._draw()

    def _text_width(self, text: str) -> int:
        self._measure_items.text = text
        return self._measure_items.width

    def _fitting_prefix(self, text: str, prefix: str = "", suffix: str = "") -> int:
        """Return the longest non-empty prefix fitting the task column."""
        low, high = 1, len(text)
        while low <= high:
            middle = (low + high) // 2
            if self._text_width(prefix + text[:middle] + suffix) <= self.TASK_TEXT_WIDTH:
                low = middle + 1
            else:
                high = middle - 1
        return max(1, high)

    def _ellipsis(self, line: str) -> str:
        if self._text_width(line + "…") <= self.TASK_TEXT_WIDTH:
            return line + "…"
        end = self._fitting_prefix(line, suffix="…")
        return line[:end].rstrip() + "…"

    def _wrapped_lines(self, title: str, prefix: str = "") -> list[str]:
        """Return at most two Pango-width-bounded visual lines."""
        lines: list[str] = []
        line = prefix
        for word in title.split() or [""]:
            separator = "" if line in ("", prefix) else " "
            candidate = f"{line}{separator}{word}"
            if self._text_width(candidate) <= self.TASK_TEXT_WIDTH:
                line = candidate
                continue
            if line != prefix:
                lines.append(line)
                line = ""
            while self._text_width(line + word) > self.TASK_TEXT_WIDTH:
                end = self._fitting_prefix(word, prefix=line)
                lines.append(line + word[:end])
                word = word[end:]
                line = ""
            line += word
        lines.append(line)
        if len(lines) > self.MAX_TASK_LINES:
            lines = lines[:self.MAX_TASK_LINES]
            lines[-1] = self._ellipsis(lines[-1])
        return lines

    def _visible_rows(self) -> list[dict[str, Any]]:
        """Single source of geometry for drawing and click hit-testing.

        The model's selection is clamped to visible logical tasks. A task's
        wrapped visual lines share one row, so selection and clicks cover its
        entire rendered height.
        """
        done = [
            (task, self._wrapped_lines(task.title, "✓ "))
            for task in list(reversed(self.store.completed))[:self.DONE_SHOWN]
        ]
        done_height = self.LINE_HEIGHT + sum(
            len(lines) * self.LINE_HEIGHT for _, lines in done
        )
        if len(self.store.completed) > self.DONE_SHOWN:
            done_height += self.LINE_HEIGHT

        tasks = [
            (name, task, self._wrapped_lines(task.title))
            for name, task in ([("today", task) for task in self.store.today]
                               + [("inbox", task) for task in self.store.inbox])
        ]
        content_bottom = self.HEIGHT - 100
        task_budget = max(
            0,
            content_bottom - self.HEADER_Y - 3 * self.LINE_HEIGHT - done_height,
        )
        shown: list[tuple[str, Any, list[str]]] = []
        used = 0
        for task_data in tasks:
            height = len(task_data[2]) * self.LINE_HEIGHT
            if used + height > task_budget:
                break
            shown.append(task_data)
            used += height

        today_shown = sum(1 for name, _, _ in shown if name == "today")
        self.model.max_rows = len(shown)
        self.model.clamp_selection()

        rows: list[dict[str, Any]] = []
        y = self.HEADER_Y
        rows.append({"kind": "header", "y": y})
        y += self.LINE_HEIGHT
        index = 0
        for _, task, lines in shown[:today_shown]:
            height = len(lines) * self.LINE_HEIGHT
            rows.append({
                "kind": "task", "task": task, "index": index,
                "selected": index == self.model.selection, "y": y,
                "lines": lines, "height": height,
            })
            index += 1
            y += height
        rows.append({"kind": "inbox_header", "y": y})
        y += self.LINE_HEIGHT
        for _, task, lines in shown[today_shown:]:
            height = len(lines) * self.LINE_HEIGHT
            rows.append({
                "kind": "task", "task": task, "index": index,
                "selected": index == self.model.selection, "y": y,
                "lines": lines, "height": height,
            })
            index += 1
            y += height
        if len(tasks) > len(shown):
            rows.append({"kind": "more", "count": len(tasks) - len(shown), "y": y})
            y += self.LINE_HEIGHT
        rows.append({
            "kind": "done_header", "count": len(self.store.completed), "y": y,
        })
        y += self.LINE_HEIGHT
        for task, lines in done:
            height = len(lines) * self.LINE_HEIGHT
            rows.append({
                "kind": "done", "task": task, "y": y,
                "lines": lines, "height": height,
            })
            y += height
        if len(self.store.completed) > self.DONE_SHOWN:
            rows.append({
                "kind": "done_more",
                "count": len(self.store.completed) - self.DONE_SHOWN, "y": y,
            })
        return rows

    def _on_click(self, x: int, y: int, button: int) -> None:
        if button != 1:
            return
        for row in self._visible_rows():
            if row["kind"] != "task":
                continue
            if row["y"] <= y < row["y"] + row["height"]:
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
        selected_height = 0
        for row in self._visible_rows():
            if row["kind"] == "header":
                self.today_header.text = f"Today ({len(self.store.today)})"
                self.today_header.draw(20, row["y"])
                pending = len(self.store.sync["queue"])
                if pending or self.store._overflow:
                    self.hint.text = ("! " if self.store._overflow
                                      else f"↻{pending} ")
                    self.hint.draw(self.WIDTH - 90, row["y"])
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
                done_titles.extend(row["lines"])
            elif row["kind"] == "done_more":
                self.hint.text = f"… {row['count']} more done"
                self.hint.draw(20, row["y"])
            else:
                (today_titles if row["task"] in self.store.today else inbox_titles)\
                    .extend(row["lines"])
                if row["selected"]:
                    selected_y = row["y"]
                    selected_height = row["height"]

        # selection highlight bar behind the selected row, drawn first
        if selected_y is not None:
            ctx = popup.drawer.ctx
            ctx.set_source_rgb(0.16, 0.24, 0.40)
            ctx.rectangle(8, selected_y - 3, self.WIDTH - 16, selected_height)
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
        self.hint.text = ("type to add  Tab:target  j/k:select  d:done  "
                          "m:move  r:refresh  Esc:close/back")
        self.hint.draw(20, self.HEIGHT - 32)

        popup.draw()
        popup.place()
        popup.unhide()
        popup.win.focus()
