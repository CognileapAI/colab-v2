# PV1-CONSUMER-BUILD — 미리보기 뒷단: 소비자·유실 감지·타일 키를 한 회차에 세운다

> 시점 = 2026-08-30 (+09:00) · 브랜치 = `wt/lane3-map` · 기점 = `76e6ed5`(main)
> 운영 스택 `colab_v2_staging_*` 은 **조회만** 했다(정지·재기동·DDL·쓰기 0건 · 접속 문자열 미출력).
> 일회용 postgres 는 `--rm` ＋ tmpfs ＋ `PGDATA` 지정 ＋ 호스트 포트 미공개로만 썼다.
> **번호 발급됨 = `PLAN-SoT §9 〈223〉`** (2026-08-30 번호 발급 회차에서 등재).

---

## 1. 전제 재검증 — 넷 다 참 (2026-08-30 실측)

| 전제 | 실측 | 판정 |
|---|---|---|
| 미리보기 산출물 슬롯과 그 쓰기 자리가 실재 | `contracts/storage/layout.json` `keys."미리보기 산출물"` · `preview.py` `_write()` → `preview_key()` | **참** |
| 그 슬롯 적재 39건 · 전부 렌더 산출물 · 지도 타일(.tif) 0 | `docker exec colab_v2_staging_viz_render ls -1 /srv/viz-previews` = **39** (`png` 16 · `webp` 9 · `json` 7 · `pgw` 7 · **`tif` 0**) | **참** |
| 기존 키 규칙이 렌더 파라미터 다이제스트를 요구 · 파이프라인에 그 재료 없음 | `d7_visualization/cache.py#render_cache_key` 입력 = 팔레트·선택 변수·다운샘플·긴 변·색범위. `d5/**` 에 그 값 0건 | **참** |
| 업로드 15건 전건 등록 전환 완료 → 스위치만 풀면 대상 0 | `d5_upload` = **15** · `registered_at` **15** · `ready` **0** → `pending_uploads()` = **0** | **참** |

덧붙여 잰 것 — `d5_pipeline_event` = `upload.accepted` 15 · `file.format-detected` 3 · `upload.failed` 3 ·
`d3_dataset_autometa` 12행 중 `format`·`crs`·`grid` **각 0**. **오늘 유실 감지를 staging 에 걸면 red 다. 그것이 옳다.**

## 2. 무엇을 세웠나

### ㉮ 지도 타일 **전용 내용 키 규칙** — 슬롯은 그대로, 키만 가른다

- 정본 = `contracts/storage/layout.json` 의 새 절 `contentKeys` — 한 슬롯에 **키를 만드는 자리가 둘**이라는 사실을 못 박는다.
- 재료 여섯(전부 필수 · 기본값 없음) = 원본 다이제스트 · 원본 크기 · 격자 다이제스트 · 변환 종류 · 오버뷰 리샘플링 · 압축.
  **렌더 파라미터를 하나도 쓰지 않는다** — 그래서 D5 가 D7 의 개념을 갖지 않는다.
- 접두사 `tile-` 로 한 디렉터리 안에서 두 규칙이 눈으로도 갈린다. 생성물은 세 단위 **바이트 동일**(codegen 등기부 그대로).
- 좌표가 파일 안에 있던 경우의 격자 다이제스트는 **명시값 `내장`** — 빈 값으로 두면 「격자가 없다」와 「안 물어봤다」가 같은 키를 얻는다.

### ㉯ 소비자 — 사건 → 장부. **반영 시점 = 등록 전환**

- 읽기: `core-api` `domains/d5_ingestion.py` 한 파일(=`d5_*` 를 만지는 유일한 파일) 에 `held_auto_metadata()`.
- 쓰기: `domains/d3_catalog.py` `apply_autometa()` — **비어 있는 칸만** 채운다(`COALESCE`). 사람이 고친 값을 덮지 않는다.
- 호출: `createDataset` 트랜잭션 안, 장부 행이 선 **직후**. 반쪽이 남지 않는다.
- 두 사건이 서로 다른 칸을 채운다 — `format` 은 ②, `crs`·`grid`(＋변수·기간·용량)는 ③.

### ㉰ **보류된 사건이 어디 사는가 — `d5_pipeline_event` 행 그 자체다**

- 새 큐도, 새 표도, 프로세스 메모리도 **만들지 않았다.** 사건 행은 이미 내구 저장이고 업로드와 함께
  지워진다(`ON DELETE CASCADE`), 멱등 키가 `<타입>:<uploadId>` 라 타입당 한 건이다.
- 그래서 「보류 목록」은 자료구조가 아니라 **질의**다 — 두 벌이 될 수 없고, 재기동을 건너 산다.
- 메모리를 골랐다면 재기동에서 사라졌을 것이고, **사라진 사실은 「값이 원래 없었다」와 구분되지 않는다.**

### ㉱ 유실 감지 — 게이트 `autometa-loss` ＋ `autometa-loss-selftest` (**같은 회차**)

- 세는 단위 = **(업로드, 칸) 쌍**. 업로드로 세면 「`format` 은 받고 `crs` 는 못 받은」 상태가 접힌다.
- 이음 = `d5_upload_file.id = d3_file.id`(`NB-A` 동일성). 업로드→데이터셋 FK 는 없다(불변규칙 1).
- 세 상태 — 대상 있으면 검사 · `gates/config/autometa-loss.toml` 에 **이름으로** 적히면 건수를 드러낸 채 통과 · **아무 말 없으면 red**.
  적용 DB URL 부재도 red(`schema-diff` 와 같은 변수·같은 규율), **대상 0건도 red**.

### ㉲ 워커 스위치 — `stage1=True` 하드코딩 해제

- `COLAB_WORKER_STAGE2` = `on`｜`off`｜무언. `on` 인데 `COLAB_WORKER_PREVIEW_DIR` 이 없으면 **뜨지 않는다.**
- **무언을 면제로 세지 않는다** — 동작은 `off` 와 같되 한 줄로 「선언되지 않았다」를 적고, 그 상태에서 값이
  안 채워지는 것은 게이트가 red 로 받는다. 여기서 프로세스를 죽이지 않은 이유 = 도는 배포가 재기동에서
  서지 못하면 그것은 검사가 아니라 사고다. **판정처는 게이트, 여기는 사실을 말하는 자리.**

### ㉳ 순서표 — `WORK-UNITS §10.3` **1단**에 등재

무의존이고 안에서 ①소비자 → ②유실 감지 → ③스위치 → ④타일 자리 순으로 갈린다는 것,
그리고 **켜도 기존 15건은 대상 밖**이라 검증은 새 업로드 1건으로만 성립한다는 것을 함께 적었다.

## 3. 실측 — 시험과 게이트

| 잰 것 | 값 | 시점·방법 |
|---|---|---|
| `core-api` 전량 | **479 passed · 0 failed · 0 skipped** | 일회용 postgres(선언 스키마 ＋ 앱 롤 ＋ 시드) · 2026-08-30 |
| 그중 이번 신설(`test_autometa_from_events.py`) | **8 passed** | 같은 실행 |
| **그 8건의 red 증명** | 소비자 호출부를 걷어내면 **3 failed / 5 passed** | 픽스처로 실측(주장 아님). 나머지 5 는 「지어내지 않는다」를 보는 음성 시험이라 green 이 옳다 |
| `pipeline-worker` 신설 2파일 | **17 passed** | `.venv` · 2026-08-30 |
| `stage2-markers` 게이트 | **green** (마커 시험 전량) | `gates/run.sh` |
| `autometa-loss-selftest` | **green — 검사 8건 전건 기대대로**(red 5 · green 2 · 건수 노출 1) | 일회용 postgres |
| 게이트 전량 `all -j 2` | **green 27 / red 2** (게이트 29종 = 기존 27 ＋ 신설 2) | 2026-08-30 · 환경 완비 후 |

**red 2의 정체 — 둘 다 적용 DB 부재이고, red 인 것이 옳은 동작이다.**
① `schema-diff` — 적용 DB 미지정(기점과 동일) ② `autometa-loss` — **이번에 신설.** 적용 DB 미지정.
지정하면 오늘 staging 에서는 **유실 3건으로 red** 가 난다(§1 실측).

**기점 재측정 주의 — 워크트리에는 실행 환경이 딸려 오지 않는다.**
이 워크트리의 첫 측정은 `green 24 / red 3` 였다: `stage2-markers` 는 `pipeline-worker/.venv` 부재로,
`generated-up-to-date` 는 `frontend/node_modules` 부재로 red 였다. **둘 다 코드가 아니라 환경이다.**
venv 와 node_modules 를 세운 뒤 기점 상당은 `green 27 / red 1`(`schema-diff`)이고, 지시가 준
`green 26 / red 1` 과는 게이트 총수가 다르다(신설 2종 반영 전후). **「어느 쪽이 틀렸다」가 아니라 시점이 달랐다.**

## 4. 세 상태 증명 (검사마다 red 를 픽스처로 못 박았다)

| 검사 | 대상 있음 → 검사 | 명시 면제 → 건수 노출 | 무언 → red | 증명 |
|---|---|---|---|---|
| `autometa-loss` | ⓓ 유실 3건 red · ⓔ 전건 반영 green | ⓕ 면제 3건 green ＋ **출력에 「면제 3」** | ⓐ 적용 DB 미지정 · ⓑ 면제 파일 부재 · ⓑ' 면제 항목 부재 · **ⓒ 대상 0건** 전부 red | `autometa-loss-selftest` 실행 |
| 지도 타일 키 | 재료 여섯이 다 있으면 키 | 해당 없음(면제 개념 없음) | 재료 하나라도 없으면 **ValueError** | `test_map_tile_key.py` 파라미터 시험 6종 |
| stage 2 선언 | `on` 이면 돈다 | `off` = 명시 면제 · 문구에 드러난다 | 무언 = 「미선언」으로 적고 면제로 세지 않음 · 값 집합 밖은 예외 | `test_stage2_declaration.py` |
| 사건 반영 | 값 있으면 채운다 | 사람이 고친 칸은 안 덮는다 | 사건 0건이면 **채우지 않는다** | `test_autometa_from_events.py` |

## 5. 이번에 세지 않은 판단기준 (다음 회차 진입조건)

- **새 업로드 1건의 실동작** — `COLAB_WORKER_STAGE2=on` ＋ `COLAB_WORKER_PREVIEW_DIR` 을 배포에 넣고 돌려야 잰다. `[미확인]`
- **지도 타일이 staging 볼륨에 실제로 떨어지는가** — 배포 설정(볼륨 마운트)이 붙어야 성립한다. `[미확인]`
- **기존 12 데이터셋의 소급 반영** — 별건(원장 되쓰기). 대상 목록을 고정한 뒤 판정. 그때까지 면제 선언은 **비어 있다**.
- **`upload.ready` 발행 0건인 채 15건이 등록된 경위** — `PV-WIRING-SCOPE §8-㉠` 그대로 열려 있다.
- **미리보기 뒷단 항목의 완료 정의** — 대장에서 이번에 확인하지 않았다. `[미확인]`

## 6. Ted 판정이 필요한 자리 (이번에 결정하지 않았다)

1. **배포에 `COLAB_WORKER_STAGE2=on` 과 `COLAB_WORKER_PREVIEW_DIR` 을 넣는 것** — 운영 접촉이라 하지 않았다.
   넣지 않으면 stage 2 는 계속 안 돌고, 게이트가 그 사실을 red 로 말한다.
2. **`autometa-loss` 를 CI 에서 어느 DB 에 대는가** — `schema-diff` 와 같은 변수를 쓴다. 지정하지 않으면 상시 red 다.
3. **소급 반영(기존 12건)의 거취** — 별건으로 두면 그동안 면제 선언에 12건을 이름으로 적어야 통과한다.

## `PLAN-SoT §9` 등재 완료 — **번호 `〈223〉` 발급됨 (2026-08-30 · 번호 발급 회차)**

> 정본은 `dev-package/PLAN-SoT.md §9 〈223〉` 다. 아래는 등재에 쓴 원문이고, 값의 정본이 아니다.
>
> (원 제목: `PLAN-SoT §9` 등재 문안 (번호는 오케스트레이터가 발급))

> **〈223〉 미리보기 뒷단 — 사건 경유 되쓰기·유실 감지·지도 타일 키를 한 회차에 세운다.**
> **전제 넷 재검증 = 전건 참**(2026-08-30 실측): 슬롯·쓰기 자리 실재 · 슬롯 적재 39건 전부 렌더 산출물(`.tif` 0) ·
> 기존 키 규칙이 요구하는 렌더 파라미터가 파이프라인에 없음 · 업로드 15건 전건 등록 전환(pending 0).
> **집행 = ⓐ 지도 타일 전용 내용 키 규칙(`contracts/storage/layout.json` `contentKeys` 신설 · 재료 여섯 전부 필수 ·
> 접두사 `tile-` · 세 단위 생성물 바이트 동일) ⓑ 사건 → 장부 소비자(반영 시점 = **등록 전환 트랜잭션**) ·
> **보류함은 `d5_pipeline_event` 행 자체**(새 표·큐·메모리 0 — 재기동을 건너 산다) ⓒ 유실 감지 게이트
> `autometa-loss` ＋ selftest(세는 단위 = (업로드, 칸) 쌍 · **대상 0건도 red** · 면제는 이름으로만 · 건수 노출) ⓓ 워커
> `stage1=True` 하드코딩 해제 → `COLAB_WORKER_STAGE2` 선언(무언을 면제로 세지 않는다) ⓔ 순서표 1단 등재.**
> **실측 = `core-api` 479 passed(신설 8 · 소비자를 걷어내면 3 failed 로 red 증명) · `pipeline-worker` 신설 17 passed ·
> 게이트 `all -j 2` green 27 / red 2(게이트 29종).** red 둘은 전부 적용 DB 부재이고 red 가 옳은 동작이다 —
> `schema-diff`(적용 DB 미지정 · 기점 동일) ·
> **`autometa-loss`(이번 신설 · 적용 DB 미지정). 적용 DB 를 대면 오늘 staging 은 유실 3건으로 red 다** —
> `file.format-detected` 3건 발행 대비 `d3_dataset_autometa.format` 0건.
> **범위 밖 = 기존 12 데이터셋 소급 반영(별건 · 면제 선언 비어 있음) · 배포 환경변수 주입(운영 접촉) ·
> 새 업로드 1건의 실동작(`[미확인]`).**
