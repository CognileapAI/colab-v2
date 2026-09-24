# Intent: K3 계보 제안을 재개한다 — 후보는 core-api 가 고르고 luna 는 순위·근거만 붙인다

메타 — 발의자: Ted(2026-09-24 「권고대로 하자」) · 정리: Claude(researcher) · 작성 2026-09-24 · 승인 **㈎-1·㈏ 두 판정만 「권고대로 2026-09-24 Ted」 · 그 밖의 항목(계약 개정 서명 · 화면 복원 · 합격선 수치 · 플래그 기본값)은 미승인**

## 문제

- 계보 제안 표면(`suggestLineage`)은 계약·서버·중계가 다 서 있는데 **참인 답이 언제나 0건**이다. 생산자가 `suggestions=[]` 를 고정으로 낸다 (`services/ai-service/src/colab_ai/app/main.py:221-227`).
- 0건의 이유가 「없더라」가 아니라 **「물어볼 재료를 못 받았다」**다. 계약 `LineageSuggestionRequest` 에 부모 후보를 실을 자리가 없고, 이 배포 단위는 카탈로그(D3)에 붙지 않는다 (`services/ai-service/src/colab_ai/app/main.py:4-10` · `services/ai-service/src/colab_ai/domains/d10_suggestion.py:15-19` · `services/ai-service/src/colab_ai/kernel/config.py:7-10`).
- 막혀 있던 것은 구현이 아니라 판정이었다 — `dev-package/sessions/K3-BUILD.md §7` 의 ㈎(요청 본문의 정본) · ㈏(후보를 누가 고르는가) · ㈐(평가셋). 2026-09-24 에 ㈎-1 과 ㈏ 가 풀렸다.
- 화면 쪽은 별건이다. E-04 의 AI 제안 영역은 2026-09-14 에 프런트에서 걷혔고(`frontend/src/components/lineage/LineageStep.tsx:5-14`) **Ted 재판정 대기(판정문 ㉮)** 상태다 (`dev-package/prd/specs/R-A2.md:79`). 서버·계약은 존치고 부르는 자리만 없다.

## 원한 결과 (proposed outcome)

- O1. 업로드 화면이 계보 제안을 물으면 **core-api 가 D3 에서 「가공 전 데이터」 후보를 골라 요청에 실어 보내고**, ai-service 는 그 후보들만 놓고 순위·근거 한 줄·3값 확신도를 붙여 돌려준다. 후보 밖의 `parentDatasetId` 는 응답에 나올 수 없다(후보 목록에 없는 ID 를 core-api 가 버린다).
- O2. **모를 때는 빈 제안이 정상 응답이다.** 후보가 0건이면 `degraded: false` + `suggestions: []`(살펴봤는데 없더라), 모델이 못 답하면 `degraded: true` + 사유. 지금의 세 영(零) 상태 구분(`services/core-api/tests/test_lineage_suggestions.py:215-260`)을 깨지 않는다.
- O3. ㈐ — ㈎㈏ 구현 뒤 **실데이터 계보 정답**으로 실측 수치가 남는다. 정답 출처는 참조 스냅샷의 `parents` 엣지다(`eval/k4-search/fixtures/reference/dev-data-snapshot.json` — 자식 4건 · 엣지 6건, `parent_dataset_id`·`parent_role`·`method` 포함).
- O4. 켜고 끄는 자리가 값으로 있다 — `query_interpretation` 과 같은 규율의 플래그 하나 (`services/ai-service/src/colab_ai/kernel/config.py:77-97`). 기본값은 끈 쪽이다.

## 영향 범위

- 사용자 / 화면: **이번 회차 0건.** E-04 는 제안을 부르지 않는다(위 `LineageStep.tsx:5-14`). 서버가 참인 제안을 내게 되어도 화면은 그대로다 — 화면 복원은 판정문 ㉮ 재판정 사항이라 범위 밖이다.
- 서비스: `services/core-api`(후보 선정 + 중계 본문) · `services/ai-service`(제안 생산자 + 배선 + 설정). DB 스키마·마이그레이션 0건. 저장 0건.
- 계약: `contracts/seams/core-ai.yaml` — `LineageSuggestionRequest` 에 **선택 필드 `candidates` 1개 추가**.
- **계약 파괴 여부: 아니오.** 다만 **계약 개정 1건이 필요하고 그것은 Ted 서명 사항이다.**
  - ㈎-1(계약이 정본 · 중계가 `UploadedFileMeta` 를 조립) 자체는 **계약 개정 0이고 이미 구현돼 있다** — 2026-08-30 정정으로 `_uploaded_file_meta()` 가 섰고(`services/core-api/src/colab_core/app/routes/ingestion.py:496-533`), 중계는 `{"scope", "file"}` 만 보낸다(`services/core-api/src/colab_core/app/relay.py:481-486`). 나가는 본문이 계약과 같은지는 이미 시험이 본다(`services/core-api/tests/test_lineage_suggestions.py:302-359`).
  - ㈏(core-api 가 후보를 골라 요청에 싣는다)는 **자리를 새로 열지 않으면 성립하지 않는다.** 현행 스키마는 `required: [scope, file]` · `additionalProperties: false` 이고 후보 필드가 없다(`contracts/seams/core-ai.yaml:182-203`), 표면도 열쇠 집합을 닫아 400 을 낸다(`services/ai-service/src/colab_ai/app/main.py:44`·`175-178`).
  - 최소 대안을 찾았으나 **없다.** ① 기존 열쇠 전용(`datasetNameDraft`·`subject`)은 후보를 실을 모양이 아니고 뜻을 비틀면 계약 산문이 거짓이 된다. ② ai-service 가 D3 를 읽는 길은 ㈏ 와 `CLAUDE.md §3-1` 위반이다(`config.py:7-10` 가 그 통로를 이미 걷어냈다). ③ 후보 없이 LLM 이 `parentDatasetId` 를 만들면 ULID 를 지어내는 것이고 `d10_suggestion._ulid` 가 막는다(`services/ai-service/src/colab_ai/domains/d10_suggestion.py:42-45`). → **선택 필드 추가가 최소안이다.** 기존 소비자는 그 열쇠를 안 보내도 그대로 200 이므로 `contract-breaking`(oasdiff) 기준의 파괴는 아니다.

## 제약

- **도메인 경계 (`CLAUDE.md §3-1`).** D3 는 core-api 의 것이다. 후보 선정·경계(RLS)·정본 이름·가공 단계는 core-api 에서 나온다. ai-service 에 카탈로그 접속을 다시 열지 않는다.
- **LLM 이 답을 고르지 않는다 (`〈72〉-㉮` 와 같은 모양).** 모델이 하는 일은 받은 후보의 순위·근거·확신도까지다. 후보 밖 ID·점수·퍼센트·순위 필드를 읽지 않는다 — `interpret.py` 의 「세 값만 읽는다」 규율(`services/ai-service/src/colab_ai/app/interpret.py:1-7`·`197-217`)을 제안에도 그대로 적용한다.
- **정직한 빈 상태 · 억지 제안 금지.** 0건은 정상 응답이다(`contracts/seams/core-ai.yaml:248-296`). 「없더라」와 「못 물어봤다」와 「닿지 못했다」를 한 값으로 접지 않는다(`services/core-api/src/colab_core/app/relay.py:310-325`·`497-518`).
- **제안은 저장하지 않는다.** `ai-no-lineage-write` 가 세 층에서 본다(`gates/tools/ai_no_lineage_write.py`). D4 쓰기는 사람이 `createDataset` 의 `lineageParents` 로만 한다.
- **확신도는 3값 enum, 근거는 필수·한 줄.** 숫자·퍼센트 금지 (`services/ai-service/src/colab_ai/domains/d10_suggestion.py:8-13`·`65-78`).
- **게이트에서 모델을 부르지 않는다.** 판정 게이트는 가짜 전송으로만 돈다. 실모델 실측은 `eval/` 러너와 측정 표식(`k4_probe` 선례 · `services/core-api/pyproject.toml:28-31`)으로 분리한다 — 표식은 게이트 선택자에 넣지 않는다.
- **모델은 luna 고정** (`PLAN-SoT §9-㊷`, 기본값 `gpt-5.6-luna` — `services/ai-service/src/colab_ai/kernel/config.py:74`·`96`). 이 회차에서 공급자·모델을 재개봉하지 않는다.
- **AI 없이도 v2 는 완결된 제품이다.** 키·플래그·후보가 없어도 업로드·등록은 그대로 돈다. 5xx 로 끝내지 않는다.
- legacy 대장(`work-items.yaml`)·세션·결정번호를 새로 만들지 않는다 (`AGENTS.md`).

## 설계트리 (grill-me 결과)

- Q1 요청 본문의 정본은 계약인가 중계인가 → **A ㈎-1 계약이 정본.** (권장안 수용 · Ted 2026-09-24) 계약 개정 0 이고 중계는 이미 그렇게 돼 있다.
- Q2 후보를 누가 고르나 → **A ㈏ core-api.** (권장안 수용 · Ted 2026-09-24) 검색 `〈72〉-㉮` 와 같은 모양이다.
  - Q2a 어느 질의로 고르나 → **A `d3_catalog.list_lineage_candidate_cores`**(`services/core-api/src/colab_core/domains/d3_catalog.py:302-326`) 재사용. `listLineageCandidates` 가 쓰는 그 함수다(`services/core-api/src/colab_core/app/routes/catalog.py:1364`·`1378`) — 사람이 고르는 후보와 AI 가 보는 후보가 **같은 모집단**이어야 한다. 새 질의를 만들면 두 벌이 갈린다.
  - Q2b 후보에 가공 단계를 실나 → **A 싣는다.** 계약이 `parentProcessingLevel` 을 optional 로 열어 둔 이유가 그것이고(`contracts/seams/core-ai.yaml:323-343`), 값의 출처는 `d4_lineage.LineageSummaryAdapter` + `d3_catalog.level_view` 다(`catalog.py:1387-1392`). **모르면 열쇠를 만들지 않는다.**
  - Q2c 후보 상한은 → **A 미해결(아래 질문 ④).** 권고 = 20건(`listLineageCandidates` 기본 limit 과 같은 값).
- Q3 ai-service 가 후보 밖 ID 를 실어 보내면 → **A core-api 가 버린다.** 범위(`scope`)를 버리는 그 자리와 같은 규율이다(`relay.py:504-510`). 신뢰하지 않는 쪽에서 거르는 것이 계약 표류를 잡는 유일한 자리다.
- Q4 제안 두 종류를 다 하나 → **A 이번 회차는 「가공 전 데이터」 하나.** 「가공 방식」(`methodText`)은 어휘가 HYD 협의 미정이고 정본에 열거값이 없다(`contracts/seams/core-ai.yaml:344-372`) — 평가 기준을 세울 수 없다.
- Q5 모델을 못 쓰는 회차에 무엇을 내나 → **A 빈 제안 + 사유.** 규칙 기반 순위를 기본 구현으로 두되 **그것을 AI 제안으로 내지 않는다** — `LiteralInterpreter` 의 「결정으로 고른 상태 ≠ degraded」 구분(`interpret.py:105-141`)을 그대로 따른다.
- Q6 프런트를 되살리나 → **A 아니오.** 판정문 ㉮ 가 대기 중이고 이 intent 는 그것을 재개봉하지 않는다.
- Q7 평가셋을 무엇으로 만드나 → **A 참조 스냅샷의 실계보.** `dev-data-snapshot.json` 의 `parents` 는 사람이 등록한 실제 엣지다(예: 「강수 — WGS84 변환·연구대상지 crop 표본 (Lv.1)」 → 주입력 `01M1SCC27AN4NZD3K978YFDCVD` · 보조입력 `01M1SCC8BZZJSCEW4MRPE4W9M8`). K4 검색 절반과 같은 일회용 DB 를 쓴다(`services/core-api/tests/test_k4_interpreter_probe.py:1-9`).

## 판정 기준 (실측 전에 못 박는다 — ㈐)

측정 대상 = 참조 스냅샷의 **부모를 가진 자식 4건 · 정답 엣지 6건**. 각 자식마다 「그 자식의 업로드 파일 메타 + core-api 가 고른 후보 목록」을 만들어 한 회차로 친다. 2회 실행한다.

| # | 항목 | 어떻게 세나 | 합격선 |
|---|---|---|---|
| J1 | 후보 포함률 (recall@k) | core-api 가 고른 후보 k건 안에 정답 부모가 들어 있는가 | **6/6.** 미달이면 모델이 아니라 **후보 선정의 결함**이다 — 모델 수치를 내기 전에 고친다 |
| J2 | 제안 적중 (hit@1 · hit@3) | 제안 목록에서 정답 부모의 순위 | 실측 전 수치를 못 박지 않는다 → **기록만.** 다만 `hit@3 < 4/6` 이면 「판정 보류·표본 확장」으로 적는다(6엣지로 승격을 결정하지 않는다) |
| J3 | 근거의 실재성 (grounding) | 각 제안의 `rationale` 에서 따온 조각이 **그 후보의 메타(이름·요약·주제·출처·격자·변수) 또는 업로드 파일 메타 원문에 문자열로 실재하는가** — 러너가 부분문자열로 기계 판정 | **위반 0건.** 후보·파일 메타에 없는 고유명사·수치가 근거에 나오면 red |
| J4 | 확신도 정직성 (calibration) | 확신도 3값 × 정오 2값 교차표 | **「확실」의 정확도 ≥ 「애매」의 정확도**. 뒤집히면 확신도가 값을 못 한다 |
| J5 | 모를 때 빈 제안 | 정답 부모를 후보에서 **일부러 뺀** 대조군 4건(자식 4건 각 1회) | **빈 제안 4/4.** 후보에 없는 것을 억지로 고르면 red — 이 항목이 「모른다고 말하는가」의 유일한 직접 측정이다 |
| J6 | 후보 밖 ID | 응답의 `parentDatasetId` 중 요청 후보 목록에 없는 값 | **0건.** 1건이라도 나오면 core-api 가 버린 건수도 함께 적는다 |
| J7 | 규격 위반 | 확신도 enum 밖 · 근거 공란/여러 줄 · 퍼센트 문자열 | **0건** (`d10_suggestion` 생성자가 이미 막지만 응답 바이트에서도 센다) |
| J8 | 지연 | 모델 왕복 초 | 제품 timeout 안. 초과 건수를 적는다 |
| J9 | 결정성 | 같은 입력 2회 | 갈린 자식 수를 **기록만** 한다(보증 대상 아님 · `〈112〉`) |

- **표본이 작다는 사실을 보고서 첫 줄에 적는다.** 자식 4건·엣지 6건이고, 후보 모집단도 9건뿐이라 dev 의 distractor 가 없다. K4 실측이 같은 한계를 안고 갔던 자리다(`dev-package/reports/k4-luna-probe/README.md`).
- 미달은 **「불충분」이 아니라 「판정 보류 · 표본 확장」**으로 적는다.

## 미해결 질문

1. **계약 개정 서명** — `LineageSuggestionRequest.candidates`(선택 · 후보 배열) 추가. 권고 = 추가한다. 이것 없이는 ㈏ 가 성립하지 않는다(위 「영향 범위」의 대안 3건 검토 결과). 서명 전까지 WU1·WU2 는 열쇠 이름을 확정할 수 없다.
2. **후보가 지고 갈 필드 집합** — 권고 = `datasetId` · `name` · `topic` · `summary` · `sourceLabel` · `processingLevel`(모르면 생략) · `periodStart`/`periodEnd`. 근거로 인용할 수 있는 값만 싣는다(J3 이 그 집합을 오라클로 쓴다). 파일 목록·변수 전체는 싣지 않는다(본문이 커지고 근거 판정이 흐려진다).
3. **자식의 가공 단계를 요청에 싣나** — 「부모 Lv ≤ 자기 Lv」는 사람이 폼에서 고른 값에 걸리는데(`LineageStep.tsx:24-28`) 그 값은 지금 중계에 들어오지 않는다. 권고 = **이번 회차엔 싣지 않는다**(계약 필드가 하나 더 늘고, 서버 400 이 최종 방어선으로 남아 있다). 대신 후보의 `processingLevel` 을 실어 사람이 화면에서 가늠하게 한다.
4. **후보 상한 k** — 권고 = 20.
5. **플래그 기본값** — 권고 = `off`. `〈136〉` 이 질의 해석에 적용한 규율(「켜는 시점을 값으로 정할 수 있어야 한다」)과 같다.
6. **화면 복원(판정문 ㉮)** — 이 intent 는 열지 않는다. 서버가 참인 제안을 내게 된 뒤 Ted 가 따로 판정한다.

## 범위 밖 (명시 제외)

- E-04 의 AI 제안 영역 복원 · 판정문 ㉮ 재개봉 · 그에 딸린 프런트 코드·시험.
- 「가공 방식」(`ProcessingMethodSuggestion`) 제안 생산 — 어휘 정본이 없어 판정 기준을 세울 수 없다.
- D9 지식 그래프를 계보 제안에 쓰는 것 — 검색 쪽 사전·그래프와 다른 축이고 이 회차의 판정 대상이 아니다.
- 모델·공급자 재선정(`PLAN-SoT §9-㊷` 재개봉) · 비용/지연 SLO 수치 · prod parity.
- 제안 결과의 저장(`ai_lineage_suggestion` 류 임시 저장소) — 이 회차는 응답과 함께 죽는다.
- dev 재시드·배포·main push.

## 확인

- 프론티어 공집합 확인: —
- Ted 확인 문장(원문 그대로): 「권고대로 하자」(2026-09-24 · ㈎-1 · ㈏ 두 항목)
- 재개봉 금지: 아니오

## 참조

- 판정 원문: `dev-package/sessions/K3-BUILD.md §7`(㈎ · ㈏ · ㈐)
- 계약: `contracts/seams/core-ai.yaml:63-96`(`suggestLineage`) · `:182-203`(`LineageSuggestionRequest`) · `:204-247`(`UploadedFileMeta`) · `:248-296`(`LineageSuggestionResponse`) · `:308-343`(`ParentCandidateSuggestion`)
- 중계·라우트: `services/core-api/src/colab_core/app/relay.py:310-325`·`453-518` · `services/core-api/src/colab_core/app/routes/ingestion.py:496-562`
- 생산자: `services/ai-service/src/colab_ai/app/main.py:157-227` · `services/ai-service/src/colab_ai/domains/d10_suggestion.py`
- 선례(같은 모양): `〈72〉-㉮` 검색 분담 · `services/ai-service/src/colab_ai/app/interpret.py`(전송·파싱·폴백 규율)
- 실측 선례: `dev-package/intent/2026-09-22-k4-luna-interpreter-probe.md` · `dev-package/reports/k4-luna-probe/README.md` · `services/core-api/tests/test_k4_interpreter_probe.py`
- 라운드 파일: `dev-package/prd/rounds/R-K3-RESUME.md`
