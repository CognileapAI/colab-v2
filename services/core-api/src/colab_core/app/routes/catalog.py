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

from ...domains import d1_identity, d2_access, d3_catalog, d4_lineage, d6_project
from ...kernel import errors
from ...kernel.auth import Subject
from ...kernel.ids import Ulid
from ...kernel.scope import read_only_scope
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
        if level < 0:
            raise errors.bad_request("processingLevel 은 0 이상이다.")
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
    unknown = sorted(set(payload) - {"query", "limit", "cursor"})
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
        # **읽기 전용 트랜잭션**에서 돈다 — 검색이 한 줄도 쓰지 않는다는 것을
        # 문서가 아니라 Postgres 의 거절이 지킨다.
        with read_only_scope(request.app.state.session_factory, subject) as ro:
            matches, total = d3_catalog.search_datasets(
                ro, terms=answer["terms"], topic=answer["topic"],
                limit=limit, offset=offset)
        hits, next_cursor = dataset_search.compose(
            matches, lab_name=lab_name, searched=searched_count, topic=answer["topic"],
            # 해석이 모델에서 오지 않았으면 근거 한 줄이 그 사실을 밝힌다.
            interpretation_degraded=answer["source"] != "llm",
            # 그래프가 데려온 말이면 근거 한 줄이 그 엣지를 이름으로 적는다 (`〈90〉-㉱`).
            expansions=answer.get("expansions"),
            total=total, offset=offset)

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
            items.append(enriched)

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


def _project_period(start, end) -> dict:
    """프로젝트 기간은 **연·월까지**이고 진행 중이면 종료가 비어 있다 (Policy_프로젝트 §5)."""
    def month(value):
        return None if value is None else f"{value.year:04d}-{value.month:02d}"
    return {"start": month(start), "end": month(end)}


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
        # 경계 밖이면 RLS 가 이미 행을 지웠고(P-9·P-10), 묘비면 상세 화면이 없다(§7).
        # 둘을 같은 404 로 낸다 — 구분해 주면 그 자체가 존재의 누설이다.
        raise errors.not_found()

    ids = [dataset_id]
    access_adapter = d2_access.DatasetAccessAdapter(db)
    access = access_adapter.dataset_access(ids).get(datasetId)
    verification = access_adapter.verification(ids).get(datasetId)
    summary = d4_lineage.LineageSummaryAdapter(db).summaries(ids).get(datasetId)
    body_accessible = False if access is None else access.body_accessible

    role = d2_access.role_of(db, subject.account_id)
    permissions = d2_access.permissions_of(db, subject.account_id, role)
    viewer = str(subject.account_id)
    is_professor = role == "교수"
    is_owner = core.owner_id == viewer
    is_uploader = core.uploader_id == viewer
    verified = False if verification is None else verification.verified

    meta = d3_catalog.find_autometa(db, dataset_id)
    basic_info = None
    projects = None
    if body_accessible:
        period = None
        if meta is not None and meta.period_start is not None and meta.period_end is not None:
            period = {"start": _iso(meta.period_start), "end": _iso(meta.period_end)}
        basic_info = {
            "variables": [] if meta is None else meta.variables,
            "crs": None if meta is None else meta.crs,
            "period": period,
            "grid": None if meta is None else meta.grid,
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
        "bodyAccessible": body_accessible,
        # 보는 사람이 이미 요청을 보냈는가. **접근 요청의 저장처가 P0 스키마에 없다** —
        # 그 자리는 P6(`createAccessRequest` = NOT_IMPLEMENTED_NO_STORE)다.
        # 저장처가 없으므로 지금 참일 수 있는 값은 false 하나뿐이고, 지어내지 않는다.
        "accessRequestPending": False,
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
            # ② 검토 대기 + 교수 → `승인`. **검토 대기의 저장처가 없다**(P6) — 대기 건이
            #    존재할 수 없으므로 지금 참이 될 수 없다. 교수라는 이유만으로 켜지 않는다.
            "canApproveVerification": False,
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
