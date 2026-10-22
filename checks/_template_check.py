#!/usr/bin/env python3
"""Template for your own check. Copy to checks/check_<what>.py and edit main().

Rules of a check (scripts/verify.py relies on them):
  1. print one problem per line, then a last summary line with numbers
  2. exit 1 if there is any problem, 0 otherwise
  3. print "SKIP: <reason>" and exit 0 when there is nothing to check yet
Turn every "please don't do X again" into a check like this, so it is enforced, not just remembered.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    problems = []
    # Example: every file in out/ must be non-empty.
    # for f in os.listdir(os.path.join(ROOT, "out")):
    #     if os.path.getsize(os.path.join(ROOT, "out", f)) == 0:
    #         problems.append(f"out/{f}: empty file")
    for p in problems:
        print(p)
    print(f"{len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
