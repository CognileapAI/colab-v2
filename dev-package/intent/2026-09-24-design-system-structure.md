# Intent: 전체 UI 의 디자인 적용 구조를 표준화·안정화한다 — 토큰 정본 단일화 · 프리미티브 단일 소유 · 집행 게이트
메타 — 발의자: Ted · 작성 2026-09-24 · 승인: **2026-09-24 Ted 원문 "권장안대로 하자."**(Q1~Q8 권장안 전부 수용 · advisor ① approve-with-changes 반영판을 그대로 승인)

## 문제
- 09-12 승인 intent(`2026-09-12-design-consistency.md`)로 **보이는 디자인**은 그 회차 `source_digest` 시점 기준 전 화면에 적용됐다(전체 확장 회차 게이트 4/4 green · 이후 UI 커밋은 이슈별 검증). 그러나 적용 **구조**는 화면마다 다르다 — 토큰 어휘가 정본 `tokens.css` 밖 7개 파일의 `:root` 에 77건 흩어져 있고, 그중 5종은 정본 값과 달라 조용히 무시된다. 한 이름의 라이트 값은 화면 파일에, 다크 값은 정본에 있다. 09-12 회차 스스로 「전부 tokens.css로 물리적으로 옮겼다고 주장하지 않는다」고 남겼다.
- 공통 부품(`.btn`·`.chip`·`.card`·모달·표)을 여러 파일이 각자 정의한다(`.chip` 7파일 · 모달 6계열). React 프리미티브는 0개다. 「calm」 디자인은 `design-system.css` 가 화면 선택자 약 190개를 덮어쓰는 보정 층이며, 이기는 근거는 로드 순서다.
- 새 화면·새 수정마다 같은 표류가 다시 생긴다. 막는 장치는 「화면 파일끼리 값이 갈리면 red」(BF-13) 하나이고, 정본과 갈리는 것·새로 흩어지는 것을 막는 게이트는 없다. 「시각 변경 0」을 증명할 캡처 구동부·대조 도구도 없다. 사용자 관점 결과 = 화면마다 미세하게 다른 버튼·칩·여백, 수정할 때마다 다른 파일이 깨지는 회귀.

## 원한 결과 (proposed outcome)
- `tokens.css` 가 저장소에서 **유일한 `:root`** 이고, 둘 이상 화면이 쓰는 모든 토큰 이름의 라이트·다크 값이 그 파일 안에 나란히 있다. 한 화면 전용 토큰은 그 화면 루트 클래스 범위에만 있다. 화면 CSS 의 `:root`·`@import` 는 0건이다.
- 공통 클래스는 **클래스마다 소유 파일 하나**다(`shell/primitives.css`). 화면 파일은 그 화면의 배치만 가진다.
- 층 순서를 `@layer tokens, base, primitives, patterns, screens` 로 선언해 로드 순서가 결과를 바꾸지 않는다. `design-system.css` 보정 층은 소유자로 흡수돼 사라진다.
- 새 게이트 `frontend-design-lint` 가 세 상태(선언·명시 면제·미선언 red)로 위 성질을 잰다 — 정본 밖 `:root` 토큰 정의 0 · 미정의 참조 0 · 다크 누락 0 · 프리미티브 중복 정의 0 · 정본 밖 색 리터럴 0 · TSX 인라인 리터럴 0. red 픽스처 selftest 로 fail-closed 를 증명한다.
- **보이는 값은 바뀌지 않는다.** 단계마다 착수 HEAD 에서 기준 캡처(30장면 이상 × 3폭 × 2테마)를 만들고 수정 뒤 픽셀 대조로 차이 0 을 보인다. 차이는 표로 내고 Ted 가 판정한다. 그 도구 자체를 먼저 만든다(P0).
- 「새 화면을 만들 때」 점검표와 토큰·프리미티브 표가 `docs/design-system.md` 에 있고, 그 내용은 게이트가 재는 것과 같다.

## 영향 범위
- 사용자 / 화면: 전 화면(12페이지). 시각 변경 0 이 완료 조건.
- 파일: `frontend/src/shell/*.css`(tokens · 신설 base·primitives·patterns · design-system 해체 · styles.ts) · `frontend/src/components/**/*.css` 13개 · `frontend/src/auth/login.css` · TSX 인라인 7건 · `frontend/test/shared-css-tokens.test.ts`(폐기) · `dev-package/work-items.yaml` BF-13 evidence(완료 정의 ⑴ 의 시험 폐기 반영 · 새 번호 없음) · `gates/run.sh`·`gates/tools/`·`gates/fixtures/frontend-design-lint/`·`gates/README.md` · `.github/workflows/ci.yml` `frontend-gates` 잡 · 캡처 구동부·대조 스크립트(P0) · `docs/design-system.md` · `.agents/skills/design-review/SKILL.md §0` · `.agents/skills/to-spec/SKILL.md` 디자인 제약 절.
- 서비스 · 스키마 · 계약: 없음. API·DB·마이그레이션 변경 없음.
- 계약 파괴 여부: 아니오.

## 제약
- 시각 값(색·크기·여백·글꼴)을 바꾸지 않는다. 09-12 시각 intent 는 재개봉 금지이며 이 intent 는 그 아래의 구조만 다룬다. 시각 정정은 이슈별 별건(#124·#125).
- 토큰 **이름**은 유지한다. 이름 개편·여백/글자 눈금 확정은 범위 밖. 여백 리터럴 729건·글자 크기 리터럴 213건은 계측만 하고 red 조건에 넣지 않는다(눈금 없이 막으면 값을 지어낸다).
- `tokens.css` 머리말 「쓰지도 않는 값이 먼저 굳는다」를 지킨다 — 정본으로 올리는 것은 둘 이상 화면이 쓰거나 정본과 겹치는 이름뿐(대안 B).
- 새 도구(Tailwind·CSS-in-JS·컴포넌트 라이브러리·stylelint)를 들이지 않는다. 예외 후보는 픽셀 대조용 devDependency 1개뿐이며 Ted 판정(Q8). 판정부는 레포 관행대로 `gates/tools/` 스크립트 + selftest.
- `@layer` 는 한 PR 안에서 전 파일에 한 번에 적용한다 — 층에 넣지 않은 규칙이 모든 층을 이기므로 중간 상태를 만들지 않는다. 외부 CSS(pretendard)의 층 배치를 명시한다.
- 게이트 우회·범위 축소 금지. 대상 파일 0건은 red(준비 · 78). 면제는 `allow.txt` 에 건수가 드러나게.
- 단계당 spec 1 · 레인 1 · PR 1. PR 게시는 사용자가 한다. 레인은 파일 면이 겹치므로 병렬하지 않는다.
- BF-13 완료 정의 ⑶ 은 「올릴지 둘지 판정한다」로 열려 있다 — 이번 판정(Q1)이 그 집행이다. legacy 대장 변경은 evidence 갱신과 `work-item-consistency` green 으로 정합을 유지하고 새 BF·결정번호는 만들지 않는다. 승인 전에는 화면 파일 `:root` 를 옮기지 않는다.

## 설계트리
- Q1 BF-13 ⑶ 을 집행해 공유 토큰을 `tokens.css` 로 물리 이동하는가 → **권장 예 · 대안 B.** ⑶ 원문 「세 파일에 공통인 이름은 `tokens.css` 로 올릴지 화면 로컬로 둘지 판정한다(…머리말과 부딪히지 않게)」는 열린 판정이고, evidence 「화면로컬 유지」는 2026-09-11 독립 수용 문구다(Ted 원문 판정 미발견). 대안 B = 공유·겹침 이름만 정본, 한 화면 전용 이름은 화면 루트 클래스 범위. `:root` 0건은 같고 머리말과 부딪히지 않는다. 대안 A(38종 전부)는 머리말과 부딪힌다.
- Q2 `@layer` 를 도입하는가 → **권장 예.** 로드 순서 의존과 `:is(.colab-ui …)` 특이도 부풀림을 없앤다. 전 주요 브라우저 지원. P2 한 PR 안에서 전 파일.
- Q3 집행을 독립 게이트로 두는가, vitest 원문 시험으로 두는가 → **권장 독립 게이트.** `gates/README` 표·CI 잡에 실리고 세 상태를 강제한다. 수정별 잠금은 vitest 병행.
- Q4 시각 값 변경 0 을 완료 조건으로 못 박는가 → **권장 예.** 구조 작업과 시각 정정을 섞으면 캡처 대조가 판정력을 잃는다.
- Q5 인라인 스타일 허용 범위 → **권장 CSS 변수 대입만**(`style={{'--w': v}}`). 데이터 기반 폭·색은 남아야 한다.
- Q6 범위·순서 → **권장 전 단계 P0 증명 도구 → P1 토큰 정본 통합 + 게이트 → P2 프리미티브 단일 소유 + @layer + 보정 층 해체 → P3 화면 CSS 색 리터럴·폴백 정리(+P4 인라인) → P5 문서·갤러리.** 더 싼 선택지 = **P0+P1+게이트에서 멈추기**(표류 방지까지만 · 보정 층·중복 클래스는 남는다). 규모 추정은 `architecture.md §3`.
- Q7 calm 이 없는 두 문맥(design-preview `design=before` · `?design=` 없는 `audit-design.html`) → **권장 폐기.** P1 뒤에는 calm 이 유일한 값이다.
- Q8 픽셀 대조 도구(devDependency 1개)를 들이는가 → **권장 예.** 없으면 「시각 변경 0」을 사람 눈과 `frontend-visual` 계측값으로만 판정한다.

## 미해결 질문
- 없음. Q1~Q8 은 2026-09-24 권장안으로 판정됐다. 아래는 판정이 아니라 spec 단계의 계측 항목이다.
- 게이트 c(다크 누락)와 죽은 폴백의 오늘 값 [미계측] — P1 spec 작성 시 계측한다.
- vitest CSS 원문 시험의 정규식이 `@layer { }` 감싸기에 깨지는지 [미확인] — P2 spec 에서 먼저 잰다.
- 09-12 의 30장면이 #73~#123 로 바뀐 화면을 덮는지 [미계측] — P0 에서 잰다.

## 범위 밖 (명시 제외)
- 색·크기·여백 값 변경, 토큰 이름 개편, 눈금 확정, React 프리미티브 컴포넌트, 새 도구 도입(Q8 예외 후보 제외).
- 이슈 #124·#125 및 다른 시각 결함 — 각자 intent.
- 09-12 라운드 파일의 미체크 항목 정리(legacy · 증거는 실행 상태 파일에 있다).
- 새 BF 번호·결정번호 발급. 커밋·push·PR 게시·배포·이슈 댓글.

## 확인
- 프론티어 공집합 확인: 2026-09-24(grill-me 미실행 · 조사 결과와 advisor ① 검토로 합성한 초안을 eli7 설명 뒤 Ted 가 항목별로 확인)
- Ted 방향 지시 문장(원문 그대로): "전체 ui에 대해 디자인 시스템을 구축하고 적용하면서 표준화되고 안정화된 디자인 적용 구조를 만들고 싶다" (2026-09-24)
- Ted 확인 문장(원문 그대로): "권장안대로 하자." (2026-09-24 · Q1 대안 B · Q2 예 · Q3 독립 게이트 · Q4 예 · Q5 CSS 변수 대입만 · Q6 전 단계 순차 · Q7 폐기 · Q8 예)
- 재개봉 금지: 예 (Q1~Q8 을 다시 묻지 않는다. 계측 결과가 전제와 어긋나면 그 값을 보고서에 남기고 해당 spec 에서 다룬다)

## 참조
- 계획·실측: `dev-package/reports/design-system/20260924/architecture.md` · `survey.md` · `css_audit.md`
- 선행 intent: `dev-package/intent/2026-09-12-design-consistency.md`(승인) · spec `dev-package/prd/specs/S-DESIGN-CONSISTENCY-FULL-20260912.md` · 회차 증거 `dev-package/reports/design-consistency/20260912/full/`(`gate-summary.json` · `execution-status.json` · `visual-review.md`)
- 검수: `dev-package/reports/design-review/20260912/findings.md` D17·D18
- 대장: `dev-package/work-items.yaml` BF-11·BF-13(완료 정의 ⑶) · `PLAN-SoT.md §9 〈331〉`
- 정본: `frontend/src/shell/tokens.css`(머리말) · `.agents/skills/design-review/SKILL.md §0`
- spec: P0 `dev-package/prd/specs/S-DESIGN-STRUCTURE-P0-20260924.md`(작성 중) · P1~P5 는 단계 착수 시
- 결정: 미부여
