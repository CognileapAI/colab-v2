# R-A-2 · 서버 · 계약 계층 — WU-A1 · WU-A2 · WU-A4 · WU-A13

> 이 파일 하나로 세션을 시작한다. 라운드 = **R-A** · 계층 = **서버(＋계약·FE 꼬리)** · WU **4건**.
> **WU-A1 · WU-A2 를 맨 앞에 둔다** — 둘 다 지금 staging 정상 사용에서 문제가 되는 결함이고, 뒤 작업이 그 위에 쌓인다.

---

## 0. 읽기 규칙 — 이 파일이 유일한 부트스트랩

> ⛔ **아래 4개를 통째로 열지 않는다.** 세션이 느려지는 원인이 이것이다.
> `dev-package/03-HANDOFF.md`(607 KB) · `dev-package/PLAN-SoT.md`(1.17 MB) · `dev-package/work-items.yaml`(513 KB) · `dev-package/WORK-UNITS.md`(138 KB)

- **허용된 접근은 아래 세 줄뿐이다.**
  1. 결정 번호 최대값 — `bash dev-package/prd/tools/max-decision.sh`
  2. 대장에서 항목 하나 — `grep -n -A14 '^  - id: WU-A1' dev-package/work-items.yaml`
  3. 게이트 이름 확인 — `sed -n '12,30p' gates/run.sh` (`ALL_GATES` 배열)
- `03-HANDOFF.md` · `CLAUDE.md` · `RESTART.md` 는 **머리 부분만** 읽는다. 본문 통독 금지.
- 요구사항 정본은 이 파일과 `dev-package/prd/PRD-260905-적용전기획.md` 다. 이 파일에 옮겨 적힌 문면이 우선이고, 더 필요하면 PRD 사본에서 **해당 `#### PRD-xx` 절만** 읽는다.
- **코드 파일은 고칠 때만 연다.** 현황 정찰·grep 스윕·다수 파일 읽기는 **서브에이전트에 위임**하고 결론만 회수한다 — 메인 컨텍스트에 파일 덤프를 들이지 않는다.
- 못 읽으면 `[미상]` 이고 실패다. 지어내지 않는다.

---

## 1. 확정 결정 — 다시 열지 않는다 (PRD §1 · Ted 2026-09-05)

미결 18건이 전부 닫혔다 = 확정 16 ＋ 해소 1(미결-8) ＋ 개발 실측 1(미결-10). **기획자에게 받아야 하는 답은 0건이다.**
아래 16줄이 요구사항이다. 다르게 구현할 사유를 찾으면 **고치지 말고 보고한다.**

- 미결-1 ⓐ — 공개 범위는 **연구실 내부 3값**(`연구실 구성원 전체`/`나만 보기`/`지정한 사람만`). RLS 경계를 열지 않고 PRD-37·WU-C5 를 열지 않는다
- 미결-2 ⓐ — 가공 단계를 **사람이 고르고**, 계보 계산값과 어긋나면 **경고만** 낸다(등록을 막지 않는다)
- 미결-3 ⓐ — 기존 13행의 3축은 **전 행 NULL**, 자동 매핑 없음. 표기 「분류를 아직 안 골랐어요」, `topic` 열은 남긴다
- 미결-4 ⓐ — 관측 간격은 **선택 입력**. 저장은 수치＋단위 두 칸, 표기는 기간 뒤 괄호
- 미결-5 ⓐ — 설명 필수화 후 빈 기존 행은 **그대로 두고** 그 행을 수정할 때 채우게 한다(`NOT NULL` 금지 · 일괄 채우기 금지)
- 미결-6 ⓐ — 확정 부모 1건 이상이면 체크박스 **잠금＋사유 한 줄**. 라벨 = `가공 전 데이터를 못 찾았어요 — 기록 없이 등록할게요`
- 미결-7 ⓐ — 가공 단계 **Lv0~Lv3 네 단**(CHECK·enum·칩 4단)
- 미결-9 ⓑ — 상세는 **한 페이지 스크롤 유지 ＋ sticky 구역 메뉴 ＋ 활성 표시**. 정본을 개정하지 않고 탭·패널 전환을 만들지 않는다
- 미결-11 ⓐ — 원천 표기는 **Lv 무관 상시 노출**, `출처 주소`·`내려받은 날` 두 칸만 Lv0 게이팅
- 미결-12 ⓐ — 유형별 주의 문구는 **선택기 아래 보조 문구 ＋ 설명란 힌트**(저장 칸 없음)
- 미결-13 ⓐ — 분류·유형은 **표시만 국문＋영문 병기**, 저장·CHECK·필터·색인은 국문 단일
- 미결-14 ⓐ — 유형↔가공 단계 **제약 없음**(조합 검증을 만들지 않는다)
- 미결-15 ⓐ — 종료 모달은 **조건만** 고치고 **문면은 유지**한다(PRD-34 범위 밖)
- 미결-16 ⓐ — 등록 ③ 의 쓰임 한 줄은 **받지 않는다**(PRD-36 · WU-C4 범위 밖)
- 미결-17 ⓐ — pdf 항목 8 잘린 1행은 원문 요청 중이다. **회신 대기가 착수를 막지 않는다**
- 미결-18 ⓐ — 기간은 **시각값 저장 유지**, 화면이 최소 단위 셀렉트＋Start/End 를 조립한다. 신규는 `period_granularity` 열 하나
- (미결-8 = 해소 · 미결-10 = WU-A11 실측 결과가 곧 범위 — 이 파일 밖이다)

---

## 2. 범위 — 이 파일의 WU 4건

### WU-A1 · 권한 스위치 기본값 (PRD-25) — 계층 서버 · 크기 S · 레인 `p3-perm-default` · 의존 없음

- **원천**: SoT조사 `DM §3 권한 기본값` · `E-01 §1.3-② 앞 둘 기본 켜짐`(둘 다 `상이`).
- **현재 코드**: `services/core-api/src/colab_core/domains/d2_access.py:76-81` — `return {s: bool(stored.get(s, False)) for s in SWITCHES}`. `d2_permission_switch` 에 저장된 행이 없으면 네 스위치를 **모두 꺼짐**으로 판정한다. `db/platform/schema.sql:139-150` 에 기본값 행을 만드는 장치도 없다. **정본은 `업로드·편집`·`프로젝트 생성` 기본 켜짐 / `승인 위임`·`연구실 설정` 기본 꺼짐**이다(`schema.sql:136-137` 주석 `P-4` 가 그 사실을 적어 두고도 코드가 어긴다).
- **결과**: 시드가 채우지 않은 계정은 **업로드 권한 없이 시작한다.** 새 연구원이 아무것도 못 올린다.
- **변경 — 서버**: `d2_access.py:76-81` 의 기본값을 스위치별로 가른다 — `업로드·편집`·`프로젝트 생성` 은 행이 없으면 `True`, 나머지 둘은 `False`. `member_permissions`(같은 파일 130-146)도 **같은 판정**을 쓴다.
- **변경 — DB**: 기본값 상수를 **한 자리에만 둔다.** 서버 상수로 두고 **DB 기본값 행을 만들지 않는다** — 행이 없는 상태가 「기본값」이라는 현행 의미를 유지하는 편이 마이그레이션 없이 끝난다.
- **변경 — 계약·프론트**: `PermissionSwitchSet.default`(`frontend/src/components/members/permissions.ts:12-15`)가 이미 정본 기본값을 들고 있다 — **서버와 값이 같아지는지 확인만 한다.**
- **기존 데이터 처리**: 저장된 행은 그대로 존중된다. **명시적으로 꺼 둔 계정이 이 변경으로 켜지지 않는다** — 행이 있으면 그 값이 이긴다. 행이 없는 계정만 켜진다.
- **수용 기준**
  - Given `d2_permission_switch` 에 행이 없는 연구원, When `/me` 조회, Then `업로드·편집=true`·`프로젝트 생성=true`·`승인 위임=false`·`연구실 설정=false`.
  - Given `업로드·편집` 을 명시적으로 `false` 로 저장한 연구원, When `/me` 조회, Then `false` 그대로다.
  - Given 교수, When `/me` 조회, Then 네 스위치 전부 `true`(현행 유지).
  - Given 행 없는 연구원, When 업로드 시도, Then 성공한다(회귀 방지 테스트).
- ⚠ **staging 의 기존 계정 권한이 실제로 바뀐다 — 배포 전에 현재 행 상태를 실측해 보고한다**(`d2_permission_switch` 행 수를 먼저 센다). staging 에 **쓰지는 않는다**.

### WU-A2 · 미리보기 생성 권한 구멍 (PRD-26) — 계층 서버 · 크기 S · 레인 `p3-preview-guard` · 의존 없음

- **원천**: SoT조사 `E-01 나-2 미리보기 생성 서버 차단` = `미적용`.
- **현재 코드**: `services/core-api/src/colab_core/app/routes/preview.py:96-132` `create_preview_render` — `업로드·편집` 검사도, 대상 데이터셋 본체 접근(`require_body_access`) 검사도 **없다.** `_target_in_lab` 으로 연구실 경계만 본다. **잠긴 데이터셋을 대상으로 한 렌더 요청이 막히지 않는다.**
- **대조**: 같은 파일의 값 조회(`preview.py:252-295`)는 잠긴 데이터셋에 서지 않는다 — 다운로드와 **같은 판정 함수를 재사용**한다. **생성 경로만 비어 있다.**
- **변경 — 서버**: `create_preview_render` 에 두 검사를 더한다. ⑴ `업로드·편집` 권한 ⑵ `target.datasetId` 가 있으면 그 데이터셋의 본체 접근 판정 — ⛔ **값 조회가 이미 쓰는 함수를 그대로 재사용한다. 새 판정 로직을 만들지 않는다.** `target.uploadId` 는 등록 전 업로드라 **소유자 판정만** 본다.
- **변경 — 계약·DB·프론트**: 없음. **403 응답이 계약에 이미 있는지 확인한다.**
- **기존 데이터 처리**: 해당 없음.
- **수용 기준**
  - Given `업로드·편집` 없는 계정, When `POST /previews`, Then **403**.
  - Given 잠긴 데이터셋(자기 것이 아님), When `POST /previews` 로 그것을 대상 지정, Then **거절된다**.
  - Given 자기 업로드(등록 전), When `POST /previews`, Then 성공한다(회귀 방지).
  - Given 다른 연구실 데이터셋 id, When `POST /previews`, Then **404**(현행 유지).
- **완료 판정에 diff 증명이 붙는다** — 값 조회가 쓰는 판정 함수를 재사용했음을 diff 로 보인다.
- FE 게이트도 확인한다(권한 없는 사용자가 버튼을 보지 않도록).

### WU-A4 · 설명 필수 ＋ 레이아웃 (PRD-15 · PRD-28) — 계층 계약·서버·FE · 크기 M · 레인 `p3-summary-required` · 의존 **WU-A3**

**PRD-15 · 설명 필수 · 세 줄 높이**
- **현재 코드**: `contracts/seams/fe-core.yaml:2758-2760` `summary: type: [string,"null"]`(선택) · `db/platform/schema.sql:371` `summary text` — **NOT NULL 아니다**. 필수는 이름 하나(`VAL-001`).
- **변경 — DB**: **없다**(미결-5 ⓐ 확정 — nullable 유지. ⛔ `NOT NULL` 을 걸지 않고 ⛔ 일괄 채우기도 하지 않는다).
- **변경 — 계약**: `DatasetCreate` required 에 `summary` 추가, `type: string, minLength: 1`. `DatasetUpdate` 는 열쇠가 오면 비울 수 없게 한다(`minLength: 1`, null 불가). ⚠ **요청 필수 칸 신설 = 파괴적 변경** — §3-㉰.
- **변경 — 서버**: 공백만 있는 문자열을 **400** 으로 거절한다(`btrim` 후 길이 검사 — `d3_dataset_description.name` CHECK 와 같은 모양).
- **변경 — 프론트**: `필수` 배지. 입력 칸을 **3줄 높이**로. rev1 은 아래 안내 문구를 없앴다 — 그대로 따른다.
- **기존 데이터 처리**: `summary IS NULL` 또는 공백인 행은 **그대로 둔다**(미결-5 ⓐ). 조회는 종전대로 되고, 상세는 「설명이 아직 없어요 — 수정에서 채워 주세요」를 보인다. 그 행을 `updateDataset` 로 **한 번이라도 수정하면** 설명을 채워야 저장된다.
- **수용 기준**
  - Given 설명 없이 등록, When `createDataset`, Then **400**.
  - Given 공백 세 칸만 입력, When `createDataset`, Then **400**.
  - Given 설명이 빈 기존 행, When 상세 조회, Then 위 문면이 뜨고 **화면이 깨지지 않는다**.
  - Given 설명이 빈 기존 행, When 설명을 비운 채 다른 필드만 수정 저장, Then **400**.
- **영향 범위**: 검색 `search_vector` C 가중치(변화 없음) · 기존 행의 수정 경로.

**PRD-28 · 입력 영역 폭 2:3 · 짧은 값 3개 한 줄**
- **현재 코드**: `frontend/src/components/upload/upload.css` 레이아웃 — 조사에서 미확인(`R-16` = 미적용, 근거 「미확인·미반영」).
- **변경 — 프론트만.** 등록 화면 좌우 비율을 **미리보기 2 : 입력 3** 으로. **기간·좌표계·격자를 한 줄 3칸**으로 묶는다.
- **수용 기준**: 1280px 폭에서 좌우 비율이 2:3 이고, 기간·좌표계·격자가 한 줄에 세 칸으로 나란하다. **마지막 줄이 반쯤 비지 않는다.**
- PRD-15 와 **같은 화면이라 한 WU 로 묶는다**.

### WU-A13 · 확장자 혼합 규칙 (PRD-32) — 계층 서버·FE · 크기 S · 레인 `p3-ext-mixed` · 의존 없음

- **원천**: rev1 `H-37` 축자 — `if(same.length!==arr.length) toast('확장자가 다른 파일은 뺐어요. 한 번에 한 종류만 묶어요')` · rev1 Policy `VAL-002` · 시험 `TC-W-001b`.
- **현재 코드**: 확장자 화이트리스트는 없다(부록 A `P-6`·`R-06`). **혼합 처리 규칙 자체가 없다.**
- **부록 A `P-5`·`R-05` 와의 관계 — 다른 규칙이다.** 그쪽은 「같은 확장자 여러 개는 데이터셋 하나」로 **성립한 뒤의 저장 규칙**이고, 이 요구는 **성립 전의 선별 규칙**이다.
- **변경 — 프론트**: 파일을 놓는 순간 확장자를 세어 **가장 먼저 놓인 파일의 확장자만 남기고 나머지를 뺀다.** 뺀 것이 1건 이상이면 토스트 **축자** = `확장자가 다른 파일은 뺐어요. 한 번에 한 종류만 묶어요`. 확장자 비교는 **소문자 기준**이다(`.NC` 와 `.nc` 는 같은 종류다).
- **변경 — 서버**: **최종 방어선을 둔다** — 한 업로드의 조각 확장자가 2종 이상이면 **400**. 화면 차단이 유일한 방어선이 되지 않게 한다.
- **변경 — DB·계약**: 없음(PRD-21 의 `file_extension` 이 데이터셋당 1값인 근거가 이 규칙이다).
- **기존 데이터 처리**: 이미 저장된 데이터셋 중 조각 확장자가 **2종 이상인 것이 있는지 마이그레이션 전에 센다.** 있으면 그 목록을 **보고하고 값을 고치지 않는다** — ⛔ 기존 행을 지우거나 쪼개지 않는다.
- **수용 기준**
  - Given `.nc` 3개와 `.tif` 1개를 한 번에 놓음, When 확인, Then 목록에 `.nc` 3개만 남고 위 토스트가 뜬다.
  - Given `.NC` 와 `.nc` 를 함께 놓음, When 확인, Then **둘 다 남는다**(대소문자 무시).
  - Given API 로 2종 확장자 조각을 실어 보냄, When 등록, Then **400**.
  - Given 한 종류만 놓음, When 확인, Then 토스트가 뜨지 않는다.
- **닿는 자리**: `FileDropCard.tsx` · `ingestion.py`.

### 이 파일 안의 순서와 의존

`WU-A1` · `WU-A2` (독립 · 먼저) → `WU-A13` (독립) → `WU-A4` (**WU-A3 선행** — `R-A-3` 파일).
⚠ **WU-A4 의 계약·서버 부분은 WU-A3 없이 시작할 수 있다.** WU-A3 이 필요한 것은 FE 부분(`필수` 배지 · 3줄 · 2:3 레이아웃)이다.

---

## 3. 지켜야 하는 규약 — 명령으로

### ㉮ 워크트리 레인

- WU 하나에 레인 하나 — `p3-perm-default`(A1) · `p3-preview-guard`(A2) · `p3-summary-required`(A4) · `p3-ext-mixed`(A13).
- 각 레인은 `origin/main` 에서 딴 자기 워크트리에서 돈다. 병합은 **ff-merge**, 병합 뒤 워크트리·로컬/원격 브랜치를 정리한다.
- 한 레인 = 한 WU. 네 WU 를 한 브랜치에 섞지 않는다.

### ㉯ 착수 전 — `work-items.yaml` 등재가 먼저다

`dev-package/work-items.yaml` 의 `items:` 리스트 **끝에** 아래를 그대로 덧붙인다(들여쓰기 2칸).

```yaml
  - id: WU-A1
    name: 권한 스위치 기본값 (PRD-25)
    status: in_progress
    stage: stage2
    owner: "T-R"
    entry_conditions: []
    depends_on: []
    completion_def: "행 없는 연구원이 업로드·편집=true·프로젝트 생성=true 로 내려오고, 명시적 false 행은 그대로다. 회귀 테스트 4건 green"
    evidence: "dev-package/sessions/p3-perm-default-<YYYYMMDD>.md"
    deadline: null
    note: "마이그레이션 0 · DB 기본값 행을 만들지 않는다(서버 상수 한 자리). staging 계정 권한이 실제로 바뀐다 — 배포 전 현재 행 상태 실측 보고"
    sources: ["dev-package/prd/rounds/R-A-2-server.md", "PRD-25"]

  - id: WU-A2
    name: 미리보기 생성 권한 검사 (PRD-26)
    status: in_progress
    stage: stage2
    owner: "T-R"
    entry_conditions: []
    depends_on: []
    completion_def: "POST /previews 가 업로드·편집 없으면 403, 잠긴 남의 데이터셋 대상이면 거절, 자기 업로드는 성공, 다른 연구실 id 는 404. 값 조회가 쓰는 판정 함수를 재사용했음을 diff 로 보인다"
    evidence: "dev-package/sessions/p3-preview-guard-<YYYYMMDD>.md"
    deadline: null
    note: "계약·DB·프론트 변경 0. 403 이 계약에 이미 있는지 확인만 한다"
    sources: ["dev-package/prd/rounds/R-A-2-server.md", "PRD-26"]

  - id: WU-A4
    name: 설명 필수 + 레이아웃 (PRD-15·28)
    status: in_progress
    stage: stage2
    owner: "T-R"
    entry_conditions: ["계약 동결 해제 19차 승인 (등급 ㉯)"]
    depends_on: ["WU-A3"]
    completion_def: "설명 없는 등록이 400, 공백만도 400, 기존 NULL 행이 안내 문구와 함께 뜬다. 1280px 에서 좌우 2:3 · 짧은 값 3칸 한 줄"
    evidence: "dev-package/sessions/p3-summary-required-<YYYYMMDD>.md"
    deadline: null
    note: "DB 변경 0 — NOT NULL 금지·일괄 채우기 금지(미결-5 ⓐ). DatasetCreate.required 에 summary 추가가 파괴적 변경이다"
    sources: ["dev-package/prd/rounds/R-A-2-server.md", "PRD-15", "PRD-28"]

  - id: WU-A13
    name: 확장자 혼합 규칙 (PRD-32)
    status: in_progress
    stage: stage2
    owner: "T-R"
    entry_conditions: []
    depends_on: []
    completion_def: "다른 확장자 파일이 빠지고 토스트 축자가 뜬다. 대소문자는 같은 종류다. API 로 2종을 보내면 400. 기존 데이터 중 2종 이상인 데이터셋 건수를 세어 보고했다"
    evidence: "dev-package/sessions/p3-ext-mixed-<YYYYMMDD>.md"
    deadline: null
    note: "기존 행을 지우거나 쪼개지 않는다 — 세어 보고만 한다"
    sources: ["dev-package/prd/rounds/R-A-2-server.md", "PRD-32"]
```

### ㉰ 계약 동결 해제 — **19차 · 등급 ㉯ · Ted 승인 필수 · 이 파일에서는 WU-A4 가 연다**

근거 문서 = `dev-package/sessions/X2-FREEZE-PROTOCOL.md` §5. 직전 회차 = **18차** ⟹ 이 라운드는 **19차**.
**계약을 여는 WU 는 R-A 전체에서 둘 — `WU-A4`(`DatasetCreate.required` 에 `summary`) · `WU-A6`(`DataPeriod.granularity` · `R-A-1` 파일).**
⛔ **둘을 쪼개 각각 ㉮ 로 통과시키지 않는다**(§5-㉰-6). **한 라운드를 목적 단위로 한 회차에 판정한다.**
㉯ 인 사유 = 파괴적 변경 ＋ 마이그레이션 ≥1(M-6·M-7·M-9) ＋ 소비자 ≥1.
⛔ **WU-A1 · WU-A2 · WU-A13 은 계약을 열지 않는다** — 계약 파일을 건드리면 그 자체가 범위 위반이다.

```bash
# ⑴ 파괴 판정을 실행 출력으로 낸다 (주장하지 않는다 — §5-㉱-1)
./gates/run.sh contract-breaking
# ⑵ 소비자 수를 grep 출력으로 낸다 (§5-㉱-3)
grep -rn 'DatasetCreate\|summary' contracts/ services/ frontend/src | wc -l
# ⑶ 마이그레이션 건수 = 3 (R-A-1 의 M-9 · M-6 · M-7, 한 head)  ⑷ 되돌림 경로
```
⛔ **승인 없이 `contracts/` 를 고치지 않는다.** ⛔ **§5-㉰-4(집행 없는 신설) 금지** — 계약만 열고 서버 수용 목록(`_ALLOWED_CREATE_FIELDS`)을 다음 회차로 미루지 않는다.

### ㉱ 결정 번호 〈N〉 — 예약하지 않는다

```bash
git fetch origin main && bash dev-package/prd/tools/max-decision.sh   # 병합 직전에 다시 잰다
```
착수 시점 참고값 = **〈326〉**(2026-09-05 실측). **병합 직전 `origin/main` 최대 ＋ 1.**
`PLAN-SoT §9` 표에 아래 한 행을 **병합 직전에** 덧붙인다 — 필드 8개(X2 §5-㉲).

```
| 〈N〉 | **R-A-2 서버 계층 — 권한 기본값 반전 · 미리보기 생성 권한 구멍 · 설명 필수 400 · 확장자 혼합 400** | **집행 (2026-MM-DD · 워크트리 `<레인>` · 병합 `<sha>`).** ①회차 = **19차**(WU-A4 분 · 직전 18차) ②값 = `DatasetCreate.required += summary` · `DatasetUpdate.summary minLength 1` ③근거 = PRD-15·25·26·28·32 (`dev-package/prd/PRD-260905-적용전기획.md`) ④가·파 판정 = **파괴**(요청 필수 칸 신설) · `contract-breaking` 출력 = `<축자>` ⑤소비자 = `<n>` 건 · 측정법 = `grep -rn 'DatasetCreate\|summary' contracts/ services/ frontend/src` ⑥마이그레이션 = **0건**(이 파일 분 · 라운드 전체는 R-A-1 의 3건 한 head) ⑦승인 = Ted · `<일자>` ⑧이번에 세지 않은 축 = staging 계정 권한 실제 변동 폭(실측 보고만 · 쓰기 0) `[미측정]` |
```
⛔ **HANDOFF 에는 값을 적지 않는다**(`CLAUDE.md §6-3`).

### ㉲ 게이트 — 작업 중엔 단독, 병합 전엔 전건

```bash
# 작업 중 (단독 게이트만 하나씩)
./gates/run.sh service-tests-core-api     # A1 · A2 · A4 · A13
./gates/run.sh rls-effect                 # A1 · A2
./gates/run.sh contract-lint              # A4
./gates/run.sh contract-breaking          # A4
./gates/run.sh frontend-typecheck         # A4 · A13
./gates/run.sh frontend-test              # A4 · A13
./gates/run.sh frontend-fixture-reach     # A4
# 병합 직전 한 번
./gates/run.sh all -j 1
```
⛔ **게이트를 끄거나 검사 대상을 줄이지 않는다.** **green 으로 시작한 테스트는 오라클이 아니다** — 실패 테스트 red 를 먼저 확인한다.

### ㉳ 커밋 문면

```
서버 계층 R-A-2 — 권한 기본값·미리보기 권한·설명 필수 400·확장자 혼합 400 (WU-A1·A2·A4·A13)

- d2_access.py 기본값을 스위치별로 갈랐다 (마이그레이션 0 · 명시 false 행은 불변)
- create_preview_render 가 값 조회와 같은 판정 함수를 재사용한다 (diff 근거)
- 계약 동결 해제 19차 · 등급 ㉯ · Ted 승인 <일자> · PLAN-SoT §9 〈N〉 등재
- RED 선실측 → GREEN: <시험 파일>:<건수>
```

### ㉴ 금지

- ⛔ `main` 에 직접 push. ⛔ staging DB 직접 쓰기 — WU-A1 의 실측은 **읽기(세기)만** 한다.
- ⛔ 원장 행 없이 마이그레이션. ⛔ WU-A2 에서 새 권한 판정 로직 신설(**기존 함수 재사용**).
- ⛔ `summary` 에 `NOT NULL`·일괄 채우기(미결-5 ⓐ). ⛔ WU-A13 에서 기존 행 삭제·분할.
- ⛔ `40 COLAB-기획/` 문서 수정. ⛔ 문서·주석에 절대경로. ⛔ 이 세션이 `03-HANDOFF.md` 를 직접 고치기.

---

## 4. 산출물과 근거

| 무엇 | 어디 |
|---|---|
| 서버 | `services/core-api/.../domains/d2_access.py`(A1) · `.../app/routes/preview.py`(A2) · `.../routes/catalog.py`·`ingestion.py`(A4·A13) |
| 계약 | `contracts/seams/fe-core.yaml` — `DatasetCreate` · `DatasetUpdate`(A4 만) |
| 프론트 | `components/members/permissions.ts` 값 대조(A1) · 설명 칸 3줄·`필수` 배지·2:3 레이아웃(A4) · `FileDropCard.tsx`(A13) |
| 실측 보고 | `d2_permission_switch` 현재 행 수(A1) · 조각 확장자 2종 이상 데이터셋 건수와 목록(A13) |
| 세션 노트 | `dev-package/sessions/p3-perm-default-<YYYYMMDD>.md` · `p3-preview-guard-…` · `p3-summary-required-…` · `p3-ext-mixed-…` — **각 ≤ 60행** |
| 대장 | `dev-package/work-items.yaml` — 위 네 블록. 완료 시 `status: done` ＋ `evidence` 갱신 |
| 원장 | `PLAN-SoT §9` 한 행(㉱ 문안) — **병합 직전** |

**오케스트레이터에 넘기는 HANDOFF 갱신문 — 5줄 이하. 세션이 `03-HANDOFF.md` 를 직접 고치지 않는다.**

```
R-A-2(서버) 완료 — WU-A1·A2·A4·A13, 레인 p3-perm-default·p3-preview-guard·p3-summary-required·p3-ext-mixed, 병합 <sha…>
PRD-25 권한 기본값 반전 · PRD-26 미리보기 생성 403 구멍 폐쇄 (둘 다 정상 사용 결함)
계약 동결 해제 19차 승인 <일자> (WU-A4 분) · PLAN-SoT §9 〈N〉 등재 · 마이그레이션 0
실측 보고: d2_permission_switch 행 <n>건 / 확장자 2종 이상 데이터셋 <n>건 (값은 고치지 않았다)
근거: dev-package/sessions/p3-perm-default-<YYYYMMDD>.md 외 3건
```

---

## 5. 완료 판정

- **WU-A1** — 행 없는 연구원이 `업로드·편집=true`·`프로젝트 생성=true`·`승인 위임=false`·`연구실 설정=false` 로 내려온다 · 명시적 `false` 행은 **그대로다** · 교수는 네 스위치 전부 `true` · 행 없는 연구원의 업로드가 **성공**한다. **회귀 테스트 4건 green.** 마이그레이션 **0건**.
- **WU-A2** — `업로드·편집` 없으면 **403** · 잠긴 남의 데이터셋 대상은 **거절** · 자기 업로드는 **성공** · 다른 연구실 id 는 **404**. **값 조회가 쓰는 판정 함수를 재사용했음을 diff 로 보인다.**
- **WU-A4** — 설명 없는 등록 **400** · 공백만 **400** · 기존 NULL 행이 안내 문구와 함께 뜨고 화면이 안 깨진다 · 그 행을 설명 없이 수정 저장하면 **400** · 1280px 에서 좌우 **2:3**, 기간·좌표계·격자가 **한 줄 3칸**.
- **WU-A13** — 다른 확장자 파일이 빠지고 **토스트 축자**가 뜬다 · `.NC`/`.nc` 는 같은 종류 · API 로 2종이면 **400** · 한 종류면 토스트 없음 · 기존 2종 이상 데이터셋 **건수를 세어 보고**했다(값 무수정).
- **게이트** — `service-tests-core-api` · `rls-effect` · `contract-lint` · `contract-breaking` · `frontend-typecheck` · `frontend-test` · `frontend-fixture-reach` 전건 green, 그리고 병합 직전 `./gates/run.sh all -j 1` green.

---

### 다음 파일

`dev-package/prd/rounds/R-A-3-frontend.md` → `R-A-4-verify.md`.
⚠ **WU-A4 의 FE 부분은 `R-A-3` 의 WU-A3 이 세운 골격 위에 얹힌다.** 계약·서버 부분은 먼저 갈 수 있다.
