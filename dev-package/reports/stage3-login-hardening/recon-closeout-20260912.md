# Stage3 로그인·백오피스 착수 전 실측 (2026-09-12)

- 성격 = 읽기 전용 정찰. 판정·승인·상태 변경 없음. 작성자 `agent(researcher)` · 승인 `미승인`.
- 근거 기준 시각 = 이 문서 작성 시점의 `main` HEAD `fc45a9aa`(= `origin/main`).

## 0. 지시와 실물의 불일치 3건 (먼저 보고)

1. 지시가 지목한 `dev-package/reports/stage3-login-hardening/final/release.md` 는 **`main` 에 없다**.
   - 근거: `git ls-files dev-package/reports/stage3-login-hardening` 결과 0행.
   - 실물 위치 = 작업 사본 `colab-stage3-staging-deploy` 의 **미추적** 디렉터리. 본 보고의 §1 은 그 사본을 읽었다.
2. `fc45a9aa` 커밋 본문 축자 「main 병합과 원격 push는 수행하지 않는다」 ↔ 실측은 **병합·push 완료**.
   - 근거: `git rev-parse HEAD origin/main` 두 값 동일 `fc45a9aa7c649062ff4641a05322f026b5e8bf1c`, `git branch -r --contains fc45a9aa` = `origin/main`.
   - 판독 = 커밋 본문이 작성 시점 의도이고 이후 push가 실행됐다. 어느 쪽이 승인 범위였는지는 문서에 없다 → `[미확인]`. 해소 = `PLAN-SoT §9` 에 push 승인 근거 행이 있는지 확인 또는 Ted 확인.
3. 대장 `BO-1` 상태가 두 사본에서 갈린다 — `main` `open`, 작업 사본 `done`. 상세 §3-3.

## 1. 로그인 강화 잔여·미실행 (출처 = 작업 사본의 `reports/stage3-login-hardening/final/release.md`, `prd/rounds/R-STAGE3-LOGIN-HARDENING.md`, `prd/specs/stage3-login-hardening.md`)

계수 기준 = 단일 최종 검증 실행 1회. **14개 중 green 13 / 판정 실패 1 / 준비 실패 0 / 실행 종료코드 1.**

| 항목 | 상태 | 근거 앵커 |
|---|---|---|
| `contract-breaking` red1 (`POST /sessions` `request-body-wrapped-in-one-of`, 1 error/0 warning/0 info) | **사용자 명시 수용으로 보존. 자동 전체 green 아님** | release.md 「검사 결과」 · round 「Task 1 … 현재 판정」 · 수용 기록 `reports/stage3-login-hardening/task1/contract-acceptance.md` |
| 실제 12시간 대기 관찰 | **미실행** — 고정시계 격리 시험으로만 판정 | release.md 대조표 「실제 12시간 대기는 수행하지 않았으며 시계 경계는 격리 시험으로 판정」 |
| stage 실제 되돌림(rollback) 실행 | **미실행** — 절차·격리 리허설만 고정, stage 장애 없어 미수행 | round Task7 「stage 장애는 없어 실제 stage 되돌림은 미실행이다」 |
| DB downgrade · 사용자 암호 복원 | **금지(범위 밖)** | release.md 「DB downgrade 및 옛 무상태 이미지 복귀 금지」 |
| 기존 발급 다운로드 URL 회수 | **잔여 제한** — 별도 10분 capability라 세션 종료와 동시 회수되지 않음. 신규 티켓 발급만 401 | release.md 「기존 발급 다운로드 URL은 별도10분 capability로 만료하며」 |
| 앱 종료 시 오프라인 종료 재시도 | **보장하지 않음** — 원래 12시간 만료가 상한 | intent 정책8 · release.md 같은 문단 |
| 브라우저 종료·새로고침 후 초안 영속 복구 | **약속하지 않음**(계획 자체 점검에서 명시 제외) | round 「계획 자체 점검」 |
| 프로세스 간 공유 실패 제한(limiter) | **범위 밖** | round 「계획 자체 점검」 · spec §1 「분산 제한·… 이번 범위가 아니다」 |
| 분산 제한 · 모든 기기 로그아웃 · 비밀번호 찾기/재설정 신규 UI | **이번 범위 아님** | spec 「분산 제한·모든 기기 로그아웃·비밀번호 찾기/재설정 신규 UI는 이번 범위가 아니다」 |
| 셸 HTTPS 요청 stage 검증 | **인증 결과로 미사용** — 전부 403이라 브라우저 실측만 채택 | release.md 「셸 HTTPS 요청은 모두403이라 인증 결과로 사용하지 않았다」 |
| Task4~6 독립 검토 지적(탭 간 종료 확인·지연401·전환 준비 경합·파일 선택 보호) | 추가 보완 수행. 「전체 검증 완료로 보지 않는다」 표기 존치 | round 「중간 실행 이력」 |
| 디자인 전체 품질 검사 | **합산 제외** | release.md 「디자인 전체의 품질 검사는 이 로그인 작업의 검증 범위에 합산하지 않는다」 |

**`watcher hold` 의 뜻** — staging 호스트의 자동배포 cron 한 줄을 원본 보관 후 중지하고 pipeline lock 을 잡아 선택 배포한 상태.
요지: `main` 이 새 세션 서명 포맷 `ss1` 과 비호환이므로 자동배포가 돌면 stage 를 미호환 이미지로 덮는다. 그래서 hold 를 유지한다.
근거 축자: release.md 「자동배포 watcher cron 한 줄을 원본 보관 후 hold했고 pipeline lock을 잡아 선택 배포했다. main이 ss1 미호환이므로 hold를 유지한다.」
→ **hold 는 아직 해제되지 않았다**(release.md 말미 「watcher hold는 유지되며」). 해제 조건 = 「호환 main 릴리스가 준비된 뒤 watcher 재개를 조정한다」.

## 2. 배포 실측 — AWS dev 에 없다

- **결론: `fc45a9aa` 및 로그인 강화 코드는 AWS dev 에 배포되지 않았다.**
- 최신 dev 태그 = **`dev-20260911-2` → `42cffb32`**(2026-09-11 23:16 KST, 「수정: Slack 알람 문구를 쉬운 한국어로 표시」).
  - 근거: `git tag -l 'dev-*' | sort | tail`, `git rev-list -1 dev-20260911-2`.
  - `git tag --contains fc45a9aa` = **빈 결과**. `fc45a9aa` 를 담은 태그가 없다.
- 원장 대조: `dev-package/PLAN-SoT.md` 의 최신 배포 행 축자 「코드42cffb3·태그dev-20260911-2」. `fc45a9aa` 문자열은 `PLAN-SoT.md`·`03-HANDOFF.md`·`docs/` 어디에도 없다.
- `03-HANDOFF.md` 최상단 블록의 최신 항목은 2026-09-11 I4 완료이며 로그인 강화·`BO-1` 언급 없음.
- `docs/DEPLOY.md` 에는 dev 태그 원장 행이 없다(grep `dev-2026` 0건). 배포 원장의 자리는 `PLAN-SoT §9`.

**마이그레이션 0025/0026**
- 두 파일 모두 **`fc45a9aa` 가 최초 추가**(`git log --diff-filter=A`). 따라서 어떤 dev 태그에도 포함되지 않는다.
- AWS dev 적용 = **미적용**(문서 근거 0건). staging(WSL) 적용만 기록 — release.md 「platform0026 적용 및 기존 인증 롤 권한 재적용」.
- `0025` 의 stage 적용 여부는 release.md 에 `0026` 만 축자로 나온다 → `[미확인]`. 해소 = staging DB 의 alembic version 조회 또는 `reports/stage3-login-hardening/final/release-evidence.json` 확인.

**「dev 인증 전용 DB 연결」의 키 이름** (값·접속문자열 미기재)
- core-api 환경변수: **`COLAB_CORE_ACCOUNT_ADMIN_DATABASE_URL_FILE`** (`infra/dev/compose.yml`, `infra/staging/compose.i2.yml` 양쪽에 신설).
- dev 볼륨 마운트 원본: `${COLAB_DEV_SECRETS_DIR}/account-admin-database.url` → 컨테이너 `/etc/colab/account-admin-database.url`.
- staging 전용 키: **`COLAB_STAGING_ACCOUNT_ADMIN_DB_URL_FILE`**. 롤 비밀 키: **`COLAB_ACCOUNT_ADMIN_PASSWORD`**.
- 부트스트랩 하위명령 신설: `infra/dev/db-bootstrap.sh` 에 `account-admin` 추가.

## 3. 작업 사본 `colab-stage3-staging-deploy` 대조

- HEAD = `b63c9e8a0d40563a12f815f407756d5d4e85b17e`. 수정 65파일(+1834/−237), 미추적 38항목. **본 정찰에서 커밋·stash·수정 0.**
- 해당 사본의 git dir 은 이 레포(`31 CoLAB-v2`)가 아니라 **별도 체크아웃(`30 CoLAB-v2`)의 worktree** 다. 원격은 동일 `CognileapAI/colab-v2`.

### 3-1. 수정 65파일 vs `fc45a9aa`
- **56파일 = `fc45a9aa` 판과 내용 동일**(차이 0). 즉 `fc45a9aa` 에 이미 포함된 부분집합.
- **9파일만 차이**(`git diff fc45a9aa -- <65파일>` = 9 files, +55/−42):
  `dev-package/03-HANDOFF.md` · `dev-package/work-items.yaml` · `frontend/src/auth/LoginPage.tsx` · `frontend/src/auth/login.css` · `frontend/src/shell/Gnb.tsx` · `frontend/src/components/lab/LabInfoPanel.tsx` · `frontend/src/components/project/ProjectFormModal.tsx` · `frontend/src/components/approval/VerificationAction.tsx` · `frontend/src/components/detail/RepresentativeImageSection.tsx`

### 3-2. 차이의 방향 (프런트 7파일)
- 방향 = **`fc45a9aa` 가 더 앞선다**. 사본에 없는 것이 `fc45a9aa` 에 있다: `ThemeSwitcher`(LoginPage·Gnb), `useDialogFocus` 기반 dialog 포커스 처리(LabInfoPanel·ProjectFormModal·VerificationAction), Gnb 계정 관리 링크의 아이콘·`aria-label`, `login.css` 추가 규칙, `RepresentativeImageSection` 클래스명 `hidden-input`.
- 판독 `[추론]`: 이 7파일은 로그인 작업 산출이 아니라 **후속 디자인 작업 산출**이고 `fc45a9aa` 에 통합됐다. 사본은 통합 이전 상태다. → 로그인 코드 기준 **사본 고유의 미반영 hunk 0**.

### 3-3. 사본에만 있는 실질 내용 2건 (문서)
- `dev-package/work-items.yaml` `BO-1`: 사본 `status: done` · `evidence: reports/stage3-login-hardening/final/release.md` · completion_def 기재 · note 「WSL stage 구현·검증 완료. 13 green/수용한 계약 red1/준비 실패0. main 미병합, AWS 미배포. 미호환 main 자동배포 watcher hold 유지.」
  ↔ **`main` 은 `status: open` · `completion_def: 완료 정의 미작성` · `evidence: null`** 로 되돌아간 상태.
- `dev-package/03-HANDOFF.md`: 사본에 2026-09-12 BO-1 완료 1행 추가, `main` 에는 없음.

### 3-4. 미추적 38항목
- 36항목은 **`fc45a9aa` 에 이미 추적 파일로 존재**(마이그레이션 0025/0026·assertions·drift, intent, round, spec, `PasswordChangePage.tsx` 등).
- **`fc45a9aa` 에 없는 것은 2개 디렉터리뿐** — `dev-package/reports/stage3-login-hardening/` · `dev-package/reports/stage3-password-change/`.
- 후속 항목: 검증 증거 전체가 `main` 미추적이므로, 다음 사본·다음 세션이 release.md 를 근거로 지목하면 읽지 못한다(`colab-rules §2-2` 의 실패 양상). 승인된 전달 경로 확정이 필요하다.

## 4. 운영자 백오피스(BO-1) 실측

### 4-1. 대장·선행
- `BO-1` (`main` 판): `status: open` · `stage: after_stage2` · `owner: D1 / core-api · frontend` · `depends_on: [PA]` · `completion_def` 축자 「완료 정의 미작성 — 운영자가 백오피스 화면에서 이메일 식별 서비스 계정을 직접 추가하는 방향만 승인. 메일함 생성 요구가 아니며 상세 발급 방식·검증 기준은 별도 설계에서 확정한다.」 · `evidence: null`.
- 선행 `PA` = **「로그인 · 세션」 · `status: done` · `stage: stage1`**. 즉 **선행 충족**. `PA` note 축자 「정본(구글 전용)과 구현(비밀번호)이 다른 것은 결함이 아니라 등재된 「알려진 예외」다.」
- `PA` evidence 에 남은 결손 2건 축자 「만료 전 조기 회수 불가 · 시도 제한이 프로세스 안에서만」 → 앞의 하나는 이번 로그인 강화(0026 세션 원장)로 해소, 뒤의 하나는 여전히 범위 밖(§1).

### 4-2. 2026-09-10 결정 (`dev-package/sessions/20260910-stage12-decisions.md`)
- 사용자 원문 축자: 「구글로그인은 빼고 우리가 백오피스화면을 만들어서 메일 계정을 직접 추가해주려고 한다. 이건 stage3의 최우선 개발로 하자」
- Q6 축자: 「Google 로그인 이번 개발 제외, PA-G deferred 및 종전 자동 개시 기한 해제. … 기존 로그인·비밀번호 발급 경로 제거는 승인 범위가 아님.」
- Stage 3 축자: 「BO-1 운영자 백오피스에서 이메일 식별 서비스 계정을 직접 추가하는 기능 최우선. 메일함 생성 요구로 확대하지 않음. 계정 발급 방식·권한·연구실 소속·기존 계정 처리와 최종 완료 정의는 별도 설계 대상.」

### 4-3. 현재 코드가 하는 것 (main `fc45a9aa`)

**있는 기능**
| 기능 | 근거 |
|---|---|
| 화면 1개 `/account-admin` — 「서비스 계정 추가」 폼(이름·이메일·연구실 select·역할 select·초기 비밀번호) | `frontend/src/app/routes.tsx` `<Route path="/account-admin" element={<AccountAdminPage />} />` · `frontend/src/routes/AccountAdminPage.tsx` |
| 연구실·역할 선택지 조회 | `GET /admin/account-options` (`accounts.py` `name="getAccountOptions"`) — `d1_lab` 목록 + `roles: ["연구원","교수"]` 고정 |
| 계정 발급(1건) — `d1_account` INSERT ＋ `d2_member_role` INSERT ＋ `account_admin.login_credential` INSERT 를 한 트랜잭션 | `POST /admin/accounts` `name="createServiceAccount"` status 201 |
| 중복 이메일 거절 | `d1_account` lower(btrim(email)) 조회 + `legacy_credentials.contains_normalized` + `IntegrityError` → `errors.conflict` |
| 이메일 형식·연구실 ID(Ulid)·역할 enum 검증, 초기 비밀번호 10~512 | `accounts.py` `AccountCreate` Field 및 본문 검증 |
| 동시 발급 직렬화 | `SELECT pg_advisory_xact_lock(1131379081)` |
| 본인 첫 비밀번호 변경 | `PUT /me/password` `name="changeOwnPassword"`, `current_session_subject` 의존 |
| 프런트 작업 보호(전환 차단) 연결 | `useWorkProtection('account-admin', …)` |
| GNB 진입 링크 노출 조건 | `frontend/src/shell/Gnb.tsx` `account?.canManageServiceAccounts` |

**운영자 식별·인가 방식**
- 서버 판정 = `account_admin.service_operator` 표에 `account_id` 행 존재 여부. `accounts.py::_require_operator` 가 없으면 403 「서비스 운영자만 계정을 추가할 수 있다.」
- 프런트 노출 판정 = `GET /me` 의 `canManageServiceAccounts`(`identity.py` `"canManageServiceAccounts": _is_operator(...)`, 계약 `contracts/seams/fe-core.yaml`).
- 운영자 등록 경로 = **화면 없음. DB 스크립트만** — `services/core-api/ops/provision-service-operator.sql`, 축자 「migration owner만 실행한다. 교수/연구실 관리자에서 서비스 운영자로 자동 승격하지 않는다.」
- 전용 DB 롤 = `services/core-api/ops/account-admin-role.sql` — `NOINHERIT BYPASSRLS`, 부여 권한은 `SELECT ON d1_lab,d1_account` / `INSERT ON d1_account,d2_member_role` / `SELECT,INSERT,UPDATE ON account_admin.login_credential`,`login_session` / `SELECT ON account_admin.service_operator`.

**없는 기능(코드 부재)**
- 계정 목록 조회 화면·API 없음(`accounts.py` 의 라우트는 3개뿐).
- 초기 비밀번호는 **운영자가 입력**하는 값이고 서버가 생성·표시하지 않는다. 응답 본문에 비밀번호 없음(`return` 필드 = accountId/email/name/labId/role).
- 운영자에 의한 비밀번호 재설정(타인) 없음. 비활성화·삭제 없음. 역할·연구실 변경 없음.
- 기존 계정 처리(덮어쓰기·병합) 없음 — 중복은 409 거절만.
- 운영자 지정·해제 UI 없음(위 SQL 수동 실행).
- 계정 1건 단위만. 일괄 등록 없음.
- 감사 로그·발급 이력 조회 없음 `[미확인]`(`account_admin` 스키마 표 목록을 `db/platform/schema.sql` 에서 확인하면 해소).

### 4-4. 디자인 정본
- `frontend/src/shell/design-system.css` 및 `40 COLAB-기획` 에 「백오피스」·「운영자 화면」 문자열 **0건**(grep -l 결과 없음).
- 언급이 있는 곳은 계획 문서 2개뿐:
  - `dev-package/prd/specs/s2-convenience.md` 축자 「Google 로그인과 계정 백오피스는 Stage 1/2에 넣지 않는다. 백오피스 계정 추가는 Stage 3 최우선 `BO-1`이다.」
  - `dev-package/prd/specs/stage1-stage2-closeout.md` 축자 「운영자가 백오피스 화면에서 이메일로 식별하는 서비스 계정을 직접 추가하는 기능을 최우선 개발한다. 메일함 생성 기능이 아니다. 초기 자격 발급·권한·연구실 소속·기존 계정 처리·완료 검증 기준은 별도 사양에서 확정한다.」
- **결론: 백오피스 화면 디자인 정본은 없다.** 현재 화면은 `frontend/src/auth/login.css` 의 로그인 카드 스타일(`login-card account-card`)을 재사용한다.

## 5. 로그인·계정 관련 open/blocked 대장 항목

계수 기준 = `work-items.yaml` 에서 `status ∈ {open, blocked}` 이고 name/note/completion_def 에 `로그인|계정|Google|인증|세션|백오피스|운영자` 중 하나가 나타나는 항목. **총 2건.**

| id | name | status | stage | completion_def |
|---|---|---|---|---|
| `BO-1` | 운영자 백오피스 — 이메일 식별 서비스 계정 직접 추가 | open | after_stage2 | 필드 존재. 내용은 「완료 정의 미작성」 |
| `PA-G` | 구글 IdP 어댑터 | open | backlog | 필드 존재(2026-08-27 작성 ⓐ~ⓕ). note 축자 「위 완료 정의는 과거 기록이며 재착수 시 새 사양으로 재검토한다」 |

- `PA-G` 는 「Stage1·2·3 미배정 백로그. 단계·착수 범위·시점을 정하기 전 자동 착수하지 않는다.」(2026-09-11 결정) → 이번 인터뷰 범위 밖.

## 6. 게이트 이름 (실행 안 함 · 이름만, `gates/README.md`)

- 계약: `contract-lint` · `contract-breaking` · `generated-up-to-date` · `contract-selftest` · `contract-gates`
- 서버: `service-tests-core-api` · `service-tests` · `service-tests-selftest` (그 외 `-ai-service`·`-pipeline-worker`·`-viz-render`)
- 프런트: `frontend-typecheck` · `frontend-test` · `frontend-visual` · `frontend-fixture-reach` (＋ 각 `-selftest`, `frontend-gates`)
- DB/마이그레이션: `migration-single-head` · `migration-drift` · `schema-diff` · `db-boundary` (＋ `migration-drift-selftest`)
- RLS: `rls-coverage` · `rls-effect` · `rls-allowlist` (＋ `rls-effect-selftest`)
- 대장: `work-item-consistency`

## 7. 후속 항목 (이 문서에서 고치지 않음)

1. `main` 의 `work-items.yaml` `BO-1` 이 `open`/`completion_def 미작성` 인데 구현·stage 검증은 끝났다. 대장 갱신 여부는 Ted 판정 대상.
2. 검증 증거(`reports/stage3-login-hardening/`)가 `main` 미추적. 인계 경로 확정 필요.
3. staging 자동배포 watcher 가 hold 상태다. `main` 이 `ss1` 호환이 된 지금(`fc45a9aa` 병합 완료) 재개 조건 재평가 필요 — release.md 의 「main이 ss1 미호환」 진술은 `fc45a9aa` 이전 기준이다.
4. 로그인 강화 코드가 AWS dev 에 없다. `deploy_doctor` 15/15 판정은 이 코드를 포함하지 않은 `dev-20260911-2` 기준이다.
5. 백오피스 화면 디자인 정본 부재 — `BO-1` 완료 정의 작성 시 함께 확정 필요.
