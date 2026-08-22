# WU-D2 세션 기록 — ④ async 봉투: `contracts/events/`

> **범위** `contracts/events/envelope.json` · `contracts/events/core-pipeline.json` · `contracts/events/README.md` 뿐. `seams/`·`schemas/`·`gates/`·`03-HANDOFF`·`PLAN-SoT`·`WORK-UNITS` 는 이 조각에서 건드리지 않았다.
> **근거 규칙** `CLAUDE.md §3-1`(도메인은 자기 테이블 + D1 만) · `§3-5`(연구실 경계) · `§3-6`(정규 ID 는 common.json) · `PLAN-SoT §9-⑳`(파생값 2종 미저장·미전달) · `contracts/README.md`(이벤트 = JSON-Schema 봉투 + 멱등 키 + DLQ 재처리 규칙) · `contracts/events/README.md`(v1 워커 트랜잭션 부재 → 고아 산출물·조용한 데드락) · `DOMAINS §2 D5`·`§4`(pipeline-worker 만 워크로드가 다르다).
> **정본 근거** `PRD_업로드와_계보_확정` v1.2 · `Policy_업로드와_계보_확정` v2.2 (E-04) · `DataModel_공통_기반` v1.8 (E-00).
> **검증** `json.load` 3파일 green · `ajv-cli@5 compile --spec=draft2020` 두 파일 모두 `is valid` · 인스턴스 검증 green 2건 / red 5건(아래 §6) · `./gates/run.sh contract-lint` **green**(seam 3건, 위반 0) · `./gates/run.sh planning-freshness` **green**(임베드 15건 일치).

---

## 1. 판단 ① — 봉투 형식과 멱등·재시도 표현

봉투는 `envelope.json#/$defs/Envelope` 하나이고 **필수 11필드**다.

| 필드 | 타입 | 왜 봉투인가 |
|---|---|---|
| `eventId` | `common.json Ulid` | **전달의 정체성.** outbox 행 1개 = 1개이며 재전달에서 바뀌지 않는다 |
| `type` | `EventType` (7값) | 라우팅 키 |
| `schemaVersion` | `주.부` | **타입마다** 매긴다. 한 단계가 바뀌었다고 나머지 여섯의 버전을 올릴 이유가 없다 |
| `source` | `core-api` \| `pipeline-worker` | 이 seam 이 한 방향이 아님을 봉투가 말한다 |
| `occurredAt` | `common.json Timestamp` | **사실이 일어난 시각.** 재전달에서 불변 |
| `labId` | `Ulid` | 아래 §5 |
| `actorAccountId` | `Ulid` | 올린 사람(D1 shared kernel) |
| `uploadId` | `Ulid` | 이 seam 의 집계 루트. 7종 전부가 여기 매달린다 |
| `idempotencyKey` | 패턴 문자열 | 아래 |
| `delivery` | 객체 5필드 | 아래 |
| `payload` | 객체 | 타입별 |

`additionalProperties: false` 다 — 봉투에 필드를 몰래 늘리는 경로를 막는다.

### 멱등키와 재시도 — **키 하나가 아니라 둘이고, 역할이 다르다**

같은 이벤트가 두 번 오는 경로가 **두 가지**이고 하나의 키로는 둘 다 못 막는다.

| 경로 | 무슨 일 | 무엇이 막나 |
|---|---|---|
| 브로커 재전달 (at-least-once) | 같은 outbox 행이 다시 배달된다. `eventId` 는 **같다** | `eventId` 중복 제거 |
| outbox 재생성 (워커 재기동·재적재·DLQ 되돌리기) | 같은 사실에 대해 **새 행**이 생긴다. `eventId` 가 **다르다** | `idempotencyKey` |

- **`idempotencyKey` = `<이벤트 타입>:<uploadId>`** — 결정론적이다. 발행자가 난수를 쓰지 않으므로 outbox 가 다시 만들어져도 같은 키가 나온다. 소비자는 이 키로 잠그고, 이미 처리한 키면 페이로드를 보지 않고 버린다. 패턴으로 강제한다: `^[a-z][a-z0-9-]*\.[a-z][a-z0-9-]*:[0-9A-HJKMNP-TV-Z]{26}$`.
- `eventId` 만 뒀다면 outbox 재생성에서 중복 제거가 뚫리고, `idempotencyKey` 만 뒀다면 같은 사실의 재전달 두 건을 로그에서 구분할 수 없다. **둘 다 있어야 v1 의 고아 산출물이 재현되지 않는다.**

### `delivery` — 재시도 판단에 쓰는 값을 전부 봉투에 싣는다

`attempt` · `maxAttempts`(기본 **5**, **정본에 항목 없음 — 레포 결정**) · `firstPublishedAt`(불변) · `publishedAt`(전달마다 바뀜) · `redelivery` · `deadLettered`(선택).

- `maxAttempts` 를 **계약에 두는** 이유: 생산자와 소비자가 서로 다른 상한을 갖는 순간 큐가 조용히 무한 재시도로 돈다. v1 의 "조용한 데드락"이 정확히 이 모양이다.
- `occurredAt` / `firstPublishedAt` / `publishedAt` 셋을 나눈 이유: 하나로 합치면 **늦게 도착한 것**과 **늦게 일어난 것**이 구분되지 않는다.
- `deadLettered` 는 사람이 DLQ 에서 꺼내 넣은 전달과 자동 재시도를 구분한다.

---

## 2. 판단 ② — 스키마 언어: **JSON Schema 2020-12** (AsyncAPI 를 버렸다)

| # | 근거 |
|---|---|
| 1 | **`contracts/README.md` 가 이미 못 박았다** — "이벤트(async) … JSON-Schema 봉투 + 멱등 키 + DLQ 재처리 규칙". 계약 권위체가 정한 형식을 이 조각이 바꾸면 `README` 를 같이 고쳐야 하고, 그건 이 조각의 범위가 아니다 |
| 2 | **`common.json` 재사용이 무손실이다.** `common.json` 은 2020-12 이고, `$id` 가 절대 URI 라 `../schemas/common.json#/$defs/Ulid` 가 그대로 해석된다(§6 에서 실측). AsyncAPI 2.x 는 자체 스키마 방언(Draft-07 서브셋)이라 `Ulid` 의 `pattern`·`ProcessingLevel` 의 `readOnly` 같은 것이 왕복에서 상한다 — **`CLAUDE.md §3-6` 이 금지하는 "정의를 두 곳에 두기"가 도구 때문에 생긴다** |
| 3 | **AsyncAPI 는 지금 없는 결정을 강제한다.** 채널·서버·프로토콜 바인딩(SQS? SNS? Postgres LISTEN?)을 적어야 문서가 성립하는데, 브로커 선택은 인프라 WU(I1·I2)의 것이고 아직 없다. **미확정 인프라를 계약에 박으면 계약이 틀린 채 동결된다** |
| 4 | **검증 도구가 하나로 끝난다.** ajv 하나로 ① 스키마 자체 유효성 ② 실제 메시지 인스턴스 검증 둘 다 된다. AsyncAPI 는 `@asyncapi/parser` 를 더 얹어야 하고, 그 도구는 페이로드 인스턴스를 검사해 주지 않는다 |
| 5 | **생성물(`contracts/codegen/`)이 바로 나온다.** `json-schema-to-typescript`·`datamodel-code-generator` 가 2020-12 를 직접 먹는다 (`contracts/README.md` 규칙 3·4) |

**대가(알고 받는다)** — 채널·토픽 이름과 구독 관계가 계약에 안 적힌다. 지금은 `source` 필드와 각 이벤트의 "발행/소비" 서술이 그 자리를 메운다. 브로커가 정해지는 WU 에서 채널 지도가 필요해지면 그때 **AsyncAPI 를 얹되 페이로드는 이 파일들을 `$ref`** 하면 된다 — 지금 결정이 그 길을 막지 않는다.

---

## 3. 판단 ③ — 이벤트 7종과 정본 근거

파이프라인은 `upload.accepted → file.format-detected → file.header-parsed → file.crs-normalized → preview.cog-built → upload.ready` 이고, 어느 단계에서든 갈라져 나오는 `upload.failed` 하나가 붙는다.

| # | `type` | 무엇을 | 근거 |
|---|---|---|---|
| ① | `upload.accepted` | 파일 묶음 접수(본체 N + 기준 격자 0~1) | **정본** `Policy §2` 규칙 맵(파일을 끌어다 놓는다 → 업로드하고 헤더를 읽는다) · `§8 파일 놓기`(여러 개를 한 번에) · `PRD §5.1 여러 파일 받기` · `DataModel §4.3` / **레포** `DOMAINS §2 D5`(presigned multipart) |
| ② | `file.format-detected` | 포맷 · 그릴 수 있는가 · 조각 포맷 일치 여부 | **정본** `Policy §5` 입력값 규칙(형식 제한 없음, **헤더 인식만 형식별**) · `§9 그릴 수 없는 형식` · `DataModel §4.3`(조각은 포맷이 같아야 한다) |
| ③ | `file.header-parsed` | 변수 · 기간(합집합) · 좌표계 · 격자 · 용량(합계) · 못 읽은 조각 · 원천 표기 후보 | **정본** `PRD §5.1 자동 메타데이터 확인` · `PRD §6`(자동으로 읽을 수 있는 것은 다시 묻지 않는다) · `Policy §8 자동 메타 칸` · `§9 헤더 인식 실패`·`조각 일부를 못 읽음` · `§5`(원천 표기 기본값 = 헤더에서 추출) · `DataModel §4.1·§4.3` |
| ④ | `file.crs-normalized` | 원본 좌표계 → 목표 좌표계 정규화 | **정본 직접 근거 없음.** `DOMAINS §2 D5`(D5 소유물 = 좌표계 변환)가 근거다. 정본은 좌표계를 *읽는* 데까지만 말한다(`Policy §8`) |
| ⑤ | `preview.cog-built` | 미리보기용 파생물 준비 완료 | **정본 직접 근거 없음(`COG` 라는 말이 정본에 없다).** `DOMAINS §2 D5`(COG)가 근거이고, 정본 쪽 간접 근거는 `Policy §8 미리보기 그리기`(**서버가 그린다** · GB 급이라 브라우저가 못 한다) |
| ⑥ | `upload.ready` | 등록 결정 게이트를 열 수 있는 상태 | **정본** `Policy §7.1`(열어보는 중 — **저장 안 됨**) · `§8 등록 결정 게이트`("보기만 할게요" / "연구실에 등록") · `§8.1 휘발 고지`(수명) |
| ⑦ | `upload.failed` | 파이프라인이 끝난 실패 | **정본** `Policy §9 오류와 예외` 표 전체 |

### 순서 판단 — **포맷 감지가 헤더 파싱보다 앞이다**

작업 지시의 나열 순서는 "헤더 파싱 → 포맷 감지"였지만 뒤집었다. 정본 `Policy §5` 가 **"형식 제한 없음, 헤더 인식만 형식별"** 이라고 적었다 — 어느 파서를 쓸지 정하려면 포맷이 먼저 정해져야 한다. 반대로 두면 ③이 ②의 결과를 미리 안다는 뜻이 되어 두 단계가 하나로 뭉개진다.

### 실패 이벤트를 **단계마다 두지 않았다**

일곱 갈래 실패 이벤트를 두면 소비자가 일곱 갈래로 분기하고, 단계가 하나 늘 때마다 소비자를 고쳐야 한다. 어디서 멈췄는지는 `failure.failedAt`(= `EventType`)이 말한다.

### 만들지 **않은** 것과 이유

| 없는 것 | 이유 |
|---|---|
| 이어올리기(resume)·파트 단위 상태 | 정본 `Policy §9` 가 `[가정] 이어올리기는 이번 범위 밖`, `§11` 이 대용량 업로드를 미결로 남겼다. 계약이 없는 기능을 약속하게 된다 |
| 데이터셋 생성·계보 확정 이벤트 | 사람이 `데이터셋 만들기`를 눌러야 생기는 **동기** 행위이고(`Policy §7.2`) D3·D4 의 것이다 |
| AI 계보 제안 이벤트 | `core-ai` seam(D10)이고 이 파이프라인을 타지 않는다. `CLAUDE.md §3-2` |
| 포맷 enum · 그릴 수 있는 포맷 목록 | 정본이 `등`으로 열어 뒀고(`Policy §5`), `§11` 이 미리보기 지원 범위를 미결로 남겼다. 여기서 닫으면 **정본에 없는 어휘를 계약이 만든다**(`sessions/D2.md §3-1` 과 같은 판단) |
| 좌표계·격자 enum | 좌표계 어휘는 **D9(Ontology)가 소유하는 수문학 도메인 사실**이다 (`DOMAINS §2 D9` · `§6`— D5 도메인 소유자 HYD). 플랫폼이 여기서 값 집합을 만들면 도메인 소유자 판단을 개발자가 대신한다 |
| `targetCrs` 상수 | 지도 타일이 무엇을 쓰는지는 viz-render 의 판단이다 (`CLAUDE.md §3-4`) |

---

## 4. 판단 ④ — 실패 표현: 두 갈래 + 정본 §9 대응 사유

```
Failure = { failedAt(EventType) · class · reason · willRetry · detail? }
FailureClass = 재시도 가능 | 영구
```

- **`class`** 로 갈랐다. 영구 실패를 재시도 큐에 넣으면 상한만큼 헛돌다 DLQ 로 가고, 재시도 가능 실패를 영구로 처리하면 정본이 사용자에게 말하기로 한 **"올리다가 끊겼어요. 다시 시도해 주세요."**(`Policy §9 업로드 중단`)의 근거가 사라진다.
- **`willRetry`** 는 결론을 실어 준다 — `class` 가 `영구` 면 항상 false, `재시도 가능` 이어도 `delivery.attempt` 가 상한에 닿았으면 false. **소비자가 상한 산술을 다시 하지 않는다.**
- **`reason` 은 정본 `Policy §9` 표의 행에 1:1 대응**한다: `업로드 중단`·`형식 인식 실패`·`헤더 인식 실패`·`조각이 서로 다름`·`좌표계 변환 실패`·`미리보기 준비 실패`·`시간 초과`·`내부 오류`(어디에도 없는 것을 모으는 자리).
- **사용자 문구를 이벤트에 싣지 않았다.** 정본 §9 가 문구를 소유하고 화면이 그린다. 봉투가 문구를 나르면 같은 문장이 정본·이벤트·화면 세 곳에 생기고 갈라진다 — `sessions/D2.md §1` 이 매핑 테이블을 거부한 것과 같은 논리. `detail` 은 운영·로그용이며 그렇게 명시했다.

### 정본이 **막지 말라고 한 것은 실패 이벤트가 아니다** (이 조각의 가장 중요한 판단)

정본 `Policy §9` 는 네 가지를 **"등록은 막지 않는다"** 로 뒀다 — 헤더 인식 실패 · 조각 일부 못 읽음 · 기준 격자 파일 없음 · 그릴 수 없는 형식. 그래서 이 넷은 **성공 이벤트가 사실을 싣고 지나간다**:

| 정본이 연 경로 | 계약의 표현 |
|---|---|
| "파일에서 정보를 읽지 못했어요 … 등록은 막지 않는다" | `file.header-parsed` 가 나가고 못 읽은 값이 `null` 이다. **빈 배열이 아니라 `null`** — 빈 배열은 "변수가 없다"는 사실이고 `null` 은 "못 읽었다"이며, 화면이 자동 칸을 입력 칸으로 바꿀지가 여기서 갈린다 |
| "조각 72개 중 3개를 읽지 못했어요" + 이름으로 밝힌다 | `unreadableFiles[]` 에 `fileId` + **`fileName`** 을 같이 싣는다 |
| "그릴 수 없는 형식 … 등록·계보 확정·다운로드 전부" 된다 | `file.format-detected.renderable: false` 로 나가고 파이프라인은 계속 간다 |
| "짝 파일 없이 그려 보기" | `preview.cog-built.referenceGridAvailable` |

**못 읽음을 실패 이벤트로 만들면 정본이 열어 둔 경로가 계약에서 막힌다.** `upload.failed` 에 오는 것은 파이프라인이 실제로 끝난 경우뿐이다.

---

## 5. 판단 ⑤ — 경계

| 규칙 | 어떻게 지켰나 |
|---|---|
| `CLAUDE.md §3-1` **타 도메인 테이블 직접 참조 금지** | 페이로드·봉투가 싣는 식별자는 **D5 소유(`uploadId`·`fileId`)** 와 **D1 shared kernel(`labId`·`actorAccountId`)** 뿐이다. `datasetId`·`projectId`·계보 관계 ID 가 **한 건도 없다.** 등록 전에는 데이터셋이 존재하지 않고(`Policy §7.1` — 열어보는 중은 저장 안 됨), 생긴 뒤에는 D3 의 것이다. `uploadId` 는 `core-viz` seam 의 `RenderTarget.uploadId` 가 이미 쓰는 어휘라 새로 만든 것이 아니다 |
| `PLAN-SoT §9-⑳` **파생값 2종 미전달** | `processingLevel`·`lineageState` 필드가 두 파일 어디에도 없다. `additionalProperties: false` 라 나중에 몰래 붙는 것도 막힌다(§6 red 검증). Lv 는 **계보가 확정될 때** 계산되는 값이고 계보는 사람이 확인해야 생기므로, 업로드 파이프라인이 알 수 있는 값이 애초에 아니다 |
| `CLAUDE.md §3-5` **연구실 경계** | `labId` 를 봉투 필수로 뒀다. 동기 seam 은 서버가 인증 주체에서 주입하지만(`fe-core.yaml` 에 `labId` 쿼리가 없는 이유) **큐에서 꺼낸 메시지에는 주체가 없다.** 소비자는 이 값으로 스코프를 세운다 |
| `CLAUDE.md §3-2` **D10 → D4 쓰기 경로 없음** | 이 파이프라인에 AI 가 등장하지 않는다. 계보 관련 필드가 0건이다 |
| `CLAUDE.md §3-6` **정규 타입 1곳** | ID·시각·파일 종류는 전부 `../schemas/common.json` `$ref`. 참조한 정의 **3종** — `Ulid`·`Timestamp`·`FileKind`. enum·ID 인라인 재선언 0건 |
| `CLAUDE.md §3-4` **core 에 geo 없음** | 좌표·격자 값이 봉투를 지나가지만 **해석되지 않는다** — 문자열이고, 그리는 일은 `core-viz` seam 이 한다 |

**표기** — 속성 이름은 lowerCamelCase(세 seam 과 동일), `type` 값은 ASCII 점 표기(**라우팅 키라서** — `fe-core.yaml` 이 경로에 한국어를 싣지 않는 것과 같은 이유, 토픽 이름에 퍼센트 인코딩이 붙는다), **도메인 값 집합인 `FailureClass`·`FailureReason` 은 정본 한국어 표기**(`common.json` 표기 규칙).

---

## 6. 검증 실측

```
python3 -c "import json; json.load(...)"                         → 3파일 green
ajv-cli@5 compile --spec=draft2020 -s envelope.json              → is valid
ajv-cli@5 compile --spec=draft2020 -s core-pipeline.json         → is valid
ajv validate --spec=draft2020 -c ajv-formats \
  -r ../schemas/common.json -r envelope.json -r core-pipeline.json \
  -s <AnyEvent 진입 스키마> -d <픽스처>
```

`common.json` `$ref` **가 실제로 해석되는지**를 인스턴스로 확인했다 — `labId` 에 26자 아닌 값을 넣으면 `schemaPath: '../schemas/common.json#/$defs/Ulid/minLength'` 로 걸린다. 스키마가 컴파일된 것만으로는 `$ref` 해석을 증명하지 못하므로 red 픽스처까지 돌렸다.

| 픽스처 | 기대 | 결과 |
|---|---|---|
| `ok` — `file.header-parsed` 정상 | valid | ✅ |
| `ok-partial` — `crs: null` + 못 읽은 조각 1건 (정본이 연 경로) | valid | ✅ |
| `red-derived` — `payload.processingLevel: 2` (**파생값 전달**) | invalid | ✅ 거부 |
| `red-crossdomain` — 봉투에 `datasetId` (**타 도메인 참조**) | invalid | ✅ 거부 |
| `red-idemkey` — `idempotencyKey: "random-uuid-1234"` | invalid | ✅ 패턴 위반 |
| `red-typemismatch` — `type` 을 `upload.ready` 로 바꿔 페이로드와 어긋냄 | invalid | ✅ 거부 |
| `red-ulid` — `labId: "not-a-ulid"` (**common.json `$ref` 해석 증명**) | invalid | ✅ `Ulid/minLength` |

게이트 — `./gates/run.sh contract-lint` **green**(seam 3건, 위반 0) · `./gates/run.sh planning-freshness` **green**(임베드 15건 일치). 둘 다 이 조각 전후로 변화 없다.

---

## 7. 한계 — **게이트가 이 파일들을 검사하지 않는다**

`gates/tools/contract-lint.sh` 는 `COLAB_SEAM_DIR`(기본 `contracts/seams`)만 `find` 한다. 실행 로그가 그것을 그대로 말한다:

```
# 대상 3건 — contracts/seams/core-ai.yaml contracts/seams/core-viz.yaml contracts/seams/fe-core.yaml
```

**`contracts/events/*.json` 은 대상 0건이다.** 이 조각의 검증은 전부 손으로 돌린 ajv 이고, **CI 가 지키는 것이 아니다.** 뒤따르는 결과:

1. `events/` 가 깨진 JSON 이 되어도, `common.json` `$ref` 가 끊겨도 게이트는 green 이다.
2. `contract-breaking`(oasdiff)도 OpenAPI 전용이라 **이벤트의 파괴적 변경(필수 필드 추가·enum 값 제거)을 아무도 못 잡는다.**
3. `contracts/README.md` 가 이벤트에 요구한 **"하위호환 소비자 테스트"**가 아직 없다.
4. `contract-lint.sh` 는 대상 0건을 red 로 세지만 그건 **seam 디렉터리** 기준이므로, 이 사각지대는 green-by-skip 이 아니라 **아예 검사 범위 밖**이다. 조용해서 더 위험하다.

**게이트를 고치지 않았다 — 범위 밖이다**(`gates/` 수정 금지). 닫는 방법은 새 WU 로 만들어야 한다. 필요한 것은 셋이다.

| 필요한 것 | 형태 |
|---|---|
| `event-lint` 게이트 | `contracts/events/**` 를 ajv 로 컴파일(`--spec=draft2020 -c ajv-formats`, `-r contracts/schemas/common.json`). 대상 0건·도구 부재는 red |
| red fixture selftest | `contract-selftest.sh` 와 같은 방식 — 위 §6 의 red 5건을 고정 픽스처로 두고 **게이트가 fail-closed 임을 증명** |
| 이벤트 파괴적 변경 검출 | oasdiff 가 못 한다. `$defs` 단위 diff 규칙(필수 필드 추가 · enum 값 제거 · `additionalProperties` 조임)을 직접 써야 한다 |

> **이것은 "나중에"가 아니라 차단 해제 WU 다** (`CLAUDE.md §5`). 이 세 가지가 서기 전까지 `contracts/events/` 는 **손으로 검증하는 계약**이며, 그 사실을 모른 채 D2 를 "게이트 green 이니 끝"으로 읽으면 v1 이 RLS 테스트를 green-by-skip 했던 자리와 같은 자리에 서게 된다.

---

## 8. 다음 조각의 진입조건

- `contracts/codegen/` 는 `events/` 두 파일도 생성 대상에 넣어야 한다 (`contracts/README.md` 규칙 3·4). 지금 생성물이 없다.
- `uploadId` 의 **수명**(`UploadReadyPayload.expiresAt` 의 실제 값)은 **정본에 없다 — 레포 결정이며 아직 정하지 않았다.** 정본이 준 것은 `이 화면을 벗어나면 사라진다`(`Policy §4·§8.1`)라는 사실뿐이다. 보관 시간을 정하는 자리는 D5 구현 WU 다.
- 브로커(SQS·SNS·Postgres outbox)가 정해지면 채널 지도가 필요해진다. 그때 AsyncAPI 를 **얹되** 페이로드는 이 파일들을 `$ref` 한다 — 정의를 두 곳에 두지 않는다 (§2).
- `maxAttempts: 5` 는 레포 결정이다. 실제 재시도 정책(백오프 곡선·DLQ 알림)은 인프라 WU 에서 정해지며, **값이 바뀌면 계약이 먼저 바뀐다.**
