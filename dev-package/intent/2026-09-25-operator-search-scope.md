# Intent: 무소속 시스템 관리자(운영자)의 자료 검색 범위를 계약으로 연다
메타 — 발의자: agent(이슈 #158 조사) · 작성 2026-09-25 · 승인 미승인

## 문제
- 연구실 소속이 없는 시스템 관리자 계정은 AI 해석 경로의 자료 검색(`POST /api/v1/dataset-searches`)에서 「검색 서비스 이용 불가」(503 `SEARCH_UNAVAILABLE`)를 받는다(이슈 #158 · dev f0be4268 실측).
- 원인: core-api 가 ai-service 에 `scope.labId` 로 문자열 `"None"` 을 보낸다(`services/core-api/src/colab_core/app/routes/catalog.py:483-487`). ai-service 는 ULID 가 아니므로 400 을 낸다(`services/ai-service/src/colab_ai/app/main.py:337-339`). core-api 는 이를 해석 불가로 받아 503 으로 바꾼다(`services/core-api/src/colab_core/app/relay.py:426-427` → `catalog.py:489-501`).
- 조건 검색 갈래(`catalog.py:479-481` → `_client_search`)는 ai-service 를 거치지 않아 503 은 나지 않는다. 다만 응답 `scope.labId` 가 여전히 `"None"` 이다(`catalog.py:689`). 이 값은 fe-core 계약 `AiSearchScope.labId`(ULID 필수)를 어긴다(`contracts/schemas/common.json:193-202`, `contracts/seams/fe-core.yaml:5355-5356`). AI 경로가 200 을 내더라도 같은 위반이 남는다(`catalog.py:615`).

## 원한 결과 (proposed outcome)
- 무소속 운영자 계정으로 AI 해석 경로의 질의(예: 「강우 자료」 — `client_search.plan_query` 가 인식하지 않는 자연어)를 검색하면 200 이 온다. 범위 줄은 「전체 연구실 데이터 N건을 뒤졌어요」이고, N 은 결과와 같은 스코프에서 센 값이다(`catalog.py:473-475` 와 `:520-521` 가 같은 인자로 연다).
- 운영자 응답의 `scope` 는 계약 스키마 검사를 통과한다. `"None"` 같은 가짜 식별자는 요청과 응답 어디에도 실리지 않는다.
- 운영자 결과 카드마다 그 자료가 속한 연구실 이름이 붙는다.
- 비운영자(교수·일반 구성원)의 요청 본문, ai-service 호출 본문, 응답은 바이트 단위로 달라지지 않는다. 기존 `test_search_scope.py` 대조군과 cross-tenant 음성 테스트가 그대로 green 이다.
- ai-service 가 400 을 내는 조건은 비운영자에게 지금과 같다. 경계 없는 요청(scope 부재, 주체 부재)은 계속 거절한다(`main.py:334-347`).

## 가치 가설
- 무소속 시스템 관리자는 전 연구실 자료를 한 번의 자연어 검색으로 찾을 수 있게 된다. 이것으로 운영 지원(문의 자료 찾기, 중복·오등록 점검)을 카탈로그 수동 필터 없이 처리한다.
- 확인 방법: dev 에서 운영자 계정으로 AI 경로 질의를 실행한다. 200 인지, 서로 다른 연구실의 결과가 함께 나오는지, 카드의 연구실 이름이 자료 상세의 소속과 같은지 본다. 같은 질의를 교수 계정으로 실행하여 변경 전후 응답이 같은지 대조한다. 셋 중 하나라도 어긋나면 가설이 틀린 것으로 본다.

## 영향 범위
- 사용자 / 화면: 운영자 검색 히어로와 검색 결과(`frontend/src/routes/SearchResultsPage.tsx:18-29` 범위 줄 · `:145`). 카드에 연구실 이름 표시를 더한다(Q2). 비운영자 화면은 변경하지 않는다.
- 서비스 · 스키마 · 계약:
  - core-api: `routes/catalog.py` 의 `search_datasets`·`_client_search`, `app/relay.py` 의 `interpret`(`:409-432` 응답 scope 대조)
  - ai-service: `app/main.py:334-347` scope 검사, `domains/d10_ai_services.py:141-142` 응답 envelope
  - 계약: `contracts/seams/core-ai.yaml` `RequestedScope`(`:1107-1120`), `contracts/schemas/common.json` `AiSearchScope`(`:193-202`, core-ai `:779`·`:982` 와 fe-core `:5356` 가 함께 참조), `contracts/seams/fe-core.yaml` `SearchResultRow`(`:5451-5459`). 생성물 `frontend/src/generated/fe-core.ts` 는 재생성한다.
  - DB: platform migration 1건 — `d3_search_evidence` 운영자 읽기 정책(`operator_read`) 추가(Q7). 표 구조 변경 없음. 근거: `0031_search_evidence.py:47-53` 에 해당 정책이 없다.
- 계약 파괴 여부: **아니오** — 요청은 선택 칸 추가·완화, 응답은 운영자용 변형 스키마를 따로 둔다(Q6). 기존 `AiSearchScope`·`SearchResultRow` 필수 속성은 손대지 않는다. `[oasdiff 는 PR 게이트 contract-breaking 에서 실측]`
  - 요청 쪽 변경 두 가지(core-ai `RequestedScope.labId` 를 required 에서 빼기, 선택 칸 `operatorScope` 추가)는 요청 완화·선택 추가다. 통상 oasdiff ERR 이 아니다.
  - 응답 쪽 `AiSearchScope.labId` 를 선택 또는 nullable 로 바꾸는 것은 응답 속성 완화다. oasdiff `breaking --fail-on ERR` 기준으로 ERR 에 해당할 가능성이 높다. 판정 게이트: `gates/tools/contract-breaking.sh:79-83`.
  - `SearchResultRow` 의 두 번째 객체에 선택 속성 `labName` 을 더하는 것은 응답 선택 속성 추가라 통상 비파괴다.
  - 파괴를 피하는 선례가 있다. `CurrentAccountV2`(`fe-core.yaml:4145-4165`, `[사용자 승인] 이슈 #36`)는 기존 스키마를 두고 labId nullable 변형을 따로 세웠다. 같은 방식으로 운영자 응답용 scope 변형을 둘 수 있다.

## 제약
- `.agents/rules/product.md` §3-5(`:68`): 모든 조회에 연구실 경계가 자동 주입된다. 운영자의 넓은 범위도 경계 해제가 아니다. `operator_read` 정책(FOR SELECT · PERMISSIVE, `db/platform/versions/0029_operator_read_policy.py:13-39`)과 `apply_scope` 가 표현한다(`services/core-api/src/colab_core/kernel/scope.py:41-65`). 쓰기는 `lab_boundary` 를 그대로 통과해야 한다.
- 「경계 없이 뒤지지 않는다」: ai-service 는 scope 나 주체가 없으면 거절한다(`main.py:334-347`). core-ai 계약은 경계를 호출자가 명시적으로 넘기고 추론하지 않게 둔다(`contracts/seams/core-ai.yaml:23-29`). 운영자 범위도 명시적 표식으로 넘겨야 한다. labId 를 빼기만 하는 설계는 이 원칙과 충돌한다.
- 경계는 두 곳에서 정하지 않는다: ai-service 는 헤더 `X-CoLAB-Lab` 과 본문 `labId` 가 다르면 400 이다(`main.py:341-345`). core-api 는 응답 scope 가 요청과 다르면 버린다(`relay.py:428-432`). 운영자 표식에도 같은 이중 대조 규칙을 정의해야 한다.
- AI 응답 규격(`product.md:73-80`): 뒤진 범위를 먼저 밝히고 근거는 한 줄이다(`:79`). 못 찾으면 정직한 빈 상태다(`:78`). AI 없이도 v2 는 완결된 제품이다(`:80`). 운영자 범위 줄도 실제로 뒤진 범위와 분모를 말해야 한다(`test_search_scope.py` 오라클 ⑴⑵).
- 503 과 0건을 구분한다(`catalog.py:430-434` · `fe-core.yaml:1362-1370`). 운영자에게 「0건 200」으로 우회하지 않는다.
- 정규 ID 타입은 `common.json` 에서만 정의한다(`product.md:69`). 생성물은 손으로 고치지 않는다(`product.md:70`).
- 경계를 넘어야 하면 우회하지 않고 멈춘다(`product.md:94-100`). ai-service(D10)는 D3 를 읽지 않는다(`main.py:16-17`). 연구실 이름 조립은 core-api 몫이다.
- ai-service 가 `labId` 로 하는 일은 세 가지뿐이다. 요청 검사(`main.py:337-345`), 응답 되비춤(`d10_ai_services.py:141-142`), 사전 실패 로그(`:199-201`). 데이터셋 조회, core-api 콜백, 테넌트별 사전 조회에는 쓰지 않는다. 사전 5표에는 `lab_id` 가 없다(`app/dictionaries.py:6-7`). 모델 호출 원장의 `lab_id` 는 이미 NULL 을 허용한다(`db/ai/versions/0011_d10_model_call_ledger.py:90-91`). 원장 lab 은 해석기 생성 때 정해지고 요청 값을 쓰지 않는다(`main.py:206-208` · `app/interpret.py:168-175`). 따라서 ai-service 가 요구하는 「경계」는 형식 검사와 되비춤 정합뿐이다.
- 운영자 권한: 승인 intent `dev-package/intent/2026-09-16-admin-full-access.md:10`·`:32` 는 시스템 관리자에게 모든 연구실의 전체 권한을 준다. 여기에는 「나만 보기」·지정 공개 자료가 포함된다. 코드도 운영자에게 `app.operator_manage=on` 을 켠다(`kernel/scope.py:61-62`). 그래서 `is_dataset_manager` 가 참이 되고(`db/platform/versions/0033_admin_body_access.py:10`), 모든 결과의 `bodyAccessible` 이 참이다(`domains/d2_access.py:72`·`:184`). `accessState` 문자열(잠김 등)은 그대로 내려간다(`catalog.py:182`).
- 재시드 최종화는 운영자가 무소속인지 검사한다(`dev-package/tools/dev-reseed/accounts.py:61` `labless operator mismatch`).

## 설계트리 (grill-me 결과)
- Q1 운영자 검색 범위를 무엇으로 하나(ⓐ 전 연구실 / ⓑ 연구실 선택 필수 / ⓒ 단일 연구실 대체) → A ⓐ 전 연구실 검색 (권장안 수용)
  - 권장 근거: spec `admin-role-scope.md:9` 「시스템 관리자는 모든 연구실」. 목록·분모가 이미 전 연구실 스코프로 돈다(`catalog.py:473-475`·`:520-521`). 필요한 것은 core-ai 계약과 ai-service 검사에 운영자 범위 표식을 정식으로 여는 것이다.
  - 반대 사유(기록): ⓐ는 응답 `AiSearchScope.labId` 완화가 계약 파괴일 가능성이 높다. ⓑ는 목록(전 연구실)과 검색(한 연구실)의 범위가 갈린다. ⓒ는 연구실 1개인 환경에서만 참이고, 2개 이상이면 뒤진 범위를 거짓으로 말해 `product.md:79` 를 어긴다.
  - 구현 메모: 요청은 `labId` 와 운영자 표식 중 정확히 하나(oneOf)로 받는다. 응답은 `CurrentAccountV2` 선례(`fe-core.yaml:4145-4165`)처럼 변형 스키마로 둘지 oasdiff 실측으로 정한다 `[미확인]`.
- Q2 운영자 결과 카드에 연구실 이름을 표시하나 → A 표시 (권장안 수용)
  - 권장 근거: 전 연구실 결과에서 소속이 없으면 같은 이름의 자료를 구분할 수 없다. `SearchResultRow` 두 번째 객체의 선택 속성으로 더한다(`fe-core.yaml:5456-5459`). 이름은 core-api 가 D1 에서 붙인다.
  - 반대 사유(기록): 카탈로그 행 `DatasetRow`(`fe-core.yaml:5214-5223`)와 카탈로그 화면에는 연구실 이름이 없어 두 화면이 달라진다.
- Q3 `X-CoLAB-Target-Lab` 으로 한 연구실로 좁히는 선택을 포함하나 → A 이번 범위 밖 (권장안 수용)
  - 메모: 운영자가 지금 이 헤더를 보내면 요청 세션만 좁혀진다(`kernel/scope.py:127-134`). 분모·실행(`catalog.py:473`·`:520`)은 전 연구실로, 카드 조립(`:560`)은 한 연구실로 돌아 적중이 조용히 빠진다(`:563-565`). 후속 과제로 남긴다.
- Q4 다른 연구실 비공개 자료의 노출 규칙 → A 목록·상세와 같은 규칙 — 운영자에게는 열린다(승인 intent 2026-09-16-admin-full-access.md 의 「시스템 관리자는 모든 자료 본체 접근」 그대로 · 새 규칙 없음) (권장안 수용 · 2026-09-25 Ted 정정 확인)
  - 근거: `kernel/scope.py:61-62` → `0033_admin_body_access.py:10` → `d2_access.py:72`·`:184` — 운영자 `bodyAccessible=true`. 「잠금 카드」로 읽지 않는다(Ted 확인).
- Q5 dev 임시 우회(dev 운영자 계정에 lab_id 지정) → A 하지 않음 (권장안 수용)
  - 근거: 재시드 최종화가 운영자 무소속을 검사한다(`dev-package/tools/dev-reseed/accounts.py:61` `labless operator mismatch`). 소속을 지정하면 그 연구실이 `current_lab` 으로 심겨(`kernel/scope.py:58-59`) 전 연구실 관찰이 왜곡된다.
- Q6 응답 `scope.labId` 를 어떻게 바꾸나(nullable 로 완화 / 운영자용 변형 스키마) → A 운영자용 응답 변형 스키마를 따로 둔다 — `CurrentAccountV2`(`fe-core.yaml:4145-4165`) 선례. 기존 `AiSearchScope` 는 그대로 → 계약 파괴 아님 (권장안 수용)
  - 요청 쪽은 `RequestedScope` 에서 `labId` 와 운영자 표식 중 정확히 하나(oneOf)로 받는다(요청 완화·선택 추가 · 비파괴).
- Q7 운영자의 조건 검색(검토된 근거 대조)을 살리나 → A 살린다 — `d3_search_evidence` 에 운영자 읽기 정책(`operator_read`) 을 더하는 platform migration 1건을 이번 범위에 넣는다 (권장안 수용)
  - 근거: `0031_search_evidence.py:47-53` 에 `operator_read` 정책이 없어 무소속 운영자의 조건 검색 후보가 0건이 된다. 정책은 읽기 전용이고 비운영자 규칙은 바뀌지 않는다.

## 미해결 질문
- 없음

## 범위 밖 (명시 제외)
- `X-CoLAB-Target-Lab` 으로 운영자 검색을 한 연구실로 좁히는 선택과 그 세 스코프 정합 수정(Q3)
- 카탈로그 목록(`GET /datasets`)의 연구실 이름 열 추가와 운영자 연구실 필터
- 교수 관리자·일반 구성원의 검색 범위 변경(자기 연구실 유지)
- 운영자 쓰기 권한·감사 체계 변경(승인 intent 2026-09-16 범위 유지)
- AI 해석·사전 확장 로직, 순위(`ts_rank_cd`) 규칙 변경
- dev 계정 소속·재시드 도구 변경

## 확인
- 프론티어 공집합 확인: 2026-09-25
- Ted 확인 문장(원문 그대로): "확인" (2026-09-25 · 설계트리 Q1~Q7 답은 같은 날 선택지 응답)
- 재개봉 금지: 아니오

## 참조
- 기획 원본: 해당 없음(운영 결함 이슈 #158 에서 출발)
- 코드: `services/core-api/src/colab_core/app/routes/catalog.py:459-501`·`:615`·`:689` · `services/ai-service/src/colab_ai/app/main.py:334-370` · `services/ai-service/src/colab_ai/domains/d10_ai_services.py:141-211` · `services/core-api/src/colab_core/app/relay.py:409-432`
- spec: `dev-package/prd/specs/admin-role-scope.md`(승인 · 시스템 관리자 = service_operator · `X-CoLAB-Target-Lab` `:25`)
- 선행 intent: `dev-package/intent/2026-09-16-admin-full-access.md`(승인 2026-09-16) · `dev-package/intent/2026-09-12-operator-designation.md`
- 라운드 파일: 없음(신규 task 로 시작 시 `docs/development/lifecycle-evidence.md` task runtime)
- 이슈: GitHub #158 「운영자(무소속) 계정의 자료 검색이 ai-service 400(scope.labId=None) 으로 503 이 된다」
- 마이그레이션: `db/platform/versions/0032_labless_operator.py`(`d1_account.lab_id` NULL 허용) · `0029_operator_read_policy.py` · `0033_admin_body_access.py` · `0042_reconcile_admin_access.py`
- 게이트: `gates/tools/contract-breaking.sh`(oasdiff `breaking -c --fail-on ERR`)
- 결정: 〈N〉 (병합 시 기입)
