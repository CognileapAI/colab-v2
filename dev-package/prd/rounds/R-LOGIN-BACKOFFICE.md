> spec: [login-backoffice-closeout.md](../specs/login-backoffice-closeout.md)
# 로그인 dev 마무리와 운영자 백오피스 확장 실행 계획

> 실행자는 `executing-plans` 를 적용한다. 쓰기 주체는 사본당 하나이며 독립 검토만 읽기 전용으로 병행한다.

**Goal:** 병합된 로그인 강화 코드를 dev 에 올려 `deploy_doctor` 15/15 를 한 번의 실행으로 세우고, 계정 목록·운영자 비밀번호 재설정·비활성화/재활성화를 추가한다.
**Architecture:** 계정 상태를 `account_admin.login_credential` 한 열로 둔다. 전 기기 종료는 기존 `session_version`(서명의 `credential_version`) 대조를 그대로 쓴다. 메일·외부 서비스 호출은 이번 범위에 없다.
**Tech Stack:** FastAPI/Pydantic, PostgreSQL/Alembic, React/TypeScript, Vitest.
**Spec:** 위 링크와 [승인 intent](../../intent/2026-09-12-login-backoffice-closeout.md) 가 설계·정책 정본이다.
**상태:** 계획 초안. 구현 미착수. Ted 입력 2건 대기.

## 공통 제약과 실행 순서

- 기준 = `main` `fc45a9aa`. 최신 dev 태그 `dev-20260911-2`(`42cffb32`) 에는 로그인 강화 코드가 없다.
- 완료 = dev 배포 green ＋ `deploy_doctor` 15/15 **한 번의 실행**. 부분 실행 합산 금지. 항목 수를 15 에서 늘리지 않는다.
- 비밀번호 원문은 응답·화면·로그에 넣지 않는다. 운영자 재설정 입력값도 같다.
- 계정 발급 흐름은 현행 유지 — `initialPassword` 를 제거하지 않는다. 메일 관련 항목은 어느 작업에도 넣지 않는다.
- 실패 제한은 기존 값 유지 — 자격·클라이언트 각각 5회/15분. 수치를 재질문하지 않는다.
- 각 작업은 실패 시험(RED) → 최소 구현 → 통과(GREEN) → 게이트 순서로 체크한다.
- core 변경 전 `.claude/rules/s3-upload.md`, ops 변경 전 `.claude/rules/deploy.md` 를 먼저 읽는다.
- 결정 번호 〈N〉 을 하드코딩하지 않는다. 병합 직전 `dev-package/prd/tools/max-decision.sh` 로 재실측한다.
- 전수 게이트 실행 중에는 다른 실행 레인을 띄우지 않는다.

| 작업 | 산출물 | 선행 | 정책/intent |
|---|---|---|---|
| 1 | 로그인 강화 dev 반영과 계약 기준 정리 | 없음 | Q1·Q2 |
| 2 | 계정 상태 열과 롤 권한 | 없음 | Q12 |
| 3 | 계정 목록·재설정·비활성화 API | 2 | Q10·Q13·Q18 |
| 4 | 프런트 — 계정 목록·재설정·비활성화 | 3 | Q4·Q18 |
| 5 | dev 배포 전수와 대장·인계·사본 정리 | 1~4 | Q5·Q6·Q7 |

작업 1 은 나머지와 독립으로 출하한다. 2~4 가 준비되지 않아도 1 만으로 dev 배포 green 을 세운다.
게이트 실행은 저장소 루트에서 `python3 scripts/agent-bridge.py run-tool gate -- <gate>` 를 쓴다.
새 시험은 기존 `frontend-test`·`service-tests-core-api` 수집 경로에 넣고 RED·GREEN 로그에서 시험 이름이 실제 실행됐는지 확인한다.

### Task 1: 로그인 강화 dev 반영과 계약 기준 정리

**Files:** Modify `dev-package/PLAN-SoT.md`(§9 배포 행 ＋ 동결 해제 서명 행), `.github/workflows/ci.yml`(단계 「파괴적 변경 탐지 (emit vs frozen seam)」); 읽기 `gates/tools/contract-breaking.sh`, `db/platform/versions/0025_stage3_accounts.py`, `db/platform/versions/0026_login_sessions.py`, `services/core-api/ops/deploy_doctor.py`, `docs/DEPLOY.md`.
**Interfaces:** `contract-breaking` 기준은 파일이 아니라 ref 다 — `COLAB_BREAKING_BASE_REF`(기본 `HEAD`) · `COLAB_CONTRACTS_BASE` · `COLAB_CONTRACTS_REV`. 배포 sha 는 `origin/main` 의 조상이어야 한다.
- [x] **기본 기준으로 `contract-breaking` 을 먼저 1회** 실행한다. ERR 0 이면 「red 부재 · 서명은 사후 등재」로 기록하고, ERR 가 남으면 항목을 그대로 적어 진행을 멈춘다. — 결과는 `PLAN-SoT §9` 서명 행 ⑤ⓐ 에 등재됐다(exit 0 · 「기준 HEAD (3건) 대비 파괴적 변경 없음」).
- [x] 기준 ref 를 `fc45a9aa^` 로 둔 1회로 ERR 가 실제로 잡히는지 확인한다(검사기 생존 증명 · 판정 계수 합산 제외). — 같은 행 ⑤ⓒ · ERR 1 `[request-body-wrapped-in-one-of] at POST /sessions`.
- [x] `PLAN-SoT §9` 에 로그인 혼합 입력 400 의 동결 해제 서명 행을 적는다. 서명 축자(수령 2026-09-12): "로그인 혼합 입력 400 계약 변경을 승인한다." — 등재 전에는 dev 배포로 넘어가지 않는다.
- [x] `.github/workflows/ci.yml` 의 해당 단계에 `COLAB_BREAKING_BASE_REF: origin/main` 을 더한다(게이트 승격). 단계 이름으로 앵커하고 행 번호를 쓰지 않는다. 단계 존재는 실측으로 확인됐다.
- [ ] 마이그레이션 적용 전 dev 에서 `deploy_doctor` 1회 — ⑥(스키마 head platform) BAD 를 관찰한다. — **미실행.** 마이그레이션은 배포 레인 도착 전(2026-09-12 01:28~01:52 KST)에 적용돼 있었고 적용 전 상태를 되돌려 재관찰하지 않았다.
- [x] dev platform 체인에 `0025`·`0026` 을 적용한다. 백업 확인 뒤 적용하고 적용 전후 alembic head 를 기록한다. — 적용 전 `0024_s2_grid_convenience`(마이그레이션 직전 덤프 `stage3-dual-20260912/platform-before.sql.gz` · 2026-09-12 01:28 KST) · 적용 후 `0026_login_sessions`(살아 있는 DB 조회).
- [x] `fc45a9aa` 이후 `main` 커밋으로 dev 이미지를 교체하고 `/opt/colab-v2` 의 `CURRENT_SHA`·`MAIN_SHA` 를 갱신한다. — 실적용 sha 는 `fc45a9aa7c64` 자체다(`origin/main` `c71eed916432` 와 코드 경로 diff **0파일** · 차이는 문서·CI 10파일). `CURRENT_SHA`·`MAIN_SHA`(`ancestor=yes`)는 2026-09-12 01:52·02:06 KST 에 기록됐다.
- [x] 마이그레이션 → 롤 → 시크릿 → 기동 순서를 지킨다 ① 마이그레이션 `0025`·`0026` 을 **먼저** 적용한다(`account-admin-role.sql` 이 `account_admin` 스키마를 전제한다).
- [x] ② `db-bootstrap.sh account-admin` 으로 `colab_account_admin` 롤을 만든다(`COLAB_ACCOUNT_ADMIN_PASSWORD` · base64url 문자만 · 출력하지 않는다).
- [x] ③ 시크릿 파일 `${COLAB_DEV_SECRETS_DIR}/account-admin-database.url`(0600 · uid 10001)을 **이미지 교체 전에** 둔다 — `compose.yml` 이 그 파일을 바인드 마운트하므로 없으면 core-api 가 기동에 실패한다. 실측 = 롤·파일 01:52 → 컨테이너 교체 01:52(같은 분에 선행) · `ls -l` 로 권한·소유 확인.
- [x] ④ 수동 인증 DB 확인(`deploy_doctor` 가 덮지 않는다) — `colab_account_admin` 으로 `SELECT count(*) FROM account_admin.login_credential` 성공(0행) · `service_operator` 0행 · `login_session` 7행. `PUT /me/password` 는 401 JSON 으로 도달한다. **서비스 운영자 등록과 실제 로그인 1회는 대상 계정이 정본·원장·docs 어디에도 없어 멈췄다 — `[Ted 입력 대기]`.**
- [x] `deploy_doctor --env dev` 를 **한 번** 실행해 15 항목 요약줄을 받는다. SKIP·BAD 0 이 아니면 항목별 원인을 적고 멈춘다. — 2026-09-12 13:16 KST · `항목 15 — ✓ 15 · ✗ 0 · ─ 0` · exit 0 · 재시도 0회. 선행으로 EC2 배포 레포 트리를 배포 sha 로 밀었다(밀기 전 트리 head 0024 / DB 0026).
- [x] dev 태그 `dev-YYYYMMDD-N` 을 찍고 `PLAN-SoT §9` 배포 행에 코드 sha·태그를 적는다. 태그의 원격 반영은 오케스트레이터가 한다. — 로컬 태그 `dev-20260912-1` → `fc45a9aa7c64`(`docs/BRANCHING.md §2` 「dev 실적용 sha」 규약). 원장 행 문안은 `dev-package/reports/r-login-backoffice/task1-deploy/release.md §5`.
- [ ] `contract-lint`, `contract-breaking`, `generated-up-to-date`, `migration-single-head`, `migration-drift`, `schema-diff` 의 종료코드를 보고서에 기록한다. — **배포 레인 미실행.** 같은 시각 다른 사본이 전수 게이트를 돌고 있어 일회용 postgres 를 공유하는 게이트를 겹쳐 띄우지 않았다(`.claude/rules/colab-rules.md §3-4`). 전수 레인의 결과로 채운다.

### Task 2: 계정 상태 열과 롤 권한

**Files:** Create `db/platform/versions/0027_account_status.py`, `db/platform/tests/0027-assertions.sql`, `db/platform/tests/0027-drift.sh`, `services/core-api/tests/test_account_status.py`; Modify `db/platform/schema.sql`, `services/core-api/ops/account-admin-role.sql`, `services/core-api/src/colab_core/kernel/db_credentials.py`.
**Interfaces:** `login_credential.status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive'))`. `DatabaseCredential` 에 `status` 를 더한다.
- [x] 최신 migration head 가 `0026_login_sessions.py` 임을 확인한다(실측값). 번호 충돌 시 세 파일을 함께 조정한다.
- [x] 비활성 계정의 로그인이 현재는 200 인 RED 를 확인한다.
```python
assert login(inactive_account).status_code == 401
```
- [x] 열을 추가하고 `DatabaseCredentialStore.find` 조회에 포함한다. 기존 행은 `status='active'` 로 남는다.
- [x] 비활성 거절이 계정 존재 여부를 구분하지 않고 실패 제한 버킷도 오염시키지 않음을 검사한다.
- [x] `account-admin-role.sql` 에 `GRANT SELECT ON d2_member_role` 를 더한다(현재 `INSERT` 만 — 실측). 부여 전 목록 조회가 권한 오류인 것을 먼저 관찰한다.
- [x] `gates/config/rls-allowlist.toml` 은 고치지 않는다 — `login_credential` 이 이미 등재됨(실측).
- [x] `migration-single-head`, `migration-drift`, `schema-diff`, `rls-coverage`, `rls-effect`, `db-boundary`, `service-tests-core-api` 를 실행하고 종료코드를 기록한다.

### Task 3: 계정 목록·재설정·비활성화 API

**Files:** Modify `services/core-api/src/colab_core/app/routes/accounts.py`, `services/core-api/src/colab_core/kernel/db_credentials.py`, `services/core-api/src/colab_core/kernel/login_sessions.py`, `contracts/seams/fe-core.yaml`, `frontend/src/generated/fe-core.ts`; Create `services/core-api/tests/test_account_backoffice.py`.
**Interfaces:** `GET /admin/accounts` · `POST /admin/accounts/{accountId}/password-reset`(요청 `{newPassword}`) · `POST /admin/accounts/{accountId}/status`(요청 `{status}`). `POST /admin/accounts` 는 무변경이다.
- [x] 목록·재설정·비활성화 경로가 없는 RED 를 확인한다.
```python
assert client.get("/admin/accounts").status_code == 404
assert new_pw not in response.text and new_pw not in caplog.text
```
- [x] 재설정이 새 비밀번호를 기존 scrypt 경로로 저장하고 `must_change_password=true` 로 둔다. 응답 본문에 비밀번호 필드가 없다.
- [x] 재설정·비활성화가 `session_version` 을 +1 하고 같은 트랜잭션에서 그 계정의 `login_session.revoked_at` 을 채운다. 다른 계정 세션은 불변이다.
- [x] 재설정 전 발급한 두 토큰이 뒤에 둘 다 401, 다른 계정 토큰은 200 인지 검사한다. 증가폭이 정확히 1 인지도 검사한다.
- [x] 목록은 전 연구실 한 벌이며 열 6개와 필터 4종을 낸다. 최근 로그인은 `login_session` 의 `MAX(issued_at)` 집계다.
- [x] 비운영자 토큰의 세 경로 403, 자기 자신 비활성화 400 을 검사한다.
- [x] 계약 3건을 `fe-core.yaml` 에 추가하고 클라이언트를 재생성한다. 생성물을 손으로 고치지 않는다.
- [x] `contract-lint`, `contract-breaking`, `generated-up-to-date`, `service-tests-core-api` 를 실행한다. 이 회차는 추가만 하므로 신규 ERR 0 이 기대값이며 ERR 가 나오면 멈추고 보고한다.

### Task 4: 프런트 — 계정 목록·재설정·비활성화

**Files:** Modify `frontend/src/routes/AccountAdminPage.tsx`, `frontend/test/account-admin.test.tsx`; 필요 시 `frontend/src/routes/account-admin.css`.
**Interfaces:** 목록·재설정·비활성화는 `frontend/src/generated/fe-core.ts` 의 생성 클라이언트만 쓴다. 비밀번호 판정은 기존 `frontend/src/auth/passwordRules.ts` 를 재사용한다.
- [x] 계정 목록 표와 행별 동작이 없는 RED 를 확인한다.
```typescript
expect(screen.queryByRole('table', {name: '계정 목록'})).toBeNull();
```
- [x] 계정 목록 표(이메일·이름·역할·연구실·상태·최근 로그인)와 네 필터를 붙인다.
- [x] 행별 「비밀번호 재설정」(값·확인 2칸)·「비활성화/재활성화」를 붙인다. 비활성 행의 버튼 라벨이 「재활성화」로 바뀌는지 검사한다.
- [x] 계정 추가 폼과 초기 비밀번호 칸은 그대로 둔다. 로그인·첫 변경 화면은 고치지 않는다.
- [x] 재설정 입력값이 DOM 잔존·`draftVault`·로그 어디에도 남지 않음을 검사한다.
- [x] 기존 작업 보호(`useWorkProtection`) 연결을 유지한다. `frontend-typecheck`, `frontend-test` 를 통과한다. CSS 변경 시 `frontend-visual` 을 더한다.
  - 종전 미이행분 `frontend-visual` 해소(작업 6 검토 조건 ②) — **green**. 로컬 dev 서버(`npm run dev`)의 두 화면을 `COLAB_VISUAL_URLS` 로 선언해 1회 실행: 「페이지 2건 · 13px 미만 0건 · 대비<4.5 0건 · 스크린샷 4장 (허용 접두사 0개)」. 근거 = `dev-package/reports/r-login-backoffice/task6/frontend-visual/`.
  - ⚠ 대상은 로그인 화면과 `/account-admin` 경로 두 개다. 로그인하지 않은 상태라 계정 목록 표 자체는 이 계측에 들어가지 않았다 — 그 자리는 `[미확인]` 이다.

### Task 5: dev 배포 전수와 대장·인계

**Files:** Modify `dev-package/work-items.yaml`, `dev-package/03-HANDOFF.md`, `dev-package/PLAN-SoT.md`, `CLAUDE.md`(`after_stage2` 괄호); Create `dev-package/reports/<회차>/release.md`.
**Interfaces:** 대장이 상태의 유일한 원본이다. `03-HANDOFF §1` 은 그 반영본이다. `work-item-consistency` 가 판정한다.
- [ ] 전수 전에 홈의 `.colab-v2-test.env` 를 export 로 선언한다. 워크트리는 `node_modules`·`.venv` 와 core-api 의 편집 가능 설치를 먼저 구성한다.
- [ ] 전수 게이트를 `-j 4` 로 백그라운드 1회 실행하고 green / red(판정) / red(준비) 3계수를 나눠 기록한다.
- [ ] dev 에 `0027` 을 적용하고 core/frontend 이미지를 교체한 뒤 `deploy_doctor --env dev` 를 **한 번** 실행해 15/15 를 받는다. 재시도로 모은 계수를 15 라 적지 않는다.
- [x] 새 dev 태그를 찍고 `PLAN-SoT §9` 배포 행에 코드 sha·태그를 적는다. — 원장 행 `〈382〉` 등재(임시 번호 · 측정값 381＋1). 태그 `dev-20260912-1` → `fc45a9aa7c64` 는 작업 1 레인이 로컬 생성했고 **미push** 다(원격 반영은 오케스트레이터 몫).
- [x] dev green 확인 뒤 staging 자동배포 watcher 를 재개한다. 재개는 intent Q5 로 확정된 결정이며 재판정 대상이 아니다 — 실행 결과와 시각만 기록한다. — 2026-09-12 16:22 KST 재개. cron 활성 행 7 → 8 · 총 55행 무변 · 바뀐 줄 1개(`# HOLD …: ` 접두 제거). 선행 확인 = 컨테이너 8/8 healthy · 헬스 6종 200 · `origin/main` 에 `0025`·`0026` 존재 · `infra/staging/deploy.sh:192` account-admin 롤 단계 존재 · `COLAB_STAGING_ACCOUNT_ADMIN_DB_URL_FILE` 가리키는 파일 `0600`·uid `10001` 존재 · 보류 사유 `ss1` 비호환 해소(`session_token.py:32` `TRACKED_PREFIX = "ss1"`). **재개 후 첫 회차(16:25) 관측 — watcher 정상 동작(fetch → ff `cbb9ff1406c5` → 배포) · 배포·검증 GREEN(헬스 6종 200 · 컨테이너 8/8 · platform head `0027_operator_audit`) · 그러나 파이프라인 종료코드는 `78` 이고 `DEPLOY-FAILED.txt` 가 섰다** — 원인은 배포가 아니라 운영자 알림 스풀 부재(`"notification": "pending"`)이고 **알림 배선 전까지 매 회차 반복된다**. 블로커 `03-HANDOFF §4 #71` 신설.
- [ ] 대장 `BO-1` 을 `done` 으로 갱신한다(intent Q7). `completion_def`·`evidence` 를 채운다.
- [ ] 확장분을 새 항목으로 등재한다 — 계정 목록·운영자 비밀번호 재설정·비활성화/재활성화. `stage: after_stage2` 면 `CLAUDE.md` 의 `after_stage2` 괄호 목록도 같은 커밋에서 갱신한다.
- [x] `03-HANDOFF §1` 해당 행과 상단 최종 갱신·현재 단계·다음 WU 를 5줄 이내로 갱신한다. 새 블로커는 `§4`. — 상단 1행 추가(작업 5 마무리 A).
- [x] 별도 작업 사본의 보고서 2개 디렉터리(`reports/stage3-login-hardening/` · `reports/stage3-password-change/`) 를 승인된 전달 경로로 레포에 복사하고 hash 를 대조한 뒤 커밋한다. 커밋 확인 후 사본을 삭제한다(intent Q6). — 46파일 반입 · 커밋 후 `cmp` 전건 대조 46/46 일치 · 사본 `colab-stage3-staging-deploy` 와 로컬 브랜치 `codex/stage3-staging-deploy` 삭제. `gate-summary.json` 10건은 `.gitignore` 지정 보존명 `gate-summary.record.json` 으로, 게이트 로그 12건은 명시 반입.
- [x] `work-item-consistency` 를 실행하고 종료코드를 기록한다. — **exit 1 · green 0 / red(판정) 1 / red(준비) 0.** 불일치 = `㈕ OP-NOTIFY-1` 이 대장 `stage: after_stage2` 인데 `CLAUDE.md` 괄호 목록에 없다. **이 레인이 만든 것이 아니다** — `work-items.yaml`·`CLAUDE.md` 둘 다 이 레인 무수정이고, `948cd2a5`(운영 알림 레인 · `origin/main` 병합분)가 항목만 넣고 괄호를 갱신하지 않았다. **`origin/main` 자체가 이 게이트에 red 였다.** → **해소** — `CLAUDE.md` 기계 표식 안의 괄호에 그 항목을 더해 닫았다(별도 커밋 `b2b1df5b` · 규칙 문안 0글자 · 항목 수 17→18). 검사 대상을 줄이지 않고 지적된 불일치 자체를 없앴다. **재실행 = exit 0 · green 1 / red(판정) 0 / red(준비) 0.** 다른 레인의 누락을 대신 닫은 것이라 커밋을 분리했다 — 오케스트레이터 검토 대상.
- [ ] 실제 종료코드·3계수·미실행·잔여 제한을 보고한다. 전체 체크 완료 시에만 구현 완료로 표시한다.

### Task 6: 관리자 지정·해제와 관리자 전 연구실 읽기

**Files:** Create `db/platform/versions/0028_operator_read_policy.py`, `db/platform/tests/0028-assertions.sql`, `db/platform/tests/0028-drift.sh`, `services/core-api/tests/test_operator_designation.py`, `dev-package/reports/r-login-backoffice/task6/overlap.md`; Modify `contracts/seams/fe-core.yaml`, `frontend/src/generated/fe-core.ts`, `frontend/src/routes/AccountAdminPage.tsx`, `frontend/src/shell/Gnb.tsx`, `frontend/test/account-admin.test.tsx`, `frontend/test/shell.test.tsx`, `db/platform/schema.sql`, `gates/tools/rls-effect.sh`, `services/core-api/ops/account-admin-role.sql`, `services/core-api/src/colab_core/app/{deps.py,routes/accounts.py,routes/catalog.py}`, `services/core-api/src/colab_core/kernel/{auth.py,authn.py,db_credentials.py,login_sessions.py,scope.py,session_token.py}`, `services/core-api/tests/{conftest.py,test_account_status.py,test_account_backoffice.py,test_body_access.py,test_route_table.py}`, `dev-package/work-items.yaml`.
**Interfaces:** `POST /admin/accounts/{accountId}/operator`(요청 `{operator}` · 응답 `{accountId, operator}`) · `POST /admin/accounts` 에 선택 칸 `operator` · `ServiceAccountSummary.operator` · GUC `app.operator_read` ＋ SQL 함수 `is_operator_read()` · `apply_scope(session, subject, operator_read=…)`.
정본 = 승인 intent [`2026-09-12-operator-designation.md`](../../intent/2026-09-12-operator-designation.md).

- [x] **검토 조건 ①** — 비활성 계정이 파일 자격(`TrackedPasswordIssuer`)·접속 코드(`TrackedPlantedCodeIssuer`) 로도 로그인하지 못한다. RED 2건 실측(둘 다 201) → `AccountInactive` 로 401, 봉투·실패 제한 셈은 DB 경로와 동일. dev 실물 겹침 건수는 문서에서 닿지 않아 `[미확인]` ＋ 재는 명령을 `reports/r-login-backoffice/task6/overlap.md` 에 남겼다.
- [x] **검토 조건 ②** — `frontend-visual` 1회 실행 green (위 작업 4 마지막 항목에 계수 기재).
- [x] 관리자 지정·해제 경로가 없는 RED 를 확인한다(14 failed / 1 passed).
- [x] 지정·해제 엔드포인트를 계약에 **추가만**으로 더하고 생성 클라이언트를 재생성한다. `contract-breaking` 기준 `origin/main` green.
- [x] 관리자 누구나 지정·해제한다. 자기 자신 해제 400 · 마지막 한 명 해제 400.
- [x] 마지막 한 명 셈을 **자문 잠금 아래**에서 한다. 동시 해제 2건에 통과는 1건뿐이고 관리자 1명이 남는다(진 쪽 코드는 400 또는 403 — 이긴 트랜잭션이 진 쪽의 운영자 행을 먼저 지우면 자격 확인에서 걸린다).
- [x] 지정·해제가 그 계정의 자격 버전을 올리고 열린 세션을 닫는다. 남의 세션은 불변이다.
- [x] `POST /admin/accounts` 에 `operator` 선택 칸을 더한다. 생략하면 아니다.
- [x] 스코프 커널에 **명시적 읽기 스코프**를 더한다 — `apply_scope(..., operator_read=True)` 는 운영자가 아닌 주체에 심지 않고, 요청은 이 값을 보낼 통로가 없다.
- [x] 마이그레이션 `0028_operator_read_policy` — 테넌트 표 31개에 `operator_read`(FOR SELECT · PERMISSIVE). **쓰기 정책에는 걸지 않는다.** `schema.sql` 반영 · `0028-assertions.sql`·`0028-drift.sh`(+x) 신설.
- [x] 세션 서명에 관리자 여부를 싣고 **매 요청 `service_operator` 에서 다시 도출**한다. 주장과 어긋나면 거절한다.
- [x] cross-tenant 음성 시험이 비관리자에 그대로 통과한다. 관리자 **쓰기**도 남의 연구실에서 403/404 다.
- [x] 양성 — 관리자가 두 연구실의 카탈로그·데이터셋 상세를 읽는다.
- [x] `gates/config/rls-allowlist.toml` 은 고치지 않았다 — 게이트가 요구하지 않았다(「그 밖의 정책이 더 걸려 있는 것은 red 가 아니다」). 대신 `gates/tools/rls-effect.sh` 의 정책 목록 오라클을 **넓히지 않고 늘렸다**: 기대 목록에 `operator_read` 를 더하면서 ⑴ RESTRICTIVE 는 `d3_file.body_access` 하나뿐 ⑵ `operator_read` 는 모든 표에서 SELECT 전용 두 검사를 새로 붙였다.
- [x] 프런트 — 행별 관리자 토글(확인 대화상자 · 자기 자신 비활성) · 발급 폼 체크박스 · GNB 「전체 연구실」 표기.
- [x] **이 회차가 스스로 만든 결함 1건을 닫았다** — `GET /lab` 의 연구실 행은 `current_lab_id()` 로 고정인데 구성원 수·구성원 격자는 RLS 에만 기대고 있었다. 읽기 스코프가 열리자 **내 연구실 이름 아래 남의 연구실 사람들**이 섰다(RED 실측 — 자기 연구실 98명 · 격자 101명). 두 질의를 연구실에 못 박아 한 화면의 두 값이 같은 범위를 말하게 했다.
- [x] `db/platform/tests/0028-drift.sh` 실행비트를 인덱스에 기록한다(`git update-index --chmod=+x` · 100755 실측).
- [x] 대장에 `BO-3` 을 등재한다(open · after_stage2 · depends_on `BO-2`).
- [ ] `work-item-consistency` green. — **red(판정) 1건**: ㈕ `BO-3` 이 `CLAUDE.md` 의 `after_stage2` 괄호 목록에 없다. 지시에 따라 `CLAUDE.md` 를 고치지 않고 보고한다 — 필요한 편집은 그 괄호의 `` `BO-2` `` 뒤에 `` ·`BO-3` `` 한 토막뿐이다.
- [ ] **특정 연구실 하나로 좁히는 전환 동작** — 미구현. 읽기 op 들이 연구실 인자를 받아야 하는데, 그것은 「경계는 요청에서 오지 않는다」(`CLAUDE.md §3-5`)를 건드리는 계약 판정이다. 지금 선 것은 intent 문면의 「전체 보기 **표시**」까지다.

## 계획 자체 점검

- [ ] intent 7개 원한 결과 → 작업 1~5 로 연결했다. 범위 밖 항목(메일 전반 포함)은 어느 작업에도 넣지 않았다.
- [ ] 작업 1 은 2~4 없이 단독 출하 가능하다. 배포·마이그레이션·계약 기준만으로 닫힌다.
- [ ] 전 기기 종료를 새 기계가 아니라 기존 `session_version` 대조로 얻는다.
- [ ] `deploy_doctor` 항목 수를 15 로 유지한다. 인프라 변경 0 이다.
- [ ] 계정 발급 흐름(`initialPassword`)을 건드리지 않아 신규 계약 파괴 0 이다.
- [ ] Ted 입력 2건이 없으면 해당 단계에서 멈춘다 — 추정으로 채우지 않는다.

## Ted 입력 대기

- (수령 완료 2026-09-12) 계약 동결 해제 서명 축자: "로그인 혼합 입력 400 계약 변경을 승인한다." — intent `## 확인` 절 원문.
- (수령 완료 2026-09-12) `fc45a9aa` push 승인 확인 ⓐ — intent `## 확인` 절.

## spec 추적 및 작업 종료 기준

| spec | 구현 작업 | 완료 증거 |
|---|---|---|
| §1 dev 반영·계약 기준 | 1 | 새 dev 태그 · 15 항목 요약줄 1벌 · 기본 base 계수 · CI base 승격 |
| §2 계정 상태·롤 권한 | 2 | 비활성 401 · `d2_member_role` SELECT 부여 · 드리프트 오라클 |
| §3 백오피스 API | 3 | 목록 6열 · 403 · 400 · `session_version` +1 · 응답·로그 비밀 0 |
| §4 프런트 | 4 | 목록·재설정·비활성화 화면 시험 · 로그인 화면 무변경 |
| §5 인프라·운영 | 5 | 인프라 변경 0 · watcher 재개 기록 |
| §6 마무리 | 5 | 대장 2행 · HANDOFF 5줄 · 보고서 hash 대조 · 사본 삭제 |

각 작업의 실패 시험과 정상 시험이 수집되고 관련 게이트 종료코드가 0 이며 검토 지적이 해소된 뒤 다음 단계로 간다.
red 는 판정과 준비를 갈라 기록한다. 「main 과 동일」은 수용 근거가 아니다.
