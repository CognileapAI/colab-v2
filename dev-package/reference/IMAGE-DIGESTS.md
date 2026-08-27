# IMAGE-DIGESTS — staging 이미지 digest 대장

> **이 파일이 digest 값의 정본이다.** 다른 문서는 여기를 가리키기만 한다(`CLAUDE.md §6-3` — 두 곳에 적으면 갈라진다).
> 판정·근거는 `PLAN-SoT §9 〈165〉-㉱`.

## 1. 왜 있는가

- **`:i2` 는 움직이는 태그다.** 같은 태그가 재빌드마다 다른 이미지를 가리킨다 — **태그는 신원이 아니다. digest 만이 신원이다.**
- `WORK-UNITS §10.3` 1 단이 재기동 검증 항목으로 **「이미지 digest 일치」**를 요구하는데 **대조할 기록이 레포에 없었다**(`sessions/R1-RESTORE-DRAFT.md §2` #9 · `§6` #3).
- **이 결손은 이미 한 번 사고를 냈다** — `〈153〉` 때 배선만 바꾸고 **옛 이미지로 올려** `ai-service` 만 healthy 였고, 사전 DB 가 `None` 으로 조용히 비어 **온톨로지가 통째로 사라진 채 헬스 200** 을 냈다. **죽은 쪽은 바로 보이고 살아 있는 쪽이 속인다.**

## 2. 언제·어떻게 쟀는가

| | |
|---|---|
| 측정일 | **2026-08-27** |
| 대상 | 살아 있는 staging 호스트(WSL2)의 로컬 이미지 |
| 방법 | `docker images --digests` / `docker image inspect` 의 digest 를 **그대로 옮겨 적었다** — 가공·축약 없음 |
| 성격 | **읽기 전용 측정.** 이 회차에 이미지를 다시 만들거나 태그를 옮긴 일이 없다 |

## 3. 대장 (8 건 — 자체 5 ＋ 외부 3)

| 이미지 | digest |
|---|---|
| `colab-v2/core-api:i2` | `sha256:c08220676167595b1b5849666552b8c608b8b2bd88a98ac7f6d1a767580ec1b2` |
| `colab-v2/pipeline-worker:i2` | `sha256:e4f6c59e89338adfa56773071d81593e789cd1f2e2a8d8baa22de5e788dba4c1` |
| `colab-v2/ai-service:i2` | `sha256:18cb90b8ec48a7ac22e69a9458897dcfe9d3ff4950dd915c3fe8eb3de0d6f5ba` |
| `colab-v2/viz-render:i2` | `sha256:6f7e69c632c09de7e2fdc0aef3893f2c820c6159ba0f8afb7f9e27a52b5b05fa` |
| `colab-v2/frontend:i2` | `sha256:0bc652f15716bc6facdda2bbcf5884436418d8cd49d6efb25ca754c4a4d7fdfb` |
| `postgres:16-alpine` | `sha256:cf78e76683b9ca8c5733cbbdce6c9262b45b6767934dd0a95e671f9a0fc20685` |
| `nginx:1.27-alpine` | `sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10` |
| `cloudflare/cloudflared:latest` | `sha256:6b599ca3e974349ead3286d178da61d291961182ec3fe9c505e1dd02c8ac31b0` |

⚠ **`cloudflare/cloudflared:latest` 는 다른 이유로 움직인다** — `:i2` 는 **우리가 재빌드할 때**, `:latest` 는 **업스트림이 밀어 올릴 때** 움직인다. 재기동 때 이 한 줄이 달라지는 것 자체는 이상이 아니고, **달라졌다는 사실을 모르고 넘어가지 않는 것**이 여기의 목적이다.

## 4. 쓰는 법

1. **재기동 직후** 같은 방법으로 다시 재고, 위 표와 **한 줄씩 대조**한다.
2. **불일치가 나오면 재기동을 계속하지 않는다.** 헬스 200 은 이 불일치를 잡지 못한다(`§1` 의 사고가 그 증거다).
3. 불일치가 **의도된 것**이면(재빌드·업스트림 갱신) **이 파일을 먼저 갱신하고**, 무엇이 왜 바뀌었는지 `PLAN-SoT §9` 에 등재한다. **문서를 안 고치고 넘어가면 다음 회차가 대조 기준을 잃는다.**
4. **digest 를 다른 문서에 복사하지 않는다.** 인용은 이 파일을 가리키는 링크로 한다.
