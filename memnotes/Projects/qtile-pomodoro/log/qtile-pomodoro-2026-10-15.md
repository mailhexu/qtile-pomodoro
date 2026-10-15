# 2026-10-15: Manual breaks and timer control panel planning

Governing draft: [Manual Breaks and Timer Control Panel PRD](../subprojects/manual-breaks-and-timer-control-panel/specs/prd.md).
Qualified identity: `qtile-pomodoro/manual-breaks-and-timer-control-panel/prd/prd`.

- Request: manually start a break and provide a control panel.
- User decision: preserve unfinished focus time during a manual break; wait for
  explicit resume after natural break completion rather than restarting work.
- User decision: panel includes controls and saved timer settings.
- Draft scope: bar-click Qtile popup; live timer state; Start/Resume, Pause,
  Reset, short/long manual break, Skip Break; persistent editing of configured
  focus/short-break/long-break minutes and long-break interval.
- Manual breaks do not count as completed focus or reset the cycle. Held focus
  survives daemon replacement; settings affect future phases, not the active
  countdown or held focus. Preserve unrelated TOML settings, including Todoist.
- `spec-create --kind prd` reserved and published immutable subproject
  `manual-breaks-and-timer-control-panel`, operation
  `d158540a52544a5c97a591b64b6b7ba4`.
- PRD populated and linked from owner-local/project specs indexes. It remains
  draft pending user approval; no architecture/story approval or implementation
  is inferred from these product choices.
- Spec-event `generate-status` was attempted with the qualified draft record;
  it refused `STATUS_ROOT_UNBOUND`. No working-directory binding or dashboard
  was silently created or claimed updated.
- Read-only checks confirmed existing timer/accounting/overlay contracts and
  required procedure-skill availability. This is planning-only: no source,
  runtime timer state, settings, or user tasks were changed; no behavioral test
  or live timer operation was needed for this draft.
