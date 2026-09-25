#!/bin/sh
# 0.3.0: the permissions page and the action log. Added only when missing; never overwrites the owner's.
[ -f company/permissions.md ] || cp .aios/templates/permissions.md company/permissions.md
[ -f memory/actions.md ] || cp .aios/templates/actions.md memory/actions.md
