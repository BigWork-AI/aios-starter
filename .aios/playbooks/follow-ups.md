# Follow-ups — prepare the chasers for anything left unanswered

Runs on a schedule (see `.aios/routines/follow-ups.md`). **Repository-only:** this job reads and
writes the brain's own files and nothing else. No email, calendar or drive connection is attached
to it, so it cannot send, and it must not try. Everything it prepares waits in `inbox/review/`
for the owner.

## Each run

1. Read `AGENTS.md` (the house rules and the owner's voice notes) and `company/voice.md` if it
   exists. Every draft is written in the owner's voice, not a generic one.
2. Read every `clients/*/meta.yml` and `memory/follow-ups.md`. Build the list of what is waiting:
   - a `next_action` whose `next_action_due` is today or past;
   - a client or prospect with `last_touch` more than 7 days ago and a `next_action` that is a
     quote, proposal or question the other side has not answered;
   - a follow-up row that is due or overdue and not DONE.
3. Skip anything already drafted: a file in `inbox/review/` for the same client and the same
   next action, not yet cleared by the owner. One draft per open item, never a pile.
4. For each item, write `inbox/review/YYYY-MM-DD-<client>-follow-up.md`:
   - what this is about, in one line, with the source row or file;
   - the draft message, ready to paste, in the owner's voice, using only facts with a status
     (a quoted price is used only if its row is `confirmed`; an `imported` price is left as a
     bracket for the owner);
   - what the owner needs to do: send it, change it, or drop it.
5. Do not change any client's `meta.yml`, ledger or follow-up row. Preparing a draft is not a
   touch. The owner's yes and the send are what move a relationship, and those happen outside
   this job.
6. Write the receipt: `python3 .aios/tools/receipt.py write follow-ups --status ok --count
   drafted=N --count skipped=M --count waiting=K`, where `waiting` is the number of drafts still
   sitting in the review folder from earlier runs. Use `--status needs-owner --note "..."` when
   a draft could not be written without a fact only the owner has (a missing price, an unknown
   contact), and `--status failed --note "..."` when the run could not read the brain. A run with
   no receipt did not happen.
7. Save (`sh .aios/hooks/autosave.sh`).

## Never

- Send, reply, post or connect to anything outside the brain. This job has no way to, and must
  not ask for one.
- Mark anything `confirmed`, close a follow-up, or update `last_touch`. Only the owner's actions do
  that.
- Invent a price, a date or a name. A gap becomes a bracket in the draft and a `needs-owner` receipt.
