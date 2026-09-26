# 레인 보고 — L2b-2 화면 CSS 2/2(대시보드 · 프로젝트 · 구성원 · 변수 표 · 업로드 · 로그인)

- spec: `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md` 「레인 확정」(L2b 분할 · 세로 넘침 대조 · 파일 끝 터치 블록 · `frontend-visual` 임시 규칙) · 부록 I 「L2b」 행 · V7 · V8 · V10 · 부록 B(레인 L2b 중 6파일 21항목) · 부록 D(4파일 10규칙) · 부록 G(프로젝트 2 · 로그인 1)
- intent: `dev-package/intent/2026-09-26-device-width-input-rules.md`
- 브랜치: `claude/dwi-l2b2` · 기준 `7ec1aa51` · 구현 커밋 `44cfebe6`
- task: `e0781bfd85cd4ed6837a8c17dcc01fd4`(범위 선언 11경로 · 게이트 `frontend-test` · `frontend-design-lint` · `frontend-visual`)
- 판정: **구현 · 게이트 · 수치 완료 · 판정 요청 1건(§8-1 기간 달력 날짜 칸 가로 44 가 두 달 달력을 넘침).** 시험 RED 51 실패 → GREEN · 전체 150파일 2140건 통과 · 게이트 green 3 / red(판정) 0 / red(준비) 0 · 페이지 14 = 선언 URL 14 · 390 레인 L2b 판정 red 86 → 0(25장면) · 터치 5크기 레인 L2b red 0(`upload-link` 39–42 포함) · 1440 마우스 대 B0 픽셀 0.

## 1. 바뀐 것

| 파일 | 변경 |
|---|---|
| `frontend/src/components/dashboard/dashboard.css` | hover 1규칙 한 줄 감싸기 · 파일 끝 `(pointer: coarse)` 블록(8–12) |
| `frontend/src/components/project/project.css` | 640px 블록의 `.pj-inp, .pj-tarea { font-size: 16px; }` 규칙 삭제(블록의 나머지 3규칙 유지) · 640px 블록의 `.pj-ctl select` 에서 `font-size: 16px` 선언만 삭제(`width: 100%` 유지) · 파일 끝 터치 블록(31–34) · hover 규칙 없음 |
| `frontend/src/components/members/members.css` | 파일 끝 터치 블록(35) · hover 규칙 없음 |
| `frontend/src/components/common/variableTable.css` | hover 2규칙(여러 줄) 블록 감싸기 · 파일 끝 터치 블록(43 · 44) |
| `frontend/src/components/upload/upload.css` | hover 6규칙 한 줄 감싸기 · 파일 끝 터치 블록(39–42 · 47–49) · 720px 블록 6개 변경 0 |
| `frontend/src/auth/login.css` | hover 1규칙(여러 줄) 블록 감싸기 · 한 규칙뿐인 640px 블록 `.login-input { font-size: 16px; }` 블록째 삭제 · 파일 끝 터치 블록(37 · 38) |
| `frontend/test/design-fix-20260924-F-css.test.ts` | 업로드 hover 쌍 3개(× 2테마)의 비교 대상 매체 자리 5번째 원소 `'@media (hover: hover)'`(Q3ⓑ · 기대 값 · 개수 불변 · 삭제 0) |
| `frontend/test/design-fix-20260924-L2.test.tsx` | `#10 .btn-strong:hover` 의 `bodyOf` 자리 인자 `'hover'` · 자리 종류에 `'hover'`(= `@media (hover: hover)` 하나 안) 1줄 추가 — 이 파일은 매체 문자열 인자 대신 자리 열거형을 쓴다 |
| `frontend/test/design-fix-followups-20260925-L2.test.tsx` | 격자 칸 hover(`:146`)의 `body()` 매체 인자 `'@media (hover: hover)'` |
| `frontend/test/device-width-input-20260926-L2b.test.ts` | spec 총합으로 올림(아래 §2) · 「부분합」 표기 0 · `L2B2` 목록 삭제(`TAPS` 로 옮김) |

- 착수 때 hover · 높이 고정 시험 grep(`test/*.test.*` 에서 `:hover` · 6파일 대상 선택자의 크기 선언): 지시된 3자리 외 고정 0. `design-fix-20260924-F-final.test.ts:55`–`64`(`.btn-strong` hover)는 파서가 `@media` 안으로 들어가 수정 없이 green. `account-admin-layout-20260918.test.ts` 의 640px 블록 읽기는 첫 640px 블록(계정 표)을 읽어 로그인 하한 블록 삭제와 무관. GREEN 뒤 전체 2140건 통과로 추가 고정 없음 확인.
- 셸 · 기본 · 프리미티브 · 토큰 CSS 변경 0 · L2b-1 파일 변경 0 · TSX 변경 0 · `!important` 추가 0 · 새 16px 하한 0.

## 2. 시험 RED → GREEN

- RED(시험만 · CSS 변경 0 · `7ec1aa51` 위): `Tests 51 failed | 150 passed (201)`(4파일). 실패 = L2b 시험 43 ＋ F-css 업로드 쌍 6 ＋ L2 `#10` 1 ＋ 후속 L2 격자 칸 1. 실패 예: `선택자 블록 수: .dr-cal-d:hover @media (hover: hover): expected +0 to be 1` · `expected [] to have length ... coarse`. **감싸기 전 green 인 hover 고정 0**(정지 조건 해당 없음).
- 처음부터 통과한 새 사례: 720px 블록 불변 · `.dropzone .big` 기본 크기 · `!important` 0 등 현재 상태가 이미 맞는 가드.
- GREEN(`44cfebe6`): 4파일 `201 passed` · 전체 `Test Files 150 passed · Tests 2140 passed`.
- L2b 시험 총합 단언: hover 24(12파일 파일별 `[8, 1, 2, 2, 0, 1, 1, 0, 0, 2, 6, 1]`) · 선택자 24 · 12파일 `:hover` 전부 `(hover: hover)` 안 · 44 대상 34(= `targets.json` 레인 L2b 34 번호 일치 · 캡처 사각 7 · 가로만 2 · 행 1) · 12파일 `@media` 16px 하한 0 · 터치 블록 11파일 각 1 · 파일 끝.
- 새 단언: 부록 G 3곳 블록 잔여 규칙 대조 · 640px 규칙 공유 선택자 3개(`.dash-bar` · `.pj-seg button` · `.dr-cal-d`)의 640px 원문 선언 불변 · 터치 규칙이 뒤 순서 · 업로드 720px 규칙 7(블록 6) 원문 불변 · 구성원 · 변수 표 터치 블록 = 35 · 43 · 44 선택자뿐(체크 칸 · 대표 라디오 · `label` · `input` 선택자 0) · 42 규칙은 업로드 CSS 에만.
- L3b 확장 방법은 시험 머리 주석에 적었다(`TAPS` 에 36 · 45 추가 · `L3B_ONLY` 기대값 갱신 · 블록 = 1 · 파일 끝 단언 유지).

## 3. hover 감싸기(부록 D 레인 L2b 중 4파일 10규칙 · spec 총합 24)

| 파일 | 규칙 | 형태 |
|---|---|---|
| `dashboard.css` 1 | `.dash-open-catalog:hover` | 한 줄 원문 같은 줄 감싸기 |
| `upload.css` 6 | `.btn-strong:where(:not(:disabled)):hover` · `.thumbrow .th-slot:where(:not(:disabled)):hover` · `.dr-field:hover` · `.dr-nav button:hover` · `.dr-cal-d:hover` · `.dr-useg button:hover` | 한 줄 원문 같은 줄 감싸기(압축 표기 원문 그대로) |
| `variableTable.css` 2 | `.vt-del:hover` · `.vt-add:hover` | 여러 줄 원문 → L2a 선례(셸 CSS)대로 블록 안 들여 쓰기 |
| `login.css` 1 | `.login-submit:hover:not(:disabled)` | 같음 |

- 모두 제자리(층 · 순서 · 명시도 불변). hover 와 초점을 한 규칙에 가진 것 0. 프로젝트 · 구성원 CSS 에는 hover 규칙이 없다.

## 4. 16px 하한 삭제(부록 G 레인 L2b 중 3곳 · advisor ① 1)

- `project.css` 640px 블록(`.pj-modal-back` · `.pj-modal` · `.pj-inp, .pj-tarea` · `.pj-cards`)에서 `.pj-inp, .pj-tarea` 규칙만 삭제 — 블록 유지.
- `project.css` 뒤 640px 블록의 `.pj-ctl select { width: 100%; font-size: 16px; }` → `{ width: 100%; }`.
- `login.css` 끝 640px 블록(규칙 1개) 블록째 삭제.
- `upload.css` `.dropzone .big { font-size: 16px }` 는 조건 없는 기본 크기(부록 G 계수 제외) — 손대지 않음 · 시험 고정. 12파일 `@media` 안 하한 0(시험).
- 390 16 red 0 이 셸 블록(`(max-width: 640px), (pointer: coarse)`)으로 유지: 390 수치 전용 25장면 × 2테마 16 red 0 · 5 터치 크기 13장면 16 red 0(§7).

## 5. 터치 44(부록 B 레인 L2b 중 21항목 · 각 파일 끝 `(pointer: coarse)` 블록)

| # | 블록 안 선택자 · 선언 | 근거 |
|---|---|---|
| 8 | `.dash-section-label` min-height · min-width | 기본 최소 32 |
| 9 | `.dash-quiet` 같음 | 기본 최소 32 |
| 10 | `.dash-bar` 같음 | 640px 규칙(`min-height: 44px` · 열 틀)과 같은 선택자 · 뒤 순서 · 640px 규칙 원문 유지(시험) |
| 11 | `.titem button` 같음 | 기본 최소 36 |
| 12 | `.todo-more, .todo-all` 같음 | 기본 최소 36 · 단추(글자 크기 불변) |
| 31 | `.pj-views button` **min-width 만** | 세로는 기본 `min-height: var(--control-height)` 로 이미 44(advisor ① 3) |
| 32 | `.pd-sect .quiet, td.right .quiet` min-height · min-width | 단추 · 글자 크기 불변 |
| 33 | `.pd-linkurl` inline-flex · 가운데 · min-height · min-width | 글자 링크(글자 크기 불변 · 기존 `word-break: break-all` 로 줄바꿈 유지) |
| 34 | `.pj-seg button` min-height · min-width | 640px 규칙(`min-height: 44px`)과 같은 선택자 · 뒤 순서(시험) |
| 35 | `.settabs .st` min-height · min-width | 고정 `height: 36px` 를 min-height 44 가 이김 |
| 37 | `.login-input` min-height · min-width | 기본에 이미 `min-height: var(--control-height)` — 규칙은 spec 「대상마다」 대로 둠(수치 변화 0) |
| 38 | `.login-submit` 같음 | 같음 |
| 39 | `.regsteps .rs-x` min-height · min-width | 「×」 19.3×21 → 44×44 |
| 40 | `.up-preview-options > summary` 같음 | 펼침 제목 · display 불변(표식 ▶ 유지 · L1 `.pv-pick-values summary` 선례) |
| 41 | `.up-file-management > summary` 같음 | 같음 |
| 42 | `.mapbar .btn-ghost` **min-width 만** | 세로는 `.btn-sm` 터치 토큰으로 44 · 업로드 CSS 터치 블록에 둠 · 셸 CSS 변경 0(advisor ① 3) |
| 43 | `.vt-del` min-height · min-width | 고정 `height: 32px` 를 min-height 44 가 이김 |
| 44 | `.vt-add` 같음 | |
| 47 | `.dr-nav button`(캡처 사각) 같음 | 28×28 |
| 48 | `.dr-useg button`(캡처 사각) 같음 | 최소 가로 40 · 높이 28 |
| 49 | `.dr-cal-d`(캡처 사각) 같음 | 640px 규칙(`.dr-cal-d { height: 44px; }` · upload.css 끝 640px 블록)과 같은 선택자 · 명시도 같음 · 터치 블록이 뒤(시험). 두 규칙은 다른 속성이라 390 터치에서 둘 다 적용(높이 44) · **가로 44 는 §8-1 판정 요청** |

- 구성원 · 변수 표 터치 블록 = 35 · 43 · 44 선택자뿐(체크 칸 36 · 대표 라디오 45 는 L3b · 시험 고정 · advisor ① 5).
- 캡처 사각 47–49: 시험이 터치 블록 안 규칙 존재 · 선언을 단언. 실제 상자는 §7-3 일회용 측정으로 확인.
- 업로드 720px 블록(`:219` · `:224` · `:232` · `:300` · `:629` · `:661`)은 이동 · 변경 0(advisor ① 2 · 시험 고정) · `:219`/`:658` 모순은 범위 밖.

## 6. 게이트(task 실행 · 호스트 단독)

- 실행: `gates/run.sh task`(선언 게이트 3개 한 번) · `COLAB_TEST_ENV_FILE=~/.colab-v2-test-32.env` · `COLAB_TASK_ID=<task>` · `COLAB_VISUAL_URLS` = 이 레인이 띄운 audit 빌드(`vite preview --config audit.vite.config.ts --host 127.0.0.1 --port 47462 --strictPort` · 시작 때 PID 저장 · 그 PID 만 종료)의 14건: `audit-design.html?scene=<장면>&design=full`(`catalog` · `search` · `search-down` · `detail` · `lab` · `projects` · `project-detail` · `project-dialog` · `settings` · `members` · `account-admin` · `login` · `lineage-picker`) ＋ 업로드 입구 `audit-upload.html?upload=1&labSettings=0&operator=0`. `COLAB_VISUAL_EXEMPT` 미사용.

| 게이트 | 결과(`44cfebe6` 트리) |
|---|---|
| `frontend-test` | green — 2140 통과 · 실패 0 |
| `frontend-design-lint` | green — 파일 21 · a–h 0 · 문서 표 갈림 0 |
| `frontend-visual` | green — **페이지 14(= 선언 URL 14)** · 13px 미만 0 · 대비 < 4.5 0 · 스크린샷 28 |
| 계 | green 3 / red(판정) 0 / red(준비) 0 |

- 이 보고서 커밋 뒤 같은 명령으로 한 번 더 돌려 인계한다(최종 gate-summary 절대경로와 3계수는 인계 메시지).

## 7. 수치(직렬 실행 · 자기 캡처 · audit 빌드 = `44cfebe6` 트리)

### 7-1. 390 터치 수치 전용 · 레인 L2b 판정

- 실행: `capture.py --label dwi0926-l2b2-390 --metrics-only --skip-build --scene <장면> --viewport 390`(L2b-1 과 같은 25장면 × 2테마 · 50파일 · 모두 종료 0).
- 판정(`judge.mjs --lane L2b`): `files=50 lane=L2b red=0 readiness=0 notMeasured=118 captureBlind=7 exemptHits=0 smallOther=16 outsideRed=16:0,44:32,넘침:0,가림:0 exit=0`. **red 86(L2b-1 보고 7-1) → 0.**
- L2b-2 대상 390 최솟값(가로×세로 · 두 테마): 8 358×44 · 9 89.1×44 · 10 316×44 · 11 84.2×44 · 12 65.3×44 · 31 44×44 · 32 48.2×44 · 33 273.2×44 · 34 64.2×44 · 35 93.8×44 · 37 258×44 · 38 284×44 · 39 44×44 · 40 324×44 · 41 358×44 · 42 44×44 · 43 44×44 · 44 81.6×44. L2b-1 대상 최솟값은 L2b-1 보고와 같다.
- 「재지 않음」(notMeasured 118 · 대상별 사유): 3 · 4(L2a · 폭 숨김 · 42 · 40) · 50 · 51 · 53(회귀 감시 · 닫힌 메뉴 · 숨은 자리 · 24) · **37 · 38(12)** = `account-admin` 의 계정 만들기 양식(`[data-testid=account-create] form.account-form` 의 입력 5 · 제출 1 × 2테마)이 닫힌 탭이라 상자 없음. 37 · 38 은 `login` · `account-admin` 표 위 입력에서 상자 있게 재짐(위 최솟값). 캡처 사각 7(15–17 · 28 · 47–49)은 맞는 요소 없음.

### 7-2. 터치 5크기 ＋ 1440(13장면 캡처 · 수치 모드)

- 실행: `capture.py --label dwi0926-l2b2-cap --skip-build --parallel 2 --metrics --only lab,projects,project-detail,project-dialog,settings,members,account-admin,login,upload,upload-classify,upload-metadata,upload-link,upload-preview-expand`(종료 0 · 156장).
- 판정(`judge.mjs --lane L2b`): `files=156 red=0 readiness=1 notMeasured=298 captureBlind=7 … outsideRed=16:0,44:130,넘침:0,가림:0 exit=78` — 78 은 이 13장면에 L2b-1 대상 장면이 없어 13 · 14 · 18 · 19 · 24–27 이 재지지 않은 것(기대 · L2b-1 7-2 와 대칭 · 7-1 이 전 장면으로 판정). 레인 밖 44 red 130 은 다른 레인 대상과 1440 마우스 파일(개수만).
- **레인 L2b 대상 red: 390 · 844x390 · 820 · 1024 · 1180 모두 0.** `upload-link` 39–42(L2b-1 보고의 red 40)는 5크기 모두 0: 39 44×44 · 40 가로 324–746 × 44 · 41 가로 358–780 × 44 · 42 44×44. 16 red 0 · 넘침 red 0.

### 7-3. 세로 넘침 대조(「레인 확정」 · advisor ① 6)

- 방법: 수치 전용 실행기의 측정 직후 같은 세션에서 컨테이너 상자와 자손 상자의 세로 범위(컨테이너 위 기준 · 괄호)를 읽는 일회용 래퍼(`frontend/.visual/` · 커밋 안 함 · 실행기 코드 변경 0 · 창 크기 · 입력 상태 확인 78 을 그대로 거침). 마우스 = 같은 폭 `WxH:mouse`. 라이트. 11장면 × 터치 3크기 ＋ 마우스 3크기 = 66실행 모두 종료 0.

| 장면 · 컨테이너 | 폭 | 터치 높이(자손 범위) | 같은 폭 마우스 | 차이 | 설명 |
|---|---|---|---|---:|---|
| `upload-*` 등록 단계 줄 `.regsteps` | 390 | 111(0–106) | 88(0–83) | +23 | 파일 이름 칩 `.rs-f` 33 → 56 = 「×」 `.rs-x` 21 → 44 |
| 같음 | 820 · 1024 | 57(0–56) | 48(0.5–46.5) | +9 | 같음(줄 최소 48 안에서 칩 56) |
| 파일 이름 칩 `.regsteps .rs-f` | 3크기 | 56(6–50) | 33(6–27) | +23 | 「×」 21 → 44 · 칩 위아래 여백 6 그대로 |
| `lab` 지도 막대 `.dash-bar` | 820 · 1024 | 44(14–30) | 40(12–28) | +4 | 막대 40 → 44 · 390 은 640px 규칙으로 두 입력 44 |
| `lab` 막대 목록 `.dash-bars` | 820 · 1024 | 200.1 / 88 | 184.1 / 80 | +16 / +8 | 막대 4 · 2개 × 4 |
| `lab` 카드 머리 `.dash-card-head`(「전체 목록 보기」) | 3크기 | 44(0–44) | 32(0–32) | +12 | `.dash-quiet` 32 → 44 |
| `lab` 구역 라벨 `.dash-section-label` | 3크기 | 44(12–31) | 32(6–25) | +12 | 32 → 44 · 글자 가운데 |
| `lab` 할 일 줄 `.titem` | 3크기 | 78.2(14–63.2) | 78.2 | 0 | 줄 높이가 이미 44 초과 |
| `projects` 보기 전환 `.pj-views` | 820 · 1024 | 44 | 40 | +4 | 토큰 `--control-height`(40 → 44 · 기존 · 이 레인 변경은 가로만) |
| `project-dialog` 구분 단추 줄 `.pj-seg` | 820 · 1024 | 54(5–49) | 46(5–41) | +8 | 36 → 44 · 390 은 640px 규칙으로 두 입력 54 |
| `project-dialog` 대화상자 `.pj-modal` | 820 · 1024 | 983.3(1–982.3) | 962.8(1–961.8) | +20.5 | `.pj-seg` +8 ＋ 입력 · 선택 토큰 40 → 44(기존) · 자손 범위 상자 안 |
| `project-detail` 구역 머리 `.pd-sect`(「정보 수정」 · 「프로젝트 닫기」) | 3크기 | 44(0–44) | 22.4(0–22.4) | +21.6 | 조용한 단추 20.8 → 44 |
| `project-detail` 소속 데이터셋 표 행 | 3크기 | 61(0–61) | 38.8 · 41 | +22.2 / +20 | 「소속 해제」 20.8 → 44 |
| `project-detail` 연결 주소 `.pd-linkurl` | 3크기 | 44 | 15 | +29 | 링크 15 → 44(글자 13 그대로) |
| `settings` · `account-admin` 탭 줄 `.settabs` | 3크기 | 44(0–44) | 36(0–36) | +8 | 탭 36 → 44 |
| `members` 구성원 표 행 | 3크기 | 274.5 / 61.5 | 같음 | 0 | 체크 칸은 L3b · 이 장면에 탭 줄 없음 |
| `account-admin` 입력 라벨 `.login-label` | 820 · 1024 | 70.8(26.8–70.8) | 66.8 | +4 | 토큰 40 → 44(기존) |
| `login` 카드 | 820 · 1024 | 418.8(33–385.8) | 406.8 | +12 | 입력 2 · 제출 1 토큰 40 → 44(기존) |
| `upload-metadata` 변수 표 행 | 820 · 1024 | 44.5 | 40.5 | +4 | `.vt-del` 32 → 44 · 행 안 |
| `upload-metadata` 행 추가 `.vt-add` | 3크기 | 44 | 30.8 | +13.2 | 30.8 → 44 |
| `upload-*` 지도 머리 `.mapbar` | 820 · 1024 | 69(12–56) | 54(12–41) | +15 | 확장보기 단추 `.btn-sm` 터치 토큰 44(기존 · 이 레인은 가로만) · 390 은 두 입력 69 |
| `upload-*` 미리보기 설정 접기 `.up-preview-options` | 3크기 | 57(13–129) | 33.8(13–105.8) | +23.2 | 펼침 제목 20.8 → 44. 자손 범위 아래 끝이 상자 밖인 것은 **닫힌 접기 속 내용**이 상자를 가진 채 재진 것으로 마우스도 같은 모양(넘침 폭 72 · 두 입력 같음) |
| `upload-*` 파일 관리 접기 `.up-file-management` | 3크기 | 44 | 28.8 | +15.2 | 펼침 제목 28.8 → 44 · 닫힌 접기 속 내용 모양은 위와 같음(두 입력 같은 꼴) |

- 스크린샷 판독(390 · 820 · 1024 터치 · `upload-classify` · `upload-link` · `project-detail` · `lab`): 자손이 막대 · 행 · 칸 밖으로 삐져나와 보이는 곳 0. 파일 이름 칩은 「×」 44 때문에 두꺼워 보인다(대상 크기 그대로의 결과).
- 판정: 모든 차이가 대상 누름 칸의 「기존 높이 → 44」 또는 기존 터치 토큰(`--control-height` 40 → 44 · 이 레인 변경 아님)으로 설명된다. 멈춤 없음 — 단 캡처 사각 달력은 §8-1.

### 7-4. 캡처 사각 기간 달력(47–49 · 일회용 측정 · `upload-metadata` 에서 기간 칸을 눌러 연 뒤)

| 폭 · 입력 | 달력 틀 | 달 수 · 달 폭 | 날짜 칸(49) | 날짜 칸 오른쪽 끝(틀 왼쪽 기준) | 틀 scrollWidth / clientWidth | 월 이동(47) | 단위 단추(48) 오른쪽 끝 |
|---|---|---|---|---|---|---|---|
| 390 터치 | 366 | 1 · 332 | 47.4×44 | 349 | 364 / 364 | 44×44 | 340 |
| 390 마우스 | 366 | 1 · 332 | 47.4×44 | 349 | 364 / 364 | 28×28 | 316 |
| 700 터치 | 308 | 1 · 274 | **44×44** | **325** | **324 / 306** | 44×44 | **340** |
| 700 마우스 | 308 | 1 · 274 | 39.1 | 291 | 306 / 306 | 28×28 | 316 |
| 820 · 1024 터치 | 576 | 2 · 261 | **44×44** | **606** | **605 / 574** | 44×44 | 340 |
| 820 · 1024 마우스 | 576 | 2 · 261 | 37.3×32 | 559 | 574 / 574 | 28×28 | 316 |

## 8. 원한 결과 대조 · 판정 요청 · 이탈 · 남은 것

### 8-1. 판정 요청(spec 과 실물 충돌 · 고치지 않고 멈춤)

- **49 `.dr-cal-d` 최소 가로 44 가 641px 이상 터치에서 달력 날짜 격자를 달력 틀 밖으로 밀어낸다.** 7열 격자(`repeat(7, 1fr)`)의 한 칸은 달 폭 / 7 = 37.3(두 달 · 761px 이상) · 39.1(한 달 308 틀 · 641–760)이고, 최소 가로 44 가 열 최소를 44 로 올려 격자가 308 이 된다. 실측: 820 · 1024 터치에서 날짜 칸 오른쪽 끝 606 대 틀 안쪽 오른쪽 559(두 번째 달이 틀 밖으로 약 47 · 첫 달은 사이 간격 20 과 둘째 달 앞을 덮음) · 700 터치에서 325 대 291. 390 은 한 칸 47.4 라 문제 없음. 캡처 사각이라 판정 스크립트 · 게이트는 이를 못 잡는다(측정은 §7-4 일회용).
- spec 부록 B 「1–49 번은 최소 높이와 최소 가로를 함께 44」 대로 두었다(브랜치 현재 상태). 고르는 안(레인이 정하지 않음):
  - ⓐ 49 는 최소 높이만 44 · 가로는 격자가 정함(390 은 47.4 로 44 이상 · 641px 이상 터치에서 37.3 · 39.1 로 가로 red — 캡처 사각이라 판정에는 안 잡힘 · 시험의 49 기대를 「세로만」으로 바꿈).
  - ⓑ spec 그대로(현재) — 641px 이상 터치에서 달력이 틀 밖으로 넘침.
  - ⓒ 달력 틀 폭 · 달 수를 터치에서 바꿈 — 배치 변경이라 이 레인 범위 밖(다음 intent · 업로드 720 · 760px 블록 정리와 함께).
- 곁가지(같은 달력 · 기존 결함): 641–760 폭의 308 틀에서 단위 단추 줄(48)은 **마우스에서도** 오른쪽 끝 316 으로 틀(308) 밖이고 터치 44 로 340 이 된다(+24). 기존 넘침은 이 레인이 만든 것이 아니며 어느 검사에도 걸리지 않는다(캡처 사각 · 판정 스크립트 · 게이트 밖) — 후속.

### 8-2. 원한 결과 대조(V7 화면 · V8 화면 · V10 감싸기 — spec 총합)

- 충족: hover 24규칙 모두 조건 안 · 조건 밖 0 · 화면 `@media` 16px 하한 0(12파일) · 새 하한 · `!important` 0 · 44 대상 34 CSS 규칙(캡처 사각 7 은 규칙 존재 단언) · 390 25장면 레인 L2b red 0 · 터치 5크기 레인 L2b red 0 · 16 red 0 · 넘침 red 0 · 1440 마우스 픽셀 0 · 게이트 페이지 14.
- 미달: 49 가로의 판정 대기(§8-1).
- 초과: 37 · 38 터치 규칙은 기본 토큰 규칙과 같은 값이라 수치 변화 0(spec 「대상마다 블록에 둔다」 대로 둔 것) · 업로드 720px 블록 불변 가드 시험 1 · `.dropzone .big` 가드 시험 1 · `design-fix-20260924-L2.test.tsx` 자리 종류 `'hover'` 1줄.

### 8-3. 1440 마우스 대 B0

- `diff.mjs --subset --viewport 1440 <B0> dwi0926-l2b2-cap <보고>` → **26장(13장면 × 2테마) · red 0 · 엄격 픽셀 0 · 종료 0**. B0 폴더: 워크트리 `agent-abf926c2ed31f5520` 의 `frontend/.visual/dwi0926-base`(읽기만).

### 8-4. L3a · L3b 에 넘길 것

- L3b: `members.css` · `variableTable.css` 끝에 터치 블록이 하나씩 있다. 체크 칸(36) · 대표 라디오(45) 규칙은 그 블록 **안**에 넣고, L2b 시험의 `TAPS` 에 36 · 45 를 더하고 `L3B_ONLY` 시험의 기대값을 L3b 선택자로 갱신한다(단언 삭제 0 · 시험 머리 주석).
- L3a: `login.css` 는 파일 끝이 터치 블록이다. 줄바꿈 규칙은 그 블록 앞에 넣거나, L2b 시험 「파일 끝 블록」 단언을 갱신한다(「레인 확정」 규칙).
- 관찰(이 레인 파일 밖 · 판정 대상 아님): `lab` 1024 터치 캡처에서 맨 위 메뉴 글자(「연구실」 · 「프로젝트」 · 「데이터셋」)가 두 줄로 감긴다. B0(`dwi0926-base` `lab-light-1024`)에도 같은 감김이 있어 이 레인 변경과 무관하다. 어느 검사에도 걸리지 않는다(판정 스크립트는 글자 감김을 재지 않음) — E 확인 후보.

### 8-5. 캡처 폴더(추적 제외 · `frontend/.visual/`)

- `dwi0926-l2b2-390` · `dwi0926-l2b2-cap` · `dwi0926-l2b2-diff-1440` · `dwi0926-l2b2-boxes-touch` · `dwi0926-l2b2-boxes-mouse` · `dwi0926-l2b2-cal700` · `dwi0926-l2b2-cal700t` · 판정 출력 `dwi0926-l2b2-judge-390.json` · `dwi0926-l2b2-judge-cap.json` · 일회용 래퍼 `l2b2_boxes.py`.

### 8-6. 오케스트레이터 결정 49 ⓐ(§8-1 판정 · Ted 번복 가능)

- 결정: 49 `.dr-cal-d` 는 터치 블록에서 **최소 높이만 44** · 최소 가로 없음. 가로는 7열 격자가 정한다. 완료 보고에는 「spec 미달 1(49 가로 · 641+ 터치)」로 올린다. 달력 틀의 터치 배치는 다음 intent(배치 정리).
- task: `afd4bc22647647f4b6c5c8463f768819`(범위 3경로 · 게이트 3개) · 기준 `a9003279`.
- 시험(RED → GREEN): L2b 시험의 49 를 `tall`(세로만)로 표시 · 기대 `['min-height: var(--control-height)']` · 「세로만 목록 = [49]」 단언 추가 · 캡처 사각 목록 유지 · 단언 삭제 0. RED `Tests 1 failed | 81 passed (82)`(`expected [ …(2) ] to deeply equal [ 'min-height: var(--control-height)' ]`) → GREEN 전체 `150 passed · 2140 passed`.
- CSS: `upload.css` 터치 블록 `.dr-cal-d { min-height: var(--control-height); }`(min-width 삭제) · 블록 머리 주석에 결정 근거 한 줄.

| 폭 · 입력 | 달력 틀 · 달 수 | 날짜 칸 전(§7-4 · 가로 44) | 날짜 칸 후(ⓐ) | 마지막 날짜 칸 오른쪽 끝 전 → 후 | 달 안쪽 오른쪽 끝 | 틀 scrollWidth / clientWidth 전 → 후 |
|---|---|---|---|---|---|---|
| 390 터치 | 366 · 1 | 47.4×44 | 47.4×44 | 349 → 349 | 349 | 364/364 → 364/364 |
| 700 터치 | 308 · 1 | 44×44 | 39.1×44 | 325 → **291** | 291 | 324/306 → **306/306** |
| 820 터치 | 576 · 2 | 44×44 | 37.3×44 | 606 → **559** | 559 | 605/574 → **574/574** |
| 1024 터치 | 576 · 2 | 44×44 | 37.3×44 | 606 → **559** | 559 | 605/574 → **574/574** |

- 판정: 네 폭 모두 격자가 틀 안(마지막 칸 오른쪽 끝 ≤ 달 안쪽 오른쪽 끝 · scrollWidth = clientWidth) · 날짜 칸 높이 44. 월 이동(47) 44×44 · 단위 단추(48) 44×44 그대로.
- 재측정 방법: §7-4 와 같은 일회용 래퍼(커밋 안 함) · 라이트 · `upload-metadata` 에서 기간 칸을 눌러 연 뒤.
- 다시 잰 수치(audit 빌드 = 이 커밋 트리):
  - 390 수치 전용 25장면 × 2테마 레인 L2b 판정: `files=50 lane=L2b red=0 readiness=0 notMeasured=118 captureBlind=7 … outsideRed=16:0,44:32,넘침:0,가림:0 exit=0`.
  - 1440 마우스 대 B0: 13장면 캡처(`dwi0926-l2b2-cap49a`) `diff.mjs --subset --viewport 1440` → 26장 · red 0 · 엄격 픽셀 0 · 종료 0.
  - 게이트는 이 보고 커밋 뒤 같은 14 URL 로 돌린다(인계 메시지에 3계수 · 절대경로 · 페이지 수).
- 다음 intent(배치 정리)로 넘기는 것:
  - 기간 달력 터치 폭 · 달 수(641px 이상 터치에서 날짜 칸 37.3 · 39.1 — 가로 44 미달 · 캡처 사각이라 판정 · 게이트 밖).
  - 48 단위 단추 줄 넘침(641–760 · 틀 308): 마우스 오른쪽 끝 316 > 308 · 터치 340(이 레인 전부터 · 어느 검사에도 안 걸림).
  - 1024 터치 맨 위 메뉴 글자 두 줄 감김(B0 에도 있음 · 어느 검사에도 안 걸림).
  - 업로드 `:219`(720px 이하 파일 이름 칩 숨김)와 `:658` 뒤 규칙(등록 장면 칩 `display: inline-flex`)의 모순 — 720px 블록 정리와 함께.
