# Setting up the follow-ups routine

The first recurring job most owners approve: every weekday morning, the brain prepares a chaser
for every quote, proposal or question the other side has left unanswered, in the owner's voice,
and leaves the drafts in `inbox/review/`. The owner sends, changes or drops each one. It runs
`.aios/playbooks/follow-ups.md`.

## Why it is repository-only

Inside a scheduled routine on a Pro or Max plan, connector writes (sending a mail, changing a
calendar event) happen **without an approval prompt**. A playbook that says "never send" is a
request, not a control. So this routine gets one connection only: the brain's own repository.
It cannot send because it has no way to. That is the right start: the owner's permissions page
(`company/permissions.md`) is empty on day one.

**When the owner wants it to send on its own.** Only after a line on the permissions page allows
exactly that (for example "send follow-ups to customers who asked for a quote, at most two per
customer") and marks it "when I am away". Then the routine may be given the email connection, its
prompt names that one permission line, every send is written to `memory/actions.md`, and the
receipt counts sends. On Pro and Max nothing stops a routine that goes beyond its line, so keep
the line narrow and read the action log in the weekly review. Connector-fed routines are for Team or Enterprise plans
where an admin blocks the write categories, or for a later Anthropic release with read-only
routine scopes.

## Setup (done by BigWork during the install, with the owner watching)

1. The owner names the job out loud and approves its scope: "prepare my follow-ups every weekday
   morning; I send them." Write that sentence into `AGENTS.md` under the house rules with the date.
2. Create a routine at claude.ai (Routines) with:
   - Schedule: weekdays, one run, early morning in the owner's time zone.
   - Fresh session each run, with **this brain's repository and no other connector**. Check the
     connector list on the routine before saving it: repository only.
   - Prompt: "Open the brain, read AGENTS.md, then run .aios/playbooks/follow-ups.md exactly.
     You have no connections outside this repository and must not ask for any. Draft only. Write
     the receipt with the receipt tool, then save."
3. Run it once by hand with the owner watching. Then, together, open `inbox/review/` and read
   one draft aloud. Check: is it accurate, is it their voice, would they send it, is it in the
   right place, did anything in the brain need updating. Fix the voice notes in `AGENTS.md` if
   the voice is off, and run it again.
4. Write the pilot log line: the run time, the counts from the receipt, and the owner's verdict on
   the draft.

## The evidence rule

A routine is not working because it exists. `python3 .aios/tools/receipt.py check follow-ups`
must say it ran within the last two days with counts. The weekly review runs that check and says
plainly if the job has gone quiet, needs the owner, or failed. Nothing is called working until a
fresh receipt exists **and** a person has read the actual output.

## What the owner sees

- A run that prepared drafts: files in `inbox/review/`, listed on the front page under "Ready for
  your review".
- A run that needs them: the receipt says `needs-owner` and names what is missing; the front
  page lists it under "Questions for you".
- A run that could not run: the receipt says `failed` with the reason, or there is no fresh
  receipt at all; the weekly review says so at the top.
