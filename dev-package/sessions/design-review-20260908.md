# design-review 20260908 — 통합 판정표 (레인 4개 취합)

- 기준 트리 = `cc05c44` (워크트리 `design-skills`) · 날짜 = 2026-09-08.
- 계약 0 · 서버 0 · 스키마 0 · 마이그레이션 0 · 코드 변경 0. 레인 4개 전부 CSS·TSX 를 한 자도 고치지 않았다.
- 계측 보고 = `dev-package/reports/design-review/20260908/css_audit.md`.
- 레인 분할과 각 소계(행 수 실측)

| 레인 | 범위 | 행 | 있음 | 없음 | [미상] |
|---|---|---|---|---|---|
| L1 | 셸·공통 — `shell/shell.css`·`shell/tokens.css`·`components/common/toast.css`·`components/common/variableTable.css`·`auth/login.css`·`components/dashboard/dashboard.css` | 19 | 4 | 13 | 2 |
| L2 | 카탈로그·검색·상세·미리보기(정적) — `catalog.css`·`search.css`·`detail.css`·`preview.css` ＋ `datasetpreview/` 인라인 style | 19 | 9 | 10 | 0 |
| L3 | 업로드·계보·프로젝트·랩·멤버·승인 — `upload.css`·`lineage.css`·`lineageGraph.css`·`project.css`·`lab.css`·`members.css` ＋ `approval/` | 30 | 16 | 12 | 2 |
| L4 | 인터랙션·모션(apple-design 전용) — `login.css`·`catalog.css`·`members.css`·`search.css`·`upload.css`·`shell.css` ＋ 오버레이·팝오버·토스트·줌팬 `.tsx` | 31 | 16 | 11 | 4 |
| 계 | — | 99 | 45 | 46 | 8 |

- L3 본문 소계는 「있음 15건」, L4 본문 소계는 「있음 15 · 없음 12」로 적혀 있으나 표 행 실측은 각각 16/12/2 · 16/11/4 다. 이 문서는 행 실측값을 쓴다.
- L4 는 판정 의미가 뒤집힌 레인이다 — 항목 문구가 「장치 서술」인 행은 `없음` 이 결함이다. 따라서 §2 에는 L4 의 `없음` 행 가운데 처리가 `Ted 판정` 인 3행(L4 #13·#20·#21)도 실었다.

---

## 2. 통합 판정표 (있음 · [미상] 전건 · L4 결함성 없음 3건 포함)

| # | 레인 | 축 | 항목 | 판정 | 근거 path:line · 실측값 | 처리 |
|---|---|---|---|---|---|---|
| 1 | L1 | 정적 | 카드 그림자 0(팝오버 허용) | 있음 | `auth/login.css:20` `.login-card { box-shadow: var(--shadow-sm) }` — `login-card` 는 카드다(팝오버·메뉴·토스트 아님) | 즉시 수정 후보 |
| 2 | L1 | 접근성 | 글자 13px 미만 | 있음 | `shell/shell.css:82` `.backlink .bl-a` 11.0px · `components/common/toast.css:17` `.toast` 12.0px · `components/dashboard/dashboard.css:140·185·190·228·268·288·326·337·352` 9건 12.0px. 합계 **11건** | 즉시 수정 후보 |
| 3 | L1 | 정적 | 보더 2층 토큰 분리(컨테이너 vs 구분선) | 있음 | `components/dashboard/dashboard.css:64` `.dash-card` 컨테이너 보더 `var(--line, #e3e6ea)` · `:150` `.dash-device-note` 내부 구분선 `border-top: 1px solid var(--line, #e3e6ea)` · `:235` `.todo-grp + .todo-grp` 구분선도 동일 `var(--line, #e3e6ea)`. 컨테이너와 구분선이 같은 토큰(같은 폴백값)이라 층이 안 갈린다 | Ted 판정 |
| 4 ▲쌍 | L1 | 정적 | 어휘 불일치(ⓐ/ⓑ 밖 · 정의 없이 폴백만 있는 이질 어휘) | 있음 | `components/dashboard/dashboard.css` 가 `tokens.css`(§0 정본) 의 `--color-*`·`--text-*` 어휘를 전혀 쓰지 않고 `--fg`·`--bg-card`·`--fg-muted`·`--bg-subtle`·`--accent-neutral`·`--fg-danger`·`--line` 7종(총 20 참조)을 쓴다. 이 7종은 `tokens.css` 에도 `dashboard.css` 안에도 **정의된 곳이 없다** — 전부 인라인 폴백(`#1b1f24`·`#fff`·`#667`·`#eef1f4`·`#5b7089`·`#a3222b`·`#e3e6ea`)만으로 버틴다. ⓐ(컴포넌트 전용)도 ⓑ(파일 내 전역 어휘 복제)도 아닌 제3의 형태 — SKILL.md §2-2-9 의 이분류에 없는 사례라 판정 보류 후 Ted 상정 | Ted 판정 |
| 5 ▲쌍 | L2 | 정적 | preview.css 미정의 토큰 20건 | 있음 | 전부 폴백 있음 — `--line`(`:32`#e2e2e2·`:74`#eee·`:113`#e2e2e2·`:165`#d8d8d8·`:186`#e2e2e2·`:231`#e2e2e2·`:303`#e2e2e2, **파일 내부에서 3개 값 혼재**) · `--surface-2`(`:34`#f7f7f6·`:115`#f5f5f4·`:188`#f5f5f4·`:305`#f5f5f4, `:34`만 다름) · `--ink-1`(`:49`·`:51` #1f1f1f 일치) · `--ink-2`(`:20`#555·`:81`#666·`:101`#666·`:159`#666, `:20`만 다름) · `--ink-3`(`:172`#888) · `--accent`(`:206`#2f6feb) · `--surface-1`(`:233`#fff). 전부 `shell/tokens.css`·다른 컴포넌트 css 어디에도 정의되지 않은 순수 미정의 어휘 | Ted 판정 |
| 6 ▲쌍 | L3 | 정적 · 미정의 토큰 | `upload.css` 9건(폴백 있음) | 있음 | `:291` `--line` · `:293` `--surface-2` · `:296` `--muted` · `:301` `--muted` · `:332` `--line` · `:333` `--surface` · `:336` `--accent` · `:338` `--line` · `:341` `--muted` — `.gridblock`·`.thumbrow` 블록. `:root`(상단 6개·하단 12개) 어디에도 정의 없음 | Ted 판정 |
| 7 ▲쌍 | L3 | 정적 · 미정의 토큰 | `lineage.css` 9건(폴백 있음) | 있음 | `:13` `--muted` · `:20` `--line` · `:22` `--soft` · `:34` `--line` · `:57` `--line` · `:79` `--muted` · `:106` `--line` · `:163` `--line` · `:242` `--line` | Ted 판정 |
| 8 | L3 | 정적 · 미정의 토큰 | `lab.css:11` `--color-danger`(폴백 `#b42318`) | 있음 | 1건. `tokens.css` 에 `--color-danger` 없음 | Ted 판정 |
| 9 ●쌍 | L2 | 정적 | `.verified--pending` 대비 | 있음 | `catalog.css:140` `background: var(--color-gray-100)`(#e8ecf2) `color: var(--color-gray-500)`(#697077) → 직접 계산 **4.25:1**(스크립트 4.23:1) — AA 4.5 미달. WU-A11·B11·C11 어느 판정표에도 지목되지 않은 신규 발견 | Ted 판정 |
| 10 ●쌍 | L3 | 정적 · 대비(같은 규칙) | `project.css:528-530` `.verified--pending` `#697077 on #e8ecf2` | 있음 | 재계산 **4.234:1**(AA 4.5 미달) — css_audit 4.23:1 오탐 아님, 실측 일치. `catalog.css:138` 와 동일 조합(레인 밖 · 참고) | Ted 판정 |
| 11 | L2 | 정적 | `.dsec-menu-i.is-active` 대비 | 있음 | `detail.css:230-233` `background: var(--color-primary-50)`(#edf4ff) `color: var(--color-primary-600)`(#1369e9) → 직접 계산 **4.51:1**(스크립트 4.49:1) — 경계값, AA 4.5 기준 스크립트는 미달·직접 계산은 근소 통과. 판정표 어디에도 지목되지 않은 신규 발견 | Ted 판정 |
| 12 | L2 | 정적 | 글자 13px 미만 — catalog.css | 있음 | 14건 — `:46` th 10px(라벨) · `:71` 정렬표식 9px(장식) · `:89` 열메뉴 섹션표제 10px(캡션) · `:92` 열메뉴 항목 12px(메뉴텍스트) · `:98` 체크박스 표식 9px(장식) · `:102` 열메뉴 카운트 11px(캡션) · `:107` 열메뉴 지우기 11px(캡션) · `:117` 필터라벨 11px(캡션) · `:121` 필터칩 11px(뱃지) · `:125` 전체지우기 11px(캡션) · `:127`·`:130`·`:137`·`:141` 칩류(`.chip`·`.lvl`·`.verified`·`.lin`) 11px(뱃지). 전부 뱃지·캡션류로 이전 승격 대상(`.fl-k`·`.fl-x`·`.up-note` 등) 계열과 다르다 — 지목 이력 없음 | Ted 판정 |
| 13 | L2 | 정적 | 글자 13px 미만 — detail.css | 있음 | 9건 — `:63` `.chip` 11px(뱃지) · `:66` `.lvl` 11px(뱃지) · `:88` `.ig .k` 10px(테이블/격자 라벨, `:154`·`:167`·`:188`와 같은 셀렉터 계열) · `:112` `.ig-more` 11px(버튼) · `:141` `.use-dl-note` 12px(캡션, PRD-39 ⑩ 명시적으로 「버튼보다 작게」 의도) · `:154` `.dt-files-k` 10px(라벨, `:88`과 동일 패턴) · `:167` `.fl-gh` 10px(라벨, 동일 패턴) · `:188` `.de-k` 10px(폼 라벨, 동일 패턴) · `:190` `.de-req` 9px(뱃지). `.fl-k`(`:120`)·`.fl-x`(`:124`)는 WU-B11 이 13px 로 이미 승격되어 이번 9건에 없다 | Ted 판정 |
| 14 | L2 | 정적 | 글자 13px 미만 — search.css | 있음 | 2건 — `:52` `.notice--empty .muted` 11px(캡션, 부가 안내) · `:124` `.verified` 11px(뱃지, catalog/detail 의 `.verified`·`.chip`·`.lvl`·`.lin` 11px 뱃지 계열과 동일 패턴) | Ted 판정 |
| 15 | L2 | 정적 | 글자 13px 미만 — preview.css | 있음 | 2건 — `:286` `.pv-value` 12px(값 조회 패널 본문) · `:356` `.pv-pick-f > span` 12px(선택 라벨). 나머지 `.pv-legend`·`.pv-control`·`.pv-slot-note`·`.pv-muted`·`.pv-zoom`·`.pv-shot`·`.pv-hud`·`.pv-pick`(13px·12px 혼재)는 css_audit 이 세지 않은 13px 선언 다수를 포함 — 13px 정확값은 위반 아님, `.pv-hud`(`:284-289`)만 12px | Ted 판정 |
| 16 | L3 | 정적 · 글자크기 | `upload.css` 13px 미만 20건 | 있음 | `:108` `.muted` 12 · `:137` `.fs` 12 · `:138` `.fkind` 12 · `:153` `.cl` 12 · `:154` `.cw` 12 · `:159` `.vs-f` 12 · `:196` `.cnt` 12 · `:197` `.rs-f` 12 · `:213` `.form-row label` 12 · `:214` `.autotag` 10 · `:218` `.reqtag` 10 · `:228` `.fieldlbl` 12 · `:231` `.chip` 12 · `:239` `.projtable th` 11 · `:248` `.qnote` 11 · `:259` `.uf-hint` 12 · `:321` `.ub-btn` 12 · `:325` `.ub-hint` 12 · `:341` `.th-n` 12 · `:358` `.an-txt` 12 | Ted 판정 |
| 17 | L3 | 정적 · 글자크기 | `project.css` 13px 미만 14건 | 있음 | `:102` `.pj-count` 12 · `:142` `.pc-m` 12 · `:185` `.pc-s .k` 11 · `:203` `.pc-cta` 12 · `:266` `.pd-sect .quiet` 12 · `:292` `.chip` 11 · `:372` `.pj-row label` 12 · `:430` `.pj-hint,.pj-muted` 11 · `:440` `.pj-defnote` 12 · `:461` `.pj-fgroup-h .t` 12 · `:480` `.pj-tm` 11 · `:490` `.pj-keepbox` 12 · `:503` `.pj-err,.pd-notice` 12 · `:525` `.project-detail .verified` 11 | Ted 판정 |
| 18 | L3 | 정적 · 글자크기 | `lineage.css` 13px 미만 9건 | 있음 | `:54` `.conf` 12 · `:70` `.lin-ok` 12 · `:92` `.lin-f label` 12 · `:194` `.lin-lvfilter` 12 · `:199` `.lin-lv` 12 · `:218` `.lin-over-why` 12 · `:225` `.lin .chip` 12 · `:265` `.lin-unknown-why` 12 · `:287` `.lin-fix-method-l` 12 | Ted 판정 |
| 19 ■쌍 | L2 | 파일 내 토큰 ⓑ 전역 어휘 중복 | catalog.css 18건 · detail.css 30건 | 있음 | 중복 정의 12개 이름이 두 파일 모두에 있다 — `--color-gray-100`(#e8ecf2=#e8ecf2)·`--color-gray-600`(#565c63=#565c63)·`--color-gray-700`(#434950=#434950)·`--color-warning-50`(#fff6ed=#fff6ed)·`--color-warning-600`(#a85400=#a85400)·`--color-primary-50`(#edf4ff=#edf4ff)·`--color-primary-100`(#e2eeff=#e2eeff)·`--color-primary-200`(#bad7ff=#bad7ff)·`--color-primary-800`(#0b4eb6=#0b4eb6)·`--font-data`(var(--font-sans)=var(--font-sans))·`--radius-lg`(12px=12px)·`--radius-pill`(9999px=9999px). **12개 전부 값 일치** — 불일치 0건. `tokens.css` 에는 이 12개 이름이 없다(`grep` 확인) | Ted 판정 |
| 20 ■쌍 | L3 | ⓑ 파일 내 토큰(전역 어휘 중복) | `upload.css` 18건 | 있음 | `:6-11` 6건(`--up-*`, ⓐ 별건) 제외한 전역 어휘 12건 = `:369` `--color-border-control` `#848c94` · `:370` `--color-primary-50` `#edf4ff` · `:371` `--color-primary-100` `#e2eeff` · `:372` `--color-text-on-primary` · `:373` `--color-text-subtle` · `:374` `--color-danger-600` · `:375` `--font-data` · `:377` `--radius-lg` `12px` · `:378` `--shadow-lg`(축자) · `:379-380` `--space-1`/`--space-2`. `catalog.css`(:6-25)·`detail.css`(:5-33) 와 이름·값 **일치** | Ted 판정 |
| 21 ■쌍 | L3 | ⓑ 파일 내 토큰(전역 어휘 중복) | `project.css` 8건 | 있음 | `:10` `--color-gray-100` `#e8ecf2` · `:11` `--color-surface-alt` `#f4f7fb` · `:12` `--color-success-50` `#efffef` · `:14` `--color-success-100` `#cde9d6`(신규 값) · `:15` `--color-success-600` `#067506` · `:16` `--color-warning-600` `#a85400` · `:18` `--radius-pill` `9999px`. `catalog.css`·`detail.css` 와 `--color-gray-100`·`--color-success-50`·`--color-warning-600`·`--radius-pill` **값 일치**. `--color-success-100`(`#cde9d6`)은 `project.css` 단독 — 불일치 아니라 **미중복**(별건) | Ted 판정 |
| 22 | L2 | 정적 · 신규 발견(11항목 밖) | search.css 폴백 hex ↔ 실제 토큰값 불일치 | 있음 | search.css 는 자체 `:root` 없이 `var(--토큰, 폴백hex)` 만 쓴다. 폴백이 `shell/tokens.css` 실측값과 다른 자리 — `:15`·`:70` `--color-primary-600` 폴백 `#1f5eff` vs 실값 `#1369e9` · `:51` 같은 토큰 폴백 `#0f62fe`(파일 내부에서도 `:15`·`:70` 과 다름) · `:75` `--color-text` 폴백 `#1b1f24` vs 실값 `#121619` · `:125` `--color-success-50` 폴백 `#e6f4ea` vs `catalog.css:10` 정의값 `#efffef` · `:115`·`:116`·`:120`·`:125`·`:128` `--color-success-600` 폴백 `#1f8b4c` vs `catalog.css:11` 정의값 `#067506` · `:33` vs `:50` `--color-border` 폴백 `#dfe3e8` vs `#dde1e6`(파일 내부 불일치, 실값은 `#e8ecf2` 로 셋 다 다름). 로드 순서가 바뀌면 값이 갈린다 — css_audit 스크립트 축 밖의 위험 | Ted 판정 |
| 23 | L3 | 신규 · 컨테이너 소유 여백 | `upload.css` 단일 요소 margin-top 5건 (이월 목록 밖) | 있음 | `:348` `.up-body .partrow` 6px · `:357` `.up-analyze` 8px · `:384` `.fieldnote` 5px · `:388` `.axis-def .ad-more` `var(--space-1)` · `:424` `.dr-foot` 12px — 모두 단일 자리(형제 간 값 불일치 사례 아님) | Ted 판정 |
| 24 | L3 | 신규 · 컨테이너 소유 여백 | `lineageGraph.css` 단일 요소 margin-top 4건 | 있음 | `:87` `.lrow .ln-sub` 2px · `:101` `.lin-empty .muted` 10px · `:102` `.lin-empty button` 14px · `:103` `.lin-act` 12px — 단일 자리 | Ted 판정 |
| 25 | L3 | 신규 · 컨테이너 소유 여백 | `lineage.css` 단일 요소 margin-top 3건 | 있음 | `:133` `.lin-ask` 12px · `:240` `.lin-unknown` 14px · `:279` `.lin-fix-pick` 12px — 단일 자리 | Ted 판정 |
| 26 | L3 | 신규 · 음수 여백 | `project.css:436` `.pj-defnote { margin: -6px 0 14px }` | 있음 | 실측 확인(css_audit `neg margin` 1건과 일치). 부모 `.pj-modal-b`(:352)는 `padding` 만 갖고 gap 이 없다 — 형제 `.pj-row`(:365)는 `margin-bottom:14px` 소유. `.pj-defnote` 만 위쪽 음수로 앞 요소 간격을 깎는 자리 | Ted 판정 |
| 27 | L3 | 정적 · 카드 그림자 | `project.css:245` `.project-detail .card { box-shadow: var(--shadow-sm) }` | 있음 | 카드류(팝오버 아님) | 즉시 수정 후보 |
| 28 | L3 | 정적 · 카드 그림자 | `members.css:9` `.card { box-shadow: var(--shadow-sm) }` | 있음 | 카드류(팝오버 아님) | 즉시 수정 후보 |
| 29 | L3 | 정적 · 카드 그림자(분류 대기) | `members.css:112` `.modal { box-shadow: var(--shadow-sm) }` · `lab.css:39` `.labinfo-modal { box-shadow: 0 18px 48px rgba(...) }` | 있음 | 모달(오버레이)류 그림자 — 「팝오버 허용」의 팝오버에 모달이 포함되는지 정본에 명문 없음 | Ted 판정 |
| 30 | L1 | 정적 | 셸 상단바 그림자 | [미상 · 판정 보류] | `shell/shell.css:107` `.gnb { box-shadow: var(--shadow-sm) }` — `.gnb` 는 「카드」가 아니라 셸 고정바다. §0 정본의 카드 그림자 축이 셸 상단바에도 적용되는지 정본이 침묵 | Ted 판정 |
| 31 | L1 | 모션 | `:active` 피드백 유무 | [미상] | L1 6개 CSS 에 `:active` 셀렉터 0건(`grep` 실측). 코드상 판정 가능한 범위에서는 「없음」이나, 클릭 피드백이 브라우저 기본 동작으로 충분한지는 실화면 확인이 필요 | 실화면 계측 |
| 32 | L3 | 실화면 계측 | `PreviewPanel.tsx:507`·`:616` 인라인 `style={{ transform, transformOrigin }}` | [미상] | 확대·이동 배율의 동적 좌표 계산 — 정적 토큰·색 값이 아니라 판정 축 대상 아님. 실화면에서 줌 상호작용 확인 필요 시에만 계측 | 실화면 계측 |
| 33 | L3 | 죽은/덮인 선언 | 6종 전수 반복 셀렉터 상위 검사 | [미상 · 저신뢰] | 규칙 쌍별 전수 대조는 하지 않음(표본 검사만) — `.lin-way` 류 C11 이 이미 정리 | 실화면 계측 밖 · 후속 |
| 34 | L4 | 응답 | `:active` 규칙(누름 순간 피드백)이 없음 | 있음 | `frontend/src` 전체 `.css`·`.tsx` 에 `:active` 선택자 0건(전수 grep) · apple-design §1 「Respond on pointer-down, not on release」 | Ted 판정 |
| 35 | L4 | 응답 | 버튼·행·칩 피드백이 hover 전용 | 있음 | `catalog.css:56` `.tbl tr.clk td { transition: background var(--ease), box-shadow var(--ease); }` · `upload.css:418` `.dr-cal-d:hover{background:var(--color-primary-100);}` · `upload.css:406`·`434` 동형 · `shell.css:65`·`143`·`172`·`210`·`233`·`251`·`276` 전부 hover·포커스 색 전환 · apple-design §1 | Ted 판정 |
| 36 | L4 | 응답 | 배경 클릭 닫기를 `onMouseDown` ＋ `onClick` 두 단으로 확인 | 있음 | `UploadModal.tsx:869` `onMouseDown` 에서 `downOnBackdrop.current = e.target === e.currentTarget` · `:873` `onClick` 에서 두 조건 동시 확인 · `PreviewExpandOverlay.tsx:32`·`:36` 동형 | — |
| 37 | L4 | 중단 가능성 | 사용자 구동 상태 전환이 `transition`(중단 가능) | 있음 | `login.css:61`·`79` · `catalog.css:56`·`150` · `members.css:41` · `search.css:109`·`113` · `upload.css:405`·`417`·`432` · `shell.css:65`·`143`·`172`·`210`·`233`·`251`·`276` — 전부 `transition` · apple-design §3 | — |
| 38 | L4 | 중단 가능성 | 모달 열기가 고정 길이 `animation`/`@keyframes` | 있음 | `upload.css:31` `animation: up-rise 0.46s ease;` ＋ `:33` `@keyframes up-rise { from { transform: translateY(3%); opacity: 0.4; } to { transform: none; opacity: 1; } }` · apple-design §3 | Ted 판정 |
| 39 | L4 | 중단 가능성 | 고정 시작값에서 출발(현재값 아님) | 있음 | `upload.css:34` `from { transform: translateY(3%); opacity: 0.4; }` — 화면의 현재값이 아니라 고정 `3%`·`0.4` 에서 시작 · apple-design §3 | Ted 판정 |
| 40 | L4 | 중단 가능성 | 무한 반복 `animation`(제스처 대상 아님) | 있음 | `upload.css:165` `animation: up-spin 0.8s linear infinite;` ＋ `:167` `@keyframes up-spin { to { transform: rotate(360deg); } }` — 로딩 표시 | — |
| 41 | L4 | reduced-motion | `upload.css` 분기 | 있음 | `upload.css:37` `@media (prefers-reduced-motion: reduce) { .modal.modal-takeover { animation: none; } }` · `:168` `@media (prefers-reduced-motion: reduce) { .vizload .spin { animation: none; } }` — 움직이는 속성 = `transform`(translateY · rotate) ＋ `opacity` · apple-design §14 | — |
| 42 | L4 | reduced-motion | `search.css` 분기 | 없음(결함) | 모션 선언 2건 = `:109` `transition: background var(--ease);`(색) · `:113` `border-radius: 50%; background: #fff; transition: left var(--ease);` — **`left` 는 위치 이동**이라 색 전용이 아니다(토글 손잡이) · apple-design §14 | Ted 판정 |
| 43 | L4 | 타이포 | 크기와 무관한 고정 `letter-spacing` | 있음 | `login.css:27` `letter-spacing: 0.01em;` · `catalog.css:46` `font-size: 10px … letter-spacing: 0.05em` · `catalog.css:59` `font-size: 13px … letter-spacing: -0.01em` · `catalog.css:89` `font-size: 10px … letter-spacing: 0.04em` · `shell.css:92` `letter-spacing: var(--tracking-body)` = `tokens.css:34` `--tracking-body: 0.0096em`(크기 무관 단일 값) · apple-design §15 | Ted 판정 |
| 44 | L4 | 타이포 | 제목 tracking 이 음수(큰 글자를 조임) | 있음 | `catalog.css:30` `font-size: var(--text-h2, 24px) … letter-spacing: -0.023em` · `search.css:6` 동일 값 · `shell.css:116` `font-size: 17px; letter-spacing: -0.02em` · apple-design §15 부합 | — |
| 45 | L4 | 타이포 | 본문 `line-height` 지정 | 있음 | `shell.css:91` `line-height: var(--leading-body)` = `tokens.css:33` `--leading-body: 1.467` · `login.css:39`·`:94` `1.5` · `search.css:19` `1.6` · `:34` `1.7` · `:74`·`:77` `1.6` · `members.css:118` `1.7` · `upload.css:226` `1.5` · apple-design §15 | — |
| 46 | L4 | 공간 연속성 | 오버레이·팝오버가 호출한 자리에서 열림(`transform-origin` 앵커 ＋ 여는 전환) | 없음(결함) | `upload.css:397` `.dr-pop{position:absolute;top:calc(100% + 6px);left:0;z-index:60; …}` — 위치는 트리거 아래에 붙으나 전환 0건 · `frontend/src` 전체 `transform-origin` 선언 0건(히트 2건은 `PreviewPanels.tsx:156`·`161` 주석) · `upload.css:450`·`452` `.pvx-back`/`.pvx` 도 전환 0건 = 즉시 표시 · apple-design §7 | Ted 판정 |
| 47 | L4 | 공간 연속성 | 열기·닫기 경로 대칭 | 없음(결함) | `upload.css:31` 열기만 `up-rise`(위로 3% 상승) 정의 · 닫기 애니메이션 정의 0건 — 조건부 렌더 해제로 즉시 사라짐(`PreviewExpandOverlay.tsx:27` 이하 반환 트리) · apple-design §7 | Ted 판정 |
| 48 | L4 | 오버레이 해제 | Escape 처리(`data-esc-layer` 표식 ＋ 층별 자기 닫기) | 있음 | `escLayer.ts:12` `ESC_LAYER_ATTR = 'data-esc-layer'` · `:15`–`:26` `useEscLayer` 가 `document` keydown 에서 `Escape` 만 받아 자기 닫기 호출 · `PreviewExpandOverlay.tsx:26`·`:31` · `PeriodCalendarPopover.tsx:14` · `UploadModal.tsx:643`–`:649` | — |
| 49 | L4 | 오버레이 해제 | 배경 클릭 닫기 | 있음 | `UploadModal.tsx:869`–`:874` · `PreviewExpandOverlay.tsx:32`–`:38` — 둘 다 `e.target === e.currentTarget` ＋ 누른 자리 확인 | — |
| 50 | L4 | 직접 조작 | 드래그가 Pointer Events ＋ `setPointerCapture` 를 쓰지 않음 | 있음 | `useZoomPan.ts:228` `onMouseDown` · `:236`–`:250` `window` 의 `mousemove`/`mouseup` 로 추적 · `frontend/src` 전체 `onPointerDown`·`setPointerCapture` 0건 · apple-design §2 | Ted 판정 |
| 51 | L4 | 직접 조작 | 드래그 히스테리시스(약 10px 임계) 없음 | 있음 | `useZoomPan.ts:229`–`:231` `if (e.button !== undefined && e.button !== 0) return; drag.current = { x: e.clientX, y: e.clientY };` — 첫 이동부터 즉시 추적, 임계 0 · apple-design §10 | Ted 판정 |
| 52 | L4 | 직접 조작 | 파일 드롭 영역에 드래그 중 시각 피드백 없음 | 있음 | `FileDropCard.tsx:168`–`:171` `onDragOver` 가 `preventDefault`·`stopPropagation` 만 수행(상태 갱신 0) · `onDragEnter`/`onDragLeave` 0건 · `upload.css` 에 `.dropzone` 드래그 상태 규칙 0건 · apple-design §1 | Ted 판정 |
| 53 | L4 | 모션 | 1:1 드래그 추적 품질(오프셋 유지·프레임 지연) | [미상 · 실화면 계측 필요] | `useZoomPan.ts:236`–`:243` 는 델타 누적식이라 코드상 1:1 이나 실제 추적 지연은 정적으로 못 잰다 | 실화면 계측 |
| 54 | L4 | 모션 | 스프링 감쇠·응답 체감 | [미상 · 실화면 계측 필요] | 스프링 미사용(L4 #27)이라 측정 대상 자체가 없다 — 도입 후에만 계측 가능 | 실화면 계측 |
| 55 | L4 | 모션 | 경계 러버밴딩 | [미상 · 실화면 계측 필요] | `useZoomPan.ts:241` `clampView` 로 경계에서 값을 자름(점진 저항 코드 0) · 하드 스톱 체감은 실화면 필요 · apple-design §9 | 실화면 계측 |
| 56 | L4 | 모션 | 프레임 평활도(스트로빙·드롭 프레임) | [미상 · 실화면 계측 필요] | 이 레인 대상 파일에 `will-change` 0건(전체 1건 = `preview/preview.css:195`, 대상 밖) · 실측은 화면에서만 | 실화면 계측 |

**쌍 표식** — `●쌍` = 같은 결함(`.verified--pending` `#697077 on #e8ecf2` 4.23:1)이 두 파일에서 나온 쌍(#9 catalog.css · #10 project.css, 한 WU 로 동시 집행해야 재발 없음). `■쌍` = 전역 토큰 파일별 복제 묶음(#19 catalog·detail · #20 upload · #21 project, 같은 이름·같은 값이 4파일에 복제). `▲쌍` = 정의 없이 폴백만 있는 이질 어휘 묶음(#4 dashboard · #5 preview · #6 upload · #7 lineage).

**없음 행 요약(표에 다시 싣지 않음)** — L1 13건 · L2 10건 · L3 12건 · L4 8건(L4 의 결함성 없음 3건은 위 #42·#46·#47 로 실었다) = 43건. 각 레인 파일의 판정표에 근거가 그대로 있다.

---

## 3. 소계

### 레인별 (행 실측)

| 레인 | 있음 | 없음 | [미상] | 행 계 |
|---|---|---|---|---|
| L1 | 4 | 13 | 2 | 19 |
| L2 | 9 | 10 | 0 | 19 |
| L3 | 16 | 12 | 2 | 30 |
| L4 | 16 | 11 | 4 | 31 |
| **계** | **45** | **46** | **8** | **99** |

### 처리별 (§2 통합표 56행)

| 처리 | 건 | 어디 |
|---|---|---|
| 즉시 수정 후보 | 4 | #1(login-card 그림자) · #2(셸·공통 13px 미만 11건) · #27(project `.card` 그림자) · #28(members `.card` 그림자) |
| Ted 판정 | 37 | #3~#26 중 22건 · #29 · #30 · #34·#35·#38·#39·#42·#43·#46·#47·#50·#51·#52 |
| 실화면 계측 | 6 | #31 · #32 · #53 · #54 · #55 · #56 |
| 실화면 계측 밖 · 후속 | 1 | #33(죽은/덮인 선언 규칙 쌍 전수 대조) |
| —(결함 아님 · 장치 존재 확인) | 8 | #36·#37·#40·#41·#44·#45·#48·#49 |

---

## 4. 이월 재판정 (WU-C11 후 잔존)

WU-C11(`2c4d335`) 이 집행한 항목의 현재 값 — **7건 전부 잔존 없음**. 재개방하지 않는다.

| 이월 | 현재 판정 | 근거 |
|---|---|---|
| `.lvl-3` 4단째(Lv 칩) 부재 | 없음(해소) | `catalog.css:136` `.lvl-3 { background:#bad7ff; color:#0b4eb6 }` **4.83:1** · `detail.css:72` 동일 값 동일 통과 (L2 #1) |
| `.lin--none` 대비 3.41:1 | 없음(해소) | `catalog.css:146` `color: var(--color-gray-500)`(#697077) on 흰 배경 **5.04:1** (L2 #2) |
| `.dt-gridact` 음수 여백 | 없음(해소) | `detail.css:148` `margin` 선언 자체가 없다 — 여백은 `.dt-split-r` gap(`:283`·`:294`) 소유 (L2 #3) |
| `lineageGraph.css:7` `.dsec` 자식 margin-top 34px | 없음(해소) | `detail.css` `.dt-secs` gap 34px 로 이관 · 대상 셀렉터 `margin-top` 잔존 0건 (L3 #5) |
| `upload.css` 자식 margin-top 9곳 | 없음(해소) | `.up-card > .card-b { gap:12px }`(:125) · `.projpick` gap 8(:245) · `.qproj` gap 8(:246) 로 컨테이너 이관 · 9개 셀렉터 블록 `margin-top` 0건 (L3 #6) |
| 상단 메뉴 활성 탭 파랑 밑줄 | 없음 | `shell/shell.css:184-192` `.mainnav a.is-active::after` 3px `--color-primary-600` (L1 #4) |
| 상단 버튼 알약→둥근 사각 | 없음 | `shell/shell.css:135·167·204·225·245` 전부 `--radius-sm`/`--radius-md` · `--radius-pill`·`9999px` 사용 0건 (L1 #5) |

### 이월 목록 밖 신규 발견 (이번 회차 최초 지목)

- 대비 — `.verified--pending` 4.23:1 두 파일(#9·#10) · `.dsec-menu-i.is-active` 4.51:1 경계(#11).
- 글자 13px 미만 — 신규 지목 계 **70건**(catalog 14 · detail 9 · search 2 · preview 2 · upload 20 · project 14 · lineage 9), 셸·공통 11건(#2)은 별건.
- 정의 없이 폴백만 있는 이질 어휘 — **39건**(dashboard 20 참조 · preview 20 · upload 9 · lineage 9 · lab 1 중 중복 계상 제외한 파일별 실측치는 §2 각 행 참조).
- 전역 토큰 파일별 복제 — catalog 18 · detail 30 · upload 18 · project 8.
- 여백 — 단일 요소 margin-top 12건(#23·#24·#25) · `project.css:436` 음수 여백 1건(#26).
- 그림자 — 카드 3건(#1·#27·#28) · 모달 2건(#29) · 셸 상단바 1건(#30).
- 인터랙션·모션 — `:active` 전수 0건 · 모달 열기 고정 애니메이션 · 닫기 경로 비대칭 · 팝오버 앵커 없음 · 마우스 이벤트 드래그 · 드롭 피드백 없음 · 고정 letter-spacing.

---

## 5. css_audit 오탐

- **L1** — `components/common/variableTable.css` 「undefined token」 2건(`--line`)과 `components/dashboard/dashboard.css` 「undefined token」 20건은 전부 폴백을 갖는다. 스크립트가 「미정의」로 표기했으나 정본의 「폴백 없음 → 선언 무효화」 기준으로는 무효 선언이 아니다 — 렌더 값이 존재한다. 「선언 무효화」 의미로는 오탐, 「전역 어휘와 다른 값으로 살아있다」는 사실은 유효(→ §2 #4 로 승격).
- **L2** — 0건. 스크립트 수치(catalog 14 · detail 9 · search 2 · preview 2 <13px, preview 20 미정의 토큰, catalog 18 · detail 30 로컬 토큰, 대비 2건)가 실물 규칙과 전부 일치.
- **L3** — 0건. `.verified--pending` `4.23:1` 재계산 `4.234:1` 일치.
- **L4** — 0건. `motion decl` 열 6파일 값(login 2 · catalog 2 · members 1 · search 2 · upload 7 · shell 7)과 `reduced-motion` 열(`upload.css` 만 yes) 전수 대조 일치.
- **스크립트 개선 후보** — `var(--x, fallback)` 를 「미정의(undefined)」로 세지 말고 별도 「폴백 있음」 열로 분리한다. 현재 열 이름이 무효 선언처럼 읽혀 L1 22건이 오탐으로 잡혔다.

---

## 6. Ted 판정 묶음

각 항목 = 무엇이 문제인가 · ⓐ/ⓑ · 권고 1개와 이유 · 걸린 §2 행 번호.

### 접근성 — 대비·글자 크기

**판정-1 · 인증 대기 뱃지의 글자·배경 대비가 기준에 못 미친다**
- 문제 — 데이터 목록과 프로젝트 화면의 「인증 대기」 뱃지가 회색 글자에 회색 배경이라 4.23~4.25:1 로, 접근성 기준선 4.5:1 아래다. 같은 색 조합이 두 파일에 각각 적혀 있다.
- ⓐ 글자색을 같은 회색 계열에서 한 단 진하게 내린다. ⓑ 배경을 한 단 연하게 올린다.
- 권고 = ⓐ. 앞 회차가 「계보 없음」 표시를 같은 방식(회색 한 단 진하게)으로 통과시킨 선례가 있고, 배경을 건드리면 같은 배경을 쓰는 다른 뱃지까지 값이 갈린다. 두 파일을 한 번에 고쳐야 재발이 없다.
- 걸린 행 — #9 · #10.

**판정-2 · 상세 화면 구역 메뉴의 선택 상태 대비가 경계값이다**
- 문제 — 데이터 상세 화면 왼쪽 구역 메뉴에서 지금 보고 있는 항목의 파란 글자·연파랑 배경이 4.51:1 이다. 계측 스크립트는 4.49:1 로 미달, 직접 계산은 4.51:1 로 근소 통과라 판정이 갈린다.
- ⓐ 통과로 보고 손대지 않는다. ⓑ 파란 글자를 한 단 진하게 내려 여유를 만든다.
- 권고 = ⓑ. 반올림 자리에서 결론이 뒤집히는 값이라, 브라우저 렌더 결과를 다시 재는 비용보다 한 단 내리는 편이 싸다. 실제 화면 캡처 재계측을 병행한다.
- 걸린 행 — #11.

**판정-3 · 뱃지·캡션류 글자가 11px 안팎으로 기준선 13px 아래에 있다**
- 문제 — 등급 칩·인증 뱃지·필터 칩·표 머리글·설명 문구 등 짧은 라벨이 9~12px 이다. 기준선 13px 를 그대로 적용하면 목업이 처음부터 11px 로 설계한 뱃지 전체가 대상이 된다.
- ⓐ 뱃지·캡션류를 기준선의 예외로 등재하고 값을 유지한다. ⓑ 뱃지류에 별도 문턱(예: 11px)을 세워 그 아래만 올린다.
- 권고 = ⓑ. 목업의 뱃지 다수가 11px 로 일관돼 있어 별도 문턱이 실태에 맞고, 예외 등재는 「어디까지 뱃지인가」를 매번 다시 다투게 만든다. 10px 라벨(격자 라벨·파일 라벨·폼 라벨)과 9px 장식 표식(정렬 표식·체크 표식)은 별도 판단이 필요하다.
- 걸린 행 — #12 · #13 · #14 · #15 · #16 · #17 · #18.

**판정-4 · 글자 크기 승격을 한 회차에 몰아서 할지, 유형별로 쪼갤지**
- 문제 — 판정-3 이 정해지면 대상이 최대 81건(화면별 70건 ＋ 셸·공통 11건)이다. 고정 높이를 가진 뱃지·표 머리글은 글자를 올리면 높이도 같이 올려야 해서 배치가 밀린다.
- ⓐ 유형별(뱃지 · 캡션 · 폼 라벨 · 표 머리글)로 쪼개 순차 집행한다. ⓑ 이번 회차에 전량 승격한다.
- 권고 = ⓐ. 고정 높이 요소가 여럿이라 전량 승격 시 배치 파급이 크고, 앞 두 회차가 이미 지목분 순차 승격 방식으로 돌아갔다.
- 걸린 행 — #2 · #12 · #13 · #14 · #15 · #16 · #17 · #18.

### 토큰 어휘 — 전역 승격 · 화면별 어휘계

**판정-5 · 색·모서리·간격 이름 12개가 화면별 파일마다 같은 값으로 복제돼 있다**
- 문제 — 데이터 목록·상세·업로드·프로젝트 네 화면 파일이 각자 파일 머리에서 같은 이름·같은 값의 색·모서리·글꼴·그림자 변수를 다시 정의한다. 값은 현재 100% 일치하지만 한쪽만 고쳐지면 화면끼리 색이 갈린다.
- ⓐ 공통 토큰 파일(`shell/tokens.css`)로 승격하고 화면 파일의 중복 정의를 지운다. ⓑ 화면별 복제를 유지한다(공유 파일 접촉 최소화 관례).
- 권고 = ⓐ. 값이 이미 전부 일치해 승격 비용이 0 이고, 복제 유지는 정본이 이미 경계한 「한쪽만 고쳐지는 사고」를 그대로 남긴다. `--color-success-100`(`#cde9d6`)처럼 한 파일에만 있는 것은 복제가 아니므로 이번 승격 대상에서 뺀다.
- 걸린 행 — #19 · #20 · #21.

**판정-6 · 미리보기 화면이 다른 화면과 다른 색 이름 체계를 쓴다**
- 문제 — 미리보기 화면은 어디에도 정의되지 않은 `--line`·`--surface-1/2`·`--ink-1/2/3`·`--accent` 를 20자리에서 쓰고, 폴백 값만으로 화면이 그려진다. 같은 이름의 폴백 값이 파일 안에서도 3종(`#e2e2e2`·`#eee`·`#d8d8d8`)으로 갈린다.
- ⓐ 공통 토큰 파일의 정본 이름(테두리·표면·본문색·강조색)으로 치환한다. ⓑ 미리보기 전용 접두사(`--pv-*`)로 새 어휘계를 세운다.
- 권고 = ⓐ. 나머지 세 화면이 이미 정본 이름을 쓰고 있어 미리보기만 다른 체계인 것 자체가 불일치이며, 치환하면 폴백 값 갈림이 자동으로 해소된다.
- 걸린 행 — #5.

**판정-7 · 대시보드가 공통 토큰을 전혀 쓰지 않고 자체 이름 7종으로 버틴다**
- 문제 — 대시보드는 본문색·카드 배경·흐린 글자·연한 배경·중립 강조·위험색·구분선을 뜻하는 이름 7종을 20자리에서 쓰는데, 이 이름들은 공통 토큰 파일에도 대시보드 파일 안에도 정의가 없다. 값은 폴백 리터럴에만 있다.
- ⓐ 7종을 공통 토큰 파일에 새 전역 이름으로 승격한다. ⓑ 대시보드 코드를 기존 공통 이름으로 치환하고 새 이름을 만들지 않는다.
- 권고 = ⓑ. 흐린 글자·위험색은 이미 기존 공통 이름과 개념이 겹쳐 새 이름을 늘리면 두 어휘가 공존한다. 다만 중립 강조(`#5b7089`)처럼 대응하는 기존 이름이 없는 것은 승격이 필요해, 값 하나하나 확인해 갈린다.
- 걸린 행 — #4 · #3.

**판정-8 · 업로드·계보·랩 화면의 정의 없는 이름 19건을 어떻게 닫을지**
- 문제 — 업로드 9자리·계보 9자리·랩 1자리가 정의 없는 이름(구분선·흐린 글자·표면·강조·위험색)을 폴백만으로 쓴다.
- ⓐ 폴백 값을 공통 토큰 파일의 전역 이름으로 승격한다. ⓑ 화면 전용 접두사로 재명명한다.
- 권고 = ⓐ 중 업로드·계보가 함께 쓰는 구분선·흐린 글자·표면·강조만 우선 승격. 랩의 위험색 1건은 사용처가 하나뿐이라 확산 전까지 보류한다.
- 걸린 행 — #6 · #7 · #8.

**판정-9 · 검색 화면의 폴백 색값이 실제 토큰 값과 다르다**
- 문제 — 검색 화면은 자체 정의 없이 「이름, 못 찾으면 이 색」 형태로만 쓰는데, 그 「못 찾으면」 색이 실제 토큰 값과 6자리에서 다르고 같은 이름의 폴백이 파일 안에서도 갈린다(파랑 3종·테두리 2종). 지금은 다른 파일이 정의를 채워 주어 화면에 드러나지 않지만, 로드 순서가 바뀌면 값이 갈린다.
- ⓐ 폴백 색을 실제 토큰 값으로 정정한다. ⓑ 필요한 이름을 검색 화면 파일에 직접 정의한다.
- 권고 = ⓐ. 폴백은 안전망이지 값의 정본이 아니며, 최소 변경으로 갈림이 사라진다.
- 걸린 행 — #22.

### 그림자·보더·여백

**판정-10 · 카드 그림자를 어디까지 지울지**
- 문제 — 정본은 카드에 그림자 0(팝오버만 허용)을 요구하는데, 로그인 카드·프로젝트 상세 카드·멤버 카드 3자리에 그림자가 남아 있다.
- ⓐ 세 자리 모두 제거하고 테두리로만 경계를 남긴다. ⓑ 로그인 카드는 화면에 단독으로 놓이는 예외로 인정해 유지한다.
- 권고 = ⓐ. 정본 문구에 「단독 배치」 예외가 없고 세 자리 전부 클래스 이름부터 카드다. 제거 후 테두리만으로 경계가 보이는지 실물 확인이 필요하다.
- 걸린 행 — #1 · #27 · #28.

**판정-11 · 셸 상단바 그림자가 카드 그림자 규칙의 대상인지**
- 문제 — 화면 위쪽에 항상 고정된 상단바에 그림자가 있다. 상단바는 카드가 아니라 셸 고정 요소인데, 정본이 이 경우를 말하지 않는다.
- ⓐ 카드 규칙을 상단바까지 넓혀 제거한다. ⓑ 카드가 아니므로 규칙 대상에서 빼고 유지한다.
- 권고 = ⓑ. 정본이 카드류를 특정했고, 상단바는 목업에서부터 그림자를 가진 「항상 떠 있는 층」이라 팝오버·메뉴와 성격이 같다.
- 걸린 행 — #30.

**판정-12 · 모달 그림자가 「팝오버 허용」에 포함되는지**
- 문제 — 멤버 화면 모달과 랩 정보 모달에 그림자가 있다. 정본은 팝오버를 허용한다고만 적었고 모달을 포함하는지 명문이 없다.
- ⓐ 모달·오버레이를 팝오버 허용 범주에 포함하도록 정본을 보완한다. ⓑ 모달을 별도 축으로 분리해 자체 합격선을 정한다.
- 권고 = ⓐ. 이미 그림자를 가진 날짜 팝오버와 같은 「배경에서 떼어 놓기」 목적이라, 면 위에 얹히는 카드와 성격이 다르다.
- 걸린 행 — #29.

**판정-13 · 대시보드의 바깥 테두리와 안쪽 구분선이 같은 색이다**
- 문제 — 대시보드 카드의 바깥 테두리와 카드 안 구분선이 같은 이름·같은 값을 쓴다. 정본은 이 둘을 두 층으로 갈라 쓰라고 정한다.
- ⓐ 현행 단일 색을 유지한다(셸의 테두리 색과 이미 값이 달라 화면 고유 결이 있다고 볼 여지). ⓑ 공통 토큰 파일의 두 층 체계(일반 테두리 · 진한 테두리)로 갈아 끼워 셸과 통일한다.
- 권고 = ⓑ. 정본이 두 층 분리를 명시 축으로 못박았고, 판정-7 의 어휘 치환과 함께 처리하면 같은 파일을 두 번 열지 않는다.
- 걸린 행 — #3.

**판정-14 · 자식 요소가 자기 위쪽 간격을 스스로 갖는 자리 12곳을 컨테이너로 옮길지**
- 문제 — 업로드 5곳·계보 그래프 4곳·계보 3곳에서 자식 요소가 위쪽 간격을 직접 갖는다. 정본 원칙은 간격을 컨테이너가 소유하라고 정하는데, 이 12곳은 형제가 조건부로 나타나는 자리가 아니라 단일 자리다.
- ⓐ 원칙을 반복되는 조건부 형제에만 적용하고 단일 자리는 손대지 않는다. ⓑ 예외 없이 전량 컨테이너 간격으로 옮긴다.
- 권고 = ⓐ. 단일 자리는 형제 간 값이 갈릴 위험이 없어, 원 판정이 겨눈 문제를 재현하지 않는다.
- 걸린 행 — #23 · #24 · #25.

**판정-15 · 프로젝트 모달의 음수 여백 1자리**
- 문제 — 프로젝트 모달의 기본값 안내 문구가 위쪽 음수 여백으로 앞 요소와의 간격을 깎는다. 부모에 간격 소유가 없고 형제들은 각자 아래쪽 여백을 갖는 구조다.
- ⓐ 부모가 간격을 소유하도록 바꾸고 음수를 없앤다(앞 회차가 상세 화면에서 쓴 방식). ⓑ 단일 자리이므로 시각 등가만 확인하고 둔다.
- 권고 = ⓐ. 다만 형제 전체의 여백 소유 구조를 함께 바꿔야 해서 별도 작업 단위가 필요하다.
- 걸린 행 — #26.

### 인터랙션·모션

**판정-16 · 누르는 순간의 시각 피드백이 화면 전체에 하나도 없다**
- 문제 — 버튼·표 행·칩 어디에도 「누르고 있는 동안」의 상태 규칙이 없고, 피드백이 전부 마우스를 올렸을 때에만 걸린다. 정본은 손을 뗄 때가 아니라 누르는 순간에 반응하라고 정한다.
- ⓐ 버튼·행·칩에 누름 상태 규칙을 새로 세운다. ⓑ 현행 유지.
- 권고 = ⓐ. 다만 어떤 선택자 묶음에 걸지, 값이 배경 한 단 어둡게인지 살짝 축소인지는 정본에 없어 값 판정이 함께 필요하다.
- 걸린 행 — #31 · #34 · #35.

**판정-17 · 모션 축소 설정 대응을 화면마다 달지, 셸에 한 벌 둘지**
- 문제 — 사용자가 운영체제에서 모션 축소를 켰을 때의 분기가 업로드 화면에만 있다. 다른 파일의 전환은 대부분 색 전환이라 정본이 유지하라고 한 종류지만, 검색 화면의 토글 손잡이 하나가 위치를 움직이는 전환이라 분기 대상이다.
- ⓐ 셸에 전역 규칙 한 벌을 세워 이동·변형 전환을 일괄로 끈다. ⓑ 이동을 쓰는 파일마다 분기를 따로 단다.
- 권고 = ⓑ. 대상이 토글 손잡이 한 건뿐이고, 전역 규칙은 유지해야 할 색 전환까지 함께 끈다. 이동·변형 전환이 늘어난 뒤 재검토한다.
- 걸린 행 — #42.

**판정-18 · 모달 열기 애니메이션이 중간에 멈출 수 없고 닫기 경로가 없다**
- 문제 — 업로드 모달이 0.46초 고정 길이 애니메이션으로 열리고, 화면의 현재 값이 아니라 고정 시작값에서 출발한다. 닫기 애니메이션은 정의가 없어 즉시 사라진다.
- ⓐ 열기를 중단 가능한 전환으로 바꾸고 닫기 경로를 대칭으로 세운다. ⓑ 현행 고정 애니메이션을 유지한다.
- 권고 = ⓑ 중 열기 부분만. 정본이 금지하는 대상은 손가락으로 잡히는 것이고 이 모달은 드래그로 잡히지 않는다. 다만 열기·닫기 대칭은 어긋나 있으므로 닫기 경로 추가는 별도로 판정한다.
- 걸린 행 — #38 · #39 · #47.

**판정-19 · 팝오버·오버레이가 눌린 자리에서 열리지 않는다**
- 문제 — 기간 선택 달력 팝오버와 확장보기 오버레이가 전환 없이 즉시 나타난다. 나오는 기준점을 지정하는 선언이 화면 전체에 하나도 없다.
- ⓐ 두 곳에 기준점과 여는 전환을 세운다. ⓑ 현행 즉시 표시를 유지한다.
- 권고 = ⓐ 중 달력 팝오버만. 팝오버는 이미 누르는 버튼 바로 아래에 붙어 기준점이 자명하지만, 전체화면 오버레이는 나오는 자리가 정본에 없다.
- 걸린 행 — #46.

**판정-20 · 확대·이동 드래그가 마우스 전용이고 시작 임계가 없다**
- 문제 — 미리보기 확대·이동 드래그가 마우스 이벤트와 창 전역 감시로 구현돼 터치·펜 입력을 받지 않고, 손가락이 1px 만 움직여도 즉시 끌기가 시작된다.
- ⓐ 포인터 이벤트와 포인터 캡처로 옮기고 약 10px 시작 임계를 둔다. ⓑ 현행을 유지한다.
- 권고 = ⓐ. 현행 창 전역 감시가 「요소 밖으로 나가도 추적」 효과는 내지만 터치·펜을 못 받는다. 임계값은 정본에 「약 10px」로만 있어 확정값 판정이 필요하다.
- 걸린 행 — #50 · #51.

**판정-21 · 파일을 끌어 오는 동안 드롭 영역이 아무 반응을 하지 않는다**
- 문제 — 파일 끌어 놓기 영역이 끌어 오는 동안 상태를 갱신하지 않고, 대응하는 시각 규칙도 없다. 사용자는 여기에 놓아도 되는지 알 수 없다.
- ⓐ 끌어 들어옴·나감 상태와 대응 시각 규칙을 세운다. ⓑ 현행 유지.
- 권고 = ⓐ. 정본은 상호작용 도중 피드백이 끊기지 않아야 한다고 정한다. 상태 색은 정본에 없어 값 선택이 함께 필요하다.
- 걸린 행 — #52.

**판정-22 · 글자 간격 값이 글자 크기와 무관하게 하나로 고정돼 있다**
- 문제 — 본문 글자 간격이 크기와 상관없이 단일 값이고, 10px 라벨과 13px 본문이 서로 다른 고정값을 각자 파일에 박고 있다. 정본은 글자 간격이 크기별이어야 한다고 정한다.
- ⓐ 크기 구간별 값을 세워 공통 토큰 파일에 올린다. ⓑ 현행 파일별 고정값을 유지한다.
- 권고 = ⓐ. 구간 경계와 각 값은 정본에 없어 판정이 필요하다.
- 걸린 행 — #43.

**판정-23 · 제스처가 끝난 뒤 속도를 이어받는 움직임을 도입할지**
- 문제 — 모든 전환이 0.14초 고정 곡선 하나를 쓰고, 확대·이동 드래그는 속도를 기록하지 않아 손을 뗀 순간 즉시 멈춘다.
- ⓐ 탄성 움직임 라이브러리를 들여 제스처 종료 시 속도를 넘긴다. ⓑ 현행 고정 곡선을 유지한다.
- 권고 = ⓑ. 이 화면들의 모션은 대부분 색 전환이고 제스처가 끝나는 자리는 확대·이동 하나뿐이다. 의존성 추가 대비 적용 면이 좁다. 판정-20 처리 뒤 재검토한다.
- 걸린 행 — #53 · #54 · #55(측정 대상 부재의 근거).

---

## 7. 후보 WU 목록 (R-C 후속 라운드 입력 · 제안)

- WU 번호를 발급하지 않는다 — `work-items.yaml` 최신 항목은 WU-C11/C12/C13 이고 이 문서는 원장을 건드리지 않는다. 아래는 **후보 D-n**(제안)이다.
- 전건 계약 0 · 스키마 0 · 마이그레이션 0 · 서버 0.
- 시험 seam 선례 = `frontend/test/design-fix-20260908.test.ts`(before→after grep 계측 유형) · `frontend/test/css-residual-rc11.test.ts`(잔여 회귀 유형).

### CSS 전용 레인

| 후보 | 범위(파일 · 선택자 family) | 걸린 판정 | 크기 | 시험 seam |
|---|---|---|---|---|
| D-1 | `auth/login.css`(`.login-card`) · `catalog.css`(`.verified--pending`) · `detail.css`(`.dsec-menu-i.is-active`) · `project.css`(`.project-detail .card`·`.verified--pending`) · `members.css`(`.card`) — 색값·`box-shadow` 선언만 | 판정-1 · 2 · 10 | S | `design-fix-<날짜>.test.ts` — 대비 3쌍 계산 단언 ＋ 카드 `box-shadow` 0건 grep |
| D-2 | `shell/tokens.css` ＋ `catalog.css`·`detail.css`·`upload.css`·`project.css` 의 `:root{}` 블록만(선택자 규칙 무접촉) — 전역 어휘 12종 승격·중복 정의 제거 | 판정-5 | M | `css-residual-<라운드>.test.ts` — 화면 파일 `:root` 안 전역 이름 재정의 0건 ＋ 승격 후 값 동일성 |
| D-3 | `preview/preview.css` 전 규칙 ＋ `search/search.css` 폴백 hex — 이질 어휘 치환·폴백 정정 | 판정-6 · 9 | M | `design-fix` — 미정의 이름 참조 0건 ＋ 폴백 hex ↔ tokens 값 일치 grep |
| D-4 | `components/dashboard/dashboard.css` 전 규칙 — 어휘 7종 치환 ＋ 테두리 2층 분리 ＋ 12px 이하 9건 | 판정-7 · 13 · 4 | M | `design-fix` — 미정의 이름 0건 ＋ 컨테이너/구분선 서로 다른 이름 ＋ `font-size` 13px 미만 0건 |
| D-5 | `catalog.css`·`detail.css`·`search.css`(뱃지·캡션 family: `.chip`·`.lvl`·`.verified`·`.lin`·`.fl-*`) — 문턱 판정 결과에 따른 승격 | 판정-3 · 4 | M | `design-fix` — 확정 문턱 미만 선언 0건 ＋ 고정 높이 동반 조정 단언 |
| D-6 | `upload.css`·`project.css`·`lineage.css` 글자 크기 43건 — 유형별 승격 | 판정-3 · 4 | M | `design-fix` — 파일별 미만 건수 before/after 단언 |
| D-7 | `upload.css`·`lineage.css`·`lab.css` 미정의 이름 19건 ＋ `shell/tokens.css` 승격분 | 판정-8 | S | `css-residual` — 미정의 이름 참조 0건 |
| D-8 | `project.css`(`.pj-defnote`·`.pj-modal-b`·`.pj-row`) 음수 여백 제거·간격 소유 이전 | 판정-15 | S | `design-fix` — 음수 `margin` 0건 ＋ 형제 간격 시각 등가 값 단언 |
| D-9 | `shell/shell.css`(`.backlink .bl-a`) · `components/common/toast.css`(`.toast`) 글자 크기 2건 | 판정-4 | S | `design-fix` — 두 선택자 `font-size` 단언 |
| D-10 | 누름 상태 규칙 신설 — `shell/shell.css`·`catalog.css`·`upload.css` 의 버튼·행·칩 공통 선택자 묶음 | 판정-16 | M | `design-fix` — `:active` 규칙 건수 0 → n 단언 |
| D-11 | `search/search.css` 토글 손잡이 모션 축소 분기 신설 | 판정-17 | S | `design-fix` — `prefers-reduced-motion` 블록 존재 ＋ `transition: left` 무력화 단언 |
| D-12 | `upload.css`(`.dr-pop` 기준점·여는 전환 · 모달 닫기 경로) | 판정-18(닫기 대칭) · 19 | S | `design-fix` — `transform-origin` 선언 존재 ＋ 닫기 전환 규칙 존재 |
| D-13 | `shell/tokens.css` 글자 간격 구간 토큰 신설 ＋ `login.css`·`catalog.css`·`shell.css` 고정값 치환 | 판정-22 | M | `design-fix` — 파일 안 고정 `letter-spacing` 리터럴 0건 |

### TSX 접촉 레인

| 후보 | 범위(파일 · 선택자 family) | 걸린 판정 | 크기 | 시험 seam |
|---|---|---|---|---|
| D-14 | `components/preview/useZoomPan.ts` — 포인터 이벤트·포인터 캡처 전환 ＋ 시작 임계 | 판정-20 | M | `design-fix` — `onPointerDown`·`setPointerCapture` 존재 ＋ 임계 상수 단언(단위 시험) |
| D-15 | `components/upload/FileDropCard.tsx` 상태 ＋ `upload.css` `.dropzone` 드래그 상태 규칙 | 판정-21 | S | `design-fix` — `onDragEnter`/`onDragLeave` 존재 ＋ 대응 CSS 규칙 존재 |

- 파일 면 분리 — D-1(규칙 본문) 과 D-2(`:root` 블록) 는 같은 파일을 열지만 서로 다른 구역이다. **D-1 → D-2 순서 직렬**로 돌린다. 나머지 후보는 파일 면이 겹치지 않는다(D-15 의 `upload.css` `.dropzone` 규칙은 D-6·D-7 이 만지는 선택자와 별개).
- D-5·D-6 은 판정-3(문턱) 확정 전에는 착수하지 않는다. D-10·D-12·D-13 은 값 판정(누름 상태 값 · 전환 곡선 · 구간 경계) 확정 전에는 착수하지 않는다.

---

## 8. 이번에 세지 않은 축

- 재질·깊이의 품질 — 정적 합격선이 정본에 없어 열거만 했다. `backdrop-filter` 는 `frontend/src` 전체 0건이고 반투명 크롬은 스크림 2건(`upload.css:20`·`:450`)뿐이다.
- 다중 감각 피드백(소리·햅틱) — 구현 0건이고 정본에 요구가 없다.
- 투명도 축소·고대비 사용자 설정 분기 — 대상이 될 반투명 요소 자체가 없다.
- 죽은/덮인 선언의 규칙 쌍 전수 대조 — 반복 셀렉터 상위 스캔·표본 검사만 했다(§2 #33). 표본에서 발견 0건.
- `.tsx` 마크업 구조(클래스 부여 누락 등) — 이번 회차는 CSS 와 인라인 `style=` 만 봤다.
- 대상 파일 밖 모션 — `components/preview/preview.css:195` `will-change: transform` 등.
- L1·L2·L3 레인의 apple-design 심화 축(스프링 느낌·속도 계승·재질·깊이) — L4 소관으로 넘겼다.

### 실화면 계측 4건 (L4 · 무엇으로 재는가)

| # | 항목 | 계측 방법 |
|---|---|---|
| 53 | 1:1 드래그 추적 품질(오프셋 유지·프레임 지연) | 확대된 미리보기를 일정 속도로 끌며 포인터 좌표와 이미지 변위를 프레임별로 기록해 차이를 잰다(개발도구 Performance 의 입력 이벤트 ↔ 페인트 타임라인) |
| 54 | 탄성 감쇠·응답 체감 | 탄성 움직임 도입 후 열기·닫기 변위 곡선을 녹화해 오버슈트 비율과 정착 시간을 잰다 |
| 55 | 경계 저항(러버밴딩) | 경계 밖으로 끌었을 때 변위 ÷ 포인터 이동 비율이 거리에 따라 줄어드는지 기록한다 |
| 56 | 프레임 평활도(스트로빙·드롭 프레임) | 모션 구간을 60fps 로 녹화해 프레임당 위치 변화량과 드롭 프레임 수를 센다 |

- 계측은 배포 창 뒤의 일이다 — 이번 회차는 staging·dev 에 접촉하지 않았다.

---

## 9. PLAN-SoT §9 등재문 초안 (병합 직전 〈N〉 재실측 — `origin/main` 최대 ＋ 1)

```
| 〈N〉 | **R-C 후속 실측 — 디자인 검수 4레인 99행 판정. 판정 없이 고치지 않는다** | **실측 (2026-09-08 · 워크트리 `design-skills` · 기준 트리 `cc05c44` · 병합 `<sha>` · 계약 0 · 마이그레이션 0 · staging 접촉 0).** ①회차 = **해당 없음**(계약 미개방) ②값 = 없음 ③근거 = `dev-package/sessions/design-review-20260908.md` · 레인 산출 `-L1`~`-L4` · 계측 `dev-package/reports/design-review/20260908/css_audit.md` ④가·파 판정 = 해당 없음 ⑤소비자 = 해당 없음 ⑥마이그레이션 = **0건** ⑦승인 = 불요 ⑧이번에 세지 않은 축 = 재질·깊이 품질 · 다중 감각 피드백 · 죽은 선언 규칙 쌍 전수 대조 · 실화면 계측 4건(배포 창 뒤) `[미집행]`. **판정 결과** — 있음 **45** · 없음 **46** · `[미상]` **8**(계 99행) · 처리 = 즉시 수정 후보 4 · Ted 판정 37 · 실화면 계측 6 · 후속 1 · Ted 판정 묶음 **23건**(접근성 4 · 토큰 어휘 5 · 그림자·보더·여백 6 · 인터랙션·모션 8) · 후보 WU **15건**(CSS 13 · TSX 2) · WU-C11 이월 7건 **전부 잔존 없음** |
```

---

## 10. advisor ② 반영

(오케스트레이터가 채운다)
