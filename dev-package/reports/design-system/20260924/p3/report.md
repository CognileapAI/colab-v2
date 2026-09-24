# 디자인 구조 P3(+P4) 결과 — 화면 CSS 색 리터럴·죽은 폴백·TSX 인라인 정리 · 게이트 f·g

spec: `dev-package/prd/specs/S-DESIGN-STRUCTURE-P3-20260924.md` · 조사: `p3/literal-map.md`(HEAD `7967e001` · P2a 전) · `survey.md §2` · 선행: `p2a/report.md`

착수 HEAD `26b8a676` · task `a48a85df6e19492ba20254a0ad6135bf` · 레인 1(직렬)

## 결론

- 게이트 `frontend-design-lint` 에 f(정본 밖 색 리터럴) · g(TSX 인라인 비변수 키)를 더했다. 착수 red **f 69 · g 7**(종전 판정부 · 현 판정부로는 f 66(면제 1) · g 8) → 최종 green **f 0(면제 1) · g 0(변수 대입 7)**. selftest 12 → **19건** 전건 기대대로. (advisor ② 반영 뒤 수치 — 아래 「advisor ② 반영」)
- CSS: 죽은 폴백 **64** 삭제 · `#fff` **2** → `var(--color-white)` · 판정 대기 **1** 면제(`.chip` `#eef2f7`) · `login.css` 토큰끼리의 `color-mix()` 2 는 f 정밀화로 리터럴이 아니다. 조사의 A 1 · B 1 · D 3 은 P2a 가 먼저 없앴다(착수 계 69 ≠ 조사 72).
- TSX 인라인 7곳(5파일)을 CSS 변수 대입 6 + 클래스 1 로, 펼침 속성 안의 8번째 자리(`PreviewPanels.tsx` `preview-layers`)도 변수 대입으로 바꿨다.
- 시각 변경 0 — `visual:diff` **196 captures · red 0 · strict px 0 · exit 0**. 계산값 전수 대조(커스텀 속성 제외) **196 페이지 · 요소·가상요소 26962 항목 차이 0**. 최종 재캡처(`p3-after2` · HEAD `5b2a2a83`)도 196장 차이 0 · 계산값 196 페이지 차이 0. 캡처가 닿지 않는 변경 자리 10종은 실브라우저 probe 로 전후 계산값 20건 동일.
- **판정 필요 1건**: 제품 시험 6파일 14곳의 단언이 인라인 값 대신 변수 값을 읽도록 바뀌었다(`search.test.tsx:175` 1 + 미리보기 변환 5파일 13 · 단언한 값은 같음 · 지시 「제품 시험 변경 0」과 다름). A 면제는 착수 코드에 A 가 없어 등록하지 않았다.

## 진행 상태

| 단계 | 상태 | 커밋 |
|---|---|---|
| 1 착수 캡처 `p3-before` · 재계측 | 완료 | — |
| 2 게이트 f·g · selftest 16 | 완료 | `844652cd` |
| 3 CSS — 죽은 폴백 64 · B 2 · 면제 3 | 완료 | `539f68ee` |
| 4 TSX 인라인 7 | 완료(제품 시험 1줄 변경 · 판정 필요) | `c80e3eab` |
| 5 캡처 범위 표 | 완료(캡처 미도달 자리는 실브라우저 probe · 나머지 [미검증] 표기) | (이 커밋) |
| 6 대장 BF-8 | 완료 | `67ce0608` |
| 7 시각 변경 0 | 완료 — 196장 엄격 차이 0 · 계산값 196 페이지 차이 0 | (이 커밋) |
| 8 게이트 | 완료 — green 6 / red(판정) 0 / red(준비) 0 | `b566e545` |
| 9 advisor ② 반영(펼침 style · g 판정 · color-mix 정밀화) | 완료 — 재캡처 196 차이 0 · green 6 | `5b2a2a83` · (이 커밋) |

## 단계 1 — 착수 캡처 · 재계측

- `npm run visual:capture -- --label p3-before`(audit 빌드 포함) · 05:45:44~05:53:34 UTC · PNG 196장 + `index.json`(`captureCount` 196 · 명세 sha256 `d6983d71…` · HEAD `26b8a676` · `gitDirty` false · `built` true) · exit 0.
- 같은 빌드 산출물을 `frontend/.visual/p3-dist-before/` 에 보관(계산값 대조의 「전」 · 로컬 · 추적 안 함).

### 색 리터럴 재계측(착수 · `frontend/src/**/*.css` · tokens.css 제외 · 주석 제외)

조사(`literal-map.md`)는 P2a 병합 **전** HEAD `7967e001` 에서 쟀다. P2a 가 보정 층 값을 소유 파일로 흡수하면서 일부 리터럴이 이미 토큰 참조로 바뀌었다.

| 분류 | 조사(7967e001) | 착수(26b8a676) | 차이의 원인 |
|---|---:|---:|---|
| A 같은 값 토큰 1개 | 1 | **0** | `project.css .pj-modal-back` background 가 P2a 흡수로 이미 `var(--color-overlay)` — 보정 층 값이 이기던 자리(spec 「P2a 뒤 실제 렌더 값을 다시 확인」의 결과) |
| B `#fff` | 3 | **2** | `catalog.css .colmenu .cm-box` color 가 P2a 흡수로 이미 `var(--color-on-primary)` — 남은 것 `detail.css .dt-edit .de-req` color · `search.css .vsw::after` background |
| C `#eef2f7` | 1 | 1 | `upload.css .chip` background |
| D 죽은 폴백 | 67 | **64** | P2a 가 경쟁 선언을 지우거나 값을 맞추며 폴백 3개가 함께 사라짐(dashboard 2→1 · search 40→38) |
| (신규) `color-mix()` | — | **2** | `auth/login.css` `.account-modal-back` · `.auth-expiry-overlay` background — 조사 정규식이 `color-mix()` 를 보지 않았다 |
| 색 이름(`white`·`black` 등 148개) | — | **0** | |
| `oklch()`/`oklab()`/`hsl()` 류 | — | 0 | |
| **계** | **72** | **69** | 직접 5(B 2 · C 1 · color-mix 2) + 폴백 64 |

D 64 파일별: search 38 · upload 9 · shell 6 · detail 3 · lineage 3 · lab 2 · preview 2 · dashboard 1.

### TSX 인라인 재계측(`style=` · `frontend/src/**/*.tsx` 91파일)

| # | 파일:행 | 키 | 종류 |
|---|---|---|---|
| 1 | `components/search/SearchHitCard.tsx:60` | `{ width }` | 동적 · **축약형** |
| 2 | `components/preview/PreviewPanels.tsx:391` | `background: c.color` | 동적(데이터 색) |
| 3 | `components/preview/PreviewPanels.tsx:487` | `position: 'absolute'` · `left`·`top`·`width`·`height` px | 정적 1 + 동적 4 |
| 4 | `components/dashboard/DataMapCard.tsx:37` | `width: …%` | 동적 |
| 5 | `components/upload/RegisterArea.tsx:1007` | `marginTop: 16` | **정적** |
| 6 | `components/upload/PreviewPanel.tsx:631` | `transform` · `transformOrigin: '0 0'` | 동적 + 정적 |
| 7 | `components/upload/PreviewPanel.tsx:794` | `transform` · `transformOrigin: '0 0'` | 동적 + 정적 |

- 7건 = spec 과 같다. 별도로 **JSX 펼침 속성 안의 `style` 키 1곳**이 있다 — `components/preview/PreviewPanels.tsx:343`(`{...(zoom ? { …, style: { transform, transformOrigin } } : {})}` · `preview-layers`). `style={…}` 속성이 아니라 spec 의 g 정의(「`style` JSX 속성의 객체 리터럴 키」) 밖이다. 게이트는 이것을 「참고 · 펼침 속성 안의 style 키」로 건수만 낸다(판정 안 함 · 아래 「하지 않은 것」).

## 단계 2 — 게이트 f·g(ⓐ 착수 red)

- 판정부 `frontend/scripts/design-lint.mjs` 에 f·g 를 더했다. 셸 `gates/tools/frontend-design-lint.sh` 는 머리 주석만(요약줄은 판정부의 `파일 …` 줄을 그대로 싣는다).
- f: 선언 값에서 문자열·`url()` 본문을 비운 뒤 색 함수(`rgb`·`rgba`·`hsl`·`hsla`·`hwb`·`lab`·`lch`·`oklab`·`oklch`·`color`·`color-mix`) · hex(3·4·6·8자리) · 표준 색 이름 148개(글꼴·애니메이션·격자·카운터 이름 속성 제외)를 찾고, 위치가 `var()` 의 첫 쉼표 뒤~닫는 괄호 안이면 폴백으로 가른다. 색 함수 안의 토큰은 다시 세지 않는다. 제외 키워드는 색 이름 목록에 없다.
- f 면제: **P1 의 면제 목록 `gates/fixtures/frontend-design-lint/same-in-dark.txt` 를 넓혔다**(spec 「파일명이 다르면 그것을 쓴다」) — 줄 형식 `f · 파일 · 선택자 · 속성 · 리터럴 · 사유`. 사유 빈칸은 red 이고 **면제하지 않는다** · 걸리는 리터럴이 없으면 낡은 항목 red · 건수는 요약줄 「색 리터럴 f(면제 m)」. c 의 「면제 m」은 c 항목만 센다.
- g: `typescript`(devDependency 5.9.3 · 판정부 위치 기준 `createRequire`)로 `.tsx` 를 `ts.createSourceFile(… TSX)` 해 `JsxAttribute` 이름 `style` 을 찾는다. 값이 `as`·괄호·`satisfies`·`!` 를 벗긴 객체 리터럴이고 키가 전부 `--` 로 시작하면 변수 대입 v, 아니면 g 1건(축약형 · 펼침 · 비리터럴 계산 키 · 객체 아닌 값 포함). 불러오지 못하면 78.
- 계수 줄 `design-lint-counts` 에 `f f_direct f_fallback f_name f_holes f_exempt f_exempted_hits g g_vars g_spread tsx` 를 더했다.

### red 확인(TDD)

- selftest 에 4건을 먼저 더하고 **종전 판정부로** 돌림 → exit 1: `ⓜ … green 이어야 하는데 red 다(rc=1)` · `ⓝ f 네 갈래 — 출력에 「f=6 f_direct=2 f_fallback=1 f_name=1 f_holes=2」이 없다` · `ⓞ g 인라인 색 · px · 축약형 — red 여야 하는데 통과했다` · `ⓟ typescript 파서 부재 — red(준비 · 78) 여야 하는데 rc=1`.
- 새 판정부 → `frontend-design-lint-selftest green — 검사 16건 전건 기대대로 (green 3 · red 9 · red(준비) 4).`
- selftest 의 `expect()` 에 갈래 하나를 더했다 — 준비 실패(`ready`)를 기대한 케이스가 판정 red(rc 1)로 끝나도 종전에는 「✓」로 통과했다(ⓟ 가 종전 판정부에서 그렇게 통과하는 것을 보고 발견). 이제 기대와 다름으로 센다. 기존 ⓖ·ⓗ 는 78 로 끝나므로 결과 무변.

### 착수 코드에 돌린 게이트(판정 red)

`bash gates/tools/frontend-design-lint.sh` → exit 1

```
f 색 리터럴(정본 밖) 69
g 인라인 style 의 비변수 키 7
참고 · 펼침 속성 안의 style 키(g 밖 · 판정 안 함) 1
파일 19 · :root 정의 밖 0 · 미정의 참조 0 · 다크 누락 0(면제 6) · :root/@import 0 · 범위 색 토큰 0(다크 미검사) · 색 리터럴 69(면제 0) · 인라인 7(변수 대입 0)
design-lint-counts files=19 a=0 … f=69 f_direct=5 f_fallback=64 f_name=0 f_holes=0 f_exempt=0 f_exempted_hits=0 g=7 g_vars=0 g_spread=1 tsx=91 tokens=1
```

- ⓐ 기대 「f ≥ 72 · g = 7」 대비: **f = 69**(위 재계측 표 — P2a 가 A 1 · B 1 · D 3 을 먼저 없앰 · color-mix 2 가 새로 걸림) · g = 7.

## 단계 3 — CSS(값 무변)

### 리터럴 처리 표

| 분류 | 건 | 처리 | 자리 |
|---|---:|---|---|
| D 죽은 폴백 | 64 | 폴백만 삭제 `var(--x, #…)` → `var(--x)` | search 38 · upload 9 · shell 6 · detail 3 · lineage 3 · lab 2 · preview 2 · dashboard 1(8파일 60줄) |
| B `#fff` | 2 | `var(--color-white)`(`tokens.css` `#ffffff` · 다크 블록에 없음 = 테마 불변 · `same-in-dark.txt` 면제 항목) | `detail.css` `.detail-page .dt-edit .de-req` color · `search.css` `.search-page .vfilter .vsw::after` background |
| B `#fff`(조사 3건째) | 0 | 없음 — P2a 흡수로 이미 `var(--color-on-primary)` | `catalog.css` `.colmenu .cm-box` color |
| A 오버레이 | 0 | 없음 — P2a 흡수로 이미 `var(--color-overlay)` | `project.css` `.pj-modal-back` background |
| C `#eef2f7` | 1 | 리터럴 유지 · f 면제(Ted 판정 대기) | `upload.css` `.chip` background |
| `color-mix()` | 2 | 리터럴 유지 · f 면제(판정 대기) | `login.css` `.account-modal-back` · `.auth-expiry-overlay` background |

- D 64 의 대상 이름 20종(`--color-border` 9 · `--color-surface` 10 · `--color-text-muted` 10 · `--color-primary-600` 6 · `--color-success-600` 6 · `--color-text-body` 4 · `--color-danger` 3 · `--lin-over-ink` 3 · `--color-warning-50` 2 · 나머지 11종 1씩)은 전부 `tokens.css` 라이트 `:root` 에 정의돼 있다 — 폴백이 렌더된 적이 없다. 증거는 단계 7(캡처 · 계산값).
- `lineage.css` `var(--lin-over-ink, #5b6472)` 3곳(`.lin-unknown:has(input:disabled) label` · `.lin-unknown-why` · `.lin-fix-method-l`): **실제 렌더 = `--lin-over-ink` → `var(--color-warning-600)`**(`tokens.css:135`). 폴백의 회색 `#5b6472` 는 렌더된 적이 없다 — 회색이 의도였는지는 P1 후속 항목 그대로.
- diff 검증: 바뀐 60줄의 `-` 쪽에서 폴백만 지운 문자열이 `+` 쪽과 바이트 동일(`cmp` 일치).
- 면제 3건은 `gates/fixtures/frontend-design-lint/same-in-dark.txt` 끝 `f · …` 줄(사유 포함). 오케스트레이터 지시의 「A · C 면제 2」와 다르다 — A 는 착수 코드에 리터럴이 없어 면제할 대상이 없고(낡은 항목은 red), color-mix 2 가 더해졌다(아래 「spec 과 다르게 한 점」).

게이트(이 단계 뒤): `색 리터럴 0(면제 3) · 인라인 7(변수 대입 0)` · `f=0 … f_exempt=3 f_exempted_hits=3 g=7` — g 가 남아 여전히 red.

## 단계 4 — TSX 인라인 7(ⓒ)

| # | 파일:행(착수) | 종전 | 이후 | 변수 이름 · CSS |
|---|---|---|---|---|
| 1 | `components/search/SearchHitCard.tsx:60` | `style={{ width }}`(축약형 · `42%` 류) | `style={{ '--hit-relbar-w': width } as React.CSSProperties}` | `--hit-relbar-w` · `search.css` `.search-page .relbar > span { width: var(--hit-relbar-w) }` |
| 2 | `components/preview/PreviewPanels.tsx:391` | `style={{ background: c.color }}` | `style={{ '--pv-swatch-bg': c.color } as …}` | `--pv-swatch-bg` · `preview.css` `.pv-swatch { background: var(--pv-swatch-bg) }` |
| 3 | `components/preview/PreviewPanels.tsx:487` | `position: 'absolute'` · `left`·`top`·`width`·`height` `${n}px` | 네 좌표만 변수 · `position` 은 클래스 규칙 | `--pv-piece-left`·`--pv-piece-top`·`--pv-piece-w`·`--pv-piece-h` · `preview.css` `.pv-mosaic .pv-tile-piece { position: absolute; left/top/width/height: var(…) }` |
| 4 | `components/dashboard/DataMapCard.tsx:37` | `style={{ width: …% }}` | `style={{ '--dash-bar-w': … } as …}` | `--dash-bar-w` · `dashboard.css` `.dash-bar-fill { width: var(--dash-bar-w) }` |
| 5 | `components/upload/RegisterArea.tsx:1007` | `style={{ marginTop: 16 }}`(정적) | `className="reg-source-block"` | 변수 없음 · `upload.css` `.reg-source-block { margin-top: 16px }` |
| 6 | `components/upload/PreviewPanel.tsx:631` | `transform: translate(…) scale(…)` · `transformOrigin: '0 0'` | 변환 문자열만 변수 · `transform-origin` 은 규칙 | `--pv-layers-transform` · `preview.css` `.pv-layers[data-zoom-scale] { transform: var(--pv-layers-transform); transform-origin: 0 0 }` |
| 7 | `components/upload/PreviewPanel.tsx:794` | 위와 같음(확장보기) | 위와 같음 | 위와 같음 |

- 이름은 컴포넌트 접두사(`--hit-` · `--pv-` · `--dash-`) · 게이트 a 의 정본 계열 접두사 없음(a=0). 게이트 b 는 TSX 의 `'--x'` 문자열을 정의로 센다(b=0).
- `React.CSSProperties` 는 기존 `React.ReactNode` 처럼 import 없이 타입 자리에서 쓴다 — `cssVars.ts` 는 만들지 않았다(필요 없음). `tsc --noEmit` 오류 0.
- 규칙을 거는 선택자는 종전 인라인이 걸리던 요소에만 걸리게 골랐다: `.pv-swatch` · `.pv-tile-piece` · `.dash-bar-fill` 은 TSX 에서 그 자리 하나만 쓴다 · `.relbar > span` 은 인라인 요소라 `display: block` 규칙 없이는 폭이 원래 적용되지 않는다 · `.pv-layers` 는 세 곳이 쓰므로 `[data-zoom-scale]`(확대 상태가 있을 때만 붙음)로 좁혔고, 데이터셋 미리보기 `preview-layers` 는 확대 상태가 있을 때 인라인 변환(펼침 속성)이 이 규칙을 이긴다 · `.reg-source-block` 은 새 클래스이고 그 `div` 의 `margin-top` 을 거는 다른 규칙이 없다(`.card-b` 규칙은 padding·gap 만).
- 변수가 없을 때: 종전 인라인 값이 없으면 속성이 비어 초기값이었고, 이제 `var()` 가 정의되지 않아 초기값이다(예: 범례 색이 비면 두 쪽 다 투명).

게이트(이 단계 뒤): `frontend-design-lint green — … · 색 리터럴 0(면제 3) · 인라인 0(변수 대입 6)` · `g=0 g_vars=6 g_spread=1`.

### 기존 시험 변경(판정 필요 1건)

| 파일:행 | 전 → 후 | 사유 |
|---|---|---|
| `frontend/test/search.test.tsx:175`(it 「관련도는 막대 하나다 — 퍼센트도 등급 텍스트도 숫자도 화면에 없다」) | `expect(span.style.width).toBe('42%')` → `expect(span.style.getPropertyValue('--hit-relbar-w')).toBe('42%')` + 주석 1줄 | spec(Q5)대로 인라인 `width` 를 변수 대입으로 바꾸면 요소의 `style.width` 는 빈 문자열이 된다 — 시험이 단언하던 **전달 수단**이 바뀐 것이고 단언한 사실(막대 길이 42% 가 막대에만 실린다)은 그대로다. red 확인: 변경 전 `AssertionError: expected '' to be '42%'` · 변경 뒤 19/19. 렌더 폭은 단계 7 의 캡처 대조가 본다(jsdom 은 층 껍질을 벗긴 CSS 를 싣지만 이 시험은 search.css 의 규칙 적용을 단언하지 않는다). **오케스트레이터 지시 「제품 시험 변경 0」과 다르다** — 판정 요청. |

- 전 시험: `npx vitest run` → Test Files 130 passed (130) · Tests 1613 passed (1613)(건수 = P2a 와 같음 · 폐기 0).

## 단계 5 — 캡처 범위(어느 장면이 바뀐 자리를 찍는가)

도구 = `p3/states/cdump_p3.py`(P2a `cdump.py` 사본 · 요소 키를 `순번:태그` 로 · 커스텀 속성을 해시에서 뺌 · 선택자별 「화면에 그려짐」 계수를 더함 — 너비·높이 > 0 · `visibility` 가 hidden 아님 · 캡처 영역(전체 페이지면 문서 높이, 아니면 뷰포트 900px) 안) · 원자료 `p3/states/cover-after.json`(선택자 → 그려진 페이지). 196 페이지 = 33장면 × 테마 × 폭.

| 자리 | 그려진 캡처(장면) | 검증 |
|---|---|---|
| B `.detail-page .dt-edit .de-req`(편집 모드) | **없음** | 캡처 [미검증] → probe 동일(라이트·다크 color `rgb(255, 255, 255)`) |
| B `.search-page .vfilter .vsw::after`(스위치 손잡이) | search · search-degraded(12장) | 캡처 · 계산값 |
| 〃 켜짐 `.vfilter.on`(폴백 3) | **없음** | 캡처 [미검증] → probe 동일(`::after` 배경 `rgb(255, 255, 255)` · 켜짐 색 라이트 `rgb(6, 117, 6)` · 다크 `rgb(144, 220, 178)`) |
| `.colmenu .cm-box`(체크) | **없음** | 이번 변경 없음(P2a 에서 이미 토큰) |
| A `.pj-modal-back` | project-close · project-dialog(12장) | 이번 변경 없음 · 캡처에 찍힘 |
| TSX 1 `.relbar > span` | search · search-degraded(12장) | 캡처 · 계산값 · probe |
| TSX 2 `.pv-swatch` | preview-done(6장) | 캡처 · 계산값 · probe |
| TSX 3 `.pv-tile-piece`(모자이크) | **없음** | 캡처 [미검증] → probe 동일(`absolute` · 10/20/30/40px) |
| TSX 4 `.dash-bar-fill` | lab · lab-dialog · gnb-more(16장) | 캡처 · 계산값 · probe |
| TSX 5 `reg-source-block` | upload-link(6장) | 캡처 · 계산값 · probe(`margin-top: 16px`) |
| TSX 6·7 `up-preview-layers` · `pv-expand-layers` | **없음** | 캡처 [미검증] → probe 동일(`matrix(2, 0, 0, 2, 5, 6)` · origin `0px 0px`) |
| `.pv-layers` 확대 없음(규칙이 걸리지 않아야 함) | preview-done 의 `preview-layers`(6장) | 캡처 · 계산값 · probe(`transform: none` · origin 기본값) |

- 색 리터럴 자리 69 중 캡처에 그려지는 것 **40** · 안 그려지는 것 **29** = 면제·무변 2(`login.css` 오버레이 둘) + B 1(`.de-req` · probe) + D **26**: `.dash-error` · `.fl-err` · `.dlerr` · `.labinfo-error` · `.labinfo-modal` · `lineage.css` 3 · `.loading` · `.hit.is-locked` · `.vfilter.on` 3 · `.up-spinner` 2 · `.gridbar` 계열 4 · `.up-transfer-percent` · `shell.css` `.loadfail` 계열 6. 이 26 은 **실화면 [미검증]** 이다 — 근거는 논증뿐(폴백 대상 이름 20종이 전부 `tokens.css` 라이트 `:root` 에 정의돼 있어 요소 위치와 무관하게 해석되고, 화면 범위 재정의는 게이트 a 가 0 으로 막는다).
- probe = `p3/states/probe.py` — 착수 빌드 CSS 에는 종전 인라인 모양, 최종 빌드 CSS 에는 새 변수·클래스 모양으로 같은 DOM 을 만들어 agent-browser 로 라이트·다크 계산값(위치·크기·변환·여백·색·`::after` 배경)을 비교: **9 모양 × 2 테마 = 18건 전부 같음**(`p3/states/probe.json`). React 출력은 그대로 쓰지 않았다 — TSX 가 변수를 싣는지는 단계 4 의 시험·타입검사, CSS 가 그 변수를 같은 값으로 읽는지는 probe 가 본다.
- `scenes.json` 무변(명세 sha256 `d6983d71…` 전후 같음) — 장면을 더하려면 새 픽스처(편집 모드 · 확대 미리보기 · 오류 상태)가 필요해 더하지 않았다.

## 단계 6 — 대장

- `dev-package/work-items.yaml` BF-8 `evidence` 끝에 한 줄: 「2026-09-24 P2a: 완료 정의의 「히어로 내용 폭 680px」는 09-12 승인 디자인(`design-system.css` → `search.css` 흡수 · `.lab-page .search-hero { max-width: 720px }`)이 720px 로 대체 · `dashboard.test.tsx` 기대값 720 (승인).」 다른 칸 무변.
- 지시문의 문장은 흡수처를 `dashboard.css` 로 적었으나 720px 규칙은 `search.css:154` 에 있다(`dashboard.css:22` 의 같은 선택자 규칙은 좌우 여백 0 만) — 파일명만 사실대로 고쳤다.
- `bash gates/run.sh work-item-consistency` → `work-item-consistency: green — 대장과 산문의 불일치 0`.

## 단계 7 — 시각 변경 0(ⓑ)

- 기준 `p3-before`: HEAD `26b8a676` · audit 빌드 포함 · 05:45:44~05:53:34 UTC · 196장.
- 후보 `p3-after`: HEAD `67ce0608`(게이트 · CSS · TSX · 대장 전부 포함) · `gitDirty` false · audit 다시 빌드 · 06:04:48~06:12:40 UTC · 196장.
- `npm run visual:diff -- .visual/p3-before .visual/p3-after .visual/p3-report` → **196 captures · red 0 · strict px 0 · exit 0** · 보조 차이 0 · 크기 차이 0 · 명세 sha256 두 쪽 같음. 보고 = `p3/visual/report.md`·`report.json`. red 0 이라 `visual/red/` 는 만들지 않았다.
- B 의 다크 판정: `.vsw::after` 는 search·search-degraded 다크 캡처에서 차이 0. `.de-req` 는 캡처 밖이라 probe 로 봤다(다크 `rgb(255, 255, 255)` 전후 같음).

### ⓑ′ 계산값 전수 대조

- 착수 빌드(`frontend/.visual/p3-dist-before`)와 최종 빌드(`p3-dist-after`)를 캡처와 같은 196 페이지에서 열어(같은 명세 · 저장소 비움 · 애니메이션 고정) 모든 요소·가상요소의 `getComputedStyle` 전 속성 해시를 비교 — **196 페이지 · 26962 항목 · 차이 0**(`compare.py`).
- P2a 도구와 다른 점: 커스텀 속성(`--*`)은 해시에서 뺐다 — 새 변수(`--hit-relbar-w` 등)는 상속돼 자손 전부의 커스텀 속성 목록을 바꾸므로, 렌더 값(비커스텀 속성)만 비교해야 뜻이 있다. 요소 키에서 클래스 이름을 뺐다 — `reg-source-block` 클래스가 새로 붙은 요소를 같은 요소로 맞추기 위해서다(DOM 순서 동일).

## ⓓ 게이트(단계 8)

`COLAB_TASK_ID=a48a85df6e19492ba20254a0ad6135bf bash gates/run.sh task` → **계 green 6 / red(판정) 0 / red(준비) 0** · 게이트 6개 exit 0(커밋 `202f1da5` · `~/.colab-v2-test.env` 존재 확인 뒤). 요약 JSON = git common dir 기준 `colab-harness/ed554caca049d79663e1502a60aea7ab/a48a85df6e19492ba20254a0ad6135bf/4dc1ecf412224b8e9e547ba1fe7be633/gate-summary.json`. 이 표를 적은 커밋 뒤 handoff 용으로 같은 명령을 한 번 더 돌리며 그 run id 는 `COLAB_HANDOFF` 줄에 실린다.

| 게이트 | 결과 | 요약 |
|---|---|---|
| `frontend-design-lint` | green | 파일 19 · :root 정의 밖 0 · 미정의 참조 0 · 다크 누락 0(면제 6) · :root/@import 0 · 범위 색 토큰 0 · **색 리터럴 0(면제 3) · 인라인 0(변수 대입 6)** · 참고 펼침 속성 style 1 |
| `frontend-design-lint-selftest` | green | 검사 16건 전건 기대대로 (green 3 · red 9 · red(준비) 4) |
| `frontend-typecheck` | green | tsc --noEmit 오류 0건 |
| `frontend-test` | green | Test Files 130 passed (130) · Tests 1613 passed (1613) — P2a 와 같은 건수 · 폐기 0 · 변경 1줄(`search.test.tsx:175`) |
| `frontend-fixture-reach` | green | 진입점 src/main.tsx 도달 205(진입점 제외 204) · 금지 모듈 0 |
| `work-item-consistency` | green | 대장 236건 · 불일치 0 |

- ⓐ 착수 → 최종: f **69 → 0(면제 3)** · g **7 → 0(변수 대입 6)** · selftest 12 → 16.
- 시험 변경: 제품 시험 1줄(`search.test.tsx:175` · 판정 요청) · selftest 픽스처 3트리(`green-fg` · `red-f` · `red-g`) · selftest 셸 · 새 시험 파일 0.

## spec 과 다르게 한 점

1. 착수 계수 69 ≠ spec 72 — A 1(`.pj-modal-back`) · B 1(`.cm-box`) · D 3 을 P2a 흡수가 먼저 토큰 참조로 바꿨다. spec 의 「`.pj-modal-back` 은 P2a 뒤 … 다시 확인」이 이 경우다. 그래서 **A 면제는 등록하지 않았다**(걸리는 리터럴이 없는 항목은 게이트가 낡은 항목으로 red 를 낸다).
2. `color-mix()` — spec 은 탐지 대상으로만 적었다. 처음에는 `login.css` 2건을 면제했고(면제 3), advisor ② 에 따라 **색 인자가 전부 `var()`·`transparent`·`currentColor` 인 `color-mix()` 는 토큰 혼합으로 보아 세지 않게** 정밀화하고 면제 2줄을 지웠다(면제 1). 리터럴 색이 섞인 혼합은 여전히 f 다(selftest ⓢ).
3. 면제 형식: spec 은 `allow.txt` 를 적었으나 「P1 면제 파일 형식을 따르고 파일명이 다르면 그것」에 따라 **P1 목록 `same-in-dark.txt` 한 파일에 `f · …` 줄**을 더했다(환경변수·게이트 입력 무변).
4. selftest 구성 — 지시의 `red-f`·`red-g` 에 f·g 대조군 `green-fg`(green) · `typescript` 부재(red(준비))를 더해 16건, advisor ② 로 `red-g-spread` · `green-mix` · `red-mix` 를 더해 **19건**(green 4 · red 11 · red(준비) 4). `red-f` 는 사유 없는 면제와 낡은 면제를 함께 담는다.
5. selftest 의 `expect()` 에 「ready 기대인데 판정 red 로 끝남 = 기대와 다름」 갈래를 더했다(기존 ⓖ·ⓗ 결과 무변).
6. 제품 시험 변경 6파일 14곳 — 아래 「advisor ② 반영」 표 · 판정 요청.
9. 게이트 g 가 JSX 펼침 속성 안의 `style` 키도 판정한다(spec 의 「`style` JSX 속성」보다 넓다 · advisor ②).
7. 대장 문장의 흡수처 파일명 `dashboard.css` → `search.css`(사실 정정).
8. 계산값 대조 도구를 P3 용으로 고쳤다(커스텀 속성 제외 · 키에서 클래스 제외 · 선택자 범위 계수) · 캡처 밖 자리 probe 를 더했다.

## 하지 않은 것

- (해소) 펼침 속성 안의 인라인 `style`(`PreviewPanels.tsx` `preview-layers`)은 advisor ② 로 변수 대입으로 옮겼고 g 가 판정한다(`g_spread=1` 은 판정한 펼침 자리 수).
- g 는 펼침 속성 밖에서 만든 객체를 펼치는 경우(`{...props}` 안의 style)는 키를 읽을 수 없어 보지 않는다.
- `.ts` 의 DOM 스타일 대입(`Gnb.tsx` 의 `setProperty('--shell-gnb-offset')` 는 변수 · `ScreenshotButton.tsx` `a.style.display = 'none'`)은 g 대상 밖.
- 색 아닌 폴백 리터럴(`search.css` `var(--text-body-sm, 13px)` 류 14 · `login.css` `var(--radius-md, 12px)` · `detail.css` `var(--font-mono, monospace)`)과 `deletion.css` `var(--color-surface-muted, transparent)`(제외 키워드)는 그대로 — f 범위 밖.
- 여백·글자 크기 리터럴 · 토큰 값·이름 · 프리미티브(P2b) · `scenes.json` · 새 의존성 0 · push·PR 게시.
- 실화면 [미검증]: D 26 자리(단계 5 목록) · TSX 3·6·7 · 펼침 자리(확대 상태) · B `.de-req` 는 실화면 대신 probe(같은 CSS · 같은 DOM 모양)로 봤다. `preview-done` 캡처의 `preview-layers` 는 확대 상태가 없다(`data-zoom-scale` 없음 · `transform: none` · 「확대」 단추를 눌러도 같음 · `p3/states/zoomcheck.json`).

## 후속 항목

1. [Ted 판정] `upload.css .chip` `#eef2f7` — 새 토큰(값 유지 · 다크 값 결정) vs `--color-gray-100` 값 변경(시각 변경). 참고: 이 `.chip` 규칙은 화면 범위 없이 선언돼 있다 — 캡처상 `.chip` 요소가 그려지는 장면은 catalog·detail·members·pending·project 계열·search 등 10개이고, 각 화면의 더 좁은 `.chip` 규칙이 배경을 덮는지는 재지 않았다.
2. (해소) `login.css` 토큰끼리의 `color-mix()` 2건 — f 정밀화로 리터럴 아님. 오버레이 토큰을 따로 둘지는 별건.
3. [판정] 제품 시험 6파일 14곳 단언 변경(변수 값 읽기) 수용 여부.
4. `.detail-page .dt-edit .de-req` 는 다크에서 흰 글자(`rgb(255, 255, 255)`)가 밝은 배경(`--color-text-body` 다크 `rgb(220, 228, 237)`) 위에 선다 — 오늘의 렌더(값 무변)이며 대비가 낮다. spec 우려 3 의 「뜻 토큰」 치환(`--color-on-…`) 판정 때 함께 본다. 검출은 probe 뿐이고 게이트·캡처 어디에도 걸리지 않는다.
5. (해소) 펼침 속성 안 인라인 변환 — advisor ② 로 옮김. 미리보기 확대 상태를 찍는 캡처 장면이 없어 실화면 대조는 probe 뿐이다(후속 6).
6. 캡처 장면 보강(편집 모드 · `.vfilter.on` · 확대 미리보기 · 모자이크 · 오류·로딩 상태) — `scenes.json` 과 픽스처 변경이 필요해 이번엔 하지 않았다. 지금 이 자리들은 캡처 대조의 사각이다.
7. 계산값 대조 도구(`p3/states/cdump_p3.py` · `compare.py`)를 `frontend/scripts/visual-baseline/` 로 올려 P2b 의 정식 오라클로 쓸지(P2a 후속 3 과 같음).
8. 색 아닌 폴백 리터럴 16건(대상 토큰 정의 여부 미조사) 정리 — 게이트로 막을지는 여백·글자 눈금 확정 뒤.

## advisor ② 반영(accept-with-fixes 3건)

| # | 지적 | 처리 |
|---|---|---|
| 1 | `PreviewPanels.tsx` 펼침 속성 `style: { transform, transformOrigin }` = 8번째 인라인(intent Q5 위반) | `style: { '--pv-layers-transform': \`translate(…) scale(…)\` } as React.CSSProperties` — 기존 `preview.css` `.pv-layers[data-zoom-scale] { transform: var(--pv-layers-transform); transform-origin: 0 0 }` 가 읽는다(`data-zoom-scale` 은 같은 `zoom ?` 갈래). `preview.css` 주석 갱신 |
| 2 | g 가 펼침 속성 안 `style` 을 판정하지 않음 | `scanStyles` 의 판정을 한 함수(`judge`)로 모아 `style={…}` 속성과 펼침 속성 안의 `style` 키(`PropertyAssignment`·축약형) 둘 다에 적용 — `gHits`/`gVars` 로 센다. 사람 출력에 「(펼침 속성)」 표시 · 「참고 · 펼침 속성」 줄 삭제 · selftest ⓠ `red-g-spread` |
| 3 | `color-mix()` 정밀화 | `colourLiterals` 가 색 인자가 전부 `var()`·`transparent`·`currentColor`(비율 허용)인 `color-mix()` 를 세지 않는다(안쪽 토큰은 그대로 스캔). `login.css` 면제 2줄 삭제 → 면제 1(`.chip`). selftest ⓡ `green-mix`(green) · ⓢ `red-mix`(`color-mix(in srgb, #fff 50%, var(--color-link))` → f=1) |

### red 확인

- 새 케이스를 직전 판정부(`b566e545` 의 `design-lint.mjs`)로 돌림: ⓠ `red 여야 하는데 통과했다` · ⓡ `green 이어야 하는데 red 다(rc=1)` — 기대와 다름. ⓢ 는 직전 판정부도 red(종전 규칙이 모든 `color-mix()` 를 셌다 — 대조군 역할).
- 착수 코드(`26b8a676` 의 `frontend/src` 를 `git archive` 로 풀어) 현 판정부로 재계수: 리터럴 **67**(직접 3 = B 2 + C 1 · 폴백 64 · 토큰 color-mix 2 는 제외) → 면제 1(`.chip`) 적용 뒤 `f=66 f_direct=2 f_fallback=64` · `g=8 g_spread=1`(속성 7 + 펼침 1). 단계 2 의 69·7 은 종전 판정부 기준.
- 새 판정부 → `frontend-design-lint-selftest green — 검사 19건 전건 기대대로 (green 4 · red 11 · red(준비) 4).`

### 제품 시험 변경(펼침 자리 · 판정 필요)

변환을 변수로 넘기면 `preview-layers` 의 `style.transform` 은 빈 문자열이다. 단언이 읽는 자리를 `style.getPropertyValue('--pv-layers-transform')` 로 바꿨다 — 비교하는 값(`translate(…px, …px) scale(…)` 원문 · `scale(2)` 포함 · 이동 전후 다름)은 같다. 변경 전 red: `Test Files 5 failed | 125 passed` · `Tests 16 failed | 1597 passed`.

| 파일 | 곳 |
|---|---:|
| `frontend/test/dataset-preview-tiles.test.tsx` | 6 |
| `frontend/test/dataset-preview-zoom.test.tsx` | 3 |
| `frontend/test/rev1-keep-regression.test.tsx` | 2 |
| `frontend/test/dataset-preview-zoom-latency.test.tsx` | 1 |
| `frontend/test/preview-map-viewport-20260918.test.tsx` | 1 |

- 층(그림·조각) 자신에 변환이 없다는 단언(`img.style.transform` · `t.style.transform` `''`)은 그대로 두었다.
- 변경 뒤 `npx vitest run` → Test Files 130 passed (130) · Tests 1613 passed (1613).

### 재검증

- 재캡처 `p3-after2`: HEAD `5b2a2a83` · `gitDirty` false · audit 다시 빌드 · 06:36:34~06:44:26 UTC · 196장. `visual:diff .visual/p3-before .visual/p3-after2` → **196 captures · red 0 · strict px 0 · exit 0**(`p3/visual/report.md`·`.json` 을 이 결과로 갈아 끼움).
- 계산값 전수 대조(`p3-dist-before` ↔ `p3-dist-after2`) → **196 페이지 · 26962 항목 · 차이 0** · 범위 표 원자료 `p3/states/cover-after.json` 갱신.
- 미리보기 확대 상태: 캡처 `preview-done` 은 확대 상태가 없다 — 두 빌드에서 장면을 열고 「확대」를 눌러도 `preview-layers` 에 `data-zoom-scale` 이 없고 `transform: none`(전후 같음 · `p3/states/zoomcheck.py`·`.json`). 그래서 probe 에 `dslayers`(같은 속성 조합 · `translate(-40px, -12.5px) scale(1.5)`)를 더했다 → 라이트·다크 `matrix(1.5, 0, 0, 1.5, -40, -12.5)` · origin `0px 0px` 전후 같음. probe 계 **10 모양 × 2 테마 = 20건 차이 0**(`p3/states/probe.json`).
- 게이트(최종 · 보고서 미커밋 상태 트리): `COLAB_TASK_ID=a48a85df6e19492ba20254a0ad6135bf bash gates/run.sh task` → **계 green 6 / red(판정) 0 / red(준비) 0** · 요약 JSON = git common dir 기준 `colab-harness/ed554caca049d79663e1502a60aea7ab/a48a85df6e19492ba20254a0ad6135bf/7540680fe5724f999838517765b270de/gate-summary.json`. 이 커밋 뒤 handoff 용으로 한 번 더 돈다.

| 게이트 | 결과 | 요약 |
|---|---|---|
| `frontend-design-lint` | green | … · **색 리터럴 0(면제 1) · 인라인 0(변수 대입 7)** · `g_spread=1` |
| `frontend-design-lint-selftest` | green | 검사 19건 전건 기대대로 (green 4 · red 11 · red(준비) 4) |
| `frontend-typecheck` | green | 오류 0건 |
| `frontend-test` | green | 통과 1613건 · 실패 0건(건수 무변 · 단언 변경 6파일 14곳) |
| `frontend-fixture-reach` | green | 도달 205 · 금지 모듈 0 |
| `work-item-consistency` | green | 불일치 0 |

- ⓐ 최종: 착수 f 69 · g 7(종전 판정부) → **f 0(면제 1) · g 0(변수 대입 7)** · selftest 12 → 19. 위 ⓓ 표(`b566e545`)는 advisor ② 전 수치다.
