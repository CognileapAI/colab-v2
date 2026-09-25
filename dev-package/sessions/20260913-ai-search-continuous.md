# 지속 갱신·검색 연결 개발 인계

출처: [사양](../prd/specs/AI-SEARCH-CONTINUOUS.md), [전체 실행 계획](../prd/rounds/R-AI-SEARCH-CONTINUOUS.md).
사용자 “한건한건 멈추지말고 전체 계획을 말하고 실행을 해라”에 따라 개념 조회부터 일일 처리·검색까지 로컬 개발 계획 6단계를 연속 수행했다. 브랜치 codex/ai-search-next, 기존 미커밋 변경 보존. 배포 정책 별도 브랜치 유지.

## 구현 흐름

1. D9의 버전 고정 개념 조회: 인증된 `/ontology-concepts`, 최대 6개 후보/각 1홉 내용 증명. core는 수신 내용 해시를 manifest와 대조한다. 사전 내용은 버전별 1개 메모리 스냅샷으로 재사용한다.
2. `/search-concept-proposals`: Sonnet Messages 어댑터, 기본 `claude-sonnet-4-5`, 출력 1,024 tokens, 실행 도구 없음. 모델 입력은 facts와 개념 후보이며 제품 DB·파일·SQL에 직접 접근하지 않는다.
3. core는 실제 인용·predicate·조회한 후보·동의 관계를 대조한다. 원본 자료에 적힌 개념/동의어만 연결한다. 임의 의미 추론을 검증된 사실로 승격하지 않는다. 모든 조회 의존성과 선택된 연결을 구분하며 사실·의존·선택·ack를 한 트랜잭션으로 저장한다.
4. selector receipt는 “정상 0개 선택”과 “아직 미실행”을 구분한다. 이전 단계에서 처리한 자료도 새 선택 단계에 자동 재등록하며, 정상 0개를 매번 모델에 보내지 않는다.
5. `search_refresh_worker`는 계정별 실행 상태/lease/generation/bootstrap 위치/다음 실행 시각을 보존한다. 처음에만 목록을 페이지로 읽고 이후 변경 원장과 버전 무효화만 처리한다. 계정 활성/비밀번호 변경 요구/session version과 원본 본문 권한을 재검사한다.
6. 실패는 고정 코드와 지수 재시도로 남긴다. 미래 재시도도 pending이며 완료로 접지 않는다. 기본 batch 100개/180초 시작 예산, 실패 10개에서 회차를 멈춘다. 개별 네트워크 읽기의 엄격 총시간 SLA를 뜻하지 않는다.
7. 검색은 현재 selector·온톨로지 의존·원본·RLS가 유효한 선택만 사용한다. 모델이 순위나 데이터셋 ID를 결정하지 않는다. 후보와 설명은 동일한 현재성 조건으로 DB에서 걸러내고 표시 페이지에 최대 3개 개념만 붙인다. 1,002개 연결에도 고정 Python 스캔 상한 때문에 검색이 실패하지 않는다.

## 실행 진입점 — 배포 시 활성화할 코드

- AI 설정: 기존 D9 읽기 DB와 `COLAB_AI_SERVICE_TOKEN`/`_FILE`, `ANTHROPIC_API_KEY`/`_FILE`. 선택 모델은 `COLAB_AI_CONCEPT_MODEL`; 실제 모델 평가·호출은 이번 회차 0건.
- core 설정: 기존 일반 앱 DB와 계정 관리 DB, AI 서비스 주소/토큰. `COLAB_SEARCH_REFRESH_ACCOUNTS`/`_FILE`에 로그인 이름의 JSON 배열을 명시한다. 모델 입력·사용자 요청으로 주체를 선택하지 않는다.
- `services/core-api` 환경에서 `python -m colab_core.app.search_refresh_worker --once`, `--loop`, `--status`.
- `--loop`는 30초마다 기한을 확인하고 정상 완료 후 24시간 뒤 다시 갱신한다. bootstrap/재시도 pending은 60초 뒤 재확인한다. 계정별 manifest 확인도 24시간 간격이다. 계정 목록의 접근 가능 범위만 처리하므로 전체 제품 데이터 처리 완료를 자동으로 뜻하지 않는다.
- HTTP 앱 시작 시 자동으로 작업하지 않는다. 운영 서비스/스케줄 설치·재시작은 실행하지 않았다. 새 설정 이름은 위 코드가 직접 소비하며 배포 정책 파일은 수정하지 않았다.
- 준비 미설정 CLI 78, 실행 오류 1, 정상 회차/기한 전 대기 0. 0은 전체 backlog 완료 의미가 아니므로 출력 status를 함께 확인한다.

## 검증 기록

- 조회 최초 RED 4건 → GREEN 4건. 인증 전에 본문을 소비하는 RED 1건을 추가하고 streaming 크기 제한/인증 선검사로 수정.
- Sonnet 어댑터 최초 RED 5건 → 어댑터/HTTP/설정 집중 17건 GREEN. 최종 AI 집중 18건 GREEN.
- core 최초 6 failed/2 passed → 첫 집중 24 passed. 검색 미연결 RED 2건 → 검색/worker 8 passed.
- 기존 처리 자료 전환 RED 1 failed/3 passed → selector receipt/reconcile 추가. 통합 집중 39 passed, skipped 0, deselected 1273, 51.16초.
- AI 전체 164 passed, skipped 0, dictdb 제외 27, 29.86초. 실제 사전 DB 연결은 별도 HTTP 연결 검사로 수행했다.
- 실제 일회용 D9 DB → 인증 HTTP manifest/lookup → HTTP proposal → Sonnet 어댑터(모델 전송만 대역) → core 인용 검증 GREEN. [로그](../reports/ai-search-continuous/http-bridge.log). 실제 모델 호출 0건, 제품 DB 접촉 0건.
- 첫 core 전체 1306 passed, skipped 0, deselected 6, 272.06초. 대량 연결 처리 보완 전 결과이며 최종으로 재사용하지 않는다.
- 계약 3 seam 위반 0, 생성물 15건 재생성 일치. import 8계약, DB 경계 8단위/444대상, AI 쓰기 금지, migration single head, RLS coverage GREEN.
- CI용 일회용 DB에서 platform/ai 각각 Alembic head 적용 후 schema-diff GREEN. 운영 DB나 홈 환경의 적용 DB를 사용하지 않았다.
- 대량 연결 최초 2건 RED(기존 1,000건 상한으로 HTTP 500). 상한을 없앤 뒤 기능 30건 통과했으나 stale 검색 104.522초를 관측해 10초 회귀 기준 추가 → 성능 RED.
- 후보 MATERIALIZED/의존 집계/JIT LOCAL 조정 후에도 정상 연결 검색 14.720초 RED. EXPLAIN (ANALYZE, BUFFERS)에서 새 연결 RLS의 원본 검사가 502,503회 반복되는 것을 확인했다. 같은 RLS 조건을 binding/fact PK scalar 조회로 바꿔 반복 dataset 스캔을 제거했다. RLS 우회·전역 DB 설정 변경 없음.
- 최종 연결/runner 집중 20 passed, skipped 0, deselected 1300, 20.44초. 실제 API 검색 1,002개 유효 연결 0.654초, stale 연결 0.333초. [로그](../reports/ai-search-continuous/connection-final.log). 10초 기준은 이 격리 회귀의 상한이며 운영 SLA를 뜻하지 않는다.
- 누락/변조/추가 dependency, discovery 누락, 무관한 manifest 항목 추가, 타 연구실 읽기, dataset 불일치 쓰기 거부를 실제 앱 DB 권한으로 확인. 최종 core 전체 1314 passed, skipped 0, E2E 제외 6, 163.63초. [전체 로그](../reports/ai-search-continuous/core-final.log).
- 모델 없는 기존 골든 helper 43건 GREEN. public API 골든 시험은 전체 core 실행에 포함한다.
- RLS 변경 뒤 schema-diff 두 체인, import/DB boundary, RLS coverage, migration single head 재검증 GREEN. 독립 advisor의 최종 SQL/RLS 의미 검토 clean.
- 이전 집중 실행 2회에 각각 검색 연결 부재 1건을 관측했다. setup 처리건수·queue/facts 진단을 추가했고 최신 집중은 통과. 최종 전체 1314건 및 추가 검색 통합 11건(20회 연속 원본 변경 1개 시험 포함)에서 재현되지 않았다. 추가 시험은 마지막 전체 실행 뒤 시험 코드만 보강한 것으로, 전체 1315건을 다시 실행했다고 합산하지 않는다. [연속 갱신 로그](../reports/ai-search-continuous/repeated-refresh.log). 원인은 미확정이다. failed=0은 한 batch의 완료 보장이 아니며 실제 일일 runner는 남은 queue를 pending으로 유지한다. 재시도나 판정 기준 완화로 숨기지 않았고, 운영 전 지속 실행에서 확인할 사항으로 남긴다.

## intent와 범위

- O1: 온톨로지 연결로 실제 검색 후보를 추가하고 기존 낱말 검색을 유지한다. 전체 자연어 품질/실제 Sonnet 평가 기준 충족은 아직 주장하지 않는다.
- O2/O3: 출처에 적힌 개념·동의어와 실제 인용만 저장하고 draft·삭제·stale·권한 회수를 구분한다. 의미 추론이나 연구 적합성을 보장하지 않는다.
- O4: 기존 결과/상세 이동 UI 구조 유지. 새 브라우저 사용자 여정은 실행하지 않았다; 실제 검색 API 검증과 구분한다.
- O5: 기존 레퍼런스 골든셋에 새 연결·변경·권한·대량 이력 회귀를 추가한다. 모델 해석은 시험용 대역/고정값이며 실제 Sonnet 품질의 근거가 아니다.
- 공통 D9 온톨로지의 개념/관계 신규 확정은 자동화하지 않는다. 이 회차의 자동 갱신은 D3 파생 KG·연결이고 D9는 읽기 전용이다.
- 실제 Sonnet 평가 보류·운영 일일 실행 활성화·배포·main 통합은 미실행. K4 전체는 open 유지. 코드만 완성한 상태를 운영 가동으로 보고하지 않는다.

모델 전송 계약 참고: [Anthropic Messages 공식 문서](https://platform.claude.com/docs/en/build-with-claude/working-with-messages). 제안의 내용 타당성 검증은 core 서버에서 별도로 한다.


## 완료 판정과 다음 실행 경계

- 이 로컬 사양의 수용 기준 1~5는 구현·계약·음성 검사·실제 DB/HTTP 회귀와 독립 검토로 확인했다. 실행 계획의 개발 단계 1~6 완료. 제품 전체 intent 완료나 실제 운영 가동을 뜻하지 않는다.
- 원본 intent 미달: O1 실제 모델 자연어 품질 수용, O4 이번 변경의 브라우저 사용자 여정, O5 실제 Sonnet 결과 평가는 미실행이다. 사용자의 모델 평가 보류와 로컬 개발 범위에 따른 구분이다.
- 범위 초과: 자동 신규 D9 개념 확정·제품 데이터 변경·배포·main 통합은 수행하지 않았다. 파생 KG 일일 worker는 이번 승인된 지속 갱신 사양 범위다.
- 운영 전 확인: 실제 Sonnet 평가 재개, 지정 계정 접근 범위로 ST 일일 실행 활성화/지속 관측, 위 간헐 사례 재발 여부. 배포 정책 작업은 별도 브랜치에 유지한다.
