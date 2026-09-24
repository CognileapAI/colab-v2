"""K3 계보 제안 실측 러너 — 기록된 후보에 **제품 파이프라인 전체**를 걸어 두 팔을 나란히 잰다.

`eval/k4-search/llm_interpreter_probe.py` 와 같은 골격이다. 더하는 것은 **지연 측정과
판정 계산뿐**이고, 답을 만드는 자리는 제품 `LlmLineageSuggester`·제품 파서·**제품 인용
검증**(`colab_core.app.relay`) 그대로다.

⭑ **⟨2026-09-24 · `WU-S6`⟩ 재는 파이프라인 = 제품 파이프라인.** 종전 러너는 ai-service
절반만 돌려 「모델이 무엇을 골랐나」를 적었는데, `WU-S2` 뒤로 **응답의 정본을 만드는 쪽은
core-api** 다 — 인용을 실제 값에 대조해 틀린 항목을 버리고, 남은 근거 종류 수에서 확신도를
파생시키고, 근거 한 줄을 다시 쓴다. 그 세 걸음을 러너가 흉내 내면 재는 것이 제품이 아니라
**러너의 사본**이 되므로, 중계가 부르는 그 함수 셋을 그대로 부른다:
`relay._within_candidates` → `relay._verified_suggestion` → `[:relay.SUGGESTION_LIMIT]`.

**후보는 여기서 고르지 않는다.** 후보 선정·적격 필터·대조군 생성은 D3 의 주인인 core-api 의
일이라 `services/core-api/tests/test_k3_lineage_probe.py`(표식 `k3_probe`)가 일회용 DB 에서
제품 함수로 하고 그 결과를 JSON 으로 적어 두며, 이 러너는 **그 파일을 읽는다**. 그래서 모델
절반은 DB 없이 돈다 — 두 절반이 같은 후보를 봤다는 것은 그 파일 하나가 보증한다.

**군 다섯 · 팔 둘.** 군은 본군 + 대조군 4종(`--groups`)이고 팔은 규칙·모델이다(`--arm`).
규칙 팔은 모델을 **한 번도 부르지 않는다** — 같은 적격 집합에 축 대조만 건다.

판정 규칙 (Ted 판정 2회차 1 · 라운드 `R-K3-STRUCTURE.md` 판정 기록)
  · `descendants`·`removed_and_siblings` 에서 **빈 제안이 아니면 구조 누수**다 → red.
    누수는 갈래를 적는다: 후손 · 자기 자신 · 후보 밖 · 인용 오류 · 그 밖.
  · `removed`·`siblings` 에서 살아남은 제안은 **참인 인용의 비부모**다 → **기록**(red 아님).
  · 최종 응답의 **인용 오류 1건이라도 red** — 검증을 통과한 근거가 실제 값과 다른 자리다.

종료코드: 0 = 측정 완료 · 78 = 준비 실패(키·입력 파일·출력 충돌). **판정 게이트가 아니다.**
"""
import argparse
import dataclasses
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
sys.path.insert(0, str(ROOT / 'services/core-api/src'))

from colab_ai.app import suggest as suggest_module  # noqa: E402
from colab_ai.app.main import _candidates as parse_candidates  # noqa: E402
from colab_ai.app.suggest import SYSTEM_PROMPT, LlmLineageSuggester  # noqa: E402
from colab_ai.app.suggest_wire import http_transport  # noqa: E402
from colab_ai.domains.d10_suggestion import CONFIDENCE_VALUES  # noqa: E402
# ⭑ **제품 core-api 쪽 절반.** 순수 함수라 DB·FastAPI 없이 선다.
from colab_core.app import relay as relay_module  # noqa: E402
from colab_core.app import rule_suggest  # noqa: E402
from colab_core.domains import d3_lineage_signals as signals  # noqa: E402

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

ARM_RULES = rule_suggest.ARM_RULES
ARM_MODEL = rule_suggest.ARM_MODEL
ARMS = (ARM_RULES, ARM_MODEL)

#: 군 이름 다섯. `test_k3_lineage_probe.GROUPS` 와 **같은 문자열**이다 — 두 벌이면 표가 갈린다.
GROUPS = ("main", "removed", "descendants", "siblings", "removed_and_siblings")
#: ⭑ **구조가 보장하기로 한 군** — 여기서 제안이 하나라도 서면 그것은 순위 문제가 아니라
#: **구조 누수**이고, 해당 WU 로 되돌린다(Ted 판정 2회차 1 · 라운드 S6).
STRUCTURAL_GROUPS = ("descendants", "removed_and_siblings")
#: 「참인 인용의 비부모」가 살아남을 수 있는 군. 미달은 red 가 아니라 **순위 한계**로 적는다.
RANKING_GROUPS = ("removed", "siblings")


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

    ⚠ ⟨`WU-S2` 뒤⟩ 최종 응답의 근거 한 줄은 **core-api 가 고정 서식으로 다시 쓴 문장**이라
    이 검사는 이제 「모델이 지어냈나」가 아니라 **「검증된 값이 원문에 실재하나」**를 잰다.
    모델의 자연어는 화면에 가지 않으므로 `raw_*` 쪽에서만 본다.

    두 갈래로 센다.
      · `hard` — 라틴·숫자를 품은 토큰(고유명사·식별자·수치). **intent J3 의 red 대상**이다.
      · `soft` — 순 한글 토큰. 한국어 서술어·연결어가 여기 떨어진다(`만든`·`같은`).
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
                        evidence_fields=[e.get('field') for e in (picked or {}).get('evidence', [])],
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
    """규격 위반 (J7). **모델에게 묻지 않기로 한 열쇠는 「있으면」 위반이다.**

    ⭑ ⟨`WU-S3` 뒤⟩ 프롬프트가 `confidence`·`rationale` 을 **묻지 않는다.** 그래서 이 함수의
    뜻이 뒤집혔다 — 종전에는 「확신도가 enum 밖인가」를 물었고 지금은 **「왜 보냈나」**를
    센다. 안 물은 것을 보내는 것은 지시를 안 읽었다는 뜻이고, 그 값은 아무도 읽지 않는다.
    인용 항목의 규격(축 enum · 두 값 문자열)도 여기서 본다.
    """
    out = []
    if 'confidence' in item:
        out.append('confidence_unasked')
        if item.get('confidence') not in CONFIDENCE_VALUES:
            out.append('confidence_enum')
    if 'rationale' in item:
        out.append('rationale_unasked')
        rationale = item.get('rationale')
        if isinstance(rationale, str) and not _ONE_LINE.match(rationale):
            out.append('rationale_multiline')
        if isinstance(rationale, str) and _PERCENTISH.search(rationale):
            out.append('percent')
    role = item.get('suggestedParentRole')
    if role is not None and role not in ROLES:
        out.append('role_enum')
    evidence = item.get('evidence')
    if evidence is None:
        out.append('evidence_missing')
    elif not isinstance(evidence, list):
        out.append('evidence_not_list')
    else:
        if len(evidence) > len(signals.EVIDENCE_FIELDS):
            out.append('evidence_over_limit')
        for entry in evidence:
            if not isinstance(entry, dict):
                out.append('evidence_item_shape')
                continue
            if entry.get('field') not in signals.EVIDENCE_FIELDS:
                out.append('evidence_field_enum')
            for key in ('uploadValue', 'candidateValue'):
                value = entry.get(key)
                if not isinstance(value, str) or not value.strip():
                    out.append('evidence_value_shape')
    seen: list[str] = []
    for kind in out:
        if kind not in seen:
            seen.append(kind)
    return seen


def outside_ids(raw_items, case: dict) -> list[str]:
    """응답 ID − 요청 후보 ID (J6). **ID 가 없는 장은 여기서 세지 않는다** — 규격 위반 쪽이다."""
    allowed = {c['datasetId'] for c in case['candidates']}
    return [i['parentDatasetId'] for i in raw_items
            if isinstance(i.get('parentDatasetId'), str) and i['parentDatasetId'] not in allowed]


def leak_kind(suggestion: dict, case: dict) -> str:
    """구조 누수 한 건의 **갈래**. Ted 판정 2회차 1 의 네 가지 + 그 밖.

    가르는 순서가 뜻이다 — 자기 자신·후손은 **적격 필터**가 막기로 한 것이고, 후보 밖은
    **`_within_candidates`**, 인용 오류는 **`_verified_suggestion`** 이 막기로 한 것이다.
    어느 문이 열렸는지를 적어야 어느 WU 로 되돌릴지가 나온다.
    """
    parent_id = suggestion.get('parent_dataset_id')
    if parent_id == case['child_dataset_id']:
        return 'self'
    if parent_id in set(case.get('descendant_ids') or ()):
        return 'descendant'
    if parent_id not in {c['datasetId'] for c in case['candidates']}:
        return 'outside_candidates'
    if not suggestion.get('evidence'):
        return 'citation_error'
    return 'other'


def citation_errors(suggestion: dict, case: dict) -> list[dict]:
    """**최종 응답의 인용 오류** (J3'). 검증을 통과한 근거를 실제 축 값에 다시 대조한다.

    ⚠ 이것은 `_verified_suggestion` 의 재탕이 아니라 **오라클**이다 — 검증기가 통과시킨
    항목을 같은 비교기로 한 번 더 세어, 「검증했다」와 「맞다」가 갈리는 자리를 드러낸다.
    1건이라도 있으면 red 다(intent 판정 기준).
    """
    upload = upload_axes_of(case)
    axes = candidate_axes_of(case, suggestion.get('parent_dataset_id'))
    if axes is None:
        return [dict(field=e.get('field'), why='no_axes') for e in suggestion.get('evidence') or ()]
    out = []
    for entry in suggestion.get('evidence') or ():
        item = signals.Evidence.from_claim(entry)
        if item is None or not signals.verify(item, upload, axes):
            out.append(dict(field=(entry or {}).get('field'), why='unverified'))
    return out


def calibration(rows) -> dict:
    """확신도 × 정오 교차표 (J4'). 파생이라 「모름」 칸은 언제나 0 이다 — 그 자리는 빈 제안이다."""
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
    """같은 입력 2회의 답이 몇 가지였나 (J9 · 기록만). 1 = 같다. 군마다 따로 센다."""
    seen: dict[str, set] = {}
    for rows in passes:
        for row in rows:
            signature = tuple((s.get('parent_dataset_id'), s.get('confidence'),
                               s.get('suggested_parent_role')) for s in row['suggestions'])
            seen.setdefault(f"{row['group']}:{row['child_dataset_id']}", set()).add(signature)
    return {key: len(values) for key, values in seen.items()}


# ═══════════════════════════ 축 되세우기 (기록 → 값) ═══════════════════════════

def _axes_kwargs(row: dict) -> dict:
    fields = {f.name for f in dataclasses.fields(signals.CandidateAxes)}
    out = {k: v for k, v in (row or {}).items() if k in fields}
    out['variables'] = tuple(out.get('variables') or ())
    return out


def upload_axes_of(case: dict) -> signals.UploadAxes:
    """**계약 본문에서 다시 만든다** — 기록된 dict 를 믿지 않고 제품 함수를 통과시킨다."""
    return signals.UploadAxes.from_file_meta(case['file_meta'])


def candidate_axes_of(case: dict, dataset_id):
    row = (case.get('candidate_axes') or {}).get(dataset_id)
    if row is None:
        return None
    return signals.CandidateAxes(**_axes_kwargs(row))


def candidate_axes_map(case: dict) -> dict:
    return {i: signals.CandidateAxes(**_axes_kwargs(row))
            for i, row in (case.get('candidate_axes') or {}).items()}


# ═══════════════════════════════ 군 생성 ═══════════════════════════════════

def without_true_parents(case: dict) -> dict:
    """대조군 한 건 — **정답 부모를 후보에서 뺀다.** 원본은 건드리지 않는다.

    ⚠ ⟨`WU-S6`⟩ 정본은 core-api 가 적은 군(`case['groups']`)이다. 이 함수는 **군 기록이
    없는 옛 후보 파일**을 되읽을 때만 쓰는 사다리이고, 시험이 지키는 자리이기도 하다.
    """
    drop = {p['parent_dataset_id'] for p in case.get('parents') or []}
    return dict(case, group='removed',
                candidates=[dict(c) for c in case['candidates'] if c['datasetId'] not in drop],
                removed_candidate_ids=sorted(drop))


def group_case(case: dict, group: str) -> dict:
    """군 하나의 입력 한 벌. **후보를 여기서 고르지 않는다** — core-api 가 적은 것을 읽는다."""
    if group == 'main':
        return dict(case, group='main')
    recorded = (case.get('groups') or {}).get(group)
    if recorded is None:
        if group == 'removed':
            return without_true_parents(case)
        raise ValueError(f'후보 기록에 {group!r} 군이 없다 — 새 후보 기록으로 다시 잰다')
    return dict(case, group=group, candidates=[dict(c) for c in recorded['candidates']],
                group_counts={k: recorded[k] for k in
                              ('population', 'in_pool', 'survived', 'blocked_by_level',
                               'removed_by_design', 'not_in_pool') if k in recorded})


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


def _as_row(suggestion: dict) -> dict:
    """계약 응답 한 장 → 판정이 세는 모양. **값을 바꾸지 않는다.**"""
    return dict(parent_dataset_id=suggestion.get('parentDatasetId'),
                parent_dataset_name=suggestion.get('parentDatasetName'),
                parent_processing_level=suggestion.get('parentProcessingLevel'),
                confidence=suggestion.get('confidence'),
                rationale=suggestion.get('rationale'),
                suggested_parent_role=suggestion.get('suggestedParentRole'),
                evidence=list(suggestion.get('evidence') or ()))


def verify_like_relay(suggestions, case: dict) -> tuple[list[dict], dict]:
    """⭑ **중계가 하는 그대로** 세 걸음을 건다 — 여기가 「재는 파이프라인 = 제품」의 자리다.

    ① 후보 밖 부모를 실은 제안을 버린다(`relay._within_candidates`).
    ② 인용을 실제 축 값에 대조해 검증되지 않은 항목을 버리고, 0종이면 제안째 버린다.
       확신도·근거 한 줄을 core-api 가 다시 쓴다(`relay._verified_suggestion`).
    ③ 상위 k 를 자른다 — **폐기를 센 뒤에** 자른다(넘쳐 잘린 건을 인용 오류로 세지 않는다).
    """
    allowed = {c['datasetId'] for c in case['candidates']}
    kept = [s for s in suggestions if relay_module._within_candidates(s, allowed)]
    outside_dropped = len(suggestions) - len(kept)
    upload = upload_axes_of(case)
    axes = candidate_axes_map(case)
    claimed = sum(len(s.get('evidence') or ()) for s in kept)
    checked = [relay_module._verified_suggestion(s, upload, axes) for s in kept]
    verified = [s for s in checked if s is not None]
    survived = sum(len(s.get('evidence') or ()) for s in verified)
    return verified[:relay_module.SUGGESTION_LIMIT], dict(
        outside_dropped=outside_dropped,
        unverified_dropped=len(kept) - len(verified),
        evidence_claimed=claimed, evidence_verified=survived,
        evidence_discarded=claimed - survived)


def run_model_case(case: dict, suggester: LlmLineageSuggester, transport) -> dict:
    """자식 한 건 = 모델 왕복 한 번, 그 뒤 **core-api 검증 한 번.**"""
    candidates = parse_candidates(case['candidates'])
    if isinstance(candidates, str):
        raise ValueError(f"후보가 계약 밖이다: {candidates}")
    before = len(transport.calls)
    outcome = suggester.suggest(file_meta=case['file_meta'], candidates=candidates,
                                dataset_name_draft=case.get('dataset_name_draft'),
                                subject=case.get('subject'),
                                processing_level=case.get('upload_level'))
    call = transport.calls[before] if len(transport.calls) > before else {}
    raw_items = read_raw(call.get('raw'))
    # ai-service 가 낸 것 = **주장**이다. 정본은 다음 줄의 core-api 검증이 만든다.
    claimed = [s.to_dict() for s in outcome.suggestions]
    final, counts = verify_like_relay(claimed, case)
    return _row(case, [_as_row(s) for s in final], raw_items, counts,
                empty_declaration=outcome.empty_declaration, call=call,
                claimed=[_as_row(s) for s in claimed], arm=ARM_MODEL)


def run_rule_case(case: dict) -> dict:
    """규칙 팔 한 건 — **모델을 부르지 않는다.** 같은 적격 집합에 축 대조만 건다."""
    body = rule_suggest.RuleBasedLineageSuggester().suggest(
        lab_id='probe', lab_name='연구실', account_id='probe',
        file_meta=case['file_meta'], candidates=case['candidates'],
        searched_count=case.get('searched_count') or len(case['candidates']),
        dataset_name_draft=case.get('dataset_name_draft'), subject=case.get('subject'),
        processing_level=case.get('upload_level'),
        upload_axes=upload_axes_of(case), candidate_axes=candidate_axes_map(case))
    final = [_as_row(s) for s in body.get('suggestions') or ()]
    counts = dict(outside_dropped=0, unverified_dropped=0,
                  evidence_claimed=sum(len(s['evidence']) for s in final),
                  evidence_verified=sum(len(s['evidence']) for s in final),
                  evidence_discarded=0)
    return _row(case, final, [], counts,
                empty_declaration=body.get('degradedReason'), call={},
                claimed=final, arm=ARM_RULES)


def _row(case: dict, suggestions, raw_items, counts: dict, *, empty_declaration,
         call: dict, claimed, arm: str) -> dict:
    by_id = {c['datasetId']: c for c in case['candidates']}
    for item in suggestions:
        item['grounding'] = grounding(item['rationale'], by_id.get(item['parent_dataset_id'], {}),
                                      case)
        item['citation_errors'] = citation_errors(item, case)
    group = case.get('group', 'main')
    leaks = ([dict(parent_dataset_id=s['parent_dataset_id'],
                   parent_dataset_name=s['parent_dataset_name'], kind=leak_kind(s, case))
              for s in suggestions] if group in STRUCTURAL_GROUPS else [])
    return dict(
        id=case['id'], child_dataset_id=case['child_dataset_id'], child_name=case['child_name'],
        arm=arm, group=group, candidate_count=len(case['candidates']),
        candidate_ids=[c['datasetId'] for c in case['candidates']],
        group_counts=case.get('group_counts'),
        true_parent_ids=[p['parent_dataset_id'] for p in case.get('parents') or []],
        suggestions=suggestions, claimed_suggestions=claimed,
        empty_declaration=empty_declaration,
        raw=call.get('raw'), seconds=call.get('seconds'), error=call.get('error'),
        raw_suggestions=len(raw_items), **counts,
        outside_candidate_ids=outside_ids(raw_items, case),
        format_violations=[dict(index=k, kinds=v)
                           for k, v in enumerate(map(format_violations, raw_items)) if v],
        structural_leaks=leaks,
        # 참인 인용을 달고 살아남은 **비부모**. 순위 문제이지 반려 사유가 아니다(Ted 판정 1).
        true_cited_non_parents=([dict(parent_dataset_id=s['parent_dataset_id'],
                                      parent_dataset_name=s['parent_dataset_name'],
                                      evidence=[e['field'] for e in s['evidence']])
                                 for s in suggestions]
                                if group in RANKING_GROUPS else []),
        edges=edge_hits(case, suggestions))


# ═══════════════════════════════ 판정 표 ═══════════════════════════════════

def judge(passes_by_arm: dict, timeout: float) -> dict:
    """J1~J9 를 한 벌로 센다. **수치로 합격/불합격을 가르지 않는다** — 러너는 재기만 한다.

    다만 **red 조건에 걸린 건수**는 센다(intent 판정 기준이 실측 전에 고정됐다) — 세지
    않으면 보고서를 쓰는 사람이 매번 다시 읽어야 하고, 그때 기준이 흔들린다.
    """
    out: dict = {}
    for arm, passes in passes_by_arm.items():
        rows = [row for rows_ in passes for row in rows_]
        # **회차 구조는 이미 있다** — 되맞추지 않는다(맞추는 순간 그 규칙이 또 하나의
        # 오라클이 되고, 틀리면 아무도 못 센다).
        main_passes = [[row for row in rows_ if row['group'] == 'main'] for rows_ in passes]
        main = [row for rows_ in main_passes for row in rows_]
        grounds = [s['grounding'] for row in main for s in row['suggestions']]
        seconds = [row['seconds'] for row in rows if row['seconds'] is not None]
        claimed = sum(row['evidence_claimed'] for row in rows)
        discarded = sum(row['evidence_discarded'] for row in rows)
        out[arm] = dict(
            J1_recall=dict(
                edges=sum(len(row['edges']) for row in main_passes[0]) if main_passes else 0,
                in_candidates=sum(1 for row in main_passes[0] for edge in row['edges']
                                  if edge['parent_dataset_id'] in row['candidate_ids'])
                if main_passes else 0),
            J2_hit=dict(per_pass=[dict(edges=sum(len(row['edges']) for row in rows_),
                                       hit1=sum(e['hit1'] for row in rows_ for e in row['edges']),
                                       hit3=sum(e['hit3'] for row in rows_ for e in row['edges']))
                                  for rows_ in main_passes]),
            J3_citations=dict(
                evidence_claimed=claimed, evidence_discarded=discarded,
                discard_rate=(round(discarded / claimed, 3) if claimed else None),
                suggestions_dropped_unverified=sum(row['unverified_dropped'] for row in rows),
                final_citation_errors=sum(len(s['citation_errors'])
                                          for row in rows for s in row['suggestions']),
                grounding_hard=sum(len(g['hard']) for g in grounds),
                grounding_hard_tokens=sorted({t for g in grounds for t in g['hard']})),
            J4_calibration=calibration(main),
            J5_groups={group: _group_judgement(rows, group) for group in GROUPS},
            J6_outside=dict(ids=sorted({i for row in rows for i in row['outside_candidate_ids']}),
                            count=sum(len(row['outside_candidate_ids']) for row in rows),
                            dropped_by_relay=sum(row['outside_dropped'] for row in rows)),
            J7_format=dict(violations=sum(len(row['format_violations']) for row in rows),
                           kinds=sorted({k for row in rows for v in row['format_violations']
                                         for k in v['kinds']})),
            J8_latency=dict(calls=len(seconds), timeout_seconds=timeout,
                            min=min(seconds) if seconds else None,
                            median=statistics.median(seconds) if seconds else None,
                            max=max(seconds) if seconds else None,
                            over_timeout=sum(1 for s in seconds if s > timeout),
                            transport_errors=sorted({row['error'] for row in rows if row['error']})),
            J9_determinism=determinism(passes),
            red=dict(structural_leaks=sum(len(row['structural_leaks']) for row in rows),
                     leak_kinds=sorted({leak['kind'] for row in rows
                                        for leak in row['structural_leaks']}),
                     final_citation_errors=sum(len(s['citation_errors'])
                                               for row in rows for s in row['suggestions'])))
    return out


def _group_judgement(rows: list[dict], group: str) -> dict:
    """군 하나의 판정 한 칸. **red 가 되는 군과 기록만 하는 군을 이름으로 가른다.**"""
    mine = [row for row in rows if row['group'] == group]
    empty = sum(1 for row in mine if not row['suggestions'])
    return dict(
        cases=len(mine), empty=empty, non_empty=len(mine) - empty,
        structural=group in STRUCTURAL_GROUPS,
        # ⚠ **안 돈 군을 green 으로 적지 않는다.** 대상 0건을 통과로 세는 것이 이 레포의
        #   대표 실패형이다 — 「돌지 않았다」는 세 번째 칸이다.
        verdict=('not_run' if not mine else
                 'red' if group in STRUCTURAL_GROUPS and empty < len(mine) else
                 'green' if group in STRUCTURAL_GROUPS else 'record'),
        candidate_counts=sorted({row['candidate_count'] for row in mine}),
        vacuous=sum(1 for row in mine if row['candidate_count'] == 0),
        leaks=[leak for row in mine for leak in row['structural_leaks']],
        true_cited_non_parents=[item for row in mine for item in row['true_cited_non_parents']],
        non_empty_children=[row['child_dataset_id'] for row in mine if row['suggestions']])


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidates', type=Path, required=True,
                    help='core-api 가 고른 후보·대조군 기록(`test_k3_lineage_probe.py` 산출)')
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--model', default='gpt-5.6-luna')
    ap.add_argument('--arm', default='both', choices=(ARM_RULES, ARM_MODEL, 'both'))
    ap.add_argument('--groups', default=','.join(GROUPS),
                    help='잴 군 이름을 쉼표로. 기본은 본군 + 대조군 4종')
    ap.add_argument('--repeats', type=int, default=2, help='같은 입력 반복 횟수(J9)')
    ap.add_argument('--timeout', type=float, default=8.0, help='제품 모델 timeout(초)')
    ap.add_argument('--base-url', default='https://api.openai.com/v1/chat/completions')
    args = ap.parse_args()
    if args.output.exists():
        print('Preparation failure: output already exists; choose a new run path')
        return 78
    try:
        groups = [g.strip() for g in args.groups.split(',') if g.strip()]
        unknown = [g for g in groups if g not in GROUPS]
        if unknown:
            raise ValueError(f'모르는 군 이름: {unknown} — 고를 수 있는 값은 {list(GROUPS)}')
        arms = list(ARMS) if args.arm == 'both' else [args.arm]
        recorded = json.loads(args.candidates.read_text())
        cases = recorded['cases']
        edges = sum(len(c['parents']) for c in cases)
        # 건수는 후보 JSON 이 싣고 온 `sample_limits`(정답 파일의 선언)와 대조한다 — 고정
        # 숫자로 두면 정답이 바뀔 때마다 러너가 78 로 멈춘다(WU5 사전 등록 §7).
        limits = recorded.get('sample_limits') or {}
        if 'children' not in limits or 'edges' not in limits:
            raise ValueError('candidates file has no sample_limits.children/edges')
        if len(cases) != limits['children'] or edges != limits['edges']:
            raise ValueError(f'unexpected case count: children={len(cases)} edges={edges} '
                             f'expected={limits["children"]}/{limits["edges"]}')
        repeats = max(1, args.repeats)

        transport = None
        passes_by_arm: dict[str, list[list[dict]]] = {}
        for arm in arms:
            if arm == ARM_MODEL:
                key = os.environ.get('OPENAI_API_KEY')
                if not key:
                    raise RuntimeError('OPENAI_API_KEY missing')
                transport = RecordingTransport(
                    http_transport(base_url=args.base_url, api_key=key, timeout=args.timeout),
                    args.model)
                suggester = build_suggester(args.model, transport, args.timeout)
                passes_by_arm[arm] = [
                    [run_model_case(group_case(case, group), suggester, transport)
                     for group in groups for case in cases]
                    for _ in range(repeats)]
            else:
                # 규칙 팔은 결정적이라 **한 회차면 충분하다** — 같은 입력에 같은 답이
                # 나온다는 것은 반복이 아니라 코드가 말한다. 그래도 J9 표를 비우지
                # 않으려고 같은 모양으로 적는다.
                passes_by_arm[arm] = [[run_rule_case(group_case(case, group))
                                       for group in groups for case in cases]]

        judgement = judge(passes_by_arm, args.timeout)
        result = dict(
            kind='K3 WU-S6 실측 — 기록된 후보·대조군 4종에 두 팔(규칙·모델)을 나란히 건다. '
                 '모델 팔은 ai-service 생산자 + core-api 인용 검증까지 제품 그대로다. '
                 '후보 선정은 core-api(재생 시험)의 몫이고 여기서 하지 않는다. 판정 게이트가 아니다',
            model=args.model, arms=arms, groups=groups, repeats=repeats,
            timeout_seconds=args.timeout,
            candidates_source=str(args.candidates.relative_to(ROOT)
                                  if args.candidates.is_absolute() and args.candidates.is_relative_to(ROOT)
                                  else args.candidates),
            candidates_sha256=_sha256(args.candidates),
            candidates_local_sha=recorded.get('local_sha'),
            sample_limits=recorded.get('sample_limits'),
            autometa_axes_present=recorded.get('autometa_axes_present'),
            sibling_rules=recorded.get('sibling_rules'),
            strategy=recorded.get('strategy'), k=recorded.get('k'),
            system_prompt_sha256=hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
            suggester_sha256=_sha256(Path(suggest_module.__file__)),
            verifier_sha256=_sha256(Path(relay_module.__file__)),
            signals_sha256=_sha256(Path(signals.__file__)),
            runner_sha256=_sha256(Path(__file__)),
            local_sha=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            model_calls=len(transport.calls) if transport is not None else 0,
            judgement=judgement,
            passes={arm: rows for arm, rows in passes_by_arm.items()},
            calls=transport.calls if transport is not None else [])
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + '\n')
        print(json.dumps(dict(
            model=args.model, arms=arms, model_calls=result['model_calls'],
            summary={arm: dict(J2=j['J2_hit']['per_pass'],
                               J3_discard=j['J3_citations']['discard_rate'],
                               J3_final_errors=j['J3_citations']['final_citation_errors'],
                               J5={g: f"{v['empty']}/{v['cases']} {v['verdict']}"
                                   for g, v in j['J5_groups'].items()},
                               J6=j['J6_outside']['count'], J7=j['J7_format']['violations'],
                               J8_over=j['J8_latency']['over_timeout'],
                               red=j['red'])
                     for arm, j in judgement.items()},
            output=str(args.output)), ensure_ascii=False))
        return 0
    except Exception as exc:
        print('Preparation failure:', type(exc).__name__, str(exc)[:200])
        return 78


if __name__ == '__main__':
    raise SystemExit(main())
