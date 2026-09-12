# Stage 3 로그인 강화 Task 2·3 인계

상태: 서버 구현과 선언한 검증 실행 완료. 배포·커밋·push 없음.

## 결과

- account_admin.login_session(platform 0026)을 추가했다. 종료 자격은 32바이트 난수 원문 대신 SHA-256 digest만 저장한다.
- 모든 브라우저 로그인은 ss1로 교환한다. 토큰과 DB에서 session/account/lab/expiry/generation/credential kind/purpose/version을 대조한다.
- 제품 배선은 static/v1/db1 bearer를 사용자 인증으로 받지 않는다. 기존 도메인 시험은 create_app의 test-only 주입만 쓴다. 설정 누락 제품 배선은 503으로 닫힌다.
- 현재 세션 종료와 별도 종료 자격 회수는 해당 브라우저 한 세션만 revoke한다. 성공·오류 응답은 Cache-Control: no-store다.
- DB 로그인은 credential lock→비밀번호/version 확인→session insert를 한 트랜잭션에서 수행한다.
- 최초 비밀번호 변경은 credential→session 잠금 순서로 자격 갱신과 generation 증가를 한 트랜잭션에서 수행한다. sessionId와 원래 expiresAt은 유지하고 revocation token 원문은 재전송하지 않는다.
- DB 장애는 로그인 발급, bearer 인증, 현재 세션 종료, 종료 자격 회수에서 503으로 구분한다.

응답 계약은 Session={token, expiresAt, sessionId, revocationToken}, RotatedSession={token, expiresAt, sessionId}, SessionRevocation={revocationToken}이다.

## RED와 GREEN

- 역사 기준 HEAD b63c9e8의 실제 FastAPI 흐름은 POST 로그인201→보호 GET200→DELETE204→같은 bearer 보호 GET200으로 실패했다. 재현 스크립트와 로그는 red/에 보존했다. 이 기준은 Task23 시작 당시의 미커밋 Task1 snapshot과 동일하다고 주장하지 않는다.
- 현재 격리 tmpfs DB 시험은 core-api 1,108/1,108 pass, skipped0, errors0, deselected6(not e2e)이다.
- 독립 경계에는 12h 발급, 재기동 후 회수 지속, 브라우저 A회수/B유지, 종료 capability 회수, DB 장애 503, 제한 세션 일반 API403, 동시 최초 변경 [200,401], 같은 sessionId/expiresAt, old token401을 포함한다.

## 게이트

최종 단일 lifecycle run cdbcaf013e9f4ecfb684aa2311422004:

- green 10: contract-lint, generated-up-to-date, seam-consistency, service-tests-core-api, migration-single-head, migration-drift(오라클21/실행21/실패0), schema-diff, rls-coverage, rls-effect, db-boundary
- red(판정) 1: contract-breaking의 기존 POST /sessions exact-oneof 변경. task1/contract-acceptance.md에서 사용자가 수용한 1건이며 red를 green으로 바꾸지 않았다.
- red(준비) 0

schema-diff는 stage가 아닌 colab_task23_schema_2901792 tmpfs PostgreSQL의 별도 platform/ai DB에서 upgrade head 후 수행했다. 전용 env는 /tmp/colab-task23-schema.env(0600)다. FE 후속 검증이 끝나면 docker rm -f colab_task23_schema_2901792로 정리할 수 있다.

## 남은 검증

계획의 정각 만료/잠금 대기 중 만료, 현재 lab 변경, 다운로드 티켓 발급401, commit 응답 유실 및 변경-vs-종료 경합의 전용 장애 주입 시험은 이번 서버 레인에 추가하지 않았다. Task7 통합 증명 전까지 해당 체크박스는 열어 뒀다. stage DB와 컨테이너는 건드리지 않았다.
