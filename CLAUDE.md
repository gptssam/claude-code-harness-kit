# CLAUDE.md — Claude Code 진입점

> 먼저 같은 폴더의 [`AGENTS.md`](./AGENTS.md)를 읽고 그대로 따르세요. 이 파일은 Claude Code에만 해당하는 내용입니다.

## Claude Code에서는 훅이 자동으로 켜집니다

`.claude/settings.json`에 등록된 훅 3개가 규칙을 말이 아니라 장치로 지킵니다.

| 훅 | 시점 | 하는 일 |
|---|---|---|
| `guard_bash.py` | Bash 실행 직전 | G1~G7 위험 명령이면 실행을 막고 이유와 대안을 돌려줍니다 |
| `guard_write.py` | Write/Edit 직전 | `raw/` · `specs/` · `_archive/` · `.env` 쓰기를 막습니다 |
| `verify_gate.py` | 답을 끝내려 할 때 | 이번 턴에 파일을 바꿨으면 `python3 scripts/verify.py`를 돌리고, FAIL이면 끝내지 못하게 돌려보냅니다(최대 3번, 그 뒤엔 사람에게 넘김) |

- 훅이 막으면(`[harness G1] 차단 …`) 우회하지 말고 메시지에 적힌 대안으로 다시 하세요.
- 처음 열면 Claude Code가 이 프로젝트의 훅을 믿을지 묻습니다. 훅 내용은 `.claude/hooks/`에서 직접 읽어 볼 수 있습니다.
- 훅이 무엇을 막았는지는 `.claude/hooks/harness_log.csv`에 남습니다.

## 셋업 확인

```bash
python3 tests/test_hooks.py   # 훅 테스트
python3 scripts/verify.py     # 현재 검사 상태
```
