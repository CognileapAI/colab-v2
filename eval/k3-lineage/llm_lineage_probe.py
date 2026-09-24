"""K3 계보 제안 실측 러너 — 기록된 후보에 **제품 생산자**로 순위·근거·확신도를 붙인다.

`eval/k4-search/llm_interpreter_probe.py` 와 같은 골격이다. 더하는 것은 **지연 측정과
판정 계산뿐**이고, 답을 만드는 자리는 제품 `LlmLineageSuggester`·제품 파서 그대로다.

**후보는 여기서 고르지 않는다.** 후보 선정은 D3 의 주인인 core-api 의 일이라
`services/core-api/tests/test_k3_lineage_probe.py`(표식 `k3_probe`)가 일회용 DB 에서
제품 함수로 골라 JSON 으로 적어 두고, 이 러너는 **그 파일을 읽는다**. 그래서 모델 절반은
DB 없이 돈다 — 두 절반이 같은 후보를 본다는 것은 그 파일 하나가 보증한다.

대조군: 같은 자식 4건에서 **정답 부모를 후보에서 뺀다**(J5). 후보에 없는 것을 억지로
고르면 red 다 — 「모른다고 말하는가」의 유일한 직접 측정이다.

종료코드: 0 = 측정 완료 · 78 = 준비 실패(키·입력 파일·출력 충돌). **판정 게이트가 아니다.**
"""
import argparse
import hashlib
import json
import os
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'services/ai-service/src'))

from colab_ai.app import suggest as suggest_module  # noqa: E402
from colab_ai.app.main import _candidates as parse_candidates  # noqa: E402
from colab_ai.app.suggest import SYSTEM_PROMPT, LlmLineageSuggester  # noqa: E402
from colab_ai.app.suggest_wire import http_transport  # noqa: E402
from colab_ai.domains.d10_suggestion import CONFIDENCE_VALUES  # noqa: E402

#: 토큰 경계 = 글자·숫자가 아닌 모든 것. `d3_catalog._TOKEN_BOUNDARY` 와 같은 규약이다.
_TOKEN_BOUNDARY = re.compile(r"[^0-9A-Za-z가-힣]+")
#: ⚠ **문자 갈래가 바뀌는 자리도 낱말 경계다.** 한국어는 조사가 라틴 어간에 그대로 붙는다 —
#: `npy가` · `tif는` · `km와` · `202305가`. 이것을 한 토큰으로 두면 원문에 실재하는 `npy` 가
#: 「지어낸 고유명사」로 잡힌다(2026-09-24 1회차 실측에서 실제로 12건이 그렇게 잡혔다).
#: 그러면 재는 것이 모델이 아니라 **이 러너의 토크나이저**가 된다.
_SCRIPT_RUN = re.compile(r"[0-9A-Za-z]+|[가-힣]+")
#: 라틴·숫자를 품은 토큰 = 고유명사·식별자·수치가 사는 자리. intent J3 의 red 조건이 가리키는 것.
_HAS_LATIN_OR_DIGIT = re.compile(r"[0-9A-Za-z]")
_PERCENTISH = re.compile(r"[%％]|퍼센트")
_ONE_LINE = re.compile(r"^[^\n\r]+$")
ROLES = ("주입력", "보조입력")


# ═════════════════════════ 판정 함수 (시험이 있는 자리) ═════════════════════════

def rationale_tokens(text) -> list[str]:
    """근거를 조각으로 가른다 — **2글자 이상만.** 한 글자는 조사·접속사라 신호가 아니다."""
    out: list[str] = []
    for raw in _TOKEN_BOUNDARY.split(text or ""):
        for piece in _SCRIPT_RUN.findall(raw):
            token = piece.casefold()
            if len(token) >= 2 and token not in out:
                out.append(token)
    return out


def _text_of(*values) -> str:
    return " ".join(str(v) for v in values if v is not None).casefold()


def _candidate_text(candidate: dict) -> str:
    return _text_of(*candidate.values())


def _upload_text(case: dict) -> str:
    """업로드 쪽 원문 — 모델이 실제로 받은 것만(`file` · `datasetNameDraft` · `subject`)."""
    return _text_of(*(case.get('file_meta') or {}).values(),
                    case.get('dataset_name_draft'), case.get('subject'))


def grounding(rationale, candidate: dict, case: dict) -> dict:
    """근거의 조각이 **그 후보의 메타 또는 업로드 메타 원문에 부분문자열로 실재하는가.**

    두 갈래로 센다.
      · `hard` — 라틴·숫자를 품은 토큰(고유명사·식별자·수치). **intent J3 의 red 대상**이다.
      · `soft` — 순 한글 토큰. 한국어 서술어·연결어가 여기 떨어진다(`만든`·`같은`).
        엄격 판정(`strict_ok`)에는 세지만 red 조건과는 갈라 적는다 — 접으면 「지어낸
        고유명사」와 「어미가 붙은 서술어」가 한 수치가 되고, 그 수치는 아무 말도 못 한다.
    """
    cand_text = _candidate_text(candidate)
    up_text = _upload_text(case)
    tokens = rationale_tokens(rationale)
    missing = [t for t in tokens if t not in cand_text and t not in up_text]
    hard = [t for t in missing if _HAS_LATIN_OR_DIGIT.search(t)]
    return dict(tokens=len(tokens), missing=missing, hard=hard,
                soft=[t for t in missing if t not in hard],
                upload_only=[t for t in tokens if t not in cand_text and t in up_text],
                ok=not hard, strict_ok=not missing)


def rank_of(parent_id, suggestions) -> int | None:
    """제안 순서에서의 순위(1부터). 같은 ID 가 두 번 와도 **첫 자리만** 센다."""
    for index, item in enumerate(suggestions):
        if item.get('parent_dataset_id') == parent_id:
            return index + 1
    return None


def edge_hits(case: dict, suggestions) -> list[dict]:
    """엣지(자식×부모) 단위 적중. **정답 0건이면 빈 목록**이지 실패가 아니다."""
    out = []
    for parent in case.get('parents') or []:
        rank = rank_of(parent['parent_dataset_id'], suggestions)
        picked = suggestions[rank - 1] if rank else None
        out.append(dict(parent_dataset_id=parent['parent_dataset_id'],
                        parent_name=parent['parent_name'], parent_role=parent['parent_role'],
                        rank=rank, hit1=rank == 1, hit3=rank is not None and rank <= 3,
                        confidence=(picked or {}).get('confidence'),
                        suggested_parent_role=(picked or {}).get('suggested_parent_role'),
                        rationale=(picked or {}).get('rationale')))
    return out


def read_raw(raw) -> list[dict]:
    """**응답 바이트**에서 제안 장들을 읽는다 — 제품 파서가 버리기 *전*의 모습이다."""
    body = (raw or "").strip()
    if body.startswith('```'):
        body = body.split('\n', 1)[1] if '\n' in body else ''
        if body.rstrip().endswith('```'):
            body = body.rstrip()[:-3]
    try:
        parsed = json.loads(body)
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(parsed, dict) or not isinstance(parsed.get('suggestions'), list):
        return []
    return [item for item in parsed['suggestions'] if isinstance(item, dict)]


def format_violations(item: dict) -> list[str]:
    """규격 위반 — 확신도 enum · 근거 공란 · 근거 여러 줄 · 퍼센트 · 역할 enum (J7)."""
    out = []
    if item.get('confidence') not in CONFIDENCE_VALUES:
        out.append('confidence_enum')
    rationale = item.get('rationale')
    if not isinstance(rationale, str) or not rationale.strip():
        out.append('rationale_blank')
    elif not _ONE_LINE.match(rationale):
        out.append('rationale_multiline')
    if isinstance(rationale, str) and _PERCENTISH.search(rationale):
        out.append('percent')
    role = item.get('suggestedParentRole')
    if role is not None and role not in ROLES:
        out.append('role_enum')
    return out


def outside_ids(raw_items, case: dict) -> list[str]:
    """응답 ID − 요청 후보 ID (J6). **ID 가 없는 장은 여기서 세지 않는다** — 규격 위반 쪽이다."""
    allowed = {c['datasetId'] for c in case['candidates']}
    return [i['parentDatasetId'] for i in raw_items
            if isinstance(i.get('parentDatasetId'), str) and i['parentDatasetId'] not in allowed]


def without_true_parents(case: dict) -> dict:
    """대조군 한 건 — **정답 부모를 후보에서 뺀다.** 원본은 건드리지 않는다."""
    drop = {p['parent_dataset_id'] for p in case.get('parents') or []}
    control = dict(case, group='control',
                   candidates=[dict(c) for c in case['candidates'] if c['datasetId'] not in drop],
                   removed_candidate_ids=sorted(drop))
    return control


def calibration(rows) -> dict:
    """확신도 3값 × 정오 2값 교차표 (J4). 제안 0건이어도 표는 선다."""
    table = {value: {'correct': 0, 'wrong': 0} for value in CONFIDENCE_VALUES}
    for row in rows:
        truth = set(row.get('true_parent_ids') or [])
        for item in row.get('suggestions') or []:
            bucket = table.get(item.get('confidence'))
            if bucket is None:
                continue          # enum 밖은 J7 이 센다 — 여기서 두 번 세지 않는다
            bucket['correct' if item.get('parent_dataset_id') in truth else 'wrong'] += 1
    return table


def determinism(passes) -> dict:
    """같은 입력 2회의 답이 몇 가지였나 (J9 · 기록만). 1 = 같다."""
    seen: dict[str, set] = {}
    for rows in passes:
        for row in rows:
            signature = tuple((s.get('parent_dataset_id'), s.get('confidence'),
                               s.get('suggested_parent_role')) for s in row['suggestions'])
            seen.setdefault(row['child_dataset_id'], set()).add(signature)
    return {child: len(values) for child, values in seen.items()}


# ═══════════════════════════════ 전송·실행 ═══════════════════════════════════

class RecordingTransport:
    """**제품 전송을 감싼다.** 더하는 것은 지연·원문·예외 기록뿐이다."""

    def __init__(self, send, model: str) -> None:
        self._send = send
        self._model = model
        self.calls: list[dict] = []

    def __call__(self, payload: dict) -> str:
        started = time.perf_counter()
        try:
            text = self._send(payload)
        except BaseException as exc:
            self.calls.append(dict(model=self._model, seconds=time.perf_counter() - started,
                                   raw=None, error=type(exc).__name__))
            raise
        self.calls.append(dict(model=self._model, seconds=time.perf_counter() - started,
                               raw=text, error=None))
        return text


class FakeTransport(RecordingTransport):
    """시험 전용 — 고정 응답 하나, 또는 던질 예외 하나."""

    def __init__(self, raw) -> None:
        def send(_payload):
            if isinstance(raw, BaseException):
                raise raw
            return raw
        super().__init__(send, 'fake')


def build_suggester(model: str, transport, timeout: float) -> LlmLineageSuggester:
    """**제품 생산자 그대로.** 키는 전송이 이미 들고 있으므로 자리만 채운다."""
    return LlmLineageSuggester(api_key='via-transport', model=model,
                               transport=transport, timeout_seconds=timeout)


def run_case(case: dict, suggester: LlmLineageSuggester, transport) -> dict:
    """자식 한 건 = 모델 왕복 한 번. **답을 만드는 자리는 제품이다.**"""
    candidates = parse_candidates(case['candidates'])
    if isinstance(candidates, str):
        raise ValueError(f"후보가 계약 밖이다: {candidates}")
    before = len(transport.calls)
    outcome = suggester.suggest(file_meta=case['file_meta'], candidates=candidates,
                                dataset_name_draft=case.get('dataset_name_draft'),
                                subject=case.get('subject'))
    call = transport.calls[before] if len(transport.calls) > before else {}
    raw_items = read_raw(call.get('raw'))
    suggestions = [dict(parent_dataset_id=s.parent_dataset_id,
                        parent_dataset_name=s.parent_dataset_name,
                        parent_processing_level=s.parent_processing_level,
                        confidence=s.confidence, rationale=s.rationale,
                        suggested_parent_role=s.suggested_parent_role)
                   for s in outcome.suggestions]
    by_id = {c['datasetId']: c for c in case['candidates']}
    for item in suggestions:
        item['grounding'] = grounding(item['rationale'], by_id[item['parent_dataset_id']], case)
    return dict(
        id=case['id'], child_dataset_id=case['child_dataset_id'], child_name=case['child_name'],
        group=case.get('group', 'main'), candidate_count=len(case['candidates']),
        candidate_ids=[c['datasetId'] for c in case['candidates']],
        true_parent_ids=[p['parent_dataset_id'] for p in case.get('parents') or []],
        suggestions=suggestions, empty_declaration=outcome.empty_declaration,
        raw=call.get('raw'), seconds=call.get('seconds'), error=call.get('error'),
        raw_suggestions=len(raw_items), dropped=len(raw_items) - len(suggestions),
        outside_candidate_ids=outside_ids(raw_items, case),
        format_violations=[dict(index=k, kinds=v)
                           for k, v in enumerate(map(format_violations, raw_items)) if v],
        edges=edge_hits(case, suggestions))


def judge(main_passes, control_passes, timeout: float) -> dict:
    """J2~J9 를 한 벌로 센다. **수치로 합격/불합격을 가르지 않는다** — 러너는 재기만 한다."""
    rows = [row for passes in (main_passes, control_passes) for rows_ in passes for row in rows_]
    edges = [edge for rows_ in main_passes for row in rows_ for edge in row['edges']]
    per_pass = [dict(edges=len(sum((row['edges'] for row in rows_), [])),
                     hit1=sum(e['hit1'] for row in rows_ for e in row['edges']),
                     hit3=sum(e['hit3'] for row in rows_ for e in row['edges']))
                for rows_ in main_passes]
    grounds = [s['grounding'] for rows_ in main_passes for row in rows_ for s in row['suggestions']]
    seconds = [row['seconds'] for row in rows if row['seconds'] is not None]
    return dict(
        J2_hit=dict(per_pass=per_pass, edges_per_pass=len(edges) // max(1, len(main_passes))),
        J3_grounding=dict(
            suggestions=len(grounds),
            hard_violations=sum(len(g['hard']) for g in grounds),
            hard_suggestions=sum(1 for g in grounds if g['hard']),
            soft_violations=sum(len(g['soft']) for g in grounds),
            strict_clean=sum(1 for g in grounds if g['strict_ok']),
            hard_tokens=sorted({t for g in grounds for t in g['hard']}),
            soft_tokens=sorted({t for g in grounds for t in g['soft']})),
        J4_calibration=calibration([row for rows_ in main_passes for row in rows_]),
        J5_control=dict(
            per_pass=[dict(cases=len(rows_), empty=sum(1 for row in rows_ if not row['suggestions']),
                           non_empty=[row['child_dataset_id'] for row in rows_ if row['suggestions']])
                      for rows_ in control_passes]),
        J6_outside=dict(ids=sorted({i for row in rows for i in row['outside_candidate_ids']}),
                        count=sum(len(row['outside_candidate_ids']) for row in rows),
                        dropped_by_parser=sum(row['dropped'] for row in rows)),
        J7_format=dict(violations=sum(len(row['format_violations']) for row in rows),
                       kinds=sorted({k for row in rows for v in row['format_violations']
                                     for k in v['kinds']})),
        J8_latency=dict(calls=len(seconds), timeout_seconds=timeout,
                        min=min(seconds) if seconds else None,
                        median=statistics.median(seconds) if seconds else None,
                        max=max(seconds) if seconds else None,
                        over_timeout=sum(1 for s in seconds if s > timeout),
                        transport_errors=sorted({row['error'] for row in rows if row['error']})),
        J9_determinism=dict(main=determinism(main_passes), control=determinism(control_passes)))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rejudge(recorded_run: dict, cases, timeout: float) -> dict:
    """기록된 실측에 **판정 함수만 다시 건다.** 모델 호출 0회.

    판정 함수의 결함을 고쳤을 때 모델을 다시 부르면 답까지 바뀌어, 고친 것이 판정인지
    모델의 기분인지 갈리지 않는다. 그래서 **원문은 그대로 두고 판정만** 다시 건다.
    """
    by_child = {case['child_dataset_id']: case for case in cases}
    for key in ('main_passes', 'control_passes'):
        for rows in recorded_run[key]:
            for row in rows:
                case = dict(by_child[row['child_dataset_id']], group=row['group'])
                by_id = {c['datasetId']: c for c in case['candidates']}
                for item in row['suggestions']:
                    item['grounding'] = grounding(
                        item['rationale'], by_id[item['parent_dataset_id']], case)
    recorded_run['judgement'] = judge(recorded_run['main_passes'],
                                      recorded_run['control_passes'], timeout)
    return recorded_run


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidates', type=Path, required=True,
                    help='core-api 가 고른 후보 기록(`test_k3_lineage_probe.py` 산출)')
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--model', default='gpt-5.6-luna')
    ap.add_argument('--repeats', type=int, default=2, help='같은 입력 반복 횟수(J9)')
    ap.add_argument('--timeout', type=float, default=8.0, help='제품 모델 timeout(초)')
    ap.add_argument('--base-url', default='https://api.openai.com/v1/chat/completions')
    ap.add_argument('--rejudge', type=Path,
                    help='기록된 실측 JSON 에 판정 함수만 다시 건다 — 모델 호출 0회')
    args = ap.parse_args()
    if args.output.exists():
        print('Preparation failure: output already exists; choose a new run path')
        return 78
    try:
        recorded = json.loads(args.candidates.read_text())
        cases = recorded['cases']
        edges = sum(len(c['parents']) for c in cases)
        if len(cases) != 4 or edges != 6:
            raise ValueError(f'unexpected case count: children={len(cases)} edges={edges}')
        if args.rejudge:
            # **모델을 부르지 않는다.** 원문은 기록된 그대로 두고 판정만 다시 건다.
            result = rejudge(json.loads(args.rejudge.read_text()), cases, args.timeout)
            result['rejudged_from'] = str(args.rejudge)
            result['rejudged_runner_sha256'] = _sha256(Path(__file__))
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + '\n')
            print(json.dumps(dict(rejudged=str(args.rejudge), model_calls=0,
                                  J3_hard=result['judgement']['J3_grounding']['hard_violations'],
                                  output=str(args.output)), ensure_ascii=False))
            return 0

        key = os.environ.get('OPENAI_API_KEY')
        if not key:
            raise RuntimeError('OPENAI_API_KEY missing')

        transport = RecordingTransport(
            http_transport(base_url=args.base_url, api_key=key, timeout=args.timeout), args.model)
        suggester = build_suggester(args.model, transport, args.timeout)
        repeats = max(1, args.repeats)
        controls = [without_true_parents(case) for case in cases]
        main_passes = [[run_case(case, suggester, transport) for case in cases]
                       for _ in range(repeats)]
        control_passes = [[run_case(case, suggester, transport) for case in controls]
                          for _ in range(repeats)]

        result = dict(
            kind='K3 계보 제안 실측 — 기록된 후보에 제품 LlmLineageSuggester 로 순위·근거·확신도를 '
                 '붙인다. 후보 선정은 core-api(재생 시험)의 몫이고 여기서 하지 않는다. 판정 게이트가 아니다',
            model=args.model, repeats=repeats, timeout_seconds=args.timeout,
            candidates_source=str(args.candidates.relative_to(ROOT)
                                  if args.candidates.is_absolute() and args.candidates.is_relative_to(ROOT)
                                  else args.candidates),
            candidates_sha256=_sha256(args.candidates),
            candidates_local_sha=recorded.get('local_sha'),
            sample_limits=recorded.get('sample_limits'),
            strategy=recorded.get('strategy'), k=recorded.get('k'),
            system_prompt_sha256=hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
            suggester_sha256=_sha256(Path(suggest_module.__file__)),
            runner_sha256=_sha256(Path(__file__)),
            local_sha=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            model_calls=len(transport.calls),
            control_removed={c['child_dataset_id']: c['removed_candidate_ids'] for c in controls},
            judgement=judge(main_passes, control_passes, args.timeout),
            main_passes=main_passes, control_passes=control_passes, calls=transport.calls)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + '\n')
        j = result['judgement']
        print(json.dumps(dict(model=args.model, model_calls=len(transport.calls),
                              J2=j['J2_hit']['per_pass'], J3_hard=j['J3_grounding']['hard_violations'],
                              J5=j['J5_control']['per_pass'], J6=j['J6_outside']['count'],
                              J7=j['J7_format']['violations'], J8_over=j['J8_latency']['over_timeout'],
                              output=str(args.output)), ensure_ascii=False))
        return 0
    except Exception as exc:
        print('Preparation failure:', type(exc).__name__, str(exc)[:200])
        return 78


if __name__ == '__main__':
    raise SystemExit(main())
