#!/bin/sh
# 0.3.15: the pipeline page. Build clients/pipeline.md from the client cards so the owner has one
# generated, never-stale view of clients, prospects, partners and past relationships. Safe to run
# twice; creates one file inside the brain and changes nothing else.
set -eu
python3 .aios/tools/pipeline.py >/dev/null
