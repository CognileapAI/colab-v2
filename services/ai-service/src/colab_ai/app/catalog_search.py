"""`tsvector` 질의 실행기 — `ports.CatalogSearchPort` 의 구현. **조립 루트에 둔다.**

무엇을 뒤지는가
  `0005_s1_search_index` 가 세운 **생성 열 3 + GIN 3** 이 전부다 (`〈81〉-㉯`).
  가중치도 그 마이그레이션이 정했다 — A=이름 · B=주제·포맷·변수·원천 · C=요약·좌표계·격자·묶음.
  **여기서 색인을 새로 만들지 않는다.** 벡터 열도, 임베딩도, 유사도도 없다 (`〈81〉`).

왜 이 단위가 카탈로그를 직접 읽는가
  계약(`core-ai.yaml searchDatasets`)이 **AI 가 식별자·관련도·근거를 돌려준다**고 못 박았고,
  `〈72〉-㉮` 가 **매칭·순위를 `tsvector` 에** 맡겼다. 두 결정이 만나면 질의를 실제로 던지는
  쪽은 이 단위다. 그래서 지키는 선을 좁게 긋는다 —
    · **읽기 전용 트랜잭션**으로만 연다 (`kernel/db.py`). 쓰기는 Postgres 가 거절한다.
    · **D3 의 검색 열만** 본다. 접근 상태(D2)도, 계보(D4)도 읽지 않는다 —
      그래서 **잠긴 데이터를 뺄 수 없고**, 그것이 정본이 요구한 성질이다 (`§1.3-6`).
    · 사본을 만들지 않는다. 색인은 D3 열 옆에 그대로 있고 이 단위는 질의만 던진다.

왜 `websearch_to_tsquery` 인가
  검색어를 문자열로 이어 붙여 `to_tsquery` 에 넣으면 따옴표 하나에 구문이 깨진다.
  `websearch_to_tsquery` 는 **파라미터로 넘긴 사용자 문자열**을 안전하게 읽고, 큰따옴표로
  묶은 여러 낱말을 구(phrase)로 다룬다 — 「낙동강 유역」처럼 공백이 든 별칭이 그대로 산다.

**한계를 여기 적어 둔다** (`〈81〉-㉲`)
  `ts_config` 가 `'simple'` 이라 형태소를 자르지 않는다. 「강수량」은 한 낱말이고
  **「강수」로는 안 잡힌다.** 접두 질의(`강수:*`)나 `pg_trgm` 은 **매칭 규칙을 바꾸는 일**이라
  `〈72〉` 가 고정한 자리를 이 레인이 혼자 옮기지 않는다 — 필요하면 멈추고 보고한다.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

from colab_ai.kernel.db import make_session_factory, read_only_scope
from colab_ai.ports import MatchRow

#: 뒤진 범위. **RLS 가 이미 남의 연구실 행을 지운 뒤**라서 조건절이 없다.
COUNT_SQL = text("SELECT count(*) FROM d3_dataset")

#: 후보 추출 + 관련도. 세 색인을 각각 `@@` 로 물어 GIN 을 쓰고, 순위는 **이어 붙인
#: 벡터 하나**로 낸다 — 가중치(A/B/C)가 그래야 한 눈금 위에 선다.
MATCH_SQL = text("""
WITH q AS (
  SELECT websearch_to_tsquery('simple', :websearch) AS tq
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
           @@ websearch_to_tsquery('simple', '"' || replace(u.t, '"', '') || '"')
  ) m ON true
 WHERE (dd.search_vector @@ q.tq
     OR am.search_vector @@ q.tq
     OR d.search_vector  @@ q.tq)
   AND (cast(:topic AS text) IS NULL OR dd.topic = cast(:topic AS text))
 ORDER BY rank DESC, d.id ASC
 LIMIT :limit OFFSET :offset
""")


def _websearch(terms: tuple[str, ...]) -> str:
    """검색어를 **OR** 로 잇는다. 하나만 맞아도 후보다 — 좁히는 일은 순위가 한다."""
    return " or ".join('"' + t.replace('"', " ").strip() + '"' for t in terms if t.strip())


class SqlCatalogSearch:
    """`CatalogSearchPort`. **쓰기 메서드가 없다.**"""

    def __init__(self, engine: Engine) -> None:
        self._factory = make_session_factory(engine)

    def session(self, *, lab_id: str, account_id: str):
        """경계가 심긴 읽기 전용 세션. 시험이 이 성질을 직접 확인한다."""
        return read_only_scope(self._factory, lab_id=lab_id, account_id=account_id)

    def count_datasets(self, *, lab_id: str, account_id: str) -> int:
        with self.session(lab_id=lab_id, account_id=account_id) as session:
            return int(session.execute(COUNT_SQL).scalar_one())

    def match(self, *, lab_id: str, account_id: str, terms: tuple[str, ...],
              topic: str | None, limit: int, offset: int) -> tuple[list[MatchRow], int]:
        websearch = _websearch(terms)
        if not websearch:
            return [], 0
        with self.session(lab_id=lab_id, account_id=account_id) as session:
            rows = session.execute(MATCH_SQL, {
                "websearch": websearch, "terms": list(terms),
                "topic": topic, "limit": limit, "offset": offset,
            }).mappings().all()
        total = int(rows[0]["total_count"]) if rows else 0
        out = [
            MatchRow(
                dataset_id=str(r["dataset_id"]),
                rank=float(r["rank"]),
                matched_terms=tuple(r["matched_terms"] or ()),
                where=tuple(label for flag, label in (
                    (r["hit_description"], "이름·주제·요약"),
                    (r["hit_autometa"], "포맷·변수"),
                    (r["hit_source"], "원천 표기"),
                ) if flag),
            )
            for r in rows
        ]
        return out, total
