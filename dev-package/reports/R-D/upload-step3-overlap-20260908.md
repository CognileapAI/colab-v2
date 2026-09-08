# 업로드 마법사 ②③ 레이아웃 결함 실측 (2026-09-08)

- 대상 = `main` `ccf76ec` · 읽기 전용(브라우저·빌드·게이트 미실행).
- **dev 배포분과 동일** — `git diff 83d3eb5..ccf76ec -- frontend` 출력 0행. 세 결함 전부 **83d3eb5 이전부터** 존재.
- 픽셀 단위 겹침 재현은 하지 않았다(브라우저 금지) — 스크린샷 서술 ↔ CSS 원문 대조 결과다.

## 1. 공통 원인 — 등록 카드 4장이 컨테이너 gap 을 못 받는다 ⭑

- 값 = `.up-card > .card-b { display:flex; flex-direction:column; gap:12px; }` (`frontend/src/components/upload/upload.css:125`).
- 등록 카드는 `class="card is-on"` 이다 — `up-card` 가 아니다: `RegisterArea.tsx:144`(①) · `:334`(②) · `:676`(연관 프로젝트) · `:847`(③).
- `.is-on` 은 **어느 CSS 에도 정의가 없다**(`grep -rn 'is-on' frontend/src --include='*.css'` = 0건).
- 남는 규칙은 `.card-b { padding: 6px 18px; }`(`frontend/src/components/members/members.css:22`) 뿐 — 세로 여백 6px.
- 회귀 출처 = `8db3deb` (FE R-B-4 · WU-B11 「여백 소유권」) — 자식 `margin-top` 을 걷고 gap 을 컨테이너에 옮기면서 선택자를 `.up-card >` 로 좁혔다. `card is-on` 은 그보다 앞선 `88fed95`(WU-B3) 산.
- 최소 수정 = `upload.css:125` 선택자를 `.up-card > .card-b, .card.is-on > .card-b` 로 넓힌다(1행). 대안 = 네 곳의 `className` 에 `up-card` 추가(4행).

## 2. ③ 연결 — 결함 3건

### (a) Lv 안내 상자가 구분선 위에 얹힌다
- 자리 = `LineageStep.tsx:346-356` `p.lin-scope-lv`.
- 원인 = `lineage.css:160-169` `.lin-scope-lv{ margin:0; border:1px …; background:#f7f8fa }` — 자기 margin 0 이고 §1 로 컨테이너 gap 도 0. 위 형제(원천 표기 `div.form-row`, `upload.css:212` `margin-bottom:10px`)와 10px, 카드 경계와는 6px 만 남아 자기 border 가 카드 border 와 붙어 보인다.
- `position:absolute`·음수 margin·`transform` 은 **0건**(`upload.css`·`lineage.css` 전수 grep — absolute 는 `.hidden-input:109`·`.dr-pop:397`·`.dr-cal-d:417` 셋뿐, 전부 ② 달력·숨김 입력).
- 최소 수정 = §1 한 행. 추가로 `.lineage-slot`(`upload.css:263`)과 같은 gap 12px 이 `.card-b` 에 서면 해소.

### (b) 「+ 새 프로젝트 만들기」 와 「직접 이어 붙이는」 문장이 겹쳐 보인다
- 두 문자열은 **다른 카드**다 — 문장 = `LineageStep.tsx:617-621` `.lin-ask .muted`(`lineage.css:136-138` `margin:0`), 버튼 = `RegisterArea.tsx:757-766` `.btn-ghost`(`upload.css:281` `border-color:transparent`).
- 사이에 있는 것 = ③ 카드 `.card-b` 하단 padding 6px ＋ 카드 경계 2줄 ＋ 연관 프로젝트 카드 상단 padding 6px. 두 카드를 감싸는 `div[data-testid="reg-s3"]`(`RegisterArea.tsx:846`)은 **CSS 규칙이 0건**이라 카드 사이 gap 도 0(바깥 `.up-steps` gap 16px 은 형제가 하나뿐이라 걸리지 않는다).
- 즉 두 줄 사이 실간격 ≈ 12px ＋ 경계선, 그 경계선이 문장을 관통해 「겹침」으로 읽힌다. **진짜 z축 겹침인지는 `[미상]`**(렌더 미실행).
- 최소 수정 = §1 한 행 ＋ `upload.css` 에 `[data-testid="reg-s3"]{display:flex;flex-direction:column;gap:16px;}` 1블록 신설.

### (c) ② 의 기간 오류가 ③ 에 남는다
- 문면 출처 = **서버 400** `services/core-api/src/colab_core/app/routes/catalog.py:1097` 「기간의 종료는 시작보다 앞설 수 없다.」
- 렌더 자리 = `RegisterArea.tsx:1088-1091` `p.warn[data-testid="reg-error"]` — 단계 분기(`.up-steps`, `:1027-1085`) **바깥**이라 `step` 과 무관하게 상시 노출.
- 지우는 자리 = `UploadModal.tsx:549`·`671`·`809` 뿐(다시 제출·첨부 재시도). **단계 이동 시 초기화 없음.**
- 등록 차단 여부 = 「데이터셋 만들기」는 `disabled={(props.lineageConflicts ?? 0) > 0}` (`RegisterArea.tsx:1141`) 하나로만 막힌다 — 이 오류는 버튼을 막지 않는다. 다만 같은 값으로 다시 눌러도 서버가 다시 400 → **실질 차단(재시도 무한)**.
- 최소 수정 = `UploadModal.tsx` 의 `setStep` 경로에 `setRegisterError(null)` 1행, 또는 `reg-error` 를 해당 칸(②) 안으로 옮긴다.

## 3. ② 메타데이터 입력 — 3건

### (1) 가독성 — 13px 미만 선언
- 대비는 합격 — `--up-muted #565c63`(`upload.css:7`) on `#fff` ≈ **7.4:1**, `.uf-hint #6b7280`(`:259`) ≈ **4.8:1**. 4.5:1 미달 클래스 **0건**.
- 미달은 **글자 크기**다. `upload.css` 주석 제거 후 13px 미만 선언 **20건** — 지목분: `.form-row label` 12px(`:213`) · `.fieldlbl` 12px(`:228` = 「파일에서 자동으로 읽었어요」·「사람이 적어요」) · `.muted` 12px(`:108`) · `.projtable th` 11px(`:239`) · `.qproj .qnote` 11px(`:248`) · `.autotag` 10px(`:214`) · `.reqtag` 10px(`:217-224`) · `.reg-actions .uf-hint` 12px(`:259`) · `.regsteps .cnt`·`.rs-f` 12px(`:196`·`:197`) · `.filecard .fs`·`.fkind` 12px(`:137`·`:138`) · `.companion .cl`·`.cw` 12px(`:153`·`:154`) · `.chip` 12px(`:231`). `lineage.css` 는 **9건**(`:54`·`70`·`92`·`181`·`186`·`205`·`212`·`248`·`268`).
- 기존 시험은 7개 셀렉터만 잰다(`frontend/test/design-fix-20260908.test.ts:96-108`) — `.form-row label`·`.fieldlbl` 은 목록 밖.
- 최소 수정 = 위 선언을 `var(--text-caption)`(13px · `shell/tokens.css:36`)로 올리고, `design-fix` 시험의 셀렉터 목록을 「`upload.css`·`lineage.css` 전수 13px 이상」으로 바꾼다(`lineageGraph.css` 전수 방식 `:84-88` 을 그대로 재사용).

### (2) 「다음」이 동작하지 않는다 · 기간 역전
- 「다음」 = `RegisterArea.tsx:1127` `disabled={analyzing || classifyBlocked}` · `analyzing = !props.status?.ready`(`:990`). 스크린샷 바닥 문구가 `NEXT_BLOCKED_HINT`(`:70` 「분석이 끝나면 다음으로 넘어갈 수 있어요」)이므로 그 시점 `status.ready === false` — **분석 미완이 원인**이고 기간과 무관. `.bin.gz` 분석이 왜 ready 로 안 갔는지는 `[미상]`(서버 로그 미열람).
- 종료<시작 검사는 **클라이언트에 없다**. 팝오버 `적용` 은 `PeriodCalendarPopover.tsx:262-278` 에서 순서 검사 없이 `onApply` 한다. `UploadModal.submit()`(`:761-808`)의 선검사는 이름·설명·분류/유형·Lv0 내려받은날 형상 넷뿐 — 기간 역전은 서버 400 에만 걸린다.
- 고른 기간이 관측 간격 **아래**에 뜨는 이유 = DOM 순서다. 기간 칸(`RegisterArea.tsx:433-473`)에는 값 표시 요소가 없고(달력 버튼만), 값은 `.regprev`(`:531-533` `data-testid="reg-period-preview"`)로 **관측 간격 `form-row`(`:492-529`) 다음** 에 그려진다. CSS grid 재배치 아님 — `form-3`(`upload.css:206`) 밖의 형제다.
- 최소 수정 = ⑴ `PeriodCalendarPopover` 의 `적용`에 시작>종료 거절 1블록(문면은 서버 축자 재사용) ⑵ `.regprev` 를 `:473` 직전(기간 `form-row` 안)으로 이동 ⑶ `submit()` 에 이름·설명과 같은 규율의 선검사 1블록 ＋ `setStep(2)`.

### (3) 필수 표기 ↔ 실제 필수 불일치
| 칸 | `submit()` 강제 | `필수` 배지 | 판정 |
|---|---|---|---|
| 데이터셋 이름 `reg-name` | 예 (`UploadModal.tsx:769-775`) | **없음** (`RegisterArea.tsx:374`) | **불일치** |
| 설명 `reg-summary` | 예 (`:777-783`) | 있음 (`RegisterArea.tsx:539-543`) | 일치 |
| 분류 `reg-category` | 예 (`:785-792`) | 있음 (`:153-156`) | 일치(단 ① 에 있음) |
| 유형 `reg-datatype` | 예 (`:785-792`) | 있음 (`:176-179`) | 일치 |
| 가공 단계 `reg-level` | 아니오(기본 `Lv2`) | 있음 (`:204-207`) | 과표기 |
| 주제 `reg-topic` | 아니오(`topic: null` 허용) | 없음 | 일치 |
| 공개 범위 `reg-visibility` | 아니오(`accessState===null` 허용) | 없음 | 일치 |
- 최소 수정 = `RegisterArea.tsx:374` 라벨에 `<span className="reqtag">필수</span>` 1행. 가공 단계 배지는 판정 사안(기본값이 있어 빈 상태가 없다) — Ted 확인 대상.

## 4. 차단성 · 자리 · 시험

- 차단 = (c)＋②(2). 기간 역전 상태에서는 등록이 서버 400 으로 계속 거절되고 화면은 고칠 칸을 지목하지 않는다. (a)(b)(1)(3)은 표시 결함.
- 원장 = 해당 항목 **없음**. `dev-package/prd/specs/R-D.md:95` 가 「디자인 fix 16 WU · R-C 후속 9건」을 **R-E 이월**로 적었고, `dev-package/intent/2026-09-08-r-d.md:92`(Q18~Q25)에 이 세 건은 없다. → **신규 WU 필요**(R-E 디자인 fix 묶음 편입 권고).
- 기존 시험 = `frontend/test/register-steps-20260907.test.tsx`·`upload.test.tsx`·`lineage-*.test.tsx` 는 jsdom RTL(레이아웃 미계산) · `design-fix-20260908.test.ts`·`css-residual-rc11.test.ts` 는 CSS 원문 문자열 계측. **겹침을 잡는 시험 0건.**
- `frontend-visual` 게이트는 못 잡는다 — `gates/tools/frontend-visual.sh:28` 「앱을 향해서는 읽기 전용이다. 클릭·입력·폼 제출을 하지 않는다」. 업로드 모달은 클릭으로만 열리므로 ②③ 은 계측 대상에 들어오지 않고, 판정 축도 `counts.small`·`counts.lowContrast` 둘뿐이라 겹침 축이 없다.
- 잡으려면 = ⑴ CSS 계측 시험에 「`card is-on` 을 쓰는 `.card-b` 가 gap 규칙을 받는가」 1건(문자열 대조로 가능) ⑵ 실화면 겹침 단언 — 모달을 연 뒤 `getBoundingClientRect()` 교차를 재는 `agent-browser` 시나리오(현 게이트의 읽기 전용 규율을 깨므로 별도 게이트).

## 5. 후속 항목 (이 보고서는 코드를 고치지 않았다)
1. `upload.css:125` 선택자 확장 — 등록 카드 4장 여백 복구.
2. `reg-s3` 두 카드 gap 규칙 신설.
3. `setStep` 시 `registerError` 초기화.
4. 기간 역전 클라이언트 선검사 ＋ `.regprev` 위치 이동.
5. 13px 미만 29건 승격 ＋ `design-fix` 시험을 전수 방식으로 교체.
6. `reg-name` 필수 배지 · 가공 단계 배지 판정.
