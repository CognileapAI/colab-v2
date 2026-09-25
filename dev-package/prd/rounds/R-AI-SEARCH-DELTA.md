> spec: dev-package/prd/specs/AI-SEARCH-DELTA.md
# AI 검색 변경 기록 실행 계획

**Goal:** 원본 변경을 누락 없이 병합 기록하고 재시도 가능한 처리 버전을 제공한다.
**Architecture:** D3 트랜잭션 트리거 + 연구실별 변경 원장 + lease/fencing 소비 인터페이스.
**Tech Stack:** PostgreSQL, Alembic, SQLAlchemy, pytest.
**실행:** 현재 세션에서 직접 구현, 독립 검토자는 읽기 전용 검토.

## 작업 1 — 변경 기록과 처리 계약

- [x] 승인 범위와 전체 5단계·출구를 spec에 기록.
- [x] `services/core-api/tests/test_search_changes.py`에서 등록 후 변경 기록 RED 확인.
- [x] `db/platform/versions/0033_search_changes.py`와 `db/platform/schema.sql`: 원장·트리거·RLS.
- [x] `services/core-api/src/colab_core/domains/d3_search_changes.py`: claim/ack/fail/renew/bootstrap.
- [x] 실 DB로 변경·삭제·rollback·동시성·lease·권한·bootstrap 동작 검증.
- [x] 전체 core 회귀 및 schema/RLS/import 게이트.
- [x] 독립 검토, 대장·총괄 재개점·인계 갱신.

## 다음 단계

단계 ① 검증 후 단계 ②의 자료별 KG·출처 계약을 구체화한다.
이번 작업의 완료를 일일 갱신/검색 품질 전체 완료로 표시하지 않는다.

검증 결과와 한계: [단계① 인계](../../sessions/20260913-ai-search-delta.md). 단계① 로컬 완료, 미배포.
