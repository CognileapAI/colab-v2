"""D3 조립 — `listDatasets` · `listDatasetFacets` · `getDataset` · `listDatasetFiles`.

카탈로그 한 행은 D3(이름·파일·업로더) · D2(접근·Verified) · D4(계보) · D6(프로젝트)의 사실을
합쳐야 그려진다. **도메인끼리 붙이지 않고 이 조립 루트가 Port 로 받아 합친다.**
"""
from __future__ import annotations

import base64
import binascii
import datetime as dt
import logging
from typing import Any

from fastapi import APIRouter, Body, Depends, Query, Request
from sqlalchemy.orm import Session

from ...domains import (d1_identity, d2_access, d3_catalog, d4_lineage, d6_project,
                        d8_insight)
from ...kernel import errors
from ...kernel.auth import Subject
from ...kernel.ids import Ulid
from ...kernel.scope import read_only_scope
from ...ports.lineage import LV_CAP
from .. import dataset_search
from ..deps import current_subject, scoped_db

router = APIRouter()

#: 검색 장애의 **감시 표면**. Ted 가 모니터링을 붙인다(2026-08-25) — 그러려면 실패가
#: 사람의 눈이 아니라 **기계가 긁을 이름**으로 서야 한다. 이름 셋을 고정한다:
#: 로거 `colab_core.search` · `record.event = "search.unavailable"` · `record.code`.
#: 문구는 바뀔 수 있어도 이 셋은 계약처럼 다룬다 — 대시보드 질의가 그 위에 선다.
_search_log = logging.getLogger("colab_core.search")

#: 검색에 못 닿았을 때의 봉투 코드. `preview.py` 의 `RENDER_UNAVAILABLE` 과 같은 모양이고
#: 계약(`fe-core.yaml#searchDatasets` 의 `"503"`)이 이 값을 이름으로 적어 뒀다.
SEARCH_UNAVAILABLE = "SEARCH_UNAVAILABLE"

PAGE_SIZE = 20   # 페이지 크기는 서버가 정한다 — 정본은 `+N건 더 보기`만 요구한다 (D2.md §3-②)

#: 조건을 걸 수 있는 열은 **다섯**이고 나머지 세 열은 정렬만 갖는다
#: (`Policy_데이터_찾기 §5` 카탈로그 조건).
FILTERABLE_COLUMNS = ("주제", "Level", "업로더", "계보", "Verified")

#: 계보 열의 값은 이 넷뿐이고 숫자를 붙이지 않는다 (`§5` 계보 열 표기).
LINEAGE_STATES = ("확정", "확인 필요", "기록 없음", "원천")

_SORT_KEYS = {
    "데이터셋": lambda row: row["name"],
    "주제": lambda row: row["topic"] or "",
    "Level": lambda row: row["processingLevel"],
    "프로젝트": lambda row: row["projects"]["moreCount"] + (1 if row["projects"]["representative"] else 0),
    "업로더": lambda row: row["uploader"]["name"],
    "수정일": lambda row: row["_lastModifiedAt"],
    "계보": lambda row: row["lineageState"],
    "Verified": lambda row: row["verified"],
}


def _iso(value: Any) -> Any:
    return value.astimezone(dt.timezone.utc).isoformat() if isinstance(value, dt.datetime) else value


def _encode_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(f"o:{offset}".encode()).decode().rstrip("=")


def _decode_cursor(cursor: str | None) -> int:
    if cursor is None:
        return 0
    try:
        pad = "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(cursor + pad).decode()
        if not raw.startswith("o:"):
            raise ValueError
        return max(0, int(raw[2:]))
    except (ValueError, binascii.Error, UnicodeDecodeError):
        raise errors.bad_request("cursor 를 해석하지 못했다.") from None


def _compose(db: Session) -> list[dict]:
    cores = d3_catalog.list_dataset_cores(db)
    ids = [Ulid(c.dataset_id) for c in cores]
    lineage = d4_lineage.LineageSummaryAdapter(db).summaries(ids)
    access = d2_access.DatasetAccessAdapter(db).dataset_access(ids)
    links = d6_project.ProjectLinkAdapter(db).projects_of(ids)

    rows: list[dict] = []
    for core in cores:
        summary = lineage.get(core.dataset_id)
        acc = access.get(core.dataset_id)
        link = links.get(core.dataset_id)
        rows.append({
            "datasetId": core.dataset_id,
            "name": core.name,
            # **본체 파일 수**다 — 기준 격자 파일은 세지 않는다 (Ted 판정 2026-08-26).
            # 잠긴 데이터셋은 본체 정책 때문에 파일 행이 보이지 않는다 — 그 자리를 지어내지 않는다.
            # 계약의 `minimum: 1` 과 어긋나는 유일한 경우이며 sessions/P0-core-api.md §5 에 적었다.
            "fileCount": core.file_count,
            "topic": core.topic,
            "processingLevel": d3_catalog.processing_level(summary),
            "projects": {
                "representative": (None if link is None or link.representative_id is None else
                                   {"projectId": link.representative_id,
                                    "name": link.representative_name}),
                "moreCount": 0 if link is None else link.more_count,
                "names": [] if link is None else link.names,
            },
            "uploader": {"accountId": core.uploader_id, "name": core.uploader_name},
            "lastModifiedAt": _iso(core.last_modified_at),
            "lineageState": d3_catalog.lineage_state(core, summary),
            "lineageConfirmedAt": _iso(core.lineage_confirmed_at),
            "verified": False if acc is None else acc.verified,
            "accessState": "열림" if acc is None else acc.access_state,
            "bodyAccessible": False if acc is None else acc.body_accessible,
            "_lastModifiedAt": core.last_modified_at,
            # ⭑ **⟨16차 해제 · `〈298〉`⟩ 요약은 밑줄 열쇠로 싣는다.** `DatasetRow` 는
            # `additionalProperties: false` 에 required 13칸이고 카탈로그 8열이 요약을 안 쓴다 —
            # 그래서 표 응답에는 나가면 안 되고(`enriched` 가 밑줄 열쇠를 떼어 낸다),
            # 검색 조립만 이 값을 집어 `SearchResultRow.summary` 로 옮긴다.
            # **여기서 싣는 이유는 재질의를 안 하기 위해서다** — `list_dataset_cores` 가
            # 상세와 같은 열(`d3_dataset_description.summary`)을 이미 들고 왔다.
            "_summary": core.summary,
        })
    return rows


def _apply_filters(rows: list[dict], *, topic=None, processingLevel=None, uploader=None,
                   lineageState=None, verified=None, skip: str | None = None) -> list[dict]:
    """열 조건을 건다. `skip` 은 **자기 열의 조건을 빼는 자리**다.

    값별 건수를 셀 때 자기 조건까지 걸면 고른 값만 남아 다른 값으로 갈아탈 수가 없다
    (`Policy_데이터_찾기 §5` 값별 건수 — "다른 열에 걸린 조건을 먼저 적용한 뒤에 센다").
    """
    if topic and skip != "주제":
        rows = [r for r in rows if r["topic"] in set(topic)]
    if processingLevel and skip != "Level":
        rows = [r for r in rows if r["processingLevel"] in set(processingLevel)]
    if uploader and skip != "업로더":
        rows = [r for r in rows if r["uploader"]["accountId"] in set(uploader)]
    if lineageState and skip != "계보":
        rows = [r for r in rows if r["lineageState"] in set(lineageState)]
    if verified is not None and skip != "Verified":
        rows = [r for r in rows if r["verified"] is verified]
    return rows


def _validate_filters(processingLevel, lineageState) -> None:
    for level in processingLevel or ():
        # 상한도 함께 본다 — 없으면 `Lv3` 필터가 **조용히 빈 결과**를 낸다.
        # 「없는 값으로 걸렀더니 0 건」과 「있는 값으로 걸렀더니 0 건」은 다르고,
        # 화면은 그 둘을 구분하지 못한다. `Lv3` 은 정본이 「존재할 수 없는 값」이라
        # 못 박았으므로(`VAL-005`·`POL-020`) 빈 상태가 아니라 잘못된 요청이다.
        if level < 0 or level > LV_CAP:
            raise errors.bad_request(f"processingLevel 은 0 이상 {LV_CAP} 이하다.")
    for state in lineageState or ():
        if state not in LINEAGE_STATES:
            raise errors.bad_request("lineageState 가 계보 열의 네 값이 아니다.")


@router.get("/datasets", name="listDatasets")
def list_datasets(
    db: Session = Depends(scoped_db),
    cursor: str | None = Query(default=None),
    sortColumn: str | None = Query(default=None),
    sortOrder: str | None = Query(default=None),
    topic: list[str] | None = Query(default=None),
    processingLevel: list[int] | None = Query(default=None),
    uploader: list[str] | None = Query(default=None),
    lineageState: list[str] | None = Query(default=None),
    verified: bool | None = Query(default=None),
) -> dict:
    if sortColumn is not None and sortColumn not in _SORT_KEYS:
        raise errors.bad_request("sortColumn 이 계약의 열 이름이 아니다.")
    if sortOrder is not None and sortOrder not in ("오름", "내림"):
        raise errors.bad_request("sortOrder 는 `오름`·`내림` 이다.")

    _validate_filters(processingLevel, lineageState)
    rows = _apply_filters(_compose(db), topic=topic, processingLevel=processingLevel,
                          uploader=uploader, lineageState=lineageState, verified=verified)

    # 기본 정렬은 수정일 최신순 (Policy_데이터_찾기 §5).
    column = sortColumn or "수정일"
    descending = (sortOrder or ("내림" if column == "수정일" else "오름")) == "내림"
    rows.sort(key=_SORT_KEYS[column], reverse=descending)

    total = len(rows)
    offset = _decode_cursor(cursor)
    page = rows[offset:offset + PAGE_SIZE]
    next_cursor = _encode_cursor(offset + PAGE_SIZE) if offset + PAGE_SIZE < total else None
    for r in page:
        r.pop("_lastModifiedAt", None)
    return {"items": page, "totalCount": total, "nextCursor": next_cursor}


#: `Policy_데이터_찾기 §5 검색 질문 — 1~200자`. 규칙 밖을 200 으로 받으면 규칙이 없는 것과 같다.
MAX_QUERY = 200
#: 화면의 `+N건 더 보기` 가 감당하는 폭. 계약 `SearchQuery.limit` 과 같은 상한이다.
MAX_SEARCH_LIMIT = 100
DEFAULT_SEARCH_LIMIT = 20
#: ⭑ **⟨16차 해제 · `〈298〉`⟩ `verified` 를 켰을 때 걸름 전에 훑는 후보 창.**
#: 승인 여부는 D2 의 값이라 실행기(D3)의 `LIMIT` 앞에서 걸 수가 없다 — 조립 층이 넓게
#: 받아서 거른다. **이 창을 넘는 후보는 걸름 대상에서 빠진다** — 「전수를 봤다」고 말하지
#: 않으려고 값을 코드에 드러내 둔다. 조립은 어차피 `_compose` 로 경계 안 데이터셋 전부를
#: 이미 들고 있어, 이 창이 새로 만드는 비용은 D3 질의 한 번의 폭뿐이다.
VERIFIED_SCAN_LIMIT = 1000


#: 자동완성 후보 상한. 계약 `limit` 과 같은 값이다.
MAX_SUGGESTIONS = 20
DEFAULT_SUGGESTIONS = 10


@router.get("/dataset-field-suggestions", name="listDatasetFieldSuggestions")
def list_dataset_field_suggestions(
        field: str = Query(...),
        q: str | None = Query(default=None, max_length=60),
        limit: int = Query(default=DEFAULT_SUGGESTIONS),
        db: Session = Depends(scoped_db)) -> dict:
    """자유 입력 칸의 자동완성 후보 (결정 2-10 · `PLAN-SoT §9 〈138〉`).

    **파편화를 입력 단계에서 막는다.** 정본이 변수·좌표계·원천 표기를 자유 입력으로
    두었으므로(`VAL-006`·`VAL-009`) 같은 것을 두 사람이 다르게 적는 일이 생긴다 —
    `ERA5` / `era5` / `ECMWF ERA5` / `ERA-5`. 결정 2-10 이 그 대가를 적어 뒀다:
    **데이터가 쌓인 뒤의 소급 정리는 사람이 하나씩 묶어야 한다.**

    **모르는 칸은 400 이다** — 계약이 값 집합을 enum 으로 박지 않았으므로(`NB-E`)
    여기가 유일한 관문이다. 조용히 빈 목록을 내면 **화면이 「후보가 없다」로 읽고**
    오타 난 필드 이름이 영원히 안 드러난다.
    """
    if field not in d3_catalog.SUGGESTABLE_FIELDS:
        raise errors.bad_request(
            f"자동완성을 낼 수 있는 칸이 아니다: {field!r}",
            {"field": field, "allowed": list(d3_catalog.SUGGESTABLE_FIELDS)})
    if isinstance(limit, bool) or not 1 <= limit <= MAX_SUGGESTIONS:
        raise errors.bad_request(f"limit 은 1~{MAX_SUGGESTIONS} 이다.")
    items = d3_catalog.suggest_field_values(db, field=field, prefix=q, limit=limit)
    return {"field": field, "items": items}


@router.post("/dataset-searches", name="searchDatasets")
def search_datasets(request: Request, body: dict | None = Body(default=None),
                    subject: Subject = Depends(current_subject),
                    db: Session = Depends(scoped_db)) -> dict:
    """자연어 검색 — **해석 중계 + 실행 + 조립** (`〈80〉-㉯ 5` · Ted 판정 2026-08-25 ㈎).

    **AI 가 돌려주는 것은 검색어·주제뿐이다.** `K4-a` 까지는 ai-service 가 `tsvector` 를 직접
    던졌고, 그것이 D10 → D3 직접 접속이라 `CLAUDE.md §3-1` 위반이었다. 이제 **찾고 매기는 것은
    여기**다 — D3 는 core-api 의 자기 도메인이라 이 실행은 아무 경계도 넘지 않는다 (`〈72〉-㉮`).

    지키는 것 다섯 —
    · **순서는 `ts_rank_cd` 내림차순, 동점은 식별자 오름차순.** 모델이 순서를 정하지 않는다.
    · **잠긴 데이터를 빼지 않고, 잠김으로 표시해서 낸다** (`§1.3-6` · `P-13`·`P-34`).
      실행이 이쪽으로 오면서 D2 를 제대로 볼 수 있게 됐다 — `K4-a` 의 무표시가 여기서 닫힌다.
    · **경계는 주체에서만 나온다.** 질의는 `READ ONLY` + 스코프 트랜잭션에서 돈다.
    · **검색에 못 닿으면 503 이다 — 0건이 아니다** (Ted 판정 2026-08-25 `〈87〉-㉯`).
      「뒤졌는데 없다」와 「뒤지지도 못했다」는 다른 사실이고, 0건으로 접으면 화면이
      「없다」고 답한다. **폴백을 두지 않는다** — 죽으면 「동작하지 않음」이 드러나야 한다.
      **`degraded`(해석만 무너짐 · 낱말 그대로 찾음)는 그대로 200 이다** — 그쪽은 **진짜로
      뒤졌고 결과가 진짜 결과**다. 두 상태를 접지 않는 것이 이 라우트의 요점이다.
    · **AI 가 얹어 보낸 식별자를 읽지 않는다** (중계가 이미 버린다).
    """
    payload = body if isinstance(body, dict) else {}
    unknown = sorted(set(payload) - {"query", "limit", "cursor", "verified"})
    if unknown:
        raise errors.bad_request(f"요청에 계약에 없는 필드가 있다: {unknown}")
    query = payload.get("query")
    if not isinstance(query, str) or not query.strip() or len(query) > MAX_QUERY:
        raise errors.bad_request(f"검색 질문은 1~{MAX_QUERY}자다.")
    limit = payload.get("limit", DEFAULT_SEARCH_LIMIT)
    if not isinstance(limit, int) or isinstance(limit, bool) \
            or not 1 <= limit <= MAX_SEARCH_LIMIT:
        raise errors.bad_request(f"limit 은 1~{MAX_SEARCH_LIMIT} 이다.")
    cursor = payload.get("cursor")
    if cursor is not None and not isinstance(cursor, str):
        raise errors.bad_request("cursor 는 문자열이다.")
    # ⭑ **⟨16차 해제 · `〈298〉`⟩ `Verified만 보기`** (`Policy_데이터_찾기 §8` `:150`).
    # **생략은 「거르지 않는다」다** — `false` 와 같은 뜻이고, 「승인되지 않은 것만」은
    # 정본에 없는 조작이라 이 칸이 표현하지 않는다. 문자열 `"true"` 를 참으로 접지 않는다.
    verified_only = payload.get("verified")
    if verified_only is not None and not isinstance(verified_only, bool):
        raise errors.bad_request("verified 는 boolean 이다.")
    verified_only = bool(verified_only)

    lab = d1_identity.find_lab(db)
    lab_name = ("" if lab is None else lab["name"]) or "연구실"
    # **뒤진 범위를 먼저 밝힌다** — 세는 것은 D3 이고, 그것이 이쪽 도메인이다.
    searched_count = d3_catalog.count_datasets(db)

    answer = request.app.state.searches.interpret(
        lab_id=str(subject.lab_id), lab_name=lab_name,
        account_id=str(subject.account_id), query=query.strip(), limit=limit, cursor=cursor,
        searched_count=searched_count,
    )

    if answer.get("unavailable"):
        # **한 건도 뒤지지 않았다.** 여기서 200 + 0건을 내면 화면이 「없다」고 말하는데
        # 사실은 「못 했다」이다. 로그가 먼저 서는 이유는 감시다 — 응답만으로는
        # 「지금 몇 건 실패했나」를 아무도 못 센다.
        reason = answer.get("unavailableReason") or "검색 서비스에 닿지 못했다."
        _search_log.warning(
            "event=search.unavailable code=%s reason=%s", SEARCH_UNAVAILABLE, reason,
            extra={"event": "search.unavailable", "code": SEARCH_UNAVAILABLE,
                   "reason": reason, "labId": str(subject.lab_id)},
        )
        raise errors.ApiError(
            503, SEARCH_UNAVAILABLE,
            f"검색이 지금 동작하지 않는다 — 없다는 뜻이 아니다: {reason}")

    items: list[dict] = []
    next_cursor = None
    if answer["isDataQuery"] and answer["terms"]:
        offset = dataset_search.decode_cursor(cursor)
        # ⭑ **⟨16차 해제 · `〈298〉`⟩ `verified` 를 켜면 `limit` 보다 먼저 거른다.**
        # `verified` 는 D2 의 값이라 실행기(D3)가 볼 수 없다(`〈295〉`-㉯) — 그래서 걸름은
        # 조립 층의 일이고, 조립이 **한 쪽만 받아서 거르면 「한 쪽 안의 걸름」**이 된다.
        # 그것이 `〈295〉`-㉲-ⓑ 가 적어 둔 한계이고(이어보기 뒤쪽의 승인 결과가 켜도 안 온다),
        # 이 회차가 닫는 것이 그 한계다. 켠 요청은 **창을 넓혀 받고 걸른 뒤 잘라 낸다.**
        #
        # ⚠ **창 값을 코드에 드러내 둔다.** 이 창을 넘는 결과는 걸름 대상에서 빠진다 —
        # 「전수를 봤다」고 말하지 않기 위해 상수로 세운다.
        fetch_limit = VERIFIED_SCAN_LIMIT if verified_only else limit
        fetch_offset = 0 if verified_only else offset
        # **읽기 전용 트랜잭션**에서 돈다 — 검색이 한 줄도 쓰지 않는다는 것을
        # 문서가 아니라 Postgres 의 거절이 지킨다.
        with read_only_scope(request.app.state.session_factory, subject) as ro:
            matches, total = d3_catalog.search_datasets(
                ro, terms=answer["terms"], topic=answer["topic"],
                limit=fetch_limit, offset=fetch_offset)
        hits, next_cursor = dataset_search.compose(
            matches, lab_name=lab_name, searched=searched_count, topic=answer["topic"],
            # 해석이 모델에서 오지 않았으면 근거 한 줄이 그 사실을 밝힌다.
            interpretation_degraded=answer["source"] != "llm",
            # 그래프가 데려온 말이면 근거 한 줄이 그 엣지를 이름으로 적는다 (`〈90〉-㉱`).
            expansions=answer.get("expansions"),
            total=total, offset=fetch_offset)

        by_id = {row["datasetId"]: row for row in _compose(db)}
        for hit in hits:
            row = by_id.get(hit["datasetId"])
            if row is None:
                # 경계 밖이거나 지워진 식별자다. **없는 카드를 지어내지 않는다** (P-9·P-10).
                continue
            enriched = {k: v for k, v in row.items() if not k.startswith("_")}
            # **잠김 표시는 여기서 붙는다** — `accessState`·`bodyAccessible` 은 D2 의 값이다.
            enriched["relevanceBar"] = hit["relevanceBar"]
            enriched["rationale"] = hit["rationale"]
            # ⭑ **⟨16차 해제 · `〈298〉`⟩ 요약** — 상세와 **같은 열**에서 온 값을 옮긴다.
            enriched["summary"] = row["_summary"]
            items.append(enriched)

        # ⭑ **⟨`〈295〉`-㉯ 가 멈춘 한 줄 · `Policy_데이터_찾기 §8` `:117`⟩ Verified 우선.**
        # **안정 정렬이라 무리 안의 순서는 관련도 그대로다** — 「우선」은 두 무리로 가르는
        # 것이지 관련도를 버리는 것이 아니다. 카드의 「교수 승인이라 위로 올렸어요」가
        # 참이 되는 자리가 여기다(`〈295〉`-㉳).
        items.sort(key=lambda r: not r["verified"])

        if verified_only:
            # 걸른 뒤에 자른다. **건수도 걸른 뒤의 건수다** (`Policy :150` 「건수 갱신」).
            kept = [r for r in items if r["verified"]]
            items = kept[offset:offset + limit]
            seen = offset + len(items)
            next_cursor = dataset_search.encode_cursor(seen) if seen < len(kept) else None

        # ⭑ **⟨16차 해제 · `〈298〉`⟩ 기간** — 상세 `basicInfo.period` 와 **같은 열**
        # (`d3_dataset_autometa.period_start/end`)에서 한 번에 읽는다. 행마다 다시 묻지 않는다.
        # `end` 가 `null` 이면 **무기한**이다 (`〈283〉` · 14차 해제) — 끝의 유무로 기간을
        # 떨어뜨리면 저장된 시작이 카드에서 사라진다.
        # ⚠ **잠긴 행에서도 값을 빼지 않는다** — 메타 열이라 본체가 아니고(`d3_catalog.periods_of`),
        # 잠긴 카드가 `기간` 을 안 그리는 것은 화면의 규칙이다 (`Policy §8` 잠긴 결과 카드).
        periods = d3_catalog.periods_of(db, [Ulid(r["datasetId"]) for r in items])
        for row_out in items:
            span = periods.get(row_out["datasetId"])
            row_out["period"] = None if span is None else {
                "start": _iso(span[0]),
                "end": None if span[1] is None else _iso(span[1]),
            }

    out = {
        "scope": {"labId": str(subject.lab_id), "labName": lab_name,
                  "searchedCount": searched_count},
        "isDataQuery": answer["isDataQuery"],
        "degraded": answer["degraded"],
        "items": items,
        "totalCount": len(items),
        "nextCursor": next_cursor,
    }
    if answer.get("degradedReason"):
        out["degradedReason"] = answer["degradedReason"]
    return out


@router.get("/datasets/{datasetId}/files", name="listDatasetFiles")
def list_dataset_files(datasetId: str, db: Session = Depends(scoped_db)) -> dict:
    if not Ulid.is_valid(datasetId):
        raise errors.bad_request("datasetId 가 정규 ID 가 아니다.")
    dataset_id = Ulid(datasetId)
    # 경계 밖이면 RLS 가 이미 행을 지웠다 → 존재를 알리지 않는 404 다 (P-9·P-10).
    if not d3_catalog.dataset_exists(db, dataset_id):
        raise errors.not_found()
    access = d2_access.DatasetAccessAdapter(db).dataset_access([dataset_id]).get(datasetId)
    if access is not None and not access.body_accessible:
        # 메타는 상세에서 보이지만 파일 목록은 본체 쪽이라 막힌다 (P-34).
        raise errors.forbidden("잠긴 데이터이고 허용 목록 밖이다.")
    items = d3_catalog.list_files(db, dataset_id)
    return {"items": items, "totalCount": len(items), "nextCursor": None}


# ─────────────────────────────── 원본 내려받기 ────────────────────────────────
# ⭑ ⟨`ST-1` 2026-09-02 · Ted 판정 「파일 저장처는 지금 볼륨을 그대로 쓴다」⟩
# 종전에는 이 자리가 **501 `NOT_IMPLEMENTED_NO_STORE`** 였다(`routes/not_implemented.py`).
# 그 사유(「저장처가 없다」)는 사실이 아니었다 — 바이트는 이미 접수 볼륨 위에 있었고
# 이력 표(`d8_download`)도 P0 이 만들어 두었다. **마이그레이션 0건 · 계약 개정 0건.**
#
# **접근 판정을 새로 만들지 않는다.** `listDatasetFiles` 와 **같은 두 줄**을 쓴다 —
# ⑴ `dataset_exists` 로 경계 밖은 404(존재를 알리지 않는다 · P-9·P-10)
# ⑵ `body_accessible` 이 거짓이면 403(잠긴 데이터의 본체 · P-34).
# 그 아래 DB 층에도 `body_access` 정책이 그대로 걸려 있어 조각 질의가 0행이 된다 —
# **두 겹이고, 둘 다 같은 기존 기계다.**


def require_body_access(db: Session, dataset_id: Ulid) -> None:
    """**본체에 닿는 두 줄** — 내려받기와 값 조회가 같은 판정을 쓴다.

    ⚠ 값 조회(`lookupDatasetValue` · `〈294〉`)가 이 함수를 **그대로** 부른다. 새 판정을
    만들지 않는 이유는 `〈254〉` 권한 ⓐ 다 — **값은 내용**이고, 확대(보기 권한만)와 다른
    자리다. 판정을 복사하면 한쪽만 고쳐지는 날이 온다.
    """
    return _dataset_for_download(db, dataset_id)


def _dataset_for_download(db: Session, dataset_id: Ulid) -> None:
    if not d3_catalog.dataset_exists(db, dataset_id):
        raise errors.not_found()
    access = d2_access.DatasetAccessAdapter(db).dataset_access([dataset_id]).get(str(dataset_id))
    if access is not None and not access.body_accessible:
        raise errors.forbidden("잠긴 데이터이고 허용 목록 밖이다.")


# ⭑ ⟨병합 창 8-a · `〈334〉`-㉳-⑥ Ted 판정 「다운로드 = 200 티켓 ＋ 바이트 op」⟩
#   여기 있던 **`downloadDataset` 302 판**(`_bundle`·`_disposition` 헬퍼 포함)을 걷었다.
#   `main` 줄기가 `ST-1` 로 세운 「302 ＋ `Location` ＋ `?deliver=1` 재방문」 경로이고,
#   PR #1 줄기가 세운 **`routes/download.py` 의 200 ＋ `DownloadTicket`** 이 그 자리를 대신한다.
#   ⛔ **둘을 함께 두지 않는다** — 같은 `operationId`·같은 경로라 라우트 표가 겹치고
#      (`tests/test_route_table.py` 오라클이 red), 병합된 계약 `fe-core.yaml` 은 이 op 을
#      **200 `DownloadTicket`** 으로 들고 있다. 302 는 한 번도 집행된 적이 없다(계약 산문).
#   걷은 판이 지키던 것은 대신 서는 쪽에 그대로 있다 — 묶음 zip 을 **메모리에 쌓지 않고**
#   청크로 흘려 보내는 것(`download.zip_stream`) · 바이트 결손을 200 으로 위장하지 않는 것 ·
#   이력을 **티켓 발급 시점**에 쌓는 것(`d8_insight.record_download`).
#   원문은 `git show 5a9d9f8:services/core-api/src/colab_core/app/routes/catalog.py` 에 있다.


@router.get("/datasets/facets", name="listDatasetFacets")
def list_dataset_facets(
    db: Session = Depends(scoped_db),
    topic: list[str] | None = Query(default=None),
    processingLevel: list[int] | None = Query(default=None),
    uploader: list[str] | None = Query(default=None),
    lineageState: list[str] | None = Query(default=None),
    verified: bool | None = Query(default=None),
) -> dict:
    """열 메뉴의 값별 건수.

    **0건인 값을 지우지 않는다** — 흐리게 두어 빈 결과로 보내지 않는 것이 정본의 요구다
    (`Policy_데이터_찾기 §5`). 그래서 값의 모집합은 *조건을 걸기 전* 행에서 뽑고,
    세는 것만 조건을 건 뒤에 한다. 이 경로는 **`/datasets/{datasetId}` 보다 먼저 등록된다** —
    뒤에 두면 `facets` 가 datasetId 로 먹힌다.
    """
    _validate_filters(processingLevel, lineageState)
    all_rows = _compose(db)
    filters = {"topic": topic, "processingLevel": processingLevel, "uploader": uploader,
               "lineageState": lineageState, "verified": verified}

    #: 값의 모집합. `계보` 만은 enum 넷이 고정이라 행에서 뽑지 않는다 — 한 값이 0건이 되는 순간
    #: 그 조건이 화면에서 사라지면 안 된다.
    universe: dict[str, list] = {
        "주제": sorted({r["topic"] for r in all_rows if r["topic"] is not None}),
        "Level": sorted({r["processingLevel"] for r in all_rows}),
        "업로더": sorted({r["uploader"]["accountId"] for r in all_rows}),
        "계보": list(LINEAGE_STATES),
        "Verified": [True, False],
    }
    pick = {
        "주제": lambda r: r["topic"],
        "Level": lambda r: r["processingLevel"],
        "업로더": lambda r: r["uploader"]["accountId"],
        "계보": lambda r: r["lineageState"],
        "Verified": lambda r: r["verified"],
    }

    columns = []
    for column in FILTERABLE_COLUMNS:
        scoped = _apply_filters(all_rows, skip=column, **filters)
        counted: dict = {}
        for row in scoped:
            value = pick[column](row)
            counted[value] = counted.get(value, 0) + 1
        columns.append({
            "column": column,
            "values": [{"value": v, "count": counted.get(v, 0)} for v in universe[column]],
        })
    return {"columns": columns}


def _account_ref(account_id: str | None, name: str | None) -> dict | None:
    return None if account_id is None or name is None else {"accountId": account_id, "name": name}


def _variables_payload(db, dataset_id, meta) -> list[dict]:
    """계약 `DatasetBasicInfo.variables` 를 조립한다 — **정본은 `d3_dataset_variable`** 이다.

    행이 0개일 때만 `d3_dataset_autometa.variables`(파이프라인이 헤더에서 읽은 이름 배열)로
    퇴행한다. 그 배열에는 단위·값 범위·결측률이 없으므로 셋은 `null` 이고 **첫 이름이 대표**다
    — 이관 마이그레이션(`0016`)이 기존 행에 한 것과 같은 규칙이라 두 경로가 같은 그림을 낸다.
    ⚠ 퇴행은 **읽기 투영**이다 — 쓰기 정본은 여전히 표 하나뿐이다.
    """
    rows = d3_catalog.list_variables(db, dataset_id)
    if rows:
        return [{"name": v.name, "unit": v.unit, "valueRange": v.value_range,
                 "missingRate": v.missing_rate, "representative": v.representative}
                for v in rows]
    names = [] if meta is None else list(meta.variables)
    return [{"name": n, "unit": None, "valueRange": None, "missingRate": None,
             "representative": i == 0}
            for i, n in enumerate(names)]


def _observation_interval(core) -> dict | None:
    """관측 간격 두 칸 → 계약 `ObservationInterval` 하나 (PRD-17 · `M-6`).

    **없으면 `null` 이고 그것이 전 행의 상태다** — 빈 객체를 내려보내지 않는다. 화면은
    `null` 자리에서 「관측 간격 미기재」를 보인다(재선택을 강제하지 않는다).

    ⚠ `numeric` 은 드라이버가 `Decimal` 로 올린다. JSON 은 `Decimal` 을 모르므로
    **여기서 숫자로 내린다** — 안 하면 직렬화가 500 이다. 정수로 떨어지는 값은 정수로
    내린다(`10.0분` 이 아니라 `10분` 이어야 화면이 조립한 글자가 목업과 같다).
    """
    value = core.observation_interval_value
    unit = core.observation_interval_unit
    if value is None or unit is None:
        return None
    number = float(value)
    return {"value": int(number) if number.is_integer() else number, "unit": unit}


def _project_period(start, end) -> dict:
    """프로젝트 기간은 **연·월까지**이고 진행 중이면 종료가 비어 있다 (Policy_프로젝트 §5)."""
    def month(value):
        return None if value is None else f"{value.year:04d}-{value.month:02d}"
    return {"start": month(start), "end": month(end)}


#: `DatasetUpdate` 가 받는 열쇠. **계약이 정본이다** — 여기는 그 목록을 서버가
#: 다시 한 번 지키는 자리다. 계약이 `additionalProperties: false` 라고 적었어도
#: **런타임에 그것을 강제하는 것은 이 줄뿐이다.**
#: ⭑ **2026-09-02 · `LV-1` · `〈194〉`** — `processingLevel` 을 뺐다. 가공 단계는
#: 언제나 계보에서 파생하고 **사람이 고르는 칸이 아니다**(「예외 없음」). 실어 보내면
#: 아래 `unknown` 판정이 400 으로 드러낸다 — 조용히 무시하지 않는다.
#: ⭑ **⟨19차 해제 · PRD-17⟩ `observationInterval` 이 들어왔다.** 계약이 열쇠를 열고
#: 서버가 그것을 받는 목록이 이 줄이다 — **한 회차에 함께 선다**(§5-㉰-4 「집행 없는
#: 신설」 금지). 계약만 열고 이 줄을 다음 회차로 미루면 열쇠는 있는데 400 이 나온다.
#: ⭑ **⟨20차 해제 · PRD-01·02·03⟩ 분류 3축 세 열쇠가 들어왔다.** 등록만 열고 이 줄을
#: 다음 회차로 미루면 「계약에 없는 필드다」 400 이 돌아온다 — 같은 §5-㉰-4 다.
_UPDATE_FIELDS = ("name", "topic", "summary", "sourceLabel",
                  "representativeFileId", "variables", "crs", "period",
                  "observationInterval",
                  "category", "dataType", "processingLevelUserSet",
                  # ⭑ ⟨20차 해제 · PRD-11 · WU-B4⟩ 공개 범위. **D2 의 값이라
                  #    `d3_catalog.update_dataset` 의 D3 열 목록에는 들어가지 않는다** —
                  #    아래 `update_dataset` 이 D2 경로로 따로 쓴다.
                  "accessState")

#: 주제 어휘. **정본은 DB CHECK 다** (`db/platform/schema.sql` `d3_dataset_description.topic`) —
#: 계약이 「값 집합은 DB CHECK 가 지킨다 · 계약 층 enum 은 만들지 않는다」로 그 자리를
#: 명시했다(`fe-core.yaml DatasetUpdate.topic`). 여기 있는 것은 **그 정본을 코드 층으로
#: 옮겨 적은 사본**이고, 검사를 안 하면 사용자의 오타가 IntegrityError → 500 이 된다.
#: ⭑ **⟨2026-09-06 · `〈359〉`⟩ 4값 → 6값** — `가뭄`·`파일 포맷 예제` 추가(마이그레이션 `0013`).
#: ⚠ **개수를 문장에 박지 않는다** — 넓어질 때 사본만 낡는다.
_TOPICS = ("강우·강수", "식생·NDVI", "지형·DEM", "토지피복·LULC",
           "가뭄", "파일 포맷 예제")

#: 분류 축 5값 (PRD-01 · `M-1`). **정본은 DB CHECK 다** (`d3_dataset_description.category`) —
#: `_TOPICS` 와 같은 자리이고 같은 이유로 여기 사본이 있다: 검사를 안 하면 사용자의 오타가
#: IntegrityError → **500** 이 된다 (`CODE-REVIEW-20260903` #12).
#: ⚠ **국문 단일이다** — 화면이 병기하는 영문(`Meteorological & Climatic Factors`)은 표시
#: 전용이라 이 목록에 없다(미결-13 ⓐ). ⚠ 개수를 문장에 박지 않는다.
_CATEGORIES = ("수문 인자", "기상·기후 인자", "식생·탄소 인자",
               "사회·경제 인자", "환경 인자")

#: 유형 축 6값 (PRD-02 · `M-2`). 정본은 `d3_dataset_description.data_type` CHECK 다.
#: ⚠ 열쇠는 `dataType` 이고 컬럼은 `data_type` 이다 — `type` 을 피한 이름이다(PRD-02 축자).
_DATA_TYPES = ("지상관측자료", "위성자료", "재분석자료",
               "수치모형자료", "합성자료", "관측 기반 산출물")

#: 사람이 고른 가공 단계 4값 (PRD-03 · `M-3`). 정본은
#: `d3_dataset.processing_level_user_set` CHECK 다 — `0011` 이 지운 열의 재신설이다.
#: ⚠ **`LV_CAP` 과 다른 축이다.** `LV_CAP` 은 **파생** Lv 의 상한이고 여기 넷은 **사람이
#: 고르는 값**의 집합이다. 한 상수로 합치면 두 뜻이 붙어 버린다(`INTERVAL_UNITS` ↔
#: `PERIOD_GRANULARITIES` 와 같은 계열의 실패).
_PROCESSING_LEVELS = ("Lv0", "Lv1", "Lv2", "Lv3")

#: 관측 간격의 단위 6값 (PRD-17 · `M-6`). **정본은 DB CHECK 다**
#: (`d3_dataset_description.observation_interval_unit`) — `_TOPICS` 와 같은 자리이고
#: 같은 이유로 여기 사본이 있다: 검사를 안 하면 사용자의 오타가 IntegrityError → **500** 이 된다.
INTERVAL_UNITS = ("초", "분", "시", "일", "월", "년")

#: 기간의 최소 단위 6값 (PRD-18 · `M-7`). 정본은 `d3_dataset_autometa.period_granularity`
#: CHECK 다. ⚠ 위 목록과 **값은 같고 뜻이 다르다** — 하나는 「얼마 간격으로 재는가」,
#: 하나는 「기간을 어느 자리까지 말하는가」다. 한 상수로 합치면 두 뜻이 붙어 버린다.
PERIOD_GRANULARITIES = ("년", "월", "일", "시", "분", "초")

#: 사람 Lv ↔ 파생 Lv 불일치를 적는 자리 (PRD-03 · PRD-10 · 미결-2 ⓐ).
_level_log = logging.getLogger("colab_core.processing_level")


def warn_if_level_mismatch(db: Session, dataset_id: Ulid, user_set: object) -> None:
    """사람이 고른 Lv 와 파생 Lv 가 어긋나면 **경고만** 남긴다. 저장을 막지 않는다.

    미결-2 ⓐ 축자 = 「가공 단계를 사람이 고르고, 계보 계산값과 어긋나면 **경고만** 낸다
    (등록을 막지 않는다)」. 그래서 이 함수는 **아무것도 raise 하지 않는다** — 400 을
    내는 순간 확정 판정을 뒤집는 것이 된다.

    ⚠ **경고의 자리가 로그인 것은 이번 회차의 범위 때문이다.** 응답에 싣는 두 열쇠
    (`processingLevelDerived` · `processingLevelMismatch`)와 화면 안내 한 줄은 PRD-10 이고
    **`WU-B5`** 가 연다 — 그 열쇠를 여기서 미리 만들지 않는다(계약 열쇠는 이번 회차에
    셋뿐이다). 사람 값이 `NULL` 인 행은 **불일치가 정의되지 않는다**(PRD-10 축자).
    """
    if user_set is None:
        return
    summary = d4_lineage.LineageSummaryAdapter(db).summaries([str(dataset_id)]).get(str(dataset_id))
    derived = d3_catalog.processing_level(summary)
    # 사람 값은 `Lv2` 꼴 문자열이고 파생값은 정수다 — 앞 두 글자를 떼어 같은 축으로 읽는다.
    # 값 집합 검사(`validate_human_metadata`)를 이미 지났으므로 `Lv` 접두는 보장된다.
    if int(str(user_set)[2:]) != derived:
        _level_log.warning(
            "가공 단계 불일치 — dataset=%s 사람=%s 파생=Lv%s. 저장은 성공했다(경고만 · 미결-2 ⓐ).",
            dataset_id, user_set, derived)


#: 반쪽 관측 간격의 문구 — **한 자리에만 둔다.** 등록과 수정이 같은 문장을 낸다.
HALF_INTERVAL_MESSAGE = "관측 간격은 숫자와 단위를 함께 적어 주세요."

#: ⭑ **⟨19차 해제 · PRD-15⟩ 설명이 비었을 때의 문구 — 한 자리에만 둔다.**
#: 등록(`createDataset`)과 수정(`updateDataset`)이 **같은 문장**을 낸다. 두 벌을 두면
#: 한쪽만 고쳐지는 날이 오고, 그날 사용자는 같은 잘못에 다른 말을 듣는다.
EMPTY_SUMMARY_MESSAGE = "설명을 적어 주세요."

#: 설명이 **이미 비어 있던 기존 행**을 고칠 때의 문구. 위와 다른 사건이다 — 사용자가
#: 설명을 지운 것이 아니라 **원래 없던 것**이고, 그래서 「채워 주세요」다(미결-5 ⓐ ·
#: rev1 상세 문면과 같은 문장).
BLANK_SUMMARY_ON_UPDATE_MESSAGE = "설명이 아직 없어요 — 수정에서 채워 주세요."

#: ⭑ **⟨20차 해제 · PRD-01·02 · WU-B3⟩ 분류·유형을 안 실었을 때의 문구.**
#: 계약 `DatasetCreate.required` 에 `category`·`dataType` 이 올랐고, **런타임에 그것을
#: 집행하는 것은 등록 경로뿐이다**(집행 없는 신설 금지 · X2 §5-㉰-4). 화면에는 기본
#: 선택값이 서 있으므로 이 400 은 **계약을 안 지킨 호출자**에게만 간다.
#: ⛔ `DatasetUpdate` 는 이 검사를 하지 않는다 — 기존 전 행이 NULL 이다(미결-3 ⓐ).
MISSING_CATEGORY_MESSAGE = "분류를 골라 주세요"


def is_blank_summary(value: object) -> bool:
    """공백만 있는 설명은 **없는 것과 같다.**

    `minLength: 1` 은 공백 세 칸을 통과시킨다 — 계약이 못 막는 자리를 여기서 막는다.
    `btrim` 후 길이 검사(`d3_dataset_description.name` CHECK 와 같은 모양)의 코드 층 사본이다.
    """
    return not isinstance(value, str) or not value.strip()


def _is_datetime(value: str) -> bool:
    """계약 `DataPeriod` 는 `format: date-time` 이다 — **자유 문자열이 아니다.**

    검사 없이 내려보내면 `timestamptz` 캐스트가 DB 에서 죽고 **사용자의 오타가 500** 이 된다.
    `Z` 접미는 3.11+ `fromisoformat` 이 받는다.
    """
    try:
        dt.datetime.fromisoformat(value)
    except ValueError:
        return False
    return True


#: 계약 `DatasetVariable` 의 열쇠. **런타임에 `additionalProperties: false` 를 강제하는
#: 것은 이 집합뿐이다** — 오타 열쇠를 조용히 버리면 사용자는 적었다고 믿고 떠난다.
_VARIABLE_FIELDS = {"name", "unit", "valueRange", "missingRate", "representative"}

#: ⭑ **⟨20차 해제 · PRD-16⟩ 행이 0개인 데이터셋을 허용하지 않는다.** 문면은 rev1 축자이고
#: 화면(마지막 행 삭제 차단)과 **같은 문장**이다 — 두 벌로 적으면 한쪽만 고쳐진다.
AT_LEAST_ONE_VARIABLE = "변수는 하나 이상 있어야 해요"


def _validate_variables(variables: object) -> None:
    """변수 행 배열의 **형상**을 본다 — 값의 뜻은 보지 않는다(`VAL-006` 계열 자유 입력).

    형상이 어긋나면 아래 저장 코드가 타입 오류로 죽고 **사용자의 오타가 500** 이 된다.
    ⚠ **대표 둘도 여기서 400 이다** — 안 막으면 부분 UNIQUE 색인이 IntegrityError 를 내고
    그것은 500 으로 나간다(`CODE-REVIEW-20260903` #12 와 같은 자리).
    """
    if not isinstance(variables, list):
        raise errors.bad_request("변수 목록은 객체 배열이다.")
    # `null`·빈 배열은 **둘 다 0행**이다. 마지막 행 삭제를 화면이 막고 여기가 뒷문이다.
    if not variables:
        raise errors.bad_request(AT_LEAST_ONE_VARIABLE)
    representatives = 0
    for row in variables:
        if not isinstance(row, dict):
            raise errors.bad_request("변수 항목이 객체가 아니다.")
        unknown = set(row) - _VARIABLE_FIELDS
        if unknown:
            raise errors.bad_request(f"계약에 없는 필드다: {sorted(unknown)}")
        name = row.get("name")
        if not isinstance(name, str) or not name.strip():
            raise errors.bad_request("변수 이름은 빈 문자열이 아니다.")
        for key in ("unit", "valueRange", "missingRate"):
            if row.get(key) is not None and not isinstance(row[key], str):
                raise errors.bad_request(f"{key} 는 문자열이거나 null 이다.")
        flag = row.get("representative", False)
        if not isinstance(flag, bool):
            raise errors.bad_request("representative 는 참·거짓이다.")
        representatives += 1 if flag else 0
    if representatives > 1:
        # 아무도 안 고른 경우는 400 이 아니다 — **첫 행이 대표**가 된다(자동 보정 ·
        # `d3_catalog.replace_variables`). 대표 없는 저장이 성립하지 않게 하는 자리다.
        raise errors.bad_request("대표 변수는 한 행만 고를 수 있다.")


#: ⭑ **⟨20차 해제 · PRD-11 · WU-B4⟩ 공개 범위 거절 문면.** 값 집합의 정본은 DB CHECK 이고
#: (`d2_dataset_access.state` ＋ `d1_lab_profile.default_visibility` 두 표), 코드 층 사본은
#: `d2_access.ACCESS_STATES` 한 자리다 — 문면만 여기 둔다(봉투의 `allowed` 가 값을 말한다).
INVALID_ACCESS_STATE_MESSAGE = "공개 범위는 열림 · 잠김 · 지정 공개 중 하나예요."


def validate_access_state(changes: dict) -> None:
    """공개 범위 한 칸의 형상. **등록과 수정이 같은 함수를 쓴다** (`variables` 와 같은 규율).

    ⛔ 3값 밖 문자열을 그대로 흘리면 DB CHECK 위반이 IntegrityError → **500** 이 된다.
    사용자의 오타는 400 이다 — `catalog.py` 의 `topic`·`category` 와 같은 자리다.
    ⚠ `null` 은 값이 아니라 **「따로 정하지 않음」**이라 통과시킨다(연구실 기본값 경로).
    """
    if "accessState" not in changes:
        return
    value = changes["accessState"]
    if value is None:
        return
    if not isinstance(value, str) or value not in d2_access.ACCESS_STATES:
        raise errors.bad_request(INVALID_ACCESS_STATE_MESSAGE,
                                 {"allowed": list(d2_access.ACCESS_STATES)})


def validate_human_metadata(changes: dict) -> None:
    """`variables`·`crs`·`period` 의 **형상**을 본다 — **생성과 수정이 이 한 벌을 쓴다.**

    정본 `VAL-006` 은 셋을 「자유 입력 · 선택 입력 · 형식 검사는 하지 않는다」로 뒀다
    (`〈138〉`). 그래서 여기서 보는 것은 **값의 뜻이 아니라 형상**뿐이다: 형상이 어긋나면
    아래 저장 코드가 `AttributeError`·타입 오류로 죽고, **사용자의 오타가 500 으로**
    돌아간다. 400 과 500 은 「누구 잘못인가」가 다르다.

    ⭑ **2026-09-02 · `#62`** — `createDataset` 이 이 함수를 부른다. 검사기를 두 벌 두면
    한쪽만 고쳐지는 날이 오고, 그날 다른 한쪽은 조용히 틀린다.
    """
    if "variables" in changes:
        _validate_variables(changes["variables"])

    if changes.get("crs") is not None and "crs" in changes:
        if not isinstance(changes["crs"], str):
            raise errors.bad_request("좌표계는 문자열이다.")

    if changes.get("topic") is not None and "topic" in changes:
        # **DB CHECK 어휘 밖은 400 이다** (`CODE-REVIEW-20260903` #12). 검사하지 않으면
        # 그 값이 IntegrityError 로 떨어져 **사용자의 오타가 500** 이 된다.
        if changes["topic"] not in _TOPICS:
            raise errors.bad_request("주제는 정해진 값 중 하나다.", {"allowed": list(_TOPICS)})

    # ⭑ **⟨20차 해제 · PRD-01·02·03⟩ 분류 3축 — 같은 규율이다.**
    # 셋 다 **선택 입력**이라 `null`·열쇠 없음은 그냥 지나간다(그것이 기존 전 행의 상태다).
    # 값이 왔는데 집합 밖이면 **400 ＋ `allowed`** 다 — 안 막으면 CHECK 위반이 **500** 으로
    # 돌아가고 사용자의 오타가 서버 잘못이 된다 (`CODE-REVIEW-20260903` #12 와 같은 자리).
    # ⛔ **조합 검증을 만들지 않는다**(미결-14 ⓐ) — 세 축을 각자 따로 본다.
    for key, allowed, label in (
        ("category", _CATEGORIES, "분류"),
        ("dataType", _DATA_TYPES, "유형"),
        ("processingLevelUserSet", _PROCESSING_LEVELS, "가공 단계"),
    ):
        if changes.get(key) is not None and key in changes:
            if changes[key] not in allowed:
                raise errors.bad_request(f"{label}는 정해진 값 중 하나다.",
                                         {"allowed": list(allowed)})

    if changes.get("period") is not None and "period" in changes:
        period = changes["period"]
        # 계약 `DataPeriod` = `required: [start, end]` ＋ `additionalProperties: false`,
        # **`end` 는 `[string, "null"]`** (14차 해제 · Ted 판정 2026-09-02).
        #
        # ⭑ **끝이 없으면 무기한이다** — `null` 도 받고 열쇠가 아예 없는 것도 받는다.
        #   빠진 열쇠를 `null` 과 같이 다루는 것은 계약보다 **넓은** 쪽이라 문면을 안 깬다.
        # ⚠ **시작은 조건부가 아니다** — 시작 없는 끝은 기간이 아니라 오타다. 기간을 통째로
        #   비우는 뜻은 `period: null` 이고, 그것은 위의 `is not None` 이 먼저 걸러 낸다.
        # ⭑ **⟨19차 해제 · PRD-18⟩ `granularity` 가 열쇠 집합에 들어왔다.** 계약이
        #   `additionalProperties: false` 로 닫아 둔 자리를 연 것이 이번 회차이고,
        #   **런타임에 그 집합을 강제하는 것은 이 줄뿐이다.**
        if not isinstance(period, dict) or not set(period) <= {"start", "end", "granularity"} \
                or not isinstance(period.get("start"), str) \
                or not isinstance(period.get("end"), (str, type(None))):
            raise errors.bad_request(
                "기간은 `start` 문자열을 가진 객체다 — `end` 는 없거나 `null` 이면 무기한이다.")
        # 최소 단위는 **6값 밖이면 400** 이다 — 안 막으면 CHECK 위반이 500 으로 돌아간다.
        # 열쇠가 없거나 `null` 인 것은 「단위 미지정」이고 그것이 기존 전 행의 상태다.
        granularity = period.get("granularity")
        if granularity is not None and granularity not in PERIOD_GRANULARITIES:
            raise errors.bad_request("기간의 최소 단위는 정해진 6값 중 하나다.",
                                     {"allowed": list(PERIOD_GRANULARITIES)})
        # **자유 문자열을 받지 않는다** (`CODE-REVIEW-20260903` #12). 계약이
        # `format: date-time` 이고, 검사 없이 내려가면 `timestamptz` 캐스트가 DB 에서 죽는다.
        for key in ("start", "end"):
            value = period.get(key)
            if isinstance(value, str) and not _is_datetime(value):
                raise errors.bad_request(f"기간의 `{key}` 는 날짜·시각(ISO 8601)이다.")
        # ⭑ **⟨WU-B3 · PRD-40 수용 기준 ㈒⟩ 시작보다 앞선 종료는 400 이다.**
        # 화면은 종료를 비울 수 있게 됐고(비우면 `period_end = period_start`), 그래서 뒤집힌
        # 기간이 들어올 자리는 **직접 적은 값**뿐이다. 안 막으면 그 행의 기간 표시가
        # 「끝이 시작보다 앞」인 문장이 되고, 기간 조건 질의가 그 행을 영영 못 찾는다.
        # ⚠ **문자열 비교를 하지 않는다** — 시간대 표기가 다르면 같은 시각이 다르게 정렬된다.
        start_at, end_at = period.get("start"), period.get("end")
        if isinstance(start_at, str) and isinstance(end_at, str):
            start_dt = dt.datetime.fromisoformat(start_at)
            end_dt = dt.datetime.fromisoformat(end_at)
            # 한쪽만 시간대를 달았으면 견줄 수 없다 — 그 자리는 다투지 않고 지나간다.
            if (start_dt.tzinfo is None) == (end_dt.tzinfo is None) and end_dt < start_dt:
                raise errors.bad_request("기간의 종료는 시작보다 앞설 수 없다.")

    # ⭑ **⟨19차 해제 · PRD-17 · 미결-4 ⓐ⟩ 관측 간격 — 두 칸이 한 값이다.**
    #
    # `null` 은 「비운다」이고 위 `is not None` 이 먼저 걸러 낸다 — **선택 입력**이라
    # 비운 채 등록해도 성공한다(⛔ 등록 게이트가 아니다).
    if changes.get("observationInterval") is not None and "observationInterval" in changes:
        interval = changes["observationInterval"]
        if not isinstance(interval, dict) or not set(interval) <= {"value", "unit"}:
            raise errors.bad_request("관측 간격은 `value`·`unit` 두 열쇠를 가진 객체다.")
        value, unit = interval.get("value"), interval.get("unit")
        # **반쪽을 만들지 않는다** — 숫자만 오면 400 이다(PRD-17 수용 기준 축자).
        # DB CHECK 가 뒷문에서 같은 것을 막지만, 그 자리에서 걸리면 IntegrityError → 500 이다.
        # 400 과 500 은 「누구 잘못인가」가 다르다.
        if (value is None) != (unit is None):
            raise errors.bad_request(HALF_INTERVAL_MESSAGE)
        if value is not None:
            # `bool` 은 `int` 의 하위형이다 — `True` 를 `1분` 으로 받아들이지 않는다.
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise errors.bad_request("관측 간격의 수치는 숫자다.")
            if value <= 0:
                # 0 초 간격·음수 간격은 관측이 아니다. 계약이 `type: number` 까지만 말하므로
                # 뜻의 판정은 여기다.
                raise errors.bad_request("관측 간격의 수치는 0보다 크다.")
            if unit not in INTERVAL_UNITS:
                raise errors.bad_request("관측 간격의 단위는 정해진 6값 중 하나다.",
                                         {"allowed": list(INTERVAL_UNITS)})


@router.patch("/datasets/{datasetId}", name="updateDataset")
def update_dataset(datasetId: str, body: dict | None = Body(default=None),
                   subject: Subject = Depends(current_subject),
                   db: Session = Depends(scoped_db)) -> dict:
    """**올린 뒤에 고치는 길** (`〈127〉` Ted 판정 ㈎ · `〈138〉`·`〈140〉` · ㈏ 범위).

    `#36` 이 열려 있던 이유가 이 op 의 부재다 — `D-01`·`D-02` 의 `summary` 를 채울
    **공개 경로가 없었다.** 다른 셋은 전부 막혀 있다: `deleteDataset` 501 · 재적재는
    12 → 14 를 만들고 · DB 직접 `UPDATE` 는 `㊾-③` 위반.

    **부분 수정이다.** 보내지 않은 열쇠는 안 건드리고, `null` 을 **명시적으로** 보내는
    것은 **비우라는 뜻**이다. 둘을 접으면 요약만 고치려다 Lv 가 날아간다.
    """
    # 판정은 **형제 op 들이 쓰는 그 헬퍼 하나**가 한다 — `업로드·편집` 스위치
    # (`〈59〉-②`·`P-6`). 두 벌을 두면 한쪽만 고쳐지는 날이 온다.
    # `ingestion` 이 이 모듈을 import 하므로 되짚는 방향은 **부를 때** 푼다.
    from .ingestion import _require_upload_edit
    _require_upload_edit(db, subject)

    payload = body if isinstance(body, dict) else {}
    unknown = sorted(set(payload) - set(_UPDATE_FIELDS))
    if unknown:
        # **조용히 무시하지 않는다.** 무시하면 사용자는 고쳤다고 믿고 떠나고,
        # `format` 처럼 **원래 못 고치는 값**을 보낸 경우 그 사실이 안 드러난다.
        raise errors.bad_request(f"요청에 계약에 없는 필드가 있다: {unknown}",
                                 {"allowed": list(_UPDATE_FIELDS)})

    if not Ulid.is_valid(datasetId):
        raise errors.bad_request("datasetId 가 정규 ID 가 아니다.")
    dataset_id = Ulid(datasetId)
    if not d3_catalog.dataset_exists(db, dataset_id):
        raise errors.not_found("데이터셋을 찾지 못했다.")

    changes = {k: v for k, v in payload.items()}

    if "name" in changes:
        name = changes["name"]
        if not isinstance(name, str) or not name.strip():
            raise errors.bad_request("데이터셋 이름을 적어 주세요.")   # ERR-001 문구 그대로

    # ⭑ **⟨19차 해제 · PRD-15 · 미결-5 ⓐ⟩ 설명은 「고치는 순간」 필수가 된다.**
    #
    # 두 갈래다 — 둘이 다른 사건이라 문구도 다르다.
    #  ⑴ **열쇠가 왔다** → 비울 수 없다. 계약이 `type: string, minLength: 1` 로 `null` 을
    #     닫았고, 공백만 있는 문자열은 `minLength` 가 못 막아 여기서 `strip` 으로 막는다.
    #  ⑵ **열쇠가 안 왔는데 저장된 값이 비어 있다** → 400. 미결-5 ⓐ 축자 =
    #     「그 행을 수정할 때 채우게 한다」. 열쇠 생략의 뜻(「그대로 두라」)은 안 바뀌지만,
    #     **그대로 둔 결과가 빈 설명이면 그 수정은 저장되지 않는다.**
    #     ⛔ 이것이 「일괄 채우기」가 아닌 이유 — **읽기는 종전대로 되고**(상세가 안내
    #     문구를 보인다) 행을 서버가 먼저 고치지도 않는다. 사람이 그 행에 손을 댈 때만 묻는다.
    #     판정은 저장된 값을 봐야 하므로 계약이 낼 수 없다 — 그래서 서버에 있다.
    if "summary" in changes:
        if is_blank_summary(changes["summary"]):
            raise errors.bad_request(EMPTY_SUMMARY_MESSAGE)
        changes["summary"] = changes["summary"].strip()
    elif changes:
        core = d3_catalog.find_dataset_core(db, dataset_id)
        if core is not None and is_blank_summary(core.summary):
            raise errors.bad_request(BLANK_SUMMARY_ON_UPDATE_MESSAGE)

    if "representativeFileId" in changes:
        file_id = changes["representativeFileId"]
        if file_id is not None:
            if not Ulid.is_valid(file_id):
                raise errors.bad_request("representativeFileId 가 정규 ID 가 아니다.")
            # **FK 가 못 막는 자리다** — `d3_file` 은 한 표라 다른 데이터셋의 조각을
            # 가리켜도 참조 무결성은 만족한다. 막는 것은 여기뿐이다.
            if not d3_catalog.file_belongs_to(db, file_id=file_id,
                                              dataset_id=dataset_id):
                raise errors.bad_request("대표 조각은 이 데이터셋의 조각이어야 한다.")

    # 세 자유 입력 칸의 형상 — **`createDataset` 과 같은 함수다** (`#62`).
    validate_human_metadata(changes)
    validate_access_state(changes)

    # ⭑ **⟨20차 해제 · PRD-11 · WU-B4⟩ 공개 범위는 D2 의 값이다.** D3 변경분에서 **떼어 낸 뒤**
    # `d2_access` 경로로 쓴다 — `d3_catalog.update_dataset` 에 넘기면 없는 열을 고치려 든다.
    # `잠김` 으로 내리면 그 함수가 **같은 트랜잭션에서** 유효 grant 를 전부 만료한다.
    if "accessState" in changes:
        d2_access.set_access_state(db, dataset_id=dataset_id,
                                   state=changes.pop("accessState"))

    if changes:
        d3_catalog.update_dataset(db, dataset_id=dataset_id, changes=changes)
        # ⭑ **⟨20차 해제 · PRD-03 · 미결-2 ⓐ⟩ 수정도 같은 경고를 낸다.** 등록에만 두면
        # 사람이 나중에 Lv 를 바꾼 순간의 불일치를 아무도 못 본다. **막지 않는다.**
        warn_if_level_mismatch(db, dataset_id, changes.get("processingLevelUserSet"))
    return get_dataset(datasetId, subject=subject, db=db)


@router.get("/datasets/{datasetId}", name="getDataset")
def get_dataset(datasetId: str,
                subject: Subject = Depends(current_subject),
                db: Session = Depends(scoped_db)) -> dict:
    """S-05 상단 — 헤더 · 기본 정보 · 활용 프로젝트.

    **잠긴 데이터도 200 이다** (P-13 · `Policy_승인_처리 §8`). 403 을 쓰면 접근 요청 흐름이
    죽는다 — 없는 것으로 만들면 요청할 상대조차 사라진다. 대신 `basicInfo` 를 **통째로 비운다**
    (`Policy_데이터셋_상세 §7` 잠김(허용 안 됨) = 헤더 요약 + 잠김 안내). 카탈로그가 잠긴 행에도
    `조각 N` 을 띄우는 것과 달라 보이는 것은 **의도다** (P1.md §2-③④).
    """
    if not Ulid.is_valid(datasetId):
        raise errors.bad_request("datasetId 가 정규 ID 가 아니다.")
    return dataset_detail(db, subject, Ulid(datasetId))


def dataset_detail(db: Session, subject: Subject, dataset_id: Ulid) -> dict:
    """`DatasetDetail` 한 벌. `getDataset` 과 `createDataset` 이 **같은 함수**를 쓴다 —
    등록 직후 화면이 상세로 이동하므로(`Policy §7.2`) 두 자리가 다른 값을 그리면 안 된다."""
    datasetId = str(dataset_id)
    core = d3_catalog.find_dataset_core(db, dataset_id)
    if core is None:
        # ⭑ ⟨개정 2026-09-03 · 17차 해제 · Ted 판정 ②⟩ **자기 연구실 묘비만 구분한다.**
        #
        # 종전 규칙(그리고 그 사유)은 그대로 남는다 — 「경계 밖이면 RLS 가 이미 행을
        # 지웠고(P-9·P-10), 묘비면 상세 화면이 없다(§7). 둘을 같은 404 로 낸다 —
        # **구분해 주면 그 자체가 존재의 누설이다**」. **누설 금지가 완화된 것이 아니다.**
        #
        # 좁혀진 것은 적용 범위 하나다. **보는 사람의 연구실에서 지워진 행**은 그 사람이
        # 지워지기 전에 이미 목록에서 보고 있던 것이라, 「지워졌다」를 말해도 **새로 새는
        # 사실이 0** 이다. 그래서 그 한 칸만 410 이고 —
        #
        #   ⑴ 내 연구실 · 묘비        → **410 GONE** (`Policy_데이터셋_상세 §9` 묘비 문구)
        #   ⑵ 남의 연구실 · 묘비      → 404 (있었다는 사실 자체가 누설이다)
        #   ⑶ 남의 연구실 · 생존      → 404
        #   ⑷ 있었던 적 없는 id       → 404
        #
        # — ⑵⑶⑷ 는 **본문까지 한 글자도 같아야 한다**. 상태코드만 맞추고 문구가 갈리면
        # 존재는 그대로 샌다(시험이 세 응답의 동일성을 직접 대조한다).
        #
        # ⚠ `is_own_lab_tombstone` 에 `lab_id` 조건을 적지 않는 것이 판정의 전부다 —
        # 경계는 RLS 가 걸고, 그래서 ⑵ 는 「묘비 아님」이 아니라 **「행 없음」**으로 떨어진다.
        if d3_catalog.is_own_lab_tombstone(db, dataset_id):
            raise errors.gone()
        raise errors.not_found()

    ids = [dataset_id]
    access_adapter = d2_access.DatasetAccessAdapter(db)
    access = access_adapter.dataset_access(ids).get(datasetId)
    verification = access_adapter.verification(ids).get(datasetId)
    summary = d4_lineage.LineageSummaryAdapter(db).summaries(ids).get(datasetId)
    body_accessible = False if access is None else access.body_accessible

    role = d2_access.role_of(db, subject.account_id)
    permissions = d2_access.permissions_of(db, subject.account_id, role)
    # 승인 처리(`P6`)가 쓰는 두 사실. 둘 다 **D2 의 자기 표**에서 온다.
    pending_requests = d2_access.datasets_with_pending_request(db, ids)
    verification_pending = d2_access.pending_verification_of(db, dataset_id) is not None
    viewer = str(subject.account_id)
    is_professor = role == "교수"
    is_owner = core.owner_id == viewer
    is_uploader = core.uploader_id == viewer
    verified = False if verification is None else verification.verified

    meta = d3_catalog.find_autometa(db, dataset_id)
    basic_info = None
    projects = None
    if body_accessible:
        # **끝은 조건부다** — 시작만 있으면 무기한이고, 그때 `end` 는 `null` 로 나간다
        # (14차 해제). 끝의 유무로 기간 전체를 떨어뜨리면 저장된 시작이 화면에서 사라진다.
        period = None
        if meta is not None and meta.period_start is not None:
            period = {"start": _iso(meta.period_start),
                      "end": None if meta.period_end is None else _iso(meta.period_end),
                      # ⭑ **⟨19차 해제 · PRD-18⟩ 최소 단위를 함께 내린다.** 저장은 종전대로
                      # 시각값이고(미결-18 ⓐ) 이 열쇠는 **그 시각값을 어느 자리까지 읽을지**를
                      # 말한다. `None` 이면 단위 미지정이고 화면은 종전 표기 그대로다.
                      "granularity": meta.period_granularity}
        basic_info = {
            # ⭑ **⟨20차 해제 · PRD-01·02·03⟩ 분류 3축.** 셋 다 **사람이 고르는 값**이라
            # `meta`(자동으로 읽은 정보)가 아니라 `core` 에서 온다. `None` 이면 아직 안
            # 고른 것이고 화면이 「분류를 아직 안 골랐어요」·「유형 미지정」·`자동` 을 그린다
            # (미결-3 ⓐ — 마이그레이션이 backfill 을 하지 않았다).
            "category": core.category,
            "dataType": core.data_type,
            "processingLevelUserSet": core.processing_level_user_set,
            # ⭑ **⟨20차 해제 · PRD-16⟩ 정본은 `d3_dataset_variable` 이다.**
            # ⚠ 행이 0개면 **`autometa.variables` 로 퇴행한다** — 파이프라인이 헤더에서 읽어
            #   채운 이름이 그 배열에만 있는 데이터셋이 있고(등록·수정 경로는 그 배열을 안
            #   쓴다 · 미러 트리거 `M-10` 은 R-B-2), 퇴행이 없으면 그 상세의 구성 칸이
            #   이유 없이 빈다. **쓰기 정본이 둘이 되는 것은 아니다** — 읽기 투영이다.
            "variables": _variables_payload(db, dataset_id, meta),
            "crs": None if meta is None else meta.crs,
            "period": period,
            # ⭑ **⟨19차 해제 · PRD-17⟩ 관측 간격 두 칸.** 사람이 적는 값이라 `meta` 가 아니라
            # `core`(`d3_dataset_description`) 에서 온다. **둘 다 값이거나 둘 다 없다**
            # (pair CHECK) — 반쪽이 내려가는 경로가 없다. 표시 문자열은 화면이 조립한다.
            "observationInterval": _observation_interval(core),
            "grid": None if meta is None else meta.grid,
            # **화면이 쓰는 값은 이쪽이다** (PRD-21) — 조각의 확장자. 점 없는 소문자(`nc`)이고
            # 화면이 `*.nc` 로 조립한다. `None` 이면 파일명이 확장자를 말하지 않는 것이고
            # 화면은 아래 `format` 으로 퇴행한다 — 지어내지 않는다.
            "fileExtension": None if meta is None else meta.file_extension,
            # **내부 판별값이다. 화면에 쓰지 않는다** — `.hdf` 하나가 서로 호환되지 않는 두
            # 포맷을 가리켜(`P-10`·`R-09`) 화면이 단정하면 그 자리에서 거짓말이 된다.
            # 남기는 이유 = 파이프라인·미리보기가 계속 쓰고, 확장자가 없는 행의 퇴행 표시이며,
            # 검색 색인이 아직 이 열을 문다(색인 재정의 `M-10` 은 R-B 에서 한 번만 돈다).
            "format": None if meta is None else meta.format,
            "files": {
                # 조각 수는 메타 열에서 온다 — 본체를 세지 않는다 (PLAN-SoT §9-㊼).
                # **격자는 빠진 본체 파일 수**다 (Ted 판정 2026-08-26) — 바로 아래
                # `hasReferenceGridFile` 이 격자의 유무를 따로 말한다.
                "count": core.file_count,
                "totalSizeBytes": 0 if meta is None or meta.total_size_bytes is None
                                  else meta.total_size_bytes,
                "hasReferenceGridFile": d3_catalog.has_reference_grid_file(db, dataset_id),
            },
            "sourceLabel": core.source_label,
            "owner": _account_ref(core.owner_id, core.owner_name),
            "uploader": _account_ref(core.uploader_id, core.uploader_name),
        }
        projects = [
            {
                "projectId": use.project_id,
                "name": use.name,
                "type": use.type,
                "period": _project_period(use.period_start, use.period_end),
                "usageNote": use.usage_note,
            }
            for use in d6_project.ProjectLinkAdapter(db).uses_of(dataset_id)
        ]

    return {
        "datasetId": core.dataset_id,
        # 파일명(묶음 이름)은 본체 쪽 사실이라 잠기면 내리지 않는다 — 잠긴 상세의 노출 범위는
        # `이름 · 요약 · 헤더 태그` 까지다 (Policy_승인_처리 §8 적용 지점 표).
        "fileName": (None if not body_accessible or meta is None else meta.bundle_file_name),
        "name": core.name,
        "summary": core.summary,
        "topic": core.topic,
        "processingLevel": d3_catalog.processing_level(summary),
        "lineageState": d3_catalog.lineage_state(core, summary),
        "verification": {
            "verified": verified,
            "approver": None if verification is None
                        else _account_ref(verification.approver_id, verification.approver_name),
            "approvedAt": None if verification is None else _iso(verification.approved_at),
            "cancelledBy": None if verification is None
                           else _account_ref(verification.cancelled_by_id,
                                             verification.cancelled_by_name),
            "cancelledAt": None if verification is None else _iso(verification.cancelled_at),
            "cancellationReason": None if verification is None
                                  else verification.cancellation_reason,
        },
        "accessState": "열림" if access is None else access.access_state,
        # ⭑ **⟨20차 해제 · PRD-11 · WU-B4⟩ 지금 볼 수 있는 사람 수.** 소유자가 `나만 보기` 로
        # 내릴 때 화면이 「지금 볼 수 있는 사람 N명의 접근이 끊깁니다」로 되묻는 그 N 이다.
        # ⛔ 사람 목록을 내리지 않는다 — 되묻는 문면에 필요한 것은 수다.
        "activeGrantCount": d2_access.active_grant_count(db, dataset_id),
        "bodyAccessible": body_accessible,
        # 보는 사람이 이미 요청을 보냈는가 (`Policy_승인_처리 §7.2` 검토 대기).
        # ⭑ **`P6` 이 저장처를 세우면서 이 값이 참이 될 수 있게 됐다.** 종전 기재
        # 「저장처가 없으므로 지금 참일 수 있는 값은 false 하나뿐이고, 지어내지 않는다」는
        # 마이그레이션 `0010`(`d2_dataset_access_request`)으로 해소됐다.
        # **보는 사람 기준이다** — 남이 건 요청은 이 칩을 켜지 않는다(질의가 `current_account_id()`).
        "accessRequestPending": datasetId in pending_requests,
        "uploadedAt": _iso(core.uploaded_at),
        "lastModifiedAt": _iso(core.last_modified_at),
        "lineageConfirmedAt": _iso(core.lineage_confirmed_at),
        "basicInfo": basic_info,
        "projects": projects,
        # **화면이 조건을 임의로 정하지 않는다** (P-7). 헤더 우측 한 자리가 상태 × 보는 사람에
        # 따라 셋으로 갈리는 규칙은 `Policy_승인_처리 §8` 이 정본이다.
        "actions": {
            # ① 미승인 + 올린 사람·소유자 → `✓ 승인 요청`
            "canRequestVerification": bool(body_accessible and not verified
                                           and (is_owner or is_uploader)),
            # ② 검토 대기 + 교수 → `승인`. ⭑ **`P6` 이 검토 대기 표를 세워 참이 될 수 있게 됐다.**
            #    종전 기재 「대기 건이 존재할 수 없으므로 지금 참이 될 수 없다」는 해소됐다.
            #    **교수라는 이유만으로 켜지 않는다** — 대기 건이 실제로 있을 때만이다.
            #    `승인 위임` 은 여기에 들어오지 않는다: Verified 는 위임 불가다 (§1.2 · P-22).
            "canApproveVerification": bool(is_professor and not verified
                                           and verification_pending),
            # ③ 승인됨 + 교수 → `⋯` 더보기 → `승인 취소`
            "canCancelVerification": bool(is_professor and verified),
            # 시각화 편집·계보 수정은 `업로드·편집` 스위치다 (Policy_데이터셋_상세 §6).
            "canEditLineage": bool(body_accessible and permissions.get("업로드·편집", False)),
            # 삭제는 소유자 또는 교수 (§6).
            "canDelete": bool(is_owner or is_professor),
            # 다운로드는 열린 데이터 또는 허용됨 (§8).
            "canDownload": body_accessible,
            # 잠겨서 못 보는 것은 숨기지 않는다 — 그 자리가 접근 요청이 된다 (P-13).
            "canRequestAccess": not body_accessible,
        },
    }
