#!/bin/sh
# 0.3.12: the access page says where live-review ticks and notes are stored. Inserted once as a
# marked block, only if absent; the owner's own bytes are never rewritten. A missing access page is
# left alone. Any failure exits non-zero so the updater puts every file back.
set -e
# The brain that runs this upgrade still uses its old updater, which knows nothing of the "what's new"
# page; this migration says it once, so the first owners hear about the page at the install itself.
if [ -s .aios/whats-new.url ]; then echo "  Something new arrived. Read what it does and one thing to try: $(head -1 .aios/whats-new.url)"; fi
[ -f company/access.md ] || exit 0
grep -q "<!-- aios:live-review-storage -->" company/access.md && exit 0
python3 - <<'PY'
from pathlib import Path
p = Path("company/access.md"); raw = p.read_bytes()
block = (b"<!-- aios:live-review-storage -->\n"
         b"The live review page is a web page hosted by Anthropic (a Claude page). The ticks and notes you\n"
         b"type on it are stored by that service, and the page keeps them as history after Send copies your\n"
         b"decisions into this brain. Nothing private belongs on the page: treat it like a whiteboard in the\n"
         b"office, not like this brain.\n"
         b"<!-- /aios:live-review-storage -->\n")
marker = b"Added by the owner during `/start`:"
i = raw.find(marker)
if i >= 0:
    out = raw[:i] + block + b"\n" + raw[i:]
else:
    out = raw + (b"" if raw.endswith(b"\n") else b"\n") + b"\n" + block
tmp = p.with_suffix(".md.aios-tmp"); tmp.write_bytes(out); tmp.replace(p)
PY
