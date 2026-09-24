#!/bin/sh
# BigWork AI-OS installer.
#
# The one line a customer pastes (fetches the kit itself, nothing to download first):
#
#   curl -fsSL https://raw.githubusercontent.com/BigWork-AI/aios-starter/main/install.sh | sh
#
# It asks for the business name and makes the short name from it. Both can be given up front
# instead: ... | sh -s -- "Acme Roofing" acme-roofing
#
# Or, with a local copy of the kit (friends-week, USB stick):
#
#   AIOS_SOURCE=./aios-starter sh aios-starter/install.sh "Acme Roofing" acme-roofing
#
# Creates a private company brain for the named business, wires the checks, makes the private
# folder and the documents drop folder outside the repository, and opens the kickoff interview. Safe to run twice: every step
# checks before it acts.
#
# Where the kit comes from, in order:
#   1. AIOS_SOURCE=/path/to/aios-starter      a local copy
#   2. AIOS_KIT_URL=<tarball url>             a specific kit archive
#   3. the public kit repository (AIOS_REPO, default BigWork-AI/aios-starter), fetched with curl
set -eu

COMPANY="${1:-}"
SLUG="${2:-}"
# Piped into sh, the script itself is on standard input, so the question is asked on the terminal.
TTY="${AIOS_TTY:-/dev/tty}"
if [ -z "$COMPANY" ] && (: < "$TTY") 2>/dev/null; then
  printf 'What is your business called? ' >&2
  IFS= read -r COMPANY < "$TTY" || COMPANY=""
fi
if [ -z "$SLUG" ]; then
  SLUG=$(printf '%s' "$COMPANY" | tr '[:upper:]' '[:lower:]' | sed 's/&/and/g; s/[^a-z0-9][^a-z0-9]*/-/g; s/^-//; s/-$//')
fi
if [ -z "$COMPANY" ] || [ -z "$SLUG" ]; then
  echo "usage: curl -fsSL https://raw.githubusercontent.com/BigWork-AI/aios-starter/main/install.sh | sh -s -- \"Company Name\" company-slug"; exit 2
fi
# The name goes into files through sed, where & and | have special meanings.
COMPANY_SED=$(printf '%s' "$COMPANY" | sed 's/[&|\\]/\\&/g')
DEST="${AIOS_DEST:-$HOME/$SLUG-brain}"
PRIVATE="${AIOS_PRIVATE:-$HOME/$SLUG-private}"
DOCUMENTS="${AIOS_DOCUMENTS:-$HOME/$SLUG-documents}"
TODAY=$(date +%Y-%m-%d)
PRIVATE_SED=$(printf '%s' "$PRIVATE" | sed 's/[&|\\]/\\&/g')
DOCUMENTS_SED=$(printf '%s' "$DOCUMENTS" | sed 's/[&|\\]/\\&/g')
# The documents folder is read (after screening); the private folder never is. Keep them apart,
# and keep both outside the brain so nothing dropped in is saved to its history unscreened.
case "$DOCUMENTS/" in
  "$PRIVATE/"|"$PRIVATE/"*|"$DEST/"|"$DEST/"*) echo "The documents folder must be its own folder, outside the brain and outside the private folder: $DOCUMENTS"; exit 2 ;;
esac

say() { printf '\n== %s\n' "$*"; }
need() { command -v "$1" >/dev/null 2>&1; }

say "Checking the machine"
OS=$(uname -s 2>/dev/null || echo unknown)
missing=""
# Git and Python: on a Mac both arrive with Apple's command line tools, one prompt.
if ! need git; then
  if [ "$OS" = Darwin ]; then
    echo "Git is not installed yet. Apple will show a window asking to install its command line tools."
    echo "Click Install, wait for it to finish (a few minutes), then paste the same line again."
    xcode-select --install >/dev/null 2>&1 || true
    exit 0
  fi
  missing="$missing\n- Git: install from https://git-scm.com then paste the same line again."
fi
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)' 2>/dev/null; then
  if [ "$OS" = Darwin ]; then
    echo "Python is not ready yet. Apple will show a window asking to install its command line tools."
    echo "Click Install, wait for it to finish, then paste the same line again."
    xcode-select --install >/dev/null 2>&1 || true
    exit 0
  fi
  missing="$missing\n- Python 3.9 or newer: install from https://python.org then paste the same line again."
fi
if [ -n "$missing" ]; then
  printf 'Before the brain can be built:%b\n' "$missing"
  exit 1
fi
# Claude Code: install it if we can, otherwise say exactly where to get it.
# AIOS_INSTALL_CLAUDE=0 skips this (the kit's tests use it so they never download anything).
if ! need claude && [ "${AIOS_INSTALL_CLAUDE:-1}" = 1 ]; then
  if need npm; then
    echo "Installing Claude Code (one minute)."
    npm install -g @anthropic-ai/claude-code >/dev/null 2>&1 && echo "Claude Code installed." || echo "Could not install Claude Code automatically. Get it at https://claude.ai/code and paste the same line again when it is in."
  elif [ "$OS" = Darwin ] && need brew; then
    echo "Installing Claude Code (one minute)."
    brew install --quiet node >/dev/null 2>&1 && npm install -g @anthropic-ai/claude-code >/dev/null 2>&1 && echo "Claude Code installed." || echo "Could not install Claude Code automatically. Get it at https://claude.ai/code and paste the same line again when it is in."
  elif need curl; then
    echo "Installing Claude Code with Anthropic's installer (one minute)."
    curl -fsSL https://claude.ai/install.sh | bash >/dev/null 2>&1 && echo "Claude Code installed." || echo "Could not install Claude Code automatically. Get it at https://claude.ai/code and paste the same line again when it is in."
  else
    echo "Claude Code is not installed yet. The brain will still be built. Get Claude Code at https://claude.ai/code, then open the brain folder and type /start."
  fi
  # Anthropic's installer puts it in ~/.local/bin, which this shell may not search yet.
  need claude || PATH="$HOME/.local/bin:$PATH"
fi
# GitHub is optional at install: it is the online backup and the phone link, connected during the session.
need gh && GH=1 || GH=0

say "Creating the brain at $DEST"
if [ -d "$DEST/.aios" ]; then
  echo "Already exists; keeping it."
elif [ -n "${AIOS_SOURCE:-}" ]; then
  mkdir -p "$DEST"
  cp -R "$AIOS_SOURCE"/. "$DEST"/
  rm -f "$DEST/install.sh"
  (cd "$DEST" && git init -q -b main)
else
  need curl || { echo "curl is missing. Install it (it ships with macOS) and run this again."; exit 1; }
  need tar || { echo "tar is missing. Install it and run this again."; exit 1; }
  KIT_URL="${AIOS_KIT_URL:-https://github.com/${AIOS_REPO:-BigWork-AI/aios-starter}/archive/refs/heads/main.tar.gz}"
  TMP=$(mktemp -d)
  echo "Fetching the kit from $KIT_URL"
  if ! curl -fsSL "$KIT_URL" -o "$TMP/kit.tar.gz"; then
    code=$(curl -s -o /dev/null -w '%{http_code}' "$KIT_URL" 2>/dev/null || echo 000)
    case "$code" in
      404) echo "The BigWork kit is not published at $KIT_URL yet. That is on BigWork's side, not yours: nothing on this computer is wrong. Tell BigWork, or install from a copy of the kit with: AIOS_SOURCE=/path/to/aios-starter sh /path/to/aios-starter/install.sh \"$COMPANY\" $SLUG" ;;
      000) echo "Could not reach GitHub. Check the internet connection and paste the same line again." ;;
      *)   echo "GitHub answered $code while fetching the kit. Paste the same line again in a minute; if it keeps happening, tell BigWork." ;;
    esac
    exit 1
  fi
  mkdir -p "$TMP/kit" && tar -xzf "$TMP/kit.tar.gz" -C "$TMP/kit"
  SRC=$(find "$TMP/kit" -maxdepth 3 -name .aios -type d | head -1)
  [ -n "$SRC" ] || { echo "The downloaded kit is not a BigWork AI-OS starter (no .aios folder)."; exit 1; }
  SRC=$(dirname "$SRC")
  mkdir -p "$DEST"
  cp -R "$SRC"/. "$DEST"/
  rm -f "$DEST/install.sh"
  (cd "$DEST" && git init -q -b main)
  rm -rf "$TMP"
fi
cd "$DEST"

say "Naming it"
ENGINE=$(cat .aios/VERSION)
for f in AGENTS.md README.md CLAUDE.md company/identity.md company/access.md guide.md .aios/interview.json; do
  [ -f "$f" ] && sed -i.bak "s|%%COMPANY%%|$COMPANY_SED|g; s|%%ENGINE_VERSION%%|$ENGINE|g; s|%%PRIVATE%%|$PRIVATE_SED|g; s|%%DOCUMENTS%%|$DOCUMENTS_SED|g" "$f" && rm -f "$f.bak"
done
if grep -q '%%COMPANY%%' aios.yml 2>/dev/null || [ ! -f aios.yml ]; then
  cat > aios.yml <<EOF
company: "$COMPANY"
slug: $SLUG
engine: $ENGINE
harness: claude-code
installed: $TODAY
private_folder: $PRIVATE
documents_folder: $DOCUMENTS
upgrade: auto
EOF
fi
grep -q '^documents_folder:' aios.yml || printf 'documents_folder: %s\n' "$DOCUMENTS" >> aios.yml

say "Making the private folder outside the brain: $PRIVATE"
mkdir -p "$PRIVATE"
[ -f "$PRIVATE/README.md" ] || cat > "$PRIVATE/README.md" <<EOF
# $COMPANY private folder

This folder is outside the company brain on purpose. Bank, payroll, contracts you have not chosen
to share, personal matters: they live here. The brain never opens this folder. Nothing here is
backed up by the brain; back it up the way you back up any private document.
EOF

say "Making the documents folder: $DOCUMENTS"
mkdir -p "$DOCUMENTS"
[ -f "$DOCUMENTS/ABOUT THIS FOLDER.md" ] || cat > "$DOCUMENTS/ABOUT THIS FOLDER.md" <<EOF
# Documents for the $COMPANY brain

Drop copies of anything you want the brain to know about in here: price lists, brochures,
proposals and quotes, how-we-do-it notes, meeting notes, a ChatGPT or Claude export. PDFs and
Word files are fine. Keep bank statements, payroll and anything personal out; those go in
$PRIVATE.

Check every file before you drop it in: PDFs, Word files, spreadsheets, notes. Open each one and
make sure it has none of these:

- bank or card numbers, account or routing numbers
- passwords or logins
- pay, salary or payroll figures
- tax, social security or ID numbers
- staff home addresses, personal phone numbers or health details

If a file has any of them, delete that part or black it out and save a new copy, or leave it out.
The brain catches some of this in text and Word files, but not all of it, and it cannot look
inside most PDFs at all. You are the main check.

The brain never opens this folder on its own. When you say "read my new documents", it checks each
file for passwords and card or bank numbers first, reads only what passes, and tells you what it
left behind. Files it cannot check, like most PDFs, it names and asks before reading; it reads
those here and never copies them into the brain.
EOF

say "Wiring the checks"
chmod +x scripts/setup.sh .aios/hooks/pre-commit .aios/tools/check.py .aios/tools/gather.py .aios/tools/receipt.py .aios/tools/frontpage.py
./scripts/setup.sh

say "First save"
git add -A
git -c user.name="${GIT_AUTHOR_NAME:-$COMPANY}" -c user.email="${GIT_AUTHOR_EMAIL:-owner@$SLUG.local}" \
  commit -q -m "Install BigWork AI-OS $ENGINE for $COMPANY" 2>/dev/null || echo "Nothing new to save."

if ! git remote get-url origin >/dev/null 2>&1; then
  if [ "$GH" = 1 ] && gh auth status >/dev/null 2>&1; then
    say "Creating the private GitHub copy"
    gh repo create "$SLUG-brain" --private --source . --push >/dev/null && echo "Pushed to GitHub (private)." \
      || echo "Could not create the GitHub copy. The brain works locally; connect GitHub later with: gh repo create $SLUG-brain --private --source . --push"
    echo "Check two-factor login is on for this GitHub account before the session ends."
  else
    say "GitHub not connected yet"
    echo "The brain is built and works on this computer. GitHub is the online backup and what links your phone."
    echo "We connect it during your setup session. If you want to do it yourself: install GitHub's tool (https://cli.github.com), run 'gh auth login', then in the brain folder run: gh repo create $SLUG-brain --private --source . --push"
  fi
fi

say "Install receipt"
mkdir -p memory
printf -- '- %s installed BigWork AI-OS %s on this machine (harness: %s, private folder: %s)\n' \
  "$TODAY" "$ENGINE" "$(need claude && echo claude-code || echo none-yet)" "$PRIVATE" >> memory/install-receipts.md
git add memory/install-receipts.md && git commit -q -m "Install receipt $TODAY" 2>/dev/null || true

say "Done."
echo "Your brain: $DEST"
echo "Private folder (never read by the brain): $PRIVATE"
echo "Documents folder (put the files you want the brain to know here): $DOCUMENTS"
echo "Talk, do not type: on a Mac press the microphone key (or tap the Globe/fn key twice) and speak your answers. Windows: hold the Windows key and press H."
if [ -n "${CLAUDECODE:-}" ] || [ "${AIOS_NO_LAUNCH:-0}" = 1 ]; then
  # Claude itself ran this (desktop app or CLI). Do not start a second Claude inside it.
  echo "NEXT STEP FOR THE OWNER: in Claude, open the folder $DEST and say hello (or type /start). The interview begins there."
elif need claude; then
  echo "Opening the interview."
  exec claude "/start"
else
  echo "Install Claude Code, open $DEST, and type /start."
fi
