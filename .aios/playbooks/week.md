# /week — the weekly review

1. Read every `clients/*/meta.yml` and `memory/follow-ups.md`. List: promises overdue; clients with no movement in 14 days; next actions with no date.
2. Read `memory/receipts/upgrade-check.json`. If the engine was updated this week, one line at the top of the review says so with what changed. If the last check is older than seven days, or its result is `deferred-unsaved-work` or `failed-checks-rolled-back`, say so plainly and run `/upgrade`. Then read `memory/decisions.md` and last week's review in `memory/reviews/` if present. Run `python3 .aios/tools/receipt.py check meeting-sweep` and `python3 .aios/tools/receipt.py check follow-ups`: any job that has gone quiet, failed or is waiting on the owner goes at the top of the review; a quiet job is a finding, not a footnote. Read `inbox/review/` and list what is still waiting on the owner. Read this week's rows in `memory/actions.md` and list everything the brain did on its own, each with the permission that allowed it; anything that does not match a line in `company/permissions.md` goes at the top as a problem. Ask once whether any permission should be added or taken off.
3. **Freshness check.** Run `python3 .aios/tools/freshness.py`. It lists facts that disagree with
   each other, imported or guessed facts nobody has confirmed after 14 days, confirmed facts older
   than six months, and facts with no date. Ask the owner about the top five at most, one at a
   time, most costly first (prices and terms before names). Write each answer with today's date and
   `confirmed`; move what is no longer true to a "History" note in the same file with its old date,
   never delete it. Say how many are left for next week.
4. Ask the owner, one at a time, about anything the files cannot see: calls, texts, DMs, handshakes. Silence in the files is not silence in real life. Write the answers as `confirmed` facts.
5. Write `memory/reviews/YYYY-MM-DD.md`: what moved, what is stuck, the three things for next week, each with a date and an owner. Decisions taken during the review go to `memory/decisions.md`.
6. Close finished follow-ups (DONE with date) and add new ones.
7. Report in the house style: one line, three bullets, the one risk, next week's first action. Then save (`sh .aios/hooks/autosave.sh`).
