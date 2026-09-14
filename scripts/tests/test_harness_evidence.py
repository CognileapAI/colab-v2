import importlib.util
import copy
import argparse
import os
import subprocess
import sys
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "harness_evidence", ROOT / "scripts/harness/verify_evidence.py"
)


class HarnessEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(cls.module)

    def test_ci_success_requires_exact_producers_and_real_evidence(self):
        # A green needs result cannot substitute for missing gate artifacts.
        registry = json.loads((ROOT / ".agents/ci-producers.json").read_text())["producers"]
        filters = {key: "false" for item in registry.values() for key in item["filters"]}
        needs = {item["job"]: {"result": "skipped"} for item in registry.values()}
        needs.update({"changes": {"result": "success"}, "repo-hygiene": {"result": "success"}})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(self.module.EvidenceReadinessError):
                self.module.collect_ci("1", 1, "a" * 40, "b" * 40, registry, needs, filters, root)
            for name in ("exec-bit", "exec-bit-selftest"):
                folder = root / "repo-hygiene" / name
                folder.mkdir(parents=True)
                spec = registry["repo-hygiene"]["checks"][name]
                record = {"schema": "colab-ci-check/1", "producer": "repo-hygiene", "check": name,
                          "run_id": "1", "run_attempt": 1, "commit": "a" * 40, "tree": "b" * 40,
                          "kind": "gate", "command": spec["command"], "exit": 0,
                          "counts": {"green": 1, "red_judgment": 0, "red_readiness": 0}}
                (folder / "evidence.json").write_text(json.dumps(record))
                summary = {"schema": "colab-gate-summary/1", "commit": "a" * 40, "tree": "b" * 40,
                           "counts": {"green": 1, "red_판정": 0, "red_준비": 0},
                           "gates": [{"name": name, "status": "green", "state": "green", "exit": 0}]}
                (folder / "gate-summary.json").write_text(json.dumps(summary))
            jobs = self.module.collect_ci("1", 1, "a" * 40, "b" * 40, registry, needs, filters, root)
            self.assertEqual(sum(job["state"] == "green" for job in jobs), 1)
            self.assertEqual(sum(job["state"] == "not_applicable" for job in jobs), len(registry) - 1)
            for mutation in ("missing-job", "wrong-run", "na-artifact", "na-success", "missing-filter"):
                modified_needs, modified_filters = copy.deepcopy(needs), dict(filters)
                record_path = root / "repo-hygiene/exec-bit/evidence.json"
                original = record_path.read_text()
                extra = root / "search-golden/stray/evidence.json"
                if mutation == "missing-job": del modified_needs["frontend-gates"]
                if mutation == "missing-filter": del modified_filters["frontend"]
                if mutation == "wrong-run":
                    record = json.loads(original); record["run_attempt"] = 2
                    record_path.write_text(json.dumps(record))
                if mutation == "na-artifact":
                    extra.parent.mkdir(parents=True); extra.write_text("{}")
                if mutation == "na-success": modified_needs["frontend-gates"]["result"] = "success"
                with self.subTest(mutation=mutation), self.assertRaises(self.module.EvidenceError):
                    self.module.collect_ci("1", 1, "a" * 40, "b" * 40, registry, modified_needs, modified_filters, root)
                record_path.write_text(original)
                if extra.exists(): extra.unlink()

    def test_pull_request_and_push_shas_are_distinct(self):
        pr = self.module.event_shas("pull_request", {
            "pull_request": {"base": {"sha": "a" * 40}, "head": {"sha": "b" * 40}, "merge_commit_sha": "c" * 40}
        }, "c" * 40)
        self.assertEqual(pr, {"base_sha": "a" * 40, "head_sha": "b" * 40, "merge_sha": "c" * 40})
        push = self.module.event_shas("push", {"before": "a" * 40, "after": "b" * 40}, "b" * 40)
        self.assertEqual(push, {"before_sha": "a" * 40, "after_sha": "b" * 40})

    def test_direct_check_records_actual_exit_and_counts(self):
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        for code in (0, 1, 78):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                command = [sys.executable, "-c", f"raise SystemExit({code})"]
                registry = root / "registry.json"
                registry.write_text(json.dumps({"schema": "colab-ci-producers/1", "producers": {
                    "test": {"job": "test", "filters": [], "checks": {"direct": {"kind": "direct", "command": command}}}}}))
                args = argparse.Namespace(producer="test", check="direct", check_command=command, artifact_root=root / "artifacts")
                with patch.object(self.module, "REGISTRY", registry), patch.dict(os.environ, {
                    "GITHUB_SHA": commit, "GITHUB_RUN_ID": "12", "GITHUB_RUN_ATTEMPT": "3"}):
                    self.assertEqual(self.module.record_command(args), code)
                record = json.loads((root / "artifacts/test/direct/evidence.json").read_text())
                self.assertEqual(record["exit"], code)
                self.assertEqual(record["counts"], {"green": int(code == 0), "red_judgment": int(code == 1), "red_readiness": int(code == 78)})

    def test_all_producers_include_direct_checks_and_reject_bad_artifacts(self):
        registry = self.module.load_registry()
        filters = {key: "true" for entry in registry.values() for key in entry["filters"]}
        needs = {entry["job"]: {"result": "success"} for entry in registry.values()}
        needs["changes"] = {"result": "success"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for producer, entry in registry.items():
                for check, spec in entry["checks"].items():
                    folder = root / producer / check
                    folder.mkdir(parents=True)
                    record = {"schema": "colab-ci-check/1", "producer": producer, "check": check,
                              "run_id": "1", "run_attempt": 1, "commit": "a" * 40, "tree": "b" * 40,
                              "kind": spec["kind"], "command": spec["command"], "exit": 0,
                              "counts": {"green": 1, "red_judgment": 0, "red_readiness": 0}}
                    (folder / "evidence.json").write_text(json.dumps(record))
                    if spec["kind"] == "gate":
                        summary = {"schema": "colab-gate-summary/1", "commit": "a" * 40, "tree": "b" * 40,
                                   "counts": {"green": len(spec["gates"]), "red_판정": 0, "red_준비": 0},
                                   "gates": [{"name": gate, "status": "green", "state": "green", "exit": 0} for gate in spec["gates"]]}
                        (folder / "gate-summary.json").write_text(json.dumps(summary))
            collect = lambda: self.module.collect_ci("1", 1, "a" * 40, "b" * 40, registry, needs, filters, root)
            self.assertTrue(all(job["state"] == "green" for job in collect()))
            for relative, key, value in [
                ("search-golden/search-regression/evidence.json", "exit", 78),
                ("search-golden/search-regression/evidence.json", "commit", "c" * 40),
                ("schema-gates/schema-diff/gate-summary.json", "tree", "c" * 40),
                ("gate-selftest/selftest/gate-summary.json", "gates", []),
            ]:
                path = root / relative
                original = path.read_text()
                record = json.loads(original); record[key] = value
                path.write_text(json.dumps(record))
                with self.subTest(relative=relative, key=key), self.assertRaises(self.module.EvidenceError): collect()
                path.write_text(original)
            path = root / "search-golden/search-regression/evidence.json"
            path.unlink()
            with self.assertRaises(self.module.EvidenceReadinessError): collect()

    def test_missing_sha_is_readiness_failure(self):
        with self.assertRaises(self.module.EvidenceReadinessError):
            self.module.event_shas("pull_request", {"pull_request": {}}, "c" * 40)

    def test_sha_format_and_event_checkout_must_match(self):
        for event, checkout in [({"before": "a" * 40, "after": "b" * 40}, "c" * 40),
                                ({"before": "a" * 40, "after": "short"}, "short")]:
            with self.assertRaises(self.module.EvidenceError):
                self.module.event_shas("push", event, checkout)

    def test_forged_gate_rows_and_counts_are_rejected(self):
        valid = {"schema": "colab-gate-summary/1", "commit": "a" * 40, "tree": "b" * 40,
                 "counts": {"green": 1, "red_판정": 0, "red_준비": 0},
                 "gates": [{"name": "x", "status": "green", "state": "green", "exit": 0}]}
        for target, field, value in [("counts", "green", 0), ("row", "status", "red"),
                                     ("row", "exit", 78), ("row", "state", "red_readiness")]:
            summary = copy.deepcopy(valid)
            (summary["counts"] if target == "counts" else summary["gates"][0])[field] = value
            with self.subTest(field=field), self.assertRaises(self.module.EvidenceError):
                self.module.verify_gate_summary(summary, "a" * 40, ["x"])
        malformed = copy.deepcopy(valid)
        malformed["gates"].append(None)
        with self.assertRaises(self.module.EvidenceError):
            self.module.verify_gate_summary(malformed, "a" * 40, ["x"])

    def test_cli_failure_still_writes_structured_counts(self):
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            event = root / "event.json"
            event.write_text(json.dumps({"before": "a" * 40, "after": commit}))
            output = root / "ci-evidence.json"
            result = subprocess.run([sys.executable, str(ROOT / "scripts/harness/verify_evidence.py"), "ci",
                "--event-name", "push", "--event-path", str(event), "--run-id", "1", "--run-attempt", "1",
                "--commit", commit, "--needs-json", "{}", "--filters-json", "{}",
                "--artifact-root", str(root / "artifacts"), "--output", str(output)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 78, result.stderr)
            self.assertTrue(output.is_file(), "readiness failure must leave CI evidence")
            self.assertEqual(json.loads(output.read_text())["counts"], {
                "green": 0, "red_judgment": 0, "red_readiness": 1, "not_applicable": 0})

    def test_applicable_skip_is_readiness_red_and_failure_is_judgment_red(self):
        jobs = [
            {"name": "green", "applicable": True, "result": "success", "state": "green"},
            {"name": "failed", "applicable": True, "result": "failure"},
            {"name": "skipped", "applicable": True, "result": "skipped"},
            {"name": "na", "applicable": False, "result": "skipped", "reason": "path filter"},
        ]
        evidence = self.module.build_ci_evidence("run", 2, "a" * 40, "b" * 40, {"head_sha": "a" * 40}, jobs)
        self.assertEqual(evidence["counts"], {
            "green": 1, "red_judgment": 1, "red_readiness": 1, "not_applicable": 1,
        })
        self.assertEqual(self.module.verdict(evidence), 1)

    def test_all_non_applicable_is_not_green(self):
        jobs = [{"name": "na", "applicable": False, "result": "skipped", "reason": "path filter"}]
        evidence = self.module.build_ci_evidence("run", 1, "a" * 40, "b" * 40, {"head_sha": "a" * 40}, jobs)
        self.assertEqual(self.module.verdict(evidence), 78)

    def test_gate_summary_rejects_wrong_sha_and_readiness(self):
        summary = {"schema": "colab-gate-summary/1", "commit": "a" * 40,
                   "counts": {"green": 1, "red_판정": 0, "red_준비": 0},
                   "gates": [{"name": "x", "status": "green", "state": "green", "exit": 0}]}
        self.module.verify_gate_summary(summary, "a" * 40, ["x"])
        with self.assertRaises(self.module.EvidenceError):
            self.module.verify_gate_summary(summary, "b" * 40, ["x"])
        summary["counts"]["red_준비"] = 1
        with self.assertRaises(self.module.EvidenceError):
            self.module.verify_gate_summary(summary, "a" * 40, ["x"])


if __name__ == "__main__":
    unittest.main()
