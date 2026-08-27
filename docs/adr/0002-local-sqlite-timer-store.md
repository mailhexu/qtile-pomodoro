# Local SQLite timer store

Runtime State and indefinitely retained Session History are stored in a local SQLite database. SQLite is available through Python's standard library, provides atomic updates for timer recovery, and supports daily and weekly reports without an external service or full-file rewrites.

## Considered Options

- One rewritten JSON document.
- An append-only JSON Lines log.
