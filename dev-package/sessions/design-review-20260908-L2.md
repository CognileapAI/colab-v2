# design-review L2 — 카탈로그·검색·상세·미리보기 (STATIC)

대상: `components/catalog/catalog.css` · `components/search/search.css` · `components/detail/detail.css` · `components/preview/preview.css` · 각 `.tsx`(`datasetpreview/` 인라인 `style=` 포함).
기준: `.claude/skills/design-review/SKILL.md` §0·§2-2·§2-3·§4 · `css_audit.md`(2026-09-08) · `p3-design-audit-20260905.md` 11항목 · `p3-design-fix-20260908.md` · WU-C11(`2c4d335`).
⛔ CSS·TSX 를 한 자도 고치지 않았다.

## 판정표

| # | 축 | 항목 | 판정 | 근거 path:line · 실측값 | 처리 |
|---|---|---|---|---|---|
| 1 | 이월 재판정 | `.lvl-3` 4단째(Lv 칩) | 없음 | `catalog.css:136` `.lvl-3 { background:#bad7ff; color:#0b4eb6 }` · WCAG 계산 **4.83:1** 통과. `detail.css:72` 동일 값 동일 통과. WU-C11 집행분, 잔존 없음 | — |
| 2 | 이월 재판정 | `.lin--none` 대비 | 없음 | `catalog.css:146` `color: var(--color-gray-500)`(#697077) on 흰 배경 → **5.04:1** 통과. WU-C11 집행분(gray-400→500), 잔존 없음 | — |
| 3 | 이월 재판정 | `.dt-gridact` 음수 여백 | 없음 | `detail.css:148` `margin` 선언 자체가 없다(`display:flex; gap:8px…`만). 여백은 `.dt-split-r` gap(`:283`·`:294`)이 소유. WU-C11 집행분, 잔존 없음 | — |
| 4 | 정적 | `.verified--pending` 대비 | 있음 | `catalog.css:140` `background: var(--color-gray-100)`(#e8ecf2) `color: var(--color-gray-500)`(#697077) → 직접 계산 **4.25:1**(스크립트 4.23:1) — AA 4.5 미달. WU-A11·B11·C11 어느 판정표에도 지목되지 않은 신규 발견 | Ted 판정 |
| 5 | 정적 | `.dsec-menu-i.is-active` 대비 | 있음 | `detail.css:230-233` `background: var(--color-primary-50)`(#edf4ff) `color: var(--color-primary-600)`(#1369e9) → 직접 계산 **4.51:1**(스크립트 4.49:1) — 경계값, AA 4.5 기준 스크립트는 미달·직접 계산은 근소 통과. 판정표 어디에도 지목되지 않은 신규 발견 | Ted 판정 |
| 6 | 정적 | 글자 13px 미만 — catalog.css | 있음 | 14건 — `:46` th 10px(라벨) · `:71` 정렬표식 9px(장식) · `:89` 열메뉴 섹션표제 10px(캡션) · `:92` 열메뉴 항목 12px(메뉴텍스트) · `:98` 체크박스 표식 9px(장식) · `:102` 열메뉴 카운트 11px(캡션) · `:107` 열메뉴 지우기 11px(캡션) · `:117` 필터라벨 11px(캡션) · `:121` 필터칩 11px(뱃지) · `:125` 전체지우기 11px(캡션) · `:127`·`:130`·`:137`·`:141` 칩류(`.chip`·`.lvl`·`.verified`·`.lin`) 11px(뱃지). 전부 뱃지·캡션류로 이전 승격 대상(`.fl-k`·`.fl-x`·`.up-note` 등) 계열과 다르다 — 지목 이력 없음 | Ted 판정 |
| 7 | 정적 | 글자 13px 미만 — detail.css | 있음 | 9건 — `:63` `.chip` 11px(뱃지) · `:66` `.lvl` 11px(뱃지) · `:88` `.ig .k` 10px(테이블/격자 라벨, `:154`·`:167`·`:188`와 같은 셀렉터 계열) · `:112` `.ig-more` 11px(버튼) · `:141` `.use-dl-note` 12px(캡션, PRD-39 ⑩ 명시적으로 「버튼보다 작게」 의도) · `:154` `.dt-files-k` 10px(라벨, `:88`과 동일 패턴) · `:167` `.fl-gh` 10px(라벨, 동일 패턴) · `:188` `.de-k` 10px(폼 라벨, 동일 패턴) · `:190` `.de-req` 9px(뱃지). `.fl-k`(`:120`)·`.fl-x`(`:124`)는 WU-B11 이 13px 로 이미 승격되어 이번 9건에 없다 | Ted 판정 |
| 8 | 정적 | 글자 13px 미만 — search.css | 있음 | 2건 — `:52` `.notice--empty .muted` 11px(캡션, 부가 안내) · `:124` `.verified` 11px(뱃지, catalog/detail 의 `.verified`·`.chip`·`.lvl`·`.lin` 11px 뱃지 계열과 동일 패턴) | Ted 판정 |
| 9 | 정적 | 글자 13px 미만 — preview.css | 있음 | 2건 — `:286` `.pv-value` 12px(값 조회 패널 본문) · `:356` `.pv-pick-f > span` 12px(선택 라벨). 나머지 `.pv-legend`·`.pv-control`·`.pv-slot-note`·`.pv-muted`·`.pv-zoom`·`.pv-shot`·`.pv-hud`·`.pv-pick`(13px·12px 혼재)는 css_audit 이 세지 않은 13px 선언 다수를 포함 — 13px 정확값은 위반 아님, `.pv-hud`(`:286` 아님·`:284-289`)만 12px | Ted 판정 |
| 10 | 정적 | 카드 그림자 | 없음 | `catalog.css:33-38` `.card` 그림자 선언 없음(WU-B11 제거). `catalog.css:58` inset(hover 피드백)·`:86` `--shadow-lg`(`.colmenu` 팝오버, 허용) 만 존재. search·detail·preview.css 는 box-shadow 선언 0건 | — |
| 11 | 정적 | 음수 여백 | 없음 | 4개 파일 전수 `grep 'margin.*-[0-9]'` — 매치는 전부 `margin: 0 …`·`margin-bottom: var(--space-N)` 류 양수/변수이고 실제 음수 선언 0건. `detail.css:86`·`:146` 주석은 WU-C11 이 제거한 과거 음수를 설명하는 문구 | — |
| 12 | 정적 | 보더 2층 분리 | 없음 | `catalog.css:36` 바깥 `--color-border-strong` vs `:52` 안쪽 `--color-border` — 역전 없음(WU-B11 정정 유지). `detail.css:79` `.infogrid` 바깥 `--color-border-strong` vs `:82` 안쪽 `--color-border` — 층 분리 유지(WU-B11). search·preview.css 는 격자/표 패턴이 없어 해당 축 대상 자체가 없음 | — |
| 13 | 정적 | 여백 컨테이너 소유 | 없음 | 4개 파일에서 자식 `margin-top` 이 형제 간격을 만드는 자리 0건 — `search.css .hits` gap(`:54`) · `preview.css .preview-page`·`.pv-controls`·`.pv-shot` 등은 전부 `gap`/컨테이너 여백. 개별 요소 자기 `margin`(`:39`·`:58` 등)은 컨테이너 소유 원칙과 충돌하지 않는 단독 요소 | — |
| 14 | 정적 | 죽은/덮인 선언 | 없음 | 4개 파일 셀렉터 중복 검사 — 실질 중복 0건(`search.css:45-46` `.quiet,\n.strong {` 은 결합 셀렉터 표기일 뿐 중복 규칙 아님). `detail.css` `.detail-page { }` 블록이 `:36`·`:260` 두 곳에 있으나 서로 다른 속성(치수 vs 커스텀 프로퍼티)이라 덮음 없음 | — |
| 15 | 파일 내 토큰 ⓐ 컴포넌트 전용 | `--dt-split-*`(detail.css:262-266) · `--pv-frame-ratio`(preview.css:295) | 없음 | 접두사가 그 화면 고유 — 정의 그대로 사용, 문제 없음 | — |
| 16 | 파일 내 토큰 ⓑ 전역 어휘 중복 | catalog.css 18건 · detail.css 30건 | 있음 | 중복 정의 12개 이름이 두 파일 모두에 있다 — `--color-gray-100`(#e8ecf2=#e8ecf2)·`--color-gray-600`(#565c63=#565c63)·`--color-gray-700`(#434950=#434950)·`--color-warning-50`(#fff6ed=#fff6ed)·`--color-warning-600`(#a85400=#a85400)·`--color-primary-50`(#edf4ff=#edf4ff)·`--color-primary-100`(#e2eeff=#e2eeff)·`--color-primary-200`(#bad7ff=#bad7ff)·`--color-primary-800`(#0b4eb6=#0b4eb6)·`--font-data`(var(--font-sans)=var(--font-sans))·`--radius-lg`(12px=12px)·`--radius-pill`(9999px=9999px). **12개 전부 값 일치** — 불일치 0건. `tokens.css` 에는 이 12개 이름이 없다(`grep` 확인) | Ted 판정 |
| 17 | 정적 · 신규 발견(11항목 밖) | search.css 폴백 hex ↔ 실제 토큰값 불일치 | 있음 | search.css 는 자체 `:root` 없이 `var(--토큰, 폴백hex)` 만 쓴다. 폴백이 `shell/tokens.css` 실측값과 다른 자리 — `:15`·`:70` `--color-primary-600` 폴백 `#1f5eff` vs 실값 `#1369e9`(불일치) · `:51` 같은 토큰 폴백 `#0f62fe`(파일 내부에서도 `:15`·`:70` 과 서로 다름) · `:75` `--color-text` 폴백 `#1b1f24` vs 실값 `#121619`(불일치) · `:125` `--color-success-50` 폴백 `#e6f4ea` vs `catalog.css:10` 정의값 `#efffef`(불일치) · `:115`·`:116`·`:120`·`:125`·`:128` `--color-success-600` 폴백 `#1f8b4c` vs `catalog.css:11` 정의값 `#067506`(불일치) · `:33` vs `:50` `--color-border` 폴백 `#dfe3e8` vs `#dde1e6`(파일 내부 불일치, 실값은 `#e8ecf2` 로 셋 다 다름). 현재는 토큰이 다른 파일(`catalog.css`)·`tokens.css` 에 정의돼 있어 폴백이 렌더에 쓰이지 않지만, 로드 순서·트리셰이킹이 바뀌면 값이 갈린다 — css_audit 스크립트는 "토큰이 어딘가 정의됨"만 보고 undefined 0건으로 셌다(오탐은 아니고 스크립트 축 밖의 위험) | Ted 판정 |
| 18 | 정적 | preview.css 미정의 토큰 20건 | 있음 | 전부 폴백 있음 — `--line`(`:32`#e2e2e2·`:74`#eee·`:113`#e2e2e2·`:165`#d8d8d8·`:186`#e2e2e2·`:231`#e2e2e2·`:303`#e2e2e2, **파일 내부에서 3개 값 혼재**) · `--surface-2`(`:34`#f7f7f6·`:115`#f5f5f4·`:188`#f5f5f4·`:305`#f5f5f4, `:34`만 다름) · `--ink-1`(`:49`·`:51` #1f1f1f 일치) · `--ink-2`(`:20`#555·`:81`#666·`:101`#666·`:159`#666, `:20`만 다름) · `--ink-3`(`:172`#888) · `--accent`(`:206`#2f6feb) · `--surface-1`(`:233`#fff). 전부 `shell/tokens.css`·다른 컴포넌트 css 어디에도 정의되지 않은 순수 미정의 어휘(catalog·detail 의 `--color-*` 와 달리 다른 파일에 실정의가 없다) | Ted 판정 |
| 19 | 정적 | `datasetpreview/` 인라인 `style=` | 없음 | `PreviewPanels.tsx:376`(스와치 동적 색) · `:419-424`(타일 위치·크기) · `SearchHitCard.tsx:60`(관련도 막대 폭) — 3곳 전부 런타임 계산값(좌표·비율·데이터 색)이고 고정 디자인값을 인라인으로 박은 자리 없음 | — |

## 소계

있음 9건(4·5·6·7·8·9·16·17·18) · 없음 10건(1·2·3·10·11·12·13·14·15·19) · `[미상]` 0건.

## css_audit 오탐

없음 — 스크립트 수치(catalog 14·detail 9·search 2·preview 2 <13px, preview 20 미정의 토큰, catalog 18·detail 30 로컬 토큰, 대비 2건)가 실물 규칙과 전부 일치했다.

## 이월 재판정(WU-C11 후 잔존)

`.lvl-3`(#4)·`.lin--none`(#5)·`.dt-gridact`(#3) 3건 모두 WU-C11 집행 후 잔존 없음 — 재개방하지 않는다.

## Ted 판정 후보

- **#4·#5 대비 미달/경계** — ⓐ `.verified--pending`·`.dsec-menu-i.is-active` 색을 한 단 더 진하게 올린다(4단 램프 다음 단) / ⓑ 배경을 한 단 연하게 올린다. 권고: ⓐ(문자색 강화). `.dsec-menu-i.is-active` 는 4.51:1 로 근소 통과 가능성도 있어 실제 렌더 스크린샷 재계측 권고.
- **#6·#7·#8·#9 뱃지·캡션 13px 미만** — ⓐ 뱃지류(`.chip`·`.lvl`·`.verified`·`.lin`·`.cm-i .cm-n` 등, 총 4파일 합계 27건)는 정본에 `Lv 칩`·`chip` 이 목업에서부터 11px 로 설계된 값이라 승격이 아니라 예외 등재 / ⓑ 13px 문턱을 뱃지류엔 적용하지 않는 별도 문턱(예: 11px)을 세운다. 권고: ⓑ(목업 다수 배지가 11px 로 일관돼 별도 문턱이 실태에 맞는다). 라벨류(`.ig .k`·`.dt-files-k`·`.fl-gh`·`.de-k` 10px 4곳 동일 패턴)와 장식용 표식(`.thf::before` 9px)은 문턱 예외에서도 따로 판단 필요.
- **#16 전역 어휘 12개 중복(전부 값 일치)** — ⓐ `tokens.css` 로 승격 / ⓑ 컴포넌트별 현행 유지. 권고: ⓐ(값이 이미 100% 일치하므로 승격 비용 0, 드리프트 방지 이득만 있다).
- **#17 search.css 폴백 hex 드리프트** — ⓐ 폴백을 `tokens.css` 실값으로 정정 / ⓑ `:root` 없이 참조만 하는 구조를 버리고 필요한 토큰을 직접 정의. 권고: ⓐ(최소 변경, 폴백은 안전망이지 값 정본이 아니다).
- **#18 preview.css 미정의 어휘(`--line`·`--surface-1/2`·`--ink-1/2/3`·`--accent`) 20건** — ⓐ `tokens.css` 정본 어휘(`--color-border`·`--color-surface`·`--color-text*`·`--color-primary-600`)로 치환 / ⓑ `preview.css` 전용 프리픽스(`--pv-*`)로 새로 세운다. 권고: ⓐ(다른 3개 파일이 이미 `--color-*` 정본을 쓰고 있어 preview 만 다른 어휘계를 쓰는 것 자체가 불일치. `--line` 폴백 3종·`--surface-2` 폴백 2종 불일치는 치환 시 자동 해소).

## 이번에 세지 않은 축

- apple-design 모션·인터랙션 축(요청 범위 = STATIC 전용, L4 별도 레인 소관).
- 스크린샷 필요한 실화면 계측(hover/focus 상태 시각·스프링감 등) — 이번 4개 파일에서 정적 근거로 닫히지 않는 항목 없음, `[미상]` 0건.
- `catalog.css` `.lvl-3` 부재·`.lin--none` 미달은 L2 자체가 아니라 상위 이월 판정 대상이었고 WU-C11 이 이미 닫아 이번 표 #1·#2 로만 재확인.
