# Spec: 디자인 구조 P2a — 보정 층 `design-system.css` 흡수 · `@layer` 도입
출처 intent: `dev-package/intent/2026-09-24-design-system-structure.md` (승인 2026-09-24 · Q2 `@layer` 예 · Q4 시각 변경 0)
계획: `dev-package/reports/design-system/20260924/architecture.md §2-1·§3 P2a` · 조사: `dev-package/reports/design-system/20260924/p2/design-system-map.md`
선행: P0(캡처·대조 도구) · P1(토큰 정본 단일화 — 화면 파일 `:root`·`@import` 0 · 이 spec 은 P1 병합 뒤 착수)

## 문제 진술
- `frontend/src/shell/design-system.css`(223행 · 규칙 192)는 프리미티브가 아니라 **보정 층**이다. 전 규칙이 `:is(.colab-ui, .design-preview) <화면 선택자>` 꼴이고, 이기는 근거는 접두사 특이도(+0,1,0)와 **로드 순서**(`shell.css` 가 마지막)다. 다른 파일과 값이 충돌하는 규칙 136 · 충돌 쌍 442(조사 부록 A).
- 「`@layer` 만 먼저 넣기」는 시각 변경 0 이 아니다 — 보정 층이 억누르는 상태 선언 3건(`members.css` `.btn-primary:hover` · `upload.css` `.inp[readonly]` · `lineage.css` `.lin .chip--warning`)이 층 도입 순간 되살아나고, 화면 특이도(0,3,x)에 이미 지는 25규칙은 층 위치에 따라 결과가 뒤집힌다.
- 그래서 순서는 **흡수 → 삭제 → 층 선언**이다. 값을 통일하는 일(프리미티브)은 P2b.

## 해법 개요
- 보정 층의 규칙마다 「오늘 실제로 렌더되는 값」을 결정해 그 값을 **소유 파일의 규칙**에 병합한다(보정 층이 이기면 보정 값으로 교체, 화면이 이기면 화면 값 유지). 병합이 끝나면 `design-system.css` 를 삭제한다.
- `@layer tokens, base, screens;` 를 **첫 CSS** 로 싣고, `tokens.css` 는 `tokens` 층, 보정 층의 문서 기본 규칙 4개(글자 크기·행간·자간 · tap-highlight · placeholder 색 · 체크박스 accent)는 새 `shell/base.css` 의 `base` 층, 나머지 화면·셸 CSS 16파일은 각 파일 본문을 `@layer screens { … }` 로 감싼다. `primitives`·`patterns` 층 이름은 선언만 하고 비워 둔다(P2b).
- 보이는 값은 바뀌지 않는다 — P0 도구로 착수 HEAD 기준 캡처 → 수정 뒤 대조 → 196장 엄격 차이 0.

## 사용자 스토리
1. 화면을 고치는 작업자로서 한 화면의 스타일을 그 화면 파일 한 곳에서 보고 싶다, 보정 층까지 두 파일을 대조하지 않기 위해.
2. 검토자로서 **층을 넘는** 우선순위(토큰 < 프리미티브 < 화면)가 파일 로드 순서와 무관하길 바란다(같은 층 안의 동률은 여전히 순서가 정한다).
3. Ted 로서 이 정리 뒤에도 화면이 픽셀 단위로 같음을 대조 보고서로 확인하고 싶다.

## 구현 결정
- **흡수 알고리즘**(규칙 192 · 조사 §1 표의 `owner`·`target file` 을 그대로 쓴다 · 갈리면 멈추고 보고):
  0. **판정 도구를 먼저 만든다** — `frontend/scripts/visual-baseline/` 옆 `frontend/scripts/cascade-map.mjs`(zero-dependency · 커밋): 전 CSS 를 파싱해 규칙마다 (파일 · 순서 · 선택자 · 특이도 · 선언)을 세우고, 보정 규칙 R 의 선택자 S 마다 **경쟁 규칙** = S 의 마지막 compound 에 든 클래스·요소·속성을 가진 모든 규칙(`:hover`·`:focus`·`:focus-visible`·`:active`·`:disabled`·`[readonly]`·`[aria-*]` 변형 포함)을 모아 특이도·순서로 오늘의 승자와 **되살아남 후보**를 표로 낸다. 조사 부록 A 의 휴리스틱 쌍은 이 표로 대체한다(우려 항목 3). 특이도 규칙: `:is()` 는 오늘은 인자 중 최대, 옮긴 뒤는 인자별 · `:where()` 는 0(DS:175) · 접두사 `:is(.colab-ui, .design-preview)` 는 +0,1,0.
  1. 보정 규칙 R = `:is(.colab-ui, .design-preview) S { d₁ … dₙ }` 마다, 각 선언 dᵢ 에 대해 경쟁 규칙과 오늘의 승자를 **(선언 × 요소 문맥)** 단위로 정한다 — 특이도(접두사 포함) 비교, 동률이면 뒤 순서 승. ⚠ 순서: `design-system.css` 는 `shell.css` 1~2행 `@import` 로 실리므로 **`shell.css` 본문보다 앞**이다 — 화면 15파일과 동률이면 보정 층 승, `shell.css` 와 동률이면 shell 승.
  2. 보정 층이 이기는 선언 → 소유 파일에서 **같은 선택자 S 의 규칙이 있으면 그 규칙의 해당 속성 값을 교체**, 없으면 소유 파일 끝(또는 같은 미디어 블록 안)에 `S { … }` 규칙을 새로 쓴다(접두사 없이). **그리고 접두사를 떼면 특이도가 (0,1,0) 내려가므로, 오늘 보정 층에 지던 경쟁 선언 중 특이도가 spec(S) 이상 spec(S)+(0,1,0) 미만이거나 같은 특이도로 뒤에 오는 것은 전부 되살아난다 — 그 선언들은 오늘 죽은 선언이므로 소유 파일이든 다른 파일이든 삭제하거나 값을 일치시킨다**(예: `.memgrid .btn`(0,2,0) 은 오늘 `:is(.colab-ui) .btn`(0,2,0)에 순서로 지지만 흡수 뒤 `.btn`(0,1,0)을 이긴다). 삭제·일치 목록은 ⓓ 표에 이름과 원래 값으로 남긴다.
  3. 화면이 이기는 선언 → **S 가 맞는 모든 문맥에서 진다**고 0 의 표가 보일 때만 보정 선언을 버린다. 어떤 문맥에서는 이기고 어떤 문맥에서는 지면 문맥별로 규칙을 나눠 쓴다(예: `.memgrid .btn` 과 `.up .btn` 을 따로).
  4. `:is(A, B, C)` 목록 선택자는 인자별로 승패가 다를 수 있다 — **인자마다 따로** 1~3 을 적용한다(예: DS:117 `:is(.inp,.sel,.login-input,.pv-control select)` 는 오늘 전 인자에 (0,2,1) 을 주고, 옮긴 뒤 `.inp` 는 (0,1,0)).
  5. 보정 층의 미디어 블록(≤900px · ≤640px · ≤1100px)은 소유 파일의 같은 조건 블록으로 옮긴다(없으면 만든다 · 이미 있으면 **병합**하고, 시험의 `mediaBlock` 도우미가 첫 블록만 잡는지 확인한다).
  6. 억눌린 상태 선언 — spec 작성 시 알려진 3건(`.btn-primary:hover` 배경 · `.inp[readonly]` 배경/색 · `.lin .chip--warning` 색)은 2 의 일반 규칙의 부분집합이다. 0 의 표가 내는 **되살아남 후보 전부**를 같은 규칙으로 처리(삭제 또는 값 일치)하고 보고서에 이름·원래 값을 남긴다. 되살릴지는 별건(우려 항목 1).
  7. 중복 2규칙(조사 `drop`)은 버린다. 「혼합」 5규칙은 선언 단위로 1~3 을 적용한다.
  8. 결과 = `design-system.css` 0행 → 파일 삭제 · `shell.css` 1~2행의 `@import` 삭제. 보정 층의 문서 기본 규칙 4개(`.colab-ui` 루트 글자 크기·행간·자간 · tap-highlight · placeholder 색 · 체크박스 accent)는 **`shell.css` 맨 앞으로 옮기고 `.colab-ui` 접두사를 유지**한다(base 층으로 내리면 오늘 특이도로 이기던 것이 screens 층에 진다 — 강등 금지). 이 4규칙에도 1~3 판정을 적용한다.
- **층 도입**
  - 새 파일 `frontend/src/shell/layers.css` = `@layer tokens, base, primitives, patterns, screens;` 한 줄. `styles.ts` 의 **첫 import**(pretendard 보다 앞). pretendard 는 `@font-face` 만이라 층 무관(조사 §4).
  - `tokens.css` 본문을 `@layer tokens { … }` 로 감싼다(`:root`·다크·미디어 블록 전부 · P1 결과 그대로).
  - `base` 층은 이번에 **비워 둔다**(이름만 선언). 문서 기본 규칙 4개는 위 8 대로 `shell.css`(screens 층) 맨 앞에 둔다.
  - 화면·셸 CSS **전부**(목록이 아니라 `find frontend/src -name '*.css'` 에서 `tokens.css` 를 뺀 것 · 오늘 17파일 = 화면 16 + `shell.css` · `deletion.css` 는 `styles.ts` 에 없고 `DatasetDeleteEntry.tsx` 가 직접 import 하므로 빠뜨리기 쉽다): 각 파일의 첫 규칙 앞에 `@layer screens {`, 파일 끝에 `}` 를 더한다(본문 들여쓰기 무변 · diff 최소). `@import`·`@charset` 은 0건이어야 한다(층 블록 안에서 무효 · P1 뒤 실측 0).
  - `styles.ts` 순서 = `layers.css` → pretendard → `tokens.css` → 화면 CSS → `shell.css`. 라우트·컴포넌트의 개별 `import './x.css'` 는 **그대로 둔다**(같은 모듈 · 순서 영향 없음 · 조사 §0). `src/**/*.tsx` 는 건드리지 않는다 — 예외: `design-system.css` 를 가리키는 **주석** 3곳(`shell.css` · `Gnb.tsx` · `AccountAdminPage.tsx`)은 주석 문면만 고친다.
  - `!important` 2건(`shell.css` 미디어 블록)은 screens 층에 그대로 — 층 안 `!important` 는 모든 층의 보통 선언을 이기므로 오늘과 같다.
  - ⚠ **jsdom 29 는 `@layer` 블록 안 규칙을 계산값에 넣지 않는다**(advisor ① 실측 · 파싱은 되나 cascade 에서 빠진다). 그대로 두면 계산값 시험 6 it 이 전부 red. 해결 = `vite.config.ts` 의 **test 모드 전용** 플러그인(의존성 0 · 코드 20행 안팎)이 CSS 문자열에서 `@layer <이름> {` 껍질과 짝 `}` 만 벗기고 `@layer a, b;` 문장은 지운다. 제품 빌드에는 적용하지 않는다. 플러그인은 red 픽스처 시험 1건으로 잠근다(껍질만 벗기고 내용은 그대로 · 중첩 `@media` 보존). 이 우회는 **층 판정 자체를 시험이 검증하지 못한다**는 뜻이므로 보고서 「하지 않은 것」에 적는다 — 층 판정의 증거는 실브라우저 캡처(ⓑ)다.
- **시험**(조사 §5)
  - 직접 깨짐 3 it: `test/shell-lth-20260913.test.tsx`(900px 블록 **과 640px 블록** 둘 다 `design-system.css` 에서 읽음 → 소유 파일 `shell.css` 로) · `test/account-admin-layout-20260918.test.ts`(`.table-scroll-hint` 와 1100px 블록을 `design-system.css` 에서 읽음 → 새 소유 파일로 · 접두사 문자열은 단언하지 않으므로 경로만). 읽는 파일 경로만 바꾼다. 단언 값은 그대로.
  - `vite.config.ts` `test.css.include` 에 `layers.css` 를 더하고 위 test 전용 껍질 제거 플러그인을 단다. 계산값 시험 6 it 은 값 무변이면 통과해야 한다 — 깨지면 원인을 보고하고 멈춘다.
  - 원문 시험 18파일: `@layer screens {` 한 줄이 앞에 붙어도 `block(css, selector)`·`:root{}` 정규식은 그대로 동작해야 한다. 깨지면 시험을 넓히지 말고 보고.
- **게이트**: P1 의 `frontend-design-lint` 는 그대로 green 이어야 한다(층 블록 안 `:root` 는 정본 파일 안이므로 a·d 무관). 게이트 e(프리미티브 단일 소유)는 P2b.
- 스키마 · 마이그레이션: 없음. API 계약: 비파괴 · 변경 없음.

## 시험 결정
- 외부 행위 기준 검증 항목:
  - ⓐ `design-system.css` 부재 · `.colab-ui` 선택자가 `shell.css` 맨 앞 4규칙에만 있음 · `find frontend/src -name '*.css'` 의 전 파일(`tokens.css` 제외 · 오늘 17)이 `@layer screens {` 로 시작하고 `}` 로 끝남 · `tokens.css` 는 `@layer tokens {` · 층 밖 규칙 0(스크립트로 센다 · 대상 0건 red).
  - ⓑ 시각 변경 0 — `visual:capture -- --label p2a-before`(착수 HEAD · 빌드 포함) → 수정 → `--label p2a-after`(빌드 포함) → `visual:diff` **196장 엄격 차이 0 · exit 0**. 차이가 있으면 장면·픽셀·원인 표를 내고 멈춘다.
  - ⓒ 상태 선언 계측 — 캡처는 상태를 보지 못하므로, `cascade-map.mjs` 가 낸 되살아남 후보의 **모든 상태 선택자**에 대해 `agent-browser` 로 상태를 강제(`hover <selector>` · `focus <selector>` · 속성은 `eval` 로 `readonly`/`disabled`/`aria-*` 설정)한 뒤 계산 스타일(해당 속성)을 **수정 전·후** 같은 장면에서 재어 표로 낸다(같아야 한다). 강제할 수 없는 상태는 이름과 사유를 [미측정] 으로 적는다.
  - ⓓ 흡수 표 — 192규칙 × (이동 선언 수 · 버린 선언 수 · 대상 파일:선택자) + 되살아남 후보 처리 표(선택자 · 파일 · 원래 값 · 삭제/일치). 합계가 조사 §1 의 계수와 맞는지.
  - ⓔ 게이트 `frontend-design-lint`·`frontend-typecheck`·`frontend-test`·`frontend-fixture-reach` green · 시험 건수 무변(폐기 0 · 경로 변경 2파일).
- 재사용 seam: P0 캡처·대조 · 조사 §1 표·부록 A · vitest CSS 원문 시험. 신설 seam: `layers.css`·`base.css`.
- 해당 서비스 단독 게이트 이름: 위 ⓔ 4종.
- green-by-skip 방지: ⓐ 의 계수 스크립트는 대상 0건 red · ⓑ 는 196장 명시 · ⓓ 합계 대조.

## 정책 대조 (작성 시점 제약)
- `.agents/rules/product.md §3`·`§5` 저촉: 없음(의존성 0 · 생성물 무변 · 절대경로 0 · legacy 대장 무변).
- 계약 동결 해제 필요: 아니오.

### 디자인 제약 확인
대상 화면: 전 화면(선언의 위치만 바뀐다 · 값 무변) · 정본 `tokens.css`
| 항목 | 충족/미충족/해당 없음 | 근거 |
|---|---|---|
| 토큰만 사용 | 충족(P1 게이트 유지) | `frontend-design-lint` |
| 글자·대비·그림자·여백·인터랙션 | 해당 없음(값 무변) | 캡처 차이 0 · ⓒ |

## 우려 항목 (판정 필요)
| # | 항목 | ⓐ | ⓑ | 권고 |
|---|---|---|---|---|
| 1 | 억눌린 상태 3건 — 오늘은 안 보이는 hover 배경·readonly 표시·계보 경고색. 보정 층이 실수로 덮은 것일 수 있다 | 삭제(오늘 모습 유지 · 이 spec) | 되살린다(시각 변경 · 별건 intent) | ⓐ · 이름을 P5 문서의 「후속 판정」에 남긴다 |
| 2 | `@layer` 블록으로 감싸면 파일마다 2행이 늘고 diff 가 커진다 vs `styles.ts` 를 CSS `@import … layer()` 로 바꾸기 | 감싸기(JS import 구조 무변 · 컴포넌트별 side-effect import 와 충돌 없음) | `@import layer()`(컴포넌트별 `import './x.css'` 를 전부 지워야 층 밖 중복 적재를 막는다 → TSX 변경) | ⓐ |
| 3 | 조사 부록 A 의 충돌 쌍은 휴리스틱이다 | `cascade-map.mjs` 로 전 규칙 재판정(구현 결정 0) | 그대로 신뢰 | ⓐ · 캡처 차이 0 + ⓒ 상태 계측이 최종 판정 |
| 4 | jsdom 이 `@layer` 를 계산에 넣지 않아 test 전용 껍질 제거 플러그인을 단다 — 시험이 층 판정을 검증하지 못한다 | 플러그인 + 실브라우저 캡처로 층 판정 증명(이 spec) | 계산값 시험 6 it 을 원문 시험으로 바꾼다(시험 변경 · Ted 판정) | ⓐ |
| 5 | P2 를 P2a/P2b 두 PR 로 나눴다 — Q6 「단계당 PR 1건 순차」의 형태 안에서 단계 수만 늘렸다 | 재승인 불필요 · PR 요약에 한 줄 명시 | Ted 재확인 | ⓐ(advisor ① 판단 동일) |

## P1 결과 반영 (2026-09-24 · `p1/report.md`)
- P1 이 `shell.css` 의 `@import` 2건(`tokens.css` · `design-system.css`)을 남겼고 게이트 d 는 화면 CSS 만 본다 — 이 spec 8 이 그 둘을 없앤 뒤 **게이트 d 의 `@import` 대상을 `tokens.css` 밖 전 CSS 로 넓힌다**(`design-lint.mjs` 한 줄 · selftest `red-d` 픽스처에 `shell.css` `@import` 케이스 추가).
- `--up-*` 6종·`--lin-over-*` 3종은 P1 에서 정본으로 올라갔다(`.up` 루트 부재). P2a 는 그대로 둔다 — 프리미티브 흡수 뒤 정본 의미 토큰으로 바꾸는 것은 P2b.
- `design-lint.mjs` 사각 3건(advisor ② 권고): `html:root` 셀렉터 인식 · `CANON_PREFIX` 에 `--accent-` 추가 · 추적 파일 부재 시 78. 이 spec 에서 함께 고치고 selftest 에 케이스를 더한다(계측 정밀도 상향 · 범위 축소 아님 · 실패 픽스처로 증명).
- 시험 건수 기준: P1 뒤 `frontend-test` 1610건(폐기 1파일). P2a 는 폐기 0 · 경로 변경 2파일 · 플러그인 시험 +1.

## 범위 밖
- 프리미티브 추출·값 통일·게이트 e(P2b). 색 리터럴 정리(P3). TSX 변경(주석 3곳 제외). 토큰 값 변경. 억눌린 상태의 복원.
- 커밋·push·PR 게시(사용자) · 배포.

## 산출 계획
- 라운드 파일: 없음. 진행 = 이 spec + `dev-package/reports/design-system/20260924/p2a/report.md` + `p2a/visual/report.md`.
- 예상 레인 수: 1(직렬) · `lane-worker` · `isolation: worktree` · 기준 = P1 병합 뒤 `claude/design-system-structure`. 별도 PR.
- 로컬 PR 요약: `~/.claude/pr-bodies/PR-BODY-design-structure-p2a.md`.
