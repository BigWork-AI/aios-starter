#!/usr/bin/env python3
"""Find facts in the brain that may have gone stale, for the weekly review.

  python3 .aios/tools/freshness.py [--today YYYY-MM-DD] [--all]

Reads every fact table (| Fact | Value | Source | Date | Status |) under company/ and clients/ and
lists, money and terms first (prices, discounts, lead times, payment terms), then by kind:

  disagree       the same fact written twice with different values
  unconfirmed    imported or inferred facts older than 14 days that nobody has confirmed
  old            confirmed facts older than 180 days (prices, people, terms change)
  undated        facts with no usable date

It changes nothing. The weekly review reads the list back to the owner as questions, at most five,
and writes each answer with today's date.
"""
import datetime
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UNCONFIRMED_DAYS, OLD_DAYS, SHOW = 14, 180, 12
MONEY_WORDS = re.compile(r'(?i)price|cost|rate|fee|discount|term|deposit|margin|lead time|shipping|minimum|payment|invoice|\$')


def tables(path: Path):
    head = None
    for line in path.read_text(errors='ignore').splitlines():
        if not line.strip().startswith('|'):
            head = None
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if head is None:
            low = [c.lower() for c in cells]
            if {'fact', 'value', 'date', 'status'} <= set(low):
                head = low
            continue
        if set(''.join(cells)) <= set('-: '):
            continue
        row = dict(zip(head, cells))
        if row.get('status', '').lower() == 'example':
            continue
        yield row


def main(argv):
    today = datetime.date.today()
    if '--today' in argv:
        today = datetime.date.fromisoformat(argv[argv.index('--today') + 1])
    found = defaultdict(list)  # category -> [(fact, line)]
    values = defaultdict(set)
    for path in sorted(list(ROOT.glob('company/*.md')) + list(ROOT.glob('clients/**/*.md'))):
        rel = path.relative_to(ROOT)
        for row in tables(path):
            fact, value = row.get('fact', ''), row.get('value', '')
            if not fact or not any(row.get(k, '').strip() for k in ('value', 'source', 'date', 'status')):
                continue  # a blank template row waiting to be filled, not a fact
            values[(str(rel), fact.lower())].add(value)
            status = row.get('status', '').lower()
            try:
                age = (today - datetime.date.fromisoformat(row.get('date', '')[:10])).days
            except ValueError:
                found['undated'].append((fact, f'{fact} ({rel}) has no date. When was it last true?'))
                continue
            if status in ('imported', 'inferred') and age > UNCONFIRMED_DAYS:
                found['unconfirmed'].append((fact, f'{fact}: "{value}" ({rel}, {status} {age} days ago from {row.get("source", "?")}). Still right?'))
            elif status == 'confirmed' and age > OLD_DAYS:
                found['old'].append((fact, f'{fact}: "{value}" ({rel}, confirmed {age} days ago). Still true?'))
    for (rel, fact), vals in sorted(values.items()):
        if len(vals) > 1:
            found['disagree'].append((fact, f'{fact} ({rel}) is written {len(vals)} ways: ' + ' / '.join(sorted(vals)) + '. Which is right?'))
    # Rank before cutting the list: money and terms first (they cost the most when wrong), then by kind.
    order = ('disagree', 'unconfirmed', 'old', 'undated')
    ranked = sorted(((0 if MONEY_WORDS.search(fact) else 1, order.index(k), f'[{k}] {line}')
                     for k in order for fact, line in found[k]), key=lambda r: (r[0], r[1]))
    lines = [r[2] for r in ranked]
    show = len(lines) if '--all' in argv else SHOW
    for line in lines[:show]:
        print(line)
    if len(lines) > show:
        print(f'...and {len(lines) - show} more (run with --all to see them).')
    print(f'{len(lines)} fact(s) to check with the owner.' if lines else 'Everything in the brain is dated, confirmed recently, and agrees with itself.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
