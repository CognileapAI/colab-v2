# 로그인 dev 마무리와 운영자 백오피스 확장 — 구현 사양

> intent: [승인 intent](../../intent/2026-09-12-login-backoffice-closeout.md)

상태: spec 초안. 승인 대기. 근거는 개정 intent(2026-09-12 · 메일 철회판)와 정찰 2건이며 값은 실측으로만 적었다.
기준: `main` HEAD `fc45a9aa`(= `origin/main`). 최신 dev 태그 `dev-20260911-2`(`42cffb32`) 에는 로그인 강화 코드가 없다.
근거: [착수 전 실측](../../reports/stage3-login-hardening/recon-closeout-20260912.md).
완료 = dev 배포 green ＋ `deploy_doctor` 15/15 를 **한 번의 실행**으로(`CLAUDE.md §0`). 항목 수 15 를 이 회차에서 늘리지 않는다.

## 0. 변경 경계

- 유지: 비밀번호 scrypt · 최초 변경 강제 · 새 비밀번호+확인 두 칸 · 10~512 코드포인트 · 고정 12시간 세션 · 실패 제한 5회/15분 두 버킷 · 계정 발급 시 운영자가 초기 비밀번호 직접 입력(`initialPassword` 유지).
- 신설: 계정 상태 열 · 계정 목록 · 운영자 비밀번호 재설정 · 비활성화/재활성화 화면.
- 제외: 메일 전반(발송 모듈 · 비밀번호 찾기 · SES/IAM/DNS · 임시 비밀번호 만료 열 · 다시 보내기 · `MAIL_MODE` · staging 실수신) ＋ intent `## 범위 밖` 그대로(§7).

## 1. 로그인 dev 반영과 계약 기준

관찰 가능한 결과

- `git tag --contains fc45a9aa` 가 새 dev 태그 1건을 낸다. 현재는 빈 결과다.
- dev platform 체인에 `db/platform/versions/0025_stage3_accounts.py` · `db/platform/versions/0026_login_sessions.py` 가 적용되고 `deploy_doctor` ⑥(스키마 head platform) 이 OK 다.
- `deploy_doctor` ⑮(실행 sha ∈ main) 가 새 배포 sha 로 OK 다 — 검사 대상은 EC2 `/opt/colab-v2` 의 `CURRENT_SHA`·`MAIN_SHA` 한 줄(`services/core-api/ops/deploy_doctor.py` 선택자 `check_main_ancestry`).
- 15 항목 요약줄에 SKIP·BAD 가 0 이고 한 번의 실행에서 나온다.

계약 동결 seam 의 기계

- 검사기 = `gates/tools/contract-breaking.sh`. 축자 「비교 기준(frozen seam) = **git HEAD 판의 contracts/**」 · 「별도의 frozen 사본을 레포에 두면 그 사본 자체가 드리프트 면이 하나 더 생긴다」.
- 갱신할 baseline 파일이 없다. 기준 이동 수단은 ref 뿐 — `COLAB_BREAKING_BASE_REF`(기본 `HEAD`) · `COLAB_CONTRACTS_BASE` · `COLAB_CONTRACTS_REV`. 도구는 oasdiff 도커 이미지(다이제스트 고정) · `--fail-on ERR`.
- 순서 = **기본 base 로 1회 먼저 실행**한다. 혼합 입력 400 변경이 `fc45a9aa` 로 커밋된 지금 ERR 0 이 예상값이며, 그 경우 판정은 「red 부재 · 서명은 사후 등재」다 `[미확인 — 실행 1회로 확정]`.
- 이 회차는 계약 **추가**만 한다(§3 3건). 기본 base·PR base 어느 쪽에서도 신규 ERR 0 이 기대값이다.
- 이미 병합된 혼합 입력 400 의 동결 해제 서명은 **dev 배포 전에** 수령한다. 자리는 `PLAN-SoT §9` 한 곳이다(`.claude/rules/colab-rules.md §8`).
- 게이트 승격 1건 — `.github/workflows/ci.yml` 의 단계 「파괴적 변경 탐지 (emit vs frozen seam)」(`run: ./gates/run.sh contract-breaking`) 에 `COLAB_BREAKING_BASE_REF: origin/main` 을 더한다. PR 문맥에서는 merge-base 가 그 값이 되어 기본 `HEAD` 기준의 무차분 통과를 막는다. 앵커는 단계 이름이며 행 번호를 쓰지 않는다.

실패 시험

- `COLAB_BREAKING_BASE_REF` 를 `fc45a9aa^` 로 두고 1회 실행해 ERR 가 실제로 잡히는지 확인한다(검사기 생존 증명). 이 실행값을 판정 계수에 합산하지 않는다.
- CI 승격분은 `origin/main` 기준으로 1회 돌려 종료코드를 기록한다.
- `deploy_doctor` 를 마이그레이션 적용 전에 1회 돌려 ⑥ 이 BAD 인 것을 먼저 관찰한다. 적용 후 OK 로 바뀐 것만 완료 근거로 쓴다.
- 부분 실행 두 벌을 합산해 15/15 라 적지 않는다.

## 2. 계정 상태 열과 롤 권한

관찰 가능한 결과

- `db/platform/versions/0027_account_status.py` 1건. 다음 번호 근거 = 현재 head `0026_login_sessions.py`(실측).
- `account_admin.login_credential` 에 열 1개가 는다 — `status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive'))`. 자리 근거 = `db/platform/schema.sql` 의 같은 표(`must_change_password`·`session_version` 과 한 행). 기존 행은 `active` 로 남는다.
- `gates/config/rls-allowlist.toml` 을 고치지 않는다 — `login_credential` 이 이미 등재돼 있다(실측 확인).
- 목록의 역할 열을 위해 `services/core-api/ops/account-admin-role.sql` 에 `GRANT SELECT ON d2_member_role` 를 더한다. 현재는 같은 표에 `INSERT` 만 있다(실측 — `GRANT INSERT ON d1_account, d2_member_role`).
- 모든 기기 종료의 기계 = `session_version`. 확인된 경로 — 발급 시 `services/core-api/src/colab_core/kernel/login_sessions.py` 가 `credential_version` 으로 서명에 싣고, 인증마다 `session_version != claims.credential_version` 이면 거절한다. 재설정·비활성화는 이 값을 +1 하고 같은 트랜잭션에서 그 계정의 `account_admin.login_session.revoked_at` 을 채운다.
- 재활성화는 `status='active'` 로만 되돌리고 비밀번호를 되살리지 않는다.

실패 시험

- 권한 부여 전 목록 조회가 역할 열에서 권한 오류인 것을 먼저 관찰한다.
- `status='inactive'` 계정의 로그인이 401 이며 응답으로 존재 여부가 갈리지 않는다.
- 비활성 거절이 실패 제한 버킷을 오염시키지 않는다.
- 재적용 판정·스키마 일치·드리프트 오라클을 `0027` 짝 파일로 고정한다.

## 3. 운영자 백오피스 API

관찰 가능한 결과

- `GET /admin/accounts` — 전 연구실 한 목록. 열 = 이메일·이름·역할·연구실·상태·최근 로그인. 최근 로그인은 `account_admin.login_session` 의 `MAX(issued_at)` 집계이며 새 열을 만들지 않는다. 이메일·연구실·역할·상태 필터.
- `POST /admin/accounts/{accountId}/password-reset` — 운영자가 **새 초기 비밀번호를 직접 입력**한다. 저장은 기존 scrypt 경로 재사용 · `must_change_password=true` · `session_version` +1 로 모든 기기 종료. 응답·로그에 비밀번호 원문 없음.
- `POST /admin/accounts/{accountId}/status` — `{status: active|inactive}`. 비활성화는 즉시 로그인 거절 ＋ 기존 로그인 종료. 데이터·소유권 유지(행 삭제 없음).
- 세 경로 모두 `services/core-api/src/colab_core/app/routes/accounts.py` 선택자 `_require_operator`(= `account_admin.service_operator` 행 존재) 를 통과한다. 비운영자는 403.
- 계약 3건(`listServiceAccounts`·`resetServiceAccountPassword`·`setServiceAccountStatus`)을 `contracts/seams/fe-core.yaml` 에 **추가**하고 `frontend/src/generated/fe-core.ts` 를 재생성한다. 기존 `POST /admin/accounts` 형태는 무변경이며 신규 파괴 0 이다. 생성물은 손으로 고치지 않는다.
- 범위 밖 — 역할·연구실 변경 · 운영자 지정 UI · 일괄 등록 · 감사 로그 조회.

실패 시험

- 비운영자 토큰의 세 경로 전부 403.
- 다른 연구실 계정이 목록에 나오는 것이 의도임을 명시 시험으로 고정한다(운영자 전용 경로의 등재된 예외).
- 자기 자신 비활성화 시도는 400 으로 거절한다.
- 재설정·비활성화가 각각 `session_version` 을 정확히 1 올린다. 재설정 전 발급한 토큰 2개(다른 기기 가정)가 둘 다 401 이고 다른 계정 토큰은 200 이다.
- 새 비밀번호 문자열이 응답 본문·로그에 없다(`assert pw not in response.text` · `assert pw not in caplog.text`).
- 재설정 뒤 당사자 로그인이 첫 변경 화면으로 가고 `PUT /me/password` 경로는 기존 그대로다(`services/core-api/src/colab_core/kernel/db_credentials.py` 선택자 `change_password`).

## 4. 프런트

관찰 가능한 결과

- `frontend/src/routes/AccountAdminPage.tsx` — 기존 계정 추가 폼 유지(초기 비밀번호 칸 유지) ＋ 계정 목록 표(필터 포함) ＋ 행별 「비밀번호 재설정」·「비활성화/재활성화」.
- 재설정은 새 초기 비밀번호 입력 2칸(값·확인)을 쓰며 기존 `frontend/src/auth/passwordRules.ts` 판정을 재사용한다.
- `frontend/src/auth/LoginPage.tsx`·`PasswordChangePage.tsx` 는 변경 없다.
- 기존 작업 보호(`frontend/src/auth/useWorkProtection.ts`) 연결 유지. 재설정 입력값은 `frontend/src/auth/draftVault.ts` 보관 대상이 아니다.

실패 시험

- 화면·DOM 어디에도 재설정 비밀번호가 응답으로 되돌아와 렌더되지 않는다.
- 비활성 계정 행의 버튼 라벨이 「재활성화」로 바뀐다.
- 목록 필터 4종이 서버 질의 인자로 전달된다.
- 비운영자 진입 시 403 안내가 표시되고 목록이 그려지지 않는다.

## 5. 인프라·운영

- 인프라 변경 0 — IAM·DNS·새 env 없음. `infra/` 파일을 고치지 않는다.
- `deploy_doctor` 항목 수는 15 로 유지한다. 16번째 항목 신설은 이 회차 범위 밖이며 완료 정의(15/15) 를 건드리지 않는다.
- staging 자동배포 watcher 는 hold 상태다. **dev 배포 green 뒤 재개**는 intent Q5 로 확정된 결정이며 이 회차에서 재판정하지 않는다.
- staging 은 리허설이다 — 완료 판정을 하지 않고 배포 창을 기록하지 않는다(`CLAUDE.md §0`).

## 6. 마무리

- 대장 `BO-1` 을 `done` 으로 갱신한다(intent Q7 — 현재 계정 추가 화면으로 완료). 확장분(목록·재설정·비활성화)은 새 항목으로 등재한다. `stage: after_stage2` 면 `CLAUDE.md` 의 `after_stage2` 괄호 목록도 같은 커밋에서 갱신한다.
- `03-HANDOFF §1` 갱신은 5줄 이내다. 새 결정은 `PLAN-SoT §9` 에 값과 근거로 적는다.
- 별도 작업 사본의 보고서 2개 디렉터리를 승인된 전달 경로로 레포에 복사하고 hash 를 대조한 뒤 커밋한다. 커밋 확인 후 사본을 삭제한다(intent Q6).

## 7. 범위 밖 (intent 축자)

메일 발송 전반(임시 비밀번호 메일 · 비밀번호 찾기 · SES) — 후일 묶음, 자체 계정 생성(가입)과 함께 · Google 로그인 · 역할·연구실 변경 UI · 운영자 지정 UI(SQL 수동 유지) · 모든 기기 로그아웃 버튼 · 프로세스 간 공유 실패 제한 · 기존 발급 다운로드 URL 10분 즉시 회수.

## 8. intent 추적

| intent 항목 | spec | 완료 증거 |
|---|---|---|
| dev 배포 ＋ 15/15 한 번의 실행 | §1 | 새 dev 태그 · 15 항목 요약줄 1벌 |
| 계약 변경 red 정리(Ted 서명) | §1 | 기본 base 계수 ＋ `PLAN-SoT §9` 서명 행 ＋ CI base 승격 |
| 계정 발급 현행 유지 | §0·§4 | `initialPassword` 무변경 계약 차분 0 |
| 계정 목록(전 연구실 · 6열 · 필터) | §3·§4 | 목록 시험 · 최근 로그인 집계 |
| 운영자 비밀번호 재설정 ＋ 전 기기 종료 | §3 | `session_version` +1 · 옛 토큰 401 · 응답·로그 비밀 0 |
| 비활성화/재활성화 | §2·§3·§4 | 비활성 401 · 행 삭제 0 · 버튼 라벨 전환 |
| 「직접 추가」 완료 · 확장은 새 항목 | §6 | 대장 2행 갱신 |
| 보고서 회수 ＋ 사본 삭제 · watcher 재개 | §5·§6 | 커밋 hash 대조 · dev green 뒤 재개 기록 |

## Ted 입력 대기

1. (수령 완료 2026-09-12) 계약 동결 해제 서명 축자: "로그인 혼합 입력 400 계약 변경을 승인한다." — 등재 자리는 `PLAN-SoT §9` 한 곳.
2. (수령 완료 2026-09-12) `fc45a9aa` push 승인 확인 ⓐ.
