# 기존 교수 계정의 시스템 관리자 자격 전환

승인 정책은 [관리자 권한 intent](../../dev-package/intent/2026-09-16-admin-full-access.md)다.
교수의 연구실·역할·데이터·비밀번호는 유지하고, 검토한 계정의 `service_operator` 자격만 회수한다.
회수한 계정은 기존 세션이 종료되므로 다시 로그인해야 한다. 유지 계정의 세션은 바뀌지 않는다.
이 문서는 사용자 실행 절차다. 에이전트가 DEV 계정 전환이나 배포를 실행한 기록이 아니다.

## 1. 현재 계정 확인과 dry-run

현재 배포의 계정 관리 화면에서 계정과 실제 운영 담당자를 확인한다. 아래 `list`는 현재 DB의
시스템 관리자 ID·연구실 ID·역할·상태를 읽으며 이메일·비밀번호·연결 문자열은 출력하지 않는다.
과거 계정 수나 ID를 기본 회수 대상으로 사용하지 않는다.

저장소 루트에서 실행한다. `--database-url-file`에는 기존 **account-admin 전용** DB 접속 문자열을
담은 보호된 파일 경로를 넣는다. 접속 문자열 자체를 명령 인자·로그·문서에 적지 않는다.
앱 일반 DB 롤이나 DB 소유자 대신 기존 좁은 계정 관리 롤을 사용한다. 이 도구는 권한을 추가하지 않는다.
서비스의 Python 환경에 현재 작업 코드가 설치되어 있어야 한다.

```bash
services/core-api/.venv/bin/python services/core-api/ops/reconcile_service_operators.py \
  --database-url-file /secure/account-admin-url list
```

출력한 **모든** 시스템 관리자를 `selection.json`의 유지·회수 목록에 정확히 한 번씩 분류한다.
실제 ID로 교체하고 계정마다 사유를 적는다. 실행자 `actorId`는 유지 목록의 활성 시스템 관리자다.
교수 겸직 계정 중 실제 시스템 운영도 맡는 사람은 유지 사유를 명시해 검토한다. 분류가 불분명하면
적용하지 않고 목록부터 확정한다. 이메일·비밀번호를 사유에 적지 않는다.

```json
{
  "actorId": "유지할 실제 시스템 관리자 계정 ID",
  "keep": [{"accountId": "유지할 실제 시스템 관리자 계정 ID", "reason": "시스템 운영 담당"}],
  "revoke": [{"accountId": "전환할 실제 교수 계정 ID", "reason": "소속 연구실 교수 관리자로 전환"}]
}
```

```bash
services/core-api/.venv/bin/python services/core-api/ops/reconcile_service_operators.py \
  --database-url-file /secure/account-admin-url prepare \
  --selection /review/selection.json --output /review/operator-plan.json
```

`prepare`는 DB를 변경하지 않는다. 계획 파일의 계정 ID·연구실·역할·상태, 적용 전후 관리자 목록,
분류 사유를 확인하고 출력된 `planSha256`을 계획 파일과 함께 보관한다. 중복·목록 중첩·미분류·
없는 계정·비교수 회수·마지막 관리자 회수·자기 회수는 거절한다.

## 2. 검토한 목록 적용

**새 전체 권한 서버를 사용자에게 노출하기 전에** 실행한다. 기존 교수 겸직 계정이 전 연구실
전체 권한을 잠시라도 얻지 않도록 권한 회수를 먼저 끝낸다. 계정 분류를 바꿨다면 prepare부터
다시 수행하고 새 계획과 새 SHA256을 검토한다.

```bash
services/core-api/.venv/bin/python services/core-api/ops/reconcile_service_operators.py \
  --database-url-file /secure/account-admin-url apply \
  --plan /review/operator-plan.json --plan-sha256 검토한_64자리_SHA256
```

도구는 기존 관리자 변경 잠금 아래에서 전체 관리자 목록과 소속·역할·상태를 다시 대조한다.
준비 이후 상태가 달라졌으면 모두 거절하고 다시 검토하도록 한다. 회수·자격 버전 증가·세션 종료는
한 트랜잭션이며 실패하면 전체가 롤백된다. 동일 계획이 이미 적용된 경우 `changed: 0`,
`alreadyApplied: true`를 출력하고 세션을 다시 끊지 않는다. 직접 관리자 SQL로 역할·소속을 동시에
수정하는 작업과 병행하지 않는다.

## 3. 데이터 보존 배포와 확인

1. 위 목록 검토와 권한 회수를 완료한다.
2. 기존 배포 절차로 platform 마이그레이션 `0033_admin_body_access`를 적용한다. 데이터 초기화·재적재는 하지 않는다.
3. 미리보기 서비스(viz)를 배포한다.
4. core-api와 프런트를 배포한다. 프런트가 새 대상 연구실 요청을 지원하는 버전인지 확인한다.
5. 실제 DEV 브라우저에서 시스템 관리자의 타 연구실 자료 미리보기·수정·신규 등록 연구실 선택을 확인한다.
6. 전환한 교수의 옛 세션 거절과 재로그인 후 자기 연구실 비공개 자료 관리, 타 연구실·계정 관리 거절을 확인한다.
   기존 데이터·연구실 소속·프로젝트 연결·계보가 유지되는지도 다시 조회한다.

새 코드의 교수 권한이 적용되기 전과 후를 구분해서 확인한다. 권한 회수 후 예전 서버에서는 기존
교수 정책이 적용되며, 새 코드 배포 뒤 자기 연구실 전체 관리가 적용된다. 실패 원인과 실제 변경
계수를 남기고, 실패한 실행을 전환 또는 배포 완료로 기록하지 않는다.
