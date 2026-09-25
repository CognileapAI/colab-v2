"""measure_draft_contribution 의 판별을 **고정 픽스처**로 잰다 — DB·모델 없이 돈다.

intent `2026-09-21-evidence-promotion.md` 완료 정의: 「기여 있는 사실 1건·기여 0 인 사실 1건·역전 1건」을
두 경로에서 판별하고, 측정 전후 지문 대조와 일회용이 아닌 URL 거절을 확인한다.
"""
import importlib.util
import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _tool():
    spec = importlib.util.spec_from_file_location("k4_measure_draft_contribution",
                                                  HERE / "measure_draft_contribution.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


M = _tool()

#: 사실 셋 — 기여(F_HIT) · 기여 0(F_ZERO) · 역전(F_BAD). 규칙도 셋으로 가른다.
FACTS = [
    {"fact_id": "seq01.directObservation", "seq": 1, "name": "d1", "key": "directObservation",
     "value": True, "rule": "direct-observation-from-level"},
    {"fact_id": "seq02.cadence", "seq": 2, "name": "d2", "key": "cadence", "value": "daily",
     "rule": "cadence-rule"},
    {"fact_id": "seq03.nativeResolutionM", "seq": 3, "name": "d3", "key": "nativeResolutionM",
     "value": 500.0, "rule": "native-resolution-carried"},
    {"fact_id": "seq04.interpolated", "seq": 4, "name": "d4", "key": "interpolated", "value": False,
     "rule": "interpolated-from-lineage"},
]
F_HIT, F_ZERO, F_BAD, F_INTERP = (f["fact_id"] for f in FACTS)

#: 케이스가 읽는 성분 — 경로 1 은 directObservation·cadence·nativeResolutionM, 경로 2 는 directObservation·interpolated.
CASE_READS = {
    "A": {"P-hit": frozenset({"directObservation"}), "P-cad": frozenset({"cadence"}),
          "P-res": frozenset({"nativeResolutionM"})},
    "B": {"G-hit": frozenset({"directObservation"}), "G-int": frozenset({"interpolated"})},
}


def fixture_evaluate(removed):
    """고정 픽스처 평가기: F_HIT 를 빼면 P-hit·G-hit 가 떨어지고, F_BAD 를 빼면 P-res 가 선다."""
    def cell(green):
        return {"green": green, "ranks": {}}
    return {
        "A": {"P-hit": cell(F_HIT not in removed), "P-cad": cell(True), "P-res": cell(F_BAD in removed)},
        "B": {"G-hit": cell(F_HIT not in removed), "G-int": cell(False)},
        "heldout_A": {}, "heldout_B": {"H1": cell(F_HIT not in removed)},
    }


RULES = ["direct-observation-from-level", "cadence-rule", "native-resolution-carried",
         "interpolated-from-lineage", "bbox-korea-peninsula"]


class ClassificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = M.measure(fixture_evaluate, FACTS, RULES, CASE_READS)
        cls.facts = {r["fact_id"]: r for r in cls.table["facts"]}
        cls.rules = {r["rule"]: r for r in cls.table["rules"]}

    def test_contributing_fact_on_both_paths(self):
        row = self.facts[F_HIT]
        self.assertEqual((row["green_with_A"], row["green_without_A"]), (2, 1))
        self.assertEqual((row["green_with_B"], row["green_without_B"]), (1, 0))
        self.assertEqual((row["contribution_A"], row["contribution_B"]), (1, 1))
        self.assertEqual((row["reversal_A"], row["reversal_B"]), (0, 0))
        self.assertEqual(row["flipped_case_ids_A"], ["P-hit"])
        self.assertEqual(row["flipped_case_ids_B"], ["G-hit"])
        self.assertTrue(row["제안"].startswith("1회차 관측 — 승격 케이스 기준(N=2) 충족"))
        # heldout 은 사후 확인 열에만 남고 제안에 섞이지 않는다
        self.assertEqual(row["heldout_B"]["flipped"], ["H1"])

    def test_zero_contribution_fact_is_held_not_discarded(self):
        row = self.facts[F_ZERO]
        self.assertEqual((row["contribution_A"], row["contribution_B"]), (0, 0))
        self.assertEqual((row["reversal_A"], row["reversal_B"]), (0, 0))
        self.assertTrue(row["measured_A"].startswith("측정"))
        self.assertEqual(row["measured_B"], "미측정(케이스 0)")
        self.assertIn("기여 0", row["제안"])
        self.assertNotIn("폐기", row["제안"].split("(")[0])

    def test_reversal_fact_is_proposed_for_discard_immediately(self):
        row = self.facts[F_BAD]
        self.assertEqual(row["reversal_A"], 1)
        self.assertEqual(row["reversal_case_ids_A"], ["P-res"])
        self.assertEqual(row["contribution_A"], 0)
        self.assertTrue(row["제안"].startswith("폐기 제안 — 역전"))

    def test_path_one_has_no_interpolated_predicate(self):
        row = self.facts[F_INTERP]
        self.assertEqual(row["measured_A"], "미측정(술어 없음)")
        self.assertTrue(row["measured_B"].startswith("측정"))
        self.assertEqual(self.rules["interpolated-from-lineage"]["제안"], "미측정(경로 1)·보류 — 결정 5 고정")

    def test_rule_level_fast_track(self):
        self.assertTrue(self.rules["direct-observation-from-level"]["제안"].startswith("승격 제안 — 결정 5"))
        self.assertTrue(self.rules["native-resolution-carried"]["제안"].startswith("폐기 제안"))
        self.assertEqual(self.rules["cadence-rule"]["제안"], "보류 — 기여 0")
        bbox = self.rules["bbox-korea-peninsula"]
        self.assertEqual((bbox["facts"], bbox["measured_A"], bbox["제안"]), (0, "미측정(초안 0건)", "미측정 — 초안 0건"))

    def test_baseline_summary(self):
        self.assertEqual(self.table["summary"]["A"], {"withAllDrafts": 2, "withoutAnyDraft": 2, "cases": 3})
        self.assertEqual(self.table["summary"]["B"], {"withAllDrafts": 1, "withoutAnyDraft": 0, "cases": 2})


class PathTwoPureFunctionTest(unittest.TestCase):
    """경로 2 의 실제 순수 함수로 — 초안 directObservation 이 있어야 후보에 든다."""

    def test_draft_direct_observation_includes_dataset(self):
        sec = M.conditions_module()
        criteria = sec.parse("2023년 5월 경기남부·충청을 100m로 직접 관측한 천리안 NDVI 월평균 자료")
        self.assertTrue(criteria["directObservation"])
        reviewed = {"cadence": "monthly", "region": "경기남부충청", "nativeResolutionM": 100.0,
                    "period": {"start": "2023-05-01", "end": "2023-05-31"}}

        def rows(facts):
            return [{"dataset_id": "D7", "file_id": "F7", "file_kind": "본체", "facts": facts}]
        with_draft, _ = sec.candidates(criteria, rows({**reviewed, "directObservation": True}), {"D7": {"F7"}})
        without, _ = sec.candidates(criteria, rows(reviewed), {"D7": {"F7"}})
        self.assertEqual((with_draft, without), (["D7"], []))
        self.assertEqual(M.criteria_reads(criteria) & {"directObservation"}, {"directObservation"})

    def test_probe_green_rules(self):
        probe = {"expectSeq": [1, 2], "forbidSeq": [3]}
        self.assertTrue(M.probe_green(probe, [2, 1, 9]))
        self.assertFalse(M.probe_green(probe, [1, 2, 3]))
        self.assertFalse(M.probe_green(probe, [1]))
        self.assertTrue(M.probe_green({"expectSeq": [], "forbidSeq": [], "expectEmpty": True}, []))
        self.assertFalse(M.probe_green({"expectSeq": [], "forbidSeq": [], "expectEmpty": True}, [4]))


class FingerprintTest(unittest.TestCase):
    ROWS = [("F1", 1, "reviewed", "a" * 64, "m1"), ("F2", 3, "reviewed", "b" * 64, "m2")]

    def test_unchanged_db_fingerprint_is_equal(self):
        before = M.fingerprint_digest(self.ROWS)
        after = M.fingerprint_digest(list(reversed(self.ROWS)))
        self.assertTrue(M.fingerprints_equal(before, after))

    def test_left_over_change_is_detected(self):
        before = M.fingerprint_digest(self.ROWS)
        for changed in ([("F1", 2, "reviewed", "a" * 64, "m1"), self.ROWS[1]],        # revision
                        [("F1", 1, "draft", "a" * 64, "m1"), self.ROWS[1]],           # status
                        [("F1", 1, "reviewed", "a" * 64, "m9"), self.ROWS[1]],        # facts
                        self.ROWS[:1]):                                                 # 행 삭제
            self.assertFalse(M.fingerprints_equal(before, M.fingerprint_digest(changed)), changed)


class RefusalTest(unittest.TestCase):
    def test_non_local_url_is_refused(self):
        self.assertIsNotNone(M.check_disposable_url("postgresql+psycopg://u:p@dev-db.example.com:5432/x", False))
        self.assertIsNotNone(M.check_disposable_url("postgresql+psycopg://u:p@172.17.0.5:5432/x", False))
        self.assertIsNone(M.check_disposable_url("postgresql+psycopg://u:p@localhost:5432/x", False))
        self.assertIsNone(M.check_disposable_url("postgresql+psycopg://u:p@127.0.0.1/x", False))
        self.assertIsNone(M.check_disposable_url("postgresql+psycopg://u:p@172.17.0.5:5432/x", True))

    def test_main_refuses_before_connecting(self):
        err = io.StringIO()
        with redirect_stderr(err):
            rc = M.main(["postgresql+psycopg://u:p@dev-db.example.com/x", "--output", "/nonexistent/out"])
        self.assertEqual(rc, 78)
        self.assertIn("일회용", err.getvalue())

    def test_no_arguments_is_preparation_failure(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(M.main([]), 78)


class RehearsalTest(unittest.TestCase):
    ROWS = [
        {"file_id": "F1", "dataset_id": "D1", "revision": 2, "file_revision": 1, "status": "reviewed",
         "facts": {"period": {"start": "2020-01-01", "end": "2020-12-31"}, "variable": "precipitation"},
         "source_label": "l", "source_locator": "loc", "source_text": "t"},
        {"file_id": "F2", "dataset_id": "D1", "revision": 1, "file_revision": 1, "status": "reviewed",
         "facts": {"variable": "precipitation", "platform": "ground"},
         "source_label": "l", "source_locator": "loc", "source_text": "t"},
        {"file_id": "F3", "dataset_id": "D2", "revision": 1, "file_revision": 1, "status": "reviewed",
         "facts": {"variable": "ndvi"}, "source_label": "l", "source_locator": "loc", "source_text": "t"},
    ]
    FACTS = [{"fact_id": "seq01.platform", "seq": 1, "name": "d1", "key": "platform", "value": "ground",
              "rule": "platform-from-instrument"}]

    def test_promotion_body_keeps_every_reviewed_fact(self):
        out = M.rehearse(self.ROWS, self.FACTS, "platform-from-instrument", {"D1": 1, "D2": 2})
        report = out["report"]
        self.assertTrue(report["ok"])
        self.assertEqual((report["files"], report["bodies"], report["unchanged"]), (2, 1, 1))
        self.assertEqual(report["reviewed_facts_kept"], report["reviewed_facts_before"])
        body = out["bodies"][0]["body"]
        self.assertEqual(body["facts"], {**self.ROWS[0]["facts"], "platform": "ground"})
        self.assertEqual((body["expectedRevision"], body["status"]), (2, "reviewed"))

    def test_two_rules_rehearse_together(self):
        facts = self.FACTS + [{"fact_id": "seq01.directObservation", "seq": 1, "name": "d1",
                               "key": "directObservation", "value": True,
                               "rule": "direct-observation-from-level"}]
        out = M.rehearse(self.ROWS, facts, "platform-from-instrument,direct-observation-from-level",
                         {"D1": 1, "D2": 2})
        self.assertTrue(out["report"]["ok"])
        self.assertEqual(out["bodies"][0]["body"]["facts"]["directObservation"], True)
        self.assertEqual(len(out["bodies"]), 2)

    def test_promoted_payload_moves_only_the_judged_rules(self):
        payload = {"datasets": [{
            "seq": 1, "facts": {"variable": "precipitation"}, "provenance": {"variable": "정본전재"},
            "draftFacts": {"platform": "ground", "interpolated": False},
            "draftProvenance": {"platform": "규칙 · rule:platform-from-instrument · x",
                                "interpolated": "규칙 · rule:interpolated-from-lineage · x"}}]}
        out = M.promote_payload(payload, ["platform-from-instrument"], "1회차 판정")
        row = out["datasets"][0]
        self.assertEqual(row["facts"], {"variable": "precipitation", "platform": "ground"})
        self.assertEqual(row["draftFacts"], {"interpolated": False})
        self.assertIn("rule:platform-from-instrument", row["provenance"]["platform"])
        self.assertEqual(out["promotion"]["movedFacts"], 1)
        self.assertEqual(payload["datasets"][0]["draftFacts"]["platform"], "ground")  # 원본 무변경
        payload["datasets"][0]["facts"]["platform"] = "satellite"
        with self.assertRaises(M.Refused):
            M.promote_payload(payload, ["platform-from-instrument"], "x")

    def test_collision_is_reported_not_overwritten(self):
        rows = [dict(self.ROWS[1], facts={"platform": "satellite"})]
        report = M.rehearse(rows, self.FACTS, "platform-from-instrument", {"D1": 1})["report"]
        self.assertFalse(report["ok"])
        self.assertEqual(report["collisions"], [{"file_id": "F2", "key": "platform"}])


if __name__ == "__main__":
    unittest.main()
