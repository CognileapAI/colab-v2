# Intent: K3 두 팔을 업로드 쪽 실제 자동 메타 축으로 다시 잰다

메타 — 발의자: agent(WU5 K3 측정 결과) · 정리: Claude(lane-worker) · 작성 2026-09-25 · 승인 **사용자 서명 2026-09-25 — ①ⓐ(정답 파일 + 동치 시험 · 점검 뒤 ①ⓑ 보류 값으로 변경 — 「서명 변경 기록」) · ① 측정 전 점검 = dev 읽기 1회(§0 가정 아님) · ② DEM · ③ 사전 등록에 추가 · ④ 범위 밖 유지.** 이 서명을 적은 커밋이 승인이다(`README.md` 「승인 = 커밋」). 2026-09-25 Fable 어드바이저 검토 반영(사실 주장은 스냅샷 v2 로 재대조).

## 문제

- 2026-09-25 WU5 K3 재측정은 후보 쪽 자동 메타를 처음으로 채운 코퍼스(period 28 · crs 24 · grid 26 · fileName 28 · variables 0)에서 돌았지만, **업로드 쪽 축은 `fileName` 하나뿐**이었다. 규칙 팔 근거 25건이 전부 `fileName` 이고, 새로 채운 period·crs·grid 는 근거로 한 번도 쓰이지 않았다. 모델 팔은 호출 38회 전부 빈 제안(침묵 38/38)이다 (`dev-package/reports/k3-lineage-probe/2026-09-25-corpus28/README.md:11-13`·`:145-147`).
- 원인은 표본이다. 업로드 축은 시험 도우미 `_upload_meta` 가 스냅샷 자식의 **파일 이름·종류·조각 수만** 옮겨 만든다(`services/core-api/tests/test_k3_candidate_recall.py:54-69`). 제품 경로는 업로드 파일에서 읽은 `format`·`variables`·`crs`·`gridDescription`·`periodStart/End` 를 싣는다(`services/core-api/src/colab_core/app/routes/ingestion.py:499-533`·`:692`·`:709`).
- 그래서 이번 측정은 「후보 쪽 축이 채워진 코퍼스」는 쟀지만 **「양쪽 축이 채워진 대조」는 재지 못했다.** K3 본래 목적(축 대조로 부모를 가리고 모를 때 침묵한다)의 판정 근거가 아직 없다. K3 플래그는 켜지 않는다.
- 대조군 ⑵ `descendants` 는 두 팔 모두 green 이지만 **5/5 전부 공허**(후보 0건)다 (`2026-09-25-corpus28/README.md:13`·`:148`). 2026-09-24 S6 도 공허 4/4 였다.

## 원한 결과 (proposed outcome)

- O1. K3 두 팔(규칙 · 규칙+모델)이 **업로드 쪽 실제 자동 메타 축**을 받아 다시 측정된다. 규칙 팔·인용 검증이 period·crs·grid 를 근거 후보로 쓸 수 있고, 모델에는 `format` 까지 제품과 같은 `UploadedFileMeta` 모양으로 간다.
- O2. 결과 JSON(후보 JSON `cases[].upload_axes`)에서 다섯 자식 모두 `file_name` 외 축이 스냅샷 v2 값과 같게 찬 것이 확인된다. 비어 있으면 측정이 아니라 준비 실패(78)다 — 아래 「78 로 치는 것」.
- O3. 대조군 ⑵ `descendants` 가 **적어도 한 자식에서 `survived` > 0** 인 채로 측정된다 — 후손이 적격 필터를 통과해 실제 후보로 모델·규칙 팔 앞에 놓인다. 불가하면(예: 후손이 `recent` 상위 20 모집단 밖) 그 사실을 측정 성립 조건에 기록한다. 나머지 자식의 공허 건수와 「왜 공허인가」(적격 필터 · 후보 선정 밖)는 군별 3수(`population`·`in_pool`·`survived`)로 드러난다. (종전 문구 「모집단 > 0」 은 2026-09-25 에 이미 참이었다 — `population` 1 인 자식 3 — 그래서 결과를 가르지 못했다.)
- O4. 판정은 J1~J9 와 2026-09-25 사전 등록의 방법 그대로 읽는다. 새 합격선을 만들지 않는다.

## 범위

- `eval/k3-lineage/lineage-cases.json` — 다섯 자식 케이스에 `upload_meta` 를 명시한다. 값은 **각 자식의 스냅샷 v2 `autometa`** 에서 온다(서명 ①). 제품 `_uploaded_file_meta` 와 같은 열쇠 이름·같은 생략 규율을 쓴다:

  | 스냅샷 `autometa` | `upload_meta.file` | 규율 |
  |---|---|---|
  | `format` | `format` | 없으면 생략 |
  | `crs` | `crs` | 없으면 생략 |
  | `grid` | `gridDescription` | 없으면 생략 |
  | `period_start`·`period_end` | `periodStart`·`periodEnd` | 없으면 생략 |
  | `variables` | `variables` | 빈 배열이면 생략(스냅샷 28건 전부 빈 배열) |
  | (`files` 의 본체 첫 파일) | `fileName`·`kind`·`partCount` | 지금 규칙 유지 — `fileName` 축의 비교 대상을 바꾸지 않는다 |

  다섯 자식의 해당 값(스냅샷 v2 · 기록용): hsr_sample · rn15_sample · pred_sample = NumPy · `WGS84 (기준 격자 파일)` · 128x128 · 2019-07-28~2024-07-09 / GK2A_NDVI_mean_202305 = GeoTIFF · `EPSG:4326` · 1280x1280 · 2023-05-01~2023-05-01 / Prediction (공간상세화) = NumPy · `WGS84 (기준 격자 파일)` · 1280x1280 · 2023-05-01~2023-05-31.
- 케이스 추가(서명 ② · 권고 DEM) — 대조군 ⑵ 가 적격 필터를 통과한 후손을 실제로 갖게 한다. `sample_limits`(자식·엣지 수)와 `test_k3_candidate_recall.py:101`·`:104` 의 고정 계수(자식 5 · 엣지 10)를 같은 커밋에서 고친다. 러너는 건수를 `sample_limits` 에서 읽는다(`eval/k3-lineage/llm_lineage_probe.py:600-606`).
- `services/core-api/tests/test_k3_lineage_probe.py:358-363` — 지금은 **모든 자식에서** 「in_pool 후손의 적격 Lv > 업로드 Lv」·「⑵ `survived` == 0」을 단언한다. DEM 케이스에서는 Aspect 적격 Lv = max(파생 1, 사람 Lv1) = 1 = 업로드 Lv 라(`d3_catalog.py:451-472`) 이 단언이 red 가 된다. 최소 변경: 「in_pool 후손마다 `적격 Lv ≤ 업로드 Lv` ⇔ 그 후손이 ⑵ 후보에 남음」(필터 일관성)으로 바꾼다 — 필터가 새는 자리를 잡는 목적은 유지하고, 같은 Lv 후손이 통과하는 것은 제품 규칙대로 허용한다. red 확인 순서는 위 시험 순서와 같다(DEM 케이스를 먼저 넣어 옛 단언의 red 를 본 뒤 단언을 바꾼다).
- `services/core-api/tests/test_k3_candidate_recall.py` — `_upload_meta` 가 정답 파일의 `upload_meta` 를 읽게 하고, **정답 파일의 `upload_meta` 가 스냅샷 `autometa` 와 한 글자도 다르지 않다**는 시험을 표식 없이 더한다(지금 `upload_level` 을 지키는 방식과 같다 · `test_k3_lineage_probe.py:22-25`).
- 시험 순서: 정답 파일에 `upload_meta` 가 없거나 스냅샷과 다르면 red 인 시험을 먼저 세워 red 를 확인한 뒤 fixture 를 채운다.
- 측정: 사전 등록 파일을 새로 만들고(아래 「판정 기준」) 커밋한 뒤, 후보 절반 `bash gates/tools/service-tests.sh core-api k3_probe` → 모델 절반 `llm_lineage_probe.py --arm both --repeats 2` 를 새 출력 경로로 돌린다. 해석기는 2026-09-25 와 같은 `services/core-api/.venv/bin/python`(`2026-09-25-corpus28/README.md:46`).

## 판정 기준 (측정 전에 다시 등록한다)

- **측정 전에 사전 등록 파일을 새로 커밋한다.** 형식·규칙은 `dev-package/reports/corpus-expansion/wu5-preregistration-2026-09-25.md` §2·§4·§5 를 그대로 옮긴다 — J1~J9 정의·계산 위치·합격선 출처, 대조군 판정(⑵·⑴′ 전건 아니면 red · ⑴·⑶ 기록), 분모가 바뀐 선을 읽는 규칙(전건 선은 전건 · J2 비율 선은 환산하지 않음 · 과거 수치는 나란히만).
- 이번 등록에 더할 것은 셋뿐이다. ⓐ 업로드 축 채움 확인(O2) · ⓑ ⑵ `survived` > 0 자식 수(O3)와 나머지의 모집단·공허 건수 · ⓒ 아래 「알고 가는 교란」의 crs 동일 문자열·GeoTIFF 형제 묶음 2건(서명 ③). 셋 다 합격선이 아니라 측정 성립 조건과 기록이다.
- 비교 기준선 = 2026-09-25 결과(`2026-09-25-corpus28/{j1,candidates,luna}-2026-09-25-corpus28.json`). 차이를 개선·악화로 읽지 않는다. 그 파일들은 고치지 않는다.
- 미달은 「불충분」이 아니라 「판정 보류 · 표본 확장」으로 적는다(`eval/k3-lineage/README.md:45-47`).

### 78 로 치는 것 (준비 실패 · 측정값 아님)

- 2026-09-25 등록 §4-5 의 78 조건 전부 — 출력 경로 존재 · 모르는 군 이름 · 자식·엣지 수 ≠ `sample_limits` · `OPENAI_API_KEY` 부재 · 후보가 계약 밖 · 그 밖 예외. `service-tests.sh` 의 78(venv·일회용 DB 기동 실패).
- **새로 더함 — 두 절반의 종료 의미가 다르다.** 이번 측정의 목적(O1)이 성립하지 않은 상태를 수치로 남기지 않는다는 뜻은 같지만, 후보 절반은 pytest 단언이라 78 을 내지 못한다.

  | 조건 | 후보 절반 (`service-tests.sh core-api k3_probe`) | 모델 절반 (`llm_lineage_probe.py`) |
  |---|---|---|
  | 자식 하나라도 `file_name` 외 업로드 축이 전부 빔 | 측정 시험 단언 실패 → exit **1** = 「측정 불성립」(판정 red 아님 · 수치 미사용) | exit **78**(준비 실패) |
  | 정답 파일 `upload_meta` ≠ 스냅샷 `autometa`(서명 ①ⓐ) | 표식 없는 동치 시험 red → 매 게이트 exit **1**(fixture 결함 · 측정 전 수정) | 해당 없음(러너는 정답 파일을 직접 대조하지 않음) |
  | 정답 파일 `upload_meta` ≠ 후보 JSON `cases[].upload_axes`(두 절반이 다른 업로드를 봄) | 해당 없음 | exit **78** |

  후보 절반의 exit 1 을 판정 red 로 세지 않는다 — 보고서에 「측정 불성립」으로 적고 원인을 고친 뒤 새 출력 경로로 다시 잰다.
- 모델 timeout·전송 예외는 78 이 아니다. J8 측정값이다. 78 뒤 자동 재시도하지 않고, 원인을 고친 뒤 새 출력 경로로 돌린다.

## 서명 항목 (사용자)

### 서명 요청 선택지

| # | 서명할 것 | 권고 | 다른 선택지 |
|---|---|---|---|
| ① | `upload_meta` 출처 = 스냅샷 v2 `autometa` | ⓐ 정답 파일에 적고 표식 없는 동치 시험으로 잠근다 | ⓑ 정답 파일에 적지 않고 `_upload_meta` 가 매번 스냅샷에서 파생 |
| ② | 추가 케이스 | **DEM**(자식 6 · 엣지 10) | Aspect(자식 6 · 엣지 11) · 둘 다(자식 7 · 엣지 11) |
| ③ | 교란 2건(crs 동일 문자열 · GeoTIFF 형제 묶음)을 사전 등록에 추가 | 추가 | 기록만(등록 밖) |
| ④ | K3 플래그 · 제품 코드 · `format` 근거 축 · 코퍼스 정본 | 범위 밖 유지 | — |

아래 ①② 는 선택의 근거다.

1. **① `upload_meta` 출처 규칙** — 권고 = 위 「범위」 표. 자식 데이터셋의 스냅샷 v2 `autometa` 를 제품 `_uploaded_file_meta` 열쇠로 옮기고, `fileName` 은 지금 규칙(본체 첫 파일)을 유지한다.
   - 대안 ⓑ = 정답 파일에 적지 않고 `_upload_meta` 가 스냅샷에서 매번 파생. 사본이 없어 어긋날 일이 없지만 정답 파일만 봐서는 업로드가 무엇이었는지 안 보인다.
   - 알고 가는 것: 이 값은 **등록이 끝난 자식의 자동 메타**다. 코드 경로상 등록은 보류 값(`held_auto_metadata`)을 `apply_autometa` 로 옮기되 사람이 고친 칸은 덮지 않는다(`ingestion.py:1003-1009` · COALESCE). 제품 업로드 메타도 같은 보류 값에서 조립된다(`ingestion.py:512-531`). 어긋날 수 있는 자리는 둘 — 사람의 수정, 등록 뒤 격자 후주입(`test_grid_postinject.py:1-14`). NumPy 자식 넷의 `crs` 는 `WGS84 (기준 격자 파일)` 이라 후자에 해당할 수 있다.
   - **측정 전 점검 또는 §0 가정(택1 · 이 서명에 포함):** 점검 = NumPy 자식 한 건(예: hsr_sample)의 업로드 보류 값(`held_auto_metadata`)과 그 데이터셋의 `d3_dataset_autometa` 를 대조한다. 이 점검은 dev 읽기 1회가 필요해 아래 「제약」(dev 무접촉)의 예외로 따로 승인받아야 한다. 승인이 없으면 **§0 가정**으로 적는다 — 「업로드 순간의 헤더 판독 = 등록 후 `autometa`」. 가정 아래 결과는 「등록 후 자동 메타를 업로드 축으로 쓴 측정」으로만 읽고, 보고서 첫 줄에 이 가정을 적는다.
2. **② 추가할 케이스** — 스냅샷 v2 를 대조한 사실부터 적는다.
   - 기존 다섯 중 셋(hsr_sample · rn15_sample · GK2A_NDVI_mean_202305)은 **이미 후손이 있다**(⑵ `population` 1). 공허의 원인은 둘로 갈린다 — GK2A_NDVI 는 **적격 필터 「부모 Lv ≤ 업로드 Lv」**(`in_pool` 1 · `blocked_by_level` 1), hsr·rn15 는 **모집단 밖**(`not_in_pool` 1). 후손은 모두 Lv2 이고 자식은 Lv1 이다(`2026-09-25-corpus28/candidates-2026-09-25-corpus28.json` `groups.descendants`).
   - 스냅샷 v2 전체에서 적격 필터를 통과하는 후손 엣지는 **DEM→Aspect 하나뿐**이다(DEM Lv1 · 부모 0 · 후손 Aspect Lv1·Prediction (공간상세화) Lv2). 부모 있는 자식 13건 중에는 0건이고, DEM 은 부모가 0 이라 지금 표본(부모 있는 자식만) 밖이었다.
   - 러너·시험의 부모 0 케이스 수용(2026-09-25 대조):
     - 러너 — 받는다. `edge_hits` 는 정답 0건이면 빈 목록(`llm_lineage_probe.py:140-143`), 건수 대조는 `len(c['parents'])` 합이라 빈 배열이면 엣지 0 으로 센다(`:599-607`).
     - `test_k3_candidate_recall.py` — 받는다. 무결성 대조는 부모 수 0 = 0 으로 통과(`:83-89`), 측정 시험은 `parents` 빈 목록으로 기록(`:163-170`). 고정 계수 `:101`·`:104` 만 고친다(위 「범위」).
     - `test_k3_lineage_probe.py` — **받지 않는다.** `:358-363` 이 모든 자식에서 ⑵ `survived` == 0 을 단언한다. 최소 변경은 위 「범위」의 필터 일관성 단언이다(이 intent 범위).
   - 권고 = **DEM(Lv1 · 부모 0 · 후손 Aspect Lv1) 추가 — ⑵ descendants 가 처음으로 실제 시험된다**(자식 6 · 엣지 10 · 엣지 불변). Aspect 가 DEM 업로드의 `recent` 상위 20 모집단(`test_k3_lineage_probe.py:159-171`)에 드는지는 측정 전 확인할 수 없다 — 2026-09-25 다섯 자식의 후보 축 기록에는 모두 있었다. 빠지면 O3 불가로 기록한다.
   - 권고의 예상 결과(판정 방법은 바꾸지 않는다): DEM 과 Aspect 는 crs(`EPSG:4326`)·grid(1280x1280)·period(2023-05-01) 셋이 같다 → 규칙 팔이 ⑵ 에서 Aspect 를 제안할 공산이 크고, 사전 등록대로 읽으면 ⑵ red 다. Aspect 는 본군에도 적격으로 들어간다. DEM 은 정답 0 이라 본군 제안은 전부 비부모 — J2 엣지에 기여 0, J4 오답 칸으로 간다. DEM 의 형제는 같은 Lv 전체로 넓혀 뽑혀(`test_k3_lineage_probe.py:96-99`) 후손 Aspect 가 ⑶ 에도 섞인다 — ⑶ 은 기록 군이라 판정은 안 바뀌고 보고서에 적는다.
   - 대안 Aspect(Lv1 · 주입력 DEM · 후손 Prediction (공간상세화) Lv2 · 자식 6 · 엣지 11) — 러너·시험 변경 없이 들어가지만 ⑵ 는 적격 필터에서 빠지는 1건이 늘 뿐이다. 이 경우 보고서 첫 줄 문장은 「부모 있는 자식 중 ⑵ 통과 후손 0 · DEM→Aspect 만 예외」다.
   - 코퍼스에 같은 Lv 후손을 새로 싣는 것은 스냅샷·재시드 정본 변경이라 이 intent 의 범위 밖이다(별건).

## 영향 범위

- 사용자 / 화면: 0건.
- 서비스 · 스키마 · 계약: **제품 코드 0건.** 바뀌는 것은 eval fixture(`eval/k3-lineage/lineage-cases.json`)와 측정 시험(`services/core-api/tests/test_k3_candidate_recall.py` · `test_k3_lineage_probe.py` 의 ⑵ 단언(서명 ② DEM 일 때)과 필요 시 업로드 축 단언)·러너의 78 조건(`eval/k3-lineage/llm_lineage_probe.py`) 뿐이다. 판정 함수(`judge`·`_group_judgement`·`citation_errors`)는 바꾸지 않는다.
- 계약 파괴 여부: 아니오(계약 무변경).

## 알고 가는 교란 (측정 전 고정 · 스냅샷 v2 `counts` 와 데이터셋 행에서 확인)

- **variables 0/28** — 변수 축은 이번에도 어느 쪽에서도 근거가 될 수 없다(`autometa_fill.variables` 0 · `variable_rows` 0). 후보 중 variables 가 찬 것은 시험 시드 `DSA1`·`DSA2` 뿐이다(`2026-09-25-corpus28/README.md:75`).
- **계보 method 전부 빈 값** — `edges_with_method` 0 · 정답 파일 `method` 전부 null. 가공 방식은 판정 근거가 아니다.
- **CRS 빈 값 4건** — SPI-4weeks · SPEI-4weeks · HLS S30 T51SYB 변환 결과 · HLS S30 T52SCE 변환 결과. 이들이 후보면 crs 축은 「안 맞음」이 아니라 「근거 없음」이다(`services/core-api/src/colab_core/domains/d3_lineage_signals.py:15-16`).
- **주입력 부모 없는 Lv1 5건** — HLS_S30_NDVI_mean_202305 · DEM · LULC_2023 · SPI-4weeks · SPEI-4weeks. 계보가 등록되지 않은 Lv1 이라, 이들이 후보로 올 때 「부모 아님」이 정답 파일로 보장되지 않는다. 규칙 팔 ⑴′ red 해석에 섞인다 — 2026-09-25 ⑴′ 누수 2건 자체는 이 5건이 아니라 Lv0 원자료(HSR 레이더합성 · GK-2A LST)의 `fileName` 토큰 공유였다(`2026-09-25-corpus28/README.md:100-102`·`:146`). 업로드 period 가 들어오면 이 2건이 갈리는지가 이번 측정에서 볼 것 중 하나다.
- CRS 정규화는 좁다(EPSG 표기만 모은다 · `d3_lineage_signals.py:38-40`). `WGS84 (기준 격자 파일)` 과 `EPSG:4326` 은 같은 값으로 접히지 않는다. 기록만 하고 정규화를 넓히지 않는다(제품 코드 변경 · 범위 밖).
- `format` 은 모델에 가는 파일 메타에는 실리지만 **근거 축이 아니다** — 근거 축은 period·crs·grid·variables·fileName 다섯뿐이다(`d3_lineage_signals.py:8-12`·`:26-27` · 계약 `ParentCandidateSuggestion.evidence`). 규칙 팔·인용 검증에서 format 근거는 나올 수 없다.
- **crs 동일 문자열(서명 ③ · 사전 등록 추가)** — `WGS84 (기준 격자 파일)` 이 28건 중 12건(NumPy 9 · Binary 2 · NetCDF 1)에 글자 그대로 같다. NumPy 11건 중 나머지 2건(HLS S30 변환 결과 둘)은 crs 빈 값이다. NumPy 안에서 crs 축은 가르는 힘이 없다 — hsr_sample · rn15_sample · pred_sample 정답 엣지의 crs 일치는 부모 고유 신호가 아니다.
- **GeoTIFF 형제 묶음(서명 ③ · 사전 등록 추가)** — GK2A_NDVI_mean_202305 · HLS_S30_NDVI_mean_202305 · DEM · Aspect · LULC_2023 다섯이 `EPSG:4326` · 1280x1280 을 공유하고, LULC_2023(2023-01-01) 외 넷은 period 2023-05-01 까지 같다. GK2A_NDVI · DEM 케이스의 대조군 ⑶ 에서 형제 적중(참인 인용의 비부모)을 예상한다.
- **정답 엣지 10 의 축 일치**(업로드 = 자식 `autometa` · 제품 비교 규칙 `d3_lineage_signals.py:223-231`) — grid 7/10(불일치 3: hsr_sample 128x128↔2881x2305 · rn15_sample 128x128↔2049x2049 · GK2A_NDVI 1280x1280↔900x900) · crs 5/10(NumPy 사슬 5 엣지 일치 · Prediction (공간상세화) 5 엣지는 `WGS84 (기준 격자 파일)`↔`EPSG:4326` 불일치) · period 9/10(LULC_2023 만 안 겹침). 검토 의견의 「정답 부모 격자 대부분 불일치 → 근거는 period·fileName 위주」는 v2 대조로 성립하지 않는다 — 격자 불일치는 3/10 이다.
- 표본이 작다(자식 6~7 · 엣지 10~11 · 서명 ② 에 따름). 보고서 첫 줄에 적는다.

## 제약

- 정답(부모 엣지)·골든·스냅샷 v2 는 바꾸지 않는다. 바꾸는 것은 업로드 쪽 입력, 케이스 1~2건 추가(서명 ②), 그에 따른 시험 계수·⑵ 단언뿐이다.
- 모델은 `gpt-5.6-luna` · timeout 8.0 · `--repeats 2` · 프롬프트·파서·검증기 hash 를 2026-09-25 와 대조한다(`2026-09-25-corpus28/README.md:37-39`).
- dev·S3 에 닿지 않는다. 후보 절반은 일회용 DB, 모델 절반은 로컬 러너다. 게이트에서 모델을 부르지 않는다.
- legacy 대장·세션·결정번호를 새로 만들지 않는다(`AGENTS.md`).

## 범위 밖 (명시 제외)

- **K3 플래그를 켜는 것.** 이 측정 결과와 무관하게 이 intent 는 플래그를 켜지 않는다 — 켜는 판정은 결과를 본 뒤 별건이다.
- 제품 코드(후보 선정·적격 필터·신호·CRS 정규화·프롬프트) 변경.
- 근거 축에 `format` 추가(계약 enum 변경).
- 코퍼스·스냅샷·재시드 정본 변경(같은 Lv 후손 케이스를 만들기 위한 데이터 추가 포함).
- E-04 화면 복원(판정문 ㉮).

## 미해결 질문

- ~~서명 ①~④~~ → 2026-09-25 서명 완료(아래 「서명 기록」). ① 은 dev 읽기 1회 점검을 골랐다 — 점검에서 보류 값 ≠ `d3_dataset_autometa` 이면 재등록 전에 멈추고 보고한다.
- `eval/k3-lineage/README.md` 의 모델 절반 해석기(`services/ai-service/.venv/bin/python`)가 `python-multipart` 부재로 import 실패한다 — 이번 측정은 core-api venv 로 돈다. README 정정은 이 intent 와 같이 할지 별건일지 미정(`2026-09-25-corpus28/README.md:165`).

## 확인

- 프론티어 공집합 확인: —
- 사용자 확인 문장(원문 그대로): — 원문은 오케스트레이터 대화에 있고 이 커밋에는 옮겨 오지 않았다. 아래 서명 기록은 전달된 서명 항목만 적는다.
- 재개봉 금지: 아니오

### 서명 기록 (사용자 · 2026-09-25)

| # | 서명 | 따르는 일 |
|---|---|---|
| ① | ⓐ — `upload_meta` 를 정답 파일에 적고 표식 없는 동치 시험으로 잠근다 | `lineage-cases.json` `cases[].upload_meta` · `test_k3_candidate_recall.py` 동치 시험 |
| ① 점검 | dev 읽기 1회 — 업로드 하나의 보류 값(`held_auto_metadata`)과 같은 데이터셋의 `d3_dataset_autometa` 대조(`begin read only; … rollback;`) | 다르면 재등록 전에 멈추고 보고 |
| ② | DEM 추가(자식 6 · 엣지 10) · `test_k3_lineage_probe.py:358-363` 을 「적격 Lv ≤ 업로드 Lv ⇔ ⑵ 후보에 남음」으로 바꾼다 | `sample_limits` · `test_k3_candidate_recall.py` 고정 계수 |
| ③ | 교란(crs 동일 문자열 12건 · GeoTIFF 형제 묶음 · 정답 엣지 축 일치 grid 7 · crs 5 · period 9 / 10)을 사전 등록에 넣는다 | 새 사전 등록 파일 |
| ④ | K3 플래그 · 제품 코드 · `format` 근거 축 · 코퍼스 정본 — 범위 밖 유지 | — |

### 서명 변경 기록 (사용자 · 2026-09-25 · ① 점검 결과 뒤)

① 점검(`dev-package/reports/corpus-expansion/wu5-k3-held-autometa-check-2026-09-25.md`)에서 보류 값과 `d3_dataset_autometa` 가 period · variables 에서 갈렸다. 사용자가 ① 을 아래와 같이 바꿨다. 위 서명 기록의 ①ⓐ 행은 이 변경으로 대체된다.

| # | 서명 | 따르는 일 |
|---|---|---|
| ① (변경) | ⓑ — `upload_meta` 출처 = 제품이 **제안 시점에 가진 보류 자동 메타**(`held_auto_metadata` · `file.format-detected`·`file.header-parsed` 페이로드). 등록 후 `d3_dataset_autometa` 가 아니다 | 나머지 5 자식의 보류 값을 dev 에서 읽기 전용 1회로 읽고, 같은 읽기에서 `d3_dataset_autometa.updated_at`·이력으로 `autometa.period` 의 출처를 확정한다 |
| ① 고정 파일 | 읽은 값을 새 고정 파일(`eval/k3-lineage/fixtures/held-upload-meta-2026-09-25.json`)에 적고, 동치 시험의 기준을 스냅샷 `autometa` 에서 이 파일로 옮긴다 | 정답 `upload_meta` = 보류 값. 스냅샷 값은 민감도 입력 파일(ⓐ)에만 남긴다 |
| ① 보류 사건 없음 | 보류 사건이 없는 자식은 러너 78 을 유지하고 건수를 기록한다 | 사전 등록 · 보고서 |
| ⓒ | 폐기(기간만 빼는 혼합안) | — |
| 민감도 | 「상한 민감도」 실행을 더한다 — 모델 절반만 1회, **같은 후보 JSON** 에 ⓐ(스냅샷 `autometa`) 값, 별도 출력 경로, 모델 호출 약 40회. **합격선이 아니다** | 해석: ⓑ 침묵 · ⓐ 발화 → 입력 빈곤 / 둘 다 침묵 → 모델·프롬프트 |
| ② 읽기 | DEM ⑵ 의 Aspect 잔존은 구조 누수가 아니다(제품 적격 규칙 Lv1 ≤ Lv1 · 새 필터 일관성 단언이 잠금). ⑵ 는 등록대로 red 로 두되 원인 칸은 「축 대조가 부모/후손 방향을 못 가름」 | DEM→Aspect 형제 적중(⑶)을 교란에 더한다 |
| 사전 등록 첫 줄 | hsr 점검 표(period · variables 불일치)와 표본(자식 6 · 엣지 10 · crs 는 12 데이터셋에서 가르는 힘 없음) | 새 사전 등록 파일 |

## 참조

- 측정 결과: `dev-package/reports/k3-lineage-probe/2026-09-25-corpus28/README.md`
- 사전 등록(방법의 원본): `dev-package/reports/corpus-expansion/wu5-preregistration-2026-09-25.md`
- 스냅샷: `eval/k4-search/fixtures/reference/dev-data-snapshot-v2.json`(`counts.autometa_fill` · `datasets[].autometa` · `datasets[].parents`)
- 선행 intent: `dev-package/intent/2026-09-24-k3-lineage-suggestion-resume.md`(J1~J9) · `dev-package/intent/2026-09-24-k3-abstention-by-structure.md`(대조군 · J3'·J4'·J5')
- 업로드 메타 조립(제품): `services/core-api/src/colab_core/app/routes/ingestion.py:499-533` · 계약 `contracts/seams/core-ai.yaml` `UploadedFileMeta`
