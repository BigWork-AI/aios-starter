# /upgrade — bring the engine up to date now

The engine keeps itself current: every time the brain opens it checks BigWork's shelf (at most
once a day) and installs a newer engine when there is no unsaved work, then says in one line what
changed. The weekly routine does the same for brains that are rarely opened. This command is the
manual version, for "do it now" or when the owner has set `upgrade: ask` in `aios.yml`.

1. Run `sh .aios/tools/upgrade.sh --check`. If it says the engine is current, say so and stop.
2. Read the owner the "what changed" lines in plain words.
3. Make sure there is no unsaved work (run `/save` if there is), then run
   `sh .aios/tools/upgrade.sh`. It replaces only BigWork's parts, runs migrations and checks,
   saves and pushes. If the checks fail it rolls back and nothing is saved: tell BigWork.
4. Report in one line: engine version now, and the one change most likely to matter to them.
