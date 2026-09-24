# 디자인 구조 P2a 결과 — 보정 층 `design-system.css` 흡수 · `@layer` 도입

spec: `dev-package/prd/specs/S-DESIGN-STRUCTURE-P2A-20260924.md` · 조사: `p2/design-system-map.md` · 선행: `p0/report.md` · `p1/report.md`

착수 HEAD `7967e001` · task `b3a0acddb8904144b566f2539b3f93fb` · 레인 1(직렬)

## 결론

- `design-system.css`(192규칙 · 621 선언 단위)를 소유 파일로 흡수해 삭제했다. `@layer tokens, base, primitives, patterns, screens` 를 첫 CSS 로 싣고 `tokens.css` 는 `tokens` 층, 나머지 CSS 17파일은 `screens` 층이다.
- 시각 변경 0 — `visual:diff` **196 captures · red 0 · strict px 0 · exit 0**(ⓑ).
- 렌더 계산값 0 차이 — 착수 빌드와 최종 빌드를 같은 196 페이지에서 **모든 요소·가상요소(`::before`·`::after`·`::placeholder`·`::marker`)의 계산 스타일 전 속성**으로 대조해 차이 0(캡처보다 엄격한 보조 오라클 · 아래 ⓑ′).
- 상태 강제 계측 16건 전후 동일(ⓒ).
- **판정 뒤 해소 — 종전 `frontend-test` red(판정) 1**: `test/dashboard.test.tsx` 「검색 히어로의 좌우 여백은 뿌리 여백과 겹치지 않는다」가 `maxWidth 680px` 를 기대하는데 `720px` 이 나온다. 680px 은 제품에서 **렌더된 적이 없는 값**이다(보정 층 `.lab-page .search-hero { max-width: 720px }` 이 접두 특이도로 덮었고, jsdom 시험에는 `.colab-ui` 가 없어 보정 층이 안 걸렸다). 흡수로 720px 이 소유 파일(`search.css`)로 오면서 시험이 처음으로 제품 값을 본다. 시험을 고치지 않고 판정을 요청했고, 오케스트레이터 승인(ⓐ 720px)으로 기대값을 바꿨다(아래 「기존 시험 변경」).

## 진행 상태

| 단계 | 상태 | 커밋 |
|---|---|---|
| 1 착수 캡처 `p2a-before` | 완료 | — |
| 2 판정 도구 `cascade-map.mjs` · 지도 | 완료 | `088f6be6` · `7e85d0e6` |
| 3 흡수 · `design-system.css` 삭제 | 완료 | `d9aafcee` · 잔여 되살아남 6곳 `f78f878c` |
| 4 `@layer` · 게이트 d 범위 · lint 사각 3건 | 완료 | `f8e99708` |
| 5 vitest 껍질 제거 플러그인 · 시험 경로 | 완료(판정 1건 승인 뒤 기대값 변경) | `5e85c477` · 기대값 `3323376c` |
| 6 상태 계측 | 완료(16건 동일) | `f78f878c` |
| 7 시각 변경 0 | 완료 — 196장 엄격 차이 0 · exit 0 | `12b29144` |
| 8 게이트 | 완료 — green 5 / red(판정) 0 / red(준비) 0 · exit 0 | — |
| 9 보고서 | 이 문서 | 이 커밋 |

## 단계 1 — 착수 캡처

- `npm run visual:capture -- --label p2a-before`(audit 빌드 포함) · 03:52:40~04:00:59 UTC · PNG 196장 + `index.json`(`captureCount` 196 · 명세 sha256 `d6983d71…` · HEAD `7967e001` · 미커밋 변경 없음 · 빌드 포함).
- 같은 빌드 산출물을 `frontend/.visual/p2a-dist-before/` 에 보관해 상태 계측·계산값 대조의 「전」 쪽으로 썼다(로컬 · 추적 안 함).

## 단계 2 — 판정 도구 `frontend/scripts/cascade-map.mjs`

- 의존성 0. `map --rev <착수>` = 적재 순서(styles.ts · shell.css `@import` 펼침 · `deletion.css` 는 컴포넌트 import 라 뒤)대로 19파일 규칙 1307개를 파싱해, DS 규칙마다 (선택자 인자 × 선언) 단위의 경쟁 규칙·오늘의 승자·되살아남 후보를 낸다. 특이도는 `:is()`·`:not()`·`:has()` = 인자 최대 · `:where()` = 0 · 접두 +0,1,0 · 옮긴 뒤는 `:is()` 인자별.
- `verify --base <착수> --exempt <면제>` = 작업 트리에서 DS 선언마다 새 자리(같은 인자·미디어·속성·값)를 찾고, 층 순위(`@layer` 선언 순서 · 층 밖이 최상)와 새 위치·특이도로 모든 경쟁 결과를 다시 계산한다. 값이 같거나 longhand 가 일치하면 무해로 본다. 비DS 선언의 삭제·변경은 「오늘 모든 문맥에서 죽음」을 선택자·미디어 포함 관계로 증명하고, 증명 못 하면 red — 사람이 확인한 경우만 사유를 적어 면제한다(`p2a/cascade-exempt.json`).
- `frontend/scripts/layer-count.mjs` = ⓐ 계수(아래).
- 산출: `p2a/cascade-map.md`·`.json`(착수 지도 · 조사 부록 A 대체) · `p2a/cascade-verify.md`·`.json`(최종 대조).
- 착수 지도 합계(현 판정부로 재생성): 선언 단위 621 · 오늘 지는 단위 49 · 되살아남 후보(키 공유 · 값 다름) 394(필연 58 · 순서 269 · 순서(셸 본문) 28 · DS쌍 39) · 그중 상태 선택자 5 · 요소/전체 compound 호환 후보 6804(그중 상태 선택자 147)(표 밖).

## 단계 3 — 흡수(ⓓ)

### 규칙 192 의 행선지(조사 §1 소유자 집계와 대조)

조사 §1: shell 21 · primitive 22 · pattern 5 · screen 137 · mixed 5 · drop 2 = 192.

| 행선지 | 규칙 |
|---|---:|
| `components/project/project.css` | 41 |
| `shell/shell.css`(셸 21 − 문서 기본 2 + 프리미티브 22 − 나눔 · 패턴 5 − 나눔) | 39 |
| `components/dashboard/dashboard.css` | 28 |
| `components/catalog/catalog.css` | 26 |
| `components/upload/upload.css` | 15 |
| `components/search/search.css` | 12 |
| `shell/shell.css` 맨 앞 문서 기본(`.colab-ui` 접두 유지 · #1 #2 #3 #107) | 4 |
| `components/preview/preview.css` · `components/lineage/lineage.css` | 4 · 4 |
| `auth/login.css` · `components/lab/lab.css` · `components/detail/detail.css` | 2 · 2 · 2 |
| `components/lineage/lineageGraph.css` | 1 |
| 나눔(인자별 여러 파일 · #5 #9 #83 #105 #106 #110 #112 #116 #117 #138) | 10 |
| 버림 — 조사 drop(#89 = #48 같은 값 · #129 = shell `:where()` focus-visible 같은 값) | 2 |
| **계** | **192** |

- 화면 규칙(137)은 조사 §1 target 파일로. 같은 선택자 규칙이 있으면 그 규칙의 값을 바꿔 넣고(병합 · 뒤 선언이 덮는 옛 longhand 는 지움), 없으면 파일 끝 표시 주석 아래에 접두 없이 새로 썼다. 미디어 안 규칙은 DS 순서를 지키려 파일 끝의 같은 조건 새 블록으로(`mediaBlock` 도우미는 같은 질의의 블록을 전부 이어 붙이므로 둘째 블록도 본다 · `media` 도우미는 첫 블록만 — 그 시험의 `.table-scroll-hint` 1100px 블록은 `shell.css` 에 하나뿐).
- 셸·프리미티브·패턴 규칙은 `shell.css` 끝(맨 앞 문서 기본 4규칙 제외). spec 은 조사 target(`primitives.css`·`patterns.css`)을 그대로 쓰라 했지만 그 파일은 P2b 가 만든다 — architecture §3 P2a 의 「소유 규칙(화면·셸 파일)」대로 셸에 두었다(아래 「spec 과 다르게 한 점」 1).
- 선언 단위 621 = 새 자리에서 같은 값으로 확인 610 + 버림 11(#89 1 · #129 10 · 사유 면제). `cascade-verify` 문제 0.

### 되살아남 후보 처리(ⓓ)

- 지도(착수)의 후보는 **새 위치에 달린 것**(순서)이 대부분이라, 실제 처리는 흡수 뒤 `verify` 가 새 위치·특이도로 다시 계산해 뒤집히는 것만 골랐다(순서 후보 중 새 자리보다 앞이거나 특이도가 낮아져도 여전히 지는 것은 처리 대상이 아니다). 판정 = 뒤집혀도 값이 같으면 무해, 다르면 경쟁 선언이 오늘 모든 문맥에서 죽었음을 증명하고 삭제 또는 값 일치.
- 비DS 선언 변경 계 146 = 삭제 52 · 값 교체 94. 그중 소유 규칙 병합(같은 선택자 규칙에 DS 값을 넣음)이 대부분이고, 경쟁 선언 삭제·일치·선택자 좁힘이 나머지다. 139건은 선택자·미디어 포함 관계로 「오늘 죽음」이 증명됐고 7건은 사유 면제(요소의 클래스 조합을 TSX 에서 확인). 전 목록 = `p2a/cascade-verify.md` 「비DS 선언 변경」(파일:행 · 선택자 · 원래 값 · 처리 · 근거).
- spec 이 이름을 적은 억눌린 상태 3건 = 전부 **삭제**(오늘 모습 유지 · 되살릴지는 후속 판정): `members.css` `.btn-primary:hover { background: var(--color-primary-700) }` · `upload.css` `.inp[readonly] { background: var(--color-surface-alt); color: var(--up-muted) }` · `lineage.css` `.lin .chip--warning { background: var(--lin-over-bg); color: var(--lin-over-ink) }`.
- 그 밖의 상태 선택자 처리: `login.css` `.login-input:focus-visible { outline: none; border-color: var(--color-primary) }` 삭제(DS#129 가 덮던 것) · `project.css` `.pcard:focus-visible { outline-offset: 2px }` 삭제 · `upload.css` `.modal-takeover button:focus-visible` 를 선택자 목록에서 뺌 · `members.css` `.btn:hover` → `.btn:where(:not(.btn-primary, .btn-secondary)):hover`(특이도 무변 · primary·secondary 의 hover 배경은 오늘도 안 보인다).
- 선택자 키 공유로 못 본 것 6곳(단계 3 뒤 계산값 전수 대조로 발견 · `f78f878c`): 위 `.btn:hover` · `catalog.css` `.tbl td.rowact { padding-right: 14px }`(th 만 남김) · `.tbl td.empty { padding: 36px 14px }` · `members.css` 640px `.memgrid .memtbl td { padding: 3px 0 }` · `project.css` `.pj-views button.on { font-weight: 600 }` · `dashboard.css` `.modal.lab-info { padding: 24px }`·640px `20px` · `upload.css` `.up-empty .up-card { border: 0 }` → `border-width: 0; border-style: none`(색 longhand 만 죽어 있었다).
- 중복 2규칙(#89 · #129) 버림. 혼합 5규칙(#9 #83 #106 #110 #112)은 인자별로 나눴다.

## 단계 4 — `@layer`(ⓐ)

- `frontend/src/shell/layers.css` = `@layer tokens, base, primitives, patterns, screens;` · `styles.ts` 첫 import(pretendard 앞) · 순서 = layers → pretendard → tokens → 화면 → shell.css. `shell.css` 의 `@import` 둘 삭제(tokens 는 styles.ts 가 싣는다).
- `node scripts/layer-count.mjs` → `layer-count files=19 wrapped=18 rules=1238 unlayered=0 design_system=0 red=0` · exit 0 — 18 = tokens 1(`@layer tokens {`) + screens 17(화면 16 + `shell.css` · `deletion.css` 포함) · 층 밖 규칙 0 · `.colab-ui` 선택자는 `shell.css` 맨 앞 4규칙에만 · `@import`/`@charset` 0. 대상 0건이면 78.
- `!important` 2건(`shell.css` 미디어 블록)은 screens 층 안 그대로.
- 게이트 d 의 `@import` 대상 = tokens.css 밖 전 CSS(셸 포함). `design-lint.mjs` 사각 3건: `html:root`(compound 의 `:root` 전부) · `CANON_PREFIX` 에 `--accent-` · 대상 목록에 있으나 디스크에 없는 파일 = 78. selftest 8 → 12건(green 2 · red 7 · red(준비) 3): `green-layer`(층 안 정본·화면) · `red-root-html` · `red-accent` · `red-d` 에 `shell.css` `@import`(d=2) · 부재 파일. **새 케이스 4건은 착수 판정부로 돌리면 red** 다(ⓔ d=2 · ⓙ · ⓚ · ⓛ 기대와 다름 → selftest exit 1). `gates/README.md` 두 행 갱신.

## 단계 5 — 시험

- jsdom 29 는 `@layer` 블록 안 규칙을 계산값에 넣지 않는다 — `test/layer-shim.test.ts` 셋째 it 가 실측한다(층 블록 안 `color` 가 계산값에 안 나오고, 껍질을 벗기면 나온다).
- `vite.config.ts` test 모드 전용 플러그인(`apply: env.mode === 'test'`) `stripLayerBlocks` — stylesheet 로 실리는 CSS(`?raw` 제외)에서 `@layer a, b;` 문장과 `@layer x {` 껍질·짝 `}` 만 벗긴다(주석·문자열 안은 그대로 · 중첩 `@media` 보존). 제품 빌드 무관 · 의존성 0. red 확인: 구현 전 3 it 전부 `TypeError: stripLayerBlocks is not a function` → 구현 뒤 3/3.
- `test.css.include` 에 `layers.css`.
- 경로만 바꾼 시험 2파일: `test/shell-lth-20260913.test.tsx`(900px · 640px 블록 → `shell.css`) · `test/account-admin-layout-20260918.test.ts`(`.table-scroll-hint` · 1100px 블록 → `shell.css` · it 제목의 파일명). 단언 값 무변.
- 결과: Test Files 1 failed | 129 passed (130) · Tests 1 failed | 1612 passed (1613). 건수 = P1 1610 + `layer-shim` 3 · 폐기 0.
- 기대값 변경 전 red 1건 = `dashboard.test.tsx` 「검색 히어로의 좌우 여백은 뿌리 여백과 겹치지 않는다」 `AssertionError: expected '720px' to be '680px'`. 원인은 결론에 적었다. 계산값 시험 나머지 5 it(뿌리 1200px 포함)는 통과 — 뿌리 `.lab-page` 1280px 규칙은 패턴이라 `shell.css` 로 갔고 대시보드 시험은 `shell.css` 를 싣지 않는다.

## ⓑ 시각 변경 0(단계 7)

- 기준 `p2a-before`: HEAD `7967e001`(착수) · audit 빌드 포함 · 03:52:40~04:00:59 UTC.
- 후보 `p2a-after`: HEAD `f78f878c`(흡수 · 층 · 잔여 6곳 전부 포함) · 미커밋 변경 없음 · audit 다시 빌드 · 05:22:12~05:30:03 UTC · 196장.
- `npm run visual:diff -- .visual/p2a-before .visual/p2a-after .visual/p2a-report` → **196 captures · red 0 · strict px 0 · exit 0** · 보조 차이 0 · 크기 차이 0 · 명세 sha256 `d6983d71…` 두 쪽 같음.
- 보고: `p2a/visual/report.md` · `p2a/visual/report.json`. red 0 이라 `visual/red/` 는 만들지 않았다.
- 캡처는 층 판정(층을 넘는 우선순위)을 실브라우저에서 본 증거다 — 층 도입 뒤 트리를 캡처했다.

## ⓑ′ 계산값 전수 대조(보조 오라클)

- 착수 빌드(`p2a-dist-before`)와 최종 빌드를 캡처와 같은 33장면 × 테마 × 폭 = 196 페이지에서 열어(같은 명세 · 저장소 비움 · 애니메이션 고정), 모든 요소와 가상요소의 `getComputedStyle` 전 속성 해시를 비교했다. 도구 = `p2a/states/cdump.py`(capture.py 재사용 · 로컬).
- 단계 3 직후(층 전) 대조: 50 페이지 · 320 요소 차이 → 원인 6곳을 고쳤다(위 「키 공유로 못 본 것」). 최종(층 포함 · `f78f878c` 트리): **196 페이지 · 차이 0**.

## ⓒ 상태 강제 계측(단계 6)

agent-browser 로 착수 빌드와 최종 빌드에서 같은 장면·폭 1440 에 상태를 강제하고 계산값을 쟀다(`hover`·`focus`(Shift 키 뒤 · `:focus-visible` 일치 확인)·`mouse down`(`:active` 일치 확인)·`readonly`/`aria-pressed` 속성). 원자료 `p2a/states/states-before.json`·`states-after.json`.

| 상태 · 대상 | 장면 | 값(전 = 후) |
|---|---|---|
| `.btn-primary:hover`(members.css 삭제 · `.btn:hover` 좁힘) | upload-link | background `rgb(19, 105, 233)` |
| `.btn-secondary:hover` | lab-dialog | background `rgb(255, 255, 255)` |
| 일반 `.btn:hover`(유지) | upload-link | background `rgb(249, 250, 251)` |
| `.btn-primary:active`(DS#83) | upload-link | background `rgb(15, 98, 224)` |
| `.search-hero button:active`(DS#83) | lab | background `rgb(15, 98, 224)` |
| `.inp[readonly]`(upload.css 삭제) | upload-metadata | background `rgb(255, 255, 255)` · color `rgb(18, 22, 25)` |
| `.login-input:focus-visible`(login.css 삭제) | login | outline `2px solid rgb(19, 105, 233)` · offset 3px · border-top-color `rgb(169, 179, 191)` |
| `.pcard:focus-visible`(outline-offset 삭제) | projects | outline 2px solid · offset 3px |
| `.modal-takeover button:focus-visible`(선택자에서 뺌) | upload | outline 2px solid · offset 3px |
| `.modal-takeover .inp:focus-visible`(유지) | upload-metadata | outline 2px solid · offset 2px |
| 일반 `button:focus-visible`(DS#129 버림) | catalog | outline 2px solid · offset 3px |
| `.lin-picker li > button[aria-pressed="true"]`(DS#170) | lineage-picker | background `rgba(105, 112, 119, 0.08)` |
| `.lin-picker li > button:hover` | lineage-picker | background 투명 · color `rgb(18, 22, 25)` |
| `.mainnav a:hover` | catalog | background `rgba(105, 112, 119, 0.08)` · color `rgb(18, 22, 25)` |
| `.gnb-upload:hover`(DS#127) | catalog | background `rgb(15, 98, 224)` · color `rgb(255, 255, 255)` |
| 표 행 hover 시 `.tbl td.rowact .ra`(opacity 삭제) | catalog | opacity 1 |

- 16건 전후 동일. `.lin-picker li > button` 은 오늘 `ParentPicker` DOM 에 없어(후보는 `label.lin-cand`) 계측 때 probe 요소 하나를 `.lin-picker` 안에 넣어 쟀다 — 규칙 판정은 같지만 **현 화면에 걸리는 요소가 없다**(후속 항목 4).
- [미측정] 없음 — 단, 계측은 위 16건이고 상태 선택자 전수를 강제하지는 않았다. 상태 선택자 전수는 특이도 범위 스캔(되살아날 수 있는 상태 규칙 51개)을 요소 클래스 조합으로 걸러 위 대상으로 줄였다(나머지는 DS 단위와 같은 요소에 걸리지 않거나 겹치는 속성이 없다).

## ⓔ 게이트(단계 8)

`COLAB_TASK_ID=b3a0acddb8904144b566f2539b3f93fb bash gates/run.sh task` → **exit 0 · 계 green 5 / red(판정) 0 / red(준비) 0**(커밋 `3323376c` · `~/.colab-v2-test.env` 존재 확인 뒤). 요약 JSON = git common dir 기준 `colab-harness/ff506810e27eac7102dde603ee891bb2/b3a0acddb8904144b566f2539b3f93fb/8c8a8d4ae56d42e1a4abe69f822821b4/gate-summary.json`. 이 표를 적은 커밋 뒤 handoff 용으로 같은 명령을 한 번 더 돌리며 그 run id 는 `COLAB_HANDOFF` 줄에 실린다.

| 게이트 | 결과 | 요약 |
|---|---|---|
| `frontend-design-lint` | green | 파일 19 · :root 정의 밖 0 · 미정의 참조 0 · 다크 누락 0(면제 6) · :root/@import 0 · 범위 색 토큰 0 |
| `frontend-design-lint-selftest` | green | 검사 12건 전건 기대대로 (green 2 · red 7 · red(준비) 3) |
| `frontend-typecheck` | green | tsc --noEmit 오류 0건 |
| `frontend-test` | green | Test Files 130 passed (130) · Tests 1613 passed (1613) = P1 1610 + `layer-shim` 3 · 폐기 0 |
| `frontend-fixture-reach` | green | 진입점 src/main.tsx 도달 205(진입점 제외 204) · 금지 모듈 0 |

이전 실행(기대값 변경 전 · 커밋 `12b29144`·`3a00bfe8`): exit 1 · green 4 / red(판정) 1(`dashboard.test.tsx:479`) / red(준비) 0.

## 시험 변경

| 시험 | 변경 |
|---|---|
| `test/shell-lth-20260913.test.tsx` | `DESIGN` 이 읽는 파일 `design-system.css` → `shell.css`(900px · 640px 블록) |
| `test/account-admin-layout-20260918.test.ts` | `DESIGN` 이 읽는 파일 → `shell.css` · it 제목의 파일명 |
| `test/layer-shim.test.ts` | 신설 3 it |
| `test/dashboard.test.tsx` | 기대값 1줄 + 주석 2줄(아래 「기존 시험 변경」 · 오케스트레이터 승인) |

## spec 과 다르게 한 점

1. 프리미티브·패턴 소유 규칙(조사 target `primitives.css`·`patterns.css`)은 `shell.css` 끝에 두었다 — 그 파일은 P2b 가 만든다(spec 「범위 밖」 · architecture §3 P2a 「화면·셸 파일」). 위치가 보정 층과 같은 자리(화면 CSS 뒤)라 순서로 이기던 것이 그대로 이긴다. P2b 가 옮길 때 cascade-map verify 로 다시 잰다.
2. 미디어 안 DS 규칙은 소유 파일의 **같은 조건 기존 블록에 병합하지 않고** 파일 끝 새 블록에 두었다 — 기존 블록은 파일 중간이라 병합하면 같은 파일 뒤쪽 동률 규칙에 지는 경우가 생긴다(착수 순서 보존). 같은 조건 블록이 파일에 둘 생긴 곳이 있다.
3. 미디어 밖 병합은 같은 선택자 규칙이 **선택자 하나일 때만**(목록 규칙이면 다른 선택자까지 바뀌므로 새 규칙). `#70 .pj-tarea`·`#179 .pj-new` 는 같은 선택자 규칙 뒤에 덮는 규칙이 있어 병합하지 않고 끝에 새로 썼다.
4. 버림은 조사의 drop 2 뿐 — 「모든 문맥에서 지는 선언 버리기」는 하지 않았다. 지는 선언을 옮겨도 렌더는 같고(특이도는 내려갈 뿐), 선택자만으로 「모든 문맥」을 증명할 수 없는 경우가 대부분이다. P2b 정리 대상.
5. `.colab-ui` 문서 기본 4규칙은 `:is(.colab-ui, .design-preview)` 접두를 그대로 둔 채 `shell.css` 맨 앞(spec 8). `base` 층·`base.css` 는 만들지 않았다(spec 층 도입 절 · 이름만 선언).
6. `.gnb` 계열의 `.colab-ui .gnb …`(`.design-preview` 없는 접두) 규칙도 접두를 뗐다 — ⓐ 「`.colab-ui` 는 맨 앞 4규칙에만」. 이 규칙은 이제 `.design-preview` 문맥(제안 · GNB 없음)에도 걸리지만 그 문맥에 GNB 가 없다.
7. 판정 도구에 `verify` 모드·면제 목록·`layer-count.mjs` 를 더했다(spec 은 지도만 요구). 면제 21건은 사유와 함께 `p2a/cascade-exempt.json`·`cascade-verify.md` 에 나온다.
8. 계산값 전수 대조(ⓑ′)를 더했다 — 선택자 키 공유 판정의 사각(같은 요소의 다른 클래스 · `className="tbl memtbl"` 등)을 잡았다.

## 하지 않은 것

- **vitest 는 층 순서를 검증하지 못한다** — test 전용 플러그인이 층 껍질을 벗기므로 시험의 계산값은 층 없는 캐스케이드다. 층 판정의 증거는 실브라우저 캡처(ⓑ)와 계산값 전수 대조(ⓑ′)다.
- 접두 없는 문맥의 값 변화: 보정 규칙은 이제 `.colab-ui`·`.design-preview` 가 없는 문서에도 걸린다 — jsdom 시험(위 red 1건이 그 결과) · `audit-design.html` 을 `design` 인자 없이 연 경우(캡처 밖 · 디버그 경로). 제품(`index.html`)·캡처 33장면·제안 경로는 종전에도 접두 문맥이었다.
- 억눌린 상태의 복원(우려 1 · 별건) · 프리미티브 추출·값 통일·게이트 e(P2b) · 토큰 값 변경(0).
- `src/**/*.tsx` 는 주석 2곳(`Gnb.tsx` · `AccountAdminPage.tsx`)만 · `scenes.json` 무변 · 새 의존성 0 · push·PR 게시.

## 기존 시험 변경

| 파일:행 | 전 → 후 | 사유 |
|---|---|---|
| `frontend/test/dashboard.test.tsx:479`(it 「검색 히어로의 좌우 여백은 뿌리 여백과 겹치지 않는다」) | `expect(cs.maxWidth).toBe('680px')` → `toBe('720px')` · 위 주석 2줄을 사실로 고침 | 09-12 승인 디자인(보정 층 `design-system.css` · P2a 에서 `search.css` 로 흡수)이 `.lab-page .search-hero { max-width: 720px }` 이고 제품 body 는 늘 `.colab-ui` 라 **2026-09-12 부터 렌더값은 720px** 이다. 종전 680px(`dashboard.css` `.lab-page .search-hero`)은 이 시험의 body 에 `.colab-ui` 가 없어 jsdom 만 보던 죽은 선언이었다. 오케스트레이터 승인(판정 ⓐ). 단독 실행 25/25 통과 |

- BF-8 의 「히어로 내용 폭 680px 불변」 문구는 09-12 intent 가 대체했다 — 이 레인에서는 대장(`work-items.yaml`)을 바꾸지 않았다(후속 6).

## 후속 항목

1. 억눌린 상태 — `.btn-primary:hover`·`.btn-secondary` hover · `.inp[readonly]` · `.lin .chip--warning` · `.login-input:focus-visible` 테두리색 · `.pcard` 초점 간격 2px — 오늘은 보이지 않는다. 되살릴지 P5 문서 「후속 판정」.
2. P2b 가 `shell.css` 끝의 프리미티브·패턴 규칙을 `primitives.css`·`patterns.css` 로 옮길 때 `cascade-map verify` 와 계산값 대조를 다시 돈다(프리미티브 층은 screens 에 진다 — 화면 쪽 옛 값 정리가 먼저).
3. `cascade-map` 의 경쟁 판정은 선택자 키 공유라 같은 요소의 다른 클래스 조합을 못 본다(이번에 계산값 대조로 6곳 발견). 계산값 대조 도구를 `frontend/scripts/visual-baseline/` 로 올려 P2b·P3 의 정식 오라클로 쓸지 판단.
4. `.lin-picker li > button` 규칙 2개(DS#169·#170 → `lineage.css`)는 현 `ParentPicker` DOM 에 걸리는 요소가 없다 — 죽은 규칙 후보.
5. 같은 조건 미디어 블록이 한 파일에 둘 생긴 곳 정리(값 무변 · P2b).
6. [오케스트레이터] BF-8 의 「히어로 내용 폭 680px 불변」 문구가 09-12 intent(720px)로 대체됐음을 대장에 반영할지 — 이 레인은 대장 무변.
