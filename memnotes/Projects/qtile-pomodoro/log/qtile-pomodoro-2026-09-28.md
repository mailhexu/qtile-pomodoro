# 2026-09-28 session

- Bug report: focus finished at 0:00 without break overlay (13:46). Forensics:
  machine resumed from suspend 13:46:12; daemon transitioned correctly
  (session row 13:46:33, break ran, next focus only started manually 14:56).
  Widget status call had timeout=0.5s; post-resume subprocess stalls exceed it.
  Fix: timeout 0.5s -> 2.0s (qtile.py _status). Deployed both envs.
- Second report: break overlay "only on one workspace". Disproven live twice
  (eval-forced and during the real 15:47 break): internal popup windows are
  group-independent; screenshots on groups 2 and 3 both fully covered.
- Live verification: 15:47:48 transition focus->short_break correct end-to-end
  (daemon state, bar text, overlay mapped). Side effect of live debugging:
  user's in-flight focus was reset at 15:12 (counter ticked to 178).
