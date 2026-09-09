---
status: draft
created: 2026-09-09
updated: 2026-09-09
feature: task-undo
related_architecture: []
related_epics: []
---

# PRD: Undo Task Completion and Move

## Problem

The Task Overlay executes `d`/click completion and `m` moves immediately. A mistaken action requires manual recovery through the task file or re-entering the task, which loses the original task identity and completion context.

## Goal

Let a user reverse the most recent completion or Today/Inbox move from the Task Overlay without leaving Qtile.

## Users

A Qtile task-overlay user who accidentally marks a task done or moves it to the wrong list.

## Requirements

### Must

1. The overlay provides one keyboard undo command in navigation mode, documented in its on-screen hint and consumer guide.
2. Undo reverses the latest undoable action from the current Qtile session when that action is either:
   - completing a task with `d` or a left click; or
   - moving a task with `m`.
3. Undoing a completion restores the same task to its pre-completion list and removes its completion timestamp/history entry.
4. Undoing a move restores the same task to its pre-move list.
5. Each successful undo persists the restored state and updates the overlay and Today counter through existing paths.
6. If no undoable action exists, the command is a safe no-op.
7. A newly performed completion or move replaces the previous undo opportunity; undo itself does not create redo support.

### Should

1. Expose brief feedback after a successful undo or unavailable undo without adding a notification service.
2. Preserve the current selection when the restored task is visible, or clamp safely when it is not.

### Won't

- Multi-step undo/redo history.
- Undo across a Qtile restart.
- Undo for added tasks, task-title edits, Todoist remote changes, or external JSON edits.
- Remote deletion/recreation semantics beyond the current sync model until separately specified.

## Non-functional Requirements

- No new runtime dependency, process, IPC service, or persisted history schema.
- Store behavior remains unit-testable without Qtile.
- Undo does not corrupt or duplicate tasks under the existing atomic JSON persistence model.

## Success Criteria

- Unit tests prove completion undo restores task/list/timestamp and move undo restores the original list.
- Unit tests prove empty undo is harmless and a later mutation replaces the available undo action.
- Live Qtile smoke test proves the undo command restores a completed task and a moved task, with the counter and overlay redrawn.
- Existing task-store and sync tests continue to pass.

## Open Questions

- What is the required Todoist behavior? Completion and moves are currently write-through. A local-only undo can be overwritten by the next sync; a cloud-consistent undo needs a researched compensating Todoist command.
- The proposal uses `u` as the navigation-mode command because it is unclaimed by the current overlay keymap.
