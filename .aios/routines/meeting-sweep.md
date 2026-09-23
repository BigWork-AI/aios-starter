# Setting up the meeting sweep

The sweep is a scheduled job that runs `.aios/playbooks/meeting-sweep.md`. It needs two things:
the owner's meeting recorder connected to their Claude account, and a schedule.

## Friends-week setup (done by BigWork during the install)

1. In the owner's Claude account, connect the meeting recorder (Fathom) and GitHub.
2. Create a routine at claude.ai (Routines) with:
   - Schedule: every 30 minutes during business hours, or hourly.
   - Fresh session each run, in an environment with this brain's repository.
   - Connectors: the meeting recorder and GitHub.
   - Prompt: "Open the brain, read AGENTS.md, then run .aios/playbooks/meeting-sweep.md exactly.
     Read-only outside the repository. File what is new, write the receipt, save, and message the
     owner only if something needs them."
3. Run it once by hand with the owner watching. Confirm a real meeting landed in the right folder
   and the receipt exists.

## The evidence rule

A routine is not working because it exists. `memory/receipts/meeting-sweep.json` must show a run
in the last day with real counts. The weekly review reads that receipt and says so plainly if the
sweep has gone quiet.
