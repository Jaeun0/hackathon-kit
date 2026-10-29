"""키트 스크립트 자체 시험. 저장소 루트에서: python -m unittest -v
가짜 데이터(fixtures/sensor_demo)만 쓴다.
"""
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = ROOT / "skills" / "kit-tools" / "scripts"
F = ROOT / "fixtures" / "sensor_demo"
PY = sys.executable


def run(*args, cwd=None):
    p = subprocess.run([PY, *map(str, args)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=cwd)
    return p.returncode, p.stdout + p.stderr


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class KitScripts(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_profile_finds_categories_ids_duplicates(self):
        code, out = run(S / "profile.py", F / "data")
        self.assertEqual(code, 0, out)
        self.assertIn("완전 중복 행 1", out)
        self.assertIn("SPARE:2", out)          # 범주 값이 전부 보인다
        self.assertIn("ID/텍스트", out)         # 고유값 컬럼은 ID로 본다

    def test_e2e_cli_success_and_failure(self):
        cmd = f'"{PY}" "{F / "demo_cli.py"}" --input {{data}} --output {{out}}'
        code, out = run(S / "run_e2e.py", "cli", "--cmd", cmd, "--data", F / "data", "--out", self.tmp / "o.csv")
        self.assertEqual(code, 0, out)
        code, out = run(S / "run_e2e.py", "cli", "--cmd", cmd + " --fail", "--data", F / "data", "--out", self.tmp / "o2.csv")
        self.assertEqual(code, 1, out)
        self.assertIn("실패 2건", out)

    def test_e2e_server_catches_409(self):
        port = free_port()
        cmd = f'"{PY}" "{F / "demo_server.py"}" --port {{port}} --data {{data}} --bad-date 2030-03-04'
        code, out = run(S / "run_e2e.py", "server", "--cmd", cmd, "--data", F / "data", "--port", port,
                        "--path", "/api/day?date={key}", "--keys-url", "/api/dates")
        self.assertEqual(code, 1, out)
        self.assertIn("2030-03-04 → 409", out)
        self.assertIn("실패 1건", out)

    def test_e2e_paths_with_spaces(self):
        spaced = self.tmp / "ai hack" / "sensor demo"
        shutil.copytree(F, spaced)
        cmd = f'"{PY}" "{spaced / "demo_cli.py"}" --input {{data}} --output {{out}}'
        code, out = run(S / "run_e2e.py", "cli", "--cmd", cmd, "--data", spaced / "data",
                        "--out", spaced / "out dir" / "o.csv")
        self.assertEqual(code, 0, out)
        port = free_port()
        cmd = f'"{PY}" "{spaced / "demo_server.py"}" --port {{port}} --data "{{data}}"'
        code, out = run(S / "run_e2e.py", "server", "--cmd", cmd, "--data", spaced / "data", "--port", port,
                        "--path", "/api/day?date={key}", "--keys", "2030-03-01")
        self.assertEqual(code, 0, out)

    def test_holdout_shifts_dates_and_keeps_source(self):
        before = (F / "data" / "readings.csv").read_text(encoding="utf-8")
        dst = self.tmp / "ho"
        code, out = run(S / "make_holdout.py", F / "data", dst, "--config", F / "holdout.example.json")
        self.assertEqual(code, 0, out)
        self.assertEqual(before, (F / "data" / "readings.csv").read_text(encoding="utf-8"))
        text = (dst / "readings.csv").read_text(encoding="utf-8")
        self.assertIn("2030-03-08T", text)
        self.assertNotIn("2030-03-01T", text)
        self.assertTrue((dst / "HOLDOUT_LOG.md").exists())

    def test_slice_report_runs(self):
        out_csv = self.tmp / "o.csv"
        run(F / "demo_cli.py", "--input", F / "data", "--output", out_csv)
        code, out = run(S / "slice_report.py", out_csv, "--by", "zone", "--metric", "mean_value", "--weight", "readings")
        self.assertEqual(code, 0, out)
        self.assertIn("ZONE-N", out)

    @unittest.skipIf(shutil.which("git") is None, "git 없음")
    def test_check_submit_flags_dirty_repo(self):
        repo = self.tmp / "r"
        (repo / "data").mkdir(parents=True)
        (repo / "data" / "x.csv").write_text("a,b\n", encoding="utf-8")
        g = lambda *a: subprocess.run(["git", *a], cwd=repo, capture_output=True)
        g("init", "-q"); g("config", "user.email", "t@t"); g("config", "user.name", "t")
        g("add", "."); g("commit", "-qm", "init")
        code, out = run(S / "check_submit.py", cwd=repo)
        self.assertEqual(code, 0, out)
        (repo / "data" / "x.csv").write_text("a,b\nc,d\n", encoding="utf-8")
        code, out = run(S / "check_submit.py", cwd=repo)
        self.assertEqual(code, 1, out)
        self.assertIn("data/ 원본 변경", out)


if __name__ == "__main__":
    unittest.main()