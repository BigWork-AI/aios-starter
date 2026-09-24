# Keeping the engine current without the owner

Two layers, so a brain never goes stale:

1. **Every session start.** The session-start hook checks BigWork's shelf at most once a day and
   installs a newer engine when the tree is clean. Quiet unless something changed. This covers
   anyone who opens their brain at least weekly.
2. **The scheduled routine.** The meeting-sweep routine (see `meeting-sweep.md`) ends by running
   `sh .aios/tools/upgrade.sh --auto`. This covers brains that sit unopened. Add that line to the
   routine prompt when you create it.

Both write `memory/receipts/upgrade-check.json`. The Friday review reads it and says plainly if
the engine has not been checked in a week, or if an upgrade was deferred or rolled back.

The owner can set `upgrade: ask` in `aios.yml` to be asked before any engine change; then only
`/upgrade` installs.
