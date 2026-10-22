---
name: harness-kit
description: AI 에이전트의 거짓 완료 보고 · 파일 삭제/덮어쓰기 · 세션 여러 개 충돌을 막는 하네스(훅 · 검사 스크립트 · 잠금 · 사고 기록)를 셋업하고 넓히는 스킬입니다. 사용자가 이 저장소 셋업, 기존 프로젝트에 하네스 붙이기, "이 실수 다시 안 하게 해줘" 같은 규칙 추가, 완료 기준(검사) 만들기, 잠금 사용을 요청할 때 사용하세요.
---

# Harness Kit Skill (Claude Code · Codex · Antigravity 공통)

이 스킬은 [`AGENTS.md`](../../../AGENTS.md) 헌법을 기반으로 작동합니다. 훅(`.claude/settings.json`)은 Claude Code에서만 자동으로 걸리고, Codex · Antigravity에서는 같은 규칙을 손으로 지킵니다.

## 1. 최초 셋업 (Bootstrap)

1. 클론(또는 `git`이 없으면 tarball 다운로드) 뒤 저장소 폴더로 이동합니다.
2. 아래를 실행하고 결과 줄을 그대로 보고합니다.
   ```bash
   python3 tests/test_hooks.py      # Ran 8 tests ... OK
   python3 scripts/verify.py        # RESULT 2/2 PASS (0 FAIL, 1 SKIP)
   python3 demo/setup_demo.py
   ```
3. 사용자에게 알립니다: Claude Code가 폴더 신뢰를 물으면 승인해야 훅이 켜진다 · 막힌 기록은 `.claude/hooks/harness_log.csv` · 직접 보기는 `demo/README.md`.
4. 맞춤 질문 3가지를 사용자의 언어로 묻습니다: ① 가장 걱정되는 사고 ② 내 업무의 "완료"를 숫자로 ③ 이 폴더에서 쓸지, 기존 프로젝트에 옮길지.

## 2. 기존 프로젝트에 붙이기

- 복사: `.claude/hooks/` · `harness.json` · `scripts/verify.py` · `scripts/lock.py` · `checks/_template_check.py`.
- 사용자 프로젝트에 `.claude/settings.json`이 이미 있으면 **덮어쓰지 말고** `"hooks"` 블록만 합칩니다. 합친 뒤 JSON이 유효한지 `python3 -m json.tool .claude/settings.json`으로 확인합니다.
- `harness.json`의 `verify_command` · `protected_paths`를 사용자 프로젝트에 맞게 묻고 고칩니다.

## 3. "이 실수 다시 안 하게 해줘" → 규칙 추가

1. `lessons/_template.md`를 복사해 `lessons/lNN_<짧은_영문_이름>.md`를 씁니다(날짜 · 무슨 일 · 손실 숫자 · 규칙 한 줄 · Why · How to apply · 강제 장치).
2. `AGENTS.md` §3 표 또는 §4에 한 줄을 더합니다.
3. 같은 실수가 **두 번째**라면 장치로 옮깁니다:
   - 결과물 문제 → `checks/check_<이름>.py`(틀: `checks/_template_check.py`)
   - 위험 명령 → `.claude/hooks/guard_bash.py`의 `check()`에 규칙 추가 + `tests/test_hooks.py`의 `BLOCK` · `ALLOW` 목록에 사례 추가
4. `python3 tests/test_hooks.py`와 `python3 scripts/verify.py`를 돌려 결과 줄을 보고합니다.

## 4. 완료 기준(검사) 만들기

- 사용자의 "완료"를 숫자로 바꿉니다(개수 · 길이 · 존재 · 금지어 · 중복 등).
- 채점 기준(규격 값)은 `specs/`에 두고 **사용자에게 확인받은 뒤** 사람이 저장하게 합니다 — `specs/`는 에이전트 읽기 전용(W1)입니다.
- 검사는 문제를 한 줄에 하나, 마지막 줄에 숫자 요약, 문제가 있으면 종료 코드 1.

## 5. 잠금

```bash
python3 scripts/lock.py acquire <자원> <세션이름> --note "<무엇>"
python3 scripts/lock.py release <자원> <세션이름>
python3 scripts/lock.py status
```
- 출력에 `LOCKED <자원>: <내 세션>`이 없으면 진행하지 않습니다. `STALE`이면 지우지 말고 사람에게 묻습니다.
