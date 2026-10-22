#!/usr/bin/env python3
"""Feed the hooks the same JSON Claude Code sends and check what they decide.

    python3 tests/test_hooks.py        # standard library only, runs in about a second
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS = os.path.join(KIT, ".claude", "hooks")


def run_hook(name, payload, project):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=project)
    r = subprocess.run([sys.executable, os.path.join(HOOKS, name)], input=json.dumps(payload),
                       capture_output=True, text=True, env=env, timeout=60)
    return r.returncode, r.stdout, r.stderr


class Project:
    """A throwaway copy of the kit, so tests never touch your real files or logs."""

    def __enter__(self):
        self.dir = os.path.join(tempfile.mkdtemp(prefix="harness_test_"), "kit")
        shutil.copytree(KIT, self.dir, ignore=shutil.ignore_patterns(
            "harness_log.csv", ".state", "__pycache__", ".git", "_archive", "titles.csv", "renders_old"))
        return self.dir

    def __exit__(self, *exc):
        shutil.rmtree(os.path.dirname(self.dir), ignore_errors=True)


BLOCK = [
    ("rm -rf build", "G1"),
    ("rm -r old_renders", "G1"),
    ("cd out && rm -fr tmp", "G1"),
    ('git commit -am "fix"', "G2"),
    ("git commit -a -m fix", "G2"),
    ("FOO=1 git commit --all -m x", "G2"),
    ("git -C sub commit -am x", "G2"),
    ("git add -A", "G3"),
    ("git add .", "G3"),
    ("git push --force", "G4"),
    ("git push -f origin main", "G4"),
    ("git reset --hard HEAD~1", "G5"),
    ("git clean -fd", "G5"),
    ("git checkout .", "G5"),
    ("ffmpeg -y -i a.mp4 b.mp4", "G6"),
    ("echo hi | pbcopy", "G7"),
]
ALLOW = [
    "rm notes.txt",
    'git commit -m "explain the -a flag"',
    "git commit --amend -m x",
    "git add src/app.py docs/README.md",
    "git push origin main",
    "git push --force-with-lease origin feature",
    "git checkout main",
    "git checkout -- src/app.py",
    "ffmpeg -n -i a.mp4 b.mp4",
    "mkdir -p _archive && mv old_renders _archive/2026-10-20_old_renders",
    'echo "never run rm -rf /" > notes.txt',
    "ls -la",
]


class GuardBash(unittest.TestCase):
    def test_blocks(self):
        with Project() as p:
            for cmd, rule in BLOCK:
                code, _, err = run_hook("guard_bash.py", {"tool_name": "Bash", "tool_input": {"command": cmd}}, p)
                self.assertEqual(code, 2, cmd)
                self.assertIn(f"[harness {rule}]", err, cmd)

    def test_allows(self):
        with Project() as p:
            for cmd in ALLOW:
                code, _, err = run_hook("guard_bash.py", {"tool_name": "Bash", "tool_input": {"command": cmd}}, p)
                self.assertEqual(code, 0, f"{cmd}: {err}")

    def test_rule_can_be_switched_off(self):
        with Project() as p:
            path = os.path.join(p, "harness.json")
            with open(path) as f:
                cfg = json.load(f)
            cfg["bash_rules_off"] = ["G7"]
            with open(path, "w") as f:
                json.dump(cfg, f)
            code, _, _ = run_hook("guard_bash.py", {"tool_name": "Bash", "tool_input": {"command": "echo hi | pbcopy"}}, p)
            self.assertEqual(code, 0)


class GuardWrite(unittest.TestCase):
    def test_protected(self):
        with Project() as p:
            for path in ("raw/meeting.md", "specs/titles_spec.json", os.path.join(p, "raw", "a.md"), ".env"):
                code, _, err = run_hook("guard_write.py", {"tool_name": "Write", "tool_input": {"file_path": path}}, p)
                self.assertEqual(code, 2, path)
                self.assertIn("[harness W1]", err)

    def test_free(self):
        with Project() as p:
            for path in ("demo/titles.csv", "rawdata/x.md", "/tmp/elsewhere.txt"):
                code, _, _ = run_hook("guard_write.py", {"tool_name": "Edit", "tool_input": {"file_path": path}}, p)
                self.assertEqual(code, 0, path)


def transcript(project, edits, feedback_rounds=0):
    """Minimal Claude Code transcript: one prompt, the edits, then any earlier Stop-hook feedback.

    Claude Code writes the gate's own feedback back as a user entry with isMeta: true —
    the gate must not mistake it for a new prompt (found in the 10-21 live run C_with_2).
    """
    lines = [{"type": "user", "message": {"role": "user", "content": "write the titles"}}]
    for path in edits:
        lines.append({"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "tool_use", "name": "Write", "input": {"file_path": path}}]}})
        lines.append({"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "content": "ok"}]}})
    for _ in range(feedback_rounds):
        lines.append({"type": "user", "isMeta": True, "message": {"role": "user",
                      "content": "Stop hook feedback: [harness V1] ..."}})
        lines.append({"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "text", "text": "These problems were already there before my edit."}]}})
    t = os.path.join(project, "transcript.jsonl")
    with open(t, "w") as f:
        f.write("\n".join(json.dumps(l) for l in lines))
    return t


GOOD = ["no,title"] + [f"{i},엘리베이터가 밤에 {i}층마다 서는 이유" for i in range(1, 11)]
BAD = ["no,title"] + [f"{i},무조건 봐야 하는 엘리베이터의 비밀 이야기 총정리편" for i in range(1, 10)]


class VerifyGate(unittest.TestCase):
    def stop(self, p, edits, rows=None, feedback_rounds=0):
        if rows is not None:
            with open(os.path.join(p, "demo", "titles.csv"), "w") as f:
                f.write("\n".join(rows) + "\n")
        payload = {"session_id": "t1", "transcript_path": transcript(p, edits, feedback_rounds),
                   "stop_hook_active": feedback_rounds > 0}
        return run_hook("verify_gate.py", payload, p)

    def test_no_edit_no_check(self):
        with Project() as p:
            code, out, _ = self.stop(p, [], BAD)
            self.assertEqual((code, out.strip()), (0, ""))

    def test_pass(self):
        with Project() as p:
            code, out, _ = self.stop(p, ["demo/titles.csv"], GOOD)
            self.assertEqual((code, out.strip()), (0, ""))

    def test_fail_blocks_then_hands_over(self):
        with Project() as p:
            decisions = []
            for i in range(4):  # the agent tries to stop again without editing: still the same turn
                code, out, _ = self.stop(p, ["demo/titles.csv"], BAD, feedback_rounds=i)
                decisions.append(json.loads(out))
            self.assertEqual([d.get("decision") for d in decisions[:3]], ["block"] * 3)
            self.assertIn("need exactly 10 rows", decisions[0]["reason"])
            self.assertIn("banned word", decisions[0]["reason"])
            self.assertNotIn("decision", decisions[3])
            self.assertIn("systemMessage", decisions[3])


if __name__ == "__main__":
    unittest.main(verbosity=2)
