"""LLM query-interpreter probe over the 12 golden cases — a comparison experiment.

Runs a model as the query interpreter (product SYSTEM_PROMPT, product `_read`
parser — three values only), sends the resulting terms/topic to the deployed
read-only D3 search exactly like ``golden_baseline.py --mode literal``, and
records the literal interpreter side by side. No dictionary/graph expansion,
no API/UI, no product configuration change.

Exit 0: run completed (this is a measurement, not a pass/fail gate).
Exit 78: preparation failure (missing key / SSH / SDK / output exists).
"""
import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'services/ai-service/src'))
sys.path.insert(0, str(HERE))

import golden_baseline  # noqa: E402  (REMOTE / assess reuse)
from colab_ai.app import interpret as interpreter_module  # noqa: E402
from colab_ai.app.interpret import LiteralInterpreter, LlmQueryInterpreter, SYSTEM_PROMPT  # noqa: E402
from colab_ai.ports import TOPICS  # noqa: E402

FUNCTION_WORDS = ('자료', '데이터', '찾아줘', '찾아', '검색', '보여줘', '알려줘')
OUTPUT_SCHEMA = {
    'type': 'object',
    'properties': {
        'isDataQuery': {'type': 'boolean'},
        'terms': {'type': 'array', 'items': {'type': 'string'}},
        'topic': {'anyOf': [{'type': 'string', 'enum': list(TOPICS)}, {'type': 'null'}]},
    },
    'required': ['isDataQuery', 'terms', 'topic'],
    'additionalProperties': False,
}


def strip_fences(text: str) -> str:
    body = (text or '').strip()
    if body.startswith('```'):
        body = body.split('\n', 1)[1] if '\n' in body else ''
        if body.rstrip().endswith('```'):
            body = body.rstrip()[:-3]
    return body.strip()


class AnthropicTransport:
    """Adapts the product's OpenAI-shaped payload to the Anthropic Messages API.

    The payload's system/user messages are sent unchanged; only three values
    come back, and the product `_read` parses them. Latency is recorded per call.
    """

    def __init__(self, model: str, timeout_seconds: float, client=None) -> None:
        import anthropic
        self._anthropic = anthropic
        self._client = client or anthropic.Anthropic(timeout=timeout_seconds)
        self._model = model
        self.calls: list[dict] = []
        self._structured = True

    def __call__(self, payload: dict) -> str:
        system = '\n'.join(m['content'] for m in payload['messages'] if m['role'] == 'system')
        user = [m for m in payload['messages'] if m['role'] == 'user']
        kwargs = dict(model=self._model, max_tokens=512, system=system,
                      messages=[{'role': 'user', 'content': user[-1]['content']}])
        started = time.perf_counter()
        try:
            if self._structured:
                try:
                    response = self._client.messages.create(
                        output_config={'format': {'type': 'json_schema', 'schema': OUTPUT_SCHEMA}}, **kwargs)
                except self._anthropic.BadRequestError:
                    self._structured = False   # model without structured outputs: plain JSON prompt
                    response = self._client.messages.create(**kwargs)
            else:
                response = self._client.messages.create(**kwargs)
        finally:
            elapsed = time.perf_counter() - started
        text = ''.join(getattr(b, 'text', '') for b in response.content)
        usage = getattr(response, 'usage', None)
        self.calls.append(dict(model=getattr(response, 'model', self._model), seconds=elapsed,
                               structured=self._structured, stop_reason=getattr(response, 'stop_reason', None),
                               input_tokens=getattr(usage, 'input_tokens', None),
                               output_tokens=getattr(usage, 'output_tokens', None), raw=text))
        return strip_fences(text)


class OpenAITransport:
    """Product transport (urllib, same wire shape) with latency capture. Used for luna if a key exists."""

    def __init__(self, model: str, api_key: str, timeout_seconds: float) -> None:
        self._inner = LlmQueryInterpreter(api_key=api_key, model=model, timeout_seconds=timeout_seconds)
        self._model = model
        self.calls: list[dict] = []

    def __call__(self, payload: dict) -> str:
        started = time.perf_counter()
        try:
            text = self._inner._http_transport(payload)
        finally:
            elapsed = time.perf_counter() - started
        self.calls.append(dict(model=self._model, seconds=elapsed, structured=True, raw=text))
        return text


def interpret_cases(cases, interpreter, transport):
    out = []
    for c in cases:
        before = len(transport.calls) if transport else 0
        r = interpreter.interpret(c['query'])
        call = transport.calls[before] if transport and len(transport.calls) > before else None
        out.append(dict(id=c['id'], query=c['query'], is_data_query=r.is_data_query,
                        terms=list(r.terms), topic=r.topic, source=r.source,
                        degraded=r.degraded, degraded_reason=r.degraded_reason, call=call))
    return out


def lint(interp: dict) -> dict:
    """Prompt-compliance counters. Not a quality score."""
    query = interp['query']
    terms = interp['terms']
    return dict(
        function_words=[t for t in terms if any(t.startswith(w) or t == w for w in FUNCTION_WORDS)],
        not_in_query=[t for t in terms if t not in query],
        topic_valid=interp['topic'] is None or interp['topic'] in TOPICS,
        term_count=len(terms),
    )


def run_remote(ssh_host, ssh_key, payload):
    remote_cmd = 'docker exec -i colab_v2_dev_core_api python -c ' + shlex.quote(golden_baseline.REMOTE)
    proc = subprocess.run(['ssh', '-i', ssh_key, '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
                           ssh_host, remote_cmd], input=json.dumps(payload), text=True,
                          capture_output=True, timeout=120)
    if proc.returncode:
        raise RuntimeError('remote query failed (details withheld to protect connection secrets)')
    result = json.loads(proc.stdout)
    if result['read_only'] != 'on' or len(result['results']) != len(payload['cases']):
        raise ValueError('incomplete read-only run')
    return result


def judge(cases, interps, remote):
    judgments = []
    for c, i, r in zip(cases, interps, remote['results']):
        j = golden_baseline.assess(c, r['rows'], r['total'])
        j.update(terms=i['terms'], topic=i['topic'], is_data_query=i['is_data_query'],
                 source=i['source'], total=r['total'], sql_seconds=r['sql_seconds'],
                 model_seconds=(i['call'] or {}).get('seconds'), lint=lint(i))
        judgments.append(j)
    return judgments


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--model', default='gpt-5.6-luna')
    ap.add_argument('--provider', choices=['openai', 'anthropic'], default='openai')
    ap.add_argument('--repeats', type=int, default=2, help='model interpretation passes (determinism record)')
    ap.add_argument('--timeout', type=float, default=8.0, help='product model timeout (seconds)')
    ap.add_argument('--skip-remote', action='store_true', help='interpretation only; no dev D3 query')
    args = ap.parse_args()
    if args.output.exists():
        print('Preparation failure: output already exists; choose a new run path')
        return 78
    try:
        suite = json.loads((HERE / 'golden-cases.json').read_text())
        cases = suite['cases']
        if len(cases) != 12:
            raise ValueError('unexpected case count')
        snapshot_path = ROOT / suite['snapshot']
        snapshot = json.loads(snapshot_path.read_text())
        expected = {d['id']: d['name'] for d in snapshot['datasets']}
        if args.provider == 'anthropic':
            if not (os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('ANTHROPIC_AUTH_TOKEN')):
                # SDK also resolves `ant auth login` profiles; let the first call decide.
                pass
            transport = AnthropicTransport(args.model, args.timeout)
        else:
            key = os.environ.get('OPENAI_API_KEY')
            if not key:
                raise RuntimeError('OPENAI_API_KEY missing')
            transport = OpenAITransport(args.model, key, args.timeout)
        llm = LlmQueryInterpreter(api_key='via-transport', model=args.model, transport=transport,
                                  timeout_seconds=args.timeout)
        passes = [interpret_cases(cases, llm, transport) for _ in range(max(1, args.repeats))]
        fell_back = [p['id'] for p in passes[0] if p['source'] != 'llm']
        literal = interpret_cases(cases, LiteralInterpreter(LiteralInterpreter.BY_DESIGN_REASON), None)
        determinism = {c['id']: len({tuple(p[k]['terms']) for p in passes}) for k, c in enumerate(cases)}

        result = dict(kind='LLM interpreter probe over golden 12; interpreter->deployed D3 (no expansion/API/UI); '
                           'comparison experiment, not a product change',
                      model=args.model, provider=args.provider, repeats=len(passes),
                      system_prompt_sha256=hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
                      interpreter_sha256=hashlib.sha256(Path(interpreter_module.__file__).read_bytes()).hexdigest(),
                      runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      suite_sha256=hashlib.sha256((HERE / 'golden-cases.json').read_bytes()).hexdigest(),
                      snapshot_sha256=hashlib.sha256(snapshot_path.read_bytes()).hexdigest(),
                      local_sha=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                      model_calls=len(transport.calls), fell_back_to_literal=fell_back,
                      determinism_distinct_term_sets=determinism,
                      passes=passes, literal=literal, calls=transport.calls)
        if not args.skip_remote:
            ssh_host = os.environ['COLAB_DEV_SSH']
            ssh_key = os.environ['COLAB_DEV_KEY_FILE']
            llm_cases = [dict(c, terms=p['terms'], topic=p['topic']) for c, p in zip(cases, passes[0])]
            lit_cases = [dict(c, terms=p['terms'], topic=p['topic']) for c, p in zip(cases, literal)]
            remote_llm = run_remote(ssh_host, ssh_key, dict(subject=snapshot['subject'], expected_names=expected, cases=llm_cases))
            remote_lit = run_remote(ssh_host, ssh_key, dict(subject=snapshot['subject'], expected_names=expected, cases=lit_cases))
            j_llm = judge(cases, passes[0], remote_llm)
            j_lit = judge(cases, literal, remote_lit)
            result.update(
                llm=dict(captured_at=remote_llm['captured_at'], judgments=j_llm,
                         counts=dict(Counter(j['retrieval'] for j in j_llm))),
                literal_run=dict(captured_at=remote_lit['captured_at'], judgments=j_lit,
                                 counts=dict(Counter(j['retrieval'] for j in j_lit))),
                search_code_sha256=remote_llm['search_code_sha256'],
                corpus_size=len(remote_llm['corpus']))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + '\n')
        summary = dict(model=args.model, model_calls=len(transport.calls), fell_back=len(fell_back),
                       llm=result.get('llm', {}).get('counts'), literal=result.get('literal_run', {}).get('counts'),
                       output=str(args.output))
        print(json.dumps(summary, ensure_ascii=False))
        return 0
    except Exception as exc:
        print('Preparation failure:', type(exc).__name__, str(exc)[:200])
        return 78


if __name__ == '__main__':
    raise SystemExit(main())
