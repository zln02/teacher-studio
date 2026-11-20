# SPDX-License-Identifier: Apache-2.0
"""run.cmd / run.sh find Python from the path doctor.py recorded in env.json, even with a bare PATH."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCR = ROOT / "skills" / "teacher-studio" / "scripts"
sys.path.insert(0, str(SCR))


class Runner(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.home, True)
        self.env = dict(os.environ, TEACHER_STUDIO_HOME=str(self.home))
        (self.home / "env.json").write_text(json.dumps({"python_path": sys.executable, "keep": 1}), encoding="utf-8")
        self.script = self.home / "hello.py"
        self.script.write_text("import sys; print('ok', sys.argv[1:])", encoding="utf-8")

    def test_record_python_keeps_other_keys(self):
        os.environ["TEACHER_STUDIO_HOME"] = str(self.home)
        self.addCleanup(os.environ.pop, "TEACHER_STUDIO_HOME", None)
        (self.home / "env.json").write_text(json.dumps({"keep": 1}), encoding="utf-8")
        import doctor
        doctor.record_python()
        data = json.loads((self.home / "env.json").read_text(encoding="utf-8"))
        self.assertEqual(data["python_path"], sys.executable)
        self.assertEqual(data["keep"], 1)

    def test_wrapper_uses_recorded_path(self):
        if os.name == "nt":
            cmd = ["cmd", "/c", str(SCR / "run.cmd"), str(self.script), "a b", "c"]
            env = dict(self.env, PATH=os.environ.get("SystemRoot", r"C:\Windows") + r"\System32;" + os.environ.get("SystemRoot", r"C:\Windows") + r"\System32\WindowsPowerShell\v1.0")
        else:
            if not shutil.which("sh"):
                self.skipTest("no sh")
            cmd = ["sh", str(SCR / "run.sh"), str(self.script), "a b", "c"]
            env = dict(self.env, PATH="/usr/bin:/bin")
        r = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("['a b', 'c']", r.stdout)


if __name__ == "__main__":
    unittest.main()
