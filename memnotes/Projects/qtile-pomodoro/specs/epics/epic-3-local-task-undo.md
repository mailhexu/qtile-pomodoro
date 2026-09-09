---
status: done
created: 2026-09-09
updated: 2026-09-09
linked_prd: ../prd-task-undo.md
linked_architecture: ../architecture-task-undo.md
linked_stories: [../stories/story-7-local-task-undo.md]
---

# Epic 3: Local Task Undo

## Description

Deliver a safe one-step undo for the most recent local completion or Today/Inbox
move from the Qtile Task Overlay.

## Scope

### In Scope

- Transient `UndoAction` held only for the current Qtile session.
- Atomic local reversal of a completion or move through `TaskStore`.
- `u` navigation command, on-screen local-only hint, and consumer guide.
- Unified keyboard and mouse completion path.
- Unit and live local-store verification.

### Out of Scope

- Undo while Todoist sync is enabled.
- Redo, multi-step history, cross-restart persistence, or remote commands.

## Story Plan

| Story | Title | Status |
|-------|-------|--------|
| [Story 7](../stories/story-7-local-task-undo.md) | One-step local task undo | done |

## Success Criteria

- [x] The latest local completion and move are reversible exactly once.
- [x] Sync-enabled `u` is safe and clearly identified as unavailable.
- [x] Store/model tests and a live local Qtile smoke pass.
- [x] Consumer guidance and code review are complete.
