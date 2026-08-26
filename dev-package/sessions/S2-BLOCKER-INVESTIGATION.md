# S2 미해소 잔존 3건 — 조사 기록

> **성격** — 읽기 전용 조사. **staging DB 쓰기·삭제·재시드 0회.** 코드·계약·마이그레이션 무수정.
> **근거 표기** — `file:line` 또는 실행 명령. 재지 않은 것은 `[미확인]`.
> **시각 표기** — DB·컨테이너 로그는 UTC. 병기 시 KST = UTC＋9.
> **경로 표기** — 프로젝트 루트(`00 CoLAB`) 기준 상대.

---

## 조사 1 — staging 데이터 소실 원인

### 1.1 판정

**원인 확정.** 소실 = **컨테이너 내부 `psql` 직접 실행에 의한 조건 없는 전량 `DELETE`**.
**제품 경로(core-api) 경유 아님**이 로그로 배제됨.

| 항목 | 값 | 근거 |
|---|---|---|
| 삭제 시각 | **2026-08-25 14:21:44 ~ 14:27:00 UTC**(= 08-25 23:21:44~23:27:00 KST) | 아래 1.3 |
| 삭제 대상 | `d3_dataset`·`d3_dataset_autometa`·`d3_dataset_description`·`d3_file`·`d4_lineage_edge`·`d4_lineage_unknown`·`d5_upload`·`d5_upload_file`·`d5_pipeline_event` | 아래 1.2 |
| 삭제 수단 | `SET app.current_lab = …; DELETE FROM <표>;` **WHERE 절 없음** | 아래 1.2 |
| 실행 주체 | **DB 계정 `[미확인]`.** 실행 경로는 **호스트에서 컨테이너 내 `psql` 세션** — 제품 API 아님 | 아래 1.4 |
| 복구 가능성 | **불가.** 보관 백업 8종 중 데이터셋 존재 구간을 덮는 산출물 0건 | 아래 1.5 |

### 1.2 삭제 문장의 실물

`docker logs colab_v2_staging_pg` 에 **실패한 삭제 시도 4회**가 남아 있음(성공 시도는 오류가 아니라 로그에 없음 — `log_statement` 미설정).

| 시각(UTC) | PID | 남은 문장 | 결과 |
|---|---|---|---|
| 2026-08-25 13:02:36.908 | 58195 | `SET app.current_lab = '…000A'; DELETE FROM d3_dataset_autometa; DELETE FROM d3_file; DELETE FROM d4_lineage_edge; DELETE FROM d3_dataset; DELETE FROM d5_pipeline_event; DELETE FROM d5_upload_file; DELETE FROM d5_upload;` | FK 위반 — `d3_dataset_description_dataset_id_fkey` |
| 2026-08-25 13:03:08.599 | 58238 | `… DELETE FROM d3_dataset_description; DELETE FROM d4_lineage_unknown; DELETE FROM d3_dataset; …` | FK 위반 — `d3_dataset_autometa_dataset_id_fkey` |
| 2026-08-25 13:03:59.943 | 58293 | 9개 표 전량 삭제(위 두 시도의 합집합) | FK 위반 — `d3_file_dataset_id_fkey` |
| 2026-08-25 13:04:21.533 | 58332 | `SET app.current_lab = '…000A'; DELETE FROM d3_dataset; DELETE FROM d5_upload;` | FK 위반 — `d3_file_dataset_id_fkey` |

- 확인 명령 = `docker logs -t colab_v2_staging_pg 2>&1 | grep -i -B3 -A3 DELETE`
- **네 시도 전부 `WHERE` 절 없음** — 픽스처·비픽스처를 가리지 않음.
- **삭제 순서를 맞추려는 반복 시도**의 형상. 네 번째 시도 뒤 삭제 문장 오류가 더 나오지 않음 = 순서를 맞춘 시도가 성공했다는 뜻.
- 같은 문장이 **레포에 없음** — `grep -rn "DELETE FROM d3_dataset"` 결과 0건, `git log --all -S "DELETE FROM d3_dataset"` 결과 0건. **커밋된 스크립트 경유 아님.**

### 1.3 삭제 시각의 확정

세 근거가 같은 구간을 가리킴.

1. **`d8_activity` 마지막 행** = `01M0WMNREVDT5A6XX8CPMAYSDJ` · `좌표계·격자 변경` · **2026-08-25 14:20:03.922 UTC**. 이 시점에 데이터셋 `01M0WMNNGNT7KPWPJGDGBFC0J6` 가 존재했음.
2. **트랜잭션 번호 순서** — 잔존 행의 `xmin` 최대값 = **921**(위 활동 행), 조회 시점 `txid_current()` = **924**. 삭제 트랜잭션은 **922 또는 923**. 즉 마지막 활동 기록 **직후**.
3. **힙 파일 기록 시각** — `PGDATA/base/16389/` 아래
   `17024`(`d3_dataset`) · `16660`(`d3_file`) · `16926`(`d5_upload`) 세 파일의 mtime이 **08-25 14:27**. 직전 체크포인트 완료 = **14:21:44.582 UTC**, 직후 체크포인트 시작 = **14:27:00.285 UTC**.
   → 삭제는 **14:21:44 ~ 14:27:00 UTC** 사이.

확인 명령
- `docker exec colab_v2_staging_pg psql -U postgres -d colab_platform -x -c "select * from d8_activity order by occurred_at;"`
- `docker exec colab_v2_staging_pg psql -U postgres -d colab_platform -c "select xmin::text::bigint, id from d8_activity order by 1;" -c "select txid_current();"`
- `docker exec colab_v2_staging_pg sh -c 'ls -la $PGDATA/base/16389/17024 …'`

`d4_lineage_edge`(`16685`) mtime = **08-25 13:07** — 계보 간선은 **13:02~13:04 시도 구간에 먼저 비워졌음**. 소실은 한 번이 아니라 **두 회차**(13:0x · 14:2x).

### 1.4 실행 경로 — 제품 API 배제

- `colab_v2_staging_core_api` 로그의 해당 구간 마지막 요청 = **2026-08-25 14:21:10.558 UTC** `POST /api/v1/previews 202`. 이후 14:35 까지 요청 0건.
  확인 = `docker logs -t colab_v2_staging_core_api 2>&1 | awk '$0 >= "2026-08-25T14:18" && $0 <= "2026-08-25T14:35"'`
- **삭제 op 자체가 제품에 없음** — `deleteDataset`·`getDatasetDeletionImpact` 는 **501**(`03-HANDOFF.md:7` 501 표).
- 귀결 = 삭제는 **API 밖**. `SET app.current_lab` 을 손으로 세우는 형태는 `psql` 세션의 형상.
- **DB 계정은 `[미확인]`** — 성공 문장이 로그에 없어 세션 주체를 재지 못함. 다만 두 연구실(A·B) 행이 함께 사라진 점은 `postgres` 슈퍼유저(RLS 우회) 또는 연구실별 반복 실행 둘 중 하나를 뜻함. **어느 쪽인지 재지 않았다.**

### 1.5 커밋 대조 — 앞선 두 커밋의 자체 보고와 어긋남

| 커밋 | 작성 시각 | diff 안의 삭제 실행 코드 |
|---|---|---|
| `03cc18c` | 2026-08-25 21:53:33 +0900(= 12:53 UTC) | **0건** — 계약·라우트·화면. 메시지에 「검증 산출물 삭제」 문구 **없음** |
| `908fbf4` | 2026-08-25 23:24:12 +0900(= **14:24:12 UTC**) | **0건** — 저장 배치·경로 계산·시험 4건. 메시지에 삭제 문구 **없음** |

- 확인 = `git show --stat 03cc18c`, `git show --stat 908fbf4`, `git log --format='%H%n%B' -40 | grep -n 삭제`
- **정정** — 두 커밋을 「검증 산출물 삭제」로 인용한 진술은 **커밋 메시지·diff 어디에도 근거가 없다.**
- 다만 **`908fbf4` 의 작성 시각 14:24:12 UTC 는 삭제 구간(14:21:44~14:27:00 UTC) 안에 있다.** 두 시도 구간(13:0x · 14:2x)은 각각 `03cc18c`(12:53 UTC) · `908fbf4`(14:24 UTC) **직후 검증 회차**와 겹친다.
- 판정 = **삭제는 두 커밋의 코드가 한 일이 아니라, 그 커밋을 검증한 회차의 사람이 손으로 한 일**이다.

### 1.6 백업이 못 살리는 이유 — 취득 시각의 공백

| 산출물 | 취득(KST) | `d3_dataset` 행 |
|---|---|---|
| `platform-20260823T044538.sql.gz` | 08-23 04:45 | 0 |
| `platform-20260823T144100.sql.gz` | 08-23 14:41 | 0 |
| `platform-20260823T161007.sql.gz` | 08-23 16:10 | 0 |
| `platform-20260824T033007.sql.gz` | 08-24 03:30 | 0 |
| `platform-20260825T033007.sql.gz` | 08-25 03:30 | 0 |
| `platform-20260825T042807.sql.gz` | 08-25 04:28 | 0 |
| **`platform-20260825T042900.sql.gz`** | **08-25 04:29** | **0** ← 삭제 직전 최신본 |
| `platform-20260826T012258.sql.gz` | 08-26 01:22 | 0 |
| `platform-20260826T033007.sql.gz` | 08-26 03:30 | 0 |

- 보관처 = `COLAB_BACKUP_DIR` 지정 홈 하위 경로(`infra/staging/backup/config.example.env:30` 의 실값 파일). 실물 산출물 = platform 9건 · ai 9건.
- 확인 = `zcat <산출물> | sed -n '/^COPY public.d3_dataset /,/^\\\.$/p'`
- **결정 사실** — 픽스처 적재 시각 = `d8_activity` 의 `데이터셋 등록` 2건 **2026-08-24 19:36:11.342 UTC = 08-25 04:36:11 KST**. **직전 백업이 08-25 04:29 KST — 7분 앞선다.**
- 그다음 백업은 **08-26 01:22 KST**, 삭제(08-25 23:2x KST) **뒤**.
- 귀결 = **데이터셋이 존재한 08-25 04:36 ~ 23:2x KST 약 19시간을 덮는 백업 산출물이 0건**이다. 「8종 전부 0」은 삭제 탓이 아니라 **취득 공백** 탓이다.
- ⚠ 백업 일정은 **1일 1회(03:30)** — `infra/staging/backup/schedule.crontab`. 그 주기가 이 공백을 만들었다.

### 1.7 재발 방지 조건

| # | 조건 | 근거 |
|---|---|---|
| 1 | **staging DB 에 대한 손 `DELETE` 를 절차로 금지한다.** 데이터 정리가 필요하면 **제품 op 또는 커밋된 스크립트**로만 한다 | 삭제 문장이 레포에 0건 — 실행 기록이 남지 않았다(1.2) |
| 2 | **정리 실행 직전 백업을 의무화한다.** 「직전 취득」이 없으면 정리를 실행하지 않는다 | 19시간 공백(1.6) |
| 3 | **`log_statement = 'mod'` 를 staging postgres 에 건다.** 지금은 **성공한 쓰기·삭제가 로그에 없다** — 실패만 남는다 | 성공 문장 부재로 주체가 `[미확인]`(1.4) |
| 4 | **백업 주기를 「일 1회」에서 「정리·배포 회차마다」로 보강한다** | 취득 시각이 사건과 어긋남(1.6) |
| 5 | **시험 픽스처와 실적재를 같은 DB 에 섞지 않는다.** 조건 없는 전량 삭제가 안전한 상태를 만든다 | 삭제 4회 전부 `WHERE` 절 없음(1.2) |

**Ted 판정 필요** — ①`log_statement` 상향을 지금 걸 것인가(로그 용량·성능 대비) ②백업 주기 보강을 S2 범위로 들일 것인가.

---

## 조사 2 — 고아 행의 FK 미차단 원인

### 2.1 판정

**스키마 결함 아님.** 네 표 모두 `dataset_id` 에 **FK 가 애초에 없다.** 부재는 **불변규칙 1(cross-domain FK 금지)의 설계 귀결**이며 주석으로 명시돼 있다.

### 2.2 제약 실물

`docker exec colab_v2_staging_pg psql -U postgres -d colab_platform -c "\d <표>"` 실측.

| 표 | 잔존 | `dataset_id` FK | 실제 FK | `ON DELETE` |
|---|---|---|---|---|
| `d6_project_dataset` | 3 | **없음** | `lab_id`→`d1_lab` · `project_id`→`d6_project` | 미지정(＝`NO ACTION`) |
| `d2_dataset_access` | 2 | **없음** | `lab_id`→`d1_lab` | 상동 |
| `d2_verified` | 2 | **없음** | `lab_id`→`d1_lab` · 승인·취소 계정→`d1_account` | 상동 |
| `d8_download` | 2 | **없음** | `lab_id`→`d1_lab` · `account_id`→`d1_account` | 상동 |

`CASCADE`·`SET NULL` 은 **어느 표에도 없다.** 삭제 순서 문제도 아니다 — **제약 자체가 부재**다.

### 2.3 설계 의도

- `db/platform/schema.sql:170` — `-- dataset_id 는 **bare 컬럼이다** — D2 가 D3 테이블을 직접 FK 하지 않는다 (CLAUDE.md §3-1).`
- `db/platform/schema.sql:602` — `-- dataset_id 는 bare 컬럼이다 — D6 가 D3 테이블을 직접 FK 하지 않는다 (CLAUDE.md §3-1).`
- `db/platform/schema.sql:642` — `d8_download.dataset_id  ulid  NOT NULL` (주석 없이 FK 부재). `d8_activity.target_id` 도 동일.
- 대조군 = **같은 도메인 안**은 FK 를 건다 — `schema.sql:262`(`d3_dataset_autometa`) · `:292`(`d3_dataset_description`) · `:332`(`d3_file`) · `:440`~`:441`(`d4_lineage_edge`) 는 전부 `REFERENCES d3_dataset(id)`. **13:0x 삭제 시도가 FK 위반으로 네 번 튕긴 것이 그 제약들이다.**
- 즉 **참조 무결성은 도메인 안에서만 기계가 지키고, 도메인 밖은 지키지 않는 것이 규약**이다. 고아 9행은 그 규약이 **설계대로 동작한 결과**다.

**결함 후보로 삼을 자리는 따로 있다** — 잔존 행을 정리하는 **애플리케이션 경로가 없다는 것**. 제품에 삭제 op 이 501 이므로(1.4) 지금은 손 SQL 말고는 수단이 없다. 이는 스키마가 아니라 **op 결손**이다.

### 2.4 append-only 트리거 — 존치 결정과 정합

- `d8_download` · `d8_activity` 에 `BEFORE UPDATE OR DELETE … deny_update_delete()` 트리거가 걸려 있다(`\d` 실측).
- 귀결 = **`d8_download` 2행·`d8_activity` 6행은 트리거를 끄지 않으면 SQL 로 지울 수 없다.**
- Ted 존치 판정 ㈎ 는 이 성질과 **충돌하지 않는다.** 반대로 삭제를 택했다면 트리거 해제가 선행 조건이 됐다.

### 2.5 재시드 시 충돌 판정

잔존 픽스처의 출처 = **`services/core-api/tests/fixtures/seed.sql`**(ID `…DSA1`·`…DSA2`·`…DSB1` 이 이 파일에만 있음 — `grep -rln 0000000000000000000000DSA2` 결과 7건 전부 시험·게이트 코드).

**같은 파일을 그대로 재적용하면 전량 충돌한다.**

| 표 | 유일성 | 잔존 키 | 재적용 결과 |
|---|---|---|---|
| `d1_lab` | PK `id` | `…000A`·`…000B` (2행 생존) | **중복** |
| `d1_account` | PK `id` | 3행 생존 | **중복** |
| `d6_project` | PK `id` | `…PRJA`·`…PRJB` | **중복** |
| `d2_dataset_access` | **PK = `dataset_id`** | `…DSA1`·`…DSA2` | **중복** |
| `d2_verified` | **PK = `dataset_id`** | `…DSA1`·`…DSA2` | **중복** |
| `d6_project_dataset` | PK `id` ＋ **UNIQUE(`project_id`,`dataset_id`)** | `…PDA1`·`…PDB1` ＋ 실 ULID 1행 | **중복 2건** |
| `d8_activity` | PK `id` | `…0AC1`·`…0BC1` | **중복 ＋ 삭제 불가**(2.4) |
| `d8_download` | PK `id` | `…0AD1`·`…0BD1` | **중복 ＋ 삭제 불가**(2.4) |
| `d3_*`·`d4_*`·`d5_*` | — | 0행 | 충돌 없음 |

확인 = `docker exec colab_v2_staging_pg psql -U postgres -d colab_platform -c "select 'd1_lab' t, id::text, name from d1_lab union all …"`

### 2.6 재시드 전 필요 조치

| # | 조치 | 사유 |
|---|---|---|
| 1 | **`fixtures/seed.sql` 을 그대로 재적용하지 않는다** | D1·D2·D6·D8 전부 중복(2.5) |
| 2 | **D3/D4/D5 만 재적용하는 부분 시드**를 쓴다 — 그 세 도메인은 0행이므로 충돌 0 | 고아 행이 오히려 **참조 대상 복원으로 해소**된다 |
| 3 | 부분 시드의 `dataset_id` 는 **잔존 고아 키와 같은 값**을 쓴다(`…DSA1`·`…DSA2`·`…DSB1`) | 다른 값을 쓰면 고아가 영구히 남는다 |
| 4 | 실 ULID 1건(`01M0TMCKMWYYZGP61BZJYD0TGC`, `d6_project_dataset`)은 **시드로 복원 불가** — E2E 산출물이다 | 이 1행만 고아로 남음. **존치 판정 ㈎ 의 실제 대상** |
| 5 | `d8_activity`·`d8_download` 는 **어떤 경로로도 지우지 않는다** | append-only 트리거(2.4) |

**Ted 판정 필요** — 부분 시드(조치 2·3)를 A·B 재시드 수단으로 채택할 것인가. 채택하면 `S2-EXEC-PLAN` 2단 관측치 고정과 4-3 「A·B 불변」 대조가 되살아난다.

---

## 조사 3 — 기준 격자 16건의 데이터셋 귀속

### 3.1 방법

- 원천 경로 = `03 Reference-Data/02.File-format/{포맷폴더}/04.Lat_Lon_info/`
- **전수 실측** = `.npy` 헤더 14건 직접 판독(형상·dtype). 명령 = `python3` 로 npy 매직 뒤 헤더 딕셔너리 읽기.
- **조각 수 대조** = 같은 포맷 폴더의 `00.Data/` 실물 개수와 `SEED-DATA.md:150-164` 의 조각 열 대조.
- 기존 실측 인용 = `DATA-REFERENCE.md:40-49`(형상·dtype 표) · `DATA-PIPELINE-MEASUREMENT.md:35-39`(격자 필요 여부).

### 3.2 조각 수 대조 — 귀속의 결정기준

| 포맷 폴더 | `00.Data` 실측 | `SEED-DATA` 조각 | 귀속 |
|---|---|---|---|
| `file_format_3_bin` | `.bin.gz` **12** | `D-15` = **12** | **`D-15` 확정** |
| `file_format_2_nc` | `.nc` **141** | `D-12` = **141** | **`D-12` 확정** |
| `file_format_5_HDF5` | `.hdf` **8** | `D-13` = **8** | **`D-13` 확정** |
| `file_format_4_tif` | `.tif` **6** | `D-14` = **6** | **`D-14` 확정** |
| `file_format_1_grib` | 원본 `.grib` **부재** | — | **범위 밖**(`〈51〉`) |

확인 = `ls "…/00.Data" | grep -c "\.nc$"` 등 4회.
**계수 4건이 전부 일치한다 — 귀속을 지어내지 않았다.**

### 3.3 16건 각각의 귀속

| # | 파일(원본 경로 = `03 Reference-Data/02.File-format/` 아래) | 형상 | dtype | 귀속 | 적재 |
|---|---|---|---|---|---|
| 1 | `file_format_3_bin/04.Lat_Lon_info/Lat_HSR.npy` | `(2881, 2305)` | `<f4` | **`D-15`** ＋ **`D-07` 과 형상 동일** | **대상** |
| 2 | `file_format_3_bin/04.Lat_Lon_info/Lon_HSR.npy` | `(2881, 2305)` | `<f4` | 상동 | **대상** |
| 3 | `file_format_3_bin/04.Lat_Lon_info/rdr_500m_latlon.nc` | `(2881, 2305)` | `<f4` | `D-15` **대체본** | **제외**(3.5-①) |
| 4 | `file_format_2_nc/04.Lat_Lon_info/lat2d.npy` | `(900, 900)` | `<f4` | **`D-12`** | 제외(`D-12`) |
| 5 | `file_format_2_nc/04.Lat_Lon_info/lon2d.npy` | `(900, 900)` | `<f4` | **`D-12`** | 제외 |
| 6 | `file_format_2_nc/04.Lat_Lon_info/gk2a_ko020lc_latlon.nc` | `(900, 900)` | `<f4` | `D-12` **대체본** | 제외 |
| 7 | `file_format_4_tif/04.Lat_Lon_info/HLS.S30.T51SYB.2025359T023019.v2.0_lat2d.npy` | `(3660, 3660)` | `<f8` | **`D-14`**(타일 T51SYB) | 제외(`D-14`) |
| 8 | `…T51SYB….v2.0_lon2d.npy` | `(3660, 3660)` | `<f8` | 상동 | 제외 |
| 9 | `…T52SCE.2025361T022121.v2.0_lat2d.npy` | `(3660, 3660)` | `<f8` | **`D-14`**(타일 T52SCE) | 제외 |
| 10 | `…T52SCE….v2.0_lon2d.npy` | `(3660, 3660)` | `<f8` | 상동 | 제외 |
| 11 | `file_format_5_HDF5/04.Lat_Lon_info/lat2d_h27v05.npy` | `(2400, 2400)` | `<f8` | **`D-13`**(타일 h27v05) | **대상** |
| 12 | `file_format_5_HDF5/04.Lat_Lon_info/lon2d_h27v05.npy` | `(2400, 2400)` | `<f8` | 상동 | **대상** |
| 13 | `file_format_5_HDF5/04.Lat_Lon_info/lat2d_h28v05.npy` | `(2400, 2400)` | `<f8` | **`D-13`**(타일 h28v05) | **대상** |
| 14 | `file_format_5_HDF5/04.Lat_Lon_info/lon2d_h28v05.npy` | `(2400, 2400)` | `<f8` | 상동 | **대상** |
| 15 | `file_format_1_grib/04.Lat_Lon_info/lat2d.npy` | `(721, 1440)` | `<f8` | ERA5 | **범위 밖**(`〈51〉`) |
| 16 | `file_format_1_grib/04.Lat_Lon_info/lon2d.npy` | `(721, 1440)` | `<f8` | ERA5 | **범위 밖** |

**귀속 확정 16 / 16. `[미확인]` 0.**

- 타일 귀속(#7~#14)의 근거는 **파일명의 타일 ID 가 `00.Data` 실물의 타일 ID 와 문자열 일치**한다는 것 — `HLS.S30.T51SYB…`·`HLS.S30.T52SCE…` / `MOD15A2H.A2019273.h27v05…`·`…h28v05…`.
- `<f8` 14건·`<f4` 4건, 형상 4종 전부 `DATA-REFERENCE.md:40-49` 기재값과 **일치**(어긋난 값 0건).

### 3.4 분리 결과

| 구분 | 건수 | 파일 |
|---|---|---|
| 적재 대상 데이터셋 귀속 | **6** | #1·#2(`D-15`) · #11~#14(`D-13`) |
| 적재 제외분(`①-b`) 귀속 | **7** | #4~#6(`D-12`) · #7~#10(`D-14`) |
| 대체본으로 제외 | **1** | #3(`D-15` 의 `.nc`) |
| 범위 밖(GRIB) | **2** | #15·#16 |

⚠ #3 은 두 구분에 걸친다(귀속은 `D-15`, 적재는 제외). 위 표는 **적재 판정 기준**으로 갈랐다 — 합 16.

### 3.5 열린 것 둘

**① `D-15` 의 격자 정본이 둘이다.**
`Lat_HSR.npy`/`Lon_HSR.npy` 와 `rdr_500m_latlon.nc` 는 **형상은 같고 값이 다르다** — lat min `30.102751`↔`30.107119`, lon max `133.553513`↔`133.560669`(약 0.004~0.007°, `DATA-REFERENCE.md:51`).
`DATA-REFERENCE.md:76` 는 **`.npy` 쌍을 정본**으로 적었다(`.nc` 는 표준위도 결손). 그리고 `〈58〉` 상한이 **데이터셋당 2건(위도·경도 한 쌍)** 이므로 **세 파일을 다 붙일 자리가 없다.**
→ **적재는 `.npy` 쌍 2건만.** `.nc` 는 원천 보존, 적재 제외.

**② `D-13` 은 타일 2장인데 격자 상한이 2건이다.**
`h27v05`·`h28v05` 두 타일 × 위도·경도 = **격자 4건이 필요**한데 `〈58〉` 상한은 **데이터셋당 2건**이다. 지금 규약으로는 **`D-13` 에 격자 4건을 붙일 수 없다.**
완화 요인 = **HDF4 는 격자 파일이 불필요하다** — 꼬리 `StructMetadata` 의 코너좌표·Sinusoidal·R=6371007.181 로 계산되고 **실측 오차 7e-14°(7.8 nm)** (`DATA-PIPELINE-MEASUREMENT.md:38`).
→ **`D-13` 은 격자 파일을 안 붙여도 성립한다.** 상한 충돌은 「붙이려 할 때만」 생긴다.

### 3.6 적재 대상 11건 중 격자가 **필요한** 데이터셋

판단기준 = `DATA-PIPELINE-MEASUREMENT.md:35-39` 의 「기준 격자 필요 여부」 실측. **필요는 HSR 하나뿐**이다 — 헤더 1024 B 중 투영 파라미터 자리(36~63 B)가 **전부 0** 이라 재현 불가(오차 5.9 km).

| 데이터셋 | 포맷 | 격자 필요 | 격자 파일의 원본 경로 |
|---|---|---|---|
| **`D-07`** HSR 레이더 합성 반사도 (Lv.0) | bin | **필요 — 대체 불가** | `03 Reference-Data/01.level-data/01.precipitation/01.precipitation/#metadata/LAT_HSR.npy` · `…/LON_HSR.npy` |
| **`D-15`** HSR 레이더 견본 | bin | **필요 — 대체 불가** | `03 Reference-Data/02.File-format/file_format_3_bin/04.Lat_Lon_info/Lat_HSR.npy` · `…/Lon_HSR.npy` |
| `D-01`~`D-06` · `D-08` · `D-09` · `D-13` | tif·nc·hdf 등 | **불필요** — 파일 내부 정보로 계산(오차 0) | — |

⚠ **`D-07` 의 격자는 16건 밖이다.** `01.level-data` 하위 `#metadata/` 에 별도 사본이 있고(`DATA-PIPELINE-MEASUREMENT.md:323` 의 `LAT/LON_HSR` 행 — `2881×2305 f32, 26.6 MB×2`), 이는 `02.File-format` 의 16건에 **포함되지 않는다.**
→ **적재 매니페스트의 격자 항목 = 총 4건**(`D-07` 2 ＋ `D-15` 2). 나머지 12건은 **적재 제외분·범위 밖·대체본**이다.
⚠ `D-08`(RN15 지상 강수)의 격자 `LAT/LON_RN15`(`2049×2049 f32`, `DATA-PIPELINE-MEASUREMENT.md:324`)도 `01.level-data` 에 있으나, **RN15 는 `.npy` 배열이라 격자 필요 판정 대상이 아니다** — 이 조사에서 **재지 않았다**(`[미확인]`).

**Ted 판정 필요** — ①`D-07`·`D-15` 두 데이터셋에 **같은 형상의 서로 다른 격자 사본**(level-data 본 · File-format 본)을 각각 붙일 것인가, 한 쪽으로 통일할 것인가 ②`D-08` 의 격자 필요 여부를 stage 1 에서 잴 것인가.

---

## 부록 — 이 조사가 만진 것

- **DB** — `SELECT` 전용. `INSERT`·`UPDATE`·`DELETE`·DDL **0회**.
- **원천 데이터** — 읽기만. `.npy` 헤더 판독 14건.
- **코드·계약·마이그레이션** — 무수정.
- **산출** — 이 문서 1건.
