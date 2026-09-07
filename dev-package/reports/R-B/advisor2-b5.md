# advisor ② — WU-B5 `p3-lv-rules` (fe576a3 ← c453d5b)

For:
- 규칙 `부모 Lv ≤ 자기 Lv` 가 등록(`ingestion.py` 존재 판정 뒤·붙이기 전)·수동 추가(`add_lineage_parent`)·확정(`confirm_lineage` 도장 전) 세 경로에 같은 함수로 서고, 사람 NULL → 무검사·NULL → `mismatch=false`·초과 후보 미삭제·파생 파라미터 부재가 전부 시험으로 고정됨(RED 10 선실측).
- 계약 변경이 optional 열쇠 2×2 ＋ description 뿐, 마이그레이션 0, 되돌림 = 소비 중단. 폐기 비용 = 서버 17·FE 8 시험과 상태 승격 재작업.

Against:
- FE 상태 승격(`lineageCards` → `UploadModal`)이 레인 자체 판단으로 들어갔고, 그 승격이 만든 새 수명(파일 제거·되묻기 판정)을 레인이 대조하지 않음 — `removeFile` 잔존 결함이 그 증거. 승격 없이는 PRD-09 왕복이 성립하지 않으므로 승격 자체는 타당하나, 수명 전수 대조 없이 병합하면 B3 가 세운 「고지 = 화면」 규율이 깨짐.
- 수용 기준 ③ 문면(「후보가 Lv0 만 뜬다」)을 레인이 「좁힐 수 있다」로 재해석하고 노트 §1 에 「충족」으로 기재 — 해석은 가능하나 판정자 없이 문면을 바꾼 것. 이 판단을 뒤집을 증거 = Ted 가 PRD-08 「자기 Lv 이하만 필터에 뜨고」를 기본 필터로 읽는다는 한 줄.

Verdict: approve-with-changes — 계약·서버 승인 / FE 는 Fixes 1·2 후 병합 / 미달 ③ 은 Ted 판정.

Risks:
1. 파일 제거 후 재등록 시 이전 연결 카드·충돌 칩이 남음(`UploadModal.tsx removeFile` — `setLineageParents([])` 만 있고 `setLineageCards([])` 없음). 모달 닫기는 `UploadEntry` 가 언마운트해 무관.
2. 표시 규칙 갈림 — 카탈로그·상세 = 사람 값 우선, 계보 그래프 노드(`routes/lineage.py:76`)·프로젝트 표(`project.py:248`) = 파생값. 같은 데이터셋이 화면마다 다른 Lv 를 그림. 레인은 후자만 §8 에 기재.
3. `.lvl-3` 클래스 부재(`catalog.css:125-127` 0·1·2 만) — LV_CAP 3 ＋ 사람 값 우선으로 Lv3 칩이 이번 회차부터 실제 렌더(배경·글자색 없음). intent D-1(Ted 판정 대기)이 이 레인으로 실현됨.

Checklist:
- ① 계약: `fe-core.yaml` diff = `DatasetRow`·`DatasetBasicInfo` 에 `processingLevelDerived`(int|null, min 0)·`processingLevelMismatch`(bool|null) ＋ `FilterProcessingLevel`·`processingLevel` description. 스키마 폭 변경 0. `common.json ProcessingLevel` = `minimum: 0` · `maximum` 없음 → Lv3 응답 적합. 생성물 `generated/fe-core.ts` 동기(diff 대응 확인). LV_CAP 접촉 = `ports/lineage.py`(값·주석 보존) · `catalog.py:163` 검증 · `d4_lineage.py:46` CTE 는 상수 참조라 자동 · `test_lineage_depth_bound.py` 3건. 마이그레이션 0.
- ② 「main 과 동일」 표현 0. 로컬 DB 4건은 게이트(일회용 DB) 밖 절차 문제로 분류 타당 — 단 증빙 파일 `gate-summary.json` 이 `contract-lint` 1건만 담고 있어(tree 5fc4e51 · fe576a3) 889/932 는 노트 문장. 통합에서 재실행 필요.
- ③ intent B5 대조 — 400 ✔(`test_a_parent_above…`·`test_add_lineage_parent…`) / 보이되 못 고름 ✔ 3행 존재·`disabled`·사유 축자 / 4.5:1 ✔ 5.00 계산 시험 / 사후 충돌 ✔ 연결 유지·칩·버튼·되돌림·확정 400 / 불일치 경고만 ✔ / 필터 사람 값 ✔(`_compose` `level_view` → `_apply_filters` 가 `processingLevel` 열 사용, NULL 행 파생 퇴행 시험 있음). **미달**: 수용 기준 ③ 「후보가 Lv0 만 뜬다」 — 기본 `levelFilter=null`. **초과**: 0(상태 승격은 요구 성립 조건, PRD-07 `분류에서 바꾸기` 는 요구 문면).
- 사후 충돌 API 경로 = `confirm_lineage`(PATCH 로 내림 → 확정 400)·`add_lineage_parent`·`createDataset` 셋. PATCH 자체는 200(PRD-09 「연결을 지우지 않는다」와 부합).
- A9R 되묻기: `lineageParents.length > 0`(확인된 것만). 승격된 미확인 카드는 「손댐」에 미포함 — 승격 전에는 언마운트로 소실돼 셀 수 없었고 지금은 남으므로 세는 것이 PRD-14 「입력한 값 하나라도」에 부합.
- 「AI 계보 제안」 존치: `LineageSection.tsx` 변경 0, 제안 영역 코드 무변, 제안 항목 `parentLevel: null` 처리.
- 갱신 단언 5건: `test_axes_three` 0→3 ＋ 열쇠 2 추가(강화) · `test_dataset_detail` 집합 확장 ＋ NULL 행 단언(강화) · depth_bound 상한값 치환(동치) · `upload.test` 2건 — `lin-lv-note` 부재 ＋ 철거 문면 5종 0건(강화). 약화 0.
- 〈194〉 반전: `LineageStep.tsx:17` 원문 취소선 보존 · 문단 원문 주석 「종전 = …」 보존 · 렌더 자리 0건 시험. 대체 문면 = PRD `:254`·`:267`·`:295` 축자 일치.
- 접근성: `<button disabled>` 는 탭 순서에서 빠지고 사유 `<p>` 와 미연결. 키보드 사용자는 초과 행 존재를 탭으로 만나지 못함(브라우즈 모드로만). 안내 색 = 회색(#5b6472) — PRD `:1097` 「정보색(파랑) · 버튼 위(R-20)」와 상이.
- 60행 규약(`R-B-2-server.md:257` 「각 ≤60행」) 122행: 판정 영향 0, 규약 위반.

Missed:
- `routes/lineage.py:76` 그래프 노드 Lv 파생값(레인 미보고).
- `.lvl-3` 미정의가 이번 회차부터 사용자 노출.
- `removeFile` 의 `lineageCards`·`lineageConflicts` 미초기화.
- 미확인 카드의 되묻기 계수.
- 안내 줄 색상 R-20 불일치.
- 증빙 `gate-summary.json` 단일 게이트.

Fixes:
1. [병합 전 필수] `UploadModal.tsx removeFile` 에 `setLineageCards([]); setLineageConflicts(0);` 추가 ＋ `lv-rules-20260907.test.tsx` 에 「파일 제거 후 재등록 시 카드 0」 시험 1건(RED 선확인).
2. [병합 전 필수] 통합 브랜치에서 7종 게이트 재실행하고 `gate-summary.json` 을 7건 포함본으로 갱신(노트 §7 축자를 파일로 뒷받침).
3. 되묻기 판정식에 `lineageCards.length > 0` 추가(`UploadModal.tsx:432` 옆) ＋ 시험 1건.
4. Ted 판정 1건 묶어 질의 — 찾기 모달 기본 셀렉트를 「전체」로 둘지 「자기 Lv」로 둘지(수용 기준 ③ 문면 vs PRD-08 「숨기지는 않는다」). 판정 전 코드 무변.
5. 표시 규칙 갈림 2자리(`lineage.py:76`·`project.py:248`)와 `.lvl-3` 은 §10 후속에 등재하고 소유 WU 지정(B10·B11 후보) — 원장 〈N〉 근거에 함께 기재.
6. 안내 줄 색 R-20(정보색) 적용 여부를 B11 검수 항목으로 이관.
7. 노트는 §1·§2 표 ＋ §5·§8 만 남기고 나머지를 후속/원장으로 이동(≤60행).
