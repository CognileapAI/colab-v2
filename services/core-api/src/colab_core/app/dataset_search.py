"""검색 결과 조립 — 순서 · 관련도 막대 · **근거 한 줄**. **조립 루트에 둔다.**

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

#: 근거 한 줄에 열거하는 검색어 상한. 카드 한 줄이 넘치면 정본의 「한 줄 고정」이 깨진다.
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


def rationale(match: SearchMatch, *, lab_name: str, searched: int, topic: str | None,
              interpretation_degraded: bool) -> str:
    """**한 줄이고, 같은 줄에서 한계도 밝힌다** (`Policy_데이터_찾기 §8` — 펼침·더보기 없음).

    앞 절은 실행기가 준 사실(뒤진 범위 · 맞은 말 · 맞은 자리)이고, 뒤 절은 **이 검색이 못 본
    것**이다. 좋은 점만 적는 줄이 따로 생기지 않도록 두 절을 한 문장에 붙여 둔다.
    """
    matched = ", ".join(match.matched_terms[:MAX_TERMS_IN_RATIONALE]) or "질문의 낱말"
    where = "·".join(match.where) if match.where else "카탈로그"
    head = f"{lab_name} 안 {searched}건에서 ‘{matched}’가 {where}에 맞았다"
    if topic:
        head += f" (주제 {topic}로 좁혀 뒤졌다)"
    tail = "기간·지역·품질은 이 검색이 확인하지 못했으니 카드의 값으로 직접 보라"
    if interpretation_degraded:
        tail = "질의 해석 없이 질문의 낱말 그대로 찾았고, " + tail
    return f"{head} — {tail}."


def compose(matches, *, lab_name: str, searched: int, topic: str | None,
            interpretation_degraded: bool, total: int,
            offset: int) -> tuple[list[dict], str | None]:
    """후보를 **정본 모양의 세 값**으로 접는다 — `datasetId` · `relevanceBar` · `rationale`.

    동점은 **식별자 오름차순**으로 고정한다 — DB 가 같은 점수를 낸 두 행의 순서까지
    재현되어야 평가셋이 회귀를 잡는다 (SQL 도 같은 순서를 내지만, 순서를 이 층에서도
    한 번 못 박아 두어야 실행기가 바뀌어도 성질이 남는다).
    """
    ordered = sorted(matches, key=lambda m: (-m.rank, m.dataset_id))
    top = max((m.rank for m in ordered), default=0.0)
    items = [
        {
            "datasetId": m.dataset_id,
            # 막대의 길이일 뿐이다. **화면에 숫자로 서면 정본 위반이다**
            # (`Policy_데이터_찾기 §4 용어(관련도)`).
            "relevanceBar": round(m.rank / top, 3) if top > 0 else 0.0,
            "rationale": rationale(m, lab_name=lab_name, searched=searched, topic=topic,
                                   interpretation_degraded=interpretation_degraded),
        }
        for m in ordered
    ]
    next_cursor = encode_cursor(offset + len(items)) if offset + len(items) < total else None
    return items, next_cursor
