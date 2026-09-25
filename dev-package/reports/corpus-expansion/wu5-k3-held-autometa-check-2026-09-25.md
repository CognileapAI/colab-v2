# K3 업로드 축 — 보류 값 vs `d3_dataset_autometa` 점검 (dev 읽기 1회 · 2026-09-25)

> ⚠ **두 값이 다르다 — 축 둘(period · variables).** intent `dev-package/intent/2026-09-25-k3-upload-axes-remeasure.md` 서명 ① 점검 규칙대로 **재사전 등록 전에 멈춘다.** 측정은 하지 않았다.

## 무엇을 대조했나

- 서명 ① 의 열린 점: 「제품이 제안 시점에 읽는 업로드 분석 값(보류 값) = `d3_dataset_autometa`」.
- 제품이 제안 시점에 읽는 값 = `ledger.held_auto_metadata(upload_id)` → `_uploaded_file_meta`(`services/core-api/src/colab_core/app/routes/ingestion.py:499-533`). 보류 값의 출처 = `d5_pipeline_event` 의 `file.format-detected` · `file.header-parsed` 페이로드(`services/core-api/src/colab_core/domains/d5_ingestion.py:132-137` · `:286-328`).
- 대상 업로드 1건: `hsr_sample`(K3-LIN-001 · NumPy · 파일 3). 업로드 `01M39T9KXE6J7JZTBKXFR503AQ` 는 `d5_upload_file.id = d3_file.id` 로 데이터셋 `01M39TA6QY5NEAR8ZPZ6AF9KNE` 에 이어진다(이어진 업로드 1건).
- 방법: dev 호스트의 일회용 `postgres:16-alpine` 클라이언트 · BYPASSRLS 백업 URL · `begin read only; … rollback;`(`transaction_read_only = on` 확인). 쓰기 0건. 질의 작성 오류(없는 열 이름 · jsonb 형 변환 우선순위)로 두 번 중단됐고, 둘 다 읽기 전용 트랜잭션 안의 오류라 쓰기는 없다. 같은 질의를 고쳐 세 번째에 완주했다 — 대조 대상은 끝까지 이 업로드 1건이다.

## 결과

| 축 | 보류 값(제안 시점) | `d3_dataset_autometa`(= 스냅샷 v2 · 정답 `upload_meta`) | 같은가 |
|---|---|---|---|
| format | `NumPy`(`uniform` true · 본체 `detected_format` 도 `NumPy`) | `NumPy` | 같음 |
| crs | `WGS84 (기준 격자 파일)` | `WGS84 (기준 격자 파일)` | 같음 |
| grid | `128x128` | `128x128` | 같음 |
| period | **없음**(`period.start`·`period.end` 둘 다 비어 있음) | `2019-07-28 00:00:00+00` ~ `2024-07-09 00:00:00+00` | **다름** |
| variables | **`["hsr_sample"]`** | `{}`(빈 배열) | **다름** |
| fileName | 본체 `hsr_sample.npy` | `bundle_file_name` `hsr_sample.npy` | 같음 |

- 보류 사건 시각 `2026-09-24 13:39:50` · 자동 메타 `updated_at` = 데이터셋 `uploaded_at` = `2026-09-24 13:40:08`(등록 시각).
- 페이로드 열쇠: `file.format-detected` = `format, perFile, renderable, uniform` · `file.header-parsed` = `byteSizeTotal, crs, grid, period, unreadableFiles, variables`.

## 읽기

- 이 업로드에서 제품 `_uploaded_file_meta` 가 만들 값은 `fileName` · `kind` · `format NumPy` · `variables ["hsr_sample"]` · `crs` · `gridDescription 128x128` · `partCount 3` 이다 — **`periodStart`·`periodEnd` 가 없고 `variables` 가 있다.** 커밋 `beee8512` 의 정답 `upload_meta`(스냅샷 `autometa` 사본)는 반대로 기간이 있고 변수가 없다.
- 기간: 보류 값에 없고 `apply_autometa` 는 보류 값만 넘기므로(`ingestion.py:1003-1009`), 자동 메타의 기간은 등록 경로의 다른 입력에서 왔다 — 어느 입력인지는 이 읽기로 확인하지 않았다(추정: 사람 입력 · 미확인).
- 변수: 보류 값의 `variables` 는 등록 때 넘기지 않는다(`ingestion.py:1007-1008` 주석 · `0019` 트리거만 쓴다). 그래서 자동 메타는 빈 배열이다.
- 영향: 업로드 쪽 period 축은 **제안 시점의 제품에는 없는 값**이다. 이 사본으로 재면 규칙 팔·인용 검증이 제품이 못 가진 period 근거를 쓸 수 있다. variables 는 후보 쪽이 28건 전부 빈 배열이라 이 차이만으로 근거가 서지는 않지만, 모델에 가는 파일 메타는 달라진다.
- 표본: 6 자식 중 1건만 대조했다(서명 범위 = 업로드 1건). 나머지 5건의 보류 값은 모른다.

## 멈춘 자리와 결정할 것

- 멈춘 자리: intent 작업 순서 3(점검) 뒤 · 4(재사전 등록) 전. 사전 등록 파일 없음 · 측정 없음 · 모델 호출 0.
- 결정 선택지(사용자):
  - ⓐ 정답 `upload_meta` 를 지금 값(등록 후 자동 메타)으로 두고, 결과를 「등록 후 자동 메타를 업로드 축으로 쓴 측정」으로만 읽는다(보고서 첫 줄에 이 점검 결과를 적는다).
  - ⓑ 정답 `upload_meta` 출처를 보류 값으로 바꾼다 — 나머지 5 자식의 보류 값 dev 읽기가 더 필요하고(별도 승인), 스냅샷 v2 에는 보류 값이 없어 동치 시험의 기준을 새 고정 파일로 옮겨야 한다.
  - ⓒ 보류 값에 없는 축(기간)만 빼고 나머지는 자동 메타로 둔다 — ⓑ 와 같은 추가 dev 읽기가 필요하다.
