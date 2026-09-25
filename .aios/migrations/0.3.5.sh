#!/bin/sh
# 0.3.5: taught skills become real Claude skills. skills/<name>.md moves to
# .claude/skills/<name>/SKILL.md (a name and description line is added from its "Use when");
# the old one-line command that pointed at it is removed. Content is never changed or deleted.
python3 - <<'PY'
import re
from pathlib import Path
for f in sorted(Path('skills').glob('*.md')):
    if f.name == 'README.md':
        continue
    name = f.stem
    dest = Path('.claude/skills') / name / 'SKILL.md'
    if dest.exists():
        continue
    text = f.read_text()
    if not text.startswith('---'):
        use = re.search(r'\*\*Use when:\*\*\s*(.+)', text)
        desc = (use.group(1).strip() if use else f'The {name} job, as taught by the owner.').replace('\n', ' ')
        text = f'---\nname: {name}\ndescription: {desc}\n---\n\n' + text
    text = text.replace('skills/voice.md', '.claude/skills/voice/SKILL.md')
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text)
    f.unlink()
    cmd = Path('.claude/commands') / f'{name}.md'
    if cmd.exists() and f'skills/{name}.md' in cmd.read_text():
        cmd.unlink()
PY
