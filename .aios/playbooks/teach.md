# /teach — teach the brain a task

Turns a task the owner hates into a reusable command, written in the owner's words.

1. Ask the owner to describe the task the way they would tell a new hire: when it comes up, what a
   good result looks like, what goes wrong, who is involved, which files or tools it touches.
2. Copy `.aios/templates/skill.md` to `skills/<name>.md`. Name it the way the owner says it
   ("chase-quotes", not "follow-up-automation").
3. Write the steps in plain English. Every step that drafts something says "draft"; nothing in a
   taught task sends, spends or deletes.
4. Add a matching one-line adapter at `.claude/commands/<name>.md` pointing to the skill file.
5. Run it once on real material with the owner watching. Fix what the run shows. Save.
6. Record it in `skills/README.md` with one line on when to use it.
