# 디자인 구조 P1 결과 — 토큰 정본 단일화(대안 B) · 게이트 `frontend-design-lint`

spec: `dev-package/prd/specs/S-DESIGN-STRUCTURE-P1-20260924.md` · intent: `dev-package/intent/2026-09-24-design-system-structure.md` · 계획: `dev-package/reports/design-system/20260924/architecture.md §2-1·§2-2·§3 P1` · 선행: `p0/report.md`

착수 HEAD `51648762` · task `8e021e5608634778b0a905bf52a206d1` · 레인 1(직렬)

## 진행 상태

| 단계 | 상태 |
|---|---|
| 1 착수 캡처 · 손 계측 | 완료 |
| 2 게이트 `frontend-design-lint` + selftest · 등록 · 착수 CSS red 기록 | 완료 |
| 3 `tokens.css` 재구성 · 화면 `:root` 제거 | 완료 — 게이트 green(a 0 · b 0 · c 0(면제 6) · d 0) |
| 4 preview 경로(Q7) | 완료 — 제안 × 어둡게 agent-browser 확인 |
| 5 시험 · 대장 | BF-13 시험 폐기 · 대장 1줄 · **`preview-slot-4x3` 1건 red — 멈춤(판정 대기)** |
| 6 시각 변경 0 대조 | 완료 — 196장 엄격 차이 0 · exit 0 |
| 7 게이트 | green 5 · red(판정) 1(`frontend-test` · 단계 5 멈춘 항목) · red(준비) 0 |

## ⓐ 게이트 — 착수 red

### 착수 캡처(단계 1)

- `npm run visual:capture -- --label p1-before`(audit 빌드 포함) · 03:06:59~03:15:02 UTC · PNG 196장 + `index.json`(`captureCount` 196 · 명세 sha256 `d6983d71…` · `gitHead` `51648762` · `gitDirty` false · `built` true · 2병렬).

### 손 계측(단계 1 · 두 방법)

| 항목 | spec 예상 | node 판정부 초판(면제 목록 비움) | python 정규식 대조 |
|---|---:|---:|---:|
| a 정본 밖 `:root` 정의 | 77 | 77 | 77 |
| b 미정의 참조 | 2 | 2(`--text-title-sm` login.css:198 · `--color-surface-muted` deletion.css:10) | 같은 2 |
| c 다크 누락 | 17+ | 19 = 다크에만 17 + 라이트에만 2(`--color-white` · `--shadow-sm`) | — |
| d 화면 CSS `:root`·`@import` | 8 | 9 = `:root` 8블록(upload 2 · catalog · detail · project · lineage · toast · preview) + `@import` 1(members) | 9 |

### 게이트 red(단계 2 · CSS 무변 · 면제 2건 등록 뒤)

`gates/run.sh frontend-design-lint` → **exit 1**

```
파일 19 · :root 정의 밖 77 · 미정의 참조 2 · 다크 누락 17(면제 2) · :root/@import 9 · 범위 색 토큰 0(다크 미검사)
design-lint-counts files=19 a=77 a_root=77 a_scoped=0 b=2 c=17 c_missing=0 c_dark_only=17 c_holes=0 exempt=2 d=9 scoped_color=0 tokens=1
```

## ⓐ 게이트 — 최종(단계 7)

`COLAB_TASK_ID=8e021e5608634778b0a905bf52a206d1 gates/run.sh task` → **exit 1 · 계 green 5 / red(판정) 1 / red(준비) 0**. 요약 JSON = git common dir 기준 `colab-harness/1e175b30943cec0a49a50bc054005cf7/8e021e5608634778b0a905bf52a206d1/<run>/gate-summary.json`(run id 는 최종 실행의 것 · handoff 줄에 실린다). `~/.colab-v2-test.env` 존재 확인 뒤 실행.

| 게이트 | 결과 | 요약 |
|---|---|---|
| `frontend-design-lint` | green | 파일 19 · :root 정의 밖 0 · 미정의 참조 0 · 다크 누락 0(면제 6) · :root/@import 0 · 범위 색 토큰 0(다크 미검사) |
| `frontend-design-lint-selftest` | green | 검사 8건 전건 기대대로 (green 1 · red 5 · red(준비) 2) |
| `frontend-typecheck` | green | tsc --noEmit 오류 0건 |
| `frontend-test` | **red(판정)** | Test Files 1 failed · 128 passed (129) · Tests 1 failed · 1609 passed (1610) — `preview-slot-4x3.test.tsx` 「비율은 CSS 한 자리(토큰)에서 온다」 1건(단계 5 멈춘 항목) |
| `frontend-fixture-reach` | green | 도달 203(진입점 제외 202) · 금지 모듈 0 |
| `work-item-consistency` | green | 대장과 산문의 불일치 0 |

착수 → 최종: a 77 → 0 · b 2 → 0 · c 17(면제 2 · 목록 없이 19) → 0(면제 6) · d 9 → 0.

## ⓑ selftest

`gates/tools/frontend-design-lint-selftest.sh` → exit 0 · 「검사 8건 전건 기대대로 (green 1 · red 5 · red(준비) 2)」. 각 red 는 계수 줄(`a_root=1 a_scoped=1` · ` b=1 ` · `c_missing=1 c_dark_only=1` · ` d=1 ` · `c_holes=3`)로 그 규칙 때문에 red 임을 확인한다.

## spec 과 다르게 한 점

1. **d 의 `@import` 범위 = 화면 CSS(`src/shell/` 밖)**. spec 게이트 절은 「tokens.css 밖 CSS 의 `:root` 셀렉터 · `@import`」, 해법 개요·ⓐ 는 「화면 CSS 의 `:root`·`@import` 0」이다. `shell/shell.css` 의 `@import './tokens.css'`·`'./design-system.css'` 는 셸 진입 CSS 가 정본을 싣는 경로이고(`styles.ts` → `shell.css`), `architecture.md §2-2` d 의 오늘 값 「7 · 1」도 셸을 세지 않는다. `:root` 셀렉터는 tokens.css 밖 전부(셸 포함)를 센다. README 「못 보는 것」에 적었다.
2. **판정부 위치** — 픽스처 트리에 판정부 사본을 두지 않고 게이트가 저장소의 `frontend/scripts/design-lint.mjs` 하나를 부른다(`frontend-fixture-reach` 는 트리마다 사본). 0건 케이스용 `empty/` 트리를 spec 의 여섯 트리에 더했다.
3. **등록 두 곳 추가** — `gates/config/parallelism.toml`(`scripts/harness/check.py` 가 `ALL_GATES ⊆ parallelism` 을 강제) · `.agents/ci-producers.json`(`verify_evidence.py record --check` 가 등록을 요구).
4. **면제 목록 부재 = red(준비 · 78)** — spec 의 78 조건(대상 0건 · node 부재)에 더했다. 목록이 없으면 c 를 판정할 수 없다.
5. **b 의 정의 집합에 TS/TSX 의 `'--x'` 문자열을 넣었다** — `style={{'--w': v}}`·`setProperty('--x')` 로 넣는 이름(오늘 `Gnb.tsx` 의 `--shell-gnb-offset` 1건 · CSS 에도 정의됨). architecture P4 가 허용하는 데이터값 대입 경로를 b 가 red 로 막지 않게.

## ⓔ 정본 실측표(단계 3)

화면 `:root` 선언 77건 = catalog 18 · detail 26 · project 8 · upload 18(두 블록 6 + 12) · lineage 3 · toast 3 · preview 1. 전부 화면 파일에서 없앴다.

| 처리 | spec | 실제 | 이름 |
|---|---:|---:|---|
| 라이트 값 이동(다크는 이미 정본) | 17 | 17 | `--color-accent-50/200/500/700` · `--color-gray-100/200/600/700` · `--color-primary-50/100/200/800` · `--color-success-50/100/600` · `--color-warning-50/600` |
| 공유 승격 | 7 | 7 | `--font-data` · `--radius-lg` · `--radius-pill` · `--shadow-lg` · `--color-ai` · `--text-h3` · `--weight-heading` |
| 정본 계열 이름 승격 | 9 | 9 | `--space-1` · `--space-2` · `--leading-body-sm`(upload) · `--space-4/5/6` · `--color-on-dark` · `--color-on-dark-muted` · `--color-band-dark-2`(detail) |
| 접두사 이름 → 루트 밖 참조로 **승격** | 0 | 9 | `--up-line` · `--up-muted` · `--up-ink` · `--up-warn` · `--up-warn-bg` · `--up-radius` · `--lin-over-bg` · `--lin-over-ink` · `--lin-over-name` |
| 접두사 이름 → 화면 루트 범위 | 13 | 4 | `--toast-fg` · `--toast-bg` · `--toast-radius` → `.toast` · `--pv-frame-ratio` → `.pv-frame-wrap` |
| 죽은 선언 삭제 | 5 | 5 | `--color-border-control`(catalog·upload) · `--color-surface-alt`(catalog·project) · `--text-h2`(detail·project) · `--color-danger-600`(upload) · `--color-text-subtle`(upload) |
| 중복 삭제 | 1 | 1 | `--color-text-on-primary`(upload) |
| **정본으로 합계** | 33 | **42** | 위 17 + 7 + 9 + 9 |

접두사 이름 9종을 범위가 아니라 정본으로 올린 근거(spec 「루트 밖에서 참조되는 이름이 나오면 승격 목록으로 올리고 표에 적는다」):

- `--up-*` 6 — spec 이 적은 `.up { }` 루트 클래스는 **저장소에 없다**(TSX 의 `className` 에 `up` 0건). 참조 셀렉터가 업로드 모달(`.modal-takeover`) · 확인 대화상자(`.confirm-back`) · 미완 업로드 배너(`.up-banner` · `UnfinishedUploads.tsx`) 세 루트에 흩어져 있고, `.btn` · `.btn-primary` · `.muted` · `.inp` · `.sel` 처럼 **앱 전역에 걸리는 셀렉터**(`upload.css:109·258·312·314`)도 이 이름을 읽는다. 한 루트 범위로 내리면 그 밖의 요소에서 값이 사라진다.
- `--lin-over-*` 3 — 참조 요소가 연결 단계 루트 `.lin`(`LineageStep.tsx:239`)과 계보 고치기 모달 루트 `.lin-fix`(`LineageFixModal.tsx:114`) 두 곳에 있다. `ParentPicker` 가 두 루트 모두에서 렌더되고(`.lin-picker` · `.lin-over-why`), `.lin-fix-method-l` 은 모달에만 있다. 한 루트 범위로는 닿지 않는다.
- 범위로 내린 4종은 참조 셀렉터가 전부 그 루트 요소 자신이거나 그 자손이다 — `--toast-*` 는 `.toast` 규칙 한 곳에서만 읽고, `--pv-frame-ratio` 는 `.pv-frame`(`PreviewSlot.tsx` 에서 늘 `.pv-frame-wrap` 의 자식)에서만 읽는다.

미정의 참조 2 · 정본 밖 이름 참조 8 처리:

| 참조 | 처리 | 근거 |
|---|---|---|
| `login.css:198` `var(--text-title-sm, 18px)` | `var(--text-h3)` | 같은 뜻(`h3` 글자 크기) · 같은 값 18px 인 기존 토큰(이번에 정본으로 승격) |
| `deletion.css:10` `var(--color-surface-muted, transparent)` | `transparent`(리터럴 키워드) | 이름이 정의된 적이 없어 **늘 폴백 `transparent` 가 렌더됐다.** 뜻이 같은 기존 토큰 중 값이 `transparent` 인 것은 없다 — 새 값을 지어내지 않고 렌더되던 값을 그대로 적었다. 채울지(`--color-surface-alt` 등)는 **Ted 판정 항목**으로 남긴다 |
| `--lin-over-ink` ×3(`lineage.css` 폴백 `#5b6472`) | 정본 승격으로 정의됨 | 폴백 `#5b6472` 는 종전에도 렌더되지 않았다(정의가 늘 있었다) · 후속 항목 |
| `--radius-pill` ×2 · `--up-muted` ×1 | 정본 승격으로 정의됨 | — |

`tokens.css` 구조: 머리말(대안 B 규칙) → `:root`(calm 블록 합침 · 원시 눈금 → 의미 토큰 → 글자 → 간격 → 셸 → 여러 루트 접두사 이름) → `@media (max-width: 900px)` → 다크 → `@media (max-width: 640px)`. 합칠 때 겹친 이름 2종(`--leading-body` 1.467/1.6 · `--tracking-body` 0.0096em/0)은 제품이 늘 쓰던 calm 값을 남겼다.

다크 짝: 라이트 색 계열 이름 중 다크 블록에 없는 6종을 `same-in-dark.txt` 에 사유와 함께 적었다 — `--color-white` · `--shadow-sm` · `--shadow-lg` · `--color-band-dark-2` · `--color-on-dark` · `--color-on-dark-muted`. 다크 값을 새로 만든 이름은 0.

### `<html>` 유효 토큰 값 대조(정적 · 캡처와 별개)

`styles.ts` 적재 순서(`@import` 펼침)대로 `:root` 계열 규칙을 특이도·순서로 풀어, 제품 문맥(`html[data-design=calm][data-theme=light|dark]`) · 폭 1440/800/375 에서 착수 HEAD 와 수정본의 `<html>` 사용자 정의 속성 값을 이름마다 비교했다. **차이 24 = 범위로 내린 4종 × 6 조합뿐**(루트에서 사라짐 · 의도). 나머지 이름은 두 테마·세 폭 모두 값이 같다 — 죽은 선언 6종이 실제로 가려져 있었다는 확인이기도 하다.

## preview 경로(단계 4 · Q7)

| 파일 | 변경 |
|---|---|
| `frontend/index.html` | `data-design="calm"` 삭제 — 읽는 CSS·코드 0건(저장소 전체 검색 · `tokens.css` 의 calm 스코프가 마지막 독자였다) |
| `frontend/audit-design.tsx` | `design=calm` 분기: 테마를 `document.body.dataset.theme` → `document.documentElement.dataset.theme` 에 건다(`body.design-preview` 클래스는 유지 · `design-system.css` 는 P2). `design=full` 분기의 `dataset.design = 'calm'` 삭제(GNB 포함 여부 무변) |
| `frontend/audit-upload.tsx` | `dataset.design = 'calm'` 삭제(같은 이유) |
| `frontend/design-preview.html` · `design-preview.js` | 「기존 복구 화면」(`design=before`) 선택지와 그 전용 분기(테마 잠금·안내문) 삭제 |
| `frontend/README-audit.md` | 제안 경로 URL 꼴(`/audit-design.html?design=calm&theme=dark&scene=catalog`) 추가 |
| `frontend/src/shell/tokens.css` | 위 수정 뒤 `body.design-preview[data-theme="dark"]` 별칭 삭제 |
| `frontend/scripts/visual-baseline/scenes.json` | **무변** |

실제 확인(agent-browser · audit 빌드 `vite preview` 127.0.0.1:4391):

- `design-preview.html?scene=catalog&design=calm&theme=dark&width=1440` — 디자인 선택지 1개(「제안」) · 테마 값 `dark` · iframe `src` = `/audit-design.html?scene=catalog&design=calm&theme=dark` · 화면이 어두운 바탕으로 그려짐(스크린샷 확인).
- iframe 문서 직접 열기(같은 URL) — `html[data-theme]` = `dark` · `body[data-theme]` 없음 · `body.className` = `design-preview` · `body` 계산 배경 `rgb(17, 22, 29)`(= 다크 `--color-bg` `#11161d`) · 글자 `rgb(237, 242, 247)`(= 다크 `--color-text` `#edf2f7`).
- `audit:build`(`tsc --noEmit -p tsconfig.audit.json` 포함) exit 0.

`calm` 이 없던 문맥의 값 변화(캡처 밖 · Q7 로 폐기된 모드): `audit-selected-preview.html` 과 `design` 인자 없는 `audit-design.html` 은 종전 calm 스코프 밖이라 기본 `:root` 값(`--leading-body` 1.467 · `--tracking-body` 0.0096em · calm 전용 이름 미정의)을 썼다. 이제 제품과 같은 값을 쓴다. 제품(`index.html`)과 캡처 33장면(`design=full`·`audit-upload`)은 종전에도 calm 값이었다.

## 시험 · 대장(단계 5)

- `frontend/test/shared-css-tokens.test.ts`(BF-13) 삭제 — 대상(화면 `:root`)이 0건이 됐다. 오라클은 게이트 a 가 승계.
- `vitest run`(삭제 뒤): **Test Files 1 failed | 128 passed (129) · Tests 1 failed | 1609 passed (1610)**.
- `css-residual-rc11.test.ts` — 통과. spec 의 처리 기준(기대값이 죽은 선언 값과 같으면 calm 값으로 고침)을 적용할 자리가 없었다 · 고친 기대값 0.
- **멈춘 항목 — `test/preview-slot-4x3.test.tsx:100`** 「비율은 CSS 한 자리(토큰)에서 온다 — 4 / 3」:

  ```
  AssertionError: 선택자 부재: :root: expected -1 to be greater than -1
   ❯ block test/preview-slot-4x3.test.tsx:45:37
  ```

  시험이 `preview.css` 안의 `:root` 블록에서 `--pv-frame-ratio: 4 / 3` 를 찾는다. spec 은 화면 CSS 의 `:root` 를 0 으로 만들라고 하고(게이트 d), 이 이름을 preview 루트 범위로 옮기라고 한다 — **두 요구가 동시에 참일 수 없다.** spec 이 예상한 실패(`css-residual-rc11` 의 죽은 값)가 아니므로 spec 의 규칙(「그 밖의 실패는 시험을 넓히지 말고 멈추고 보고한다」)대로 시험을 고치지 않았다. 값·렌더는 같다(`.pv-frame` 의 `aspect-ratio: var(--pv-frame-ratio)` 무변 · 값 `4 / 3` 은 `.pv-frame-wrap` 범위로 이동 · 시각 대조는 단계 6).
  제안(판정 뒤 1줄): `expect(block(CSS, ':root'))` → `expect(block(CSS, '.pv-frame-wrap {'))`. 오라클(비율이 CSS 한 자리 토큰에서 온다 · 값 4 / 3)은 그대로다.
- `dev-package/work-items.yaml` BF-13 `evidence` 끝에 한 문장 추가: 「2026-09-24 P1: 완료 정의 ⑶ 판정 = 공유 이름은 tokens.css 로(대안 B) · ⑴ 시험은 게이트 `frontend-design-lint` a 로 승계·폐기.」 `status`·번호·다른 필드 무변. `gates/run.sh work-item-consistency` → exit 0 「대장과 산문의 불일치 0」.

## ⓒ 시각 변경 0(단계 6)

- 기준 `p1-before`: HEAD `51648762`(착수) · audit 빌드 포함 · 03:06:59~03:15:02 UTC.
- 후보 `p1-after`: HEAD `7d662b9b`(단계 5 커밋 · CSS·preview 경로 변경 전부 포함) · `gitDirty` false · **audit 다시 빌드**(`--skip-build` 없이 · CSS 변경 뒤 번들을 새로 만들어야 하므로) · 03:26:57~03:34:47 UTC · 196장.
- `npm run visual:diff -- .visual/p1-before .visual/p1-after .visual/p1-report` → **196 captures · red 0 · strict px 0 · exit 0**. 보조 차이 0 · 크기 차이 0 · 명세 sha256 `d6983d71…` 두 쪽 같음.
- 보고: `p1/visual/report.md` · `p1/visual/report.json`.
- 캡처 33장면은 전부 `audit-design.html?design=full` 또는 `audit-upload.html` 경로다 — `design=calm`(제안) 경로는 단계 4 의 agent-browser 확인이 본다.

## ⓕ 09-12 「전부 tokens.css 로 물리적으로 옮겼다고 주장하지 않는다」에 대한 결과

- **옮겼다** — 화면 `:root` 선언 77건 전부를 화면 파일에서 없앴다. 정본 `tokens.css` 로 온 이름 42종(라이트 값 17 · 공유 7 · 정본 계열 9 · 여러 루트가 참조하는 접두사 9) · 지운 선언 6(죽은 5 · 중복 1). calm 블록도 기본 `:root` 로 합쳐 정본은 라이트 `:root` 한 블록 + 다크 한 블록 + 분기 둘이다.
- **범위로 내렸다** — 한 컴포넌트 루트 안에서만 읽히는 4종: `--toast-*` 3 → `.toast` · `--pv-frame-ratio` → `.pv-frame-wrap`.
- **남긴 것** — 화면 CSS 의 색·여백 리터럴과 `var()` 폴백 리터럴(P3) · `design-system.css` 의 `.design-preview` 셀렉터(P2) · 다크 값이 없는 색 이름 6종(면제 목록에 사유와 함께) · `shell/shell.css` 의 `@import` 둘(셸 진입 경로).
- 게이트 `frontend-design-lint` 가 이 상태를 매 PR 에서 잰다(CI `frontend-gates`).

## 하지 않은 것

- `frontend/src/**/*.tsx` · `design-system.css` · `scenes.json` 변경 0. 토큰 값 변경 0 · 새 토큰 이름 0 · 다크 값 신설 0.
- `test/preview-slot-4x3.test.tsx:100` 수정 — 멈춘 항목(단계 5).
- `deletion.css` `.dl-keep` 바탕을 토큰으로 채우는 결정 — Ted 판정 항목.
- `tsconfig.audit.json` 을 `frontend-typecheck` 에 넣기(spec 우려 3 · 범위 밖) · 시각 대조 게이트 승격(우려 4 · P3 뒤 판정).
- 커밋 push · PR 게시 · 병합.

## 후속 항목

1. `preview-slot-4x3.test.tsx:100` 의 셀렉터를 `.pv-frame-wrap {` 로 바꿀지 판정(위 단계 5). 이 1건이 남는 동안 `frontend-test` 는 red(판정)다.
2. `deletion.css:10` `.dl-keep` 바탕 — 이름(`--color-surface-muted`)이 뜻한 채움이 한 번도 렌더되지 않았다. `--color-surface-alt` 로 채울지 Ted 판정(시각 변경이 생긴다).
3. `lineage.css` 의 `var(--lin-over-ink, #5b6472)` 3곳 — 주석은 안내 줄을 `#5b6472` 로 설명하지만 이름이 늘 정의돼 있어 실제로는 `--color-warning-600` 이 렌더된다. 폴백 정리(P3) 때 의도를 확인한다. 어느 검사에도 걸리지 않는다(게이트 b 는 정의 여부만 본다).
4. `--up-*` 6종은 업로드 CSS 의 전역 셀렉터(`.btn`·`.muted`·`.inp`·`.sel`)가 읽어서 정본에 올렸다. P2 에서 이 셀렉터들이 프리미티브로 흡수되면 정본 의미 토큰으로 바꾸고 `--up-*` 를 없앨 수 있다.
5. `.up { }` 루트가 저장소에 없는데 spec 이 그것을 전제했다 — P2 spec 작성 때 업로드 화면 루트를 실측으로 다시 잡는다.
6. 게이트 c 는 색 계열 접두사(`--color-`·`--fg-`·`--bg-`·`--accent-`·`--shadow-`)만 본다 — 정본의 `--up-*`·`--lin-over-*` 는 별칭이라 오늘은 다크를 따라가지만, 누가 리터럴 색을 넣으면 c 가 못 본다(README 「못 보는 것」에 적음).
