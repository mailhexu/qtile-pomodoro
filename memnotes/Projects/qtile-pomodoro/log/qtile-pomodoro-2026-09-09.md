# 2026-09-09 — Task Overlay Layout and Undo

- Implemented [Wrapped Task Text](../specs/quick-tasks/2026-09-09-wrapped-task-text.md): Pango left alignment, two-line pixel-bounded titles, and height-aware selection/click geometry. Unit suite passed; the deployed Qtile overlay screenshot confirmed flush-left wrapping and intact Done rows. Review approved.
- Round-1 two-axis review found and resolved STD-001 (restore the Quick Task template) and SPEC-001 (measure Pango width rather than characters); Round 2 approved d10f86c with no regressions.
- Drafted [Undo Task Completion and Move PRD](../specs/prd-task-undo.md); it awaits the required product approval before architecture or implementation.
- PRD approved with local-only undo semantics; drafted [Local Task Undo architecture](../specs/architecture-task-undo.md), awaiting the required architecture approval.
- Local Task Undo architecture approved; preparing the single Epic for approval.
- Drafted [Epic 3: Local Task Undo](../specs/epics/epic-3-local-task-undo.md), awaiting the required epic approval.
- Epic 3 approved; drafted [Story 7: One-step local task undo](../specs/stories/story-7-local-task-undo.md), awaiting story approval.
- Story 7 approved and implemented (TDD): store UndoAction/undo(), model u key with unified click/d completion, hint feedback, selection preservation, sync-off guard. 60/60 tests; live Qtile smoke d/u and m/u net-zero with sync restored.
- Story 7 round-1 review: 13 findings (STD-001..008, SPEC-001..005) all resolved; round 2 verification pending.
