#!/bin/sh
# 0.3.10 copies .aios and Claude commands, but not .agents. Carry the exact Codex
# adapters inside the verified engine so that OLD updater can install them before
# it runs the new structural check. Never replace an owner's conflicting skill.
set -eu
python3 - <<'PY'
import json
from pathlib import Path
import re
import subprocess

bundle = json.loads(Path('.aios/compat/command-skills.json').read_text())
pending = []
for name, content in bundle.items():
    if not re.fullmatch(r'[a-z][a-z0-9-]*', name) or not isinstance(content, str):
        raise SystemExit('Invalid engine command adapter bundle; upgrade stopped.')
    dest = Path('.agents/skills') / name / 'SKILL.md'
    # Check every component before writing anything. A skill symlink must never
    # let a migration write outside this brain, including through a parent folder.
    for path in [*reversed(dest.parents), dest]:
        if path.is_symlink():
            raise SystemExit(f'Cannot install engine command through a symlink: {path}')
        if path != dest and path.exists() and not path.is_dir():
            raise SystemExit(f'Engine command folder is occupied: {path}')
    if dest.exists():
        if not dest.is_file() or dest.read_bytes() != content.encode('utf-8'):
            raise SystemExit(f'Keeping an existing skill at {dest}; ask BigWork to resolve the command conflict.')
        continue
    ignored = subprocess.run(['git', 'check-ignore', '-q', '--', str(dest)])
    if ignored.returncode != 1:
        raise SystemExit(f'Cannot safely save engine command at {dest}; check the brain ignore rules.')
    pending.append((dest, content))

created = []
try:
    for dest, content in pending:
        dest.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation also prevents replacing a file created since preflight.
        with dest.open('x', encoding='utf-8', newline='') as f:
            created.append(dest)
            f.write(content)
    if created:
        # The 0.3.10 rollback snapshots untracked/ignored folders by directory.
        # Stage our additions so its git reset removes them even when .agents
        # already contained an ignored owner skill. Never stage the owner's files.
        subprocess.run(['git', 'add', '--', *map(str, created)], check=True)
except BaseException:
    for path in created:
        path.unlink(missing_ok=True)
    raise
PY
