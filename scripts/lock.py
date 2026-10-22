#!/usr/bin/env python3
"""One-at-a-time lock for things several agent sessions share (an account, a GPU, a render slot).

Why: two sessions sent jobs to the same AI video account at the same moment and the
service flagged "unusual activity". Each session only saw its own screen. A lock file
that every session checks makes the overlap visible.

    python3 scripts/lock.py acquire video session-A --note "4 clips"   # waits while someone else holds it
    python3 scripts/lock.py release video session-A
    python3 scripts/lock.py status

Exit codes: 0 = you hold it · 1 = waited too long (run again) · 2 = lock looks stale (ask a person, don't delete it)
The lock lives in ~/.harness_locks (shared by every folder and worktree on this computer;
set HARNESS_LOCK_DIR to change it). Every acquire/release is appended to lock_log.csv there.
"""
import argparse
import csv
import datetime
import json
import os
import sys
import time

LOCKDIR = os.path.expanduser(os.environ.get("HARNESS_LOCK_DIR", "~/.harness_locks"))
STALE_MIN = 30


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def path(name):
    return os.path.join(LOCKDIR, f"{name}.lock")


def info(name):
    try:
        return json.load(open(os.path.join(path(name), "info.json")))
    except Exception:
        return None


def log(action, name, session, note=""):
    p = os.path.join(LOCKDIR, "lock_log.csv")
    new = not os.path.exists(p)
    with open(p, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time", "action", "lock", "session", "note"])
        w.writerow([now(), action, name, session, note])


def acquire(name, session, note, wait):
    os.makedirs(LOCKDIR, exist_ok=True)
    t0, shown = time.time(), None
    while True:
        try:
            os.mkdir(path(name))  # atomic: only one process can create it
            json.dump({"session": session, "since": time.time(), "since_s": now(), "note": note},
                      open(os.path.join(path(name), "info.json"), "w"))
            log("acquire", name, session, note)
            print(f"LOCKED {name}: {session}")
            return 0
        except FileExistsError:
            i = info(name)
            if i and i.get("session") == session:
                print(f"LOCKED {name}: {session} (already yours since {i['since_s']})")
                return 0
            if i and time.time() - i["since"] > STALE_MIN * 60:
                print(f"STALE {name}: held by {i['session']} since {i['since_s']} (> {STALE_MIN} min). "
                      "Do not delete it yourself — ask a person.")
                return 2
            holder = f"{i['session']} since {i['since_s']}" if i else "unknown"
            if holder != shown:
                print(f"WAIT {name}: held by {holder}")
                shown = holder
            if time.time() - t0 > wait:
                print(f"TIMEOUT {name}: still held by {holder} after {wait}s — you do NOT hold the lock")
                return 1
            time.sleep(5)


def release(name, session):
    i = info(name)
    if not i:
        print(f"FREE {name}: nothing to release")
        return 0
    if i.get("session") != session:
        print(f"REFUSED {name}: held by {i['session']}, not {session}")
        return 1
    os.remove(os.path.join(path(name), "info.json"))
    os.rmdir(path(name))
    log("release", name, session)
    print(f"RELEASED {name}: {session}")
    return 0


def status():
    if not os.path.isdir(LOCKDIR):
        print("no locks")
        return 0
    held = [f[:-5] for f in sorted(os.listdir(LOCKDIR)) if f.endswith(".lock")]
    for name in held:
        i = info(name) or {}
        print(f"{name}: {i.get('session', '?')} since {i.get('since_s', '?')} {i.get('note', '')}")
    if not held:
        print("no locks")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["acquire", "release", "status"])
    ap.add_argument("name", nargs="?")
    ap.add_argument("session", nargs="?")
    ap.add_argument("--note", default="")
    ap.add_argument("--wait", type=int, default=900, help="seconds to wait before giving up")
    a = ap.parse_args()
    if a.action == "status":
        return status()
    if not (a.name and a.session):
        ap.error("acquire/release need <name> <session>")
    return acquire(a.name, a.session, a.note, a.wait) if a.action == "acquire" else release(a.name, a.session)


if __name__ == "__main__":
    sys.exit(main())
