---
type: Consumer Guide
title: Using the Task Overlay
status: stable
audience: usage
tags: [qtile, tasks, overlay]
---

# Using the Task Overlay

Press `Mod+N` (or click `Tasks:N` in the bar) to open a centered popup listing
**Today** and **Inbox** tasks. The bar counter shows incomplete Today tasks
and updates within a second of any change.

- **Add**: start typing (or press `i`/`Enter`); `Tab` switches the add-target
  between Today and Inbox; `Enter` commits.
- **Navigate**: `j`/`k` move the highlight across both lists.
- **Complete**: `d` on the selected row, or click the row. Completed tasks are
  hidden but retained in `~/.local/share/qtile-pomodoro/tasks.json`.
- **Move**: `m` swaps the selected task between Today and Inbox.
- **Close**: `Esc` (backs out of typing first) or `Mod+N` again.

Space is deliberately not a completion key — single-key completion caused
accidental task removal. Titles beginning with `j/k/m/d/i` need `i` or
`Enter` first to enter typing mode. Tasks persist across Qtile restarts.
