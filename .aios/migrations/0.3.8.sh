#!/bin/sh
# 0.3.8: "never touch accounting" read as "never look". The never-list line now says change, not touch:
# reading invoices and reports from connected bookkeeping or payments is fine; changing a record is not.
# Only the exact old line is replaced, so an owner's own wording is left alone.
f=company/permissions.md
[ -f "$f" ] || exit 0
grep -qx -- '- Touch banking, accounting, payroll or pay.' "$f" || exit 0
tmp="$f.tmp.$$"
awk '$0=="- Touch banking, accounting, payroll or pay." {print "- Change anything in banking, accounting, payroll or pay. (Reading invoices, reports and totals"; print "  is fine once you connect them; it never changes a record or saves a card or bank number.)"; next} {print}' "$f" > "$tmp" && mv "$tmp" "$f"
