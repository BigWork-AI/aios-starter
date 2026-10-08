#!/bin/sh
# 0.3.10: a brain that took the unreleased 2026-10-07 engine may hold a /live command adapter whose
# playbook is not in this engine. Remove the adapter when its playbook is absent; nothing else changes.
[ -f .claude/commands/live.md ] && [ ! -f .aios/playbooks/live.md ] && rm -f .claude/commands/live.md
exit 0
