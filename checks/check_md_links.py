#!/usr/bin/env python3
"""Fail if a Markdown file links to a local file that does not exist.

Checks relative links like [text](docs/a.md) or ./img.png; skips web links and #anchors.
"""
import os
import re
import sys
from urllib.parse import unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", "_archive", "node_modules"}
LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)|\!\[[^\]]*\]\(([^)\s]+)\)")
CODE = re.compile(r"```.*?```|`[^`\n]*`", re.S)


def main():
    problems, files, links = [], 0, 0
    for d, dirs, fs in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in fs:
            if not f.endswith(".md"):
                continue
            files += 1
            path = os.path.join(d, f)
            text = CODE.sub("", open(path, encoding="utf-8").read())
            for m in LINK.finditer(text):
                target = m.group(1) or m.group(2)
                if re.match(r"^[a-z][a-z0-9+.\-]*:", target, re.I) or target.startswith("#"):
                    continue
                links += 1
                local = unquote(target.split("#", 1)[0])
                if not os.path.exists(os.path.normpath(os.path.join(d, local))):
                    problems.append(f"{os.path.relpath(path, ROOT)}: broken link -> {target}")
    for p in problems:
        print(p)
    print(f"{files} markdown files, {links} local links, {len(problems)} broken")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
