"""D3 Catalog — 데이터셋 · 파일 · 메타.

계보 상태와 가공 단계 Lv 는 **저장하지 않고 계산한다** (PLAN-SoT §9-⑳). 계산에 필요한
D4 사실은 `ports.LineageSummaryPort` 로 받는다 — D4 테이블을 여기서 직접 읽지 않는다.
"""
from __future__ import annotations

import dataclasses

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..kernel.ids import Ulid
from ..ports.lineage import LV_CAP, LineageSummary

# 묘비(삭제된 데이터셋)는 카탈로그 목록에 서지 않는다 — 상세 화면도 없다
# (Policy_데이터셋_상세 §7). 계보 그래프에는 묘비 노드로 남는다(그건 D4 의 일이다).
_ROWS = text("""
    SELECT d.id, d.uploader_account_id, d.owner_account_id, d.source_label,
           d.last_modified_at, d.uploaded_at, d.lineage_confirmed_at,
           d.processing_level_user_set,
           dd.name, dd.topic, dd.summary,
           u.name AS uploader_name,
           -- **조각 수는 메타다** — `d3_file` 을 세지 않는다 (PLAN-SoT §9-㊼).
           -- `body_access` RESTRICTIVE 아래서 본체 테이블을 세면 잠긴 행이 0 을 낸다(실측).
           -- 트리거가 이 열을 유지하고, `tests/test_file_count_drift.py` 가 드리프트를 잡는다.
           --
           -- **응답으로 나가는 수는 본체 기준이다** (Ted 판정 2026-08-26). 저장 열은
           -- 격자 포함 총수로 두고 읽는 시점에 격자를 뺀다 — 마이그레이션이 없다.
           -- 잠긴 데이터셋은 격자 행도 안 보여 빼는 값이 0 이 되고 총수가 그대로 나간다
           -- (최대 2 초과 계상). `tests/test_file_count_body_only.py` 가 그 경로를 못 박는다.
           d.file_count - _grid.n AS file_count
      FROM d3_dataset d
      LEFT JOIN LATERAL (
        SELECT count(*) AS n FROM d3_file f
         WHERE f.dataset_id = d.id AND f.kind = '기준 격자 파일'
      ) AS _grid ON true
      JOIN d3_dataset_description dd ON dd.dataset_id = d.id
      JOIN d1_account u ON u.id = d.uploader_account_id
     WHERE d.deleted_at IS NULL
""")

#: `common.json#/$defs/FileKind` 의 둘 중 격자 쪽. **값 집합의 정본은 계약이다** —
#: 여기 있는 것은 그 값을 SQL 과 대조하는 상수일 뿐 두 번째 선언이 아니다.
GRID_KIND = "기준 격자 파일"

_FILES = text("""
    SELECT f.id, f.file_name, f.kind, f.carries_lat, f.carries_lon
      FROM d3_file f
     WHERE f.dataset_id = :dataset_id
     ORDER BY f.kind DESC, f.file_name, f.id
""")

_EXISTS = text("SELECT 1 FROM d3_dataset WHERE id = :dataset_id AND deleted_at IS NULL")

# 상세 한 건. 목록 질의와 같은 형태를 쓰되 소유자 이름까지 함께 읽는다 —
# 상세의 `기본 정보` 는 소유자와 올린 사람을 **둘 다** 적는다 (Policy_데이터셋_상세 §5 · P-30).
_ONE = text("""
    SELECT d.id, d.uploader_account_id, d.owner_account_id, d.source_label,
           d.last_modified_at, d.uploaded_at, d.lineage_confirmed_at,
           -- 목록 질의와 **같은 식**이다 — 두 화면이 다른 수를 그리면 안 된다 (위 주석).
           d.file_count - _grid.n AS file_count,
           d.processing_level_user_set,
           dd.name, dd.topic, dd.summary,
           u.name AS uploader_name,
           o.name AS owner_name
      FROM d3_dataset d
      LEFT JOIN LATERAL (
        SELECT count(*) AS n FROM d3_file f
         WHERE f.dataset_id = d.id AND f.kind = '기준 격자 파일'
      ) AS _grid ON true
      JOIN d3_dataset_description dd ON dd.dataset_id = d.id
      JOIN d1_account u ON u.id = d.uploader_account_id
      JOIN d1_account o ON o.id = d.owner_account_id
     WHERE d.id = :dataset_id AND d.deleted_at IS NULL
""")

# 자동으로 읽은 정보. 사람이 타이핑하지 않는다 (Policy_데이터셋_상세 §5).
_AUTOMETA = text("""
    SELECT format, variables, period_start, period_end, crs, grid,
           total_size_bytes, bundle_file_name
      FROM d3_dataset_autometa
     WHERE dataset_id = :dataset_id
""")

# 기준 격자 파일 유무. **없으면 없다고 적는다** — 짝 파일이 없어 못 그리는 것인지
# 원래 필요 없는 포맷인지가 갈린다 (Policy_데이터셋_상세 §5).
# 본체 테이블이라 잠긴 데이터에서는 0행이 나온다. 그래서 이 값은 `basicInfo` 를
# 내리는 경우(=본체에 닿는 경우)에만 묻는다.
_HAS_GRID = text("""
    SELECT 1 FROM d3_file
     WHERE dataset_id = :dataset_id AND kind = '기준 격자 파일'
     LIMIT 1
""")


@dataclasses.dataclass(frozen=True)
class DatasetAutometa:
    """자동으로 읽은 메타. 값이 없으면 `None` 이고 **지어내지 않는다**."""

    format: str | None
    variables: list[str]
    period_start: object
    period_end: object
    crs: str | None
    grid: str | None
    total_size_bytes: int | None
    bundle_file_name: str | None


@dataclasses.dataclass(frozen=True)
class DatasetCore:
    dataset_id: str
    name: str
    topic: str | None
    summary: str | None
    #: **본체 파일 수.** 기준 격자 파일은 세지 않는다 (Ted 판정 2026-08-26).
    #: 저장 열 `d3_dataset.file_count` 는 격자 포함 총수로 남고, 이 값은 그 열에서
    #: 격자 수를 뺀 것이다. 잠긴 데이터셋은 격자 행이 안 보여 총수가 그대로 온다.
    file_count: int
    uploader_id: str
    uploader_name: str
    owner_id: str | None = None
    owner_name: str | None = None
    source_label: str | None = None
    last_modified_at: object = None
    uploaded_at: object = None
    lineage_confirmed_at: object = None
    #: **사람이 고른 가공 단계.** `None` 이면 계보에서 파생한다 (`〈140〉`).
    #: 계산 결과는 여기 담기지 않는다 — 담는 순간 계보와 갈라진다.
    processing_level_user_set: int | None = None


def list_dataset_cores(session: Session) -> list[DatasetCore]:
    """연구실 경계는 RLS 가 이미 걸었다 — 여기에 lab_id 조건을 다시 적지 않는다."""
    rows = session.execute(_ROWS).mappings().all()
    return [
        DatasetCore(
            dataset_id=r["id"], name=r["name"], topic=r["topic"], summary=r["summary"],
            file_count=int(r["file_count"]), uploader_id=r["uploader_account_id"],
            uploader_name=r["uploader_name"], owner_id=r["owner_account_id"],
            owner_name=None, source_label=r["source_label"],
            last_modified_at=r["last_modified_at"], uploaded_at=r["uploaded_at"],
            lineage_confirmed_at=r["lineage_confirmed_at"],
            processing_level_user_set=r["processing_level_user_set"],
        )
        for r in rows
    ]


def find_dataset_core(session: Session, dataset_id: Ulid) -> DatasetCore | None:
    """상세 한 건. **묘비는 여기서 걸러진다** — 지운 데이터는 상세 화면이 없다 (§7)."""
    r = session.execute(_ONE, {"dataset_id": str(dataset_id)}).mappings().first()
    if r is None:
        return None
    return DatasetCore(
        dataset_id=r["id"], name=r["name"], topic=r["topic"], summary=r["summary"],
        file_count=int(r["file_count"]), uploader_id=r["uploader_account_id"],
        uploader_name=r["uploader_name"], owner_id=r["owner_account_id"],
        owner_name=r["owner_name"], source_label=r["source_label"],
        last_modified_at=r["last_modified_at"], uploaded_at=r["uploaded_at"],
        lineage_confirmed_at=r["lineage_confirmed_at"],
        processing_level_user_set=r["processing_level_user_set"],
    )


def find_autometa(session: Session, dataset_id: Ulid) -> DatasetAutometa | None:
    r = session.execute(_AUTOMETA, {"dataset_id": str(dataset_id)}).mappings().first()
    if r is None:
        return None
    return DatasetAutometa(
        format=r["format"], variables=list(r["variables"] or []),
        period_start=r["period_start"], period_end=r["period_end"],
        crs=r["crs"], grid=r["grid"],
        total_size_bytes=(None if r["total_size_bytes"] is None else int(r["total_size_bytes"])),
        bundle_file_name=r["bundle_file_name"],
    )


#: 데이터가 다루는 시간 범위 — **메타 열이라 잠긴 데이터셋도 나온다**(본체가 아니다).
#: 소속 데이터셋 표(`ProjectDatasetRow.period`)가 이 값을 쓴다.
_PERIODS = text("""
    SELECT dataset_id, period_start, period_end
      FROM d3_dataset_autometa
     WHERE dataset_id = ANY(CAST(:ids AS char(26)[]))
       AND period_start IS NOT NULL AND period_end IS NOT NULL
""")


def periods_of(session: Session, dataset_ids: list[Ulid]) -> dict[str, tuple]:
    """여러 건의 기간을 한 번에. **없으면 키가 없다** — 없는 기간을 지어내지 않는다."""
    if not dataset_ids:
        return {}
    rows = session.execute(_PERIODS, {"ids": [str(i) for i in dataset_ids]}).mappings()
    return {r["dataset_id"]: (r["period_start"], r["period_end"]) for r in rows}


def has_reference_grid_file(session: Session, dataset_id: Ulid) -> bool:
    return session.execute(_HAS_GRID, {"dataset_id": str(dataset_id)}).first() is not None


#: 자동완성이 후보를 낼 수 있는 칸 — **D3 이 소유한 자유 입력 칸만** (`〈138〉` · 결정 2-10).
#:
#: ⚠ **`가공 방식` 은 여기 없다.** 그 어휘는 D9 온톨로지 시드가 소유하고(`d9_method_term`,
#: 결정 2-11) **core-api 는 그 저장소에 붙지 않는다**(`CLAUDE.md §3-1`·`§3-3`). 넣으면
#: 불변규칙을 깬다 — 그쪽은 ai-service 의 사전 표면으로 간다.
#:
#: 값은 **계약 층 enum 으로 만들지 않는다**(`NB-E`) — 서버가 모르는 값이면 400 이다.
SUGGESTABLE_FIELDS = ("sourceLabel", "variables", "crs")

#: 원천 표기·좌표계 — `d3_dataset` / `d3_dataset_autometa` 의 **스칼라** 열이다.
_SUGGEST_SCALAR = {
    "sourceLabel": ("d3_dataset", "source_label"),
    "crs": ("d3_dataset_autometa", "crs"),
}


def suggest_field_values(session: Session, *, field: str, prefix: str | None,
                         limit: int) -> list[dict]:
    """이 연구실에서 **이미 쓰인 값**만 돌려준다 (`listDatasetFieldSuggestions`).

    **만들어 내지 않는다.** 후보에 없는 값이 섞이면 사용자가 그것을 「연구실에서 쓰는
    표기」로 믿는다 — 그 순간 자동완성이 파편화를 막기는커녕 새 표기를 하나 더 낳는다.

    **경계는 스코프 커널이 주입한다** — 이 질의는 랩을 직접 적지 않는다. 빈 목록은
    정상이다(첫 사람은 후보가 없다).

    순서 = **많이 쓰인 순 → 사전순.** 동수일 때 순서가 흔들리면 같은 글자를 쳤는데
    후보가 매번 달라 보인다.
    """
    if field == "variables":
        # 배열 열이라 펼쳐 센다. `d3_dataset_autometa.variables` 는 `text[]` 다.
        sql = """
            SELECT v AS value, count(*) AS use_count
              FROM d3_dataset_autometa a, unnest(a.variables) AS v
             WHERE (CAST(:prefix AS text) IS NULL OR v ILIKE CAST(:like AS text))
             GROUP BY v
             ORDER BY count(*) DESC, v ASC
             LIMIT :limit
        """
    else:
        table, column = _SUGGEST_SCALAR[field]
        sql = f"""
            SELECT {column} AS value, count(*) AS use_count
              FROM {table}
             WHERE {column} IS NOT NULL AND btrim({column}) <> ''
               AND (CAST(:prefix AS text) IS NULL OR {column} ILIKE CAST(:like AS text))
             GROUP BY {column}
             ORDER BY count(*) DESC, {column} ASC
             LIMIT :limit
        """
    cleaned = (prefix or "").strip() or None
    rows = session.execute(text(sql), {
        "prefix": cleaned,
        # `ILIKE` 특수문자를 글자로 돌린다 — `%` 를 친 사람이 전체를 훑지 않게 한다.
        "like": None if cleaned is None else (
            cleaned.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"),
        "limit": limit,
    }).mappings().all()
    return [{"value": r["value"], "useCount": int(r["use_count"])} for r in rows]


def count_datasets(session: Session) -> int:
    """AI 가 **뒤진 범위**를 먼저 밝히기 위한 셈 (`AiSearchScope.searchedCount`).
    0건이면 그 자체가 「제안할 근거가 없다」의 정직한 형태다."""
    return int(session.execute(
        text("SELECT count(*) FROM d3_dataset WHERE deleted_at IS NULL")).scalar_one())


#: 후보 추출 + 관련도. 세 색인을 각각 `@@` 로 물어 GIN 을 쓰고, 순위는 **이어 붙인 벡터
#: 하나**로 낸다 — 가중치(A=이름 · B=주제·포맷·변수·원천 · C=요약·좌표계·격자)가 그래야
#: 한 눈금 위에 선다. 색인·가중치는 `0005_s1_search_index` 가 정했다 (`〈81〉-㉯`).
#: **여기서 색인을 새로 만들지 않는다.** 벡터 열도, 임베딩도, 유사도도 없다 (`〈81〉`).
#:
#: **접두 질의다** (`PLAN-SoT §9-〈89〉-㉮①`). `ts_config='simple'` 은 형태소를 안 자르므로
#: 「강수」가 「강수량」을 못 잡는다 — `0005` 서두가 스스로 적어 둔 한계이고, 같은 줄이
#: **「접두 질의 `강수:*` 로는 잡힌다」**고도 적었다. 여기가 그 줄을 실행한 자리다.
#:
#: 만드는 법 — 낱말마다 `phraseto_tsquery` 를 태워 `'낙동강' <-> '유역'` 같은 **구 질의**를
#: 얻고, 그 텍스트 끝(=마지막 어휘소)에 `:*` 를 붙여 `tsquery` 로 **캐스팅**한다.
#: 캐스팅이지 `to_tsquery` 재파싱이 아니다 — 재파싱하면 이미 어휘소가 된 글자를 한 번 더
#: 렉싱해 값이 조용히 달라질 수 있다. 사용자 문자열은 `phraseto_tsquery` 의 **파라미터**로만
#: 들어가므로 따옴표 하나에 구문이 깨지지 않는다(`websearch_to_tsquery` 를 쓰던 이유 그대로).
#: 빈 질의(구두점뿐인 낱말)는 `nullif` 로 떨어져 `' | '` 이음에서 빠진다.
#:
#: 조건절에 연구실이 없는 것은 **RLS 가 이미 남의 연구실 행을 지운 뒤**이기 때문이다.
#: 묘비(`deleted_at`)는 카탈로그 목록과 같은 규칙으로 뺀다 — 검색만 죽은 행을 보이면 안 된다.
_PREFIX_TSQUERY = """
  (SELECT string_agg('(' || pfx.e || ')', ' | ')
     FROM (SELECT nullif(phraseto_tsquery('simple', u.t)::text, '') || ':*' AS e
             FROM unnest(cast(:terms AS text[])) AS u(t)) pfx
    WHERE pfx.e IS NOT NULL)::tsquery
"""

_SEARCH = text("""
WITH q AS (
  SELECT """ + _PREFIX_TSQUERY + """ AS tq
)
SELECT d.id AS dataset_id,
       ts_rank_cd(
         coalesce(dd.search_vector, ''::tsvector) ||
         coalesce(am.search_vector, ''::tsvector) ||
         coalesce(d.search_vector,  ''::tsvector), q.tq) AS rank,
       (dd.search_vector @@ q.tq) AS hit_description,
       (am.search_vector @@ q.tq) AS hit_autometa,
       (d.search_vector  @@ q.tq) AS hit_source,
       m.matched AS matched_terms,
       count(*) OVER () AS total_count
  FROM d3_dataset d
  CROSS JOIN q
  LEFT JOIN d3_dataset_description dd ON dd.dataset_id = d.id
  LEFT JOIN d3_dataset_autometa    am ON am.dataset_id = d.id
  LEFT JOIN LATERAL (
    SELECT array_agg(u.t ORDER BY u.ord) AS matched
      FROM unnest(cast(:terms AS text[])) WITH ORDINALITY AS u(t, ord)
     WHERE (coalesce(dd.search_vector, ''::tsvector) ||
            coalesce(am.search_vector, ''::tsvector) ||
            coalesce(d.search_vector,  ''::tsvector))
           @@ (nullif(phraseto_tsquery('simple', u.t)::text, '') || ':*')::tsquery
  ) m ON true
 WHERE d.deleted_at IS NULL
   AND (dd.search_vector @@ q.tq
     OR am.search_vector @@ q.tq
     OR d.search_vector  @@ q.tq)
   AND (cast(:topic AS text) IS NULL OR dd.topic = cast(:topic AS text))
 ORDER BY rank DESC, d.id ASC
 LIMIT :limit OFFSET :offset
""")

#: 어느 색인에서 맞았는가. 근거 한 줄의 「어디에 맞았다」가 되는 말이고,
#: 열 이름이 아니라 **사람이 화면에서 읽는 말**이다.
_WHERE_LABELS = (("hit_description", "이름·주제·요약"),
                 ("hit_autometa", "포맷·변수"),
                 ("hit_source", "원천 표기"))

#: 유사도 문턱 (`〈89〉-㉮②`). `pg_trgm` 의 기본값 0.3 을 **코드에 명시**한다 —
#: `SET pg_trgm.similarity_threshold` 는 세션 설정이라 접속마다 달라질 수 있고,
#: 그러면 같은 질의가 접속에 따라 다른 답을 낸다. 재현성이 세션 설정에 걸리면 안 된다.
TRGM_THRESHOLD = 0.3

#: 근거 한 줄이 읽는 자리 이름. **`tsvector` 로 맞은 것과 다른 말이어야 한다** —
#: 글자가 정확히 맞은 것과 비슷한 것을 같은 문장으로 말하면 근거가 과장이 된다.
_TRGM_WHERE = ("이름(비슷한 말)",)

#: **`tsvector` 가 한 건도 못 잡았을 때만** 도는 보조 팔 (`〈89〉-㉮②`).
#:
#: 두 질의를 나눠 둔 것이 곧 「대체가 아니라 보조」의 실물이다 — `tsvector` 가 한 건이라도
#: 잡으면 이 SQL 은 **실행되지 않으므로**, 기존 질의의 결과 집합도 순위도 유사도 때문에
#: 바뀔 수 없다. 한 질의로 합쳐 `OR` 로 이으면 그 성질이 문장 하나로 사라진다.
#:
#: 순위는 `유사도 DESC, 식별자 ASC` 다. 둘 다 DB 가 낸 결정적 값이라 같은 질의가 같은
#: 순서를 낸다 (`〈89〉-㉮③` — 이 팔이 도는 동안 `tsvector` 순위는 존재하지 않는다).
_SEARCH_TRGM = text("""
SELECT d.id AS dataset_id,
       s.sim AS rank,
       m.matched AS matched_terms,
       count(*) OVER () AS total_count
  FROM d3_dataset d
  JOIN d3_dataset_description dd ON dd.dataset_id = d.id
  LEFT JOIN LATERAL (
    SELECT max(similarity(dd.name, u.t)) AS sim
      FROM unnest(cast(:terms AS text[])) AS u(t)
  ) s ON true
  LEFT JOIN LATERAL (
    SELECT array_agg(u.t ORDER BY u.ord) AS matched
      FROM unnest(cast(:terms AS text[])) WITH ORDINALITY AS u(t, ord)
     WHERE similarity(dd.name, u.t) >= :threshold
  ) m ON true
 WHERE d.deleted_at IS NULL
   AND s.sim >= :threshold
   AND (cast(:topic AS text) IS NULL OR dd.topic = cast(:topic AS text))
 ORDER BY s.sim DESC, d.id ASC
 LIMIT :limit OFFSET :offset
""")


@dataclasses.dataclass(frozen=True)
class SearchMatch:
    """검색 후보 한 건. **관련도는 DB 가 계산한 값 그대로**다.

    `matched_terms` 는 **실제로 맞은 검색어**다 — 안 맞은 말을 근거에 적지 않으려고
    행마다 따로 받는다. `where` 는 맞은 자리다.
    """
    dataset_id: str
    rank: float
    matched_terms: tuple[str, ...]
    where: tuple[str, ...]


def _websearch(terms: tuple[str, ...]) -> bool:
    """뒤질 말이 하나라도 있는가. **없으면 SQL 을 던지지 않는다.**

    ⚠ 이제 **질의 문자열을 만들지 않는다.** 검색어를 문자열로 이어 붙여 넘기던 자리는
    `〈89〉` 의 접두 질의가 가져갔고, 그쪽은 낱말 배열을 그대로 받아 SQL 안에서 잇는다 —
    파이썬이 만든 질의 문자열과 SQL 이 만든 질의 문자열 둘이 공존하면 규칙이 갈라진다.
    """
    return any(t.strip() for t in terms)


def search_datasets(session: Session, *, terms: tuple[str, ...], topic: str | None,
                    limit: int, offset: int) -> tuple[list[SearchMatch], int]:
    """`tsvector` 로 후보를 뽑고 **순위를 낸다** (`〈72〉-㉮` · `〈81〉`).

    **D3 는 core-api 의 자기 도메인이다** — 이 질의는 도메인 경계를 넘지 않는다.
    `K4-a` 는 같은 질의를 D10(ai-service)에서 던졌고 그것이 `CLAUDE.md §3-1` 위반이었다.
    Ted 판정(2026-08-25 ㈎)이 실행을 이쪽으로 옮겼고, **LLM 은 질의 해석까지만** 한다.

    접근 상태(D2)를 **여기서 보지 않는다** — 그래서 잠긴 데이터를 뺄 수 없고, 그것이
    정본이 요구한 성질이다 (`Policy_데이터_찾기 §1.3-6` · `P-13`·`P-34`).
    잠김 **표시**는 조립 루트가 D2 Port 로 붙인다.

    **매칭 규칙이 둘이다** (`〈89〉` — `〈72〉-㉮` 의 개정). ① 검색어는 **접두 질의**로
    던진다 — `ts_config='simple'` 이 형태소를 안 자르는 한계(`〈81〉-㉲`)를 그렇게 넘는다.
    ② 그래도 한 건도 못 잡으면 **이름의 삼중자 유사도**로 한 번 더 본다. **②는 ①이
    실패했을 때만 돈다** — 그래서 ①이 잡은 질의의 결과도 순위도 유사도가 못 바꾼다.

    **여전히 남는 한계** — 「강수량」으로 「강우」를 부르는 것은 매칭의 일이 아니다.
    표기가 다른 같은 말은 사전(D9)이, 상위어의 하위들은 그래프(`K4-b`)가 맡는다.
    """
    if not _websearch(terms):
        return [], 0
    params = {"terms": list(terms), "topic": topic, "limit": limit, "offset": offset}
    rows = session.execute(_SEARCH, params).mappings().all()
    if rows:
        return ([SearchMatch(dataset_id=str(r["dataset_id"]),
                             rank=float(r["rank"]),
                             matched_terms=tuple(r["matched_terms"] or ()),
                             where=tuple(lb for key, lb in _WHERE_LABELS if r[key]))
                 for r in rows],
                int(rows[0]["total_count"]))

    # ── 보조 팔. **여기 오는 것은 `tsvector` 가 0건을 냈다는 뜻이다** ──────────
    # ⚠ `offset > 0` 이어도 상관없다 — 같은 질의의 첫 쪽이 0건이었으면 뒤쪽도 0건이라,
    #    이어보기가 갑자기 다른 규칙의 결과로 갈아타는 일이 생기지 않는다.
    rows = session.execute(_SEARCH_TRGM, {**params,
                                          "threshold": TRGM_THRESHOLD}).mappings().all()
    if not rows:
        return [], 0
    return ([SearchMatch(dataset_id=str(r["dataset_id"]),
                         rank=float(r["rank"]),
                         matched_terms=tuple(r["matched_terms"] or ()),
                         where=_TRGM_WHERE)
             for r in rows],
            int(rows[0]["total_count"]))


def dataset_exists(session: Session, dataset_id: Ulid) -> bool:
    """경계 밖이면 RLS 가 행을 지우므로 여기서 False 가 되고, 호출자는 404 를 낸다 (P-9·P-10)."""
    return session.execute(_EXISTS, {"dataset_id": str(dataset_id)}).first() is not None


def list_files(session: Session, dataset_id: Ulid) -> list[dict]:
    """계약 `DatasetFile`. **축은 기준 격자 파일에만 붙는다** (`K-3` · `〈80〉-㉯ 3`).

    본체에 `gridAxis` 자리를 만들면 없는 사실을 있는 척하게 된다 — `0004` 의 CHECK 가
    축 붙은 본체를 애초에 만들지 않으므로, 그 사실을 응답 모양이 그대로 비춘다.
    """
    rows = session.execute(_FILES, {"dataset_id": str(dataset_id)}).mappings().all()
    out: list[dict] = []
    for r in rows:
        item = {"fileId": r["id"], "fileName": r["file_name"], "kind": r["kind"]}
        if r["kind"] == GRID_KIND:
            item["gridAxis"] = {"carriesLat": bool(r["carries_lat"]),
                                "carriesLon": bool(r["carries_lon"])}
        out.append(item)
    return out


# ════════════════════════════════════════════════════════════════════════════
# 쓰기 — 등록 전환 · 파일 후주입/교체/삭제 · 계보 확인 기록
#
# **`createDataset` 은 「새로 만들기」가 아니라 「등록 전환」이다** (계약 산문 · `Policy §7.2`).
# 업로드 세계의 `fileId` ULID 가 `d3_file.id` 로 **그대로** 온다 — 새로 만들지 않는다
# (`NB-A` 동일성, Ted 승인 2026-08-23). `d5_upload_file.id → d3_file.id` 에 FK 가 없으므로
# (불변규칙 1 이 금지한다) 이 동일성을 지키는 것은 **여기 코드와 그 시험뿐**이다.
# ════════════════════════════════════════════════════════════════════════════

_INSERT_DATASET = text("""
    INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id, source_label)
    VALUES (:id, current_lab_id(), :owner, :uploader, :source_label)
    RETURNING id
""")

_INSERT_DESCRIPTION = text("""
    INSERT INTO d3_dataset_description (dataset_id, lab_id, name, topic, summary)
    VALUES (:dataset_id, current_lab_id(), :name, :topic, :summary)
""")

# 자동으로 읽은 정보의 **자리**를 함께 세운다. 값은 파일에서 나오고 그 읽기는
# pipeline-worker 의 일이라(`P2.md §2-14`), 접수 단계에서 아는 것 말고는 **비워 둔다.**
# 비워 두는 것과 지어내는 것은 다르다.
_INSERT_AUTOMETA = text("""
    INSERT INTO d3_dataset_autometa (dataset_id, lab_id, format, bundle_file_name,
                                     total_size_bytes)
    VALUES (:dataset_id, current_lab_id(), :format, :bundle_file_name, :total_size_bytes)
""")

_INSERT_FILE = text("""
    INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, size_bytes, storage_key,
                         carries_lat, carries_lon)
    VALUES (:id, current_lab_id(), :dataset_id, :kind, :file_name, :size_bytes, :storage_key,
            :carries_lat, :carries_lon)
    RETURNING id
""")

_FIND_FILE = text("""
    SELECT id, dataset_id, kind, file_name, size_bytes, storage_key, carries_lat, carries_lon
      FROM d3_file
     WHERE id = :file_id AND dataset_id = :dataset_id
""")

_DELETE_FILE = text("DELETE FROM d3_file WHERE id = :file_id RETURNING id")

_GRID_FILES = text("""
    SELECT id, dataset_id, kind, file_name, size_bytes, storage_key, carries_lat, carries_lon
      FROM d3_file
     WHERE dataset_id = :dataset_id AND kind = '기준 격자 파일'
     ORDER BY id
""")

# 축 뒤집기 (`K-3`) — **두 문장이다. 한 문장으로는 안 된다.**
#
# ⚠ `0004:192-195` 의 유일성은 **부분 유니크 인덱스**이고, 인덱스는 `DEFERRABLE` 이 될 수 없다.
#    한 `UPDATE` 가 두 행을 훑어도 검사는 **행마다 즉시** 일어나므로, A 를 경도로 바꾸는 순간
#    아직 경도인 B 와 부딪힌다. 「한 문장이면 원자적이라 괜찮다」는 **틀렸다** —
#    재 보고 알았다(`UniqueViolation: d3_file_one_lon_grid_per_dataset`).
#
# 그래서 **인덱스 술어 밖으로 잠시 뺐다가 되돌린다.** 술어가 `kind = '기준 격자 파일' AND …` 이라
# `kind` 를 본체로 두면 두 행이 두 인덱스 어디에도 안 걸린다 — 그리고 그 상태는
# CHECK ㈏(본체는 축이 없다)를 지키므로 **합법이다.** 트랜잭션 밖에서는 보이지 않는다.
#
# **기각한 대안 = 지웠다 다시 넣기.** `created_at` 이 밀린다 — 그것은 「이 파일 행이 언제
# 생겼는가」라는 **사실**이고, 축을 바로잡았다고 그 사실이 바뀌지 않는다.
# **마이그레이션(제약을 DEFERRABLE 로)도 기각** — `〈70〉-㉱`·`〈79〉` 의 「`0004` 무수정」을 깬다.
_PARK_GRID_AXES = text("""
    UPDATE d3_file
       SET kind = '본체', carries_lat = false, carries_lon = false
     WHERE dataset_id = :dataset_id AND kind = '기준 격자 파일'
""")

_RESTORE_GRID_AXIS = text("""
    UPDATE d3_file
       SET kind = '기준 격자 파일', carries_lat = :carries_lat, carries_lon = :carries_lon
     WHERE id = :file_id
""")

_UPDATE_FILE = text("""
    UPDATE d3_file
       SET file_name = :file_name, size_bytes = :size_bytes, storage_key = :storage_key
     WHERE id = :file_id
     RETURNING id, dataset_id, kind, file_name, size_bytes, storage_key,
               carries_lat, carries_lon
""")

# `〈60〉-②` — 좌표계·격자는 **그 파일에서 나오는 값**이라 격자 파일이 바뀌면 재계산한다.
# core-api 는 파일을 읽지 못하므로(`CLAUDE.md §3-4`) **재계산의 결과로 「모른다」를 쓴다** —
# 낡은 값을 그대로 두면 지워진 파일에서 읽은 값이 화면에 남는다. 새 값은 파일을 읽는 쪽이 채운다.
_CLEAR_GRID_META = text("""
    UPDATE d3_dataset_autometa SET crs = NULL, grid = NULL, updated_at = now()
     WHERE dataset_id = :dataset_id
""")

# **`마지막 수정` 을 건드리지 않는다** (`〈60〉-①`) — 그 열을 밀면 파생인 `계보 상태` 가
# `확정` 에서 `확인 필요` 로 접히고, 사람이 확인하러 갔다가 아무것도 안 바뀐 걸 본다.
_CONFIRM_LINEAGE = text("""
    UPDATE d3_dataset SET lineage_confirmed_at = now()
     WHERE id = :dataset_id AND deleted_at IS NULL
     RETURNING id
""")


@dataclasses.dataclass(frozen=True)
class FileRow:
    file_id: str
    dataset_id: str
    kind: str
    file_name: str
    size_bytes: int | None
    storage_key: str
    carries_lat: bool
    carries_lon: bool


def _file_row(r) -> FileRow:
    return FileRow(
        file_id=r["id"], dataset_id=r["dataset_id"], kind=r["kind"],
        file_name=r["file_name"],
        size_bytes=(None if r["size_bytes"] is None else int(r["size_bytes"])),
        storage_key=r["storage_key"],
        carries_lat=bool(r["carries_lat"]), carries_lon=bool(r["carries_lon"]),
    )


def register_dataset(session: Session, *, dataset_id: Ulid, owner_id: Ulid,
                     uploader_id: Ulid, name: str, topic: str | None,
                     summary: str | None, source_label: str | None,
                     detected_format: str | None, bundle_file_name: str | None,
                     total_size_bytes: int | None) -> str:
    """D3 세 표를 한 트랜잭션에서 세운다.

    **반쪽이 남지 않는다** — 요청 하나 = 트랜잭션 하나이고(`app/deps.scoped_db`),
    뒤에 오는 파일·계보·프로젝트 삽입이 하나라도 실패하면 이 행까지 통째로 rollback 된다
    (음성 시험 ㉰ 등록 원자성).
    """
    new_id = session.execute(_INSERT_DATASET, {
        "id": str(dataset_id), "owner": str(owner_id), "uploader": str(uploader_id),
        "source_label": source_label,
    }).scalar_one()
    session.execute(_INSERT_DESCRIPTION, {
        "dataset_id": str(dataset_id), "name": name, "topic": topic, "summary": summary,
    })
    session.execute(_INSERT_AUTOMETA, {
        "dataset_id": str(dataset_id), "format": detected_format,
        "bundle_file_name": bundle_file_name, "total_size_bytes": total_size_bytes,
    })
    return new_id


#: **생략과 `null` 을 가르는 표식.** `None` 은 「비워라」라는 **값**이라 「안 보냈다」를
#: 표현할 수 없다. 이 둘을 접으면 「요약만 고치려다 Lv 가 날아가는」 일이 생긴다.
UNSET = object()


#: 이 op 이 고칠 수 있는 칸 ↔ 그 값이 사는 표. **계약(`DatasetUpdate`)이 정본이고**
#: 여기는 그것을 SQL 자리로 옮긴 표일 뿐이다.
_UPDATABLE = {
    "name": ("d3_dataset_description", "name"),
    "topic": ("d3_dataset_description", "topic"),
    "summary": ("d3_dataset_description", "summary"),
    "sourceLabel": ("d3_dataset", "source_label"),
    "processingLevel": ("d3_dataset", "processing_level_user_set"),
    "representativeFileId": ("d3_dataset", "representative_file_id"),
    "variables": ("d3_dataset_autometa", "variables"),
    "crs": ("d3_dataset_autometa", "crs"),
}


def update_dataset(session: Session, *, dataset_id: Ulid, changes: dict) -> None:
    """**부분 수정.** `changes` 에 있는 열쇠만 건드린다 (`〈127〉`·`〈138〉`·`〈140〉`).

    `UNSET` 이 아닌 값만 온다고 가정한다 — 라우트가 이미 걸러 냈다.

    **표를 나눠 UPDATE 한다.** 이름·주제·요약은 `d3_dataset_description`, 원천 표기·
    가공 단계·대표 조각은 `d3_dataset`, 변수·좌표계·기간은 `d3_dataset_autometa` 다.
    한 표에 몰려 있지 않은 것은 **자동으로 읽은 값과 사람이 적은 값을 갈라 둔** 설계
    때문이고(`정본 §4.1`), `〈138〉` 로 그 경계가 옮겨졌어도 **표는 그대로 둔다** —
    표를 옮기는 것은 마이그레이션이고 얻는 것이 없다.
    """
    by_table: dict[str, dict[str, object]] = {}
    for key, value in changes.items():
        table, column = _UPDATABLE[key]
        by_table.setdefault(table, {})[column] = value

    # 기간은 두 열로 갈라진다 — 계약은 한 덩어리(`DataPeriod`)로 받는다.
    if "period" in changes:
        period = changes["period"]
        target = by_table.setdefault("d3_dataset_autometa", {})
        target["period_start"] = None if period is None else period.get("start")
        target["period_end"] = None if period is None else period.get("end")

    for table, columns in by_table.items():
        assignments = ", ".join(f"{c} = :{c}" for c in columns)
        key_column = "id" if table == "d3_dataset" else "dataset_id"
        session.execute(
            text(f"UPDATE {table} SET {assignments} WHERE {key_column} = :dataset_id"),
            {**columns, "dataset_id": str(dataset_id)})

    # **마지막 수정 시각은 언제나 움직인다.** 계보 상태 판정이 이 값을 본다
    # (`DATAMODEL-BASELINE §3-③` — 「마지막 수정 > 계보 확정일」이면 `확인 필요`).
    # 빈 요청이어도 갱신하지 않는다 — 아무것도 안 고쳤으면 고친 것이 아니다.
    if by_table:
        session.execute(
            text("UPDATE d3_dataset SET last_modified_at = now() WHERE id = :dataset_id"),
            {"dataset_id": str(dataset_id)})


def file_belongs_to(session: Session, *, file_id: str, dataset_id: Ulid) -> bool:
    """대표 조각이 **이 데이터셋의 조각인가.**

    FK 는 이것을 못 막는다 — `d3_file` 은 한 표라서 다른 데이터셋의 조각을 가리켜도
    참조 무결성은 만족한다. **막는 것은 여기뿐이다.**
    """
    return session.execute(
        text("SELECT 1 FROM d3_file WHERE id = :file_id AND dataset_id = :dataset_id"),
        {"file_id": file_id, "dataset_id": str(dataset_id)}).first() is not None


def insert_file(session: Session, *, file_id: str, dataset_id: Ulid, kind: str,
                file_name: str, size_bytes: int | None, storage_key: str,
                carries_lat: bool, carries_lon: bool) -> str:
    """**`file_id` 를 여기서 만들지 않는다** — 부르는 쪽이 업로드가 발급한 값을 넘긴다.

    이 함수가 ULID 를 새로 뽑는 순간 `NB-A` 동일성이 조용히 깨진다. FK 가 없어
    DB 는 아무 말도 하지 않는다 — 그래서 인자로만 받는다.
    """
    if not Ulid.is_valid(file_id):
        raise ValueError(f"파일 ID 가 정규 ID 가 아니다: {file_id!r}")
    return session.execute(_INSERT_FILE, {
        "id": file_id, "dataset_id": str(dataset_id), "kind": kind,
        "file_name": file_name, "size_bytes": size_bytes, "storage_key": storage_key,
        "carries_lat": carries_lat, "carries_lon": carries_lon,
    }).scalar_one()


def find_file(session: Session, *, dataset_id: Ulid, file_id: Ulid) -> FileRow | None:
    r = session.execute(_FIND_FILE, {
        "file_id": str(file_id), "dataset_id": str(dataset_id)}).mappings().first()
    return None if r is None else _file_row(r)


def replace_file(session: Session, *, file_id: Ulid, file_name: str,
                 size_bytes: int | None, storage_key: str) -> FileRow:
    """교체는 **행을 갈아 끼우지 않고 같은 행의 본체를 바꾼다** — `fileId` 가 유지돼야
    계보·활동 기록이 같은 대상을 가리킨다. 축(`carries_*`)은 건드리지 않는다: 새 파일의
    축은 파일을 읽는 쪽이 다시 정한다."""
    r = session.execute(_UPDATE_FILE, {
        "file_id": str(file_id), "file_name": file_name, "size_bytes": size_bytes,
        "storage_key": storage_key,
    }).mappings().one()
    return _file_row(r)


def grid_files(session: Session, dataset_id: Ulid) -> list[FileRow]:
    """그 데이터셋의 기준 격자 파일 전건. **0~2건**이다 (`〈58〉` · `common.json FileKind`)."""
    rows = session.execute(_GRID_FILES, {"dataset_id": str(dataset_id)}).mappings().all()
    return [_file_row(r) for r in rows]


def swap_grid_axes(session: Session, dataset_id: Ulid) -> None:
    """축 뒤집기 (`K-3` · `〈80〉-㉯ 3`) — 그 데이터셋의 두 격자 파일의 축 배정을 맞바꾼다.

    **파일은 건드리지 않는다** — 이름·크기·저장 키·`created_at` 이 그대로여야
    「파일을 다시 올리지 않는다」가 참이다. 뒤집기는 **잘못 붙인 격자를 바로잡는 정상 동작**이지
    새 데이터가 아니다 (`〈59〉`).

    절차는 위 `_PARK_GRID_AXES` 주석이 「왜 두 문장인가」를 적었다.
    """
    before = grid_files(session, dataset_id)
    session.execute(_PARK_GRID_AXES, {"dataset_id": str(dataset_id)})
    for row in before:
        # 뒤집기 = 두 축을 맞바꾸는 것. 결합축(둘 다 true)은 바꿔도 같은 값이라 무해하다 —
        # 그 경우는 애초에 짝이 아니어서 호출자가 409 로 막는다.
        session.execute(_RESTORE_GRID_AXIS, {
            "file_id": row.file_id,
            "carries_lat": row.carries_lon, "carries_lon": row.carries_lat,
        })


def delete_file(session: Session, file_id: Ulid) -> bool:
    return session.execute(_DELETE_FILE, {"file_id": str(file_id)}).first() is not None


def recompute_grid_metadata(session: Session, dataset_id: Ulid) -> None:
    """`〈60〉-②` 재계산. 위 `_CLEAR_GRID_META` 주석이 「왜 NULL 인가」를 적었다."""
    session.execute(_CLEAR_GRID_META, {"dataset_id": str(dataset_id)})


def confirm_lineage(session: Session, dataset_id: Ulid) -> bool:
    return session.execute(_CONFIRM_LINEAGE, {"dataset_id": str(dataset_id)}).first() is not None


def processing_level(summary: LineageSummary | None,
                     user_set: int | None = None) -> int:
    """원자료 Lv0 · 주입력 부모의 최대 + 1, **상한 `LV_CAP`** (E-00 · common.json#/$defs/ProcessingLevel).

    상한은 정본이 준 값이다 — `POL-020` 「연결된 가공 전 데이터 중 가장 높은 Lv + 1,
    **상한 Lv2**」 · `VAL-005`. 자르지 않으면 정본이 **「존재할 수 없는 값」**이라고 한
    `Lv3` 이 나오고, 카탈로그 필터가 아무 화면도 그릴 수 없는 칸을 열게 된다.

    **자르는 것이지 막는 것이 아니다.** 깊은 사슬은 합법이고(`POL-020` 은 금지하지
    않는다) Lv 은 깊이가 아니라 종류이므로(`Lv2 = 집계·분석용`) 접어도 잃는 것이
    없다 — 깊이는 계보 그래프에 그대로 남는다.
    """
    # **사람이 고른 값이 먼저다** — `POL-020` 의 예외이자 `TC-W-001` 이 요구하는 그대로다.
    # 「Lv1 로 직접 선택 → Lv1 부모를 연결 → 보정하지 않음(사람이 정한 값 유지)」.
    if user_set is not None:
        return min(max(int(user_set), 0), LV_CAP)
    if summary is None or summary.max_primary_parent_level is None:
        return 0
    return min(summary.max_primary_parent_level + 1, LV_CAP)


def lineage_state(core: DatasetCore, summary: LineageSummary | None) -> str:
    """계보 상태 4값을 계산한다. 저장 컬럼이 없는 것이 이 계산의 강제다 (DATAMODEL-BASELINE §3-③).

    판정 순서 —
      1) 부모가 있고 `마지막 수정 > 계보 확정일`(또는 확정일 없음) → `확인 필요`
         (DATAMODEL-BASELINE §3-③ 이 못 박은 유일한 판정식)
      2) 부모가 있고 확정일이 최신 → `확정`
      3) 부모가 없고 원천 표기가 있다 → `원천`
      4) 그 밖 → `기록 없음`
    """
    if summary is not None and summary.parent_count > 0:
        confirmed = core.lineage_confirmed_at
        if confirmed is None or core.last_modified_at > confirmed:
            return "확인 필요"
        return "확정"
    if core.source_label:
        return "원천"
    return "기록 없음"
