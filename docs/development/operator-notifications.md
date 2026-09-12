# 운영자 Slack 알림 개발·운영 절차

사건 계약은 contracts/operator-notifications/event.schema.json, 환경 계약은 infra/notifications/manifest.schema.json이다. 개발 사건은 development, 일일 활동·감사 보고는 activity 채널로만 전달한다.

배포 계획에 operator_notifications.spool_directory가 있으면 배포 성공·실패·검증 실패를 먼저 0600 spool에 기록한다. 실패 알림 재전송은 배포를 다시 실행하지 않는다. 운영 probe는 첫 실패를 보류하고 연속 두 번째 실패, 활성 상태의 첫 성공 복구, 재발을 새 incident로 기록한다.

업무 감사와 export pending은 같은 DB transaction에서 저장된다. operator_audit_export.py가 각 연구실 scope에서 미접수 원천을 JSONL로 내보내고 원격 receipt를 받은 뒤 해당 source ID만 완료 처리한다. 보고 job은 08:00 KST 이후 누락 날짜를 오래된 순서로 처리하고 늦은 commit은 원래 날짜의 정정 revision으로 보낸다.

로컬 검증은 gates/run.sh operator-notifications와 operator-notifications-selftest다. 실제 Slack·AWS·운영 DB 연결은 포함되지 않는다.

AWS 연결 시 primary stack은 서비스가 실행되는 실제 리전에 배치하고, AWS Health 전역 사건 forwarding stack은 `us-east-1`에 배치한다. manifest에는 현재 환경의 EC2 InstanceId와 관리 경보 `StatusCheckFailed_Instance`, `StatusCheckFailed_System`의 실제 이름을 환경에 매핑해야 readiness가 통과한다.
