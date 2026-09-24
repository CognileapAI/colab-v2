# WU3 — dev 코퍼스 스냅샷 v2 재포획 (2026-09-25 · 읽기 전용)

**⛔ 계보 `method`(가공 방법)는 18간선 전부 비어 있다(0/18).** 28건 재적재는 그 칸을 기록하지 않는다 —
K3 정답(WU4)의 `method` 는 **빈 값으로 둔다**(intent `2026-09-24-corpus-expansion-dev-reseed.md` 판정 기준 3).

메타 — 가지 `corpus-wu3-snapshot`(`origin/k3-resume` `c94f198a` 위) · dev 무쓰기 · 재시드·reset 미실행.

## 1. 무엇을 잡았나

| 항목 | 값 |
|---|---|
| 도구 | `eval/k4-search/recapture_snapshot.py`(신설 · 쓰기 SQL 0줄) · 시험 `eval/k4-search/test_recapture_snapshot.py` 16건 |
| 읽기 경로 | dev 호스트의 일회용 `postgres:16-alpine` 클라이언트 → BYPASSRLS 백업 URL · `begin read only; … rollback;` · `transaction_read_only = on` 확인 |
| 대응 규칙 | `dev-package/tools/dev-seed/plan-manifest.yaml` 28 이름 → dev `d3_dataset_description.name`. 0건·2건 이상이면 준비 실패(78) |
| 포획 시각 | `2026-09-24T18:35:25Z`(UTC) |
| dev 배포 revision | `ea21d8c2aa54`(컨테이너 4종 이미지 태그 `dev-ea21d8c2aa54` 일치) |
| 산출물 ⓐ | `eval/k4-search/fixtures/reference/dev-data-snapshot-v2.json`(sha256 `db9677a0…5932`) — v1 은 **그대로 둔다**(골든 재박기가 둘 다 쓴다) |
| 산출물 ⓑ | `eval/k4-search/fixtures/reference/dev-name-id-v2.json` — 이름→데이터셋 ID 28행만(sha256 `1c315901…84c8`) |
| 결정성 | 41초 뒤 재포획 → `captured_at` 외 **완전 일치** · 대응표 바이트 일치 |

### v2 형식 (v1 열쇠 전부 유지 + 추가)
- 데이터셋 — v1 열쇠 그대로(`manifest_key` 는 `LD-*` 묶음이 없어 `null`) + `plan_seq` · `lab_id` ·
  **`processing_level`**(열 `processing_level_user_set` 원값 `Lv0`~`Lv3`) · `processing_level_derived`
  (제품 규칙 `d4_lineage._SUMMARY` 의 주입력 최대 단계 + 1 · 상한 `LV_CAP=3` · 부모 없으면 0) · `projects[{id,name}]`.
- `files[]` — v1 열쇠 + `carries_lat`·`carries_lon`. 순서 = 격자 → 본체, 파일명, id.
- `autometa` — v1 9열쇠 그대로. `variable_rows[]` — `d3_dataset_variable` 행(ordinal 순).
- `parents[]` — `parent_dataset_id`·`parent_role`·`method`. 순서 = 주입력 → 보조입력, id.
- 최상위 — `format_version: 2` · `deployed_revision` · `source` · `subject`(v1 선례대로 연구실 ID·시드 소유 계정 ID) ·
  `counts` · `projects[{id,name,datasets}]`.

## 2. 검증 (도구 판정 · exit 0)

| 검사 | 기대 | 실측 | 판정 |
|---|---|---|---|
| 데이터셋 | 28 | 28(삭제 0) | ✅ |
| 프로젝트 | precipitation · vegetation · drought · 포멧테스트 | 같은 4 · 연결 28/28 | ✅ |
| 계보 간선 | 18 | 18 · 주입력 16 · 보조입력 2 | ✅ |
| 간선 쌍(이름) | 등재표 `parents` | 일치 | ✅ |
| 보조입력 역할 | Prediction(공간상세화) ← DEM · Aspect | 일치 | ✅ |
| 자동메타 행 | 28 | 28 | ✅ |
| 가공 단계 대 등재표 | 불일치 0 | 0 · 분포 Lv0 10 · Lv1 16 · Lv2 2(등재표 동일) | ✅ |
| 데이터셋별 프로젝트 | 등재표와 동일 | 불일치 0 | ✅ |
| 본체 파일 수 | 데이터셋별 `expect_files` | 불일치 0 · 총 543 | ✅ |
| 격자 파일 부재 | 파일 자체 CRS 가 있을 때만 | 부재 8건 전부 파일 CRS 보유 | ✅ |
| 계획 밖 격자 | 0 | 0 | ✅ |

### 자동메타 fill (28건 기준)

| 축 | intent 예측 | 과제 기대 | 실측 |
|---|---|---|---|
| `period_start/end` | 28 | 28 | **28 / 28** |
| `format` | 26 | — | **26** |
| `grid` | 26 | 26 | **26** |
| `crs` | 26 | 24 | **24** |
| `variables` 배열 | 미확인 | 0(알려짐) | **0** |
| `d3_dataset_variable` 행 | 미확인 | — | **0행 · 0건** |

## 3. 이상·관찰

1. **`method` 0/18** — 위 머리말. 전 간선 `origin=manual`.
2. **`variables` 0/28 · 변수 행 0** — 알려진 사항(인계서 §4-(e)). 재시드 경로는 변수 행을 세우지 않는다.
3. **`crs` 빈 4건** — GeoPackage 2(seq 13·14 · `format`·`grid` 도 빈 값 · 예측대로) ＋
   **HLS S30 변환 결과 2(seq 23·24)**: NumPy · 격자 파일 2개 부착 · `grid 3660x3660` 은 섰는데 `crs` 만 빈 값.
   같은 흐름의 다른 npy 9건은 `WGS84 (기준 격자 파일)`. intent 예측(26)과 차이 2 의 원인은 **미확인**.
4. **등재표 격자 22건 중 8건은 격자 파일 없음**(seq 6·7·15·17·21·22·25·26) — 전부 파일 내장 CRS
   (NetCDF LCC · GeoTIFF EPSG · GRIB · HDF4 Sinusoidal). 러너 `do_grid` 의 「격자 칸 미출현 = 화면이 좌표 보유로 판정」과 일치.
   격자 파일 행 28 = 14건 × 2.
5. **파생 단계 ≠ 사람 단계 5건** — seq 8·9·11·13·14 는 등재표·열 모두 Lv1 인데 주입력 부모가 없어 파생 0.
   K3 적격 필터(`max(파생, 사람)`)에는 영향 없음. v1 처럼 이름의 「(Lv.n)」 에서 읽으면 28건 전부 실패한다(이름에 없다).
6. **`topic` 0/28 · `source_label` 0/28** — v1 9건은 둘 다 있었다. K4 설명 벡터에 주제어가 빠진다.
   `summary`·`category`·`data_type`·관측 간격은 28/28.

## 4. 이름 → 새 ID 대응표 (Ted 서명 대상 ㉮ · 28행)

기계 판독본 = `eval/k4-search/fixtures/reference/dev-name-id-v2.json`(이름·ID 만). 아래는 서명용 확장본.

| seq | 이름 | 새 ID | 프로젝트 | Lv(열) | 파생 |
|---|---|---|---|---|---|
| 1 | HSR 레이더 반사도 원자료 | `01M39T7N812JDX7GW62F8YFZ0V` | precipitation | Lv0 | 0 |
| 2 | rn15 15분 누적강수 | `01M39T979PMQKRSK3GPCNYWHH3` | precipitation | Lv0 | 0 |
| 3 | hsr_sample | `01M39TA6QY5NEAR8ZPZ6AF9KNE` | precipitation | Lv1 | 1 |
| 4 | rn15_sample | `01M39TB4NTBCFC8TSTNB93N5YP` | precipitation | Lv1 | 1 |
| 5 | pred_sample | `01M39TCARM2C2NJ8S9SA4QBSER` | precipitation | Lv2 | 2 |
| 6 | GK-2A 일 단위 식생자료 | `01M39TK0F5P3W4APB91N08KTMY` | vegetation | Lv0 | 0 |
| 7 | GK2A_NDVI_mean_202305 | `01M39TSEPR820QBZ1DBBFKDJEP` | vegetation | Lv1 | 1 |
| 8 | HLS_S30_NDVI_mean_202305 | `01M39TT0S5PSJ0DQNR0XMTHFNW` | vegetation | Lv1 | 0 |
| 9 | DEM | `01M39TTPB2T87ESQKHCZPBAKD6` | vegetation | Lv1 | 0 |
| 10 | Aspect | `01M39TVD38600D4EKH13EV55DV` | vegetation | Lv1 | 1 |
| 11 | LULC_2023 | `01M39TW21793T8631ATHJREHK5` | vegetation | Lv1 | 0 |
| 12 | Prediction (공간상세화) | `01M39TZ0SCEYHHMBWZ991M1QGN` | vegetation | Lv2 | 2 |
| 13 | SPI-4weeks | `01M39V005J6SQ9SW8MZ8D16ZWK` | drought | Lv1 | 0 |
| 14 | SPEI-4weeks | `01M39V0T17DHQ5PF5XSSERTZ8H` | drought | Lv1 | 0 |
| 15 | surface (ERA5 GRIB 원자료) | `01M39V7N5V054MKPFW7N0DTYEX` | 포멧테스트 | Lv0 | 0 |
| 16 | ERA5 변환 결과 | `01M39VBGCMRM3K31W963PGG7E8` | 포멧테스트 | Lv1 | 1 |
| 17 | GK-2A LST 원자료 | `01M39VM0GYXG98CXDJKFD8RPYJ` | 포멧테스트 | Lv0 | 0 |
| 18 | GK-2A LST 변환 결과 | `01M39XWZBR39ZDX38RZVADF3BR` | 포멧테스트 | Lv1 | 1 |
| 19 | HSR 레이더합성 원자료 | `01M39XZFZ6NYXQ48YD4KZN168X` | 포멧테스트 | Lv0 | 0 |
| 20 | HSR 레이더합성 변환 결과 | `01M39Y5NEBAW44F2Y2Q0WJE5QX` | 포멧테스트 | Lv1 | 1 |
| 21 | HLS S30 T51SYB 원자료 | `01M39YCEB2RHDTPH26KEV70TK4` | 포멧테스트 | Lv0 | 0 |
| 22 | HLS S30 T52SCE 원자료 | `01M39YJVRFA5N1T1498KNN007Y` | 포멧테스트 | Lv0 | 0 |
| 23 | HLS S30 T51SYB 변환 결과 | `01M39YP2K5A3CEEF99M5TNVR44` | 포멧테스트 | Lv1 | 1 |
| 24 | HLS S30 T52SCE 변환 결과 | `01M39YSE2MMXGA14SHG08PHY6S` | 포멧테스트 | Lv1 | 1 |
| 25 | hdf4 MOD15A2H h27v05 원자료 | `01M39Z0009K337B2N4DK4TSE9C` | 포멧테스트 | Lv0 | 0 |
| 26 | hdf4 MOD15A2H h28v05 원자료 | `01M39Z6ABH9Z2EW0CZTZM4C6DH` | 포멧테스트 | Lv0 | 0 |
| 27 | hdf4 MOD15A2H h27v05 변환 결과 | `01M39ZCMYVKSA6N5SS3HJZ225F` | 포멧테스트 | Lv1 | 1 |
| 28 | hdf4 MOD15A2H h28v05 변환 결과 | `01M39ZK1YKQRT84W0PSJFD89SJ` | 포멧테스트 | Lv1 | 1 |

## 5. 미검증·범위

- API `listDatasets` 교차 대조는 하지 않았다(SQL 단일 경로).
- `processing_level_derived` 는 제품 SQL 을 옮겨 계산한 값이다 — API 응답 `processingLevel` 과 대조하지 않았다.
- seq 23·24 `crs` 빈 값의 원인 · `source_url`·`source_downloaded_on`(Lv0 출처 칸)은 포획하지 않았다.
- intent 와 다른 점 — intent ㉳ 는 `dev-data-snapshot.json` 교체를 적었으나 이 WU 는 **새 파일**로 두고 v1 을 보존한다.
  기존 소비자(`golden_baseline.py`·`seed_reference_corpus` 등)는 아직 v1 을 읽는다 — 전환은 WU4.

## 6. 재실행

```bash
# dev-operator.env 의 COLAB_DEV_SSH · COLAB_DEV_KEY_FILE 을 환경에 둔 뒤, 새 출력 경로로
python3 eval/k4-search/recapture_snapshot.py --output <새 스냅샷.json> --idmap <새 대응표.json> [--checks <검사.json>]
python3 -m unittest discover -s eval/k4-search -p 'test_recapture_snapshot.py'
```
기존 경로를 주면 준비 실패(78)로 멈춘다 — 덮어쓰지 않는다.
