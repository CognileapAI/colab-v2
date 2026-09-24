# 디자인 구조 P0 결과 — 캡처·픽셀 대조 도구

spec: `dev-package/prd/specs/S-DESIGN-STRUCTURE-P0-20260924.md` · intent: `dev-package/intent/2026-09-24-design-system-structure.md` · 계획: `dev-package/reports/design-system/20260924/architecture.md §2-3·§3 P0`

## 결론

- 같은 HEAD(`e6c7f9c6`)를 두 번 찍어 **196장 · 33장면 전 캡처 엄격 차이 0 · `visual:diff` exit 0**.
- red 경로: PNG 1장 1픽셀 변경 → 그 캡처만 red · exit 1 · 차이 이미지 생성. PNG 1장 삭제 → exit 78. 명세 sha256 불일치 → exit 78.
- 조건: 캡처 브라우저 래스터 인자 고정(아래 ⓑ). 인자 없이는 같은 HEAD 두 번 찍기가 red 4~8장(1~40px)이었다.
- 제품 코드(`frontend/src/**`) 변경 0. 게이트 green 3 / red(판정) 0 / red(준비) 0.

## 산출 파일

| 경로 | 내용 |
|---|---|
| `frontend/scripts/visual-baseline/scenes.json` | 장면 명세 33개 · 캡처 196 · 브라우저 인자 · 장면별 계정 플래그 |
| `frontend/scripts/visual-baseline/capture.py` | audit 빌드 → 빈 포트 `vite preview` → agent-browser 캡처 → `index.json` |
| `frontend/scripts/visual-baseline/compare.mjs` · `compare.d.mts` | PNG 두 장 비교(엄격 · 보조 · 크기 차이 · 차이 이미지) |
| `frontend/scripts/visual-baseline/diff.mjs` | 디렉터리 대조 · `report.json`·`report.md` · exit 0/1/78 |
| `frontend/test/visual-diff.test.ts` | ⓓ 시험 4건 |
| `frontend/audit-design.tsx` | 장면 3개 추가 · 계정 플래그 쿼리 · preview 픽스처 `target` |
| `frontend/package.json` · `package-lock.json` | `visual:capture`·`visual:diff` · `pixelmatch 7.2.0`·`pngjs 7.0.0`(고정) |
| `.gitignore` | `frontend/.visual/` |
| `dev-package/reports/design-system/20260924/p0/visual/` | 최종 대조 보고 · red 증명 보고 · 인자 고정 전 대조 보고 2건 |

사용법(작업 디렉터리 `frontend/`):

```
npm run visual:capture -- --label before          # audit 빌드 포함 · frontend/.visual/before/
npm run visual:capture -- --label after --skip-build
npm run visual:diff -- .visual/before .visual/after .visual/report
```

## ⓐ 캡처 196장

- `p0-a`: `npm run audit:build` 포함 · 2병렬(테마당 세션 1) · 02:26:35~02:34:35 UTC(8분 0초). `p0-b`: `--skip-build` · 02:34:40~02:42:31 UTC.
- 두 실행 모두 PNG 196장 + `index.json`(`captureCount` 196 · `scenes` 33 · 명세 sha256 `d6983d71…` · HEAD `e6c7f9c6` · 미커밋 변경 없음).
- 0바이트 파일 0장(최소 13,935B). 캡처별 `agent-browser errors` 출력이 비어 있지 않은 캡처 0장.
- 매 캡처 전 페이지 상태 확인: `documentElement.dataset.theme`·`innerWidth`·`devicePixelRatio` 가 명세(테마·폭·1)와 다르면 capture.py 가 78 로 멈춘다. 196장 모두 통과.

## ⓑ 같은 HEAD 두 번 찍기

최종: `visual/report.md` — 196장 · red 0 · 엄격 차이 합 0 · 보조 차이 합 0 · 크기 차이 0 · **exit 0**.

래스터 인자 고정 전 측정(같은 HEAD `f417c769`):

| 실행 | 병렬 | red | 엄격 px 합 | 보조 px 합 | 보고 |
|---|---|---:|---:|---:|---|
| pre-a ↔ pre-b | 2 | 4 | 14 | 0 | `visual/pre-fix/parallel2.md` |
| s1 ↔ s2 | 1 | 8 | 83 | 0 | `visual/pre-fix/serial.md` |
| 부분집합 5장면 u1 ↔ u2 / u1 ↔ u3 | 2 | 6 / 7 | 58 / 83 | — | 로컬만 |
| 같은 부분집합 + 인자 v1 ↔ v2 / v1 ↔ v3 | 2 | 0 / 0 | 0 / 0 | — | 로컬만 |

- spec 우려 2 대로 1병렬로 다시 찍었으나 red 가 줄지 않았다(4 → 8) — 병렬 부하가 원인이 아니다.
- 인자: `--disable-gpu` `--disable-gpu-rasterization` `--disable-partial-raster` `--disable-skia-runtime-opts` `--force-color-profile=srgb` `--disable-lcd-text`. `scenes.json` 의 `browser.args` 에 두어 명세 sha256 이 함께 잠근다. capture.py 가 매 호출에 `--args` 로 넘긴다(환경변수 경로와 결과 바이트 동일 확인).
- 인자 적용 전후 캡처는 전 캡처가 다르다(부분집합 30장 전부 red) — 인자가 실제로 적용됐다는 확인이자, **P1 기준 캡처는 이 명세로 새로 찍어야 한다**는 뜻이다.
- `diff.mjs` 는 캡처 뒤 한 번 고쳤다(`3327cb9a` · 「캡처 뒤 바뀐 PNG」 표기). 캡처는 `e6c7f9c6` 에서, 위 보고들은 `3327cb9a` 의 diff.mjs 로 다시 냈다.

### 불안정 장면 (인자 고정 전 · 최종 실행에서는 0)

| 캡처 | 엄격 px | 보조 px | 위치 | 추정 원인 |
|---|---:|---:|---|---|
| `project-dialog-dark-768` · `project-dialog-dark-1440` · `project-dialog-light-375` · `project-dialog-light-768` | 1 | 0 | 닫기 버튼 포커스 링 가장자리 | 둥근 외곽선 안티앨리어싱 값 ±1~3 (GPU 래스터) |
| `project-close-light-768` · `project-close-dark-768` | 1 | 0 | 닫기 버튼 포커스 링 | 같음 |
| `lab-dialog-dark-768` · `lab-dialog-light-768` | 11 · 17 | 0 | 대화상자 오른쪽 아래 둥근 모서리 | 같음 |
| `search-dark-375` (그리고 시행 캡처 `lab-dark-375`) | 11 | 0 | GNB 로그아웃 버튼 네 모서리 | 같음 |
| `upload-metadata-dark-375` | 40 | 0 | 하단 버튼 둥근 테두리 | 같음 |

모든 차이가 둥근 테두리·외곽선의 가장자리 픽셀이고 값 차이가 채널당 1~4 다(보조 설정 0). 원인은 측정으로 좁힌 추정이며 Chrome 내부에서 확인하지 않았다. P1 대조에서 제외한 장면은 없다.

## ⓒ red 픽스처

`p0-b` 를 두 벌 복사해 만든다(조작 스크립트는 커밋하지 않음 · 사본은 `frontend/.visual/`).

| 조작 | 명령 | 출력 | exit |
|---|---|---|---:|
| `p0-red/catalog-light-768.png` (100,100) 255,255,255 → 0,0,0 | `diff.mjs .visual/p0-b .visual/p0-red …` | `196 captures · red 1 · strict px 1 · exit 1` · red = `catalog-light-768` 하나 · `catalog-light-768.diff.png` 생성 | 1 |
| `p0-missing/login-dark-375.png` 삭제 | `diff.mjs .visual/p0-b .visual/p0-missing …` | `::visual-diff-readiness:: PNG missing (1): frontend/.visual/p0-missing/login-dark-375.png` | 78 |
| 인자 고정 전 명세로 찍은 `pre-b` 와 대조 | `diff.mjs .visual/pre-b .visual/p0-b …` | `::visual-diff-readiness:: manifest sha256 differs: baseline a5ba3306… vs candidate d6983d71…` | 78 |
| 인자 없음 · 장면 집합 다름 · `index.json` 없음 | (개발 중 확인) | `usage: …` · `scene sets differ …` · `candidate index.json missing …` | 78 |

red 보고: `visual/red-proof/report.md`. 바뀐 PNG 는 자기 `index.json` sha256 과 달라 「캡처 뒤 바뀜」으로 표기되고 불안정 목록에 들어가지 않는다.

## ⓓ 시험 `frontend/test/visual-diff.test.ts`

- 이름: `visual-diff compare — PNG 픽스처 4종(동일 · 1픽셀 다름 · 미세 색 1픽셀 · 크기 다름)`. 4건: 동일 → 0/0 · 1픽셀 흑백 → 엄격 1/보조 1 · R 100→101 → 엄격 1/보조 0 · 8×6 대 9×6 → 크기 차이 · 6px.
- 먼저 red 확인: `Error: Failed to resolve import "../scripts/visual-baseline/compare.mjs" from "test/visual-diff.test.ts". Does the file exist?`
- 구현 뒤 4건 통과. 픽스처 PNG 는 시험 안에서 `compare.mjs` 의 `encodePng`(pngjs)로 만든다 — `pngjs` 에 타입 선언이 없어(`@types/pngjs` 는 승인 범위 밖) 시험이 pngjs 를 직접 import 하지 않는다.

## ⓔ 새 장면 DOM 질의

`agent-browser eval`(같은 브라우저 인자)로 질의했다. 스크린샷으로 판정하지 않았다.

| 장면 · 테마 · 폭 | 결과 |
|---|---|
| `account-admin` light 1440 · dark 375 | `th` 8개 = 이메일 · 이름 · 역할 · 연구실 · 상태 · 시스템 관리자 · 최근 로그인 · 행 동작(`aria-label`) · `tbody tr` 5행 · GNB 있음 |
| `password-change` light 768 · dark 375 | `form.login-card [data-testid=new-password]` 있음 · GNB 없음 |
| `gnb-more` light 375 · dark 768 | `.gnb-more` `aria-expanded="true"` · 목록 항목 = 업로드 · 연구실 설정(운영자 아님 → 계정 관리 없음) |

## ⓕ 커버리지 — 09-12 이후 `frontend/src` 변경 파일

`git diff --stat 09b97a34 HEAD -- frontend/src` = **91개**(spec 문구는 93개 — spec 작성 HEAD `0e5b8361` 기준으로도 91개다).

읽는 법: 「대응 장면」은 장면의 루트 컴포넌트(audit 파일이 그리는 컴포넌트)에서 상대 import 를 따라 닿는지로 셌다(`frontend/scripts/reachable-from-entry.mjs` 와 같은 방식 · CSS `@import` 포함). import 도달은 **그 코드 경로가 화면에 그려진다는 증명이 아니다**. 「GNB 경유」는 GNB 모듈 그래프에서 닿는다는 뜻이고 GNB 는 `login`·`password-change`·`upload*` 를 뺀 27장면에 그려진다. 「전역 CSS」는 `src/shell/styles.ts` 가 싣는 파일로 모든 장면에 적용된다.

장면 루트에서 닿지 않는 파일 6개:

- `shell/AppLayout.tsx` — **대응 장면 없음.** audit 는 `AppLayout` 을 마운트하지 않는다(GNB 를 직접 그린다).
- `auth/AuthGate.tsx` — GNB 경유 import 만. 바뀐 분기(`mustChangePassword` → `PasswordChangePage`)는 어느 장면도 거치지 않는다(`password-change` 는 페이지를 직접 그린다).
- `shell/Gnb.tsx` · `components/upload/UploadEntry.tsx` — 27장면의 GNB 로 그려진다(`gnb-more` 는 열린 메뉴까지).
- `shell/shell.css` · `shell/design-system.css` — 전역 CSS 로 전 장면.

| # | 파일 (`frontend/src/` 이하) | 대응 장면 (장면 루트에서 import 도달) | GNB 경유 | 전역 CSS |
|---:|---|---|:---:|:---:|
| 1 | `api/client.ts` | 전 33장면 중 30개: `catalog`, `lab`, `empty`, `gnb-more`, `lab-dialog`, `projects`, `project-table`, `project-dialog`, `project-close`, `project-detail`, `detail`, `settings`, `members`, `search`, `search-empty`, `search-down`, `search-degraded`, `preview`, `preview-done`, `preview-expired`, `approval`, `approval-dialog`, `lineage-picker`, `login`, `account-admin`, `password-change`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 2 | `auth/AuthGate.tsx` | — | 예 |  |
| 3 | `auth/LoginPage.tsx` | `login` | 예 |  |
| 4 | `auth/PasswordChangePage.tsx` | `password-change` | 예 |  |
| 5 | `auth/login.css` | `login`, `account-admin`, `password-change` | 예 | 예 |
| 6 | `components/catalog/CatalogTable.tsx` | `catalog` |  |  |
| 7 | `components/catalog/catalog.css` | `catalog` |  | 예 |
| 8 | `components/common/TargetLabSelect.tsx` | 전 33장면 중 15개: `lab`, `empty`, `gnb-more`, `lab-dialog`, `projects`, `project-table`, `project-dialog`, `project-close`, `project-detail`, `detail`, `settings`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 9 | `components/common/VariableTable.tsx` | `detail`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 10 | `components/common/accessState.ts` | `detail`, `settings`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 11 | `components/common/processingLevel.ts` | 전 33장면 중 16개: `catalog`, `lab`, `empty`, `gnb-more`, `lab-dialog`, `project-detail`, `detail`, `search`, `preview`, `preview-done`, `preview-expired`, `lineage-picker`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 12 | `components/common/toastCopy.ts` | `lab`, `empty`, `gnb-more`, `lab-dialog`, `detail`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 13 | `components/common/variableTable.css` | `detail`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 | 예 |
| 14 | `components/dashboard/dashboardSource.ts` | `lab`, `empty`, `gnb-more`, `lab-dialog` |  |  |
| 15 | `components/datasetpreview/DatasetPreviewSection.tsx` | `detail` |  |  |
| 16 | `components/datasetpreview/datasetPreviewSource.ts` | `detail` |  |  |
| 17 | `components/datasetpreview/types.ts` | `detail` |  |  |
| 18 | `components/detail/DatasetDeleteEntry.tsx` | `detail` |  |  |
| 19 | `components/detail/DatasetEditForm.tsx` | `detail` |  |  |
| 20 | `components/detail/DeleteConfirmModal.tsx` | `detail` |  |  |
| 21 | `components/detail/DetailHeader.tsx` | `detail` |  |  |
| 22 | `components/detail/FileList.tsx` | `catalog`, `detail` |  |  |
| 23 | `components/detail/LockedNotice.tsx` | `detail` |  |  |
| 24 | `components/detail/SearchEvidenceEditor.tsx` | `catalog`, `detail` |  |  |
| 25 | `components/detail/UsageSection.tsx` | `detail` |  |  |
| 26 | `components/detail/deletion.css` | `detail` |  |  |
| 27 | `components/detail/deletionSource.ts` | `detail` |  |  |
| 28 | `components/detail/detail.css` | `detail` |  | 예 |
| 29 | `components/detail/editFields.ts` | `detail` |  |  |
| 30 | `components/detail/fixture.ts` | `detail`, `approval`, `approval-dialog` |  |  |
| 31 | `components/detail/searchEvidenceSource.ts` | `catalog`, `detail` |  |  |
| 32 | `components/detail/types.ts` | 전 33장면 중 17개: `catalog`, `lab`, `empty`, `gnb-more`, `lab-dialog`, `detail`, `settings`, `search`, `search-empty`, `search-down`, `search-degraded`, `approval`, `approval-dialog`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 33 | `components/lab/LabInfoPanel.tsx` | `settings` |  |  |
| 34 | `components/lab/lab.css` | `settings` |  | 예 |
| 35 | `components/lab/labSource.ts` | `lab`, `empty`, `gnb-more`, `lab-dialog`, `settings` |  |  |
| 36 | `components/lineage/LineageSection.tsx` | `detail` |  |  |
| 37 | `components/lineage/LineageStep.tsx` | `detail`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 38 | `components/lineage/ParentPicker.tsx` | `detail`, `lineage-picker`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 39 | `components/lineage/lineage.css` | `detail`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 | 예 |
| 40 | `components/lineage/lineageSource.ts` | `detail`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 41 | `components/lineage/types.ts` | 전 33장면 중 15개: `catalog`, `lab`, `empty`, `gnb-more`, `lab-dialog`, `detail`, `search`, `preview`, `preview-done`, `preview-expired`, `lineage-picker`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 42 | `components/members/MemberPermissionGrid.tsx` | `settings`, `members` |  |  |
| 43 | `components/members/members.css` | `settings`, `members` |  | 예 |
| 44 | `components/members/permissions.ts` | `settings`, `members` |  |  |
| 45 | `components/members/port.ts` | `settings`, `members` |  |  |
| 46 | `components/preview/PreviewOverlay.tsx` | `detail`, `preview`, `preview-done`, `preview-expired`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 47 | `components/preview/PreviewPanels.tsx` | `detail`, `preview`, `preview-done`, `preview-expired` |  |  |
| 48 | `components/preview/PreviewPickRow.tsx` | `detail`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 49 | `components/preview/PreviewSlot.tsx` | `detail`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 50 | `components/preview/preview.css` | `detail`, `preview`, `preview-done`, `preview-expired`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 | 예 |
| 51 | `components/preview/previewSource.ts` | `preview`, `preview-done`, `preview-expired` |  |  |
| 52 | `components/preview/requestError.ts` | `lab`, `empty`, `gnb-more`, `lab-dialog`, `detail`, `preview`, `preview-done`, `preview-expired`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 53 | `components/preview/usePreviewRender.ts` | `detail`, `preview`, `preview-done`, `preview-expired` |  |  |
| 54 | `components/preview/useZoomPan.ts` | `detail`, `preview`, `preview-done`, `preview-expired`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 55 | `components/project/ProjectCards.tsx` | `projects`, `project-table`, `project-dialog`, `project-close` |  |  |
| 56 | `components/project/ProjectDatasetTable.tsx` | `project-detail` |  |  |
| 57 | `components/project/ProjectFormModal.tsx` | `projects`, `project-table`, `project-dialog`, `project-close`, `project-detail` |  |  |
| 58 | `components/project/format.ts` | `projects`, `project-table`, `project-dialog`, `project-close`, `project-detail`, `detail` |  |  |
| 59 | `components/project/project.css` | `projects`, `project-table`, `project-dialog`, `project-close`, `project-detail` |  | 예 |
| 60 | `components/project/projectSource.ts` | `projects`, `project-table`, `project-dialog`, `project-close`, `project-detail`, `detail` |  |  |
| 61 | `components/project/types.ts` | `projects`, `project-table`, `project-dialog`, `project-close`, `project-detail`, `detail` |  |  |
| 62 | `components/upload/GridAttachEntry.tsx` | `detail` |  |  |
| 63 | `components/upload/PeriodCalendarPopover.tsx` | `detail`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 64 | `components/upload/PreviewPanel.tsx` | `detail`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 65 | `components/upload/RegisterArea.tsx` | `detail`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 66 | `components/upload/UnfinishedUploads.tsx` | `lab`, `empty`, `gnb-more`, `lab-dialog` |  |  |
| 67 | `components/upload/UploadEntry.tsx` | — | 예 |  |
| 68 | `components/upload/UploadModal.tsx` | `detail`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 69 | `components/upload/openUpload.ts` | `lab`, `empty`, `gnb-more`, `lab-dialog` | 예 |  |
| 70 | `components/upload/pendingStore.ts` | `lab`, `empty`, `gnb-more`, `lab-dialog`, `detail`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 71 | `components/upload/previewSource.ts` | `detail`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 72 | `components/upload/projectSource.ts` | `detail`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 73 | `components/upload/transferSource.ts` | `lab`, `empty`, `gnb-more`, `lab-dialog`, `detail`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 74 | `components/upload/types.ts` | 전 33장면 중 15개: `catalog`, `lab`, `empty`, `gnb-more`, `lab-dialog`, `detail`, `search`, `preview`, `preview-done`, `preview-expired`, `lineage-picker`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 75 | `components/upload/upload.css` | `lab`, `empty`, `gnb-more`, `lab-dialog`, `detail` | 예 | 예 |
| 76 | `components/upload/uploadSource.ts` | `lab`, `empty`, `gnb-more`, `lab-dialog`, `detail`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 77 | `generated/fe-core.ts` | 전 33장면 중 30개: `catalog`, `lab`, `empty`, `gnb-more`, `lab-dialog`, `projects`, `project-table`, `project-dialog`, `project-close`, `project-detail`, `detail`, `settings`, `members`, `search`, `search-empty`, `search-down`, `search-degraded`, `preview`, `preview-done`, `preview-expired`, `approval`, `approval-dialog`, `lineage-picker`, `login`, `account-admin`, `password-change`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 78 | `permission/PermissionGate.tsx` | 전 33장면 중 15개: `catalog`, `lab`, `empty`, `gnb-more`, `lab-dialog`, `projects`, `project-table`, `project-dialog`, `project-close`, `detail`, `settings`, `upload`, `upload-classify`, `upload-metadata`, `upload-link` | 예 |  |
| 79 | `routes/AccountAdminPage.tsx` | `account-admin` |  |  |
| 80 | `routes/DatasetDetailPage.tsx` | `detail` |  |  |
| 81 | `routes/LabPage.tsx` | `lab`, `empty`, `gnb-more`, `lab-dialog` |  |  |
| 82 | `routes/LabSettingsPage.tsx` | `settings` |  |  |
| 83 | `routes/ProjectDetailPage.tsx` | `project-detail` |  |  |
| 84 | `routes/ProjectsPage.tsx` | `projects`, `project-table`, `project-dialog`, `project-close` |  |  |
| 85 | `routes/UnregisteredPreviewPage.tsx` | `preview`, `preview-done`, `preview-expired` |  |  |
| 86 | `shell/AppLayout.tsx` | — |  |  |
| 87 | `shell/Gnb.tsx` | — | 예 |  |
| 88 | `shell/GnbMoreMenu.tsx` | `gnb-more` | 예 |  |
| 89 | `shell/design-system.css` | — |  | 예 |
| 90 | `shell/shell.css` | — |  | 예 |
| 91 | `shell/tokens.css` | `settings`, `members` |  | 예 |

## 게이트

| 게이트 | 결과 | 요약 |
|---|---|---|
| `frontend-typecheck` | green | tsc --noEmit 오류 0건 |
| `frontend-test` | green | 130 파일 · 1614건 통과 · 실패 0 |
| `frontend-fixture-reach` | green | `src/main.tsx` 도달 203개 · 금지 모듈 0건 |

`COLAB_TASK_ID=<task> bash gates/run.sh task` · 계: green 3 / red(판정) 0 / red(준비) 0 · exit 0. 마지막 변경(이 보고서) 뒤 다시 실행한 결과가 handoff 증거다.

`npm run audit:build`(= `tsc --noEmit -p tsconfig.audit.json` + vite build)는 게이트가 아니며 `p0-a` 캡처가 실행해 통과했다.

## spec 대비 달라진 점 · 더한 것

1. **명세 동작 종류를 늘렸다.** spec 은 `click`·`wait` 만 적었으나 09-12 업로드 3장면(`upload-classify`·`upload-metadata`·`upload-link`)은 파일 고르기·분류 선택 없이는 그 상태가 되지 않는다. `select` · `pickFile` · `waitFor` · `scrollIntoView` 를 더했다. 09-12 캡처 스크립트가 git 에 없어 그때의 정확한 스크롤 위치는 재현하지 않았다 — 단계 영역(`.up-steps`)을 화면에 들인 상태가 새 기준이다. `project-table`(표 보기 전환)·`approval-dialog`(더보기 → 승인 취소)도 `click` 동작으로 연다.
2. **`pickFile` 은 DataTransfer 로 넣는다.** agent-browser 0.27.0 `upload` 명령 뒤에는 `snapshot`(`DOM.enable`)·`eval`(`Runtime.evaluate`)이 시간 초과로 멈췄다(빈 파일·16B 파일 모두 · 스크린샷만 동작). 페이지 안 `DataTransfer` 로 같은 파일을 넣으면 정상 동작했다.
3. **audit 픽스처 타입 오류를 고쳤다.** 착수 HEAD 에서 `tsc -p tsconfig.audit.json` 이 `audit-design.tsx` preview 장면의 `RenderJob` 에 `target` 이 없어 실패했고, 그래서 `npm run audit:build` 가 서지 않았다. 픽스처에 `target: {uploadId: 'upload'}` 를 채웠다(런타임에서 `target` 을 읽는 코드 없음 · 화면 무변).
4. **브라우저 래스터 인자**를 명세에 고정했다(ⓑ).
5. 계정 플래그는 명세 값을 쿼리(`upload`·`labSettings`·`operator`)로 넘기고 `audit-design.tsx` 가 읽는다. 값이 없으면 종전 기본값이다. `audit-upload.html` 은 자기 계정을 고정하므로 무시한다(명세 `notes` 에 적음).
6. `account-admin` 은 제품의 `AppLayout` 처럼 `<main className="appmain">` 안에 그린다.
7. `capture.py --only`(부분 캡처 · 디버그용 — 부분 집합은 `diff.mjs` 가 78)와 `--parallel 1|2`, `diff.mjs` 의 「캡처 뒤 바뀐 PNG」 표기를 더했다.
8. `visual:capture` 스크립트는 `--out` 을 박지 않았다 — npm 스크립트에 자리표시를 둘 수 없어 `-- --label <이름>` 또는 `-- --out <경로>` 로 넘긴다.
9. 전체 페이지 여부: 대화상자·모달·업로드·`gnb-more` 10장면은 뷰포트(900px), 나머지 23장면은 전체 페이지(spec 우려 1 권고 ⓑ). 전체 페이지 캡처는 문서 스크롤바 폭만큼 좁다(예: 375 → 360px).
10. 저장소 비움: 매 캡처 전 같은 오리진의 정적 자산(`assets/audit-tile-*.svg`)을 열고 localStorage·sessionStorage 를 비운 뒤 장면을 연다. 실행마다 세션 이름과 포트가 새로 정해진다.

## 하지 않은 것

- 제품 CSS·TSX 변경 없음. 새 장면 화면을 정정하지 않았다.
- 캡처 PNG 커밋 없음(최종 red 장면 0 이므로 세 장 복사 대상도 없음). red 증명의 차이 이미지는 조작으로 만든 것이라 커밋하지 않았다.
- 캡처 구동부를 도는 게이트를 만들지 않았다(spec 범위 밖 · P1 우려 항목).
- 로컬 PR 요약 `~/.local/state/colab/pr/design-structure-p0.md` 를 쓰지 않았다 — 레인 지시가 워크트리 밖 경로 쓰기를 금지한다. 오케스트레이터 몫.
- 09-12 PNG 와의 대조 없음(spec 범위 밖). 실제 서버·운영 화면·iOS/Safari 캡처 없음.
- 래스터 불안정의 Chrome 내부 원인은 확인하지 않았다(측정으로 인자 조합만 확인).

## 후속 항목

- `tsconfig.audit.json` 타입 검사는 어느 게이트에도 걸리지 않는다(`frontend-typecheck` 는 `tsconfig.json` 만 · `include=src·test`). 그래서 preview 픽스처 타입 오류가 `npm run audit:build` 를 깬 채 남아 있었다. P1 에서 `visual:capture` 가 매 단계 돌면 드러나지만 게이트로 묶을지는 P1 우려 항목으로 올린다.
- agent-browser 0.27.0 `upload` 뒤 페이지 질의가 멈추는 현상 — 도구 결함 후보. 재현: `audit-upload.html` 에서 `upload "input[type=file]" <파일>` 후 `snapshot -i`.
- `AppLayout.tsx`·`AuthGate` 의 바뀐 분기에 대응 장면이 없다. 필요하면 P1 에서 장면 추가 여부를 판정.
- spec 문구의 「93개」는 실측 91개다 — spec 정정은 오케스트레이터 판정.
