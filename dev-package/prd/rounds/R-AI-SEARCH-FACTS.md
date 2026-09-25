> spec: dev-package/prd/specs/AI-SEARCH-FACTS.md
# 자료별 사실·출처 구현 계획

**Goal:** 변경 대장을 소비해 출처·버전이 있는 사실을 보관하고 오래된 결과를 차단한다.
**Architecture:** D3 source reader → 결정적 사실 추출 → lease 검증/원자적 저장 → 현재 원본 대조 조회.
**Tech Stack:** PostgreSQL/Alembic, SQLAlchemy, pytest.
**실행:** 부모 단일 writer, 독립 읽기 전용 reviewer.

- [x] 승인 범위·전체 후속 순서·이번 출구 spec 기록.
- [x] `tests/test_search_facts.py`에 실제 DB RED 작성/확인.
- [x] `0034_search_fact_snapshots.py`, `schema.sql`: 버전별 source snapshot·RLS.
- [x] `domains/d3_search_facts.py`: source read/process/read_current/reconcile 계약 구현.
- [x] 실패·stale·권한·멱등성·추출 버전 재처리 검사.
- [x] core 전체 1257건 통과(skipped 0, E2E 제외 6) 및 migration/schema/RLS/import 검사.
- [x] 독립 수용 검토·대장·총괄 계획·인계 갱신.

검증 보강: 기존 시간 기반 테스트 정리의 누락을 RED로 재현하고 시작 전 PK 비교를 추가했다.
상세 결과와 미구현 범위는 [인계](../../sessions/20260913-ai-search-facts.md)에 기록했다.

완료 후 다음: 단계②의 온톨로지 내용 버전·개념별 의존 연결/agent 도구 계약, 이후 단계③ 일일 갱신 실행.
실제 LLM 의미 추출/평가 및 제품 배포는 이 단계 완료와 구분한다.
