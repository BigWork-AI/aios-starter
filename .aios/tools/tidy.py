#!/usr/bin/env python3
"""Find the mechanical mess in what the brain has read, so the owner hears it as questions.

  python3 .aios/tools/tidy.py [folder ...]      (default: inbox/ and memory/imported/)

Looks through the spreadsheets and CSV files already screened into the brain and reports:

  duplicate contacts   the same email or phone number on more than one customer row
  price clashes        the same product or item name with different prices in different files
  possible old copies  files whose names say old, draft, copy, v1, backup, or an earlier month

It never changes a file and never decides which one is right: it hands the brain a list, and the
brain raises each one with the owner as a question. Judgement calls (which discount was approved,
whether a reminder chases a paid invoice) stay with the brain's read-back.
"""
import csv
import io
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EMAIL = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')
MONEY = re.compile(r'^\$?\s*\d{1,6}(?:,\d{3})*(?:\.\d{1,2})?$')
OLD = re.compile(r'(?i)\b(old|draft|copy|backup|v\d+|scratch\w*|superseded|archive\w*|previous)\b')


def rows_from(path: Path):
    """Yield dict rows from a CSV or the first sheet of an .xlsx, without any library."""
    if path.suffix.lower() == '.csv':
        with path.open(newline='', errors='ignore') as f:
            yield from csv.DictReader(f)
    elif path.suffix.lower() == '.xlsx':
        try:
            with zipfile.ZipFile(path) as z:
                shared = re.findall(r'<si>.*?</si>', z.read('xl/sharedStrings.xml').decode('utf-8', 'ignore'), re.S) if 'xl/sharedStrings.xml' in z.namelist() else []
                shared = [re.sub(r'<[^>]+>', '', s) for s in shared]
                sheets = sorted(n for n in z.namelist() if n.startswith('xl/worksheets/sheet'))
                if not sheets:
                    return
                xml = z.read(sheets[0]).decode('utf-8', 'ignore')
        except (zipfile.BadZipFile, KeyError, OSError):
            return
        table = []
        for row in re.findall(r'<row[^>]*>(.*?)</row>', xml, re.S):
            cells = []
            for c in re.finditer(r'<c([^>]*)>(.*?)</c>', row, re.S):
                v = re.search(r'<v>(.*?)</v>', c.group(2), re.S) or re.search(r'<t[^>]*>(.*?)</t>', c.group(2), re.S)
                val = v.group(1) if v else ''
                if 't="s"' in c.group(1) and val.isdigit() and int(val) < len(shared):
                    val = shared[int(val)]
                cells.append(val)
            table.append(cells)
        if len(table) > 1:
            head = table[0]
            for r in table[1:]:
                yield {head[i] if i < len(head) else f'col{i}': v for i, v in enumerate(r)}


def phone_key(s: str) -> str:
    d = re.sub(r'\D', '', s or '')
    return d[-10:] if len(d) >= 10 else ''


def label(row: dict) -> str:
    """'Lena Ortiz (C001)': the best name column, then an id column if there is one."""
    name = ident = ''
    for pattern in (r'(?i)^(full.?)?name$', r'(?i)^(customer|contact|client).?name$', r'(?i)^(contact|customer|client|company)$'):
        name = name or next((row[k] for k in row if k and re.search(pattern, k.strip()) and row[k]), '')
    ident = next((row[k] for k in row if k and re.search(r'(?i)(^|\b)(id|number|no\.?|#)$', k.strip()) and row[k]), '')
    if name and ident:
        return f'{name} ({ident})'
    return name or ident or '(no name)'


def main(argv):
    folders = [Path(a) for a in argv] or [ROOT / 'inbox', ROOT / 'memory/imported']
    files = [p for f in folders if f.exists() for p in sorted(f.rglob('*')) if p.is_file()]
    by_email, by_phone = defaultdict(set), defaultdict(set)
    prices = defaultdict(lambda: defaultdict(set))
    for path in files:
        if path.suffix.lower() not in ('.csv', '.xlsx'):
            continue
        rel = str(path.relative_to(ROOT)) if ROOT in path.parents else str(path)
        for row in rows_from(path):
            row = {str(k or '').strip(): str(v or '').strip() for k, v in row.items()}
            who = label(row)
            for k, v in row.items():
                for e in EMAIL.findall(v):
                    by_email[e.lower()].add((who, rel))
                if re.search(r'(?i)phone|mobile|cell|tel', k) and phone_key(v):
                    by_phone[phone_key(v)].add((who, rel))
            item = next((row[k] for k in row if re.search(r'(?i)^(product|item|sku|description|name)$', k) and row[k]), '')
            for k, v in row.items():
                if item and re.search(r'(?i)price|rate|unit', k) and MONEY.match(v):
                    prices[item.lower()][f"${float(v.replace('$', '').replace(',', '').strip()):,.2f}"].add(rel)
    found = 0
    for key, kind in ((by_email, 'email'), (by_phone, 'phone number')):
        for value, hits in sorted(key.items()):
            names = {h[0] for h in hits}
            if len(names) > 1:
                found += 1
                print(f'Duplicate contact? The same {kind} is on {len(names)} rows: ' + '; '.join(sorted(f'{n} ({f})' for n, f in hits)))
    for item, vals in sorted(prices.items()):
        if len(vals) > 1:
            found += 1
            print(f'Price clash? "{item}" is priced ' + '; '.join(f'{p} in {", ".join(sorted(fs))}' for p, fs in sorted(vals.items())))
    for path in files:
        if OLD.search(path.stem.replace('_', ' ').replace('-', ' ')):
            found += 1
            print(f'Possible old copy: {path.name}. Is it history, or still current?')
    print(f'{found} thing(s) to raise with the owner.' if found else 'Nothing mechanical to raise. Still check discounts, payments and dates by reading.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
