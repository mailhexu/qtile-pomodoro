# Local service with a Qtile adapter

Timer state, notifications, break-overlay requests, and session history belong to a local Timer Service exposed through a CLI or local API; Qtile starts it once per session and the Qtile Widget only presents and controls it. This preserves an active timer through Qtile bar reloads and enables lightweight keybinding integration without making Qtile the owner of persistent state.

## Considered Options

- Keep the timer entirely in a Qtile-native widget.
- Build a standalone GUI application.
