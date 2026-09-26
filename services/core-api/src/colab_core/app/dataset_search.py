"""검색 결과 조립 — 순서 · 관련도 막대 · **근거(검색된 이유)**. **조립 루트에 둔다.**

`K4-a` 가 `services/ai-service/src/colab_ai/domains/d10_ai_services.py` 에 두었던 조립이다.
Ted 판정(2026-08-25 ㈎)이 `tsvector` 실행을 core-api 로 옮기면서 **근거의 재료**(맞은 말·
맞은 자리·뒤진 개수)도 전부 이쪽에 생겼다. 재료가 있는 곳에서 문장을 만든다 —
두 배포 단위가 같은 문장을 나눠 만들면 갈라진다.

**여기에 없는 것이 결정이다.**
  · 순위 규칙이 없다. 순서는 `ts_rank_cd` 내림차순 그대로이고 동점이면 식별자 오름차순이다.
    LLM 이 순서를 정하면 같은 질의가 때마다 다른 순서를 내고 **근거 한 줄이 사후 정당화로
    전락**한다 (`〈72〉-㉮`).
  · 접근 상태를 읽지 않는다. 잠김 표시는 라우트가 D2 Port 로 붙인다 —
    그래서 **잠긴 데이터가 결과에서 사라질 수 없다** (`Policy_데이터_찾기 §1.3-6`).
  · 확신도·점수·퍼센트 필드가 없다 (`CLAUDE.md §3 AI 응답 규격`).
"""
from __future__ import annotations

import base64
import binascii

from ..domains.d3_catalog import SearchMatch

#: 「낱말 일치」 항목에 열거하는 검색어 상한. 항목 한 줄이 넘치지 않게 한다.
MAX_TERMS_IN_RATIONALE = 3


def encode_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(f"o:{offset}".encode()).decode()


def decode_cursor(cursor: str | None) -> int:
    """망가진 토큰은 **처음부터**다. 400 을 내면 이어보기 한 번의 실수가 검색을 끊는다."""
    if not cursor:
        return 0
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    except (binascii.Error, UnicodeDecodeError, ValueError):
        return 0
    return int(raw[2:]) if raw.startswith("o:") and raw[2:].isdigit() else 0


def _josa(phrase: str, final: str, open_: str) -> str:
    """닫는 따옴표 앞 마지막 글자가 **받침 있는 한글 음절**이면 `final`, 아니면 `open_`.

    한글로 끝나지 않는 말(‘NDVI’)은 종전 모양(`open_`)을 그대로 쓴다.
    """
    last = phrase.rstrip("’")[-1:]
    if "가" <= last <= "힣" and (ord(last) - 0xAC00) % 28:
        return final
    return open_


#: 그래프가 데려온 말을 근거에 **어떻게 읽어 주는가.** 관계 3값을 사람 문장으로 옮긴 것이고,
#: 빈칸 둘은 (부모, 넓힌 말) 순서다. 열쇠는 `d9_concept_edge.relation` CHECK 값 그대로다.
_EXPANSION_PHRASE = {
    "~의 한 가지다": "‘{parent}’의 한 가지인 ‘{term}’",
    "같은 말이다": "‘{parent}’{wa} 같은 말인 ‘{term}’",
    "안에 있다": "‘{parent}’ 안에 있는 ‘{term}’",
}


def _matched_phrase(term: str, expansions: dict[str, tuple[str, str]] | None) -> str:
    """맞은 말 하나를 읽어 준다. **그래프가 데려온 말이면 그 엣지를 이름으로 적는다.**

    「적을 수 없으면 확장하지 않는다」(`sessions/K1b-ONTOLOGY-CONTENT §D-6` 의 다섯째
    안전장치)의 이쪽 절반이다 — 여기서 문장이 나오지 않으면 그 확장은 사람이 눈으로
    검사할 수 없는 것이 된다. **여전히 한 줄이고 숫자는 하나도 없다.**
    """
    hop = (expansions or {}).get(term)
    if not hop:
        return f"‘{term}’"
    relation, parent = hop
    template = _EXPANSION_PHRASE.get(relation)
    return (template.format(parent=parent, term=term, wa=_josa(parent, "과", "와"))
            if template else f"‘{term}’")


#: 근거 종류 — 화면 「AI」 패널의 상위 항목 순서다(낱말 일치 → 관련 개념 → 연결된 자료 →
#: 파일 근거 · intent `2026-09-25-search-rationale-separation.md` Q7 · 계약
#: `SearchResultRow.rationaleFacts`). 사실이 없는 종류는 싣지 않는다.
FACT_KINDS = ("term", "concept", "linked", "evidence")

#: 파일 근거 자리 이름(`d3_catalog._WHERE_LABELS`). 「낱말 일치」 자리 목록에는 싣지 않는다 —
#: 그 사실은 「파일 근거」·「연결된 자료」 종류가 말한다(intent `2026-09-26-rationale-facts-wording.md` ③).
_EVIDENCE_WHERE = "확인한 파일 근거"
#: 개념 주석 자리 이름(`d3_catalog._WHERE_LABELS`). 내부 기법 이름이라 카드 문구에 쓰지 않는다 —
#: 그 사실은 「관련 개념」 종류가 말한다(선행 intent `2026-09-25-search-rationale-separation.md` Q7).
_ONTOLOGY_WHERE = "온톨로지 연결 근거"
#: 「낱말 일치」 자리 목록에서 빼는 자리와, 그 자리로만 맞았을 때 대신 서는 사실(근거 필수).
_FACT_ONLY_WHERE = {
    _EVIDENCE_WHERE: {"kind": "evidence", "items": ["확인한 파일 근거가 질문 조건에 맞았어요"]},
    # 이 항목이 없으면 개념 주석으로만 맞은 결과의 이유가 0개다(`product.md` §3).
    _ONTOLOGY_WHERE: {"kind": "concept", "items": ["자료에 적힌 개념이 질문과 연결돼요"]},
}


def _fold(text: str) -> str:
    return " ".join(text.split()).casefold()


def _shown_terms(terms: tuple[str, ...], topic: str | None, query: str) -> tuple[str, ...]:
    """응답 `topic` 과 같고 질의 원문에 없는 검색어를 뺀다 — 헤더가 이미 주제를 말한다.

    남는 낱말이 없으면 그대로 둔다(근거 필수). 검색어·순위는 건드리지 않는 표시 규칙이다
    (intent `2026-09-26-rationale-facts-wording.md` ② · 해소 ⒜).
    """
    if not topic or _fold(topic) in _fold(query):
        return terms
    kept = tuple(t for t in terms if _fold(t) != _fold(topic))
    return kept or terms


def rationale_facts(match: SearchMatch, *,
                    expansions: dict[str, tuple[str, str]] | None = None,
                    topic: str | None = None, query: str = "") -> list[dict]:
    """맞은 사실을 **근거 종류별 항목**으로 적는다 — **검색된 이유만** 싣는다.

    ⭑ Ted 2026-09-26 결정(intent `2026-09-25-search-rationale-separation.md` Q6·Q8)으로
    종전 「한 줄 안에 한계도 함께 밝힌다」를 버렸다. 뒤진 범위·주제·해석 여부는 응답 머리
    (`scope`·`topic`·`degraded`)가 한 번 말하고, 한계·부정 문장은 카드 근거에 싣지 않는다.
    그래프 확장어는 「낱말 일치」 아래에 둔다(미해결 질문 ⒜) — 「관련 개념」은 개념 주석 일치다.

    ⭑ **종결은 해요체다** (화면 검수 2026-09-03 #12 · `Policy_데이터_찾기 §120행`). 이 문장은
    **서버가 만들어 화면이 그대로 싣는다** — 그래서 문체도 여기서 정해진다.
    """
    places = tuple(w for w in match.where if w not in _FACT_ONLY_WHERE)
    if match.where and not places:
        # 파일 근거·개념 주석 자리로만 맞았다 — 낱말 일치 줄 없이 그 종류의 사실만 낸다.
        return [dict(_FACT_ONLY_WHERE[w], items=list(_FACT_ONLY_WHERE[w]["items"]))
                for w in dict.fromkeys(match.where)]
    terms = _shown_terms(match.matched_terms, topic, query)
    heads = [_matched_phrase(t, expansions) for t in terms[:MAX_TERMS_IN_RATIONALE]]
    matched = ", ".join(heads) or "‘질문의 낱말’"
    where = "·".join(places) if places else "카탈로그"
    return [{"kind": "term", "items": [f"{matched}{_josa(matched, '이', '가')} {where}에 맞았어요"]}]


def ordered_facts(facts: list[dict]) -> list[dict]:
    """종류 순서를 고정하고 **빈 종류를 뺀다.** 항목의 공백·줄바꿈은 한 칸으로 접는다."""
    by_kind: dict[str, list[str]] = {}
    for fact in facts:
        by_kind.setdefault(fact["kind"], []).extend(
            " ".join(item.split()) for item in fact["items"] if item and item.strip())
    return [{"kind": kind, "items": by_kind[kind]} for kind in FACT_KINDS if by_kind.get(kind)]


def rationale_line(facts: list[dict]) -> str:
    """`rationale` 한 줄 = 사실 항목을 순서대로 이은 문장(구 화면 호환 · 미해결 질문 ⒝).

    패널과 같은 사실을 말하고, 한계·공통부가 없으며, 줄바꿈이 없다(`AiRationale` 패턴).
    """
    return " ".join(f"{item.rstrip('.')}." for fact in facts for item in fact["items"])


def compose(matches, *, total: int, offset: int,
            expansions: dict[str, tuple[str, str]] | None = None,
            topic: str | None = None, query: str = ""
            ) -> tuple[list[dict], str | None]:
    """후보를 **정본 모양의 값**으로 접는다 — `datasetId` · `relevanceBar` · 근거(구조형 + 한 줄).

    동점은 **식별자 오름차순**으로 고정한다 — DB 가 같은 점수를 낸 두 행의 순서까지
    재현되어야 평가셋이 회귀를 잡는다 (SQL 도 같은 순서를 내지만, 순서를 이 층에서도
    한 번 못 박아 두어야 실행기가 바뀌어도 성질이 남는다).
    """
    ordered = sorted(matches, key=lambda m: (-m.rank, m.dataset_id))
    top = max((m.rank for m in ordered), default=0.0)
    items = []
    for m in ordered:
        facts = ordered_facts(rationale_facts(m, expansions=expansions, topic=topic, query=query))
        items.append({
            "datasetId": m.dataset_id,
            # 막대의 길이일 뿐이다. **화면에 숫자로 서면 정본 위반이다**
            # (`Policy_데이터_찾기 §4 용어(관련도)`).
            "relevanceBar": round(m.rank / top, 3) if top > 0 else 0.0,
            "rationaleFacts": facts,
            "rationale": rationale_line(facts),
        })
    next_cursor = encode_cursor(offset + len(items)) if offset + len(items) < total else None
    return items, next_cursor
