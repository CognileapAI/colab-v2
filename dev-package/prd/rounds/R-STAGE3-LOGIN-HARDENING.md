> spec: [stage3-login-hardening.md](../specs/stage3-login-hardening.md)
# Stage 3 로그인 신뢰성과 복구 실행 계획

> 실행자는 `executing-plans`를 적용한다. 쓰기 주체는 사본당 하나이며 독립 검토만 읽기 전용으로 병행한다.

**Goal:** 확정된 8개 로그인 정책·후속 동작 3개와 감사 결함 LH-1~7을 구현하고 격리 검증 후 WSL stage에서 확인한다.
**Architecture:** 서버에 개별 세션과 종료 전용 자격을 둔다. 브라우저 세션 조정기가 탭 전환·종료 큐를 관리하고 작업 보호기가 초안과 업로드의 주체를 고정한다.
**Tech Stack:** FastAPI/Pydantic, PostgreSQL/Alembic, React/TypeScript, Vitest, agent-browser.
**Spec:** 위 링크와 [확정 intent](../../intent/stage3-login-hardening.md)가 설계 및 정책 정본이다.
**상태:** 구현·전체 관련 게이트·WSL stage 검증 완료(2026-09-12). 13 green/사용자 수용 계약 red1/준비 실패0. 자동 전체 green 아님. 최종 [실행 보고](../../reports/stage3-login-hardening/final/release.md)에서 시험 종류·호환 복구 한계·watcher hold를 구분한다.

## 공통 제약과 실행 순서

- 작업 사본 `/home/ttlhi10/colab-stage3-staging-deploy`, HEAD `b63c9e8a0d40`와 기존 미커밋 변경을 보존한다.
- 세션은 로그인부터 고정12시간. 실패 제한은 자격/클라이언트 각각5회/15분, 프로세스 메모리 유지.
- 비밀번호10~512 Unicode 코드포인트, 첫 변경은 새 값+확인만. 실제 사용자 암호 변경 금지.
- 문서 확정과 구현 완료는 별개다. 각 작업은 실패 시험→최소 구현→통과→검토 순서로 체크한다.
- 변경 전 guard, lifecycle 선언, 관련 규칙을 적용한다. core 변경 전 s3-upload, infra/ops 변경 전 deploy 규칙을 읽는다.
- WSL stage 배포만 기존 승인 범위다. 커밋/push, AWS dev/prod 배포, 제품 데이터 삭제는 하지 않는다.
- 표의 의존 순서로 진행하고 각 작업 종료 시 실제 게이트 종료코드·실패·면제·준비 실패 계수를 기록한다.

| 작업 | 산출물 | 선행 | 정책/결함 |
|---|---|---|---|
| 1 | 안전한 오류와 엄격한 로그인 계약 | 없음 | LH-1/5/6 |
| 2 | 서버 추적 세션·만료·종료 | 1 | 정책2/3/8 |
| 3 | 최초 변경의 원자성 | 2 | 정책3/6 |
| 4 | 탭 세션 조정·오프라인 종료 | 2 | 정책1/2/5/8, LH-3/4 |
| 5 | 모든 작성 표면·업로드 보호 | 4 | 정책4/7 |
| 6 | 입력·통신 실패 화면 복구 | 3/4/5 | 정책6, LH-2/7 |
| 7 | 전체 증명 및 호환 배포 | 1~6 | 전체 |

시험 실행은 저장소 루트에서 `python3 scripts/agent-bridge.py run-tool gate -- <gate>`를 사용한다.
이 세션에서 순차 구현하고 작업별 검토를 받는 방식을 기본으로 한다. 쓰기 레인을 위임하면 기존 미커밋 계정 변경을 포함한 기준 사본을 먼저 만들고 HEAD만 복제해 변경을 누락하지 않는다.
작업별 새 시험을 기존 frontend-test/service-tests-core-api 수집 경로에 넣고, RED와 GREEN 로그에서 해당 시험 이름이 실제 실행됐는지 확인한다.

### Task 1: 오류 비밀 제거와 입력 계약

**Files:** Modify `services/core-api/src/colab_core/app/main.py`, `app/routes/session.py`(이하 app/kernel 경로는 같은 colab_core 아래), `contracts/seams/fe-core.yaml`; Generate `frontend/src/generated/fe-core.ts`; Create `services/core-api/tests/test_login_validation_privacy.py`; Modify `test_session_login.py`, `test_admin_account_flow.py`(이하 test_*.py는 services/core-api/tests 아래).
**Interfaces:** 기존400 envelope 유지. accountName 최대320; accountName+password 또는 accessCode 단독만 허용한다.
- [x] 길이·자료형·중첩객체·잘못된 JSON·다른 필드 오류에 시험 marker가 응답/로그에 반사되는 RED를 확인한다.
```python
assert response.status_code == 400
assert marker not in response.text
assert marker not in caplog.text
```
- [x] validation details에는 안전한 오류 type만 담고 입력을 담는 msg/input/ctx/loc는 직렬화하지 않는다.
```python
safe = [{"type": e["type"]} for e in exc.errors()]
```
- [x] 혼합 입력은 인증기 이전400으로 차단한다. null은 미지정, 빈 값은 min_length 검증으로 거절한다.
- [x] 유효137자 이메일 생성→로그인, 320/321 경계, 두 정상 로그인 형태, 모든 혼합 형태를 검사한다.
- [x] 실패5회 이후429, 성공 초기화, 자격·클라이언트 버킷을 각각 검사한다. 혼합형400이 인증 시도를 우회 실행하지 못함을 확인한다.
- [x] contract-lint/generated-up-to-date/service-tests-core-api 통과와 contract-breaking 사용자 수용 red1을 구분해 LH-1/5/6을 갱신한다.
  - 현재 판정: strict 혼합400이 기존 허용 요청을 거절하므로 `contract-breaking` ERR1. 우회·baseline 변경 없이 red를 유지한다. 사용자 명시 승인으로 계약 변경을 수용했으며 [수용 기록](../../reports/stage3-login-hardening/task1/contract-acceptance.md)에 근거를 남겼다. 자동 전체 green은 아니며 Task2 구현 진입은 가능하다.

### Task 2: 개별 서버 세션과 종료 자격

**Files:** Create `db/platform/versions/0026_login_sessions.py`, `db/platform/tests/0026-assertions.sql`, `db/platform/tests/0026-drift.sh`, `services/core-api/src/colab_core/kernel/login_sessions.py`, `services/core-api/tests/test_tracked_sessions.py`; Modify `db/platform/schema.sql`, `gates/config/rls-allowlist.toml`, `services/core-api/ops/account-admin-role.sql`, `kernel/authn.py`, `kernel/session_token.py`, `app/deps.py`, `app/routes/session.py`, `contracts/seams/fe-core.yaml`, `frontend/src/generated/fe-core.ts`.
**Interfaces:** `IssuedBrowserSession(token: str, expires_at: datetime, session_id: str, revocation_token: str)`; `issue_session(subject, *, credential_kind, credential_version, now) -> IssuedBrowserSession`; `authenticate_session(token, *, purpose, now) -> Subject | None`; `revoke_session(session_id, *, now) -> None`; `revoke_by_capability(value, *, now) -> None`. `credential_kind`는 `database|planted-code|legacy-file`, `purpose`는 `normal|password-change`로 제한한다. 저장소 장애는 명시적 예외→503.
- [x] 최신 migration head를 확인한다. 번호 충돌 시 새 head 다음 번호로 세 파일을 함께 조정한다.
- [x] 별도 브라우저A/B 로그인 후 A 종료 시 A401/B200, DB 장애503, 종료 자격으로 일반 API 접근401 시험의 RED를 확인한다.
```python
assert request_with(session_a.token).status_code == 401
assert request_with(session_b.token).status_code == 200
assert request_with(session_a.revocation_token).status_code == 401
```
- [x] spec §3 표·권한을 만들고 32바이트 난수의 digest만 저장한다. ss1에 sid/sub/lab/exp/generation/필요 credential_version을 서명한다.
- [x] DB/file-password/accessCode 발급을 공통 issue_session으로 합친다. DB 계정 세션은 `credential_version`을 필수로 싣고 매 요청마다 현재 DB 값과 대조한다. 인증은 DB 행과 서명·주체·만료·generation을 모두 통과한 뒤 제한 범위의 `Subject`만 요청 의존성에 전달한다.
- [x] static/v1/db1 직접 bearer 사용처를 코드·배포 설정의 키 이름 수준에서 목록화한다. 사용자 API 우회는 제거하고 실제 machine 인증은 기존 별도 경로로 보존한다. 분리가 불가능한 사용처는 해결 전 배포 차단한다.
- [x] POST /sessions 응답에 sessionId/revocationToken을 추가하고 DELETE /sessions/current 및 POST /sessions/revoke를 구현한다. 후자는 unknown/expired/revoked204, malformed400, DB503이다.
- [x] 발급 실패 시 token을 반환하지 않는다. 일반 앱 롤의 표 접근 거절과 인증 롤의 제한된 권한을 실제 DB에서 검증한다.
- [x] issued_at+12h 직전/정각, 토큰 변조·다른 주체·옛 형식 거절, 반복 종료, 서버 재시작 뒤 회수 유지, 로그/응답 비밀0을 검사한다. 제한 세션은 일반 API403이고, 같은 계정의 다른 최초 세션은 한 세션의 비밀번호 변경 뒤 credential_version 불일치401인지 검사한다.
- [x] 회수된 세션으로 신규 다운로드 티켓 발급이401인지 검사한다. 회수 전에 이미 발급된 다운로드 URL은 기존10분 capability 계약대로 별도 만료하며 이 작업에서 회수하지 않는다.
- [x] 계약·서버 게이트와 platform migration/schema/drift/권한 검사를 실행한다. `migration-single-head`, `migration-drift`, `schema-diff`, `rls-coverage`, `rls-effect`, `db-boundary`의 종료코드를 보고서에 기록한다.

### Task 3: 최초 비밀번호 변경과 원래 만료 보존

**Files:** Modify `kernel/db_credentials.py`, `kernel/login_sessions.py`, `app/routes/accounts.py`; Test `test_db_account_auth.py`, `test_admin_account_flow.py`, `test_tracked_sessions.py`.
**Interfaces:** 첫 변경은 같은 session_id/expires_at/종료 자격을 유지하고 token generation만 증가한다. 일반 세션 변경403, 초기값 재사용400.
- [x] 12h 만료 직전 변경해도 원래 시각에 만료되고 동시 두 요청 중 하나만 성공하는 RED를 확인한다.
```python
assert changed.session_id == initial.session_id
assert changed.expires_at == initial.expires_at
assert sorted(statuses) == [200, 401]
```
- [x] DB 자격 로그인·최초 변경은 credential→session 순으로 잠근다. 종료는 session만 잠그며 이후 credential 잠금을 요청하지 않는다.
- [x] 상태/version/만료 재확인, credential 갱신과 generation 증가를 한 트랜잭션에 넣고 잠금 조회+UPDATE RETURNING으로 반환값을 만든다.
- [x] commit 후 find 조회가 없음을 장애 주입으로 확인한다. commit/HTTP 응답 유실은 성공 여부 불명으로 남고 자동 재실행하지 않는다.
- [x] 옛 token401, 새 token200, 초기 암호 거절, 새 암호 재로그인 성공, 동시 변경 version증가1, 변경과 종료 경합을 실제 DB에서 검사한다.
- [x] service-tests-core-api를 통과한다.

### Task 4: 탭 세션 조정과 종료 큐

**Files:** Modify `frontend/src/auth/store.ts`, `AuthGate.tsx`, `frontend/src/api/client.ts`; Create `frontend/src/auth/sessionCoordinator.ts`, `logoutQueue.ts`, `workGuard.ts`, `frontend/test/session-coordinator.test.ts`, `logout-queue.test.ts`, `work-guard.test.tsx`.
**Interfaces:** `BrowserSession={token:string,sessionId:string,expiresAt:string,revocationToken:string}`; `getSession():BrowserSession|null`; `transitionTo(next:BrowserSession, verifiedAccountId:string):Promise<boolean>`; `logoutCurrent():Promise<void>`; `clearIfCurrent(token:string):void`; `registerWork(key:string,state:{accountId:string,dirty:boolean,inFlight:boolean}):()=>void`; `canTransition():boolean`; `discardAccountWork(accountId:string):Promise<void>`. getToken은 활성 세션만 반환하는 호환 adapter다.
- [x] 이전401/logout/me 응답이 새 세션을 지우거나 덮는 RED와 실제 storage 이벤트 미전파 RED를 확인한다.
```typescript
clearIfCurrent('old-token');
expect(getSession()?.token).toBe('new-token');
```
- [x] Web Locks로 전환을 직렬화하고 storage/BroadcastChannel로 전파한다. 각 탭 확인을 기다리며 미지원·응답 불명은 전환 차단 안내를 표시한다.
- [x] 전환 준비 중 각 탭 새 mutation도 잠가 작업 시작과 전환 승인의 경합을 닫는다. 차단된 전환에서 이미 발급한 후보 세션은 종료 큐로 회수하고 활성화하지 않는다.
- [x] API 요청의 token/sessionId와 응답 epoch를 고정한다. 현재값에 해당하는401만 제거하며 /me 확인 전 계정 화면을 가린다.
- [x] 명시적 로그아웃 요청은 Task5 작업 보호기의 확인 결과를 받은 뒤 logoutCurrent를 호출한다. 확정 후에는 종료 큐 기록 및 모든 탭 접근 제거를 즉시 수행한다. 큐에는 접근 token을 넣지 않는다.
- [x] 시작/online/backoff1~60초로 이전 capability만 재시도한다. 204제거,503/연결실패 유지,400중단안내, 원래 만료 시 만료와 종료 확인을 구분한다.
- [x] 저장소 실패·중복탭 재시도·앱 재시작·새 로그인 뒤 옛 종료 완료를 검사한다. 저장 실패 시 메모리 토큰 제거와 영속 큐 유실 안내를 확인한다.
- [x] `workGuard.ts`의 등록·해제·전환 판정·계정별 폐기를 구현한다. 두 탭 dirty/inFlight, 해제, 폐기 완료 전 차단을 `work-guard.test.tsx`에서 검증하며 Task5는 이 인터페이스를 화면에 연결한다.
- [x] legacy 저장 token은 재인증 상태로 전환한다. access token이 종료 큐/로그에 없는지 검사하고 frontend-test/typecheck를 통과한다.

### Task 5: 작성 상태와 업로드 주체 보호

**Files:** Create `frontend/src/auth/draftVault.ts`; Modify `AuthGate.tsx`, `sessionCoordinator.ts`, `frontend/src/api/client.ts`, Task4의 `workGuard.ts`와 아래 화면·관련 화면 시험. 컴포넌트 상대 경로는 `frontend/src/components/` 아래다.
**Interfaces:** Task4의 `registerWork`·`canTransition`·`discardAccountWork`를 각 화면에 연결한다. `saveDraft(accountId:string,key:string,value:unknown):void`; `readDraft(accountId:string,key:string):unknown`. vault는 메모리만 사용하며 비밀 필드는 등록하지 않는다.

| 표면 | 실제 파일 | 보호할 상태 |
|---|---|---|
| 계정 발급 | frontend/src/routes/AccountAdminPage.tsx | 이메일/역할/연구실, 초기 암호 복원 제외 |
| 프로젝트 | project/ProjectFormModal.tsx | 생성·수정 draft |
| 데이터셋 | detail/useDatasetEdit.ts, detail/DatasetEditForm.tsx | metadata draft |
| 연구실 | lab/LabInfoPanel.tsx | 연구실 정보 |
| 권한 | members/MemberPermissionGrid.tsx | 권한 draft/확인 |
| 업로드 | upload/UploadModal.tsx, upload/pendingStore.ts, upload/transferSource.ts, upload/uploadSource.ts, upload/xhrPut.ts | File·메타·uploadId·datasetId·전송 controller |
| 파일/대표 그림 | detail/FileList.tsx, detail/RepresentativeImageSection.tsx | 선택 File/진행 요청 |
| 계보 | lineage/LineageSection.tsx, lineage/LineageFixModal.tsx | 선택/방법/사유 |
| 단문 사유 | dashboard/TodoInbox.tsx, approval/VerificationAction.tsx | 접근 거절·검증 취소 사유 |

- [x] `onSubmit|FormData|api\.(POST|PUT|PATCH|DELETE)` 검색 결과를 표와 대조한다. 빠진 mutation을 추가한 뒤 구현한다.
- [x] 두 탭 중 하나 dirty/inFlight면 전환 차단, 저장·명시 취소 후 허용하는 RED를 확인한다.
```typescript
const release = registerWork('project', {accountId:'A', dirty:true, inFlight:false});
expect(canTransition()).toBe(false);
release();
expect(canTransition()).toBe(true);
```
- [x] 각 표면에 등록/해제를 연결한다. 초기 빈 폼은 clean이다. 응답 없는 탭은 사용자에게 해당 탭 작업 종료/취소 후 재시도를 안내하며 heartbeat 유실만으로 clean 처리하지 않는다.
- [x] 만료 시 앱 트리와 File 참조를 현재 탭에서 보존한 채 inert 인증 overlay로 가린다. 비밀번호 입력은 지우고 새 mutation을 차단한다.
- [x] /me로 확인한 accountId가 보관 초안의 소유자와 같으면 dirty 상태여도 재인증을 적용하고 overlay를 해제한다. 사용자 입력 이메일만으로 같은 계정이라고 판정하지 않는다.
- [x] 다른 계정은 기존 작업 폐기 확인을 먼저 받는다. 취소하면 초안 유지·후보 세션 회수, 확정하면 각 탭 discardAccountWork 완료 후에만 새 계정 화면을 표시한다.
- [x] 직접 로그아웃 시 작업이 있으면 ‘돌아가기 / 작업 버리고 로그아웃’을 표시한다. 돌아가기는 세션·초안을 유지한다. 확정은 모든 탭 초안·비밀 입력 제거와 로컬 전송 abort 후 logoutCurrent를 실행한다. 서버 접수 작업까지 취소됐다고 표시하지 않는다.
```typescript
// 실제 탭 상호작용 시험의 관찰 결과
expect(sameAccountAfterExpiry.draftText).toBe(originalDraftText);
expect(cancelledLogout.draftText).toBe(originalDraftText);
expect(confirmedLogout.activeSession).toBeNull();
expect(confirmedLogout.draftText).toBe('');
```
- [x] 작업 탭이 응답하지 않아도 확정 로그아웃의 로컬 종료를 무기한 기다리지 않는다. 공유 종료 상태를 기록하고 해당 탭이 다시 실행될 때 UI/API 접근 전에 초안 폐기와 종료를 적용한다. 다른 계정 전환은 모든 탭의 안전 확인 전까지 차단한다.
- [x] upload 체인에 시작 account/session snapshot과 AbortController를 전달한다. 새 단계는 유효 세션 확인 후 시작하고 명시 취소는 abort한다.
- [x] pending upload를 account/lab/uploadId로 묶고 재로그인 후 서버 상태와 datasetId를 조회한다. 자동 재업로드·자동 등록0을 검증한다.
- [x] 만료 전 접수 후 응답 유실, 파일 전송 중 만료, 다른 계정 재인증, 확인되지 않은 취소를 실제 브라우저에서 시험한다. frontend-test/typecheck를 통과한다.

### Task 6: 통신 실패 및 비밀번호 안내

**Files:** Modify `frontend/src/auth/LoginPage.tsx`, `PasswordChangePage.tsx`, `frontend/src/routes/AccountAdminPage.tsx`; Create `frontend/src/auth/passwordRules.ts`, `frontend/test/password-rules.test.ts`; Modify `frontend/test/auth.test.tsx`, `account-admin.test.tsx`.
**Interfaces:** `passwordLength(value:string):number`, `validNewPassword(value:string):boolean`. 발급·변경에서 같은 함수를 쓴다.
- [x] 세 폼 fetch reject 후 busy 해제, 중복 제출1회, 기존401/429 안내 유지 시험의 RED를 확인한다.
- [x] catch에 고정 안내, finally에 busy 해제를 넣는다. 비밀번호 변경 응답 유실은 결과 불명과 새 비밀번호 재로그인 안내를 보여 주고 자동 재전송하지 않는다.
- [x] 새 비밀번호 인증이401로 거절되면 기존 초기 비밀번호를 직접 시도하도록 안내한다. 연결 실패·503·429에는 암호가 틀렸다고 표시하지 않는다. 기존 값 성공 시 서버의 최초 변경 상태에 따라 변경 화면을 표시한다.
```typescript
expect(afterLostChangeResponse.automaticLoginRequests).toBe(0);
expect(afterLostChangeResponse.automaticPasswordChangeRequests).toBe(0);
expect(loginWithUnchangedInitialPassword.screen).toBe('password-change');
```
- [x] commit 완료+응답 유실과 commit 이전 실패를 각각 주입해 새 값/기존 값의 실제 인증 결과 및 안내를 검사한다.
- [x] 확인 불일치는 입력 후 표시하고 제출을 막는다. 비밀번호를 trim/정규화하지 않는다.
```typescript
export const passwordLength = (value:string) => Array.from(value).length;
export const validNewPassword = (value:string) => passwordLength(value)>=10 && passwordLength(value)<=512;
```
- [x] UTF-16 minLength/maxLength를 제거하고 ASCII/한글/이모지9·10·512·513 경계와 붙여넣기를 검사한다. 이모지257개는 잘리지 않아야 한다.
- [x] 격리 DB 발급→로그인→변경과 프런트 판정이 같음을 확인한다. frontend-test/typecheck 및 service-tests-core-api를 통과한다.

### Task 7: 통합 증명과 WSL stage 적용

**Files:** 실행 보고서 `dev-package/reports/stage3-login-hardening/`, 본 계획; 필요 운영 변경 `infra/staging/compose.i2.yml`, `db-bootstrap.sh`, `preflight.sh`, `deploy.sh`.
**Interfaces:** 새 API·DB·FE를 하나의 호환 release로 배포한다. 예전 무상태 이미지로 rollback하지 않는다.
- [x] 모든 쓰기 후 lifecycle snapshot을 선언하고 contract-lint/breaking/generated-up-to-date, frontend-typecheck/test, service-tests-core-api를 한 검증 실행에 기록한다. `migration-single-head`, `migration-drift`, `schema-diff`, `rls-coverage`, `rls-effect`, `db-boundary`도 선언한다. CSS 변경 시 정적 검사/frontend-visual을 추가한다.
- [x] 별도 DB에서 migration 적용·재적용 판정·schema 일치·제한 롤 접근·실제 백업/복원을 확인한다. 기존 계정/자격과 새 회수 상태가 복원되는지 검사한다.
- [x] agent-browser 실제 두 탭·두 브라우저 문맥과 격리 DB/고정시계 경계시험을 대조해 8정책과 spec §8 후속 동작3개를 각각 증명한다. 브라우저 주입과 실제12시간 대기를 구분한다. 고정시계는 격리 시험에만 사용하고 stage 시계를 바꾸지 않는다.
- [x] LH-1~7 재현 시험의 기대값을 정상 동작으로 바꿔 전부 통과시킨다. 초기 로그인·최초 변경·비운영자403·동시 변경·DB503을 포함한다.
- [x] ss1 검증·세션 조회·회수를 보존하는 최소 호환 기준 이미지의 source snapshot을 고정한다. snapshot은 Task2 세션 저장소, Task3 최초 변경, Task4 종료 큐 API 호환, Task6 오류 계약을 포함하며 전체 기능 이미지와 태그·digest를 구별한다.
- [x] 전체 이미지로 ss1 발급→최초 변경→원래 만료 유지→오프라인 종료 큐 적재를 만든 뒤 기준 이미지로 전환해 재접속 종료 재시도204, 회수 세션401, 별도 정상 세션200을 한 흐름으로 증명한다.
- [x] stage head/이미지 digest/자동배포 watcher 상태를 확인하고 검증 중 덮어쓰기 가능성을 통제한다. 백업과 호환 rollback 증거가 없으면 배포하지 않는다.
- [x] platform migration 후 core/frontend를 고유 태그로 교체한다. 다른 서비스 신원과 실제 사용자 계정/암호를 보존한다.
- [x] 비로그인401, 새 브라우저 세션, 두 탭 로그아웃, 다른 문맥 유지, 최초 변경, 번들/인증 소스 일치를 stage 시험 계정으로 확인한다.
- [x] 장애 시 호환 기준 이미지로 core/frontend만 되돌리는 절차를 고정했다. 격리 이미지 전환에서 회수 유지·상태를 확인했으며 stage 장애는 없어 실제 stage 되돌림은 미실행이다. DB downgrade/사용자 암호 복원은 하지 않는다.
- [x] 기존 발급 다운로드 URL은 별도10분 capability라 세션 회수와 함께 취소되지 않는 잔여 범위로 보고한다. 새 다운로드 티켓 발급만 회수 세션401로 막는다.
- [x] 실제 종료코드·세 계수·미실행·시험 데이터 정리·잔여 제한을 보고하고 전체 체크 완료 시에만 구현 완료로 표시한다.

## 계획 자체 점검

- [x] 확정8정책→작업2~6, 후속3동작→작업5/6, 기존7결함→작업1/4/6으로 연결했다.
- [x] 서버 migration, 종료 전용 자격, 모든 작성 표면, 업로드 주체, 호환 rollback을 포함했다.
- [x] 브라우저 종료/새로고침 후 초안 영속 복구는 약속하지 않는다. 프로세스 간 공유 limiter는 범위 밖이다.
- [x] 구현·게이트·stage 검증 완료 — 수용 red1 보존, 자동 전체 green 아님.

### 중간 실행 이력 (최종 결과는 상단 보고서 참조)

- Task1: `task1/contract-acceptance.md`의 사용자 수용대로 contract-breaking ERR1을 그대로 보존한다.
- Task2/3: `task23/gate-summary.json` 11개 중 10개 통과, 수용한 계약 오류 1개, 준비 실패 0개. `task23-boundaries/gate-summary.json` 서버 후속 시험 1111 통과·실패0·skip0·E2E 제외6이며 작업 기록과 현재 파일 대조를 통과했다. 이후 문서 갱신 이전의 검증 snapshot이다.
- Task4~6: 별도 프런트 사본에 작성 표면 10파일 통합, 집중 시험과 typecheck 통과. 독립 검토에서 탭 간 종료 확인·지연401·전환 준비 경합·파일 선택 보호의 추가 보완을 요청했다. 전체 검증 완료로 보지 않는다.
- Task7: 운영과 분리한 `colab_login_hardening_e2e` DB/API와 로컬 브라우저를 준비했다. 백업 복원·호환 rollback·stage 배포는 아직 미실행이다.
- 후속 통합: `integration-core/gate-summary.json`은 수정 전 프런트1237 통과·타입 오류0의 역사 증거다. 실제 두 탭의401 전파와 새 탭의 동일 계정 복구를 추가 수정했으므로 최종 검증으로 재사용하지 않는다.
- 격리 실측: 계정 UI발급/최초 변경, 세션ID·원래 만료 유지, 두 탭 종료와 별도 세션 유지, 원격 초안 로그아웃 확인·취소, 만료 후 동일 계정 초안 복구, 오프라인 종료 후 옛 세션만 회수, 비밀번호 변경 commit 전/후 응답 유실과 수동 초기값/새값 재로그인을 확인했다. 시험 전용 주입과 실제 서버 응답을 구분해 최종 보고서에 기록한다.
- 격리 백업: pg_dump 전체 DB→별도 DB복원, account_admin 3표 및 계정 본문 일치, 제한 롤 권한 재적용, 회수 세션 거절·별도 활성 세션 인증을 확인했다. stage 백업과 호환 이미지 전환 증명은 별도 진행한다.

## spec 추적 및 작업 종료 기준

| spec | 구현 작업 | 완료 증거 |
|---|---|---|
| §1/6 기존 정책·7결함 | 1/3/6 | 비밀0·입력 경계·최초 변경·오류 복구 시험 |
| §2/3 서버 세션 | 2/3 | 기기별 종료·12h 경계·회수 지속·권한/DB 장애 시험 |
| §4 브라우저 상태 | 4 | 지연401/me/logout·오프라인 큐·탭 전파 시험 |
| §5 작성 보호 | 5 | 표의 모든 작성 표면·업로드 응답 유실·같은 계정 복구 |
| §7 운영 | 7 | 전체 게이트·백업 복원·호환 되돌림·stage 실측 |
| §8 확정 후속 동작 | 5/6 | 로그아웃 확인·계정별 복구/폐기·초기 암호 수동 재시도 |

각 작업의 실패 시험과 정상 시험이 수집되고 관련 게이트가0이며 리뷰 지적이 해소된 뒤 다음 단계로 진행한다. 예외는 사용자가 명시 수용한 Task1의 contract-breaking 1건뿐이며, 원래 red와 승인 근거를 보존한 상태로 후속 구현을 진행한다. 자동 lifecycle complete나 배포 green으로 간주하지 않는다. 환경 준비 실패78과 판정 실패1은 구분해 기록한다. 배포는 작업7의 선행 증거가 모두 확보된 뒤 수행한다.
