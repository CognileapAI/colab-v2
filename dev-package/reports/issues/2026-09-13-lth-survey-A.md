# 이태헌 1차 검증 — 조사 A (상단 셸 · 검색 · 로그인)

- 입력 = `dev-package/reports/issues/2026-09-13-lth-review-1-raw.md`
- 트리 = 워크트리 `worktree-lth-review-260913` · HEAD `2e45ce9a` · dev 배포 sha `6ff0eecd`(코드 동일)
- 대상 항목 = `D-1` · `D-5` · `I-9` · `I-2` · `I-7`
- 방법 = 코드 읽기 전용 대조. 브라우저 재현·DB 조회 미실시 → 해당 값은 `[미확인]`
- 인용 위치는 행 번호 대신 앵커 문자열(레포 규약)

---

## D-1 전체 연구실 (읽기 전용) 버튼 무반응

### 1. 재현/확인
- 확인 결과 = 코드로 확인됨. 해당 요소에 `onClick` 이 없다.
- 근거 `frontend/src/shell/Gnb.tsx` 앵커 `data-testid="lab-switcher"`
  > `<button type="button" className="labswitch" data-testid="lab-switcher"`

  이어지는 속성은 `aria-label` 하나뿐 — `onClick`·`aria-expanded`·`aria-haspopup`·`disabled` 없음.
- 근본 원인 = 이 자리는 표기 전용으로 설계됨. 같은 파일 주석 축자 —
  > `전환 목록·동작은 P0 범위 밖이라 자리만 둔다.`

  > `⚠ **특정 연구실 하나로 좁히는 동작은 아직 없다.** 좁히려면 읽기 op 들이 연구실 인자를 받아야 하고, 그것은 「경계는 요청에서 오지 않는다」(CLAUDE.md §3-5)를 건드리는 계약 판정이다 — 그래서 여기서 `▾` 를 달지 않는다. 달면 없는 동작을 약속하게 된다.`
- `[추론]` 요소가 `<button>` 이라 포커스·눌림 효과가 발생하고, 그것이 「눌렸는데 아무 일 없음」으로 관찰된다. `▾` 는 제거됐으나 `button` 역할 자체가 동작을 약속한다.

### 2. 의도 대조
- 의도 기록 = 위 주석이 「동작 없음」을 명시. 관리자 전 연구실 읽기는 승인 intent 근거로 표기만 변경(주석 축자 `승인 intent 2026-09-12`).
- 대장 항목 = `BO-3` · `status: done` · `stage: after_stage2` (`dev-package/work-items.yaml` 앵커 `id: BO-3`).
- **전환 동작은 `BO-3` 범위 밖으로 이미 명시됨** — 같은 블록 `note:` 축자
  > `범위 밖 = 특정 연구실 하나로 좁히는 전환 동작(읽기 op 이 연구실 인자를 받아야 하므로 계약 판정이 선행한다)`
- 같은 블록 `completion_def:` ⑷ 축자 = `관리자가 모든 연구실의 데이터를 읽기 전용으로 열람한다` → 전 연구실 일괄 읽기가 완료 정의이고 선택 동작은 정의에 없다.
- 같은 블록 `note:` 가 실동작 미확인을 이미 적재 = 축자 `⚠ `[미확인]` = 로그인한 상태의 관리자 토글·전 연구실 열람 실동작(Ted 실사용 확인 대기)` → 이 피드백이 그 확인분에 해당.
- 판정 상태 = 전환 동작은 **신규 판정 대상**(기존 결정이 「범위 밖 ＋ 계약 판정 선행」으로만 닫아 둠).
- 현재 동작은 의도대로. 버튼 모양이 의도와 어긋난다.

### 3. 원인 분류
- **설계 차이 ＋ 표기 결함** — 범위(전환 동작 없음)는 설계대로, 요소 역할(`button`)이 없는 동작을 약속하는 점은 결함.

### 4. 수정 범위 추정
- 칩화안 = `frontend/src/shell/Gnb.tsx` · `frontend/src/shell/shell.css`(`.labswitch`) · `lab-switcher` 참조 테스트. 계약 무변경 · 파괴 없음 · **S**.
- 전환 목록 구현안 = 읽기 op 에 연구실 인자 추가 → `contracts/` 개정 ＋ `services/core-api/src/colab_core/kernel/scope.py`·`app/deps.py` 변경. 계약 파괴 가능 · **L**. 선행 조건은 `BO-3` `note:` 가 적은 「계약 판정」이다.

### 5. 판정 질문
- 사용자가 보는 것 = 상단의 「전체 연구실 (읽기 전용)」이 ⓐ 누를 수 없는 상태 표시로 바뀐다 ⓑ 누르면 연구실 목록이 열리고 한 곳만 골라 본다.
- 두 갈래의 대가 = ⓐ 화면 한 곳과 스타일만 고치고, 관리자는 계속 전 연구실을 한꺼번에 본다. ⓑ 조회 범위를 요청이 지정하는 구조로 바꿔야 하므로 서버 계약과 경계 규칙을 다시 정한다.
- 권고 = ⓐ 즉시 집행, ⓑ 는 관리자 기능 묶음에서 별도 판정.

---

## D-5 내 계정 · 〈이름〉 버튼 무반응

### 1. 재현/확인
- 확인 결과 = 코드로 확인됨. `onClick` 없음 ＋ 펼침 화살표 존재.
- 근거 `frontend/src/shell/Gnb.tsx` 앵커 `data-testid="gnb-avatar"`
  > `<button type="button" className="avatar" data-testid="gnb-avatar" aria-label={`내 계정 · ${account?.name ?? ''}`}>`

  내부에 `<span className="cv" aria-hidden="true">▾</span>` 존재.
- 같은 파일 직전 주석 축자 = `아바타 — 현재 사용자·역할·계정. 드롭다운 내용은 P0 범위 밖`
- 로그아웃은 별 버튼으로 분리 = 같은 파일 앵커 `data-testid="gnb-logout"`(주석 근거 `PLAN-SoT §9 〈90〉-㉳`).
- `[추론]` 같은 파일이 연구실 전환기에는 「`▾` 를 달지 않는다」를 규칙으로 적었으나 아바타에는 적용되지 않음 — 파일 내부 규칙 불일치.

### 2. 의도 대조
- 의도 기록 = 「드롭다운 내용은 P0 범위 밖」 = 미구현 의도 존재.
- 대장 항목 = `[미확인]` — 해소 = `grep -n "아바타\|avatar\|계정 메뉴" dev-package/work-items.yaml`.
- 동작 부재는 의도대로, `▾` 는 레포 자신이 금지한 표기.

### 3. 원인 분류
- **결함(표기)** ＋ 동작 자체는 **미구현**(대장 등재 `[미확인]`).

### 4. 수정 범위 추정
- 최소안 = `frontend/src/shell/Gnb.tsx` 에서 `<span className="cv">▾</span>` 제거 ＋ `button` 을 표기 요소로 변경, `frontend/src/shell/shell.css` `.avatar .cv` 정리, `gnb-avatar` 참조 테스트 수정. 계약·core-api 무변경 · **S**.
- 메뉴 구현안 = 아바타 드롭다운(내 계정·로그아웃·설정 도달) 신설 · `frontend` 한정 · **M**.
- 적용 범위 = 데스크톱 한정. 390px 에서는 아바타가 숨는다 — `frontend/src/shell/design-system.css` 앵커 `.colab-ui .gnb .avatar { display: none; }`(`@media (max-width: 640px)` 블록).

### 5. 판정 질문
- 사용자가 보는 것 = ⓐ 이름 옆 화살표가 없어지고 단순 사용자 표시가 된다 ⓑ 누르면 내 계정·로그아웃이 담긴 메뉴가 열린다.
- 두 갈래의 대가 = ⓐ 즉시 가능하고 계정 동작은 계속 상단 개별 버튼으로 남는다. ⓑ 상단 버튼 수가 줄어 휴대전화에 유리하나 새 메뉴 부품과 키보드·포커스 동작을 함께 만든다.
- 권고 = ⓐ 즉시 적용, ⓑ 는 모바일 상단 정리(`I-9`)와 한 묶음으로 판정.

---

## I-9 모바일 390px 상단 아이콘에 글자 없음

### 1. 재현/확인
- 확인 결과 = 코드로 확인됨.
- 라벨 숨김 `frontend/src/shell/shell.css` 앵커 `@media (max-width: 740px)`
  > `.gnb-upload .lbl { display: none; }   /* 화살표 아이콘만 */`
- 설정·계정 관리 라벨 숨김 `frontend/src/shell/design-system.css` 앵커 `@media (max-width: 900px)`
  > `.colab-ui .gnb-settings .lbl { display: none; }`
- 두 아이콘이 모바일에서도 표시되는 근거 = `frontend/src/shell/design-system.css` 앵커
  > `:is(.colab-ui, .design-preview) .gnb-settings { display: inline-flex; }`

  이 규칙의 특이도(0,2,0)가 `frontend/src/shell/shell.css` 앵커 `@media (max-width: 880px)` 의 `.gnb-settings { display: none; }`(0,1,0)보다 높다. `.colab-ui` 는 `frontend/index.html` 앵커 `<body class="colab-ui">` 로 상시 적용. 두 파일의 적용 순서도 design-system 이 먼저다(`frontend/src/shell/shell.css:1~2` 의 `@import './design-system.css';`).
- 보조기기 이름 존재 = `aria-label="업로드"`(`frontend/src/components/upload/UploadEntry.tsx`) · `aria-label="계정 관리"`·`aria-label="연구실 설정"`(`frontend/src/shell/Gnb.tsx`). `title` 속성은 없음 → 마우스 도움말 없음.
- 주 내비 3탭은 라벨 유지 = `frontend/src/shell/shell.css` 앵커 `@media (max-width: 560px)` 축자
  > `/* **주 내비 라벨은 여기서도 지킨다.** 넘치면 감추지 않고 가로로 굴린다 (목업 :163~168) */`
- 근본 원인 = 라벨을 접는 사다리에 가시 대체 표기가 없다.

### 2. 의도 대조
- 의도 기록 = `frontend/src/shell/shell.css` 앵커 `GNB 반응형 사다리` 주석이 목업 축자를 인용 —
  > `「좁아질수록 라벨부터 접고 아이콘만 남긴다. **마지막까지 지키는 건 주 내비와 업로드**다.」`

  아이콘 전용은 의도대로.
- 접근성 근거로 `aria-label` 만 제시 = 같은 주석 축자
  > `라벨을 감추는 컨트롤에는 전부 `aria-label` 이 붙어 있다 (`Gnb.tsx`) — 접근성은 그대로다`
- 대장 항목 = `[미확인]` — 해소 = `grep -n "모바일\|반응형\|390" dev-package/work-items.yaml`.

### 3. 원인 분류
- **설계 차이** — 아이콘 전용은 목업 정본대로, 가시 라벨 요구는 기획자 기대.

### 4. 수정 범위 추정
- `title` 추가안 = `frontend/src/shell/Gnb.tsx` · `frontend/src/components/upload/UploadEntry.tsx` · **S**. 터치 기기에서 `title` 미표시 한계 존재.
- 더보기 메뉴안 = 상단 셸 구조 변경(아바타 메뉴와 같은 부품 재사용) · `frontend/src/shell/*` · **M**.
- 계약·core-api 무변경 · 파괴 없음.

### 5. 판정 질문
- 사용자가 보는 것 = 휴대전화 상단에서 ⓐ 지금처럼 그림만 보인다 ⓑ 그림 옆에 짧은 글자가 붙는다 ⓒ 그림 하나(더보기)만 남고 누르면 기능 이름이 적힌 목록이 열린다.
- 두 갈래의 대가 = ⓑ 는 폭이 좁아 주 내비 3탭이 가로로 밀린다. ⓒ 는 한 번 더 눌러야 하나 이름이 항상 글자로 보인다.
- 권고 = ⓒ. 아바타 메뉴 판정과 한 부품으로 묶는다.

---

## I-2 검색 범위 표기와 목록 건수 불일치 (목록 26 · 검색 25)

### 1. 재현/확인
- 확인 결과 = 코드로 확인됨. 두 숫자가 서로 다른 스코프에서 나온다.
- 범위 줄 출력 `frontend/src/routes/SearchResultsPage.tsx` 앵커 `건을 뒤졌어요`
  > `{scope.labName} 데이터 {scope.searchedCount}건을 뒤졌어요.`
- 응답 조립 `services/core-api/src/colab_core/app/routes/catalog.py` 앵커 `"scope": {"labId"`
  > `"scope": {"labId": str(subject.lab_id), "labName": lab_name, "searchedCount": searched_count},`
- 분모 계산 = 같은 파일 앵커 `searched_count = d3_catalog.count_datasets(db)`. 여기의 `db` 는 라우트 서명 `db: Session = Depends(scoped_db)` 세션.
- 검색 실행은 다른 세션 = 같은 파일 앵커 `with read_only_scope(`
  > `with read_only_scope(request.app.state.session_factory, subject, operator_read=subject.operator) as ro:`
- `operator_read` 의 효과 = `services/core-api/src/colab_core/kernel/scope.py` 앵커 `GUC_OPERATOR_READ` 주석
  > `켜지면 `operator_read` 정책(FOR SELECT · PERMISSIVE)이 열리고 **읽기만** 넓어진다`
- 분모 쿼리에 연구실 조건 없음 = `services/core-api/src/colab_core/domains/d3_catalog.py` 앵커 `def count_datasets`
  > `SELECT count(*) FROM d3_dataset WHERE deleted_at IS NULL`

  값은 RLS 가 정한다.
- 근본 원인 `[추론]` = `scoped_db` 도 `operator_read` 판정을 거치나(`services/core-api/src/colab_core/app/deps.py` 앵커 `apply_scope(session, subject, operator_read=_operator_read(request, subject))`) 그 판정이 읽기 메서드 한정이다 — 같은 파일 앵커
  > `if not (subject.operator and request.method.upper() in _READ_METHODS):`

  검색은 `POST /dataset-searches` 이므로 `scoped_db` 쪽 확장이 꺼진다 = 소속 연구실 25건. 결과 항목은 `read_only_scope(operator_read=True)` 라 전 연구실. 곧 분모는 소속 연구실, 결과는 전 연구실.
- `labName` 도 소속 연구실 이름 = 같은 라우트 앵커 `lab = d1_identity.find_lab(db)` → 상단 「전체 연구실」 표기와 불일치.
- 25 vs 26 의 실데이터 근거 = `[미확인]` — 해소 = dev DB 에서 `SELECT lab_id, count(*) FROM d3_dataset WHERE deleted_at IS NULL GROUP BY 1`. 코드상 차이는 「다른 연구실 소속 1건」으로 설명된다.

### 2. 의도 대조
- 범위 줄 선행은 의도 = `frontend/src/routes/SearchResultsPage.tsx` 머리 주석 축자
  > `· 범위 줄이 결과보다 **위이자 먼저**다 (0건이어도, 장애여도)`
- 운영자 전 연구실 읽기는 승인 intent 근거 = `services/core-api/src/colab_core/app/deps.py` 앵커 `운영자의 **읽기 요청에만** 전 연구실 스코프를 연다 (승인 intent 2026-09-12)`
- 운영자일 때의 범위 줄 문안 규정 = `[미확인]` — 해소 = `grep -n "searchedCount\|범위 줄" dev-package/PLAN-SoT.md dev-package/intent/*.md`.
- 검색 항목 `K4`(stage `after_stage2`)는 열려 있음(`CLAUDE.md` 표 축자 「`K4` 는 열려 있다」). 이 불일치의 `K4` 포함 여부 `[미확인]`.

### 3. 원인 분류
- **결함(코드가 의도와 다름)** — 한 응답 안에서 분모와 분자의 스코프가 갈리고, 「뒤진 범위를 먼저 밝힌다」를 범위 줄이 지키지 못한다.
- 연동 설계 차이 1건 = 운영자에게 연구실 선택권을 주는지(＝`D-1` 판정).

### 4. 수정 범위 추정
- 최소 정합안 = `searched_count` 를 검색 실행과 같은 세션(`read_only_scope(operator_read=subject.operator)`)에서 계산, 운영자일 때 `labName` 대신 「전체 연구실(읽기 전용)」 문안 사용.
  - 파일 = `services/core-api/src/colab_core/app/routes/catalog.py` · `frontend/src/routes/SearchResultsPage.tsx`.
  - 계약 = 확인 완료. `contracts/schemas/common.json` 앵커 `"AiSearchScope"` 가 `required: [labId, labName, searchedCount]` ＋ `additionalProperties: false` 이고 `labName` 은 `minLength: 1` 문자열 — **문안 교체는 계약 무변경·무파괴**다. 스키마 설명 축자
    > `AI 검색이 **뒤진 범위**. 응답에 필수로 실린다 — 0건이어도 어디를 찾았는지 먼저 밝힌다.`
    새 칸(`scopeKind` 류) 추가는 `additionalProperties: false` 때문에 `contracts/schemas/common.json` 개정 필요 — 추가 칸이므로 소비자 파괴는 아니다.
  - 크기 = **M**.
- 검색창 옆 사전 표기안(기획자 권고) = `frontend/src/components/search/SearchHero.tsx` 에 범위 문구 추가. 건수를 미리 보이려면 별도 조회 필요 · **M**.

### 5. 판정 질문
- 사용자가 보는 것 = 관리자로 검색하면 ⓐ 「전체 연구실 데이터 26건을 뒤졌어요」로 상단 표기와 같아진다 ⓑ 「우리 연구실 25건에서 검색」으로 좁혀지고 전체를 보려면 따로 고른다.
- 두 갈래의 대가 = ⓐ 서버가 세는 자리만 맞추면 되고 남의 연구실 데이터가 계속 결과에 섞인다. ⓑ 선택 장치를 새로 만들고 조회 범위를 요청이 지정하는 구조 변경이 따른다.
- 권고 = ⓐ 선행 집행(화면이 사실과 다르게 말하는 상태를 닫는다). ⓑ 는 `D-1` 과 같은 판정에서 결정.

---

## I-7 로그인 실패 시 이메일까지 지워짐

### 1. 재현/확인
- 확인 결과 = **코드로 확인되지 않음**. 코드는 비밀번호만 지운다.
- 근거 `frontend/src/auth/LoginPage.tsx` 앵커 `if (response?.status === 401) {`
  > `setPassword('');`

  `setAccountName('')` 호출은 레포에 없다 — 측정 `grep -rn "setAccountName" frontend/src` 결과 3행(선언·`value` 전달·`onChange`)뿐.
- 다른 실패 경로도 입력 초기화 없음 = 같은 파일 429 분기·`error?.message` 분기·`catch` 분기.
- 재마운트 가능성 검토 = `frontend/src/auth/AuthGate.tsx` 의 `<LoginPage />` 반환 위치 3곳 확인. 401 실패 시 세션 상태가 바뀌지 않는다. 로그인 op 은 전역 401 처리에서 제외 = `frontend/src/api/client.ts` 앵커
  > `if (response.status === 401 && !isPublicSessionOp(request.url)) {`
- 브라우저 실제 동작 `[미확인]` — 해소 = CloudFront 화면에서 잘못된 자격으로 제출 후 `#accountName` 의 `value` 확인(자동완성·비밀번호 관리도구 개입 동시 확인).

### 2. 의도 대조
- 의도 = 현재 코드가 기획자 권고(비밀번호만 초기화)와 일치.
- 로그인 강화 intent `dev-package/intent/stage3-login-hardening.md` 실재. 해당 문서의 결함 7종 열거에 **입력 보존 항목 없음** — 축자
  > `오류응답의 입력 원문 반사, 통신 실패 후 대기 상태 고정, 늦은401의 새 세션 제거, 탭 간 로그아웃 미동기화, 이메일 길이 불일치, 로그인 방식 부분 혼합, 문자 길이 단위 불일치의 7종`
- 같은 폴더의 로그인 회차 intent 2건(`dev-package/intent/2026-09-12-login-backoffice-closeout.md`·`dev-package/intent/2026-09-12-operator-designation.md`) 내 이메일 보존 언급 `[미확인]` — 해소 = `grep -n "이메일" dev-package/intent/2026-09-12-*.md`.

### 3. 원인 분류
- **문면** — 피드백 원문의 관찰과 코드가 어긋난다. 브라우저 재현 증거가 나오면 결함으로 재분류.

### 4. 수정 범위 추정
- 코드 변경 불요(현 상태가 권고와 일치). 재현 시 `frontend/src/auth/LoginPage.tsx` 1행 내외 · **S** · 계약 무변경.

### 5. 판정 질문
- 없음. 브라우저 재현 1건만 필요.

---

## 요약표

| 항목 | 확인 결과 | 분류 | 기존 결정/항목 | 크기 | Ted 판정 필요 |
|---|---|---|---|---|---|
| D-1 연구실 전환 버튼 | 확인 — `onClick` 없음 · 주석이 「자리만 둔다」 명시 | 설계 차이 ＋ 표기 결함 | `BO-3` done · `note:` 가 전환 동작을 범위 밖으로 명시 | S(칩화) / L(전환 구현) | 예 |
| D-5 내 계정 버튼 | 확인 — `onClick` 없음 · `▾` 존재 | 결함(표기) ＋ 미구현 | 대장 항목 `[미확인]` | S / M(메뉴) | 예 |
| I-9 모바일 아이콘 라벨 | 확인 — 라벨 숨김 사다리 · `aria-label` 만 존재 | 설계 차이 | 목업 사다리 정본(주석 축자) | S(`title`) / M(더보기) | 예 |
| I-2 검색 범위 25 vs 26 | 확인 — 분모 `scoped_db`, 결과 `read_only_scope(operator_read)` | 결함 | 계약 `AiSearchScope` 무변경으로 정정 가능 · `K4` 포함 여부 `[미확인]` | M | 예(ⓑ 갈래만) |
| I-7 로그인 이메일 삭제 | 미확인 — 코드는 `setPassword('')` 만 | 문면 | `stage3-login-hardening.md` 7종에 미포함 | S | 아니오 |

### 후속 항목 (이 조사에서 고치지 않음)
- `dev-package/work-items.yaml` 대조 일부 미실시 — 아바타 메뉴·모바일 라벨·`K4` 의 포함 범위 확정 필요(`BO-3` 는 대조 완료).
- `BO-3` 블록 `note:` 의 `[미확인]`(관리자 전 연구실 열람 실동작)은 이 피드백으로 일부 해소 — 대장 갱신은 오케스트레이터 소관.
- `frontend/src/shell/Gnb.tsx` 내부 규칙 불일치(전환기는 `▾` 금지 · 아바타는 `▾` 유지) — 한 규칙으로 통일.
