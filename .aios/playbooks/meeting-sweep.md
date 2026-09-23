# Meeting sweep — file recorded meetings automatically

Runs on a schedule (see `.aios/routines/meeting-sweep.md`) with the owner's meeting recorder
connected (Fathom today; anything that records Zoom, Google Meet or Teams calls and exposes a
connector). Nothing is sent anywhere. Everything filed is marked `imported` until the owner confirms.

## Each run

1. Read `memory/filed-meetings.md`. Every recording already listed there is done; skip it.
2. List recordings from the last 3 days. For each one not yet filed, read the summary and the
   transcript. Every claim about what was said comes from the transcript, not from memory.
3. Route by attendees, using the table below. Read `company/people.md` for teammates and
   `clients/*/meta.yml` for client contacts and email domains.
4. Extract: decisions and why; promises (who, what, by when; undated promises get a proposed date
   marked "proposed"); new facts (numbers, needs, objections); the single next step; the next
   meeting if booked. Do not paste transcripts into the brain; link the recording and summarise.
5. Screen against `company/access.md`. Anything on the private list is not written; note "not saved
   here" in the receipt.
6. File it. Facts carry source (recorder link), date and status `imported`. Promises go to
   `memory/follow-ups.md`. Add a dated row to the destination's ledger and update its `meta.yml`
   in the same save.
7. Append a row to `memory/filed-meetings.md`: date, title, attendees, where it was filed, link.
8. Write the receipt `memory/receipts/meeting-sweep.json`: run time, recordings seen, filed,
   skipped, errors. A run with no receipt did not happen.
9. Save (`sh .aios/hooks/autosave.sh`).
10. Message the owner only if something needs them: an unknown attendee to route, a promise with
    no date, or a recorder that could not be reached. Otherwise stay silent; the weekly review
    carries the summary.

## Routing

| Who was in the meeting | Where it goes |
|---|---|
| A contact or email domain that matches a client or prospect folder | `clients/<name>/` (ledger row, facts, meta) |
| A person listed in `company/people.md` (teammate, contractor) | `memory/operations/<date>-<topic>.md` and `memory/decisions.md` for decisions |
| A supplier or partner named in `company/tools.md` or `company/customers.md` | `memory/operations/` |
| Nobody the brain knows | `inbox/<date>-<title>.md` with a one-line question to the owner: who is this and where should it live? |
| The owner alone (a voice memo) | `memory/imported/<date>-memo.md` |

## Never

- Send, reply or post. This job reads and files.
- Mark anything `confirmed`. Only the owner does that.
- Guess a destination. Unknown goes to the inbox with a question.
