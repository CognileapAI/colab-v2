# events — 비동기 계약 (core-api ↔ pipeline-worker)

OpenAPI가 아니다. 명령·이벤트 봉투를 버전 JSON-Schema로 계약화한다.

봉투가 반드시 담는 것 — **멱등 키** · 스키마 버전 · 발생 시각 · 재처리(DLQ) 규칙 · 하위호환 소비자 테스트.

> v1(PoC)에서 워커 트랜잭션 부재로 고아 산출물이 생기고 큐가 조용히 데드락됐다.
> 멱등 키와 재처리 규칙을 계약에 넣는 이유가 이것이다.

---

## 동결된 파일 (WU-D2)

| 파일 | 담는 것 |
|---|---|
| `envelope.json` | 공통 봉투 · `EventType` 7종 · `IdempotencyKey` · `Delivery`(재전달·DLQ) · `FailureClass`·`FailureReason`·`Failure` |
| `core-pipeline.json` | 이벤트 7종의 페이로드와 구체 정의 · `AnyEvent`(소비자 검증 진입점) |

- 스키마 언어는 **JSON Schema 2020-12** 다. 고른 이유와 대안(AsyncAPI)을 버린 근거는 `dev-package/sessions/D2-events.md §2`.
- 정규 타입은 전부 `../schemas/common.json` 을 `$ref` 한다. 값 집합·ID 를 여기서 다시 선언하지 않는다 (`CLAUDE.md §3-6`).
- 검증은 `ajv`(`--spec=draft2020 -c ajv-formats`)로 한다. **`contract-lint` 게이트는 `contracts/seams/**` 만 보므로 이 두 파일을 검사하지 않는다** — 한계와 닫는 방법은 `sessions/D2-events.md §7`.
