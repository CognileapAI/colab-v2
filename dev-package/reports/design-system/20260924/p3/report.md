# 디자인 구조 P3(+P4) 결과 — 화면 CSS 색 리터럴·죽은 폴백·TSX 인라인 정리 · 게이트 f·g

spec: `dev-package/prd/specs/S-DESIGN-STRUCTURE-P3-20260924.md` · 조사: `p3/literal-map.md`(HEAD `7967e001` · P2a 전) · `survey.md §2` · 선행: `p2a/report.md`

착수 HEAD `26b8a676` · task `a48a85df6e19492ba20254a0ad6135bf` · 레인 1(직렬)

## 진행 상태

| 단계 | 상태 | 커밋 |
|---|---|---|
| 1 착수 캡처 `p3-before` · 재계측 | 완료 | — |
| 2 게이트 f·g · selftest 16 | 완료 | (이 커밋) |
| 3 CSS — 죽은 폴백 · B · 면제 | 대기 | |
| 4 TSX 인라인 7 | 대기 | |
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
