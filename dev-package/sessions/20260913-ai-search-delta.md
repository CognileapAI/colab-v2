# AI 검색 증분 갱신 — 단계 ① 인계

출처: [사양](../prd/specs/AI-SEARCH-DELTA.md), [실행 계획](../prd/rounds/R-AI-SEARCH-DELTA.md).
**상태: 단계① 로컬 구현·검증 완료 / 미커밋·미배포.**
작업 브랜치 `codex/ai-search-next` (기준 HEAD `90a0df2e`, 시험은 신규 파일을 포함한 작업 사본으로 실행). 배포 정책 브랜치와 분리하며 제품 DB·온톨로지는 변경하지 않았다.

## 구현

- platform `0033_search_changes`: 자료 메타·파일·검색 근거의 최신 변경을 `d3_search_change`에 병합한다.
  7개 원본 테이블의 deferred 트리거가 커밋 직전 기록하므로 원본과 함께 성공하거나 rollback한다.
- 자료/파일 삭제 FK로 대장을 지우지 않는다. 삭제한 파일·근거는 tombstone 포인터를 유지한다.
- 내부 `domains/d3_search_changes.py`: 제한된 batch claim, captured version ack, 실패 backoff,
  lease renew, generation fencing, 명시적 ID 페이지 bootstrap. 별도 HTTP/스케줄러는 없다.
- 타 연구실 큐 접근은 FORCE RLS로 차단한다. bootstrap은 원본 본체 RLS를 유지한다.
  큐의 ID는 원문 접근 권한이 아니며 후속 작업자는 삭제·권한·파일 revision을 다시 확인해야 한다.

## 실패를 재현하고 고친 사항

1. 등록은 201이나 변경 기록이 없음: RED 1 failed / 0 errors.
2. 소비 인터페이스 부재: RED 6 failed / 5 passed. 이후 claim/ack/retry/bootstrap 구현.
3. 요약 수정 → 대장 잠금과 원천 표기 수정 → 자료 잠금의 역전: lock timeout RED.
   대장 트리거를 deferred로 바꿔 원본 쓰기가 끝난 후 잠근다. 임의 다중 자료 DML 전체 무교착 보장은 아니다.
4. bootstrap 첫 NULL cursor의 PostgreSQL 타입 추론 실패: 명시적 text cast로 수정.
5. 행 잠금 대기 중 lease가 만료됐는데 ack/fail/renew가 성공하는 RED 3건:
   먼저 행 잠금을 얻고 별도 SQL에서 만료를 다시 판정한다. 3건 모두 거절되는 GREEN 확인.

6. 전체 회귀 첫 실행은 1241 passed / 1 failed. 기존 변수 미러 시험이 전체 트리거를 3개로 고정했다.
   정확한 트리거 목록을 4개로 확장하고 기존 미러 3개 조건과 새 deferred 조건을 모두 검사한다.
   독립 검토에서 검사 축소가 아닌 계약 확장으로 확인했다. 전체 재실행으로 최종 판정한다.

초기 시험 호출의 selector 누락과 시험 계정 상수 오타는 시험 준비 오류로 수정했다.
이를 기능 RED나 성공 증거로 세지 않는다.

## 검증

- focused: 일회용 PostgreSQL·앱 롤에서 22 passed / skipped 0 / deselected 1226.
  [로그](../reports/ai-search-delta/focused.log).
- migration-single-head: platform/AI 각각 head 1개.
- schema-diff: 빈 일회용 DB 2개에 전체 migration upgrade 후 선언/적용 차이 0.
- rls-coverage: 52표 조사, 기존 allow-list 11표 면제, 신규 표 FORCE RLS.
- rls-effect: 우회 불가 앱 롤로 lab_id 41표 경계와 기존 본체 권한 검증.
- import-boundary: 8개 계약 통과.
- 전체 core-api 회귀: **1242 passed / skipped 0 / deselected 6** (135.56초, exit 0).
  기존 검색 골든 회귀를 포함한 `not e2e` 묶음이다. 원천 마운트가 필요한 E2E 6건은 이번 내부 DB 작업에서 제외.
  [최종 로그](../reports/ai-search-delta/core-final.log), [판정 JSON](../reports/ai-search-delta/core-final/gate-summary.json).
- work-item-consistency: 불일치 0. 기존 파싱 대상 밖 9곳은 검사 성공 근거에 포함하지 않음.
- 독립 정적 검토: 추가 차단 사항 없음. 검토자가 전체 게이트를 재실행했다고 주장하지 않는다.

## intent 대조와 남은 일

- O1 자연어/복합 조건 검색: 이번 변경은 갱신 기반만 제공. 전체 검색 품질 기준은 아직 미충족.
- O2 역할과 추천 이유: 기존 결과 동작 유지. 자료별 KG 연결과 출처 판정은 단계②에 남음.
- O3 정직한 근거·한계: 삭제/버전 추적 기반 추가. 실제 KG 반영·조회 시 최신 권한 재판정은 후속 연결 필요.
- O4 상세 이동: UI 변경 없음. 이번 DB 내부 작업으로 새 사용자 여정을 완료했다고 주장하지 않음.
- O5 보유 레퍼런스/골든셋: 기존 문항 유지. 실제 Sonnet 의미 품질 평가는 보류 상태.
- 사용자 후속 요구에 없는 범위 확대 없음. 단계① 완료를 intent 전체 충족이나 일일 갱신 가동으로 세지 않는다.

## 다음 진입점

단계②에서 자료별 사실·출처·파일 revision·추출 버전·연구실/본문 권한 계약을 정한다.
현재 D9 공통 온톨로지에 비공개 자료 사실을 전역으로 섞지 않는다.
그 뒤 단계③ 일일 증분 실행과 검증 후 공개 버전 전환·캐시, 단계④ 복합 검색,
단계⑤ 의미 검색/Sonnet 평가를 진행한다. 결과 저장에도 fencing을 적용해야 하며 현재 ack만으로 exactly-once는 성립하지 않는다.

bootstrap은 자동 실행하지 않았다. 도입 때 허용된 계정/범위를 지정하여 kind별 ID 페이지를 끝까지 처리한다.
파일 내용·전체 원문 스캔은 필요 없다. 삭제/권한 회수는 일일 주기를 기다리지 않고 원본 권한으로 검색에서 차단해야 한다.
