# 2026-10-12: Focus expiry and workspace break overlay repair

Governing record: [Break Overlay Failure Diagnostics](../specs/quick-tasks/2026-09-09-break-overlay-diagnostics.md).

## Captured failures

- Qtile bar: `Focus 00:00 · 229/4`; its timer was still scheduled approximately
  one second ahead of the live monotonic clock. Polling was not frozen.
- Sole socket owner: PID 1236703, started 2026-09-28 15:12:33, before the
  corrected `Timer.status()` code was installed. It returned `focus/running`,
  remaining 0, deadline 1791456131.2452602, overlay false despite being overdue.
  The historical code clamps remaining to zero without advancing phase.
- Its independent ticker had stopped advancing persisted state. The initiating
  ticker failure is not captured; no suspend or timeout cause is asserted.
- Reused X11 popup 8388863: root-stack index 10; application windows on occupied
  groups 1/2/4/9 at indexes 13/16/23/30. The popup was below those applications.
- Qtile 0.37 `Popup.place(above=True)` calls `change_layer()`, which returns early
  for group-less Internal windows. Mapped/focused alone does not mean visible.
- Previous timeout-root-cause and workspace-disproof claims were unsupported.

## Repair

- Explicit X11 `StackMode.Above` after mapping, and active-only `setgroup`
  restacking/focus after workspace clients have been mapped.
- Widget finalization unsubscribes the hook and destroys popup/layout resources.
  Temporary per-poll debug inspection was removed.
- Replaced only the confirmed socket-owning stale daemon, suppressing widget
  self-heal during handoff. Installed into Qtile's Python and restarted Qtile.
  No reset/start commands, config edits, task-data edits, or history rewrites.
- User approved bounded Kosmic metadata migration: normalized the existing
  active Quick Task; migrated Project knowledge metadata/projections to the
  installed tooling. Unrelated flat feature specifications remain in place.

## Verification

- Full suite in Python 3.12 with actual Qtile dependencies and isolated pytest:
  `env PYTHONPATH=src:/home/hexu/.local/share/uv/tools/qtile/lib/python3.12/site-packages uv run --no-project --python /home/hexu/.local/share/uv/tools/qtile/bin/python --with pytest python -m pytest tests/ -q`
  — **70 passed**, including expiry without ticker, exactly-once history,
  persisted recovery, non-expired deadline preservation, reused-popup stacking,
  occupied-workspace switches, inactive hook and finalization boundaries.
- Live stale-daemon replacement recovered to `short_break/running/300s`,
  overlay true, counter 229 -> 230, history rows 230 -> 231: exactly one recovered
  focus and one fresh break, no catch-up phases.
- Live state subsequently showed a new focus. A second live replacement preserved
  deadline **1791792364.3931727**, counter **230**, and history **231** exactly.
  First immediate readiness request saw connection refused; the next request
  succeeded with the unchanged focus deadline.
- Independent temporary overlay controller on actual X11 switched occupied
  groups **1, 2, 4, 9**: viewable, focused, and above every application on each.
  This avoided the prior fake-state/real-poll race and did not mutate timer state.
- Screenshot captured after returning control to Qtile's event loop showed a
  full-screen dark **BREAK / 02:03** surface and **Click here to skip break**.
  Capturing synchronously inside a blocked Qtile IPC callback initially caught
  the pre-presentation desktop; that was not treated as passing visual evidence.
- Temporary controllers and runtime verification attributes were disposed of;
  no screenshot or throwaway script files were retained. Original workspace and
  application focus were restored.

## Tooling limits

- `spec-create` required legacy feature-spec migration; resuming the old Quick
  Task initially failed because identity metadata was absent. Normalizing the
  approved existing Quick Task allowed `work start` without moving other specs.
- Managed `scratch begin` fails for this nested vault Project with a path
  `relative_to()` error; reported through automated QA. Verification used
  in-memory scripts/images and isolated pytest fixtures instead.

## Review

Standards round 1 requested one documentation fix: STD-001, upgrade checks
must invoke the installed Qtile interpreter rather than an unreliable wrapper.
That fix was applied. Independent Standards and Spec reviewers both approved
the focused round-2 revision; no unresolved blocking findings remain.
The receipt's review artifact pins source revision
`66b4d1db8930107eeb359d2d28ee60bd8261a7d2697589bd369ed482e63fedbc`.
