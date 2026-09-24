# Migrations

One script per engine version that changes where the owner's files live: `0.2.0.sh`, `0.3.0.sh`.
`/upgrade` runs every script whose version is newer than the installed one, oldest first, after
the engine folder is replaced and before the checks. A script moves or renames the owner's files;
it never deletes content and never edits the meaning of a fact. Test each one on a sample brain
before release.
