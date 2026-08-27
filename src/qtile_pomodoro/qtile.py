"""Qtile integration for qtile-pomodoro; import this module from config.py."""
from __future__ import annotations

import json
import subprocess
import sys
from typing import Any

from libqtile.popup import Popup
from libqtile.widget import base


def _command(command: str) -> list[str]:
    return [sys.executable, "-m", "qtile_pomodoro.cli", command]



def _status() -> dict[str, Any] | None:
    try:
        output = subprocess.check_output(_command("status") + ["--json"], text=True, timeout=0.5)
        return json.loads(output)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return None


class BreakOverlays:
    """One X11 internal window per screen, shown only for an active break."""
    def __init__(self, qtile: Any):
        self.qtile = qtile
        self.popups: list[Popup] = []

    def sync(self, state: dict[str, Any]) -> None:
        command = "skip" if state.get("overlay") else "start" if state["status"] == "resume" else None
        if command is None:
            for popup in self.popups: popup.hide()
            return
        seconds = state["remaining"]
        text = f"BREAK\n{seconds // 60:02d}:{seconds % 60:02d}" if command == "skip" else "BREAK COMPLETE"
        button_text = "Click here to skip break" if command == "skip" else "Click here to start work · or press Space"
        while len(self.popups) < len(self.qtile.screens):
            screen = self.qtile.screens[len(self.popups)]
            popup = Popup(
                self.qtile,
                x=screen.x,
                y=screen.y,
                width=screen.width,
                height=screen.height,
                background="#111111",
                foreground="#ffffff",
                fontsize=42,
                text_alignment="center",
            )
            popup.timer_layout = popup.drawer.textlayout(
                text="",
                colour="#ffffff",
                font_family="sans",
                font_size=42,
                font_shadow=None,
                wrap=False,
                markup=True,
            )
            popup.button_layout = popup.drawer.textlayout(
                text="",
                colour="#ffffff",
                font_family="sans",
                font_size=24,
                font_shadow=None,
                wrap=False,
                markup=True,
            )
            self.popups.append(popup)
        for screen, popup in zip(self.qtile.screens, self.popups):
            popup.x, popup.y, popup.width, popup.height = screen.x, screen.y, screen.width, screen.height
            popup.win.process_button_click = lambda x, y, button, height=screen.height, action=command: self.activate(x, y, button, height, action)
            popup.win.process_key_press = lambda keysym, action=command: self.keypress(keysym, action)
            popup.timer_layout.text = text
            popup.button_layout.text = button_text
            popup.clear()
            popup.timer_layout.draw((screen.width - popup.timer_layout.width) // 2, screen.height // 3)
            popup.button_layout.draw((screen.width - popup.button_layout.width) // 2, screen.height * 2 // 3)
            popup.draw()
            popup.place()
            popup.unhide()
            popup.win.focus()

    def activate(self, x: int, y: int, button: int, height: int, command: str) -> None:
        if button == 1 and y >= height * 2 // 3:
            subprocess.Popen(_command(command))

    def keypress(self, keysym: Any, command: str) -> None:
        if command == "start" and str(keysym).lower() in {"space", "32"}:
            subprocess.Popen(_command("start"))


class Pomodoro(base.InLoopPollText):
    """Display-only status widget. Controls belong in CLI-backed Qtile keys."""
    defaults = [("update_interval", 1.0, "Polling interval in seconds")]
    def __init__(self, **config: Any):
        super().__init__("Idle", **config)
        self.add_defaults(self.defaults)
        self.overlays: BreakOverlays | None = None

    def poll(self) -> str:
        state = _status()
        if state is None: return "Pomodoro unavailable"
        if self.overlays is None: self.overlays = BreakOverlays(self.qtile)
        self.overlays.sync(state)
        if state["status"] == "idle": return "Idle"
        if state["status"] == "paused": return f"Paused {state['phase']}"
        if state["status"] == "resume": return "Ready to work"
        return f"{state['phase'].replace('_', ' ').title()} {state['remaining'] // 60:02d}:{state['remaining'] % 60:02d} · {state['completed_in_cycle']}/{state['long_break_after']}"
