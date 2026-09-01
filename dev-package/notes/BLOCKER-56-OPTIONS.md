# 블로커 #56 — 등록 전환 시 미리보기 산출물 소유 이전 · 선택지 셋의 사실 대조

조사 회차 2026-09-01 · 읽기 전용(코드·설정·계약 실물 대조) · 이 파일 외 편집 0건.
인용은 전부 `파일:줄`. 값이 없는 자리는 `[미측정]` 로 적고 지어내지 않았다.

## 1. 지금의 실물 — 어디에 굽고 어디서 읽는가

| 사실 | 값 | 근거 |
|---|---|---|
| 접수분 배치 | `uploads/{targetId}/{fileId}` · 격자는 `uploads/{targetId}/grid/{fileName}` | `contracts/storage/layout.json` `keys` |
| `targetId` 의 뜻 | **등록 전 `uploadId` · 등록 뒤 `datasetId`** | `contracts/storage/layout.json` `targetId` |
| 등록 때 바이트 이동 | `os.replace` 로 `uploads/{uploadId}/` → `uploads/{datasetId}/`, 모든 판정 뒤 마지막 단계 | `services/core-api/src/colab_core/app/routes/ingestion.py:125`(`_relocate`) · `:551` · `:710` |
| 미리보기 산출물 배치 | **평평하다 — 경로에 대상이 없다**: `{contentKey}{extension}`, 별도 루트(`previews`) | `contracts/storage/layout.json` `keys.미리보기 산출물` · `why` ③ · `roots` |
| 렌더 산출물 키 | `render_cache_key` — 원본 다이제스트·팔레트·변수·다운샘플·긴 변·좌표계·색범위. **대상 ID 없음** | `services/viz-render/src/colab_viz/domains/d7_visualization/cache.py:28-55` |
| 지도 타일 키 | `tile-` + sha256(`sourceDigest`·`sourceByteSize`·`gridDigest`·`conversionKind`·`overviewResampling`·`compression`). **대상 ID 없음** | `services/viz-render/src/colab_viz/kernel/storage_layout.py:124-170` · `services/pipeline-worker/src/colab_pipeline/d5/pipeline.py:100-118` |
| 굽는 시점의 대상 | `uploadId`(D5 는 업로드 사건에서만 돈다) | `dev-package/sessions/ARTIFACT-OWNER-DESIGN-20260831.md:700-708` 표 |
| 등록 뒤 읽는 대상 | `datasetId` — D7 은 `uploads/{datasetId}` 디렉터리를 훑는다(원장 없음) | `services/viz-render/src/colab_viz/ports/source.py:101-124` |
| 등록 경로의 재굽기 트리거 | **없다** | 같은 표(설계문 `:704`) |
| core-api 볼륨 | `uploads` **하나**. `previews` 는 nginx(:ro)·pipeline-worker·viz-render 에만 | `infra/staging/compose.i2.yml:199-200`(core-api) · `:46`·`:283`·`:338` |

### 1-a 불일치의 정확한 자리 — **오늘이 아니라 안 ⑴ 이후에 생긴다**

오늘의 미리보기 자리는 **내용 주소 · 평평**이라 등록 전환이 경로를 바꾸지 않는다.
`_relocate` 는 같은 볼륨 안의 `os.replace` 라 **바이트가 그대로**이고, 따라서 `sourceDigest`·
`gridDigest` 가 그대로이며 **키도 그대로**다 — 지금 배선에서는 옮길 것이 없다.

깨지는 것은 **A-1 이 채택한 안 ⑴(데이터셋 종속 전환)** 을 배선한 뒤다. 안 ⑴ 은 자리를
`{previewsRoot}/{targetId}/{contentKey}{ext}` 로 바꾼다(`ARTIFACT-OWNER-DESIGN-20260831.md:700`).
그 순간 경로에 `targetId` 가 들어가고, `targetId` 는 등록에서 `uploadId` → `datasetId` 로 바뀐다.
⟹ 등록된 데이터셋의 지도 미리보기가 **에러 없이 빈 채로** 뜬다(`:706`). `#20` 과 같은 무늬다.

`#20` 이력 — core-api 는 `uploads/{targetId}/{fileId}` 로 평평히 놓는데 viz-render 는 격자를
`{root}/{targetId}/grid/` 에서 찾았고, **그 디렉터리를 만드는 코드가 없어** ③지도형이 서지 않았다.
①② 는 200 이라 상태코드로는 안 보였다. 해소 = 2026-08-26 `〈115〉-㉮`, 실적재 6 데이터셋 전건 완료
(`dev-package/03-HANDOFF.md:368`). 규약을 안 세운 대가라는 판단이 `layout.json` `$comment` 에 박혀 있다.

## 2. 경계 규칙의 축자

- `CLAUDE.md:59` — 「**도메인은 자기 테이블 + D1(shared kernel)만 참조한다.** 타 도메인 테이블 직접
  FK·접근 금지. cross-domain은 Port 경유」
- `CLAUDE.md:90-94` — 「경계를 넘어야 할 때 … 우회하지 말고 **멈추고 보고한다.** 셋 중 하나다.
  1. Port를 하나 추가하면 되는가 (경계 유지) 2. 도메인이 잘못 쪼개졌는가 3. 기획이 애매한가」
- `contracts/events/envelope.json` `description` — 「경계 — 페이로드는 D5 가 소유한 `uploadId`·`fileId` 와
  D1 의 `labId`·`actorAccountId` 만 싣는다. **다른 도메인 테이블을 직접 가리키는 식별자(`datasetId`·
  `projectId`·계보 관계 ID)를 두지 않는다**(CLAUDE.md §3-1).」
- `X2-FREEZE-PROTOCOL §5-㉰-4` — 계약만 열고 배선을 미루는 것 금지(`03-HANDOFF.md` #56 행 인용).
- `CLAUDE.md:100-104` — 게이트 우회·검사 축소 금지(green-by-skip).

⚠ 마지막 인용이 ⓑ·ⓒ 모두에 걸린다 — **등록 사건을 이벤트로 보내려면 페이로드에 `datasetId` 가 필요하고,
봉투가 그것을 명시적으로 금지한다.** 이 제약은 ⓑ 만의 것이 아니라 ⓒ 의 트리거에도 똑같이 걸린다.

## 3. D5→D7 이벤트 계약의 현재 상태 (Y-1 배선이 남긴 것)

- `EventType` **10종** — E-04 7종(core-api ↔ pipeline-worker) ＋ 12차 해제로 더한 3종
  (`preview.backend-rerun`·`preview.grid-changed`·`preview.file-added`, D5 발행 → D7 수신).
  `contracts/events/envelope.json` `$defs.EventType`.
- `Source` 열거는 **`core-api`·`pipeline-worker` 둘 그대로** — core-api 가 발행자로 이미 서 있다.
- 멱등 키 = `<타입>:<uploadId>`(`$defs.IdempotencyKey`), 정규식이 뒤에 **ULID 하나**를 요구한다.
- `Delivery` 블록이 at-least-once 재전달·시도 상한을 봉투에 싣는다.
- 발신 실물 — `services/pipeline-worker/src/colab_pipeline/d5/events.py`(238줄 · `make_envelope`·
  타입별 payload 빌더 · `preview_stale_payload:193`), spool 은 `COLAB_WORKER_EVENT_SPOOL`.
- 수신 실물 — `services/viz-render/src/colab_viz/app/trigger_bus.py:57` `SpoolTriggerPort`
  (`poll`·`ack`·`_discard`, 128줄) → `domains/d7_visualization/invalidation.py`(175줄, 트리거 3종 상수 ·
  `apply()` 한 자리).
- core-api 쪽 발행 실물 — `domains/d5_ingestion.py:282` `publish_accepted`(「core-api 가 내는 유일한
  이벤트」), outbox insert 는 `ON CONFLICT DO NOTHING` 으로 멱등(`:112-120`), 키 생성 `:155`.
- 등록 시점의 후크가 이미 있다 — `mark_registered(upload_id)` 가 `routes/ingestion.py:484`·`:690` 에서
  **등록 트랜잭션 안**에 불린다. 새 이벤트를 낼 자리로 그대로 쓸 수 있다.

⟹ **배관은 대부분 서 있다.** ⓑ·ⓒ 어느 쪽이든 새로 짓는 것은 ① 이벤트 종류 1개(＋마이그레이션 1 —
`0009` 가 CHECK 7→10 을 한 선례가 있다) ② 페이로드 빌더 1개 ③ 수신 측 집행 분기 1개 다.
막는 것은 배관이 아니라 **`datasetId` 를 실을 수 없다는 봉투 조항**이다.

⛔ 배포 현실 — `events` 볼륨이 `volume-init` 의 `chown 10001` 목록에서 빠져 `/srv/viz-events` 가
`root:root` 이고 두 단위(uid 10001) 모두 쓰기 거부다(`infra/staging/compose.i2.yml:149` 대상 목록 ·
`03-HANDOFF.md §4 #59`). **지금 이 버스는 배포에서 물리적으로 못 쓴다.** ⓑ·ⓒ 둘 다 이 한 줄이 선행이다.

## 4. 재굽기 비용 — 실측

| 값 | 수 | 근거 |
|---|---|---|
| COG 변환 (장당) | **0.07 ~ 2.2 초** | `dev-package/DATA-PIPELINE-MEASUREMENT.md:58`(§5.8) |
| 타일 1장 서빙 | 4.1 ~ 72.0 ms | 같은 줄 |
| 타일 피라미드 전량 사전 생성 | tif 1장 **61.3 초**·28.0 MB · 167장 직렬 9.4분(계산) | `DATA-PIPELINE-MEASUREMENT.md:59` — **채택하지 않은 방식이다**(「전량 굽지 않는다」) |
| 미리보기 최초 표시 게이트 | 합격선 **p95 10초 · 상한 60초**, 실측 **p95 2.043~2.189초**(표본 25 · 5포맷) | `gates` `render-latency` · `sessions/P3-TILE-DEPLOY-20260831.md:71` · `P3-TILE-SURFACE-20260831.md:65` · `DEPLOY-269-20260901.md`(p95 2.118초) |
| 격자 전체 계산 | tif 기준 1.8초 · 204 MB | `DATA-PIPELINE-MEASUREMENT.md:52` |
| 등록 전환 1건당 재굽기 총시간 | **[미측정]** — 위 장당 값 × 데이터셋 파일 수. 데이터셋당 파일 수 분포는 이 회차에 세지 않았다 |

⟹ 재굽기는 **초 단위**이고 게이트 합격선(10초/60초)의 안쪽이다. 「9.4분」은 다른 방식(피라미드 전량)의 수라
이 판단에 인용하면 틀린다.

## 5. 이미 있는 멱등·중복 제거 장치 (셋 다 재사용 가능)

1. **내용 주소 키** — 같은 입력이면 같은 키. 무효화가 규율이 아니라 키 자신의 일
   (`layout.json` `why.미리보기 산출물` ① · `cache.py:28` · `storage_layout.py:146`).
2. **outbox 멱등 키** `<타입>:<uploadId>` ＋ `ON CONFLICT DO NOTHING`(`d5_ingestion.py:112-120`,`:155`).
3. **재전달 봉투** `Delivery`(attempt·maxAttempts·redelivery) ＋ D7 `SpoolTriggerPort.ack`
   (`trigger_bus.py:106`) — 「이미 처리한 키면 페이로드를 보지 않고 버린다」(envelope `IdempotencyKey`).
4. **`_relocate` 자체가 멱등에 가깝다** — `storage_key == new_key` 면 건너뛰고, 원본이 없으면 원장만
   새 자리를 적어 두 자리를 만들지 않는다(`ingestion.py:143-150`).
5. **`invalidation.apply()` 단일 집행문** — 지우는 문을 늘리지 않는다는 A-1 완료 정의 ⑶.

## 6. 선택지 셋

### ⓐ core-api 에 미리보기 볼륨을 붙여 옮긴다

- **무엇** — `infra/staging/compose.i2.yml` core-api 블록에 `previews:/srv/viz-previews`(rw) 추가 ＋
  `routes/ingestion.py` 의 `_relocate` 뒤에 산출물 이동 코드 ＋ core-api 쪽 `storage_layout` 소비 확대.
- **작업량** — compose 1 · core-api 코드 1~2 · 시험 2~3. **가장 적다.**
- **깨지는 것** — ⑴ core-api 가 D7 산출물 배치를 알게 되어 두 자리에서 배치를 정하게 된다.
  ⑵ 이동이 **DB 트랜잭션 밖**이라 등록 롤백 시 산출물만 옮겨진 상태가 남는다(`_relocate` 주석이
  바이트에 대해 경계한 그 실패형이 산출물 쪽에 재현된다). ⑶ 볼륨 소유권 — `previews` 는 uid 10001
  기준으로 `chown` 돼 있고(`compose.i2.yml:149`) core-api 도 같은 uid 이나 rw 붙임은 백업·회수
  범위(A-1 ⑸ 스냅숏 등급)의 쓰는 주체를 하나 늘린다.
- **되돌리기** — 쉽다. compose 1줄 · 코드 revert. 옮겨진 파일은 백업 대상(`previews` 는 백업에 있다).
- **위반** — `CLAUDE.md:59` §3-1(도메인 경계 · cross-domain 은 Port 경유) ＋ `CLAUDE.md:90-94`
  (경계를 넘어야 하면 멈추고 보고). `03-HANDOFF.md` #56 행이 이미 「경계를 넘는다」로 못 박았다.

### ⓑ 등록 사건을 D5·D7 이 받아 옮긴다

- **무엇** — `contracts/events/envelope.json` `EventType` 10 → 11(가칭 `upload.registered`) ＋
  `core-pipeline.json` 페이로드 스키마 1 ＋ 마이그레이션 1(CHECK 확장 · `0009` 선례) ＋
  core-api 발행(`d5_ingestion.py` 에 `publish_registered`, 후크는 `mark_registered` 자리) ＋
  D5 또는 D7 수신 집행(파일 이동) ＋ 게이트 `event-lint`·`contract-breaking` 재통과.
- **작업량** — 계약 2 · 생성물 3(세 단위 동일본 재생성) · 마이그레이션 1 · 코드 3~4 · 시험 5~6.
  **가장 많다.** ＋ **동결 해제 1회**(등급은 마이그레이션 ≥ 1 이므로 ㉯ = Ted 승인 필수 —
  `X2-FREEZE-PROTOCOL §5`, `#53` 선례).
- **깨지는 것** — ⑴ **페이로드에 `datasetId` 가 필요한데 봉투가 금지한다**(§2 축자). 우회하려면
  「`uploadId` 만 싣고 받는 쪽이 datasetId 를 알아낸다」인데, D7 은 원장을 못 읽는다(불변규칙 1 ·
  `source.py` 가 디렉터리를 사실로 쓰는 이유). ⟹ **계약 조항 자체의 개정이 따라붙는다.**
  ⑵ `events` spool 이 배포에서 쓰기 거부다(`#59`) — 고치기 전에는 「배선은 있는데 아무 일도 안 난다」.
  ⑶ 비동기라 등록 직후 지도를 열면 이동 전 상태를 본다(빈 지도의 시간 창).
- **되돌리기** — 계약·마이그레이션이 걸려 있어 **가장 어렵다**. 종류 추가는 순수 가산이라 되돌릴 수
  있으나(`0009` 가 그렇게 했다) 되돌림도 마이그레이션 1회다.
- **위반** — 직접 위반 0. 단 `envelope.json` 의 페이로드 경계 조항을 **개정해야** 성립한다.

### ⓒ 옮기지 않고 다시 굽는다

- **무엇** — 등록 시점에 재굽기 트리거 1개(발신은 core-api `mark_registered` 자리 또는 D5)
  ＋ D5 `run_file` 을 `targetId = datasetId` 로 한 번 더 돌린다(`pipeline.py:120` `previews_root` 인자
  이미 있음) ＋ 옛 `uploadId` 자리 산출물은 A-1 의 회수 등급(고아)으로 넘긴다.
- **작업량** — 이벤트 종류 1(ⓑ 와 같은 계약 비용) 또는 core-api → D5 직접 호출 1 · 코드 2~3 · 시험 3~4.
  **중간.** ⚠ 「트리거를 새로 세운다」는 곧 ⓑ 와 같은 계약 표면을 건드린다 — 이 비용을 0 으로 세면 틀린다.
- **깨지는 것** — ⑴ **같은 그림을 두 번 굽는다**(장당 0.07~2.2초 · §4). 게이트 합격선 안쪽이지만
  대상 간 재사용은 이미 A-1 ⑺ 이 **의도된 손실**로 못 박았다(상한 316,201 B · 등록 대기분까지 632,402 B).
  ⑵ 재굽기가 끝나기 전 지도를 열면 빈 지도 — ⓑ 와 같은 시간 창. ⑶ 원본을 다시 읽으므로 등록 직후
  `_relocate` 와의 순서가 어긋나면 원본을 못 찾는다(`_relocate` 는 트랜잭션 마지막 단계다 ·
  `ingestion.py:551`) — 트리거는 반드시 그 뒤여야 한다.
- **되돌리기** — **가장 쉽다.** 산출물은 다시 만들 수 있는 부산물이고(`invalidation.py` 머리말 ·
  `〈247〉`), 트리거를 끄면 원상 복귀다. 마이그레이션은 이벤트 종류를 더할 때만 1건.
- **위반** — 직접 위반 0. `〈247〉`(자동 재생성은 렌더 산출물 한정)의 **범위 안**이다 — 원본·격자·데이터셋을
  다시 만들지 않는다. 다만 「자동 재생성 목록을 넓히는 것은 별도 판정」이라는 주석이 걸린다
  (`invalidation.py:36-40` TRIGGERS 위 ⚠).

## 7. 셋의 대조

| | ⓐ 볼륨 마운트 | ⓑ 이벤트로 이동 | ⓒ 재굽기 |
|---|---|---|---|
| 파일 수 | 3~5 | 12~15 | 6~9 |
| 계약 개정 | 0 | **2 ＋ 마이그레이션 1 ＋ 동결 해제 ㉯** | 1 ＋ 마이그레이션 1(＋동결 해제 ㉯) |
| 경계 위반 | **있다**(`CLAUDE.md:59`) | 없다(단 봉투 조항 개정 필요) | 없다 |
| 실패형 | 산출물만 옮겨진 반쪽 상태 | 「배선은 있는데 아무 일도 안 난다」(`#59`) | 빈 지도의 시간 창 · 중복 연산 |
| 되돌리기 | 쉽다 | 어렵다 | **가장 쉽다** |
| 비용의 수 | 0 | 0 | **0.07~2.2초/장** (합격선 p95 10초) |

## 8. 관측 하나 — 넷째 안이 성립할 수 있다

안 ⑴ 이 자리에 `targetId` 를 넣는 이유는 소유 판정(A-1 ⑴)이고, 그 판정은 **경로가 아니라 사이드카**로도
설 수 있다 — A-1 완료 정의 ⑹ 이 「사이드카를 전 층에 남긴다」를 이미 신설했고, 판정 불가 34 키의
유일한 원인이 사이드카 부재라고 실측이 적는다. 경로에 `targetId` 를 넣지 않으면 **#56 자체가 생기지 않는다**
(§1-a — 오늘 배선에서는 옮길 것이 없다). 이 선택지는 A-1 안 판정(Ted 2026-09-01 ③)을 다시 여는 것이므로
여기서 권고하지 않고 **사실만 적는다**.
