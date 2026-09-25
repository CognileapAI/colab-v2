# K3 계보 제안 — 보류 값 재측정 (2026-09-25 · held)

> **첫 줄 — 표본이 작다(자식 6 · 엣지 10), 업로드 입력은 제안 시점 보류 값(기간 0/6 · variables 6/6)이다.** crs 축은 `WGS84 (기준 격자 파일)` 동일 문자열 12 데이터셋 안에서 가르지 못한다. 보류 사건 없는 자식 0/6 · 78 없음. 판정: J1 충족 · J3'·J6·J7 0건 · **⑴′ 두 팔 red · ⑵ 규칙 팔 red(DEM)** · 모델 침묵 43/48. 미달은 「판정 보류 · 표본 확장」이다. K3 플래그는 켜지 않는다.

측정이지 게이트가 아니다. 판정 기준은 측정 전에 등록한 `dev-package/reports/corpus-expansion/wu5-k3-held-preregistration-2026-09-25.md`
(커밋 `9cf99b18` · 등록 2026-09-25T09:37:02+09:00)와 그 문서가 따르는 `wu5-preregistration-2026-09-25.md` §4·§5 를 그대로 읽는다.
이 문서는 새 선을 만들지 않는다. 등록에 없는 지표는 「사후 추가」로 표시했다.

## 요지

- 세 실행 모두 **78 없이 완주**했다. 후보 절반 종료코드 0 · 모델 절반 본측정 0 · 상한 민감도 0.
- 모델 호출: 본측정 **48회** · 민감도 **48회**(비공허 칸 24 × 2회. 등록의 「약 40회」는 추정값이고 실제 수를 여기 적는다). 후보 절반 0회.
- 규칙 팔: J2 hit@1 **2/10** · hit@3 **6/10**(descriptive only). 근거 축 crs 60 · grid 33 · fileName 25 · period 0 · variables 0.
- 모델 팔(ⓑ 보류 값): 침묵 **43/48**. J2 hit@3 0/10 · 0/10. 최종 근거 축 crs 5 · grid 1.
- 상한 민감도(ⓐ 스냅샷 autometa · 합격선 아님): 칸 48 중 **입력 빈곤 8 · 모델·프롬프트 25 · ⓑ 발화 5 · 측정 불가(ⓐ timeout) 10 → 「섞임」**(§4).
- 대조군: ⑴′ `removed_and_siblings` 규칙 **2/6 red** · 모델 **9/12 red**. ⑵ `descendants` 규칙 **5/6 red**(DEM → Aspect · 원인 「축 대조가 부모/후손 방향을 못 가름」) · 모델 12/12 green(공허 10).

## 명령 (비밀값 없음)

```
# ⑴ 후보 절반 — 일회용 DB · 모델 호출 0 (준비 단계 · 등록 커밋 뒤 · 결과 커밋 484747aa)
COLAB_K3_PROBE_OUT=<워크트리>/dev-package/reports/k3-lineage-probe/2026-09-25-held/j1-2026-09-25-held.json \
COLAB_K3_CANDIDATES_OUT=<워크트리>/dev-package/reports/k3-lineage-probe/2026-09-25-held/candidates-2026-09-25-held.json \
  bash gates/tools/service-tests.sh core-api k3_probe
# → 2 passed · 종료코드 0

# ⑵ 모델 절반 본측정 — OPENAI_API_KEY 는 운영자 로컬 환경 파일에서 이 프로세스에만 넣었다(값 미출력)
services/core-api/.venv/bin/python eval/k3-lineage/llm_lineage_probe.py --arm both --repeats 2 \
  --candidates dev-package/reports/k3-lineage-probe/2026-09-25-held/candidates-2026-09-25-held.json \
  --output dev-package/reports/k3-lineage-probe/2026-09-25-held/luna-2026-09-25-held.json
# → 종료코드 0 · model_calls 48

# ⑶ 상한 민감도 — 같은 후보 JSON · 업로드 메타만 ⓐ 로 교체 · 모델 팔만
services/core-api/.venv/bin/python eval/k3-lineage/llm_lineage_probe.py --arm model --repeats 2 \
  --candidates dev-package/reports/k3-lineage-probe/2026-09-25-held/candidates-2026-09-25-held.json \
  --upload-meta-override eval/k3-lineage/fixtures/snapshot-autometa-upload-meta-2026-09-25.json \
  --output dev-package/reports/k3-lineage-probe/2026-09-25-held/luna-sensitivity-autometa-2026-09-25-held.json
# → 종료코드 0 · model_calls 48 · d10.suggest.unreachable TimeoutError 10건(J8 측정값)
```

- 키 주입: core-api venv 해석기의 `-c` 한 줄이 환경 파일에서 `OPENAI_API_KEY` 한 줄만 읽어 `os.environ` 에 넣고 `runpy.run_path(<러너>, run_name='__main__')` 로 러너를 실행했다. 러너 인자·경로는 위와 같다.
- 모델·설정 = 등록 §1 그대로: `gpt-5.6-luna`(기본값) · `--timeout 8.0` · `--repeats 2` · `seed 20260924`(`suggest_wire.py` 고정값) · `--base-url`·`--groups` 기본값.
- 해석기 = `services/core-api/.venv/bin/python`(등록 §1 · 2026-09-25-corpus28 과 같음).
- 같은 후보 JSON: 두 결과의 `candidates_sha256` = **`f6dc9ad6…`**(같음) · `candidates_local_sha 9cf99b18`.
- 제품 동일성: `system_prompt_sha256 0f71e746…` · `suggester_sha256 a2437a42…` · `verifier_sha256 b4d30a69…` · `signals_sha256 480de539…` — 두 결과와 2026-09-25-corpus28 결과가 네 값 모두 같다.
  `runner_sha256 bced0dd0…`(두 결과 같음 · corpus28 의 `5735c593…` 와 다름 — 등록 §3 의 `--upload-meta-override` 추가분) · `local_sha 484747aa`.
- 민감도 결과 `upload_meta_override.sha256 2bcca50f…` · `kind` 에 「상한 민감도 … 합격선 아님」.

### 등록과 다르게 한 것 · 기록

| 항목 | 등록 | 실제 | 이유 |
|---|---|---|---|
| ⑴ 후보 절반 실행 시점 | §3-1 | 준비 단계에서 등록 커밋(09:37:02) 뒤 1회 실행 · 결과 커밋 `484747aa`(09:37:53). 이번 단계에서 다시 돌리지 않았다 | 등록 §7 「새 파일 · 있으면 78」. 모델 절반·민감도가 같은 후보 JSON 을 써야 한다(§3) |
| 모델 호출 수 | 「약 40회」 | 48회 × 2 실행 | 비공허 칸 24(30 칸 − 공허 6) × 2회. 등록은 실제 수를 `model_calls` 로 적게 했다 |
| 민감도 timeout | — | 10/48 칸 `TimeoutError`(8초) · 재시도 없음 | 등록 §2: timeout 은 78 이 아니라 J8 측정값이다. 해석 칸에서는 「측정 불가」로 따로 센다(§4) |

## §1 표본 · 입력 확인

| 항목 | 등록 값 | 이번 결과 |
|---|---|---|
| 자식 · 엣지 · 모집단 | 6 · 10 · 28 | `sample_limits` 6 · 10 · 28(두 결과 같음) |
| 업로드 축(후보 JSON `cases[].upload_axes`) | 6/6 이 file_name 외 축 · 정답과 같음 | 6/6 이 crs · grid · variables 를 가짐 · period 0/6 · 러너 대조 통과(78 없음) |
| 보류 사건 없는 자식 | 0/6 | 0/6 |
| 후보 쪽 축 | period 28 · crs 24 · grid 26 · variables 0 · fileName 28 | 같음(`autometa_axes_present`) |

| 자식 | Lv | 정답 부모 | 업로드 축(보류 값) |
|---|---|---|---|
| 001 hsr_sample | 1 | 1 | `hsr_sample.npy` · WGS84 (기준 격자 파일) · 128x128 · [hsr_sample] |
| 002 GK2A_NDVI_mean_202305 | 1 | 1 | `GK2A_NDVI_mean_202305.tif` · EPSG:4326 · 1280x1280 · [band1] |
| 003 pred_sample | 2 | 2 | `pred_sample.npy` · WGS84 (기준 격자 파일) · 128x128 · [pred_sample] |
| 004 Prediction (공간상세화) | 2 | 5 | `Prediction_20230501.npy` · WGS84 (기준 격자 파일) · 1280x1280 · [Prediction_20230502] |
| 005 rn15_sample | 1 | 1 | `rn15_sample.npy` · WGS84 (기준 격자 파일) · 128x128 · [rn15_sample] |
| 006 DEM | 1 | 0 | `DEM.tif` · EPSG:4326 · 1280x1280 · [band1] |

## §4-1 후보 절반 — J1 recall@k (`j1-2026-09-25-held.json`)

| 전략 | recall@5 | @10 | @20 | missed@20 | 자식별 모집단 |
|---|---|---|---|---|---|
| `recent` | 0/10 | 0/10 | 4/10 | 6 | 29 × 6 |
| `filtered`(제품) | 8/10 | **10/10** | **10/10** | 0 | 8 · 8 · 7 · 6 · 6 · 6 |

- J1 선 = 엣지 전건 10/10 → `filtered` @10·@20 충족. 모집단이 전부 20 이하라 @20 은 모집단 전체 포함 여부다.

## §4-2 군별 후보 수 (`candidates-2026-09-25-held.json`)

| 군 | 001 · 002 · 003 · 004 · 005 · 006 | 공허(0건) |
|---|---|---|
| main | 7 · 7 · 7 · 6 · 5 · 5 | 0 |
| ⑴ removed | 6 · 6 · 5 · 1 · 4 · 5 | 0 |
| ⑵ descendants | 0 · 0 · 0 · 0 · 0 · **1** | 5 |
| ⑶ siblings | 12 · 12 · 1 · 0 · 12 · 11 | 1 |
| ⑴′ removed_and_siblings | 4 · 1 · 4 · 1 · 3 · 1 | 0 |

- 측정 성립 조건 ⓑ(등록 §5): ⑵ `survived` > 0 자식 = **1**(DEM · 예상과 같음). 나머지 `population` · `in_pool` · `survived`:
  001 1 · 0 · 0 / 002 1 · 1 · 0(Lv 차단 1) / 003 0 · 0 · 0 / 004 0 · 0 · 0 / 005 1 · 0 · 0 / 006 2 · 2 · **1**(Aspect · Lv 차단 1). ⑵ 공허 5.

## §4-4 두 팔 · §4-5 J1~J9

| # | 규칙 팔 (1회 · 모델 0) | 규칙+모델 팔 ⓑ (2회 · 호출 48) | 선 (등록) |
|---|---|---|---|
| J1 적격 필터 뒤 정답 포함 | 10/10 | 10/10 | 전건 10/10 — 충족 |
| J2 hit@1 · hit@3 | 2/10 · 6/10 | 0/10 · 0/10 · 0/10 · 0/10 | descriptive only |
| J3' 최종 인용 오류 | 0 | 0 | 1건이라도 red — 0 |
| J3' 폐기율 (분모 = 주장 근거) | 0/118 = 0.0 | 2/8 = 0.25(검증 탈락 제안 1) | 기록 |
| J3 근거 hard 토큰 | 0 | 0 | 위반 0 — 0 |
| J4' 「확실」 정확도 | 확실 16건 중 정답 3 · 애매 13건 중 정답 7 | 본군 제안 0건 | 기록 |
| J6 후보 밖 ID | 0 | 0 (relay 폐기 0) | 0건 — 0 |
| J7 규격 위반 | 0 | 0 | 0건 — 0 |
| J8 지연 (8초 초과) | 호출 없음 | 48회 · 최소 1.75 · 중앙 3.66 · 최대 7.65초 · 초과 0 · 전송 오류 0 | 초과 건수 기록 — 0/48 |
| J9 결정성 (갈린 칸) | 0/30 | 2/30(⑴ 005 · ⑴′ 003) | 기록만 |

- 규칙 팔 hit@3 6건 = 003 pred_sample 2 · 004 Prediction 3 · 005 rn15_sample 1. hit@1 2건 = 003 · 004. 001 의 정답은 4위, 002 의 정답은 7위.
- 규칙 팔 본군 제안 수: 5 · 7 · 5 · 5 · 3 · 4. 006 DEM 은 정답 부모가 없는 자식이라 본군 제안 4건(LULC_2023 · Aspect · HLS_S30_NDVI · GK2A_NDVI · 전부 확실 · crs·grid)이 모두 비부모다.

## §4-3 대조군 — 자식별 (⑴′ · ⑵ · ⑶)

판정: ⑵ · ⑴′ 는 빈 제안이 전건이 아니면 red · ⑶ · ⑴ 는 기록. 모델 칸 = 회차 1 / 회차 2. 「침묵」 = 원문 빈 배열.

### ⑴′ removed_and_siblings — 규칙 **2/6 red** · 모델 **9/12 red**

| 자식 | 후보 | 규칙 팔 | 모델 팔 ⓑ | 누수 갈래 |
|---|---|---|---|---|
| 001 hsr_sample | 4 | HSR 레이더합성 원자료(확실 · crs·fileName) · rn15 15분 누적강수(애매 · crs) | 침묵 / 침묵 | 규칙 other 2 |
| 002 GK2A_NDVI_mean_202305 | 1 | GK-2A LST 원자료(애매 · fileName) | 침묵 / 침묵 | 규칙 other 1 |
| 003 pred_sample | 4 | rn15 15분 누적강수 · HSR 레이더 반사도 원자료(애매 · crs) | 침묵 / 같은 2건(애매 · crs) | 규칙 other 2 · 모델 other 2 |
| 004 Prediction (공간상세화) | 1 | 빈 제안 | 주장 1건 → 인용 검증 탈락(최종 빈 제안) / 침묵 | — |
| 005 rn15_sample | 3 | HSR 레이더 반사도 원자료(애매 · crs) | 같은 1건 / 같은 1건(애매 · crs) | 규칙 other 1 · 모델 other 2 |
| 006 DEM | 1 | 빈 제안 | 침묵 / 침묵 | — |

- 누수는 전부 갈래 `other` = 참인 인용(crs · grid · fileName)의 비부모다. crs 단독 근거가 규칙 4건 · 모델 4건이다(crs 동일 문자열 12건 교란).

### ⑵ descendants — 규칙 **5/6 red** · 모델 12/12 green(공허 10)

| 자식 | 후보 | 규칙 팔 | 모델 팔 ⓑ | 원인 (등록 §5-1) | `leak_kind` |
|---|---|---|---|---|---|
| 001 · 002 · 003 · 004 · 005 | 0 | 빈 제안(공허) | 부르지 않음(공허) | — | — |
| 006 DEM | 1 (Aspect) | **Aspect(확실 · crs·grid · 보조입력)** → red | 침묵 / 침묵 | **축 대조가 부모/후손 방향을 못 가름** | `descendant` |

- Aspect 가 ⑵ 후보에 남는 것은 구조 누수가 아니다 — 제품 적격 규칙 「적격 Lv ≤ 업로드 Lv」(Lv1 ≤ Lv1)대로이고 `services/core-api/tests/test_k3_lineage_probe.py` 필터 일관성 단언이 잠근다. 판정은 등록대로 red 로 둔다.
- 모델 팔 ⑵ green 은 DEM 2칸 침묵 + 공허 10칸이다. 실제 후보로 시험된 칸은 2칸뿐이다.

### ⑶ siblings — 기록 (규칙 빈 제안 1/6 · 모델 12/12 · 공허 2)

| 자식 | 후보 | 규칙 팔 | 모델 팔 ⓑ |
|---|---|---|---|
| 001 hsr_sample | 12 | HSR 레이더합성 변환 결과(확실 · crs·fileName) · ERA5 변환 결과 · GK-2A LST 변환 결과 · hdf4 MOD15A2H 변환 결과 2건(애매 · crs) | 침묵 / 침묵 |
| 002 GK2A_NDVI_mean_202305 | 12 | DEM · Aspect · LULC_2023(확실 · crs·grid) · GK-2A LST 변환 결과(애매 · fileName) | 침묵 / 침묵 |
| 003 pred_sample | 1 | Prediction (공간상세화)(확실 · crs·fileName) | 침묵 / 침묵 |
| 004 Prediction (공간상세화) | 0 | 빈 제안(공허) | 부르지 않음(공허) |
| 005 rn15_sample | 12 | ERA5 · GK-2A LST · HSR 레이더합성 · hdf4 MOD15A2H 2건 변환 결과(애매 · crs) | 침묵 / 침묵 |
| 006 DEM | 11 | **Aspect(확실 · crs·grid)** · LULC_2023(확실 · crs·grid) | 침묵 / 침묵 |

- **DEM→Aspect 형제 적중(등록 §6 교란)**: 규칙 팔 ⑶ 에서 Aspect 가 참인 인용(crs · grid)으로 살아남았다. ⑵ 의 red 와 **같은 데이터셋**이다(형제 규칙 `same_level` 이 후손 Aspect 를 ⑶ 에도 넣는다). ⑶ 은 기록 군이라 판정은 바뀌지 않는다.

### main · ⑴ removed (기록)

- main 빈 제안: 규칙 0/6 · 모델 12/12. ⑴ removed 빈 제안: 규칙 1/6(004) · 모델 11/12(회차 2 의 005 rn15_sample → hsr_sample 확실 · crs·grid 1건).

## 실제로 쓰인 근거 축 (최종 제안의 근거 행 · 사후 추가 집계)

| 실행 | crs | grid | fileName | period | variables | 합 (주장 → 최종) |
|---|---|---|---|---|---|---|
| 규칙 팔 | 60 | 33 | 25 | 0 | 0 | 118 → 118 |
| 모델 팔 ⓑ(보류 값) | 5 | 1 | 0 | 0 | 0 | 8 → 6 |
| 모델 민감도 ⓐ(스냅샷 autometa) | 13 | 4 | 2 | 18 | 0 | 42 → 37 |

- 2026-09-25-corpus28 의 규칙 팔 근거 25건이 전부 `fileName` 이던 것과 달리, 보류 값의 crs · grid 가 근거로 쓰였다. period 는 업로드 쪽 보류 값에 없어 ⓑ 에서 0 이고, ⓐ 에서만 나온다(기간 시작·끝이 각각 한 행).
- variables 는 세 실행 모두 0 — 후보 쪽 variables 0/28 이라 짝이 없다(등록 §6).

## §4 상한 민감도 — ⓑ 대 ⓐ 칸 대조 (합격선 아님)

칸 = (자식 · 군 · 회차). 비공허 칸 48. 등록 해석 규칙 그대로 적용.

| 분류 | 건수 | 등록 해석 |
|---|---|---|
| ⓑ 침묵 · ⓐ 발화 | **8** | 입력 빈곤 |
| ⓑ · ⓐ 둘 다 침묵 | **25** | 모델 · 프롬프트 |
| ⓑ 발화 | **5** | 기록(ⓐ 도 5칸 모두 발화) |
| ⓑ 침묵 · ⓐ timeout(측정 불가 · 사후 추가 분류) | **10** | 해석하지 않음 |

- **입력 빈곤 8칸 중 7칸은 ⑴ · ⑴′(정답 부모를 뺀 군)이다.** 그 7칸에서 ⓐ 의 발화는 전부 비부모 제안(주장)이다 — 후보에 정답이 없다. 입력을 채워 모델이 말하게 된 것이지, 맞히게 된 것이 아니다.
- 본군(main)에서 ⓐ 가 정답을 낸 칸은 **1칸뿐**이다(003 pred_sample 회1 · 두 부모 · 확실 · crs·grid·fileName). main 의 나머지는 모델·프롬프트 4칸 · 측정 불가 7칸이다.
- **결론: 섞임** — 분모 33(비공허 48 − ⓑ 발화 5 − 측정 불가 10) 중 입력 빈곤 **8/33** · 모델·프롬프트 **25/33**. 등록 규칙대로 전체 결론은 적지 않는다.
- 입력 빈곤 8칸: main 003 회1 · ⑴ 004 회1·회2 · ⑴ 005 회1 · ⑴′ 001 회1·회2 · ⑴′ 003 회1 · ⑴′ 004 회2.
- 모델·프롬프트 25칸의 군 분포: ⑶ 10 · ⑴ 5 · main 4 · ⑴′ 4 · ⑵ 2(DEM).
- ⓑ 발화 5칸: ⑴′ 004 회1(주장 1 · 검증 탈락) · ⑴′ 005 회1·회2 · ⑴ 005 회2 · ⑴′ 003 회2.
- 측정 불가 10칸: main 001 회1·회2 · main 002 회1·회2 · main 005 회1 · main 003 회2 · main 004 회2 · ⑴ 001 회1 · ⑴ 003 회1·회2. **main 12칸 중 7칸이 ⓐ 에서 측정 불가**라 본군의 입력 빈곤 여부는 이 실행으로 거의 가르지 못했다.
- 모델 침묵률: ⓑ **43/48** · ⓐ **25/38**(응답 받은 칸 · timeout 10 제외). 2026-09-25-corpus28 은 38/38.
- ⓐ 참고 수치(판정 아님): J2 hit@1 · hit@3 회1 1/10 · 2/10(003 pred_sample 의 두 부모 · 확실 · crs·grid·fileName) · 회2 0/10 · 0/10 · J3' 최종 인용 오류 0 · 폐기 5/42 · J6 0 · J7 0 · J8 중앙 5.28초 · 최대 8.08초 · 초과 10/48 · J9 갈린 칸 4/30 · ⑴′ 빈 제안 4/12(누수 `other` 10) · ⑵ 12/12(공허 10).
- ⓐ 에서 ⑴′ 누수 근거에 period 가 들어간 칸이 있다(001 → rn15 15분 누적강수 · 003 → rn15 15분 누적강수 · HSR 레이더 반사도 원자료(회1) · 004 → GK-2A 일 단위 식생자료 · 005 → HSR 레이더 반사도 원자료). 참인 period 인용이 비부모 제안의 근거가 됐다(사후 관찰 · 판정 아님).

## 등록 §6 교란 — 이번 결과에서 드러난 것

- crs 동일 문자열 12건: 규칙 팔 ⑶ 에서 crs 단독 근거 제안 9건 · ⑴′ 누수 4건이 crs 단독이다.
- DEM→Aspect: ⑵ red 와 ⑶ 적중이 같은 데이터셋(위 표).
- 업로드 variables 6/6 은 근거로 쓰이지 않았다(0행).
- dev 원장 파일 순서(`LAT_crop.npy` 첫 파일)는 측정 입력이 아니다. 이번 `fileName` 은 본체 첫 파일이다.

## 2026-09-25-corpus28 과 나란히 (등록 §7 — 개선·악화로 읽지 않는다 · 업로드 입력이 다르다)

| 항목 | corpus28 (업로드 = fileName 만) | held (업로드 = 보류 값) |
|---|---|---|
| 자식 · 엣지 | 5 · 10 | 6 · 10 (DEM 추가 · 부모 0) |
| J1 `filtered` @5/@10/@20 | 8/10 · 10/10 · 10/10 | 8/10 · 10/10 · 10/10 |
| 모델 호출 | 38 | 48 |
| J2 규칙 hit@1 · hit@3 | 0/10 · 2/10 | 2/10 · 6/10 |
| J2 모델 hit@3 (회차별) | 0/10 · 0/10 | 0/10 · 0/10 |
| 모델 침묵 | 38/38 | 43/48 |
| 규칙 근거 축 | fileName 25 | crs 60 · grid 33 · fileName 25 |
| J5' ⑵ 규칙 · 모델 | 5/5 green (공허 5) · 10/10 green (공허 10) | **5/6 red** (DEM) · 12/12 green (공허 10) |
| J5' ⑴′ 규칙 · 모델 | 3/5 red · 10/10 green | 2/6 red · **9/12 red** |
| J3' 최종 인용 오류 | 0 · 0 | 0 · 0 |
| J3' 폐기율 규칙 · 모델 | 0/25 · 0/0 | 0/118 · 2/8 |
| J8 초과 · 중앙값 | 0/38 · 1.89초 | 0/48 · 3.66초 |
| J9 갈린 칸 (모델) | 0/25 | 2/30 |

## 종료코드 · 78 기록

| 실행 | 종료코드 | 모델 호출 | 출력 |
|---|---|---|---|
| ⑴ 후보 절반 `service-tests.sh core-api k3_probe` (준비 단계) | 0 | 0 | j1 · candidates |
| ⑵ 모델 절반 본측정 `--arm both` | 0 | 48 | `luna-2026-09-25-held.json` |
| ⑶ 상한 민감도 `--arm model --upload-meta-override` | 0 | 48 (timeout 10 포함) | `luna-sensitivity-autometa-2026-09-25-held.json` |

- 78 없음. 재시도 없음.

## 후속

- ① ⑴′ red 의 원인은 두 팔 모두 참인 crs · grid · fileName 인용의 비부모다. crs 동일 문자열이 12 데이터셋에 걸려 있어 규칙 팔 근거 60행 중 다수가 가르는 힘이 없다. 어느 검사에도 걸리지 않는다(측정 전용).
- ② ⑵ DEM red 는 축 대조(crs · grid)가 방향을 담지 않아 생긴다. 제품 적격 규칙은 Lv1 ≤ Lv1 로 Aspect 를 남긴다. 계보 방향을 가를 축이 제품에 없다. **표본 확장으로 풀리지 않음 · 축에 방향 정보 없음** — 자식·엣지를 늘려도 crs · grid · period · variables · fileName 어느 축도 부모/후손 방향을 싣지 않으므로 같은 red 가 반복된다. 첫 줄의 「판정 보류 · 표본 확장」 대상에서 뺀다.
- ③ 민감도 실행(ⓐ · 업로드에 기간 포함)에서 8초 제품 timeout 초과가 10/48 이다(ⓑ 최대 7.65초 · 중앙 3.66초 / ⓐ 중앙 5.28초). 즉 ⓐ 식 입력 보강(제안 시점에 기간 등을 싣는 개선)은 제품 8초 안에서 **10/48 무응답**을 낳았다 — 그 10칸의 결과는 빈 제안 · `empty_declaration` 「계보 제안 모델에 닿지 못했다 …」다. K3 플래그 판단 재료다. 입력 길이와 지연의 관계는 이번 측정으로 가르지 않았다. 어느 게이트도 이 지연을 재지 않는다.
- ④ 제안 시점 NumPy 업로드에 기간이 없다(보류 값 period 0/6 · `autometa.period` 는 등록 화면의 사람 입력) — 개선 이슈 초안은 준비 단계에서 작성했고 생성하지 않았다.
- ⑤ K3 플래그: 규칙 팔 hit@3 6/10 은 crs 동일 문자열 12 데이터셋(`WGS84 (기준 격자 파일)`) 위에 서 있고(근거 60행 중 다수가 가르는 힘 없음 · ①), ⑴′ 는 규칙 · 모델 **두 팔 모두 red** 다. 플래그를 켜지 않는 현재 결정은 이 데이터와 맞는다.

## 파일

| 파일 | 무엇 |
|---|---|
| `j1-2026-09-25-held.json` | 후보 절반 J1(전략 2 × k 5·10·20) |
| `candidates-2026-09-25-held.json` | 본군·대조군 후보 · 업로드 축 · `sample_limits` (sha256 `f6dc9ad6…`) |
| `luna-2026-09-25-held.json` | 본측정 두 팔 원문 · 호출 48건 원문 · 판정 표 |
| `luna-sensitivity-autometa-2026-09-25-held.json` | 상한 민감도(모델 팔만 · 합격선 아님) 원문 · 호출 48건 |
