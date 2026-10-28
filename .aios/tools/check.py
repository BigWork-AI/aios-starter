#!/usr/bin/env python3
"""BigWork AI-OS checks for a company brain.

  python3 .aios/tools/check.py            # structure + fact status + secret scan of tracked files
  python3 .aios/tools/check.py --staged   # same, on the files about to be committed (pre-commit)
  python3 .aios/tools/check.py --scan FILE [FILE ...]   # secret scan only, on given files

Exit 0 when clean, 1 with a plain-English list of problems. This is a backstop, not the privacy
promise: the private folder lives outside the repository and the interview screens material before
it is read. Patterns here catch the obvious leaks (keys, tokens, cards, private keys, passwords, bank
account and routing numbers next to a bank word, IBANs, social security numbers).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True  # importing a sibling tool must not leave a cache file in the engine folder for the save to pick up
sys.path.insert(0, str(Path(__file__).resolve().parent))

REQUIRED = [
    'AGENTS.md', 'CLAUDE.md', '.agents/skills/start/SKILL.md', 'README.md', 'aios.yml', '.aios/VERSION', '.aios/interview.json',
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
    # A card is written as one run of digits or in the usual groups (4-4-4-4, 4-6-5). Any spacing
    # looser than that joins neighbouring spreadsheet cells into false alarms.
    ('card number', re.compile(r'(?<![\d.,])(?:[3-6]\d{12,18}|[3-6]\d{3}(?:[ -]\d{4}){2}[ -]\d{1,7}|3\d{3}[ -]\d{6}[ -]\d{5})(?![\d.,])')),
    # Bank numbers only next to a bank word. A blocked save blocks the whole session, so a bare
    # "account 10023456" (a customer or supplier account) is left alone.
    ('bank routing number', re.compile(r'(?i)\b(?:routing|aba)\s*(?:number|no\.?|#)?\s*[:#]?\s*\d{9}\b')),
    ('bank account number', re.compile(r'(?i)\b(?:bank\s+account|account\s+(?:number|no\.?|#)|acct\.?|a/c)\s*(?:number|no\.?|#)?\s*[:#]?\s*\d{8,17}\b')),
    ('IBAN', re.compile(r'\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){3,7}(?: ?[A-Z0-9]{1,3})?\b')),
    ('social security number', re.compile(r'\b(?!000|666|9\d\d)\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b')),
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
            article = 'an' if label[0].lower() in 'aeiou' or label.startswith('IBAN') else 'a'
            problems.append(f'{name} line {line}: looks like {article} {label}. Remove it; it never belongs in the brain.')
            break
    return problems


def tracked_files(staged: bool) -> list:
    # -z gives every name whole: spaces and accents ("Client Notes.md", "Café.md") are neither split
    # nor quoted. --no-renames lists a moved-and-edited file as added, so its new content is read.
    args = ['git', '-C', str(ROOT), 'diff', '--cached', '--name-only', '-z', '--no-renames', '--diff-filter=ACM'] if staged \
        else ['git', '-C', str(ROOT), 'ls-files', '-z']
    out = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='surrogateescape')
    if out.returncode != 0:
        return [str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.parts]
    return [name for name in out.stdout.split('\0') if name]


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


def check_pipeline(staged: bool) -> list:
    """clients/pipeline.md is generated from the client cards; a page that does not match them is stale and must not be saved."""
    try:
        import pipeline
    except ImportError:
        return ['.aios/tools/pipeline.py is missing: the brain is incomplete; run the install again.']
    return pipeline.problems(ROOT, staged)


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
        problems = check_structure() + check_onboarding() + check_fact_tables(names, staged) + check_pipeline(staged)
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
