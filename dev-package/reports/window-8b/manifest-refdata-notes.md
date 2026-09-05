# 적재 매니페스트 — 로더가 표현하지 못하는 것

## ⛔ 1. `kind` 로 Data/Code/Results/Figure/Lat_Lon_info 를 가를 수 없다

`FileKind` 는 **두 값뿐**이다.

> `contracts/schemas/common.json:78-82` — `"enum": ["본체", "기준 격자 파일"]`
> `contracts/seams/fe-core.yaml:303-309` — `fileKinds` items 가 그 `$ref` 다. 「생략하면 전부 `본체`」

`load-seed.py:_files_of()` 는 매니페스트의 `kind` 문자열을 그대로 `fileKinds` 에 실어 보낸다
(`load-seed.py` `_create_upload`). 어휘 밖 값을 쓰면 계약 위반이고, 서버가 받아도 열이 없다.

⟹ **지시받은 `kind` = `readme`/`metadata`/`code`/`figure`/`results` 는 두 안 모두에서 만들지 않았다.**
그 구분은 **경로에만** 남는다(`02.File-format/file_format_4_tif/03.Figure/...`).
표현하려면 계약 동결 해제(FileKind enum 확장 + 마이그레이션)가 필요하다 — 이 회차의 범위 밖이다.

## ⛔ 2. 「레벨」은 매니페스트가 선언하지 못한다 — 계보에서 나온다

> `PLAN-SoT §9 〈276〉` — 「`LV-1` 집행 — 사람이 가공 단계를 직접 고르는 경로를 **쓰기 바디에서 제거**한다
> (생성 요청 포함)」 · 필드 제거 2 = `DatasetCreate.processingLevel` · `DatasetUpdate.processingLevel`
> 근거 = `〈194〉` 축자 「레벨은 언제나 계보에서 나온다 — 사람이 직접 정하지 못한다 … **예외 없음**」

⟹ 매니페스트에 `processingLevel` 자리가 없다. **안 A 는 계보 간선으로 레벨이 서고, 안 B 는 레벨이 서지 않는다** —
안 B 의 8 데이터셋은 전부 계보 뿌리(Lv.0 상당)로 적재되고, 이름의 「Lv.0~Lv.2」는 **문자열일 뿐 제품이 계산한 레벨이 아니다.**
안 B 를 고르면 `〈276〉`/`〈194〉` 가 세우려던 성질이 이 데이터에 대해서는 나타나지 않는다.

## ⚠ 3. 기준 격자 파일 상한 2건 — tif·HDF5 에서 걸린다

> `common.json:79` — 「기준 격자 파일은 데이터셋당 **0~2건**」(`〈58〉`)

`04.Lat_Lon_info` 가 `file_format_4_tif` 는 위·경도 쌍 **2벌**(T51SYB·T52SCE), `file_format_5_HDF5` 도
**2벌**(h27v05·h28v05)이다. 한 벌만 `기준 격자 파일` 로 싣고 나머지 한 벌은 `본체` 로 실었다.
`file_format_3_bin` 의 `rdr_500m_latlon.nc`·`레이더합성자료포맷정보.pdf`,
`file_format_2_nc` 의 `gk2a_ko020lc_latlon.nc` 도 같은 이유로 `본체` 다.

## ⚠ 4. 「#readme·#metadata 를 그 주제의 **모든** 데이터셋에 붙인다」는 검증 조건과 충돌한다

지시의 검증 조건은 「전 파일이 **정확히 한 번** 나타난다」이다. 같은 문서를 주제의 여러 데이터셋에 붙이면
그 조건이 깨진다. **검증 조건을 택했다** — 문서는 그 주제의 **뿌리 데이터셋 한 곳에만** 붙인다
(강수 → `LD-PRCP-LV0-HSR` · 식생 → `LD-VEG-LV0` · 가뭄 → `LD-DRGH-LV1`).
`LAT_crop`/`LON_crop` 은 `#readme` 가 「Lv.1, Lv.2 공용」이라 적었으나 같은 이유로 **Lv.1 에만** 붙였다.

## ⚠ 5. 안 A 의 `Lv.1_(Model_Input_Data)` = Lv.1 의 **형제**다 (자식 아님)

근거 = `01.level-data/02.vegetation/02.vegetation/#readme/#processing_description_NDVI.docx`
「[2] 메인 처리 프로세스 — NDVI」 Lv.2 절 「모델 학습 시 활용 자료 · 입력자료 = 월 단위 GK-2A NDVI(2 km) ·
수치표고모형(100 m) · 경사향(100 m) · 연 단위 토지피복지도(100 m) · **검증자료** = 월 단위 HLS NDVI(100 m)」.
폴더의 4건(`DEM.tif`·`Aspect.tif`·`LULC_2023.tif`·`HLS_S30_NDVI_mean_202305.tif`)은
**Lv.1 을 가공해 만든 것이 아니라 별개 원천에서 온 자료**다 ⟹ Lv.1 의 자식이 아니다.
넷 다 Lv.2 로만 들어가므로 **Lv.2 의 `보조입력` 부모**로 세웠다(부모 자신은 계보 부모 0건).
`D-06` 이 DEM 을 `보조입력` 으로 단 선례를 그대로 따랐다(`manifest-s2.json` `D-06.lineageParents`).

## ⚠ 6. 매니페스트 순서가 계보 순서다

`load-seed.py:load_dataset()` — `resolved.get(parent["parentKey"])` 가 비면
`Abort("계보 부모 … 부모가 먼저 적재돼야 한다")`. `datasets` 배열은 **부모가 앞**이어야 한다.
두 안 모두 그 순서로 정렬했고 `build.py:validate()` 가 단언한다.

## ⚠ 7. 멱등은 **이름 완전 일치**다 — 이름을 바꾸면 중복 적재된다

`load-seed.py:build_index()`/`decide()` · 근거 `PLAN-SoT §9 〈106〉`.
`--force` 류 인자가 없고, `deleteDataset` 은 501 이라 잘못 적재하면 도구로 지울 수 없다.
**두 안을 같은 환경에 둘 다 적재하면 안 된다** — 이름이 달라 34 개 데이터셋이 서고 파일이 2벌 올라간다.

## ⚠ 8. 실행 시 부하 — `createUpload` 가 한 데이터셋 전량을 메모리에 담는다

`load-seed.py:post_multipart()` 가 `bytearray` 에 전 파일 바이트를 누적한다.
최대 데이터셋 = `FF-HDF5` **1.35 GB**(두 안 공통) · 안 B 의 `TP-VEG` 363 MB.
HTTP 타임아웃은 600 초 고정(`Client._send`)이다. 총 **3.78 GB** 를 한 번에 밀면 이 자리에서 깨질 수 있다.
`--round` 로 나눠 돌리도록 회차를 매겼다(안 A: 1→2→3→4 · 안 B: 1→4). 파일 상한 500(`fe-core.yaml:299`)은
최대 152 건이라 여유가 있다.

## 참고 — 파일 종류 계수

| | 데이터셋 | 파일 | 바이트 | 본체 | 기준 격자 파일 | 계보 간선 |
|---|---|---|---|---|---|---|
| 안 A | 14 | 434 | 3,780,910,612 | 414 | 20 | 6 |
| 안 B | 8 | 434 | 3,780,910,612 | 420 | 14 | 0 |

제외 = `03_KWRA_conference-20260517T141236Z-3-001/` 전체 · `desktop.ini` **50건**(484 − 50 = 434).
