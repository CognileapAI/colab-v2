# `D5` 마감 실측 — 인제스트·파이프라인 (2026-08-30)

／ 브랜치 `lane-d5` · `main` 무접촉(병합·푸시 없음) · 운영 스택 무접촉(읽기 전용 조회만)
／ 판정의 정본 = `dev-package/work-items.yaml` · 판정자 = 게이트 `work-item-consistency`
／ 착수 근거 = `reports/STAGE2-READINESS-20260830.md §6` 권고 착수 순서 ①

---

## 0. 이 회차가 판정한 것과 판정하지 않은 것

- **판정한 것** = `D5` 완료 정의 **①~④** 의 충족 여부, 그리고 그 항목이 닫히지 않는 사유로 대장이 든 **`§4` #23 · #26** 둘의 현재 실물.
- **판정하지 않은 것** = `D5` 의 stage 2 파트(헤더 파싱·좌표계 통일·지도용 영상 변환). 그 파트는 **`PV-1` 로 독립**했고(`PLAN-SoT §9 〈189〉`) 이 항목의 완료 정의가 아니다.
- **코드는 한 줄도 고치지 않았다** — 실측 결과 완료 정의가 요구하는 구현이 **이미 전건 서 있다.** 이 회차의 산출은 **대장·산문의 정정**이다.

## 1. 실측 환경 (모두 선언하고 쟀다)

| 값 | 무엇 |
|---|---|
| `COLAB_REFERENCE_DATA` | 원천 마운트 — 미선언이면 실데이터 시험 26건이 **red** 로 떨어진다(건너뛰지 않는다) |
| `COLAB_PIPELINE_DB_URL` | 일회용 DB — 미선언이면 DB 시험 15건이 **error** 로 떨어진다 |
| venv · `node_modules` | 새 체크아웃에 없어 첫 회차가 `stage2-markers` 준비 red · `generated-up-to-date` 판정 red 를 냈다. **게이트를 고치지 않고 환경을 세웠다** |

- 값은 `~/.colab-v2-test.env` 에만 있다(`RESTART.md §「시험용 환경변수」`). **레포에 적지 않았다.**

## 2. 완료 정의 ①~④ — 전건 충족

| 조건 | 요구 | 실측 |
|---|---|---|
| ① | 감지·파싱 자기 증명이 **red fixture 로 fail-closed** — 확장자만 바꾼 파일이 magic-byte 로 바로잡히고, 좌표 못 찾은 파일이 「성공」을 반환하지 않는다(`DR-9` 음성) | `test_detect.py` — `test_extension_swap_is_corrected_by_magic` · `test_hdf_extension_is_hdf4_by_magic` · `test_unknown_bytes_fail_closed` green. 음성 = `test_axis_detect.py` `test_rejected_file_yields_no_row` · `test_internal_grid_real.py` `test_no_projection_means_failure_not_a_made_up_grid` green. **소스 `linspace` 0건**(`services/pipeline-worker/src` 전수) · `[미상]` 상수 실재(`d5/formats.py`) |
| ② | 이미-COG 판별 **3부류 red→green (6·16·40)** | `test_tiff_classes_pipeline_real.py` **5건 전건 green** — 실물 코호트 분할 · 타일만 규칙이 정확히 16 에서 갈림 · 음성 둘(이미-COG 6 은 우리 산출물로 기록되지 않는다 · 타일만 16 은 입력이지 산출이 아니다) · 양성(스트립 40 이 우리 산출물을 낳는다) |
| ③ | 게이트 green — **core-api 에 rasterio 0** | `bash gates/run.sh all` — `banned-import` · `import-boundary` · `boundary-selftest` green. `services/core-api` 의 `requirements.in`·`src` 전수에서 `rasterio`·`gdal`·`xarray`·`pyhdf` **0건** |
| ④ | 실데이터 E2E **지원 4종 각 최소 1건 완주** | `test_e2e_real.py` 7건 green — `NetCDF`(GK2A) · `Binary`(HSR) · `HDF4`(폴더명이 HDF5 라 적힌 실체 HDF4) · `GeoTIFF`(이미-COG 1건 ＋ 스트립→COG 1건). ＋ 좌표 결손 음성 1건 |

- **`services/pipeline-worker` 전 시험 = 196 passed / 0 failed** (원천 마운트 ＋ DB 선언 상태 · 141 초).
- ⚠ 원천·DB 를 선언하지 않으면 같은 명령이 **26 failed · 15 errors** 다 — 이 시험들은 **green-by-skip 하지 않는다.** 그 성질 자체가 이번 실측의 부수 확인이다.

## 3. 닫지 않는 사유로 대장이 든 둘 — 현재 실물

### `#23` `/healthz` 가 `implemented:false` — **해소**

- **코드** — `app/health.py:29` 가 `{"unit":"pipeline-worker","status":"alive","implemented":True}` 를 낸다. 회귀 시험 `test_health_endpoint.py` 2건 green(본문 대조 ＋ 다른 경로 404).
- **실이미지** — 운영 중인 staging 컨테이너에 직접 물었다. 응답 `{"unit": "pipeline-worker", "status": "alive", "implemented": true}`. 이미지 = `colab-v2/pipeline-worker:cfc98e302ae4`.
- 이 사유가 적힌 근거였던 「실이미지가 false 를 낸다」는 **더 이상 참이 아니다.**

### `#26` 저장 배치 회귀 시험 **0건** — **해소**

- 배치 시험 **24건** 실재 — `core-api` 11 · `viz-render` 7 · `pipeline-worker` 6. pipeline-worker 몫 6건 green 재확인.
- 세 배포 단위의 `kernel/storage_layout.py` **md5 동일**(`5996f605…`) — 정본은 `contracts/storage/layout.json` 하나(`PLAN-SoT §9 〈102〉`).
- 「시험이 배치를 자기 손으로 다시 타이핑한다」던 무늬가 사라졌다 — `test_storage_layout.py` 는 배치를 **규약 함수에게만** 묻는다.
- 대장이 든 「0건」은 2026-08-25 표기이고, 그 뒤 `P2` 실측(`sessions/P2-MEASURE.md §3`)이 이미 해소로 판정했다.

## 4. 대장 대 산문 — 어긋난 자리와 고친 쪽

| 자리 | 적혀 있던 것 | 실물 | 처분 |
|---|---|---|---|
| `work-items.yaml` `D5` | `status: partial` · 사유 = `#23`·`#26` | 완료 정의 ①~④ 전건 green · 사유 둘 다 해소 | **대장을 고쳤다** — `partial` → `done` |
| `03-HANDOFF §1 T-D` `D5` 행 | 🟧 · 「저장 배치 회귀 시험 0건 · `/healthz` `implemented:false`」 | 위와 같음 | **산문을 고쳤다** — 🟧 → ✅ · 원문은 지우지 않고 개정 표시 |
| `03-HANDOFF §4` 머리말 | `#23`·`#26` **✅ 해소** | 실물과 **일치** | **고치지 않았다** — 옳았던 쪽이다 |
| `WORK-UNITS §11` 「경계」줄 | `(D5 는 🟧 — …)` 괄호 주석 · **독립 행 없음** | 위와 같음 | **표기만 ✅ 로 맞췄다.** 독립 행 신설은 하지 않았다 — 범위를 늘리지 않는다 |

- ⭑ **낡은 쪽은 대장과 `§1` 산문이었다.** 같은 문서 `§4` 가 이미 해소로 적고 있는데 `§1` 행과 대장이 2026-08-25 표기에 멈춰 있었다 — `P2` 에서 한 번 일어난 것과 **같은 무늬**다(`WORK-UNITS.md:583`).

## 5. 남는 것 — 닫는 근거로도 막는 근거로도 쓰지 않았다

- **stage 2 파트**(헤더 파싱 ⑶ · 좌표계 변환 ⑷ · COG ⑸) = `PV-1` 소유. `D5` 완료 정의 밖이다.
- **`D5` 항목의 `stage` 값** — 실제로는 두 단에 걸쳐 있으나 스키마 값이 하나뿐이라 `stage1` 로 남긴다(종전 note 그대로).
- 이 회차는 **staging 재배포를 하지 않았다.** `D5` stage 1 파트는 2026-08-25 배포분이 지금도 healthy 로 서 있고(위 §3 실측), 그 뒤 `services/pipeline-worker` 변경분은 **`PV-1` 몫**(지도 타일 재사용)이다.

## 6. 게이트 (`bash gates/run.sh all`)

| 회차 | green | red(판정) | red(준비) |
|---|---|---|---|
| 편집 전 (환경 정비 후) | **29** | **0** | **4** |
| 편집 후 | **29** | **0** | **4** |

- red(준비) 넷 = `schema-diff` · `autometa-loss` · `preview-tile-slot`(적용 DB URL 미선언) · `e2e-format-coverage`(원천 미마운트). **판정 red 는 0건**이고 `reports/STAGE2-READINESS-20260830.md §3` 실측과 동일하다.
- `work-item-consistency` green — 대장과 산문의 불일치 **0**.

## 7. 해제되는 것

- `PV-1` · `P3` — 미충족 선행이 `D5` 하나뿐이었다. **열린다.**
- `Y-1` — 선행 `P3`·`D5` 중 `D5` 가 빠진다. **잔여 선행 = `P3`.**
- `S3` — 선행은 `S2`·`P3`. `D5` 는 `P3` 을 통한 간접이었다.
- `P6` — `D5` 는 `P3` 을 통한 간접. **잔여 선행 = `P3`·`P5`.**
