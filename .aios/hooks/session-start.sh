#!/bin/sh
# Runs when a session starts (Claude Code SessionStart hook).
# 1. Pull the latest saves from the other device.
# 2. Fold any side branch another device left behind (a phone or cloud session pushes to a side
#    branch, and cloud sessions cannot delete remote branches). Each fold goes through the same
#    checks as a save: if a branch holds something that must not go in the brain, it is left
#    alone and named, never merged.
# Quiet when there is nothing to do. Never touches a dirty tree or a session not on main.
set -u
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 0
git remote get-url origin >/dev/null 2>&1 || exit 0
[ "$(git branch --show-current 2>/dev/null)" = main ] || exit 0
[ -z "$(git status --porcelain)" ] || exit 0

git fetch -q --prune origin 2>/dev/null || { echo "Could not reach GitHub for the latest saves. Working with the local copy."; exit 0; }
git pull -q --ff-only origin main 2>/dev/null || echo "Could not pull the latest saves from GitHub. Working with the local copy."

folded=0
for ref in $(git for-each-ref --format='%(refname:short)' refs/remotes/origin | grep -v -e '^origin/main$' -e '^origin/HEAD$'); do
  branch=${ref#origin/}
  # already in main? then only the leftover branch needs removing
  if git merge-base --is-ancestor "$ref" main 2>/dev/null; then
    git push -q origin --delete "$branch" 2>/dev/null || true
    continue
  fi
  if ! git merge -q --no-ff --no-commit "$ref" 2>/dev/null; then
    git merge --abort 2>/dev/null || git reset -q --hard main
    echo "Could not fold the save from another device ('$branch') automatically: it changes the same lines as this copy. Run /save and read the message."
    continue
  fi
  if ! python3 .aios/tools/check.py --staged; then
    git merge --abort 2>/dev/null || git reset -q --hard main
    echo "Not folded: the save from another device ('$branch') holds something that must not go in the brain. Fix it on that device, then start again."
    continue
  fi
  git -c user.name="${GIT_AUTHOR_NAME:-$(git config user.name || echo owner)}" \
      -c user.email="${GIT_AUTHOR_EMAIL:-$(git config user.email || echo owner@brain.local)}" \
      commit -q -m "Fold save from another device ($branch)" 2>/dev/null || true
  git push -q origin --delete "$branch" 2>/dev/null || true
  folded=$((folded + 1))
done
if [ "$folded" -gt 0 ]; then
  git push -q origin main 2>/dev/null && echo "Brought in $folded save(s) from another device." || echo "Brought in $folded save(s) from another device. Could not push to GitHub yet; it will push at the next save."
fi
exit 0
