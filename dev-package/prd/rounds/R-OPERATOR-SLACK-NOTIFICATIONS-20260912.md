> spec: dev-package/prd/specs/S-OPERATOR-SLACK-NOTIFICATIONS-20260912.md
# 운영자 Slack 알림 Implementation Plan

> **For agentic workers:** AGENTS.md·dual-agent.md의 위임/격리 규칙을 적용한다. 구현은 한 번에 `lane-worker` 1개, 부모가 결과를 검토한다. 이 문서는 실행 뷰이며 설계 판단은 위 spec이 우선한다.

**Goal:** 개발 상태와 사용자 활동을 Slack 두 채널에 정확히 전달하고, 실패·누락·중복을 구분한다.
**Architecture:** 도메인 원장/내보내기 → 영속 사건 → 집계/전송을 분리한다. 개발 상태는 기존 실행기에서, 사용자 보고는 독립 운영 job에서 만들고 AWS 전달기는 앱/DB 밖에서 실행한다.
**Tech Stack:** Python 3.12, PostgreSQL 16, 기존 FastAPI/SQLAlchemy/Alembic, 표준 라이브러리 unittest·기존 pytest, EventBridge/SQS/Lambda/DynamoDB/관리 비밀, Slack incoming webhook.
**Spec:** `dev-package/prd/specs/S-OPERATOR-SLACK-NOTIFICATIONS-20260912.md` · intent 승인/시험 경계 확인 2026-09-12.
**현재 상태:** 로컬 구현 반영 · 최종 검증은 `dev-package/reports/operator-slack-notifications/implementation/gate-summary.json` 참조. 실제 연결 미실행. 아래 원래 시험 지시는 유지하며 완료 증거는 단계 표와 결과 보고서로 추적한다.

## Global Constraints
- 개발/사용자 활동 채널 분리. 08:00 Asia/Seoul, 전날 [00:00,00:00), 무활동 보고, 실제 사용 dev 전 연구실·명시 시험 제외.
- 일반은 사용자별 요약, 삭제·권한 변경·접근 승인/거절은 행위자·시각·대상·변경 내용 상세. 프로젝트는 생성/삭제만.
- 5분 probe·연속 2회 실패·활성 이후 첫 성공 복구·15분 heartbeat 누락. 메시지 3,000자 이하·채널당 초당 1건 이하.
- 명확한 일시 실패: 1/5/15/60분 이후 60분 재시도, 429 Retry-After 우선. 중요 uncertain은 중복 표시 재전송, 일반 uncertain은 확인/명시 재개.
- NOBYPASSRLS 보고/내보내기 role 분리. 도메인 소유 Port·lab scope 유지. backup role·정적 AWS 키·NAT·앱 background scheduler 금지.
- 기존 사용자용 API·pipeline 계약·Stop 완료 Slack 유지. 생성물 수동 수정·운영 데이터 삭제·HOLD 해제·재배포·외부 전송·커밋·push는 이 계획 작성의 실행 권한이 아니다.
- 실행 시 `colab-v2-work`, 단계에 맞는 TDD/검증 스킬, core 변경 전 s3-upload, infra 변경 전 deploy 규칙을 읽는다. guard-edit는 각 파일 수정 전에 실행한다.
- 테스트는 격리 DB/가짜 AWS transport/loopback Slack만 사용한다. 대상 부재=78, 불일치=1, 전건 일치=0. 로컬 통과를 AWS/Slack 실제 연결 완료로 표시하지 않는다.

## 의존·작업 사본·실행 상태
| 단계 | 선행 | 독립적으로 수용할 결과 | 상태 |
|---|---|---|---|
| 1 | 없음 | 영속 전송·두 채널·실패 복구 계약 | 구현·개별 검증 |
| 2 | 1 계약 | 실제 업무 사건·snapshot·도메인별 pending/권한 | 구현 반영 · 최종 gate 대조 |
| 3 | 1,2 | 늦은 commit 포함 내보내기·08시 일일 보고 | 구현 반영 · 최종 gate 대조 |
| 4 | 1 | 배포 결과·dev/st probe·영속 producer | 구현 반영 · 최종 gate 대조 |
| 5 | 1,3,4 | AWS 수집/전송/IAM/스케줄 구성과 배포 번들 | 구현 반영 · 최종 gate 대조 |
| 6 | 1~5 | 실제 진입점부터 가짜 Slack까지 통합 검증 | 구현 반영 · 최종 gate 대조 |
| 7 | 6 | 연결에 필요한 고정 입력·변경/원복 패킷 | 구현 반영 · 최종 gate 대조 |
- 기본 순서는 1→2→3→4→5→6→7, 병렬 쓰기 없음. 하위 단계 완료를 전체 완료로 보고하지 않는다.
- 구현 사본 생성 전 HEAD·tracked/untracked 목록·내용 hash를 보존한다. 현재 사본의 미커밋 배포 실행기/테스트/진입점도 의존 코드다. HEAD만 복제해 누락시키지 않는다.
- 격리 사본에 필요한 승인된 로컬 의존 파일을 manifest로 복사하고 hash를 대조한다: `scripts/deploy_release.py`, `scripts/slack_completion.py`, 두 파일의 `scripts/tests/test_*.py`, `infra/releases/`, ST 진입점/파이프라인, `services/core-api/ops/deploy_web.py`. 외부 비밀·런타임 상태는 복사하지 않는다.
- 같은 원본 파일을 다른 작업이 수정하면 덮어쓰지 않고 차이를 반영한다. 최초 사본의 전체 dirty 변경을 stash/reset/clean하지 않는다. 구현 시작 시 대장에 이 라운드와 단계 상태를 연결하고 원장 번호는 임의 발급하지 않는다.
- 각 단계에서 실패 시험→최소 구현→해당 시험/게이트→검토→상태 갱신. 자동 커밋 단계는 두지 않으며 승인 없는 커밋으로 인계를 대신하지 않는다.

## 공통 인터페이스와 시험 규약
- 새 운영 라이브러리는 `infra/notifications/` Python package다. 앱 도메인이 이를 import하지 않는다. core 운영 CLI는 버전 있는 JSONL spool/receipt 파일로 연결하며 파일은 0600, 디렉터리는 0700이다.
- 사건 JSON의 필수 키: `schema,event_id,source,environment,occurred_at,received_at,severity,channel,payload`; `schema=colab.operator-event/1`, channel=`development|activity`, environment=`dev|staging`. 엔티티 ID는 기존 common ID 정의를 재사용한다.
- payload는 사건별 allowlist다. 감사에는 `lab_id,actor_id,target_id,action,before,after,source_id`; report part에는 `report_id,revision,part,total,text`. 원시 요청·비밀·임의 webhook은 금지한다.
- 신규 `scripts/tests/operator_notifications_support.py`의 `run_case(name: str) -> dict`는 단계별 fixture registry다. 가짜 HTTP/시계/transport만 제공하고 production CLI/worker/renderer를 실제 호출한다. 동작 자체를 fixture에 복제하지 않는다. 케이스 이름과 기대값은 아래 시험에 고정한다.
- DB 케이스는 신규 `services/core-api/tests/operator_support.py`의 `operator_case(name, live_client, p2_client, session_factory, sql) -> dict`를 사용한다. 기존 `tests/conftest.py` fixture와 테스트 전용 인증 패턴을 재사용하고 요청→commit→운영 CLI를 실행한다.
- 아래 표준 unittest는 `python3 -m unittest <모듈> -v`로, DB pytest는 기존 `service-tests-core-api` 게이트가 로드한 시험 환경에서 실행한다. 준비 실패를 의존 도구 설치나 fixture 부재의 GREEN으로 바꾸지 않는다.

### Task 1: 영속 전송 경계와 두 채널
**Files — create:** `contracts/operator-notifications/event.schema.json`, `infra/__init__.py`, `infra/notifications/__init__.py`, `infra/notifications/manifest.schema.json`, `infra/notifications/events.py`, `infra/notifications/delivery.py`, `infra/notifications/spool.py`, `infra/notifications/cli.py`, `scripts/tests/operator_notifications_support.py`, `scripts/tests/test_operator_delivery.py`.
**Files — modify:** `gates/config/db-boundaries.toml`에 새 알림 unit `dir=infra/notifications, chains=[]`를 등록한다. 기존 unit의 허용 DB는 바꾸지 않는다.
**Interfaces:** `events.validate(record: dict) -> dict`, `events.render(record:dict)->str`; `spool.append(directory: Path, record: dict) -> str`; `delivery.process(event_id: str, store, sender, now: datetime) -> str`; `cli.main(argv: list[str]) -> int`. sender는 `(channel:str,text:str)->tuple[int,str,int]`로 HTTP status/body/Retry-After 초를 반환하고 전송 결과 불명확은 별도 예외로 구분한다.
**Store contract:** `put(record)->bool`(동일 ID/내용 중복 false, 다른 내용 충돌); `claim(id,now)->dict|None`; `finish(id,state,next_at,reason)->None`; `due(now)->list[str]`; `resolve(id,action,actor,now)->None`. 채널 lease도 claim에 포함하고 sent 불변/본문 hash를 검사한다. 테스트 store는 파일/SQLite 영속 상태로 재시작까지 검사한다.
- [ ] RED: `test_operator_delivery.py`에 다음과 HTTP200/body불일치·429·5xx·영구거절·경쟁·일반 uncertain 확인/재개 케이스를 작성한다.
```python
import unittest
class DeliveryTests(unittest.TestCase):
    def test_restart_keeps_important_uncertain_and_channel(self):
        from scripts.tests.operator_notifications_support import run_case
        r = run_case("important_timeout_then_restart")
        self.assertEqual(r["activity_posts"], [])
        self.assertEqual(r["development_posts"][1]["event_id"], r["development_posts"][0]["event_id"])
        self.assertIn("중복 가능", r["development_posts"][1]["text"])
        self.assertEqual(r["deployment_runs"], 0)
```
- [ ] RED 실행: `python3 -m unittest scripts.tests.test_operator_delivery -v`; 위 TestCase가 실제 수집됐는지 확인하고, 실패 이유를 채널/전송 동작의 미구현으로 남긴다.
- [ ] 구현: append는 exclusive 임시 파일→flush/fsync→atomic replace→디렉터리 fsync. process는 영속 claim 후 HTTP 호출하고 아래 판정표를 적용한다. 전송 완료와 업무 완료를 합치지 않는다.
```python
from datetime import timedelta
retry_minutes = (1, 5, 15, 60)
delay = retry_minutes[min(attempt - 1, 3)] * 60
next_at = now + timedelta(seconds=max(delay, retry_after_seconds))
state = "sent" if status == 200 and body == "ok" else "retry_wait"
```
- [ ] 중요/일반 uncertain·영구오류 held는 위 HTTP 응답 경로 전에 별도 분기한다. resolve는 `confirmed-sent|retry`만 받고 actor/시각을 남긴다. 상태 알림의 자기 실패로 무한 재귀 사건을 만들지 않는다.
- [ ] manifest 계약을 먼저 고정한다: env/usage, 시험 ID·적용시각·coverage 시작, owner sources, probe별 argv/timeout, AWS account/region/resource 매핑, 두 채널의 서로 다른 secret 참조. `validate --profile local|connected`에서 모드를 명시하며, connected 필수 입력 부재는78. 로컬 검증에는 가짜 수신처만 허용한다.
- [ ] GREEN: 같은 unittest 재실행. 합격=재시작/경쟁에도 성공 ID 중복0·중요 불명확 표시·429 대기·잘못된 채널 거부·비밀 노출0. CLI `validate/ingest/publish-pending/status/resolve`를 이 단계에서 공개한다.

### Task 2: 소유 도메인의 감사 snapshot·내보내기 대기
**Files — create:** `db/platform/versions/0025_operator_audit.py`, `db/platform/tests/0025-operator-audit-drift.sh`, `services/core-api/src/colab_core/ports/operator_audit.py`, `services/core-api/src/colab_core/domains/d3_audit.py`, `services/core-api/src/colab_core/domains/d6_audit.py`, `services/core-api/tests/operator_support.py`, `services/core-api/tests/test_operator_audit.py`.
**Files — modify:** `db/platform/schema.sql`, `gates/config/migration-drift.toml`, `gates/config/importlinter.ini`, `gates/config/boundaries.toml`; `services/core-api/src/colab_core/` 아래 `domains/d2_access.py`, `domains/d5_ingestion.py`, `domains/d8_insight.py`, `app/routes/catalog.py`, `app/routes/ingestion.py`, `app/routes/project.py`; 별도 `services/core-api/ops/purge_datasets.py`. 새 모듈은 소유 도메인의 경계 검사에 먼저 등록한다.
**Interfaces:** `AuditExportPort.pending(session,limit:int)->list[dict]`, `AuditExportPort.ack(session,source_id:str,receipt_hash:str)->None`; 소유 모듈의 `append_snapshot(session, *, actor_id, target_id, action, before, after, occurred_at)->str`. D1에는 업무 감사표를 만들지 않는다.
- [ ] head 재확인. 현재 `0024_s2_grid_convenience`→`0023_upv_image_grid`, 0025는 비어 있다. 달라졌으면 이 단계의 번호를 갱신한 뒤 단일 자식 revision을 만든다.
- [ ] RED: 아래 시험과 권한 여러 스위치/rollback/삭제 후/role 거부를 `test_operator_audit.py`에 추가한다.
```python
def test_original_approval_survives_grant_change(live_client, p2_client, session_factory, sql):
    from operator_support import operator_case
    r = operator_case("approve_then_change_expiry", live_client, p2_client, session_factory, sql)
    assert r["first_snapshot"]["after"] == r["reexported_snapshot"]["after"]
    assert r["reporter_write_denied"] and r["cross_lab_read_denied"]
```
- [ ] RED 실행: core test env에서 `.venv/bin/python -m pytest tests/test_operator_audit.py -q` (cwd=`services/core-api`).
- [ ] 구현: D2 `apply_switch/create_access_request/decide_access_request`에 당시 snapshot, D3 `update_dataset`/기존 file-grid 변경 helper/승인된 purge, D6 `delete_project`, D5 `UploadLedgerAdapter.accept/mark_registered`, D8 `record_activity/record_download`에 같은 트랜잭션 기록을 연결한다.
```python
# 각 소유 도메인의 업무 transaction 안에서만 실행하며 네트워크 호출은 없다.
source_id = append_snapshot(session, actor_id=actor_id, target_id=target_id,
    action=action, before=before, after=after, occurred_at=occurred_at)
# append_snapshot은 같은 transaction에서 소유 도메인의 export_pending 행도 만든다.
```
- [ ] 표: `d2_operator_audit`(결정 snapshot), `d3_operator_audit`(변경/삭제), `d6_operator_audit`(생성/삭제 snapshot); `d2/d3/d5/d6/d8_operator_export`는 소유 도메인별 payload/receipt 상태. 감사표는 append-only, export표는 ack 열만 갱신 가능. 모든 표 lab RLS, 삭제 cascade 없음, source ID 유일, pending index.
- [ ] `colab_reporter`는 한정 SELECT만, `colab_audit_exporter`는 같은 SELECT+export표 ack 열 UPDATE만, 둘 다 NOBYPASSRLS. PUBLIC grant 없음. 기존 app role에는 자신이 소유한 업무/감사 INSERT만 추가한다. 새 role의 불필요한 표 읽기가 거부되는지 검사한다.
- [ ] GREEN: 위 pytest, `service-tests-core-api`, `migration-single-head`, `migration-drift`, `schema-diff`, `rls-coverage`, `rls-effect`, `import-boundary`. 운영 purge는 고정된 격리 fixture로만 검증한다.

### Task 3: 내보내기와 오전 8시 일일 보고
**Files — create:** `services/core-api/ops/operator_audit_export.py`, `services/core-api/tests/test_operator_export.py`, `infra/notifications/archive.py`, `infra/notifications/digest.py`, `infra/notifications/jobs.py`, `scripts/tests/test_operator_digest.py`.
**Files — modify:** Task 2의 소유 모듈 `d2_access.py/d3_audit.py/d5_ingestion.py/d6_audit.py/d8_insight.py`의 `AuditExportPort` 구현, `services/core-api/src/colab_core/domains/d1_identity.py`, `infra/notifications/cli.py`.
**Interfaces:** core CLI `export --manifest --output` / `ack --receipt-file`; `archive.accept(record:dict)->dict`는 source ID/내용 hash/접수 receipt를 반환하고 dirty-date도 원자적으로 저장. `digest.build(date:str,manifest:dict,archive)->list[dict]`; `jobs.run(now:datetime,manifest:dict,archive)->list[str]`는 미보고/dirty 날짜를 오래된 순서로 처리.
- [ ] RED: 실제 API에서 commit한 2개 연구실+시험 연구실 export, 오래된 발생시각의 지연 commit, ack 직전 중단을 core tests에, 날짜 경계/부분 실패/분할을 digest tests에 추가한다.
```python
import unittest
class DigestTests(unittest.TestCase):
    def test_late_commit_corrects_the_original_day(self):
        from scripts.tests.operator_notifications_support import run_case
        r = run_case("report_then_old_timestamp_commit")
        self.assertEqual(r["report_dates"], ["2026-09-11", "2026-09-11"])
        self.assertEqual(r["revisions"], [1, 2])
        self.assertIn("정정 보고", r["messages"][-1]["text"])
```
- [ ] RED 실행: core `.venv/bin/python -m pytest tests/test_operator_export.py -q`; root `python3 -m unittest scripts.tests.test_operator_digest -v`.
- [ ] 구현: D1 lab 목록→각 lab 새 transaction/SET LOCAL→owner pending 전체 page→0600 spool→remote accept→receipt hash 확인→exporter role로 ack. 원격 미접수 상태에서 ack하지 않는다. 발생시각 cursor 때문에 pending을 버리지 않는다.
```python
from datetime import timedelta, timezone
from zoneinfo import ZoneInfo
local_now = now.astimezone(ZoneInfo("Asia/Seoul"))
end = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
start = end - timedelta(days=1)
window = (start.astimezone(timezone.utc), end.astimezone(timezone.utc))
```
- [ ] 원천 우선순위: D2 권한/결정 snapshot, D3 변경 audit, D6 project snapshot이 정본이며 D8의 같은 operation ID는 보조. D5 접수와 D8 등록은 upload ID로 연결한다. 같은 사용자/초 단위 시간만으로 dedup하지 않는다.
- [ ] manifest의 live/rehearsal, 시험 lab/account ID와 적용 시작, 전체 source, coverage 시작을 필수로 선언. 0건/0연구실/부분/전체 실패를 구분한다. immutable revision/part hash, mention escape, 3,000자 분할, 마지막 part 이전 complete 금지를 구현한다.
- [ ] GREEN: core export tests와 digest unittest. 8시 전 미실행, 8시 이후 1회, 누락일 catch-up, 추가/삭제 대상, 전체 page, 48시간을 넘긴 지연 commit의 원래 날짜 정정, 첫날 partial, 중간 part 재개를 포함한다.

### Task 4: 배포·dev/st 상태 사건 연결
**Files — modify:** `scripts/deploy_release.py`, `scripts/tests/test_deploy_release.py`, `infra/staging/deploy.sh`, `infra/staging/pipeline/run-pipeline.sh`, `infra/staging/pipeline/watch.sh`, `services/core-api/ops/deploy_web.py`; `infra/ops/alarm_runner.py`, `infra/ops/run-scheduled.sh`, `infra/ops/install-schedule.sh`, `infra/ops/alarms.toml`, `infra/ops/probes/service-health.sh`, `infra/ops/probes/deploy-verification.sh`, `infra/ops/probes/backup-freshness.sh`, `infra/ops/probes/backup-freshness.py`, `infra/ops/build-source-bundle.sh`.
**Files — create:** `infra/notifications/producers.py`, `scripts/tests/test_operator_producers.py`.
**Interfaces:** `producers.release_result(release_id,env,phase,exit_code,version,at)->dict`; `producers.observe(state:dict,passed:bool,env:str,target:str,at:datetime)->tuple[dict,list[dict]]`; Task 1 manifest를 소비한다. 기존 입력 dv/st만 정규 env dev/staging으로 변환하고 미지 값은 거부한다.
- [ ] RED: 기존 ‘실패 시 전송 0’은 ‘성공 통지 0/실패 사건 1’로 변경하고 성공의 이중 전송 방지 시험을 추가한다. 잠금/ID 충돌/자식 process 상속 시험을 삭제하지 않는다.
```python
import unittest
class ProducerTests(unittest.TestCase):
    def test_retry_does_not_deploy_again(self):
        from scripts.tests.operator_notifications_support import run_case
        r = run_case("st_verification_failed_then_delivery_retry")
        self.assertEqual(r["deploy_count"], 1)
        self.assertEqual(r["success_messages"], [])
        self.assertEqual(r["failure_event_ids"], [r["expected_id"]])
```
- [ ] RED 실행: `python3 -m unittest scripts.tests.test_deploy_release scripts.tests.test_operator_producers -v`.
- [ ] 구현: 환경별 terminal 결과를 state에 먼저 저장→spool에 idempotent append. 새 경로가 설정된 대상에는 legacy sender를 호출하지 않는다. 기존 sent receipt를 재전송하지 않는다. `--retry-notification`은 알림만 재개하며 deploy/verify를 다시 실행하지 않는다.
```python
for target in terminal_targets:
    record = release_result(release_id, target["env"], target["phase"], target["exit_code"], target["version"], at)
    spool.append(spool_directory, record)
```
- [ ] dev에 고정된 endpoint/port/image/backup oracle을 환경 manifest로 옮긴다. st를 dev로 fallback하지 않는다. 미선언 target=78. observe의 incident 번호·active 상태·pending 사건을 같은 atomic state 저장에 포함해 전송 실패 후 재시작에도 전이를 잃지 않는다.
- [ ] GREEN: 위 unittest, `agent-bridge`, `ops-observability`, `ops-observability-selftest`. dev/st 각각 실패→복구→재발, 최초 OK의 복구 통지 없음, heartbeat, bundle의 새 library 포함을 검사한다.

### Task 5: AWS 전달 구성과 스케줄의 로컬 검증
**Files — create:** `infra/notifications/aws_store.py`, `infra/notifications/aws_events.py`, `infra/notifications/handlers.py`, `infra/notifications/build_bundle.py`, `infra/notifications/template.yaml`, `infra/notifications/install_jobs.py`, `infra/notifications/requirements.in`, `infra/notifications/requirements.txt`, `scripts/tests/test_operator_aws.py`, `scripts/tests/test_operator_schedule.py`.
**Interfaces:** `aws_store`는 Task 1 store+Task 3 archive 계약을 DynamoDB로 구현; `aws_events.normalize(raw:dict,manifest:dict)->list[dict]`; `handlers.ingest(event,context)->dict`, `handlers.retry(event,context)->dict`; `install_jobs.main(argv)->int`는 `--check/--render`와 명시적 `--apply`를 구분한다.
- [ ] RED: AWS 사건 fixture/SDK stub으로 Health issue/closed/page 중복·CloudWatch 상태·queue ARN 위조·Dynamo 조건 경쟁·partial batch를 검사한다. stub 통과를 실제 AWS 검증으로 표시하지 않는다.
```python
import unittest
class AwsTests(unittest.TestCase):
    def test_cloud_event_survives_application_shutdown(self):
        from scripts.tests.operator_notifications_support import run_case
        r = run_case("aws_issue_without_core_or_database")
        self.assertEqual((r["development_count"], r["activity_count"]), (1, 0))
        self.assertEqual(r["database_connections"], 0)
```
- [ ] RED 실행: `python3 -m unittest scripts.tests.test_operator_aws scripts.tests.test_operator_schedule -v`.
- [ ] 구현: CloudFormation에 2개 queue+DLQ, DynamoDB, 비VPC Lambda, 1분 retry schedule, Health 사용 region/us-east-1 규칙, CloudWatch 상태/heartbeat, 채널별 secret 참조, 최소 IAM을 정의한다. SDK 의존성은 알림 bundle에만 고정하고 core에 추가하지 않는다.
```python
# Archive 저장은 하나의 DynamoDB transaction: event와 dirty 날짜를 동시에 기록한다.
request = {"TransactItems": [event_put, dirty_day_update]}
dynamodb.transact_write_items(**request)
```
- [ ] Lambda timeout=30초, queue visibility≥180초, partial batch response, 미전송 due 재발행을 선언한다. queue TTL/DLQ 이동으로 영속 event를 지우지 않는다. queue 접수만으로 source를 ack하지 않고 원격 영속 receipt를 대조한다.
- [ ] cron은 기존 job과 별도 이름으로 render: probe 5분, export/retry 기동 1분, daily 08:00 Asia/Seoul. 설치하지 않고 앱 중단 중 AWS 경로, 잘못된 manifest, 시험 제외 미선언, 같은 채널 secret 거부, secret 미출력을 검사한다.
- [ ] GREEN: 두 unittest, 로컬 template 구조/IAM 음성 검사, package import smoke. source bundle의 handler·의존성 hash 포함과 core/DB credentials 제외를 확인한다. AWS 자원 생성 0.

### Task 6: 합의한 외부 동작을 게이트로 검증
**Files — create:** `gates/tools/operator-notifications.sh`, `gates/tools/operator-notifications-selftest.sh`, `gates/config/operator-notifications.toml`, `services/core-api/tests/test_operator_notifications_e2e.py`, `scripts/tests/test_operator_notifications_gate.py`.
**Files — modify:** `gates/run.sh`, `gates/README.md`, `gates/config/parallelism.toml`, `gates/config/artifact-ownership.toml`, `gates/config/db-boundaries.toml`, `gates/config/importlinter.ini`, `gates/config/boundaries.toml` (새 알림 unit은 chains=[], core exporter는 platform만, 신규 소유 모듈을 경계 검사에 포함하고 기존 허용 경계를 넓히지 않는다).
**Interfaces:** `operator-notifications`는 case manifest 전건, `operator-notifications-selftest`는 고장 낸 manifest/fixture/route를 판정한다. 기존 `run.sh`의 report schema/exit 0·1·78을 사용한다.
- [ ] RED: 실제 TestClient/격리 DB→core export CLI→archive→08시 job→loopback HTTP server 두 개까지 통과시킨다. SDK stub은 AWS 경계에만 둔다. HTTP 수신 건수/본문/순서를 기대표와 대조한다.
```python
def test_two_real_labs_reach_only_activity_channel(live_client, p2_client, session_factory, sql):
    from operator_support import operator_case
    r = operator_case("two_labs_audit_to_http", live_client, p2_client, session_factory, sql)
    assert r["reported_lab_ids"] == r["expected_live_lab_ids"]
    assert r["test_actor_occurrences"] == 0 and r["development_audit_posts"] == 0
    assert r["received_part_ids"] == r["expected_part_ids"]
```
- [ ] 구현: manifest는 spec 시험표 20행을 개별 case로 풀어 필수 env/source/lab/기대 건수를 선언한다. case 부재/DB 부재/수신처 부재는78, 거짓 무활동/잘못된 채널은1. 전건 선언을 줄여 GREEN으로 만들지 않는다.
```python
ready = bool(cases) and required_cases <= executed_cases
exit_code = 78 if not ready else (1 if failures else 0)
```
- [ ] GREEN: 신규 gate 두 개, `service-tests-core-api`, `agent-bridge`, `ops-observability`, `ops-observability-selftest`, spec의 schema/경계/계약 gate 전체를 직렬 실행한다. 준비 실패는 준비 실패로 보고한다.
- [ ] `COLAB_GATE_REPORT_DIR=dev-package/reports/operator-slack-notifications/integration`을 명시하고 task ID/tree/hash/실행 case와 검증 결과를 대조한다. 기존 미커밋 변경을 이유로 범위를 줄이지 않는다.
- [ ] intent proposed outcome 7항의 로컬 대응을 열거한다. 실제 AWS/Slack 접수는 Task 7에서 별도 상태로 두며 intent 전체 완료로 선언하지 않는다.

### Task 7: 실제 연결에 필요한 자료 준비
**Files — create:** `infra/notifications/README.md`, `docs/development/operator-notifications.md`, `dev-package/reports/operator-slack-notifications/connection-readiness.md`.
**Files — modify:** `infra/releases/README.md`, `infra/ops/README.md`, `dev-package/work-items.yaml`, `dev-package/03-HANDOFF.md` (5행 이내, 기존 항목을 교체하지 않는다).
- [ ] `cli validate`와 `install_jobs --render` 결과, bundle hash, template 차이, 필요 IAM/region/resource/env, 두 채널, 시험 ID, 시작시각, 원복 순서를 문서화한다. 비밀값은 기록하지 않고 실제 입력 부재는 항목명으로 표시한다.
- [ ] 운영 절차에 pending/uncertain/held 확인, ID 지정 resolve, 지연 날짜 재집계, secret 변경 후 재개, 구 sender 중지/신 sender 활성화 순서를 적는다.
- [ ] 최종 확인: 로컬 검증 범위/미실행 연결 범위/필요 사용자 입력을 구분한다. 연결 입력이 없어도 1~6의 독립 작업은 계속한다.
- [ ] 실제 AWS 변경·Slack 전송 전 대상과 원복 방법을 고정하고 현재 대화의 승인 범위를 대조한다. 이 계획 ‘작성’ 확인만으로 실행하지 않는다. 기존 자동배포 HOLD는 별도 해제 조건이 충족될 때까지 유지한다.

## 사양 대응과 현재 검증
| spec의 외부 결과 | 담당 task | 증거 |
|---|---|---|
| 개발 결과/이상/복구/AWS/반복 억제 | 1,4,5,6 | producer/SDK 경계/HTTP 수신 시험 |
| 두 채널, 비밀·연구실 경계 | 1,2,5,6 | 오배송/권한/비밀 음성 시험 |
| 08시/전날/전체 연구실/시험 제외/무활동 | 2,3,6 | API→DB→job→HTTP |
| 누가 언제 무엇을 어떻게 변경했는지, 삭제 후 snapshot | 2,3,6 | 현재 상태 변경 후에도 당시 감사 유지 |
| 부분 실패/지연 commit/정정/재시작/중복 | 1,2,3,5,6 | pending/receipt/hash/HTTP 건수 |
| 실제 환경·채널 연결 | 7의 자료 이후 별도 실행 | 현재 미실행, 로컬 GREEN과 구분 |
- 계획의 기존/신규 파일 구분·함수명·spec 대응·300행 이하를 확인한다. 본문의 시험 코드는 구현 시 시험 지시이며 이번에 실행한 시험이 아니다.

## 구현 후 수용 기록

- 실제 API→PostgreSQL→전용 exporter role→Dynamo SDK 경계→일일 보고→두 loopback HTTP 수신처 검증을 추가했다.
- 기존 단계별 체크박스는 원래 계획을 보존한다. 실행된 시험 ID와 필수 20개 시나리오는 gate case evidence에서 대조한다. 실제 실행 없는 항목을 체크박스 수로 통과 처리하지 않는다.
- 별도 원격 연결을 제외한 구현과 로컬 자료는 `reports/operator-slack-notifications/implementation/result.md`에 대응한다.
- SDK는 독립 운영 실행 환경/전달 bundle에서 사용한다. core 앱 도메인·앱 의존성에는 추가하지 않는다.

## 실제 연결 통합
최신 main의 이미 배포된 0025_stage3_accounts와 0026_login_sessions를 보존하고, 아직 배포하지 않은 감사 migration을 0027_operator_audit로 이동한다. 기존 로컬 검증 증거는 당시 0025 기준이며 새 후보의 검증을 다시 수행한다.
