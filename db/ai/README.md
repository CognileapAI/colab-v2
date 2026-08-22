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
