#!/usr/bin/env python3
"""Screen a folder the owner points at, BEFORE the AI reads any of it.

  python3 .aios/tools/gather.py /path/to/folder [--label quotes]

The AI never opens a chosen folder directly. It runs this first. The tool walks the folder, runs the
same secret scan as a save over every file it can read as text, and then:

  kept          copied into inbox/<label>/ for the AI to read and file
  screened out  NOT copied, NOT read; named (never quoted) in the read-back and in a note in the
                owner's private folder, so the owner knows what stayed behind and why
  unscreened    files the tool cannot read as text (PDFs, images, unknown types): NOT copied,
                NOT read; named so the owner can approve them, all at once or one by one
  skipped       shortcuts (symlinks) and hidden files: NOT followed, NOT copied, NOT read; named. A
                shortcut can point anywhere, including the private folder, so it is never opened.

A file already looked at in an earlier run, and unchanged since, is skipped and only counted, so the
owner can keep adding to the same folder and say "read my new documents". The folder's own note to
the owner (ABOUT THIS FOLDER.md) is never gathered.

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
FOLDER_NOTE = 'ABOUT THIS FOLDER.md'


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


def walk(folder: Path):
    """Yield (path, rel, kind) for every entry, never stepping through a shortcut."""
    stack = [folder]
    while stack:
        current = stack.pop()
        for path in sorted(current.iterdir()):
            rel = path.relative_to(folder)
            if path.name in SKIP_DIRS:
                continue
            if path.is_symlink():
                yield path, rel, 'shortcut'
            elif path.name.startswith('.'):
                if path.name not in ('.DS_Store', '.localized'):
                    yield path, rel, 'hidden'
            elif path.is_dir():
                stack.append(path)
            elif path.is_file():
                yield path, rel, 'file'


def gather(folder: Path, label: str, seen: dict) -> dict:
    kept, screened, unscreened, earlier, skipped = [], [], [], [], []
    dest = ROOT / 'inbox' / label
    for path, rel, kind in sorted(walk(folder), key=lambda item: str(item[1])):
        if str(rel) == FOLDER_NOTE:
            continue
        if kind != 'file':
            skipped.append(str(rel))
            continue
        stamp = f'{path.stat().st_size}:{int(path.stat().st_mtime)}'
        if seen.get(str(rel)) == stamp:
            earlier.append(str(rel))
            continue
        text = readable_text(path)
        if text is None:
            unscreened.append(str(rel))
            seen[str(rel)] = stamp
            continue
        problems = scan_text(text, str(rel))
        if problems:
            # keep the reason, never the value: "looks like a card number"
            reason = re.sub(r'^.*looks like (an? .+?)\. Remove it.*$', r'\1', problems[0])
            screened.append({'file': str(rel), 'reason': reason})
            continue
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        kept.append(str(rel))
        seen[str(rel)] = stamp
    return {'kept': kept, 'screened_out': screened, 'unscreened': unscreened, 'skipped': skipped, 'looked_at_before': earlier}


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
    private = private_folder().resolve()
    if folder == private or private in folder.parents:
        print('That is your private folder. The brain never reads it; point me at a different folder.')
        return 1
    now = datetime.datetime.now()
    today = now.date().isoformat()
    receipts = ROOT / 'memory/receipts'
    receipts.mkdir(parents=True, exist_ok=True)
    seen_file = receipts / f'seen-{label}.json'
    seen = json.loads(seen_file.read_text()) if seen_file.exists() else {}
    result = gather(folder, label, seen)
    seen_file.write_text(json.dumps(seen, indent=2, sort_keys=True) + '\n')
    receipt = {'date': today, 'folder': str(folder), 'label': label, **result}
    (receipts / f'gather-{label}-{now:%Y-%m-%d-%H%M%S}.json').write_text(json.dumps(receipt, indent=2) + '\n')

    if result['screened_out']:
        note = private_folder() / 'screened-out.md'
        note.parent.mkdir(parents=True, exist_ok=True)
        with note.open('a') as f:
            f.write(f'\n## {today}: screened out of "{label}" ({folder})\n\n')
            f.write('These files were not copied into the brain and were not read by the AI. Each one looked like it held something that must not go in the brain. They are still where they were.\n\n')
            for item in result['screened_out']:
                f.write(f"- {item['file']}: looks like {item['reason']}\n")

    k, s_, u = len(result['kept']), len(result['screened_out']), len(result['unscreened'])
    print(f'Looked at "{folder.name}".')
    if result['looked_at_before']:
        print(f"Skipped {len(result['looked_at_before'])} file(s) already looked at before and unchanged since.")
    print(f'Kept {k} file(s) for reading, now in inbox/{label}/.' if k else 'Kept nothing: no readable files found.')
    if s_:
        names = ', '.join(i['file'] for i in result['screened_out'])
        print(f'Left {s_} file(s) where they were, unread, because they look like they hold private numbers or passwords: {names}. Listed in your private folder.')
    if u:
        names = ', '.join(result['unscreened'])
        print(f'Could not screen {u} file(s), so I did not copy or read them: {names}. Say "read them all" or name the ones you want read; I read those where they are and never copy them into the brain.')
    if result['skipped']:
        names = ', '.join(result['skipped'])
        print(f"Passed over {len(result['skipped'])} shortcut(s) or hidden file(s) without opening them: {names}. A shortcut can point at your private folder, so I never follow one. If you want one of these read, put a real copy in the folder instead.")
    print(f'Receipt: memory/receipts/gather-{label}-{now:%Y-%m-%d-%H%M%S}.json')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
