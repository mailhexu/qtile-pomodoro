# Pomodoro Timer

A Qtile-specific local Linux timer service for focused work and recovery breaks.

## Language

**Timer Service**:
The long-lived local owner of timer state, completion notifications, break-overlay coordination, and session records.
_Avoid_: Background app, widget timer

**Qtile Widget**:
A Qtile bar integration that presents and controls the Timer Service without owning its state.
_Avoid_: Timer service, pomodoro app

**Focus Session**:
One configured interval of intentional work in a cycle.
_Avoid_: Task, pomodoro

**Completed Focus Session**:
A Focus Session whose timer reaches zero; it is the sole kind of session counted in productivity statistics.
_Avoid_: Started pomodoro, partial pomodoro

**Break**:
A recovery interval following a Focus Session, classified as a Short Break or Long Break.
_Avoid_: Rest session

**Cycle**:
The ordered sequence of Focus Sessions and Breaks, including a Long Break after a configured number of Completed Focus Sessions.


**Configuration**:
The durable, declarative settings that establish timer defaults and integration behavior.
_Avoid_: Runtime state

**Runtime State**:
The current phase and its countdown, controlled interactively without rewriting Configuration.
_Avoid_: Settings, configuration

**Productivity Statistics**:
Aggregates derived from Completed Focus Sessions over time.
_Avoid_: Activity tracking

**Break Overlay**:
A full-screen timer surface shown when a Focus Session transitions to a Break; while active, it offers only the control to skip that Break.
_Avoid_: Lock screen, break popup

**Resume Gate**:
The explicit action required to begin a Focus Session after a Break reaches zero, available through a button and the Space key.
_Avoid_: Automatic resume

**Elapsed Time**:
Real wall-clock time consumed by an active phase, including time while the machine is suspended.
_Avoid_: Active uptime

**Configuration Reload**:
An explicit command that re-reads Configuration without rewriting it.
_Avoid_: Automatic configuration watch

**Session History**:
The indefinitely retained, local-only dated record of Completed Focus Sessions used to produce daily and weekly Productivity Statistics.
_Avoid_: Cloud activity log

**Paused Phase**:
A Focus Session or Break whose countdown is explicitly frozen with its remaining duration preserved.

**Aborted Focus Session**:
A Focus Session ended by reset before it reaches zero; it is excluded from Completed Focus Sessions and Productivity Statistics.

**Restored Phase**:
The persisted active phase resumed after a Timer Service restart or machine reboot with Elapsed Time deducted.

**Statistics Report**:
A CLI text view of daily and weekly Productivity Statistics and Session History.

**Completion Notification**:
A desktop notification emitted when a Focus Session ends and when a Break reaches the Resume Gate.

**Break Reset**:
The action that ends an active Break and transitions it to the Resume Gate without beginning a Focus Session.

**Qtile Session Startup**:
The once-per-Qtile-session action that starts the Timer Service without duplicating it on configuration reload.

**Timer Store**:
The local store containing Runtime State and indefinitely retained Session History.
_Avoid_: Cloud database, JSON log


**Overlay Set**:
The collection of Break Overlays displayed on every physical screen during an active Break.

**Recovery Completion**:
The first phase completion recognized after the Timer Service recovers; it presents the normal next UI, begins that next phase at recovery time, and never silently advances through further phases.

**Configured Interval**:
A positive whole-minute Configuration value for a Focus Session, Short Break, or Long Break.

**Timer Status**:
The Qtile bar display of the current phase, its remaining countdown, and progress toward the next Long Break; when inactive, it presents an explicit state label.

**Statistics Calendar**:
The machine-local calendar that groups Productivity Statistics into local dates and ISO Monday–Sunday weeks.

**Idle State**:
The non-counting state reached when an active Focus Session is reset; it is ready to begin a fresh Focus Session while retaining Cycle progress.

**Control Commands**:
The CLI-backed actions exposed through Qtile keybindings to start, pause, reset, reload, and report on the Timer Service.
