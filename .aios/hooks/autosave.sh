#!/bin/sh
# BigWork AI-OS autosave. Runs when a session ends (Claude Code SessionEnd hook) and on /save.
# Safe by design: if the checks find something private, nothing is saved and the reason is printed.
set -u
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 0
git rev-parse --git-dir >/dev/null 2>&1 || exit 0
branch=$(git branch --show-current 2>/dev/null || echo main)
if [ -z "$(git status --porcelain)" ] && [ "$branch" = main ]; then
  # nothing new locally; still push anything unpushed
  git remote get-url origin >/dev/null 2>&1 && git push -q origin main 2>/dev/null
  exit 0
fi
python3 .aios/tools/frontpage.py >/dev/null 2>&1 || true
git add -A
if ! python3 .aios/tools/check.py --staged; then
  echo "Not saved: the checks above found something that must not go in the brain. Fix it, then /save."
  git reset -q
  exit 0
fi
git -c user.name="${GIT_AUTHOR_NAME:-$(git config user.name || echo owner)}" \
    -c user.email="${GIT_AUTHOR_EMAIL:-$(git config user.email || echo owner@brain.local)}" \
    commit -q -m "Session save $(date +%Y-%m-%d\ %H:%M)" 2>/dev/null || true
if [ "$branch" != main ]; then
  # a cloud or phone session started on a side branch: fold it into main, one line of history
  git checkout -q main 2>/dev/null || git checkout -q -b main
  git remote get-url origin >/dev/null 2>&1 && git pull -q --ff-only origin main 2>/dev/null
  git merge -q --no-edit "$branch" 2>/dev/null || { echo "Could not fold branch '$branch' into main automatically. Run /save and read the message."; exit 0; }
  git branch -q -D "$branch" 2>/dev/null
  git remote get-url origin >/dev/null 2>&1 && git push -q origin --delete "$branch" 2>/dev/null
fi
if git remote get-url origin >/dev/null 2>&1; then
  git push -q origin main 2>/dev/null && echo "Saved and backed up to GitHub." || echo "Saved locally. Could not reach GitHub; it will push next time."
else
  echo "Saved locally (no GitHub copy connected yet)."
fi
