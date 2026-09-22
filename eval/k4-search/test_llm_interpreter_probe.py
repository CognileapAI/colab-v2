"""Offline checks for the LLM interpreter probe. No network, no model, no dev access."""
import json
import unittest
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / 'services/ai-service/src'))

import llm_interpreter_probe as probe  # noqa: E402
from colab_ai.app.interpret import LlmQueryInterpreter  # noqa: E402


class FakeTransport:
    def __init__(self, raw):
        self.raw = raw
        self.calls = []

    def __call__(self, payload):
        assert payload['messages'][0]['role'] == 'system'
        self.calls.append(dict(model='fake', seconds=0.01, structured=True, raw=self.raw))
        return self.raw


class ProbeTests(unittest.TestCase):
    def test_product_parser_reads_three_values_and_records_call(self):
        t = FakeTransport(json.dumps({'isDataQuery': True, 'terms': ['경기 남부', '식생', '자료'], 'topic': '식생·NDVI', 'rank': [1]}))
        llm = LlmQueryInterpreter(api_key='x', model='m', transport=t)
        cases = [dict(id='C1', query='경기 남부 식생 자료 찾아줘')]
        out = probe.interpret_cases(cases, llm, t)
        self.assertEqual(out[0]['terms'], ['경기 남부', '식생', '자료'])
        self.assertEqual(out[0]['source'], 'llm')
        self.assertEqual(out[0]['call']['model'], 'fake')

    def test_lint_flags_function_words_and_fabricated_terms(self):
        li = probe.lint(dict(query='경기 남부 식생 자료 찾아줘', terms=['경기 남부', '식생', '자료', 'NDVI'], topic='없는주제'))
        self.assertEqual(li['function_words'], ['자료'])
        self.assertEqual(li['not_in_query'], ['NDVI'])
        self.assertFalse(li['topic_valid'])

    def test_unreadable_answer_falls_back_to_literal_and_is_marked(self):
        t = FakeTransport('not json')
        llm = LlmQueryInterpreter(api_key='x', model='m', transport=t)
        out = probe.interpret_cases([dict(id='C1', query='강수 자료')], llm, t)
        self.assertEqual(out[0]['source'], 'literal')
        self.assertTrue(out[0]['degraded'])

    def test_strip_fences(self):
        self.assertEqual(probe.strip_fences('```json\n{"a":1}\n```'), '{"a":1}')
        self.assertEqual(probe.strip_fences('{"a":1}'), '{"a":1}')

    def test_judge_reuses_golden_assess(self):
        cases = [dict(id='C1', mode='retrieval', required=['A'], scope=['A', 'B'])]
        interps = [dict(query='q', terms=['q'], topic=None, is_data_query=True, source='llm', call=dict(seconds=0.5))]
        remote = dict(results=[dict(rows=[dict(dataset_id='B'), dict(dataset_id='A')], total=2, sql_seconds=0.01)])
        j = probe.judge(cases, interps, remote)
        self.assertEqual(j[0]['retrieval'], 'pass')
        self.assertEqual(j[0]['required_ranks'], {'A': 2})
        self.assertEqual(j[0]['model_seconds'], 0.5)


if __name__ == '__main__':
    unittest.main()
