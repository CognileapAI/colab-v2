# 레인 보고 — L2b-1 화면 CSS 1/2(목록 · 검색 · 상세 · 계보 그래프 · 계보 · 승인)

- spec: `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md` 「레인 확정」(L2b 분할 · 세로 넘침 대조 · `frontend-visual` 임시 규칙) · 부록 I 「L2b」 행 · V7 · V8 · V10 · 구현 결정 「터치 규칙 CSS」 · 「입력 글자 하한 규칙」 · 「hover 감싸기」 · 부록 B(레인 L2b 중 6파일 13항목) · 부록 D(6파일 14규칙) · 부록 G(목록 · 검색 2곳) · 우려 1ⓐ
- intent: `dev-package/intent/2026-09-26-device-width-input-rules.md`
- 브랜치: `claude/dwi-l2b1` · 기준 `76d5bfe1` · 구현 커밋 `732ce323`
- task: `cc199dd573614ab58a8bc9dd03885e4e`(범위 선언 10경로 · 게이트 `frontend-test` · `frontend-design-lint` · `frontend-visual`)
- 판정: **L2b-1 완료.** 시험 RED 37 실패 → GREEN · 전체 150파일 2099건 통과 · 게이트 green 3 / red(판정) 0 / red(준비) 0 · 페이지 6 = 선언 URL 6 · 390 레인 L2b 판정에서 L2b-1 대상 red 0(터치 5크기 모두 0) · 16 · 넘침 red 0 · 1440 마우스 대 B0 픽셀 0.

## 1. 바뀐 것

| 파일 | 변경 |
|---|---|
| `frontend/src/components/catalog/catalog.css` | hover 7규칙 제자리 한 줄 감싸기 · 행 작업 칸 hover+초점 한 줄을 둘로 나눔(hover 쪽 감싸기 · `:focus-within` 쪽 조건 없음) · 640px 블록의 `.catalog-filters select { font-size: 16px; }` 삭제 · 파일 끝 `(pointer: coarse)` 블록(13–17) |
| `frontend/src/components/search/search.css` | hover 1규칙 감싸기 · 한 줄 640px 블록 `.search-hero input { font-size: 16px; }` 블록째 삭제 · 파일 끝 터치 블록(18 · 19) |
| `frontend/src/components/detail/detail.css` | hover 2규칙 감싸기 · L1a 의 `.detail-page .dh-file` 줄바꿈 규칙 **뒤** 파일 끝 터치 블록(24 · 25 · 28) |
| `frontend/src/components/lineage/lineageGraph.css` | hover 2규칙 감싸기 · 파일 끝 터치 블록(26 · 27) |
| `frontend/src/components/lineage/lineage.css` | 파일 끝 터치 블록(46) · hover 규칙 없음 |
| `frontend/src/components/approval/approval.css` | hover 1규칙 감싸기 · 44 대상 없음(터치 블록 없음) |
| `frontend/test/design-fix-20260924-F-css.test.ts` | 목록 hover 쌍 1개(× 2테마)의 비교 대상 매체 자리 5번째 원소 `'@media (hover: hover)'`(Q3ⓑ 승인 단언 변경 · 기대 값 · 개수 불변 · 삭제 0) |
| `frontend/test/device-width-input-20260926-L2b.test.ts` | 새 시험 41사례(개수 단언은 L2b-1 부분합 · 시험 이름에 표기) |

- 기존 hover 고정 시험 판정(착수 때 grep): `design-fix-20260924-L2.test.tsx:214`(`.btn-strong`) 와 `design-fix-followups-20260925-L2.test.tsx:146`(`.th-slot`) 은 둘 다 `upload.css` 규칙이라 **L2b-2 몫** — 이 레인은 두 파일을 고치지 않았다. F-css 의 업로드 쌍 3개(× 2테마)도 L2b-2 몫으로 남겼다.
- 셸 · 기본 · 프리미티브 · 토큰 CSS 변경 0 · TSX 변경 0 · `!important` 추가 0 · 새 16px 하한 0.

## 2. 시험 RED → GREEN

- RED(시험만 · CSS 변경 0 · `76d5bfe1` 위): `Tests 37 failed | 58 passed (95)`(새 L2b 시험 35 ＋ F-css 목록 쌍 2). 실패 예: `선택자 블록 수: .tbl tr.clk:hover td @media (hover: hover): expected +0 to be 1` · `expected '' to be '@media (hover: hover)'`. hover 시험이 감싸기 전 green 인 경우 0(도우미가 `@media` 중첩을 기록 · 정지 조건 해당 없음).
- 처음부터 통과한 새 사례 6(대상 개수 2 · `!important` 0 · 터치 블록 글자 크기 0 · 우려 1ⓐ 제외 · 명시도 — 현재 상태가 이미 맞는 것).
- GREEN(`732ce323`): 두 파일 `95 passed` · 새 파일 `41 passed` · 전체 `Test Files 150 passed · Tests 2099 passed`.
- 수정 없이 green: `design-fix-20260924-L1.test.ts`(`.tbl tr.clk td` transition · `:active` 단언) · `device-width-input-20260926-L1.test.tsx`(`.detail-page .dh-file` 규칙 2개 · 두 번째가 줄바꿈).

## 3. hover 감싸기(부록 D 레인 L2b 중 6파일 · L2b-1 부분합 14규칙 · 선택자 14)

| 파일 | 규칙 |
|---|---|
| `catalog.css` 8 | `.tbl tr.clk:hover td` · `.tbl tr.clk:hover td:first-child` · `.tbl thead th > .thf:hover` · `.colmenu button.cm-i:hover` · `.colmenu .cm-clr:hover` · `.tbl tbody tr:hover td.rowact .ra`(나눈 hover 쪽) · `.tbl td.rowact .rab:hover` · `.catalog-open:hover` |
| `search.css` 1 | `.search-page .hit-name:hover` |
| `detail.css` 2 | `.detail-page .use-sec .use-t a:hover` · `.detail-page .dsec-menu-i:hover` |
| `lineageGraph.css` 2 | `.detail-page a.ln:hover` · `.detail-page .lrow .ln-go:hover .ln-name` |
| `approval.css` 1 | `.dh-menu button:hover` |

- 형태: 모두 한 줄 원문을 `@media (hover: hover) { <원문> }` 로 같은 자리에서 감쌈(시험이 원문 포함을 단언).
- 초점 분리: `.tbl td.rowact .ra:focus-within { opacity: 1; }` 는 조건 없이 hover 쪽 바로 뒤에 둠. 여섯 파일에서 hover 와 초점을 한 규칙에 가진 것 0.
- L2b-2 에 남은 hover: 업로드 6 · 변수 표 2 · 대시보드 1 · 로그인 1 = 10 → spec 총합 24.

## 4. 16px 하한 삭제(부록 G 레인 L2b 중 2곳)

- `catalog.css` 640px 블록에서 `.catalog-filters select { font-size: 16px; }` 한 줄만 삭제(블록의 `.catalog-page` · `.catalog-filters` · `.catalog-page .desc` 규칙 유지 · 시험 고정).
- `search.css` 한 줄 블록 `@media (max-width: 640px) { .search-hero input { font-size: 16px; } }` 블록째 삭제.
- 390 에서 16 red 0 이 셸 블록(`(max-width: 640px), (pointer: coarse)`)으로 유지됨: 390 수치 전용 25장면 × 2테마 판정 16 red 0. 5 터치 크기(8장면 캡처) 16 red 0.
- L2b-2 에 남은 하한: `project.css` 2 · `login.css` 1.

## 5. 터치 44(부록 B 레인 L2b 중 L2b-1 13항목 · 각 파일 끝 `(pointer: coarse)` 블록)

| # | 측정 선택자 | 블록 안 선택자 · 선언 | 근거 |
|---|---|---|---|
| 13 | `.tbl .catalog-open`(행 높이) | `.tbl tr.clk { height: var(--control-height); }` | 우려 1ⓐ — 링크는 키우지 않음 · 표 행 `height` 는 최솟값 |
| 14 | `.tbl .rowact .rab` | 같은 선택자 · min-height · min-width | 640px 규칙과 같은 선택자 · 뒤 순서 |
| 15 | `.colmenu button`(캡처 사각) | 같은 선택자 | 640px 규칙과 같은 선택자 |
| 16 | `.fchips .fc button`(캡처 사각) | 같은 선택자 | 경쟁 규칙 없음 |
| 17 | `.fchips .fall`(캡처 사각) | 같은 선택자 | 같음 |
| 18 | `.hit-name` | `.search-page .hit-name` | 단추 · 글자 크기 불변 |
| 19 | `.crosslink a` | `.crosslink a` ＋ `display: inline-flex; align-items: center` | 글자 링크 · 검색 · 목록 공용(목록 장면의 교차 안내에는 링크 없음) |
| 24 | `.dsec-menu-i` | `.detail-page .dsec-menu-i` ＋ inline-flex · 가운데 | 탭 · 글자 크기 불변 |
| 25 | `.ig-more` | `.detail-page .infogrid .ig .v .ig-more` | 기존 선택자와 같은 명시도 |
| 26 | `.lrow .ln-go` | `.detail-page .lrow .ln-go` | 이미 inline-flex |
| 27 | `.lin-use` | `.detail-page .lin-use` | 고정 `height: 25px` 를 min-height 44 가 이김 |
| 28 | `.dt-edit.de-inline input` · `select`(캡처 사각) | 기본 규칙과 같은 두 선택자 | 기본 `height/min-height: 40px` 뒤 순서 |
| 46 | `.lin-link` | `.lin-link` | 단추 |

- 제외: 20 검색 중단 문장 속 링크(우려 1ⓐ · 터치 블록에 `.notice` 선택자 0 · 시험 고정). 13 「열기」 링크 자체(행 높이로 잼 · 시험 고정).
- 캡처 사각 15–17 · 28: 시험이 터치 블록 안 규칙 존재와 선언을 단언한다(개수만이 아님).
- 터치 블록 선택자 집합 = 대상 선택자뿐(시험 고정) · 글자 크기 선언 0.
- 상세 CSS 순서: L1a 줄바꿈 규칙(`.detail-page .dh-file { overflow-wrap: anywhere; }`) → 터치 블록(파일 끝) · 기존 시험에 순서 고정이 없어 새 시험이 순서를 단언.

## 6. 게이트(task 실행 · 호스트 단독)

- 실행: `gates/run.sh task`(선언 게이트 3개 한 번) · `COLAB_TEST_ENV_FILE=~/.colab-v2-test-32.env` · `COLAB_TASK_ID=<task>` · `COLAB_VISUAL_URLS` = 이 레인이 띄운 audit 빌드(`vite preview --config audit.vite.config.ts --host 127.0.0.1 --port 47461 --strictPort` · 시작 때 PID 저장 · 그 PID 만 종료)의 `audit-design.html?scene=<장면>&design=full` 6건(`catalog` · `search` · `search-down` · `detail` · `lineage-picker` · `approval` · 「레인 확정」 임시 규칙대로 장면 먼저). `COLAB_VISUAL_EXEMPT` 미사용.

| 게이트 | 결과(`732ce323`) |
|---|---|
| `frontend-test` | green — 2099 통과 · 실패 0 |
| `frontend-design-lint` | green — 파일 21 · a–h 0 · 문서 표 갈림 0 |
| `frontend-visual` | green — **페이지 6(= 선언 URL 6)** · 13px 미만 0 · 대비 < 4.5 0 · 스크린샷 12 |
| 계 | green 3 / red(판정) 0 / red(준비) 0 |

- 이 보고서 커밋 뒤 같은 명령으로 한 번 더 돌려 인계한다(최종 gate-summary 절대경로와 3계수는 인계 메시지).

## 7. 수치(직렬 실행 · 자기 캡처 · 트리 `732ce323`)

### 7-1. 390 터치 수치 전용 · 레인 L2b 판정

- 실행: `capture.py --label dwi0926-l2b1-390 --metrics-only --scene <장면> --viewport 390`(25장면 × 2테마 · 50파일 · 모두 종료 0 · 첫 실행이 audit 빌드). 장면 = L2b 레인 장면 17 전부(L2b-2 대상이 「재지 않음」 78 을 내지 않게) ＋ 이 레인 대상이 그려지는 `search-empty` · `search-degraded` · `detail-preview-map` · `detail-preview-map-value` · `approval` · `approval-dialog` · `access` · `pending`.
- 판정(`judge.mjs --lane L2b`): `files=50 lane=L2b red=86 readiness=0 notMeasured=118 captureBlind=7 exemptHits=0 smallOther=16 outsideRed=16:0,44:32,넘침:0,가림:0 exit=1`.
  - **L2b-1 대상 red 0.** red 86 은 전부 L2b-2 대상 44(개수만): 8 → 4 · 9 → 2 · 11 → 6 · 12 → 4 · 31 → 4 · 32 → 28 · 33 → 2 · 35 → 8 · 39 → 6 · 40 → 6 · 41 → 6 · 42 → 6 · 43 → 2 · 44 → 2.
  - 16 red 0 · 넘침 red 0. 레인 밖 44 red 32(다른 레인 대상 · 개수만).
- L2b-1 대상 390 상자(최솟값 · 라이트 · 다크 합): 13 행 1065.1×73.5 · 14 44×44 · 18 154×44 · 19 67.4×44 · 24 48.2×44 · 25 44×44 · 26 177.7×44 · 27 126.5×44 · 46 88.2×44.
- 「재지 않음」(L2b-1 대상): 상자 없는 적중 0. 캡처 사각 15 · 16 · 17 · 28 은 어느 장면에도 맞는 요소가 없다(열 메뉴 닫힘 · 적용된 조건 없음 · 인라인 편집 아님 · 판정의 캡처 사각 7 에 포함 · §5 CSS 시험으로 확인). `notMeasured=118` 은 모두 다른 레인 대상(폭 숨김 3 · 4 등)의 상자 없는 적중이다.

### 7-2. 터치 5크기(8장면 캡처 · 수치 모드)

- 실행: `capture.py --label dwi0926-l2b1-cap --skip-build --parallel 2 --metrics --only catalog,search,search-down,detail,lineage-picker,approval,upload-link,detail-preview-map`(종료 0 · 96장).
- 판정(`judge.mjs --lane L2b`): `files=96 red=40 readiness=1 … exit=78` — 78 은 이 8장면에 L2b-2 대상 장면이 없어 그 대상(8–12 · 31–35 · 37 · 38 · 43 · 44)이 재지지 않은 것이다(기대 · 7-1 이 전 장면으로 판정). red 40 은 전부 `upload-link` 의 L2b-2 대상 39–42(크기마다 8).
- **L2b-1 대상 red: 390 · 844x390 · 820 · 1024 · 1180 모두 0.** 최솟값은 5크기 모두 7-1 과 같다(13 행은 1180 에서 1114×73.5). 16 red 0 · 넘침 red 0(5크기).

### 7-3. 세로 넘침 대조(「레인 확정」 · 막대 · 행 · 탭 · 컨테이너)

- 방법: 수치 전용 캡처 실행기의 측정 직후 같은 세션에서 컨테이너 상자와 자손 상자의 세로 범위(컨테이너 위 기준)를 읽는 일회용 래퍼(커밋 안 함 · 실행기 코드 변경 0). 창 크기 · 입력 방식은 실행기의 상태 확인(78)을 그대로 거침. 마우스 = 같은 폭 `WxH:mouse` 수치 전용 실행. 라이트.

| 장면 · 컨테이너 | 폭 | 터치 높이 | 터치 자손 범위 | 같은 폭 마우스 높이 | 마우스 자손 범위 | 차이 | 설명 |
|---|---|---:|---|---:|---|---:|---|
| `catalog` 표 행 `tr.clk`(3행) | 390 · 820 · 1024 | 74 | 0–74 | 74 | 0–74 | 0 | 행은 이미 44 초과 |
| `catalog` 교차 안내 | 390 / 820 · 1024 | 75.6 / 54.8 | 17–58.6 / 17–37.8 | 75.6 / 54.8 | 같음 | 0 | 목록 교차 안내에는 링크 없음 |
| `search` 결과 머리 `.hit-head`(2 · 3번째) | 390 · 820 · 1024 | 44 | 0–44 | 24 | 0–24 | +20 | 이름 단추 24 → 44 |
| `search` 결과 머리(1번째) | 390 / 820 · 1024 | 73 / 44 | 0–73 / 0–44 | 53 / 24 | 0–53 / 0–24 | +20 | 같음(390 은 두 줄로 감김) |
| `search` · `search-down` 교차 안내 | 390 / 820 · 1024 | 106.8 / 78 | 17–89.8 / 17–61 | 83.6 / 54.8 | 17–66.6 / 17–37.8 | +23.2 | 링크 20.8 → 44 |
| `detail` 구역 메뉴 막대 `.dsec-menu` | 390 · 820 · 1024 | 61 | 8–52 | 51.4 | 8–42.4 | +9.6 | 탭 34.4 → 44 |
| `detail` 기본 정보 칸(「보기」) | 390 · 1024 / 820 | 92.8 / 116.8 | 12–80.8 / 12–104.8 | 72.8 / 96.8 | 12–60.8 / 12–84.8 | +20 | 「보기」 17 → 44 · 줄 높이 24 에서 +20 |
| `detail` 계보 목록 줄 `.lrow`(이동 링크 있는 줄) | 390 / 820 · 1024 | 170.4 / 88.8 | 11–159.4 / 11–77.8 | 150.4 / 68.8 | 11–139.4 / 11–57.8 | +20 | 이동 링크 24 → 44 |
| `detail` 계보 목록 줄(링크 없는 2줄) | 390 / 820 · 1024 | 98.4 · 75.8 / 65.6 · 43 | 같음 | 같음 | 같음 | 0 | |
| `detail` 계보 그래프 칸(활용 배지) `.lin-col` | 3크기 | 153.6 | 13.9–139.7 | 153.6 | 23.4–130.2 | 0 | 배지 25 → 44 · 자손 범위가 위아래 9.5 씩 넓어졌지만 칸 안(칸 높이는 옆 칸이 정함) |
| `detail` 계보 그래프 틀 `.lin-graph` | 3크기 | 191.6 | 19–172.6 | 206.6 | 19–172.6 | −15 | 마우스만 가로 스크롤 막대 15px(장면 목록 `scrollbars`: 터치 숨김 · 마우스 기본) · 44 와 무관 · 자손 범위 같음 |
| `upload-link` 범위 안내 문단 `.lin-scope-lv` | 390 | 89.8 | 34.8–78.8 | 89.8 | 34.8–78.8 | 0 | 390 은 기존 640px 규칙으로 이미 44 |
| 같음 | 820 · 1024 | 66 | 11–55 | 45.8 | 11–34.8 | +20.2 | 「분류에서 바꾸기」 23.8 → 44 |

- 캡처 사각(CSS 계산 · 캡처 없음): 적용된 조건 줄 `.fchips` — 칩 `.fc` 는 고정 높이 32 그대로이고 빼기 단추(16)는 44 라 칩 위아래로 6px 씩 나간다(단추 배경 없음 · 보이는 변화는 칩 폭 +20). 줄 높이는 「전체 해제」(17) 44 때문에 32 → 44(+12 · 줄 안쪽 여백 12 는 그대로 · 넘친 6px 는 그 여백 안).
- 스크린샷 판독(390 · 820 · 1024 터치 · `catalog` · `search` · `search-down` · `detail` · `upload-link`): 자손이 막대 · 행 · 칸 밖으로 삐져나와 보이는 곳 0. 상세 「보기」 · 활용 배지는 44 높이의 파란 면으로 커져 보인다(대상 크기 그대로의 결과).
- 판정: 모든 차이가 대상 누름 칸의 「기존 높이 → 44」로 설명된다(−15 는 스크롤 막대). 멈춤 없음.

### 7-4. 1440 마우스 대 B0 `dwi0926-base`

- `diff.mjs --subset --viewport 1440 <B0> dwi0926-l2b1-cap <보고>` → **16장(8장면 × 2테마) · red 0 · 엄격 픽셀 0 · 종료 0**.
- B0 폴더: 워크트리 `agent-abf926c2ed31f5520` 의 `frontend/.visual/dwi0926-base`(읽기만).

## 8. 원한 결과 대조 · 이탈 · 남은 것

- 원한 결과 대조(V7 화면 · V8 화면 · V10 감싸기 — L2b-1 부분):
  - 충족: hover 14규칙 조건 안 · 조건 밖 0 · 초점 분리 1 · 화면 16px 하한 2곳 삭제 · 새 하한 · `!important` 0 · 터치 5크기에서 L2b-1 대상 44 red 0 · 16 red 0 · 넘침 0 · 캡처 사각 4 CSS 단언 · 1440 마우스 픽셀 0.
  - 미달(L2b-2 몫 · 설계대로): hover 10 · 44 대상 21 · 하한 3곳 · F-css 업로드 쌍 · L2 · 후속 L2 시험 1자리씩.
  - 초과: 13 번에 행 높이 규칙 1줄(`.tbl tr.clk { height: var(--control-height); }` · 현재 행 74 라 수치 변화 0 · 대상 규칙을 CSS 로 고정하려는 레인 결정).
- 레인 결정(spec 빈칸 · 근거로 닫음):
  - 13 은 링크가 아니라 행에 최소 높이를 둠(우려 1ⓐ 「행 높이 44로 잰다」 · 표 행은 min-height 가 정의되지 않아 `height` 사용).
  - 19 교차 안내 44 규칙은 `search.css` 에 한 번(spec 부록 B 자리 · 목록 화면에도 적용되는 공용 선택자).
  - 16 빼기 단추는 칩 높이를 바꾸지 않고 누름 칸만 키움(§7-3).
- L2b-2 에 넘길 것:
  - `device-width-input-20260926-L2b.test.ts` 의 부분합 단언(시험 이름 「L2b-1 부분합」)을 spec 총합으로 올린다: `FILES` 에 6파일 · `HOVERS` 에 10 · `TAPS` 에 21(`L2B2` 목록을 옮김) · 하한 삭제 3곳.
  - F-css 업로드 쌍 3(× 2테마) · `design-fix-20260924-L2.test.tsx:214` · `design-fix-followups-20260925-L2.test.tsx:146` 은 손대지 않았다.
  - 7-1 과 같은 25장면 390 판정을 다시 돌리면 L2b-2 대상 red 86 이 0 이 되어야 한다. 마지막 게이트는 L2b 14 URL 전부.
- 후속: 세로 넘침 측정은 여전히 일회용 래퍼다(판정 스크립트 · 수치 파일에 막대 · 컨테이너 높이 없음 · E 몫).
- 캡처 폴더(추적 제외 · `frontend/.visual/`): `dwi0926-l2b1-390` · `dwi0926-l2b1-cap` · `dwi0926-l2b1-diff-1440` · `dwi0926-l2b1-boxes-touch` · `dwi0926-l2b1-boxes-mouse` · 판정 출력 `dwi0926-l2b1-judge-390.json` · `dwi0926-l2b1-judge-cap.json`.
