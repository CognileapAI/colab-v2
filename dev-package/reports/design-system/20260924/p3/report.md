# 디자인 구조 P3(+P4) 결과 — 화면 CSS 색 리터럴·죽은 폴백·TSX 인라인 정리 · 게이트 f·g

spec: `dev-package/prd/specs/S-DESIGN-STRUCTURE-P3-20260924.md` · 조사: `p3/literal-map.md`(HEAD `7967e001` · P2a 전) · `survey.md §2` · 선행: `p2a/report.md`

착수 HEAD `26b8a676` · task `a48a85df6e19492ba20254a0ad6135bf` · 레인 1(직렬)

## 진행 상태

| 단계 | 상태 | 커밋 |
|---|---|---|
| 1 착수 캡처 `p3-before` · 재계측 | 완료 | — |
| 2 게이트 f·g · selftest 16 | 완료 | `844652cd` |
| 3 CSS — 죽은 폴백 64 · B 2 · 면제 3 | 완료 | `539f68ee` |
| 4 TSX 인라인 7 | 완료(제품 시험 1줄 변경 · 판정 필요) | (이 커밋) |
| 5 캡처 범위 표 | 대기 | |
| 6 대장 BF-8 | 대기 | |
| 7 시각 변경 0 | 대기 | |
| 8 게이트 | 대기 | |

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
