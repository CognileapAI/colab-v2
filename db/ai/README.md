# db/ai — 지식·추론 스키마 (D9 D10)

마이그레이션 head가 `db/platform` 과 **분리된다**.

여기에는 온톨로지·그래프와 **AI 제안 임시 저장소**가 산다.
제안은 여기서 태어나 여기서 죽고, 사람이 확인한 것만 플랫폼(D4)으로 넘어간다.

## 온톨로지 시드 (WU-K2)

| 경로 | 무엇 |
|---|---|
| `seed/k2-coverage-standard.tsv` | **완료 오라클의 기준.** 정본 인용 13 + 주제 4 + 지명 4 = 21항목, 항목마다 정본 출현 위치 |
| `seed/k2_ontology_seed.sql` | **적재물.** 멱등(`ON CONFLICT … DO UPDATE`) — 두 번 돌려도 사전이 두 벌이 되지 않는다 |
| `versions/0003_k2_ontology_seed.py` | 위 SQL 을 실행하는 리비전. 시드는 **모든 환경에 있어야 하므로 체인 안**에 있다 |
| `tools/k2-coverage-check.sh` | 기준 ↔ 적재 대조. 미커버 1건이라도 있으면 red. DB 를 못 붙어도 red(skip 없음) |

```bash
COLAB_AI_DB_CONTAINER=<컨테이너> COLAB_AI_DB_NAME=<db> db/ai/tools/k2-coverage-check.sh
COLAB_AI_DB_URL=postgresql://…                      db/ai/tools/k2-coverage-check.sh
```

기준과 적재물은 **일부러 두 파일이다.** 기준을 적재물에서 생성하면 체크가 영원히 green 인 자동통과가 된다.

## 개념 그래프 (WU-K1b · K2b)

내용 정본 = `dev-package/sessions/K1b-ONTOLOGY-CONTENT.md` · 판정 = Ted 2026-08-25 (`PLAN-SoT §9-〈86〉`).
**위 세 표를 흡수하지 않는다** (F-13 ㈎) — 세 표는 `질의어 → 값` 조회(사전)이고, 두 표는 `질의어 → term set` 확장(그래프)이다.

| 경로 | 무엇 |
|---|---|
| `versions/0004_k1b_concept_graph.py` | `d9_concept`(노드) · `d9_concept_edge`(엣지) DDL. 선언 정본은 `schema.sql §4·§5` |
| `seed/k2b_concept_graph_seed.sql` | **적재물.** 노드 49 · 엣지 19. 멱등 |
| `versions/0005_k2b_concept_graph_seed.py` | 위 SQL 을 실행하는 리비전 |
| `seed/k2b-graph-standard.tsv` | **완료 오라클의 기준.** 노드·엣지 전 행 + 근거 |
| `tools/k2b_graph_check.py` · `k2b-graph-check.sh` | 기준 ↔ 적재 **완전일치** 판정. 특히 `source_grade=6` 행이 Ted 승인 목록과 일치하는지 본다 |
| `tools/k2b-graph-selftest.sh` | **판정기가 red 를 낼 수 있다는 증명** — 16 케이스. DB 없이 돈다 |
| `tests/0004-0005-drift.sh` | 되돌리면 오라클이 red 를 낸다 + `schema.sql` = 마이그레이션 결과. docker + alembic 필요 |

```bash
COLAB_AI_DB_CONTAINER=<컨테이너> db/ai/tools/k2b-graph-check.sh
bash db/ai/tools/k2b-graph-selftest.sh            # DB 불필요
COLAB_ALEMBIC=<alembic> bash db/ai/tests/0004-0005-drift.sh
```

**확장 경계 넷**(과확장 방지 — `K1b-ONTOLOGY-CONTENT §D-6` · Ted F-11): 하향 전용 · 깊이 1 ·
팬아웃 상한 6 · 부모 금지 목록(`전처리`·`품질검사`·`유역 집계` = `expandable=false`).
앞의 둘은 소비자(`K4-b`)가 지키고, 뒤의 둘은 이 표와 오라클이 데이터로 강제한다.
