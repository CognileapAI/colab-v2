# Spec: R-C — 미리보기 5건(축 ①) ＋ R-B 후속(축 ②) 12 WU (계약 동결 해제 21차 · 마이그레이션 2건 전망 · head 1개)
출처 intent: `dev-package/intent/2026-09-08-r-c.md`(우산) · `dev-package/intent/2026-09-08-preview-slot.md`(축 ① 측정·16 판정) — **미승인 초안 · 커밋이 승인**

> ⛔ 이 spec 은 intent 두 벌을 재인터뷰 없이 합성한 것이다. 판정 밖의 값은 「레인 실측 위임」 또는 `[미측정]` 으로 적었고 새로 정하지 않았다. `path:line` 은 트리 `d969f34` 에서 재측정했다.

## 문제 진술

- 미리보기 자리가 그리기 완료 뒤에 생긴다 — `.mapstage`·`.mapcanvas` 에 높이·비율 규칙이 없고(`frontend/src/components/upload/upload.css:168-169` `margin-top`·`max-width` 뿐) 상세 `.pv-tile`·`.pv-viewport` 도 같다(`frontend/src/components/preview/preview.css:111,184`). 컨테이너 폭이 곧 배율이라 크기가 데이터마다 다르다.
- 상세는 세로 단일 컬럼이다(`frontend/src/components/detail/detail.css:27` `.detail-page { max-width: 1200px }` 하나 · 좌우 grid 0) — 순서 = `BasicInfoGrid`(`DatasetDetailPage.tsx:243`) → `FileList`(`:286`) → `LineageSection`(`:298`) → `#sec-preview`(`:325`) → `UsageSection`.
- 500MB 초과는 viz-render 가 413 `RENDER_TOO_LARGE` 로 거절하고(`services/viz-render/src/colab_viz/app/routes/renders.py:88,97` · `kernel/errors.py:18` · 문면 `failures.py:54`) FE 는 `createRender({ target: { uploadId }, style, withoutReferenceGrid })`(`PreviewPanel.tsx:140`)에 `fileIds`·`variable`·`instant` 어느 것도 싣지 않는다 — 복구 경로가 계약에만 있다.
- 그릴 변수를 고를 목록이 없다 — `readers.py:78 _pick_default` 가 첫 2D 변수를 고르고 `:351,437` 에서 생략 시 그것을 쓴다. 파일 목록(`fe-core.yaml:574,1070`)·시각(`core-viz.yaml:425-431 instant`)은 있다.
- 배경 지도 0(레포에 geo 자산·라이브러리 0건 · `services/viz-render/requirements.txt` rasterio 만) · 확대/축소는 상세의 `useZoomPan`(`frontend/src/components/preview/useZoomPan.ts:65`)에만 있고 확장보기 `PreviewExpandOverlay.tsx` 는 모달 껍데기(`:29-58`)라 배율이 없다.
- R-B 후속 19건이 소유 WU 없이 `R-B-ROUND-20260908.md §6` 에 놓여 있고, 그중 6건은 계약 첨가가 필요해 21차 없이는 착수할 수 없다.

## 해법 개요

- **틀을 먼저 세운다** — 업로드 장면2 진입·상세 열림 즉시 `aspect-ratio: 4/3` 고정 틀이 서고, 그 안에서만 `.vizph` → 진행 3단계 → 그림/실패 문면이 바뀐다(바깥 치수 불변). 문면·단계는 현행 그대로(신설 0).
- **상세를 좌우로 가른다** — 새 grid 컨테이너 한 겹(좌 미리보기 sticky · 우 기본 정보＋파일) · 계보·활용은 아래 전폭 · 960px 미만 한 열(미리보기 먼저). `SectionMenu` 앵커 3개 무변. 업로드 모달은 이미 좌우(`upload.css:71-78`)라 무변.
- **500MB 는 조각으로 도달한다** — 413 `RENDER_TOO_LARGE` 를 받으면 FE 가 `GET …/files` 의 첫 `renderable` 조각을 `RenderTarget.fileIds` 로 자동 재요청한다. 상한값·서버 무변.
- **선택은 바꿔 그리기다** — 파일(기존 files 조회)·변수·시각 세 드롭다운이 틀 안 컨트롤 줄에 서고, 변수＋시각 목록은 core-viz 「대상 기술(describe)」 조회 1건(21차 ⑴)이 준다. 기본값 = 서버 선택값을 화면에 표시. 한 번에 값 하나(`Policy_데이터셋_상세 §1.3-5`).
- **축척은 사다리다** — 기본 배율 = `bounds` 중심 ＋ 표준 축척 사다리 스냅 · `useZoomPan`/`.pv-zoom` 을 세 화면이 공유 · 작은 유역은 외곽선＋더블클릭 맞춤. 배경 = 자립형 Natural Earth 1:110m 해안선＋국경 SVG(외부 요청 0 · 500KB 상한).
- **축 ② 는 4묶음 6 WU** — 게이트 승격(G) · 서버 소형＋마이그레이션(S-서버) · FE 소형(S-FE) · Lv 통일＋계약(L＋K 일부) · 기록 없음 선언＋method op＋byCategory(K) · CSS 잔여(L). 사용자 관점 동일 행위는 기존 흐름 재사용(`rules §6-1`).

## 사용자 스토리

1. 올리는 사람으로서 파일을 놓는 순간 미리보기가 놓일 자리를 보고 싶다, 그림이 오면서 화면이 뛰지 않기 위해.
2. 보는 사람으로서 상세를 열면 그림이 왼쪽에, 기본 정보가 오른쪽에 있기를 원한다, 스크롤 없이 둘을 같이 읽기 위해.
3. 올리는 사람으로서 500MB 를 넘는 묶음도 미리보기가 그려지기를 원한다, 거절 문구 대신 첫 조각이라도 보기 위해.
4. 보는 사람으로서 어느 파일·변수·시각을 그릴지 고르고 싶다, 서버가 고른 첫 값이 내가 보려는 값이 아닐 때를 위해.
5. 보는 사람으로서 어느 데이터셋을 열어도 같은 축척 등급으로 보이길 원한다, 크기만 보고 범위를 오판하지 않기 위해.
6. 보는 사람으로서 래스터 아래 해안선·국경을 보고 싶다, 위치와 크기를 눈으로 확인하기 위해.
7. 보는 사람으로서 업로드·상세·확장보기 어디서든 같은 확대/축소 버튼을 원한다, 화면마다 다른 조작을 배우지 않기 위해.
8. 운영하는 사람으로서 마이그레이션 오라클 11벌과 `alembic upgrade head` 가 게이트 안에서 돌기를 원한다, 배포 창에서 드리프트를 처음 보지 않기 위해.
9. 연구실 관리자로서 기본 공개 범위에서 `지정 공개` 를 고르고 싶다, 3값 저장이 있는데 화면이 2값만 주기 때문에.
10. 보는 사람으로서 카탈로그·상세·계보 노드·프로젝트 표의 Lv 가 같은 값이기를 원한다, 한 데이터가 화면마다 다른 단으로 보이지 않기 위해.
11. 고치는 사람으로서 등록 뒤에도 「기록 없음」을 선언하고 이미 붙은 관계의 가공 방식을 고치고 싶다, 등록 때 놓친 것을 상세에서 닫기 위해.
12. 홈을 보는 사람으로서 데이터 맵이 주제가 아니라 분류 축으로 나뉘기를 원한다, 등록 화면이 분류를 받기 때문에.

## 구현 결정

- **WU 분할 12건 · 순서 고정(계약·DB → 서버 → FE → 검증)**
  - `WU-C6` 게이트 승격 3종(G · 질의 3·4·17·30) — 맨 앞. `db/platform/tests/{0004,0005,0006,0008,0009,0013,0015,0016,0017,0018,0019}-drift.sh`(실측 11벌 · §6 「7벌」은 낡은 수) 를 게이트 `migration-drift` 로 · `alembic upgrade head` 를 `schema-diff` 준비 단계로(`gates/run.sh:75` 설계 문장이 이미 그 순서) · `alembic` 을 `services/core-api/requirements-dev.txt`·`gates/requirements.txt` 에(실측 0건 · `grep -c alembic` 전부 0). 선례 = `gates/run.sh:268` dispatch ＋ `gates/tools/<name>.sh` ＋ `<name>-selftest` 짝(`gates/README.md:37` — selftest 없는 게이트는 집합에 없다).
  - `WU-C10` 계약 21차 패키지 집행(K · 첨가 6건 · 아래 「API 계약」) — 승인 커밋이 `contracts/` 첫 수정보다 먼저. `generated-up-to-date` green.
  - `WU-C7` 서버 소형＋마이그레이션(S-서버) — 프로젝트 이름 `UNIQUE (lab_id, name)`(`db/platform/schema.sql:1047` 표에 제약 0 · 앱 방어선은 `routes/project.py:148` 뿐 → DB 제약 추가) · 공개 범위 내림 소유자 한정(현행은 `업로드·편집` 스위치 · `routes/catalog.py:1113,1393` · 질의 19) · 이관 빈틈 보정(`0017:25` `NULL → NULL` 인 행 중 연구실 기본값 `잠김` ∧ 유효 grant ≥1 → `지정 공개` · 질의 20 · **배포 창 실측 선행**) · `ordinal` 0행 읽기 퇴행 제거(질의 9) · `replace_variables`(`d3_catalog.py:280`) statement-level 트리거(질의 36) · `d9_topic_synonym` 4값(`db/ai/schema.sql:85`) ↔ `category` 5값(`db/platform/schema.sql:440`) 이관(질의 5 · ai-service).
  - `WU-C9` Lv 표시 사람 값 통일(L 27·41 ＋ K 23·24) — 계보 노드(`routes/lineage.py:75-76`)·프로젝트 표(`routes/project.py:250`)가 파생값을 내고 카탈로그·상세는 사람 값 우선 → 서버 조립 함수 하나로 통일 · `ParentCandidateSuggestion`(`contracts/seams/core-ai.yaml:308`)에 `parentProcessingLevel` 첨가 · `ProjectDatasetRow`(`fe-core.yaml:4599`)에 `processingLevelUserSet` 첨가.
  - `WU-C1` 자리 선점 4:3 틀(FE · 업로드＋상세) → `WU-C2` 상세 좌우 배치(FE) → `WU-C3` 500MB 조각 폴백＋파일·변수·시각 선택 UI(FE · viz-render describe 소비) → `WU-C4` 축척 사다리＋공유 zoom 세 화면(FE) → `WU-C5` 자립형 배경 지도(FE 자산 · POL-021 부분 반전 〈N〉) — 다섯이 `PreviewPanel.tsx`·`DatasetPreviewSection.tsx`·`preview.css` 를 공유하므로 **직렬**.
  - `WU-C8` FE 소형(S-FE) — `LabInfoPanel.tsx:30` `VISIBILITIES` 3값 · `UploadModal.tsx:844` catch 의 400 ↔ 그 외 분리(질의 31) · 기간 인라인 칸 철거(`RegisterArea.tsx:341` 「종전 인라인 칸은 그대로 산다」 반전 · 질의 14) · Lv0 출처 안내 사람 Lv 기준(`BasicInfoGrid.tsx:114`·`detail/format.ts:16` · 질의 28) · 빈 상태 3문면 권한 무관(`LineageSection.tsx:316,323` `canEdit` 분기 · 질의 43).
  - `WU-C11` CSS 잔여(L 45~49) — `catalog.css:127-129` 에 `.lvl-3`(Lv2 보다 한 단 진한 같은 계열) · `:137 .lin--none` AA · `detail.css:134 .dt-gridact margin: -8px` 제거 · `upload.css` 자식 `margin-top` 9곳(`:147,150,159,166,168,170,191,234-237,243,251`)＋`lineageGraph.css:7 .dsec` 컨테이너 이관 · 코랄 복원은 목업 `:root` 회수 조건부(없으면 `[미상]` 보고).
  - `WU-C12` R-C 종료 검증 — 디자인 검수 재실측 ＋ 전수 게이트 `all` ＋ intent `원한 결과` 미달·초과 열거.
  - 의존 = C6 → C10 → C7 → C9 → C1 → C2 → C3 → C4 → C5 → C8 → C11 → C12. C3 은 C10(describe 계약)에, C9 는 C10 에 의존.
- **모듈 · 인터페이스**
  - `frontend/src/components/preview/` — 틀 컴포넌트 1개 신설(4:3 · 상태별 내부 슬롯) ＋ `useZoomPan` 에 사다리 스냅·더블클릭 맞춤 추가 ＋ 배경 SVG 컴포넌트 1개(`bounds` 있을 때만 · `pvLonOf`/`pvLatOf` 역산과 같은 좌표계 · `PreviewPanels.tsx:175-190`). 업로드 `PreviewPanel.tsx`·확장보기 `PreviewExpandOverlay.tsx` 가 그 셋을 재사용한다.
  - 축척 사다리 상수 = `frontend/src/components/preview/` 한 파일 한 자리(값은 레인 실측 위임 `[미측정]` · 후보 100·300·1,000·3,000·10,000 km). 하드코드 재정의 금지.
  - 배경 자산 = `frontend/src/assets/basemap/` Natural Earth 1:110m 해안선＋국경 GeoJSON(Public Domain · 출처·버전·간략화 수준을 같은 폴더 README 에) · 상한 500KB(`[미측정]` · 초과 시 간략화).
  - `services/viz-render` — `GET /targets/describe`(가칭 · 이름은 21차 패키지가 확정) 1건: 입력 `RenderTarget`, 출력 = 그릴 수 있는 변수명 배열(`readers.py:341-343` drawable 규칙 그대로) ＋ 시각 목록(건수·첫·끝 · `_time_index` `:295-333` 이 이미 세는 값) ＋ 서버 기본값. 읽기 전용 · 렌더 부작용 0 · 캐시 키 무접촉.
  - `services/core-api/app/routes/preview.py` — 릴레이 1건 추가(`:83 listPalettes` 와 같은 모양 · `_require_target_access` `:56` 재사용). core 는 식별자만 넘긴다(`core-viz.yaml:8-12`).
  - 500MB 폴백 = FE `usePreviewRender` 소비 규약 한 자리(`DatasetPreviewSection.tsx:135-136` 주석 「두 벌로 두면 판정이 갈린다」) — 413 `RENDER_TOO_LARGE` 수신 → files 조회 → 첫 `renderable` → `fileIds:[그것]` 재요청 → 틀 안 문면 「조각 `<이름>` 으로 그렸어요」(문면 원천 = `TOO_LARGE_MESSAGE` 둘째 문장 · 새 문장 짓지 않는다).
- **스키마 · 마이그레이션 — 2건 전망 · head 1개**
  - 현 head = `0019_rb7_search_index_m10`(`db/platform/versions/0019_rb7_search_index_m10.py:75-76`). 신설 `0020_rc7_project_name_unique`(`down_revision = 0019` · `UNIQUE (lab_id, name)` · 기존 중복 행 있으면 마이그레이션이 **멈추고 보고** — 지우지 않는다) → `0021_rc7_access_state_gap`(`down_revision = 0020` · 조건 = `0017:23-25` 의 NULL 행 ∧ 연구실 기본 `잠김` ∧ 유효 grant ≥1 → `지정 공개` · 배포 창 실측 건수가 0 이면 데이터 이동 0 인 채로도 체인에 남긴다).
  - 각각 `db/platform/tests/00NN-drift.sh`＋`-assertions.sql` 짝을 세운다(`0019-drift.sh:1-20` 형태 · WU-C6 이 이것을 게이트로 센다). drop 0. 되돌림 = 제약 DROP ＋ `지정 공개`→`잠김` 역이관(값 소실 0).
  - `db/ai` 체인 — `d9_topic_synonym` 5값 이관은 `db/ai/versions/0004_*`(down = `0003_k2_ontology_seed`) 1건 전망(WU-C7 · ai-service 소유 · `db/ai/tests/0004-0005-drift.sh` 선례).
- **API 계약 — 21차 · 첨가 6건 · 등급 전망 ㉮(비파괴)** — 확정은 `contract-breaking` 출력 축자(병합 직전).
  - ⑴ `core-viz.yaml` `/targets/describe`(신설 경로 · 기존 스키마 무변) ＋ `fe-core.yaml` 릴레이 경로 1 — 첨가.
  - ⑵ Lv 사람 값 통일 — `LineageGraph` 노드·`ProjectDatasetRow`(`fe-core.yaml:4599-4610` `processingLevel` required 유지)에 `processingLevelUserSet` **optional 첨가**(`:3571,3747` 기존 열쇠와 같은 이름·의미). 기존 `processingLevel` 열쇠의 의미를 바꾸지 않는다 → ㉮. ⚠ 「표시 규칙」은 FE 가 사람 값 우선으로 고른다 — 서버가 `processingLevel` 에 사람 값을 덮어 넣으면 열쇠 의미 변경 = ㉯ 이므로 하지 않는다.
  - ⑶ `DataMap`(`fe-core.yaml:4726-4750`) `byCategory` optional 첨가 · `byTopic` 유지(required 무변) → ㉮.
  - ⑷ `declareLineageUnknown`(사후 「기록 없음」 선언 · `unknownParents` `:4529` 의 쓰기 경로) ＋ `updateLineageParentMethod`(`LineageEdge.method` `:4508` 수정) — 기존 `addLineageParent`(`:1471`)·`removeLineageParent`(`:1505`)·`confirmLineage`(`:1521`) 형제 경로로 **신설 2** → ㉮. D10→D4 쓰기 경로가 아니다(사람이 부른다 · `ai-no-lineage-write` 무접촉).
  - ⑸ `ParentCandidateSuggestion`(`core-ai.yaml:308-322`) `parentProcessingLevel` optional 첨가 → ㉮.
  - ⑹ `ProjectDatasetRow` 는 ⑵ 에 포함.
  - 승인 패키지 = `dev-package/sessions/R-C-C21-REQUEST-<날짜>.md`(20차 선례 `R-B-C20-REQUEST-20260907.md`) · `PLAN-SoT §9` 행 ①~⑧(`R-B-2-server.md:205` 축자 항목) · 회차 번호 발급처 = `PLAN-SoT §9`(`X2-FREEZE-PROTOCOL.md §5`).
- 자리 선점 상태기계(FE · 틀 내부만 바뀐다):
  ```
  idle(.vizph) → drawing(stage: read|draw|legend) → done(img+legend) | failed(.vizerr · salvage 유지)
                                       └ 413 RENDER_TOO_LARGE → fallback(fileIds=[첫 renderable]) → drawing
  ```
- 문면 신설 0 — `UNAVAILABLE`(`PreviewPanel.tsx:22`)·`UnavailableNotice`·진행 3단계·`TOO_LARGE_MESSAGE` 그대로. 새 문장이 필요해지면 `[미상]` 으로 멈추고 보고한다.

## 시험 결정

- 외부 행위 기준 검증 항목(WU 별 수용 기준 축자는 라운드 파일 `§2`)
  - C1 — 파일 선택 직후·상세 열림 직후 틀 `aspect-ratio` 4:3 존재 · idle/drawing/done/failed 네 상태에서 바깥 `getBoundingClientRect` 폭·높이 불변 · `data-testid="up-preview-stage"` 문면 3단계 유지.
  - C2 — 1200px 에서 grid 2열(좌 preview · 우 infogrid＋files) · 960px 미만 1열이고 preview 가 먼저 · `sec-lineage`·`sec-preview`·`sec-usage` 앵커 3개 존재.
  - C3 — 413 `RENDER_TOO_LARGE` 픽스처 → files 조회 1회 → `createRender` 두 번째 호출의 `target.fileIds` 길이 1 · 드롭다운 3개(파일·변수·시각) · 변수 바꾸면 `variable` 열쇠 송신 · 시각 바꾸면 `instant` 송신 · 기본값 표시 문자열 = describe 응답값 · viz-render `describe` 시험 = NetCDF 픽스처의 drawable 배열이 `_pick_default` 규칙과 같은 순서 · GeoTIFF = `band1..N`.
  - C4 — `bounds` 폭 W 에 대해 스냅 단 = W 를 담는 최소 단(사다리 상수 전 단 각 1건) · 세 화면에서 `.pv-zoom` 버튼 3개 · 더블클릭 → `bounds` 맞춤 · 비지도형은 현행 회귀 시험 green.
  - C5 — `bounds` 있는 결과에 SVG 배경 1개 · 없는 결과에 0개 · 자산 파일 크기 ≤ 500KB 를 **시험이 센다** · 네트워크 요청 0(fetch 스파이).
  - C6 — `migration-drift` 게이트가 11벌 전부를 돌고 1벌이라도 빠지면 red · selftest 짝(ⓐ 대조군 green · ⓑ 되돌린 델타 red · ⓒ 대상 0건 red · ⓓ alembic 부재 red(준비)) · `schema-diff` 준비 단계가 `upgrade head` 뒤에만 비교.
  - C7 — 같은 연구실 같은 이름 INSERT 가 DB 에서 거절(앱 우회 시험) · 다른 연구실 성공 · 내림 요청이 소유자 아니면 403 · 소유자면 200 · `0021` 조건 행 픽스처 3종(NULL∧잠김∧grant / NULL∧열림 / 잠김∧grant0) 중 첫 것만 `지정 공개` · `ordinal` 0행 요청이 옛 배열로 퇴행하지 않음 · `replace_variables` N행에 트리거 실행 1회 · `d9` 5값 CHECK.
  - C8 — `LabInfoPanel` 셀렉트 3값 · 서버 400 문면이 그대로 뜨고 500 은 일반 문구 · 인라인 기간 칸 0개＋팝오버 1개 · Lv0 안내가 사람 Lv 기준 · `canEdit` false 계정도 3문면.
  - C9 — 노드·프로젝트 표·카탈로그·상세 4자리에서 같은 데이터셋의 표시 Lv 동일(사람 값 ≠ 파생값 픽스처) · 제안에 `parentProcessingLevel` · 화면 충돌 판정이 그 값을 쓴다.
  - C10 — 계약 첨가 6건 `contract-lint`·`generated-up-to-date` green · `contract-breaking` 출력 축자 = 파괴 0(㉯ 이면 멈추고 보고) · `declareLineageUnknown` 이 관계 있는 데이터셋에 400 · `method` 수정이 `confirmedAt` 을 바꾸지 않음 · `byCategory` 5값 전부(0 이어도 줄 유지 · `byLineageState` 규칙 준용).
  - C11 — `.lvl-3` 존재＋대비 AA · `.lin--none` ≥ 4.5:1 · `.dt-gridact` 음수 margin 0 · `upload.css` 자식 `margin-top` 0곳(컨테이너 gap 으로) · `.dsec` 부모 클래스 존재.
  - C12 — `all -j 1` green / red(판정) 0 / red(준비) 0 · 디자인 검수 항목 재실측표 · intent 원한 결과 미달·초과 열거.
- 재사용 seam: `frontend/test/*.test.tsx`(vitest · `vite.config.ts:19-21` jsdom · 현 72 파일) — 특히 `dataset-preview-zoom.test.tsx`(304행)·`preview.test.tsx`(445행)·`detail.test.tsx`(264행)·`upload-preview-poll-20260903.test.tsx`·`detail-section-menu.test.tsx` · viz-render `tests/test_upload_target_and_partial.py`·`test_instant_and_grid_digest.py`·`test_s3_source.py`·`test_numpy_format_and_axis_ladder.py` · core-api `tests/test_project_name_duplicate.py`·`test_access_state_three.py`·`test_variable_rows.py`·`test_lineage_graph_read.py`·`test_lineage_unknown.py`·`test_lv_parent_rules.py`·`test_dashboard.py`·`test_preview_relay.py` · `db/platform/tests/00NN-drift.sh` 형태.
- 신설 seam: 틀 컴포넌트의 상태 슬롯 export · 사다리 상수 export · 배경 SVG 의 `data-testid` · viz-render `describe` 라우트 · 게이트 `migration-drift`＋selftest · 마이그레이션 `0020`·`0021` drift 짝.
- 해당 서비스 단독 게이트 이름(레인별 좁은 집합): `work-item-consistency` · `exec-bit` · `frontend-typecheck` · `frontend-test` · `frontend-fixture-reach` · `service-tests-viz-render` · `service-tests-core-api` · `service-tests-ai-service` · `contract-lint` · `contract-breaking` · `generated-up-to-date` · `migration-single-head` · `schema-diff` · `rls-coverage`(0020·0021) · `ai-no-lineage-write`(C10). 전수 `all` 은 C12 한 번.
- green-by-skip 방지: 대상 0건이 아님을 무엇으로 보이나
  - C1·C2·C4 = 상태·분기 **건수를 단언**(4상태 · 2분기 · 사다리 단 수) · 상수 목록 길이 단언.
  - C3 = `createRender` 스파이 호출 횟수 2 와 두 번째 인자 형태 단언 · describe 응답 배열 길이 ≥1.
  - C5 = 자산 파일 존재＋크기 단언(파일이 없으면 red · 네트워크 0 은 스파이 호출 0 단언).
  - C6 = 게이트가 센 오라클 건수 11 을 출력에 드러내고 11 미만이면 red · 대상 0건 red.
  - C7 = 마이그레이션 `0021` 이 이동한 행 수를 출력하고 픽스처에서 1 을 단언 · UNIQUE 위반이 실제 IntegrityError 인지 단언.
  - C10 = `contract-breaking` 출력 축자를 라운드 파일에 붙인다(출력이 비면 red).
  - 각 WU 는 구현 전 **red 를 눈으로 확인한다**.

## 정책 대조 (작성 시점 제약)

- CLAUDE.md §2 도메인 / §3 불변 규칙 중 저촉 항목: **1건(부분 반전 · Ted 판정 필요)** — POL-021 「타일 서버도 바탕 지도도 쓰지 않는다」(`PLAN-SoT.md:591` · `WORK-UNITS.md:425` · `CLAUDE.md:19` `〈240〉`) ＋ PLAN-SoT ㉴ 「B-2 해안선 오버레이 미채택」. 반전 범위 = **자립형 벡터 배경만 허용** · 타일 서버·외부 CDN 금지 유지 · 타일 서빙 강제 없음(`〈240〉` 기본값 「한 장」). 〈N〉 에 축자 기록 · 원문은 지우지 않고 덧붙인다. 그 밖: ⑴ `CLAUDE.md:64` §3-4 geo 금지 — 미리보기 서버 변경은 viz-render 만 · core 는 릴레이(`core-viz.yaml:5-12`) ⑵ D10→D4 쓰기 무접촉(신설 계보 op 2건은 사람 호출 · `ai-no-lineage-write` 로 증명) ⑶ 마이그레이션 head 1 ⑷ RLS — `0020`·`0021` 은 기존 표 제약·값 이동뿐(`rls-coverage` 무변) ⑸ 문서 절대경로 0.
- CLAUDE.md §5 저촉: **없음** — 범위는 intent 두 벌 안 · 부분 완료로 닫지 않는다 · 게이트 우회 0.
- `rules §6-2`(편의 기능 유예): 선택 UI·확대/축소·배경은 Ted 발의 5건의 직접 요구라 편의 기능 유예 대상이 아니다. 도시 표기·겹쳐 보기는 끌어오지 않는다.
- 계약 동결 해제 필요: **예(Ted 서명 · 21차 · 등급 전망 ㉮)** — 서명 자리 = `intent/2026-09-08-r-c.md ## 확인` ＋ `sessions/R-C-C21-REQUEST-<날짜>.md`. 승인 없이 `contracts/` 를 고치지 않는다.

## 우려 항목 (판정 필요)

> 프론티어는 공집합이다(intent `## 확인`). 아래는 Ted 질문이 아니라 **레인 실측 위임 · advisor ② 판정 자리**다. 결과가 판정과 어긋나면 고치지 말고 보고한다.

| # | 항목 | ⓐ | ⓑ | 권고 |
|---|---|---|---|---|
| 1 | 축척 사다리 단 값 — 데이터 폭을 담는 「가장 작은 단」이 몇 단이어야 국내 유역(수십 km)부터 동아시아(수천 km)까지 등급이 갈리는가 | 5단(100·300·1,000·3,000·10,000 km) · 상수 한 자리 | 3단(300·1,000·3,000) | **ⓐ** — 작은 유역이 3단에서는 전부 첫 단에 뭉친다. 레인이 staging 실물 `bounds` 분포로 실측해 확정 |
| 2 | Natural Earth 1:110m 해안선＋국경 파일 실크기 | 500KB 이하 그대로 반입 | 초과 시 동아시아 창으로 잘라 간략화(출처·절차 README) | 실측 뒤 결정 — 상한은 판정값(500KB) |
| 3 | 21차 등급 — 첨가 6건 중 ⑵ Lv 통일이 기존 `processingLevel` 의미를 바꾸는가 | optional 열쇠 첨가만 · 기존 열쇠 무변 → ㉮ | 서버가 `processingLevel` 에 사람 값을 덮어 씀 → ㉯ | **ⓐ** — 표시 규칙은 FE 가 고른다. `contract-breaking` 출력이 ㉯ 를 내면 멈추고 보고 |
| 4 | 이관 빈틈 보정 `0021` — 실측 없이 마이그레이션을 짓는가 | 배포 창 실측(대상 건수) 선행 → 건수 0 이어도 체인에 남긴다 | 실측 없이 짓고 배포 창에서 확인 | **ⓐ** — 판정 20 축자 「배포 전 실측」. 레인은 픽스처로 짓고 실물 건수는 배포 창이 적는다 |
| 5 | `describe` 조회 소유 — viz-render 가 직접 내고 core 가 릴레이하는가, core 가 파일을 읽어 만드는가 | viz-render 라우트 ＋ core 릴레이(`preview.py:83` 모양) | core 가 NetCDF 를 열어 변수 목록 생성 | **ⓐ** — ⓑ 는 `CLAUDE.md §3-4`·`core-viz.yaml:8-10` 「core 가 파일을 해석하면 멈추고 보고」 위반 |
| 6 | 프로젝트 이름 UNIQUE `0020` — 기존 중복 행이 staging/prod 에 있을 때 | 마이그레이션이 멈추고 건수 보고(지우지 않는다) | 뒤 이름에 접미 붙여 자동 개명 | **ⓐ** — 사람 입력값 자동 변경 금지(PRD-32 「기존 행을 지우거나 쪼개지 않는다」 준용) |
| 7 | 500MB 폴백이 고른 「첫 renderable 조각」 이 사용자가 보려던 조각이 아닐 때 | 문면에 조각 이름을 적고 드롭다운으로 바꾸게 둔다(C3) | 조각 목록을 먼저 묻는 모달 | **ⓐ** — 판정 「자동 재요청」 축자. 모달은 흐름 추가 |

## 범위 밖

- 배포 창 실측 3건(질의 35·40·20 의 실측) · `COLAB_VIZ_WORK_MAX_BYTES` 배포값 실측 — 배포 창 항목. 실측 순서만 이 회차가 명시한다(`0021` 선행).
- 미리보기 렌더 성능 · 겹쳐 보기(overlay) · 타일 서빙 · 배경 지도 도시 표기 · 새 시각화 종류 · 상한 상향/철폐.
- 변수명 UNIQUE(질의 11 · 판정 A 「중복 허용 유지」로 종결 — §6 문면과 어긋남은 intent Q6 기록).
- `w9-dev-deploy-rebased` 처리(HANDOFF 다음 ⑷ · 별건).
- **존치 제거 금지** — 2단 등록 게이트 · 기준 격자 파일 흐름 · 이어올리기 배너 · 확장보기 · 격자 업로드 블록 · AI 계보 제안 · 값 조회 패널. 컴포넌트·훅·서버 경로·회귀 시험을 지우지 않는다.
- PRD-260905:385(장면1 = 드롭존만) 무개정.

## 산출 계획

- 라운드 파일: **3개로 쪼갠다**(R-B 방식 · 12 WU 가 한 파일 300행을 넘긴다) — `dev-package/prd/rounds/R-C-1-contract-db.md`(C6 · C10 · C7 · C9) · `R-C-2-frontend.md`(C1 · C2 · C3 · C4 · C5 · C8 · C11) · `R-C-3-verify.md`(C12 ＋ R-C 종료 검증). 각 ≤300행 · 첫 줄에서 이 spec 을 링크 · 겹치는 WU 는 가장 이른 계층 파일에(R-B intent Q2 축자). 대조용 `R-C.md` 는 만들지 않는다(R-B 는 쪼갬 전 원본이 있었고 이번엔 없다).
- 예상 레인 수: **12(직렬 1개씩).** 병렬 후보는 C6(게이트)‖C10(계약) 둘뿐이나 C10 승인 대기가 있어 기본 직렬. 축 ① 다섯은 같은 파일을 공유해 병렬 금지(`rules §3-1`).
- 통합 브랜치 `integration/r-c` · 기점 = `main` tip(해시를 박지 않는다 · `git rev-parse` 로 읽는다) · 워크트리 `.claude/worktrees/r-c`.
- 대장 = `WU-C1`~`WU-C12` 12건 `status: open` · `depends_on` 위 순서 · `stage: stage2` · `owner` 는 R-B 선례(`WU-B11` 레코드 `work-items.yaml:2866-2877` 필드 12개). `done` 재개봉 0.
- 결정 번호 〈N〉 = 병합 직전 재실측(현 최대 **374** · `bash dev-package/prd/tools/max-decision.sh`). POL-021 부분 반전 · 21차 집행 · R-C 집행 — 최소 3행.
