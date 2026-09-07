# 레인 `rc-lv-unify` — WU-C9 · Lv 표시 사람 값 우선 통일 (2026-09-08)

기반 = `integration/r-c` `2f91592`(WU-C10 done). 브랜치 `lane/wu-c9`. push 안 함. 계약 개정 **0** · 마이그레이션 **0**.

## C10 이 이미 해 둔 것 (재확인)

- 계보 노드(`routes/lineage.py`)·`ProjectDatasetRow`(`routes/project.py`) 가 `processingLevelUserSet` 을 **이미 싣고 있었다** · `processingLevel` 은 파생값 그대로(㉮ 유지).
- ai-service `d10_suggestion.Suggestion.parent_processing_level` ＋ `to_dict()` 도 이미 있다 — **부모 제안을 만드는 생산자는 아직 없다**(제안은 degraded 0건). ⇒ ai-service **무접촉**.
- 카탈로그·상세는 R-B 부터 서버가 `level_view` 로 표시용 `processingLevel` 을 사람 값 우선으로 채운다(계약 산문 축자). 여기는 손대지 않았다.

## 이 레인이 한 것

- 서버 조립 **한 자리** — `d3_catalog.level_pair(core, summary)` 신설(파생값 ＋ 사람 값을 나란히). 계보 노드·프로젝트 표가 각자 자르던 두 벌을 이 함수로 모았다. **표시 규칙은 고르지 않는다**(FE 몫).
- FE 표시 규칙 **한 자리** — `frontend/src/components/common/processingLevel.ts` (`displayLevel` ＋ `levelOf`·`LV_VALUES` 이사). `lineage/types.ts` 는 그대로 재수출해 종전 수입 경로를 끊지 않았다.
- 네 자리가 그 함수를 부른다 — 카탈로그(`CatalogTable`) · 상세(`DetailHeader`) · 계보 그래프 노드(`LineageSection` 3자리 ＋ `selfLv` 퇴행) · 프로젝트 표(`ProjectDatasetTable`). 후보 줄(`ParentPicker`)·등록 ③ 카드도 같은 함수로 통일.
- 등록 ③ 충돌 판정 — 제안 카드가 `s.parentProcessingLevel ?? null` 을 쥔다. 실려 오면 **서버 400 전에** `확인 필요` ＋ 충돌 안내가 뜨고, 열쇠가 없으면 종전대로 조용하다(판정 정본은 서버 400).

## 시험 — RED 선실측 → GREEN

- `frontend/test/lv-display-unify-20260908.test.tsx` 신설 4건.
  - 4자리 통일: 되돌린 상태에서 `['Lv3','Lv3','Lv1','Lv1']` **red** → 고친 뒤 `['Lv3','Lv3','Lv3','Lv3']`(자리 수 4를 먼저 센다).
  - 제안 `parentProcessingLevel` 있음 → `lin-need-check` ＋ `lin-conflict-note`(되돌리면 red).
  - 열쇠 없음 → 카드 1장은 그대로 서고 경고 0건(깨지지 않는다).
- `services/core-api/tests/test_lineage_graph_read.py` +2 — 두 라우트가 `level_pair` 를 쓰고 사람 Lv 를 직접 싣지 않는다 · `level_pair` 가 파생 열쇠를 덮어 쓰지 않는다.

## 못 잰 축

- ai-service 부모 제안 생산자가 없어 `parentProcessingLevel` 의 **실서버 왕복**은 `[미측정]` — 계약형·화면형만 잰다.
