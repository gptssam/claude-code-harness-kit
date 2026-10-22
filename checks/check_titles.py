#!/usr/bin/env python3
"""Demo deliverable check: demo/titles.csv must follow specs/titles_spec.json.

This is the "exam" the agent cannot grade itself on. The spec lives in specs/, which the
write guard keeps read-only, so the agent has to fix the titles — not the rules.
"""
import csv
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(ROOT, "specs", "titles_spec.json")
OUT = os.path.join(ROOT, "demo", "titles.csv")


def main():
    if not os.path.exists(OUT):
        print("SKIP: demo/titles.csv not written yet")
        return 0
    spec = json.load(open(SPEC, encoding="utf-8"))
    with open(OUT, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    problems = []
    if not rows or [c.strip() for c in rows[0]] != spec["header"]:
        problems.append(f"header must be {','.join(spec['header'])} (got {','.join(rows[0]) if rows else 'empty file'})")
    body = [r for r in rows[1:] if any(c.strip() for c in r)]
    if len(body) != spec["count"]:
        problems.append(f"need exactly {spec['count']} rows, got {len(body)}")
    seen = set()
    for i, r in enumerate(body, 1):
        if len(r) != len(spec["header"]):
            problems.append(f"row {i}: {len(r)} columns, need {len(spec['header'])}")
            continue
        no, title = r[0].strip(), r[1].strip()
        if no != str(i):
            problems.append(f"row {i}: no must be {i} (got {no!r})")
        n = len(title)
        if n > spec["max_chars"]:
            problems.append(f"row {i}: {n} chars > {spec['max_chars']} — {title}")
        if n < spec["min_chars"]:
            problems.append(f"row {i}: {n} chars < {spec['min_chars']} — {title}")
        if spec.get("need_digit") and not re.search(r"\d", title):
            problems.append(f"row {i}: no number — {title}")
        for w in spec["banned"]:
            if w in title:
                problems.append(f"row {i}: banned word {w!r} — {title}")
        if title in seen:
            problems.append(f"row {i}: duplicate title — {title}")
        seen.add(title)
    for p in problems:
        print(p)
    print(f"{len(body)} titles, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
