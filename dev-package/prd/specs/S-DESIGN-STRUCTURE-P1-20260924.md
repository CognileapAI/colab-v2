# Spec: 디자인 구조 P1 — 토큰 정본 단일화(대안 B) · 집행 게이트 `frontend-design-lint`
출처 intent: `dev-package/intent/2026-09-24-design-system-structure.md` (승인 2026-09-24 · Q1 대안 B · Q3 독립 게이트 · Q4 시각 변경 0 · Q7 calm 없는 모드 폐기)
계획: `dev-package/reports/design-system/20260924/architecture.md §2-1·§2-2·§3 P1` · 선행: P0 `S-DESIGN-STRUCTURE-P0-20260924.md`(캡처·대조 도구 · 완료)

## 문제 진술
- 토큰 정의가 정본 `frontend/src/shell/tokens.css` 밖 7개 CSS 파일의 `:root` 에 77건 있다. 그중 23종은 정본과 이름이 겹치고(다크 값만 정본에 있는 17종 + 정본 calm 값과 다른 죽은 선언 5종 + 같은 값 중복 1종), 7종은 둘 이상 파일이 쓰는 공유 어휘이며, 22종은 한 화면만 쓴다.
- 정본 자체가 두 겹이다 — 기본 `:root`(셸 토큰)와 `:root[data-design="calm"]`(09-12 승격 토큰). 제품은 `index.html` 이 `data-design="calm"` 을 항상 붙여 calm 값만 쓴다. calm 이 없는 문맥은 preview 의 「기존 복구 화면」 모드뿐이며 Q7 로 폐기가 결정됐다.
- 새로 흩어지는 것을 막는 게이트가 없다. BF-13 시험(`shared-css-tokens.test.ts`)은 화면 파일끼리 값이 같은지만 본다.

## 해법 개요
- `tokens.css` 를 **라이트 `:root` 한 블록 + 다크 `[data-theme="dark"]` 한 블록 + 640px 분기** 로 편다. calm 블록의 선언을 기본 `:root` 로 합치고 `[data-design="calm"]`·`body.design-preview` 스코프를 없앤다(제품 값 무변 — calm 이 항상 이기고 있었다).
- 화면 파일 `:root` 77건을 대안 B 로 처리한다 — 겹침 23종은 정본으로(라이트 값 이동 17 · 죽은 선언 삭제 5 · 중복 삭제 1), 공유 7종은 정본으로 승격, 한 화면 전용 22종은 그 화면 **루트 클래스 범위**로 옮긴다. 화면 파일에 `:root`·`@import` 가 남지 않는다.
- 게이트 `frontend-design-lint` 를 세 상태·selftest 로 세워 a(정본 밖 `:root` 토큰 정의 0) · b(미정의 참조 0) · c(다크 누락 0) · d(화면 CSS 의 `:root`·`@import` 0) 를 잰다. `gates/run.sh`·`gates/README.md`·CI `frontend-gates` 잡에 등록한다.
- 보이는 값은 바뀌지 않는다 — P0 도구로 착수 HEAD 기준 캡처 → 수정 뒤 대조 → 196장 엄격 차이 0.

## 사용자 스토리
1. 화면을 고치는 작업자로서 토큰 값을 `tokens.css` 한 곳에서 찾고 싶다, 같은 이름을 네 파일에서 대조하지 않기 위해.
2. 다크 테마를 확인하는 사람으로서 한 이름의 라이트·다크 값을 나란히 보고 싶다.
3. 검토자로서 새 PR 이 화면 파일에 `:root` 를 다시 만들거나 없는 토큰을 참조하면 게이트가 red 를 내길 바란다.
4. Ted 로서 이 정리 뒤에도 화면이 픽셀 단위로 같음을 대조 보고서로 확인하고 싶다.

## 구현 결정
- **토큰 정본 `frontend/src/shell/tokens.css`**
  - 구조: 머리말(개정) → `:root { … }`(라이트 전부 · 원시 눈금 → 의미 토큰 순으로 정렬 · 이름 무변) → `:root[data-theme="dark"] { … }` → `@media (max-width: 640px) { :root { … } }`. `body.design-preview` 별칭과 `[data-design="calm"]` 스코프는 지운다. 머리말은 「셸 토큰만 옮긴다 · 통째로 복사하면 안 쓰는 값이 굳는다」를 「둘 이상 화면이 쓰는 이름만 정본에 둔다 · 한 화면 전용은 그 화면 루트 범위」로 고쳐 쓴다(대안 B 의 규칙을 파일이 스스로 말하게).
  - 이동 목록(실측 2026-09-24 · HEAD a98b084b · 레인이 착수 시 재계측해 표로 남긴다):
    - 라이트 값 이동 17: `--color-accent-50/200/500/700` · `--color-gray-100/200/600/700` · `--color-primary-50/100/200/800` · `--color-success-50/100/600` · `--color-warning-50/600` — 화면 파일의 값을 `:root` 로 옮긴다(값 무변 · 파일 간 값 동일은 BF-13 시험이 보증).
    - 죽은 선언 삭제 5: `--color-border-control`(catalog·upload) · `--color-surface-alt`(catalog·project) · `--text-h2`(detail·project) · `--color-danger-600`(upload) · `--color-text-subtle`(upload) — 정본 값이 이미 이기고 있으므로 화면 값은 지운다.
    - 중복 삭제 1: `--color-text-on-primary`(upload).
    - 공유 승격 7: `--font-data` · `--radius-lg` · `--radius-pill` · `--shadow-lg` · `--color-ai` · `--text-h3` · `--weight-heading` — 정본 `:root` 로.
    - 한 화면 전용 22(upload 9 · detail 6 · lineage 3 · toast 3 · preview 1): 그 파일의 루트 클래스 블록으로(`.up { --up-…: }` · `.detail-page { … }` · toast·lineage·preview 는 레인이 실제 최상위 클래스를 확인해 정한다). 루트 밖에서 참조되는 이름이 있으면 그 이름은 승격 목록으로 올리고 표에 적는다.
  - `members.css` 의 `@import '../../shell/tokens.css'` 를 지운다(`styles.ts` 가 이미 싣는다).
  - 다크 블록: 라이트에만 있는 색 계열 이름이 0 이 되게 한다. 별칭(`var()` 값) 토큰은 대상이 덮이면 덮인 것으로 본다. 테마 무관 이름(`--color-white` · `--shadow-sm` 등)은 `gates/fixtures/frontend-design-lint/same-in-dark.txt` 에 사유와 함께 적는다(면제 건수 노출).
- **`index.html` · audit 진입점**: `data-design="calm"` 속성과 `audit-design.tsx` 의 `design=calm|full` 분기 중 토큰 스코프에 기대던 부분을 정리한다(`full` 의 GNB 포함 여부는 유지). `design-preview.html` 의 「기존 복구 화면」(`design=before`) 선택지를 지운다(Q7). `README-audit.md` 의 URL 예시를 맞춘다. **`scenes.json` 은 바꾸지 않는다**(명세 sha256 이 바뀌면 P0 기준과 대조 불가 · 쿼리 `design=full` 은 그대로 동작해야 한다).
- **`design-system.css`** 는 P1 에서 건드리지 않는다(P2). `.design-preview` 클래스 선택자는 남아도 무해하다.
- **게이트 `frontend-design-lint`** (`gates/tools/frontend-design-lint.sh` + 판정부 `frontend/scripts/design-lint.mjs` · zero-dependency · `frontend-fixture-reach.sh` 와 같은 골격):
  - 대상 = `git ls-files 'frontend/src/**/*.css'`(주석 제거 뒤 계측). 대상 0건 → red(준비 · 78). `node` 부재 → 78.
  - a. `tokens.css` 밖 파일의 `:root` 블록 안 `--*:` 정의 > 0 → red(파일·이름 열거). 화면 루트 클래스 범위의 `--*` 정의는 허용.
  - b. 어느 파일에서든 `var(--x[, …])` 의 `--x` 가 저장소 어디에도(정본 `:root`·다크·화면 루트 범위 포함) 정의되지 않으면 red(폴백 유무 무관). 오늘 값 2(`--text-title-sm` · `--color-surface-muted`)와 정본 밖 이름 참조 8건은 레인이 정본 이름으로 고치거나 이름을 정의한다 — 값을 지어내지 않고, 뜻이 같은 기존 토큰이 없으면 Ted 판정 항목으로 올린다.
  - c. 라이트 `:root` 의 색 계열 이름(`--color-*`·`--fg-*`·`--bg-*`·`--accent-*`·`--shadow-*`)이 다크 블록에 없고 `same-in-dark.txt` 에도 없으면 red. 다크 블록에만 있는 이름도 red. 면제 목록은 건수와 사유를 요약줄에 낸다.
  - d. `tokens.css` 밖 CSS 의 `:root` 셀렉터 · `@import` → red.
  - 요약줄: `파일 N · :root 정의 밖 a · 미정의 참조 b · 다크 누락 c(면제 m) · :root/@import d` · exit 0/1/78. `COLAB_GATE_REPORT_DIR` 배출 규약 준수.
  - selftest `frontend-design-lint-selftest.sh`: `gates/fixtures/frontend-design-lint/{green,red-a,red-b,red-c,red-d}/` 트리를 `COLAB_FRONTEND_DIR` 로 가리켜 대조군 green 1 + red 4 + 대상 0건 78 + node 부재 78 을 증명한다(`frontend-fixture-reach-selftest` 와 같은 꼴).
  - 등록: `gates/run.sh` case 2개 · `ALL_GATES`·selftest 목록 · `gates/README.md` 행 2개(왜 있는가 · red 조건 · 78 조건 · 세는 단위) · `.github/workflows/ci.yml` `frontend-gates` 잡에 step 1개(`verify_evidence.py record --check frontend-design-lint`).
- **기존 시험**
  - `frontend/test/shared-css-tokens.test.ts`(BF-13) 폐기 — 대상이 0건이 된다. 오라클은 게이트 a 가 승계.
  - `dev-package/work-items.yaml` BF-13 `evidence` 에 한 줄 추가: 「2026-09-24 P1: 완료 정의 ⑶ 판정 = 공유 이름은 tokens.css 로(대안 B) · ⑴ 시험은 게이트 `frontend-design-lint` a 로 승계·폐기」. `status`·번호·다른 필드 무변. `work-item-consistency` 게이트 green 확인.
  - `project-css-tokens.test.ts` · `css-residual-rc11.test.ts` · `design-fix-20260908.test.ts` 는 `:root { }` 평문 블록에서 토큰을 읽으므로 정본 `:root` 로 합치면 그대로 통과해야 한다. 깨지면 **시험을 넓히지 말고** 원인을 보고한다(시험이 잡은 것이 실제 회귀일 수 있다).
- 스키마 · 마이그레이션: 없음. API 계약: 비파괴 · 변경 없음.

## 시험 결정
- 외부 행위 기준 검증 항목:
  - ⓐ 게이트 `frontend-design-lint` green — 요약줄에 `:root 정의 밖 0 · 미정의 참조 0 · 다크 누락 0(면제 m) · :root/@import 0`. 착수 HEAD 에서는 같은 게이트가 **red(a=77 · b=2 · c=17+ · d=8)** 임을 먼저 기록한다(게이트가 실제로 재는 증거).
  - ⓑ selftest 6 케이스 전부 기대 종료코드.
  - ⓒ 시각 변경 0 — 착수 HEAD 에서 `npm run visual:capture -- --label p1-before`(빌드 포함), 수정 뒤 `--label p1-after --skip-build`, `visual:diff` **196장 엄격 차이 0 · exit 0**. 차이가 있으면 장면·픽셀·원인을 표로 내고 멈춘다(Ted 판정 · 「의도한 정정」으로 넘기지 않는다).
  - ⓓ `frontend-typecheck` · `frontend-test`(BF-13 시험 폐기 뒤 건수를 적는다) · `frontend-fixture-reach` · `work-item-consistency` green.
  - ⓔ 정본 파일 실측표 — 이동·삭제·승격·범위 이동 각 건수와 이름이 spec 의 목록과 같은지, 다르면 무엇이 달랐는지.
  - ⓕ 09-12 `full/visual-review.md` 의 「전부 tokens.css로 물리적으로 옮겼다고 주장하지 않는다」에 대응하는 결과 문장을 보고서에 둔다(옮긴 것 · 범위로 내린 것 · 남긴 것).
- 재사용 seam: P0 캡처·대조 · `css_audit.py`(계측 참고) · `frontend-fixture-reach.sh` 골격 · vitest CSS 원문 시험. 신설 seam: 게이트 1 + selftest 1 + 면제 목록 파일 1.
- 해당 서비스 단독 게이트 이름: `frontend-design-lint` · `frontend-design-lint-selftest` · `frontend-typecheck` · `frontend-test` · `frontend-fixture-reach` · `work-item-consistency`.
- green-by-skip 방지: 대상 0건 78 · 착수 HEAD red 기록 · 면제 건수 요약줄 노출 · selftest red 픽스처.

## 정책 대조 (작성 시점 제약)
- `.agents/rules/product.md §3` 불변 규칙 중 저촉 항목: 없음. 절대경로 없음. 생성물 무변.
- `§5` 중 저촉 항목: 없음(새 의존성 0 · 게이트 우회 0). legacy 대장은 BF-13 evidence 한 줄만(정합 게이트로 확인) · 새 BF·결정번호 없음.
- 계약 동결 해제 필요: 아니오.

### 디자인 제약 확인
대상 화면: 전 화면(토큰 정의 위치만 바뀐다) · 정본 `frontend/src/shell/tokens.css`
| 항목 | 충족/미충족/해당 없음 | 근거 |
|---|---|---|
| 토큰만 사용 (파일별 `:root` 전역 없음) | 충족(이 spec 의 목표) | 게이트 a·d |
| 글자 13px 이상 · 대비 4.5:1 | 해당 없음(값 무변) | 캡처 차이 0 이 증명 |
| 카드 그림자 0 · 여백 컨테이너 소유 · 인터랙션 하한 | 해당 없음(규칙 무변) | 같음 |

## 우려 항목 (판정 필요)
| # | 항목 | ⓐ | ⓑ | 권고 |
|---|---|---|---|---|
| 1 | 정본 밖 이름 참조 8건(`--lin-over-ink`×3 · `--radius-pill`×2 · `--color-surface-muted` · `--up-muted` · `--text-title-sm`)의 처리 — 뜻이 같은 기존 토큰이 없을 때 | 폴백 값으로 새 이름을 정본에 만든다 | 그 자리를 기존 토큰으로 바꾸고 캡처 차이가 나면 Ted 판정 | ⓑ · 새 토큰 이름은 Ted 판정 뒤에만(`design-review` §4) |
| 2 | 한 화면 전용 토큰의 루트 클래스가 포털·모달 밖(예: `document.body` 에 붙는 toast)에서 참조되면 범위가 안 닿는다 | 승격(정본으로) | 포털 루트에 클래스 부여(TSX 변경) | ⓐ · P1 은 `src/**/*.tsx` 를 건드리지 않는다 |
| 3 | `tsconfig.audit.json` 타입 검사가 게이트 밖(P0 후속) | `frontend-typecheck` 에 두 번째 tsconfig 를 더한다 | 별건 | ⓑ · 이 spec 범위 밖으로 두고 후속 항목으로 남긴다 |
| 4 | 캡처 구동부·명세를 도는 게이트(P0 후속) | 이번에 `frontend-visual-diff` 게이트 신설 | P1 완료 조건 ⓒ 로만 강제 | ⓑ · 매 단계 ⓒ 가 돈다. 게이트 승격은 P3 뒤 판정 |

## 범위 밖
- `design-system.css` 해체 · `@layer` · 프리미티브(P2). 색 리터럴·폴백 정리(P3 — 단, 게이트 b 가 요구하는 **미정의** 참조만 P1 에서 고친다). TSX 변경. 토큰 이름 개편·값 변경.
- 커밋·push·PR 게시(사용자) · 배포.

## 산출 계획
- 라운드 파일: 없음. 진행 = 이 spec + `dev-package/reports/design-system/20260924/p1/report.md`(ⓐ~ⓕ · 게이트 3계수 · 실측표 · 하지 않은 것) + `p1/visual/report.md`.
- 예상 레인 수: 1(직렬) · `lane-worker` · `isolation: worktree` · 기준 = `claude/design-system-structure` 최신. P0 와 별도 PR(P0 PR 병합 뒤 `develop` 대상으로 연다 · 스택 PR 금지).
- 로컬 PR 요약: `~/.claude/pr-bodies/PR-BODY-design-structure-p1.md`(오케스트레이터).
