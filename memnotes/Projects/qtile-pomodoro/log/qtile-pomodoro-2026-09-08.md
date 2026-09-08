# 2026-09-08 — Todoist client sync (Epic 2)

- PRD approved (cache+sync, token auth, due-date/Inbox mapping, full R/W).
- Architecture: 3 review rounds. R1: 9 findings (migration data loss, dead-id
  remap, threading). R2 caught REST v2/Sync v9 sunset (2026-02-10) — retargeted
  Unified API v1 (POST /api/v1/sync, Command UUID idempotency, temp_id
  mapping, user.inbox_project_id; no completed-items endpoint -> Done = local
  log, ADR-007). R3: two v3 defects (incremental/full-sync contradiction,
  v9 date_string) fixed -> approved.
- Story 4: TodoistClient + 7 stubbed-transport tests (da291b8). Live probe
  BLOCKED on user token.
- Story 5: SyncEngine + additive migration; 10 tests incl. pre-migration
  task survival, temp-id rewrite, inbox survivors (9c7fd0d).
- Story 6: wiring (refresh-on-open, r key, ↻N/! indicator, token config)
  (cedefbb); review R1 FAIL — 5 findings (cmd/type wire shape, drain queue
  wipe, unreachable r, inbox→today merge, no autokick) fixed (4271f2a);
  R2 PASS + 3 non-blocking hardenings (worker-exit race, done callbacks,
  keysym guard) (065ee7e); restored _id_map/TaskStore clobbered in an edit
  (7f6d745). 40/40 tests; deployed; no-token mode screenshot-verified.
- Pending: live probe + live smoke — blocked on user's Todoist API token.
