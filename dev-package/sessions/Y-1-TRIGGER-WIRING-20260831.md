# `Y-1` — D5 → D7 트리거 발신을 계약으로 열고, 발신·수신을 같은 회차에 배선한다

> 등재 = `PLAN-SoT §9 〈253〉`(Ted RULING ㉗) · **12차 동결 해제**. **값·근거의 정본은 거기다** —
> 이 문서는 절차와 실측표만 남긴다. 워크트리 `lane-trigger` · 2026-08-31 ·
> **`Y-1` 은 닫지 않았다**(§6).

## 1. 물음

`〈247〉` 회차가 무효화·범위 계산·집행·재생성을 `viz-render` 에 세웠다(시험 16건 · 음성 8).
**없던 것은 하나** — 「미리보기 뒷단 재실행 · 격자 변경 · 파일 추가」를 **D5 가 어디로 어떻게
보내는가**(`03-HANDOFF §4 #55`). 우회로 둘은 스스로 막혀 있었다:

| 우회로 | 왜 막히나 |
|---|---|
| D7 이 D5 의 표·outbox 를 직독 | **불변규칙 1** 위반 — `db-boundary`·`import-boundary` 가 막는다 |
| 계약을 안 건드리고 잇기 | 이벤트 계약이 `core-api ↔ pipeline-worker` 전용이라 **종류 추가 = 계약 개정** |

**Ted RULING ㉗ = ⓐ 이벤트 계약을 확장한다.** ⓑ 직접 호출은 도메인 결합을 키우고,
ⓒ 배포 배선은 **이번 세션에 두 번 물린 방식**이다 — 코드에 남지 않는 연결은 조용히 끊어져도 모른다.

## 2. 순서 (`CLAUDE.md §4` — 바꾸지 않았다)

| 단계 | 실측 |
|---|---|
| 진입조건 | `Y-1` 선행 `P3`·`D5` 둘 다 `done`. 착수 가능 |
| **계약 동결** | `event-lint` green(스키마 2 · valid **8** · invalid **10**) · `event-breaking` **green — ERR 0 · WARN 6** · `contract-lint`·`contract-breaking`·`seam-consistency`(G-b **7 → 10**)·`generated-up-to-date` green |
| **실패 시험 red 선확인** | pipeline-worker **13 red**(＋ 음성 2 는 착수 전부터 green — 잘못 구현하면 red 가 된다) · viz-render **수집 단계 red**(모듈 부재 · 14건) |
| 구현 | 아래 §3·§4 |
| 게이트 | 전 게이트 green(§5) |

## 3. 계약 — 무엇을 늘렸나

- `envelope.json` — `EventType` **7 → 10** · 새 `$def` **`InvalidationTrigger`**(한국어 3값)
- `core-pipeline.json` — 새 `$def` **4**(`PreviewStalePayload` ＋ 구체 이벤트 3) · `AnyEvent` `oneOf` **7 → 10**
- **op 총계 무변동 54** — HTTP 표면 0건이다. 4차·11차와 성격이 다르다

**셋으로 가른 근거 = 멱등 키.** 키가 `<타입>:<uploadId>` 라서 한 종류로 묶으면 업로드
하나당 트리거가 **한 번만** 나가고, 완료 정의 ⓑ(3종이 **각각**)가 배선에서 성립하지 않는다.

**페이로드는 `trigger` 하나뿐이다.** 대상은 봉투의 `uploadId` 가 말하고, **지울 경로·캐시
키는 싣지 않는다** — 이벤트는 **사실**이지 명령이 아니다. 음성 픽스처가 그것을 거절한다.

## 4. 배선 — 발신과 수신

| 쪽 | 무엇을 세웠나 |
|---|---|
| **D5 발신** | `IngestionService` 가 **「이미 `ready` 인 업로드」에서만** 셋을 낸다 — 격자 축 행 신설 → `격자 변경` · 처음 보는 본체 감지 → `파일 추가` · 뒷단 ③④⑤ 재실행 → `미리보기 뒷단 재실행`. `record_detected_format` 이 「처음 적는가」를 돌려주게 해 **원장이 그 사실의 오라클**이 된다 |
| **D5 전송** | `spool_publish`/`fan_publish` — 릴레이가 **D7 종류만** 버스로 보낸다(표준출력은 그대로). `COLAB_WORKER_EVENT_SPOOL` · 원자적 `rename` |
| **D7 수신** | `app/trigger_bus.SpoolTriggerPort` — poll → 집행 → **ack**. 멱등 키로 재전달을 거르고, **ack 전에는 알림을 안 지운다**. 지우는 자리는 버스 안으로 갇혀 있다 |
| **D7 집행** | `app/triggers.drain` — `JobStore.regenerate` 를 부르고, **그린 적 없는 대상은 건너뛴다**. `create_app` 이 `app.state.triggers` 로 자리를 들고 선다 |
| **DB** | `0009_preview_stale_event_types` — `event_type` CHECK 7 → 10. 순수 가산 · 값 이행 0행 · **전진 전용** |
| **배포 선언** | `compose.i2.yml` — 버스 볼륨 `events` ＋ 두 단위 env. **시험이 두 값을 대조한다**(신설 3건) |

## 5. 계수와 게이트

| 축 | 전 | 후 |
|---|---|---|
| viz-render | 180 | **194** (＋14 · 새 음성 **7**) |
| pipeline-worker | 204 | **222** (＋18 = 트리거 15 ＋ 배포 선언 3 · 새 음성 **5** · 기존 오라클 4건 갱신) |
| 이벤트 픽스처 | valid 5 · invalid 8 | valid **8** · invalid **10** |
| op 총계 | 54 | **54** |
| 게이트 `all` | **green 35 / red 0** | **green 35 / red 0** |

⚠ **경계를 한 번 밟았고, 게이트가 잡았고, 우회하지 않았다.** 어댑터를 처음에 `ports/trigger.py` 로 두었더니 `import-boundary` 가 red — viz-render 층은 `app > domains > ports > kernel` 이라 `ports` 가 `domains` 를 import 할 수 없다. `CLAUDE.md §4` 의 셋 중 **어느 것도 아니었다**(Port 추가 불요 — 도메인이 이미 `TriggerPort` 로 자리를 선언했다 · 분할 오류 아님 · 기획 애매 아님). **조립이 조립 층에 있지 않았을 뿐**이라 `app/trigger_bus.py` 로 옮겼고 그 뒤 green. `app/main.py` 가 `FilesystemSourcePort` 를 세우는 것과 같은 자리다.

**경계 위반 0건을 어떻게 쟀나** — ⑴ `import-boundary`·`banned-import`·`db-boundary`·
`ai-no-lineage-write` 전부 green ⑵ **산문이 아니라 식별자를 잰다** — 수신부 두 모듈의
토큰 집합에 `sqlalchemy`·`psycopg`·`requests`·`httpx`·`boto3`·`kafka`·`publish`·`outbox`·
`append_event`·`d5_upload`·`d5_pipeline_event`·`d4_lineage` **0건** ⑶ `〈247〉` 의 음성 8건이
그대로 green 이고, 배선 끝까지 원본 불변을 잠그는 음성이 하나 늘었다.

## 6. `Y-1` 완료 정의 — 조건별 충족표

| 조건 | 판정 | 근거 |
|---|---|---|
| ⓐ 무효화 대상 = 렌더 산출물뿐 | ✅ | `〈247〉` 회차 ＋ 이번 배선 끝단에서 다시 잠갔다(음성) |
| ⓑ 트리거 3종이 **각각** 무효화를 일으킨다 | ✅ | 발신 3 · 수신 3 · 재생성 3 이 각각 시험을 갖는다 |
| ⓒ 수동 「다시 만들기」 흡수 · 두 경로가 같은 계산기 | ✅ | `〈247〉` 그대로. 버튼을 발신부로 개조하지 않았다 |
| ⓓ stage 1 원칙이 여기서만 뒤집힌다 | ✅ | 예외 범위 = 렌더 산출물 한정(`〈247〉`) · 원본 불변 음성 유지 |
| ⓔ 경계 — 발신 D5 · 무효화·재생성 D7 · cross-domain 은 Port | ✅ | 계약 경유 단방향 · 위 §5 의 측정 |
| **ⓕ staging 배포 green** | ⛔ **미충족** | **이 회차는 배포 금지 조건이었다.** staging 무접촉 |

**⛔ 닫지 않았다 — 부분 완료로 닫지 않는다**(`WORK-UNITS §12`). 대장 `Y-1` = **`partial`**.

**다음 회차의 진입조건** — 배포 인가 ＋ 새 버스 볼륨 `events` 가 실제로 뜬 상태 ＋
`verify/verify-deploy.sh` green ＋ **트리거 1왕복 실측**(업로드 재처리 → 미리보기 재생성).

## 7. 이번에 세지 않은 축

`〈253〉`-⑧ 에 넷이 이름으로 있다 — ⓐ staging 실물 왕복 ⓑ 같은 트리거의 재발행(멱등 키
형태를 넓히는 것은 **E10 ERR** 이라 별도 판정) ⓒ 버스의 수명·적체 상한 ⓓ 데이터셋 단위
무효화(`attachUploadGridFiles`) — 봉투의 집계 루트가 `uploadId` 라 이 seam 으로는 못 알린다.
