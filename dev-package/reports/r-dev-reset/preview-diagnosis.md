# R-DEV-RESET — 업로드 직후 미리보기 미표시 진단 (읽기 전용)

- 작성 2026-09-14 · 역할 `researcher` · 작업 id `db820488b2ae41ea8af9559c44e05b94`
- 성격 = **읽기 전용.** 레포 코드 수정 0 · 재기동 0 · DB DML/DDL 0 · S3 쓰기 0. 비밀값 미기재.
- 실측 = dev EC2 `docker compose logs --since 3h`(19,948행) · `docker inspect` · `dmesg -T` · `aws s3 ls`(프로파일 `colab-dev`) · `psql` 읽기 전용 롤 `colab_backup`(`/etc/colab/backup-platform-db.url`) SELECT 3회.
- 로그 시각은 UTC. KST = UTC+9.

## 1. 생성 방식 — **동기(요청 시 생성)다. 업로드 완료 큐가 아니다**

- 화면 경로 = `POST /api/v1/previews` → core-api 중계 → viz-render `POST /viz/v1/renders`(202) → 화면이 `GET /api/v1/previews/{renderId}` 폴링.
  근거 `services/core-api/src/colab_core/app/routes/preview.py:188-246` · `services/viz-render/src/colab_viz/app/routes/renders.py:70`.
- **업로드 완료 시 미리보기를 거는 워커 잡이 없다.** `pipeline-worker` 쪽 트리거는 **이미 그린 대상의 재생성**만 한다 — 그린 적 없는 대상은 `LookupError` 로 걷힌다.
  근거 `services/viz-render/src/colab_viz/app/triggers.py:49-60`.
- viz-render 는 **요청 스레드에서** S3 내려받기와 포맷 감지를 끝낸 뒤에야 202 를 낸다. 축자 주석(`services/viz-render/src/colab_viz/app/routes/renders.py:91-92`)
  > `detect_format` 이 파일 전체를 요구하므로 요청 스레드에서 한다 — 지연은 `〈340〉` 전환 조건의 실측 항목.
- 렌더 작업 상태는 **DB 에 없다.** `d3_*`·`d5_*` 어디에도 preview/render 테이블이 없다(`information_schema.tables` 조회 15행 중 0건). 작업 저장소는 viz-render 프로세스 안이다 — **재시작하면 사라진다.**
- 화면 대기/실패 표기 = `getPreviewRender` 는 실패도 200 으로 내고 `failure` 에 사유를 담는다(`preview.py:236-238` 독스트링). 중계가 끊기면 그 대신 **503** 이 간다.

## 2. 실측 차단 요인 3가지

| # | 요인 | 값·근거 |
|---|---|---|
| ㉮ | **중계 타임아웃 10초 고정** | `services/core-api/src/colab_core/app/relay.py:28` `RELAY_TIMEOUT_SECONDS = 10`. 같은 창의 viz-render 실소요 **20,037 ms · 26,766 ms · 29,440 ms · 33,391 ms · 33,567 ms · 35,602 ms · 38,391 ms**(전부 202 로 끝남). core-api 는 10,02x ms 에 끊고 **503** 을 냈다 — 화면은 `renderId` 를 못 받는다 |
| ㉯ | **viz-render OOM kill 2회** | `dmesg -T` — `Memory cgroup out of memory: Killed process … (python) … anon-rss:1518944kB`(14:29:58Z) · `anon-rss:1562976kB`(15:06:56Z). 한도 `COLAB_MEM_VIZ=1536m`. `docker inspect … RestartCount=3`, 마지막 기동 `2026-09-13T15:06:56Z`. 재시작으로 진행 중이던 렌더 작업이 전부 소실 |
| ㉰ | **413 4회** | `POST /api/v1/previews` 413 — 15:05:52 · 15:06:07 · 15:06:19(+ `preview-target-descriptions` 동수). 사유 후보 둘 = `max_render_bytes` 기본 500 MiB(`services/viz-render/src/colab_viz/kernel/config.py:65`) 초과, 또는 작업 디렉터리 상한 `COLAB_VIZ_WORK_MAX_BYTES=1073741824`(1 GiB) 초과 시 `WorkspaceExceeded`(`services/viz-render/src/colab_viz/app/routes/renders.py:96-98`). **응답 본문이 로그에 없어 어느 쪽인지 `[미확인]`** |

- 파생 500 2회 = `preview.py:246 get_preview_render` → `relay.py:263` → `ConnectionResetError: [Errno 104] Connection reset by peer`(OOM 으로 끊긴 연결).
- 창 전체 계수(15:04~15:08Z) = `POST /api/v1/previews` **202 9건 · 503 10건 · 413 3건 · 500 1건**. 계수 기준 = `"path":"/api/v1/previews"` 정확 일치 행.

## 3. 포맷별 핸들러 — 「지원 안 함」 해당 0건

- viz-render `read_field` 분기 7종 전부 존재 — GeoTIFF·NetCDF·HDF4·Binary·NumPy·GRIB·HDF5(`services/viz-render/src/colab_viz/domains/d7_visualization/readers.py:767-780`).
- pipeline-worker `NOT_RENDERABLE_FORMATS: list[str] = []`(`services/pipeline-worker/src/colab_pipeline/d5/renderable.py:32`) — **GRIB 을 빼는 목록이 비어 있어 6종 전부 `renderable=true`** 다. 같은 파일 독스트링은 아직 「GRIB 은 미리보기 대상이 아니다」라고 적고 있다. **산문과 코드가 갈려 있다**(후속 항목 1).
- HDF4 = `readers.py:150-151` 매직 `0e031301` 로 감지, `_read_hdf4`(`:577`) 존재. `DATA-REFERENCE` 의 「폴더명 HDF5 · 실체 HDF4」 실측과 같은 자리.

## 4. S3 `previews/` 실측

- 객체 **518건**(2026-09-14 00:2x KST · `aws s3 ls s3://colab-platform-data-dev/previews/ --recursive | wc -l`). 시각대 분포 = 09-13 22시 126 · 23시 288 · 09-14 00시 104.
- 사이드카 `.json` **234건**을 내려받아 `baked_for.target_id` 로 대조한 결과:

| 포맷 | 데이터셋 id | 산출물 층 | 생성 시각(KST) |
|---|---|---|---|
| grib | `01M2DHTD0Y37RJKF04VS5VZ3KN` | 3층(비지도형·썸네일·지도형) | 00:06:54 |
| nc | `01M2DJKW31M6WJT8WGFRA0WVYN` | **0건** | — |
| bin | `01M2DK2WBR6GZ5KB6NEMXM9YW5` | 2층(비지도형·썸네일) · **지도형 없음** | 00:07:41 |
| tif | `01M2DKFZ98ZZFF50Y99M0TZN91` | 3층 | 23:42:19 |
| hdf4 | `01M2DM3550JHG8AE6X466QT0TB` | 3층 | 23:52:58 |

- 파일 실측(`d3_file`) — grib = `surface.grib` **149,514,336 B 단일 1건**. nc = `gk2a_ami_le2_lst_ko_*.nc` 다수(건당 약 34만~40만 B).
- ⚠ **S3 실물이 화면 관측과 반대다.** 「그려짐」으로 보고된 nc 는 산출물 0건이고, 「안 그려짐」 4건 중 tif·hdf4 는 00:04 판정 시점에 이미 산출물이 있었다. 이 어긋남의 뜻 = **화면 미표시의 원인은 산출물 부재가 아니라 그 순간의 렌더 요청이 503 으로 끊긴 것**이다(`[추론]`).

## 5. 포맷별 판정

| 포맷 | 판정 | 한 줄 원인 |
|---|---|---|
| grib | **대기 중(동기 경로가 10초에 끊김)** | 149,514,336 B 단일 파일 내려받기+감지가 20~38초 → 중계 10초 타임아웃 503. 크기 상한 500 MiB 미만이라 413 사유 아님. 산출물은 00:06:54 에 결국 생성 |
| bin | **대기 중 · 지도형 층만 미생성** | 썸네일·비지도형 00:07:41 생성. **지도형 부재 사유는 `[미확인]`** — HSR 기준격자쌍 부착 여부를 `d5_upload_grid_profile`·`d3_dataset_grid_profile` 로 확인하지 못했다 |
| tif | **렌더 실패 아님 — 중계 503** | 3층 산출물 23:42:19 존재. 3밴드 HLS 다밴드 처리 여부는 이번에 재지 않았다 `[미확인]` |
| hdf4 | **렌더 실패 아님 — 중계 503** | 3층 산출물 23:52:58 존재. HDF4 핸들러 `readers.py:577` 실재 |
| nc | **`[미확인]`** | 화면에서는 그려졌다고 보고되었으나 S3 사이드카 0건. 파일이 건당 40만 B 이하라 10초 안에 끝났을 개연 `[추론]` |

## 6. 각각을 무엇이 닫는가

1. **grib·tif·hdf4·bin 공통** — `RELAY_TIMEOUT_SECONDS = 10` 을 렌더 경로만 늘리거나, viz-render 의 `materialize`+`detect_format` 을 202 이전에서 빼 **진짜 비동기**로 만든다(`renders.py:91-92` 주석이 이미 그 전환을 `〈340〉` 조건으로 예고). **코드 수정 · 레인 1건**.
2. **OOM** — `COLAB_MEM_VIZ=1536m` 상향 또는 동시 렌더 수 제한. 149 MB 단일 파일 1건이 RSS 1.5 GB 를 만든다. **배포 env 변경 · 판정 필요**.
3. **413** — 응답 본문(`limitBytes`·`reason`)을 로그에 남기는 관측 추가 뒤 재현. 현재는 두 상한 중 어느 쪽인지 가릴 근거가 없다.
4. **bin 지도형** — 격자쌍 부착 상태 조회 1회로 닫힌다.
5. **nc** — 렌더 산출물이 S3 에 없는데 화면에 그려진 경로를 확인한다(캐시·로컬 싱크 잔존 여부).

## 7. 후속 항목 (이 작업에서 고치지 않는다)

1. `d5/renderable.py:32` `NOT_RENDERABLE_FORMATS = []` 와 같은 파일 독스트링(「GRIB 은 미리보기 대상이 아니다」)이 갈려 있다. 어느 쪽이 정본인지 판정 필요.
2. 렌더 작업 상태가 프로세스 메모리에만 있어 재시작마다 진행 중 작업이 소실된다. `deploy_doctor` 에 걸리는 항목 없음.
3. 미리보기 경로에 데이터셋 id 를 싣는 구조화 로그가 없다 — 이번 진단에서 요청↔데이터셋 대응을 시각으로만 추정해야 했다.
4. ⚠ 조사 중 호스트 env 를 정규식으로 grep 하다 **토큰 2건이 조사 세션 출력에 노출**됐다(파일·커밋에는 미기재). 회전 여부 판정 필요.
