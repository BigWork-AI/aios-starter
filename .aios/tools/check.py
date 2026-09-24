#!/usr/bin/env python3
"""BigWork AI-OS checks for a company brain.

  python3 .aios/tools/check.py            # structure + fact status + secret scan of tracked files
  python3 .aios/tools/check.py --staged   # same, on the files about to be committed (pre-commit)
  python3 .aios/tools/check.py --scan FILE [FILE ...]   # secret scan only, on given files

Exit 0 when clean, 1 with a plain-English list of problems. This is a backstop, not the privacy
promise: the private folder lives outside the repository and the interview screens material before
it is read. Patterns here catch the obvious leaks (keys, tokens, cards, private keys, passwords).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    'AGENTS.md', 'CLAUDE.md', 'README.md', 'aios.yml', '.aios/VERSION', '.aios/interview.json',
    'company/identity.md', 'company/services.md', 'company/customers.md', 'company/people.md',
    'company/access.md', 'company/tools.md', 'clients/README.md', 'skills/README.md',
    'memory/README.md', 'inbox/README.md', 'inbox/review/README.md',
]
STATUSES = {'confirmed', 'imported', 'inferred', 'example'}
SCAN_SUFFIXES = {'.md', '.yml', '.yaml', '.json', '.txt', '.csv', '.html', '.py', '.sh', '.env'}

SECRET_PATTERNS = [
    ('private key block', re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----')),
    ('AWS access key', re.compile(r'\bAKIA[0-9A-Z]{16}\b')),
    ('GitHub token', re.compile(r'\bgh[pousr]_[A-Za-z0-9]{30,}\b')),
    ('Slack token', re.compile(r'\bxox[abprs]-[A-Za-z0-9-]{10,}\b')),
    ('API key (sk-...)', re.compile(r'\bsk-(?:ant-|proj-|live-)?[A-Za-z0-9_-]{20,}\b')),
    ('Stripe key', re.compile(r'\b(?:pk|rk)_(?:live|test)_[A-Za-z0-9]{16,}\b')),
    ('Google API key', re.compile(r'\bAIza[0-9A-Za-z_-]{35}\b')),
    ('password assignment', re.compile(r'(?i)\b(?:password|passwd|pwd)\s*[:=]\s*\S{6,}')),
    ('bearer token', re.compile(r'(?i)\bbearer\s+[A-Za-z0-9._-]{20,}')),
    ('card number', re.compile(r'\b(?:\d[ -]?){13,19}\b')),
]


def luhn_ok(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d = d * 2 - 9 if d * 2 > 9 else d * 2
        total += d
        alt = not alt
    return total % 10 == 0


def scan_text(text: str, name: str) -> list:
    problems = []
    for label, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            if label == 'card number':
                digits = re.sub(r'\D', '', match.group(0))
                if not (13 <= len(digits) <= 19 and luhn_ok(digits)):
                    continue
            line = text.count('\n', 0, match.start()) + 1
            problems.append(f'{name} line {line}: looks like a {label}. Remove it; it never belongs in the brain.')
            break
    return problems


def tracked_files(staged: bool) -> list:
    args = ['git', '-C', str(ROOT), 'diff', '--cached', '--name-only', '--diff-filter=ACM'] if staged \
        else ['git', '-C', str(ROOT), 'ls-files']
    out = subprocess.run(args, capture_output=True, text=True)
    if out.returncode != 0:
        return [str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.parts]
    return out.stdout.split()


def read(name: str, staged: bool) -> str:
    if staged:
        out = subprocess.run(['git', '-C', str(ROOT), 'show', f':{name}'], capture_output=True, text=True)
        if out.returncode == 0:
            return out.stdout
    try:
        return (ROOT / name).read_text(errors='ignore')
    except OSError:
        return ''


def check_structure() -> list:
    return [f'missing {name}: the brain is incomplete; run the install again.' for name in REQUIRED if not (ROOT / name).exists()]


def check_fact_tables(names: list, staged: bool) -> list:
    """Every fact row in company/*.md must carry a status the engine understands."""
    problems = []
    row = re.compile(r'^\|(?!\s*-)(?!\s*Fact\b)([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|\s*$')
    for name in names:
        if not (name.startswith('company/') and name.endswith('.md')):
            continue
        for i, line in enumerate(read(name, staged).splitlines(), 1):
            m = row.match(line)
            if not m:
                continue
            status = m.group(5).strip().lower()
            if status == 'status':  # table header row
                continue
            if status and status not in STATUSES:
                problems.append(f'{name} line {i}: status "{status}" is not one of confirmed, imported, inferred.')
    return problems


def check_onboarding() -> list:
    path = ROOT / 'memory/onboarding.json'
    if not path.exists():
        return []
    try:
        json.loads(path.read_text())
    except ValueError as err:
        return [f'memory/onboarding.json is not valid: {err}. The interview cannot resume until it is fixed.']
    return []


def main(argv: list) -> int:
    if argv[:1] == ['--scan']:
        problems = [p for f in argv[1:] for p in scan_text(Path(f).read_text(errors='ignore'), f)]
    else:
        staged = argv[:1] == ['--staged']
        names = [n for n in tracked_files(staged) if Path(n).suffix.lower() in SCAN_SUFFIXES or Path(n).name == '.env']
        problems = check_structure() + check_onboarding() + check_fact_tables(names, staged)
        for name in names:
            if name.startswith('.aios/tools/'):
                continue
            problems += scan_text(read(name, staged), name)
    if problems:
        print('\n'.join(problems))
        return 1
    print('brain check passed')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
