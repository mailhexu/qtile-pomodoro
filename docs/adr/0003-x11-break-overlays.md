# X11-only break overlays

The first release supports Break Overlays only under Qtile on X11 and displays one on every physical screen. Qtile's verified Popup/Internal-window behavior provides controllable screen-sized surfaces on X11, while Wayland layer-shell surfaces can remain above those internals and cannot guarantee the requested full-screen intervention.

## Considered Options

- Best-effort Wayland overlays.
- A separate, non-Qtile overlay application.
