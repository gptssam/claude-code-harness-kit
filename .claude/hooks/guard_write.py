#!/usr/bin/env python3
"""PreToolUse hook (matcher: Write|Edit|MultiEdit|NotebookEdit) — keeps read-only folders read-only.

`protected_paths` in harness.json (default: raw/, specs/, _archive/, .env) may be read but never written.
Exit 2 blocks the edit and tells the agent where to write instead.
"""
import os
import sys

from harness_common import load_config, log_event, project_dir, read_payload

EDIT_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def is_protected(path, root, protected):
    abs_path = os.path.abspath(os.path.join(root, path))
    rel = os.path.relpath(abs_path, root).replace(os.sep, "/")
    if rel.startswith("../"):
        return None  # outside the project — not this hook's business
    for p in protected:
        p = p.strip("/")
        if rel == p or rel.startswith(p + "/"):
            return p
    return None


def main():
    payload = read_payload()
    if payload.get("tool_name") not in EDIT_TOOLS:
        return 0
    ti = payload.get("tool_input") or {}
    path = ti.get("file_path") or ti.get("notebook_path") or ""
    if not path:
        return 0
    root = project_dir(payload)
    hit = is_protected(path, root, load_config(root).get("protected_paths", []))
    if hit:
        log_event(root, "guard_write", "block", "W1", path)
        print(f"[harness W1] 차단: {path}\n`{hit}/`는 읽기 전용입니다(원본·보관본). "
              "고친 결과는 다른 폴더에 새 파일로 쓰고, 원본은 그대로 두세요.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
