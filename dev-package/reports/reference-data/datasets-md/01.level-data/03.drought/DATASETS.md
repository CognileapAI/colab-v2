# 가뭄(drought) 데이터셋 정본

- 출처 문서: `#readme/[Data Info]SPI-4weeks.docx` · `#readme/[Data Info]SPEI-4weeks.docx` · `#readme/01.가뭄 데이터 여는 코드.ipynb` · 추출일 2026-09-14 · 상태: 확정 — Ted 판정 2026-09-14
- 유형 폴더: `01.level-data/03.drought/`(참조자료 뿌리 기준 · 이 문서가 놓이는 자리) — 아래 글롭은 전부 이 문서 폴더 기준 상대경로이고 안쪽 `03.drought/` 을 포함한다
- 표기 대응: 폴더 `Lv.N` ↔ 제품 값 `LvN` (제품 값 집합 `Lv0`~`Lv3` · `db/platform/schema.sql` CHECK)
- 프로젝트: drought · 설명: SPI-4weeks 와 SPEI-4weeks 두 가뭄지수의 L1 보정 결과. 두 자료는 서로 독립이며 파생 관계가 없다.
- 계수 기준: 파일 건수·바이트 = `glob` 매칭 후 `desktop.ini` 제외 · 2026-09-14 실측

## 데이터셋 표

| # | 이름 | 레벨 | 부모 | 파일 글롭 | 건수 | 바이트 | 기준 격자(쌍) | 포맷 | 미리보기 기대 | 비고 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | SPI-4weeks | Lv1 | — | `03.drought/Lv.1/SPI_4weeks_sig_wide.gpkg` | 1 | 24,797,184 | 없음(벡터) | GeoPackage | 미성립(포맷 미지원 · 판정 표에 이름으로) | 등록 예정(미리보기 없음) · 화면 수정 WU-C2a 뒤 |
| 2 | SPEI-4weeks | Lv1 | — | `03.drought/Lv.1/SPEI_4weeks_sig_wide.gpkg` | 1 | 24,797,184 | 없음(벡터) | GeoPackage | 미성립(포맷 미지원 · 판정 표에 이름으로) | 등록 예정(미리보기 없음) · 화면 수정 WU-C2a 뒤 |

- 데이터셋 2 · 계보 간선 0 · 자료 바이트 49,594,368 · 기준 격자 0

## 데이터셋 상세

### SPI-4weeks

- 레벨: Lv1(폴더 `Lv.1` · 출처 축자 「L1 Calibrated」) — 출처 문장 축자 「Data Level : L1 Calibrated」 · 폴더도 `03.drought/Lv.1/` 하나뿐이고 `Lv.0`·`Lv.2` 가 없다
- 부모: 없음 — 출처 문서에 상위 자료·파생 관계 문장이 없다. 산정 근거 문장은 「대한민국 내 기상관측소의 강우 관측자료를 활용하여 SPI-4weeks를 산정하고, 각 관측소의 주소지를 기준으로 해당 관측자료가 소재 시군구를 대표하는 것으로 가정하여 데이터를 구축하였다.」이고 그 강우 관측자료는 폴더에 없다. Ted 확정 「꼐보는 없을거같고.」
- 파일: `03.drought/Lv.1/SPI_4weeks_sig_wide.gpkg` · 1건 · 24,797,184 B · 관측 기간 2000-01-01 ~ 2025-12-31 · 관측 간격 1 week · 공간해상도 1 km · 좌표계 WGS84
- 격자: 파일 0건 · 근거 = GeoPackage 벡터(시군구 폴리곤)이고 좌표가 파일 안에 있다. `#readme/01.가뭄 데이터 여는 코드.ipynb` 가 `gpd.read_file(gpkg_path, layer="spi_4weeks_wide")` 로 열고 `spi_YYYYMMDD` 열을 골라 그린다 — 별도 위경도 배열을 쓰지 않는다
- 설명: 대한민국 내 기상관측소의 강우 관측자료로 산정한 4주 SPI 를 시군구 단위로 담은 벡터 자료. 각 관측소의 주소지를 기준으로 그 관측자료가 소재 시군구를 대표한다고 가정해 구축했다. 2000-01-01 ~ 2025-12-31 을 주 단위로 담는다. 제품 값은 Lv1 이고 출처 문서의 데이터 레벨 축자는 「L1 Calibrated」다.
- 비고: **등록 예정(미리보기 없음) · 화면 수정 `WU-C2a` 뒤**. 2026-09-13 실측은 차단 — 화면 축자 「이 확장자는 지도로 못 그려요」 · 「파일 분석을 마치지 못했어요 · 형식 인식 실패」. 분석 단계에서 등록 단추(「다음 →」)가 비활성이라 다음 단계로 갈 수 없다. 제품이 GeoPackage 를 받지 않는다(`DR-3 §3`).

### SPEI-4weeks

- 레벨: Lv1(폴더 `Lv.1` · 출처 축자 「L1 Calibrated」) — 출처 문장 축자 「Data Level: L1 Calibrated」
- 부모: 없음 — SPI 와 같은 사유. 두 문서가 서로를 참조하는 문장이 없고 산정식·입력이 각자 기재된다
- 파일: `03.drought/Lv.1/SPEI_4weeks_sig_wide.gpkg` · 1건 · 24,797,184 B · 관측 기간 2000-01-01 ~ 2025-12-31 · 관측 간격 1 week · 공간해상도 1 km · 좌표계 WGS84
- 격자: 파일 0건 · 근거 = SPI 와 같음(벡터 · 좌표 내장 · 여는 코드가 `spei_4weeks_wide` 레이어를 직접 읽는다)
- 설명: 대한민국 내 기상관측소의 강우 관측자료로 산정한 4주 SPEI 를 시군구 단위로 담은 벡터 자료. 각 관측소의 주소지를 기준으로 그 관측자료가 소재 시군구를 대표한다고 가정해 구축했다. 2000-01-01 ~ 2025-12-31 을 주 단위로 담는다. 제품 값은 Lv1 이고 출처 문서의 데이터 레벨 축자는 「L1 Calibrated」다.
- 비고: **등록 예정(미리보기 없음) · 화면 수정 `WU-C2a` 뒤**. 2026-09-13 실측은 SPI 와 같은 자리에서 같은 문면으로 차단. 화면 수정 뒤 두 건 모두 등록 대상이다.

## 판정 기록 (Ted 확정 2026-09-14)

㈎ **제품이 GeoPackage 를 받지 않는다 — 가뭄 프로젝트가 화면에 서지 않는다.** 오늘 두 건 모두 분석 단계에서 막혔고 우회 투입은 하지 않았다. 대장 항목 `FMT-GPKG` 가 열려 있다. ⓐ GeoPackage 수용을 기능으로 연다(가뭄 프로젝트가 서고 벡터 미리보기 설계가 새로 붙는다) / ⓑ 이번 회차는 가뭄 프로젝트를 빈 채로 둔다(프로젝트 4개 중 1개가 데이터셋 0건) / ⓒ 두 자료를 다른 포맷으로 다시 받는다(생산자 재작업).

→ 확정: 등록 허용 · 미리보기 없음 — 두 건을 데이터셋으로 등록하고 미리보기는 만들지 않는다. 등록을 막는 화면 조건 수정은 `WU-C2a`. GeoPackage 판독(벡터 미리보기 설계)은 `FMT-GPKG` 로 분리해 별도 판정.

㈏ **등재표의 가뭄 경로가 실물과 다르다.** `dev-package/tools/dev-seed/plan-manifest.yaml` seq 13·14 는 `01.level-data/03.drought-20260518T233626Z-3-001/03.drought/Lv.1/` 를 가리키는데 실물 폴더는 `01.level-data/03.drought/03.drought/Lv.1/` 다. 지금 `build_plan.py` 를 돌리면 MISMATCH 2건 ＋ 총 바이트 -49,594,368 로 비영 종료한다(실측). ⓐ 등재표 경로를 실물로 고친다 / ⓑ 폴더 이름을 되돌린다(참조자료는 읽기 전용이라 배제 권고).

→ 확정: ⓐ 계열 — 등재표를 이 md 에서 생성한다. 참조자료 폴더는 무수정이고, 이 문서의 글롭이 실물 경로 `01.level-data/03.drought/03.drought/Lv.1/` 를 가리킨다. `plan-manifest.yaml` 은 생성물이 되므로 손으로 고치지 않는다.

㈐ **레벨 표기를 `Lv.1` 로 쓸지 `L1 Calibrated` 로 쓸지.** 출처 축자는 「L1 Calibrated」이고 폴더 이름은 `Lv.1` 이다. 다른 두 유형은 문서가 `Lv.0/Lv.1/Lv.2` 를 쓴다. ⓐ 화면 표기는 `Lv.1` 로 통일하고 「L1 Calibrated」는 설명 칸에 둔다(현재 초안) / ⓑ 출처 축자를 그대로 쓴다.

→ 확정: ⓐ 제품 값은 `Lv1` — 레벨 칸은 제품 값 하나만 적는다. 출처 축자 「L1 Calibrated」는 설명 칸에 둔다.

## 참조

- 출처 문서: `#readme/[Data Info]SPI-4weeks.docx` · `#readme/[Data Info]SPEI-4weeks.docx`(생산자 차호영 · 고려대학교 · Upload Date 2026-05-17) · `#readme/01.가뭄 데이터 여는 코드.ipynb`(레이어 이름·열 이름 규칙)
- 재고 조사: `dev-package/reports/reference-data/2026-09-13-inventory-v2.md` §4-3 · §5-3
- 오늘 등록 실측: `dev-package/sessions/DR-3-run-2026-09-13.md` §1 순번 13·14 · §3
- 판정: `dev-package/intent/2026-09-13-dev-reset-reference-scenario.md` 판정 ㈎(데이터셋 2건 · 계보 0간선 · Ted 확정 2026-09-13)
- 기계 등재표: `dev-package/tools/dev-seed/plan-manifest.yaml` seq 13·14

## 기계 블록 (생성기 입력)

```yaml
# colab-datasets v1 — 이 블록이 생성기의 입력이다. 표와 어긋나면 생성기가 비영 종료한다.
# `summary` = 러너가 화면에 그대로 치는 한 줄. `description`·`note` = 문서 요약(생성기 미출력).
project: drought
project_name: "drought"
project_description: "SPI-4weeks 와 SPEI-4weeks 두 가뭄지수의 L1 보정 결과. 두 자료는 서로 독립이며 파생 관계가 없다."
folder: 01.level-data/03.drought   # 참조자료 뿌리 기준 · 아래 files/grid_files 는 이 폴더 기준
datasets:
  - seq: 13
    name: "SPI-4weeks"
    level: Lv1
    parents: []
    summary: "4주 SPI 유의구간 벡터 (L1 Calibrated)"
    files: ["03.drought/Lv.1/SPI_4weeks_sig_wide.gpkg"]
    file_count: 1
    bytes: 24797184
    grid_files: []
    format: "GeoPackage"
    preview_expected: "미성립(포맷 미지원 · 판정 표에 이름으로)"
    description: "대한민국 내 기상관측소의 강우 관측자료로 산정한 4주 SPI 를 시군구 단위로 담은 벡터 자료. 각 관측소의 주소지를 기준으로 그 관측자료가 소재 시군구를 대표한다고 가정해 구축했다. 2000-01-01 ~ 2025-12-31 을 주 단위로 담는다. 제품 값은 Lv1 이고 출처 문서의 데이터 레벨 축자는 「L1 Calibrated」다."
    note: "**등록 예정(미리보기 없음) · 화면 수정 `WU-C2a` 뒤**. 2026-09-13 실측은 차단 — 화면 축자 「이 확장자는 지도로 못 그려요」 · 「파일 분석을 마치지 못했어요 · 형식 인식 실패」. 분석 단계에서 등록 단추(「다음 →」)가 비활성이라 다음 단계로 갈 수 없다. 제품이 GeoPackage 를 받지 않는다(`DR-3 §3`)."
  - seq: 14
    name: "SPEI-4weeks"
    level: Lv1
    parents: []
    summary: "4주 SPEI 유의구간 벡터 (L1 Calibrated)"
    files: ["03.drought/Lv.1/SPEI_4weeks_sig_wide.gpkg"]
    file_count: 1
    bytes: 24797184
    grid_files: []
    format: "GeoPackage"
    preview_expected: "미성립(포맷 미지원 · 판정 표에 이름으로)"
    description: "대한민국 내 기상관측소의 강우 관측자료로 산정한 4주 SPEI 를 시군구 단위로 담은 벡터 자료. 각 관측소의 주소지를 기준으로 그 관측자료가 소재 시군구를 대표한다고 가정해 구축했다. 2000-01-01 ~ 2025-12-31 을 주 단위로 담는다. 제품 값은 Lv1 이고 출처 문서의 데이터 레벨 축자는 「L1 Calibrated」다."
    note: "**등록 예정(미리보기 없음) · 화면 수정 `WU-C2a` 뒤**. 2026-09-13 실측은 SPI 와 같은 자리에서 같은 문면으로 차단. 화면 수정 뒤 두 건 모두 등록 대상이다."
```
