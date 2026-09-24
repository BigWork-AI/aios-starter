#!/usr/bin/env python3
"""Screen a folder the owner points at, BEFORE the AI reads any of it.

  python3 .aios/tools/gather.py /path/to/folder [--label quotes]

The AI never opens a chosen folder directly. It runs this first. The tool walks the folder, runs the
same secret scan as a save over every file it can read as text, and then:

  kept          copied into inbox/<label>/ for the AI to read and file
  screened out  NOT copied, NOT read; named (never quoted) in the read-back and in a note in the
                owner's private folder, so the owner knows what stayed behind and why
  unscreened    files the tool cannot read as text (PDFs, images, unknown types): NOT copied,
                NOT read; named so the owner can say "read that one" file by file

Prints a plain-words read-back and writes a receipt to memory/receipts/. Never prints file contents.
This is a backstop for keys, tokens, passwords and card or bank numbers. It cannot recognise every
kind of private information; the owner chooses the folder and hears every file name before it is
kept.
"""
import datetime
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check import scan_text, SCAN_SUFFIXES  # noqa: E402

TEXT_SUFFIXES = (SCAN_SUFFIXES | {'.rtf', '.tsv', '.xml', '.eml', '.ics', '.vcf'}) - {'.py', '.sh', '.env'}
OFFICE_SUFFIXES = {'.docx', '.xlsx', '.pptx'}
MAX_BYTES = 5 * 1024 * 1024
SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.Trash'}


def private_folder() -> Path:
    for line in (ROOT / 'aios.yml').read_text().splitlines():
        if line.startswith('private_folder:'):
            return Path(line.split(':', 1)[1].strip()).expanduser()
    return ROOT.parent / 'private'


def office_text(path: Path) -> str:
    """Word, Excel and PowerPoint files are zips of XML; pull the text out without any library."""
    parts = []
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if name.endswith('.xml') and ('word/' in name or 'xl/' in name or 'ppt/slides/' in name):
                parts.append(re.sub(r'<[^>]+>', ' ', z.read(name).decode('utf-8', errors='ignore')))
    return '\n'.join(parts)


def readable_text(path: Path):
    """Return the file's text, or None when it cannot be screened."""
    if path.stat().st_size > MAX_BYTES:
        return None
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return path.read_text(errors='ignore')
    if suffix in OFFICE_SUFFIXES:
        try:
            return office_text(path)
        except (zipfile.BadZipFile, OSError):
            return None
    return None


def gather(folder: Path, label: str) -> dict:
    kept, screened, unscreened = [], [], []
    dest = ROOT / 'inbox' / label
    for path in sorted(p for p in folder.rglob('*') if p.is_file()):
        rel = path.relative_to(folder)
        if any(part in SKIP_DIRS or part.startswith('.') for part in rel.parts):
            continue
        text = readable_text(path)
        if text is None:
            unscreened.append(str(rel))
            continue
        problems = scan_text(text, str(rel))
        if problems:
            # keep the reason, never the value: "looks like a card number"
            reason = re.sub(r'^.*looks like a (.+?)\..*$', r'\1', problems[0])
            screened.append({'file': str(rel), 'reason': reason})
            continue
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        kept.append(str(rel))
    return {'kept': kept, 'screened_out': screened, 'unscreened': unscreened}


def main(argv: list) -> int:
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 2
    folder = Path(argv[0]).expanduser().resolve()
    label = folder.name
    if '--label' in argv:
        label = argv[argv.index('--label') + 1]
    label = re.sub(r'[^a-z0-9-]+', '-', label.lower()).strip('-') or 'files'
    if not folder.is_dir():
        print(f'Not a folder: {folder}')
        return 1
    if ROOT in folder.parents or folder == ROOT:
        print('That folder is inside the brain already; point me at where the files live now.')
        return 1
    today = datetime.date.today().isoformat()
    result = gather(folder, label)
    receipt = {'date': today, 'folder': str(folder), 'label': label, **result}
    receipts = ROOT / 'memory/receipts'
    receipts.mkdir(parents=True, exist_ok=True)
    (receipts / f'gather-{label}-{today}.json').write_text(json.dumps(receipt, indent=2) + '\n')

    if result['screened_out']:
        note = private_folder() / 'screened-out.md'
        note.parent.mkdir(parents=True, exist_ok=True)
        with note.open('a') as f:
            f.write(f'\n## {today}: screened out of "{label}" ({folder})\n\n')
            f.write('These files were not copied into the brain and were not read by the AI. Each one looked like it held something that must not go in the brain. They are still where they were.\n\n')
            for item in result['screened_out']:
                f.write(f"- {item['file']}: looks like a {item['reason']}\n")

    k, s_, u = len(result['kept']), len(result['screened_out']), len(result['unscreened'])
    print(f'Looked at "{folder.name}".')
    print(f'Kept {k} file(s) for reading, now in inbox/{label}/.' if k else 'Kept nothing: no readable files found.')
    if s_:
        names = ', '.join(i['file'] for i in result['screened_out'])
        print(f'Left {s_} file(s) where they were, unread, because they look like they hold private numbers or passwords: {names}. Listed in your private folder.')
    if u:
        names = ', '.join(result['unscreened'])
        print(f'Could not screen {u} file(s), so I did not copy or read them: {names}. Say the name of any you want read, one at a time.')
    print(f'Receipt: memory/receipts/gather-{label}-{today}.json')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
