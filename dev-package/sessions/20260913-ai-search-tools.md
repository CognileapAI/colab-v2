# 온톨로지 전송·갱신 도구 인계

출처: [사양](../prd/specs/AI-SEARCH-TOOLS.md), [계획](../prd/rounds/R-AI-SEARCH-TOOLS.md).
사용자 “다음 작업!”에 따른 후속. codex/ai-search-next에서 기존 미커밋 개발을 보존했다.

## 구현

- core-ai 계약 GET /ontology-manifest와 양 서비스의 계약 생성 상수 추가.
- AI 서비스는 COLAB_AI_SERVICE_TOKEN 또는 _FILE을 요구한다. 미설정/DB 부재 503, 잘못된 인증 401.
  token은 Settings repr에서 제외한다. 기존 검색/계보 endpoint의 인증 정책은 이 작업에서 변경하지 않았다.
- core OntologyHttpClient는 redirect를 따르지 않고 실제 수신 bytes 16 MiB 상한과 내용 해시를 검사한다.
  네트워크 timeout/반복 deadline 검사이며, blocking read마다 남은 시간을 설정하는 엄격 총시간 SLA는 아니다.
  실패 메시지에 서버 응답·토큰·연결 문자열을 싣지 않는다.
- build_search_refresh_tools는 core 설정의 ai_base_url/ai_service_token과 신뢰된 인증 Subject를 사용한다.
  caller가 서버 조립 코드에서 인증 주체를 제공해야 한다. 도구 API의 제한이며 임의 Python 실행을 격리하는 OS sandbox가 아니다.
- sync_manifest는 네트워크 전에 현재 버전을 캡처하고 DB 연결을 닫은 후 가져와 CAS로 발행한다.
- claim은 최대 100개, 인스턴스당 핸들 1000개, 수명 300초. read/complete 때도 lease·원본·권한·head를 재검사한다.
- read 결과를 서버에 별도 복사하여 반환 객체 수정으로 증거를 바꿀 수 없게 한다.
- ready의 사실·개념 의존·ack는 한 transaction이며 commit 뒤 handle을 소비한다.
  candidate는 후보 저장/ack만, deleted는 tombstone ack만 한다. 둘에는 concept_ids를 허용하지 않는다.
  비공개/미접근을 삭제로 추정하지 않는다. 부분 실패·commit 직전 실패 주입에서 rollback 후 같은 핸들로 재시도할 수 있음을 확인했다.
- concept_ids는 해석기의 읽기 의존이다. 임의 사실 문장·SQL·원본 파일 경로를 입력받는 도구는 없다.

## 검증 기록

- 최초 RED: AI 404/서비스 토큰 설정 부재 3 failed; core 도구/HTTP 어댑터 부재 2 failed + 4 setup errors.
- 삭제 작업 RED 1 failed → 삭제 증명 후 종결; draft RED 1 failed → 후보 저장 후 종결.
- token repr 노출 RED 1 failed/3 passed → repr 제외 후 AI HTTP 4 passed.
- 중간 시험 설정 오류: lease 없는 큐까지 만료 시각을 넣어 CHECK 위반. lease 있는 행만 수정하도록 시험을 고쳤다.
  설정 패치의 문법 오류로 helper 인자가 반영되지 않은 실행도 실패로 보존했다. 제품 기능 결함과 구분한다.
- 최종 집중 **16 passed / skipped 0 / deselected 1273**, 26.09초.
  [로그](../reports/ai-search-tools/core-focused-green.log).
  원본/권한/head/lease 변경, 늦은 CAS 응답, 바깥 transaction commit 직전 실패 주입, 인스턴스/메모리 만료,
  반환 객체 변경, redirect/timeout/실제 크기/내용 검증을 포함한다.
- 실제 일회용 사전 DB → AI HTTP 200 → core 인증/내용 검증, 동일 내용 재요청 일치.
  [연결 로그](../reports/ai-search-tools/http-bridge.log). 두 서비스 모듈을 시험 프로세스에만 조립해 localhost 실제 HTTP로 검증했다.
- AI 서비스 **150 passed / skipped 0 / dictdb 제외 27**, 15.14초. 실제 DB 전송 검사는 별도 위 연결 기록이다.
- contract-lint: seam 3건 위반 0. generated-up-to-date: 등기부 15건 재생성 일치, 미등재 생성물 0.
- 독립 설계/수용 검토: candidate·삭제 종결 보완 후 추가 차단 사항 0.
- 첫 전체 core: **1282 passed / 1 failed / skipped 0 / deselected 6**, 205.94초.
  기존 감사 시험이 ORDER BY 없는 결과의 마지막 행을 최신으로 가정했다.
  PATCH 전 source_id 집합과 비교하여 신규 이벤트 정확히 1건/이전 이름/변경 이름/요약을 검증하도록 보강했다.
  독립 검토에서 순서 의존 제거 및 검증 강화로 확인했다. 제품 감사 코드는 변경하지 않았다.
- import-boundary 8계약, db-boundary 8단위 430대상, AI 쓰기 금지 3층, work-item-consistency 모두 통과.
- 감사 시험 집중 재검증: **1 passed / skipped 0 / deselected 1288**, 6.75초.
- 최종 core: **1283 passed / skipped 0 / deselected 6**, 166.30초, 종료 0.
  [최종 로그](../reports/ai-search-tools/core-final.log). 선택자 `not e2e`이며 브라우저 E2E는 이번 검증에 포함하지 않았다.
- 최종 `git diff --check` 통과. 독립 수용 검토와 intent 대조 완료; 이 단위 완료, 전체 K4는 open 유지.

## intent 대조와 다음 단위

- O1 자연어 탐색: 갱신 실행 도구 기반까지. 실제 검색 경로와 품질 기준은 미달 유지.
- O2 이유/역할: 해석 의존을 원자적으로 기록하지만 개념 의미 조회/LLM 판단/추천 설명은 후속이다.
- O3 한계: draft의 사실 승격을 금지하고 오래된 읽기를 거부한다. 의미 추론의 정답률은 검증하지 않았다.
- O4 상세 이동: UI 변경 없음. 기존 E2E를 새 성공으로 재사용하지 않는다.
- O5 레퍼런스/골든셋: 기존 유지, 실제 Sonnet 평가는 보류 유지.
- 초과: 검증 신뢰성을 위해 기존 감사 시험의 조회 순서 의존 1건을 보강했다. 사용자의 후속 승인인 지속 갱신/agent 도구 기반 확장. UI·운영 DB·배포 범위 확대 없음.

다음: 온톨로지 개념 내용 조회 도구 → 제한된 실제 agent 실행 조율 → 매일 실행/재시도/실행 상태 → 검색 연결.
아직 실제 LLM agent, 새 개념 자동 제안, 일일 스케줄러, 검색 결과 경로 교체를 가동하지 않았다.
공통 D9 데이터/스키마/삭제 보호는 변경하지 않았다. 제품 DB 갱신·커밋·push·배포 미실행, K4 open 유지.
