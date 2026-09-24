# Spec: 디자인 구조 P3(+P4) — 화면 CSS 색 리터럴·죽은 폴백·TSX 인라인 리터럴 정리 · 게이트 f·g
출처 intent: `dev-package/intent/2026-09-24-design-system-structure.md` (승인 2026-09-24 · Q4 시각 변경 0 · Q5 인라인은 CSS 변수 대입만)
계획: `dev-package/reports/design-system/20260924/architecture.md §2-2 f·g · §3 P3·P4` · 조사: `dev-package/reports/design-system/20260924/p3/literal-map.md` · `survey.md §2`
선행: P0 · P1 · P2a. **P2b 보다 먼저** 한다(advisor ① 권고 · P2b 가 폴백 없는 선언을 옮기게 되고, 게이트 f 가 P2b 에서 새 리터럴이 들어오는 것을 막는다 · 두 단계는 `upload.css` 를 같이 건드리므로 동시 진행 금지).

## 문제 진술
- P1 뒤에도 화면 CSS 에 색 리터럴 72건이 남아 있다 — 직접 색 5(A 1 · B 3 · C 1) + `var(--x, 리터럴)` 죽은 폴백 67(전부 `--x` 가 정본에 정의돼 폴백이 렌더된 적 없음 · `search.css` 40). 폴백은 정본을 두 곳으로 가르는 두 번째 값이다(BF-11 이 `project.css` 한 파일에서 이미 없앤 모양).
- TSX 인라인 `style={{…}}` 7건(5파일) 중 정적 리터럴 1건(`RegisterArea.tsx`)이 있고, 나머지 6건은 데이터값이다.
- 게이트 f(정본 밖 색 리터럴 0) · g(TSX 인라인 리터럴 0) 가 아직 없다.

## 해법 개요
- 죽은 폴백 67건은 폴백만 지운다(`var(--x, #…)` → `var(--x)` · 값 무변).
- 직접 색 5건 — **치환 규칙: 후보 토큰은 라이트 값과 다크 값이 모두 리터럴과 같아야 한다**(조사는 라이트 표만 대조했다 · 리터럴은 테마와 무관하게 고정값이므로 테마 따라 바뀌는 토큰으로 바꾸면 다크가 변한다). B 3건(`#fff`)은 테마 불변 흰색 토큰 `--color-white` 로 고정한다(`--color-on-primary`(다크 #10233c)·`--color-surface`(다크 #1a222c)는 다크가 바뀐다 · 「뜻」으로 고르는 치환은 시각 변경이라 별건). A 1건(`project.css` `.pj-modal-back` `rgb(15 20 28 / 45%)`)은 `--color-overlay` 의 다크 값이 `rgb(3 7 12 / 65%)` 라 같은 값이 아니다 → C 와 같이 **Ted 판정** · 판정 전 면제. C(`upload.css` `.chip` 배경 `#eef2f7`)는 같은 값 토큰이 없어 **Ted 판정**(새 토큰 vs 기존 토큰으로 값 변경 = 시각 변경). 판정 전에는 리터럴을 두고 `allow.txt` 에 사유와 함께 면제(건수 2 노출).
- TSX 정적 인라인 1건은 CSS 클래스로 옮기고, 데이터값 6건은 `style={{'--w': v}}` 꼴로 바꿔 CSS 가 `var(--w)` 를 읽게 한다(Q5).
- 게이트 `frontend-design-lint` 에 f·g 를 더하고 selftest 에 red 픽스처를 더한다.
- 보이는 값은 바뀌지 않는다 — P0 도구로 196장 엄격 차이 0.

## 사용자 스토리
1. 화면을 고치는 작업자로서 색은 토큰 이름으로만 적고 싶다, 리터럴이 정본과 갈리는 두 번째 값이 되지 않도록.
2. 검토자로서 새 PR 이 색 리터럴이나 TSX 인라인 색·크기를 넣으면 게이트가 red 를 내길 바란다.
3. Ted 로서 뜻이 갈리는 자리(B)와 값이 없는 자리(C)만 표로 보고 판정하고 싶다.

## 구현 결정
- **D 죽은 폴백 67건**(`literal-map.md` 분류 D 표): 폴백만 삭제. 파일별 = search 40 · upload 9 · shell 6 · detail 3 · 그 외. `lineage.css` 의 `var(--lin-over-ink, #5b6472)` 3곳은 P1 후속 항목(의도가 회색이었는지) — 폴백을 지우되 보고서에 「실제 렌더 = `--color-warning-600`」을 적는다.
- **B 3건** → 전부 `var(--color-white)`: `catalog.css` `.colmenu .cm-box`(체크 상태 primary 배경 위 흰 글자 · 다크에서도 `#fff`) · `detail.css` `.dt-edit .de-req`(배경 `--color-text-body` 위 흰 글자) · `search.css` `.vsw::after`(스위치 손잡이 · 다크에서도 흰색). 값 무변.
- **A 1건 · C 1건 → Ted 판정 · 면제 2건**: `gates/fixtures/frontend-design-lint/allow.txt`(P1 의 면제 파일 형식을 따른다 · 파일명이 다르면 그것을 쓴다)에 `project.css .pj-modal-back background rgb(15 20 28 / 45%) · 사유: --color-overlay 는 다크 값이 다름 · Ted 판정 대기` 와 `upload.css .chip background #eef2f7 · 사유: 같은 값 토큰 없음 · Ted 판정 대기` 를 등록(건수 2 노출).
- **캡처 범위 확인**: B 3자리(`.cm-box` 체크 상태 · `.dt-edit` 편집 모드 · `.vfilter` 스위치)와 A(`.pj-modal-back`)가 196장 중 어느 장면에 찍히는지 표로 적는다. 찍히지 않는 자리는 장면(action)을 더하거나 「미검증」으로 보고한다 — 조용히 통과시키지 않는다. `.pj-modal-back` 은 P2a 뒤 소유 파일에서 실제 렌더 값을 다시 확인한다(보정 층이 덮고 있었을 수 있다).
- **TSX 인라인 7건**(`survey.md §2` 목록 · 착수 시 재계측): 정적 1건은 클래스 + 화면 CSS 규칙으로. 동적 6건(진행률 폭 % · transform 문자열 · 견본 색 · 절대 좌표)은 `style={{ '--<이름>': value } as React.CSSProperties}` 와 CSS `var(--<이름>)` 로. `PreviewPanels.tsx` 의 `position: 'absolute'` 처럼 색·px 가 아닌 정적 값은 클래스로 옮긴다(`--` 키만 허용이므로). `style={{ width }}` 축약형도 대상. 이름은 컴포넌트 접두사(`--pv-…` 등) · 게이트 a 의 계열 접두사 금지 준수. 공용 타입이 필요하면 `frontend/src/shell/cssVars.ts` 하나. **TSX 변경은 이 7곳뿐**(P3 는 intent 가 TSX 인라인 정리를 명시한 단계).
- **게이트 f**: `tokens.css` 밖 CSS 의 색 리터럴 > 0 → red. 탐지 = hex · `rgb()`/`rgba()`/`hsl()`/`hsla()` · `oklch()`/`oklab()`/`color-mix()` · CSS 색 이름(`white`·`black` 등 표준 148개 목록) · 직접 값과 `var()` 폴백 모두. 제외 = `transparent`·`currentColor`·`inherit`·`initial`·`unset`. 면제 = `allow.txt`(파일 · 선택자 · 리터럴 · 사유 · 건수 노출 · 사유 없음 red · 낡은 항목 red).
- **게이트 g**: `frontend/src/**/*.tsx` 의 `style={{ … }}`(축약형 `{ width }` 포함) 안에서 `--` 로 시작하지 않는 키가 하나라도 있으면 red(색·px 만이 아니라 **모든 비변수 키** — 정적 값은 클래스로). 판정은 정규식이 아니라 TS 파서(`typescript` 는 devDependency 에 이미 있다)로 `style` JSX 속성의 객체 리터럴 키를 읽는다. 요약줄에 인라인 총건수와 변수 대입 건수를 낸다.
- selftest: `red-f`(직접 색 · 폴백 색 · 면제 사유 없음) · `red-g`(색 · px · 변수 대입은 green) 픽스처 추가 → 케이스 수를 README 행에 갱신.
- 스키마 · 마이그레이션: 없음. API 계약: 비파괴.

## 시험 결정
- ⓐ 게이트 착수 red(f = 72 이상 · 색 이름 리터럴은 착수 시 계측 · g = 7) → 최종 green(f 0 면제 2 · g 0). selftest 전건 기대대로.
- ⓑ 시각 변경 0 — `visual:capture` 전·후(빌드 포함) → 196장 엄격 차이 0. B 의 다크 판정은 여기서 난다.
- ⓒ 인라인 7건 처리 표(파일 · 종전 · 이후 · 데이터값이면 변수 이름).
- ⓓ `frontend-typecheck`·`frontend-test`·`frontend-fixture-reach`·`frontend-design-lint`(+selftest) green.
- green-by-skip 방지: 면제 건수 요약줄 노출 · 대상 0건 78 · 착수 red 기록.

## 정책 대조
- `product.md §3·§5` 저촉 없음(의존성 0 · 값 변경 0 · 절대경로 0). 계약 동결 해제: 아니오.

### 디자인 제약 확인
대상 화면: 전 화면(선언 표기만 바뀐다) · 값 무변 — 캡처 차이 0 이 증거. C 1건만 판정 뒤 시각 변경 가능.

## 우려 항목 (판정 필요)
| # | 항목 | ⓐ | ⓑ | 권고 |
|---|---|---|---|---|
| 1 | `upload.css` `.chip` 배경 `#eef2f7`(같은 값 토큰 없음) | 새 토큰 `--color-chip-bg`(값 유지 · 다크 값도 정해야) | `--color-gray-100`(#e8ecf2)으로 값 변경(시각 변경) | Ted 판정 · 판정 전 면제 |
| 2 | `project.css` `.pj-modal-back` 오버레이 `rgb(15 20 28 / 45%)` — `--color-overlay` 는 라이트 같고 다크 다름(`rgb(3 7 12 / 65%)`) | `--color-overlay` 로 치환(다크 모달 배경이 진해짐 · 시각 변경) | 리터럴 유지(면제) | Ted 판정 · 판정 전 면제 |
| 3 | 「뜻」에 맞는 토큰(`--color-on-primary` 등)으로 바꾸고 싶은 자리 3건은 다크가 변한다 | 이번엔 `--color-white`(값 무변) | 뜻 토큰으로(시각 변경 · 별건) | ⓐ |

## 범위 밖
- 여백·글자 크기 리터럴(729·213) — 눈금 확정 없이 막지 않는다(계측만). 토큰 값·이름 변경. 프리미티브(P2b). 커밋·push·PR 게시(사용자).

## 산출 계획
- 레인 1(직렬) · `lane-worker` · `isolation: worktree` · 기준 = **P2a 병합 뒤** 통합 브랜치(P2b 앞). 보고서 `dev-package/reports/design-system/20260924/p3/report.md` + `p3/visual/`. PR 본문 `~/.claude/pr-bodies/PR-BODY-design-structure-p3.md`.
