"""Shared helpers for the harness hooks (config, logging, project root).

Standard library only. Every hook reads the JSON payload Claude Code sends on stdin.
"""
import csv
import datetime
import json
import os
import sys

HOOK_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_CONFIG = {
    # Command that defines "done". The Stop gate runs it whenever files changed this turn.
    "verify_command": "python3 scripts/verify.py",
    # Folders/files the agent may read but never write (relative to the project root).
    "protected_paths": ["raw/", "specs/", "_archive/", ".env"],
    # Bash guard rule ids to switch off, e.g. ["G7"] if you never run sessions in parallel.
    "bash_rules_off": [],
    # How many times the Stop gate may send the agent back in one turn before handing over to you.
    "max_stop_blocks": 3,
}


def project_dir(payload=None):
    d = os.environ.get("CLAUDE_PROJECT_DIR")
    if not d and payload:
        d = payload.get("cwd")
    return os.path.abspath(d or os.getcwd())


def load_config(root):
    cfg = dict(DEFAULT_CONFIG)
    path = os.path.join(root, "harness.json")
    try:
        with open(path, encoding="utf-8") as f:
            cfg.update(json.load(f))
    except FileNotFoundError:
        pass
    return cfg


def read_payload():
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def log_event(root, hook, decision, rule, detail):
    """Append one row to .claude/hooks/harness_log.csv so you can count what the harness caught."""
    path = os.path.join(root, ".claude", "hooks", "harness_log.csv")
    new = not os.path.exists(path)
    try:
        with open(path, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["time", "hook", "decision", "rule", "detail"])
            w.writerow([
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                hook, decision, rule, detail[:300].replace("\n", " "),
            ])
    except OSError:
        pass
