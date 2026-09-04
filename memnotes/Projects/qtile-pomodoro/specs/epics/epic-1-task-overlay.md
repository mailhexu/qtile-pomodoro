---
status: done
created: 2026-09-04
updated: 2026-09-04
linked_prd: ../prd.md
linked_architecture: ../architecture.md
linked_stories: [../stories/story-1-task-store.md, ../stories/story-2-today-count-widget.md, ../stories/story-3-task-overlay.md]
---

# Epic 1: Minimal Qtile Task Overlay

## Description

Deliver a daemonless, Qtile-native task capture and review feature: Inbox and Today lists, a keyboard-driven popup overlay summoned by Mod+N, and a Today counter in the Qtile bar, persisted locally as JSON.

## Scope

### In Scope

- Pure-stdlib task store with JSON persistence (atomic writes, hidden completed history)
- `TaskCount` bar widget with click-to-open
- Centered popup overlay: view lists, add via inline line editor, complete, move, close
- `Mod+N` keybinding and bar wiring in `~/.config/qtile/config.py`
- Unit tests for the store; live smoke verification of the widget and overlay

### Out of Scope

- Todoist sync, dates/recurrence, labels, projects, reminders, notifications
- Any daemon or IPC protocol
- Wayland support

## Stories

| Story | Title | Status |
|-------|-------|--------|
| [story-1](../stories/story-1-task-store.md) | TaskStore with JSON persistence | done |
| [story-2](../stories/story-2-today-count-widget.md) | TaskCount bar widget and config wiring | done |
| [story-3](../stories/story-3-task-overlay.md) | Keyboard-driven TaskOverlay popup | done |

## Success Criteria

- [ ] All stories complete
- [ ] Unit tests pass under the mydev pytest environment
- [ ] Live smoke: add/complete/move via Mod+N overlay; bar count tracks; restart preserves tasks
- [ ] Code reviewed and approved

## Progress

- Stories: 3/3 done
- Last updated: 2026-09-04
