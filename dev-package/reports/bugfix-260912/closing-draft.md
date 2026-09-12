# R-BUGFIX-260912 마감 원장 초안 (DRAFT · 미승인)

- 성격 = **초안 1건**. 추적 파일 편집 0 · 커밋 0 · 원장 번호 발급 0. 전수 게이트가 이 트리에서 실행 중이라 `work-items.yaml`·`03-HANDOFF.md`·`PLAN-SoT.md`·`CLAUDE.md` 를 한 글자도 고치지 않았다.
- 작성 = 2026-09-12 · 근거 = 라운드 파일 `dev-package/prd/rounds/R-BUGFIX-260912.md` 「병합·원장」 · 판정 정본 `dev-package/reports/issues/2026-09-12-ted-decisions.md` · L4 보고 `dev-package/reports/issues/2026-09-12-measure-L4.md` · 커밋 `10a3fb8..f98d09de` 27건.
- 실측 두 값(병합 직전 오케스트레이터가 **재실측**) —
  - `bash dev-package/prd/tools/max-decision.sh` = **381** ⟹ 이 문서의 `〈382〉`~`〈387〉` 은 임시 번호다(`.claude/rules/colab-rules.md §4-1`).
  - 대장 최대 `BF-` 번호 = **13**(`grep -o "id: BF-[0-9]*" | sort -t- -k2 -n | tail -1`) ⟹ 신규 `BF-14`~`BF-17`.
- ⛔ **미확인 1건 — 레인 게이트 요약 3계수.** `dev-package/reports/bugfix-260912/{L1,L2,l3,L3b}/gate-summary.json` 은 이 워크트리에 **없고**(`find` 0건) `git ls-files` 에도 없다. 커밋 본문에도 3계수가 없다. 아래 `completion_def`·`evidence` 의 게이트 계수 자리는 `<green N / red(판정) N / red(준비) N — 요약줄 축자>` 플레이스홀더로 두었다. **기재 전에 요약 파일 실물에서 채운다.**

---

## 0. 커밋 대조 (근거)

| 항목군 | 이슈 | 커밋 sha (통합 브랜치) |
|---|---|---|
| 등록 설명문 배치 | `#31` | `bb3e77d8` |
| 미리보기 축소본 자리 | `#26` | `6afa776a` · `c9e95eb2`(중복 방지 규칙) |
| 업로드 이어가기·버리기·고지 | `#33`㉠ · `#34` · `#32` · `#24`㉯ | `b8b4e7e2` · `aa26db94` · `cef275a0` · `1a381310` |
| 미리보기 조작 줄 | `#25`⑵ · `#27` · `#28` ＋ 확장보기 고르개 | `ccaf27f6` · `a841d7a1` · `67e25399` · `bf02a0c8` · `f98d09de`(R-C-2 문면) |
| 실측·재현 | `#24`㉮ · `#25`⑴ · `#29`⑴ · `#30`㈎ | `9f925219` · 판정 확정 `75a053ea` |

---

## 1. `dev-package/work-items.yaml`

### 1-1. 삽입 지점

- **파일 끝 `items:` 리스트 마지막 항목 뒤**. 실측 = 마지막 항목 `id: WU-PREVIEW`(그 블록의 `sources:` 행이 파일 마지막 줄). 그 줄 다음에 빈 줄 1개를 두고 아래 6블록을 순서대로 덧붙인다.
- 들여쓰기 = 항목 머리 `  - id:` (공백 2) · 필드 `    ` (공백 4). 키 순서는 `BF-` 관행 그대로 — `id` · `name` · `status` · `stage` · `owner` · `entry_conditions` · `depends_on` · `completion_def` · `evidence` · `deadline` · `note` · `sources`.
- `stage` 값 = **`stage1`**. 근거 = `BF-1`~`BF-9`·`BF-11`·`BF-13` 이 전부 `stage1`(예외 = `BF-10` `backlog` · `BF-12` `stage2`)이고 이번 4건은 전부 프론트 화면 결함이다.

### 1-2. `BF-14` — 등록 카드 설명문 배치 (`#31`)

```yaml
  - id: BF-14
    name: "등록 카드 기간 칸의 안내 문단이 컨트롤 앞에 있어 카드 안 배치가 둘로 갈린다 (#31)"
    status: done
    stage: stage1
    owner: "frontend (D3 등록 카드)"
    entry_conditions:
      - "없음 — 실측: 카드 안 안내 문단 4건 중 3건이 이미 컨트롤 뒤이고, 기간 칸 하나만 앞이다. PRD-40 은 앞/뒤를 지정하지 않는다"
      - "Ted 판정 정본 `dev-package/reports/issues/2026-09-12-ted-decisions.md` — 「#31 문면 삭제」는 판정 카드 ①~⑪ 에 없다(문면 유지 · 위치만 통일)"
    depends_on: []
    completion_def: >-
      ⑴ `frontend/src/components/upload/RegisterArea.tsx` 의 기간 칸이 「라벨 → 컨트롤 → 설명문」 순서다
      ⑵ 문면 상수 · `data-testid` · 클래스명 무변(문면 삭제는 범위 밖)
      ⑶ `upload.css` 접촉 0
      ⑷ `frontend/test/register-steps-20260907.test.tsx` 에 순서 단언이 서고 red 선실측 뒤 green
      ⑸ 단독 게이트 `frontend-test` 연속 2회 green.
    evidence: "2026-09-12 커밋 `bb3e77d8`. 게이트 `frontend-test` <green N / red(판정) N / red(준비) N — 요약줄 축자> · 요약 `dev-package/reports/bugfix-260912/L2/gate-summary.json`. 이슈 https://github.com/CognileapAI/colab-v2/issues/31"
    deadline: null
    note: "라운드 R-BUGFIX-260912 L2 레인. 배치 규약을 정책 문서에 적는 것은 후속 항목(이 회차 범위 밖)."
    sources: ["dev-package/prd/rounds/R-BUGFIX-260912.md", "dev-package/prd/specs/2026-09-12-issue-register-hints-parent-picker.md", "dev-package/intent/2026-09-12-issue-register-hints-parent-picker.md", "dev-package/reports/issues/2026-09-12-ted-decisions.md"]
```

### 1-3. `BF-15` — 미리보기 64×64 축소본 자리 (`#26`)

```yaml
  - id: BF-15
    name: "미리보기 64×64 축소본이 지도 자리 위에 겹쳐 그려진다 — 접히는 자리로 이동 ＋ 중복 방지 (#26)"
    status: done
    stage: stage1
    owner: "frontend (D7 미리보기)"
    entry_conditions:
      - "Ted 판정 ⑤ ⓑ(2026-09-12) — 지도 자리에서 빼고 접히는 자리(대표 그림 고르개 옆)로 옮긴다. 결정 `〈88〉`-3 의 표시 목적은 유지한다"
      - "Ted 추가 확인(2026-09-12 · 미리보기 spec v2 「모두 권고대로」) — 축소본 중복 방지 규칙을 같은 묶음에 넣는다"
    depends_on: []
    completion_def: >-
      ⑴ 축소본이 `.mapcanvas` 위에 그려지지 않는다 — 자리는 `up-preview-options` details 안 `up-thumb-img` 옆이다
      ⑵ 대표 그림을 고른 경우에만 자동 축소본을 그 옆에 대조용으로 세우고, 고른 그림이 없으면 기존대로 한 장이다
      ⑶ 판정 수단 두 가지 — DOM 조상·형제 관계 ＋ 주석을 제거한 CSS 원문 계측(jsdom 은 레이아웃을 계산하지 않는다)
      ⑷ 단독 게이트 `frontend-test` 연속 2회 green ＋ `frontend-typecheck` 1회 green.
    evidence: "2026-09-12 커밋 `6afa776a`(자리 이동) · `c9e95eb2`(중복 방지). 게이트 <green N / red(판정) N / red(준비) N — 요약줄 축자> · 요약 `dev-package/reports/bugfix-260912/l3/gate-summary.json`. 이슈 https://github.com/CognileapAI/colab-v2/issues/26"
    deadline: null
    note: "결정 `〈88〉`-3 의 재판정 기록 대상 — 등재 `PLAN-SoT §9 〈N+2〉`(임시 번호 · 병합 직전 재실측). 라운드 R-BUGFIX-260912 L3 레인."
    sources: ["dev-package/prd/rounds/R-BUGFIX-260912.md", "dev-package/prd/specs/2026-09-12-issue-preview-controls.md", "dev-package/prd/specs/2026-09-12-issue-preview-controls-v2.md", "dev-package/intent/2026-09-12-issue-preview-controls.md", "dev-package/reports/issues/2026-09-12-ted-decisions.md"]
```

### 1-4. `BF-16` — 업로드 이어가기·버리기·분석 중 고지 (`#33`㉠ `#34` `#32` `#24`㉯)

```yaml
  - id: BF-16
    name: "업로드 모달 4건 — 배너 재개 배선 ＋ 닫기 세 번째 선택지 ＋ 배너 행 폐기 ＋ 분석 중 사유·동작 표시 (#33㉠ · #34 · #32 · #24㉯)"
    status: done
    stage: stage1
    owner: "frontend (D5 업로드 모달)"
    entry_conditions:
      - "Ted 판정 ①(#32 포함 · 공통 헬퍼 `discardUpload` 추출) · ②(세 번째 선택지 신설 · 뜻 = 이 브라우저에서 감춤 · 서버 행은 24h 만료 스윕) · ③(사유 한 줄 고지 · 비활성 유지) · ④(#33 을 ㉠ 배선 / ㉡ 등록 장면 복원 으로 분리 · ㉡ 은 범위 밖) · ⑧(소요 수용 ＋ 「동작 중」 표시 보강) — 2026-09-12"
      - "L4 실측 회수 완료 — `dev-package/reports/issues/2026-09-12-measure-L4.md`"
    depends_on: []
    completion_def: >-
      ⑴ `#33`㉠ — 배너 재개 요청의 재개 식별자를 업로드 진입 컴포넌트가 모달 props 로 전달하고 모달이 무장한 채 열린다. 기존 경로(`resumeRef`·`resumeFromRef='banner'`·`resumeArm`·`seq` 재무장) 재사용 · 신규 개념 0
      ⑵ `#34` — 닫기 확인의 세 번째 선택지가 서고, 뜻이 「이 브라우저의 미완결 기억 삭제」(`forgetPending` 1회 · 서버 호출 0)이며 문면이 24시간 만료를 그대로 말한다. 지울 기억이 있을 때만 낸다
      ⑶ `#32` — 메인 배너의 **접수 완료 행**에 폐기 버튼이 서고 같은 공통 헬퍼를 부른다. 폐기 후 배너가 비면 카드가 사라진다. 등록을 마친 데이터셋에는 닿지 않는다
      ⑷ `#24`㉯ ＋ 판정 ⑧ — `다음 →`(`reg-open`)은 비활성을 유지하고 사유 한 줄이 `title`·`aria-describedby` 로 연결된다. 분석 중 칩에 활동 표시(CSS · `prefers-reduced-motion` 존중)와 클라이언트 경과 시간(`N초 경과`)이 붙는다. 진행 수치가 응답에 없으므로 조각 진행률은 표시하지 않는다(계약 변경 0)
      ⑸ `upload.css` 는 파일 끝 구획 블록(`/* == R-BUGFIX-260912 L1 == */`) 안에만 덧붙는다
      ⑹ 단독 게이트 `frontend-test` 연속 2회 green ＋ `frontend-typecheck` 1회 green · vitest 수집 건수가 착수 전 대비 6건 이상 증가.
    evidence: "2026-09-12 커밋 `b8b4e7e2`(#33㉠) · `aa26db94`(#34) · `cef275a0`(#32) · `1a381310`(#24㉯＋⑧). 게이트 <green N / red(판정) N / red(준비) N — 요약줄 축자> · 요약 `dev-package/reports/bugfix-260912/L1/gate-summary.json`. 이슈 https://github.com/CognileapAI/colab-v2/issues/33 · /34 · /32 · /24"
    deadline: null
    note: "문면 2건은 초안이다 — `UPLOAD_CLOSE_FORGET`·`UPLOAD_CLOSE_FORGET_NOTE`(PRD-34 문면표 개정 대기) · `REG_OPEN_ANALYZING_REASON`·`analyzeElapsed`(PRD-43 자리표 등재 대기). 확정 전까지 PRD-43 21행 표(`COPY_ROW_IDS`·`COPY_ROWS`·`FIXED_COPY`)에 등재하지 않는다. 범위 밖 = `#33`㉡ 접수 완료분 등록 장면 복원 · 서버 즉시 삭제 창구(계약 개정)."
    sources: ["dev-package/prd/rounds/R-BUGFIX-260912.md", "dev-package/prd/specs/2026-09-12-issue-upload-resume-discard.md", "dev-package/prd/specs/2026-09-12-issue-upload-analysis-notice.md", "dev-package/intent/2026-09-12-issue-upload-resume-discard.md", "dev-package/intent/2026-09-12-issue-upload-analysis-notice.md", "dev-package/reports/issues/2026-09-12-measure-L4.md", "dev-package/reports/issues/2026-09-12-ted-decisions.md"]
```

### 1-5. `BF-17` — 미리보기 조작 줄 (`#25`⑵ `#27` `#28` ＋ 확장보기 고르개)

```yaml
  - id: BF-17
    name: "미리보기 조작 줄 3화면 — 고르개를 틀 위 고정 줄로 ＋ 확장보기 고르개 신설 ＋ 확대 줄 접힘·가림 해소 (#25⑵ · #27 · #28)"
    status: done
    stage: stage1
    owner: "frontend (D7 미리보기 · 업로드 인라인 · 상세 · 확장보기)"
    entry_conditions:
      - "Ted 판정 ⑥ ⓐ(2026-09-12) ＋ 같은 날 재확인 — 인라인·상세 2화면 이동에 더해 **확장보기에도 고르개 줄을 신설**한다(원문 「니 권곧로 확장보기에서도 추가하다」). 기능 추가분은 Ted 지정 예외(편의 기능 유예 규칙 `.claude/rules/colab-rules.md §6-2` 의 예외)"
      - "Ted 판정 ⑦ ⓐ(2026-09-12) — 접힘·가림 해소까지만. 고정 배치 재설계는 범위 밖"
      - "Ted 판정 ⑧(2026-09-12) — 그리는 동안 「동작 중」임을 화면이 보여 준다"
    depends_on: [BF-15]
    completion_def: >-
      ⑴ `#25`⑵ — 파일·변수·시각 고르개 줄이 `.pv-frame` 바깥 고정 줄로 서고, 같은 공용 줄을 세 화면이 쓴다(업로드 인라인 `PreviewPanel.tsx` · 상세 `datasetpreview/DatasetPreviewSection.tsx` · 확장 오버레이 `PreviewExpandOverlay.tsx`)
      ⑵ 확장보기의 선택 상태는 인라인 미리보기와 공유한다 — 새 상태 저장소 신설 0
      ⑶ 오버레이에 「그리는 중」 진행 표시가 선다(판정 ⑧)
      ⑷ `#27`＋`#28` — 인라인에서 확대 줄이 스크롤 없이 보이고, `.modal-b.pvx-b` 의 flex 방향과 `.pv-layers .pv-tile` 폭 상한으로 가림이 사라진다. 버튼 글자 줄바꿈 금지
      ⑸ 규약 문면 개정이 같은 커밋에 든다 — 부품 머리 주석(`PreviewPickRow.tsx` 「틀 안의 컨트롤 줄」)과 `dev-package/prd/rounds/R-C-2-frontend.md` 해당 축자
      ⑹ `upload.css` 는 기존 규칙만 고치고 파일 끝에 덧붙이지 않는다
      ⑺ 단독 게이트 `frontend-test` 연속 2회 green ＋ `frontend-typecheck` 1회 green. `frontend-visual` 은 세 화면 주소를 `COLAB_VISUAL_URLS` 로 선언할 수 있을 때만 1회.
    evidence: "2026-09-12 커밋 `ccaf27f6`·`a841d7a1`(#25⑵ 2화면) · `67e25399`(확장보기 고르개 ＋ 그리는 중) · `bf02a0c8`(#27·#28) · `f98d09de`(R-C-2 문면 개정). 게이트 <green N / red(판정) N / red(준비) N — 요약줄 축자> · 요약 `dev-package/reports/bugfix-260912/L3b/gate-summary.json`. 이슈 https://github.com/CognileapAI/colab-v2/issues/25 · /27 · /28"
    deadline: null
    note: "규약 `R-C-2` 「틀 안 컨트롤 줄」 → 「틀 위 고정 줄」 개정 등재 = `PLAN-SoT §9 〈N+3〉`(임시 번호). 범위 밖 = 미리보기 고정 배치 재설계 · 「이미지에서 고르기」 설계."
    sources: ["dev-package/prd/rounds/R-BUGFIX-260912.md", "dev-package/prd/specs/2026-09-12-issue-preview-controls.md", "dev-package/prd/specs/2026-09-12-issue-preview-controls-v2.md", "dev-package/intent/2026-09-12-issue-preview-controls.md", "dev-package/prd/rounds/R-C-2-frontend.md", "dev-package/reports/issues/2026-09-12-ted-decisions.md"]
```

### 1-6. `PA-T` — 다중 서버 로그인 실패 제한 공유 (`#11` · 판정 ⑪ ⓐ)

- 모양 근거 = `BO-2`(`after_stage2` · `open` · `evidence: null`).
- `completion_def` 안의 인용 = `CR-2` 축자 「dev 로그인 제한은 현행 프로세스 메모리·자격/클라이언트 각각 5회/15분·성공 시 초기화 수용」.

```yaml
  - id: PA-T
    name: "다중 서버 로그인 실패 제한 공유 ＋ 신뢰 프록시 판정"
    status: open
    stage: after_stage2
    owner: "D2 / core-api"
    entry_conditions: ["Ted 판정 ⑪ ⓐ(2026-09-12) — 대장 항목 등재만 · 미착수. 착수 시점·범위는 별도 판정", "인스턴스 2대 이상 운용이 결정된 뒤 — 1대 운용에서는 현행 프로세스 메모리로 닫혀 있다"]
    depends_on: []
    completion_def: "둘을 모두 만족한다. ⑴ 로그인 실패 제한이 인스턴스 사이에서 공유된다 — 서버 대수가 늘어도 자격·클라이언트 각각의 계수 창(5회/15분 · 성공 시 초기화)이 한 벌로 동작한다. 현행 수용 축자는 `CR-2` completion_def 의 「dev 로그인 제한은 현행 프로세스 메모리·자격/클라이언트 각각 5회/15분·성공 시 초기화 수용」이고, 이 항목은 그 수용의 전제(단일 프로세스)가 깨지는 시점을 대상으로 한다. ⑵ 클라이언트 식별의 신뢰 프록시 판정이 기록된다 — 어느 홉까지 신뢰하고 어느 헤더를 읽는지, 위조 헤더로 다른 클라이언트의 계수를 소모시키지 못하는지 음성 시험 1건."
    evidence: null
    deadline: null
    note: "출처 = GitHub 이슈 https://github.com/CognileapAI/colab-v2/issues/11 . Ted 판정 ⑪ ⓐ 는 「대장 항목 등재만 · 미착수」이고 근거는 「열린 항목이 없어 남은 일로 집계되지 않는다」. 등재와 동시에 `CLAUDE.md §0` 세 번째 단 괄호 목록을 갱신한다(게이트 `work-item-consistency` ㈕ 대조)."
    sources: ["dev-package/prd/rounds/R-BUGFIX-260912.md", "dev-package/reports/issues/2026-09-12-ted-decisions.md", "dev-package/reports/issues/2026-09-12-github-open-issues.md"]
```

### 1-7. `LV-5` — 계보 부모 찾기 창을 목록 화면 형태로 (제안 · backlog)

- 모양 근거 = `BF-10`(`backlog` · `open` · `owner` 끝에 「착수 시점은 Ted」).
- ⚠ **제안이다.** 판정 ⑨ ⓐ 는 「화면 형태 재구성은 **신규 항목 후보**」까지이고 등재 지시가 아니다. Ted 승인 없이 넣지 않는다.

```yaml
  - id: LV-5
    name: "계보 부모 찾기 창을 목록 화면 형태로 재구성 (제안 · #30 후속)"
    status: open
    stage: backlog
    owner: "frontend (D4 계보 화면) — 착수 시점은 Ted"
    entry_conditions:
      - "Ted 판정 ⑨ ⓐ(2026-09-12) — 이번 회차는 0행 재현 확인까지이고 화면 형태 재구성은 **신규 항목 후보**다. 이 항목의 등재 자체가 Ted 승인 대상이다"
      - "L4 재현 결과가 조회 결함이 아니라 **사용법**으로 닫혔다(`dev-package/reports/issues/2026-09-12-measure-L4.md` §4-2) — 즉 이 항목은 결함 수정이 아니라 화면 형태 개선이다"
    depends_on: []
    completion_def: >-
      ⑴ 부모 찾기 창이 데이터셋 목록 화면과 같은 형태(열 구성·필터·건수 표시)로 후보를 보여 준다
      ⑵ 결과가 0행일 때 **왜 0행인지**를 화면이 가른다 — 후보 부재 / 필터가 결과를 비움 / 연구실 경계. 현행 두 갈래 문면(`ParentPicker.tsx` 축자 「검색 조건에 맞는 데이터가 없어요. 조건을 바꿔 주세요.」 · 「고를 수 있는 연구실 데이터가 아직 없어요.」)보다 넓다
      ⑶ 필터가 어떤 값으로 걸려 있는지 화면에 보이고 한 번에 지울 수 있다
      ⑷ 연구실 경계(RLS) 동작은 바꾸지 않는다.
    evidence: null
    deadline: null
    note: "L4 부수 관측(등재 아님 · 보고만) = `category` 를 한 값이라도 고르면 0행이다 — staging 표본 14행 전부 응답 `category` 가 null. 이것이 화면 결함인지 표본 결함인지는 `[미측정]`. 이 항목과 별개로 다뤄야 한다."
    sources: ["dev-package/reports/issues/2026-09-12-measure-L4.md", "dev-package/prd/specs/2026-09-12-issue-register-hints-parent-picker.md", "dev-package/reports/issues/2026-09-12-ted-decisions.md"]
```

### 1-8. 반영 뒤 확인

```bash
python3 -c "import yaml,sys; d=yaml.safe_load(open('dev-package/work-items.yaml')); ids=[i['id'] for i in d['items']]; print(len(ids), len(set(ids)))"
bash gates/run.sh work-item-consistency
```

---

## 2. `CLAUDE.md §0` — `after_stage2` 괄호와 계수

### 2-1. 현재 (22행 · 실측)

```
2026-09-12 대장 반영 **17항목** ／ 종전 ~~2026-09-10 · 16항목~~ — `BO-2`(계정 목록·비밀번호 재설정·비활성화) 신설(`〈381〉` 회차 · intent `dev-package/intent/2026-09-12-login-backoffice-closeout.md` Q7). <!-- work-items:after_stage2 -->(`BO-1`·`BO-2`·`C1`·`C2`·`C3`·`C3·C4`·`C4`·`DP-1`·`G1b`·`K3`·`K4`·`K5`·`LV-3`·`LV-4`·`P4`·`R2`·`T-1`)<!-- /work-items:after_stage2 -->
```

### 2-2. 개정본 (`PA-T` 를 정렬 순서에 넣고 17 → 18)

- 정렬 자리 = 현재 목록이 `BO-1`·`BO-2`·`C1`…`T-1` 로 이어지는 순서다. `PA-T` 는 `LV-4` 와 `P4` 사이에 든다.

```
2026-09-12 대장 반영 **17항목** ／ 종전 ~~2026-09-10 · 16항목~~ — `BO-2`(계정 목록·비밀번호 재설정·비활성화) 신설(`〈381〉` 회차 · intent `dev-package/intent/2026-09-12-login-backoffice-closeout.md` Q7). ⭑ **⟨증보 2026-09-12 · 버그개선 회차 마감⟩ 18항목** ／ 종전 ~~17항목~~ — `PA-T`(다중 서버 로그인 실패 제한 공유 ＋ 신뢰 프록시 판정) 신설(Ted 판정 ⑪ ⓐ 「대장 항목 등재만 · 미착수」 · 출처 이슈 `#11` · 등재문 `dev-package/reports/issues/2026-09-12-ted-decisions.md`). <!-- work-items:after_stage2 -->(`BO-1`·`BO-2`·`C1`·`C2`·`C3`·`C3·C4`·`C4`·`DP-1`·`G1b`·`K3`·`K4`·`K5`·`LV-3`·`LV-4`·`PA-T`·`P4`·`R2`·`T-1`)<!-- /work-items:after_stage2 -->
```

- 뒤따르는 문장(「— **이 괄호는 게이트 `work-item-consistency` ㈕ 가 대장과 대조한다**(`〈268〉`). **stage 값의 원본은 대장이다**」)은 **무변**이다.
- ⚠ `LV-5` 는 `stage: backlog` 라 이 괄호에 들어가지 않는다.

---

## 3. `dev-package/03-HANDOFF.md`

### 3-1. `§1` 표 행 (BF 묶음 · 삽입 지점)

- 삽입 지점 = `§1` BF 묶음의 마지막 행 뒤. 실측 = `| **BF-12** 지도 타일 회수 루프 …` 행(현재 `BF-13` 행 **다음**에 놓여 있다). 그 행 뒤, `| **G10** …` 행 앞에 아래 4행을 넣는다.
- 행 모양 = `| **<id>** <짧은 이름> | <상태 기호> | <비고 한 줄> |`. 표기 = ✅ 닫힘 · ⬜ 대기(`§1` 머리말).

```markdown
| **BF-14** 등록 카드 기간 안내 문단 배치 통일 (#31) | ✅ | 2026-09-12 R-BUGFIX-260912 L2 · 커밋 `bb3e77d8` · 문면·`data-testid` 무변, JSX 순서 1건 · 근거 `dev-package/prd/rounds/R-BUGFIX-260912.md` |
| **BF-15** 미리보기 64×64 축소본 자리 이동 ＋ 중복 방지 (#26) | ✅ | 2026-09-12 R-BUGFIX-260912 L3 · 커밋 `6afa776a`·`c9e95eb2` · Ted 판정 ⑤ ⓑ · `〈88〉`-3 재판정 등재 `§9 〈N+2〉`(임시 번호) |
| **BF-16** 업로드 이어가기·버리기·분석 중 고지 (#33㉠·#34·#32·#24㉯) | ✅ | 2026-09-12 R-BUGFIX-260912 L1 · 커밋 `b8b4e7e2`·`aa26db94`·`cef275a0`·`1a381310` · 문면 4건은 초안(PRD-34 문면표·PRD-43 자리표 Ted 확정 대기) |
| **BF-17** 미리보기 조작 줄 3화면 ＋ 확장보기 고르개 (#25⑵·#27·#28) | ✅ | 2026-09-12 R-BUGFIX-260912 L3b · 커밋 `ccaf27f6`·`a841d7a1`·`67e25399`·`bf02a0c8`·`f98d09de` · Ted 판정 ⑥ 재확인(지정 예외)·⑦ ⓐ·⑧ · `R-C-2` 규약 개정 등재 `§9 〈N+3〉`(임시 번호) |
```

- `PA-T` 행 = `after_stage2` 묶음(`BO-2` 가 있는 자리) 뒤에 1행.

```markdown
| **PA-T** 다중 서버 로그인 실패 제한 공유 ＋ 신뢰 프록시 판정 | ⬜ | 2026-09-12 등재만 · 미착수(Ted 판정 ⑪ ⓐ) · 출처 이슈 `#11` · `stage: after_stage2` · `CLAUDE.md §0` 괄호 17 → 18 |
```

- ⚠ **`LV-5` 행은 넣지 않는다** — 대장 등재 자체가 Ted 승인 대상이다(위 §1-7).
- ⚠ **미확인** — `§1` BF 묶음의 표 머리(`| WU | 상태 | 비고 |`)가 어느 소제목 아래인지는 실측 앵커가 `|---|---|---|`(BF 묶음 바로 위) 한 줄뿐이다. 반영 시 그 앵커로 자리를 잡는다.

### 3-2. 상단 「최종 갱신 · 현재 단계 · 다음 WU」

- 자리 = 기존 「최종 갱신」 문단 뒤에 ⭑ 증보 1줄을 덧붙인다(파일의 `⟨증보 …⟩` 관행 그대로 · 산문 ≤5줄 · `.claude/rules/colab-rules.md §1-4`).

```markdown
⭑ **⟨증보 2026-09-12 · 버그개선 회차 마감⟩ 최종 갱신 = 2026-09-12 — R-BUGFIX-260912 신규 4 항목(`BF-14`~`BF-17`) 전건 done · 통합 `integration/r-bugfix-260912` tip `f98d09de`(＋등재 커밋) → `main` ff 한 줄 **대기** · 대장 등재만 1건(`PA-T` · 이슈 `#11` · 판정 ⑪ ⓐ) · 등재 `PLAN-SoT §9 〈N+1〉`~`〈N+6〉`(임시 번호 · 병합 직전 재실측).**
**현재 단계** = `main` ff → dev 배포 green ＋ `deploy_doctor` **15/15 를 한 번의 실행으로**(재시도해 모은 15 는 15 가 아니다).
**다음 WU** → 배포 뒤 ⑴ PRD-34 문면표 개정 · PRD-43 자리표 2건에 **Ted 문면 확정**(초안 상수 4건이 그 확정을 기다린다) ⑵ `LV-5` 등재 여부 판정(부모 찾기 창 목록 형태 · 판정 ⑨ ⓐ 의 「신규 항목 후보」) ⑶ 후속 항목 = `#33`㉡ 설계 · `#31` 배치 규약의 정책 문서 기재 · 분류 필터 0행 원인(`[미측정]`).
```

---

## 4. `dev-package/PLAN-SoT.md §9` — 결정 행 6건

- **삽입 지점** = 파일 **마지막 줄**(`〈381〉` 행) 다음. `§9` 는 마크다운 표이고 한 결정 = **한 행**이다(`| 〈N〉 | **제목** | **확정 (…)** … |`). 표 사이에 빈 줄을 넣지 않는다(`CLAUDE.md §5-b`).
- **번호** = 실측 `max-decision.sh` = **381**. 아래 `〈382〉`~`〈387〉` 은 임시 번호이고 **병합 직전 재실측한다** — 다른 레인이 먼저 들어오면 그만큼 밀린다.

### 4-1. 기존 행 1건 (모양 대조용 · 축자)

> `dev-package/PLAN-SoT.md:757` 첫머리 —
> `| 〈381〉 | **계약 동결 해제 서명 — 로그인 혼합 입력 400 (기수용 1건 정리 · 신규 파괴 0) ＋ CI 기준 ref 승격** | **확정 (2026-09-12 · 발의 Ted · 서명 수령 2026-09-12 · 근거 `dev-package/intent/2026-09-12-login-backoffice-closeout.md` `## 확인` 절).** ①서명 축자 = …`
> (…중략 — ②~⑦ 항과 「**역링크** — intent: … · spec: … · 라운드: …」 로 끝난다. 생략한 것은 그 행의 근거 항목 본문이다.)

- 규약 3 = ⓐ 한 행 = 한 결정 ⓑ 항 번호는 `①②③…` ⓒ 행 끝에 「**역링크** — intent: … · spec: … · 라운드: …」.

### 4-2. (a) `〈382〉` — 버그개선 회차 판정 11건

```markdown
| 〈382〉 | **버그개선 회차 판정 11건 — 이슈 `#24`~`#34` 범위 확정(⑥ 재확인 · ⑧ 확정 포함)** | **확정 (2026-09-12 · 판정자 Ted · 확인 문장 축자 「좋아 전부권고안으로」 · 근거 `dev-package/reports/issues/2026-09-12-ted-decisions.md`).** ①입력 = `dev-package/reports/issues/2026-09-12-survey-SUMMARY.md` §4 판정 카드 ①~⑪(번호 일치) · 선택지 기호 ⓐⓑⓒ 는 그 절의 것. ②판정 = ① `#32` 포함(공통 헬퍼 `discardUpload` 추출) · ② 닫기 세 번째 선택지 신설, 뜻 = 이 브라우저에서 감춤(서버 행은 24h 만료 스윕) · ③ `다음 →` 사유 한 줄 고지 ＋ 비활성 유지(정책 6 무변) · ④ `#33` 분리(㉠ 배선 이번 · ㉡ 등록 장면 복원 설계 뒤) · ⑤ ⓑ 64×64 축소본을 지도 자리 밖 접히는 자리로 · ⑥ ⓐ 고르개를 틀 밖 고정 줄로 · ⑦ ⓐ 확대 줄 접힘·가림 해소까지만 · ⑧ ⓐ 소요는 실측 후 지정 · ⑨ ⓐ `#30` 0행 재현 확인만 · ⑩ ⓐ `#29` 재현 후 판정 · ⑪ ⓐ `#11` 대장 등재만. ③**⑥ 재확인(같은 날)** = 확장보기에도 고르개 줄을 신설한다(원문 축자 「니 권곧로 확장보기에서도 추가하다」) — 인라인·상세 2화면 이동 ＋ 확장보기 신설로 **3화면**. 기능 추가분은 **Ted 지정 예외**이므로 편의 기능 유예 규칙(`.claude/rules/colab-rules.md §6-2`)의 예외로 기록한다. ④**⑧ 확정(같은 날 · staging 실측 뒤)** = 별도 행 `〈386〉`. ⑤**미리보기 spec v2 승인**(원문 축자 「모두 권고대로」) = `dev-package/prd/specs/2026-09-12-issue-preview-controls-v2.md` · 6단계 계획 채택 · 우려 6건 권고 채택 · 축소본 중복 방지 규칙은 판정 ⑤ ⓑ 의 보강. ⑥판정 재개봉 성격 = 5건(②③⑤⑥⑩) · 레인 절단이 종속된 것 = 2건(①④). ⑦미반영 상충 1건 = 취합본 §2 `/grill-me` 세션 ② 가 열거한 「`#31` 문면 삭제」에 대응하는 판정 카드가 ①~⑪ 에 **없다** — 문면 유지 · 위치 통일로 작성했다. ⑧이번에 세지 않은 축 = 이슈 첨부 화면의 커밋 sha·뷰포트 폭·환경(`[미확인]` · `#29`·`#30` 두 건 공통). **역링크** — 라운드: `dev-package/prd/rounds/R-BUGFIX-260912.md` · 판정: `dev-package/reports/issues/2026-09-12-ted-decisions.md` · intent: `dev-package/intent/2026-09-12-issue-{upload-resume-discard,upload-analysis-notice,preview-controls,register-hints-parent-picker}.md` |
```

### 4-3. (b) `〈383〉` — `〈88〉`-3 보강

```markdown
| 〈383〉 | **`〈88〉`-3 보강 — 64×64 축소본은 지도 자리 밖 접히는 자리에 두고, 중복은 조건으로 막는다** | **확정 (2026-09-12 · Ted 판정 ⑤ ⓑ ＋ 미리보기 spec v2 승인 · 대장 `BF-15` · 근거 `dev-package/reports/issues/2026-09-12-ted-decisions.md`).** ①**`〈88〉`-3 을 반전하지 않는다** — 축소본의 **표시 목적은 유지**하고 **자리만** 옮긴다. 지도 자리(`.mapcanvas`) 위 중복 표시만 제거한다. ②새 자리 = 접히는 설정 자리(`up-preview-options` details 안 · `up-thumb-img` 옆). ③**중복 방지 규칙(신설)** = 대표 그림을 **골랐을 때만** 자동 축소본을 그 옆에 대조용으로 세운다. 고른 그림이 없으면 기존대로 **한 장**이다. 근거 = spec v2 승인(원문 「모두 권고대로」) · 판정 ⑤ ⓑ 의 보강. ④집행 = 커밋 `6afa776a`(자리 이동) · `c9e95eb2`(중복 방지) · 통합 `integration/r-bugfix-260912`. ⑤판정 수단 = jsdom 이 레이아웃을 계산하지 않으므로 ㈎ DOM 조상·형제 관계 ㈏ **주석을 제거한 뒤** 잰 CSS 원문 계측 두 가지(`CLAUDE.md §5-b` 정적 계측기 오탐 3건 선례). ⑥이번에 세지 않은 축 = 실제 브라우저 렌더 위치(잰 것은 DOM 관계와 CSS 원문까지 · `[미측정]`) · `frontend-visual` 실행 여부는 레인 보고에 따른다. **역링크** — spec: `dev-package/prd/specs/2026-09-12-issue-preview-controls-v2.md` · 라운드: `dev-package/prd/rounds/R-BUGFIX-260912.md` |
```

### 4-4. (c) `〈384〉` — `R-C-2` 규약 개정 ＋ 확장보기 고르개 신설

```markdown
| 〈384〉 | **`R-C-2` 「틀 안 컨트롤 줄」 → 「틀 위 고정 줄」 개정 ＋ 확장보기 고르개 신설(Ted 지정 예외)** | **확정 (2026-09-12 · Ted 판정 ⑥ ⓐ ＋ 같은 날 재확인 · 대장 `BF-17` · 근거 `dev-package/reports/issues/2026-09-12-ted-decisions.md`).** ①개정 = 파일·변수·시각 고르개의 자리를 `.pv-frame` **안**에서 **밖(틀 위 고정 줄)**으로 바꾼다. 근거 = 그림 렌더 후에도 고르개가 계속 보여야 한다(`#25`⑵). ②문면 개정 대상 2곳 = 부품 머리 주석 `frontend/src/components/preview/PreviewPickRow.tsx` 축자 「틀 안의 컨트롤 줄」 · 라운드 파일 `dev-package/prd/rounds/R-C-2-frontend.md` 의 해당 축자. 같은 커밋(`f98d09de`)에 넣었다. ③적용 화면 = **3화면** — 업로드 인라인(`PreviewPanel.tsx`) · 상세(`datasetpreview/DatasetPreviewSection.tsx`) · **확장 오버레이(`PreviewExpandOverlay.tsx` · 신설)**. ④**확장보기 신설은 기능 추가**이므로 편의 기능 유예 규칙(`.claude/rules/colab-rules.md §6-2`)의 **Ted 지정 예외**로 기록한다 — 원문 축자 「니 권곧로 확장보기에서도 추가하다」 · 판정 근거는 `#29` 원문 「미리보기 확장에서 달력에서 고르기」. ⑤제약 = 선택 상태는 인라인 미리보기와 **공유**하고 새 상태 저장소를 신설하지 않는다. ⑥`#27`＋`#28` = 접힘·가림 해소까지만(판정 ⑦ ⓐ) — `.modal-b.pvx-b` flex 방향 · `.pv-layers .pv-tile` 폭 상한 · 버튼 글자 줄바꿈 금지. **고정 배치 재설계는 범위 밖**이고 세 화면 공유 규약(`WU-C4` 완료 정의)은 유지한다. ⑦집행 = 커밋 `ccaf27f6`·`a841d7a1`(2화면 이동) · `67e25399`(확장보기 고르개 ＋ 「그리는 중」 표시) · `bf02a0c8`(#27·#28) · `f98d09de`(규약 문면). ⑧이번에 세지 않은 축 = 실제 브라우저에서의 겹침 재측정(`[미측정]`) · `frontend-visual` 은 세 화면 주소를 `COLAB_VISUAL_URLS` 로 선언할 수 있을 때만 실행. **역링크** — spec: `dev-package/prd/specs/2026-09-12-issue-preview-controls.md`·`…-v2.md` · 라운드: `dev-package/prd/rounds/R-BUGFIX-260912.md`·`dev-package/prd/rounds/R-C-2-frontend.md` |
```

### 4-5. (d) `〈385〉` — PRD-34 문면표 개정 ＋ PRD-43 자리표 2건

```markdown
| 〈385〉 | **PRD-34 문면표에 세 번째 선택지 1행 증설 ＋ PRD-43 자리표 2건 신설 — 문면은 초안, Ted 문면 확정: `<대기 / 확정일 YYYY-MM-DD>`** | **초안 (2026-09-12 · 발의 = 개발 세션 · 승인 = 미승인 · 근거 `dev-package/prd/rounds/R-BUGFIX-260912.md` 「문면 취급」).** ①**개발 세션이 문면을 확정하지 않는다** — PRD-34 축자 「축차 확정 시점 … **개발 세션이 새로 짓지 않는다**」. rev2 원문(`10_적용전/업로드_계보_260905_rev2_이태헌.html`)에 세 번째 선택지에 대응하는 문장이 **없어** 초안을 적었다. ②PRD-34 개정 3건 = ㈎ 문면표에 행 1개 증설(상황 「이 브라우저에서 감추기」) ㈏ 버튼 라벨 줄에 세 번째 라벨 병기 ㈐ 수용 기준 1행 증설. 상세는 아래 §5. ③PRD-43 자리표 = 21행 표에 **2행 신설**(업로드 장면1 · 사유 줄 / 경과 시간). 확정 전까지 `COPY_ROW_IDS`·`COPY_ROWS`·`FIXED_COPY` 에 **등재하지 않는다** — 등재하면 21행 표가 확정되지 않은 문면을 담는다. ④초안 상수 4건(`frontend/src/components/common/toastCopy.ts`) = `UPLOAD_CLOSE_FORGET` 축자 「이 브라우저에서 감추기」 · `UPLOAD_CLOSE_FORGET_NOTE` 축자 「이 브라우저에서 감추면 올리다 만 기록이 이 브라우저에서만 사라져요. 서버에 접수된 것은 24시간 뒤 저절로 정리돼요.」 · `REG_OPEN_ANALYZING_REASON` 축자 「분석이 끝나면 다음으로 갈 수 있어요.」 · `analyzeElapsed(seconds)` 축자 `` `${seconds}초 경과` ``. 각 상수 위에 대기 주석(`// PRD-34 문면표 개정 · Ted 확정 대기` · `// PRD-43 자리표 등재 · Ted 확정 대기`)이 붙어 있다. ⑤뜻의 근거 = 세 번째 선택지는 **`forgetPending` 1회 · 서버 호출 0**이고 서버 접수 행은 24시간 만료 스윕이 정리한다(판정 ②). 즉시 삭제 창구는 계약 개정이라 범위 밖이다. ⑥**이 행은 문면 확정이 아니다** — Ted 확정 전에는 초안으로 인용한다. **역링크** — 문면표: `dev-package/prd/PRD-260905-적용전기획.md` `#### PRD-34` · 자리표: 같은 파일 `#### PRD-43` · 라운드: `dev-package/prd/rounds/R-BUGFIX-260912.md` |
```

### 4-6. (e) `〈386〉` — 판정 ⑧ 소요 수용 (실측값)

```markdown
| 〈386〉 | **분석·렌더 소요 합격선 = 수용(성능 작업 0) ＋ 「동작 중」 표시 보강 — staging 실측 4벌** | **확정 (2026-09-12 · Ted 판정 ⑧ ⓐ → 지정 완료 · 원문 축자 「받아들일게 근데 띄워줌에서 사용자에게 이게 동작중임을 보여주길바란다」 · 근거 `dev-package/reports/issues/2026-09-12-measure-L4.md`).** ①환경 = **staging**(로컬 `infra/staging/compose.i2.yml` · 이미지 태그 `cbb9ff1406c5` · 표면 `https://www.colab-hydro.com`) · 측정 창 UTC `2026-09-12T07:39Z`~`08:00Z` · 컨테이너 8/8 healthy · 헬스 6종 200. **dev 값이 아니다.** ②표본 = `gk2a_ami_le2_lst_ko_2020050100*.nc` 계열 · 조각 **141** · **49,997,946 B**(≈47.7 MiB · `du -cshb` 실측). ③값 = 워커 분석 **39.761 s**(1회차) · **41.450 s**(2회차) / viz 렌더 **69.782 s**(1회차) · **73.229 s**(2회차). 대조(조각 1) = 분석 5.723 s · 렌더 2.756 s. ④**계수 기준** = ㈎ 「접수 수락」은 `POST /uploads` 의 **201 을 클라이언트가 받은 시각**이고 바이트 전송 구간은 **불산입**(1회차 전송 19.075 s 는 별도) ㈏ 「viz 렌더」의 종료 사건은 **그림 바이트를 받은 시각**이며 상태가 `완료` 로 바뀐 시각까지는 1회차 69.242 s · 2회차 72.864 s. ⑤내역 = 워커는 고정 지연 순회(`services/pipeline-worker/src/colab_pipeline/app/worker.py` 함수 `serve` 기본 인자 `interval_seconds: float = 5.0` · 실측 간격 5.03 s) ⟹ 순회 대기 1회차 4.03 s · 2회차 2.07 s. 화면 폴링 1000 ms 의 몫 = 0.81 s / 0.17 s(상한 = 폴링 주기 1 s). ⑥**판정 = 소요를 수용한다. 성능 작업 없음.** 대신 **분석·그리기 동안 「동작 중」임을 화면이 보여 준다** — 분석 중 칩 활동 표시(CSS · `prefers-reduced-motion` 존중) · 클라이언트 경과 시간 `N초 경과` · 사유 줄(커밋 `1a381310`) · 오버레이 「그리는 중」(커밋 `67e25399`). 상태 응답에 진행 수치가 없어 **조각 진행률은 표시하지 않는다**(계약 변경 0). ⑦`PLAN-SoT §9 〈241〉` p95 와 `gates/config/render-latency.toml` 눈금을 합격선으로 **유도하지 않는다** — 전자는 분포 통계이자 다른 산출물(NDVI)의 값이다. ⑧이번에 세지 않은 축 = **10 조각 표본 `[미측정]`**(spec 요구 3벌 중 1·141 만 수행) · 「순차 자재화」와 「형식 판별」의 몫을 가르지 못함 `[미측정]`(워커가 한 순회에 `worker.pass.completed` 한 줄만 낸다) · dev 환경 값 `[미측정]` · staging 저장 모드 값 `[미확인]`. ⑨상태 조회 오류 경로 = **0회**(상태 폴링 29회 · 렌더 폴링 96·100회 · 오류 0). **역링크** — 보고: `dev-package/reports/issues/2026-09-12-measure-L4.md` · 원본 기록: `dev-package/reports/issues/l4/run-p141-1.json`·`…-2.json` · 라운드: `dev-package/prd/rounds/R-BUGFIX-260912.md` |
```

### 4-7. (f) `〈387〉` — `#29` · `#30` 종결 근거

```markdown
| 〈387〉 | **`#29`(확장보기 기간 입력 겹침) 재현 안 됨 · `#30`(부모 찾기 0행) 사용법 — 코드 변경 0으로 닫는다** | **확정 (2026-09-12 · Ted 판정 ⑩ ⓐ·⑨ ⓐ 의 「재현 후 판정」 집행 · 근거 `dev-package/reports/issues/2026-09-12-measure-L4.md` §4).** ①`#29` 방법 = staging 표면 · `agent-browser` 0.27.0 · 뷰포트 2벌 고정(**1440×900**(≥1280) · **900×800**(≤1023)) · 판정 수단 ㈎ 스크린샷 ㈏ 확장 오버레이 DOM 텍스트 조회. ②`#29` 값 = 확장 오버레이 안의 기간 문면이 **두 폭 모두 없음**. DOM 텍스트 전량 = `미리보기`·`×`·`확대`·`축소`·`기본 배율로` 다섯 줄뿐. 스크린샷 `dev-package/reports/issues/l4/29-expand-1440x900.png`·`29-expand-900x800.png`·`29-inline-1440.png`. ③`#29` 판정 = **재현 안 됨**(태그 `cbb9ff1406c5` staging). 확장보기 시점 선택 요구는 판정 ⑥ 의 확장보기 고르개 신설(`〈384〉`)로 충족된다. `[미확인]` = 이슈 첨부 화면의 커밋 sha·뷰포트 폭·환경 — 그 기록이 없어 「이미 고쳐졌다」와 「다른 조건에서만 난다」를 가르지 못한다. ④`#30` 방법 = `GET /api/v1/lineage-candidates` 6벌 조회(스크립트 `dev-package/reports/issues/l4/probe_d.py`) ＋ 원장 읽기 질의 3건(쓰기 0). ⑤`#30` 값 = 필터 없음 **14행** · 자기 제외 13행 · 주제 1값 9행 · 가공 단계 0 → 9행 · 가공 단계 1 → 5행 · **분류 1값 → 0행**. 같은 주체의 `GET /datasets?limit=100` `totalCount` **14** · 원장 `select lab_id, count(*) from d3_dataset group by 1;` → `…HYMETS | 14` 한 행. ⑥`#30` 판정 = **사용법** — 조회 결함 아님. 신규 `BF-` 등재 대상 아님. 0행이 나오는 자리 둘 = ㈎ 후보 0건인 연구실(「임시 연구실」 · 원장 0행)로 로그인 ㈏ `category` 필터(staging 14행 전부 응답 `category` 가 null). `[미확인]` = 이슈 첨부 화면의 환경·계정. ⑦**후속(등재 아님 · 보고만)** = 분류 필터가 항상 0행을 내는 상태 — `category` 를 응답에 채우는 자리가 없는지, staging 표본에만 없는지는 `[미측정]`. ⑧화면 형태 재구성은 **신규 항목 후보**이고(판정 ⑨ ⓐ) 등재 여부는 Ted 판정 대상이다(제안 `LV-5`). ⑨연구실 경계(RLS) 동작은 관찰만 했고 바꾸지 않았다. **역링크** — 보고: `dev-package/reports/issues/2026-09-12-measure-L4.md` · 라운드: `dev-package/prd/rounds/R-BUGFIX-260912.md` |
```

---

## 5. PRD 문서 (초안 · 개발 세션이 확정하지 않는다)

### 5-1. 자리

| 대상 | 파일 | 앵커 |
|---|---|---|
| PRD-34 문면표 | `dev-package/prd/PRD-260905-적용전기획.md` | `#### PRD-34 · 업로드 종료 확인 모달의 문면 — **채택 (미결-r2-2 ⓐ · Ted 2026-09-06)**` |
| PRD-43 자리표 | 같은 파일 | `#### PRD-43 · 공통 토스트 한 개와 문면 21행` |

- `policy-map` 후보(`dev-package/reports/upload-layout-preview/policy-map.md`)는 이 두 표를 담지 않는다 — 문면표·자리표의 자리는 위 한 파일뿐이다.

### 5-2. PRD-34 — 문면표에 1행 증설

- 현재 표(3행 · 축자) 뒤에 1행을 붙인다. 기존 3행은 무변.

```markdown
| 이 브라우저에서 감추기 | 접수 완료 행이 1건 이상 | 이 브라우저에서 감추면 올리다 만 기록이 이 브라우저에서만 사라져요. 서버에 접수된 것은 24시간 뒤 저절로 정리돼요. (⚠ 초안 · Ted 문면 확정: `<대기>`) |
```

### 5-3. PRD-34 — 버튼 라벨 줄 개정

- 현재 축자 = 「**버튼 라벨** — `계속 작성` 을 `계속하기` 로 바꾼다. `닫고 나가기` 는 유지한다.」
- 개정본 —

```markdown
- **버튼 라벨** — `계속 작성` 을 `계속하기` 로 바꾼다. `닫고 나가기` 는 유지한다. ⭑ ⟨증보 2026-09-12 · `#34`⟩ **세 번째 라벨 `이 브라우저에서 감추기` 를 더한다** — 지울 기억(접수 완료 행)이 있을 때만 낸다. ⚠ 초안이다 — rev2 원문에 대응 문장이 없어 개발 세션이 적었고 **Ted 문면 확정: `<대기>`** 다.
```

### 5-4. PRD-34 — 수용 기준 1행 증설

```markdown
  - Given 접수 완료 행 1건 ＋ 닫기 확인 모달, When 세 번째 버튼 클릭, Then 이 브라우저의 미완결 기억만 지워지고 **서버 호출은 0회**다(서버 접수 행은 24시간 만료 스윕이 정리한다).
```

### 5-5. PRD-43 — 자리표 2행 신설

- 표의 `| 업로드 장면1 | U-14 | …` 묶음 안, `U-17` 행 뒤에 2행을 붙인다.

```markdown
| | U-18 | 등록 결정 사유 `분석이 끝나면 다음으로 갈 수 있어요.` (⚠ 초안 · Ted 문면 확정: `<대기>`) |
| | U-19 | 분석 중 경과 `N초 경과` — 클라이언트 벽시계 보간값. 조각 진행률·퍼센트를 쓰지 않는다 (⚠ 초안 · Ted 문면 확정: `<대기>`) |
```

- ⚠ 행 번호 `U-18`·`U-19` 는 **제안**이다 — 기존 표의 행 코드가 자리별 연번(`U-14`·`U-17`)이라 그 규칙을 따랐고, 실제 채번은 문면 확정 시 정한다.
- 수용 기준 「21행이 전부 코드에 있고 하드코드 중복이 0건」의 **21 → 23** 개정이 같이 필요하다. 확정 전에는 고치지 않는다(현재 초안 상수 4건이 `COPY_ROWS` 에 미등재이므로 21행 검사는 그대로 성립한다).

---

## 6. GitHub 이슈 종결 문안 (초안 · 게시 여부는 Ted)

- 대상 12건. `CognileapAI/colab-v2` · sha 는 통합 브랜치 `integration/r-bugfix-260912` 기준이고 **`main` ff 뒤에 게시한다**.

**#24 — 분석·렌더 소요와 분석 중 고지**
```
소요를 실측해 받아들이기로 했습니다(141조각 · 분석 39.8/41.5초 · 렌더 69.8/73.2초, staging 실측). 성능 작업은 하지 않습니다.
대신 기다리는 동안 화면이 동작 중임을 보여 줍니다 — 분석 중 칩에 움직임과 「N초 경과」가 붙고, 비활성인 `다음 →` 옆에 이유 한 줄이 섭니다(1a381310). 그림을 그리는 동안에는 확장보기에 진행 표시가 뜹니다(67e25399).
실측 근거는 dev-package/reports/issues/2026-09-12-measure-L4.md 입니다.
```

**#25 — 미리보기 조작 줄과 렌더 소요**
```
고르개 줄(파일·변수·시각)을 그림 틀 밖 고정 줄로 옮겼습니다. 그림을 그린 뒤에도 고르개가 계속 보입니다 — 업로드 인라인·데이터셋 상세 두 화면(ccaf27f6 · a841d7a1)에 더해 확장보기에도 같은 줄을 새로 세웠습니다(67e25399).
렌더 소요(⑴)는 실측 뒤 받아들이는 것으로 정리했고, 대신 그리는 동안 진행 표시가 뜹니다.
```

**#26 — 그림 위 64×64 축소본**
```
축소본을 지도 자리에서 빼고 접히는 설정 자리(대표 그림 옆)로 옮겼습니다(6afa776a). 표시 자체는 유지하고 그림 위 중복만 없앴습니다.
덧붙여 대표 그림을 직접 고른 경우에만 자동 축소본을 그 옆에 대조용으로 세웁니다 — 고른 그림이 없으면 예전처럼 한 장입니다(c9e95eb2).
```

**#27 — 확대 줄이 접힌다**
```
인라인 미리보기에서 확대 줄이 스크롤 없이 보이도록 세로 배분을 고쳤고, 버튼 글자가 세로로 접히지 않게 줄바꿈을 막았습니다(bf02a0c8).
자리 자체를 다시 설계하는 것은 이번 범위 밖입니다 — 접힘·가림 해소까지입니다.
```

**#28 — 확대 줄이 가려진다**
```
확장보기 본문의 배치 방향과 조각 폭 상한을 고쳐 확대 줄이 가려지지 않게 했습니다(bf02a0c8).
#27 과 한 단계로 처리했습니다. 고정 배치 재설계는 범위 밖입니다.
```

**#29 — 확장보기 기간 입력 겹침**
```
재현되지 않아 닫습니다. staging(태그 cbb9ff1406c5)에서 뷰포트 1440×900 과 900×800 두 벌로 확장보기를 열었고, 오버레이 안에 기간 입력 문면이 아예 없었습니다(dev-package/reports/issues/2026-09-12-measure-L4.md §4-1, 스크린샷 3장 첨부).
확장보기에서 시점을 고르고 싶다는 요구는 이번에 신설한 확장보기 고르개 줄로 충족됩니다(67e25399). 첨부 화면의 커밋·뷰포트 폭 기록이 있으면 다시 열겠습니다.
```

**#30 — 부모 찾기 창 결과 0행**
```
조회 결함이 아니라 사용법으로 확인돼 닫습니다. 필터를 비운 조회는 14행을 돌려줍니다(같은 연구실 데이터셋 원장 건수도 14).
0행이 나오는 자리는 둘이었습니다 — ⑴ 데이터가 0건인 연구실 계정으로 로그인한 경우 ⑵ 「분류」 필터를 고른 경우(현재 표본은 분류 값이 전부 비어 있습니다). 근거는 dev-package/reports/issues/2026-09-12-measure-L4.md §4-2 입니다.
창을 목록 화면 형태로 다시 만드는 것은 별도 항목 후보로 올렸습니다.
```

**#31 — 등록 카드 설명문 배치**
```
기간 칸의 안내 문단을 달력 열기 버튼 뒤로 옮겨, 카드 안 배치를 「라벨 → 컨트롤 → 설명문」 하나로 통일했습니다(bb3e77d8).
문면과 문단 자체는 그대로 둡니다 — 삭제는 이번 범위가 아닙니다.
```

**#32 — 올리다 만 것 버리기**
```
메인 화면 배너의 접수 완료 행마다 버리기 버튼을 뒀습니다(cef275a0). 창을 열지 않고 그 자리에서 정리할 수 있고, 다 버리면 배너 카드가 사라집니다.
등록을 마친 데이터셋에는 닿지 않습니다.
```

**#33 — 이어서 하기**
```
㉠ 전송이 덜 끝난 건은 고쳤습니다 — 배너에서 「이어서 하기」를 누르면 그 건을 집은 채로 업로드 창이 열립니다(b8b4e7e2).
㉡ 접수까지 끝난 건의 등록 화면을 되살리는 것은 새 설계가 필요해 이번 범위 밖입니다. 별도로 다룹니다.
```

**#34 — 닫기 확인 선택지**
```
닫기 확인에 세 번째 선택지 「이 브라우저에서 감추기」를 더했습니다(aa26db94). 누르면 이 브라우저에 남은 올리다 만 기록만 사라지고, 서버에 접수된 것은 24시간 뒤 저절로 정리됩니다 — 확인 창 문면이 그 사실을 그대로 말합니다.
서버에서 즉시 지우는 창구는 계약 개정이라 이번 범위 밖입니다. 문면은 아직 초안이고 확정 뒤 바뀔 수 있습니다.
```

**#11 — 다중 서버 로그인 실패 제한 (닫지 않는다 · 등재 안내 댓글)**
```
남은 일 목록에 항목으로 세웠습니다(PA-T · 세 번째 단계 · 미착수). 서버를 여러 대로 늘릴 때 로그인 실패 제한을 서버들이 함께 세도록 하는 것과, 어느 앞단까지 신뢰할지 정하는 것 두 가지입니다.
현재 한 대 운용에서는 자격·클라이언트 각각 5회/15분 · 성공 시 초기화로 동작합니다. 이슈는 열어 둡니다.
```

---

## 7. `planning-applied` — 해당 없음

- 판정 = **아니요.** `python3 dev-package/tools/planning-applied.py --sync` 는 이 회차에 실행하지 않는다.
- 근거 = 이 회차의 입력은 GitHub 이슈 10건 · Ted 판정 11건 · intent 4건 · spec 5건이고, `40 COLAB-기획/10_적용전/` 의 기획자 문서를 **소비한 라운드가 아니다**. 게이트 `planning-freshness` 는 ㈎ 병합된 라운드의 기획 문서가 `30_적용완료/<라운드>/` 에 사본으로 있는지 ㈏ 사본이 매니페스트에 등재됐는지를 본다(`.claude/rules/colab-rules.md §7`) — 소비한 기획 문서가 0건이므로 대조 대상이 생기지 않는다.
- 라운드 파일 `dev-package/prd/rounds/R-BUGFIX-260912.md` 「병합·원장」 절의 기재 대상 목록에도 `planning-applied` 가 없다.
- 병합 뒤 실행할 게이트 = `work-item-consistency` 1회(대장 ＋ `CLAUDE.md §0` 괄호 대조 · 판정 ⑪ 조건).

---

## 8. 반영 순서 (오케스트레이터 · 직렬)

1. `bash dev-package/prd/tools/max-decision.sh` **재실측** → `〈382〉`~`〈387〉` 를 실측값+1..+6 으로 일괄 치환(브랜치 전 파일 · `main` 쪽 같은 번호 인용은 무수정).
2. `grep -o "id: BF-[0-9]*" dev-package/work-items.yaml | sort -t- -k2 -n | tail -1` **재실측** → `BF-14`~`BF-17` 확인.
3. 레인 `gate-summary.json` 4건에서 3계수·요약줄 축자를 읽어 `<green N / …>` 플레이스홀더를 채운다.
4. 대장 → `CLAUDE.md §0` → `03-HANDOFF.md` → `PLAN-SoT.md §9` 순서(상태 변경은 대장 먼저 · `CLAUDE.md §6`).
5. `bash gates/run.sh work-item-consistency` 1회 green.
6. PRD 2건은 **Ted 문면 확정 뒤** 별도 커밋. `LV-5` 는 Ted 승인 뒤 별도 커밋.
7. 이슈 댓글은 `main` ff 뒤 Ted 결정에 따라 게시.

---

## 9. 미결·미확인

| 항목 | 상태 | 해소 방법 |
|---|---|---|
| 레인 게이트 3계수 4건 | `[미확인]` — 요약 파일이 이 워크트리·`git ls-files` 양쪽에 없다 | 본 체크아웃의 `dev-package/reports/bugfix-260912/{L1,L2,l3,L3b}/gate-summary.json` 실물에서 읽는다 |
| 통합 트리 전수 게이트 1회 결과 | `[미확인]` — 실행 중 | 요약줄 축자를 `〈382〉` ⑧항 또는 별도 집행 행에 기재 |
| `03-HANDOFF §1` BF 묶음 표 머리의 소제목 | `[미확인]` — 실측 앵커가 `|---|---|---|` 한 줄 | 반영 시 `BF-12` 행 앵커로 자리를 잡는다 |
| PRD-43 신설 행 코드 `U-18`·`U-19` | 제안 | 문면 확정 시 채번 |
| `LV-5` 등재 여부 | Ted 판정 대기 | 판정 ⑨ ⓐ 는 「신규 항목 후보」까지다 |
| 분류 필터 0행 원인 | `[미측정]` | 후속 항목 |
| 10 조각 표본 소요 | `[미측정]` | 후속 회차(필요 시) |
