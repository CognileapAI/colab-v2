# 핫픽스 레인 `hotfix-upload` — 업로드 마법사 4건 (2026-09-08 · X-9)

- 기준 `origin/integration/hotfix-upload` `ccf76ec` · 제품 코드 `frontend` 만 · 계약 0 · 마이그레이션 0.
- 진단 정본 `dev-package/reports/R-D/upload-step3-overlap-20260908.md` · `git diff --stat origin/main -- services contracts db` **0행**.

## RED 선실측 → GREEN

- 1차(모듈 부재) `Failed to resolve import "../src/components/upload/registerError"` · `Tests no tests`.
- 2차(스텁 뒤 전건 계측) `Tests 13 failed | 4 passed (17)` — 판정 문장 발췌: `expected '.up-card > .card-b' to contain '.card.is-on > .card-b'` · `선택자 부재: [data-testid="reg-s3"]` · `expected 'htmlFor="reg-name">데이터셋 이름' to contain '<span className="reqtag">필수</span>'` · `expected undefined to be '기간의 종료는 시작보다 앞설 수 없다.'` · `expected null to deeply equal { step: 2, …(1) }`.
- GREEN `Tests 17 passed (17)` — `frontend/test/upload-hotfix-20260908.test.ts`.

## 고친 것

| 건 | 자리(전 → 후) | 요지 |
|---|---|---|
| F1 기간 역전 | `periodParts.ts` 신설 `isPeriodInverted`·`PERIOD_INVERTED_MESSAGE` / `PeriodCalendarPopover.tsx` `적용` 무검사 → `disabled={inverted}` ＋ `reg-period-pop-error` / `RegisterArea.tsx` 기간 `form-row.daterange` 안 `reg-period-error` 신설 / `UploadModal.submit()` 역전이면 `goStep(2)`＋`failAt(2,…)`＋`return` | 요청 전 차단 · 문면은 서버 축자 재사용 |
| F2 오류 단계 범위 | `registerError.ts` 신설(`{step,message}`·`messageForStep`·`clearedOnStepChange`) / `UploadModal.tsx` `registerError: string` → `registerErrorAt` ＋ `failAt`·`failAnywhere`·`goStep` | ③ 이 ② 문면을 내지 않는다 · 단계 이동 시 초기화 |
| F3 필수 배지 | `RegisterArea.tsx` `htmlFor="reg-name"` 라벨에 `<span className="reqtag">필수</span>` | `설명` 과 같은 배지 하나 |
| F4 카드 간격 | `upload.css` `.up-card > .card-b` → `.card.is-on > .card-b,` 한 줄 추가 / `.up-steps` → `[data-testid="reg-s3"],` 한 줄 추가 | 기존 선언(`gap:12px`·`16px`) 재사용 |

- 치수 토큰 실측 = `src/shell/tokens.css` 에 간격(space·gap) 토큰 **0건**(색·글자·둥근 모서리·그림자만) ·
  이웃 규칙도 px 리터럴. 그래서 새 리터럴 없이 **선택자만** 넓혔다. `members.css` 무변.
- `step: null` = 파일 소실·접수 끊김·격자 후주입 — 단계 무관이라 종전대로 어느 단계에서도 보인다.

## 고치지 않은 것 (의도)

- 글자 크기 13px 미만 29건 승격(진단 §3-(1)) · `.regprev` 위치 이동(§3-(2) ⑵) — **R-E 이월**.
- 서버 기간 검사 · 필수 칸 강제 범위 · 값 clamp·swap — 무변.
- 과표기 1건 `가공 단계`(`reg-level`) — 배지 있고 강제 없음(기본값 `Lv2`). 지시문대로 강제를 만들지 않았다.

## 계측

- `npx vitest run` 전체 `Test Files 81 passed (81)` · `Tests 1100 passed (1100)` — 회귀 0. `npx tsc --noEmit` 오류 0.
  ⚠ 1차 전체는 `Tests 2 failed | 1098 passed (1100)` — 원인은 이 레인의 선택자 확장이 `css-residual-rc11.test.ts` 문자열 탐침(`'.up-card > .card-b '`·`'.up-steps '` 끝 공백 포함)을 깨뜨린 것. 새 선택자를 **앞줄**로 옮겨 원문 탐침을 보존했고 재실행이 위 값이다.
- 게이트 6건 · 배출처 `dev-package/reports/HF/hotfix-upload/<게이트>/` · 요약줄 축자 —
  - `frontend-typecheck green — tsc --noEmit(frontend/tsconfig.json · include=src·test) 오류 0건.`
  - `frontend-test green — vitest run(frontend/vite.config.ts · jsdom) 통과 1100건 · 실패 0건.`
  - `frontend-fixture-reach green — 진입점 src/main.tsx 에서 도달 174개(진입점 제외 173개), 금지 모듈 0건.`
  - `frontend-visual green(명시 면제) — COLAB_VISUAL_EXEMPT=1 로 선언됨. 페이지 0건 · small 0건 · lowContrast 0건.`
  - `exec-bit green — '.sh' 176건 전부 인덱스 모드 100755 (100644 = 0건).`
  - `work-item-consistency: green — 대장과 산문의 불일치 0`
- **3계수 = green 6 / red(판정) 0 / red(준비) 0**(실행마다 `계 : green 1 / red(판정) 0 / red(준비) 0`).
- ⚠ `gates/run.sh` 는 한 번에 게이트 **하나**만 받는다(`usage: gates/run.sh <gate> | all [-j N]`) —
  요약 JSON 이 실행마다 한 건이라 게이트 이름별 하위 폴더로 갈라 두었다.

## intent 대조 — Ted 불만 3건

- 「깨진다」(③ 겹침) → F4 2건. **충족** — 다만 계측은 CSS 원문 대조이고 실화면 픽셀 교차는 미측정.
- 「다음이 동작하지 않는다」 → F1 요청 차단 ＋ F2 단계 범위. **부분** — 진단 §3-(2) 는 그 화면의 `다음` 정지 원인을 **분석 미완**(`status.ready === false`)으로 실측했고 그 원인은 서버측이라 이 레인 범위 밖이다.
- 「필수 값 표기」 → F3 1건. **충족**(강제 칸 기준). 과표기 1건은 판정 대기.
- **미달 4** = 글자 크기 승격 · 기간 표시 줄 위치(둘은 R-E · X-10 이월) · `가공 단계` 과표기 판정(Ted 판정 대기) · ⭑ ⟨advisor ② 정정⟩ **「다음이 동작하지 않는다」의 실측 원인 `status.ready === false`(서버측 분석 준비 · X-9 범위 밖 · 별건 조사 중)** — 범위 밖이 미달을 없애지 않는다.
- **초과 1** = 팝오버 안 오류 문장 `reg-period-pop-error`. 지시문이 「버튼 비활성 ＋ 인라인 메시지」를 허용했고, 비활성만 남기면 이유가 화면에 없어 두 번째 침묵이 된다. 새 문면 아님(서버 축자 재사용).

## 후속 항목

1. `가공 단계` 필수 배지 — 걷을지 강제할지 판정(진단 §3-(3)).
2. 실화면 겹침 오라클 부재 — `frontend-visual` 은 앱을 향해 읽기 전용이라(`gates/tools/frontend-visual.sh`) 클릭으로만 열리는 업로드 모달을 계측 대상에 넣지 못하고, 판정 축도 `small`·`lowContrast` 둘뿐이라 겹침 축이 없다. **검사가 게이트 밖에도 없다** — 그 자체가 결함이므로 별도 WU 필요.
3. `status.ready` 가 `.bin.gz` 에서 서지 않는 원인 — 서버 로그 미열람(진단 §3-(2) `[미상]`).
