# advisor 게이트 ② — WU-A12R (lane `p3-rev2-build` · HEAD 65c63f9 · base bec1ced)

검토일 2026-09-07 · 읽기 전용 · 대조 = diff `bec1ced..65c63f9` · 세션 노트 · intent `2026-09-06-r-a2.md` · spec/round `R-A2.md` · PRD-39 절 · 신규 시험 파일 · 기존 코드(`FileDropCard.tsx` · `UploadModal.tsx` · `Toast.tsx` · `useZoomPan.ts` · `upload.css` · `tokens.css`).

## 체크리스트 3항

- **① revision 체인** — 해당 없음. `git diff bec1ced..65c63f9 -- contracts db alembic` = 0행(실측). 변경 12 파일 전부 `frontend/` ＋ `dev-package/`.
- **② 「main 과 동일」** — 보고서에 그 문구 0건. 수용 근거 = `frontend-typecheck` green · `frontend-test` 832/832 green(세션 노트 §3 축자). 전수 `all` 은 라운드 끝 몫(round §㉲) — 이 레인 수용 조건 아님.
- **③ intent 대조** — 아래 표.

### intent 「원한 결과」 #2 대조 — 항목별 미달·초과

| 항목 | 요구(intent/round/PRD 축자) | 실측 | 판정 |
|---|---|---|---|
| ① 분석 3단계 ＋ `다음` 비활성 | 「3단계 표시」· rev1 `pbStatus` 4문면 · `anNext.disabled` | `ANALYZE_STAGES` 3건(`UploadModal.tsx:55-60`) · `disabled={analyzing}`(`RegisterArea.tsx:840`) | 충족. **미달(부분)** = 4문면 중 `파일 읽는 중…` 부재 — 레인 자기표시 1 · Ted 판정 대상. **초과** = `NEXT_BLOCKED_HINT` 4번째 안내 문면(rev1 장면1 갈래 축자 주장 · 라운드 3문면 밖) |
| ② 모달 전역 드롭 | `document.addEventListener('drop', …)` | `UploadModal.tsx:415-437` document 1쌍 ＋ cleanup | **결함** — 아래 R1. 기존 라벨 핸들러(`FileDropCard.tsx:166`)와 **이중 수신** |
| ③ 파일 빼기 ＋ 고지 | `removeFile()` · `파일을 뺐어요. 입력하던 내용은 사라져요` | `removeFile` `:397-410` · Toast 공통 컴포넌트 · 문면 축자 일치 | 충족. **미달(부분)** = 고지가 약속한 「입력 내용 초기화」가 부분 — 아래 R2 |
| ⑩ 접근 구역 출처 문장 | 문면 축자 | `UsageSection.tsx:36-37` 축자 일치 · `canDownload` 구역 안 | 충족. 값 칸 없이 문장만(R-B 몫 · 레인 자기표시 3) |
| ⑫ 바닥 고정 ＋ 3문면 | `syncFoot()` · `#ufHint` · sticky | `FOOT_HINTS` 3건 · `.reg-actions{position:sticky;bottom:0}` | 충족. `FOOT_HINTS[1]` 「분류를 고르고…」 vs 단계명 `자동 메타데이터 확인` 불일치 — 판정 없이 무수정(규율 준수) · Ted 판정 대상 |
| HUD | `mousemove` 1 ＋ `pvLatOf`/`pvLonOf` ＋ `커서를 지도 위로`·`지도 밖` · 서버 0 | `onMouseMove` 1개(`PreviewPanels.tsx:272`) · 함수 2개 `:172-193` · 문면 2종 `:211,213` · fetch/source 호출 0 | 충족. **초과** = `onMouseLeave`(HUD 리셋 · 필요) · `HUD_SOURCE_LABEL='역산값'`(round 「라벨로 가른다」의 집행) · `pointFromViewport` 를 두 함수로 재작성(동작 보존) |
| 병존 | HUD 가 값 조회 대체 금지 · 출처 라벨 분리 | `ValueLookupPanel.tsx` 변경 = `<dt>값</dt>` → `셀값` 1곳 · 경로·훅·시험 무변 | 충족 |
| 존치 6종 | 컴포넌트·훅·경로·회귀 시험 무삭제 | diff 에 삭제 파일 0 · `gridFlow`·`LineageStep`·`LockedNotice`·`DetailHeader` 무접촉 · 시험 삭제 0 | 충족 |
| 회귀 5건 | 「있음 4 ＋ ⑼ 각각 회귀 시험 1건 green」 | 5건 전부 **기존**(`09247df` WU-A12 · `rev1-keep-regression.test.tsx`·`lineage-graph.test.tsx`) · 이번 레인 신규 0 | PRD-39·대장 완료조건(green) 충족. spec §53 「최소 11건이 **새로** 선다」 기준으로는 5건 미달 — 계수 추정문이라 수용 |
| 토스트 문면 | `toastCopy.ts` 재사용 · 재타이핑 0 | `ANALYZED_CHIP`/`ANALYZING_CHIP` import(`UploadModal.tsx:17`) · U-14 행 재사용 | 충족. `FILE_REMOVED_NOTICE` 는 `UploadModal.tsx` 상수 — `toastCopy.ts` 밖(PRD-43 「문면의 자리는 toastCopy.ts 하나」 — Toast.tsx 머리말 축자)이라 **자리 위반 후보** |

## 실화면 결함 (jsdom 이 못 보는 것)

- **R1 (병합 전 필수) — 드롭존 라벨에 놓으면 파일이 두 번 들어간다.** `FileDropCard.tsx:166` 라벨 `onDrop` 은 `preventDefault()` 만 하고 `stopPropagation()` 없음. 네이티브 `drop` 이 `document` 까지 버블 → `UploadModal.tsx:421` 문서 핸들러가 같은 `dataTransfer` 로 `collectDrop` 재실행 → `pick()` 2회(`pick` 에 중복 제거 없음 · `:371-383`). 결과 = `picked` 에 같은 File 2건 → `signature` 변화 → `upload.create(files)` 가 **2건으로 서버 접수** · 조각 묶음 「조각 2개」 오표시. 시험이 못 본 이유 = 신규 시험은 `upload-modal` 본문에 드롭(`prd39…test.tsx` ② 1번) · 유일한 라벨 드롭 시험(`upload-droptree.test.tsx:77`)은 `FileDropCard` 단독 렌더라 문서 리스너 부재.
- **R2 (병합 전 필수) — ③ 고지 문면과 동작 불일치.** `removeFile` 이 내리는 것 = name·draft·step·registerOpen·errors·rendered·gridSkipped. **남는 것** = `startParts`·`endParts`(기간) · `projects` · `lineage` · `lineageParents` · `transfer`(`UploadModal.tsx:119-147` useState 목록). 파일 하나를 빼고 등록을 다시 열면 이전 기간·프로젝트·계보 부모가 그대로 — 문면 「입력하던 내용은 사라져요」가 거짓. 레인 주석 `:392` 「화면이 실제로 그렇게 한다」와 상충.
- **R3 (병합 전 필수) — ① 실패 상태에서 단계 표시가 멈춘다.** `analyzeStage = !uploadId ? 1 : status?.ready ? 3 : 2`(`:291`). `status.failure` 세팅 시 폴링 정지(`:273`)하나 단계는 2 `확장자·용량 확인 중…` ＋ `분석 중` 칩으로 고정 · 그 아래 실패 배너가 동시 표시. `intakeError`(접수 실패) 시 단계 1 `파일 올리는 중…` 고정. 화면이 「진행 중」과 「실패」를 함께 말함.
- **R4 (판정) — ① 이 격자 검증 중에도 `다음` 을 막는다.** `ready` 는 격자 축 확정 판정을 포함(`:295-297` 주석). 종전에는 격자 검증 중 등록 ②③ 진행 가능 → 이제 `다음` 비활성 ＋ `분석이 끝나면…` 안내. rev1 `anNext.disabled` 와 정합하나 **기존 흐름 변경**이라 Ted 인지 필요(회귀 시험 없음 = 832 green 이 이 변화를 재지 않음).
- **R5 (관찰) — 전역 `dragover` preventDefault 가 모달 열림 중 전 페이지 드롭을 가로챈다.** 텍스트를 입력칸에 끌어 넣는 동작이 막힘(`collectDrop` 0건 → no-op). 모달 스코프 기능이라 수용 가능 · 문서화만.
- **R6 (관찰) — HUD `setHud` 가 mousemove 마다 `PreviewMap` 전체 재렌더.** throttle 없음. 타일 갈래(`tiled`)에서 타일 `<img>` 목록이 매 이벤트 재조립 — 브라우저가 src 동일이면 재요청 없음 · 실측 부하 미측정. 현재 규모(S-08 한 장 기본 · POL-021)에서 문제 확률 낮음. 수정 조건 = 실측 프레임 드롭 시 HUD 상태를 별도 컴포넌트로 분리.
- **R7 (관찰) — sticky 실효 미검증.** `.reg-actions` sticky 는 스크롤 컨테이너 `.up-body`(`overflow-y:auto` `upload.css:53-55`) 기준 · 중간 조상 `.regarea` 에 overflow 없음(`:81`) → 성립 조건 충족. jsdom 시험은 CSS 원문 문자열만 검사. 실화면 1회 확인 필요. `--color-surface` 는 `tokens.css:17` 정의 · 다크 테마 없음(`prefers-color-scheme` 0건) → 배경 fallback 위험 0.
- **R8 (관찰) — 색 하드코드 `#6b7280` 신규 4곳**(preview.css `.pv-hud` · upload.css `.uf-hint`·`.an-txt` · detail.css 는 크기만). 기존 파일에 같은 패턴 3곳 선재 · 토큰 규약 위반 여부는 프로젝트 규칙 없음 → 지적만.

## For / Against / Verdict

**For:**
- 6행 전부 축자·자리·근거가 세션 노트 `파일:행` 과 실물 일치. 계약·DB·서버 0 실측. 존치 6종 무접촉 · 값 조회는 `<dt>` 한 낱말만 변경. RED 20 → GREEN 22 선실측 · 게이트 2종 green 832/832.
- 「판정 없이 고치지 않는다」 규율을 두 곳(3/4 문면 · `FOOT_HINTS[1]`)에서 지키고 자기표시로 올림 — 재개봉 없이 Ted 판정 입력이 됨.

**Against:**
- ② 는 「종전 0건」 위에 **더한 것이 아니라 기존 라벨 핸들러와 겹친 것**이다 — 라벨 드롭 = 사용자의 기본 경로에서 파일이 2벌 접수되고 서버까지 2벌 간다. 시험 22건이 그 경로를 한 번도 밟지 않아 green 이 결함 부재의 증거가 아니다. 이 상태의 병합은 기능을 더한 것이 아니라 정상 경로를 깨는 것이다.
- ③ 은 고지 문면이 동작을 앞서고, ① 은 실패 상태에서 화면이 두 말을 한다 — 셋 다 「화면이 거짓을 말하지 않는다」는 레인 자신의 판단기준에 걸린다.

**Verdict: approve-with-changes** — ⑩ · ⑫ · HUD · 병존 · 존치 = 승인 / ② = R1 수정 ＋ 라벨 드롭 시험 1건 추가 전 병합 불가 / ① ③ = R2·R3 수정 조건부. approve-with-changes 는 기본값이 아니라 R1~R3 가 각각 5행 이내 결정적 수정이고 설계 방향 자체는 맞기 때문.

## Risks (상위 3)
1. R1 — 라벨 드롭 시 파일 2벌 접수(서버 부하·조각 오판) — 사용자 기본 경로.
2. R4 — 격자 검증 중 `다음` 차단은 기존 흐름 변경 · 시험 미보유 · Ted 미인지.
3. Ted 판정 대기 2건(4문면 · `FOOT_HINTS[1]`)이 병합 뒤 재작업으로 돌아올 수 있음 — 판정을 병합과 같은 회차에 받는 것이 비용 최소.

## Missed
- 라벨 드롭 ＋ 모달 통합 시험 0건(R1 원인).
- `removeFile` 이 남기는 상태 목록을 세션 노트가 적지 않음(R2).
- `status.failure`·`intakeError` 갈래의 단계 표시 시험 0건(R3).
- `FILE_REMOVED_NOTICE` 가 `toastCopy.ts` 밖 — PRD-43 「문면의 자리 하나」 대조 없음.
- 세션 노트 §1 회귀 5건 「기존분 green — 신규 추가 불요」— spec §53 「새로 선다」 와의 차이를 노트가 명시하지 않음.

## Fixes
- **[병합 전 필수] F1** `FileDropCard.tsx:166` 라벨 `onDrop`·`onDragOver` 에 `e.stopPropagation()` 추가(또는 문서 핸들러에서 `e.target.closest('[data-testid="up-drop"]')` 면 return). 시험 추가 = 모달 안에서 `fireEvent.drop(getByTestId('up-drop'), {files:[1건]})` → `up-files` 에 그 이름 **1회** · `조각` 묶음 미생성. RED 선실측.
- **[병합 전 필수] F2** `removeFile` 에서 `setStartParts`·`setEndParts`·`setProjects([])`·`setLineage(null)`·`setLineageParents([])`·`setTransfer` 초기값 복귀 추가 — 또는 고지 문면을 바꾸지 않는 이상(축자 정본) 동작을 문면에 맞춘다. 시험 = 파일 2건 → 등록 열고 프로젝트 선택 → 1건 빼기 → 등록 재개 시 선택 0.
- **[병합 전 필수] F3** `.up-analyze` 표시 조건에 `!status?.failure && !intakeError` 추가(실패 시 단계 표시 숨김 · 실패 배너 단독). 시험 = `failure` 세팅 fake → `up-analyze` null.
- **[Ted 판정 · 병합 전 질의 1묶음]** ㈎ `파일 읽는 중…` 4문면 요구 여부(요구면 서버 상태 1개 추가 = R-B) ㈏ `FOOT_HINTS[1]` 「분류를 고르고…」 존치 vs 단계명 정합(WU-B3 재편 시점) ㈐ R4 격자 검증 중 `다음` 차단 수용 여부 ㈑ ⑩ 값 칸 없는 출처 문장 단독 노출 수용(R-B 전까지).
- **[권고 · 선택]** F4 `FILE_REMOVED_NOTICE` 를 `toastCopy.ts` 로 이전(PRD-43 자리 규칙). F5 실화면 sticky·HUD 프레임 1회 확인 후 세션 노트에 기록. F6 세션 노트 §1 회귀 행에 「WU-A12 `09247df` 선재 · 신규 0」 명기.
