# Gate ② — WU-B10 (lane p3-lineage-fix · 1ae8c37 vs 652712e)

For:
- 반복 금지 요구(PRD-31 「등록 ③ 과 같은 찾기·연결 UI」)가 diff 로 증명된다 — `LineageStep.tsx` 에서 `picker()` 본문 51행 삭제·`<ParentPicker/>` 11행, `overReason` 삭제 후 `parentOverReason` import. 사본 0.
- 새 op 0 · 계약/서버/DB 0 · `addLineageParent` 응답 = `LineageGraph`(`fe-core.yaml:1488`, 서버 `return lineage_graph(...)`, 엣지 `method` 포함 `lineage.py:135`) 라 「응답 그래프 채택」이 성립한다. 폐기 비용 = 모달·소스·시험 9건 재작성.

Against:
- 모달의 유일한 화면 방어선(초과 후보 차단)이 **잘못된 기준값** 위에 서 있다. 기준 = 그래프 노드 `processingLevel` = `d3_catalog.processing_level()`(파생 · 부모 없으면 0 · 상한 Lv2, `d3_catalog.py:1125-1127`). 서버는 `user_set_level()`(사람 Lv, `lineage.py:200-202`). 두 기준이 갈리면 ⑴ `기록 없음` 상세에서 Lv≥1 후보 전부 차단(핵심 흐름 불능) ⑵ 사람 Lv3 이면 상한 Lv2 로 잘려 Lv3 부모 차단 ⑶ 반대 방향(파생>사람)이면 화면은 허용·서버 400 — 그 400 문구는 F2 로 삼켜져 사용자에게 「계보를 고치지 못했어요.」 만 보인다. 레인이 §5 에서 「규칙은 같고 기준값의 출처만 다르다」로 0 위험 처리한 대목이 실제 결함이다.

Verdict: approve-with-changes — F1·F2 병합 전 필수. 나머지 승인.

Risks:
1. F1 — 실서버에서 `계보 채우기` 가 Lv0 후보 외 전부 막힘. 시험 fixture(`processingLevel: 2`)가 실서버 값(0)을 가리고 있다.
2. F2 — 서버 400/409(순환 `LineageCycle`) 사유가 화면에 닿지 않음. 관례 위반 + 오류 경로 시험 0건.
3. 빈 상태 보조 문구 「원자료(Lv0)…」 가 `canEdit` 안에 있어 권한 없는 계정은 3문면 중 2문면만 본다(기존 코드 · PRD ⑵ 는 「빈 상태 3문면」). 룰 — Ted/PRD 해석 사안, 보고만.

Missed (intent 대조 · 미달/초과):
- 미달: 오류 경로 시험(400 문구 노출) 없음. 기준 Lv 시험이 `이 데이터 processingLevel: 0` 케이스 없음.
- 초과: `DatasetEditForm` 보조 문구 「부모 연결과 가공 방식은 계보 구역에서 고쳐요.」 신규 문면(정본 축자 아님). `LINEAGE_LINK_LABEL/ACTION` 상수 2개 신설 — PRD-22 확장 범위 내.
- 하지 않은 것 3건(사후 `기록 없음` 선언 · 기존 엣지 `method` 수정 · B5 표시 규칙 갈림)은 계약/서버 필요로 FE-only 밖 — 후속 WU 등재 필요, 이 레인 결함 아님.

Fixes:
- [병합 전 필수] F1 — `DatasetDetailPage` 에서 `selfLv={levelOf(shown.basicInfo.processingLevelUserSet)}`(`DetailHeader.tsx:117` 과 같은 함수)를 `LineageSection` → `LineageFixModal` 로 prop 전달. `LineageSection.tsx:234` 의 노드 기반 계산 삭제. 시험: fixture 의 「이 데이터」 `processingLevel: 0`(기록 없음 실값) + `processingLevelUserSet: 'Lv2'` 로 Lv1·Lv2 후보가 고를 수 있음을 잠근다.
- [병합 전 필수] F2 — `lineageEditSource.ts` 를 관례로: `if (!r.data) fail(r.error as Envelope, '계보를 고치지 못했어요.')`(또는 `messageOf`). 시험 1건: `addParent` reject(서버 문구) → `lin-fix-error` 에 그 문구 축자, 모달 열린 채 유지.
- [권고] 세션 노트 §5 첫 항목을 「기준값 출처 차이 = 결함, F1 로 정정」으로 갱신.
