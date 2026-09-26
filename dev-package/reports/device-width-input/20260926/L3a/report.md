# 레인 보고 — L3a 누르면 보이는 설명(V9 · `title` 전용 정보 10곳)

- spec: `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md` V9 · 부록 C · 부록 I 「L3a」 행 · 「새 문구안」 9–18 · 우려 10ⓐ · 「레인 확정」(L3a 제약 · 파일 끝 터치 블록 · 세로 넘침 대조 · 문구 확정)
- intent: `dev-package/intent/2026-09-26-device-width-input-rules.md`
- 브랜치: `claude/dwi-l3a` · 기준 `ac0a612b` · 중간 인계 `4843e50e` · 구현 `3494c242`
- task: `e4dd2a2b985c4b93bf99197c73c25585`(게이트 `frontend-typecheck` · `frontend-test` · `frontend-fixture-reach` · `frontend-design-lint` · `frontend-visual`)
- 판정: **구현 · 게이트 · 수치 완료.** 시험 RED 25 실패 → GREEN 46 · 전체 151파일 2186건 통과 · 게이트 green 5 / red(판정) 0 / red(준비) 0 · 페이지 4 = 선언 URL 4 · 390 터치 새 단추 높이 전부 44 · 목록 밖 작은 누름 칸 0 · 레인 L2b · L2a 판정 red 0 · 1440 마우스 대 B0 픽셀 0.

## 1. 바뀐 것

| 파일 | 변경 |
|---|---|
| `frontend/src/components/common/TouchNote.tsx`(새) | 「누르면 보이는 설명」 부품 `TouchNote`(설명 단추 `type=button` · `aria-expanded` · `aria-controls` → 펼침 글 `id` · `stopPropagation` · `as="node"` 는 `role=button` · `tabIndex=0` · Enter/Space) ＋ 자리 갈래 `TouchOrMouse`(터치면 감싸고 마우스 · 설명 없음이면 라벨 그대로) |
| `frontend/src/components/common/touchNote.css`(새) | `@layer screens` · 투명 설명 단추(`font: inherit` · 누름 `:active` = `--color-surface-pressed`) · 펼침 글(`--text-caption` · `--color-text-muted` · 내용 폭 최대 16rem · `[hidden]` 은 숨김) · 터치 블록 `.touch-note-trigger` 최소 높이 · 최소 가로 `var(--control-height)`(글자 크기 선언 0) |
| `frontend/src/components/catalog/CatalogTable.tsx` | 1 · 2 · 3 · 5 — 터치면 라벨을 `TouchOrMouse` 로 감싸고 `title` 은 `mouse ? … : undefined`. 새 상수 `VERIFIED_PENDING_TITLE`(마우스 원문) · `VERIFIED_PENDING_NOTE`(터치 확정 문구) |
| `frontend/src/components/project/ProjectDatasetTable.tsx` | 4 — 같은 방식 · 같은 상수 쌍 |
| `frontend/src/components/approval/VerifiedBadge.tsx` | 6 — 같은 방식 · 상수 `VERIFIED_MEANING` · 「표시 전용」 머리 주석에 터치 예외 한 단락 |
| `frontend/src/components/lineage/LineageSection.tsx` | 7 — 원천 · 묘비 노드는 터치면 `TouchNote as="node"`(상자 클래스 · `data-*` 그대로) · 마우스는 원래 `div` 와 `title={nodeTitle(n)}` 그대로. 8 — 이름 `title` 은 마우스만 · 터치면 이름 줄 아래 `ln-sub` 한 줄. 9 — 방법 라벨 `title` 은 마우스만 · 터치면 `lin-way--wrap` 표지 |
| `frontend/src/routes/AccountAdminPage.tsx` | 10 — 4칸 `title` 은 마우스만 · 터치면 `account-cell-wrap` 표지 |
| `frontend/src/components/lineage/lineageGraph.css` | 파일 끝 터치 블록 **앞**에 3규칙: `.lin-way.lin-way--wrap`(줄바꿈 · 한 줄 높이 23 그대로) · `.lin-col > .touch-note-text`(최대 178px) · `.ln[role="button"]:active`(누름 테두리) |
| `frontend/src/auth/login.css` | 파일 끝 터치 블록 **앞**에 `.account-table td.account-cell-wrap { white-space: normal; overflow-wrap: anywhere; }` |
| `frontend/test/device-width-input-20260926-L3a.test.tsx`(새) | 아래 §2 |

- 셸 · 토큰 CSS 변경 0 · L3b 파일 변경 0 · 다른 TSX 변경 0 · 기존 시험 수정 0 · L2b 시험 수정 0(규칙을 터치 블록 앞 · 조건 없는 표지 규칙으로 두어 「파일 끝 · 블록 1 · 선택자 집합」 단언이 그대로 green).
- 새 문구 = 「새 문구안」 확정 원문: 「승인 처리가 아직 도착하지 않았어요」(3 · 4 터치 · 마우스 `title` 은 「…않았다」 그대로) · 「가공 단계가 계보로 계산한 값과 다릅니다」 · 「교수가 품질을 보증했어요」 · 「연구실 밖 출처라 상세 화면이 없어요」 · 「지워진 데이터라 상세 화면이 없어요 · {삭제일}」 · 「{확정일} 에 확정했는데 {수정일} 에 파일이 바뀌었어요」 · 「외 N」 전체 프로젝트 목록(` · ` 이음). 9 · 10 은 새 문구 0.

## 2. 시험 RED → GREEN

- RED(시험만 · 제품 코드 0 · `ac0a612b` 위): `Tests 25 failed | 21 passed (46)`. 예: `src/components/catalog/CatalogTable.tsx <span title=…VERIFIED_PENDING_TITLE…>: expected [] to have a length of 1 but got +0` · `expected  to have a length of 8 but got +0`(목록 설명 단추) · `ENOENT … touchNote.css`. 처음부터 통과한 21 = 목록 길이 · `title` 전수 · 자리 1 · 2 · 5 · 7 · 8 · 9 · 10 의 속성 위치 · 마우스 갈래 5 · 대비 6.
- 중간(목록 4곳 뒤 · `4843e50e`): `14 failed | 32 passed`.
- 추가 RED(390 캡처 판독 뒤): 펼침 글이 표 칸 안에서 한 글자 폭으로 눌림 → `width: max-content` · `max-width: 16rem` 단언을 먼저 더해 `1 failed | 45 passed`(`expected [ 'display: block', …(9) ] to include 'width: max-content'`) → CSS 한 줄 → GREEN.
- GREEN(`3494c242`): `Tests 46 passed (46)` · 전체 `Test Files 151 passed · Tests 2186 passed` · 타입 검사 오류 0. 단언 삭제 0.
- 구성: ⑴ 목록 먼저 — 자리 10 · 속성 13 · 파일별 `title` 수(9파일) · 원소 속성 24 ＋ 부품 속성 1(`PreviewExpandOverlay`) = 25 · 자리마다 속성 위치(TS 구문 나무) · 새 부품 파일 `title` 0. ⑵ 터치(입력 방식 훅 모듈 모의) — 1–6 설명 단추 계약(`type=button` · `aria-expanded` 거짓→참→거짓 · `aria-controls` = 펼침 글 `id` · `hidden` · 문장 정확 일치 · 행 이동 0 · 라벨 `title` 없음) · 목록 단추 수 8 · 대조군(확정 · 원천 · 기록 없음 칩은 단추 아님) · 7 누르는 노드(클릭 · Enter · Space · 다른 키 무시) · 8 줄 아래 글(누르지 않아도) · 9 · 10 표지와 `title` 없음. ⑶ 마우스 — 새 단추 0 · `aria-controls` 0 · 원래 `title` 원문 · 대상 요소 수를 먼저 셈(green-by-skip 방지). ⑷ CSS — 부품 CSS 층 · 새 색 0 · 터치 블록 44 · 글자 선언 0 · 누름 피드백 · 줄바꿈 규칙이 파일 끝 터치 블록 앞 · 기존 150px 말줄임 · 계정 말줄임 규칙 불변. ⑸ 대비 — `--color-text-muted` 대 `--color-surface` · `--color-surface-alt` · `--color-bg`(라이트 · 다크) ≥ 4.5.

## 3. `title` 전수(TSX `title=` · 파일별 · 전 → 후)

| 파일 | 전 | 후 | 이 레인 자리 |
|---|---:|---:|---|
| `components/catalog/CatalogTable.tsx` | 6 | 6 | 1 · 2 · 3 · 5(조건부) · 아이콘 단추 2 그대로 |
| `components/project/ProjectDatasetTable.tsx` | 1 | 1 | 4(조건부) |
| `components/approval/VerifiedBadge.tsx` | 1 | 1 | 6(조건부) |
| `components/lineage/LineageSection.tsx` | 3 | 3 | 7(마우스 갈래 원문) · 8 · 9(조건부) |
| `routes/AccountAdminPage.tsx` | 5 | 5 | 10 × 4(조건부) · 본인 상태 1 그대로 |
| `components/preview/PreviewPickRow.tsx` | 6 | 6 | — |
| `components/common/VariableTable.tsx` | 1 | 1 | — |
| `components/upload/UploadModal.tsx` | 1 | 1 | — |
| `components/upload/PreviewPanel.tsx`(부품 속성) | 1 | 1 | — |
| `components/common/TouchNote.tsx`(새) | — | 0 | — |
| 계 | 25 | 25 | 원소 24 ＋ 부품 1 |

## 4. 10곳 — 터치 동작 · 글

| # | 자리 | 터치 | 보이는 글 |
|---|---|---|---|
| 1 | 목록 계보 「확인 필요」 | 칩 = 설명 단추 · 같은 칸 라벨 바로 뒤 펼침 · 칸 `title` 없음 | 「{확정일} 에 확정했는데 {수정일} 에 파일이 바뀌었어요」 |
| 2 | 목록 프로젝트 「외 N」 | 칩 = 설명 단추 · 칸 `title` 없음 | 전체 프로젝트 이름 ` · ` 이음 |
| 3 | 목록 「승인 전」 | 칩 = 설명 단추 | 「승인 처리가 아직 도착하지 않았어요」 |
| 4 | 프로젝트 상세 「승인 전」 | 같음 | 「승인 처리가 아직 도착하지 않았어요」 |
| 5 | 목록 「계산값과 다름」 | 표식 = 설명 단추(낭독기 이름 유지) | 「가공 단계가 계보로 계산한 값과 다릅니다」 |
| 6 | 상세 머리 「Verified」 | 배지 = 설명 단추 | 「교수가 품질을 보증했어요」 |
| 7 | 계보 그래프 원천 · 묘비 노드 | 노드 = 누르는 노드(`role=button` · `tabIndex=0` · Enter/Space) · 글은 노드 아래 칸 폭 안 | 「연구실 밖 출처라 상세 화면이 없어요」 · 「지워진 데이터라 상세 화면이 없어요 · {삭제일}」 |
| 8 | 계보 목록 묘비 줄 | 이름 줄 아래 보이는 글(누르지 않음) | 위 묘비 문장 |
| 9 | 계보 방법 라벨 | 말줄임 대신 줄바꿈 · `title` 없음 | 새 글 0 |
| 10 | 계정 관리 이메일 · 이름 · 역할 · 연구실 | 말줄임 대신 줄바꿈 · `title` 없음 | 새 글 0 |

- 마우스(판별 불가 포함): 10곳 모두 원래 요소 · 원래 `title` · 새 단추 0(시험 · 1440 픽셀 0).

## 5. 게이트(task 실행 · 호스트 단독)

- 실행: `gates/run.sh task`(선언 5개 한 번) · `COLAB_TEST_ENV_FILE=~/.colab-v2-test-32.env` · `COLAB_TASK_ID=<task>` · `COLAB_VISUAL_URLS` = 이 레인이 띄운 audit 빌드(`vite preview --config audit.vite.config.ts --host 127.0.0.1 --port 47473 --strictPort` · 시작 때 PID 저장 · 그 PID 만 종료)의 4건 `audit-design.html?scene=<장면>&design=full`(`catalog` · `detail` · `project-detail` · `account-admin` · 장면 인자가 먼저). `COLAB_VISUAL_EXEMPT` 미사용.

| 게이트 | 결과(`3494c242` 트리) |
|---|---|
| `frontend-typecheck` | green — 오류 0 |
| `frontend-test` | green — 2186 통과 · 실패 0 |
| `frontend-fixture-reach` | green — 도달 213 · 금지 모듈 0 |
| `frontend-design-lint` | green — 파일 22(새 부품 CSS 포함) · a–h 0 · 문서 표 갈림 0 |
| `frontend-visual` | green — **페이지 4(= 선언 URL 4)** · 13px 미만 0 · 대비 < 4.5 0 · 스크린샷 8 |
| 계 | green 5 / red(판정) 0 / red(준비) 0 |

- 이 보고서 커밋 뒤 같은 명령으로 한 번 더 돌려 인계한다(최종 gate-summary 절대경로와 3계수는 인계 메시지).

## 6. 수치(직렬 실행 · 자기 캡처 · audit 빌드 = `3494c242` 트리)

### 6-1. 390 터치 수치 전용(4장면 × 2테마 · 8파일 · 모두 종료 0)

- 실행: `capture.py --label dwi0926-l3a-390 --metrics-only --skip-build --scene <장면> --viewport 390`(측정 직후 같은 세션에서 새 단추 상자를 읽는 일회용 래퍼 · 커밋 안 함 · 실행기 변경 0).
- 목록 밖 작은 누름 칸(`smallOther`): **8파일 모두 0**.
- 새 단추(두 테마 같음): 목록 7개(「외 1」 50.7×44 · 「확인 필요」 66×44 × 2 · 「승인 전」 54.8×44 × 4) · 상세 3개(「Verified」 72.8×44 · 원천 노드 178×71.8 × 2) · 프로젝트 상세 7개(「승인 전」 54.8×44). **최소 높이 44 · 최소 가로 50.7.** 계정 관리 0(줄바꿈만). 펼친 뒤 문서 가로 폭 = 창 폭(390 · 넘침 0).
- 판정(`judge.mjs`):
  - `--lane L2b`: `files=8 lane=L2b red=0 readiness=1 … smallOther=0 outsideRed=16:0,44:2,넘침:0,가림:0 exit=78` — 78 은 이 4장면에 없는 L2b 대상(8–12 · 18 · 19 · 31 · 34 · 38–44 · 46)이 재지지 않은 것(장면 부분 실행 · 기대). **재진 L2b 대상 red 0.**
  - `--lane L2a`: `red=0 readiness=1`(3 · 4 · 21 이 이 장면에 없음 · 기대).
  - `--lane L3a`: `red=0 readiness=0 … exit=0`(부록 B 에 L3a 대상 없음 · 16 · 넘침 · 50–53 만).
  - 레인 밖 44 red 2 = `detail` 의 변수 표 대표 라디오(45 · L3b 몫) × 2테마.
- 이 audit 장면에 없는 것: 5 「계산값과 다름」(`?mismatch=1` 에서만) · 8 묘비 줄(픽스처에 묘비 없음) — vitest 가 확인.

### 6-2. 1440 마우스 대 B0

- `capture.py --label dwi0926-l3a-cap --skip-build --parallel 2 --only catalog,detail,project-detail,account-admin`(48장 · 종료 0) → `diff.mjs --subset --viewport 1440 <B0> dwi0926-l3a-cap` → **8장(4장면 × 2테마) · red 0 · 엄격 픽셀 0 · 종료 0.** B0 = 워크트리 `agent-abf926c2ed31f5520` 의 `frontend/.visual/dwi0926-base`(읽기만).

### 6-3. 세로 넘침 대조(「레인 확정」 · 펼침이 칸 안에서 늘어나는 자리)

- 방법: 수치 전용 실행기의 측정 직후 같은 세션에서 컨테이너 세로 범위(괄호 = 자손 위–아래 · 컨테이너 위 기준)를 읽고, 설명 단추를 모두 누른 뒤 다시 읽는 일회용 래퍼. 라이트. 터치 390 · 820 · 1024 ＋ 같은 폭 마우스(`390x844:mouse` · `820x1180:mouse` · `1024x1366:mouse`). 펼친 상태 전체 화면 스크린샷을 390 · 820 · 1024 터치로 찍어 눈으로 확인.

| 장면 · 컨테이너 | 폭 | 터치 접힘 | 터치 펼침 | 같은 폭 마우스 | 설명 |
|---|---|---|---|---|---|
| 목록 행(`tbody tr` 6) | 3폭 같음 | 84.5 · 74 · 74 · 74 · 74 · 73.5 | 127.5 · 88.5 · 88.5 · 74 · 112.5 · 107.5 | 74 · 74 · 74 · 74 · 74 · 73.5 | 접힘 첫 행 +10.5 = 줄바꿈된 프로젝트 칸 둘째 줄의 「외 1」 21 → 44 단추. 펼침 증가 = 설명 글 줄(우려 10ⓐ 「누른 행 높이가 늘어남」). 자손 범위 모두 행 안 |
| 목록 표 틀 `.tblwrap` | 3폭 | 498.5(0–498.5) | 643(0–643) | 503(0–488) | 마우스 +4.5 = 가로 스크롤 막대 15(터치는 겹쳐 그림). 펼침 = 행 합 |
| 상세 머리 칩 줄 `.dh-tags` | 3폭 | 44 | 44 | 21 | 「Verified」 21 → 44 설명 단추. 펼침 글은 배지 뒤 같은 줄(자리 남음) |
| 계보 그래프 `.lin-graph` | 3폭 | 191.6(19–172.6) | 289.6(19–270.6) | 206.6(19–172.6) | 마우스 +15 = 가로 스크롤 막대. 펼침 +98 = 원천 노드 2개 아래 설명 글(각 2줄 · 칸 폭 178 안) |
| 계보 칸 `.lin-col`(4) | 3폭 | 153.6 × 4 · 셋째 칸 자손 13.9–139.7 | 251.6 × 4 | 153.6 × 4 · 셋째 칸 23.4–130.2 | 셋째 칸 범위 차이 19 = 「활용 프로젝트」 25 → 44(L2b 27 · 이 레인 변경 아님). 펼침 = 원천 칸 설명 글 |
| 계보 목록 줄 `.lrow`(4) | 390 | 98.4 · 170.4 · 75.8 · 170.4 | 같음 | 98.4 · 150.4 · 75.8 · 150.4 | 둘째 · 넷째 +20 = 이동 링크 `.ln-go` 44(L2b 26 · 이 레인 변경 아님 · 이 장면에 묘비 없음) |
| 같음 | 820 · 1024 | 65.6 · 88.8 · 43 · 88.8 | 같음 | 65.6 · 68.8 · 43 · 68.8 | 같음 |
| 프로젝트 상세 표 행(8) | 390 · 820 | 61 × 8 | 84.5 · 61.8 · 61 · 84.5 · 61 · 84.5 × 3 | 38.8 · 41 · 38.8 × 6 | 접힘 차이 = 「소속 해제」 44(L2b 32 · 이 레인 변경 아님 · 「승인 전」 단추 44 는 같은 행 안). 펼침 +23.5 = 설명 글 한 줄 |
| 같음 | 1024 | 61 × 8 | 84.5 · 61 · 61 · 84.5 · 61 · 84.5 × 3 | 같음 | 같음 |
| 계정 관리 표 행(5) | 390 | 169 × 5 | 같음 | 169 × 5 | 640px 이하 규칙으로 두 입력 같은 높이(동작 단추 줄바꿈) |
| 같음 | 820 · 1024 | 65 · 65.8 · 65.8 · 88.2 · 65.8 | 같음 | 61 × 5 | +4 = 동작 단추 토큰 `--control-height` 40 → 44(기존). 둘째 · 셋째 +0.8 · 넷째 +27.2 = 이름 · 연구실 · 긴 이메일이 말줄임 대신 2–3줄(자리 10 의도) |
| 계정 표 틀 `.account-table-scroll` | 820 · 1024 | 393.9 | 같음 | 363.4(0–348.4) | 마우스 가로 스크롤 막대 15 · 행 합 차이 |

- 스크린샷 판독(390 · 820 · 1024 터치 펼침 · 4장면): 자손이 행 · 칸 · 막대 밖으로 삐져나와 보이는 곳 0 · 펼침 글은 라벨 바로 뒤(목록 칸 아래 줄 · 상세 머리는 배지 옆 · 계보는 노드 아래). 첫 판독에서 목록 칸 펼침 글이 한 글자 폭으로 눌린 것을 찾아 고쳤다(§2 추가 RED).
- 판정: 모든 차이가 ⑴ 누름 칸 21–25 → 44, ⑵ 기존 토큰 40 → 44, ⑶ 마우스 가로 스크롤 막대 15, ⑷ spec 이 정한 설명 글 줄(우려 10ⓐ · 부록 C 8 · 9 · 10) 가운데 하나로 설명된다. 판정 요청 0.

## 7. 원한 결과 대조 · 이탈 · 남은 것

- 충족(V9): 터치에서 부록 C 10곳의 `title` 전용 정보가 보이는 글자이거나 누르면 보인다(vitest 10곳 각각 · 목록 길이 먼저) · 마우스 요소 · `title` 불변(1440 픽셀 0) · 새 단추 터치 44 · 문구 원문 일치 · 설명 글 대비 ≥ 4.5(두 테마) · `title` 전수 25 파일별 불변.
- 이탈 · 초과:
  - `catalog.css` 는 바꾸지 않았다(부록 I 가 허용한 파일 · 필요 없음 — 펼침 글 규칙은 부품 CSS 한 곳).
  - 줄바꿈(9 · 10)은 CSS 입력 조건이 아니라 **입력 방식 훅이 다는 표지 클래스**로 했다 — `title` 조건과 같은 판별 한 곳을 쓰고, L2b 의 「파일 끝 터치 블록 1 · 선택자 집합」 단언을 건드리지 않는다. 마우스에는 표지가 없어 규칙이 맞는 요소 0.
  - 새 단추에 최소 가로 44 도 둔다(spec 은 최소 높이 · 390 의 「외 1」 칩 가로가 44 미만이라 목록 밖 작은 누름 칸을 만들지 않으려고).
  - 목록 · 프로젝트 「승인 전」 칩은 터치에서 단추 안에 들어가며 칩의 `aria-disabled="true"` 는 원래대로 둔다(일반 요소라 단추 동작에 영향 없음 — 실기기 낭독 확인 후보).
  - 열 메뉴가 열린 채 설명 단추를 누르면 메뉴가 닫히지 않는다(다른 행 단추와 같은 `stopPropagation` 꼴).
- 남은 것 · 후속:
  - 5 · 8 은 audit 장면에 그 상태가 없어 캡처 수치 · 1440 비교 밖이다(vitest 만). 어느 게이트에도 캡처로는 걸리지 않는다 — E 확인 또는 픽스처 후보.
  - 부록 J 실기기 확인 후보: 터치에서 설명 단추를 누를 때 행 이동이 일어나지 않는지 · 계보 원천 노드 탭 펼침 · 낭독기가 펼침 상태를 읽는지.

## 8. 캡처 폴더(추적 제외 · `frontend/.visual/`)

- `dwi0926-l3a-390` · `dwi0926-l3a-vert` · `dwi0926-l3a-shot390` · `dwi0926-l3a-cap` · `dwi0926-l3a-diff-1440` · 판정 출력 `dwi0926-l3a-judge-390-{L2b,L2a,L3a}.json` · 일회용 래퍼 `l3a_boxes.py` · `l3a_vert_table.py`.
