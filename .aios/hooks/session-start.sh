#!/bin/sh
# Pull the latest saves from the other device before work starts. Quiet when there is nothing.
set -u
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 0
git remote get-url origin >/dev/null 2>&1 || exit 0
[ "$(git branch --show-current 2>/dev/null)" = main ] || exit 0
[ -z "$(git status --porcelain)" ] || exit 0
git pull -q --ff-only origin main 2>/dev/null || echo "Could not pull the latest saves from GitHub. Working with the local copy."
exit 0
