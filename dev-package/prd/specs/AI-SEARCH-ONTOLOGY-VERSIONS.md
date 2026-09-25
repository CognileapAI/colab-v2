# 온톨로지 내용 버전과 해석 의존 계약

출처: [AI 검색 intent](../../intent/2026-09-12-ai-search.md), [사실 기반](AI-SEARCH-FACTS.md).
사용자 2026-09-13 “다음작업”에 따라 단계②의 다음 단위인 내용 버전·의존 연결을 구현한다.

## 수용 기준

- D9 기존 5표를 한 SELECT의 일관된 스냅샷으로 읽는다. D9 쓰기·새 표·권한 변경은 없다.
- manifest v1은 protocol, entries, version으로 구성한다. entries는 discovery 및 concept:<안정ID>의 SHA256이다.
  version은 protocol/entries의 정렬된 UTF-8 JSON 내용 해시다. 시각·행 순서가 버전에 영향을 주지 않는다.
- discovery는 사전 3종의 내용과 개념 ID/kind/label 및 matcher 규약 버전을 포함한다.
  개념 digest는 자기 내용·인접 관계·그 끝 노드의 내용을 포함한다. 현재 깊이 1 확장만 지원한다.
- core는 D9 DB에 접속하지 않는다. manifest Port 값만 받아 연구실별 D3 수신 이력/현재 포인터에 저장한다.
  전송 어댑터와 매일 실행은 후속 단위이며 이번에 실제 가동했다고 주장하지 않는다.
- publish(session, manifest, expected_previous)는 이전 포인터가 일치할 때만 교체한다.
  동일 버전 재수신은 멱등. 해시를 시간 순서로 비교하지 않는다. 잘못된 digest/형식은 거부한다.
- bind(session, fact_id, expected_version, concept_ids)는 현재 ready 사실과 현재 manifest에만 의존을 기록한다.
  개념 0건도 discovery 의존으로 기록한다. 사실 테이블의 ontology_snapshot_id NULL은 그대로 유지한다.
  이 기록은 의미 추론 정답/공개 승인이 아니라 후속 해석기의 읽기 의존이다.
- binding에 예상 의존 전체 집합도 함께 보관하여 일부 행 누락/변조를 유효 상태로 취급하지 않는다.
- current_bindings는 현재 원본 권한·버전과 모든 dependency digest가 현재 manifest에 맞는 결과만 반환한다.
  조회도 버전 교체와 연구실별로 직렬화한다. 무관한 개념 변경은 기존 연결을 재사용할 수 있다. 원본·용어 변경 즉시 오래된 연결을 제외한다.
- requeue(limit)는 완료된 변경 포인터 중 해석 의존이 무효화된 자료만 작은 묶음으로 다시 기록한다.
  원문을 읽지 않는다. 같은 변경을 반복 적용하지 않고, 활성 lease는 침범하지 않는다.
  새로운 어휘/별칭은 기존 매칭 유무와 관계없이 모든 해석 대상에 영향을 준다.
- 모든 D3 표에 FORCE RLS와 연구실 경계. source 관련 표는 사실 스냅샷 RLS를 따른다.
  이력은 삭제하지 않는다. 제품 온톨로지 보호·배포 정책 분리·Sonnet 평가 보류를 유지한다.

## 검증 및 다음 단위

실패 테스트부터 시작: 해시 정렬/내용 변경/인접 영향, 잘못된 manifest, 포인터 CAS, 미매칭 기록,
영향/무관 자료 분리, 용어 변경 전체 재판정, 페이지 멱등, 원본·권한·연구실 경계와 rollback.
core/ai 서비스 회귀와 schema/migration/RLS/import 검사. 실제 모델 품질·전송 E2E는 이 검사와 구분한다.
다음 단위: manifest 전송과 제한된 agent 도구 실행, 일일 작업 조율/재시도/실행 상태, 검색 연결.
