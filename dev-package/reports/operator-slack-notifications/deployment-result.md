# 운영자 Slack 배포 결과 — 2026-09-12

main 반영, Dev(AWS)·Stage 배포, AWS 전달과 두 Slack 채널 연결을 완료했다. 첫 **2026-09-13 08:00 KST 예약 보고 실행은 아직 미래이므로 미확인**이다. OP-NOTIFY-1은 이 실측 조건만 남겨 open을 유지한다.

## 실제 배포와 연결

- 앱 릴리스: `0a4aecb58e68`. Dev·Stage 모두 이 버전으로 배포·마이그레이션·검증 완료. 후속 `2bd875fc`는 Lambda CodeUri 패키징 수정이며 앱 변경이 아니다.
- Dev 배포 검증 15/15, 실패 0, 생략 0. Stage 배포 검증 15/15, 생략 0 및 체인 2/2. 플랫폼 head `0027_operator_audit`, AI head `0007_merge_vocab_and_category`.
- AWS `colab-notify-dev`(서울), `colab-notify-health`(미국 동부) 활성화. 두 채널 연결 시험과 배포 종결 사건 4개, 총 6개 상태가 `sent`다. 재시도 실측 unresolved 0, pending 0. 최종 두 queue와 두 DLQ 모두 대기·처리 중 0건, 두 stack UPDATE_COMPLETE.
- Dev·Stage 서비스/백업/배포 검증 6개 자동 heartbeat 확인. Dev 실제 활동 수집 complete: 연구실 2, 계정 6, 소스 경로 10. 시험 계정은 명시 제외했다.
- 수집 시작: 9/12 15:55 KST. 매일 08시 KST 전날 보고, 첫날은 부분 기간임을 표시한다. Stage는 일일 사용자 보고를 보내지 않는다.
- Dev EC2는 인스턴스 역할로 필요한 테이블·큐에만 접근한다. Slack 비밀은 Secrets Manager에서 Lambda가 읽으며 저장소에 포함하지 않는다.

## 검증

깨끗한 앱 릴리스에서 관련 게이트 20개와 보고서 출처 검증 20개 통과. 알림 시험 115개 및 필수 시나리오 20개, core-api 시험 1127개 통과(생략 0, 별도 외부 E2E 6개 선택 제외). 패키징 수정 뒤 cfn-lint, 관련 시험 14개 및 operator-notifications/ops-observability 게이트 재검증 통과.

실제 Lambda 3개의 배포 ZIP SHA256은 `493d6d3537fda5e53033a3268fba6360d76fb3928156200ab2a6fd746954b68c`. 패키징→S3 다운로드의 동일 해시와 handlers import를 확인했다. 실제 Ingest→queue→consumer→Slack 전달로 두 채널을 확인했다.

실행 증거는 `/home/ttlhi10/.cache/colab-operator-verification/`의 `actual-release-recovery2.log`, `aws-package/connected-runtime-result.json`, `aws-package/actual-slack-test-results.json`, `aws-package/actual-retry-result.json`, `final-gates/`에 보존했다. 게이트 보고서는 이 보고 디렉터리의 `final-checks/`, `final-schema/`, `package-fix-operator/`, `package-fix-ops/`에 있다. 최종 검토는 에이전트 가용 한도로 역할 원본을 읽고 직접 수행했으며 독립 검토로 주장하지 않는다.

## 해결한 배포 문제와 보존

초기 배포 두 번은 compose 파일 권한과 디스크 부족으로 실패했다. 권한을 바로잡고 과거 이미지 tar 3개를 WSL로 복사·해시 검증 후 해당 원격 사본만 정리해 재배포했다. 두 실패 알림도 정상 전달했다. 제품 데이터·볼륨은 삭제하지 않았다. SAM의 조건부 스케줄과 Globals CodeUri 패키징 문제를 수정하고 실제 AWS 변환·번들·전송으로 검증했다. exporter의 PYTHONPATH 설정도 바로잡아 실제 수집 완료를 확인했다.

배포 전 두 DB 백업과 환경 사본을 보존했다. 기존 미커밋 작업 사본과 별도 Stage 자동배포 HOLD는 유지했다.

## 운영과 남은 확인

두 호스트의 cron은 `/etc/cron.d/colab-operator-notifications`, 설정은 `/etc/colab/operator/runtime.env`, 실행 소스는 `/opt/colab-operator/versions/0a4aecb58e68`다. Dev의 기존 중복 알림 cron은 백업 후 교체했다. Stage relay는 승인된 사건만 Dev로 전달한다.

첫 9/13 08시 보고의 실제 수신·집계 기간·부분 기간 표시를 확인한 뒤 OP-NOTIFY-1을 닫는다. 보고 누락/수집 문제는 15분 지속 시 개발 채널 자체 감시 대상으로 구성돼 있다. 예약이 설치된 사실과 미래 실행 성공을 혼동하지 않는다.

[쉬운 그림 설명](../../../docs/development/operator-notifications-eli5.html)

문서 대장 검사도 불일치 0으로 통과했다(기존 파서 대상 밖 9자리, 항목표 아닌 표 2개는 검사 범위에 포함하지 않음). ELI5는 브라우저 표시와 DOM 클릭의 아침 보고 전환을 확인했다.
