"""Eval results are bound to a configuration hash (spec S-HARNESS-E0-EVAL-GATE-20260926 §4.1 · §4.3).

⑴ same tree twice = same hash
⑵ a byte inside the hash set, a symlink target, or a link text changes the hash
⑶ files outside the hash set (product code, eval results) do not
⑷ an untracked, non-ignored hook file changes the hash
+ verify rules: candidate selection · previous result selection · regression · readiness (78).
"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PATHS_FILE = ROOT / "eval/harness/config-paths.txt"
_SPEC = importlib.util.spec_from_file_location("config_hash", ROOT / "eval/harness/config_hash.py")
config_hash = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(config_hash)


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True, text=True).stdout


class FixtureRepo:
    """A throwaway git repository carrying the real canonical path list."""

    def __init__(self, case: unittest.TestCase):
        temp = tempfile.TemporaryDirectory()
        case.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        git(self.root, "init", "-q")
        self.write("eval/harness/config-paths.txt", PATHS_FILE.read_text(encoding="utf-8"))
        self.write("AGENTS.md", "rules\n")
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.write(".claude/settings.json", "{}\n")
        self.write(".claude/rules/colab-rules.md", "adapter\n")
        self.write("gates/x.sh", "echo x\n")
        self.write("scripts/harness/hooks/guard.sh", "exit 0\n")
        self.write("eval/harness/H01-a/task.md", "task\n")
        self.write("frontend/src/x.ts", "export {}\n")
        self.write(".gitignore", "__pycache__/\n.venv/\n")
        git(self.root, "add", "-A")
        git(self.root, "-c", "user.name=t", "-c", "user.email=t@example.com",
            "commit", "-q", "-m", "fixture")

    def write(self, rel: str, text: str) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def hash(self) -> str:
        return config_hash.compute(self.root)["hash"]


class ConfigHashTests(unittest.TestCase):
    def test_1_same_tree_twice_gives_same_hash_and_fields(self):
        repo = FixtureRepo(self)
        first = config_hash.compute(repo.root, selected="all", claude_version="9.9.9 (stub)")
        second = config_hash.compute(repo.root, selected="all", claude_version="9.9.9 (stub)")
        self.assertEqual(first["hash"], second["hash"])
        self.assertRegex(first["hash"], r"^[0-9a-f]{64}$")
        self.assertEqual(first["head"], git(repo.root, "rev-parse", "HEAD").strip())
        self.assertEqual(first["dirty"], [])
        self.assertEqual(first["selected"], "all")
        self.assertEqual(first["claude_version"], "9.9.9 (stub)")
        self.assertRegex(first["patterns_sha256"], r"^[0-9a-f]{64}$")
        # AGENTS.md CLAUDE.md settings rules gates hook task config-paths .gitignore? (.gitignore is outside)
        self.assertEqual(first["files"], 8)

    def test_2_byte_change_inside_the_set_changes_the_hash(self):
        repo = FixtureRepo(self)
        before = repo.hash()
        repo.write("gates/x.sh", "echo y\n")
        after = repo.hash()
        self.assertNotEqual(before, after)
        self.assertEqual(config_hash.compute(repo.root)["dirty"], ["gates/x.sh"])

    def test_2_symlink_target_and_link_text_change_the_hash(self):
        repo = FixtureRepo(self)
        repo.write("scripts/harness/hooks/real.sh", "echo real\n")
        repo.write("docs/outside.md", "outside v1\n")
        os.symlink("../scripts/harness/hooks/real.sh", repo.root / ".claude/hooks-link.sh")
        os.symlink("../../docs/outside.md", repo.root / ".claude/rules/outside.md")
        base = repo.hash()
        # target inside the set — counted through the target's own entry
        repo.write("scripts/harness/hooks/real.sh", "echo changed\n")
        inside = repo.hash()
        self.assertNotEqual(base, inside)
        # target outside the set — the link carries the target's content
        repo.write("docs/outside.md", "outside v2\n")
        outside = repo.hash()
        self.assertNotEqual(inside, outside)
        # link text only (both targets exist, same content)
        repo.write("scripts/harness/hooks/twin.sh", "echo changed\n")
        (repo.root / ".claude/hooks-link.sh").unlink()
        os.symlink("../scripts/harness/hooks/twin.sh", repo.root / ".claude/hooks-link.sh")
        with_twin = repo.hash()
        (repo.root / ".claude/hooks-link.sh").unlink()
        os.symlink("../../scripts/harness/hooks/twin.sh", repo.root / ".claude/hooks-link.sh")
        self.assertNotEqual(with_twin, repo.hash(), "a broken link must not hash like a live one")
        (repo.root / ".claude/hooks-link.sh").unlink()
        os.symlink("./../scripts/harness/hooks/twin.sh", repo.root / ".claude/hooks-link.sh")
        self.assertNotEqual(with_twin, repo.hash(), "link text is part of the hash")

    def test_2_broken_link_is_recorded_as_missing(self):
        repo = FixtureRepo(self)
        os.symlink("nowhere.md", repo.root / ".claude/rules/broken.md")
        entries = dict(config_hash.entries(repo.root))
        self.assertTrue(entries[".claude/rules/broken.md"].startswith("missing"))

    def test_3_changes_outside_the_set_keep_the_hash(self):
        repo = FixtureRepo(self)
        before = repo.hash()
        repo.write("frontend/src/x.ts", "export const y = 1\n")
        repo.write("eval/harness/results/20260101-000000/summary.md", "result\n")
        repo.write("eval/harness/results/20260101-000000/config-hash.json", "{}\n")
        repo.write("gates/__pycache__/x.cpython-312.pyc", "ignored\n")
        self.assertEqual(before, repo.hash())

    def test_3_eval_harness_tasks_are_inside_the_set(self):
        # 8라운드 판정 #5 ⓐ — the measuring tool (runner · tasks · expect) is part of the set.
        repo = FixtureRepo(self)
        before = repo.hash()
        repo.write("eval/harness/H01-a/task.md", "task v2\n")
        self.assertNotEqual(before, repo.hash())

    def test_4_untracked_hook_file_changes_the_hash(self):
        repo = FixtureRepo(self)
        before = repo.hash()
        repo.write("scripts/harness/hooks/new-guard.sh", "exit 0\n")
        after = config_hash.compute(repo.root)
        self.assertNotEqual(before, after["hash"])
        self.assertIn("scripts/harness/hooks/new-guard.sh", after["dirty"])

    def test_canonical_list_is_the_decided_set(self):
        patterns = config_hash.read_patterns(PATHS_FILE)
        for want in ("AGENTS.md", "CLAUDE.md", ".claude/**", ".agents/**", "gates/**",
                     "scripts/harness/hooks/**", "eval/harness/**", "eval/harness/config-paths.txt",
                     ":(exclude)eval/harness/results/**"):
            self.assertIn(want, patterns)
        for excluded in (".codex/**", "scripts/agent-bridge.py", "scripts/harness/**"):
            self.assertNotIn(excluded, patterns)
        self.assertNotIn(":(exclude)eval/harness/results/**", config_hash.include_patterns(PATHS_FILE))

    def test_git_failure_is_an_error_not_an_empty_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "eval/harness").mkdir(parents=True)
            shutil.copy(PATHS_FILE, root / "eval/harness/config-paths.txt")
            with self.assertRaises(config_hash.ConfigHashError):
                config_hash.compute(root)

    def test_cli_compute_writes_json(self):
        repo = FixtureRepo(self)
        result = subprocess.run(
            [sys.executable, str(ROOT / "eval/harness/config_hash.py"), "compute",
             "--root", str(repo.root), "--selected", "H01", "--claude-version", "x"],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["hash"], repo.hash())
        self.assertEqual(data["selected"], "H01")


def write_result(results: Path, run_id: str, *, green, red=(), ready=0, selected="all",
                 hash_value=None, extra_rows=()):
    out = results / run_id
    out.mkdir(parents=True)
    names = sorted(list(green) + list(red))
    rows = [f"| {n} | {'green' if n in green else '실패'} | 1.0/1.0 | 0.1/0.1 | x |" for n in names]
    rows += list(extra_rows)
    tasks = len(names) + len(extra_rows)
    (out / "summary.md").write_text(
        f"# harness eval 실측 — {run_id}\n\n"
        f"- 요약 — 과제 {tasks} · 실행 {tasks * 2} · green {len(green)} · 불안정 {len(red)} · "
        f"준비 {ready} · 초 p50 1.0/p95 1.0 · USD 합 0.1000 · 판정실패 관측 과제 {len(red)}\n\n"
        "| 과제 | 판정 | 초(1/2) | USD(1/2) | 사유 |\n|---|---|---|---|---|\n" + "\n".join(rows) + "\n",
        encoding="utf-8")
    if hash_value is not None:
        (out / "config-hash.json").write_text(
            json.dumps({"hash": hash_value, "selected": selected}), encoding="utf-8")
    return out


class VerifyTests(unittest.TestCase):
    def setUp(self):
        self.repo = FixtureRepo(self)
        self.current = self.repo.hash()
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.results = Path(temp.name)

    def verify(self, tasks=3):
        return config_hash.verify(self.repo.root, self.results, tasks)

    def test_no_result_is_readiness(self):
        write_result(self.results, "20260912-211809", green=["H01-a", "H02-b", "H03-c"])  # hashless
        code, current, detail = self.verify()
        self.assertEqual(code, 78)
        self.assertEqual(current, self.current)

    def test_match_without_regression_is_green(self):
        write_result(self.results, "20260912-211809", green=["H01-a", "H02-b"], red=["H03-c"])
        write_result(self.results, "20260926-100000", green=["H01-a", "H02-b", "H03-c"],
                     hash_value=self.current)
        code, current, detail = self.verify()
        self.assertEqual(code, 0, detail)
        self.assertIn("20260926-100000", detail)
        self.assertIn(f"hash(head)={self.current} hash(회차)={self.current}", detail)
        self.assertIn("green 3/3", detail)
        self.assertIn("직전 20260912-211809", detail)

    def test_regression_is_judgement_red_naming_the_task(self):
        write_result(self.results, "20260912-211809", green=["H01-a", "H02-b", "H03-c"])
        write_result(self.results, "20260926-100000", green=["H01-a", "H02-b"], red=["H03-c"],
                     hash_value=self.current)
        code, _, detail = self.verify()
        self.assertEqual(code, 1)
        self.assertIn("H03-c", detail)

    def test_first_result_has_no_regression_baseline(self):
        write_result(self.results, "20260926-100000", green=["H01-a", "H02-b"], red=["H03-c"],
                     hash_value=self.current)
        code, _, detail = self.verify()
        self.assertEqual(code, 0, detail)
        self.assertIn("직전 없음", detail)

    def test_selected_run_and_ready_run_are_not_candidates(self):
        write_result(self.results, "20260926-100000", green=["H02-b"], selected="H02",
                     hash_value=self.current)
        self.assertEqual(self.verify()[0], 78)
        write_result(self.results, "20260926-110000", green=["H01-a", "H02-b"], ready=1,
                     hash_value=self.current,
                     extra_rows=["| H03-c | 준비 | - | - | 시간 상한 |"])
        self.assertEqual(self.verify()[0], 78)

    def test_other_hash_or_task_count_mismatch_is_not_a_candidate(self):
        write_result(self.results, "20260926-100000", green=["H01-a", "H02-b", "H03-c"],
                     hash_value="0" * 64)
        self.assertEqual(self.verify()[0], 78)
        write_result(self.results, "20260926-110000", green=["H01-a", "H02-b"], hash_value=self.current)
        self.assertEqual(self.verify(tasks=3)[0], 78)

    def test_previous_skips_selected_runs_and_takes_the_latest_full_one(self):
        write_result(self.results, "20260912-211809", green=["H01-a", "H02-b", "H03-c"])
        write_result(self.results, "20260926-090000", green=["H01-a"], selected="H01",
                     hash_value=self.current)
        write_result(self.results, "20260926-100000", green=["H01-a", "H02-b"], red=["H03-c"],
                     hash_value=self.current)
        code, _, detail = self.verify()
        self.assertEqual(code, 1, "a smoke run must not hide the regression against the last full run")
        self.assertIn("직전 20260912-211809", detail)

    def test_latest_candidate_wins(self):
        write_result(self.results, "20260926-100000", green=["H01-a", "H02-b"], red=["H03-c"],
                     hash_value=self.current)
        write_result(self.results, "20260926-110000", green=["H01-a", "H02-b", "H03-c"],
                     hash_value=self.current)
        code, _, detail = self.verify()
        self.assertEqual(code, 0, detail)
        self.assertIn("일치 결과 20260926-110000", detail)
        self.assertIn("직전 20260926-100000", detail)

    def test_unreadable_inputs_are_readiness(self):
        out = write_result(self.results, "20260926-100000", green=["H01-a", "H02-b", "H03-c"],
                           hash_value=self.current)
        (out / "config-hash.json").write_text("{broken", encoding="utf-8")
        self.assertEqual(self.verify()[0], 78)
        (out / "config-hash.json").write_text(json.dumps({"hash": self.current, "selected": "all"}))
        (out / "summary.md").write_text("no summary line\n", encoding="utf-8")
        self.assertEqual(self.verify()[0], 78)

    def test_cli_exit_codes_and_first_field(self):
        write_result(self.results, "20260926-100000", green=["H01-a", "H02-b", "H03-c"],
                     hash_value=self.current)
        result = subprocess.run(
            [sys.executable, str(ROOT / "eval/harness/config_hash.py"), "verify", "--root",
             str(self.repo.root), "--results", str(self.results), "--tasks", "3"],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.split("\t", 1)[0], self.current)
        missing = subprocess.run(
            [sys.executable, str(ROOT / "eval/harness/config_hash.py"), "verify", "--root",
             str(self.repo.root), "--results", str(self.results / "none"), "--tasks", "3"],
            capture_output=True, text=True)
        self.assertEqual(missing.returncode, 78)


if __name__ == "__main__":
    unittest.main()
