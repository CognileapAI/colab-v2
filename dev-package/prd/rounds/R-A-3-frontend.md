# R-A-3 · 프론트엔드 계층 — WU-A3 · WU-A7 · WU-A8 · WU-A9 · WU-A10

> 이 파일 하나로 세션을 시작한다. 라운드 = **R-A** · 계층 = **FE 전용** · WU **5건**.
> ⚠ **선행 두 건이 있다.** ⑴ **WU-A12**(`R-A-4` 파일 · rev1 유지 항목 실측)가 **WU-A9·A10 보다 먼저** 돈다 — 같은 화면을 고치는 WU 가 그 방어선 위에서 돈다. ⑵ **WU-A3 이 이 파일 안에서 맨 먼저** 돈다 — `R-A-1`(WU-A6)·`R-A-2`(WU-A4)의 FE 부분이 그 골격 위에 얹힌다.

---

## 0. 읽기 규칙 — 이 파일이 유일한 부트스트랩

> ⛔ **아래 4개를 통째로 열지 않는다.** 세션이 느려지는 원인이 이것이다.
> `dev-package/03-HANDOFF.md`(607 KB) · `dev-package/PLAN-SoT.md`(1.17 MB) · `dev-package/work-items.yaml`(513 KB) · `dev-package/WORK-UNITS.md`(138 KB)

- **허용된 접근은 아래 세 줄뿐이다.**
  1. 결정 번호 최대값 — `bash dev-package/prd/tools/max-decision.sh`
  2. 대장에서 항목 하나 — `grep -n -A14 '^  - id: WU-A3' dev-package/work-items.yaml`
  3. 게이트 이름 확인 — `sed -n '12,30p' gates/run.sh` (`ALL_GATES` 배열)
- `03-HANDOFF.md` · `CLAUDE.md` · `RESTART.md` 는 **머리 부분만** 읽는다. 본문 통독 금지.
- 요구사항 정본은 이 파일과 `dev-package/prd/PRD-260905-적용전기획.md` 다. 더 필요하면 PRD 사본에서 **해당 `#### PRD-xx` 절만** 읽는다.
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
- (미결-8 = 해소 · 미결-10 = WU-A11 실측 결과가 곧 범위 — `R-A-4` 파일이다)

---

## 2. 범위 — 이 파일의 WU 5건

### WU-A3 · 상세 수정 UI — **현행 필드만** (PRD-22) — 크기 M · 레인 `p3-detail-edit` · 의존 없음 · **이 파일의 첫 WU**

- **현재 코드**: **서버·계약은 이미 서 있다** — `contracts/seams/fe-core.yaml:2794 DatasetUpdate` · `updateDataset` op · `services/core-api/.../routes/catalog.py:678` · `tests/test_dataset_update.py`. **프론트에 수정 UI 만 없다**(`frontend/src/components/detail/` 전체에 수정 진입점 **0건**).
- **변경 — 프론트만.** 상세 헤더에 `수정` 버튼(게이트 = `업로드·편집` — `catalog.py:653-711` 이 이미 그 권한을 요구한다).
- **⚠ R-A 의 편집 대상은 지금 `DatasetUpdate` 가 이미 받는 필드로 한정한다** — **이름 · 설명 · 원천 표기 · 좌표계 · 기간**.
  - ⛔ **`주제`(`topic`)는 편집 대상에서 뺀다** — R-B 의 PRD-01 이 그 축을 `분류`(`category`)로 갈아치우므로 곧 지울 칸을 만들 이유가 없고, 그 사이 사람이 고친 `topic` 값이 **이관 대조를 흐린다**. 상세 **표시**에는 남기고 **읽기 전용**이다.
  - ⛔ **R-B 가 더하는 필드(분류 · 유형 · 가공 단계 · 변수 표 · 공개 범위 · 관측 간격 · 기간 최소 단위 · Lv0 2칸)는 이 WU 가 그리지 않는다** — 계약에 없는 칸을 미리 그리면 WU-B3 이 같은 화면을 두 번 만든다.
  - **이 라운드의 값 = 진입점 · 권한 게이트 · 저장 왕복 · 낙관적 갱신을 세우는 것.** R-B 는 그 골격을 **그대로 쓰고 필드만 늘린다**(화면 골격 재작성 없음).
- **기존 데이터 처리**: 값이 NULL 인 필드는 빈 칸으로 열린다. (R-B 에서) 필수 항목은 채워야 저장된다 — **이 화면이 기존 행의 재선택을 받는 유일한 창구다.**
- **수용 기준** (R-A 범위)
  - Given `업로드·편집` 권한 없는 계정, When 상세 조회, Then `수정` 버튼이 **보이지 않고** API 직접 호출도 거절된다.
  - Given 이름만 바꿔 저장, When 재조회, Then **이름만 바뀌고 나머지 값이 그대로다**.
  - Given 저장 성공, When 검색, Then 바뀐 값으로 찾을 수 있다(색인 갱신).
  - Given 상세 화면, When `주제` 칸 확인, Then **읽기 전용**이고 편집 진입이 없다.
- **뒤에 오는 것**: `R-A-2` WU-A4(설명 3줄·필수 배지·2:3) · `R-A-1` WU-A6(관측 간격·기간 최소 단위)이 이 골격에 얹힌다.

### WU-A7 · 프로젝트·논문 패널 분리 (PRD-23) — 크기 S · 레인 `p3-project-panels` · 의존 없음

- **현재 코드**: `frontend/src/components/upload/RegisterArea.tsx:263-269` — 칩(`chip chip--info`) 나열, **유형 구분 표시가 없다.** 유형값 자체는 있다(`ProjectFormModal.tsx:18` `['국가과제','논문']`).
- **변경 — 프론트만.** ③ 연결 단계의 연관 프로젝트·논문 영역을 **두 패널로 가른다** — `국가과제` 패널 / `논문` 패널. 각 패널 안은 **칩이 아니라 행**이고 위에서 아래로 쌓인다. 각 행에 이름 ＋ 해제 버튼. **0건인 패널은 빈 상태 한 줄**을 보인다.
- **`+ 새 프로젝트 만들기` 링크는 두 패널 공통으로 영역 맨 아래 한 곳에만 둔다.** 누르면 유형(국가과제·논문)을 먼저 고르는 칸이 뜬다. 근거 = docx image6 의 실사용 오류가 이 링크에서 났다. **패널마다 링크를 두면 같은 오독이 두 곳으로 는다.**
- **계약·서버·DB**: 없음(유형값이 이미 있다). **기존 데이터**: 해당 없음(표시 방식이다).
- **수용 기준**
  - Given 국가과제 1건 · 논문 2건 선택, When 화면 확인, Then 두 패널이 각각 1행·2행을 쌓아 보인다.
  - Given 프로젝트를 새로 추가, When 확인, Then 해당 유형 패널에 행이 **아래로 붙고** 화면 이동 없이 보인다.
  - Given 논문 0건, When 확인, Then 논문 패널이 빈 상태 문구와 함께 보인다(**패널 자체가 사라지지 않는다**).
  - Given 영역 확인, When `+ 새 프로젝트 만들기` 를 셈, Then 화면에 **한 개**이고 두 패널 아래 공통 자리에 있다.

### WU-A8 · 상세 구역 메뉴 sticky ＋ 활성 표시 (PRD-24 · 미결-9 ⓑ) — 크기 S · 레인 `p3-detail-sticky` · 의존 없음

- **현재 코드**: `frontend/src/routes/DatasetDetailPage.tsx:1-3, 198` — 「미리보기는 한 페이지 스크롤 안의 한 구역이다(§1.3-1 탭으로 숨기지 않는다)」가 **정본 규칙으로 코드 주석에 박혀 있다.** 구역 이동은 `#sec-usage` 같은 앵커다.
- **변경 — 프론트만.** 구역 메뉴(계보 · 미리보기 · 활용/접근)를 `position: sticky` 로 화면 위에 붙이고, 스크롤 위치에 따라 **현재 구역을 활성 표시**한다.
- ⛔ **패널 전환·탭 숨김을 하지 않고 정본 `Policy_데이터셋_상세 §1.3-1` 을 개정하지 않는다**(미결-9 ⓑ 확정). 한 페이지 스크롤 구조를 그대로 둔다. **상세 전면 재구성 분기(종전 WU-C3)는 없어졌다.**
- **기존 데이터**: 해당 없음.
- **수용 기준**
  - Given 상세에서 `활용/접근` 클릭, When 스크롤 이동 후, Then 구역 메뉴가 **화면 위에 그대로 보인다**.
  - Given 아래로 스크롤, When 미리보기 구역에 들어감, Then 메뉴의 `미리보기` 가 **활성 표시**된다.
  - Given 어느 구역이든, When DOM 확인, Then 다른 구역이 **숨겨지지 않았다**(정본 §1.3-1 준수 증명).

### WU-A9 · 종료 확인 조건 (PRD-14 · 미결-15 ⓐ) — 크기 S · 레인 `p3-close-guard` · **의존 WU-A12**

- **현재 코드**: `frontend/src/components/upload/UploadModal.tsx:239-243` `requestClose()` — `registerOpen` 이면 **무조건** 확인 모달을 띄운다.
- **변경 — 프론트**: 확인 조건을 「등록 단계가 열려 있다」에서 「**사람이 입력한 값이 하나라도 있다**」로 바꾼다. 판정 대상 = ①②③ 의 **사람 입력 필드 전부 ＋ 확정된 계보 부모 건수**. **자동으로 채워진 값**(확장자·용량·기본 선택값 `Lv2`·`연구실 구성원 전체`)은 **입력으로 세지 않는다**.
- ⛔ **문면은 고치지 않는다**(미결-15 ⓐ 확정 · PRD-34 는 §4 범위 밖). 현행 본문 `확인한 계보와 입력한 내용이 사라져요. 데이터셋은 만들어지지 않아요.` 를 **그대로 둔다.**
- **기존 데이터 / 영향 범위**: 없음.
- **수용 기준**
  - Given 파일만 올리고 아무것도 안 적음, When 닫기, Then **되묻지 않고 닫힌다**.
  - Given 설명을 한 글자 적음, When 닫기, Then 확인 모달이 뜬다.
  - Given 계보 부모를 1건 확정, When 닫기, Then 확인 모달이 뜬다.
  - Given 모달 본문 문자열, When 코드 확인, Then **종전 문면 그대로**다.

### WU-A10 · 썸네일 넛지 (PRD-20) — 크기 S · 레인 `p3-thumb-nudge` · **의존 WU-A12**

- **현재 코드**: `frontend/src/components/upload/PreviewPanel.tsx:312` — 썸네일 자리만 있고 **교체 안내 문구가 없다**. 대표 그림 교체 UI 자체가 없다(260825 정본 `VAL-008` 도 미구현).
- **변경 — 프론트**: ② 메타데이터 단계에 `대표 그림(썸네일)` 블록(rev1 `thumbrow`). 자동 생성된 미리보기 축소본이 기본으로 들어가고, **썸네일 옆·아래에 넛지 한 줄** — 「눌러서 다른 그림으로 바꿀 수 있어요」. 클릭하면 **파일 선택기가 열린다**.
- ⛔ **저장 경로는 이 WU 밖이다.** `d3_dataset.representative_file_id` 는 **조각 지정용이지 업로드 이미지용이 아니다.** 이 요구는 **넛지 문구와 클릭 진입까지만**이고 저장 경로는 별건(`WU-C2`)이다. 계약·서버·DB 변경 **0**.
- **기존 데이터**: 해당 없음.
- **수용 기준**
  - Given ② 단계 진입, When 화면 확인, Then 썸네일과 함께 **교체 안내 문구가 읽힌다**.
  - Given 썸네일 클릭, When 확인, Then **파일 선택기가 열린다**.

### 이 파일 안의 순서와 의존

`WU-A3`(첫 WU · 다른 파일이 기다린다) → `WU-A7` · `WU-A8`(독립 · 병렬 가능) → **WU-A12 완료 확인** → `WU-A9` · `WU-A10`.
⚠ **WU-A9 · WU-A10 은 `R-A-4` 의 WU-A12(rev1 유지 항목 실측 13건 ＋ 회귀 시험)가 green 이 된 뒤에 시작한다.** 같은 화면을 고치므로 방어선이 없으면 유지 항목이 **조용히 사라진다**.

---

## 3. 지켜야 하는 규약 — 명령으로

### ㉮ 워크트리 레인

- WU 하나에 레인 하나 — `p3-detail-edit`(A3) · `p3-project-panels`(A7) · `p3-detail-sticky`(A8) · `p3-close-guard`(A9) · `p3-thumb-nudge`(A10).
- 각 레인은 `origin/main` 에서 딴 자기 워크트리에서 돈다. 병합은 **ff-merge**, 병합 뒤 워크트리·로컬/원격 브랜치를 정리한다. 한 레인 = 한 WU.

### ㉯ 착수 전 — `work-items.yaml` 등재가 먼저다

`dev-package/work-items.yaml` 의 `items:` 리스트 **끝에** 아래를 그대로 덧붙인다(들여쓰기 2칸).

```yaml
  - id: WU-A3
    name: 상세 수정 UI — 현행 필드만 (PRD-22)
    status: in_progress
    stage: stage2
    owner: "T-R"
    entry_conditions: []
    depends_on: []
    completion_def: "상세에 수정 진입점이 있고, 권한 없으면 안 보이며, 이름만 바꾼 저장이 나머지를 건드리지 않는다. 편집 대상 = 이름·설명·원천 표기·좌표계·기간. topic 은 읽기 전용"
    evidence: "dev-package/sessions/p3-detail-edit-<YYYYMMDD>.md"
    deadline: null
    note: "FE 만 바뀐다(서버·계약은 이미 있다). R-B 가 이 골격을 그대로 쓰고 필드만 늘린다"
    sources: ["dev-package/prd/rounds/R-A-3-frontend.md", "PRD-22"]

  - id: WU-A7
    name: 프로젝트·논문 패널 분리 (PRD-23)
    status: in_progress
    stage: stage2
    owner: "T-R"
    entry_conditions: []
    depends_on: []
    completion_def: "국가과제·논문 두 패널이 각각 행을 쌓고, 0건 패널도 빈 상태로 남는다. + 새 프로젝트 만들기 는 화면에 한 개"
    evidence: "dev-package/sessions/p3-project-panels-<YYYYMMDD>.md"
    deadline: null
    note: "계약·서버·DB 변경 0"
    sources: ["dev-package/prd/rounds/R-A-3-frontend.md", "PRD-23"]

  - id: WU-A8
    name: 상세 구역 메뉴 sticky + 활성 표시 (PRD-24)
    status: in_progress
    stage: stage2
    owner: "T-R"
    entry_conditions: []
    depends_on: []
    completion_def: "구역 메뉴가 position:sticky 로 화면 위에 남고 현재 구역이 활성 표시되며, 어느 구역도 DOM 에서 숨겨지지 않는다"
    evidence: "dev-package/sessions/p3-detail-sticky-<YYYYMMDD>.md"
    deadline: null
    note: "미결-9 ⓑ 확정 — 이 형태가 최종. 정본 Policy_데이터셋_상세 §1.3-1 을 개정하지 않고 탭·패널 전환을 만들지 않는다"
    sources: ["dev-package/prd/rounds/R-A-3-frontend.md", "PRD-24"]

  - id: WU-A9
    name: 종료 확인 조건 (PRD-14)
    status: in_progress
    stage: stage2
    owner: "T-R"
    entry_conditions: ["WU-A12 회귀 방어선 green"]
    depends_on: ["WU-A12"]
    completion_def: "빈 상태 닫기는 안 묻고, 한 글자라도 적었거나 계보 부모 1건이면 묻는다. 문면은 종전 그대로다"
    evidence: "dev-package/sessions/p3-close-guard-<YYYYMMDD>.md"
    deadline: null
    note: "미결-15 ⓐ — 조건만 고치고 문면 유지. PRD-34 는 §4 범위 밖"
    sources: ["dev-package/prd/rounds/R-A-3-frontend.md", "PRD-14"]

  - id: WU-A10
    name: 썸네일 넛지 (PRD-20)
    status: in_progress
    stage: stage2
    owner: "T-R"
    entry_conditions: ["WU-A12 회귀 방어선 green"]
    depends_on: ["WU-A12"]
    completion_def: "② 단계에 썸네일과 교체 안내가 있고 클릭하면 파일 선택기가 열린다"
    evidence: "dev-package/sessions/p3-thumb-nudge-<YYYYMMDD>.md"
    deadline: null
    note: "저장 경로는 이 WU 밖 — 별건 WU-C2. 계약·서버·DB 변경 0"
    sources: ["dev-package/prd/rounds/R-A-3-frontend.md", "PRD-20"]
```

### ㉰ 계약 동결 해제 — **이 파일의 5건은 계약을 열지 않는다**

근거 문서 = `dev-package/sessions/X2-FREEZE-PROTOCOL.md` §5. 라운드 회차 = **19차 · 등급 ㉯ · Ted 승인 필수**이지만,
그 회차가 여는 것은 **`WU-A4`(`R-A-2`) · `WU-A6`(`R-A-1`) 둘뿐이다.**
⛔ **이 파일의 WU-A3·A7·A8·A9·A10 은 `contracts/` 를 건드리지 않는다** — 건드리면 그 자체가 범위 위반이고, 19차 요청문에 실리지 않은 값을 여는 것이다(§5-㉰-6 묶음 쪼개기 금지).
- WU-A3 이 쓰는 `DatasetUpdate`·`updateDataset` 은 **이미 있는 계약**이다. 없는 열쇠가 필요하다고 판단되면 **고치지 말고 보고한다** — R-B 의 몫이다.

### ㉱ 결정 번호 〈N〉 — 예약하지 않는다

```bash
git fetch origin main && bash dev-package/prd/tools/max-decision.sh   # 병합 직전에 다시 잰다
```
착수 시점 참고값 = **〈326〉**(2026-09-05 실측). **병합 직전 `origin/main` 최대 ＋ 1.**
결정이 생기면 `PLAN-SoT §9` 표에 아래 한 행을 **병합 직전에** 덧붙인다 — 필드 8개(X2 §5-㉲).

```
| 〈N〉 | **R-A-3 FE 계층 — 상세 수정 진입점 신설 · 구역 메뉴 sticky(미결-9 ⓑ 최종형) · 종료 조건 개정** | **집행 (2026-MM-DD · 워크트리 `<레인>` · 병합 `<sha>` · 계약 개정 0 · 마이그레이션 0 · staging 접촉 0).** ①회차 = **해당 없음**(계약 미개방) ②값 = 없음 ③근거 = PRD-14·20·22·23·24 (`dev-package/prd/PRD-260905-적용전기획.md`) ④가·파 판정 = **해당 없음** · `contract-breaking` 출력 = `<축자 · 변경 0 확인>` ⑤소비자 = 해당 없음 ⑥마이그레이션 = **0건** ⑦승인 = 불요(㉮ 밖 · 계약 미접촉) ⑧이번에 세지 않은 축 = 대표 그림 저장 경로(WU-C2 별건) `[미측정]` |
```
⛔ **HANDOFF 에는 값을 적지 않는다**(`CLAUDE.md §6-3`).

### ㉲ 게이트 — 작업 중엔 단독, 병합 전엔 전건

```bash
# 작업 중 (단독 게이트만 하나씩)
./gates/run.sh frontend-typecheck        # 5건 전부
./gates/run.sh frontend-test             # 5건 전부
./gates/run.sh frontend-fixture-reach    # A3
# 병합 직전 한 번
./gates/run.sh all -j 1
```
⛔ **게이트를 끄거나 검사 대상을 줄이지 않는다.** **green 으로 시작한 테스트는 오라클이 아니다** — 실패 테스트 red 를 먼저 확인한다. `frontend-test` 는 **수집된 시험 0건도 red** 다.

### ㉳ 커밋 문면

```
FE 계층 R-A-3 — 상세 수정 진입점·패널 분리·sticky 구역 메뉴·종료 조건·썸네일 넛지 (WU-A3·A7·A8·A9·A10)

- WU-A3 는 현행 DatasetUpdate 필드만 연다 (topic 은 읽기 전용 — R-B 가 category 로 갈아친다)
- WU-A8 은 미결-9 ⓑ 최종형: 정본 §1.3-1 무개정 · 어느 구역도 DOM 에서 숨기지 않는다
- WU-A9·A10 은 WU-A12 회귀 방어선 green 위에서 돌았다
- 계약 0 · 마이그레이션 0 · RED 선실측 → GREEN: <시험 파일>:<건수>
```

### ㉴ 금지

- ⛔ `main` 에 직접 push. ⛔ staging DB 직접 쓰기. ⛔ 원장 행 없이 마이그레이션(이 파일은 마이그레이션 **0**).
- ⛔ `contracts/` 수정(이 파일 범위 밖). ⛔ WU-A3 에서 `topic` 편집 칸 만들기 · R-B 필드 미리 그리기.
- ⛔ WU-A8 에서 탭·패널 전환 만들기 · 정본 개정. ⛔ WU-A9 에서 모달 문면 수정.
- ⛔ WU-A10 에서 저장 경로 만들기. ⛔ WU-A12 green 전에 A9·A10 착수.
- ⛔ `40 COLAB-기획/` 문서 수정. ⛔ 문서·주석에 절대경로. ⛔ 이 세션이 `03-HANDOFF.md` 를 직접 고치기.

---

## 4. 산출물과 근거

| 무엇 | 어디 |
|---|---|
| 프론트 | `components/detail/`(A3 수정 진입점) · `components/upload/RegisterArea.tsx`(A7) · `routes/DatasetDetailPage.tsx` ＋ `shell/`·`detail.css`(A8) · `components/upload/UploadModal.tsx`(A9) · `components/upload/PreviewPanel.tsx`(A10) |
| 시험 | WU 마다 실패 테스트 red 선실측 → green. A9 는 「문면 문자열 불변」 단언을 포함한다 |
| 세션 노트 | `dev-package/sessions/p3-detail-edit-<YYYYMMDD>.md` · `p3-project-panels-…` · `p3-detail-sticky-…` · `p3-close-guard-…` · `p3-thumb-nudge-…` — **각 ≤ 60행** |
| 대장 | `dev-package/work-items.yaml` — 위 다섯 블록. 완료 시 `status: done` ＋ `evidence` 갱신 |
| 원장 | `PLAN-SoT §9` 한 행(㉱ 문안) — **병합 직전 · 결정이 생겼을 때만** |

**오케스트레이터에 넘기는 HANDOFF 갱신문 — 5줄 이하. 세션이 `03-HANDOFF.md` 를 직접 고치지 않는다.**

```
R-A-3(FE) 완료 — WU-A3·A7·A8·A9·A10, 레인 p3-detail-edit·p3-project-panels·p3-detail-sticky·p3-close-guard·p3-thumb-nudge, 병합 <sha…>
WU-A3 이 상세 수정 골격(진입점·권한 게이트·저장 왕복)을 세웠다 — R-B WU-B3 이 필드만 늘린다
WU-A8 = 미결-9 ⓑ 최종형 (정본 §1.3-1 무개정 · DOM 숨김 0 증명) · WU-A9 문면 불변
계약 0 · 마이그레이션 0 · staging 접촉 0 · 게이트 frontend-* 전건 green
근거: dev-package/sessions/p3-detail-edit-<YYYYMMDD>.md 외 4건
```

---

## 5. 완료 판정

- **WU-A3** — 상세에 `수정` 진입점이 있고 권한 없으면 **안 보이며** API 직접 호출도 거절 · 이름만 바꾼 저장이 **나머지를 안 건드린다** · 저장 뒤 바뀐 값으로 검색된다 · `주제` 는 **읽기 전용** · R-B 필드가 **그려져 있지 않다**.
- **WU-A7** — 국가과제·논문 두 패널이 각각 행을 쌓는다 · 0건 패널도 **빈 상태로 남는다** · `+ 새 프로젝트 만들기` 가 화면에 **한 개**.
- **WU-A8** — 메뉴가 sticky 로 남는다 · 스크롤에 따라 활성 표시 · **어느 구역도 DOM 에서 숨겨지지 않았다**(정본 §1.3-1 준수 증명).
- **WU-A9** — 빈 상태 닫기는 **안 묻고** · 한 글자라도 적었으면 묻고 · 계보 부모 1건이면 묻는다 · **문면 문자열이 종전과 같다**.
- **WU-A10** — ② 단계에 썸네일 ＋ 교체 안내가 읽히고 클릭하면 파일 선택기가 열린다 · **저장 경로를 만들지 않았다**.
- **게이트** — `frontend-typecheck` · `frontend-test` · `frontend-fixture-reach` 전건 green, 그리고 병합 직전 `./gates/run.sh all -j 1` green.
- **절차** — WU-A9·A10 착수 시점에 WU-A12 방어선이 green 이었음이 커밋 순서로 보인다.

---

### 다음 파일

`dev-package/prd/rounds/R-A-4-verify.md`(실측 ＋ R-A 종료 검증).
⚠ 그 파일의 **§A(WU-A12)는 이 파일의 WU-A9·A10 보다 먼저** 돌아야 한다.
