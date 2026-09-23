# /save — save now, by hand

Saving is automatic: when a session ends, the brain runs its checks, saves, folds any side branch
into main and pushes to GitHub. This command does the same thing on demand, for when the owner
wants to be sure, or when a window was closed hard and the automatic save did not get to run.

1. Run `sh .aios/hooks/autosave.sh` and show its last line to the owner.
2. If it says "Not saved", read the check output, remove the private item it names, and run it
   again. Never override the check.
3. If it says it could not reach GitHub, say so plainly; the next save will push.
4. Report in one line: saved and backed up, saved locally only, or not saved and why.
