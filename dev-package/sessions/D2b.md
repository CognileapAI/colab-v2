# D2b — 이벤트 계약 게이트 (`event-lint` · `event-breaking`)

D2b 의 완료 판정은 **「게이트 self-test green + 이벤트 계약 변경이 실제로 red 를 냄」**(`WORK-UNITS.md §6`)이다.

이 세션이 닫은 것은 `sessions/D2-events.md §7` 이 스스로 적어 둔 구멍이다 —
`contract-lint`(spectral)는 `COLAB_SEAM_DIR`(기본 `contracts/seams`)만 훑고,
`contract-breaking`(oasdiff)은 OpenAPI 전용이다. 그래서 **`contracts/events/**` 는 어떤 게이트도 보지 않았다.**
green-by-skip 보다 나쁘다. green-by-skip 은 최소한 대상이 0건이라는 사실이라도 남기지만,
이 사각지대는 **아예 검사 범위 밖**이라 로그에 아무 흔적이 없다.

`contracts/**` 에는 한 글자도 쓰지 않았다. red 케이스는 전부 임시 디렉터리 픽스처다
(§4 의 실증만 예외적으로 실제 파일을 잠깐 고쳤다가 되돌렸고, `git status` 로 무변경을 확인했다).

---

## 1. 만든 것

| 파일 | 역할 |
|---|---|
| `gates/tools/event-lint.sh` | `event-lint` 실행기 — 도구 확보 · 대상 수집 · 0건 판정 |
| `gates/tools/event_lint.mjs` | 검사 엔진 (ajv). 스키마 컴파일 + 인스턴스 픽스처 검증을 **한 프로세스**에서 |
| `gates/tools/event-breaking.sh` | `event-breaking` 실행기 — 기준(git HEAD) 판 추출 · 0건 판정 |
| `gates/tools/event_breaking.py` | `$defs` 단위 파괴적 변경 판정 엔진 (파이썬 표준 라이브러리만) |
| `gates/tools/event-selftest.sh` | 위 두 게이트의 fail-closed 증명 — **33 케이스** |
| `gates/tools/node/package.json` · `package-lock.json` · `.gitignore` | 도구 버전 고정 (`ajv` 8.17.1 · `ajv-formats` 3.0.1) |
| `gates/fixtures/events/entry.schema.json` | 인스턴스 검증 진입 스키마 — `core-pipeline.json#/$defs/AnyEvent` 를 `$ref` |
| `gates/fixtures/events/valid/*.json` (5건) | 계약을 지킨 인스턴스 |
| `gates/fixtures/events/invalid/*.json` (8건) | 계약이 **거부해야 하는** 인스턴스 |
| `gates/run.sh` | `event-lint` · `event-breaking` · `event-selftest` 배선 + `selftest` 묶음에 편입 |
| `.github/workflows/ci.yml` | `contract-gates` 잡에 두 스텝 추가 (`gate-selftest` 잡은 `selftest` 를 부르므로 자동 포함) |
| `gates/README.md` | 게이트 표 · selftest 케이스 수 갱신 |

### 왜 도구 핀을 `gates/tools/node` 에 두는가

`contracts/package.json` 은 **계약 동결분**이다. 게이트가 자기 도구를 거기에 얹으면
"계약 변경"과 "게이트 도구 변경"이 같은 파일의 diff 로 섞인다. 게이트의 도구는 게이트가 고정한다.
`spectral 6.16.3` · oasdiff 다이제스트 고정과 같은 규율로 `ajv` 도 **정확한 버전**을 박았다.
떠다니는 ajv 는 조용히 바뀌는 게이트이고, 조용히 바뀌는 게이트는 게이트가 아니다.

### `event-lint` 이 두 겹인 이유

① **스키마 유효성** — `events/*.json` 이 그 자체로 유효한 JSON Schema 2020-12 인가 (ajv 컴파일, `strict: true`).
② **인스턴스 검증** — 고정 픽스처가 계약대로 통과·거부되는가.

②가 없으면 **"컴파일은 되는데 `../schemas/common.json` `$ref` 가 실제로는 안 풀리는"** 상태를 못 잡는다.
`D2-events.md §6` 이 손으로 확인했던 것이 정확히 이것이다 — `labId` 에 26자 아닌 값을 넣어야
`schemaPath: '.../Ulid/minLength'` 가 뜬다. 스키마가 컴파일된 것만으로는 `$ref` 해석의 증거가 되지 않는다.

**invalid 픽스처를 매 실행 돌리는 것**이 이 게이트의 핵심이다. valid 만 보는 게이트는 fail-open 이다 —
`additionalProperties: false` 가 통째로 사라져도 valid 픽스처는 여전히 통과한다.

`strict: true` 를 켜 둔 이유: 오탈자 키워드(`requred: [...]`)가 조용히 무시되면
**계약이 아무것도 강제하지 않는 채로 green** 이 된다. selftest ④가 이것을 증명한다.

---

## 2. 파괴적 변경의 정의 — 규칙표

> **판정 관점은 소비자(consumer)다.** 이벤트는 생산자가 밀고 소비자가 읽는 **단방향** 계약이라,
> "이미 배포된 소비자가 다음 메시지에서 깨지는가"가 기준이다. OpenAPI 의 요청/응답 양방향 감각을
> 그대로 옮기면 답이 달라지는 자리가 둘 있다 — `required` 제거(§E05)와 enum 값 추가(§W01)다.

규칙 코드는 `gates/tools/event_breaking.py` 의 `RULES` 표와 **같은 기호**를 쓴다. 코드와 문서가 갈라지면
규칙이 암묵이 되고, 규칙이 암묵인 게이트는 게이트가 아니다.

### 파괴다 (ERR — red)

| 코드 | 변경 | 왜 파괴인가 |
|---|---|---|
| **E01** | 이벤트 스키마 파일 제거 | 그 파일을 `$ref` 하던 소비자·생성물이 통째로 끊긴다 |
| **E02** | `$def` 제거·이름 변경 | 같은 이유. 이름 변경은 제거 + 추가로 보인다 — 리네임을 무해하게 세면 `AnyEvent` 한 종을 지우는 것과 구분되지 않는다 |
| **E03** | 속성 제거 | 소비자가 읽던 필드가 사라진다. `additionalProperties: false` 라 생산자가 계속 실어 보낼 수도 없다 |
| **E04** | `required` 에 속성 추가 | **이미 배포된 생산자**가 내는 메시지가 그날부터 전부 스키마 위반이 된다 |
| **E05** | `required` 에서 속성 제거 | 동기 API 라면 완화지만 **이벤트에서는 파괴다.** 소비자는 "항상 온다"를 전제로 분기해 두었고, 그 전제가 사라지면 `undefined` 를 만난다. 선택으로 낮추고 싶으면 소비자를 먼저 고치고 `schemaVersion` 주 버전을 올린다 |
| **E06** | enum 값 제거 | 큐에 **아직 남아 있는** 옛 메시지가 그 값을 담고 있다. at-least-once 재전달까지 있으므로 "다시 안 보낸다"는 보증이 되지 않는다 |
| **E07** | `type` 축소 (허용 타입 집합에서 값 제거, 또는 `type` 신설) | 예: `["string","null"]` → `"string"`. 정본이 열어 둔 **부분 성공(null)** 경로가 계약에서 막힌다 (`Policy §9`) |
| **E08** | `additionalProperties` 조임 (`true`/스키마 → `false`) | 생산자가 이미 싣고 있던 확장 필드가 위반이 된다 |
| **E09** | `const` 값 변경 | `type`·`source`·`schemaVersion` 의 `const` 는 **라우팅 키**다. 바뀌면 소비자 분기가 통째로 빗나가고, 아무도 처리하지 않는 메시지가 조용히 쌓인다 |
| **E10** | 값 제약 조임 — `min*` 증가 · `max*` 감소 · `pattern`/`multipleOf` 추가·변경 · `uniqueItems` 신설 · `enum` 신설 | 어제 통과하던 값이 오늘 거부된다. `IdempotencyKey.pattern` 이 대표적이다 — 조이면 재전달 중인 메시지가 DLQ 로 간다 |
| **E11** | `oneOf`/`anyOf`/`allOf`/`prefixItems` 분기 제거 | `AnyEvent` 에서 한 종을 빼는 것 = 그 이벤트 타입의 폐기다 |
| **E12** | `$ref` 대상 변경 | 가리키는 정의가 달라지면 값 집합이 통째로 바뀐다. 문자열 비교로 잡는다 — 새 대상이 우연히 호환이어도 **리뷰 없이 지나가면 안 되는 변경**이다 |
| **E13** | `format` 추가·변경 | `-c ajv-formats` 로 실제 검사하므로 제약 신설과 같다 |
| **E14** | `$id` 변경 | 소비자·다른 계약 파일의 `$ref` 가 그 자리에서 끊긴다 |

### 파괴가 아니다 (WARN — 로그에 남기고 green)

| 코드 | 변경 | 왜 red 가 아닌가 |
|---|---|---|
| **W01** | enum 값 추가 | 소비자는 모르는 값을 만날 수 있지만, 이걸 red 로 두면 **새 `EventType`·새 `FailureReason` 을 영원히 못 늘린다.** 계약이 자라지 못하면 사람이 계약을 우회한다. `AnyEvent` 의 `oneOf` 한 줄이 같이 늘어 CODEOWNERS 리뷰에 걸리는 것이 이 자리의 방어선이다 (`D2-events.md §5`) |
| **W02** | 선택 속성 추가 | `schemaVersion` 부 버전 증가의 정의 그 자체다 (`envelope.json` `SchemaVersion` 설명) |
| **W03** | 새 `$def`·새 파일 추가 | 기존 소비자가 읽는 것이 하나도 바뀌지 않는다 |
| — | 제약 완화 (`max*` 증가 · `min*` 감소 · `type` 확대 · `enum` 삭제) | 어제 통과하던 것은 오늘도 통과한다 |
| — | `description`·`title`·`$comment`·`default`·`examples` 변경 | 값에 아무 영향이 없다. 이것이 red 를 내면 주석 한 줄 고치는 데 계약 리뷰가 붙고, 그러면 아무도 주석을 안 고친다 |

### 기준(base)을 어디서 잡는가

`contract-breaking` 과 **같은 자세**다 — 기준 = **git `HEAD` 판의 `contracts/events`**, 대상 = **워킹트리 판**.
별도의 frozen 사본을 레포에 두면 그 사본 자체가 새 드리프트 면이 된다(누가 갱신하는가 문제).
CI 에서 PR 을 볼 때는 `COLAB_BREAKING_BASE_REF=origin/main` 으로 기준을 옮긴다 —
`contract-breaking` 과 **같은 환경변수 이름**이라 CI 가 두 게이트에 서로 다른 기준을 주는 사고가 안 난다.

기준에 이벤트 계약이 0건이면 **최초 동결**이라 파괴할 이전 계약이 없다 → green.
대상(워킹트리)이 0건이면 **red** 다. 비교 대상 없는 파괴적-변경 게이트를 green 으로 세는 것이 green-by-skip 이다.

---

## 3. selftest 케이스 — 33건, 각각이 무엇을 증명하는가

`./gates/run.sh event-selftest` (또는 `selftest` 묶음). `contract-selftest.sh` 와 **같은 방식**이다 —
`expect <기대> <라벨> <명령>` 한 줄에 케이스 하나, 전부 임시 디렉터리. 두 번째 스타일을 발명하지 않았다.

### `event-lint` — 12건

| # | 케이스 | 기대 | 증명하는 것 |
|---|---|---|---|
| ① | 실제 이벤트 계약 + 실제 픽스처 | green | **기준선.** 이게 red 면 나머지 케이스는 의미가 없다 (전부 red 를 내는 게이트는 fail-closed 가 아니라 고장이다) |
| ② | 깨진 JSON | red | 파싱 단계에서 잡는다 |
| ③ | `$ref` 를 없는 `$def`(`common.json#/$defs/NoSuchDef`)로 | red | **`$ref` 가 실제로 해석되는지**를 게이트가 본다. `D2-events §7-1` 이 지적한 "끊긴 `$ref` 가 green" 상태를 닫는다 |
| ④ | 오탈자 키워드 `requred` | red | ajv `strict` 가 켜져 있다. 조용히 무시되면 계약이 아무것도 강제하지 않는다 |
| ⑤ | 이벤트 계약 0건 | red | green-by-skip 금지 |
| ⑥ | valid 픽스처 0건 | red | 인스턴스 검증 없는 이벤트 게이트는 `$ref` 해석을 증명하지 못한다 |
| ⑦ | invalid 픽스처 0건 | red | **거부를 증명하지 않는 게이트는 fail-open 이다** |
| ⑧ | 계약을 어긴 인스턴스를 `valid/` 에 둠 | red | 게이트가 위반을 통과시키지 않는다 |
| ⑨ | 정상 인스턴스를 `invalid/` 에 둠 | red | 거부돼야 할 것이 안 됐음을 게이트가 알아챈다 (픽스처 관리 실수도 red) |
| ⑩ | 진입 스키마(`entry.schema.json`) 부재 | red | 검사 진입점이 없으면 통과가 아니다 |
| ⑪ | `contracts/schemas/common.json` 부재 | red | 정규 타입 정본 없이 도는 검사는 검사가 아니다 (`CLAUDE.md §3-6`) |
| ⑫ | ajv 도구 확보 실패 (빈 도구 디렉터리) | red | **도구 부재·네트워크 실패는 skip 이 아니라 red** (`CLAUDE.md §4`) |

### `event-breaking` — 21건

E01~E14 각 규칙에 red 케이스가 하나씩(14건) + green 이어야 하는 것 5건 + 운영 실패 2건.

| # | 케이스 | 기대 | 증명하는 것 |
|---|---|---|---|
| — | 변경 없음 | green | 기준선. 항상 red 를 내는 diff 는 게이트가 아니라 소음이다 |
| E01 | `core-pipeline.json` 파일 제거 | red | 파일 단위 소실 검출 |
| E02 | `envelope.json#/$defs/Failure` 제거 | red | `$defs` 단위 검출 — **이 게이트의 존재 이유** |
| E03 | `Delivery.deadLettered` 속성 제거 | red | 속성 단위 검출 (선택 속성이어도 파괴다) |
| E04 | `Delivery.required` 에 `deadLettered` 추가 | red | 이미 배포된 생산자를 깨는 변경 |
| E05 | `Delivery.required` 에서 `redelivery` 제거 | red | **소비자 관점 규칙이 실제로 작동함** — 동기 API 감각이면 놓쳤을 자리 |
| E06 | `FailureReason` enum 에서 `시간 초과` 제거 | red | 큐에 남은 옛 메시지가 위반이 된다 |
| E07 | `HeaderParsedPayload.crs` 를 `["string","null"]` → `"string"` | red | 정본이 연 **부분 성공** 경로가 계약에서 막히는 것을 잡는다 (`Policy §9`) |
| E08 | `Envelope.payload.additionalProperties: false` | red | 조임 검출 |
| E09 | `UploadReady.type.const` 를 `upload.done` 으로 | red | **라우팅 키 변경** — 소비자 분기가 통째로 빗나가는 자리 |
| E10 | `FileRef.fileName.maxLength` 255 → 64 | red | 값 제약 조임 |
| E11 | `AnyEvent.oneOf` 에서 분기 하나 제거 | red | 이벤트 타입 폐기 검출 |
| E12 | `Envelope.labId.$ref` 를 다른 정의로 | red | 참조 바꿔치기 검출 |
| E13 | `IdempotencyKey.format: uuid` 추가 | red | format 신설 = 제약 신설 |
| E14 | `envelope.json` 의 `$id` 변경 | red | 소비자 `$ref` 가 끊기는 자리 |
| W01 | `FailureReason` enum 에 값 추가 | **green** | **완화 규칙이 실제로 완화다.** 이게 red 면 새 이벤트 타입을 영영 못 늘린다 |
| W02 | `FileRef` 에 선택 속성 `checksum` 추가 | **green** | 하위호환 확장이 막히지 않는다 |
| — | `maxLength` 255 → 512 (완화) | green | 완화를 파괴로 오판하지 않는다 |
| — | `description` 만 변경 | green | 주석 수정에 계약 리뷰가 붙지 않는다 |
| — | 대상(워킹트리) 이벤트 계약 0건 | red | green-by-skip 금지 |
| — | 기준 git ref 부재 | red | 기준을 못 잡은 것은 통과가 아니다 |

**green 케이스 5건이 이 표의 절반이다.** 전부 red 를 내는 게이트는 fail-closed 가 아니라 고장이며,
고장 난 게이트는 사람이 끄고 싶어지는 게이트다. "무엇이 파괴가 **아닌가**"를 증명하지 않으면
§2 의 규칙표는 문서일 뿐이고 코드가 아니다.

---

## 4. 실증 — 실제 파괴적 변경이 red 를 낸다

완료 판정의 후반부(「이벤트 계약 변경이 실제로 red 를 냄」)는 픽스처가 아니라 **실제 파일**로 증명한다.
`contracts/events/envelope.json` 을 잠깐 고쳤다가 되돌렸고, 되돌린 뒤 무변경을 확인했다.

### 변경 전

```
$ ./gates/run.sh event-breaking
# 기준 HEAD (2건) ↔ 대상 (2건)
# 판정 — ERR 0건 · WARN 0건 (규칙표 = dev-package/sessions/D2b.md §2)
event-breaking green — 기준 HEAD (2건) 대비 파괴적 변경 없음.
```

### 실제 파괴적 변경 두 건을 넣는다

`FailureReason` enum 에서 `시간 초과` 를 지우고(E06), `Delivery.required` 에 `deadLettered` 를 넣는다(E04).

```
$ ./gates/run.sh event-breaking
# 기준 HEAD (2건) ↔ 대상 (2건)
  [ERR] E04 required 에 속성 추가 — envelope.json#/$defs/Delivery : 추가 ['deadLettered']
  [ERR] E06 enum 값 제거 — envelope.json#/$defs/FailureReason : 제거된 값 ['시간 초과']
# 판정 — ERR 2건 · WARN 0건 (규칙표 = dev-package/sessions/D2b.md §2)
::error::event-breaking red — 기준(HEAD) 대비 이벤트 계약에 파괴적 변경이 있다.
   계약을 깨야 한다면 우회하지 말고 멈추고 보고한다 (CLAUDE.md §4 '경계를 넘어야 할 때').
   하위호환으로 낼 수 있는 길은 셋이다 — ① 선택 필드로 추가 ② 새 EventType 추가
   ③ schemaVersion 주 버전을 올리고 소비자가 두 버전을 동시에 받는 기간을 둔다.
(exit=1)
```

**`event-lint` 도 같이 red 를 냈다.** 두 게이트가 서로 다른 각도로 같은 사고를 잡는다 —
`event-breaking` 은 "기준 대비 깨졌다"를, `event-lint` 는 "현행 인스턴스가 더 이상 계약을 못 지킨다"를 말한다.

```
$ ./gates/run.sh event-lint ; echo "exit=$?"
::error::계약을 지킨 인스턴스가 거부됐다: gates/fixtures/events/valid/header-parsed-full.json
::error::계약을 지킨 인스턴스가 거부됐다: gates/fixtures/events/valid/header-parsed-partial.json
::error::계약을 지킨 인스턴스가 거부됐다: gates/fixtures/events/valid/upload-accepted.json
::error::계약을 지킨 인스턴스가 거부됐다: gates/fixtures/events/valid/upload-failed-permanent.json
::error::event-lint red — 이벤트 계약 검사 실패.
exit=1
```

### 복원 — `contracts/` 는 바이트 단위로 그대로다

```
$ git checkout -- contracts/events/envelope.json
$ git status --porcelain contracts/ ; git diff --stat -- contracts/
(출력 없음 — contracts/ 변경 0건)

$ ./gates/run.sh event-lint     | tail -1
event-lint green — 스키마 2건 컴파일 · valid 5건 통과 · invalid 8건 거부.
$ ./gates/run.sh event-breaking | tail -1
event-breaking green — 기준 HEAD (2건) 대비 파괴적 변경 없음.
```

`./gates/run.sh event-selftest` → **33/33 green**. `contract-lint` · `contract-breaking` 은 이 세션 전후로 변화 없다.

---

## 5. 이 게이트가 여전히 못 잡는 것

닫힌 구멍보다 **남은 구멍을 적어 두는 것**이 다음 세션의 시간을 아낀다.

| 못 잡는 것 | 왜 | 닫는 길 |
|---|---|---|
| **의미 파괴** — 필드 이름·타입은 그대로인데 뜻이 바뀌는 것 (`byteSizeTotal` 을 합계 → 최대값으로) | 스키마에 뜻이 없다. 어떤 구조 diff 도 못 본다 | 계약 리뷰(CODEOWNERS)·`schemaVersion` 주 버전. **기계가 대신할 수 없는 자리다** |
| **`schemaVersion` 규율** — 파괴적 변경을 하면서 주 버전을 안 올려도 게이트는 "파괴"만 말하고 버전을 요구하지 않는다 | 두 사실의 연결을 규칙으로 안 박았다. 지금 박으면 W01/W02 에서 오탐이 난다 | 후속 WU. `type` 별 `schemaVersion` `const` 와 변경 종류를 묶는 규칙 |
| **생산자·소비자 코드가 계약을 지키는가** | 이 게이트는 **계약 문서**와 **픽스처**만 본다. `services/` 는 아직 이벤트를 내지도 받지도 않는다 | D5 구현 WU — 생산자가 낸 실제 메시지를 픽스처로 승격하고, 소비자 계약 테스트를 붙인다 |
| **하위호환 소비자 테스트** — `contracts/README.md` 가 이벤트에 요구한 것 | "옛 소비자가 새 메시지를 먹는가"는 옛 소비자 코드가 있어야 돌릴 수 있다 | 같은 D5 WU. `D2-events §7-3` 이 남긴 항목이며 **아직 열려 있다** |
| **생성물 최신성** — `contracts/codegen/` 이 events 두 파일을 생성 대상에 넣어야 한다 | `generated-up-to-date` 게이트가 미구현(red)이다 | WU-B2 / `generated-up-to-date` |
| **브로커 채널 지도** — 어느 이벤트가 어느 큐로 가는가 | 브로커(SQS·SNS·outbox)가 아직 안 정해졌다 | 인프라 WU. 그때 AsyncAPI 를 얹되 페이로드는 이 파일들을 `$ref` 한다 — 정의를 두 곳에 두지 않는다 |
| **enum 값 추가로 인한 소비자 깨짐** (W01) | 의도적으로 WARN 이다 (§2) | 소비자 쪽 "모르는 값은 무시" 규약을 D5 구현에서 테스트로 박는다 |
| **`gates/fixtures/events/` 자체의 커버리지** | valid 픽스처가 이벤트 7종 중 4종만 덮는다(`file.format-detected`·`file.crs-normalized`·`preview.cog-built` 없음) | 값싼 후속 작업. 다만 **AnyEvent 진입점을 쓰므로 7종 전부가 스키마 컴파일 대상이긴 하다** |

> 한 줄로: 이 게이트는 **계약의 모양**을 지킨다. **계약의 뜻**과 **계약을 지키는 코드**는 아직 사람과 후속 WU 의 몫이다.
