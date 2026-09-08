---
status: approved
created: 2026-09-08
updated: 2026-09-08
---

# Epic 2: Todoist Client Sync

Parent: [Architecture: Todoist Client Sync](../architecture-todoist-sync.md) (approved 2026-09-08)

## Narrative

The task overlay becomes a real Todoist client: Todoist is authoritative,
the local JSON file is the cache, and overlay actions write through via
Unified API v1 (`POST /api/v1/sync`) with an offline replay queue.

## Success Criteria

- Tasks added/scheduled in Todoist appear in the overlay on open or `r`.
- Overlay `d`/add/`m` are reflected in Todoist within seconds.
- Offline: overlay still works; queued ops replay on reconnect; offline
  create→complete replays correctly (temp-id remap).
- No token configured: behavior byte-identical to Epic 1 (all 20 existing
  tests pass unmodified).
- Pre-migration tasks.json loads with all tasks intact.

## Scope

- Stories: 3 (0/3 done)
- Out of scope: Wayland, other Todoist projects, labels/filters,
  background sync daemon.
