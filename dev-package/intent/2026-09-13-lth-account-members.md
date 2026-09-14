# Intent: 계정 관리·구성원 권한 화면의 가드·마크업 5건을 닫는다
메타 — 발의자: 이태헌 · 작성 2026-09-13 · 승인 2026-09-13

## 문제
- 계정 관리 화면이 본문 영역(`<main>`)을 두 겹으로 낸다(`D-3`).
- 휴대전화에서 계정 표가 좌우로 밀리는데 그 안내가 없다 — 데이터셋·프로젝트 표에는 있다(`I-4`).
- 계정 추가 폼의 초기 비밀번호 칸에 새 비밀번호용 자동완성 기준이 없다(`I-8`).
- 자기 줄의 「비활성화」를 누를 수 있고, 누르면 서버가 400 으로 거절한다(`I-5`).
- 비활성 계정이 구성원 권한 표에 상태 없이 현재 구성원처럼 나오고 권한을 켜고 끌 수 있다(`D-4`).

## 원한 결과 (proposed outcome)
- 검증 문장 ⑴ `/account-admin` 의 `<main>` 이 화면당 1개다(`grep -rn "<main" frontend/src` 기준 `AccountAdminPage.tsx` 0건).
- 검증 문장 ⑵ 1100px 이하에서 계정 표 위에 좌우 이동 안내가 보이고 래퍼가 키보드 초점을 받는다.
- 검증 문장 ⑶ 초기 비밀번호 입력에 `autoComplete="new-password"` 가 있다.
- 검증 문장 ⑷ 자기 줄의 「비활성화」가 처음부터 눌리지 않고 그 이유가 화면에 적혀 있다.
- 검증 문장 ⑸ 두 화면이 같은 사람을 다르게 말하지 않는다 — 계정 관리에서 「비활성」인 사람이 구성원 권한 표에서도 그렇게 보인다(판정 ⓐ 채택 시).

## 영향 범위
- 사용자 / 화면: `/account-admin`(관리자) · `/lab-settings` → 구성원 · 권한(교수·위임자).
- 서비스 · 스키마 · 계약:
  - S 묶음 = `frontend/src/routes/AccountAdminPage.tsx` · `frontend/src/auth/login.css` · `frontend/test/account-admin.test.tsx`. core-api·`contracts/` 변경 0.
  - `D-4` 채택 시 = `contracts/seams/fe-core.yaml` 앵커 `LabMember:`(상태 필드 1개 · optional) · `services/core-api/src/colab_core/domains/d1_identity.py` 앵커 `_MEMBERS = text(` · `services/core-api/src/colab_core/app/routes/members.py` 앵커 `def _grid(`·`def _editable_permissions(` · `frontend/src/components/members/MemberPermissionGrid.tsx`.
- 계약 파괴 여부: 아니오 — S 묶음은 계약 무접촉. `D-4` 는 상태 필드를 optional 로 더하면 비파괴이고 `required` 에 넣으면 파괴(그 경우 Ted 서명 필요).

## 제약
- 도메인은 자기 테이블 ＋ D1 만 참조한다 · 조회에 연구실 경계가 자동 주입된다(`CLAUDE.md §3` 규칙 1·5).
- 계정 상태의 실제 자리가 다른 스키마다 — `db/platform/versions/0028_account_status.py` 앵커 `ALTER TABLE account_admin.login_credential` ＋ `ADD COLUMN status text NOT NULL DEFAULT 'active'`. `d1_account` 에 상태 열이 없다.
- 그 스키마는 앱 롤 접근을 차단한다 — `db/platform/schema.sql` 앵커 `REVOKE ALL ON SCHEMA account_admin FROM PUBLIC;` ＋ 앵커 `-- Stage 3 관리자 자격은 일반 앱 롤이 접근할 수 없는 별도 스키마에 둔다.` ⟹ `GET /lab/members`(`scoped_db` 롤)가 상태를 읽으려면 권한 경로를 새로 연다.
- 화면 단독 수정으로 닫히지 않는다 — `frontend/src/components/members/permissions.ts` 앵커 `export function isEditable(` 주석 축자 「이 요청자가 이 칸을 고칠 수 있는가 — **서버가 실어 준 배열만** 읽는다 (P-31)」.
- 본인 비활성화는 서버가 이미 막는다 — `services/core-api/src/colab_core/app/routes/accounts.py` 앵커 `def set_account_status(` 의 `"자기 계정은 비활성화할 수 없다."`.
- 「마지막 관리자」 가드는 관리자 해제 경로에만 있다 — `services/core-api/src/colab_core/kernel/db_credentials.py` 앵커 `def set_operator(`. 비활성화 경로(`def set_status(`)에는 관리자 수를 세는 자리가 없다.
- ⚠ 「활성 관리자 0명 불가」를 보장된 성질로 인용하지 않는다 — `set_status` 의 잠금은 대상 행 `FOR UPDATE` 하나이므로 동시 요청에서의 보장이 아니다 `[미확인]`.
- `ops/account-admin-role.sql` 이 dev(RDS)에서 통째로 실패한 이력 — `dev-package/PLAN-SoT.md` 앵커 `〈384〉` ⑨ⓐ.

## 설계트리 (grill-me 결과)
- Q1 판정 없이 바로 집행할 수 있는 것은 → A 4건. `D-3`(`<main>`→`<div>`/`<section>`) · `I-4`(공용 `.table-scroll-hint` ＋ `role="region"`·`tabIndex={0}` 적용) · `I-8`(`autoComplete="new-password"` 1개) · `I-5` 화면 가드(자기 줄 비활성화 `disabled`). 전부 `frontend` 한정 · 크기 **S** · 한 묶음.
  - Q1a 근원이 하나인가 → A `D-3`·`I-4` 는 계정 관리 화면이 로그인 레이아웃 CSS(`frontend/src/auth/login.css`) 계열로 따로 지어져 공용 패턴(`frontend/src/shell/design-system.css` ＋ `tblwrap`)을 경유하지 않은 데서 같이 나온다.
  - Q1b `I-5` 화면 가드의 근거 → A 같은 파일이 관리자 해제에는 같은 규칙을 이미 적용했다 — `frontend/src/routes/AccountAdminPage.tsx` 앵커 `disabled={rowBusy || row.accountId === account?.accountId}` ＋ 주석 축자 「서버도 400 을 내지만, 누를 수 있게 두면 그 거절이 사고처럼 보인다.」 비활성화 버튼은 앵커 `disabled={rowBusy}` 다.
- Q2 `D-4` 를 화면만으로 닫을 수 있는가 → A 아니다. 계약에 상태 필드가 없고(`contracts/seams/fe-core.yaml` 앵커 `LabMember:` 의 `required: [accountId, name, email, role, permissions, editablePermissions]`) 서버 질의도 상태를 읽지 않는다(`_MEMBERS` 의 `SELECT a.id, a.name, a.email`).
  - Q2a 사용자가 보는 것 → A 구성원 권한 표에 퇴소·비활성 처리된 사람이 현재 구성원과 똑같이 한 줄로 보이고 그 사람의 업로드·프로젝트 생성 권한을 켜고 끌 수 있다. 계정 관리 화면에서는 같은 사람이 「비활성」이다.
  - Q2b 선례 → A 같은 구조가 이미 한 번 났다 — `dev-package/PLAN-SoT.md` 앵커 `〈384〉` ⑥ⓑ 의 「비활성 계정이 파일 자격·접속 코드 경로로는 그대로 201 이던 것」. `status` 를 보는 코드가 특정 경로에만 있다는 같은 모양이다 `[추론]`.
  - Q2c 크기 → A **M~L** — 계약 필드 ＋ core-api 읽기 경로 ＋ `account_admin` 읽기 권한 판정 ＋ 화면. 마이그레이션 필요 여부 `[미확인]`(상태를 `d1_account` 로 투영할지 `account_admin` 을 직접 읽을지 판정 후 결정).
- Q3 `I-5` 확장(계정명 재입력 · 활성 관리자 잔존 셈)을 같이 넣는가 → A 별 판정으로 분리한다. 본인 비활성화가 서버에서 막히므로 화면 가드만으로 관측된 불편이 사라지고, 관리자 A 가 다른 관리자 B 를 비활성화하는 경로의 위험은 별도 측정이 선행한다. **(권고안 수용 · Ted 2026-09-13 — 카드 ⑤ ⓐ 화면 가드만 이번에 집행)**

## 미해결 질문
- 해소(Ted 2026-09-13 · 카드 ④) — `D-4` = **ⓐ** 수용. 표에 「비활성」 칩을 붙이고 그 줄의 권한 편집을 막는다(계약 필드 ＋ core-api 읽기 경로 · **M~L**). 근거 = 계정 관리 화면이 이미 「비활성」을 판정 기준으로 쓴다.
- 해소(Ted 2026-09-13 · 권고안 수용) — 경계 처리 = **ⓐ-1** 상태를 `d1_account` 로 투영(마이그레이션 1건 · 앱 롤 권한 무변 · `CLAUDE.md §3` 규칙 1·5 무접촉). 투영 비용 `[미확인]` 은 구현 레인에서 측정한다.
- 해소(Ted 2026-09-13 · 카드 ⑤) — `I-5` = **ⓐ** 화면 가드만 이번에 집행. ⓑ(계정명 재입력 ＋ 활성 관리자 셈 · **M**)는 활성 관리자 0명 상태 확인 뒤 별 항목 후보. ⚠ 현재 구조가 활성 관리자 0명을 보장한다고 적지 않는다 `[미확인]`.
- `StatusDialog` 본문의 계정명 재입력 유무 `[미확인]` — 해소 = `frontend/src/routes/AccountAdminPage.tsx` 앵커 `<StatusDialog row={statusRow}` 의 구현 확인.
- 390px 에서 계정 표의 실제 폭(lth 측정 약 950px) `[미확인]` — `.account-table` 에 `min-width` 선언 0건이므로 내용 폭에서 나온 값 `[추론]`.
- 권한 표에 비활성 계정 2건이 실제로 보이는지 `[미확인]` — 이 조사는 코드 정적 대조만 수행.

## 범위 밖 (명시 제외)
- 계정 표의 이메일 열 고정 · 모바일용 카드 목록(lth 추가 권고 · 크기 **M** · 별 항목).
- 역할·연구실 변경 UI · 메일 발송 전반 · 모든 기기 로그아웃 버튼(대장 `BO-2` `note:` 가 범위 밖으로 명시).
- 계정 관리 화면을 `frontend/src/auth/login.css` 계열에서 공용 디자인 시스템으로 옮기는 재구성 — `D-3`·`I-4` 의 공통 근원이나 이번 회차는 해당 자리만 고친다(후속 항목).
- 접근성 검사 게이트 신설 — `gates/run.sh` 에 `a11y` 0건. `CLAUDE.md §3-3` 대상 후보이며 별 intent.
- `services/core-api/src/colab_core/app/routes/accounts.py` 앵커 `# 자기를 끄면 되살릴 사람이 없다 — 운영자 지정은 아직 SQL 수동이다.` 의 문면 정정 1건(운영자 지정 UI 가 선 뒤에도 「SQL 수동」 표기 잔존) — 후속 항목.

## 확인
- 프론티어 공집합 확인: 2026-09-13
- Ted 확인 문장(원문 그대로): "전부 권고대로 하자. 이걸로 스펙이랑 계획잡아보자"
- 재개봉 금지: 예

## 참조
- 기획 원본: 검증 피드백 원문 `dev-package/reports/issues/2026-09-13-lth-review-1-raw.md`(D-3 · D-4 · I-4 · I-5 · I-8)
- 조사: `dev-package/reports/issues/2026-09-13-lth-survey-B.md`
- 대장 항목: `BO-1` · `BO-2` · `BO-3` — `dev-package/work-items.yaml` 앵커 `id: BO-1`·`id: BO-2`·`id: BO-3`
- 결정: `PLAN-SoT §9 〈384〉`(⑥ⓑ 비활성 계정 경로 선례 · ⑨ⓐ `account-admin-role.sql` 실패 이력) · 새 결정 번호 〈N〉 은 병합 시 기입
- spec: `dev-package/prd/specs/2026-09-13-lth-review-1.md`
- 라운드 파일: `dev-package/prd/rounds/R-LTH-REVIEW-1.md`
- 판정 기록: `dev-package/reports/issues/2026-09-13-ted-decisions.md`
