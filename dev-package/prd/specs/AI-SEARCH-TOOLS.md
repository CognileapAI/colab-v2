# 온톨로지 전송·제한된 갱신 도구

출처: [검색 intent](../../intent/2026-09-12-ai-search.md), [내용 버전](AI-SEARCH-ONTOLOGY-VERSIONS.md).
2026-09-13 사용자 “다음 작업!”에 따라 전송과 실행 도구 연결을 구현한다.

- core-ai GET /ontology-manifest: 서비스 bearer 필수. 미설정 503, 인증 실패 401,
  사전 조회 실패 503. D9 내용은 읽기 전용. 기존 검색 endpoint 인증 정책은 이 작업의 범위 밖.
- 계약에서 wire 상수를 생성하고 양 서비스가 소비한다. core HTTP Port는 timeout/실제 수신 바이트
  16 MiB 상한/redirect 거부/manifest 해시 검증을 적용한다. 토큰·원문 예외는 노출하지 않는다.
- SearchRefreshTools는 신뢰된 조립 코드가 Subject와 session factory/manifest Port를 주입한다.
  agent가 연구실·계정·SQL·파일 경로·임의 manifest를 지정할 수 없다. HTTP 사용자 endpoint는 추가하지 않는다.
- sync_manifest: 네트워크 전 기존 head 확보 → DB 연결을 닫고 fetch → 기존 head CAS로 발행.
- claim: 최대 100개 작업, 인스턴스당 최대 1000개 메모리 핸들, 300초 수명. 핸들은 난수이며
  해당 인스턴스/주체에만 유효하다. 만료 핸들을 정리하고 프로세스 재시작은 기존 lease 재claim으로 복구한다.
- read: 유효 lease와 원본 권한을 확인하고 source hash/revision, 현재 ontology version을 서버에 보관한다.
  반환값에는 원문 파일 bytes/storage key가 없다. 읽지 않은 핸들의 완료는 금지한다.
- complete: 저장했던 read 버전/해시를 다시 대조하고 ontology lock→queue 순서로
  facts.process와 ontology.bind를 한 transaction에 실행한다. 변경/만료/권한 회수/부분 실패는 모두 rollback.
  candidate는 후보 저장/ack만, 삭제 증명된 작업은 tombstone ack만 하며 둘에는 concept_ids를 받지 않는다.
  성공 commit 뒤에만 핸들을 제거한다. concept_ids는 해석 의존 기록이고 의미 사실의 자동 승인 아님.
- 실제 Sonnet/LLM 실행·새 개념 제안·일일 스케줄러·검색 결과 경로·배포는 후속이며 미가동으로 표시한다.

검증: 인증과 HTTP 음성 경로, source/head/권한/lease 변경, 실패시 fact+ack rollback, 늦은 응답 CAS,
행동 기반 집중 검사·전체 core/AI·계약 린트/생성물 최신·도메인 경계. 토큰 설정은 _FILE 규약 유지.
