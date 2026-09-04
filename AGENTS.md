## Kosmic Integration

This project uses **Kosmic** for persistent memory and knowledge management.

### Configuration
- **Vault**: `./memnotes`
- **Target**: `qtile-pomodoro` (vault Project folder)
- **Project ID**: `qtile-pomodoro` (immutable)
- **Usage Skill**: `qtile-pomodoro-usage`
- **Development Skill**: `qtile-pomodoro-development`
- **Canonical Pair**: `./memnotes/Projects/qtile-pomodoro/skills/`

### Skills

The `kosmic` skill is the workflow orchestrator. Contributor work loads `qtile-pomodoro-development`, which requires `qtile-pomodoro-usage` for consumer and shared behavior. Consumers may invoke `qtile-pomodoro-usage` directly.

### Project Knowledge Format

`memnotes/Projects/qtile-pomodoro/notes/` is the authoritative Obsidian-compatible OKF v0.2 bundle. Use `index.md` for discovery. Concept notes require YAML frontmatter on line 1, a non-empty `type`, `status: draft | stable | deprecated`, and relative Markdown links.

### Required Workflow

Before implementation or architectural changes: load `qtile-pomodoro-development` and search the knowledge bundle. New features require Kosmic PRD, architecture, epic, and approved story gates before code changes.
