"""X11 stacking and lifecycle regressions for the Qtile integration."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

pytest.importorskip("libqtile", reason="Run integration tests in the Qtile environment")
pytest.importorskip("xcffib", reason="X11 integration requires xcffib")

from libqtile import hook
from libqtile.backend.x11.window import Internal
from xcffib.xproto import StackMode

from qtile_pomodoro import qtile as integration


class _Resource:
    def __init__(self):
        self.finalized = False

    def finalize(self):
        self.finalized = True


class _Layout(_Resource):
    width = 80
    text = ""

    def draw(self, x, y):
        pass


class _Drawer(_Resource):
    def textlayout(self, **kwargs):
        return _Layout()


class _XWindow:
    def __init__(self, qtile):
        self.qtile = qtile
        self.hidden = True
        self.destroyed = False
        qtile.stack.append(self)

    def configure(self, *, stackmode):
        assert stackmode == StackMode.Above
        self.qtile.stack.remove(self)
        self.qtile.stack.append(self)


class _Internal:
    group = None

    def __init__(self, qtile):
        self.qtile = qtile
        self.window = _XWindow(qtile)
        qtile.windows_map[id(self)] = self

    def place(self, *args, above=False):
        if above:
            # Exercise Qtile's real group=None early return, not a fake raise.
            Internal.change_layer(self)

    def focus(self):
        # X input focus alone does not change the root stacking order.
        self.qtile.focus = self.window


class _Popup:
    def __init__(self, qtile, *, x, y, width, height, **kwargs):
        self.x, self.y, self.width, self.height = x, y, width, height
        self.win = _Internal(qtile)
        self.drawer = _Drawer()
        self.layout = _Layout()

    def clear(self):
        pass

    def draw(self):
        pass

    def place(self):
        self.win.place(self.x, self.y, self.width, self.height, above=True)

    def unhide(self):
        # MapWindow preserves the existing root-stack position of a reused window.
        self.win.window.hidden = False

    def hide(self):
        self.win.window.hidden = True

    def kill(self):
        self.win.window.destroyed = True
        del self.win.qtile.windows_map[id(self.win)]
        self.layout.finalize()
        self.drawer.finalize()


class _Qtile:
    def __init__(self):
        self.screens = [SimpleNamespace(x=0, y=0, width=800, height=600)]
        self.current_screen = self.screens[0]
        self.windows_map = {}
        self.stack = []
        self.focus = None
        self.clients = []

    @property
    def visible_stack(self):
        return [win for win in self.stack if not win.hidden and not win.destroyed]

    def switch_group(self):
        for client in self.clients:
            client.hidden = True
        # Screen.set_group maps/layouts and focuses new clients before setgroup.
        client = _XWindow(self)
        client.hidden = False
        self.windows_map[id(client)] = client
        self.clients = [client]
        self.focus = client
        hook.fire("setgroup")
        return client


def _state(command):
    return {
        "phase": "short_break" if command == "skip" else "focus",
        "status": "resume" if command == "start" else "running",
        "remaining": 60,
        "overlay": command == "skip",
        "completed_in_cycle": 1,
        "long_break_after": 4,
    }


@pytest.fixture
def qtile(monkeypatch):
    monkeypatch.setattr(hook, "subscriptions", {})
    monkeypatch.setattr(integration, "Popup", _Popup)
    # Workspace hooks must not poll the daemon, even while an overlay is active.
    def unexpected_status():
        pytest.fail("Workspace switching must not query daemon status")

    monkeypatch.setattr(integration, "_status", unexpected_status)
    return _Qtile()


@pytest.mark.parametrize("command", ["skip", "start"])
def test_reused_overlay_stays_above_occupied_workspaces(qtile, command):
    overlays = integration.BreakOverlays(qtile)
    qtile.switch_group()
    overlays.sync(_state(command))
    popup = overlays.popups[0]
    window = popup.win.window
    assert qtile.visible_stack[-1] is window
    assert qtile.focus is window

    overlays.sync(_state(None))
    client = qtile.switch_group()
    assert qtile.stack.index(window) < qtile.stack.index(client)
    # Popup.place(above=True) cannot raise an Internal with no group.
    popup.place()
    assert qtile.stack.index(window) < qtile.stack.index(client)

    overlays.sync(_state(command))
    assert overlays.popups[0] is popup
    assert qtile.visible_stack[-1] is window
    assert qtile.focus is window

    # No poll or timer tick occurs between mapping the next group and assertions.
    qtile.switch_group()
    assert qtile.visible_stack[-1] is window
    assert qtile.focus is window
    overlays.finalize()


def test_inactive_workspace_hook_does_not_raise_or_focus(qtile):
    overlays = integration.BreakOverlays(qtile)
    client = qtile.switch_group()
    assert qtile.focus is client
    overlays.sync(_state("start"))
    window = overlays.popups[0].win.window
    overlays.sync(_state(None))
    client = qtile.switch_group()
    assert window.hidden
    assert qtile.stack.index(window) < qtile.stack.index(client)
    assert qtile.visible_stack[-1] is client
    assert qtile.focus is client
    overlays.finalize()


def test_overlays_cover_all_screens_and_focus_current_screen(qtile):
    qtile.screens.append(SimpleNamespace(x=800, y=0, width=800, height=600))
    overlays = integration.BreakOverlays(qtile)
    qtile.switch_group()
    overlays.sync(_state("start"))
    client = qtile.switch_group()
    for popup in overlays.popups:
        assert qtile.stack.index(popup.win.window) > qtile.stack.index(client)
    assert qtile.focus is overlays.popups[0].win.window
    overlays.finalize()


def test_widget_finalize_destroys_popups_and_unsubscribes(qtile, monkeypatch):
    monkeypatch.setattr(integration, "_status", lambda: _state("start"))
    widget = integration.Pomodoro()
    widget.qtile = qtile
    widget.drawer = _Drawer()
    widget.poll()
    overlays = widget.overlays
    popup = overlays.popups[0]
    widget.finalize()

    assert widget.finalized
    assert widget.overlays is None
    assert overlays.popups == []
    assert popup.win.window.destroyed
    assert all(resource.finalized for resource in (
        popup.timer_layout, popup.button_layout, popup.layout, popup.drawer,
    ))
    assert not hook.subscriptions["qtile"]["setgroup"]
    client = qtile.switch_group()
    # A stale callback reference must also be inert after finalization.
    overlays._restack()
    assert qtile.visible_stack[-1] is client
    assert qtile.focus is client

    replacement = integration.Pomodoro()
    replacement.qtile = qtile
    replacement.drawer = _Drawer()
    replacement.poll()
    assert qtile.visible_stack[-1] is replacement.overlays.popups[0].win.window
    assert len(hook.subscriptions["qtile"]["setgroup"]) == 1
    replacement.finalize()
    assert not hook.subscriptions["qtile"]["setgroup"]


@pytest.mark.parametrize("command", ["skip", "start"])
def test_controls_preserve_active_actions_but_ignore_stale_input(qtile, monkeypatch, command):
    launched = []
    monkeypatch.setattr(integration.subprocess, "Popen", lambda args: launched.append(args[-1]))
    overlays = integration.BreakOverlays(qtile)
    overlays.sync(_state(command))
    popup = overlays.popups[0]
    popup.win.process_button_click(10, 10, 1)
    assert launched == []
    popup.win.process_button_click(10, 500, 1)
    assert launched == [command]
    popup.win.process_key_press("space")
    assert launched == ([command, "start"] if command == "start" else [command])
    launched.clear()

    overlays.sync(_state(None))
    popup.win.process_button_click(10, 500, 1)
    popup.win.process_key_press("space")
    overlays.finalize()
    popup.win.process_button_click(10, 500, 1)
    popup.win.process_key_press("space")
    assert launched == []
