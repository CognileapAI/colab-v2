# WU-A11 · 디자인 검수 실측 (PRD-29 · 미결-10) — 판정표

레인 `p3-design-audit` · 기준 `origin/integration/r-a` = `947bf1f` · 2026-09-05
대상 6종 전부 확인 — `shell/tokens.css`(43행) · `shell/shell.css`(347) · `lineage/lineageGraph.css`(97) · `catalog/catalog.css`(168) · `detail/detail.css`(152) · `upload/upload.css`(230).
⛔ CSS 를 한 자도 고치지 않았다. 산출물은 이 표다. 대비·글자크기는 토큰 값에서 계산한 실측치다(WCAG 2.x 상대휘도).

| # | 항목 | 판정 | 근거 `path:line` · 실측값 |
|---|---|---|---|
| 1 | Lv 칩 글자색 (목업 Lv3 **3.71:1**) | **없음** | `detail.css:53` `.lvl-2,.lvl-3` = `#0f62e0` on `#e2eeff` → **4.66:1**(AA 4.5 통과) · `detail.css:52` Lv1 **4.94:1** · `detail.css:51` Lv0 `#565c63` on `#e8ecf2` **5.70:1**. 목업 결함이 v2 로 넘어오지 않았다 |
| 2 | 제약 안내 초록 → 파랑 · 버튼 위 | **없음** | v2 에 「제약 안내」 요소가 없다. 초록 토큰 사용처는 `catalog.css:128` `.verified` 배지 한 곳뿐(**5.69:1**)이고 이는 확인됨 배지지 제약 안내가 아니다 |
| 3 | 연결 불가 후보 행 흐림 (목업 **2.33:1**) | **없음** | 후보 목록 `lineage.css:105~117` `.lin-picker` 에 `opacity`·흐림 규칙이 0건. 흐리게 하는 자리 자체가 아직 없다(PRD-08 이 만든다) |
| 4 | 상단 메뉴 활성 탭 = 파랑 밑줄 | **없음** | `shell.css:183-192` `.mainnav a.is-active::after` 3px `--color-primary-600` 밑줄이 이미 있다. `shell.css:181` 의 `background: var(--color-surface)` 는 GNB 면색(`shell.css:104`)과 같은 값이라 색칠로 보이지 않는다 |
| 5 | 상단 버튼 알약 → 둥근 사각 | **없음** | `shell.css:203·224·244·134` 전부 `--radius-md`(10px) 둥근 사각. GNB 에 `--radius-pill`·`9999px` 사용 0건 |
| 6 | 카드 그림자 제거 | **있음** | `catalog.css:31` `.catalog-page .card { box-shadow: var(--shadow-sm) }` — 카드가 그림자를 진다. (허용: `catalog.css:80` `.colmenu` = 팝오버) |
| 7 | 계보 그래프 라벨 **13px 이상** | **있음** | `lineageGraph.css` 13개 선언이 13px 미만 — `:31` 10px · `:44` 10.5px · `:45` 12.5px · `:72` 10px · `:76` 12px · `:81` 11px · `:82` 10px · `:83` 10px · `:85` 10px · `:10` 11px · `:14` 11px · `:58` 11px · `:95` 11px. 최소 **10px** |
| 8 | 캡션 크기로 눌린 **7곳** | **있음** | 6종 합계 13px 미만 선언 **47건**. 지목된 4유형 = 파일명 `detail.css:101`(11px)·`upload.css:106`(12px)·`upload.css:168`(12px) / 빈 화면 안내 `lineageGraph.css:95`(11px) / 목록 링크 `lineageGraph.css:81`(11px)·`:76`(12px) / 오류 본문 `upload.css:92`(12px) — **7곳 충족** |
| 9 | 보더 2층 분리 | **있음** | `detail.css:59`(컨테이너) 와 `:62`(칸 구분선)가 같은 `--color-border` — 층이 안 갈린다. `catalog.css:30` 바깥선 `--color-border` vs `:41` 안쪽선 `--color-border-strong` 는 **역전**(안쪽이 더 진하다) |
| 10 | 여백을 컨테이너가 소유 | **있음** | 음수 상쇄 2건 — `detail.css:93` `margin: -12px 0 …` · `shell.css:58` `margin-left: -7px`. 자식 소유 여백 — `lineageGraph.css:7` `margin-top:34px` · `upload.css:95·112·127·130·148·150·171·189·191` `margin-top` |
| 11 | 죽은 스타일 (미사용 규칙 4 ＋ 덮인 선언 1) | **있음** | 덮인 선언 1 — `lineageGraph.css:33` `display:inline-block` 이 `:29` `display:inline-flex` 를 덮는다. 미정의 토큰 참조 **11건**(폴백 없음 → 선언 무효화) — `lineageGraph.css:30`(`--color-accent-50`,`-200`)·`:31`(`--color-accent-700`)·`:48`·`:49`(`--color-gray-300`)·`:51`(`--color-primary-800`)·`:57`(`--color-primary-200`,`-800`)·`:83`(`--color-accent-700`,`-50`)·`:84`(`--color-ai`) |

**있음 = 6건 / 11 · 없음 = 5건 / 11 · `[미상]` 0건.**

## R-B · WU-B11 범위 (있음 6건)

- 접근성 합격선(1·3·7) 중 **⑦ 계보 그래프 라벨 13px** 만 살아 있다 — **여기부터 돈다**(최소 10px, 13건).
  ①(4.66:1)·③(요소 부재)은 v2 에 결함이 없어 범위에서 빠진다. **없는 결함을 고치지 않는다.**
- ⑥ 카드 그림자 제거 (`catalog.css:31`)
- ⑧ 캡션 눌림 7곳 승격
- ⑨ 보더 2층 토큰 분리 (`detail.css:59/62` · `catalog.css:30/41` 역전 정정)
- ⑩ 여백 소유권 컨테이너 이관 ＋ 음수 상쇄 2건 제거
- ⑪ 죽은 스타일 제거 — 덮인 선언 1 ＋ 미정의 토큰 참조 11

## 추가 발견 (R-19~R-29 밖 · 참고)

- `catalog.css:126-128` 에 `.lvl-0/-1/-2` 는 있고 **`.lvl-3` 이 없다**. 마크업은 `CatalogTable.tsx:160` 등에서 `lvl-${processingLevel}` 로 Lv3 을 낸다(미결-7 = Lv0~Lv3 네 단) → 카탈로그·검색·프로젝트 표의 Lv3 칩은 배경·글자색이 붙지 않는다. **디자인 검수 11건과 별개 항목이라 여기서 판정하지 않는다.**
- `catalog.css:135` `.lin--none` = `--color-gray-400`(`#848c94`) on 흰 배경 → **3.41:1**(AA 미달). 역시 11건 밖.

## PLAN-SoT §9 초안 (병합 직전 〈N〉 재실측 — `origin/main` 최대 ＋ 1)

```
| 〈N〉 | **R-A-4 실측 — 디자인 검수 11건 판정. 판정 없이 고치지 않는다** | **실측 (2026-09-05 · 워크트리 `p3-design-audit` · 병합 `<sha>` · 계약 0 · 마이그레이션 0 · staging 접촉 0).** ①회차 = **해당 없음**(계약 미개방) ②값 = 없음 ③근거 = PRD-29 · 미결-10 (`dev-package/prd/PRD-260905-적용전기획.md`) ④가·파 판정 = 해당 없음 ⑤소비자 = 해당 없음 ⑥마이그레이션 = **0건** ⑦승인 = 불요 ⑧이번에 세지 않은 축 = `있음` 판정 6건의 수정(= R-B `WU-B11` 범위) `[미집행]`. **판정 결과** — 디자인 결함 있음 **6/11**(⑥⑦⑧⑨⑩⑪) · 접근성 3건 중 살아남은 것은 ⑦뿐(①=4.66:1 통과 · ③=요소 부재) |
```

## 게이트

돌릴 게이트가 없다 (R-A-4 §3-㉲ 축자 「WU-A11 은 돌릴 게이트가 없다 — 산출물이 판정표다」). CSS·코드 변경 0건이라 회귀면도 없다.
