# 자료별 사실·출처와 지속 갱신 계약

출처: [AI 검색 intent](../../intent/2026-09-12-ai-search.md), [증분 갱신 사양](AI-SEARCH-DELTA.md).
2026-09-13 사용자 “좋아 그렇게해보자”: 변경 기록 → 매일 증분 갱신 → 주기적 누락 점검 방향 채택.
이번 실행 단위는 단계② 자료별 사실·출처 저장과 stale 차단이다. 단계③ 일일 실행/검증 후 공개,
단계④ 검색 연결, 단계⑤ 실제 Sonnet 추출/평가는 후속이며 기존 LLM 평가 보류는 유지한다.

## 수용 기준

- 자료별 사실을 D3의 `d3_search_fact_snapshot`에 저장한다. 공통 D9 온톨로지는 변경하지 않는다.
- 각 스냅샷은 source kind/ID, dataset/lab, change version, file/evidence revision,
  원본 SHA256, extractor version, 상태, predicate/value/source locator 사실 목록을 가진다.
- ontology snapshot은 아직 구현되지 않았으므로 NULL=미연결. Alembic 버전을 개념 내용 버전으로 사용하지 않는다.
- 원본 메타/파일 메타의 명시된 필드와 reviewed 근거에서 결정적으로 가져온 사실만 ready로 저장한다.
  draft 근거는 candidate다. ready는 후속 검색에 사용 가능한 상태이며 외부 공개 권한이 아니다.
- 실제 원문 의미 추론/새 개념 제안은 향후 agent 도구 연결 범위. 이번에는 임의 모델 출력의 사실 승격을 허용하지 않는다.
- source reader는 metadata/file/evidence 한 건만 읽는다. 파일 경로나 바이트, 전체 자료 원문을 읽지 않는다.
- 완료 처리는 최신 source hash/revision과 요청 버전/lease를 확인한 뒤 결과 저장과 ack를 같은 트랜잭션으로 수행한다.
  실패하면 둘 다 rollback. source 조회는 잠금을 잡지 않고, queue 이후 source write lock을 얻지 않는다.
- 공개용 조회는 최신 change version 및 원본 hash/revision/권한/삭제 여부를 다시 대조한다.
  처리 직후 원본이 바뀌면 이전 사실은 현재 사실로 반환하지 않는다. 후보는 기본 결과에서 제외한다.
- 보이지 않는 본체는 source_unavailable이다. 삭제로 간주해 완료하지 않는다.
  실제 deleted 변경은 source 포인터 기록만 ack하며 사실 이력은 삭제하지 않는다.
- 연구실 RLS와 원본 file 본체 접근 경계를 적용한다. raw 저장소 조회도 비공개 사실을 우회 노출하지 않는다.
- extractor 변경 시 과거 snapshot 포인터를 페이지 단위로 다시 큐에 넣는 reconcile을 제공한다.
  초기 누락은 기존 bootstrap(kind별 ID 페이지)로 처리하며, 변경 없는 완료 자료는 다시 처리하지 않는다.
- 삭제/권한 회수는 일일 갱신을 기다리지 않고 현재 조회에서 제외한다.

## 다음 단계

에이전트는 허용된 source reader로 필요한 자료를 읽고 출처가 있는 후보를 제출한다.
온톨로지 버전/개념별 의존 인덱스를 연결한 뒤 영향받는 자료만 재처리한다.
이번 저장의 semantic ontology 연결을 NULL로 명시하고 일일 agent가 이미 가동된 것으로 보고하지 않는다.

## 검증

일회용 DB: 원본/출처 저장, candidate/ready, 변경/파일 교체/삭제/권한 회수,
이전 worker fence와 원자성, 연구실 차단, 재처리 버전/멱등성, 원문 없는 페이지 재점검.
기존 core 회귀, schema-diff/migration-single-head/rls-coverage/rls-effect/import-boundary.
