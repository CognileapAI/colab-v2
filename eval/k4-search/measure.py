"""K4 검색 실측 하네스 — **말이 아니라 `SELECT` 로 판정한다.**

`sessions/K1b-ONTOLOGY-CONTENT §D` 의 질의 예시들은 **지면 대조**였다(그 절이 스스로
`[미확인]` 이라 적었다). 이 파일은 그 대조를 실물로 바꾼다 — 실제 두 DB, 실제 확장 규칙,
실제 실행기다. `DATA-REFERENCE §0 M-4`(측정 안 한 것을 측정된 것처럼 인용하기)가 금지한
자리가 정확히 여기였다.

**제품 코드가 아니다.** 배포 단위 둘을 한 프로세스에서 부르는 것은 측정을 위해서이고,
그래서 `services/` 밖에 산다. 제품에서 두 단위는 HTTP 로만 만난다 — 그리고 core-api 는
AI 체인에 **붙지 않는다**(`PLAN-SoT §9-〈90〉-㉮`). 이 파일도 그 성질을 지킨다:
그래프는 `colab_ai` 만 읽고, `colab_core` 에는 **말**만 넘어간다.

쓰는 법
  python3 eval/k4-search/measure.py <platform-app-url> <ai-app-url>
"""
from __future__ import annotations

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "services" / "ai-service" / "src"))
sys.path.insert(0, str(REPO / "services" / "core-api" / "src"))

from colab_ai.app.dictionaries import SqlDictionaries          # noqa: E402
from colab_ai.app.interpret import LiteralInterpreter          # noqa: E402
from colab_ai.kernel.db import make_engine as ai_engine        # noqa: E402
from colab_core.domains import d3_catalog                      # noqa: E402
from colab_core.kernel.auth import Subject                     # noqa: E402
from colab_core.kernel.db import make_engine, make_session_factory  # noqa: E402
from colab_core.kernel.ids import Ulid                         # noqa: E402
from colab_core.kernel.scope import read_only_scope            # noqa: E402

LAB = "0000000000000000000000000K"
ACCOUNT = "00000000000000000000000KP1"

#: `SEED-DATA §3.1` 의 줄 번호. 화면에 ULID 를 찍으면 사람이 못 읽는다.
LABEL = {f"{'0' * (26 - len(f'D{i}'))}D{i}": f"D-{i:02d}" for i in range(1, 16)}

QUERIES = (
    ("재격자화한 NDVI 자료", "§D-2 — 그래프가 사는 가장 큰 자리. D-03·D-04·D-05 셋이다"),
    ("전처리한 강우 자료", "§D-6 첫 과확장 — 금지 목록이라 확장이 시작되지 않는다"),
    ("Bilinear 로 만든 자료", "§D-6 둘째 과확장 — 하향 전용이 형제 둘을 막는다"),
    ("한국수자원학회 학회 발표에 쓴 다운스케일 자료", "§D-4 — E5-8 + E1-11"),
    ("한반도 전체 식생 자료", "§D-5 — 집합이 아니라 순위가 바뀐다"),
    ("25년도 낙동강 유역 강우 데이터 찾아줘", "§D-1 — 0건이 정답이다. 그래프가 0건을 없애지 않는다"),
    ("천리안위성2A호 자료", "§D-3 — E1-9·E1-8"),
    ("강수", "〈89〉 — 접두 질의가 「강수」로 「강수」를 담은 이름을 잡는가"),
    ("강수량", "〈89〉 한계 — 질의가 더 길면 접두로도 안 된다. pg_trgm 이 받는 자리"),
)


def _run(factory, terms, topic=None):
    with read_only_scope(factory, Subject(account_id=Ulid(ACCOUNT), lab_id=Ulid(LAB))) as s:
        rows, total = d3_catalog.search_datasets(s, terms=tuple(terms), topic=topic,
                                                 limit=20, offset=0)
    return [LABEL.get(r.dataset_id, r.dataset_id) for r in rows], total


def main() -> int:
    platform_url, ai_url = sys.argv[1], sys.argv[2]
    factory = make_session_factory(make_engine(platform_url))
    dicts = SqlDictionaries(ai_engine(ai_url))
    interpreter = LiteralInterpreter()

    for query, note in QUERIES:
        base = interpreter.interpret(query)
        expansion = dicts.expand(base.terms, query)
        graph_terms = tuple(h.term for h in expansion.graph_hops)
        without = tuple(t for t in expansion.terms if t not in set(graph_terms))

        before_ids, before_total = _run(factory, without)
        after_ids, after_total = _run(factory, expansion.terms, expansion.topic)

        print(f"\n■ {query}\n  ({note})")
        print(f"  그래프가 붙인 말 : {', '.join(graph_terms) or '없음'}")
        for h in expansion.graph_hops:
            print(f"      ↳ ‘{h.parent}’ —{h.relation}→ ‘{h.term}’")
        print(f"  그래프 없이      : {before_total}건  {before_ids}")
        print(f"  그래프 있음      : {after_total}건  {after_ids}")
        gained = [d for d in after_ids if d not in before_ids]
        print(f"  그래프가 더한 것 : {gained or '없음'}   상위 3 = {after_ids[:3]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
