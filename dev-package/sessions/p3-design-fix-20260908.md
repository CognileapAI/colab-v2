# WU-B11 · 디자인 검수 수정 (PRD-29 후속 · WU-A11 「있음」 6건 집행)

레인 `p3-design-fix` · 기준 `integration/r-b` = `0a17d2e` · 2026-09-08 · 계약 0 · 서버 0 · 스키마 0 · 마이그레이션 0.
판정표 = `dev-package/sessions/p3-design-audit-20260905.md` · 범위 정의 = `dev-package/prd/rounds/R-B-4-verify.md §2-A`.
경로는 `frontend/src/` 이하. ⑦(유일하게 살아남은 접근성 합격선)을 먼저 돌았다.

## 「있음」 6건 ↔ 변경 선언 (before → after)

| # | 파일:행 | before → after |
|---|---|---|
| ⑦ | `components/lineage/lineageGraph.css` 13px 미만 **13건** → 13px | `:10` `.hint` 11 · `:14` `.lin-stale .d` 11 · `:31` `.lin-way` 10 · `:44` `.n-role` 10.5 · `:45` `.ln .n-name` 12.5 · `:58` `.lin-use` 11 · `:72` `.stg` 10 · `:76` `.ln-name` 12 · `:81` `.ln-sub` 11 · `:82` `.hist` 10 · `:83` `.aiflag` 10 · `:85` `.manflag` 10 · `:95` `.lin-empty .muted` 11 |
| ⑦ | 같은 파일 `:83`·`:85` 고정 높이 | `height: 17px` → `20px` (13px 글자 수용) |
| ⑥ | `components/catalog/catalog.css:31` `.catalog-page .card` | `box-shadow: var(--shadow-sm)` 제거 (팝오버 `.colmenu` 그림자 유지) |
| ⑧ | `components/detail/detail.css:104` `.fl-k` · `:108` `.fl-x` · `components/upload/upload.css:109` `.up-note` | 10px·11px·12px → 13px (나머지 4곳 = ⑦ 의 `:76`·`:81`·`:95` ＋ 이미 13px 인 `.vizerr,.warn`) |
| ⑨ | `detail.css:66` 컨테이너 `.infogrid` | `--color-border` → `--color-border-strong` · 칸 구분선 `:69`·`:76` 은 `--color-border` 유지 = 서로 다른 토큰 |
| ⑨ | `catalog.css:30` 바깥선 | `--color-border`(#e8ecf2) → `--color-border-strong`(#dfe3e8) · 안쪽선(`:41`·`:45`)과 동률 = 역전 해소 |
| ⑩ | `detail.css:100` `.filelist` | `margin: -12px 0 var(--space-6)` → `0 0 var(--space-6)` · 컨테이너 `.infogrid:has(+ .filelist)` 가 12px 소유 |
| ⑩ | `shell/shell.css:58` `.backlink` | `margin-left: -7px` 제거 · `padding-left` 7px → 0 (글자 시작 위치 불변) |
| ⑩ | `upload.css:113`·`:135`·`:108` | 자식 `margin-top: 12px`·`12px`·`8px` 제거 → 컨테이너 `.up-card > .card-b { display:flex; flex-direction:column; gap:12px }` 신설 |
| ⑪ | `lineageGraph.css:33` `.lin-way` | 덮인 `display: inline-block` 제거 (`:29` `inline-flex` 가 산다) |
| ⑪ | 같은 파일 미정의 토큰 **11건** → 0 | `:30`·`:31`·`:83` 액센트 → `--color-gray-50`·`--color-border-strong`·`--color-text-muted`·`--color-text`·`--color-gray-100` · `:48`·`:49` `--color-gray-300` → `--color-border-strong` · `:51`·`:57` `--color-primary-800/200` → `--color-primary-700/100` · `:84` `--color-ai` → `--color-primary-600` |

## 수용 기준 7 (R-B-4 §2-A 축자)

| 기준 | 결과 |
|---|---|
| `.catalog-page .card` 그림자 0 (팝오버 유지) | green — 시험 2건 |
| `lineageGraph.css` 13px 미만 선언 0건 | green — 13건 승격 |
| 지목 캡션 7곳 13px 이상 | green — 6곳 승격 ＋ `.vizerr,.warn` 은 이미 13px(무접촉) |
| 상세 컨테이너 ↔ 칸 구분선 상이 토큰 · 카탈로그 바깥 ≥ 안쪽 진하기 | green — 휘도 계산으로 계측 |
| 지목 음수 상쇄 2건 0건 · 여백 컨테이너 소유 | green |
| 덮인 `display` 0건 ＋ 미정의 토큰 참조 0건 | green — 11건 → 0 |
| `frontend-typecheck`·`frontend-test`·`frontend-fixture-reach` green | green |

## RED → GREEN

- 시험 파일 `frontend/test/design-fix-20260908.test.ts` · 17건.
- RED 선실측 = `Tests 15 failed | 2 passed (17)` — green 2건은 이미 충족된 자리(`.colmenu` 그림자 유지 · `.vizerr,.warn` 13px).
- GREEN = `Tests 17 passed (17)` · 전수 FE `Test Files 72 passed · Tests 996 passed` (착수 시 979 ＋ 17).

## 게이트 (`COLAB_GATE_REPORT_DIR=dev-package/reports/R-B/p3-design-fix`)

```
green  frontend-typecheck      — 계 green 1 / red(판정) 0 / red(준비) 0
green  frontend-test           — 계 green 1 / red(판정) 0 / red(준비) 0
green  frontend-fixture-reach  — 계 green 1 / red(판정) 0 / red(준비) 0
```

## 자기 표시 — 토큰 선택 근거

- ⑪ 미정의 토큰 11건은 **정의된 토큰으로 치환**했다. `tokens.css` 에 세우지 않은 이유 = 값의 정본이 목업 `:root` 이고 그 목업이 이 레포에 없다 — 코랄 액센트 7색을 세우려면 hex 를 지어내야 하고 그것은 정본 무근거다. `tokens.css` 머리 주석도 「액센트는 AI 액션 전용이라 셸에 두지 않는다」로 못박고 있다.
- 치환 시 의미 구분은 유지했다 — `.aiflag`(중립 회색) ↔ `.manflag`(파랑)가 여전히 갈린다. 코랄 액센트 복원은 목업 `:root` 회수 뒤 후속.
- ⑨ 는 `tokens.css` 에 토큰을 **추가하지 않았다** — 기존 `--color-border`/`--color-border-strong` 두 단으로 2층이 갈린다.
- 레이아웃 무붕괴 정적 확인 — 고정 높이 상자 3곳만 승격 글자를 담는다. `.lin-way` `height:23px`＋`line-height:23px`(13px 글자 = 23px 줄상자 ✔) · `.lin-use` `height:25px`(13px 기본 줄상자 ≈15.6px ✔) · `.aiflag`·`.manflag` `height:17px` 는 13px 글자를 담지 못해 **20px 로 올렸다**. `.lrow` 는 고정 높이가 없고 `.stg` 는 92px 칸에서 줄바꿈으로 흡수된다.

## 하지 않은 것

- 「없음」 5건(① Lv 칩 4.66:1 통과 · ② 제약 안내 요소 부재 · ③ 흐림 대상 부재 · ④ 밑줄 이미 있음 · ⑤ 이미 둥근 사각) — 없는 결함이라 무접촉.
- 판정 대기 2건(`catalog.css` `.lvl-3` 부재 · `.lin--none` 3.41:1) — 무접촉, 아래 후속.
- 6종 합계 13px 미만 선언 60건 일괄 승격 — 하지 않았다. 지목된 자리만 올렸다.
- `upload.css` `.vizph` — 판정표 미지목이라 무접촉(`font-size` 선언 자체가 없다).
- `upload.css` `.vizerr, .warn` — 이미 13px 이라 다시 고치지 않았다.
- `lineageGraph.css:7` `.dsec { margin-top: 34px }` 의 컨테이너 이관 — **하지 않았다.** `.dsec` 형제들의 부모가 `LockedContent.tsx` 의 무클래스 `div[data-locked]` 라 CSS 만으로는 잡을 자리가 없고, 그 div 를 flex 컬럼으로 바꾸면 머리·기본 정보 사이에도 34px 이 끼어 B3·B10 이 세운 구조를 건드린다. 이 WU 는 CSS 만 고친다.

## 후속

- `catalog.css:125-127` 에 `.lvl-3` 이 없다 — 마크업 `CatalogTable.tsx:159` 이 `lvl-3` 을 낸다. **미결-7 ⓐ(Lv0~Lv3 네 단)와 맞물린 Ted 판정 대상.** 이 WU 가 4단째 색을 임의로 정하지 않았다.
- `catalog.css:135` `.lin--none` = `--color-gray-400` on 흰 배경 → **3.41:1**(AA 미달). 판정 대기 → Ted.
- `detail.css:130` `.dt-gridact { margin: -8px 0 var(--space-4) }` = 음수 상쇄 **3건째**. WU-A11 도 R-B-4 재측정도 「2건」으로 세어 이 자리를 지목하지 않았다 — 판정 없이 고치지 않았다. 다음 회차 판정 대상.
- `lineageGraph.css` 코랄 액센트 색(`--color-accent-*`·`--color-ai`) 복원 — 목업 `:root` 회수 뒤.
