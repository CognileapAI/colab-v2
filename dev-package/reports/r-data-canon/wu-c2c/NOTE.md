# WU-C2c — 분석 실패 업로드의 등록 단계 이동 (`#40` 두 번째 잠금)

- 판정 기준 = 「분석 끝남」 ＝ `ready || failure`. 분석 산출물이 실제로 필요한 자리는 `ready` 단독 유지.
- **변경 1건** — `frontend/src/components/upload/RegisterArea.tsx:1021` `analyzing = !props.status?.ready` → `!(props.status?.ready || props.status?.failure)`. 소비처 = 바닥 안내(`reg-foot-hint`)·`reg-next` 비활성.
- **무변 · 이미 둘 다** — `UploadModal.tsx:539`(상태 폴링 종료) · `:618`(`analyzeBlocksNext`) · `:643`(`gridVerifying`) · `:1581`(`reg-open` · WU-C2a).
- **무변 · `ready` 단독 유지** — `UploadModal.tsx:567`·`:575`(격자 후보 조회 = 워커 프로필 필요) · `:1452`(`renderable` → 미리보기) · `:1530`(`grid-attach-confirm` = 축 해석 산출물 필요).
- **무변 · 무관** — `UploadModal.tsx:610`(`analyzeStage` 칩 — `:1341` 이 실패 시 블록 자체를 감춤) · `gridFlow.ts:247~255`·`PreviewPanel.tsx:275`(렌더 작업 실패이지 업로드 상태 아님).
- **지시문과 어긋난 사실 1건** — 단계 표시기 클릭은 잠겨 있지 않았다. `RegisterArea.tsx` 표시기 버튼은 `disabled` 가 없고 `onStep` → `UploadModal.tsx:312` `editRegistration` 은 제출 잠금만 본다. 잠긴 것은 `reg-next`·바닥 안내 둘뿐이다.
- **잠금을 박아 둔 기존 시험 0건** — `frontend-test` 1403건 전건 green, 수정한 기존 시험 없음.
- 오라클 = `frontend/test/upload-register-on-analysis-failure.test.tsx` 신설 케이스 1건(① → ② → ③ 를 `reg-next` 로 걷고 `reg-done` 클릭 · 생성 요청에 `variables`·`crs`·`period`·`observationInterval` 부재 단언).
- 게이트 = `frontend-test` · `frontend-typecheck` · `frontend-fixture-reach` green 3 / red(판정) 0 / red(준비) 0.
