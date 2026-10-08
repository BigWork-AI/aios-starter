# Keeping the engine current without the owner

Two layers, so a brain never goes stale:

1. **Every session start.** The session-start hook asks the updater at most once a day. With
   `upgrade: auto` in `aios.yml` it installs a newer signed engine when the tree is clean and says
   in one line what changed. With `upgrade: ask` it only says one is waiting. Quiet otherwise.
   This covers anyone who opens their brain at least weekly.
2. **The scheduled routine.** The meeting-sweep routine (see `meeting-sweep.md`) ends by running
   `sh .aios/tools/upgrade.sh --auto`. This covers brains that sit unopened. Add that line to the
   routine prompt when you create it.

The updater itself honours the owner's setting, whoever calls it: `--auto` installs only when
`aios.yml` says `upgrade: auto`, and treats a missing or garbled setting as `ask`. So an ask-mode
brain is never upgraded by the hook, the routine or anything else; only `/upgrade`, after the
owner's yes, installs. Every install is verified first (BigWork's signature, the release digest, a
newer version) and rolled back whole if anything fails.

Both layers write `memory/receipts/upgrade-check.json`. The Friday review reads it and says plainly
if the engine has not been checked in a week, if a newer one is waiting, or if an upgrade was
deferred or rolled back.

A brain never pushes to BigWork's public kit: the hooks and the updater refuse when the brain's
`origin` is the kit's home (`.aios/tools/kit_home.sh`).
