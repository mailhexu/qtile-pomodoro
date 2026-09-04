---
type: Contributor Guide
title: Qtile Integration Constraints
status: stable
audience: development
tags: [qtile, python, integration]
---

# Qtile Integration Constraints

Qtile runs in its own UV-managed Python environment. Install this package with `uv pip install --python ~/.local/share/uv/tools/qtile/bin/python .`; a pipx installation cannot expose the widget module to Qtile.

Use `sys.executable -m qtile_pomodoro.cli` from Qtile configuration and widgets. Do not launch the `~/.local/bin/qtile-pomodoro` wrapper: its system-Python shebang cannot import the package when user site-packages are disabled.

Qtile 0.37 provides `base.InLoopPollText`, not `ThreadPoolText`. Package upgrades require a Qtile restart because configuration reload does not reload imported package modules.
