# K3 보류 값 재측정 — 판정 기준 사전 등록 (측정 전)

> **첫 줄 — 업로드 입력이 등록 후 자동 메타와 다르다(period · variables), 표본이 작다.** 제안 시점 보류 값에는 6 자식 모두 기간이 없고 variables 가 있으며, 등록 후 `d3_dataset_autometa` 는 6 자식 모두 기간이 있고 variables 가 비어 있다(아래 점검 표). 표본 = 자식 6 · 엣지 10. crs 축은 `WGS84 (기준 격자 파일)` 동일 문자열을 가진 12 데이터셋 안에서 가르는 힘이 없다.

| 자식 | format | crs | grid | period(보류 → 등록 후) | variables(보류 → 등록 후) | fileName |
|---|---|---|---|---|---|---|
| hsr_sample (① 점검 1건) | 같음 NumPy | 같음 | 같음 128x128 | **없음** → 2019-07-28~2024-07-09 | **["hsr_sample"]** → [] | 같음 |
| rn15_sample | 같음 NumPy | 같음 | 같음 128x128 | **없음** → 2019-07-28~2024-07-09 | **["rn15_sample"]** → [] | 같음 |
| pred_sample | 같음 NumPy | 같음 | 같음 128x128 | **없음** → 2019-07-28~2024-07-09 | **["pred_sample"]** → [] | 같음 |
| Prediction (공간상세화) | 같음 NumPy | 같음 | 같음 1280x1280 | **없음** → 2023-05-01~2023-05-31 | **["Prediction_20230502"]** → [] | 같음 |
| GK2A_NDVI_mean_202305 | 같음 GeoTIFF | 같음 EPSG:4326 | 같음 1280x1280 | **없음** → 2023-05-01~2023-05-01 | **["band1"]** → [] | 같음 |
| DEM | 같음 GeoTIFF | 같음 EPSG:4326 | 같음 1280x1280 | **없음** → 2023-05-01~2023-05-01 | **["band1"]** → [] | 같음 |

- 보류 값 출처 = dev 읽기 전용 1회(2026-09-25 · `transaction_read_only = on` · rollback · 쓰기 0) → 고정본 `eval/k3-lineage/fixtures/held-upload-meta-2026-09-25.json`. 「crs 같음」은 NumPy 넷의 `WGS84 (기준 격자 파일)` 이 보류 값에 이미 있다는 뜻이다(등록 뒤 후주입이 아니다).
- 등록 시각 = **이 파일을 처음 담은 커밋의 커밋 시각.** 이 커밋 전에 아래 §6 출력 경로의 파일은 한 건도 없다(`dev-package/reports/k3-lineage-probe/2026-09-25-held/` 디렉터리 없음). 모델 호출 0.
- 근거 intent = `dev-package/intent/2026-09-25-k3-upload-axes-remeasure.md` 「서명 변경 기록」(①ⓑ · ⓒ 폐기 · 민감도 · ② 읽기 · 첫 줄).
- **이 문서는 새 합격선을 만들지 않는다.** 형식·규칙은 `dev-package/reports/corpus-expansion/wu5-preregistration-2026-09-25.md` §1·§2·§4·§5 를 그대로 따른다(아래는 바뀐 자리와 더한 자리만 적는다).

## 0. `autometa.period` 의 출처 (같은 dev 읽기에서 확정)

- 6 자식 모두 보류 사건 `file.header-parsed` 의 `period` 가 `null` 이다. 등록 경로 `apply_autometa` 는 보류 값만 넘기고 `COALESCE` 로 빈 칸만 채운다(`services/core-api/src/colab_core/app/routes/ingestion.py` 등록 함수 ①-b · `d3_catalog._APPLY_AUTOMETA`) — 보류 값에서 기간이 올 수 없다.
- 같은 등록 트랜잭션의 ①-a `update_dataset(changes=human_metadata)` 가 기간을 쓴다(`d3_catalog.update_dataset` 의 `period` 분기). 근거 셋:
  - `d3_dataset_autometa.updated_at` = `d3_dataset.uploaded_at` = 첫 `d3_operator_audit` `dataset.updated` 시각(6/6 · 같은 `now()`). `update_dataset` 은 사람 메타가 있을 때만 불리고 그때 감사 행을 남긴다.
  - `period_granularity` 가 6/6 채워져 있다(일 4 · 월 2). 이 열은 `update_dataset` 의 `period` 분기만 쓴다 — `apply_autometa` 는 쓰지 않는다.
  - 값이 재적재 정본 `dev-package/tools/dev-seed/canonical-metadata.json` 의 start·end·granularity 와 같다. 재적재 러너가 등록 화면의 기간 입력(`dev-package/tools/dev-seed/runner.py` `fill_period`)으로 넣는다. 근거 문장은 정본의 `basis`(예: DEM 「사용자 제공 맥락; 파일 내부 날짜 없음」).
- 결론: `autometa.period` = **등록 화면에서 사람이 입력한 기간**(dev 에서는 재적재 러너가 정본 파일로 입력). 헤더에서 읽은 값이 아니다.
- 한정: 등록 뒤 감사 2건(19:28 · 21:46 · 자식 5건, DEM 은 21:46 1건)이 더 있다. 감사 스냅샷은 이름·요약·단계만 싣고 `update_dataset` 은 `autometa.updated_at` 을 올리지 않으므로, 이 둘이 기간을 **같은 값으로** 다시 썼는지는 이 읽기로 배제하지 못한다. 값이 정본과 같다는 사실은 그대로다.

## 1. 표본 · 입력 (측정 전 고정값)

| 항목 | 값 | 출처 |
|---|---|---|
| K3 정답 | 자식 6 · 엣지 10 · 후보 모집단 28 | `eval/k3-lineage/lineage-cases.json` `sample_limits` |
| 업로드 입력(정답) | 보류 값 — 6/6 이 crs · grid · variables · format 을 가짐, period 0/6 | 같은 파일 `cases[].upload_meta`(동치 = `test_k3_candidate_recall.py` `test_계보_정답의_업로드_메타가_보류_자동_메타와_같다`) |
| 보류 사건 없는 자식 | **0/6**(6 자식 모두 `file.format-detected` · `file.header-parsed` 둘 다 있음) | 고정본 `read.children_without_held_event` |
| 민감도 입력(ⓐ · 정답 아님) | 스냅샷 v2 `autometa` 사본 — period 6/6 · variables 0/6 | `eval/k3-lineage/fixtures/snapshot-autometa-upload-meta-2026-09-25.json`(동치 = `test_상한_민감도_입력이_스냅샷_자동_메타와_같다`) |
| 후보 쪽 | 스냅샷 v2 그대로(period 28 · crs 24 · grid 26 · variables 0 · fileName 28) | `eval/k4-search/fixtures/reference/dev-data-snapshot-v2.json` `counts.autometa_fill` |
| 모델 · 설정 | `gpt-5.6-luna` · timeout 8.0 · `seed 20260924` · `response_format json_object` · `temperature` 없음 | `services/ai-service/src/colab_ai/kernel/config.py:79`·`:117` · `app/suggest_wire.py:33`·`:102` |
| 해석기 | `services/core-api/.venv/bin/python`(2026-09-25 와 같음 · `dev-package/reports/k3-lineage-probe/2026-09-25-corpus28/README.md:48`) | — |

## 2. 「측정됨」 · 「측정 실패(78)」 · 「측정 불성립」

- 공통 정의는 `wu5-preregistration-2026-09-25.md` §2 그대로다. 모델 timeout·전송 예외는 78 이 아니라 J8 측정값이다. 78 뒤 자동 재시도하지 않는다.
- **두 절반의 종료 의미가 다르다**(이번 등록에서 갈라 적는다):

| 조건 | 후보 절반 (`service-tests.sh core-api k3_probe`) | 모델 절반 (`llm_lineage_probe.py`) |
|---|---|---|
| 자식 하나라도 `file_name` 외 업로드 축이 전부 빔(보류 사건 없음 포함) | 측정 시험 단언 실패 → exit **1** = 「측정 불성립」(판정 red 아님 · 수치 미사용) | exit **78** |
| 정답 `upload_meta` ≠ 보류 고정본을 제품 조립기에 통과시킨 값 | 표식 없는 동치 시험 red → 매 게이트 exit **1**(fixture 결함 · 측정 전 수정) | 해당 없음 |
| 정답 `upload_meta` ≠ 후보 JSON `cases[].upload_axes` | 해당 없음 | exit **78** |
| 민감도 입력에 자식이 빠짐 · 축이 `file_name` 뿐 | 해당 없음 | exit **78**(민감도 실행만) |

- 보류 사건 없는 자식 = 0 이므로 이번 실행에서 위 첫 줄 조건은 예상되지 않는다. 생기면 건수를 보고서 첫 줄에 적는다.

## 3. 측정 순서와 명령

1. 후보 절반(모델 호출 0 · 일회용 DB):
   `COLAB_K3_PROBE_OUT=<워크트리>/dev-package/reports/k3-lineage-probe/2026-09-25-held/j1-2026-09-25-held.json COLAB_K3_CANDIDATES_OUT=<워크트리>/dev-package/reports/k3-lineage-probe/2026-09-25-held/candidates-2026-09-25-held.json bash gates/tools/service-tests.sh core-api k3_probe`
2. 모델 절반 본측정(판정): `services/core-api/.venv/bin/python eval/k3-lineage/llm_lineage_probe.py --arm both --repeats 2 --candidates <1의 후보 JSON> --output dev-package/reports/k3-lineage-probe/2026-09-25-held/luna-2026-09-25-held.json`
3. 상한 민감도(합격선 아님 · §4): `services/core-api/.venv/bin/python eval/k3-lineage/llm_lineage_probe.py --arm model --repeats 2 --candidates <1의 후보 JSON · 2와 같은 파일> --upload-meta-override eval/k3-lineage/fixtures/snapshot-autometa-upload-meta-2026-09-25.json --output dev-package/reports/k3-lineage-probe/2026-09-25-held/luna-sensitivity-autometa-2026-09-25-held.json`

- 2·3 의 결과 JSON `candidates_sha256` 이 같아야 「같은 후보 JSON」이다. 다르면 3 은 민감도로 읽지 않는다.
- 프롬프트·파서·검증기 동일성 = 결과 JSON `system_prompt_sha256` · `suggester_sha256` · `verifier_sha256` · `signals_sha256` 을 2026-09-25 결과(`2026-09-25-corpus28/luna-2026-09-25-corpus28.json`)와 대조한다. 러너 hash 는 `--upload-meta-override` 추가로 달라진다 — 그 변경은 인자 없을 때 경로를 바꾸지 않는다(`eval/k3-lineage/test_llm_lineage_probe.py` 61건).

## 4. 상한 민감도 실행 (등록 · 합격선 아님)

- 무엇: 모델 절반만(`--arm model`), 한 번, **같은 후보 JSON** 에 업로드 메타만 ⓐ(등록 후 스냅샷 `autometa`)로 갈아 끼운다. 러너는 먼저 후보 기록의 업로드 축을 정답(보류 값)과 대조한 뒤 갈아 끼운다(`llm_lineage_probe.override_upload_meta`). 갈아 끼운 값은 모델 입력 · core-api 인용 검증 · 인용 오류 오라클이 모두 같이 본다.
- 호출 수: 본측정 모델 팔과 같은 칸(비공허 자식×군) × 2 — 약 40회. 실제 수는 결과 `model_calls` 로 적는다. 규칙 팔은 돌리지 않는다.
- 판정에 쓰지 않는다: J1~J9 · 대조군 판정을 이 실행으로 green/red 로 읽지 않는다. 결과 JSON `kind` 에 「상한 민감도 … 합격선 아님」, `upload_meta_override.sha256` 이 실린다.
- **해석 규칙(측정 전 고정)** — 칸 = (자식 · 군 · 회차). 「침묵」= 그 칸 모델 원문이 빈 배열(`raw_suggestions == 0`, 2026-09-25 보고서의 「모델 침묵」과 같은 정의). 본측정(ⓑ) 모델 팔과 민감도(ⓐ)를 같은 칸끼리 맞춘다.
  - ⓑ 침묵 · ⓐ 발화 → **입력 빈곤**(제안 시점 제품에 없는 기간 등 입력이 모델 발화를 가른다).
  - ⓑ · ⓐ 둘 다 침묵 → **모델 · 프롬프트**(입력을 채워도 말하지 않는다).
  - ⓑ 발화 → 기록(민감도가 가를 칸이 아니다).
  - 보고는 세 칸 건수와 칸 목록. 전체 결론은 칸이 한쪽으로 모일 때만 적고, 섞이면 「섞임」과 건수만 적는다.

## 5. 판정 (2026-09-25 등록 §4 그대로 · 바뀐 자리만)

- J1~J9 정의 · 계산 위치 · 합격선 출처 = `wu5-preregistration-2026-09-25.md` §4-1·§4-5(계산 함수 이름은 같다 — `judge` · `_group_judgement` · `citation_errors` · `edge_hits`. 줄 번호는 러너 변경으로 밀렸다).
- 대조군: ⑵ `descendants` · ⑴′ `removed_and_siblings` 는 빈 제안이 전건이 아니면 red · ⑴ `removed` · ⑶ `siblings` 는 기록(같은 문서 §4-3).
- 분모가 바뀐 선: 전건 선은 전건(J1 = 10/10 · J5' = 군별 자식 전건) · J2 비율 선은 환산하지 않음(descriptive only) · 과거 수치는 나란히만(같은 문서 §5).
- 미달은 「불충분」이 아니라 「판정 보류 · 표본 확장」(`eval/k3-lineage/README.md:45-47`).
- 측정 성립 조건(합격선 아님 · 기록): ⓐ 업로드 축 채움 — 후보 JSON `cases[].upload_axes` 6/6 이 `file_name` 외 축을 가짐 · 정답과 같음 / ⓑ ⑵ `survived` > 0 자식 수(예상 1 = DEM)와 나머지 자식의 `population` · `in_pool` · `survived` · 공허 건수.

### 5-1. DEM ⑵ 읽기 (측정 전 고정)

- DEM(Lv1)의 ⑵ 후보에 Aspect(적격 Lv1)가 남는 것은 **구조 누수가 아니다** — 제품 적격 규칙 「적격 Lv ≤ 업로드 Lv」(`d3_catalog.eligibility_level` · Lv1 ≤ Lv1)대로이고, `services/core-api/tests/test_k3_lineage_probe.py` 필터 일관성 단언(「적격 Lv ≤ 업로드 Lv ⇔ ⑵ 후보에 남음」)이 잠근다.
- 그래도 ⑵ 판정은 등록대로 둔다 — DEM ⑵ 에서 제안이 나오면 ⑵ **red**. 보고서의 원인 칸은 「**축 대조가 부모/후손 방향을 못 가름**」으로 적고, 러너가 계산한 누수 갈래(`leak_kind`)는 그대로 옆에 적는다.
- 예상(판정 방법은 바꾸지 않는다): 보류 값 DEM 업로드 = `EPSG:4326` · 1280x1280 · 기간 없음 → Aspect 와 crs · grid 둘이 같다. 규칙 팔이 ⑵ 에서 Aspect 를 제안할 공산이 크다.

## 6. 알고 가는 교란 (측정 전 고정)

- 2026-09-25 intent 「알고 가는 교란」 전부(variables 후보 쪽 0/28 · method 전부 빈 값 · CRS 빈 값 4건 · 주입력 부모 없는 Lv1 5건 · CRS 정규화 좁음 · `format` 근거 축 아님 · crs 동일 문자열 12건 · GeoTIFF 형제 묶음)를 그대로 싣는다.
- **정답 엣지 10 의 축 일치(업로드 = 보류 값)** — grid 7/10 · crs 5/10(종전과 같음 · 보류 값의 crs·grid 가 등록 후와 같다) · **period 0/10**(업로드에 기간 없음 · 종전 9/10) · variables 0/10(후보 쪽 0/28). 규칙 팔 근거 후보는 crs · grid · fileName 셋뿐이다.
- **업로드 variables 는 6/6 에 생겼지만 근거가 될 수 없다** — 후보 코퍼스 28건 variables 0, 일회용 DB 시험 시드 `DSA1`·`DSA2` 는 `강우량`(`services/core-api/tests/fixtures/seed.sql:63-64`)이라 업로드 값(`hsr_sample` 등 · `band1`)과 겹치지 않는다. 모델 입력에는 실린다.
- **DEM→Aspect 형제 적중(⑶ · 새로 추가)** — DEM 의 형제는 같은 Lv 전체로 넓혀 뽑혀(`test_k3_lineage_probe._siblings` `same_level`) 후손 Aspect 가 ⑶ 에도 들어간다. ⑶ 에서 Aspect 가 참인 인용(crs · grid)으로 살아남으면 형제 적중으로 기록하고, 그것이 ⑵ 와 같은 데이터셋임을 함께 적는다. ⑶ 은 기록 군이라 판정은 바뀌지 않는다.
- **dev 원장 파일 순서(기록 · 측정 입력 아님)** — 같은 dev 읽기에서 제품 `_FILES` 와 같은 정렬(`kind DESC, file_name, id`)이 NumPy 4 자식의 첫 파일을 **기준 격자 파일 `LAT_crop.npy`** 로 돌려줬다(고정본 `ledger_files.dev_order_head`). 제품 `_uploaded_file_meta` 의 「본체 우선」 주석과 다르다. 게이트 일회용 DB 와 같은 이미지(`postgres:16-alpine` · `en_US.utf8`)의 로컬 컨테이너에서는 `'기준 격자 파일' > '본체'` 가 거짓이라 본체가 앞선다. 이번 정답의 `fileName` 은 서명 ① 범위표대로 본체 첫 파일을 유지한다 — dev 에서 제품이 실제로 보낸 `fileName` 은 다를 수 있다. 제품 코드 변경은 범위 밖이다(후속).
- 표본이 작다(자식 6 · 엣지 10). 보고서 첫 줄에 적는다.

## 7. 비교 기준선 · 이번 출력(새 파일)

| 측정 | 기준선(읽기만) | 이번 출력(새 파일 · 있으면 78) |
|---|---|---|
| K3 J1 | `dev-package/reports/k3-lineage-probe/2026-09-25-corpus28/j1-2026-09-25-corpus28.json` | `dev-package/reports/k3-lineage-probe/2026-09-25-held/j1-2026-09-25-held.json` |
| K3 후보·대조군 | `.../2026-09-25-corpus28/candidates-2026-09-25-corpus28.json` | `.../2026-09-25-held/candidates-2026-09-25-held.json` |
| K3 두 팔 | `.../2026-09-25-corpus28/luna-2026-09-25-corpus28.json`(모델 침묵 38/38) | `.../2026-09-25-held/luna-2026-09-25-held.json` |
| 상한 민감도(합격선 아님) | — | `.../2026-09-25-held/luna-sensitivity-autometa-2026-09-25-held.json` |

- 기준선과의 차이를 개선·악화로 읽지 않는다 — 업로드 입력이 다르다(기준선은 `fileName` 만). 기준선 파일은 고치지 않는다.

## 8. 실행 규율

- dev · S3 에 닿지 않는다. dev 읽기는 이 등록 전의 1회로 끝났다. 게이트에서 모델을 부르지 않는다.
- 키는 프로세스 환경으로만 준다. 출력·커밋하지 않는다.
- 결과 보고서는 이 문서의 표 순서대로 적고, 등록에 없는 지표는 「사후 추가」로 표시한다.
- K3 플래그 · 제품 코드 · `format` 근거 축 · 코퍼스 정본은 범위 밖이다(intent ④).
