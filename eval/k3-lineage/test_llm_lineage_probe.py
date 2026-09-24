"""러너의 판정 함수만 여는 offline 시험. **망·모델·DB 0건.**

K4 선례(`eval/k4-search/test_llm_interpreter_probe.py`)와 같은 자리다 — 실측 러너가
내는 수치는 그 자체가 산출물이라 되돌려 세지 못한다. 그래서 **오판 방지**를 여기서 본다:
정답 0건 · 후보 중복 · 순위 없음 · 빈 응답 · 지어낸 인용 · 규격 위반 한 장 ·
**구조 누수와 「참인 인용의 비부모」를 가르는 자리**(Ted 판정 2회차 1).

⚠ core-api 쪽 검증 함수를 그대로 부르므로 이 시험은 **core-api venv** 로 돈다
(`services/core-api/.venv/bin/python -m unittest`). 두 배포 단위를 한 프로세스에 올리는
것은 **측정 러너의 사정**이지 제품의 배치가 아니다 — 제품에서는 여전히 갈라져 있다.
"""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / 'services/ai-service/src'))
sys.path.insert(0, str(HERE.parents[1] / 'services/core-api/src'))

import llm_lineage_probe as probe  # noqa: E402

#: ⟨WU4 2026-09-25⟩ 스냅샷 v2 의 실제 간선(K3-LIN-003) — pred_sample ← hsr_sample(주입력) ·
#: rn15_sample(보조입력, O4 보정 뒤). 옛 픽스처의 RN15 → crop 표본 보조입력 간선은 새 코퍼스에 없다.
#: pred_sample 에는 후손이 없어 KID 는 판정 함수용 **가상 후손**이다(코퍼스 ID 아님).
PARENT = '01M39TA6QY5NEAR8ZPZ6AF9KNE'   # hsr_sample
OTHER = '01M39TB4NTBCFC8TSTNB93N5YP'    # rn15_sample
CHILD = '01M39TCARM2C2NJ8S9SA4QBSER'    # pred_sample
KID = '0000000000000000000000DESC'      # 가상 후손

CAND_A = {'datasetId': PARENT, 'name': 'hsr_sample',
          'topic': None, 'summary': 'HSR 합성 반사도 원자료를 crop 한 전처리 자료',
          'sourceLabel': None, 'processingLevel': 1,
          'crs': 'EPSG:4326', 'fileName': 'hsr_sample.npy'}
CAND_B = {'datasetId': OTHER, 'name': 'rn15_sample',
          'topic': None, 'fileName': 'rn15_sample.npy'}
FILE_META = {'fileName': 'pred_sample.npy', 'kind': '본체', 'crs': 'epsg:4326'}

#: 축 기록 — core-api 가 후보 기록에 적는 그 모양이다(`_axes_json`).
AXES = {
    PARENT: {'dataset_id': PARENT, 'file_name': 'hsr_sample.npy', 'crs': 'EPSG:4326',
             'grid': None, 'variables': [], 'period_start': None, 'period_end': None},
    OTHER: {'dataset_id': OTHER, 'file_name': 'rn15_sample.npy', 'crs': None,
            'grid': None, 'variables': [], 'period_start': None, 'period_end': None},
}


def _case(**over):
    case = dict(id='K3-LIN-003', child_dataset_id=CHILD,
                child_name='pred_sample',
                topic=None, upload_level=2, file_meta=dict(FILE_META),
                dataset_name_draft='pred_sample',
                subject=None, searched_count=30,
                candidates=[dict(CAND_A), dict(CAND_B)],
                candidate_axes={k: dict(v) for k, v in AXES.items()},
                descendant_ids=[KID], sibling_ids=[],
                parents=[dict(parent_dataset_id=PARENT, parent_name=CAND_A['name'],
                              parent_role='주입력'),
                         dict(parent_dataset_id=OTHER, parent_name=CAND_B['name'],
                              parent_role='보조입력')])
    case.update(over)
    return case


def _suggestion(parent_id=PARENT, evidence=(), **over):
    body = {'suggestionId': '01M1SCC27AN4NZD3K978YFDCVE', 'kind': '가공 전 데이터',
            'confidence': '애매', 'rationale': '근거 검증 대기',
            'parentDatasetId': parent_id, 'parentDatasetName': '이름',
            'suggestedParentRole': '주입력', 'evidence': [dict(e) for e in evidence]}
    body.update(over)
    return body


EV_FILE = {'field': 'fileName', 'uploadValue': 'pred_sample.npy',
           'candidateValue': 'hsr_sample.npy'}
EV_CRS = {'field': 'crs', 'uploadValue': 'epsg:4326', 'candidateValue': 'EPSG:4326'}
EV_FAKE = {'field': 'grid', 'uploadValue': '0.5 km', 'candidateValue': '0.5 km'}


class TokenTests(unittest.TestCase):
    def test_한_글자_조각과_구분자는_토큰이_아니다(self):
        self.assertEqual(probe.rationale_tokens('HSR 레이더 · 0 m'), ['hsr', '레이더'])

    def test_라틴_어간에_붙은_조사를_갈라_낸다(self):
        # 한국어 조사는 라틴 어간에 그대로 붙는다. 한 토큰으로 두면 원문에 실재하는
        # `npy`·`202305` 가 「지어낸 고유명사」로 잡힌다 — 1회차 실측의 오판 12건이 이것이다.
        self.assertEqual(probe.rationale_tokens('GK2A_NDVI_mean_202305.tif는'),
                         ['gk2a', 'ndvi', 'mean', '202305', 'tif'])
        self.assertEqual(probe.rationale_tokens('npy가 0.5 km와'), ['npy', 'km'])

    def test_빈_근거는_토큰_0건이다(self):
        self.assertEqual(probe.rationale_tokens(''), [])
        self.assertEqual(probe.rationale_tokens(None), [])


class GroundingTests(unittest.TestCase):
    def test_후보와_파일_메타에_있는_말만_쓰면_위반이_없다(self):
        g = probe.grounding('HSR 합성 반사도 원자료', CAND_A, _case())
        self.assertEqual(g['missing'], [])
        self.assertTrue(g['ok'])

    def test_어미가_붙으면_엄격_판정만_걸린다(self):
        g = probe.grounding('HSR 합성 반사도 원자료다', CAND_A, _case())
        self.assertEqual(g['hard'], [])
        self.assertTrue(g['ok'])
        self.assertFalse(g['strict_ok'])

    def test_지어낸_고유명사는_hard_위반이다(self):
        g = probe.grounding('MODIS 위성에서 온 자료다', CAND_A, _case())
        self.assertIn('modis', g['hard'])
        self.assertFalse(g['ok'])

    def test_다른_후보에만_있는_말은_실재가_아니다(self):
        g = probe.grounding('RN15 지상 자료', CAND_A, _case())
        self.assertIn('rn15', g['hard'])


class RankTests(unittest.TestCase):
    def test_순위는_1부터_세고_없으면_None_이다(self):
        sugg = [dict(parent_dataset_id='X'), dict(parent_dataset_id='Y')]
        self.assertEqual(probe.rank_of('Y', sugg), 2)
        self.assertIsNone(probe.rank_of('Z', sugg))

    def test_같은_ID_가_두_번_오면_첫_자리만_센다(self):
        sugg = [dict(parent_dataset_id='X'), dict(parent_dataset_id='X')]
        self.assertEqual(probe.rank_of('X', sugg), 1)

    def test_제안_0건이면_엣지는_hit_이_아니다(self):
        hits = probe.edge_hits(_case(), [])
        self.assertEqual(len(hits), 2)
        self.assertTrue(all(h['rank'] is None and not h['hit1'] and not h['hit3'] for h in hits))

    def test_정답_0건인_케이스도_터지지_않는다(self):
        self.assertEqual(probe.edge_hits(_case(parents=[]), []), [])


class RawReadTests(unittest.TestCase):
    def test_JSON_이_아니면_원시_제안_0건이다(self):
        self.assertEqual(probe.read_raw('not json'), [])
        self.assertEqual(probe.read_raw(''), [])
        self.assertEqual(probe.read_raw(json.dumps({'items': []})), [])

    def test_울타리를_친_JSON_도_읽는다(self):
        raw = '```json\n{"suggestions": [{"parentDatasetId": "X"}]}\n```'
        self.assertEqual(probe.read_raw(raw), [{'parentDatasetId': 'X'}])


class FormatTests(unittest.TestCase):
    """⭑ `WU-S3` 뒤로 **안 물은 열쇠를 보내는 것**이 위반이다 — 뜻이 뒤집힌 함수다."""

    def test_규격대로면_위반_0건이다(self):
        self.assertEqual(probe.format_violations(
            {'parentDatasetId': 'X', 'suggestedParentRole': '보조입력',
             'evidence': [dict(EV_FILE)]}), [])

    def test_묻지_않은_확신도와_근거를_보내면_센다(self):
        v = probe.format_violations({'parentDatasetId': 'X', 'confidence': '80%',
                                     'rationale': '확률 80% 로 맞다',
                                     'evidence': [dict(EV_FILE)]})
        self.assertIn('confidence_unasked', v)
        self.assertIn('confidence_enum', v)
        self.assertIn('rationale_unasked', v)
        self.assertIn('percent', v)

    def test_인용이_아예_없으면_센다(self):
        self.assertIn('evidence_missing', probe.format_violations({'parentDatasetId': 'X'}))

    def test_축_enum_밖과_빈_값을_가른다(self):
        v = probe.format_violations({'parentDatasetId': 'X', 'evidence': [
            {'field': 'score', 'uploadValue': 'a', 'candidateValue': 'b'},
            {'field': 'crs', 'uploadValue': '  ', 'candidateValue': 'b'}]})
        self.assertIn('evidence_field_enum', v)
        self.assertIn('evidence_value_shape', v)

    def test_역할이_계약_밖이면_센다(self):
        self.assertIn('role_enum', probe.format_violations(
            {'suggestedParentRole': '입력', 'evidence': [dict(EV_FILE)]}))

    def test_같은_갈래를_두_번_세지_않는다(self):
        v = probe.format_violations({'evidence': [
            {'field': 'score', 'uploadValue': 'a', 'candidateValue': 'b'},
            {'field': 'rank', 'uploadValue': 'a', 'candidateValue': 'b'}]})
        self.assertEqual(v.count('evidence_field_enum'), 1)


class OutsideTests(unittest.TestCase):
    def test_후보_밖_ID_를_센다(self):
        raw = [{'parentDatasetId': PARENT}, {'parentDatasetId': '01ZZZ'}]
        self.assertEqual(probe.outside_ids(raw, _case()), ['01ZZZ'])

    def test_ID_가_없는_장은_후보_밖으로_세지_않는다(self):
        self.assertEqual(probe.outside_ids([{'evidence': []}], _case()), [])


class ControlTests(unittest.TestCase):
    def test_대조군은_정답_부모만_빼고_입력을_건드리지_않는다(self):
        case = _case()
        control = probe.without_true_parents(case)
        self.assertEqual([c['datasetId'] for c in control['candidates']], [])
        self.assertEqual(len(case['candidates']), 2)   # 원본 무변
        self.assertEqual(control['group'], 'removed')

    def test_군_기록이_있으면_그것을_읽고_새로_고르지_않는다(self):
        case = _case(groups={'siblings': dict(
            candidates=[dict(CAND_B)], population=1, in_pool=1, survived=1,
            blocked_by_level=0, removed_by_design=0, not_in_pool=0)})
        row = probe.group_case(case, 'siblings')
        self.assertEqual([c['datasetId'] for c in row['candidates']], [OTHER])
        self.assertEqual(row['group_counts']['survived'], 1)

    def test_군_기록이_없으면_지어내지_않고_터진다(self):
        with self.assertRaises(ValueError):
            probe.group_case(_case(), 'descendants')


class LeakTests(unittest.TestCase):
    """**구조 누수의 갈래** — 어느 문이 열렸는지를 적어야 어느 WU 로 되돌릴지가 나온다."""

    def test_자기_자신과_후손을_가른다(self):
        case = _case()
        self.assertEqual(probe.leak_kind(dict(parent_dataset_id=CHILD, evidence=[EV_FILE]), case),
                         'self')
        self.assertEqual(probe.leak_kind(dict(parent_dataset_id=KID, evidence=[EV_FILE]), case),
                         'descendant')

    def test_후보_밖은_따로_센다(self):
        self.assertEqual(probe.leak_kind(dict(parent_dataset_id='01ZZZ', evidence=[EV_FILE]),
                                         _case()), 'outside_candidates')

    def test_근거가_0건인_채_살아남았으면_인용_오류다(self):
        self.assertEqual(probe.leak_kind(dict(parent_dataset_id=PARENT, evidence=[]), _case()),
                         'citation_error')

    def test_후보_안의_참인_인용은_그_밖_갈래다(self):
        # 적격이고 후보 안이고 근거도 있다 — **구조가 막기로 한 넷 중 어느 것도 아니다.**
        self.assertEqual(probe.leak_kind(dict(parent_dataset_id=PARENT, evidence=[EV_FILE]),
                                         _case()), 'other')


class CitationOracleTests(unittest.TestCase):
    def test_실재하는_인용은_오류가_아니다(self):
        errors = probe.citation_errors(
            dict(parent_dataset_id=PARENT, evidence=[dict(EV_FILE), dict(EV_CRS)]), _case())
        self.assertEqual(errors, [])

    def test_지어낸_축은_오류로_잡힌다(self):
        errors = probe.citation_errors(
            dict(parent_dataset_id=PARENT, evidence=[dict(EV_FAKE)]), _case())
        self.assertEqual([e['field'] for e in errors], ['grid'])

    def test_축_기록이_없는_후보는_전건_오류다(self):
        errors = probe.citation_errors(
            dict(parent_dataset_id='01ZZZ', evidence=[dict(EV_FILE)]), _case())
        self.assertEqual([e['why'] for e in errors], ['no_axes'])


class VerifyLikeRelayTests(unittest.TestCase):
    """**재는 파이프라인 = 제품 파이프라인**인지를 여는 자리."""

    def test_참인_인용_두_종이면_확실로_파생된다(self):
        final, counts = probe.verify_like_relay(
            [_suggestion(evidence=[EV_FILE, EV_CRS], confidence='모름')], _case())
        self.assertEqual(len(final), 1)
        self.assertEqual(final[0]['confidence'], '확실')
        self.assertEqual(counts['evidence_discarded'], 0)
        # 모델이 보낸 확신도는 **읽지 않는다** — 덮어쓴다.
        self.assertNotEqual(final[0]['confidence'], '모름')

    def test_틀린_인용_한_건만_버리고_나머지로_산다(self):
        final, counts = probe.verify_like_relay(
            [_suggestion(evidence=[EV_FILE, EV_FAKE])], _case())
        self.assertEqual(len(final), 1)
        self.assertEqual(final[0]['confidence'], '애매')
        self.assertEqual(counts['evidence_claimed'], 2)
        self.assertEqual(counts['evidence_discarded'], 1)

    def test_전부_지어냈으면_제안째_버린다(self):
        final, counts = probe.verify_like_relay([_suggestion(evidence=[EV_FAKE])], _case())
        self.assertEqual(final, [])
        self.assertEqual(counts['unverified_dropped'], 1)

    def test_후보_밖_부모는_검증_전에_버린다(self):
        final, counts = probe.verify_like_relay(
            [_suggestion(parent_id='01ZZZZZZZZZZZZZZZZZZZZZZZZ', evidence=[EV_FILE])], _case())
        self.assertEqual(final, [])
        self.assertEqual(counts['outside_dropped'], 1)
        # 후보 밖으로 이미 버린 것을 **인용 오류로 두 번 세지 않는다.**
        self.assertEqual(counts['unverified_dropped'], 0)


class RuleArmTests(unittest.TestCase):
    def test_규칙_팔은_모델_없이_축_대조만으로_답한다(self):
        row = probe.run_rule_case(dict(_case(), group='main'))
        self.assertEqual(row['arm'], 'rules')
        # rn15_sample.npy 도 업로드 pred_sample.npy 와 `sample` 토큰을 공유한다(v2 실제 파일명) —
        # 축 두 종(fileName·crs)이 맞는 hsr_sample 이 앞, 한 종만 맞는 rn15_sample 이 뒤다.
        self.assertEqual([s['parent_dataset_id'] for s in row['suggestions']], [PARENT, OTHER])
        self.assertEqual(row['suggestions'][0]['confidence'], '확실')
        self.assertIsNone(row['seconds'])          # 왕복이 없다
        self.assertEqual(row['raw_suggestions'], 0)

    def test_맞는_축이_없으면_빈_제안과_사유가_남는다(self):
        # 부모가 아닌 v2 후보 — rn15 원자료(seq2). 파일명·CRS 어느 축도 업로드와 맞지 않는다.
        raw_rn15 = '01M39T979PMQKRSK3GPCNYWHH3'
        cand = {'datasetId': raw_rn15, 'name': 'rn15 15분 누적강수', 'topic': None,
                'fileName': 'sfc_grid_rn_15m_201907281430.nc'}
        axes = {raw_rn15: {'dataset_id': raw_rn15, 'file_name': 'sfc_grid_rn_15m_201907281430.nc',
                           'crs': 'WGS84 (기준 격자 파일)', 'grid': None, 'variables': [],
                           'period_start': None, 'period_end': None}}
        row = probe.run_rule_case(dict(_case(candidates=[cand], candidate_axes=axes), group='main'))
        self.assertEqual(row['suggestions'], [])
        self.assertTrue(row['empty_declaration'])


class GroupJudgementTests(unittest.TestCase):
    def _row(self, group, suggestions, candidate_count=2):
        return dict(group=group, child_dataset_id=CHILD, candidate_count=candidate_count,
                    suggestions=suggestions,
                    structural_leaks=([dict(parent_dataset_id=KID, parent_dataset_name='n',
                                            kind='descendant')] if suggestions and
                                      group in probe.STRUCTURAL_GROUPS else []),
                    true_cited_non_parents=([dict(parent_dataset_id=PARENT,
                                                  parent_dataset_name='n', evidence=['fileName'])]
                                            if suggestions and group in probe.RANKING_GROUPS
                                            else []))

    def test_구조_군에서_제안이_서면_red_다(self):
        got = probe._group_judgement([self._row('descendants', [dict(parent_dataset_id=KID)])],
                                     'descendants')
        self.assertEqual(got['verdict'], 'red')
        self.assertEqual([leak['kind'] for leak in got['leaks']], ['descendant'])

    def test_구조_군이_비면_green_이다(self):
        got = probe._group_judgement([self._row('removed_and_siblings', [])],
                                     'removed_and_siblings')
        self.assertEqual(got['verdict'], 'green')

    def test_순위_군의_비부모는_red_가_아니라_기록이다(self):
        got = probe._group_judgement([self._row('removed', [dict(parent_dataset_id=PARENT)])],
                                     'removed')
        self.assertEqual(got['verdict'], 'record')
        self.assertEqual(got['non_empty'], 1)
        self.assertEqual(len(got['true_cited_non_parents']), 1)

    def test_후보가_0건인_군은_공허한_green_임을_드러낸다(self):
        got = probe._group_judgement([self._row('descendants', [], candidate_count=0)],
                                     'descendants')
        self.assertEqual(got['verdict'], 'green')
        self.assertEqual(got['vacuous'], 1)

    def test_안_돈_군을_green_으로_적지_않는다(self):
        self.assertEqual(probe._group_judgement([], 'descendants')['verdict'], 'not_run')


class CalibrationTests(unittest.TestCase):
    def test_확신도_x_정오_교차표(self):
        rows = [dict(suggestions=[dict(parent_dataset_id=PARENT, confidence='확실'),
                                  dict(parent_dataset_id='01ZZZ', confidence='애매')],
                     true_parent_ids=[PARENT])]
        table = probe.calibration(rows)
        self.assertEqual(table['확실'], {'correct': 1, 'wrong': 0})
        self.assertEqual(table['애매'], {'correct': 0, 'wrong': 1})
        self.assertEqual(table['모름'], {'correct': 0, 'wrong': 0})

    def test_제안_0건이면_표가_비어도_터지지_않는다(self):
        self.assertEqual(probe.calibration([]),
                         {'확실': {'correct': 0, 'wrong': 0}, '애매': {'correct': 0, 'wrong': 0},
                          '모름': {'correct': 0, 'wrong': 0}})


class DeterminismTests(unittest.TestCase):
    def _one(self, group, confidence):
        return [dict(group=group, child_dataset_id='C1',
                     suggestions=[dict(parent_dataset_id='X', confidence=confidence,
                                       suggested_parent_role='주입력')])]

    def test_두_회차가_같으면_갈린_자식_0건이다(self):
        one = self._one('main', '확실')
        self.assertEqual(probe.determinism([one, one]), {'main:C1': 1})

    def test_확신도만_갈려도_갈린_것으로_센다(self):
        self.assertEqual(probe.determinism([self._one('main', '확실'), self._one('main', '애매')]),
                         {'main:C1': 2})

    def test_군이_다르면_다른_칸에_센다(self):
        # 같은 자식이라도 **군이 다르면 다른 입력**이다 — 한 칸에 접으면 언제나 「갈렸다」가 된다.
        self.assertEqual(probe.determinism([self._one('main', '확실')
                                            + self._one('removed', '확실')]),
                         {'main:C1': 1, 'removed:C1': 1})


class SuggesterTests(unittest.TestCase):
    """제품 생산자를 **그대로** 세우고 전송만 감싼다 — 판정이 아니라 배선 확인이다."""

    def test_제품_파서와_core_api_검증이_이어져_돈다(self):
        raw = json.dumps({'suggestions': [
            {'parentDatasetId': PARENT, 'suggestedParentRole': '주입력',
             'evidence': [dict(EV_FILE), dict(EV_CRS)]},
            {'parentDatasetId': '01ZZZZZZZZZZZZZZZZZZZZZZZZ', 'suggestedParentRole': '주입력',
             'evidence': [dict(EV_CRS)]}]})
        transport = probe.FakeTransport(raw)
        row = probe.run_model_case(dict(_case(), group='main'),
                                   probe.build_suggester('m', transport, 8.0), transport)
        self.assertEqual([s['parent_dataset_id'] for s in row['suggestions']], [PARENT])
        self.assertEqual(row['suggestions'][0]['confidence'], '확실')
        self.assertEqual(row['raw_suggestions'], 2)
        self.assertEqual(row['outside_candidate_ids'], ['01ZZZZZZZZZZZZZZZZZZZZZZZZ'])
        self.assertIsNotNone(row['seconds'])

    def test_지어낸_인용만_단_제안은_최종_응답에_서지_않는다(self):
        raw = json.dumps({'suggestions': [
            {'parentDatasetId': PARENT, 'suggestedParentRole': '주입력',
             'evidence': [dict(EV_FAKE)]}]})
        transport = probe.FakeTransport(raw)
        row = probe.run_model_case(dict(_case(), group='main'),
                                   probe.build_suggester('m', transport, 8.0), transport)
        self.assertEqual(row['suggestions'], [])
        self.assertEqual(row['unverified_dropped'], 1)
        self.assertEqual(row['evidence_discarded'], 1)

    def test_빈_배열이면_빈_제안과_사유가_남는다(self):
        transport = probe.FakeTransport(json.dumps({'suggestions': []}))
        row = probe.run_model_case(dict(_case(), group='main'),
                                   probe.build_suggester('m', transport, 8.0), transport)
        self.assertEqual(row['suggestions'], [])
        self.assertTrue(row['empty_declaration'])

    def test_전송이_터지면_지연과_사유가_남고_러너가_계속_돈다(self):
        transport = probe.FakeTransport(TimeoutError('timed out'))
        row = probe.run_model_case(dict(_case(), group='main'),
                                   probe.build_suggester('m', transport, 8.0), transport)
        self.assertEqual(row['suggestions'], [])
        self.assertEqual(row['error'], 'TimeoutError')
        self.assertIsNotNone(row['seconds'])


if __name__ == '__main__':
    unittest.main()
