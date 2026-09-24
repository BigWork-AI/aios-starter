#!/usr/bin/env python3
"""Write or check the receipt of a scheduled job. No receipt, no run.

  python3 .aios/tools/receipt.py write JOB --status ok|needs-owner|failed [--count key=N ...] [--note "..."]
  python3 .aios/tools/receipt.py check JOB [--max-age-days 2]

`write` saves memory/receipts/JOB.json (run time, status, counts, note) and appends one line to
memory/receipts/log.md, the running history. `check` prints one plain sentence about the last run
and exits 0 when it is fresh and ok, 1 when it is stale, missing, failed or waiting on the owner.
The weekly review and the front page read `check`; a configured schedule is not evidence.
"""
import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECEIPTS = ROOT / 'memory/receipts'
STATUSES = ('ok', 'needs-owner', 'failed')


def write(job: str, argv: list) -> int:
    status, counts, note = None, {}, ''
    i = 0
    while i < len(argv):
        if argv[i] == '--status':
            status = argv[i + 1]; i += 2
        elif argv[i] == '--count':
            key, _, value = argv[i + 1].partition('=')
            counts[key] = int(value); i += 2
        elif argv[i] == '--note':
            note = argv[i + 1]; i += 2
        else:
            print(f'Unknown option {argv[i]}'); return 2
    if status not in STATUSES:
        print('--status must be one of ok, needs-owner, failed'); return 2
    now = datetime.datetime.now().astimezone().replace(microsecond=0)
    receipt = {'job': job, 'ran_at': now.isoformat(), 'status': status, 'counts': counts, 'note': note}
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    (RECEIPTS / f'{job}.json').write_text(json.dumps(receipt, indent=2) + '\n')
    log = RECEIPTS / 'log.md'
    if not log.exists():
        log.write_text('# Job history\n\nOne line per run, newest last. Written by the receipt tool, never by hand.\n\n')
    summary = ', '.join(f'{k} {v}' for k, v in counts.items()) or 'no counts'
    with log.open('a') as f:
        f.write(f'- {now.isoformat()} {job}: {status} ({summary}){" " + note if note else ""}\n')
    print(f'Receipt written for {job}: {status}, {summary}.')
    return 0


def check(job: str, argv: list) -> int:
    max_age = 2.0
    if '--max-age-days' in argv:
        max_age = float(argv[argv.index('--max-age-days') + 1])
    path = RECEIPTS / f'{job}.json'
    if not path.exists():
        print(f'{job}: has never run (no receipt).'); return 1
    try:
        receipt = json.loads(path.read_text())
        ran_at = datetime.datetime.fromisoformat(receipt['ran_at'])
    except (ValueError, KeyError):
        print(f'{job}: the receipt is unreadable; treat the job as not running.'); return 1
    age = datetime.datetime.now().astimezone() - ran_at
    days = age.total_seconds() / 86400
    when = ran_at.strftime('%Y-%m-%d %H:%M')
    summary = ', '.join(f'{k} {v}' for k, v in receipt.get('counts', {}).items()) or 'no counts'
    status = receipt.get('status', 'unknown')
    if days > max_age:
        print(f'{job}: last ran {when}, {days:.1f} days ago; it has gone quiet.'); return 1
    if status == 'ok':
        print(f'{job}: ran {when} ({summary}).'); return 0
    if status == 'needs-owner':
        print(f'{job}: ran {when} and needs the owner: {receipt.get("note") or "see the review folder"}.'); return 1
    print(f'{job}: ran {when} and failed: {receipt.get("note") or "no reason recorded"}.'); return 1


def main(argv: list) -> int:
    if len(argv) < 2 or argv[0] not in ('write', 'check'):
        print(__doc__); return 2
    return write(argv[1], argv[2:]) if argv[0] == 'write' else check(argv[1], argv[2:])


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
