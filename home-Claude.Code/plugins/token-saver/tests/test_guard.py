"""Tests für guard.py – Ausführen mit: python3 -m unittest discover plugins/token-saver/tests"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")


def run(tool, tool_input, cwd, env=None):
    payload = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input, "cwd": cwd}
    proc = subprocess.run(
        ["sh", os.path.join(SCRIPTS, "run.sh"), "guard.py"],
        input=json.dumps(payload), capture_output=True, text=True,
        env=dict(os.environ, CLAUDE_PROJECT_DIR=cwd, CLAUDE_CONFIG_DIR=cwd, **(env or {})),
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecisionReason"] if proc.stdout else None


class GuardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        with open(os.path.join(self.dir, "small.py"), "w") as fh:
            fh.write("x = 1\n" * 10)
        with open(os.path.join(self.dir, "big.py"), "w") as fh:
            fh.write("x = 1\n" * 2000)
        with open(os.path.join(self.dir, "package-lock.json"), "w") as fh:
            fh.write("{}\n")

    def tearDown(self):
        self.tmp.cleanup()

    def bash(self, cmd, **kw):
        return run("Bash", {"command": cmd}, self.dir, **kw)

    def test_read(self):
        self.assertIsNone(run("Read", {"file_path": "small.py"}, self.dir))
        self.assertIn("2000 lines", run("Read", {"file_path": "big.py"}, self.dir))
        self.assertIsNone(run("Read", {"file_path": "big.py", "offset": 1, "limit": 100}, self.dir))
        self.assertIn("generated", run("Read", {"file_path": os.path.join(self.dir, "package-lock.json")}, self.dir))
        self.assertIsNone(run("Read", {"file_path": "missing.py"}, self.dir))

    def test_cat(self):
        self.assertIsNone(self.bash("cat small.py"))
        self.assertIsNotNone(self.bash("cat big.py"))
        self.assertIsNotNone(self.bash("cat big.py 2>/dev/null"))
        self.assertIsNotNone(self.bash("cd x && cat big.py"))
        self.assertIsNone(self.bash("cat big.py | head -n 20"))
        self.assertIsNone(self.bash("cat big.py > copy.py"))
        self.assertIsNone(self.bash("cat > new.py <<'EOF'\nhi\nEOF"))

    def test_listing(self):
        self.assertIsNotNone(self.bash("ls -laR"))
        self.assertIsNone(self.bash("ls -la"))
        self.assertIsNotNone(self.bash("tree"))
        self.assertIsNone(self.bash("tree -L 2"))
        self.assertIsNotNone(self.bash("find . -type f"))
        self.assertIsNone(self.bash("find . -name '*.py'"))
        self.assertIsNone(self.bash("find . -type f | head"))

    def test_git_log(self):
        self.assertIsNotNone(self.bash("git log"))
        self.assertIsNone(self.bash("git log -n 5"))
        self.assertIsNone(self.bash("git log --oneline -20"))
        self.assertIsNone(self.bash("git log | head"))

    def test_config(self):
        self.assertIsNone(self.bash("git log", env={"TOKEN_SAVER_DISABLE": "1"}))
        os.makedirs(os.path.join(self.dir, ".claude"))
        with open(os.path.join(self.dir, ".claude", "token-saver.json"), "w") as fh:
            json.dump({"maxReadLines": 5000, "allowPatterns": ["*package-lock.json"]}, fh)
        self.assertIsNone(run("Read", {"file_path": "big.py"}, self.dir))
        self.assertIsNone(run("Read", {"file_path": "package-lock.json"}, self.dir))


if __name__ == "__main__":
    unittest.main()
