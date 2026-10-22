# AGENTS.md — Claude Code Harness Kit 공통 헌법

> **호환 에이전트**: Claude Code(훅까지 자동 적용) · Codex CLI · Antigravity/Gemini · Cursor(규칙 · 검사 스크립트는 같이 쓰고, 훅 대신 아래 §2를 손으로 실행)
> **한 줄 요약**: 프롬프트로 부탁하지 말고, 규칙은 파일로 · 금지는 훅으로 · 완료는 검사 스크립트로 정한다.

이 저장소는 AI 에이전트가 **"다 했어요"라고 거짓 완료를 보고하거나, 파일을 지우고 덮어쓰거나, 세션 여러 개가 서로의 작업을 망가뜨리는 사고**를 막는 하네스(harness: 에이전트를 감싸는 규칙 · 검사 · 차단 장치) 스타터 킷입니다. 모든 규칙은 실제 운영 중 일어난 사고 8건(`lessons/`)에서 나왔습니다.

---

## 1. 폴더 구조

```text
claude-code-harness-kit/
├── AGENTS.md / CLAUDE.md / GEMINI.md   # 헌법(이 파일)과 도구별 진입점
├── harness.json                        # 하네스 설정: 완료 검사 명령 · 읽기 전용 경로 · 끌 규칙
├── .claude/
│   ├── settings.json                   # 훅 등록(Claude Code가 자동으로 읽음)
│   └── hooks/
│       ├── guard_bash.py               # G1~G7 위험 명령 차단 (PreToolUse · Bash)
│       ├── guard_write.py              # W1 읽기 전용 경로 쓰기 차단 (PreToolUse · Write/Edit)
│       └── verify_gate.py              # V1 검사 통과 전 완료 금지 (Stop)
├── scripts/
│   ├── verify.py                       # "완료"의 정의: checks/check_*.py 전부 실행
│   └── lock.py                         # 공용 자원 한 번에 한 세션 잠금
├── checks/                             # 검사 스크립트 (지적 한 번 → 검사 하나)
├── specs/                              # 채점 기준 — 사람만 고침 (에이전트는 읽기 전용)
├── lessons/                            # 사고 기록 → 규칙 한 줄 (L01~L08 + _template.md)
├── demo/                               # 직접 해 보는 시나리오 3개
└── tests/test_hooks.py                 # 훅이 실제로 막는지 확인하는 테스트
```

## 2. 완료의 정의 (V1)

1. 파일을 하나라도 바꿨다면, 끝내기 전에 반드시 실행합니다:
   ```bash
   python3 scripts/verify.py
   ```
2. 마지막 줄이 `RESULT n/n PASS (0 FAIL, …)`일 때만 완료입니다. 보고에 이 줄을 **그대로** 붙입니다.
3. FAIL이면 결과물을 고칩니다. **`specs/`(채점 기준)나 `checks/`(채점기)를 바꿔서 통과시키지 않습니다.** 규격이 틀렸다고 생각되면 사람에게 묻습니다.
4. 검사로 확인할 수 없는 것(소리 · 화면 느낌 등)은 "확인 못 함"이라고 적습니다. 추측으로 채우지 않습니다.

## 3. 하지 않는 것 (G1~G7 · W1)

| 번호 | 하지 않는 것 | 대신 하는 것 | 출처 |
|---|---|---|---|
| G1 | `rm -r` / `rm -rf` | `mkdir -p _archive && mv <대상> _archive/<날짜>_<이름>` | [L03](lessons/l03_archive_not_delete.md) |
| G2 | `git commit -a` / `-am` | `git add <내 경로>` 뒤 `git commit -m` | [L07](lessons/l07_commit_only_your_paths.md) |
| G3 | `git add -A` / `git add .` | 바꾼 파일 경로만 `git add` | [L07](lessons/l07_commit_only_your_paths.md) |
| G4 | `git push --force` | 사람에게 알리기 | [L07](lessons/l07_commit_only_your_paths.md) |
| G5 | `git reset --hard` · `git clean -f` · `git checkout .` | `git stash` 또는 파일 하나씩 | [L03](lessons/l03_archive_not_delete.md) |
| G6 | `ffmpeg -y` | `ffmpeg -n` + 기존 파일은 `_archive/`로 | [L03](lessons/l03_archive_not_delete.md) |
| G7 | 클립보드(`pbcopy` 등) — 세션 여러 개일 때 | 파일로 주고받기 | [L04](lessons/l04_no_shared_clipboard.md) |
| W1 | `raw/` · `specs/` · `_archive/` · `.env`에 쓰기 | 다른 폴더에 새 파일로 | [L08](lessons/l08_subagent_read_only.md) |

## 4. 세션을 여러 개 돌릴 때

- 공용 자원(같은 계정 · 렌더 자리 · GPU)은 쓰기 직전 `python3 scripts/lock.py acquire <자원> <세션이름>`, 끝나면 `release`. 출력에 `LOCKED <자원>: <내 세션>`이 없으면 진행하지 않습니다([L05](lessons/l05_one_submitter_lock.md) · [L06](lessons/l06_read_the_lock_output.md)).
- 30분 넘게 묵은 잠금(`STALE`)은 지우지 말고 사람에게 묻습니다.
- 다운로드 폴더처럼 같이 쓰는 폴더에서는 "방금 생긴 파일 전부"가 아니라 **내 파일 이름 · 크기 · 해시로 고른 것만** 옮깁니다.
- 서브에이전트 · 다른 세션에 일을 맡길 땐 "어디는 읽기만, 결과는 어디에만"을 지시문에 적습니다([L08](lessons/l08_subagent_read_only.md)).

## 5. 지적 한 번 = 규칙 한 줄 (lessons/)

사람이 같은 실수를 지적하면:
1. `lessons/_template.md`를 복사해 `lessons/lNN_<짧은_영문_이름>.md`로 저장합니다(날짜 · 무슨 일 · 손실 숫자 · 규칙 한 줄 · Why · How to apply · 강제 장치).
2. 이 파일 §3 표나 §4에 한 줄을 더합니다.
3. **같은 실수가 두 번째 나오면** 말로 두지 말고 장치로 옮깁니다: 검사는 `checks/check_<이름>.py`(틀: `checks/_template_check.py`), 금지 명령은 `guard_bash.py` 규칙.

## 6. 보고 형식

- 무엇을 바꿨는지(파일 경로) · 검사 결과 줄(`RESULT …`) · 확인 못 한 것, 이 세 가지를 적습니다.
- 숫자는 측정한 값만 씁니다. 추정이면 "추정"이라고 씁니다.
- 사용자가 쓴 언어로 답합니다(한국어로 물으면 한국어, 영어로 물으면 영어). 이 저장소 문서가 영어라도 마찬가지입니다. / Reply in the language the user wrote in, even though some docs here are in English.
