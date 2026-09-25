# design-review 20260924 — L2 (catalog/search/detail/preview/datasetpreview, STATIC only)

task_id: c859956278564042a315fa2a1e333d22
Scope: frontend/src/components/catalog/**, components/search/**, components/detail/**, components/preview/**, components/datasetpreview/**
Axes: p3 11-item baseline, AA 4.5:1(light/dark), font>=13px, undefined token, neg margin, card shadow, border 2-layer, container-owned spacing, local-token ⓐ/ⓑ split.
Not this lane: motion/:active/reduced-motion/typography tracking (L4a/L4b).

## 1. 판정표

| # | 축 | 항목 | 판정 | 근거 path:line · 실측값 | 처리 |
|---|---|---|---|---|---|
| 1 | font≥13px | `catalog.css:48` 정렬 표식 | 있음 | `.tbl thead th > .thf::before { content:"▾"; font-size:9px }` — 읽는 글자가 아닌 단일 방향 글리프(장식). 텍스트 캡션류(0908 판정)와 성격이 다르다 | Ted 판정 |
| 2 | font≥13px | `catalog.css:138` `.lvl-mismatch` | 있음 | `font-size: 12px` — Lv 칩 옆 「불일치」 표식, 읽는 텍스트. 12px < 13px 문턱 | Ted 판정 |
| 3 | AA 4.5:1 | `detail.css:205` `.detail-page .dsec-menu-i.is-active` (light) | 있음 | `#1369e9` on `#edf4ff` → **4.49:1**(css_audit 채택, 재확인) — AA 미달 | 즉시 수정 후보 |
| 4 | AA 4.5:1 | `detail.css:205` `.detail-page .dsec-menu-i.is-active` (dark) | 없음 | dark `--color-primary-600:#92c2ff` on `--color-primary-50:#203954` → 수기 계산 **6.43:1** — AA 통과 | — |
| 5 | AA 4.5:1 | `detail.css:166` `.detail-page .dt-edit .de-req` (light) | 없음 | bg `--color-text-body:#21272ae0`(88% 위 `--color-surface` 흰 배경 합성 ≈ rgb(60,65,68)) + `--color-white` 글자 → 수기 계산 **10.3:1** — AA 통과 | — |
| 6 | AA 4.5:1 | `detail.css:166` `.detail-page .dt-edit .de-req` (dark) | 있음 | dark 토큰 대입 시 bg `--color-text-body:#dce4ed`(밝은 회청) + `color:var(--color-white)` → 수기 계산 **1.28:1** — 라이트에서 어두운 값이던 토큰이 다크에서 밝은 값으로 뒤집히며 흰 글자와 충돌. design-system.md ⑦-9 항목과 동일 | 즉시 수정 후보 |
| 7 | undefined token | `preview.css:150,293,368,369,370,371` `--pv-swatch-bg` `--pv-layers-transform` `--pv-piece-left/top/w/h` | 없음 | 전부 `PreviewPanels`류 TSX `style={{'--pv-*': ...}}` 인라인 대입(gate g 패턴). 코드 확인 완료 — KNOWN 오탐 | — |
| 8 | undefined token | `search.css:92` `--hit-relbar-w` | 없음 | `SearchHitCard.tsx:60` `style={{'--hit-relbar-w': width}}` 인라인 대입(gate g 패턴). 코드 확인 완료 — KNOWN 오탐 | — |
| 9 | local-token ⓐ/ⓑ | `preview.css:418` `.pv-frame-wrap { --pv-frame-ratio: 4/3 }` | 없음 | 컴포넌트 전용 접두 `--pv-*` = ⓐ. 전역 어휘(`--color-*`/`--radius-*`/`--space-*`) 아님 | — |
| 10 | card shadow | `catalog.css:14` `.catalog-page .card` | 없음 | `box-shadow` 선언 없음(주석 「카드는 그림자를 지지 않는다」). `.colmenu`(:63) `box-shadow: var(--shadow-lg)`는 팝오버라 허용 | — |
| 11 | card shadow | `detail.css:317` `:is(.dt-header,.dt-card)` | 없음 | `box-shadow: none` 명시 | — |
| 12 | card shadow | `preview.css:265` | 없음 | `box-shadow: none` 명시 | — |
| 13 | neg margin | catalog.css / search.css / detail.css / deletion.css / preview.css 전수 grep | 없음 | `margin: -` / `margin-*: -` 패턴 0건(주석 속 과거 값 언급 2곳 `detail.css:62,122` 제외 — 코드 아님) | — |
| 14 | border 2-layer | `catalog.css:14` (외곽 `--color-border-strong`) vs `catalog.css:26` `.tbl td`(내부 `--color-border`) | 없음 | `--color-border-strong:#dfe3e8`(어두움) vs `--color-border:#e8ecf2`(밝음) — 외곽이 내부보다 진하다. 역전 해소(0905 판정⑨ 이후 수정 유지) | — |
| 15 | border 2-layer | `detail.css:55` `.dt-card`(외곽 `--color-border-strong`) vs `detail.css:58` `.ig`(내부 `--color-border`) | 없음 | 위와 동일 값 관계 — 역전 없음 | — |
| 16 | container-owned spacing | `detail.css:62` 주석 · WU-C11 | 없음 | 종전 `.ig` 목록 `margin: -12px` 음수 상쇄를 `.dt-split-r` 컨테이너 `gap`(16px) 한 곳으로 이관 완료(주석 확인) | — |
| 17 | local-token ⓑ | catalog.css / detail.css 전역 어휘(`--color-*`/`--radius-*`/`--space-*`) 재정의 | 없음 | `grep '^\s*--'` 결과 두 파일 모두 0건 — 0908 round 지목분(catalog 18·detail 30건) 제거됨 | — |

## 2. 이월 재판정

| 이전 항목 | 상태 | 근거 |
|---|---|---|
| 20260908(-L2) #6·#7 catalog/detail 13px 미만 캡션·뱃지군 (14건/9건) | **변경** | 대부분 승격/제거됨. 현재 css_audit 20260924는 catalog.css 2건(9px 장식·12px `.lvl-mismatch`)만 남음, detail.css는 0건. → 이번 표 #1·#2로 축소 재등재 |
| p3-design-audit-20260905 #6 카드 그림자(`catalog.css:31`) | **해소** | 현재 `.card`에 `box-shadow` 없음(#10) |
| p3-design-audit-20260905 #9 보더 2층 역전(`catalog.css:30/41`, `detail.css:59/62`) | **해소** | 외곽=`--color-border-strong` / 내부=`--color-border`로 정렬(#14·#15) |
| p3-design-audit-20260905 #10 여백 컨테이너 미소유(음수 상쇄, `detail.css:93`·`shell.css:58`) | **해소**(detail.css 범위) | WU-C11이 `.dt-split-r` gap 1곳으로 통합(#16). `shell.css`는 L1 소관 |
| 20260912 D17 전역 control/card/modal 중복 정의 (`catalog.css:127` 등) | **해소**(catalog.css·detail.css 범위) | 두 파일 ⓑ 전역 토큰 재정의 0건(#17). `upload.css`/`members.css`/`project.css`는 L3 소관 — 이 표에서 판단 안 함 |
| 20260912 D18 대체 토큰/정본 혼용 (`preview.css`, 미정의 변수 fallback) | **잔존이나 무결함** | `preview.css` 6곳 전부 TSX 인라인 대입 패턴(#7) — CSS 무효 아님. 원 판정도 "무효 아님"이었고 이번에도 동일 |
| 20260912 D12 상태/보조 글자 대비 (`catalog.css:140`, `preview.css`) | **잔존(일부 확인)** | `catalog.css:140`(대략 `.lin--none`류)은 0905 WU-C11 판정46에서 `-500`로 승격되어 대비 문제 해소로 보이나 이번 라운드에서 catalog.css AA 재계측은 표에 없음(css_audit 0건 보고) — `preview.css`는 이번 라운드 대비 미달 0건(css_audit) |
| 20260912 D29 WU-C11 항목 재이탈 없음 (`catalog.css:134`, `detail.css:69`) | **해소 유지** | `catalog.css:134` `.lvl-3` 계열·`detail.css:69` 인접 여백 규칙 현재도 유지 확인 |
| design-system.md ⑦-7 `deletion.css` `.dl-keep` `--color-surface-muted` 미정의 | **해소** | `background: transparent`로 교체, 주석에 사유 명시(`deletion.css:11`) |
| design-system.md ⑦-9 `detail.css` `.dt-edit .de-req` 다크 대비 | **잔존(재확인)** | 다크에서 1.28:1로 실측 확인(#6) — 미해결 |

## 3. 소계

있음 4 / 없음 13 / 미상 0. Ted 판정 후보 2 / 즉시 수정 후보 2.

## 4. Ted 판정 후보

- **catalog.css:48 정렬 표식 9px(장식 글리프)** — ⓐ 예외 등재(장식용 비텍스트 표식은 13px 문턱에서 제외) / ⓑ 10~11px대로 소폭 확대. 권고 ⓐ — 0908 round에서도 "장식"으로 별도 분류했고 방향 지시 글리프는 읽는 텍스트가 아니다.
- **catalog.css:138 `.lvl-mismatch` 12px(실제 텍스트 라벨)** — ⓐ 13px로 승격 / ⓑ 뱃지류 별도 문턱(11px) 신설 후 그 문턱 내 포함. 권고 ⓐ — 0908 round 권고(`design-review-20260908-L2.md:46`)가 이미 ⓑ를 "뱃지류"에 한정했고 이 항목은 Lv 칩 옆 보조 텍스트로 뱃지 자체가 아니다.

## 5. css_audit 오탐

- `preview.css:150,293,368,369,370,371` 미정의 토큰 6건 — `PreviewPanels`/`PreviewSlot` TSX가 `style={{'--pv-*': value}}`로 인라인 대입(gate g 패턴). 선언 무효 아님.
- `search.css:92` 미정의 토큰 1건(`--hit-relbar-w`) — `SearchHitCard.tsx:60` 인라인 대입. 선언 무효 아님.

## 6. 이번에 세지 않은 축

- motion/:active/reduced-motion/typography tracking — L4a/L4b 소관, 이 표에서 판단하지 않음.
- 실화면(라이브) 계측 전반(1440/375px 렌더, 다크 스크린샷 대조) — 라이브 스택 다운, `[미상 · 실화면 계측 필요]`로 넘어가지 않고 이번 라운드는 정적 전용이라 표에도 올리지 않음.
- `datasetpreview/**`(ScreenshotButton·DatasetPreviewSection·ValueLookupPanel) 전용 CSS 파일 없음(css_audit 목록 21종에 datasetpreview 항목 자체가 없음) — TSX 인라인 스타일·className 연결은 정적 CSS 축 감사 대상 외라 이번 표에서 별도 행을 만들지 않음.
- `catalog.css`/`detail.css`/`search.css`/`preview.css` 나머지 파일 전체 라인의 p3 11항목 중 계보 그래프(`lineageGraph.css`) 전용 항목(#7 원문)은 L3 소관이라 이 표에서 재판정하지 않음.
- 20260912 D01(폰트 불일치)·D02(AxisFilterBar 스타일 누락)·D11(11~12px 잔존, catalog/dashboard/project/lineage 합산)의 catalog 부분 세부 재계측 — 턴 한도로 미도달, 재개 시 우선 처리.
