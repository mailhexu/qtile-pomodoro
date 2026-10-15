# Manual Breaks and Timer Control Panel Specs

- [PRD](prd.md) — approved; manual breaks preserve focus progress, control panel includes saved settings.
- [Architecture](architecture.md) — approved.
- [Settings persistence research](research/2026-10-15-toml-settings.md) — primary-source findings; implementation-specific tests remain pending.
- [Epic 001](epics/epic-001.md) — approved.

## Implementation stories — draft approval bundle

- [001: Manual-break state, accounting and recovery](stories/story-001.md).
- [002: Durable timer-settings persistence](stories/story-002.md) — after 001.
- [003: Asynchronous client and Qtile controller](stories/story-003.md) — after 001/002.
- [004: Native control panel and delivery](stories/story-004.md) — after 001/002/003.
