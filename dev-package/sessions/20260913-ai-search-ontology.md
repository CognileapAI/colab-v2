# 온톨로지 내용 버전·해석 의존 기반 인계

출처: [사양](../prd/specs/AI-SEARCH-ONTOLOGY-VERSIONS.md), [계획](../prd/rounds/R-AI-SEARCH-ONTOLOGY-VERSIONS.md).
브랜치 codex/ai-search-next, 기존 단계①/② 미커밋 변경을 보존했다. 사용자 “다음작업”에 따른 후속 구현.

## 구현과 범위

- D9 기존 5표를 ai-service에서 한 SELECT로 읽고 생성 시각을 제외한 내용 해시를 생성한다.
  어휘 탐색 범위와 개념별 1-hop 의미 의존 해시를 구분한다. D9 쓰기/DDL/권한 변경은 없다.
- core는 manifest Port 값을 검증하고 D3에 연구실별 수신 이력/현재 포인터/사실별 의존을 저장한다.
  D9 DB 직접 접속이나 D10→기록 도메인 직접 쓰기 경로를 만들지 않았다.
- 개념 관계 변경은 관련 해석만, 어휘 변경은 매칭 0건을 포함한 모든 기존 해석을 재점검 대상으로 삼는다.
  큐에 넣는 과정은 원문을 읽지 않으며 작은 묶음·lease·기존 처리 버전을 유지한다.
- 내용 해시는 시간 순서가 아니다. 발행에는 이전 버전 비교를 요구하고 같은 버전 재수신은 멱등이다.
- 사실 스냅샷의 미연결 표시는 유지한다. 별도 binding은 해석기의 읽기 의존이지 의미 정답/공개 승인 증거가 아니다.
- 온톨로지 삭제 보호와 배포 정책 분리, 실제 Sonnet 평가 보류는 유지한다.

## 검증 기록

- 최초 RED: core 신규 저장소 없음 1 failed, AI 모듈 없음 4 failed.
- 초기 core 집중 6 passed. 시험 설정에서 보이지 않는 과거 binding이 참조하는 release를 지우려 해 FK 오류가 났다.
  시험은 이력을 보존하고 해당 일회용 연구실의 현재 포인터만 초기화하도록 수정했다.
- AI 내용 해시/단일 SELECT 실제 사전 DB 검사 5 passed. 첫 시험 준비는 임시 DB mount 경로가
  기존 온톨로지 보호 조건과 달라 거부되었다(exit 65). 보호 장치는 수정하지 않았으며 요구한 tmpfs 경로로
  새 일회용 DB를 준비했다. 운영 DB에 접속하지 않았다.
- 독립 리뷰: 의존 일부 누락 및 head 조회 경합을 지적했다. 누락 RED 1 failed,
  동시 실행 RED 1 failed를 확인했다. 예상 집합 완전성 검사와 조회 직렬화를 추가한 뒤
  최종 집중 **10 passed / skipped 0 / deselected 1263**, 42.92초. 재검토 추가 차단 사항 없음.
- AI 서비스 회귀 **146 passed / skipped 0 / dictdb 제외 27**, 20.95초.
  이 27건 중 신규 manifest의 실제 DB 검사는 위 5건 실행에 포함했다. 두 실행의 겹치는 4건은 합산하지 않는다.
- 스키마 첫 실행은 잘못된 환경 변수 이름을 사용하여 기존 시험 설정의 연결을 시도하다
  연결 실패로 종료했다(exit 1, upgrade 전). 올바른 `COLAB_APPLIED_DB_URL_PLATFORM/AI`를
  전용 임시 설정 파일에 선언하고 새 일회용 DB로 실행한 최종 검사는 두 체인 upgrade 후 drift 0.
- migration-single-head: platform 0035 / AI 기존 0007, 각각 head 1개.
- RLS coverage: 새 표 포함 FORCE RLS 유지. RLS effect: lab_id 46표, 우회 불가 앱 롤 경계 통과.
- import-boundary 8계약 통과, work-item-consistency 불일치 0.
- 중간 core 집중 실행 중 시험 추가로 수집/실행 수가 달라 해당 실행은 통과 증거에서 제외했다.
  삭제 시험의 deleted_by 필수값 누락도 설정 오류로 구분한다.
- 최종 core 회귀 **1267 passed / skipped 0 / deselected 6 / failed 0 / errors 0**,
  201.64초, exit 0. 제외 6건은 기존 실데이터 E2E이며 이번 UI/모델 성공으로 세지 않는다.
  [로그](../reports/ai-search-ontology/core.log), [게이트 요약](../reports/ai-search-ontology/core/gate-summary.json).
- ai-no-lineage-write: 계약/코드/체인 3층 통과. db-boundary: 8단위 423대상, 위반 0.
- 신규 migration SQL과 schema 선언 일치, `git diff --check` exit 0.
- 이번 사양의 로컬 구현·검증 완료. 전체 AI 검색 품질이나 실제 일일 agent 가동 완료가 아니다.

## intent 대조와 다음 진입점

- O1 자연어 검색: 갱신 의존 기반 추가, 실제 검색 경로 연결·품질 판정은 미달 유지.
- O2 추천 이유/역할: 사실과 개념의 읽기 의존 추적까지. 실제 의미 연결/추천 설명 생성은 미달.
- O3 확인 가능한 한계: 미매칭·오래된 결과·불완전 의존을 제외하는 기반. LLM 의미 정확도를 주장하지 않는다.
- O4 상세 이동: UI 변경 없음, 기존 흐름 유지. 신규 E2E 검증으로 세지 않는다.
- O5 레퍼런스/골든셋: 기존 유지, 실제 Sonnet 평가 보류. 품질 완료를 주장하지 않는다.
- 초과: 원래 intent의 최초 범위 이후 사용자가 승인한 지속 갱신 기반 개발. 제품 UI/배포 범위 확대 없음.

다음: manifest 전송 어댑터와 제한된 agent 도구 연결 → 매일 실행 조율/재시도/운영 상태 → 검색 연결.
미구현: 실제 의미 추론 agent, manifest 서비스 전송, 일일 스케줄러, KG 공개본 전환, 검색 경로 적용.
제품 DB 갱신·커밋·push·배포는 실행하지 않았다. 작업 대장 K4는 open을 유지한다.
