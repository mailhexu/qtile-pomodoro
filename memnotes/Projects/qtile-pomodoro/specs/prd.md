---
status: approved
created: 2026-09-04
updated: 2026-09-04
linked_research: []
linked_epics: []
---

# Minimal Qtile Task Overlay

## Problem Statement

The Qtile session has no fast, low-distraction way to capture and review work items. Opening a full task application breaks focus; keeping tasks only in memory loses incoming work. The user needs a Todoist-like split between an Inbox and Today that appears on demand inside Qtile and exposes a compact count in the bar.

## Goals

- Provide a Qtile-native overlay that is summoned by a Qtile button/keybinding and dismissed without opening a separate application.
- Let the user add a task directly to Inbox or Today with minimal interaction.
- Let the user view, complete, and move tasks between Inbox and Today from the overlay.
- Show a compact count of incomplete Today tasks in the Qtile bar.
- Keep task behavior entirely inside Qtile integration: no daemon, network account, or external task service.

## Non-Goals

- Todoist account synchronization, collaboration, sharing, or a web/mobile client.
- Recurrence, labels, projects beyond Inbox/Today, attachments, reminders, or natural-language date parsing.
- Replacing the persistent Pomodoro Timer Service or coupling task state to a Pomodoro cycle.
- Wayland support in this release; the task overlay follows the project’s X11 Qtile scope.

## Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-001 | A Qtile keybinding or bar button opens and closes a single minimalist task overlay. | must |
| FR-002 | The overlay presents separate Inbox and Today task lists with incomplete counts. | must |
| FR-003 | The user can create a task and explicitly choose Inbox or Today as its destination. | must |
| FR-004 | The user can mark an Inbox or Today task complete from the overlay. | must |
| FR-005 | The user can move an incomplete task between Inbox and Today. | must |
| FR-006 | The Qtile bar displays the current incomplete Today count and opening the overlay does not require the Pomodoro service. | must |
| FR-007 | Task state survives a Qtile restart and is local to the user. | must |
| FR-008 | Opening, adding, moving, completing, and closing the overlay are usable entirely with the keyboard. | should |
| FR-009 | The overlay supports mouse interaction for visible actions. | should |

## Non-Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-001 | No background daemon, network dependency, account, or non-standard Python runtime dependency is introduced. | must |
| NFR-002 | The Today count refreshes in the Qtile bar within one widget polling interval after a task mutation. | must |
| NFR-003 | The task overlay does not block normal Qtile operation when closed. | must |
| NFR-004 | The feature operates with the deployed Qtile 0.37 X11 environment. | must |

## Success Criteria

- [ ] A user can open the overlay, add one Inbox task and one Today task, then see the Today bar count increment without restarting Qtile.
- [ ] A user can keyboard-complete and move tasks; completed tasks no longer contribute to the Today count.
- [ ] Restarting Qtile preserves incomplete Inbox and Today tasks.
- [ ] The task feature works when the Pomodoro Timer Service is unavailable.
- [ ] No task-related background process remains after Qtile exits.

## Open Questions

- [ ] What exact Qtile keybinding and/or bar click should invoke the task overlay without colliding with existing bindings?
- [ ] Should completed tasks be retained as local history, hidden but recoverable, or deleted immediately?
- [ ] What local persistence representation best fits a Qtile-only function: a small JSON document, SQLite through Qtile’s process, or another standard-library format?
- [ ] Should Inbox and Today remain the only lists in the initial release, or is an explicit archive view needed to recover completed tasks?
