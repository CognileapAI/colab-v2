# 레인 보고 — L2a 셸 · 기본 · 프리미티브 CSS(hover 감싸기 · 16px 하한 한 곳 · 터치 44)

- spec: `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md` 「레인 확정」 · 부록 I 「L2a」 행 · V7 · V8 · V10 · 구현 결정 「터치 규칙 CSS」 · 「입력 글자 하한 규칙」 · 「hover 감싸기」 · 부록 B(레인 L2a 9항목) · 부록 D(L2a 9규칙) · 부록 G(L2a 3곳) · 우려 3ⓐ
- intent: `dev-package/intent/2026-09-26-device-width-input-rules.md`
- 브랜치: `claude/dwi-l2a` · 기준 `d2a45938` · 구현 커밋 `2eecfff3` · 막대 넘침 수정 커밋 `f179edc8`
- task: 1차 `6fb372e6161044df940d8c62ca9da467`(범위 선언 7경로) · 2차(오케스트레이터 후속 지시) `0a0b607f91734999a6b0d510593b5420` · 게이트 `frontend-test` · `frontend-design-lint` · `frontend-visual`
- 판정: **L2a 완료(820 터치 막대 높이 1건은 판정 요청 · §9).** 시험 RED 50 실패 → GREEN · 전체 149파일 2058건 통과 · 게이트 green 3 / red(판정) 0 / red(준비) 0 · 페이지 6 · 390 ＋ 1024 레인 L2a 판정 red 0 · 1440 대 B0 픽셀 0.

## 1. 바뀐 것

| 파일 | 변경 |
|---|---|
| `frontend/src/shell/primitives.css` | `.btn` · `.btn-primary` hover 2규칙을 같은 줄에서 `@media (hover: hover) { … }` 로 감쌈(한 줄 원문 유지) · `:is(.inp, .sel)` 640px 16px 블록 삭제 |
| `frontend/src/shell/base.css` | 640px 입력 16px 블록 삭제 · 머리 주석 1문장 |
| `frontend/src/shell/shell.css` | hover 7규칙 제자리 감싸기 · 16px 바닥 줄을 640px 블록에서 떼어 새 블록 `@media (max-width: 640px), (pointer: coarse)` 하나로 옮김 · 파일 끝 `@media (pointer: coarse)` 블록(44 대상 9 ＋ 아바타 · 로그아웃 한 줄) · 주석 |
| `docs/design-system.md` | 프리미티브 생성 블록 재생성(`design-docs.mjs`) ＋ 손글은 층 표의 기본 층 16px 문장 1개 |
| `frontend/test/design-fix-20260924-L1.test.ts` | hover 8사례의 도우미 매체 자리 `''` → `'@media (hover: hover)'` |
| `frontend/test/design-fix-20260924-F-css.test.ts` | 프리미티브 · 셸 hover 6쌍(× 2테마)에 비교 대상 매체 자리 5번째 원소 · A2 두 줄 매체 자리 · 쌍 주석 1줄 |
| `frontend/test/device-width-input-20260926-L2a.test.ts` | 새 시험 36사례 |

`tokens.css` 변경 0. 프리미티브 `.btn-sm` 의 `(max-width: 640px), (pointer: coarse)` 블록 변경 0. 목록 · 업로드 hover 쌍(L2b) 변경 0.

## 2. 시험 RED → GREEN

- RED(시험만 · CSS 변경 0 · `d2a45938` 위): `Tests 50 failed | 94 passed (144)`. 기존 2파일 22사례(L1 8 · F-css 14 = 6쌍 × 2 ＋ 2) 전부 실패 — 도우미가 `@media` 중첩을 기록하므로 감싸기 전 green 이 아니었다(정지 조건 해당 없음). 새 파일 28사례 실패. 실패 예: `선택자 블록 수: .gnb-upload:hover @media (hover: hover): expected 0 to be 1` · `규칙 수: primitives :is(.inp, .sel): expected 2 to be 1`.
- 처음부터 통과한 새 단언 7(개수 2 · 초점 윤곽 조건 없음 · 640/900 규칙 선택자 · 터치 블록 글자 크기 0 · 기본/프리미티브 터치 단독 블록 0 · 토큰 터치 블록 선언 1).
- GREEN(`2eecfff3`): `Tests 144 passed (144)` · 전체 149파일 2057건.
- 막대 넘침 수정 시험(`f179edc8`): 새 사례 「아바타 · 로그아웃 묶음은 터치에서 한 줄」 — 수정 규칙을 빼면 `expected +0 to be 1` 로 실패, 넣으면 통과 확인. 전체 2058건.
- 기존 시험 단언 삭제 0 · 기대 값 · 개수 불변. `design-fix-followups-20260925-L1.test.ts:195–196`(hover 원문 한 줄) 수정 없이 green.

## 3. hover 감싸기 목록(부록 D 레인 L2a · 규칙 9 · 선택자 10)

| 파일 | 규칙 | 형태 |
|---|---|---|
| `shell.css` | `.detail-page .backlink:hover, .project-detail .backlink:hover` | 여러 줄 블록을 `@media (hover: hover) { … }` 안으로(들여쓰기만) |
| `shell.css` | `.mainnav a:hover` | 여러 줄 |
| `shell.css` | `.gnb-settings:hover` | 여러 줄 |
| `shell.css` | `.gnb-upload:hover` | 한 줄 감싸기 |
| `shell.css` | `.gnb-more:hover` | 여러 줄 |
| `shell.css` | `.gnb-more-item:hover` | 한 줄 |
| `shell.css` | `.gnb-logout:hover` | 여러 줄 |
| `primitives.css` | `.btn:where(:not(.btn-primary, :disabled)):hover` | 한 줄 |
| `primitives.css` | `.btn-primary:where(:not(:disabled)):hover` | 한 줄 |

- hover 와 `:focus-visible` 을 함께 가진 규칙은 이 레인 파일에 0 — 나눌 것 없음. `base.css` 초점 윤곽 규칙은 조건 없이 남음(시험 고정).
- 세 파일의 `:hover` 규칙 = 9 · 조건 밖 0(시험 고정).

## 4. 16px 하한 이동(부록 G 레인 L2a 3곳)

- `shell.css`: `body input, body select, body textarea { font-size: max(16px, 1em) !important; }` 한 줄을 640px 블록에서 떼어 바로 뒤 새 블록 `@media (max-width: 640px), (pointer: coarse)` 에 둠. 640px 블록의 나머지 규칙(노치 여백 · 아바타 · 로그아웃 · 설정/없는 페이지 여백)은 그대로.
- `base.css:17–20` 블록째 삭제 · `primitives.css:54–56` 블록째 삭제.
- 새 시험: 세 파일에서 `@media` 안 16px 하한 선언 = 1 · 매체 문자열 = `@media (max-width: 640px), (pointer: coarse)` · 그 블록 안 규칙 1.

## 5. 터치 44 목록(부록 B 레인 L2a · 셸 CSS 끝 `(pointer: coarse)` 블록 하나)

| # | 측정 선택자 | 블록 안 선택자 | 명시도 근거 |
|---|---|---|---|
| 1 | `a.brand` | `.gnb a.brand` | 경쟁 규칙 없음 · 막대 높이 안 |
| 2 | `.mainnav a` | `.gnb .mainnav a` | 900px `.gnb .mainnav a` 와 같음 · 뒤 순서 |
| 3 · 4 · 5 | `.gnb-settings` · `.gnb-upload` · `.gnb-more` | `.gnb :is(.gnb-settings, .gnb-upload, .gnb-more)` | 640px `.gnb :is(.labswitch, …)` 와 같음(0,2,0) · 뒤 순서 |
| 6 | `.gnb-logout` | `.gnb .gnb-logout` | 640px 같은 선택자 |
| 7 | `select.theme-switcher` | `.theme-switcher` | 640px 같은 선택자 |
| 21 | `.notfound a` | `.notfound a`(＋ `display: inline-flex` · `align-items: center` · 글자 크기 변경 0) | 경쟁 규칙 없음 |
| 22 | `.backlink` | `.detail-page .backlink` · `.project-detail .backlink` | 두 화면 한정(미등록 미리보기는 L1 몫) |

- 선언: `min-height: var(--control-height); min-width: var(--control-height);`. 50–53 토큰 블록 · 토큰 층 터치 블록(선언 1) 불변(시험 고정).
- 기본 · 프리미티브 CSS 에는 레인 L2a 대상이 없어 터치 블록을 두지 않음.
- 후속 수정(`f179edc8`): 같은 블록에 `.gnb .avatar-wrap { display: flex; align-items: center; white-space: nowrap; }` — §8-3.

## 6. 문서 생성 블록 재생성

- `design-docs.mjs --check`: 재생성 전 `h primitives 갈림` 1 → 재생성 뒤 갈림 0.
- 차이(프리미티브 블록만 · 토큰 블록 같음):
  - `primitives.css` sha256 `b3af7999…` → 새 값.
  - 합계 규칙 37 → 36 · 선언 125 → 124. `field` 계열 2규칙/8선언 → 1규칙/7선언(부록 G 삭제분 · 예정된 감소).
  - `.inp` · `.sel` 행에서 `:is(.inp, .sel) · (max-width: 640px)` 줄이 빠짐(예정).
  - `.btn` · `.btn-primary` 행의 hover 선택자 줄은 남고 ` · (hover: hover)` 가 붙음. btn 계열 규칙 11 · 선언 31 불변 — hover 행이 사라지지 않음(정지 조건 해당 없음).
- 손글 변경은 층 표 기본 층 칸 1문장(「640px 입력 글자 바닥」 → 바닥은 `shell.css` 의 「640px 이하 또는 터치 기기」 블록 한 곳).

## 7. 게이트(task 실행 · 호스트 단독)

- 실행: 게이트 실행기 `gates/run.sh` 의 `task`(선언 게이트 3개 한 번) · 환경 `COLAB_TEST_ENV_FILE=~/.colab-v2-test-32.env` · `COLAB_TASK_ID=<task>` · `COLAB_VISUAL_URLS=<6건>`. URL = 이 레인이 띄운 audit 빌드(`vite preview --config audit.vite.config.ts --host 127.0.0.1 --port 47452 --strictPort` · 시작 때 PID 저장 · 그 PID 만 종료)의 `audit-design.html?scene=<장면>&design=full` 6건(`primitives` · `catalog` · `detail` · `gnb-more` · `login` · `not-found`). `COLAB_VISUAL_EXEMPT` 미사용.

| 게이트 | 1차 task(`2eecfff3`) | 2차 task(`f179edc8`) |
|---|---|---|
| `frontend-test` | green — 2057 통과 · 실패 0 | green — 2058 통과 · 실패 0 |
| `frontend-design-lint` | green — 파일 21 · a–h 0 · 문서 표 갈림 0 | 같음 |
| `frontend-visual` | green — **페이지 6** · 13px 미만 0 · 대비 < 4.5 0 · 스크린샷 12 | 같음 |
| 계 | green 3 / red(판정) 0 / red(준비) 0 | green 3 / red(판정) 0 / red(준비) 0 |

- 이 보고서 커밋 뒤 2차 task 로 한 번 더 돌려 인계한다(최종 gate-summary 절대경로와 3계수는 인계 메시지).

## 8. 수치(직렬 실행 · 자기 캡처 · 트리 `f179edc8`)

### 8-1. 390 터치 6장면 ＋ `catalog` 1024 터치 · 레인 L2a 판정

- 실행: 캡처 실행기 수치 전용(`--metrics-only`) · 라벨 `dwi0926-l2a2-390`(6장면 × 2테마 · 뷰포트 390) · `dwi0926-l2a2-1024`(`catalog` · 뷰포트 1024) · 모두 종료 0.
- 판정(`judge.mjs --lane L2a`, 두 폴더 함께): `files=14 lane=L2a red=0 readiness=0 notMeasured=18 captureBlind=0 exemptHits=0 smallOther=0 outsideRed=16:0,44:52,넘침:0,가림:0 exit=0`.
- 3 · 4 가 1024 실행에서 재졌다는 근거: 같은 판정을 390 폴더만으로 돌리면 `::visual-judge-readiness:: lane L2a targets never measured with a box: 3, 4` · 종료 78. 1024 폴더를 더하면 0. 1024 수치 파일 상자: 3 `.gnb-settings` 104.6–105.7 × 44 · 4 `.gnb-upload` 82.7–83.4 × 44.
- 「재지 않음」 18 = 3 · 4 번 390(각 8 · 4장면 × 2테마) ＋ 5 번 `.gnb-more` 1024(2 · 900 초과에서 숨김). 모두 폭 숨김 · 설계상 숨김.
- 390 상자(라이트 · 다크 같음): 1 로고 44×44 · 2 주 내비 121.3×44 · 5 더보기 44×44 · 6 로그아웃 59×44 · 7 테마 88×44 · 21 없는 페이지 링크 107.5×44 · 22 되돌아가기 99.6×44.
- 뒤 레인 대상 red 개수(44 · 레인 거르기 밖): 52.

### 8-2. 820 터치 수치 전용(6장면 · 입력 < 16 개수만)

- 라벨 `dwi0926-l2a-820`(`2eecfff3` 빌드): 입력 < 16 = **0**(12파일 모두 `inputFont.small` 빈 목록 · 대상 입력 1–5개).

### 8-3. 메뉴 막대(`.gnb`) 높이 · 자식 상자 세로 범위(`getBoundingClientRect` · `catalog` 라이트)

- 방법: 수치 전용 캡처 실행기의 측정 직후 같은 세션에서 `.gnb` 상자와 자식(로고 · 연구실 표기 · 주 내비 · 업로드 · 설정 · 더보기 · 테마 · 아바타 묶음 · 아바타 · 로그아웃) 상자를 읽는 일회용 래퍼(커밋 안 함 · 실행기 코드 변경 0). 창 크기와 입력 방식은 실행기의 상태 확인(78)을 그대로 거쳤다.

| 창 · 입력 | 막대 높이 | 자식 세로 범위 | 같은 폭 마우스 막대 | 비고 |
|---|---:|---|---:|---|
| 390 터치 | 113 | 10–102 | 113 | 900 이하 두 줄 막대(설계) · 마우스와 같음 |
| 820 터치 | **117** | 10–106 | 109.4 | 첫 줄이 36 → 44(대상 1 · 5 · 6 · 7) · **+7.6** · §9 판정 요청 |
| 1024 터치(수정 전 `2eecfff3`) | 64 | **−8.5–71.5** | 64 | 아바타 · 로그아웃 두 줄 묶음 80 이 막대 밖으로 8px 씩 |
| 1024 터치(수정 뒤 `f179edc8`) | **64** | 9.5–53.5 | 64 | 묶음 한 줄 44 · 가로 넘침 0(scrollWidth = clientWidth 1024) · 로그아웃 63×44 |
| 1180 터치 | 64 | 9.5–53.5 | 64 | |
| 1440 마우스 | 64 | 11.5–51.5 | — | |

- 수정 뒤 터치 4크기에서 대상 누름 칸 최솟값 44(로고 · 주 내비 · 업로드 · 설정 · 더보기 · 테마 · 로그아웃).
- 1024 터치 수정 뒤 캡처 판독: 로그아웃 글자 한 줄 · 막대 아래 선 위. 주 내비 글자 두 줄(「연구/실」)은 B0 부터 있던 모양이다.

### 8-4. 1440 마우스 대 B0 `dwi0926-base`

- 캡처 실행기 `--metrics --only primitives,catalog,detail,gnb-more,login,not-found`(라벨 `dwi0926-l2a2-cap` · 종료 0 · 66장) → `diff.mjs --subset --viewport 1440` → **10장 · red 0 · 엄격 픽셀 0 · 종료 0**(`gnb-more` 는 1440 뷰포트 없음). `2eecfff3` 에서도 같은 결과.
- B0 폴더: 워크트리 `agent-abf926c2ed31f5520` 의 `frontend/.visual/dwi0926-base`(읽기만).

## 9. 이탈 · 결정 · 남은 것

- 원한 결과 대조(spec V7 셸 · V8 셸/기본/프리미티브 · V10 감싸기 9):
  - 충족: hover 9규칙 조건 안 · 조건 밖 0 · 16px 하한 한 곳(640px 이하 또는 터치) · 641 이상 터치 입력 < 16 0(820 실측) · 레인 L2a 44 대상 9 red 0(390 ＋ 1024) · 1440 마우스 픽셀 0 · 생성 표 재생성.
  - 미달: 없음(아래 판정 요청 1건은 오케스트레이터 후속 지시 「모든 터치 폭에서 막대 높이 = 마우스 높이」에 대한 것).
  - 초과: `.gnb .avatar-wrap` 한 줄 규칙(오케스트레이터 후속 지시로 추가 · 터치 블록 안만).
- **판정 요청 — 820(641–900) 터치 막대 높이.** 900 이하에서는 마우스에서도 막대가 두 줄(마우스 820 = 109.4 · 390 = 113)이라 「64」가 기준이 될 수 없다. 같은 폭 마우스와 비교하면 390 은 같고 820 은 +7.6 이다. 원인은 첫 줄 대상(로고 · 더보기 · 로그아웃 · 테마)이 44 가 되어 줄 높이가 36 → 44 로 커진 것 자체다. 44 를 지키면서 같게 하려면 설계 결정이 필요해 고르지 않았다.
  - ⓐ 받아들인다: 641–900 터치 막대 117(마우스 109.4) · 코드 변경 0.
  - ⓑ 터치에서 900 이하 막대 세로 여백을 10 → 6px 로 줄인다(6 ＋ 44 ＋ 8 ＋ 44 ＋ 6 ＋ 선 1 ≈ 109 · 마우스와 −0.4). 목업 치수(`.gnb` padding)를 터치에서만 바꾼다.
  - ⓒ 터치에서 두 줄 사이 간격 8 → 0px 로 줄인다(≈ 109 · 두 줄이 붙어 보임).
- 레인 결정(spec 빈칸 · 근거로 닫음):
  - 여러 줄 hover 블록은 들여쓰기만 바꿔 감쌈(원문 한 줄 단언은 한 줄 규칙에만 있음 · 시험 green).
  - 새 16px 블록은 옛 640px 블록 바로 뒤에 둠(`!important` 라 순서 영향 없음).
  - 로고 누름 칸은 왼쪽 정렬 유지(로고 x 위치 불변 · 누름 칸만 오른쪽으로 넓어짐).
- 후속:
  - 레인 보고 파일은 1차에서 Write 도구가 「하위 에이전트는 보고 파일을 쓰지 않는다」로 거절해 부모에 본문을 반환했고, 2차 지시로 셸에서 썼다.
  - 막대 높이는 수치 파일(`measure.js`)에 없다. 막대 · 자식 세로 넘침은 판정 스크립트의 넘침(가로) 검사에 걸리지 않는다 — 이번 1024 넘침도 판정 red 0 인 채였다. 어느 검사에도 걸리지 않는 결함 유형이므로 측정 항목 추가를 후속으로 올린다.
- 캡처 폴더(추적 제외 · `frontend/.visual/`): `dwi0926-l2a-390` · `dwi0926-l2a-1024` · `dwi0926-l2a-820` · `dwi0926-l2a-cap` · `dwi0926-l2a-diff-1440`(1차) · `dwi0926-l2a2-390` · `dwi0926-l2a2-1024` · `dwi0926-l2a2-cap` · `dwi0926-l2a2-diff-1440` · `dwi0926-l2a-fixcheck`(2차).
