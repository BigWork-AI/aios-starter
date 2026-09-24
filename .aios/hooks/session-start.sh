#!/bin/sh
# Runs when a session starts (Claude Code SessionStart hook).
# 1. Pull the latest saves from the other device.
# 2. Fold any side branch another device left behind (a phone or cloud session pushes to a side
#    branch, and cloud sessions cannot delete remote branches). Each fold goes through the same
#    checks as a save: if a branch holds something that must not go in the brain, it is left
#    alone and named, never merged.
# 3. Keep the engine current: at most once a day, check BigWork's shelf and install a newer engine
#    when the tree is clean (set "upgrade: ask" in aios.yml to be asked instead).
# Quiet when there is nothing to do. Never touches a dirty tree or a session not on main.
set -u
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 0
sync_from_other_devices() {
git remote get-url origin >/dev/null 2>&1 || return 0
[ "$(git branch --show-current 2>/dev/null)" = main ] || return 0
[ -z "$(git status --porcelain)" ] || return 0

git fetch -q --prune origin 2>/dev/null || { echo "Could not reach GitHub for the latest saves. Working with the local copy."; return 0; }
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
}

keep_engine_current() {
  [ -f .aios/tools/upgrade.sh ] || return 0
  [ "$(git branch --show-current 2>/dev/null)" = main ] || return 0
  mode=$(sed -n 's/^upgrade: *//p' aios.yml 2>/dev/null | head -1)
  [ "$mode" = ask ] && return 0
  stamp=memory/receipts/upgrade-check.json
  if [ -f "$stamp" ] && [ -n "$(find "$stamp" -mmin -1440 2>/dev/null)" ]; then return 0; fi
  before=$(cat .aios/VERSION 2>/dev/null)
  log=$(mktemp)
  sh .aios/tools/upgrade.sh --auto >"$log" 2>&1 || true
  after=$(cat .aios/VERSION 2>/dev/null)
  if [ "$before" != "$after" ]; then
    echo "Engine updated to $after. What changed:"
    awk -v v="$after" '$0 ~ "^## "v {f=1; next} /^## / {f=0} f' .aios/CHANGELOG.md 2>/dev/null | sed 's/^/  /'
  elif grep -q "Rolling back" "$log" 2>/dev/null; then
    echo "A newer engine was found but its checks failed, so it was not installed. Tell BigWork."
  fi
  rm -f "$log"
}

sync_from_other_devices
keep_engine_current
exit 0
