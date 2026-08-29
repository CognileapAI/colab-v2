#!/usr/bin/env python3
"""2세대 평가셋의 **자기 시험** — 이 평가셋이 fail-closed 임을 실패 픽스처로 증명한다.

    python3 eval/s2b-alayer-g2/selftest.py

이 평가셋의 위험은 하나다 — **기대를 검색 결과에서 뽑으면 아무것도 검사하지 못하는 변경
감지기가 된다.** 그래서 여기서 시험하는 것은 「도출 규칙이 데이터를 실제로 읽는가」와
「어긋난 결과가 실제로 실패로 떨어지는가」 둘이다. 컨테이너 없이 도는 순수 시험이다.
"""
from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import common as C
import run as R

DATA = {
    "D-A": {"name": "GK-2A NDVI 충청권", "topic": "식생·NDVI", "summary": "다운스케일링으로 만들었다.", "updated_at": "t"},
    "D-B": {"name": "지상 강수 관측", "topic": "강우·강수", "summary": "국가기상위성센터 배포 자료. 강수량 단위 mm.", "updated_at": "t"},
    "D-C": {"name": "레이더 견본", "topic": "강우·강수", "summary": "반사도 견본이다.", "updated_at": "t"},
}


class 낱말접두매칭(unittest.TestCase):
    def test_이름_주제_설명_세_칸을_모두_읽는다(self):
        self.assertEqual(C.hits_for_word(DATA, "충청")["D-A"], ["name"])
        self.assertEqual(C.hits_for_word(DATA, "강우")["D-B"], ["topic"])
        self.assertEqual(C.hits_for_word(DATA, "강수량")["D-B"], ["summary"])

    def test_낱말_앞부분만_쳐도_걸린다(self):
        self.assertEqual(sorted(C.hits_for_word(DATA, "다운스케")), ["D-A"])

    def test_낱말_가운데는_걸리지_않는다(self):
        # 「국가기상위성센터」 안의 「위성」. 이것을 맞히려면 형태소 분석이 필요하고 그 수단은 폐기됐다.
        self.assertEqual(C.hits_for_word(DATA, "위성"), {})

    def test_대소문자를_가리지_않는다(self):
        self.assertEqual(sorted(C.hits_for_word(DATA, "ndvi")), sorted(C.hits_for_word(DATA, "NDVI")))

    def test_없는_낱말은_빈_집합(self):
        self.assertEqual(C.hits_for_word(DATA, "코크리깅"), {})

    def test_데이터가_바뀌면_기대도_바뀐다(self):
        """도출이 **데이터를 실제로 읽는다**는 증명. 안 바뀌면 기대가 어딘가에 박혀 있다는 뜻이다."""
        before = sorted(C.hits_for_word(DATA, "코크리깅"))
        mutated = {k: dict(v) for k, v in DATA.items()}
        mutated["D-C"]["summary"] += " 코크리깅으로 보간했다."
        self.assertEqual(before, [])
        self.assertEqual(sorted(C.hits_for_word(mutated, "코크리깅")), ["D-C"])


class 경계도출(unittest.TestCase):
    def test_상계는_합집합_하계는_교집합(self):
        item = C.derive_case({"id": "T", "kind": "derived_bounds"}, DATA, ["충청", "강수"])
        self.assertEqual(item["expected"]["상계"], ["D-A", "D-B", "D-C"])
        self.assertEqual(item["expected"]["하계"], [])

    def test_결합_규칙을_정하지_않는다(self):
        item = C.derive_case({"id": "T", "kind": "derived_bounds"}, DATA, ["충청", "강수"])
        self.assertIn("유보", item["derivation"]["규칙"])

    def test_범위_밖은_기대를_만들지_않는다(self):
        item = C.derive_case({"id": "X", "kind": "out_of_scope", "사유": "s", "이월_출처": "o"}, DATA, ["충청"])
        self.assertIsNone(item["expected"])


class 판정이_fail_closed_인가(unittest.TestCase):
    """실패 픽스처. **어긋난 결과가 실제로 실패로 떨어지는지**를 못 박는다."""

    def _exact(self):
        return C.derive_case({"id": "T", "kind": "derived_exact"}, DATA, ["충청"])

    def test_일치하면_통과(self):
        self.assertEqual(R.compare(self._exact(), ["D-A"])[0], "통과")

    def test_초과가_있으면_실패(self):
        v, why = R.compare(self._exact(), ["D-A", "D-B"])
        self.assertEqual(v, "실패")
        self.assertIn("초과", why)

    def test_결손이_있으면_실패(self):
        v, why = R.compare(self._exact(), [])
        self.assertEqual(v, "실패")
        self.assertIn("결손", why)

    def test_상계를_넘으면_실패(self):
        item = C.derive_case({"id": "T", "kind": "derived_bounds"}, DATA, ["충청"])
        self.assertEqual(R.compare(item, ["D-A", "D-C"])[0], "실패")

    def test_이름_매칭이_뒤로_밀리면_실패(self):
        item = C.derive_case({"id": "T", "kind": "derived_field_order"}, DATA, ["강수"])
        # 이름에 「강수」가 있는 D-B 가 주제에만 있는 D-C 보다 뒤에 오면 가중치 선언과 어긋난다.
        self.assertEqual(R.compare(item, ["D-C", "D-B"])[0], "실패")
        self.assertEqual(R.compare(item, ["D-B", "D-C"])[0], "통과")

    def test_비교할_쪽이_결과에_없으면_통과가_아니다(self):
        item = C.derive_case({"id": "T", "kind": "derived_field_order"}, DATA, ["강수"])
        self.assertEqual(R.compare(item, ["D-B"])[0], "실패")

    def test_범위_밖은_통과로도_실패로도_세지_않는다(self):
        item = C.derive_case({"id": "X", "kind": "out_of_scope", "사유": "s", "이월_출처": "o"}, DATA, ["충청"])
        self.assertEqual(R.compare(item, ["D-A"])[0], "범위 밖")


class 못_쟀다로_끝나는가(unittest.TestCase):
    def test_확장이_늘면_exact_는_도출을_거부한다(self):
        with self.assertRaises(C.Unmeasurable):
            C.derive_case({"id": "T", "kind": "derived_exact"}, DATA, ["충청", "강수"])

    def test_순위_비교가_성립_안_하면_도출을_거부한다(self):
        with self.assertRaises(C.Unmeasurable):
            C.derive_case({"id": "T", "kind": "derived_field_order"}, DATA, ["코크리깅"])

    def test_제품_SQL_모양이_바뀌면_못_쟀다(self):
        with self.assertRaises(C.Unmeasurable):
            R._extract("아무것도 없다", "_PREFIX_TSQUERY")


class 입력과_기대가_갈려_있는가(unittest.TestCase):
    def test_cases_json_에는_기대값이_없다(self):
        import json
        doc = json.loads(C.CASES.read_text(encoding="utf-8"))
        for case in doc["cases"]:
            self.assertNotIn("expected", case, f"{case['id']}: 입력 파일에 기대값이 들어왔다")
            self.assertNotIn("check", case, f"{case['id']}: 입력 파일에 기대값이 들어왔다")


if __name__ == "__main__":
    unittest.main(verbosity=2)
