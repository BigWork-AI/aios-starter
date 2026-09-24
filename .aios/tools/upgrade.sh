#!/bin/sh
# BigWork AI-OS engine upgrade. Runs from the brain's root.
#
#   sh .aios/tools/upgrade.sh            fetch the newest engine from BigWork's public shelf and install it
#   sh .aios/tools/upgrade.sh --check    only say whether a newer engine exists
#   sh .aios/tools/upgrade.sh --auto     used by the session-start hook and the weekly routine: quiet when
#                                        current or offline, installs a newer engine when the tree is clean
#
# What it replaces: the .aios folder, the generated command adapters that came from the kit, the
# hook settings, and the fenced engine block inside AGENTS.md. What it never touches: company/,
# clients/, memory/, skills/, inbox/, the owner's own commands, or anything outside that block.
# Source: AIOS_SOURCE (local copy) > AIOS_KIT_URL (tarball) > github.com/${AIOS_REPO:-BigWork-AI/aios-starter}
set -eu
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
[ -f .aios/VERSION ] || { echo "This folder is not a BigWork AI-OS brain (no .aios/VERSION)."; exit 1; }
CURRENT=$(cat .aios/VERSION)
MODE="${1:-apply}"
RECEIPT=memory/receipts/upgrade-check.json
receipt() { mkdir -p memory/receipts; printf '{"checked_at":"%s","installed":"%s","available":"%s","result":"%s"}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$CURRENT" "$1" "$2" > "$RECEIPT"; }

fetch_kit() {
  TMP=$(mktemp -d)
  if [ -n "${AIOS_SOURCE:-}" ]; then
    mkdir -p "$TMP/kit/src" && cp -R "$AIOS_SOURCE"/. "$TMP/kit/src"/
  else
    KIT_URL="${AIOS_KIT_URL:-https://github.com/${AIOS_REPO:-BigWork-AI/aios-starter}/archive/refs/heads/main.tar.gz}"
    if ! curl -fsSL --max-time 12 "$KIT_URL" -o "$TMP/kit.tar.gz"; then
      rm -rf "$TMP"; receipt "unknown" "offline"
      [ "$MODE" = "--auto" ] && exit 0
      echo "Could not reach BigWork's shelf ($KIT_URL). Try again later; nothing was changed."; exit 1
    fi
    mkdir -p "$TMP/kit" && tar -xzf "$TMP/kit.tar.gz" -C "$TMP/kit"
  fi
  SRC=$(find "$TMP/kit" -maxdepth 3 -name .aios -type d | head -1)
  [ -n "$SRC" ] || { echo "The downloaded kit is not a BigWork AI-OS engine."; rm -rf "$TMP"; exit 1; }
  SRC=$(dirname "$SRC")
}

fetch_kit
NEW=$(cat "$SRC/.aios/VERSION")
if [ "$NEW" = "$CURRENT" ]; then
  receipt "$NEW" "current"; rm -rf "$TMP"
  [ "$MODE" = "--auto" ] || echo "Engine $CURRENT is current. Nothing to do."; exit 0
fi
if [ "$MODE" = "--check" ]; then
  echo "Engine $NEW is available (you have $CURRENT). What changed:"
  awk -v v="$NEW" '$0 ~ "^## "v {f=1; next} /^## / {f=0} f' "$SRC/.aios/CHANGELOG.md" 2>/dev/null | sed 's/^/  /'
  echo "Type /upgrade to install it."
  rm -rf "$TMP"; exit 0
fi

# Refuse to upgrade over unsaved work: the owner's files must be safe first.
if [ -n "$(git status --porcelain)" ]; then
  receipt "$NEW" "deferred-unsaved-work"; rm -rf "$TMP"
  [ "$MODE" = "--auto" ] && exit 0
  echo "There is unsaved work. Run /save first, then /upgrade."; exit 1
fi

echo "Upgrading engine $CURRENT -> $NEW"
COMPANY=$(sed -n 's/^company: *"\{0,1\}\([^"]*\)"\{0,1\}$/\1/p' aios.yml | head -1)
PRIVATE=$(sed -n 's/^private_folder: *//p' aios.yml | head -1)

# 1. Engine folder, replaced whole.
rm -rf .aios && cp -R "$SRC/.aios" .aios
chmod +x .aios/hooks/*.sh .aios/hooks/pre-commit .aios/tools/*.py .aios/tools/*.sh 2>/dev/null || true

# 2. Command adapters from the kit (the owner's own taught commands are left alone).
mkdir -p .claude/commands
for f in "$SRC"/.claude/commands/*.md; do cp "$f" .claude/commands/; done
cp "$SRC/.claude/settings.json" .claude/settings.json

# 3. The fenced engine block inside AGENTS.md, and nothing outside it.
python3 - "$SRC/AGENTS.md" "$COMPANY" "$NEW" "$PRIVATE" <<'PY'
import re, sys
from pathlib import Path
src, company, version, private = sys.argv[1:5]
block = re.search(r'<!-- aios:engine-begin -->.*?<!-- aios:engine-end -->', Path(src).read_text(), re.S).group(0)
block = block.replace('%%COMPANY%%', company).replace('%%ENGINE_VERSION%%', version).replace('%%PRIVATE%%', private)
p = Path('AGENTS.md'); s = p.read_text()
if '<!-- aios:engine-begin -->' in s:
    s = re.sub(r'<!-- aios:engine-begin -->.*?<!-- aios:engine-end -->', lambda m: block, s, count=1, flags=re.S)
else:
    s = s.rstrip('\n') + '\n\n' + block + '\n'
p.write_text(s)
PY

# 4. Migrations for any version between the old and the new, oldest first.
if [ -d .aios/migrations ]; then
  for m in $(ls .aios/migrations/*.sh 2>/dev/null | sort -V); do
    v=$(basename "$m" .sh)
    if [ "$(printf '%s\n%s\n' "$CURRENT" "$v" | sort -V | head -1)" = "$CURRENT" ] && [ "$v" != "$CURRENT" ]; then
      echo "Applying migration $v"; sh "$m"
    fi
  done
fi

# 5. Record and save.
sed -i.bak "s/^engine: .*/engine: $NEW/" aios.yml && rm -f aios.yml.bak
git config --local core.hooksPath .aios/hooks
if ! python3 .aios/tools/check.py; then
  echo "The checks failed after the upgrade. Rolling back; nothing was saved. Tell BigWork."
  git checkout -q -- . && git clean -qfd .aios .claude && receipt "$NEW" "failed-checks-rolled-back"; rm -rf "$TMP"; exit 1
fi
receipt "$NEW" "installed"
printf -- '- %s upgraded engine %s -> %s\n' "$(date +%Y-%m-%d)" "$CURRENT" "$NEW" >> memory/install-receipts.md
git add -A
git -c user.name="${GIT_AUTHOR_NAME:-$(git config user.name || echo owner)}" -c user.email="${GIT_AUTHOR_EMAIL:-$(git config user.email || echo owner@brain.local)}" \
  commit -q -m "Upgrade BigWork AI-OS engine $CURRENT -> $NEW"
git remote get-url origin >/dev/null 2>&1 && git push -q origin main 2>/dev/null || true
rm -rf "$TMP"
echo "Engine $NEW installed. What changed:"
awk -v v="$NEW" '$0 ~ "^## "v {f=1; next} /^## / {f=0} f' .aios/CHANGELOG.md 2>/dev/null | sed 's/^/  /'
