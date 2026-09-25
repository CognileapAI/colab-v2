# 자료별 사실·출처 — 지속 갱신 기반 인계

출처: [사양](../prd/specs/AI-SEARCH-FACTS.md), [실행 계획](../prd/rounds/R-AI-SEARCH-FACTS.md).
브랜치 `codex/ai-search-next`, 기준 HEAD `90a0df2e` + 단계① 미커밋 변경을 보존한 작업 사본.
사용자 “좋아 그렇게해보자”에 따라 지속 갱신의 다음 실행 단위인 사실/출처 저장을 구현했다.

## 이번 구현

- platform `0034_search_fact_snapshots`: 자료별 사실 이력을 D3에 저장. 원본 종류·ID·변경 버전,
  파일/근거 revision·SHA256·추출 방식 버전·근거 위치를 함께 보관한다.
- `domains/d3_search_facts.py`: 단일 원본 읽기, 결정적 사실 추출, 원자적 결과 저장/ack,
  현재 사실 조회, 추출 방식 변경 시 완료 자료의 제한된 묶음 재처리.
- 메타데이터 명시 필드/파일 메타/사람이 확인한 근거에서 가져온 사실은 ready,
  draft 근거는 candidate. ready는 권한 내 검색 사용 가능이며 외부 공개가 아니다.
- ontology_snapshot_id는 NULL(미연결)로 강제한다. 현재 D9에는 의미 있는 공개 버전 체계가 없으며
  Alembic revision을 온톨로지 내용 버전으로 대체하지 않았다.
- 실제 source 일반 조회만 사용한다. 원본 write lock을 queue 뒤에서 얻지 않아 잠금 역전을 피한다.
- 새 결과와 작업 완료는 savepoint 안에서 함께 확정한다. 만료/과거 claim의 결과는 저장하지 않는다.
- raw snapshot RLS도 현재 lab/부모 삭제/queue 버전/파일 권한·revision/근거 revision을 확인한다.
  `read_current`는 추가로 원본 해시와 ready 상태를 재검사한다. 오래된 이력은 지우지 않고 조회에서 제외한다.
- 소유자 외 비공개 source는 재시도한다. 부모의 실제 삭제가 확인된 자식 작업은 완료하여 무한 재시도를 막는다.
- `reconcile`은 추출 버전이 달라진 완료 포인터만 다시 기록하며 원문을 읽지 않는다.
  최초 누락은 단계①의 kind별 ID 페이지 bootstrap으로 처리한다.

## 검증 기록

- RED: 출처 저장소/소비 모듈 없음 2 failed, 0 errors.
- 추가 RED: soft-deleted 부모의 file/evidence 작업이 source_unavailable로 남음.
  부모 삭제 확인 후 tombstone 완료하도록 수정, 새 회귀에서 변경 3종 모두 완료 확인.
- 시험 수정: 접근 상태 행이 없는 곳에 UPDATE를 보내던 설정을 INSERT/UPSERT로 수정.
  화면 문구와 DB enum도 구분하여 DB의 `잠김`을 사용했다. 이를 보안 기능 성공 증거로 세지 않았다.
- 집중 검사 14 passed / skipped 0 / deselected 1248, 23.61초.
  [로그](../reports/ai-search-facts/focused-3.log). 이후 타 연구실 raw 조회/쓰기 42501 검사를 보강하여 전체 검사에 포함했다.
- migration-single-head: platform/AI 모두 head 1개. schema-diff: 전체 upgrade 후 두 체인 드리프트 0.
- rls-coverage: 53표 조사, 기존 allow-list 11표 면제, 새 표 FORCE RLS 유지.
- rls-effect: 우회 불가 앱 롤, lab_id 42표 전수 경계. import-boundary: 8개 계약 통과.
- 첫 core 전체 회귀: 1245 passed / 11 failed / errors 0. 기존 테스트가 만든 자료가 남아
  목록·집계 기대값을 오염했다. 새 기능→기존 조회의 순차 집중 검사 30건은 통과했다.
- 기존 테스트 정리의 시각 기준만으로는 과거 시각의 새 행을 놓치는 문제를 별도 재현했다.
  `cleanup-red.log` 1 failed → 시작 전 PK 비교를 추가한 `cleanup-green.log` 1 passed.
  기존 시간 조건·시드 보호·FK 순서·앱 롤 RLS를 유지했다. 실제 전체 누출의 시계 원인을 단정하지 않는다.
- core 최종 전체 회귀: **1257 passed / skipped 0 / deselected 6 / failed 0 / errors 0**,
  177.17초, exit 0. [최종 로그](../reports/ai-search-facts/core-final.log).
  `COLAB_SERVICE_TEST_JOBS=2 bash gates/tools/service-tests.sh core-api 'not e2e'`로
  동일 서비스 게이트를 직접 실행했다. 이전 `core/gate-summary.json`의 실패 기록은 그대로 보존하며
  최종 통과 JSON으로 바꿔 쓰지 않았다. 실제 브라우저 E2E 6건은 선택자에서 제외했다.
- `git diff --check`: exit 0. 커밋·push·배포 없이 기존 단계① 변경과 함께 작업 사본에 보관.
- 독립 수용 검토: 부모 삭제 재시도 수정 및 테스트 정리 보강 모두 추가 차단 사항 없음. 검토자의 정적 판정과 실제 게이트 실행을 구분한다.

## intent 대조

- O1 자연어/복합 검색: 지속 갱신의 자료 기반 추가. 기존 검색 질의 경로는 이번에 교체하지 않았고 품질 기준 미충족은 유지.
- O2 맞는 이유/자료 역할: 출처와 사실 버전을 보관하지만 개념 관계 연결과 결과 설명에 실제 결합하는 일은 남음.
- O3 확인 가능한 한계: draft/ready 분리, 원본 무효화와 권한 차단. 의미 추론의 정확도는 이번 결정적 추출 시험으로 주장하지 않음.
- O4 상세 이동: 화면 변경 없음. 신규 UI/E2E 성공으로 세지 않음.
- O5 레퍼런스/골든셋: 기존 자료/문항 유지, 실제 Sonnet 평가 보류 유지.
- 검증을 위해 추가한 범위: 공통 테스트 정리 보강 1건. 신규 기능의 전체 회귀를 신뢰할 수 있도록 재현된 격리 취약점을 수정했으며 제품 동작 변경은 아니다.
- 후속 사용자 승인인 지속 갱신 범위 안의 구현이다. 이 기반을 전체 ontology/KG/agent 완료로 보고하지 않는다.

## 다음 진입점과 제한

현재 단계② 중 **사실·출처 저장 기반**까지다. 다음은 온톨로지 내용 버전과 개념별 의존 연결이다.
그 연결을 받은 에이전트가 source reader로 허용된 자료를 읽고 출처가 있는 후보를 제출하도록 도구 계약을 만든다.
이후 단계③ 일일 실행·검증 후 공개/캐시, 단계④ 검색 연결, 단계⑤ 실제 Sonnet 추출/평가로 이어간다.

미구현: 의미 관계를 자동 생성하는 실제 agent, 온톨로지 변경 영향 인덱스, 전체 KG 공개본 전환,
일일 스케줄러, 검색 경로 교체. 제품 DB bootstrap/reconcile 및 실제 LLM 호출·배포는 실행하지 않았다.
공통 D9 온톨로지와 기존 삭제 보호·배포 정책 분리는 유지한다.
