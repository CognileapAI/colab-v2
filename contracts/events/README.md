# events — 비동기 계약 (core-api ↔ pipeline-worker → viz-render)

OpenAPI가 아니다. 명령·이벤트 봉투를 버전 JSON-Schema로 계약화한다.

봉투가 반드시 담는 것 — **멱등 키** · 스키마 버전 · 발생 시각 · 재처리(DLQ) 규칙 · 하위호환 소비자 테스트.

> v1(PoC)에서 워커 트랜잭션 부재로 고아 산출물이 생기고 큐가 조용히 데드락됐다.
> 멱등 키와 재처리 규칙을 계약에 넣는 이유가 이것이다.

---

## 동결된 파일 (WU-D2)

| 파일 | 담는 것 |
|---|---|
| `envelope.json` | 공통 봉투 · `EventType` **10종** · `IdempotencyKey` · `Delivery`(재전달·DLQ) · `FailureClass`·`FailureReason`·`Failure` · **`InvalidationTrigger`** |
| `core-pipeline.json` | 이벤트 **10종**의 페이로드와 구체 정의 · `AnyEvent`(소비자 검증 진입점) |

⭑ **⟨증보 2026-08-31 · 12차 동결 해제 · `PLAN-SoT §9 〈253〉` · Ted RULING ㉗⟩ 7종 → 10종.**
／ 이전 표기 ~~`EventType` 7종 · 이벤트 7종~~ — **두 집합이 갈라졌다:**

| 묶음 | 종 | 방향 | 성격 |
|---|---|---|---|
| E-04 업로드 파이프라인 | 7 | core-api ↔ pipeline-worker | 업로드 하나가 단계를 지나는 **진행** |
| 미리보기 무효화 알림 | 3 | pipeline-worker(D5) **→** viz-render(D7) | 「이미 선 미리보기의 재료가 바뀌었다」는 **사실** |

- 뒤의 3종 = `preview.backend-rerun`·`preview.grid-changed`·`preview.file-added`.
  트리거 이름의 정본은 **대장**(`WORK-UNITS §10.2-b` `Y-1` 행)이고 계약은 그것을
  `InvalidationTrigger` 열거로 옮겨 적었다 — 계약이 이름을 새로 짓지 않는다.
- **명령이 아니라 사실이다.** 「다시 그려라」가 아니라 「무엇이 바뀌었다」이고, 무엇을
  지울지는 받는 쪽(D7)이 계산한다(`Y-1` 완료 정의 ⓔ). 그래서 페이로드에 **지울 경로·
  캐시 키가 없다** — 발신자가 수신자의 산출물 배치를 알면 그 순간 경계가 무너진다.
- **왜 셋으로 갈랐나** — 멱등 키가 `<타입>:<uploadId>` 라서다. 한 종류로 묶으면 업로드
  하나당 트리거가 한 번만 나가고 「3종이 **각각** 무효화를 일으킨다」(완료 정의 ⓑ)가
  배선에서 성립하지 않는다.
- **D7 은 받기만 한다.** `d5_upload`·`d5_pipeline_event`(outbox)를 읽는 경로는 계약에도
  코드에도 없다(불변규칙 1 · 음성 시험 `services/viz-render/tests/test_trigger_intake.py`).
- 전송 수단은 여전히 계약 밖이다(`〈61〉`) — 지금 실물은 두 배포 단위가 함께 보는
  **디렉터리 하나**(`COLAB_WORKER_EVENT_SPOOL` ↔ `COLAB_VIZ_TRIGGER_SPOOL`)이고,
  브로커가 정해지면 발행자·어댑터를 갈아 끼운다. **원장에 남는 사실은 같다.**

- 스키마 언어는 **JSON Schema 2020-12** 다. 고른 이유와 대안(AsyncAPI)을 버린 근거는 `dev-package/sessions/D2-events.md §2`.
- 정규 타입은 전부 `../schemas/common.json` 을 `$ref` 한다. 값 집합·ID 를 여기서 다시 선언하지 않는다 (`CLAUDE.md §3-6`).
- 검증은 `ajv`(`--spec=draft2020 -c ajv-formats`)로 한다. **`contract-lint` 게이트는 `contracts/seams/**` 만 보므로 이 두 파일을 검사하지 않는다** — 한계와 닫는 방법은 `sessions/D2-events.md §7`.
