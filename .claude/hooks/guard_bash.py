#!/usr/bin/env python3
"""PreToolUse hook (matcher: Bash) — blocks commands that destroyed work in real projects.

Exit 2 = the command is blocked and the message on stderr goes back to the agent,
which then retries the safe way (e.g. `mv` into _archive/ instead of `rm -rf`).
Each rule comes from a real incident; see lessons/.
"""
import re
import shlex
import sys

from harness_common import load_config, log_event, project_dir, read_payload

SEPARATORS = {";", "&&", "||", "|", "&", "\n"}


def segments(command):
    """Split a shell line into simple commands: [['git', 'commit', '-am', 'x'], ['ls']]."""
    try:
        lex = shlex.shlex(command, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        tokens = list(lex)
    except ValueError:  # unbalanced quotes — fall back to a rough split
        tokens = command.replace("&&", " ; ").replace("||", " ; ").replace("|", " ; ").split()
    segs, cur = [], []
    for t in tokens:
        if t in SEPARATORS or set(t) <= set(";&|"):
            if cur:
                segs.append(cur)
            cur = []
        else:
            cur.append(t)
    if cur:
        segs.append(cur)
    # drop leading env assignments and wrappers: `FOO=1 sudo git ...` -> `git ...`
    out = []
    for s in segs:
        while s and (re.match(r"^\w+=", s[0]) or s[0] in ("sudo", "command", "env", "nohup", "time")):
            s = s[1:]
        if s:
            out.append(s)
    return out


def short_flags(args):
    """Letters from single-dash flags: ['-am', '-f'] -> {'a', 'm', 'f'}."""
    letters = set()
    for a in args:
        if a.startswith("-") and not a.startswith("--") and len(a) > 1:
            letters.update(a[1:])
    return letters


def git_sub(seg):
    """('commit', args) for `git -C dir commit -am x`."""
    args = seg[1:]
    i = 0
    while i < len(args) and args[i].startswith("-"):
        i += 2 if args[i] in ("-C", "-c") else 1
    if i < len(args):
        return args[i], args[i + 1:]
    return None, []


def check(seg):
    """Return (rule_id, reason) if this simple command must be blocked."""
    prog = seg[0].rsplit("/", 1)[-1]
    args = seg[1:]
    flags = short_flags(args)

    if prog == "rm" and ("r" in flags or "R" in flags or "--recursive" in args):
        return ("G1", "폴더째 지우는 rm -r/-rf는 막혀 있습니다. 지우지 말고 "
                      "`mkdir -p _archive && mv <대상> _archive/<날짜>_<이름>`으로 옮기세요. "
                      "정말 지워야 하면 사용자에게 명령을 드려 직접 지우게 하세요.")

    if prog == "git":
        sub, rest = git_sub(seg)
        rflags = short_flags(rest)
        if sub == "commit" and ("a" in rflags or "--all" in rest):
            return ("G2", "git commit -a/-am은 다른 세션이 아직 커밋하지 않은 변경까지 함께 올립니다. "
                          "`git status --short`로 내 파일만 골라 `git add <경로>` 뒤 `git commit -m`을 쓰세요.")
        if sub == "add" and ("A" in rflags or "--all" in rest or "." in rest or ":/" in rest):
            return ("G3", "git add -A / git add . 는 남의 변경까지 담습니다. 내가 바꾼 파일 경로만 `git add <경로>`로 올리세요.")
        if sub == "push" and ("f" in rflags or "--force" in rest):
            return ("G4", "강제 푸시(--force)는 원격 이력을 지웁니다. 실수가 있었다면 되돌리지 말고 사용자에게 먼저 알리세요.")
        if sub == "reset" and "--hard" in rest:
            return ("G5", "git reset --hard는 커밋 안 한 작업을 지웁니다. `git stash` 또는 사용자 확인을 먼저 받으세요.")
        if sub == "clean" and "f" in rflags:
            return ("G5", "git clean -f는 추적 안 된 파일을 지웁니다. 지울 목록을 사용자에게 보여 주고 확인을 받으세요.")
        if sub in ("checkout", "restore") and ("." in rest or "--" in rest and rest[-1] in (".", "*")):
            return ("G5", "작업 트리 전체를 되돌리는 명령은 커밋 안 한 변경을 지웁니다. 파일 하나씩 경로로 지정하세요.")

    if prog == "ffmpeg" and "-y" in args:
        return ("G6", "ffmpeg -y는 같은 이름의 결과물을 말없이 덮어씁니다. `-n`을 쓰고, 바꿀 파일은 먼저 _archive/로 옮기세요.")

    if prog in ("pbcopy", "pbpaste", "xclip", "xsel", "wl-copy", "wl-paste", "clip.exe"):
        return ("G7", "클립보드는 컴퓨터 전체가 같이 씁니다. 세션을 여러 개 돌리면 다른 세션이 덮어써 엉뚱한 글이 들어갑니다. "
                      "파일로 주고받거나 직접 입력하세요. (혼자만 쓰면 harness.json의 bash_rules_off에 G7을 넣으세요.)")
    return None


def main():
    payload = read_payload()
    if payload.get("tool_name") != "Bash":
        return 0
    command = (payload.get("tool_input") or {}).get("command", "")
    root = project_dir(payload)
    off = set(load_config(root).get("bash_rules_off", []))
    for seg in segments(command):
        hit = check(seg)
        if hit and hit[0] not in off:
            rule, reason = hit
            log_event(root, "guard_bash", "block", rule, command)
            print(f"[harness {rule}] 차단: {' '.join(seg)}\n{reason}", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
