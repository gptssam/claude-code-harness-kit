#!/usr/bin/env python3
"""Run every checks/check_*.py and print one PASS/FAIL line each.

This is the project's definition of "done": the Stop hook runs it, and humans can too.
    python3 scripts/verify.py            # all checks
    python3 scripts/verify.py titles     # only checks whose name contains "titles"

A check is any Python file in checks/ named check_*.py that
  - exits 0 to pass, 1 to fail, and prints its problems one per line,
  - prints a last line that summarises what it measured (e.g. "10 titles, 0 problems"),
  - may print "SKIP: <reason>" as its last line and exit 0 when it has nothing to check.
Standard library only.
"""
import glob
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    checks = sorted(p for p in glob.glob(os.path.join(ROOT, "checks", "check_*.py")) if only in os.path.basename(p))
    if not checks:
        print("RESULT 0/0 — checks/ 폴더에 check_*.py가 없습니다.")
        return 1
    t0 = time.time()
    passed = failed = skipped = 0
    print(f"[verify] {len(checks)} checks")
    for path in checks:
        name = os.path.basename(path)[:-3]
        r = subprocess.run([sys.executable, path], cwd=ROOT, capture_output=True, text=True, timeout=120)
        lines = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
        last = lines[-1] if lines else ""
        if r.returncode == 0 and last.startswith("SKIP"):
            skipped += 1
            print(f"SKIP  {name:<24} {last[5:].strip()}")
        elif r.returncode == 0:
            passed += 1
            print(f"PASS  {name:<24} {last}")
        else:
            failed += 1
            print(f"FAIL  {name:<24} {last}")
            for l in lines[:-1][:20]:
                print(f"      - {l}")
    total = passed + failed
    print(f"RESULT {passed}/{total} PASS ({failed} FAIL, {skipped} SKIP) in {time.time() - t0:.2f}s")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
