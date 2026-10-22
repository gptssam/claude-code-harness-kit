#!/usr/bin/env python3
"""Stop hook — "done" means the checks pass, not that the agent says so.

When the agent tries to finish a turn in which it changed files, this hook runs
`verify_command` from harness.json (default: python3 scripts/verify.py).
- PASS  -> the turn ends normally.
- FAIL  -> the stop is blocked and the failing lines go back to the agent, which keeps working.
After `max_stop_blocks` failed rounds in one turn it lets the turn end and warns you instead,
so the agent never loops forever.
"""
import json
import os
import subprocess
import sys

from harness_common import load_config, log_event, project_dir, read_payload

EDIT_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def is_real_prompt(entry):
    """A user prompt typed by a person (not a tool result fed back to the model)."""
    if entry.get("type") != "user" or entry.get("isMeta"):
        return False  # isMeta = text Claude Code injects itself, e.g. this hook's own "Stop hook feedback"
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, str):
        return not content.startswith("Stop hook feedback")
    if isinstance(content, list):
        return any(isinstance(b, dict) and b.get("type") == "text" for b in content) and \
            not any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content)
    return False


def turn_activity(transcript_path):
    """(turn_start_line, changed_files) for the current turn. None if the transcript is unreadable."""
    try:
        with open(transcript_path, encoding="utf-8") as f:
            entries = [json.loads(line) for line in f if line.strip()]
    except Exception:
        return None
    start = 0
    for i, e in enumerate(entries):
        if is_real_prompt(e):
            start = i
    changed = []
    for e in entries[start:]:
        if e.get("type") != "assistant":
            continue
        for b in (e.get("message") or {}).get("content") or []:
            if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") in EDIT_TOOLS:
                ti = b.get("input") or {}
                changed.append(ti.get("file_path") or ti.get("notebook_path") or "?")
    return start, changed


def state(root, session, turn, bump=False):
    d = os.path.join(root, ".claude", "hooks", ".state")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{session or 'default'}.json")
    try:
        with open(path) as f:
            s = json.load(f)
    except Exception:
        s = {}
    if s.get("turn") != turn:
        s = {"turn": turn, "blocks": 0}
    if bump:
        s["blocks"] += 1
        with open(path, "w") as f:
            json.dump(s, f)
    return s["blocks"]


def main():
    payload = read_payload()
    root = project_dir(payload)
    cfg = load_config(root)
    activity = turn_activity(payload.get("transcript_path", ""))
    if activity is not None and not activity[1]:
        return 0  # nothing was edited this turn — nothing to verify
    turn = activity[0] if activity else -1

    try:
        r = subprocess.run(cfg["verify_command"], shell=True, cwd=root,
                           capture_output=True, text=True, timeout=300)
        ok, out = r.returncode == 0, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        ok, out = False, "verify_command가 300초 안에 끝나지 않았습니다."

    summary = out.splitlines()[-1] if out else ""
    if ok:
        log_event(root, "verify_gate", "pass", "V1", summary)
        return 0

    blocks = state(root, payload.get("session_id"), turn)
    if blocks >= cfg.get("max_stop_blocks", 3):
        log_event(root, "verify_gate", "handover", "V1", summary)
        print(json.dumps({"systemMessage": f"[harness V1] 검사를 {blocks}번 돌려도 통과하지 못했습니다. "
                                           f"사람이 확인해 주세요: {summary}"}, ensure_ascii=False))
        return 0

    state(root, payload.get("session_id"), turn, bump=True)
    log_event(root, "verify_gate", "block", "V1", summary)
    tail = "\n".join(out.splitlines()[-30:])
    reason = (f"[harness V1] 아직 완료가 아닙니다. 이번 턴에 파일을 바꿨는데 검사(`{cfg['verify_command']}`)가 통과하지 않았습니다.\n"
              f"{tail}\n"
              "FAIL 항목을 고친 뒤 검사를 다시 돌리고, 통과한 숫자(예: 3/3 PASS)를 보고에 그대로 적으세요. "
              "규격을 바꿔서 통과시키지 마세요.")
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
