> spec: dev-package/prd/specs/AI-SEARCH-CONTINUOUS.md
# 지속 갱신·검색 통합 실행 계획

> **For agentic workers:** 부모 단일 writer, 독립 읽기 전용 advisor. executing-plans로 이 세션에서 계속 실행한다.

**Goal:** 변경된 자료를 온톨로지에 연결하고 매일 갱신하여 검색에서 사용할 수 있는 로컬 개발을 한 흐름으로 완성한다.
**Architecture:** D9 읽기 Port → 제한된 Sonnet 제안 → D3 검증/파생 저장 → scoped 검색. 네트워크 동안 DB 트랜잭션을 유지하지 않는다.
**Tech Stack:** 기존 Python/FastAPI/PostgreSQL/계약 생성기와 테스트 게이트.
**Spec:** 위 출처 문서. 기존 변경 보존, 실제 모델 평가 보류, 배포 미실행.

## 실행 단계

- [x] 1. 개념 내용 조회: core-ai 계약/생성 상수, AI ontology 조회, core ontology Port/client, 버전·해시·상한 RED→GREEN.
- [x] 2. 제한된 모델 실행: AI Sonnet 제안 어댑터/인증 경로, core refresh tools와 제안 검증/파생 연결 저장, 원자성·위조 출력 RED→GREEN.
- [x] 3. 일일 실행: core 갱신 runner/실행 상태/재시도/중복 lease, 신뢰된 주체 설정과 실행 진입점, 변경량 한도와 재시작 RED→GREEN.
- [x] 4. 검색 연결: D3 현재 연결 조회와 catalog 라우트 조립, 기존 순위/권한/한계 설명 유지, 실제 API 회귀와 골든셋.
- [x] 5. 통합 검증: 서비스 전체 회귀, contract-lint/generated-up-to-date/import-boundary/db-boundary/AI 쓰기금지, DDL 변경 시 migration/schema 검사, 독립 수용 검토.
- [x] 6. intent 대조와 기록: 대장→인계/세션, 미실행 모델 평가와 운영 활성화 경계 명시. 실행 가능한 단계를 남긴 채 종료하지 않는다.

## 검증·의존 상태

현재: 로컬 개발 단계 1~6 완료. 전체 회귀·연속 변경 검사와 독립 수용 검토를 기록했다. 실제 모델 품질·운영 활성화 및 과거 간헐 사례의 지속 관측은 운영 전 확인 사항이다. [검증 기록](../../sessions/20260913-ai-search-continuous.md). 단계 1→2→3/4→5→6. 각 단계의 시험 증거를 여기에서 연결한다.
실제 Sonnet 평가 보류는 모델 연결 구현·가짜 전송 기반 실패 시험·나머지 통합 개발을 막지 않는다.
