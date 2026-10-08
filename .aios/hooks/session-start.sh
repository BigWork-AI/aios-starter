#!/bin/sh
# Runs when a session starts (Claude Code SessionStart hook).
# 1. Pull the latest saves from the other device.
# 2. Fold any side branch another device left behind (a phone or cloud session pushes to a side
#    branch, and cloud sessions cannot delete remote branches). Each fold goes through the same
#    checks as a save: if a branch holds something that must not go in the brain, it is left
#    alone and named, never merged.
# 3. Keep the engine current: at most once a day, ask the updater. With "upgrade: auto" it installs
#    a newer signed engine when the tree is clean; with "upgrade: ask" (or no setting) it only says
#    one is available. The updater itself decides; this hook never installs anything.
# Quiet when there is nothing to do. Never touches a dirty tree or a session not on main, and never
# pushes to BigWork's public kit (see .aios/tools/kit_home.sh).
set -u
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 0
. .aios/tools/kit_home.sh 2>/dev/null || { aios_kit_home() { return 1; }; aios_push() { git push "$@"; }; }
yml_value() { sed -n "s/^$1:[[:space:]]*//p" aios.yml 2>/dev/null | head -1 | sed 's/#.*//; s/["'"'"' 	]//g' | tr -d '\r' | tr '[:upper:]' '[:lower:]'; }

sync_from_other_devices() {
git remote get-url origin >/dev/null 2>&1 || return 0
if aios_kit_home; then
  echo "This folder's GitHub copy is BigWork's public kit, not your brain. Not syncing with it. Tell BigWork."
  return 0
fi
[ "$(git branch --show-current 2>/dev/null)" = main ] || return 0
[ -z "$(git status --porcelain)" ] || return 0

git fetch -q --prune origin 2>/dev/null || { echo "Could not reach GitHub for the latest saves. Working with the local copy."; return 0; }
git pull -q --ff-only origin main 2>/dev/null || echo "Could not pull the latest saves from GitHub. Working with the local copy."

folded=0
for ref in $(git for-each-ref --format='%(refname:short)' refs/remotes/origin | grep -v -e '^origin/main$' -e '^origin/HEAD$'); do
  branch=${ref#origin/}
  # already in main? then only the leftover branch needs removing
  if git merge-base --is-ancestor "$ref" main 2>/dev/null; then
    aios_push -q origin --delete "$branch" 2>/dev/null || true
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
  aios_push -q origin --delete "$branch" 2>/dev/null || true
  folded=$((folded + 1))
done
if [ "$folded" -gt 0 ]; then
  aios_push -q origin main 2>/dev/null && echo "Brought in $folded save(s) from another device." || echo "Brought in $folded save(s) from another device. Could not push to GitHub yet; it will push at the next save."
fi
}

keep_engine_current() {
  [ -f .aios/tools/upgrade.sh ] || return 0
  [ "$(git branch --show-current 2>/dev/null)" = main ] || return 0
  if [ "$(yml_value verify)" = none ]; then
    echo "This brain installs unsigned engines (verify: none in aios.yml). That is for BigWork's own testing only; if you did not choose it, tell BigWork."
  fi
  stamp=memory/receipts/upgrade-check.json
  if [ -f "$stamp" ] && [ -n "$(find "$stamp" -mmin -1440 2>/dev/null)" ]; then return 0; fi
  # The updater says what matters and nothing else: silent when current or offline, one line when a
  # newer engine waits for the owner, the change list when it installed one, a warning when something
  # on the shelf did not check out.
  log=$(sh .aios/tools/upgrade.sh --auto 2>/dev/null || true)
  [ -z "$log" ] || printf '%s\n' "$log"
}

sync_from_other_devices
keep_engine_current
exit 0
