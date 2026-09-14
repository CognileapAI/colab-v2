# 이태헌 1차 검증 — 조사 B (계정 관리 · 연구실 설정)

- 입력 = `dev-package/reports/issues/2026-09-13-lth-review-1-raw.md` (D-3·D-4·D-6·D-7·I-4·I-5·I-8)
- 조사 사본 = 워크트리 `worktree-lth-review-260913` · HEAD `2e45ce9a` · dev 실적용 코드 sha `6ff0eecd`(이후 커밋은 문서 전용)
- 역할 = researcher(읽기 전용) · 코드·게이트 무접촉 · 이 파일 1건만 작성
- 인용 = `파일:앵커문자열`. 행 번호는 앵커 보조로만 병기
- 관측 방식 = 코드 정적 대조. 실행 중 화면 관측 0건

---

## D-3 `/account-admin` 본문 영역(`<main>`) 중첩

### 1. 재현/확인 — 확인됨

- 셸이 `<main>` 을 소유한다 — `frontend/src/shell/AppLayout.tsx` 앵커 `<main className="appmain">` 안에 `<Outlet />` 이 든다.
- `/account-admin` 은 그 `Outlet` 자리다 — `frontend/src/app/routes.tsx` 앵커 `<Route path="/account-admin" element={<AccountAdminPage />} />` 가 같은 파일 앵커 `<Route element={<AppLayout />}>` 의 자식이다.
- 화면 자신이 또 `<main>` 을 낸다 — `frontend/src/routes/AccountAdminPage.tsx` 앵커 `<main className="login">`.
- 운영자 아닌 경우의 조기 반환도 같다 — 같은 파일 앵커 `if (!operator) return <main><h1>계정 관리</h1>`.
- 근원 = 이 화면이 로그인 화면 레이아웃(`login` 클래스 계열) 마크업을 재사용하면서 `<main>` 까지 가져왔다. `LoginPage`·`PasswordChangePage` 는 `AppLayout` 밖 라우트라 그쪽 `<main>` 은 정당하다 — `frontend/src/auth/LoginPage.tsx` 앵커 `<main className="login">`.
- 계수 = `<main` 전수 **6자리** (기준 = `grep -rn "<main" frontend/src`): `AppLayout` 1 · `LoginPage` 1 · `PasswordChangePage` 1 · `AccountAdminPage` 2 · (닫는 태그 제외). 다른 화면은 중첩 0.

### 2. 의도 대조

- `BO-1`·`BO-2` 완료 정의에 본문 영역(landmark) 조항 0건 — `dev-package/work-items.yaml` 앵커 `id: BO-1` · `id: BO-2`.
- 기존 접근성 등재분은 색 대비·글자 크기 계열뿐 — `dev-package/work-items.yaml` 앵커 `대비 3건(1·3·7)이 접근성 합격선`(WU-A11·WU-B11). landmark·제목 단계 항목 0건.
- 게이트에 접근성 검사 없음 — `gates/run.sh` 에 `a11y`·`accessib` 0건.
- 판정 = 기존 결정 없음 · 기존 항목 없음 · **신규**. 의도된 동작 아님(레이아웃 재사용의 부수 효과).

### 3. 원인 분류

결함(마크업).

### 4. 수정 범위 추정

- 파일 1 = `frontend/src/routes/AccountAdminPage.tsx` (두 자리의 `<main>` → `<div>`/`<section>`).
- `contracts/` 변경 0 · core-api 변경 0 · 계약 파괴 없음.
- 크기 S. 회귀 시험 자리 = `frontend/test/account-admin.test.tsx`(기존 파일).

### 5. 판정 질문

필요 없음 — 수정 방향이 하나다.

---

## D-4 비활성 계정이 구성원 권한 표에 상태 없이 편집 가능 상태로 표시

### 1. 재현/확인 — 확인됨 (원인 둘)

- 권한 표를 먹이는 API = `GET /lab/members` — `frontend/src/components/members/port.ts` 앵커 `await api.GET('/lab/members')`.
- **계약에 상태 필드가 아예 없다** — `contracts/seams/fe-core.yaml` 앵커 `LabMember:` 의 `required: [accountId, name, email, role, permissions, editablePermissions]` 이고 `properties` 에 `status`·`isActive` 0건. 화면이 칩을 그릴 값을 받지 못한다.
- **서버 질의도 상태를 읽지 않는다** — `services/core-api/src/colab_core/domains/d1_identity.py` 앵커 `_MEMBERS = text(` 본문 축자:
  > `SELECT a.id, a.name, a.email`
  > `  FROM d1_account a`
  > ` WHERE a.lab_id = current_lab_id()`

  상태 열·상태 조건 0건. `services/core-api/src/colab_core/app/routes/members.py` 앵커 `def _grid(` 이 이 목록을 그대로 행으로 만든다.
- **상태의 실제 자리가 다른 스키마다** — `db/platform/versions/0028_account_status.py` 앵커 `ALTER TABLE account_admin.login_credential` ＋ `ADD COLUMN status text NOT NULL DEFAULT 'active'`. `d1_account` 에는 상태 열이 없다(`db/platform/schema.sql` 앵커 `CREATE TABLE d1_account (` — 열 6개에 상태 없음).
- `account_admin` 은 앱 롤 접근을 차단한 스키마다 — `db/platform/schema.sql` 앵커 `-- Stage 3 관리자 자격은 일반 앱 롤이 접근할 수 없는 별도 스키마에 둔다.` ＋ 앵커 `REVOKE ALL ON SCHEMA account_admin FROM PUBLIC;`. ⟹ `GET /lab/members`(`scoped_db` 롤)가 상태를 읽으려면 권한 경로를 새로 연다.
- 편집 가능 판정이 역할만 본다 — `services/core-api/src/colab_core/app/routes/members.py` 앵커 `def _editable_permissions(` (교수 행 `[]` · 교수 열람자 전체 · 위임자 2열). 상태 분기 0건.
- 저장 경로도 같다 — 같은 파일 앵커 `def save_lab_member_permissions(` 의 검사 4종(정규 ID · `member_exists` · 스위치 4종 · `editable`)에 상태 검사 0건.
- 화면은 서버가 준 것만 읽는다 — `frontend/src/components/members/permissions.ts` 앵커 `export function isEditable(` 축자 주석 「이 요청자가 이 칸을 고칠 수 있는가 — **서버가 실어 준 배열만** 읽는다 (P-31)」. ⟹ 화면 단독 수정으로 닫히지 않는다.

### 2. 의도 대조

- `BO-2` 범위 밖 축자 = `dev-package/work-items.yaml` 앵커 `id: BO-2` 의 `note` — 「범위 밖 = 메일 발송 전반 · 역할·연구실 변경 UI · 운영자 지정 UI · 모든 기기 로그아웃 버튼」. 구성원 권한 표 상태 표시는 이 목록에도 `completion_def` 에도 없다 ⟹ 범위 밖으로 명시된 것도 아니고 요구된 것도 아니다.
- `BO-3` 범위 밖 = 「특정 연구실 하나로 좁히는 전환 동작 · 관리자의 타 연구실 반출」 — 같은 파일 앵커 `id: BO-3` 의 `note`. 이 항목도 아니다.
- `dev-package/PLAN-SoT.md` 앵커 `〈384〉` 의 후속 7건(ⓐ~ⓖ)에 구성원 권한 표 항목 0건.
- 같은 유형의 선례가 그 원장 행에 있다 — `dev-package/PLAN-SoT.md` 앵커 `〈384〉` ⑥ⓑ 축자:
  > **비활성 계정이 파일 자격(`TrackedPasswordIssuer`)·접속 코드(`TrackedPlantedCodeIssuer`) 경로로는 그대로 201 이던 것**(`47fe20bb`)

  「`status` 를 보는 코드가 DB 자격 경로 하나뿐」이라는 같은 구조의 세 번째 경로가 이번 D-4 다 `[추론]`.
- 판정 = 기존 결정 없음 · 기존 항목 없음 · **신규**. 관측 동작은 의도된 것이 아니다.

### 3. 원인 분류

미구현(대장 항목 없음) ＋ 설계 차이(Ted 판정 필요). 상태를 권한 표에 노출할지가 제품 판정이고, 노출하면 계약 ＋ 스키마 경계 ＋ 롤 권한이 함께 움직인다.

### 4. 수정 범위 추정

- 계약 = `contracts/seams/fe-core.yaml` `LabMember` 에 상태 필드 1개. `required` 에 넣으면 **계약 파괴**(기존 소비자·시험), optional 이면 비파괴.
- core-api = `services/core-api/src/colab_core/domains/d1_identity.py`(`_MEMBERS`) · `app/routes/members.py`(`_grid`·`_editable_permissions`·저장 검사) · 상태 조회 경로(`kernel/db_credentials.py` 의 계정 상태 조회 재사용 또는 새 Port).
- DB·롤 = `account_admin` 읽기를 `GET /lab/members` 경로에 열 것인가의 판정. `services/core-api/ops/account-admin-role.sql` 이 dev(RDS)에서 통째로 실패한 이력 — `dev-package/PLAN-SoT.md` 앵커 `〈384〉` ⑨ⓐ. 마이그레이션 필요 여부 `[미확인]`(해소 = 상태를 `d1_account` 로 투영할지 `account_admin` 을 직접 읽을지 판정 후 결정).
- frontend = `frontend/src/components/members/MemberPermissionGrid.tsx`(상태 칩 ＋ 행 편집 잠금) · `permissions.ts`(타입) · 시험.
- 크기 M~L.

### 5. 판정 질문 (Ted)

**사용자가 보는 것** — 연구실 설정의 구성원 권한 표에 퇴소·비활성 처리된 사람이 현재 구성원과 똑같이 한 줄로 보이고, 그 사람의 업로드·프로젝트 생성 권한을 켜고 끌 수 있다. 계정 관리 화면에서는 같은 사람이 「비활성」으로 나온다. 두 화면이 같은 사람을 다르게 말한다.

**두 갈래의 대가**

- ⓐ 표에 「비활성」 표시를 붙이고 그 줄의 권한 편집을 막는다 — 오해가 사라지고 재활성화 때 권한이 남는 사고를 막는다. 대가 = 계정의 활성 상태를 연구실 설정 화면까지 전달하는 경로를 새로 연다(계정 관리 전용으로 격리해 둔 자리를 한 칸 연다). 교수가 비활성 계정의 권한을 미리 정리하려면 먼저 다시 활성화한다.
- ⓑ 「비활성」 표시만 붙이고 편집은 지금처럼 둔다 — 전달 경로는 같게 열리고 교수가 퇴소자 권한을 미리 내릴 수 있다. 대가 = 비활성인 사람에게 권한이 켜진 상태가 남을 수 있다.
- ⓒ 지금 그대로 둔다 — 작업 0. 대가 = 두 화면이 같은 사람을 다르게 말하는 상태가 남는다.

**권고** — ⓐ. 계정 관리 화면이 이미 「비활성」을 판정 기준으로 쓰고 있고, 권한 편집은 되살아난 뒤에 하는 것이 순서에 맞다.

---

## D-6 `/lab-settings` 제목 단계가 h3 부터 시작

### 1. 재현/확인 — 확인됨

- 화면 본체에 h1·h2 가 0건 — `frontend/src/routes/LabSettingsPage.tsx` 전문 47줄에 `<h1`·`<h2` 0건. 최상위는 앵커 `<div className="settings-page" data-screen="S-07">` ＋ 탭 목록 앵커 `<div className="settabs" role="tablist" aria-label="연구실 설정 탭">`(버튼 라벨 `연구실 정보`·`구성원 · 권한`).
- 탭 본체 둘이 각각 h3 로 시작한다 — `frontend/src/components/lab/LabInfoPanel.tsx` 앵커 `<h3>연구실 정보</h3>` · `frontend/src/components/members/MemberPermissionGrid.tsx` 앵커 `<h3>구성원 · 권한</h3>`.
- 근원 = 두 패널이 카드 컴포넌트(`<div className="card ...">` ＋ `<div className="card-h">`)로 설계되고 카드 머리 제목을 h3 로 고정했다. 그 카드를 담는 화면이 h1 을 두지 않아 단계가 비었다.
- 같은 화면의 모달 제목도 h3 — `MemberPermissionGrid.tsx` 앵커 `<h3>권한을 이렇게 바꿀까요?</h3>`.
- **같은 유형이 `/lab` 에도 있다** — `frontend/src/routes/LabPage.tsx` 에 `<h1` 0건이고 카드 제목이 h2 다: `frontend/src/components/dashboard/DataMapCard.tsx` 앵커 `<h2>우리 연구실 데이터 맵</h2>` · `TodoInbox.tsx` 앵커 `<h2>할 일 함</h2>` · `RecentActivity.tsx` 앵커 `<h2>최근 활동</h2>` · `EmptyLabOnboarding.tsx` 앵커 `<h2>이렇게 시작해요</h2>`.
- h1 을 두는 화면은 **4곳** (기준 = `grep -rn "<h1" frontend/src/routes`): `DatasetsPage.tsx` 앵커 `<h1>데이터셋</h1>` · `ProjectsPage.tsx` 앵커 `<h1>프로젝트</h1>` · `ProjectDetailPage.tsx` 앵커 `<h1>{detail.name}</h1>` · `SearchResultsPage.tsx` 앵커 `<h1>검색 결과</h1>`.

### 2. 의도 대조

- 제목 단계 규약이 레포에 없다 — `dev-package/work-items.yaml` 에 `제목 단계`·`heading` 0건.
- 두 패널 제목이 목업 계열이라는 표시는 있다 — `frontend/src/components/members/members.css` 앵커 ``연구실 설정 두 탭 — `연구실 정보` / `구성원 · 권한` (IA_사이트맵 §3 · 목업 `.settabs`)``. 단계(h3)가 목업 지정인지는 `[미확인]`(해소 = `40 COLAB-기획/10_적용전/` 의 S-07 목업 HTML 에서 해당 제목 태그를 읽는다 — 읽기 전용 경로).
- 판정 = 기존 결정 없음 · 기존 항목 없음 · **신규**. 의도된 동작 아님.

### 3. 원인 분류

결함(마크업). 범위를 `/lab` 까지 넓히면 설계 차이(화면 대표 제목 규약 신설).

### 4. 수정 범위 추정

- 최소안(이 화면만) = `frontend/src/routes/LabSettingsPage.tsx` 에 h1 1개 ＋ 두 패널 h3 → h2. 파일 3 · 크기 S.
- 전체안(규약) = `/lab` 포함 화면 전수의 대표 제목 ＋ 카드 제목 단계 정리. 파일 10+ · 크기 M. 글자 크기 유지를 위해 CSS 에 단계별 크기 고정이 따른다.
- `contracts/` 0 · core-api 0 · 계약 파괴 없음.

### 5. 판정 질문 (Ted)

**사용자가 보는 것** — 연구실 설정 화면에 그 화면의 이름이 제목으로 없다. 화면 읽기 프로그램으로 제목만 훑으면 「연구실 정보」·「구성원 · 권한」이 무슨 화면의 구역인지 알 수 없다. 연구실 홈도 같은 상태다.

**두 갈래의 대가** — ⓐ 연구실 설정 한 화면만 고친다(작업 작음 · 연구실 홈은 같은 상태로 남음) ⓑ 모든 화면에 대표 제목을 두는 규약을 세운다(일관됨 · 화면 10곳 이상 손대고 글자 크기가 바뀌지 않는지 확인이 따름).

**권고** — ⓑ 로 규약을 세우고 이번 회차는 ⓐ 범위로 집행한다. 나머지 화면은 같은 항목의 후속으로 둔다.

---

## D-7 「할 일 함」 문면 — 오탈자 아님 (지시문 전제와 실물이 갈린다)

### 1. 재현/확인 — 문자열 확인됨 · 오탈자 판정은 부정

- 사용자에게 보이는 자리 **정확히 2건** (계수 기준 = `grep -rn "할 일 함" frontend/src` 결과에서 주석·JSDoc 제외):
  - `frontend/src/components/dashboard/TodoInbox.tsx` 앵커 `<h2>할 일 함</h2>` (연구실 홈 `내 일` 구역)
  - `frontend/src/components/members/MemberPermissionGrid.tsx` 앵커 `승인 위임을 켜면 그 연구원의 할 일 함에 접근 요청이 들어오고` (연구실 설정 권한 안내)
- 두 자리 모두 목업 축자라고 코드가 명시한다 — `MemberPermissionGrid.tsx` 바로 위 앵커 `{/* 목업 하단 안내문 — 한 자도 바꾸지 않았다 */}` · `TodoInbox.tsx` 앵커 `목업 축자 「할 일 함 · 14건」`.
- **「할 일 함」은 레포 전역의 확정 용어다** — 같은 표기가 계약·정본·원칙 문서에 전부 쓰였다.
  - 계약 = `contracts/seams/fe-core.yaml` 앵커 `summary: 받은 접근 요청 (할 일 함 그룹)` · 앵커 `summary: Verified 검토 대기 (교수 할 일 함 그룹)`
  - 도메인 = `dev-package/DOMAINS.md` 앵커 `활동 기록 타임라인 · 할 일 함 집계`
  - 권한 원칙 = `dev-package/PERMISSION-PRINCIPLES.md` 앵커 `P-16. 권한 훅은 최소 단위에 건다.` 의 축자 「할 일 함이 선례다」
  - 작업 단위 = `dev-package/WORK-UNITS.md` 앵커 `비워 둘 자리 3곳(Verified 배지·잠금 표시·할 일 함)` · 앵커 `연구실 대시보드 — 데이터 맵(계보 상태별·주제별) · 할 일 함`
  - 기획 정본 개정 기록 = `dev-package/PLAN-SoT.md` 앵커 `〈281〉` 축자 「숨기는 자리 **8행** · 서버 재판정 **10행** · 할 일 함 **3그룹**」(`Policy_역할과_권한` v1.4)
- 「할 일함」·「할일함」·「할 일 목록」 표기는 레포 전역 **0건** (기준 = `grep -rn "할 일함\|할일함\|할 일 목록"`).
- 용어 전용 파일(`strings*`·`i18n`·`copy`)은 존재하지 않는다 — `frontend/src` 에 해당 이름 0건. 용어의 자리는 목업 HTML ＋ 정본 md 이고 원본은 `40 COLAB-기획/10_적용전/`(읽기 전용).
- ⟹ **지시문의 「오탈자」 전제와 실물이 갈린다.** 코드만 바꾸면 `.claude/rules/colab-rules.md §7`(코드를 기획에 맞추는 방향이 기본)과 반대 방향이 된다. 이 항목은 여기서 멈추고 갈림을 보고한다.

### 2. 의도 대조

- 대장·원장에 이 문면 항목 0건.
- 판정 = 관측 문자열은 **의도된 것**이다(목업 축자 ＋ 정본 표기 일치).

### 3. 원인 분류

문면 — 결함이 아니라 기획 정본 용어. 바꾸려면 기획 정본 개정(Ted 판정 ＋ 번호 · 선례 `〈232〉`·`〈245〉`·`〈254〉`·`〈281〉`)이 선행한다.

### 4. 수정 범위 추정

- 정본 유지 시 = 수정 0.
- 표기 변경 승인 시 = `frontend/src/components/dashboard/TodoInbox.tsx` · `frontend/src/components/members/MemberPermissionGrid.tsx` · `contracts/seams/fe-core.yaml`(summary 2건) · 정본 md ＋ 목업 패키지 재생성(`planning-freshness` 게이트가 대조) ＋ 정본 인용 문서 다수. `contracts/` 변경 있음(설명 문면만 · 계약 파괴 없음). 크기 M(문서 쪽 비중).

### 5. 판정 질문 (Ted)

**사용자가 보는 것** — 연구실 홈의 「할 일 함」 구역 이름, 그리고 연구실 설정의 권한 안내 문장. 검증자는 이것을 띄어쓰기 오류로 읽었다.

**두 갈래의 대가** — ⓐ 지금 표기를 유지한다(작업 0 · 기획 문서·계약·화면이 한 이름으로 일치한 상태가 유지됨 · 검증자에게 「정한 용어」로 회신) ⓑ 이름을 바꾼다(지적 반영 · 기획 정본 개정 ＋ 목업 패키지 재생성 ＋ 계약 설명 ＋ 화면 2곳을 한 회차에 함께 움직인다. 안 맞으면 게이트가 red 를 낸다).

**권고** — ⓐ. 바꿀 이유가 생기면 기획 정본 쪽에서 먼저 정한다.

---

## I-4 모바일 `/account-admin` 표에 좌우 이동 안내 없음

### 1. 재현/확인 — 확인됨

- 공용 안내 클래스가 있다 — `frontend/src/shell/design-system.css` 앵커 `.table-scroll-hint { display: none; }` ＋ 앵커 `@media (max-width: 1100px)` 안의 `.table-scroll-hint { display: block;`. 1100px 이하에서만 보인다.
- 세 표가 그것을 쓴다(감싼 div 에 `role="region"` ＋ `tabIndex={0}` 동반):
  - `frontend/src/components/catalog/CatalogTable.tsx` 앵커 `<p className="table-scroll-hint">표를 좌우로 밀면 나머지 항목과 작업을 볼 수 있어요.</p>` ＋ 앵커 `<div className="tblwrap" data-scroll="both" role="region" aria-label="데이터셋 표 스크롤" tabIndex={0}>`
  - `frontend/src/components/project/ProjectTable.tsx` 앵커 `<p className="table-scroll-hint">표를 좌우로 밀면 나머지 항목을 볼 수 있어요.</p>` ＋ 앵커 `<div className="pj-ds-scroll" role="region" aria-label="프로젝트 표 스크롤" tabIndex={0}>`
  - `frontend/src/components/project/ProjectDatasetTable.tsx` 앵커 `<p className="table-scroll-hint">표를 좌우로 밀면 나머지 항목과 작업을 볼 수 있어요.</p>`
- **계정 표는 그 래퍼를 재사용하지 않는다** — `frontend/src/routes/AccountAdminPage.tsx` 앵커 `<div className="account-table-scroll">` 하나뿐이고, 안내 `<p>` 0건 · `role="region"` 0건 · `tabIndex` 0건.
- 래퍼 CSS 도 독자적이다 — `frontend/src/auth/login.css` 앵커 `.account-table-scroll { margin-top: 16px; overflow-x: auto; }`. 가로 스크롤은 동작하므로 lth 관측과 일치한다.
- 근원 = 계정 관리 화면이 로그인 레이아웃 CSS(`login.css`) 계열로 따로 지어져 공용 표 패턴(`design-system.css` ＋ `tblwrap`)을 경유하지 않았다. D-3 과 같은 근원이다.
- 표 실제 폭 약 950px 은 lth 측정값이고 이 조사에서 재지 않았다 `[미확인]`. `.account-table` 에 `min-width` 선언 0건(`frontend/src/auth/login.css` 앵커 `.account-table { width: 100%; border-collapse: collapse;`)이라 내용 폭에서 나온 값이다 `[추론]`. 해소 = 390px 뷰포트에서 `scrollWidth` 실측.
- 키보드로 래퍼에 초점이 가지 않는 것은 마크업상 확인됨(`tabIndex` 부재). 실제 스크롤 동작은 `[미확인]`.

### 2. 의도 대조

- `BO-2` 완료 정의는 열 6개 ＋ 필터까지다 — `dev-package/work-items.yaml` 앵커 `id: BO-2` 의 `completion_def` ⑴. 모바일·스크롤 안내 조항 0건.
- lth 가 정상 동작으로 확인한 항목에 「데이터셋·프로젝트 표의 모바일 좌우 이동 안내」가 있다 — `dev-package/reports/issues/2026-09-13-lth-review-1-raw.md` §5. ⟹ 패턴은 제품 기준으로 성립해 있고 계정 표만 빠졌다.
- 판정 = 기존 결정 없음 · 기존 항목 없음 · **신규**. 의도된 누락이라는 근거 0건.

### 3. 원인 분류

결함(기존 공용 패턴 미적용).

### 4. 수정 범위 추정

- 파일 1~2 = `frontend/src/routes/AccountAdminPage.tsx`(안내 `<p className="table-scroll-hint">` ＋ `role="region"`·`aria-label`·`tabIndex={0}`) · 필요 시 `frontend/src/auth/login.css`(또는 `.account-table-scroll` 을 공용 `tblwrap` 으로 교체).
- `contracts/` 0 · core-api 0 · 계약 파괴 없음. 크기 S.
- lth 추가 권고(이메일 열 고정 · 모바일 카드 목록)는 별건 · 크기 M.

### 5. 판정 질문

필요 없음 — 기존 패턴 적용이고 제품 기준이 이미 정해져 있다. 열 고정·카드 목록까지 갈지는 별도 판정 대상.

---

## I-5 본인 계정 비활성화 — 서버는 막고 화면은 누를 수 있다

### 1. 재현/확인 — 확인됨 (서버 가드 존재 · 화면 가드 부재)

- 화면: 관리자 해제 버튼만 자기 행에서 비활성 — `frontend/src/routes/AccountAdminPage.tsx` 앵커 `disabled={rowBusy || row.accountId === account?.accountId}` (라벨 앵커 `{row.operator ? '관리자 해제' : '관리자 지정'}`).
- 같은 행의 비활성화 버튼은 자기 검사가 없다 — 같은 파일 앵커 `disabled={rowBusy}` ＋ 라벨 앵커 `{row.status === 'inactive' ? '재활성화' : '비활성화'}`.
- 화면 주석이 이 갈림을 스스로 설명한다 — 같은 파일 앵커 `자기 자신 해제는 화면에서 막는다 — 되살릴 사람이 없어지는 자리라` 의 축자:
  > 서버도 400 을 내지만, 누를 수 있게 두면 그 거절이 사고처럼 보인다.

  그 규칙이 관리자 해제에만 적용되고 비활성화에는 적용되지 않았다.
- **서버에 본인 비활성화 가드가 있다** — `services/core-api/src/colab_core/app/routes/accounts.py` 앵커 `def set_account_status(` 안:
  > `if body.status == "inactive" and account_id == str(subject.account_id):`
  > `    raise errors.bad_request("자기 계정은 비활성화할 수 없다.")`

  ⟹ 실제 사고는 발생하지 않고, 사용자는 누를 수 있고 400 을 받는다.
- **「마지막 남은 관리자」 가드는 관리자 해제에만 있다** — `services/core-api/src/colab_core/kernel/db_credentials.py` 앵커 `def set_operator(` 의 두 거절:
  > `raise OperatorChangeRefused("자기 자신의 관리자 권한은 해제할 수 없다. 다른 관리자에게 요청한다.")`
  > `raise OperatorChangeRefused("마지막 관리자는 해제할 수 없다. 먼저 다른 관리자를 지정한다.")`

  셈은 잠금 아래다 — 같은 함수 앵커 `db.execute(text(_OPERATOR_LOCK))`.
- **비활성화 경로에는 관리자 수를 세는 자리가 없다** — 같은 파일 앵커 `def set_status(` 전문에 `service_operator` 0건이고 잠금은 대상 행 `FOR UPDATE` 하나(앵커 `SELECT status FROM account_admin.login_credential`). ⟹ 관리자 A 가 다른 관리자 B 를 비활성화하는 것은 허용된다. 본인 가드 때문에 활성 관리자가 0명이 되지는 않는다 `[추론]`(해소 = 관리자 2명 환경에서 B 비활성화 후 `service_operator` ⋈ `login_credential.status` 교차 실측).
- 확인 대화상자는 이미 있다 — 같은 화면 앵커 `<StatusDialog row={statusRow}`. 계정명 재입력 요구 유무는 `[미확인]`(해소 = `StatusDialog` 본문 확인).

### 2. 의도 대조

- `BO-3` 완료 정의 ⑵ 축자 = `dev-package/work-items.yaml` 앵커 `id: BO-3` — 「자기 자신 해제와 마지막 관리자 해제는 400 으로 거절된다(마지막 한 명 셈은 잠금 아래 · 동시 해제에도 관리자 1명 이상이 남는다)」. **대상이 관리자 해제다.** 비활성화의 같은 조항은 없다.
- `BO-2` 완료 정의 ⑶ = 같은 파일 앵커 `id: BO-2` — 「비활성화 즉시 로그인 거절 ＋ 기존 로그인 전부 종료」. 본인 보호·관리자 잔존 조항 0건.
- 판정 = 서버 쪽은 **이미 결정·구현됨**. 화면 `disabled` 누락은 기존 항목 없음 · **신규**. 관측 동작(누를 수 있음)은 의도된 것이 아니다 — 같은 파일 주석이 반대를 말한다.

### 3. 원인 분류

결함(화면 가드 누락). 계정명 재입력·관리자 잔존 셈까지 올릴지는 설계 차이(Ted 판정).

### 4. 수정 범위 추정

- 최소안 = `frontend/src/routes/AccountAdminPage.tsx` 비활성화 버튼에 자기 자신 조건 추가(관리자 해제와 같은 식) ＋ 비활성 이유 안내. 파일 1 · 시험 `frontend/test/account-admin.test.tsx`. `contracts/` 0 · core-api 0 · 계약 파괴 없음 · 크기 S.
- 확장안 = 비활성화에 계정명 입력 재확인 ＋ `set_status` 에 잠금 아래 활성 관리자 셈 추가. `services/core-api/src/colab_core/kernel/db_credentials.py` ＋ `app/routes/accounts.py` ＋ 시험. 크기 M · 계약 파괴 없음(거절 문구는 봉투 `message` 로 전달).

### 5. 판정 질문 (Ted)

**사용자가 보는 것** — 계정 관리 목록에서 자기 줄의 「비활성화」 버튼을 누를 수 있다. 누르면 확인 창이 뜨고, 확인하면 서버가 「자기 계정은 비활성화할 수 없다」로 거절한다. 같은 줄의 「관리자 해제」는 처음부터 눌리지 않는다.

**두 갈래의 대가**

- ⓐ 자기 줄의 비활성화 버튼을 처음부터 못 누르게 한다 — 관리자 해제와 같은 모양이 되고 거절이 사고처럼 보이지 않는다. 대가 = 작업은 작고, 「왜 안 되는지」를 버튼 옆에 적어야 비활성 버튼이 고장으로 보이지 않는다.
- ⓑ 더해서, 남은 관리자가 본인뿐인 계정을 끄려 할 때도 막고 계정명을 직접 입력하게 한다 — 관리자 전원이 꺼지는 경로가 추가로 닫힌다. 대가 = 서버에 관리자 수를 세는 판정이 하나 더 생기고 정상 퇴소 처리도 한 단계 길어진다.

**권고** — ⓐ 를 이번에 집행한다. 현재 구조에서는 본인 비활성화가 서버에서 막혀 활성 관리자 0명 상태가 나오지 않는다(위 `[추론]` 확인 후 확정). ⓑ 는 그 확인 결과를 보고 별 항목으로 둔다.

---

## I-8 서비스 계정 초기 비밀번호 입력에 `autocomplete="new-password"` 없음

### 1. 재현/확인 — 확인됨

- 누락 자리 = `frontend/src/routes/AccountAdminPage.tsx` 앵커:
  > `<label className="login-label">초기 비밀번호<input className="login-input" name="initialPassword" aria-describedby="initial-password-help" type="password" required /></label>`

  `autoComplete` 속성 0건.
- **같은 파일의 비밀번호 재설정 대화상자에는 있다** — 같은 파일 앵커 `<input id={valueId} className="login-input" type="password" autoComplete="new-password"` ＋ 앵커 `<input id={confirmId} className="login-input" type="password" autoComplete="new-password"`. ⟹ 한 화면 안의 불일치다.
- 레포 전역 `autoComplete` 사용 **6건** (기준 = `grep -rn "autoComplete" frontend/src frontend/test`): `frontend/src/auth/LoginPage.tsx` 앵커 `autoComplete="username"` · 앵커 `autoComplete="current-password"` / `frontend/src/auth/PasswordChangePage.tsx` 2건(`new-password`) / `AccountAdminPage.tsx` 2건(`new-password`). 소문자 `autocomplete` 는 0건.
- 근원 = 계정 추가 폼이 재설정 대화상자보다 먼저 지어졌고(`BO-1` → `BO-2`) 뒤에 세운 쪽에만 속성이 붙었다 `[추론]`.

### 2. 의도 대조

- `BO-1` 완료 정의 = `dev-package/work-items.yaml` 앵커 `id: BO-1` — 이메일·역할·연구실 등록 ＋ 초기 비밀번호 직접 입력 ＋ 첫 로그인 변경 강제. 자동완성 조항 0건.
- `BO-2` 완료 정의·`note` 에도 조항 0건.
- 판정 = 기존 결정 없음 · 기존 항목 없음 · **신규**. 같은 파일의 선례가 반대 방향이다.

### 3. 원인 분류

결함(같은 화면 내 불일치 누락).

### 4. 수정 범위 추정

- 파일 1 = `frontend/src/routes/AccountAdminPage.tsx` 의 `name="initialPassword"` 입력에 `autoComplete="new-password"` 1개 추가.
- `contracts/` 0 · core-api 0 · 계약 파괴 없음. 크기 S.

### 5. 판정 질문

필요 없음.

---

## 요약표

| 항목 | 확인 결과 | 분류 | 기존 결정/항목 | 크기 | Ted 판정 필요 |
|---|---|---|---|---|---|
| D-3 `/account-admin` `<main>` 중첩 | 확인됨 — `AppLayout.tsx` `<main className="appmain">` ＋ `AccountAdminPage.tsx` `<main className="login">` 2자리 | 결함(마크업) | 없음 | S | 아니요 |
| D-4 비활성 계정이 권한 표에 상태 없이 편집 가능 | 확인됨 — `LabMember` 계약에 상태 필드 0 · `_MEMBERS` 질의 상태 미조회 · 상태는 `account_admin.login_credential`(앱 롤 접근 차단 스키마) | 미구현(항목 없음) ＋ 설계 차이 | 없음 — `BO-2`·`BO-3` 범위 밖 목록에도 없음 | M~L | 예 |
| D-6 `/lab-settings` h1 없이 h3 시작 | 확인됨 — `LabSettingsPage.tsx` h1·h2 0건 · `LabInfoPanel.tsx`·`MemberPermissionGrid.tsx` 가 `<h3>` · `/lab` 도 h1 0건 | 결함(마크업) ＋ 규약 신설 시 설계 차이 | 없음 | S(이 화면) / M(전 화면) | 예(범위만) |
| D-7 「할 일 함」 | 문자열 2건 확인 · **오탈자 아님** — 계약·`DOMAINS.md`·`PERMISSION-PRINCIPLES.md`·`WORK-UNITS.md`·정본 v1.4 가 같은 표기 · 지시문 전제와 실물 갈림 | 문면(기획 정본 용어) | 정본 표기로 확정 | 0(유지) / M(변경 시) | 예 |
| I-4 모바일 계정 표 좌우 이동 안내 없음 | 확인됨 — 공용 `.table-scroll-hint` 를 3표가 사용, `account-table-scroll` 래퍼만 안내·`role="region"`·`tabIndex` 0건 | 결함(공용 패턴 미적용) | 없음 | S | 아니요 |
| I-5 본인 비활성화 버튼 활성 | 확인됨 — 화면 `disabled={rowBusy}`(자기 검사 없음) / **서버 가드 존재** `accounts.py` 「자기 계정은 비활성화할 수 없다.」 · 마지막 관리자 가드는 `set_operator` 에만 | 결함(화면 가드 누락) ＋ 확장은 설계 차이 | `BO-3` 완료 정의 ⑵ = 관리자 **해제** 한정 | S(최소) / M(확장) | 예(확장 여부) |
| I-8 초기 비밀번호 `autocomplete` 없음 | 확인됨 — `name="initialPassword"` 에 0건, 같은 파일 재설정 입력 2건은 `new-password` | 결함(불일치 누락) | 없음 | S | 아니요 |

---

## 후속 항목 (이 조사에서 고치지 않음 — 읽기 전용 역할)

1. `services/core-api/src/colab_core/app/routes/accounts.py` 앵커 `# 자기를 끄면 되살릴 사람이 없다 — 운영자 지정은 아직 SQL 수동이다.` — `BO-3` 로 운영자 지정 UI 가 선 뒤에도 「SQL 수동」 표기가 남아 있다(문면 정정 1건).
2. 화면 대표 제목(h1) 규약이 레포에 없고 게이트에도 접근성 검사가 없다(`gates/run.sh` 에 `a11y` 0건) — D-3·D-6 유형을 사후에만 발견한다. `CLAUDE.md §3-3`(검사가 게이트에 없으면 그 자체가 결함) 대상 후보.
3. 계정 관리 화면이 로그인 레이아웃 CSS(`frontend/src/auth/login.css`) 계열로 따로 지어져 공용 표·본문 패턴(`frontend/src/shell/design-system.css`)을 경유하지 않는다 — D-3·I-4 의 공통 근원.

## 이 조사에서 재지 않은 것

- 실행 중 화면 관측 0건 — 전부 코드 정적 대조. 390px 표 실제 폭 · 키보드 스크롤 동작 · 권한 표에 비활성 계정 2건이 실제로 보이는지는 `[미확인]`.
- `StatusDialog` 본문(계정명 재입력 유무) `[미확인]`.
- S-07 목업 HTML 의 제목 태그 단계 `[미확인]` — 원본은 `40 COLAB-기획/10_적용전/`(읽기 전용).
- 관리자 2명 환경에서 비활성화 경로로 활성 관리자가 0명이 될 수 있는지 `[미확인]` — I-5 의 `[추론]`.
