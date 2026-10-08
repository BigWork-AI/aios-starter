#!/usr/bin/env python3
"""Coach notes for the owner, for the weekly review.

  python3 .aios/tools/coach.py [--today YYYY-MM-DD] [--days 7]

Looks back over the last week using only what the brain already keeps, and writes a few plain
lines under "Going well" and "Worth a look", each with the number behind it:

  memory/follow-ups.md   promises kept on time, promises gone overdue, due dates pushed forward
  memory/actions.md      what the brain did for you in your connected accounts
  saved history (git)    where the week's work went (customers, your business facts, skills,
                         notes and meetings) and how many saves landed late at night

It sees only work that reached the brain. Calls, texts, DMs, meetings nobody filed and anything
done outside Claude are invisible to it, and a save time is when a chat saved, not proof of when
you worked. Every line is a prompt for a conversation, not a verdict. No screen recording, no
keystrokes, no mailbox reading. It changes nothing.
"""
import datetime
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATE = re.compile(r'\d{4}-\d{2}-\d{2}')
AREAS = [('customers', ('clients/',)), ('your business facts', ('company/',)),
         ('skills', ('.claude/skills/', 'skills/')), ('notes and meetings', ('memory/', 'inbox/'))]


def area(path: str):
    for name, prefixes in AREAS:
        if path.startswith(prefixes):
            return name
    return None  # engine and setup files are not the owner's work


def day(text: str):
    m = DATE.search(text or '')
    return datetime.date.fromisoformat(m.group()) if m else None


def table(path: Path):
    """Rows of the first table in a file, as dicts keyed by lower-case header. Blank rows skipped."""
    if not path.exists():
        return []
    head, rows = None, []
    for line in path.read_text(errors='ignore').splitlines():
        if not line.strip().startswith('|'):
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if head is None:
            head = [c.lower() for c in cells]
        elif not set(''.join(cells)) <= set('-: '):
            rows.append(dict(zip(head, cells)))
    return rows


def saves(since: datetime.date, until: datetime.date):
    try:
        out = subprocess.run(['git', '-C', str(ROOT), 'log', '--no-merges', '--name-only', '--date=iso-strict', '--format=@@%ad'],
                             capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    result = []
    for block in out.split('@@')[1:]:
        lines = [l for l in block.splitlines() if l.strip()]
        if not lines:
            continue
        when = datetime.datetime.fromisoformat(lines[0])  # the owner's own clock, as saved
        if not since <= when.date() <= until:  # filtered here: git's --since stops at the first older save
            continue
        areas = Counter(a for a in map(area, lines[1:]) if a)
        if areas:
            result.append((when, areas.most_common(1)[0][0]))
    return result


def pct(n, total):
    return round(100 * n / total) if total else 0


def main(argv):
    today = datetime.date.fromisoformat(argv[argv.index('--today') + 1]) if '--today' in argv else datetime.date.today()
    days = int(argv[argv.index('--days') + 1]) if '--days' in argv else 7
    start = today - datetime.timedelta(days=days - 1)

    rows = []
    for r in table(ROOT / 'memory/follow-ups.md'):
        what = r.get('what') or r.get('item') or ''
        status = (r.get('status') or '').split()[0].upper() if r.get('status') else ''
        if what or status:
            rows.append({'what': what, 'due': day(r.get('due', '')), 'status': status, 'closed': day(r.get('status', ''))})
    closed = [r for r in rows if r['status'] == 'DONE' and r['closed'] and start <= r['closed'] <= today]
    on_time = [r for r in closed if r['due'] and r['closed'] <= r['due']]
    late = [r for r in closed if r['due'] and r['closed'] > r['due']]
    overdue = sorted((r for r in rows if r['status'] not in ('DONE', 'DROPPED') and r['due'] and r['due'] < today), key=lambda r: r['due'])
    pushed = [r for r in rows if r['status'] not in ('DONE', 'DROPPED') and re.search(r'(?i)\b(pushed|moved to|rescheduled)\b', r['what'])]
    actions = [r for r in table(ROOT / 'memory/actions.md') if day(r.get('when', '')) and start <= day(r['when']) <= today]

    history = saves(start, today)
    by_area = Counter(a for _, a in history or [])
    total = sum(by_area.values())
    late_night = [w for w, _ in history or [] if w.hour >= 22 or w.hour < 5]

    good, look = [], []
    if on_time:
        good.append(f'Kept {len(on_time)} promise(s) on or before the day they were due ({", ".join(r["what"][:40] for r in on_time[:3])}).')
    if actions:
        good.append(f'The brain did {len(actions)} thing(s) for you in your accounts this week (see memory/actions.md).')
    if total:
        top, n = by_area.most_common(1)[0]
        good.append(f'{total} saves this week; most went to {top} ({pct(n, total)}%).')
    if rows and not overdue:
        good.append('Nothing on your follow-up list is overdue.')

    if overdue:
        oldest = overdue[0]
        look.append(f'{len(overdue)} follow-up(s) past due. Oldest: {oldest["what"][:60]}, {(today - oldest["due"]).days} days late.')
    if late:
        look.append(f'{len(late)} promise(s) kept, but after the day they were due.')
    if total and overdue and pct(by_area.get('customers', 0), total) < 20:
        look.append(f'Only {pct(by_area.get("customers", 0), total)}% of saves touched customers while {len(overdue)} follow-up(s) sit overdue.')
    if pushed:
        look.append(f'{len(pushed)} open follow-up(s) already had the date moved ({", ".join(r["what"][:40] for r in pushed[:3])}).')
    if len(late_night) >= 3:
        look.append(f'{len(late_night)} saves landed between 10pm and 5am.')

    print(f'Coach notes, {start.isoformat()} to {today.isoformat()}')
    print('Going well:')
    for line in good or ['Nothing the files can show yet.']:
        print(f'  + {line}')
    print('Worth a look:')
    for line in look or ['Nothing the files flag.']:
        print(f'  - {line}')
    if total:
        print('Where the saves went: ' + ', '.join(f'{name} {pct(n, total)}%' for name, n in by_area.most_common()) + '.')
    print('Seen: your follow-up list, the action log and saved history. Not seen: calls, texts, DMs, '
          'meetings nobody filed, work outside Claude. Ask before drawing a conclusion.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
