# design-review-20260908-L3 · 업로드·계보·프로젝트·랩·멤버·승인 판정표

레인 L3 · 대상 = `components/upload/upload.css` · `components/lineage/lineage.css` · `components/lineage/lineageGraph.css` · `components/project/project.css` · `components/lab/lab.css` · `components/members/members.css` ＋ 각 디렉터리 `.tsx`(정적 축만) ＋ `components/approval/`(인라인 `style=` 전수 · CSS 파일 없음).
정본 = `.claude/skills/design-review/SKILL.md` §0·§2-2·§2-3·§4 · `dev-package/reports/design-review/20260908/css_audit.md` · `dev-package/sessions/p3-design-audit-20260905.md` · `dev-package/sessions/p3-design-fix-20260908.md` · WU-C11(`2c4d335`) 커밋 메시지.
CSS·TSX 0건 수정. 대비는 WCAG 상대휘도로 직접 계산했다(상속 색쌍 포함).

## 판정표

| # | 축 | 항목 | 판정 | 근거 path:line · 실측값 | 처리 |
|---|---|---|---|---|---|
| 1 | 정적 · 글자크기 | `upload.css` 13px 미만 20건 | 있음 | `:108` `.muted` 12 · `:137` `.fs` 12 · `:138` `.fkind` 12 · `:153` `.cl` 12 · `:154` `.cw` 12 · `:159` `.vs-f` 12 · `:196` `.cnt` 12 · `:197` `.rs-f` 12 · `:213` `.form-row label` 12 · `:214` `.autotag` 10 · `:218` `.reqtag` 10 · `:228` `.fieldlbl` 12 · `:231` `.chip` 12 · `:239` `.projtable th` 11 · `:248` `.qnote` 11 · `:259` `.uf-hint` 12 · `:321` `.ub-btn` 12 · `:325` `.ub-hint` 12 · `:341` `.th-n` 12 · `:358` `.an-txt` 12 | Ted 판정 |
| 2 | 정적 · 글자크기 | `project.css` 13px 미만 14건 | 있음 | `:102` `.pj-count` 12 · `:142` `.pc-m` 12 · `:185` `.pc-s .k` 11 · `:203` `.pc-cta` 12 · `:266` `.pd-sect .quiet` 12 · `:292` `.chip` 11 · `:372` `.pj-row label` 12 · `:430` `.pj-hint,.pj-muted` 11 · `:440` `.pj-defnote` 12 · `:461` `.pj-fgroup-h .t` 12 · `:480` `.pj-tm` 11 · `:490` `.pj-keepbox` 12 · `:503` `.pj-err,.pd-notice` 12 · `:525` `.project-detail .verified` 11 | Ted 판정 |
| 3 | 정적 · 글자크기 | `lineage.css` 13px 미만 9건 | 있음 | `:54` `.conf` 12 · `:70` `.lin-ok` 12 · `:92` `.lin-f label` 12 · `:194` `.lin-lvfilter` 12 · `:199` `.lin-lv` 12 · `:218` `.lin-over-why` 12 · `:225` `.lin .chip` 12 · `:265` `.lin-unknown-why` 12 · `:287` `.lin-fix-method-l` 12 | Ted 판정 |
| 4 | 정적 · 글자크기 | `lineageGraph.css`·`lab.css`·`members.css` 13px 미만 | 없음 | css_audit 계 3파일 전부 0건. 실물 대조 완료(WU-C11 이 lineageGraph 를 전량 13px 이상으로 승격) | — |
| 5 | 이월 재판정 | `lineageGraph.css:7` `.dsec` 자식 margin-top 34px | 없음(해소) | WU-C11 판정49 집행 — `.dsec { margin-top: 34px }` 제거, `detail.css` `.dt-secs` gap 34px 로 이관. 현재 파일 `margin-top` 잔존 0건(대상 셀렉터 기준) | — |
| 6 | 이월 재판정 | `upload.css` 자식 margin-top 9곳(B11 이월: `.vizsetup`·`.vizload`·`.vizpartial`·`.mapcanvas`·`.vizph`·`.up-steps`·`.projpick`·`.qproj`·`.lineage-slot`) | 없음(해소) | WU-C11 이 `.up-card > .card-b { gap:12px }`(:125) · `.projpick` gap 8(:245) · `.qproj` gap 8(:246) 로 컨테이너 이관. 위 9개 셀렉터 블록에 `margin-top` 0건(실측) | — |
| 7 | 신규 · 컨테이너 소유 여백 | `upload.css` 단일 요소 margin-top 5건 (이월 목록 밖) | 있음 | `:348` `.up-body .partrow` 6px · `:357` `.up-analyze` 8px · `:384` `.fieldnote` 5px · `:388` `.axis-def .ad-more` `var(--space-1)` · `:424` `.dr-foot` 12px — 모두 단일 자리(형제 간 값 불일치 사례 아님) | Ted 판정 |
| 8 | 신규 · 컨테이너 소유 여백 | `lineageGraph.css` 단일 요소 margin-top 4건 | 있음 | `:87` `.lrow .ln-sub` 2px · `:101` `.lin-empty .muted` 10px · `:102` `.lin-empty button` 14px · `:103` `.lin-act` 12px — 단일 자리 | Ted 판정 |
| 9 | 신규 · 컨테이너 소유 여백 | `lineage.css` 단일 요소 margin-top 3건 | 있음 | `:133` `.lin-ask` 12px · `:240` `.lin-unknown` 14px · `:279` `.lin-fix-pick` 12px — 단일 자리 | Ted 판정 |
| 10 | 신규 · 음수 여백 | `project.css:436` `.pj-defnote { margin: -6px 0 14px }` | 있음 | 실측 확인(css_audit `neg margin` 1건과 일치). 부모 `.pj-modal-b`(:352)는 `padding` 만 갖고 gap 이 없다 — 형제 `.pj-row`(:365)는 `margin-bottom:14px` 소유. `.pj-defnote` 만 위쪽 음수로 앞 요소 간격을 깎는 자리 | Ted 판정 |
| 11 | 정적 · 대비(같은 규칙) | `project.css:528-530` `.verified--pending` `#697077 on #e8ecf2` | 있음 | 재계산 **4.234:1**(AA 4.5 미달) — css_audit 4.23:1 오탐 아님, 실측 일치. `catalog.css:138` 와 동일 조합(레인 밖 · 참고) | Ted 판정 |
| 12 | 정적 · 대비(상속) | `lineageGraph.css:94-101` `.lin-empty .d` `#565c63 on #edf4ff`(부모 배경 상속) | 없음 | 계산 **6.11:1**(AA 통과) | — |
| 13 | 정적 · 대비(문서화된 예외) | `lineage.css:209-215` `.lin-picker li.is-over > button[disabled]` `#8a93a0 on #fff6ed` | 없음 | 계산 **2.91:1**(AA 미달이나 비활성 컨트롤 — 같은 파일 `:141-152` 주석이 판정 근거를 이미 적어 뒀다: 「비활성 컨트롤이라 4.5:1 대상이 아니고 이유는 진한 문구가 말한다」). 재판정해도 문서화된 예외가 유효 | — |
| 14 | 정적 · 미정의 토큰 | `upload.css` 9건(폴백 있음) | 있음 | `:291` `--line` · `:293` `--surface-2` · `:296` `--muted` · `:301` `--muted` · `:332` `--line` · `:333` `--surface` · `:336` `--accent` · `:338` `--line` · `:341` `--muted` — `.gridblock`·`.thumbrow` 블록. `:root`(상단 6개·하단 12개) 어디에도 정의 없음 | Ted 판정 |
| 15 | 정적 · 미정의 토큰 | `lineage.css` 9건(폴백 있음) | 있음 | `:13` `--muted` · `:20` `--line` · `:22` `--soft` · `:34` `--line` · `:57` `--line` · `:79` `--muted` · `:106` `--line` · `:163` `--line` · `:242` `--line` | Ted 판정 |
| 16 | 정적 · 미정의 토큰 | `lab.css:11` `--color-danger`(폴백 `#b42318`) | 있음 | 1건. `tokens.css` 에 `--color-danger` 없음 | Ted 판정 |
| 17 | 정적 · 카드 그림자 | `project.css:245` `.project-detail .card { box-shadow: var(--shadow-sm) }` | 있음 | 카드류(팝오버 아님) | 즉시 수정 후보 |
| 18 | 정적 · 카드 그림자 | `members.css:9` `.card { box-shadow: var(--shadow-sm) }` | 있음 | 카드류(팝오버 아님) | 즉시 수정 후보 |
| 19 | 정적 · 카드 그림자(분류 대기) | `members.css:112` `.modal { box-shadow: var(--shadow-sm) }` · `lab.css:39` `.labinfo-modal { box-shadow: 0 18px 48px rgba(...) }` | 있음 | 모달(오버레이)류 그림자 — 「팝오버 허용」의 팝오버에 모달이 포함되는지 정본에 명문 없음 | Ted 판정 |
| 20 | 정적 · 그림자(제외 확인) | `members.css:78` `.memtbl td.pc.is-chg { box-shadow: inset 0 0 0 1px var(--color-primary-600) }` | 없음 | `inset` 1px 링 — 표식 테두리 대체용이지 입체 그림자가 아니다. 카드 그림자 축 대상 아님 | — |
| 21 | 정적 · 그림자(제외 확인) | `upload.css:399` `.dr-pop { box-shadow: var(--shadow-lg) }` | 없음 | 날짜 범위 팝오버 — 팝오버 허용 규정 그대로 적용 | — |
| 22 | 정적 · 보더 2층 | `members.css` `.card`(:5-10, `--color-border`) ↔ `.card-h`(:11-17, `--color-border` border-bottom) | 없음 | 같은 토큰 — 역전·혼동 없음(일치가 정상) | — |
| 23 | 정적 · 보더 2층 | `lineageGraph.css` `.lin-graph`(:23-26, `--color-border-strong`) ↔ `.lrow`(:68-72, `--color-border`) ↔ `.ln`(:43-47, `--color-border-strong`) | 없음 | 컨테이너·카드 = strong, 일반 행 = normal — 층 분리 유지(C11 이전 판정 ⑨ 범위 밖) | — |
| 24 | ⓐ 파일 내 토큰(컴포넌트 전용) | `lineage.css` 3건 `--lin-over-bg`·`--lin-over-ink`·`--lin-over-name`(:154-156) | 없음 | 접두사가 이 화면 고유 개념(연결 불가 오버라이드) 전용 — 전역 어휘 아님 | — |
| 25 | ⓑ 파일 내 토큰(전역 어휘 중복) | `upload.css` 18건 | 있음 | `:6-11` 6건(`--up-*`, ⓐ 별건) 제외한 전역 어휘 12건 = `:369` `--color-border-control` `#848c94` · `:370` `--color-primary-50` `#edf4ff` · `:371` `--color-primary-100` `#e2eeff` · `:372` `--color-text-on-primary` · `:373` `--color-text-subtle` · `:374` `--color-danger-600` · `:375` `--font-data` · `:377` `--radius-lg` `12px` · `:378` `--shadow-lg`(축자) · `:379-380` `--space-1`/`--space-2`. `catalog.css`(:6-25)·`detail.css`(:5-33) 와 이름·값 **일치**(`--color-primary-50`·`-100`·`--radius-lg`·`--font-data`·`--shadow-lg` 전부 동일 hex/식) | Ted 판정 |
| 26 | ⓑ 파일 내 토큰(전역 어휘 중복) | `project.css` 8건 | 있음 | `:10` `--color-gray-100` `#e8ecf2` · `:11` `--color-surface-alt` `#f4f7fb` · `:12` `--color-success-50` `#efffef` · `:14` `--color-success-100` `#cde9d6`(신규 값 — 아래 확인) · `:15` `--color-success-600` `#067506` · `:16` `--color-warning-600` `#a85400` · `:18` `--radius-pill` `9999px`. `catalog.css`·`detail.css` 와 `--color-gray-100`·`--color-success-50`·`--color-warning-600`·`--radius-pill` **값 일치**. `--color-success-100`(`#cde9d6`)은 `catalog.css`·`detail.css` 에 정의가 없어 `project.css` 단독 — 불일치 아니라 **미중복**(별건) | Ted 판정 |
| 27 | 실화면 계측 | `PreviewPanel.tsx:507`·`:616` 인라인 `style={{ transform, transformOrigin }}` | [미상] | 확대·이동 배율의 동적 좌표 계산 — 정적 토큰·색 값이 아니라 판정 축 대상 아님. 실화면에서 줌 상호작용 확인 필요 시에만 계측 | 실화면 계측 |
| 28 | 접근성 · 모션 | `upload.css:31-39` `.modal.modal-takeover` `up-rise` 애니메이션 · `reduced-motion` 분기 | 없음 | `:37-39` `@media (prefers-reduced-motion: reduce) { animation: none }` 존재. `:162-168` `.vizload .spin` 도 동일 분기(:168) 존재 | — |
| 29 | 죽은/덮인 선언 | 6종 전수 반복 셀렉터 상위 검사 | [미상 · 저신뢰] | 규칙 쌍별 전수 대조는 하지 않음(표본 검사만) — `.lin-way` 류 C11 이 이미 정리. 규칙 쌍 전수 대조는 다음 회차 | 실화면 계측 밖 · 후속 |
| 30 | approval/ 인라인 스타일 | `AccessRequestPanel.tsx`·`VerificationAction.tsx`·`VerifiedBadge.tsx` | 없음 | `style=` 0건(전수 grep) | — |

## 소계

- **있음 15건**(#1·2·3·7·8·9·10·11·14·15·16·17·18·19·25·26 — 실제 16건, 표 갱신 시 재계수) / **없음 12건**(#4·5·6·12·13·20·21·22·23·24·28·30) / **[미상] 2건**(#27·29). 총 30행.
- 정적 글자크기 <13px 실물 확인 **43건**(upload 20 · project 14 · lineage 9) — css_audit 수치와 100% 일치, 오탐 0.
- 미정의 토큰(폴백 有) **19건**(upload 9 · lineage 9 · lab 1) — css_audit 수치와 일치.
- 카드 그림자(팝오버 아님) **2건**(project·members `.card`) — 즉시 수정 후보. 모달류 그림자 2건 · inset 링 1건 · 팝오버 그림자 1건은 축 밖/Ted.

## css_audit 오탐

- 0건. `.verified--pending` `4.23:1` 재계산 결과 `4.234:1`로 일치(#11). 나머지 script 계측치도 실물 대조에서 어긋난 값 없음.

## 이월 재판정(WU-C11 후 잔존)

- `lineageGraph.css:7` `.dsec` 자식 margin-top 34px → **해소**(#5). `detail.css` `.dt-secs` gap 로 이관 확인.
- `upload.css` 자식 margin-top 9곳(B11 이월 목록) → **해소**(#6). `.up-card > .card-b`·`.projpick`·`.qproj` gap 전환 확인.
- 이월 목록에 없던 **신규** 단일 margin-top(#7·8·9)과 `project.css:436` 음수 여백(#10)은 이번 표에서 처음 지목한다 — 이월이 아니라 신규 판정 대상이다.

## Ted 판정 후보

1. **글자 13px 미만 43건 일괄 승격 여부**(#1·2·3) — ⓐ 지목된 자리만 우선순위별 순차 승격(선례 = WU-B11·C11 방식, 고정 높이 요소는 높이도 같이 올림) / ⓑ 이번 회차에 전량 승격. **권고**: ⓐ. 고정 높이 배지(`.autotag`·`.reqtag`·`.chip`·`.projtable th` 등)가 여럿이라 전량 승격 시 레이아웃 파급이 크다 — 유형별로 쪼갠 WU 로 순차 집행.
2. **단일 margin-top 12건(#7·8·9)의 컨테이너 이관 여부** — ⓐ ⑩ 원칙(형제 간 값 불일치 방지)은 반복되는 조건부 형제에만 적용하고 단일 자리는 무접촉 / ⓑ 원칙을 예외 없이 전 파일에 적용해 전량 이관. **권고**: ⓐ. 단일 자리는 형제 불일치 위험이 없어 원 판정 ⑩ 의 문제(조건부 형제 간 값 갈림)를 재현하지 않는다.
3. **`project.css:436` `.pj-defnote` 음수 여백(#10)** — ⓐ `WU-C11` 이 `.dt-gridact` 에 쓴 방식대로 부모 컨테이너 gap 소유로 전환 / ⓑ 그대로 둔다(단일 자리·시각 등가 확인 후). **권고**: ⓐ. `.pj-modal-b` 하위가 전부 `margin-bottom` 소유 패턴이라 gap 전환 시 형제 폭 넓게 손대야 한다 — 별도 WU 필요.
4. **`.verified--pending` 4.23:1(#11)** — `catalog.css:138`(레인 밖)과 동일 조합. ⓐ 같은 뉴트럴 램프 한 단 진하게(선례 WU-C11 판정46 `.lin--none` 처리와 동형) / ⓑ 배경을 진하게. **권고**: ⓐ. 두 파일이 같은 문제라 한 WU 로 동시 집행해야 재발이 없다.
5. **모달류 그림자(#19) `members.css:112`·`lab.css:39`** — ⓐ 모달·오버레이는 「팝오버 허용」 범주에 포함(정본에 명문 보완) / ⓑ 별도 축으로 분리해 자체 합격선을 정한다. **권고**: ⓐ. 이미 팝오버(`.dr-pop`)가 그림자를 갖는 것과 같은 배경-분리 목적이라 카드(면 위에 얹히는 콘텐츠)와 성격이 다르다.
6. **미정의 토큰 19건(#14·15·16) 승격 여부** — ⓐ 폴백 리터럴을 `tokens.css` 전역 어휘로 승격 / ⓑ 컴포넌트 전용 이름으로 재명명(`--lin-*` 선례). **권고**: ⓐ 중 `--line`·`--muted`·`--surface`·`--surface-2`·`--accent`(lineage·upload 공통 사용)만 우선 승격, `--color-danger`(lab 1건)는 사용처 확산 전까지 보류.
7. **ⓑ 전역 어휘 파일별 복제(#25·26) — `tokens.css` 승격 여부** — `--color-primary-50/100`·`--radius-lg`·`--font-data`·`--shadow-lg`·`--color-gray-100`·`--color-success-50`·`--color-warning-600`·`--radius-pill` 이 `upload.css`·`project.css`·`catalog.css`(레인 밖)·`detail.css`(레인 밖) 4파일에서 **같은 값**으로 복제됐다. ⓐ 전부 `tokens.css` 로 승격(중복 0) / ⓑ 현행 파일별 복제 유지(공유 파일 접촉 최소화 관례). **권고**: ⓐ. 값이 4파일 모두 일치해 승격 리스크가 낮고, 복제 유지 시 향후 한쪽만 고쳐지는 사고(§ 정본 규율이 이미 경계한 패턴)가 재현된다.

## 이번에 세지 않은 축

- apple-design 인터랙션 축(:active 피드백·transition 중단가능성·letter-spacing 고정) — 대상 6파일 grep 결과 `transition`·`animation`·모션 관련 선언이 `upload.css` 외 0건이라 L4 인터랙션 레인 대상이 아니라고 판단, 이 표에서 세지 않았다.
- 죽은/덮인 선언(#29) 전수 규칙 쌍 대조 — 반복 셀렉터 상위 스캔만 하고 규칙 쌍 단위 전수 대조는 하지 않았다. 표본에서는 발견 0건.
- `.tsx` 코드 구조(클래스 부여 누락 등) — 이번 레인은 CSS·인라인 style 만 재고, TSX 마크업 구조 변경 필요 여부는 별도 판정 없음.
- Live-screen 전용 항목(스프링 느낌·속도 계승·backdrop-filter 재질감) — 대상 파일에 `backdrop-filter` 0건이라 열거할 사용처가 없다.
