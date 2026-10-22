#!/usr/bin/env python3
"""Fail if an API key, private key or a personal home path is about to be shared.

Scans every text file in the project except .git/, _archive/ and the hook log.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", "_archive", "node_modules", "__pycache__", ".state"}
SKIP_FILES = {"harness_log.csv"}
PATTERNS = [
    ("Anthropic key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("OpenAI key", re.compile(r"sk-(?:proj-)?[A-Za-z0-9]{32,}")),
    ("AWS key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GitHub token", re.compile(r"gh[pousr]_[A-Za-z0-9]{36}")),
    ("Slack token", re.compile(r"xox[abprs]-[A-Za-z0-9\-]{10,}")),
    ("Google key", re.compile(r"AIza[0-9A-Za-z_\-]{35}")),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("home path", re.compile(r"(?:/Users/|/home/|C:\\\\Users\\\\)([A-Za-z0-9._\-]+)")),
]
PLACEHOLDER_USERS = {"you", "your-name", "username", "user", "name", "example", "me", "runner", "Shared"}


def text_files():
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            if f in SKIP_FILES:
                continue
            p = os.path.join(d, f)
            try:
                with open(p, encoding="utf-8") as fh:
                    yield p, fh.read()
            except (UnicodeDecodeError, OSError):
                continue  # binary or unreadable


def main():
    problems, n = [], 0
    for path, text in text_files():
        n += 1
        rel = os.path.relpath(path, ROOT)
        for label, rx in PATTERNS:
            for m in rx.finditer(text):
                if label == "home path" and m.group(1) in PLACEHOLDER_USERS:
                    continue
                line = text.count("\n", 0, m.start()) + 1
                problems.append(f"{rel}:{line} {label}: {m.group(0)[:24]}…")
    for p in problems:
        print(p)
    print(f"{n} files scanned, {len(problems)} secrets/home paths")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
