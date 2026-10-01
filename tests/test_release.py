"""The small download (tools/build_release.py): it must contain everything needed to run, and nothing else."""
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build_release  # noqa: E402


class ReleaseZip(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.path, _ = build_release.build(cls.tmp)
        cls.zf = zipfile.ZipFile(cls.path)
        cls.names = {n[len("Nabd/"):] for n in cls.zf.namelist()}

    @classmethod
    def tearDownClass(cls):
        cls.zf.close()

    def test_everything_needed_to_run_is_inside(self):
        need = {"Start-Mac.command", "Start-Windows.bat", "tools/bootstrap-windows.ps1", "app.py", "LICENSE",
                "How to start.txt", "web/index.html", "web/app.js", "web/style.css", "web/vendor/chart.umd.js"}
        need |= {"tracker/" + n for n in os.listdir(os.path.join(ROOT, "tracker")) if n.endswith(".py")}
        self.assertEqual(need - self.names, set())
        html = open(os.path.join(ROOT, "web", "index.html"), encoding="utf-8").read()
        for ref in re.findall(r'(?:src|href)="([^":#/][^":#]*)"', html):  # every local file the page loads
            self.assertIn("web/" + ref, self.names)

    def test_nothing_for_developers_only(self):
        for n in self.names:
            self.assertFalse(n.startswith(("tests/", "docs/", ".github/", "data/", "runtime/")) or "__pycache__" in n, n)
        self.assertLess(os.path.getsize(self.path), 600 * 1024)

    def test_mac_launcher_is_executable_and_line_endings_kept(self):
        info = self.zf.getinfo("Nabd/Start-Mac.command")
        self.assertTrue((info.external_attr >> 16) & stat.S_IXUSR)
        self.assertNotIn(b"\r\n", self.zf.read("Nabd/Start-Mac.command"))
        for win in ("Nabd/Start-Windows.bat", "Nabd/tools/bootstrap-windows.ps1"):
            data = self.zf.read(win)
            self.assertEqual(data.count(b"\r\n"), data.count(b"\n"), win)  # every line ends in CRLF

    def test_unzipped_app_starts(self):
        out = tempfile.mkdtemp()
        self.zf.extractall(out)
        code = "import app, tracker.collect, tracker.live; print('ok')"
        res = subprocess.run([sys.executable, "-c", code], cwd=os.path.join(out, "Nabd"),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=60)
        self.assertEqual(res.stdout.strip(), "ok", res.stderr)


if __name__ == "__main__":
    unittest.main()
