# Intent: 초안 검색 사실의 실히트 계측과 회차 승격·폐기
메타 — 발의자: Ted · 정리: Claude(researcher, 읽기 전용 대조) · 작성 2026-09-21 · 승인 **승인 2026-09-25 (Ted, 「다 권고대로」)**

**판정 결과(2026-09-25, Ted):** 아래 7개 결정 전부 권고대로(결정 7 은 재검토에서 추가). 판정문의 길 A = 경로 1, 길 B = 경로 2 다. 원문 그대로 —
> 다 권고대로
>
> 초안 사실 승격 판정(2026-09-25):
> 1. 실험실(오프라인) 먼저
> 2. 길 A·길 B 두 경로를 따로 집계
> 3. 승격 2케이스·2회차, 폐기 3회차 0점, 역전 즉시
> 4. 초안은 파일로만 보관
> 5. 규칙 단위 지름길, 두 경로 역전 0 조건, 가공 여부 규칙은 미측정·보류
> 6. 회차 intent + 기존 검토 경로
> 7. dev 적재와 같은 payload로 일회용 DB

## Ted 요구(2026-09-21, 원문 그대로)
> 실제로 얼마나 히트했냐를 측정하고 이에 따라 승격 또는 폐기하는 구조를 가져야한다. (온톨로지를 만들때 이를 검토하는 형태)

## 문제
- 규칙으로 추론한 검색 사실(platform·representation·directObservation·interpolated, 보조로 bbox→region)은 정본 축자가 아니라 규칙 ID 가 근거다. 이 값이 맞는지 확인할 자리가 지금 없다.
- **행 하나가 상태 하나다.** `db/platform/schema.sql:836` file_id ulid PRIMARY KEY, :841 status 는 **행 단위**다. 한 파일이 reviewed 사실과 draft 사실을 동시에 가질 수 없다. 행을 통째로 draft 로 내리면 정본전재 사실까지 검색에서 사라진다.
- 그래서 구현 레인(5d65a9b5..868a96bc)은 규칙 추론 110칸을 **DB 에 아예 쓰지 않는다**. `dev-package/tools/dataset_evidence_apply.py:3-6` 축자 — 「초안(규칙 추론) 사실은 쓰지 않는다 … 이 스크립트는 draft_withheld 로 그 칸 수만 보고한다」, :83 report["draft_withheld"] += len(row.get("draftFacts") or {}). 110칸은 생성물 payload 의 draftFacts·draftProvenance(`dev-package/tools/dataset_evidence_backfill.py:382-383`)에 rule:<ID> locator 를 달고만 있다.
- 이 사실이 draft 로 남으면 조건 검색은 그것을 **읽지 않는다**. `services/core-api/src/colab_core/domains/d3_client_search.py:89` 축자 — WHERE e.dataset_id=d.id AND e.status='reviewed' AND e.file_revision=f.content_revision. LLM 해석 경로도 같다 — `app/search_evidence_conditions.py` 는 사람이 확인한(reviewed) 사실만 받는다(아래 현재 상태 1b). 즉 초안은 두 경로 어디서도 검색을 바꾸지 않고 조용히 묵힌다.
- 반대로 reviewed 로 올리면 검증 없이 후보 집합·순위를 바꾼다. 현재 생성기는 규칙값까지 포함해 전부 `dev-package/tools/dataset_evidence_backfill.py:378` 에서 "status": "reviewed" 로 적는다 — 규칙 등급과 정본전재 등급이 저장 상태에서 구별되지 않는다.
- **승격·폐기를 판단할 계측이 0 이다.** 사용자 질의·히트를 남기는 표가 스키마에 없다(아래 현재 상태 2). 지금 상태로는 「얼마나 히트했나」에 답할 수 없다.
- 검토·release 경로도 아직 열려 있다. `dev-package/prd/rounds/R-KNOWLEDGE-LIFECYCLE.md:53` 미체크 — 「개별 제안의 조회·검토·승인·거절을 수행할 운영 진입점과 인증·감사 기록을 동결한다」, 같은 파일 :189·:191 도 미체크다.

## 현재 상태 (path:line 으로 확인한 사실만 · 기준 develop 67a03a05)

### 1. 사실 저장·상태 전이
- 표: `db/platform/schema.sql:835` CREATE TABLE d3_search_evidence, :836 file_id PK, :841 status text NOT NULL CHECK (status IN ('draft','reviewed')), :853 d3_search_evidence_review_pair CHECK — reviewed 면 reviewed_by·reviewed_at 필수, draft 면 둘 다 NULL. 파일당 1행(file_id PK)이고 revision 이 1씩 오른다.
- 쓰기: `services/core-api/src/colab_core/domains/d3_search_evidence.py:70` save(...) — expected_revision·expected_file_revision 낙관적 잠금, :25 reviewed_at=CASE WHEN :status='reviewed' THEN now() ELSE NULL END.
- 계약·라우트: `services/core-api/src/colab_core/app/routes/search_evidence.py:99` status: Literal["draft","reviewed"], :128 PUT /datasets/{datasetId}/files/{fileId}/search-evidence. 권한은 _require_upload_edit + require_body_access.
- 화면: `frontend/src/components/detail/SearchEvidenceEditor.tsx:303` 「초안 저장」(save('draft')), :304 「확인하고 저장」(save('reviewed')), :74 상태 라벨 draft=초안 / reviewed=확인됨 / stale.
- **감사 기록 없음.** d3_operator_audit(`db/platform/schema.sql:1634`)은 있으나 routes/search_evidence.py·domains/d3_search_evidence.py 어디도 이 표에 쓰지 않는다(grep operator_audit 무매치). 상태 전이는 revision·reviewed_by·reviewed_at·updated_at 만 남는다.

### 1b. 두 번째 소비 경로 — LLM 해석
- 검색 진입 `services/core-api/src/colab_core/app/routes/catalog.py:442` POST /dataset-searches. :507 client_search.plan_query 가 알아들은 질의(recognized)는 **경로 1** = `d3_client_search.candidates`(catalog :683)로 간다.
- 못 알아들은 질의는 :512 `request.app.state.searches.interpret(...)`(LLM 해석)를 거친다. 답이 isDataQuery·terms 를 내면 :551 criteria = `search_evidence_conditions.parse(query)`, :552 `d3_search_evidence.read_reviewed(...)` 로 읽은 행 중 topic 이 맞는 것을 :564 `search_evidence_conditions.candidates(criteria, relevant, body_ids)` 에 넘긴다 — **경로 2**.
- `services/core-api/src/colab_core/app/search_evidence_conditions.py:1` docstring 축자 — 「Conservative condition checks over current, accessible, human-reviewed facts」. 입력은 reviewed 사실뿐이다(`domains/d3_search_evidence.py:38` WHERE e.status='reviewed').
- 경로 2 는 경로 1 에 없는 성분을 읽는다 — parse 가 :37 criteria['directObservation'], :40 criteria['interpolated'] 를 세우고, 판정이 :74 directObservation · :76 interpolated 사실값을 표시·대조한다. **interpolated 는 경로 1 술어에 없고 경로 2 에서만 읽힌다.**
- :106 candidates() 는 criteria 에 directObservation·nativeResolutionM·quality 가 있으면 :117 에서 제외(excluded) 판정을 건너뛴다 — 부분 주석으로 부재를 단정하지 않는다. 즉 경로 2 에서 이 성분은 후보를 **넣을** 수만 있고 빼지 못한다.
- 주의: criteria 는 LLM 출력이 아니라 질의 원문의 결정적 parse 다(:13 parse). LLM 이 정하는 것은 경로 2 진입 여부(isDataQuery·terms)와 answer['topic'] 이다.

### 2. 「receipt」 라고 불리는 것들 — 질의 로그가 아니다
- d3_search_selection_receipt(`db/platform/schema.sql:2094`) = (lab_id, binding_id, selector_version) 3열. **온톨로지 바인딩의 선택기 버전**이지 사용자 질의 기록이 아니다.
- d3_search_concept_match(`db/platform/schema.sql:1890`) = 바인딩별 개념 매칭(concept_id·quote·terms). 릴리스된 온톨로지의 파생 사실이며 질의별 기록이 아니다.
- d3_client_search.candidates 가 만드는 receipt(`services/core-api/src/colab_core/domains/d3_client_search.py:113`)는 {file_id, revision, file_revision, modified} 의 **응답 payload** 다. 저장되지 않는다. :118 current_receipts() 는 그 값을 되돌려 받아 아직 유효한지 다시 확인할 뿐이다.
- d3_search_refresh_run(:1910)은 새로고침 작업의 리스·상태이고, d3_search_change(:1713)·d3_search_fact_snapshot(:1784)은 온톨로지 파이프라인 쪽이다.
- **결론: 질의·히트 로그 표가 없다.** CREATE TABLE 전체에서 log/query/telemetry/event 계열은 d5_pipeline_event(:1265) 뿐이고 검색과 무관하다.
- LLM 호출 원장 d10_model_call(`db/ai/schema.sql:260`)은 call_site('search.interpret')·provider·model·outcome 을 남기지만 질의 원문·file_id·술어 열이 없다 — 히트 신호로 쓸 수 없다.

### 3. 오프라인 계측 자산은 이미 있다
- `eval/k4-search/measure_evidence.py` — 같은 DB·같은 트랜잭션에서 **after** 를 재고, 근거·topic·source_label 을 지운 **before** 를 잰 뒤 :96 session.rollback()(:86 apply_scope, :81 인자 없으면 78). 반사실(counterfactual) 측정 패턴이 이미 구현돼 있다. 1회용 DB 전용이라고 :11 에 못박혀 있다.
- 케이스셋: `eval/k4-search/golden-cases.json`(scope/required/mode), `eval/k4-search/practitioner-conditions.json`(사례별 probes: conditions·expectSeq·forbidSeq), `eval/k4-search/heldout-cases.json`.
- 채점: `eval/k4-search/golden_baseline.py:58` assess() — scope 로 거른 뒤 required 가 scoped 의 부분집합이면 pass, :71 required_ranks 로 순위도 남긴다.
- 술어 정본: practitioner-conditions.json 의 predicateSource 축자 — 「d3_client_search.py::candidates 가 받는 술어만 쓴다. 그 밖은 ValueError 다.」 — 받는 술어는 16개(`d3_client_search.py:49-85`). 그중 maxMissingRatePercent(0043)는 d3_dataset_variable 을 읽어 근거 사실과 독립이다 — 기여 측정 대상에서 제외하고, 그 술어를 쓰는 probe 3건(practitioner-conditions.json)도 제외한다.
- 적재 도구: `dev-package/tools/dataset_evidence_apply.py`(멱등, --reviewer <ULID>, --dry-run).

### 4. 온톨로지 회차가 판정을 적는 법
- `dev-package/intent/2026-09-18-practitioner-cases-ontology.md:2` 메타에 「승인 2026-09-18 (Ted, 「다 권고대로」)」, :4 「**판정 결과(2026-09-18, Ted):** 아래 8개 결정 전부 권고대로.」 — 번호 매긴 결정 목록에 Ted 판정을 원문으로 덧붙이는 형식이다. 회차를 두 번 연 근거도 「2026-09-18 Ted 판정」으로 같은 파일에 적었다(:6).

## 두 계측안 비교

### (A) OFFLINE — 오라클 질의셋에 대한 반사실 측정 (권고)
- **입력이 두 갈래다**: reviewed 사실은 **DB**(d3_search_evidence)에서, draft 사실은 **생성물 payload**(dataset_evidence_backfill.py 산출 JSON 의 draftFacts)에서 읽는다. draft 는 DB 에 없으므로 DB 만 읽어서는 잴 수 없다.
- **무엇을 재나**: 일회용 DB 의 트랜잭션 안에서 payload 의 draftFacts 를 해당 file_id 의 facts 에 **겹쳐 쓴 뒤**(reviewed 사실 + 초안 사실 합본) 케이스를 전량 평가하고, 초안 사실을 하나씩(또는 규칙 ID 단위로) 빼며 재평가한다. 끝나면 rollback — 영속화하지 않는다(`eval/k4-search/measure_evidence.py:80-96` 과 동일 골격).
- **두 경로를 따로 잰다(판정 2).** 경로 1 = plan_query → `d3_client_search.candidates`. 경로 2 = LLM interpret → `search_evidence_conditions.candidates`. 경로 2 는 interpret 출력(isDataQuery·terms·topic)을 **녹화한 픽스처로 고정**하고 criteria 는 질의 원문 parse 로 재현한다 — 측정 중 모델을 부르지 않는다.
- **「히트」 정의**: 경로마다 케이스가 golden_baseline.assess 기준 pass 이거나(= required 가 scoped 의 부분집합) practitioner-conditions.json 의 probe 가 expectSeq 를 모두 포함하고 forbidSeq 를 하나도 포함하지 않으면 그 경로에서 그 케이스는 green. **기여(contribution)** = 그 사실을 지우면 green→fail 로 뒤집히는 케이스 수(경로별). **역전(reversal)** = 지웠을 때 fail→green 으로 바뀌는 케이스 수(경로별). 기여표 열 = green_with_A/green_without_A · green_with_B/green_without_B · reversal_A · reversal_B(A=경로 1, B=경로 2). 순위만 떨어지는 경우는 별도 열(rank_delta)로 적고 기여로 세지 않는다.
- **닿는 자리**: 새 파일 `eval/k4-search/measure_draft_contribution.py`(신규), 읽기 전용 소비 = 생성물 payload(draftFacts·draftProvenance)와 `eval/k4-search/golden-cases.json`·`eval/k4-search/practitioner-conditions.json`·`eval/k4-search/golden_baseline.py:58`, 경로 2 판정 `services/core-api/src/colab_core/app/search_evidence_conditions.py:106`(읽기 전용 호출), 적재 `dev-package/tools/dataset_evidence_apply.py`, 대상 표 d3_search_evidence(트랜잭션 안에서만 수정 후 rollback — `eval/k4-search/measure_evidence.py:80-96` 과 동일 패턴).
- **제품 변경**: 없다. 라우트·계약·스키마·프론트 모두 그대로다.
- **프라이버시·RLS**: 일회용 DB 에 dev 실적재와 같은 payload 를 올려 쓴다(결정 7) — 근거 543행 · topic 3 · source_label 9 · draft_withheld 110, payload sha256 은 측정 시점에 산출물에 적는다. dev DB 에 직접 대지 않는다. 실 사용자 질의를 다루지 않으므로 연구실 경계 노출이 없다. apply_scope/read_only_scope 로 기존 평가와 같은 주체 범위에서 돈다.
- **계약 변경**: 없다.
- **한계**: 오라클 질의셋이 곧 모집단이다. 케이스가 없는 술어는 영원히 기여 0 으로 나온다 — 「기여 0 = 폐기」를 곧바로 적용하면 미측정을 무가치로 오판한다(위험 절 참조).

### (B) ONLINE — 실제 질의 receipt 에 매칭 근거를 기록
- **무엇을 재나**: 실 사용자 질의마다 어떤 근거 행·술어가 맞았는지 남기고, 같은 질의를 초안 포함으로 한 번 더 평가(shadow)해 초안이 추가로 끌어온 자료를 기록한다.
- **「히트」 정의**: 질의 결과 목록에 어떤 자료가 들어갔고 그 자료가 들어간 이유가 특정 file_id·revision·술어였다는 사실. 「좋은 히트」인지는 알 수 없다 — 사용자 선택·다운로드 같은 후속 행동을 추가로 남겨야 비로소 품질 신호가 된다(현재 그런 표도 없다).
- **닿는 자리**: 신규 표(예: d3_search_query_receipt + d3_search_match_row) → `db/platform/schema.sql` + 새 리비전 `db/platform/versions/00NN_*.py`, RLS 정책 2개, `services/core-api/src/colab_core/domains/d3_client_search.py:26`(candidates 가 매칭한 술어·file_id 를 되돌려 주도록 확장) + :89·:126·:137 세 곳의 status='reviewed' 조건을 shadow 경로에서 완화, `services/core-api/src/colab_core/app/routes/catalog.py:442`·:683(기록 지점), 계약 `contracts/seams/fe-core.yaml`.
- **프라이버시·RLS**: 질의 원문은 사용자가 쓴 자유 문장이다. 연구실별 격리(lab_id=current_lab_id())가 필수이고, 보존 기간·삭제 경로·삭제 연쇄(`services/core-api/src/colab_core/app/routes/deletion.py`)까지 같이 정해야 한다. 회차 검토용 집계는 연구실을 가로질러 봐야 하는데 그것은 RLS 를 넘는 조회다 — 별도 승인 범위가 필요하다.
- **계약 변경**: 있다(응답에 매칭 근거를 실으면 파괴 아님, 새 조회 API 는 새 계약).
- **위험**: shadow 평가가 status='reviewed' 조건을 우회하는 코드 경로를 제품에 들인다. 플래그가 새면 초안이 실제 결과를 바꾼다.

### 권고
**(A) 먼저.** 이유: 지금 질의 로그가 하나도 없어 (B) 는 표·RLS·계약·보존정책을 새로 세워야 첫 숫자가 나오는데, (A) 는 measure_evidence.py 의 기존 패턴과 이미 있는 두 오라클 케이스셋만으로 제품 변경 0 으로 첫 표를 낸다. (B) 는 실사용 질의가 쌓이고 (A) 의 「케이스 없는 술어」 사각이 실제 문제로 드러난 뒤에 연다.

## 원한 결과 (proposed outcome)
- 규칙 추론 사실 하나하나에 대해 「이 사실이 없었으면 몇 건의 합격 사례가 빠졌나」를 경로 1·경로 2 **따로 숫자로** 낼 수 있다.
- 온톨로지 보강 회차마다 그 숫자를 담은 「초안 사실 검토 표」가 나오고, 기계는 승격·폐기를 **제안만** 하며 Ted 가 판정한다.
- 판정 결과가 d3_search_evidence.status 변경으로 실제 반영되고, 되돌릴 수 있다.

## 승격·폐기 정책 (제안 — 결정 대기)
- **승격 제안 기준**: 서로 다른 green 케이스 **N=2** 건 이상에 기여 + 서로 다른 회차 **2** 회 이상에서 같은 방향 → draft → reviewed 제안.
- **폐기 제안 기준**: 회차 **K=3** 연속 기여 0 **이고** 그 술어를 건드리는 케이스가 1건 이상 존재(= 측정은 됐는데 안 맞았다) → 폐기 제안. 케이스가 0건이면 「미측정」으로 분류하고 폐기 제안하지 않는다.
- **역전 신호**: 사실을 지웠을 때 green 이 **늘어나면**(잘못된 값이 정답을 밀어냄) 회차 수와 무관하게 즉시 폐기 제안한다.
- **판정 주체**: 기계는 제안만. Ted 가 온톨로지 회차에서 다른 결정과 같은 방식으로 판정한다(`dev-package/intent/2026-09-18-practitioner-cases-ontology.md:4` 형식).
- **승격의 실제 동작**: payload 의 draft 사실을 **reviewed 행의 facts 에 병합**해 기존 PUT 로 저장한다. PUT 은 facts 를 **통째로 교체**한다 — `services/core-api/src/colab_core/domains/d3_search_evidence.py:28` facts=CAST(:facts AS jsonb), 라우트는 `routes/search_evidence.py:99` EvidenceWrite 전체 본문을 받는다. 함의: ㈀ 승격 요청은 「기존 reviewed 사실 전부 + 승격 사실」을 항상 같이 보내야 한다. 빠뜨린 성분은 조용히 사라진다. ㈁ 멱등이 아니다 — 같은 내용을 다시 보내도 `d3_search_evidence.py:27` revision=revision+1 로 리비전이 오르고 reviewed_at 이 갱신된다. 따라서 승격기는 보내기 전에 현재 facts 를 읽어 비교하고, 같으면 보내지 않는다(`dev-package/tools/dataset_evidence_apply.py` 의 멱등 판정과 같은 방식). ㈂ 감사는 reviewed_by·reviewed_at 뿐이므로 회차 intent 가 사실상의 원장이다.
- **기록 위치**: 하나, 회차 intent 파일의 「판정 결과」 절에 사실별 승격/폐기와 근거 숫자. 둘, 실제 반영은 기존 PUT /datasets/{id}/files/{id}/search-evidence(`services/core-api/src/colab_core/app/routes/search_evidence.py:128`) 로 status 변경 — 새 경로를 만들지 않는다.
- **되돌림**: 폐기는 행 삭제가 아니라 reviewed → draft 강등으로 한다. d3_search_evidence 는 파일당 1행이라 값 자체는 덮이므로, 회차 표(JSON 산출물)에 직전 facts·revision·source_sha256 을 같이 적어 원복 근거로 남긴다. 규칙 추론값은 dataset_evidence_backfill.py 가 정본에서 다시 만들 수 있다.

## 권고하는 첫 증분
1. `eval/k4-search/measure_draft_contribution.py` 신규 — 일회용 DB(reviewed 사실) + 생성물 payload 의 draftFacts 를 입력으로 받아, 트랜잭션 안에서 draft 를 facts 에 겹쳐 쓰고 케이스 전량을 경로 1·경로 2 로 따로 평가, 규칙 ID 단위·사실 단위로 하나씩 빼며 재평가, 마지막에 rollback. DB 에 초안을 영속하지 않는다.
2. 산출물: 사실별 {dataset_seq, file_id, predicate, rule_id, green_with_A, green_without_A, green_with_B, green_without_B, reversal_A, reversal_B, flipped_case_ids, rank_delta, 제안} 표(JSON) + 사람이 읽는 「초안 사실 검토 표」.
3. `eval/k4-search/README.md` 에 실행 명령 한 줄 추가, 온톨로지 회차 절차에 「이 표를 첨부한다」 한 줄.
4. 제품 코드·스키마·계약은 건드리지 않는다.

## 완료 정의
- measure_draft_contribution.py 가 종료코드 0 으로 표를 내고, 인자 없으면 78 로 끝난다(`eval/k4-search/measure_evidence.py:81` 와 같은 관례).
- 단위 시험 `eval/k4-search/test_measure_draft_contribution.py` 가 「기여 있는 사실 1건·기여 0 인 사실 1건·역전 1건」을 고정 픽스처로 판별한다.
- 실주행 후 DB 에 남은 변경이 0 이다(측정 전후 d3_search_evidence 의 (revision, status, source_sha256) 집합 동일).
- 경로 1 술어가 있는 규칙 4개(platform-from-instrument · representation-from-shape · direct-observation-from-level · bbox-korea-peninsula)의 경로별 기여 합계가 표에 있다. interpolated-from-lineage 는 「경로 1 미측정 · 경로 2 만 측정」으로 표기한다 — interpolated 는 경로 1 술어에 없고 경로 2(`search_evidence_conditions.py:40`·:76)에서만 읽힌다. 결정 5 의 규칙 단위 심사가 이 숫자로 선다.
- 회차 intent 에 붙일 표 1부가 dev 실적재와 같은 payload(근거 543행 · topic 3 · source_label 9 · draft_withheld 110)로 채워져 있고, 그 payload 의 sha256 이 표에 적혀 있다.
- 승격 리허설: 규칙 1개를 병합한 PUT 본문을 만들어 「기존 reviewed 사실이 하나도 빠지지 않는다」를 대조한다(전체 교체 API 이므로).

## 게이트
- python3 -m unittest discover -s eval/k4-search -p 'test_*.py'
- services/core-api/.venv/bin/python eval/k4-search/run_regression.py
- python3 eval/k4-search/golden_baseline.py --output <새 경로> — 측정 전후 동일함을 대조
- CI search-golden 잡(경로 정본 `.github/workflows/ci.yml` 의 같은 이름 필터) — eval 경로 변경이 걸린다
- 제품 코드를 건드리지 않으므로 core service-tests·schema-diff·rls-coverage 는 이 증분의 선언 대상이 아니다. (B) 로 가면 그때 선언한다.

## Ted 결정 (번호)
1. **오프라인 먼저인가?** 권고 = (A) 오프라인 반사실 측정부터. (B) 온라인 질의 receipt 는 이번 회차에서 열지 않는다. — 수용 / 반대
2. **「히트」의 정의.** 권고 = 경로 1(plan_query → d3_client_search.candidates)과 경로 2(LLM interpret → search_evidence_conditions.candidates, interpret 출력은 녹화 픽스처로 고정)를 **따로 집계**하고, 경로마다 green 케이스의 **뒤집힘**(pass→fail)만 기여로 센다. 순위 변화는 기록만 하고 승격 근거로 쓰지 않는다. — 수용 / 반대
3. **임계값.** 권고 = 승격 N=2 케이스 그리고 2 회차, 폐기 K=3 회차 연속 기여 0 그리고 해당 술어 케이스 1건 이상, 역전은 즉시 폐기 제안. — 수용 / 다른 값 지정
4. **초안 사실이 장기적으로 어디에 살 것인가.** 행 단위 status 때문에 지금은 DB 에 자리가 없다.
   - ㈎ **payload·eval 파일에만 둔다** — 제품 변경 0. 승격기는 payload 를 읽어 PUT 으로 병합한다. 한계 = 연구실 사용자가 초안을 볼 수 없고 화면 편집기와 무관하다. **(첫 증분 권고)**
   - ㈏ **사이드카 표** `d3_search_evidence_draft(file_id, facts, provenance, rule_id, round)` — 부모와 같은 RLS(lab_id=current_lab_id()), reviewed 행을 건드리지 않고 초안을 영속한다. 비용 = 새 리비전·RLS·삭제 연쇄·계약.
   - ㈐ **facts jsonb 안에 성분별 status** — 계약(SearchEvidenceFacts) 변경이고, 조건 검색이 성분마다 status 를 걸러야 해서 `services/core-api/src/colab_core/domains/d3_client_search.py:49-85` 의 술어 SQL 전부가 바뀐다. 가장 비싸다.
   — ㈎ / ㈏ / ㈐
5. **1회차 fast-track 을 쓸 것인가.** 권고 = **쓴다.** Ted 는 110행이 아니라 **규칙 4개**(platform-from-instrument · representation-from-shape · direct-observation-from-level · interpolated-from-lineage)와 보조 1개(bbox-korea-peninsula)를 심사하고, 규칙 단위로 승격·보류한다. 규칙 승격 조건 = **경로 1·경로 2 모두 역전 0** 이고 기여 ≥1. interpolated-from-lineage 는 「미측정(경로 1)·보류」로 고정한다. 근거 = 110칸은 전부 이 5개 규칙의 기계적 적용이고 규칙 ID 가 provenance 에 남아 있어(`dev-package/tools/dataset_evidence_backfill.py:357`) 규칙이 옳으면 그 산출도 옳다. 측정표는 같은 회차에 규칙별 기여 합계를 함께 낸다. 규칙별 예외(정본이 규칙과 어긋나는 건)만 행 단위로 뽑아 따로 본다. — 수용 / 반대(110행 전수 심사)
6. **판정의 기록 자리.** 권고 = 회차 intent 파일의 「판정 결과」 절 + 기존 PUT 경로로 status 변경. 새 승인 API·새 원장 표는 만들지 않는다. — 수용 / 반대
7. **측정 픽스처.** 권고 = dev 에 적재한 것과 **같은 payload** 를 일회용 DB 에 올려 잰다. payload sha256 을 산출물에 적는다. 측정은 일회용 DB 에서만 하고 dev DB 에 직접 대지 않는다. — 수용 / 반대

## 위험
- **오라클 과적합**: 골든·실무자 케이스에 맞춰 사실을 승격하면 케이스가 곧 정답이 된다. 완화 = heldout-cases.json 을 승격 판단에서 제외하고 사후 확인용으로만 쓴다.
- **미측정을 무가치로 오판**: 해당 술어를 부르는 케이스가 0 건인데 기여 0 이라고 폐기하면 정본에 근거가 있는 값을 버린다. 완화 = 폐기 기준에 「케이스 1건 이상」 조건을 넣었다(결정 3).
- **승격 전까지 사용자 눈에는 후퇴(dev 실상태 기준)**: dev(f0be4268→67a03a05)에는 근거 543행이 reviewed 로 적재됐고 LLM 해석(경로 2)도 켜져 있다. 그러나 규칙 추론값(draft_withheld 110)은 적재되지 않아 platform·directObservation 축은 두 경로 모두 0건이다. 초안이 DB 에 없으니 이 축은 승격 전까지 0 건이다. 즉 이 intent 를 미루면 회복이 아니라 현상 유지가 손실이다. 완화 = 결정 5 의 규칙 단위 fast-track 으로 1회차 안에 닫는다.
- **초안이 조용히 순위를 바꾸는 것**: (B) 의 shadow 플래그가 새면 미검토 값이 실제 결과에 섞인다. 완화 = 이번 증분에서 제품 경로를 열지 않는다.
- **측정이 DB 를 더럽힘**: `eval/k4-search/measure_evidence.py:11-12` 축자대로 1회용 DB 전용이며 운영·DEV 제품 DB 에 대고 돌리지 않는다. 완화 = 완료 정의에 「남은 변경 0」 대조를 넣었다.
- **감사 공백**: 상태 전이에 d3_operator_audit 기록이 없어 누가 왜 승격했는지가 reviewed_by·reviewed_at 뿐이다. 이번 증분 범위 밖이지만 `dev-package/prd/rounds/R-KNOWLEDGE-LIFECYCLE.md:53` 의 미체크 항목과 같은 구멍이다.
- **동시 편집 충돌**: `dev-package/tools/dataset_evidence_backfill.py`·eval/k4-search 전반·contracts 를 다른 에이전트가 지금 고치는 중이다. 이 문서의 path:line 은 develop 67a03a05 기준이며 착수 전 재확인이 필요하다.

## 설계트리 (grill-me 결과)
- Q1 「히트」를 순위 개선까지 포함해 셀까? → A 아니다. 케이스 정의가 required ⊆ scoped 뿐이라(`eval/k4-search/golden_baseline.py:68`) 순위에 임계값을 세울 근거가 없다. required_ranks(:71)는 기록만 한다. (권장안 수용)
- Q2 기여를 사실 단위로 잴까, 규칙 단위로 잴까? → A 둘 다. 승격·폐기의 단위는 사실(행·술어)이지만 규칙 ID 별 합계가 있어야 「이 규칙 자체가 쓸모없다」를 판단할 수 있다.
  - Q2a 규칙 ID 는 어디서 오나? → A `dev-package/tools/dataset_evidence_backfill.py:357` 의 draft_provenance[key] = "규칙 · rule:<id> · ..." 문자열. 현재 DB 의 facts jsonb 에는 provenance 가 들어가지 않으므로 측정기는 생성기 산출물 JSON 을 같이 읽는다.
  - Q2b provenance 를 DB 에 넣을까? → A 이번 증분에서는 넣지 않는다. 계약(SearchEvidenceFacts 15종, `contracts/seams/fe-core.yaml:5879`)과 서버 검증을 바꿔야 하고 오프라인 측정에는 불필요하다.
- Q3 초안을 reviewed 로 올린 상태를 어떻게 만들까? → A 트랜잭션 안에서 UPDATE ... SET status='reviewed' 후 측정, 끝나면 rollback. `eval/k4-search/measure_evidence.py:80-96` 과 같은 골격이다. (권장안 수용)
- Q4 새 표를 만들어 회차별 기여 이력을 쌓을까? → A 아니다. 회차마다 JSON 산출물 파일을 남기고 회차 intent 가 그것을 참조한다. 표를 만들면 RLS·삭제·마이그레이션이 붙는데 아직 지속 계측이 필요하다는 근거가 없다.
- Q5 폐기를 행 삭제로 할까? → A 아니다. reviewed → draft 강등으로 한다. 삭제는 되돌릴 근거를 같이 지운다.

## 영향 범위
- 사용자 / 화면: 없다. SearchEvidenceEditor.tsx 는 그대로다.
- 서비스 · 스키마 · 계약: 없다. 신규는 eval/k4-search 안의 스크립트와 시험뿐이다.
- 계약 파괴 여부: 아니오.

## 제약
- 「정본에 없으면 만들지 않는다」(PLAN-SoT §9-㊴-②) — 측정은 값을 새로 짓지 않고 기존 생성기 산출물만 재료로 쓴다.
- 술어는 d3_client_search.candidates 가 받는 것만 쓴다. 그 밖은 ValueError(`services/core-api/src/colab_core/domains/d3_client_search.py:83-85`). 경로 2 는 `search_evidence_conditions.candidates` 가 받는 criteria 만 쓴다.
- 1회용 DB 전용. 운영·DEV 제품 DB 금지(결정 7 — dev 적재와 같은 payload 를 일회용 DB 에 올린다).
- 경로 2 측정은 모델을 부르지 않는다. interpret 출력은 녹화 픽스처로 고정한다.

## 미해결 질문
- 실사용 질의 로그를 언제 열 것인가(= (B) 의 착수 조건). 현재는 「(A) 에서 케이스 없는 술어가 실제 불만으로 드러날 때」로만 적어 둔다.
- 사용자 만족 신호(선택·다운로드)를 남길지 여부. 지금 스키마에 자리가 없다.

## 범위 밖 (명시 제외)
- 실 사용자 질의·히트의 영속 기록, 그 표의 RLS·보존·삭제 정책.
- d3_client_search 의 shadow 평가 플래그, 제품 검색 경로 변경.
- d3_operator_audit 에 근거 상태 전이를 남기는 일(별건, R-KNOWLEDGE-LIFECYCLE.md:53).
- 승인·거절 전용 운영 UI·API(R-KNOWLEDGE-LIFECYCLE.md:189·:191).
- 온톨로지 개념·동의어 자체의 승격·폐기(이 문서는 d3_search_evidence 사실만 다룬다).
- facts jsonb 에 provenance·규칙 ID 를 싣는 계약 확장(결정 4-㈐ 가 채택되면 그때 연다).
- 사이드카 표 d3_search_evidence_draft 의 구현(결정 4-㈏ 가 채택될 때만).

## 확인
- 프론티어 공집합 확인: 미실시
- Ted 요구 문장(2026-09-21, 원문 그대로): "실제로 얼마나 히트했냐를 측정하고 이에 따라 승격 또는 폐기하는 구조를 가져야한다. (온톨로지를 만들때 이를 검토하는 형태)"
- Ted 확인 문장(2026-09-25, 원문 그대로):
> 다 권고대로
>
> 초안 사실 승격 판정(2026-09-25):
> 1. 실험실(오프라인) 먼저
> 2. 길 A·길 B 두 경로를 따로 집계
> 3. 승격 2케이스·2회차, 폐기 3회차 0점, 역전 즉시
> 4. 초안은 파일로만 보관
> 5. 규칙 단위 지름길, 두 경로 역전 0 조건, 가공 여부 규칙은 미측정·보류
> 6. 회차 intent + 기존 검토 경로
> 7. dev 적재와 같은 payload로 일회용 DB
- 재개봉 금지: 아니오

## 참조
- 기준 커밋: 67a03a05 (develop)
- LLM 호출 원장: `db/ai/schema.sql:260` d10_model_call — 질의 원문·file_id·술어 없음 → 히트 신호 불가
- 선행 회차 intent: `dev-package/intent/2026-09-18-practitioner-cases-ontology.md`, `dev-package/intent/2026-09-18-dataset-metadata-backfill.md`
- 라운드 파일: `dev-package/prd/rounds/R-KNOWLEDGE-LIFECYCLE.md`, `dev-package/prd/rounds/R-AI-SEARCH-FACTS.md`
- 결정: 〈N〉 (병합 시 기입)

## 판정 결과 — 1회차(2026-09-26)

**오라클 복원 판정(2026-09-26, Ted, 원문 그대로):**
> 전부 권고대로

- 권고 = 2회차(d533d374)가 거두거나 바꾼 1회차 probe 11건을 `eval/k4-search/practitioner-conditions.json` 의 사례별 `measureOnlyProbes`(`"mode": "measure_only"` · 「초안 값 측정 전용 · 정답 주장 아님」)로 되살린다. 조건 검색 pytest 는 이것을 green 으로 세지 않고, 측정기는 이것을 공식 오라클로 쓴다. heldout 은 계속 판정에서 뺀다.
- PC-1-4 「5 km 이하」는 1회차 기대(seq 3 포함)를 `supersedes` 로 되살렸다. 2회차가 seq 3 을 forbidSeq 로 옮긴 것은 seq 3 의 해상도(native-resolution-carried)를 초안으로 내린 결과이지, seq 3 이 5 km 를 넘는다는 정본 주장이 아니다. 측정에서는 1회차 기대가 그 probe 를 대신한다. 그래서 첫 측정의 역전 1건(PC-1-4#p5)은 **probe 산물**이었고, 대체 뒤 역전은 0 이다.

**측정:** `dev-package/reports/evidence-promotion/round-1-2026-09-26/` — payload sha256 `27c6ed87c178a8b6bcd686b7c55ad86391c659668e1888f1dbc789c7ff9192ca`(dev 적재본 · 근거 543 · topic 3 · source_label 9 · draft_withheld 110) · 일회용 DB · 평가 118회 · 모델 호출 0 · 측정 전후 지문 543행 동일. 경로 1 28케이스 green: 초안 포함 28 / 제외 17. 경로 2 10케이스: 9 / 9.

| 규칙 | 초안 | 경로 1 기여 / 역전 | 경로 2 기여 / 역전 | 제안 |
|---|---:|---|---|---|
| platform-from-instrument | 26 | 8 / 0 (PC-1-2 m1–m3 · PC-1-3 m1–m2 · PC-2-2 m1–m2 · PC-2-3 m1) | 0 / 0 · 미측정(술어 없음) | **승격 제안** — 규칙 단위 fast-track(결정 5: 두 경로 역전 0 · 기여 ≥1) |
| direct-observation-from-level | 26 | 2 / 0 (PC-1-6 m1–m2) | 0 / 0 · 미측정(케이스 0) | **승격 제안** — 규칙 단위 fast-track(결정 5) |
| representation-from-shape | 28 | 0 / 0 · 미측정(케이스 0) | 0 / 0 · 미측정(술어 없음) | 미측정 · 보류 |
| interpolated-from-lineage | 28 | 0 / 0 · 미측정(술어 없음) | 0 / 0 · 미측정(케이스 0) | 보류 — 결정 5 고정(heldout N23 사후 확인 기여 1, 판정에 안 씀) |
| bbox-korea-peninsula | 0 | 초안 0건 | 초안 0건 | 초안 0건 |
| (결정 5 목록 밖) native-resolution-carried | 1 | 2 / 0 (PC-1-4 m1 · PC-2-2 m2) | 0 / 0 | 기계 제안은 승격 — 이 회차 판정 목록 밖이라 별도 판정 대기 |
| (결정 5 목록 밖) region-from-registration-note | 1 | 0 / 0 · 미측정(케이스 0) | 0 / 0 · 측정(4) | 보류 — 기여 0 |

**승격 적용 계획:** `dev-package/reports/evidence-promotion/round-1-2026-09-26/promotion-plan/apply-plan.md`. 두 규칙 52칸을 `facts` 로 옮긴 승격 payload(sha256 `724dcbd6ad56ff0330df1e550dbb54d203bd5705bc3181cd68ddd858708c1941`)를 기존 적재기(`dataset_evidence_apply.py`, `--reviewer <ULID>`)로 싣는다. 순서 = 되돌림 스냅숏 → dry-run → 적용 → 멱등 재확인. 되돌림은 원본 payload 재적재. 일회용 DB 리허설: PUT 본문 541건 계약 검증 · reviewed 사실 누락 0 · 적재 dry-run evidence 541 / unchanged 2 · 재실행 0 / 543.

~~**dev 반영은 별도 GO 대기다.** 이 회차는 dev 에 아무것도 쓰지 않았다.~~ → 아래 「승격 판정(2026-09-26)」으로 GO.

**승격 판정(2026-09-26, Ted, 원문 그대로):**
> 전부 권고대로

- ① dev 반영 GO ② 결정 5 목록 밖이던 native-resolution-carried 도 승격 — **승격 규칙 3개**(platform-from-instrument · direct-observation-from-level · native-resolution-carried) ③ 공용 AI 게이트 DB(`colab_ai_applied_30`) 재구성 승인 — 별도 레인 몫(이 회차는 손대지 않는다).
- 세 규칙 승격 payload sha256 `41f488a42ffb07c1c64d4460ea86a6b98c72b63494ec45291f72f5c73561c6fc`(53칸 이동 · 두 규칙판 `724dcbd6…` 대체). 일회용 DB 리허설: PUT 본문 541건 계약 검증 · reviewed 사실 2071 → 2071 · 승격 추가 1083 · 충돌·누락 0 · 적재 dry-run evidence 541 / unchanged 2 · 적용 뒤 재실행 0 / 543. 계획 = `promotion-plan/apply-plan.md`.
