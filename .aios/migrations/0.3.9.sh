#!/bin/sh
# 0.3.9: live review pages are rebuilt from the files each time, so the brain does not keep them.
# Adds one ignore line to the owner's .gitignore if it is not there yet. Nothing else changes.
f=.gitignore
line='memory/reviews/live-*.html'
[ -f "$f" ] || touch "$f"
grep -qxF -- "$line" "$f" && exit 0
printf '\n# Live review pages are rebuilt from the files each time\n%s\n' "$line" >> "$f"
