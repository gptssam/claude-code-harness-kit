# GEMINI.md — Antigravity · Gemini CLI 진입점

> 먼저 같은 폴더의 [`AGENTS.md`](./AGENTS.md)를 읽고 그대로 따르세요.

## 훅이 없는 환경에서는 손으로 같은 순서를 지킵니다

`.claude/settings.json`의 훅은 Claude Code 전용입니다. 이 환경에서는 자동으로 막히지 않으므로 아래를 스스로 지킵니다.

1. 명령을 실행하기 전에 [`AGENTS.md` §3 표](./AGENTS.md)의 G1~G7에 해당하는지 확인합니다. 해당하면 표의 "대신 하는 것"으로 바꿉니다.
2. `raw/` · `specs/` · `_archive/` · `.env`에는 쓰지 않습니다.
3. 파일을 바꿨으면 끝내기 전에 `python3 scripts/verify.py`를 실행하고, `RESULT n/n PASS` 줄을 보고에 그대로 붙입니다. FAIL이면 고친 뒤 다시 실행합니다.

검사 스크립트(`scripts/verify.py` · `checks/`)와 잠금(`scripts/lock.py`)은 어느 에이전트에서나 똑같이 작동합니다.
