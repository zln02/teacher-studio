# SPDX-License-Identifier: Apache-2.0
"""Harness scripts must work inside an agent's security box (Codex on Windows): no tempfile private folders, a fast
no-browser path, an installer whose folders the box can read, and skill text that says the tools are a floor.
Measured background: docs/research/cross-vendor-fix-2026-11.md.   py tools/test_sandbox_safe.py"""
import os
import re
import shutil
import subprocess
import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "shared" / "tools"))
import workdir  # noqa: E402

SCRATCH = ROOT / "tools" / f".test-sandbox-{uuid.uuid4().hex[:6]}"
BANNED = re.compile(r"tempfile\.(mkdtemp|TemporaryDirectory|NamedTemporaryFile|mkstemp|TemporaryFile)\s*\(")


def harness_scripts():
    files = list((ROOT / "scripts").glob("*.py")) + list((ROOT / "shared").rglob("*.py")) + list((ROOT / "skills").glob("*/scripts/*.py"))
    files += list((ROOT / "skills").glob("*/shared/**/*.py"))
    return [f for f in files if "__pycache__" not in f.parts and not f.name.startswith("test_") and f.name != "workdir.py"]  # workdir.py only names the calls in its notes


def run(args, env=None, cwd=None, timeout=300):
    e = dict(os.environ, PYTHONUTF8="1", **(env or {}))
    return subprocess.run([sys.executable] + [str(a) for a in args], cwd=str(cwd or SCRATCH), env=e, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


class NoPrivateTemp(unittest.TestCase):
    def test_no_tempfile_private_folders_in_harness_scripts(self):
        bad = []
        for f in harness_scripts():
            for n, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if BANNED.search(line) and not line.lstrip().startswith("#"):
                    bad.append(f"{f.relative_to(ROOT)}:{n}")
        self.assertEqual(bad, [], "use shared/tools/workdir.py (temp_dir / make / named) instead")

    def test_every_tools_skill_has_workdir(self):
        for skill in (ROOT / "skills").iterdir():
            if (skill / "shared" / "tools" / "ensure.py").is_file():
                self.assertEqual((skill / "shared" / "tools" / "workdir.py").read_bytes(), (ROOT / "shared" / "tools" / "workdir.py").read_bytes(), skill.name)


class WorkDir(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, SCRATCH, True)
        self._env = os.environ.pop(workdir.ENV_DIR, None)
        self.addCleanup(lambda: os.environ.__setitem__(workdir.ENV_DIR, self._env) if self._env else os.environ.pop(workdir.ENV_DIR, None))

    def test_made_beside_the_output_and_removed(self):
        out = SCRATCH / "out" / "x.pptx"
        out.parent.mkdir()
        with workdir.temp_dir("deck", near=out) as td:
            self.assertEqual(Path(td).parent, out.parent.resolve() / workdir.WORK_NAME)
            (Path(td) / "a.txt").write_text("x", encoding="utf-8")
        self.assertFalse((out.parent / workdir.WORK_NAME).exists(), "work folder must not be left in the user's folder")

    def test_env_override(self):
        os.environ[workdir.ENV_DIR] = str(SCRATCH / "mine")
        d = workdir.make("t", near=SCRATCH / "elsewhere" / "f.html")
        self.assertEqual(d.parent, SCRATCH / "mine")
        workdir.cleanup(d)

    def test_falls_back_when_the_first_place_is_not_writable(self):
        blocker = SCRATCH / "blocked"
        blocker.write_text("a file, not a folder", encoding="utf-8")
        os.environ[workdir.ENV_DIR] = str(blocker / "sub")  # cannot be created
        d = workdir.make("t", near=SCRATCH / "o.html")
        self.assertTrue(d.is_dir())
        self.assertNotIn("blocked", str(d))
        workdir.cleanup(d)

    @unittest.skipUnless(os.name == "nt", "Windows permissions")
    def test_folder_inherits_permissions(self):
        d = workdir.make("acl", near=SCRATCH / "o.html")
        acl = subprocess.run(["icacls", str(d)], capture_output=True, text=True, errors="replace").stdout
        workdir.cleanup(d)
        self.assertIn("(I)", acl, "the folder must inherit its parent's permissions (tempfile.mkdtemp would not)")


class NoBrowser(unittest.TestCase):
    ENV = {workdir.ENV_NO_BROWSER: "1"}

    def setUp(self):
        SCRATCH.mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, SCRATCH, True)

    def test_stub_fails_fast_and_imports(self):
        code = ("import sys; sys.path.insert(0, r'%s'); import workdir; assert workdir.guard_browser(quiet=True)\n"
                "from playwright.sync_api import expect, sync_playwright\n"
                "try:\n    sync_playwright()\nexcept RuntimeError as e:\n    print('OK', workdir.is_no_browser(e))\n") % (ROOT / "shared" / "tools")
        r = run(["-c", code], self.ENV)
        self.assertIn("OK True", r.stdout, r.stderr[-400:])

    def test_pptx_build_draws_a_sketch_and_is_ready(self):
        spec = ROOT / "skills/teacher-slides/assets/spec-examples/context/class-light-reflection.json"
        shutil.copyfile(spec, SCRATCH / "deck.json")
        r = run([ROOT / "skills/teacher-slides/scripts/deck.py", "--spec", "deck.json", "--pptx", "수업.pptx", "--pptx-only", "--review", "review"], self.ENV)
        out = r.stdout + r.stderr
        self.assertEqual(r.returncode, 0, out[-1500:])
        self.assertIn("READY", out)
        self.assertEqual(out.count(workdir.NO_BROWSER + " "), 1, "the no-browser line is said once")
        self.assertTrue((SCRATCH / "review" / "수업-sketch-sheet.png").is_file())
        self.assertGreater((SCRATCH / "review" / "수업-sketch-sheet.png").stat().st_size, 20000)
        self.assertFalse((SCRATCH / workdir.WORK_NAME).exists())
        self.assertNotIn("Traceback", out)

    def test_game_build_is_partial_not_a_crash(self):
        shutil.copyfile(ROOT / "skills/teacher-game/assets/spec-examples/c-survival-history.json", SCRATCH / "game.json")
        r = run([ROOT / "skills/teacher-game/scripts/build.py", "--spec", "game.json", "--out", "게임.html", "--review"], self.ENV)
        out = r.stdout + r.stderr
        self.assertEqual(r.returncode, 2, out[-1500:])
        self.assertIn("PARTIAL", out)
        self.assertNotIn("Traceback", out)
        self.assertTrue((SCRATCH / "게임.html").is_file())
        self.assertEqual(out.count(workdir.NO_BROWSER + " "), 1)
        self.assertFalse((SCRATCH / workdir.WORK_NAME).exists())

    def test_webapp_tool_and_web_deck_do_not_crash(self):
        shutil.copyfile(ROOT / "skills/teacher-studio/assets/webapp/examples/speed-sim.json", SCRATCH / "app.json")
        shutil.copyfile(ROOT / "skills/teacher-class-tools/assets/spec-examples/a-timer-5min.json", SCRATCH / "tool.json")
        shutil.copyfile(ROOT / "skills/teacher-slides/assets/spec-examples/context/class-light-reflection.json", SCRATCH / "deck.json")
        for args in ([ROOT / "skills/teacher-studio/scripts/build_webapp.py", "--spec", "app.json", "--out", "app.html", "--shot", "app.png"],
                     [ROOT / "skills/teacher-class-tools/scripts/build_tool.py", "--spec", "tool.json", "--out", "tool.html"],
                     [ROOT / "skills/teacher-slides/scripts/deck.py", "--spec", "deck.json", "--out", "deck.html", "--review", "rv"]):
            r = run(args, self.ENV)
            out = r.stdout + r.stderr
            self.assertEqual(r.returncode, 2, f"{args[0].name}: {out[-1200:]}")
            self.assertIn("PARTIAL", out)
            self.assertNotIn("Traceback", out)
            self.assertNotIn("not installed", out, "a blocked browser must not read as a missing install")

    def test_pdf_says_what_to_do_instead(self):
        shutil.copyfile(ROOT / "skills/teacher-docs/assets/examples/notice-field-trip.json", SCRATCH / "n.json")
        r = run([ROOT / "skills/teacher-docs/scripts/docs.py", "make", "--spec", "n.json", "--out", "n.pdf"], self.ENV)
        self.assertIn("Ctrl+P", r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stdout + r.stderr)
        r = run([ROOT / "skills/teacher-docs/scripts/docs.py", "make", "--spec", "n.json", "--out", "n.hwpx"], self.ENV)
        self.assertEqual(r.returncode, 0, (r.stdout + r.stderr)[-800:])
        self.assertNotIn(workdir.NO_BROWSER, r.stdout, "a HWPX needs no browser: no notice")


class Installer(unittest.TestCase):
    def test_setup_does_not_stage_in_a_private_folder(self):
        src = (ROOT / "scripts" / "setup.py").read_text(encoding="utf-8")
        self.assertIsNone(BANNED.search("\n".join(ln for ln in src.splitlines() if not ln.lstrip().startswith("#"))))

    @unittest.skipUnless(os.name == "nt", "Windows permissions")
    def test_codex_install_is_readable_by_a_security_box(self):
        home = SCRATCH / "home"
        home.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, SCRATCH, True)
        r = run([ROOT / "scripts" / "setup.py", "--agent", "codex"], {"USERPROFILE": str(home), "HOME": str(home), "TEACHER_STUDIO_HOME": str(home / ".teacher-studio")}, cwd=ROOT)
        skill = home / ".agents" / "skills" / "teacher-studio"
        self.assertTrue((skill / "SKILL.md").is_file(), (r.stdout + r.stderr)[-800:])
        for target in (skill, skill / "SKILL.md", skill / "scripts" / "studio.py"):
            acl = subprocess.run(["icacls", str(target)], capture_output=True, text=True, errors="replace").stdout
            self.assertIn("(I)", acl, f"{target.name}: permissions must be inherited, not owner-only")
        self.assertEqual([p.name for p in (home / ".agents").iterdir() if p.name.startswith(".teacher-studio-")], [])


class FloorNotCeiling(unittest.TestCase):
    def test_skill_text_says_floor(self):
        for rel in ("shared/content/CONTENT-RULES.md", "skills/teacher-studio/SKILL.md", "skills/teacher-game/SKILL.md", "skills/teacher-slides/SKILL.md",
                    "skills/teacher-class-tools/SKILL.md", "skills/teacher-docs/SKILL.md", "skills/teacher-studio/references/webapp.md"):
            t = (ROOT / rel).read_text(encoding="utf-8").lower()
            self.assertTrue("floor, not ceiling" in t or "floor, not a ceiling" in t or "floor, not the ceiling" in t, rel)

    def test_no_browser_is_explained_where_it_is_printed(self):
        for rel in ("skills/teacher-studio/SKILL.md", "skills/teacher-game/SKILL.md", "skills/teacher-slides/SKILL.md", "skills/teacher-class-tools/SKILL.md",
                    "skills/teacher-docs/SKILL.md", "skills/teacher-studio/references/webapp.md"):
            self.assertIn("NO-BROWSER", (ROOT / rel).read_text(encoding="utf-8"), rel)

    def test_release_status_rule_was_left_for_the_owner(self):
        t = (ROOT / "shared/content/CONTENT-RULES.md").read_text(encoding="utf-8")
        self.assertIn("Any blocking fact still 「확인 필요」, or user material that conflicts with an official source → the output is a **「교사 초안」**.", t)
        d = (ROOT / "skills/teacher-docs/references/content-docs.md").read_text(encoding="utf-8")
        self.assertIn("Missing fact → ask or mark 「〈확인 필요〉」 visibly; never fill with a plausible guess.", d)


if __name__ == "__main__":
    unittest.main(verbosity=1)
