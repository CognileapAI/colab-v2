# 디자인 시스템 — 목표 구조와 단계 계획 (초안 · 미승인)

작성 2026-09-24 · 기준 HEAD `ea21d8c2`(develop) · 상태: Ted 판정 대기 · 제품 코드 변경 0.
출발점 = 승인 intent `dev-package/intent/2026-09-12-design-consistency.md`(시각 기준 · 재개봉 금지)와
그 전체 확장 회차 `dev-package/reports/design-consistency/20260912/full/`(필수 게이트 4/4 green · `execution-status.json` `remaining_required_work: []`).
이 문서는 **시각 값을 바꾸지 않고 적용 구조만** 표준화·안정화하는 계획이다.
계측 원자료 = 같은 디렉터리의 `survey.md`(researcher) · `css_audit.md`(`css_audit.py`). advisor ① 검토(approve-with-changes · 교정 8건) 반영판.

## 0. 한 줄 진단

09-12 회차 `source_digest` 시점 기준으로 **보이는 디자인**은 전 화면에 적용됐다(그 뒤 약 12일치 UI 커밋 #73~#123 은 이슈별 검증). 적용 **구조**는 세 갈래로 남아 있다.
① 토큰 어휘가 정본 밖 7개 파일의 `:root` 에 77건 흩어져 있고, 그중 5종은 정본 calm 블록과 값이 달라 **조용히 무시되는 죽은 선언**이다.
② 공통 클래스(`.btn`·`.chip`·`.card`·`.modal`·표)를 여러 파일이 각자 정의한다. React 프리미티브 컴포넌트는 0개다.
③ 「calm」 디자인은 `design-system.css` 가 화면별 선택자 약 190개를 **덮어쓰는 보정 층**으로 얹혀 있고, 이기는 근거는 로드 순서다.
막는 장치는 「화면 파일끼리 값이 갈리면 red」(BF-13 시험) 하나이고, 정본과 갈리는 것·새로 흩어지는 것은 아무것도 막지 않는다.
09-12 회차 스스로 `full/visual-review.md` 에 「로컬 토큰 선언은 기존 구조에 남아 있으며 전부 tokens.css로 물리적으로 옮겼다고 주장하지 않는다」고 남겼다.

## 1. 현재 구조 실측 (2026-09-24 · HEAD ea21d8c2)

| 축 | 실측 | 근거 |
|---|---|---|
| CSS 파일 · 페이지 | 19개 · 4,850행 · 페이지 12(`routes/` 10 + `auth/` 2) · TSX 91 | `find` · `survey.md §3·§4` |
| 토큰 정본 | `shell/tokens.css` 128행 · 선언 95건 · 블록 4(기본 · `:root[data-design="calm"]` · `[data-theme="dark"]` · ≤640px). 머리말 원문: 「셸(GNB·본문 캔버스)이 실제로 쓰는 토큰만 옮겼다 … 지금 통째로 복사하면 쓰지도 않는 값이 먼저 굳는다」 | `tokens.css:1-5` · `survey.md §1-1` |
| 정본 밖 `:root` 토큰 정의 | **77건** · 전부 `:root` 전역 스코프 · detail 26 · catalog 18 · upload 18 · project 8 · toast 3 · lineage 3 · preview 1 | `css_audit.md` G축 |
| 그중 전역 어휘 이름 | **38종**(`--color-*` 26 · `--space-*` 5 · `--radius-*` 2 · `--text-*` 2 · `--font-data` · `--shadow-lg` · `--leading-body-sm`) · 같은 이름을 최대 3파일이 정의 | 같은 계측 · 접두사 분류 |
| 정본과 값이 다른 죽은 `:root` 선언 | **5종** — `--color-border-control`(catalog·upload `#848c94` vs calm `#a9b3bf`) · `--color-surface-alt`(catalog·project `#f4f7fb` vs `#f5f7fa`) · `--text-h2`(detail·project `24px` vs `28px`) · `--color-danger-600`(upload `#ba3125` vs calm `var(--fg-danger)`=`#a3222b`) · `--color-text-subtle`(upload `#697077` vs calm `var(--color-text-muted)`=`#565c63`). 특이도 `:root[data-design="calm"]`(0,2,0) > `:root`(0,1,0)이고 `index.html` 이 `data-design="calm"` 을 항상 붙이므로 화면 파일 값은 제품에서 죽은 선언. 죽은 **폴백**은 따로 센다(예 `catalog.css` `var(--text-h2, 24px)`) — [미계측] | `survey.md §1-4` · 2026-09-24 grep 재확인 · advisor 특이도 검증 |
| calm 이 없는 문맥 | 제품 0곳. `design-preview.js` 의 `design=before` 모드와 `?design=` 없이 연 `audit-design.html` 두 곳(Q7) | advisor 검증 |
| 화면 파일끼리 값 충돌 | 0건 | `frontend/test/shared-css-tokens.test.ts`(BF-13) — 정본 대조는 하지 않는다 |
| 다크 값의 자리 | 다크 블록이 재정의하는 gray·primary·success·warning·accent 계열의 **라이트 값이 정본에 없다** — detail·catalog·project·upload 에 있다. 한 이름의 두 테마 값이 두 파일에 갈라져 있다 | `survey.md §1-2` |
| 공통 클래스 다중 소유 | `.btn` 블록 정의 3파일(참조 5) · `.chip` 7~8 · `.card` 4 · 모달 6계열 · 표 6계열 · `.input`/`.select` 프리미티브 0 · React 프리미티브 0 | `survey.md §3` · grep |
| 보정 층 | `design-system.css` 223행 · 전 규칙이 `:is(.colab-ui, .design-preview) <화면 선택자>` · 셀렉터 약 190개 12패밀리 · 독립 프리미티브 정의 0 | `survey.md §1-5` |
| 로드 순서 | `shell/styles.ts` 가 화면 CSS 13개 → `shell.css`(@import tokens · design-system). 보정 층이 이기는 것은 **순서** 덕분. `members.css` 는 따로 `@import tokens`. audit 진입점 3개(`audit-design`·`audit-upload`·`audit-selected-preview`)와 `design-preview`(iframe) 모두 `styles.ts` 를 거친다 | `styles.ts` · `audit-*.tsx` |
| 토큰 미사용 | 여백 리터럴 px **729** vs `var(--space-*)` 29 · 글자 크기 리터럴 213 vs `var()` 142 · CSS 직접 색 5 · `var()` 폴백 색 67(css_audit 기준 · hex 만 세면 63, 그중 `search.css` 35) · TSX 하드코딩 색 0 | `survey.md §2` · advisor grep |
| 인라인 스타일 | `style={{` 7건 / 5파일 · 정적 값은 `RegisterArea.tsx` 1건, 나머지 동적 | `survey.md §2` |
| 반응형 기준 폭 | 10종 혼재 | `survey.md §5` |
| 정적 접근성 | 13px 미만 3(카탈로그 장식 9px×2 · 12px×1) · 대비<4.5 1(4.49 · cascade 미반영 계측) · 미정의 토큰 2(모두 fallback) · 음수 여백 0 · 그림자 15 | `css_audit.md` |
| 집행 장치 | `frontend-visual`(글자≥13px · 대비≥4.5 · 선언 URL 만) · CSS 원문 vitest 5종(값 동일 · project.css 한 파일의 미정의 0 · 수정별 잠금) · `css_audit.py`(계측만 · 항상 exit 0) · stylelint·토큰 lint·픽셀 회귀 없음 | `gates/README.md` · `survey.md §6` |
| 시각 변경 0 증명 도구 | **없다.** 09-12 전체 회차의 캡처 구동부는 git 에 없고(`representative/capture.py`·`design-review/20260912/capture.py` 만 있다) `scenes.json` 은 계측값이지 캡처 명세가 아니다. 픽셀 대조 도구는 `frontend/package.json` 에 없다. 09-12 PNG 360장은 #73~#123 이전 상태라 기준으로 못 쓴다 | advisor 검증 |

## 2. 목표 구조

### 2-1. 층 (CSS cascade layers)

```
@layer tokens, base, primitives, patterns, screens;
```

| 층 | 파일 | 소유하는 것 | 금지 |
|---|---|---|---|
| tokens | `shell/tokens.css` | **저장소 유일의 `:root`**. 원시 눈금(`--gray-100`…`--blue-600`) → 의미 토큰(`--color-surface`·`--color-text-muted`·`--color-danger`…) 두 단. 한 이름의 라이트·다크 값이 **같은 파일**에 | 화면 이름이 붙은 토큰 |
| base | `shell/base.css` | reset · body 글꼴 · `:focus-visible` · `prefers-reduced-motion` 전역 · 반응형 기준 폭 정의(현재 10종 → 3종) | 클래스 규칙 |
| primitives | `shell/primitives.css` | `.btn`(+ `--primary`·`--ghost`·`--danger` · 크기) · `.field`(`input`·`select`·`textarea`) · `.card` · `.chip` · `.modal`(backdrop·dialog·head·body·foot) · `.table`(+ scroll wrapper · hint) · `.tabs` · `.toast` · `.badge`. **클래스마다 소유 파일 하나** | 화면 선택자 |
| patterns | `shell/patterns.css` | `.page`(폭·여백 컨테이너) · `.page-head` · 절 간격 · 폼 그리드 · 빈 상태 | 색 리터럴 |
| screens | `components/<x>/<x>.css` | 그 화면의 배치만. 한 화면만 쓰는 토큰은 `:root` 가 아니라 **그 화면 루트 클래스 범위**(`.catalog-page { --cat-…: }`)에 둔다 | `:root` · `@import` · 프리미티브 이름 재정의 · 색 리터럴 · 폴백 리터럴 |

- `design-system.css` 의 보정 규칙은 소유자(프리미티브·패턴·화면)로 **흡수해 해체**한다. `.colab-ui` 루트 클래스는 마운트 스코프로만 남기거나 제거한다(층 순서가 특이도 싸움을 대신한다).
- 로드 순서 의존을 없앤다 — `@layer` 선언이 순서를 고정하므로 `styles.ts` 의 import 순서가 결과를 바꾸지 않는다.
- ⚠ `@layer` 의 함정: **층에 넣지 않은 규칙은 모든 층을 이긴다.** 일부 파일만 층에 넣은 중간 상태는 우선순위가 뒤집힌다. 따라서 P2 는 **한 PR 안에서 전 파일을 층에 넣고**, 외부 CSS(pretendard 글꼴 선언)의 층 배치를 명시한다. CSS 원문을 정규식으로 읽는 vitest 시험(`project-css-tokens.test.ts` 등)이 `@layer { }` 감싸기에 깨지는지는 P2 spec 에서 먼저 잰다.
- 토큰 이름은 **기존 이름을 유지**한다. 이름 개편·눈금 확정은 별건.
- React 프리미티브 컴포넌트(`<Button>` 등)는 **이번 범위가 아니다**. 클래스 단일 소유가 먼저다.

### 2-2. 집행 장치 — 새 게이트 `frontend-design-lint`

레포 관행대로 판정부는 `gates/tools/` 의 스크립트 하나, 셀프테스트는 red 픽스처로 증명한다(`frontend-fixture-reach` 와 같은 꼴 · `gates/README.md` 의 세 상태 관례).
**세 상태** — 대상 파일 0건이면 red(준비 · 78) · 면제는 `gates/fixtures/frontend-design-lint/allow.txt` 에 건수가 드러나게 · 아무 선언 없이 통과 없음.

| # | red 조건 | 오늘 값 | 단계 |
|---|---|---|---|
| a | `tokens.css` 밖의 `:root` 안 `--*:` 정의(화면 루트 클래스 범위는 허용 · 대안 B) | 77 | P1 |
| b | 정의되지 않은 `var(--x)` 참조(폴백 유무 무관) | 2 | P1 |
| c | 라이트에 있는 의미 토큰이 다크에 없음(명시 「동일」 목록 제외) | [미계측] | P1 |
| d | 화면 CSS 안의 `:root` · `@import` | 7 · 1 | P1 |
| e | 프리미티브 클래스 이름을 `primitives.css` 밖에서 정의 | `.chip` 7 · `.btn` 3 · `.card` 4 · 모달 6 | P2 |
| f | `tokens.css` 밖의 색 리터럴(hex·rgb·hsl · `transparent`·`currentColor` 제외) — 직접 색과 `var()` 폴백 모두. **전제 둘** = 게이트 b 가 0건 · 모든 진입점(`index.html` · audit 3종 · design-preview iframe)이 `tokens.css` 를 로드함(2026-09-24 실측 충족) | 5 + 63~67 | P3 |
| g | TSX `style={{…}}` 안의 색·글자 크기·px 리터럴(데이터값은 CSS 변수 대입 `style={{'--w': v}}` 만 허용) | 1(정적) / 7(전체) | P4 |

기존 `frontend-visual` 은 유지한다. P1 이 끝나면 BF-13 시험(`shared-css-tokens.test.ts`)은 대상 0건이 되므로 그 오라클을 게이트 a 로 옮기고 시험은 폐기한다. ⚠ 이는 legacy 항목 BF-13(`work-items.yaml` · `status: done`)의 완료 정의 ⑴ 을 실제로 바꾸는 일이므로, P1 spec 에 **`work-items.yaml` BF-13 evidence 갱신 + `work-item-consistency` 게이트 green** 을 넣는다. 새 BF 번호·새 결정번호는 만들지 않는다.
여백·글자 크기 리터럴(729·213)은 **red 조건에 넣지 않는다** — 눈금 확정(별건) 없이 막으면 값을 지어내게 된다. 계측으로 추이만 낸다.

### 2-3. 시각 변경 0 을 증명하는 방법 — 도구가 아직 없다

각 단계의 완료 조건은 「보이는 값이 같다」다. 그런데 §1 마지막 행대로 **재현 가능한 캡처 구동부도, 픽셀 대조 도구도, 현재 HEAD 기준 캡처도 없다.** 그래서 **P0** 을 둔다 —
- 캡처 구동부를 git 에 커밋한다(장면 명세 = 09-12 의 30장면을 출발점으로, #73~#123 로 바뀐 화면(`AccountAdminPage` 표 등)이 덮이는지 계측으로 확인해 보강) · audit 빌드(`frontend/audit.vite.config.ts`)와 `agent-browser` 로 3폭 × 2테마.
- 픽셀 대조 도구 — 후보는 Node 만으로 되는 PNG 비교 라이브러리 1개(예 `pixelmatch`, devDependency). intent 제약 「새 도구를 들이지 않는다」와 부딪히므로 **Ted 판정(Q8)**. 대안 = 대조 없이 `frontend-visual` 계측값(글자·대비·넘침)과 사람 눈 검토만 — 「같다」의 판정력이 떨어진다.
- 각 단계 **착수 HEAD 에서 기준 캡처를 다시 만든다.** 09-12 PNG 는 쓰지 않는다.
차이가 있으면 그 자리를 표로 내고 Ted 가 「의도한 정정」인지 판정한다. 계측만으로 「같다」를 주장하지 않는다.
⚠ 죽은 선언 5종을 정본으로 통합하면 제품 화면은 **바뀌지 않는다**(이미 calm 값이 이긴다). calm 이 없는 두 문맥(§1)만 바뀐다 — Q7.

## 3. 단계 — 각 단계 = spec 1 · 레인 1 · PR 1

| 단계 | 내용 | 규모(실측 기반 추정) | 완료 조건 | 위험 |
|---|---|---|---|---|
| **P0 증명 도구** | 캡처 구동부 커밋 · 대조 도구(Q8) · 착수 HEAD 기준 캡처 · 장면 커버리지 계측 | 스크립트 2~3개 · 제품 CSS 0줄 | 같은 HEAD 두 번 찍어 차이 0(도구 자체 검증) | 도구 도입 판정 |
| **P1 토큰 정본 통합** | 38종 전역 어휘를 `tokens.css` 로 물리 이동(라이트·다크 나란히) · 죽은 선언 5종 제거 · 한 화면 전용 이름은 화면 루트 클래스 범위로 · `:root` 7블록·`@import` 1 제거 · 게이트 a·b·c·d + selftest · BF-13 evidence 갱신 | CSS 7파일 · 선언 77건 · `tokens.css` +약 40행 · 게이트 스크립트 1 + 픽스처 | 게이트 green · 캡처 차이 0 · `frontend-test`·`frontend-typecheck`·`work-item-consistency` green | BF-13 ⑶ 판정(Q1) |
| **P2a 보정 층 흡수 + `@layer`** ⟨2026-09-24 분할 · 조사 `p2/design-system-map.md`⟩ | `design-system.css` 192규칙의 선언을 **지금 렌더되는 값 그대로** 소유 규칙(화면·셸 파일)으로 병합하고 파일을 삭제. 화면 특이도에 이미 지는 25규칙은 화면 값 유지, 보정 층이 억누르던 상태 선언 3건(`.btn-primary:hover`·`.inp[readonly]`·`.lin .chip--warning`)은 **억눌린 상태 그대로**(선언 삭제 또는 값 일치) 유지 · `@layer tokens, base, screens` 를 전 파일에 한 번에(프리미티브 층은 비워 둠) · 깨지는 시험 3건 갱신 | 보정 규칙 192 · 충돌 쌍 442(부록 A) · CSS 16파일 | 캡처 차이 0 · 게이트 green | 「@layer 만 먼저」는 시각 변경 0 이 아니다 — 억눌린 상태 3건이 되살아나고 지는 25규칙이 뒤집힌다. 흡수가 먼저 |
| **P2b 프리미티브 단일 소유** ⟨spec `S-DESIGN-STRUCTURE-P2B-20260924` · advisor ① 반영⟩ | 0단계 = `base.css`(원소·`:where()` 규칙 — primitives 층이 screens 의 낮은 특이도에도 지는 두 번째 층 함정) → 계열별(btn·field·chip·card·table·modal) 기본값을 `primitives.css` 로, 오늘 순서·특이도로 지던 화면 선언은 삭제·일치, 특이도 편차는 **화면 범위 선택자**로 남김(값 통일은 시각 결정 · 범위 밖) · 게이트 e(맨 클래스 정의는 `primitives.css` 에만 · 목록 `gates/fixtures/frontend-design-lint/primitives.txt` 를 계열마다 늘려 매 경계 green) · `--up-*`·`--lin-over-*` 9/9 정본 토큰으로 치환. **`patterns.css`(페이지 컨테이너)는 P5 로**(선택자에 화면 이름 · TSX 이름 변경 없이는 이득 없음) | 정의 자리: 모달 115 · 표 106 · 입력 63 · 버튼 40 · 카드 38 · 칩 26 → 계열 경계에서 끊고 이어 받는다 | 캡처 차이 0 · 계산값 대조 0 · 게이트 green | 탭 3계열·별 계열 이름(`.login-input`·`.pj-modal` 등)은 범위 밖 |
| **P3 화면 CSS 정리** | 색 리터럴 5 · 폴백 63~67 → 토큰 · 배치만 남김 · 반응형 기준 폭 3종으로 · 게이트 f | 13파일 · 약 70곳 · `search.css` 35곳이 절반 | 3레인 순차(L1 셸·auth·common·dashboard / L2 catalog·search·detail·preview / L3 upload·lineage·project·lab·members) · 캡처 차이 0 | 정본에 없는 색이면 **새 토큰 이름은 Ted 판정** |
| **P4 TSX 인라인** | 정적 1건 제거 · 동적 6건 CSS 변수 대입 · 게이트 g | 5파일 7곳 | 게이트 green | 작다 — P3 에 합칠 수 있다 |
| **P5 문서·갤러리** | `docs/design-system.md`(토큰표 · 프리미티브 사용법 · 「새 화면 만들 때」 점검표) · `design-preview` 를 프리미티브 갤러리로 · `to-spec` 디자인 제약 절과 `design-review` §0 정본 표를 새 게이트로 갱신 | 문서 3~4개 | 문서가 실물과 대조된 표만 담음 | 없음 |

순서는 P0 → P1 → P2a → **P3(+P4) → P2b** → P5 ⟨2026-09-24 advisor ① 권고로 P3 를 P2b 앞으로 — 게이트 f 가 P2b 의 새 리터럴 유입을 막고, 두 단계가 `upload.css` 를 함께 건드려 동시 진행이 안 된다⟩. P2 의 분할은 Q6(단계당 PR 1건 순차)의 형태 안에서 단계 수만 늘린 것이며 원한 결과는 같다. **P0+P1+게이트에서 멈추는 선택지**(Q6)도 성립한다 — 가장 큰 표류원(토큰 산재·죽은 선언)을 막고 새 표류를 게이트가 잡는 상태까지만 가는 안이며, 보정 층과 중복 클래스는 그대로 남는다.

## 4. Ted 판정 항목

| # | 물음 | 권장 | 근거 |
|---|---|---|---|
| Q1 | BF-13 ⑶ 을 집행해 공유 토큰을 `tokens.css` 로 물리 이동하는가 | 예 · **대안 B** 로 | BF-13 완료 정의 ⑶ 원문 「세 파일에 공통인 이름은 `tokens.css` 로 올릴지 화면 로컬로 둘지 판정한다(「셸이 실제로 쓰는 토큰만 옮긴다」는 `tokens.css` 머리말과 부딪히지 않게)」 — 판정은 **열린 채**였고, evidence 의 「화면로컬 유지」는 2026-09-11 독립 수용 문구이며 Ted 원문 판정은 찾지 못했다. `tokens.css:4` 머리말 「쓰지도 않는 값이 먼저 굳는다」와 부딪히지 않는 형태 = **대안 B**: 둘 이상 화면이 쓰거나 정본과 겹치는 이름만 정본으로, 한 화면 전용 이름은 그 화면 루트 클래스 범위로(`:root` 0건은 똑같이 달성). 대안 A(38종 전부 정본) 는 머리말과 부딪힌다 |
| Q2 | `@layer` 를 도입하는가 | 예 · P2 한 PR 안에서 전 파일 | 로드 순서 의존과 `:is(.colab-ui …)` 특이도 부풀림을 없앤다. 2022년 이후 전 주요 브라우저 지원. 중간 상태 위험은 §2-1 |
| Q3 | 집행을 독립 게이트(`gates/tools` + selftest)로 두는가, vitest 원문 시험으로 두는가 | 독립 게이트 | `gates/README` 표와 CI `frontend-gates` 잡에 실리고 세 상태를 강제한다. 수정별 잠금은 vitest 병행 |
| Q4 | 시각 값 변경 0 을 완료 조건으로 못 박는가 | 예 | 09-12 시각 intent 는 재개봉 금지. 구조 작업과 시각 정정을 섞으면 캡처 대조가 판정력을 잃는다. 시각 정정은 이슈별 별건(#124·#125) |
| Q5 | 인라인 스타일의 허용 범위 | CSS 변수 대입만 | 데이터 기반 폭·색(그래프·진행률)은 남아야 한다 |
| Q6 | 범위 — 전 단계(P0~P5)인가, P0+P1+게이트에서 멈추는가 | 전 단계 · 단계당 PR 1건 순차 | 비용은 §3 규모 열. 프리미티브 이동은 전 파일을 건드려 레인 병렬 불가. 멈추는 안은 표류 방지까지만 얻는다 |
| Q7 | calm 이 없는 두 문맥(design-preview `design=before` · `?design=` 없는 `audit-design.html`)을 유지하는가 | 폐기 | P1 뒤에는 calm 이 유일한 값이 되어 그 모드는 뜻을 잃는다 |
| Q8 | 픽셀 대조 도구(devDependency 1개)를 들이는가 | 예 | 없으면 「시각 변경 0」을 사람 눈과 계측값으로만 판정한다(§2-3) |

## 5. 범위 밖

- 색·크기·여백 값의 변경, 토큰 이름 개편, 여백·글자 눈금 확정, React 프리미티브 컴포넌트, Tailwind·CSS-in-JS·컴포넌트 라이브러리·stylelint 도입(Q8 의 대조 도구만 예외 후보).
- 열린 시각 이슈 #124(표 폭)·#125(미리보기 진행 표시) — 각자 intent 1건.
- 09-12 라운드 파일 `R-DESIGN-CONSISTENCY-FULL-20260912.md` 의 미체크 항목 정리(증거는 `full/gate-summary.json` 4/4 green · `execution-status.json` 으로 존재하고 라운드 파일 스스로 「실행 상태의 실측 결과와 대조한다」고 적었다 · legacy 라운드라 건드리지 않음).
- 새 BF 번호·결정번호 발급.

## 6. 참조

- 정본: `frontend/src/shell/tokens.css` · `.agents/skills/design-review/SKILL.md §0` · `.agents/skills/apple-design/SKILL.md`
- 선행 결정: `dev-package/intent/2026-09-12-design-consistency.md` · `dev-package/prd/specs/S-DESIGN-CONSISTENCY-FULL-20260912.md` · `dev-package/work-items.yaml` BF-11·BF-13 · `PLAN-SoT.md §9 〈331〉`
- 검수: `dev-package/reports/design-review/20260912/findings.md` D17·D18(공통화 설계 후보 — 이 계획이 그 둘의 집행이다)
- 계측: `survey.md` · `css_audit.md`(같은 디렉터리)
- 검토: advisor ① 2026-09-24 approve-with-changes(교정 8건 반영 · 미확인으로 남긴 것 = vitest 정규식과 `@layer` 의 상호작용 · pretendard 로드 위치 · product.md §3/§5 대조 → P1·P2 spec 의 정책 대조 절에서 잰다)
