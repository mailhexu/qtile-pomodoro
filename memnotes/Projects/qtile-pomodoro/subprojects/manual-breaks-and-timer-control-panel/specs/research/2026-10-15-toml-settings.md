---
project_id: qtile-pomodoro
subproject_id: manual-breaks-and-timer-control-panel
record_kind: research
local_id: 2026-10-15-toml-settings
status: draft
type: Research Memo
title: Style-preserving TOML settings updates
created: 2026-10-15
updated: 2026-10-15
linked_prd: ../prd.md
governing_record: qtile-pomodoro/manual-breaks-and-timer-control-panel/architecture/architecture
---

# Research: Style-preserving TOML settings updates

## Question and Scope

Can an existing non-GUI library safely preserve unrelated TOML while the control
panel updates its four timer settings? This bounded documentary research supports
[PRD](../prd.md) FR-010–013 and the draft [Architecture](../architecture.md).
It does not authorize dependency installation, probes or implementation.

## Primary Sources and Findings

- [TOMLKit overview](https://tomlkit.readthedocs.io/en/latest/) states TOML 1.0.0
  compliance and preservation of comments, indentation, whitespace and ordering.
- [Official quickstart: parsing](https://tomlkit.readthedocs.io/en/latest/quickstart/#parsing)
  demonstrates a dictionary-like TOMLDocument and an unchanged sample round trip
  with `dumps`. Its [modifying example](https://tomlkit.readthedocs.io/en/latest/quickstart/#modifying)
  retains an inline comment while editing nested data.
- [Official public interface](https://tomlkit.readthedocs.io/en/latest/api/)
  documents `parse`/`loads`, string-returning `dumps` and stream-writing `dump`.
  These support targeted document edits; they do not implement application-level
  atomic replacement, permissions or daemon-application semantics.
- [Python tomllib documentation](https://docs.python.org/3/library/tomllib.html)
  explicitly says it does not write TOML and recommends TOMLKit when editing
  existing files. The deployed package targets Python 3.11+; do not assume
  newer Python/TOML-language extensions are supported by the selected writer.

These are documented capabilities, not locally executed application-specific
preservation results. No library was installed and no runtime probe was run.

## Options and Recommendation

Recommend TOMLKit as one new non-GUI runtime dependency, subject to architecture
approval and an implementation-time version compatible with Python 3.11+.
A document model avoids introducing a partial TOML source editor in the project.

Stdlib `tomllib` can validate values but has no lossless editable syntax model.
A line/stanza rewriter must either restrict accepted TOML syntax or recognize
quoted/dotted keys, inline tables and multiline strings containing apparent
headers. Refusing arbitrary valid layouts would frustrate the settings feature;
naively matching headers risks corrupting unrelated configuration. This is an
engineering inference, not a measured performance comparison.

For each Save, read the current document afresh and edit only
`timer.focus_minutes`, `timer.short_break_minutes`, `timer.long_break_minutes`,
and `timer.long_break_after`. Validate strict positive integers, rejecting bool.
The application owns same-directory temporary output, replacement/permission
policy, and the distinct saved/applied/unknown outcomes. Do not expose the rest
of the document to the control panel.

## Required Implementation Evidence

- Preserve the actual `tasks.todoist_api_token` key and unrelated nested values;
  never print credentials or include them in service snapshots.
- Cover absent config, comments, whitespace/order, quoted/dotted keys, inline
  tables, multiline strings, and valid existing non-timer sections.
- Invalid input or invalid TOML leaves the original file unchanged; replacement
  failure preserves it. Preserve existing permissions and use owner-only mode
  for newly created credential-capable files.
- Changes apply to future phases while running, paused and held focus retain
  remaining time/original duration. File save and in-memory application are not
  one global transaction; exercise the documented partial/unknown outcomes.

## Remaining Decision

Approve the dependency at the architecture gate. Select and lock a compatible
version during the approved implementation story, then run the application-level
preservation tests before claiming these cases work in qtile-pomodoro.
