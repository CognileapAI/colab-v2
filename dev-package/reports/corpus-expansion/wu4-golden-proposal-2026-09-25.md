# WU4 — 골든셋·계보 정답 재박기 서명 제안 (2026-09-25 · 서명 ①② 완료)

**서명 ①②는 사용자가 2026-09-25 에 받았다(§1·§2 머리의 서명 줄).** 골든 파일(`eval/` 의 골든·K3 정답)은 이 문서에서 수정하지 않았다 — WU4 재박기가 서명본으로 한다. 선행 조건 O4·O7 의 dev 보정 결과는 §7.

메타 — 가지 `corpus-wu4-golden`(`origin/corpus-wu3-snapshot` `a60e3fa0` 위) · dev 무접촉 · 검색·모델 호출 0회.
기계 판독본 = 같은 폴더 `wu4-golden-proposal-2026-09-25.json`(스키마 `colab-wu4-golden-proposal/1`). 이 문서의 표·ID 는 그 파일과 같은 생성 과정에서 나왔다.

## 0. 요약

| 항목 | 값 |
|---|---|
| 방법 | 독립 제안 2건(STRICT = 정본 문자 기준, SEMANTIC = 연구자 의미 기준) ＋ 대응·계보 도출 1건을 대조 |
| 12문항 required | 두 제안 12/12 일치 |
| 12문항 mode | 12/12 일치(옛 값 유지) |
| 12문항 scope | 일치 1건(001) · 불일치 11건(002~012) — 불일치 전부가 결정 하나(D1: 14건 대 28건)에서 나옴 |
| 옛→새 대응 | 옛 9건 → 새 14건(seq1~14). same-content 4 · contains 5 · part-of 0. 새 seq15~28 은 대응 없음 |
| K3 케이스 | 4건 재선정 · 간선 9개. 같은 모양이 없는 것은 LIN-001 하나(대체안) |
| Ted 판정 필요 | §5 의 O1~O10(핵심: O1 scope 범위 · O2 golden-set.md 재박기 범위 · O4 계보 역할 · O8 K3 케이스 수) |

생성 과정에서 기계 확인한 것(전건 통과):
- v2 스냅샷 28건의 `plan_seq`·이름·ID 가 `dev-name-id-v2.json` 과 일치.
- 두 제안의 문항별 required ID 가 서로 같고, 이 문서의 required 와 같음.
- scope 선택지 전부(S-VEG·A·B)가 채점기 검증 규칙(`golden_baseline.py` 137~144행: 비지 않은 scope · required ⊆ scope · retrieval 이면 required 필수)을 통과.
- 정본이 지목한 필수 파일 11개가 각각 v2 에서 정확히 한 데이터셋에만 있고, 그 데이터셋이 required 에 들어 있음.
- K3 제안 4건의 부모·역할·Lv 가 v2 스냅샷과 일치하고 method 는 전부 빈 값.

## 1. 서명 ① — 옛 → 새 대응

**서명 ① — 사용자 · 2026-09-25 · 승인.** 1-1 옛→새 대응 9행과 1-2 이름→ID 28행을 그대로 받는다.

### 1-1. 옛 9건 → 새 데이터셋 (9행)

relation 은 옛 데이터셋 기준. 대조는 본체 파일 이름·크기 전수.

| 옛 별칭 | 옛 ID | 옛 이름 | relation | 새 seq · 이름 · ID | 근거 |
|---|---|---|---|---|---|
| HSR0 | `01M1SCC27AN4NZD3K978YFDCVD` | 강수 — HSR 레이더 합성 반사도 (Lv.0) | contains | seq1 HSR 레이더 반사도 원자료 `01M39T7N812JDX7GW62F8YFZ0V` | 본체 RDR_CMP_HSR_PUB_*.bin.gz 10/10 · 격자 LAT_HSR·LON_HSR 이름·크기 일치. 옛 쪽에만 자료설명.pptx·#processing_description_Precipitation.docx. |
| RN0 | `01M1SCC8BZZJSCEW4MRPE4W9M8` | 강수 — RN15 지상 15분 누적 강수 (Lv.0) | same-content | seq2 rn15 15분 누적강수 `01M39T979PMQKRSK3GPCNYWHH3` | 본체 sfc_grid_rn_15m_*.nc 10/10 · 격자 LAT_RN15·LON_RN15 일치. 계보 역할: 옛 crop 표본의 보조입력 → 새 seq4 의 주입력. |
| VEG0 | `01M1SCCM2Q4ST81GZK3YM0PFZR` | 식생 — GK-2A/AMI Lv.2 식생산출물 원자료 (Lv.0) | contains | seq6 GK-2A 일 단위 식생자료 `01M39TK0F5P3W4APB91N08KTMY` | 본체 gk2a_ami_le2_vgt_ko_20230501~0531.nc 31/31 일치. 옛 쪽에만 #processing_description_NDVI.docx. 옛 LAT.npy·LON.npy 는 새 쪽에 없음(파일 내장 LCC). |
| RAIN1 | `01M1SCGM0K7FACRYTCWVMDDBY8` | 강수 — WGS84 변환·연구대상지 crop 표본 (Lv.1) | contains | seq3 hsr_sample `01M39TA6QY5NEAR8ZPZ6AF9KNE`<br>seq4 rn15_sample `01M39TB4NTBCFC8TSTNB93N5YP` | 묶음 분할 — hsr_sample.npy → seq3, rn15_sample.npy → seq4(각 655,488 B). 옛 HSR 주입력·RN15 보조입력 → 새 3←1·4←2 모두 주입력. |
| VEG1 | `01M1SCGX4PFD796VX8093WQMS7` | 식생 — GK-2A NDVI 100 m 월평균 (Lv.1) | same-content | seq7 GK2A_NDVI_mean_202305 `01M39TSEPR820QBZ1DBBFKDJEP` | 본체 GK2A_NDVI_mean_202305.tif 1/1 일치. 옛 격자 LAT_crop·LON_crop 은 새 쪽에 없음(GeoTIFF 내장 EPSG:4326). 계보 7←6 주입력 동일. |
| VEG-AUX | `01M1SCH2SAEFRXCZ2N6RSNR3GB` | 식생 — Lv.2 모델 보조입력·검증자료 (Lv.1 형제) | contains | seq8 HLS_S30_NDVI_mean_202305 `01M39TT0S5PSJ0DQNR0XMTHFNW`<br>seq9 DEM `01M39TTPB2T87ESQKHCZPBAKD6`<br>seq10 Aspect `01M39TVD38600D4EKH13EV55DV`<br>seq11 LULC_2023 `01M39TW21793T8631ATHJREHK5` | 묶음 분할 — tif 4개 → seq8 HLS·9 DEM·10 Aspect·11 LULC. 새 간선 10←9 추가. Prediction 부모 역할: HLS·LULC 주입력, DEM·Aspect 보조입력. |
| DROUGHT | `01M1SCH9DF18DXH793JTP01W61` | 가뭄 — 시군구 주간 SPI/SPEI-4weeks (Lv.1) | contains | seq13 SPI-4weeks `01M39V005J6SQ9SW8MZ8D16ZWK`<br>seq14 SPEI-4weeks `01M39V0T17DHQ5PF5XSSERTZ8H` | 묶음 분할 — SPI·SPEI gpkg → seq13·14. 옛 쪽에만 여는 코드.ipynb·[Data Info] docx 2개. 새 기간 끝 2025-12-20(옛 요약 ~2025-12-31). |
| RAIN2 | `01M1SCJTXHXT37CZD22TKMJ13P` | 강수 — U-Net 강우 추정 예측장 (Lv.2) | same-content | seq5 pred_sample `01M39TCARM2C2NJ8S9SA4QBSER` | 본체 pred_sample.npy 1/1 일치. 새 쪽에 LAT_crop·LON_crop 부착. 부모 1(crop 묶음) → 2(seq3·4, 합치면 옛 부모와 동일). |
| VEG2 | `01M1SCKW76AZQCHT5HAMZH9KH0` | 식생 — U-Net NDVI 예측장 (Lv.2) | same-content | seq12 Prediction (공간상세화) `01M39TZ0SCEYHHMBWZ991M1QGN` | 본체 Prediction_20230501~0531.npy 31/31 일치. 부모 2 → 5(주입력 7·8·11, 보조입력 9·10). |

- relation 규약 — `same-content`: 본체 파일 이름·크기 전건 일치. `contains`: 옛 데이터셋이 새 데이터셋(들)의 본체 전부를 포함(묶음 분할 또는 옛 쪽에만 설명 문서). `part-of`: 0건.
- 새 코퍼스에 없는 옛 파일 6개(1,251,824 B, 전부 설명 문서·코드): 자료설명.pptx · #processing_description_Precipitation.docx · #processing_description_NDVI.docx · 01.가뭄 데이터 여는 코드.ipynb · [Data Info]SPI-4weeks.docx · [Data Info]SPEI-4weeks.docx.
- 대응 없는 새 데이터셋 14건(seq15~28, 포멧테스트). 옛 파일과 겹침 0. 관련만 있는 것: 19·20(HSR 같은 제품군, 2025-08-13) · 17·18(GK-2A LST) · 21~24(HLS S30 원시 타일) · 25~28(MOD15A2H).
- 옛 6간선 → 새 10간선: 3←1 · 7←6 · 12←7 그대로 / RN15 보조입력 → 4←2 주입력 / 5←3·4(분할) / 12←8·11 주입력 ＋ 12←9·10 보조입력(분할). 옛 코퍼스에 없는 새 간선 8개: 10←9 ＋ 포멧테스트 7쌍.

### 1-2. 새 이름 → ID (28행)

출처 = WU3 보고 `wu3-snapshot-2026-09-25.md` §4(기계 판독본 `eval/k4-search/fixtures/reference/dev-name-id-v2.json`). 서명 ① 은 이 표와 1-1 을 함께 받는다.

| seq | 이름 | 새 ID | 프로젝트 | Lv(열) | 옛 대응 |
|---|---|---|---|---|---|
| 1 | HSR 레이더 반사도 원자료 | `01M39T7N812JDX7GW62F8YFZ0V` | precipitation | Lv0 | HSR0 |
| 2 | rn15 15분 누적강수 | `01M39T979PMQKRSK3GPCNYWHH3` | precipitation | Lv0 | RN0 |
| 3 | hsr_sample | `01M39TA6QY5NEAR8ZPZ6AF9KNE` | precipitation | Lv1 | RAIN1 |
| 4 | rn15_sample | `01M39TB4NTBCFC8TSTNB93N5YP` | precipitation | Lv1 | RAIN1 |
| 5 | pred_sample | `01M39TCARM2C2NJ8S9SA4QBSER` | precipitation | Lv2 | RAIN2 |
| 6 | GK-2A 일 단위 식생자료 | `01M39TK0F5P3W4APB91N08KTMY` | vegetation | Lv0 | VEG0 |
| 7 | GK2A_NDVI_mean_202305 | `01M39TSEPR820QBZ1DBBFKDJEP` | vegetation | Lv1 | VEG1 |
| 8 | HLS_S30_NDVI_mean_202305 | `01M39TT0S5PSJ0DQNR0XMTHFNW` | vegetation | Lv1 | VEG-AUX |
| 9 | DEM | `01M39TTPB2T87ESQKHCZPBAKD6` | vegetation | Lv1 | VEG-AUX |
| 10 | Aspect | `01M39TVD38600D4EKH13EV55DV` | vegetation | Lv1 | VEG-AUX |
| 11 | LULC_2023 | `01M39TW21793T8631ATHJREHK5` | vegetation | Lv1 | VEG-AUX |
| 12 | Prediction (공간상세화) | `01M39TZ0SCEYHHMBWZ991M1QGN` | vegetation | Lv2 | VEG2 |
| 13 | SPI-4weeks | `01M39V005J6SQ9SW8MZ8D16ZWK` | drought | Lv1 | DROUGHT |
| 14 | SPEI-4weeks | `01M39V0T17DHQ5PF5XSSERTZ8H` | drought | Lv1 | DROUGHT |
| 15 | surface (ERA5 GRIB 원자료) | `01M39V7N5V054MKPFW7N0DTYEX` | 포멧테스트 | Lv0 | — |
| 16 | ERA5 변환 결과 | `01M39VBGCMRM3K31W963PGG7E8` | 포멧테스트 | Lv1 | — |
| 17 | GK-2A LST 원자료 | `01M39VM0GYXG98CXDJKFD8RPYJ` | 포멧테스트 | Lv0 | — |
| 18 | GK-2A LST 변환 결과 | `01M39XWZBR39ZDX38RZVADF3BR` | 포멧테스트 | Lv1 | — |
| 19 | HSR 레이더합성 원자료 | `01M39XZFZ6NYXQ48YD4KZN168X` | 포멧테스트 | Lv0 | — |
| 20 | HSR 레이더합성 변환 결과 | `01M39Y5NEBAW44F2Y2Q0WJE5QX` | 포멧테스트 | Lv1 | — |
| 21 | HLS S30 T51SYB 원자료 | `01M39YCEB2RHDTPH26KEV70TK4` | 포멧테스트 | Lv0 | — |
| 22 | HLS S30 T52SCE 원자료 | `01M39YJVRFA5N1T1498KNN007Y` | 포멧테스트 | Lv0 | — |
| 23 | HLS S30 T51SYB 변환 결과 | `01M39YP2K5A3CEEF99M5TNVR44` | 포멧테스트 | Lv1 | — |
| 24 | HLS S30 T52SCE 변환 결과 | `01M39YSE2MMXGA14SHG08PHY6S` | 포멧테스트 | Lv1 | — |
| 25 | hdf4 MOD15A2H h27v05 원자료 | `01M39Z0009K337B2N4DK4TSE9C` | 포멧테스트 | Lv0 | — |
| 26 | hdf4 MOD15A2H h28v05 원자료 | `01M39Z6ABH9Z2EW0CZTZM4C6DH` | 포멧테스트 | Lv0 | — |
| 27 | hdf4 MOD15A2H h27v05 변환 결과 | `01M39ZCMYVKSA6N5SS3HJZ225F` | 포멧테스트 | Lv1 | — |
| 28 | hdf4 MOD15A2H h28v05 변환 결과 | `01M39ZK1YKQRT84W0PSJFD89SJ` | 포멧테스트 | Lv1 | — |

## 2. 서명 ② — 12문항 scope · required

**서명 ② — 사용자 · 2026-09-25 · 승인.** required·mode 는 제안대로(두 제안 12/12 일치). scope 는 001 = S-VEG(7건), 002~012 = 선택지 A(S-LD · level-data 14건). `golden-set.md` 는 수치만 재박는다(예: 55·66·171~173·198~199행의 9 → 14, 010 기대 응답의 9 → 14). 의미 기준 문장은 바꾸지 않는다.

### 2-0. 한눈에

| 문항 | mode | 옛 required | 새 required | STRICT scope | SEMANTIC scope | 합의 |
|---|---|---|---|---|---|---|
| 001 | retrieval | VEG1 | seq7 GK2A_NDVI_mean_202305 | S-VEG 7 | S-VEG 7 | 완전 일치 |
| 002 | retrieval | VEG1 | seq7 GK2A_NDVI_mean_202305 | A 14 | B 28 | required·mode 일치 / scope D1 |
| 003 | retrieval | VEG2 | seq12 Prediction (공간상세화) | A 14 | B 28 | required·mode 일치 / scope D1 |
| 004 | retrieval | VEG0 | seq6 GK-2A 일 단위 식생자료 | A 14 | B 28 | required·mode 일치 / scope D1 |
| 005 | retrieval | VEG-AUX | seq9 DEM, seq10 Aspect, seq11 LULC_2023, seq8 HLS_S30_NDVI_mean_202305 | A 14 | B 28 | required·mode 일치 / scope D1 |
| 006 | retrieval | RAIN2, RAIN1 | seq5 pred_sample, seq4 rn15_sample | A 14 | B 28 | required·mode 일치 / scope D1 |
| 007 | retrieval | RAIN1 | seq4 rn15_sample | A 14 | B 28 | required·mode 일치 / scope D1 |
| 008 | retrieval | DROUGHT | seq13 SPI-4weeks, seq14 SPEI-4weeks | A 14 | B 28 | required·mode 일치 / scope D1 |
| 009 | retrieval | DROUGHT | seq13 SPI-4weeks | A 14 | B 28 | required·mode 일치 / scope D1 |
| 010 | empty | 없음 | 없음 | A 14 | B 28 | required·mode 일치 / scope D1 |
| 011 | manual | 없음 | 없음 | A 14 | B 28 | required·mode 일치 / scope D1 |
| 012 | manual | 없음 | 없음 | A 14 | B 28 | required·mode 일치 / scope D1 |

### 2-1. scope 집합 정의

- **S-VEG (7건, 001 전용)** — seq6 GK-2A 일 단위 식생자료 `01M39TK0F5P3W4APB91N08KTMY` · seq7 GK2A_NDVI_mean_202305 `01M39TSEPR820QBZ1DBBFKDJEP` · seq8 HLS_S30_NDVI_mean_202305 `01M39TT0S5PSJ0DQNR0XMTHFNW` · seq9 DEM `01M39TTPB2T87ESQKHCZPBAKD6` · seq10 Aspect `01M39TVD38600D4EKH13EV55DV` · seq11 LULC_2023 `01M39TW21793T8631ATHJREHK5` · seq12 Prediction (공간상세화) `01M39TZ0SCEYHHMBWZ991M1QGN`
- **S-LD (14건, 선택지 A)** — S-VEG ＋ seq1 HSR 레이더 반사도 원자료 `01M39T7N812JDX7GW62F8YFZ0V` · seq2 rn15 15분 누적강수 `01M39T979PMQKRSK3GPCNYWHH3` · seq3 hsr_sample `01M39TA6QY5NEAR8ZPZ6AF9KNE` · seq4 rn15_sample `01M39TB4NTBCFC8TSTNB93N5YP` · seq5 pred_sample `01M39TCARM2C2NJ8S9SA4QBSER` · seq13 SPI-4weeks `01M39V005J6SQ9SW8MZ8D16ZWK` · seq14 SPEI-4weeks `01M39V0T17DHQ5PF5XSSERTZ8H`
- **S-ALL (28건, 선택지 B)** — S-LD ＋ seq15 surface (ERA5 GRIB 원자료) `01M39V7N5V054MKPFW7N0DTYEX` · seq16 ERA5 변환 결과 `01M39VBGCMRM3K31W963PGG7E8` · seq17 GK-2A LST 원자료 `01M39VM0GYXG98CXDJKFD8RPYJ` · seq18 GK-2A LST 변환 결과 `01M39XWZBR39ZDX38RZVADF3BR` · seq19 HSR 레이더합성 원자료 `01M39XZFZ6NYXQ48YD4KZN168X` · seq20 HSR 레이더합성 변환 결과 `01M39Y5NEBAW44F2Y2Q0WJE5QX` · seq21 HLS S30 T51SYB 원자료 `01M39YCEB2RHDTPH26KEV70TK4` · seq22 HLS S30 T52SCE 원자료 `01M39YJVRFA5N1T1498KNN007Y` · seq23 HLS S30 T51SYB 변환 결과 `01M39YP2K5A3CEEF99M5TNVR44` · seq24 HLS S30 T52SCE 변환 결과 `01M39YSE2MMXGA14SHG08PHY6S` · seq25 hdf4 MOD15A2H h27v05 원자료 `01M39Z0009K337B2N4DK4TSE9C` · seq26 hdf4 MOD15A2H h28v05 원자료 `01M39Z6ABH9Z2EW0CZTZM4C6DH` · seq27 hdf4 MOD15A2H h27v05 변환 결과 `01M39ZCMYVKSA6N5SS3HJZ225F` · seq28 hdf4 MOD15A2H h28v05 변환 결과 `01M39ZK1YKQRT84W0PSJFD89SJ`

### 2-2. 결정 D1 — 002~012 의 scope

| | A: S-LD 14건 (STRICT) | B: S-ALL 28건 (SEMANTIC) |
|---|---|---|
| 근거 1 | golden-set.md 66행 「LD 접두 9개 묶음」과 같은 파일을 담은 가장 좁은 동치 — seq1~14 의 파일은 모두 옛 9묶음 파일의 부분집합, seq15~28 은 겹침 0. | 66행이 범위를 제한한 이유는 dev 25건 중 16건의 내용이 판정되지 않았기 때문 — 새 28건은 전부 DATASETS.md 정본 설명이 있어 그 이유가 사라짐. |
| 근거 2 | 옛 K4 기준선과 후보 구성이 같아 재측정 전후 비교가 성립. | scope = visible 28 이 되어 제품이 보는 범위와 평가 범위가 같아짐. 010 기대 응답의 「확인한 N개」와 제품 응답의 불일치가 없어짐. |
| 근거 3 | 채점기는 scope 밖 결과를 outside_ids 로 따로 남기므로 15~28 의 방해 효과는 판정과 별개로 관측됨. | 포멧테스트 14건이 연구자가 실제로 마주칠 방해 후보(천리안 LST·HSR 레이더합성·MOD15A2H·HLS 3밴드)를 판정 안으로 넣음. |
| 근거 4 | 010 의 「이 검색 대상」 의미(고정 범위)를 그대로 유지. | intent 제목(「코퍼스를 28건으로 넓히고」)의 목적과 맞음. |
| 약점 | 66행의 제한 이유(미판정 16건)가 사라졌는데 범위를 좁게 유지. 제품은 28건을 보므로 010 기대 응답 「확인한 N개」와 어긋날 수 있음. | 66행 문자(「LD 접두」 = level-data)에서 벗어남. 010 이 더 엄격해지고 옛 기준선과 후보 구성이 달라 비교가 끊김. |

불변 사항(어느 쪽이든):
- 어느 쪽이든 12문항의 required 는 같다(두 제안이 문항별로 확인: seq15~28 가운데 어느 문항의 조건도 충족하는 자료 없음).
- retrieval 문항의 자동 판정은 required ⊆ scoped 이므로 scope 선택에 영향받지 않는다. 판정이 달라질 수 있는 문항은 010(empty) 하나.
- golden_baseline.py:134 가 세는 것은 스냅샷 전체 건수라 어느 쪽이든 28.
- 어느 쪽이든 golden-set.md 의 「9묶음」 수치는 재박기 대상이다.

**권고: A(S-LD 14건).** 66행의 문자 그대로에 가장 가까운 동치이고 옛 기준선과 비교 가능성을 지키며, 15~28 의 영향은 outside_ids 로 관측된다. B 의 근거(제한 이유 소멸·scope = visible)도 성립하므로 Ted 가 「평가 범위 = 제품이 보는 범위」를 우선하면 B 로 바꾼다. B 로 바꿔도 required·mode 는 그대로다.

### 2-3. 문항별

scope 는 001 = S-VEG, 002~012 = 권고 A(S-LD) · 대안 B(S-ALL). 줄 번호는 `golden-set.md`(a60e3fa0) 기준. 질문 문장은 무수정.

#### SEARCH-GOLD-001 · retrieval

- 질문: 2023년 5월 경기 남부와 충청권의 식생 상태를 살펴볼 수 있는 월평균 위성 자료 찾아줘.
- 옛 값: scope 4건(VEG0, VEG1, VEG-AUX, VEG2) · required VEG1
- 새 scope: S-VEG(7건)
- 새 required: GK2A_NDVI_mean_202305 `01M39TSEPR820QBZ1DBBFKDJEP`
- 필수 파일: GK2A_NDVI_mean_202305.tif
- 합의: 두 제안 완전 일치.
- 근거: 13행 「자료 범위: 02.vegetation/02.vegetation/」 → 같은 폴더 7건(seq6~12). 옛 scope 4묶음(VEG0·VEG1·VEG-AUX·VEG2)의 파일 단위 분할과 같다. 주 정답 15행 → seq7(파일 유일 보유). C5 함정 seq6(일별 원자료)·seq12(일별 예측장)는 범위 안.
- 열린 문제:
  - C2 「경기 남부~충청권」·C4 「2 km→100 m 균등 분할」 근거가 v2 메타·코퍼스에 없음(v1 summary·#processing_description_NDVI.docx 에만 있었음).
  - seq8 HLS_S30_NDVI_mean_202305 가 단독 데이터셋이 되어 메타상 「2023-05·월평균·위성·NDVI」를 똑같이 충족. C1 이 주 정답을 고정하므로 required 에서 제외. 「허용 동반 후보」로 명시할지 판정 필요(§5 O3).

#### SEARCH-GOLD-002 · retrieval

- 질문: 2023년 5월 경기 남부와 충청권에서 식물이 얼마나 푸른지 월평균으로 볼 수 있는 자료 찾아줘.
- 옛 값: scope 9건(HSR0, RN0, VEG0, RAIN1, VEG1, VEG-AUX, DROUGHT, RAIN2, VEG2) · required VEG1
- 새 scope: 권고 A: S-LD(14건) · 대안 B: S-ALL(28건)
- 새 required: GK2A_NDVI_mean_202305 `01M39TSEPR820QBZ1DBBFKDJEP`
- 필수 파일: GK2A_NDVI_mean_202305.tif
- 합의: required·mode 일치 · scope 불일치(D1).
- 근거: 99행(VEG1)·101행(001과 같은 정답) → seq7. 102행 함정 seq11 LULC_2023(토지피복만 제시). NDVI 가 아닌 식생 계열(B 선택 시 MOD15A2H LAI/FPAR·HLS 3밴드)은 지표·기간 불일치.
- 열린 문제:
  - 001과 같은 지역·균등분할 근거 공백.
  - HLS(seq8)가 같은 조건 충족 후보로 드러남(O3).

#### SEARCH-GOLD-003 · retrieval

- 질문: 2023년 5월 1일의 식생지수를 U-Net으로 예측한 자료 찾아줘.
- 옛 값: scope 9건(HSR0, RN0, VEG0, RAIN1, VEG1, VEG-AUX, DROUGHT, RAIN2, VEG2) · required VEG2
- 새 scope: 권고 A: S-LD(14건) · 대안 B: S-ALL(28건)
- 새 required: Prediction (공간상세화) `01M39TZ0SCEYHHMBWZ991M1QGN`
- 필수 파일: Prediction_20230501.npy
- 합의: required·mode 일치 · scope 불일치(D1).
- 근거: 108행(VEG2, Prediction_20230501.npy) → seq12(파일 유일 보유). summary 「U-Net 기반 100 m 일 단위 NDVI 예측」·Lv2. 111행 함정 seq6·seq7, 강수 U-Net seq5.
- 열린 문제:
  - U-Net 근거는 summary 한 곳뿐(계보 method 빈 값).
  - Prediction_20230501.npy 를 파일 31개 중에서 지목했는지는 수동 확인.

#### SEARCH-GOLD-004 · retrieval

- 질문: GK2A_NDVI_mean_202305.tif를 만드는 데 쓴 천리안 원자료 찾아줘.
- 옛 값: scope 9건(HSR0, RN0, VEG0, RAIN1, VEG1, VEG-AUX, DROUGHT, RAIN2, VEG2) · required VEG0
- 새 scope: 권고 A: S-LD(14건) · 대안 B: S-ALL(28건)
- 새 required: GK-2A 일 단위 식생자료 `01M39TK0F5P3W4APB91N08KTMY`
- 필수 파일: gk2a_ami_le2_vgt_ko_202305010000.nc
- 합의: required·mode 일치 · scope 불일치(D1).
- 근거: 117·119행(VEG0, VEG1 의 직접 부모) → seq6. v2 계보에서 seq7 의 부모는 seq6(주입력) 1간선뿐. 120행 함정 seq12·seq9, 「모든 보조입력을 VEG1 부모로 연결」 대상 seq8·10·11.
- 열린 문제:
  - 118행 「가공 과정에서 NDVI 추출」 근거 약함 — method 0/18, seq6 summary 에 NDVI 언급 없음, 처리 설명서 부재.
  - 「천리안」이 v2 메타에 0회(전부 GK-2A). 동의어 사전 의존.
  - B 선택 시 seq17 GK-2A LST 원자료(천리안 원자료이나 지표온도, 2020-05-01)가 추가 함정.

#### SEARCH-GOLD-005 · retrieval

- 질문: U-Net 식생지수 모델에 쓴 지형·토지피복 보조자료와 검증용 식생자료 찾아줘.
- 옛 값: scope 9건(HSR0, RN0, VEG0, RAIN1, VEG1, VEG-AUX, DROUGHT, RAIN2, VEG2) · required VEG-AUX
- 새 scope: 권고 A: S-LD(14건) · 대안 B: S-ALL(28건)
- 새 required: DEM `01M39TTPB2T87ESQKHCZPBAKD6` · Aspect `01M39TVD38600D4EKH13EV55DV` · LULC_2023 `01M39TW21793T8631ATHJREHK5` · HLS_S30_NDVI_mean_202305 `01M39TT0S5PSJ0DQNR0XMTHFNW`
- 필수 파일: DEM.tif, Aspect.tif, LULC_2023.tif, HLS_S30_NDVI_mean_202305.tif
- 합의: required·mode 일치 · scope 불일치(D1). 확신도만 다름(STRICT high · SEMANTIC medium).
- 근거: 126행이 파일 4개를 모두 요구 → 옛 VEG-AUX 가 4건으로 분할됐고 각 파일이 한 데이터셋에만 있으므로 4건 모두 required. 129행 함정 seq7(「보조자료가 VEG1에서 생성」).
- 열린 문제:
  - v2 계보 역할이 정본 127행과 충돌 — Prediction ← LULC_2023·HLS 가 「주입력」(보조입력은 DEM·Aspect 2간선뿐). 정본: 토지피복=보조입력, HLS=검증자료. 자료 쪽 역할 정정 여부 판정 필요(§5 O4, 골든 수정 사항 아님).
  - 128행 「한 데이터셋 안에서 입력·검증 역할 구분」은 데이터셋 사이 역할 구분으로 읽어야 함.
  - required 1→4건. retrieval 자동 판정이 엄격해짐.

#### SEARCH-GOLD-006 · retrieval

- 질문: 레이더 반사도로 만든 강우 추정 결과와 검증에 쓴 강수 자료 찾아줘.
- 옛 값: scope 9건(HSR0, RN0, VEG0, RAIN1, VEG1, VEG-AUX, DROUGHT, RAIN2, VEG2) · required RAIN2, RAIN1
- 새 scope: 권고 A: S-LD(14건) · 대안 B: S-ALL(28건)
- 새 required: pred_sample `01M39TCARM2C2NJ8S9SA4QBSER` · rn15_sample `01M39TB4NTBCFC8TSTNB93N5YP`
- 필수 파일: pred_sample.npy, rn15_sample.npy
- 합의: required·mode 일치 · scope 불일치(D1). 확신도만 다름(STRICT medium · SEMANTIC high).
- 근거: 135행 → pred_sample(seq5)·rn15_sample(seq4) 필수. hsr_sample(seq3)은 135행 「입력으로 함께 설명 가능」 → 선택. 138행 함정 seq1(HSR 원자료를 강수 직접 측정값으로 취급), B 선택 시 seq19·20 추가.
- 열린 문제:
  - 「rn15_sample 은 검증에 쓴 자료」(136행) 근거가 v2 에 없음 — 계보상 pred_sample ← rn15_sample 이 「주입력」, method 빈 값, #processing_description_Precipitation.docx 부재. DATASETS.md 에만 「검증은 rn15_sample.npy」.
  - 제품이 rn15_sample 을 「입력」으로 설명하면 수동 판정 실패 위험(O4).
  - rn15 원자료(seq2)를 검증자료로 제시한 경우의 판정이 정본에 없음(§5 O6).

#### SEARCH-GOLD-007 · retrieval

- 질문: WGS84로 바꾸고 연구대상지에 맞춰 잘라 둔 15분 누적 강수 표본 찾아줘.
- 옛 값: scope 9건(HSR0, RN0, VEG0, RAIN1, VEG1, VEG-AUX, DROUGHT, RAIN2, VEG2) · required RAIN1
- 새 scope: 권고 A: S-LD(14건) · 대안 B: S-ALL(28건)
- 새 required: rn15_sample `01M39TB4NTBCFC8TSTNB93N5YP`
- 필수 파일: rn15_sample.npy
- 합의: required·mode 일치 · scope 불일치(D1).
- 근거: 144행 → seq4. summary 「WGS84 변환·crop 한 rn15 전처리 자료」·15분·Lv1 이 146행 세 조건과 맞음. 함정 seq3(같은 처리, HSR 5분)·seq2(147행 명시 오답).
- 열린 문제:
  - 147행 오답 「10개 표본을 연속 5분 시계열로 단정」을 판정할 근거가 dev 메타에 없음 — period 2019-07-28~2024-07-09 가 연속처럼 보이고, 「10개 불연속 표본」은 canonical-metadata 에만 있음.
  - 「연구대상지」 낱말이 v2 summary 에 없음(v1 에는 있었음).

#### SEARCH-GOLD-008 · retrieval

- 질문: 2000년부터 2025년까지 대한민국 시군구의 4주 가뭄지수를 주간으로 비교할 자료 찾아줘.
- 옛 값: scope 9건(HSR0, RN0, VEG0, RAIN1, VEG1, VEG-AUX, DROUGHT, RAIN2, VEG2) · required DROUGHT
- 새 scope: 권고 A: S-LD(14건) · 대안 B: S-ALL(28건)
- 새 required: SPI-4weeks `01M39V005J6SQ9SW8MZ8D16ZWK` · SPEI-4weeks `01M39V0T17DHQ5PF5XSSERTZ8H`
- 필수 파일: SPI_4weeks_sig_wide.gpkg, SPEI_4weeks_sig_wide.gpkg
- 합의: required·mode 일치 · scope 불일치(D1).
- 근거: 153행 「SPI·SPEI 두 GPKG」 → 옛 DROUGHT 분할분 seq13·14 둘 다 필수. period 끝 2025-12-20(155행과 일치)·간격 7일.
- 열린 문제:
  - 「대한민국 시군구」·「관측소 기반 시군구 대표값」 근거가 v2 메타에 없음([Data Info] docx 부재).
  - gpkg 2건 format·crs·grid 빈 값.
  - period_granularity 「일」과 간격 7일 공존 → 오답 「일별 자료」 유발 가능.
  - required 1→2건.

#### SEARCH-GOLD-009 · retrieval

- 질문: 시군구별 주간 SPI-4weeks 자료 찾아줘. SPEI 말고 SPI가 필요해.
- 옛 값: scope 9건(HSR0, RN0, VEG0, RAIN1, VEG1, VEG-AUX, DROUGHT, RAIN2, VEG2) · required DROUGHT
- 새 scope: 권고 A: S-LD(14건) · 대안 B: S-ALL(28건)
- 새 required: SPI-4weeks `01M39V005J6SQ9SW8MZ8D16ZWK`
- 필수 파일: SPI_4weeks_sig_wide.gpkg
- 합의: required·mode 일치 · scope 불일치(D1).
- 근거: 162행(SPI_4weeks_sig_wide.gpkg)·165행(SPEI만 지목하면 오답) → seq13 만 필수. seq14 는 범위 안, 필수 아님.
- 열린 문제:
  - 164행 「묶음 추천 허용하되 파일 구분」은 묶음이 사라져 적용 대상 없음. 자동 판정은 오히려 강해짐(SPEI 만 내면 fail).
  - 채점기에 금지 후보 칸이 없음 — SPEI 가 SPI 보다 앞 순위여도 자동 pass, 수동으로만 잡힘.
  - 「시군구」 근거 공백은 008과 같음.

#### SEARCH-GOLD-010 · empty

- 질문: 이 검색 대상 자료 중 U-Net으로 예측한 가뭄지수 자료 찾아줘.
- 옛 값: scope 9건(HSR0, RN0, VEG0, RAIN1, VEG1, VEG-AUX, DROUGHT, RAIN2, VEG2) · required 없음
- 새 scope: 권고 A: S-LD(14건) · 대안 B: S-ALL(28건)
- 새 required: 없음(빈 배열)
- 합의: required(빈 값)·mode 일치 · scope 불일치(D1). 확신도 다름(STRICT high · SEMANTIC medium).
- 근거: mode=empty 유지. 14건·28건 어느 쪽에서도 U-Net 가뭄 예측은 0건 — U-Net 산출물은 seq5(강수)·seq12(식생)뿐, seq13·14 는 L1 Calibrated 지수, seq15~28 에 가뭄·U-Net 자료 없음. 174행 함정 seq5·12.
- 열린 문제:
  - 171~173행·198행의 「9묶음·9개 자료 묶음」 수치는 14 또는 28로 재박기 필요 — 편집 범위를 서명 ②에 명시(§5 O2).
  - empty 는 scope 안 결과 1건이라도 있으면 fail(golden_baseline.py 65~66행). 「가뭄지수」로 seq13·14, 「U-Net」으로 seq5·12 가 잡힐 수 있고 이 넷은 A·B 모두 범위 안.
  - B 선택 시 scope = visible 28 이 되어, 오답 「제한 범위를 넘어 전체 제품에 없다고 단정」의 경계 고지를 다시 정해야 함.

#### SEARCH-GOLD-011 · manual

- 질문: 결측률이 0%로 검증된 2023년 5월 식생 자료 찾아줘.
- 옛 값: scope 9건(HSR0, RN0, VEG0, RAIN1, VEG1, VEG-AUX, DROUGHT, RAIN2, VEG2) · required 없음
- 새 scope: 권고 A: S-LD(14건) · 대안 B: S-ALL(28건)
- 새 required: 없음(빈 배열)
- 합의: required(빈 값)·mode 일치 · scope 불일치(D1).
- 근거: mode=manual 유지. 관련 후보 seq6·7·8·12 모두 결측률 검증값 없음(variables 0/28, variable_rows 0). 182행 「정규 변수 표에도 검증값 없음」 성립.
- 열린 문제:
  - 182행 전반부 「처리 설명에는 제거·보간 과정이 있지만」의 근거가 v2 에 없음(seq7 summary 축약, docx 부재, method 빈 값). 결론(확인 불가)은 유지.
  - 수동 판정 때 준비 실패와 품질 실패를 나눠 기록할 기준 필요(§5 O7).
  - B 선택 시 seq25~28 MOD15A2H QC 층이 「검증」 오인 함정 후보(2019년이라 기간 조건으로 걸러짐).

#### SEARCH-GOLD-012 · manual

- 질문: 100m로 직접 관측한 천리안 월평균 NDVI 자료 찾아줘.
- 옛 값: scope 9건(HSR0, RN0, VEG0, RAIN1, VEG1, VEG-AUX, DROUGHT, RAIN2, VEG2) · required 없음
- 새 scope: 권고 A: S-LD(14건) · 대안 B: S-ALL(28건)
- 새 required: 없음(빈 배열)
- 합의: required(빈 값)·mode 일치 · scope 불일치(D1). SEMANTIC 만 HLS 오답 처리 제안.
- 근거: mode=manual 유지. 189행 → 직접 관측 100 m 정답 없음, seq7 은 관련 가공본으로만. seq6 은 천리안 직접 관측이나 일별. seq8 HLS 는 천리안 아님. 192행 함정 seq12(summary 에 「100 m」).
- 열린 문제:
  - 191행 근거(처리 설명서의 균등 분할 설명·VEG1 summary)가 v2 에 없음 — seq7 summary 에 100 m·2 km·균등분할 언급 없음, autometa grid 1280x1280·EPSG:4326 에 해상도(m) 없음.
  - 「100 m」는 seq9·10·12 summary 에만 있어 오답 쪽으로 끌림. 「천리안」 0회.
  - HLS(seq8)를 「100 m 관측」으로 제시한 경우의 판정이 정본에 없음 — SEMANTIC 은 천리안 조건 불충족으로 오답 처리 제안(§5 O5).
  - B 선택 시 seq21·22 HLS S30 원자료(30 m, NIR 없음)·seq17 GK-2A LST 가 추가 함정.

## 3. K3 계보 사례 (4건) 제안

method 는 4건 모두 빈 값(WU3 · intent 판정 기준 3). upload_level 은 `processing_level` 열에서 읽는다. topic 은 null.

| 케이스 | 옛 자식 ← 옛 부모(역할) | 새 자식 | 새 부모(역할) | 모양 |
|---|---|---|---|---|
| K3-LIN-001 | RAIN1 ← HSR0(주입력)<br>RN0(보조입력) | seq3 hsr_sample `01M39TA6QY5NEAR8ZPZ6AF9KNE` · Lv1 | seq1 HSR 레이더 반사도 원자료 `01M39T7N812JDX7GW62F8YFZ0V` (주입력) | replaced |
| K3-LIN-002 | VEG1 ← VEG0(주입력) | seq7 GK2A_NDVI_mean_202305 `01M39TSEPR820QBZ1DBBFKDJEP` · Lv1 | seq6 GK-2A 일 단위 식생자료 `01M39TK0F5P3W4APB91N08KTMY` (주입력) | same-shape |
| K3-LIN-003 | RAIN2 ← RAIN1(주입력) | seq5 pred_sample `01M39TCARM2C2NJ8S9SA4QBSER` · Lv2 | seq3 hsr_sample `01M39TA6QY5NEAR8ZPZ6AF9KNE` (주입력)<br>seq4 rn15_sample `01M39TB4NTBCFC8TSTNB93N5YP` (주입력) | split-parent |
| K3-LIN-004 | VEG2 ← VEG1(주입력)<br>VEG-AUX(보조입력) | seq12 Prediction (공간상세화) `01M39TZ0SCEYHHMBWZ991M1QGN` · Lv2 | seq7 GK2A_NDVI_mean_202305 `01M39TSEPR820QBZ1DBBFKDJEP` (주입력)<br>seq8 HLS_S30_NDVI_mean_202305 `01M39TT0S5PSJ0DQNR0XMTHFNW` (주입력)<br>seq11 LULC_2023 `01M39TW21793T8631ATHJREHK5` (주입력)<br>seq9 DEM `01M39TTPB2T87ESQKHCZPBAKD6` (보조입력)<br>seq10 Aspect `01M39TVD38600D4EKH13EV55DV` (보조입력) | split-parent |

- **K3-LIN-001** — 옛 모양(Lv1 자식 ← Lv0 주입력 HSR + Lv0 보조입력 RN15)은 새 코퍼스에 없음 — 옛 자식 묶음이 hsr_sample·rn15_sample 로 분할. 대체안 seq3 ← seq1: 옛 주입력 간선과 파일 동일, 옛 대표 파일이 hsr_sample.npy, 후손 구조(3 → 5) 동일. 살아 있는 축: 기간 겹침·CRS 동일·토큰 hsr. 오답 후보 seq19·20(HSR 레이더합성, 기간만 다름)·seq4.
  - 열린 문제: 보조입력 역할 신호가 이 케이스에서 사라짐. 옛 RN15 간선은 4←2(주입력)로만 남음 — 이 간선도 정답으로 남기려면 케이스 추가 필요(§5 O9).
  - 열린 문제: test_llm_lineage_probe.py 의 OTHER(RN15)=CHILD 보조입력 픽스처 간선은 새 코퍼스에 없음 — ID 치환만으로는 존재하지 않는 간선을 계속 적게 됨.
- **K3-LIN-002** — 같은 모양(Lv1 ← Lv0 주입력 1) 그대로. 자식·부모 본체 파일 동일, 후손 구조(7 → 12) 동일. 축: 기간 겹침(2023-05)·토큰 gk2a·202305. 격자 900x900 대 1280x1280 다름. 오답 후보 seq17·18(GK-2A LST, 토큰·LCC CRS 공유).
  - 열린 문제: 옛 자식의 격자 파일 LAT_crop·LON_crop 이 새 자식에 없음 — _upload_meta partCount 3 → 1.
  - 열린 문제: CRS 표기(LCC→WGS84 대 EPSG:4326)를 인용 검증기가 같다고 판정하는지 미확인.
- **K3-LIN-003** — 의도(강수 U-Net Lv2 ← Lv1 전처리 표본, 주입력만) 유지. 옛 부모 1(crop 묶음) → 2(seq3·4, 합치면 옛 부모와 동일). 부모 순서는 스냅샷 순서(주입력 → id). 후손 0. 축: 기간·CRS·격자 128x128 동일, 토큰 sample — 네 케이스 중 축 신호 최강.
  - 열린 문제: 간선 1 → 2 로 J2 hit@k 분모 변경.
  - 열린 문제: graph 기준 형제 0건 → same_level 로 떨어져 형제 집합 {seq12}(옛 코퍼스와 같은 동작).
- **K3-LIN-004** — 같은 모양(Lv2 ← Lv1 주입력 + Lv1 보조입력). 보조입력 간선이 있는 유일한 자식. 스냅샷 대조 시험이 부모 수·순서 일치를 요구하므로 부모 5건 전부. 후손 0. 축: 격자 1280x1280(5건 모두)·기간 2023-05 겹침(7·8·9·10). LULC 는 2023-01-01 연 단위라 입도 무시 판정이면 불일치.
  - 열린 문제: 역할이 옛 케이스·정본과 다름 — HLS·LULC 가 주입력(옛 요약: HLS=검증자료, LULC=보조입력). 정답에 박기 전 원본 DATASETS.md 와 역할 대조 필요(§5 O4).
  - 열린 문제: 부모 5건 — k=3 에서 최대 3/5, J2 합격선 분모 변경.
  - 열린 문제: test_k3_lineage_probe._siblings graph 기준이 부모 자신을 형제에서 빼지 않아 형제 집합이 {Aspect}(실제 보조입력 부모) — 「형제만」 군 오염. 시험 결함 후보(§5 O10).

구조 결정(재박기 전):
- K1 [결정] 케이스 수 — `test_k3_candidate_recall.py` 104~106행은 스냅샷 쪽 「부모 있는 자식 == 4 · 간선 == 6」을 확인한다. v2 스냅샷은 부모 있는 자식 13 · 간선 18. (a) 위 4건(간선 9)을 쓰고 시험을 부분집합 대조로 바꾼다. (b) 13자식·18간선 전체로 재생성한다(모델 호출 수·J 분모 증가). 위 4건은 어느 쪽에도 포함된다.
- K2 [사실] `snapshot_level` 은 이름의 「(Lv.n)」에서 읽는데 새 이름에는 없다 → 열에서 읽도록 변경. 값 seq3·7=1, seq5·12=2.
- K3 [사실] topic 0/28 → 케이스 topic null, `_upload_meta` 가 subject 를 보내지 않음. 옛 실측의 filtered 전략 「주제」 신호 소실.
- K4 [사실] `corpus` 를 v2 로. (a) 기준 `sample_limits` = children 4 · edges 9 · candidate_population 28 · visible 28.

## 4. 영향

### 4-1. 서명 뒤 재박기 대상

| 파일 | 바뀌는 것 |
|---|---|
| `eval/k4-search/golden-cases.json` | 12문항 scope·required 를 서명본으로 교체, `snapshot` 을 v2 로. 질문 문장 무수정(intent WU4 ⑴). |
| `eval/k4-search/golden_baseline.py` | 134행 `!= 9` 를 스냅샷에서 읽은 건수로(다시 박지 않음, intent WU4 ⑵). 스냅샷 경로는 v2. |
| `eval/k4-search/golden-set.md` | 의미 기준 원문 유지. 사실 참조만 재박기 — 55·66·171~173·198~199행의 「9묶음·LD 접두·25건」, 문항별 옛 별칭·매핑 후보, 문항마다 「어느 데이터셋이 답인가」 한 줄(intent WU4 ⑹). 편집 범위는 서명 ② 대상(O2). |
| `eval/k4-search/fixtures/reference/expanded-normalized-02.json` | 손으로 고치지 않음 — `golden_baseline.py --mode expanded` 재실행 산출물로 교체(intent WU4 ⑷, README.md:107). |
| `eval/k4-search/fixtures/reference/dev-data-snapshot.json` | v1. 수정하지 않음 — 옛 ID 의 원본으로 보존(WU3 결정). 소비자만 v2 로 전환. |
| `eval/k3-lineage/lineage-cases.json` | v2 스냅샷의 parents 에서 재생성(intent WU4 ⑶). corpus 경로 v2, method 빈 값, upload_level 은 processing_level 열, topic null. sample_limits 는 §3 K1 결정에 따름. |
| `eval/k3-lineage/test_llm_lineage_probe.py` | 25~27행 OTHER·CHILD·KID 와 픽스처 이름·파일. CHILD/KID 는 seq3/seq5 로 대응되나 OTHER(RN15 보조입력) 간선은 새 코퍼스에 없어 픽스처 재설계 필요. |
| `services/core-api/tests/test_k3_candidate_recall.py` | 104~106행 `== 4`·`== 6`, 187행 `edges == 6` — v2 스냅샷 계수(부모 있는 자식 13 · 간선 18)와 케이스 계수가 갈라짐. K1 결정에 따라 부분집합 대조 또는 전체 대조로 변경. |
| `stage-evidence-packet-02.json` | 이름 기준 유지. 옛 이름 9건·설명 문서를 가리키므로 `reference_evidence.py --verify` 로 부재 항목을 드러낸 채 빼거나 재수집(intent WU4 ⑸). |

옛 ID 를 담은 그 밖의 파일 — `dev-package/intent/2026-09-24-k3-lineage-suggestion-resume.md` · `dev-package/prd/rounds/R-K3-RESUME.md` 는 과거 기록이라 재박기 대상이 아니다.

### 4-2. 측정에 영향을 줄 수 있는 알려진 이상

| 이상 | 영향 |
|---|---|
| variables 0/28 · 변수 행 0 | 011 근거는 유지되나 변수 축 신호 0. K3 apply_snapshot_autometa 의 변수 축도 비어 있음. |
| 계보 method 0/18 | K3 정답 method 빈 값. 004·006 의 처리 근거(NDVI 추출·검증 역할)를 계보로 설명 불가. |
| topic 0/28 · source_label 0/28 | K4 설명 벡터에 주제어 없음. K3 filtered 전략의 「주제」 matched_by 신호 소실(옛 6간선 전부에 있었음). |
| summary 축약 | 대상지(경기 남부~충청권)·시군구·2 km→100 m 균등분할·처리 사슬·「연구대상지」 낱말 소실 — 001·002·007·008·009·012 의미 판정 재료 공백. |
| 설명 문서 6개 미적재(1,251,824 B) | pptx 1·docx 4·ipynb 1. golden-set.md 18·119·136~137·154·182·191행과 증거 패킷이 이 파일을 근거로 듦. |
| 계보 역할 충돌 | Prediction ← HLS·LULC 주입력(정본: 검증자료·보조입력), pred_sample ← rn15_sample 주입력(정본: 검증). 005·006·K3-LIN-004 에 영향. |
| crs 빈 값 4건 | seq13·14(gpkg, format·grid 도 빈 값) · seq23·24(HLS 변환 결과, 원인 미확인). 008·009 의 형식 축 신호 없음. |
| 파생 단계 ≠ 사람 단계 5건 | seq8·9·11·13·14 주입력 부모 없음 → 파생 0. K3 적격 필터(max) 영향 없음. 13·14 는 K3 자식 불가. |
| 「천리안」 0회 | 004·012 질문 낱말이 메타에 없음(전부 GK-2A). 동의어 확장 의존. |
| required 건수 증가 | 005 1→4, 006 2(구성 변경), 008 1→2 — retrieval 자동 판정 엄격화. 옛 기준선과 수치 직접 비교 불가. |

## 5. Ted 판정이 필요한 열린 문제

- **O1** D1 — 002~012 scope 를 A(level-data 14건) 또는 B(28건 전체) 중 무엇으로 할지. 권고 A. 010 의 엄격도와 기대 응답 「확인한 N개」 문구가 이 결정에 달림.
- **O2** golden-set.md 사실 참조 재박기 범위 승인 — 55·66·171~173·198~199행 수치·「LD 접두」, 문항별 옛 별칭·매핑 후보·근거 문서 경로. 의미 기준 문장은 무수정. 사라진 근거 문서(docx 등)를 가리키는 줄을 주석으로 둘지 삭제할지.
- **O3** 001·002 에서 HLS_S30_NDVI_mean_202305(seq8)를 「허용 동반 후보」로 명시할지(C1 수동 판정 기준).
- **O4** 계보 역할 정정 여부 — Prediction ← LULC(보조입력?)·HLS(검증?), pred_sample ← rn15_sample(검증?). 자료 쪽 수정이면 dev 재적재 경로, 아니면 K3-LIN-004 정답에 현 역할(주입력)을 그대로 박음. 골든 수정 사항 아님.
- **O5** 012 에서 HLS(seq8)를 「100 m 관측」으로 제시하면 오답으로 처리할지(SEMANTIC 제안, STRICT 미언급).
- **O6** 006 에서 rn15 원자료(seq2)를 검증자료로 제시한 경우 관련 후보인가 오답인가(정본 미명시).
- **O7** 근거 재료 공백 처리 — 평가 전에 설명 문서 적재·summary 보강 또는 증거 패킷 재수집을 할지, 아니면 수동 판정에서 「준비 실패」로 분리 기록할지(C2·C4, 007 연속 시계열, 008 시군구, 011 결측 처리, 012 균등분할).
- **O8** K1 — K3 케이스를 4건(자식 4·간선 9)으로 유지하고 시험을 부분집합 대조로 바꿀지, 13자식·18간선 전체로 재생성할지(모델 호출 수·J 분모 증가).
- **O9** K3 에 4←2(rn15_sample ← rn15, 옛 RN15 보조입력 간선의 후신)·13/14(빈 제안이 정답인 대조) 케이스를 추가할지.
- **O10** test_k3_lineage_probe._siblings 의 graph 형제에 부모 자신이 섞이는 문제(LIN-004 에서 Aspect) — 재박기 전에 고칠지 별건으로 둘지.

## 6. 미검증·범위

- 검색·모델 호출은 하지 않았다. 순위·상위 N 잘림 영향은 WU5 재측정에서 확인한다.
- 계보 역할의 원본(DATASETS.md) 대조는 두 제안의 인용에 기댔고 이 문서에서 원문을 다시 읽지 않았다.
- CRS 표기 동치 판정(LIN-002)·seq23·24 crs 빈 값 원인은 미확인.
- 증거 패킷 `--verify` 는 실행하지 않았다(WU4 ⑸ 몫).

## 7. dev 보정(O4·O7) — 2026-09-25

### 7-1. 되돌리기용 이전 상태 (쓰기 전 기록)

읽기 = BYPASSRLS 백업 URL · `begin read only; … rollback;`(`transaction_read_only = on`) · 2026-09-24T19:26:47Z(UTC) · 배포 `dev-ea21d8c2aa54` · 데이터셋 28 · 간선 18(주입력 16 · 보조입력 2). 같은 값을 제품 API `GET /datasets/{id}`·`GET /datasets/{id}/lineage` 로 다시 읽어 일치를 확인했다.

간선(대상 자식 3건의 부모 전부 · method 전부 NULL · origin 전부 `manual` · 확인 계정 = 데이터셋 소유자):

| 자식 | 부모 | 역할(이전) | 간선 ID(이전) | confirmed_at(이전, UTC) | 이번 변경 |
|---|---|---|---|---|---|
| rn15_sample | rn15 15분 누적강수 | 주입력 | `01M39TB4Q65R4Z0C17V2F79GW6` | 2026-09-24T13:40:38Z | 없음 |
| pred_sample | hsr_sample | 주입력 | `01M39TCASYVJR5MW2CRMSCTAA0` | 2026-09-24T13:41:17Z | 없음 |
| pred_sample | rn15_sample | 주입력 | `01M39TCAT1HV1AJVWXGHMGVPZE` | 2026-09-24T13:41:17Z | → 보조입력 |
| Prediction (공간상세화) | GK2A_NDVI_mean_202305 | 주입력 | `01M39TZ0YADJ2AXTDNDSX52MAN` | 2026-09-24T13:51:30Z | 없음 |
| Prediction (공간상세화) | HLS_S30_NDVI_mean_202305 | 주입력 | `01M39TZ0YE71NTNG636JX3KD89` | 2026-09-24T13:51:30Z | → 보조입력 |
| Prediction (공간상세화) | DEM | 보조입력 | `01M39TZ995E1F21KS6P40GMGW0` | 2026-09-24T13:51:38Z | 없음 |
| Prediction (공간상세화) | Aspect | 보조입력 | `01M39TZ9G5MN8793E81AFHF9GE` | 2026-09-24T13:51:38Z | 없음 |
| Prediction (공간상세화) | LULC_2023 | 주입력 | `01M39TZ0YH28F87RBSY6QWAP4F` | 2026-09-24T13:51:30Z | → 보조입력 |

설명(summary) 이전 값:

| seq | 이름 | ID | 이전 summary | updated_at(이전, UTC) |
|---|---|---|---|---|
| 3 | hsr_sample | `01M39TA6QY5NEAR8ZPZ6AF9KNE` | WGS84 변환·crop 한 HSR 전처리 자료 | 2026-09-24T13:40:08Z |
| 4 | rn15_sample | `01M39TB4NTBCFC8TSTNB93N5YP` | WGS84 변환·crop 한 rn15 전처리 자료 | 2026-09-24T13:40:38Z |
| 5 | pred_sample | `01M39TCARM2C2NJ8S9SA4QBSER` | U-Net 기반 강수 예측 결과 | 2026-09-24T13:41:17Z |
| 6 | GK-2A 일 단위 식생자료 | `01M39TK0F5P3W4APB91N08KTMY` | GK-2A AMI 일 단위 식생 원본 | 2026-09-24T13:44:56Z |
| 7 | GK2A_NDVI_mean_202305 | `01M39TSEPR820QBZ1DBBFKDJEP` | GK-2A 기반 2023-05 월평균 NDVI | 2026-09-24T13:48:27Z |
| 8 | HLS_S30_NDVI_mean_202305 | `01M39TT0S5PSJ0DQNR0XMTHFNW` | 검증용 HLS S30 2023-05 월평균 NDVI | 2026-09-24T13:48:46Z |
| 12 | Prediction (공간상세화) | `01M39TZ0SCEYHHMBWZ991M1QGN` | U-Net 기반 100 m 일 단위 NDVI 예측 | 2026-09-24T13:51:30Z |
| 13 | SPI-4weeks | `01M39V005J6SQ9SW8MZ8D16ZWK` | 4주 SPI 유의구간 벡터 (L1 Calibrated) | 2026-09-24T13:52:02Z |
| 14 | SPEI-4weeks | `01M39V0T17DHQ5PF5XSSERTZ8H` | 4주 SPEI 유의구간 벡터 (L1 Calibrated) | 2026-09-24T13:52:28Z |

되돌리는 법(같은 공식 API) — 역할: `DELETE /api/v1/datasets/{자식}/lineage/parents/{부모}` → `POST /api/v1/datasets/{자식}/lineage/parents` `{"parentDatasetId": 부모, "parentRole": "주입력"}`. 설명: `PATCH /api/v1/datasets/{id}` `{"summary": 이전 값}`. 간선 ID·confirmed_at 은 API 로 되살릴 수 없다(새 관계가 새 ID·새 시각을 받는다).

### 7-2. 쓴 경로 — 배포 코드 `ea21d8c2aa54` 의 공식 API

| 목적 | API | 근거(`git show ea21d8c2aa54:<경로>`) |
|---|---|---|
| 로그인 | `POST /api/v1/sessions` `{accountName, password}` → 201 `token` | `services/core-api/src/colab_core/app/routes/session.py:66` · 접두 `main.py:47` `API_PREFIX = "/api/v1"` |
| 역할 변경 ⑴ 관계 제거 | `DELETE /datasets/{자식}/lineage/parents/{부모}` → 204 | `routes/lineage.py:238-252` |
| 역할 변경 ⑵ 관계 재부착 | `POST /datasets/{자식}/lineage/parents` `{parentDatasetId, parentRole}` → 201. 역할 2값 검사 214-216행, 부모 Lv ≤ 자기 Lv 검사 224-226행, origin 은 언제나 `manual` | `routes/lineage.py:192-235` |
| (역할 수정 전용 op 없음) | `PATCH …/lineage/parents/{부모}` 는 `method` 만 받는다 — 「`parentRole` 을 받지 않는다 … 관계를 다시 세우는 일이다(`removeLineageParent` → `addLineageParent`)」 | `routes/lineage.py:255-289`(축자 265-266행) |
| 설명 수정 | `PATCH /datasets/{id}` `{summary}` → 200 | `routes/catalog.py:1227` · 허용 열쇠 809행 · 빈 값·공백 거절 1278-1281행(`is_blank_summary` 954행) |
| 설명 상한 | 서버·계약에 상한 없음(`contracts/seams/fe-core.yaml:5095-5105` `type: string` · `minLength: 1`). 화면 등록 칸만 3000자(`frontend/src/components/upload/RegisterArea.tsx:662` · 6705675d) | — |
| 역할 값 집합 | `주입력`·`보조입력` 2값 — 「검증자료」는 역할로 표현 불가, 설명 문장에만 적었다 | `db/platform/schema.sql:1043-1044` |

로그인 계정 = 재시드 러너가 쓴 연구실 교수 계정(데이터셋 소유자). 러너 작업 자리의 계정 목록·상태 파일에서 읽었고, 교수 역할 계정이 1건 · 러너 로그인 계정과 같음 · 스냅샷 v2 의 소유자와 같음 세 가지를 쓰기 전에 대조했다(값은 출력하지 않음). 세션은 끝에 `DELETE /api/v1/sessions/current`(204)로 닫았다.

### 7-3. 요청 기록 (KST · 본문 값·토큰 없음)

확인 실행(쓰기 없음) 14건 — 04:26 경 `POST /sessions` 201 · `GET /datasets/{id}` 9건 200 · `GET …/lineage` 3건 200 · `DELETE /sessions/current` 204.

쓰기 실행 29건 — 2026-09-25 04:28:45~04:28:48:

| # | 요청 | 상태 |
|---|---|---|
| 1 | `POST /api/v1/sessions` | 201 |
| 2~10 | `PATCH /api/v1/datasets/{id}` `{summary}` — seq 3·4·5·6·7·8·12·13·14 (ID 는 7-1 표) | 200 × 9 |
| 11 | `DELETE /api/v1/datasets/01M39TZ0SCEYHHMBWZ991M1QGN/lineage/parents/01M39TT0S5PSJ0DQNR0XMTHFNW` (Prediction ← HLS) | 204 |
| 12 | `POST /api/v1/datasets/01M39TZ0SCEYHHMBWZ991M1QGN/lineage/parents` `{parentDatasetId: HLS, parentRole: 보조입력}` | 201 |
| 13 | `DELETE /api/v1/datasets/01M39TZ0SCEYHHMBWZ991M1QGN/lineage/parents/01M39TW21793T8631ATHJREHK5` (Prediction ← LULC_2023) | 204 |
| 14 | `POST /api/v1/datasets/01M39TZ0SCEYHHMBWZ991M1QGN/lineage/parents` `{parentDatasetId: LULC_2023, parentRole: 보조입력}` | 201 |
| 15 | `DELETE /api/v1/datasets/01M39TCARM2C2NJ8S9SA4QBSER/lineage/parents/01M39TB4NTBCFC8TSTNB93N5YP` (pred_sample ← rn15_sample) | 204 |
| 16 | `POST /api/v1/datasets/01M39TCARM2C2NJ8S9SA4QBSER/lineage/parents` `{parentDatasetId: rn15_sample, parentRole: 보조입력}` | 201 |
| 17~25 | `GET /api/v1/datasets/{id}` 9건 — 저장된 summary = 보낸 문장 9/9 | 200 × 9 |
| 26~28 | `GET /api/v1/datasets/{id}/lineage` — Prediction · pred_sample · rn15_sample | 200 × 3 |
| 29 | `DELETE /api/v1/sessions/current` | 204 |

SQL 쓰기 0 · reseed/reset 실행 0 · 다른 계정 로그인 0.

### 7-4. 쓴 설명 문장 (정확한 저장값)

출처 = `DATASETS.md` 기계 블록의 `description`(레포 사본 `dev-package/reports/reference-data/datasets-md/`). 원문과 다른 곳은 굵게 표시한 두 가지뿐이다.

| seq | 이름 | 저장한 summary | 원문과 다른 점 |
|---|---|---|---|
| 3 | hsr_sample | HSR 반사도를 기상청 제공 lat·lon 파일에 맞추어 WGS84 로 좌표계 변환하고, 특정 연구대상지를 중심으로 crop 한 전처리 자료. 형태는 (10, 128, 128). 첫 축 10 은 2019~2024 년에 흩어진 불연속 표본 시각이며 연속 계열이 아니다. | **끝 문장 추가** — 강수 md 판정 ㈏ 확정(설명 칸에 「연속 계열 아님」 명시)·원자료 시각 10점·`canonical-metadata.json` 기간 근거 「10개 불연속 표본」. 골든 007 오답 「연속 시계열로 단정」의 판정 재료 |
| 4 | rn15_sample | rn15 15분 누적강수를 기상청 제공 lat·lon 파일에 맞추어 WGS84 로 좌표계 변환하고 연구대상지를 중심으로 crop 한 전처리 자료. 형태는 (10, 128, 128). 첫 축 10 은 2019~2024 년에 흩어진 불연속 표본 시각이며 연속 계열이 아니다. | **끝 문장 추가**(seq3 과 같은 근거) |
| 5 | pred_sample | 레이더 반사도 격자를 입력으로 받아 같은 격자의 강우 분포를 출력하는 U-Net 기반 모델의 예측 결과. 입력은 hsr_sample.npy, 검증은 rn15_sample.npy 다. 형태는 (10, 128, 128). 첫 축 10 은 2019~2024 년에 흩어진 불연속 표본 시각이며 연속 계열이 아니다. | **끝 두 문장 추가** — 형태는 md 상세 「파일」 줄, 나머지는 seq3 과 같은 근거 |
| 6 | GK-2A 일 단위 식생자료 | 국가기상위성센터가 제공하는 GK-2A le2 식생자료. 좌표계는 Lambert Conformal Conic, 시/공간해상도는 1일 / 2 km 다. 파일 하나에 NDVI·EVI·FVC·DQF·좌표계 정의 5개 자료가 들어 있고 이 흐름은 NDVI 만 사용한다. | 없음(축자) |
| 7 | GK2A_NDVI_mean_202305 | DQF 로 품질 저하 픽셀을 NaN 으로 바꾸고 유효 범주 -1~1 밖을 NaN 처리한 뒤, 원자료 좌표계 LCC 를 WGS84 로 변환해 NDVI 레이어만 TIF 로 저장한 자료. 경기도 남부~충청권 일대로 영역을 추출하고 2 km 를 100 m 로 균등 분할한 뒤 일 단위를 월 단위 평균으로 변환했다. | 없음(축자) |
| 8 | HLS_S30_NDVI_mean_202305 | Lv.2 공간상세화 모델의 검증자료. HLS S30 자료의 Red·NIR 밴드로 NDVI 를 계산하고 3~7일 간격 자료를 월평균 100 m 로 변환한 것이다. | 없음(축자) |
| 12 | Prediction (공간상세화) | U-Net 기반 공간상세화 모델의 산출물. 월평균 GK-2A NDVI 와 수치표고모형·경사향·토지피복지도를 입력으로, 월평균 HLS NDVI 를 검증자료로 학습했다. Lv.1 과 달리 Lv.0 처럼 일 단위 시간해상도를 갖고 지형 변화에 따른 NDVI 변화가 픽셀별로 다르게 나타난다. | 없음(축자) |
| 13 | SPI-4weeks | 대한민국 내 기상관측소의 강우 관측자료로 산정한 4주 SPI 를 시군구 단위로 담은 벡터 자료. 각 관측소의 주소지를 기준으로 그 관측자료가 소재 시군구를 대표한다고 가정해 구축했다. 2000-01-01 ~ 2025-12-20 을 주 단위로 담는다. 제품 값은 Lv1 이고 출처 문서의 데이터 레벨 축자는 「L1 Calibrated」다. | **끝 날짜 2025-12-31 → 2025-12-20** — `canonical-metadata.json` 기간 근거 「실물 파일 시간 범위; 문서의 12-31보다 실물 우선」, dev 기간 칸과 일치 |
| 14 | SPEI-4weeks | 대한민국 내 기상관측소의 강우 관측자료로 산정한 4주 SPEI 를 시군구 단위로 담은 벡터 자료. 각 관측소의 주소지를 기준으로 그 관측자료가 소재 시군구를 대표한다고 가정해 구축했다. 2000-01-01 ~ 2025-12-20 을 주 단위로 담는다. 제품 값은 Lv1 이고 출처 문서의 데이터 레벨 축자는 「L1 Calibrated」다. | **끝 날짜 2025-12-31 → 2025-12-20**(seq13 과 같은 근거) |

- 길이 89~189자 — 상한(화면 3000자) 안이라 사실 발췌 없이 전문을 넣었다.
- 지시문 최소 범위(seq 3·4·5·7·8·12·13·14) ＋ **seq6 추가**: 004(「가공 과정에서 NDVI 추출」)·012(천리안 일별 2 km)의 근거 공백(§2-3)이 seq6 의 옛 한 줄 요약에 있었다.
- seq 1·2·9·10·11·15~28 은 바꾸지 않았다(9·10 은 `registrationNote` 를 러너 검증이 요구한다).

### 7-5. 검증

- API — 쓰기 뒤 `GET /datasets/{id}` 9건의 summary = 보낸 문장 9/9. `GET …/lineage`: Prediction ← GK2A_NDVI_mean_202305 주입력 · HLS·DEM·Aspect·LULC_2023 보조입력 / pred_sample ← hsr_sample 주입력 · rn15_sample 보조입력 / rn15_sample ← rn15 주입력(무변경). method 전부 null. `processingLevel` 무변화(pred_sample·Prediction 2 · 나머지 0/1).
- BYPASSRLS 읽기(2026-09-24T19:28:54Z · `transaction_read_only = on` · 배포 `dev-ea21d8c2aa54`) — 데이터셋 28 · 간선 18(주입력 13 · 보조입력 5). 새 간선 ID: pred_sample ← rn15_sample `01M3AE8MRWX9HKE1ZSWCGGB1JD` · Prediction ← HLS `01M3AE8MHD8GQX87H7GRNJ73VY` · Prediction ← LULC_2023 `01M3AE8MN0CCDM2GRC9NK4XED3`(origin `manual` · 확인 계정 = 소유자 · method NULL). 나머지 5간선은 ID·confirmed_at 무변화. summary 9/9 가 보낸 문장과 같음. `d4_lineage_unknown` 대상 0건.
- 관측 — `PATCH` 뒤에도 `d3_dataset_description.updated_at` 이 바뀌지 않았다(9건 모두 이전 값 그대로). 아래 7-9 후속.

### 7-6. 재시드 정본 반영 (다음 재시드가 같은 상태를 만든다)

| 파일 | 변경 |
|---|---|
| `dev-package/tools/dev-seed/canonical-metadata.json` | `auxiliaryParents` 2 → 5건(pred_sample ← rn15_sample · Prediction ← HLS·DEM·Aspect·LULC_2023). seq 3·4·5·6·7·8·12·13·14 행에 `registrationSummary`(7-4 의 문장과 글자 단위 동일) |
| `dev-package/tools/dev-seed/build_plan.py` | 보조입력 정본 집합을 상수 `EXPECTED_AUXILIARY`(5건)로. `registrationSummary` 가 있으면 md 한 줄 요약을 대체(빈 값·3000자 초과는 거절), 그 뒤 `registrationNote` 를 기존대로 덧붙인다 |
| `dev-package/tools/dev-seed/tests/test_build_plan.py` | 보조입력 5건 결합 · 옛 2건 집합 거절 · 대체·덧붙임 · 빈 값/초과 거절 · 커밋된 정본의 역할·설명 사실 확인 — red 6건 확인 뒤 green |
| `dev-package/tools/dev-seed/README.md` | 정본 사슬의 예외 셋(기간·보조입력·등록 설명) 한 단락 |

- `plan-manifest.yaml` 은 바꾸지 않았다 — 등재표는 md 한 줄 요약을 싣는 생성물이고(`build_manifest`), 러너는 덧씌운 값이 실린 `upload-plan.json` 을 친다. md 정본(참조자료 뿌리)도 바꾸지 않았다.
- 러너는 부모별 역할을 이미 일반화해 처리한다(`runner.py` `split_lineage_parents` → 등록 카드엔 주입력만, 보조입력은 공식 계보 API 로 추가 · 검증 단계가 역할까지 대조).
- 레포 md 사본 ＋ 새 정본으로 계획 행을 결합해 dev 쓰기 뒤 상태와 대조 — summary 9/9 · 대상 간선 8/8 역할 일치(시험 밖 일회 대조).

### 7-7. 스냅샷 재포획 (`eval/k4-search/fixtures/reference/dev-data-snapshot-v2.json`)

`recapture_snapshot.py` 읽기 전용 재실행(2026-09-24T19:31:04Z) · 검증 11건 전부 통과(`edge_roles_vs_plan` 은 새 `auxiliaryParents` 기준). 옛 v2 와의 차이:

- ID 28건·순서·`dev-name-id-v2.json` 동일(이름→ID 표는 다시 쓰지 않음).
- `counts.edges_by_role` 보조입력 2 · 주입력 16 → 보조입력 5 · 주입력 13. 그 밖의 계수 동일(부모 있는 자식 13 · 간선 18 · Lv0 10/Lv1 16/Lv2 2).
- `summary` 9건(seq 3·4·5·6·7·8·12·13·14)이 7-4 문장으로.
- `parents` 2건 — pred_sample: rn15_sample 주입력 → 보조입력 / Prediction: HLS·LULC_2023 주입력 → 보조입력(정렬 = 역할 → 부모 ID).
- `captured_at` 만 그 밖에 바뀜. 배포 `ea21d8c2aa54` 동일.

§3 표·같은 폴더 JSON 의 K3 부모 역할과 §4-2 「계보 역할 충돌」 행은 보정 **전** 상태다. 재박기는 이 스냅샷의 역할을 쓴다.

### 7-8. 재박기로 넘기는 결정 (이 커밋에서 골든·K3 파일은 수정하지 않음)

- O3·O5·O6 승인 — 001·002 에서 seq8 HLS 는 허용 동반 후보 · 012 에서 「100 m 관측」으로 제시하면 오답 · 006 에서 seq2 는 관련 후보(오답 아님).
- 010 (scope A) — 수동 판정 문구의 「실제 검색 범위 고지」를 14건에 맞춰 다시 적는다.
- K3 — 제안 4건 유지 ＋ 5번째 케이스. `sample_limits` 에 `snapshot_children_with_parents` 13 · `snapshot_edges` 18 을 두고 `test_k3_candidate_recall.py` 104~106행 대조를 그 값으로 해 드리프트 검출을 유지. `services/core-api/tests/test_k3_lineage_probe.py:92` `_siblings` graph 갈래에 `other not in mine` 누락(형제에 부모가 섞임) 수정.
- ⚠ 5번째 케이스의 지시 축자는 「4 ← 2 as 보조입력 after the role fix」다. 이번 보정(O4) 뒤에도 dev 의 4 ← 2(rn15_sample ← rn15)는 **주입력**이다 — O4 대상이 아니고, rn15_sample 의 유일한 부모라 보조입력이면 주입력 부모가 없어진다. 보정 뒤 보조입력인 강수 간선은 5 ← 4(pred_sample ← rn15_sample)다. 재박기 전 사용자 확인 필요.
- K3-LIN-003(pred_sample)·K3-LIN-004(Prediction)의 정답 역할은 7-7 스냅샷 기준으로 바뀐다 — LIN-003: hsr_sample 주입력 · rn15_sample 보조입력 / LIN-004: GK2A_NDVI 주입력 · HLS·DEM·Aspect·LULC_2023 보조입력.

### 7-9. 하지 않은 것 · 후속

- 골든(`golden-cases.json`·`golden-set.md`·`golden_baseline.py`)·K3(`lineage-cases.json`·시험) 재박기 — WU4 본 작업 몫. 이 커밋은 선행 조건 O4·O7 과 서명 기록까지.
- 설명 칸 보강은 검색 순위에 쓰이는 설명 벡터·색인이 새 문장으로 다시 계산됐는지 확인하지 않았다(검색·모델 호출 0회). WU5 재측정 전에 확인 필요.
- `PATCH /datasets/{id}` 가 `d3_dataset_description.updated_at` 을 올리지 않는다(7-5). 어느 게이트·시험도 이 열의 갱신을 보지 않는다 — 별건 후속.
- 사라진 설명 문서 6개(docx·pptx·ipynb) 적재·증거 패킷 재수집(O7 의 다른 선택지)은 하지 않았다.
