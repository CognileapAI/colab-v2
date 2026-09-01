# A-1 안 ⑷ — 「Port 하나」의 실측 비용 · #56-ⓒ 와의 역전 판정

조사 회차 2026-09-02 · 읽기 전용 · 이 파일 외 편집 0건. 인용은 전부 `파일:줄`. 값이 없으면 `[미확인]`.
전제 = Ted 판정 2026-09-02 「안 ⑷ 사이드카 판정 채택」. **안 자체는 다시 열지 않는다.**
측정 대상 = `A-1-OPTION-REVIEW.md §5` 딸린 조건 1 — 「Port 1 의 비용이 #56-ⓒ(6~9 파일 ＋ 이벤트 계약 1 ＋ 동결 해제 ＋ #59 선행)를 넘는가」.

---

## 1. 사이드카는 오늘 무엇을 담는가 — 재검토문의 기술 하나를 정정한다

| 사실 | 값 | 근거 |
|---|---|---|
| 사이드카 필드 | 8 — `name` `crs` `bbox_3857` `bbox_4326` `width` `height` `pixel_size_m` `source` `created` | `services/viz-render/src/colab_viz/domains/d7_visualization/preview.py:168-187` |
| `source` 에 실제로 들어가는 값 | **`reads[0].part.file_name`** — 즉 **디스크의 파일 이름**이다 | `services/viz-render/src/colab_viz/domains/d7_visualization/jobs.py:388` → `preview.py:270` |
| 그 파일 이름이 실배포에서 무엇인가 | **`fileId`** — 본체 키가 `{uploadsPrefix}/{targetId}/{fileId}` 라 디스크 이름이 곧 `fileId` 다 | `contracts/storage/layout.json` `keys.본체` · `ports/source.py:22-23`·`:69-77` |
| ⟹ 재검토문 `§3.1` 의 「`source` 는 `fileId` 하나다」 | **실배포에서는 맞고, 문면상으로는 파일명이다.** 시험 픽스처는 사람 이름을 넣는다(`tests/test_preview_layers.py:69`) — 그 자리가 `fileId` 임을 **못 박은 규약이 없다** | `preview.py:171-172` 축자 「`name`·`source` 는 **파일명**이다」 |
| 사이드카를 쓰는 자리 | `build_map_layer` **한 곳**(`preview.py:270-272`) — 지도형만 |
| 사이드카를 **읽는 생산 코드** | **0건**. 전 레포에서 사이드카를 파싱하는 자리는 시험 3곳뿐(`tests/test_e2e_real.py:154` · `tests/test_preview_layers.py:72`·`:125`) | grep 전수(`services`·`gates`·`contracts`) |

⟹ **소유 판정은 아직 어느 코드에도 없다.** 「판정 불가 34 키」는 사람이 센 조사값이지 기계 판정이 아니다.

## 2. 판정이 실제로 필요한 매핑 — 확인한 것

- 사이드카가 주는 것 = `fileId`(실배포) ＋ 산출물이 놓인 자리. **`datasetId` 는 없다.**
- **`uploadId → datasetId` 표는 원장에 존재하지 않는다** — 축자 「등록 전환 시각. **`datasetId` 를 두지 않는다** — D5 가 D3 를 직접 가리키면 불변규칙 1 위반이다」(`db/platform/schema.sql:617-619`).
- 유일한 다리는 **`fileId` 동일성**이다 — `d5_upload_file.id` 가 등록 시 `d3_file.id` 로 그대로 간다(`schema.sql:629-631` `NB-A`), 그리고 `d3_file.dataset_id`(`schema.sql:437`)가 소유를 답한다.
- ⟹ 필요한 매핑은 **`fileId → d3_file.dataset_id`** 이고 **소유 도메인은 D3(core-api)** 다. D5 가 아니다.
- 묻는 쪽 = 산출물 자리를 읽는 단위. `previews` 볼륨은 **viz-render·pipeline-worker·nginx(:ro)** 에만 붙고 **core-api 에는 없다**(`BLOCKER-56-OPTIONS.md §1` · `infra/staging/compose.i2.yml:199-200`).
- ⟹ **판정에 필요한 두 사실(사이드카 · `d3_file`)이 한 단위 안에 함께 있지 않다.** 이것이 이 항목의 실제 난점이고, `source` 필드의 내용이 아니다.

## 3. 이 레포의 Port 패턴 — 잣대

| Port | 구성 | 규모 |
|---|---|---|
| `SourcePort`(D7) | Protocol ＋ 어댑터 1(같은 파일) ＋ 조립 1줄(`app/main.py:32`) | **파일 1 ＋ 조립 1줄** · 126줄 |
| `DatasetAccessPort`(core-api) | Protocol(`ports/access.py:42`) ＋ 구현 `domains/d2_access.py:86` ＋ 조립은 app | **파일 2** · Port 파일 45줄 |
| `LineageSummaryPort` | `ports/lineage.py:31` ＋ `domains/d4_lineage.py:217` | **파일 2** · 32줄 |
| `PreviewRenderPort`(core-api→viz) | Protocol `ports/relay.py:21` ＋ 전송 구현 `app/relay.py` ＋ compose env 2(`compose.i2.yml:177`·`:182`) ＋ 계약 `contracts/seams/core-viz.yaml` | **배포 단위를 넘는 유일한 선례** |

⚠ **같은 프로세스 안의 Port 는 파일 1~2 다. 배포 단위를 넘는 Port 는 계약·토큰·compose 가 따라붙는다.** 이 둘을 한 숫자로 세면 틀린다.

⛔ 결정적 실측 — **viz-render 에는 나가는 HTTP 클라이언트가 0개다**(`httpx`·`requests`·`urlopen` 전수 0건, `services/viz-render/src`). 계약도 `contracts/seams/` 셋(`core-ai`·`core-viz`·`fe-core`) 전부 **core-api 가 부르는 방향**이다. **viz→core 방향의 표면은 존재하지 않는다.**

## 4. Port 비용 — 두 갈래로 갈린다

### 갈래 A — D7 런타임이 직접 묻는다 (재검토문이 가정한 그것)

- 신설 `contracts/seams/viz-core.yaml` **계약 1 신설**(방향 자체가 없다) ＋ 게이트 `contract-breaking`·`seam` 재통과
- core-api: 라우트 1 ＋ 서비스 토큰 검증(역방향은 선례 없음) ＋ D3 조회 1
- viz-render: `ports/ownership.py`(Protocol) ＋ HTTP 어댑터 1(**클라이언트 자체가 없다**) ＋ `app/main.py` 조립 ＋ settings 1
- `infra/staging/compose.i2.yml`: core base url ＋ 토큰 env 2
- 시험 viz 2~3 ＋ core 2~3
- **합계 파일 9~12 · 계약 1 신설 · 마이그레이션 0 · 동결 해제 필요(등급 `[미확인]` — 마이그레이션 0 이라 ㉯ 자동 적용은 아니다) · 배포 필요(두 단위) · 선행 블로커 0**
- 생성물(codegen) 영향 `[미확인]` — `contracts/codegen/manifest.toml` 은 `gen_storage_layout.py` 하나만 싣는다(seam 은 대상 아님으로 보이나 확증 못 함)

### 갈래 B — 판정을 게이트 대조로 세운다 (Port 0)

- **선례가 이미 돈다** — `gates/tools/autometa-loss.sh:14` 축자 「이음 = `payload` 가 아니라 **`d5_upload_file.id = d3_file.id`**(`NB-A` 동일성). 업로드→데이터셋 FK 는 없다(불변규칙 1) — **그 동일성이 유일한 다리다**」. **§2 가 필요하다고 잰 바로 그 조인이 이미 게이트 안에 있다.**
- `gates/tools/preview-tile-slot.sh` 는 **산출물 자리와 platform DB 를 한 게이트에서 함께 본다** — 두 사실을 한 자리에 모으는 선례도 이미 있다.
- 신설분 = 게이트 스크립트 1 ＋ selftest 1 ＋ config 1(면제 파일 · 세 상태 규율 그대로)
- **합계 파일 2~3 · 계약 0 · 마이그레이션 0 · 동결 해제 0 · Port 0 · 배포 불요(게이트는 배포물이 아니다) · 선행 블로커 0**
- ⚠ 한계 — 게이트는 **계수·판정**을 답하고 **런타임 회수 집행**은 답하지 않는다. A-1 완료 정의 ⑴⑵⑸ 는 갈래 B 로 성립한다(⑵ 의 요구는 「프로세스 메모리 밖」이고 사이드카가 디스크에 있으면 성립). ⑶ 의 집행은 `invalidation.apply()` 가 이미 `target_id` 를 알고 도므로(`jobs.py:609-611`) 소유 질의를 필요로 하지 않는다.
- ⛔ **런타임 판정이 A-1 의 요구인가 여부는 `[미확인]`** — 완료 정의 ⑴ 문면은 「경로 **또는 원장 대조**로 판정할 수 있다」이고(`work-items.yaml` A-1 ⑴) 대조의 실행 주체를 못 박지 않는다. **Ted 판정 자리다.**

## 5. 역전 판정 — 나란히

| | Port 갈래 A(D7 런타임) | Port 갈래 B(게이트 대조) | **#56-ⓒ 재굽기** |
|---|---|---|---|
| 파일 | 9~12 | **2~3** | 6~9 |
| 계약 | 1 **신설**(없는 방향) | **0** | 1 ＋ 마이그레이션 1 |
| 동결 해제 | 필요(등급 `[미확인]`) | **0** | **㉯ Ted 승인 필수** |
| 선행 블로커 | 0 | 0 | **#59(events 볼륨 쓰기 거부)** |
| 배포 | 두 단위 재배포 | 불요 | 필요 |
| 되돌리기 | 계약이 걸린다 | 파일 삭제 | 트리거 off |

- **갈래 B 기준 — 역전하지 않는다.** 2~3 파일 · 계약 0 · 동결 해제 0 · 선행 0 은 #56-ⓒ 의 6~9 파일 · 계약 1 · 마이그레이션 1 · 동결 해제 ㉯ · #59 선행에 **모든 축에서 미달한다.** 권고 유지.
- **갈래 A 기준 — 파일 수는 넘고(9~12 > 6~9) 계약도 「신설」이라 더 무겁다. 다만 마이그레이션 0 · 선행 블로커 0 으로 상쇄되어 총량은 대략 동급이다.** 단독으로도 재검토 권고를 뒤집기에는 부족하다 — #56-ⓒ 는 **안 ⑴ 을 유지할 때 반드시 따라오는** 비용이고, 갈래 A 는 **갈래 B 가 막힐 때만** 발생하는 조건부 비용이다.
- ⟹ **역전 없음. 안 ⑷ 채택은 이 측정으로 유지된다.** 최소 비용 경로는 **갈래 B** 이고, 갈래 A 는 「런타임 판정을 요구로 세울 때만」 든다.

## 6. 안 ⑷ 아래 `A-1` 이 요구하는 것 — 순서대로

| # | 단계 | 의존 | 채우는 완료 정의 | 계약/동결 |
|---|---|---|---|---|
| 1 | 사이드카 `source` 를 **`fileId` 로 규약화**한다 — 지금은 「파일명」이고(`preview.py:171`) 실배포에서만 우연히 `fileId` 다. 문면과 시험을 못 박는다 | — | ⑴ 의 전제 | 0 |
| 2 | 사이드카를 **썸네일 `.webp`·비지도형 `.png` 층까지 확장**한다 — `_write` 계열 한 자리(`preview.py:216-227`)와 `build_value_layers`(`:229`) | 1 | **⑹** ＋ ⑴ 의 34 키 원인 제거 | `layout.json` `why ④` 가 `.json` 층을 이미 인정 → 문면 개정 필요 여부 `[미확인]` |
| 3 | 사이드카에 **소유 대상을 적는다** — `job.spec.target.target_id`·`is_upload` 는 이미 D7 안에 있다(`jobs.py:340-342` · `ports/source.py:36-39`). **Port 불요.** ⚠ 등록 전환 뒤 낡는다 → 「굽는 시점의 대상」임을 필드 이름으로 못 박고, 최신 소유는 4 가 답한다 | 2 | ⑴ ⑵ | 0 |
| 4 | **소유 대조를 세운다** — `사이드카 source(fileId) → d3_file.dataset_id`. 갈래 B(게이트 1 ＋ selftest ＋ config) 로 시작한다. 선례 `autometa-loss.sh:14` | 3 | **⑴ ⑵ ⑸** | 0 |
| 5 | **네 등급 계수 ＋ 회수 전 전수 스냅숏**(키·확장자·크기·사이드카 `source`) · 회수는 고아 등급만 | 4 | **⑸** | 0 |
| 6 | **집행은 `invalidation.apply()` 한 자리**(`jobs.py:609-611` · `invalidation.py`) — 지우는 문을 늘리지 않는다 | 5 | **⑶** | 0 |
| 7 | **음성 시험** — 접수분 루트·데이터셋 무접촉 · `tile-` 키는 `kept` | 6 | **⑷** | 0 |
| 8 | **재사용 시험을 대상 간 판 그대로 다시 세운다** — ⑷ 아래에서 `PV-1` 완료 조건 ⑵ 의 실측(`〈236〉`)이 계속 성립함을 회귀로 못 박는다 | 2 | **⑺(개정판)** | 0 |
| 9 | 전 게이트 green ＋ staging 배포 green | 1~8 | **⑻** | — |
| 10 | 대장 정리 — 진입조건 둘째 줄(#56 선행 판정) 소멸 · #56 은 「성립하지 않게 됨」으로 닫음 · 완료 정의 ⑺ 개정 · `PLAN-SoT §9 〈264〉`-㉮ 취소선 | 9 | — | 대장·`PLAN-SoT` 문면 |

**착수 최소 묶음** = 1→2→3 (사이드카 층 완성 · Port 0 · 계약 0). 4~7 은 그 위에서만 성립한다.

## 7. 여덟 완료 정의 중 다시 써야 할 항

- **⑺ — 반드시 개정.** 안 ⑷ 는 자리를 가르지 않아 **대상 간 재사용이 그대로 산다.** 손실 **316,201 B / 632,402 B 는 발생하지 않는다** → 「승계」가 아니라 「**승계 불요 · `PV-1` 완료 조건 ⑵ 가 원문대로 계속 성립함을 회귀로 지킨다**」로 고쳐 쓴다(`〈264〉`-㉮ 는 취소선 보존).
- **⑴ — 표현 보강 권고.** 「경로 또는 원장 대조」에서 **경로 갈래가 소멸**한다. 판정 근거를 「사이드카 ＋ 원장 대조」로 좁히고, **대조의 실행 주체(런타임 / 게이트)를 명시**한다 — 지금 문면이 그 자리를 비워 두어 §4 의 갈래 A·B 가 갈린다.
- **⑹ — 그대로.** 이 안의 본체가 곧 ⑹ 이다.
- **⑵⑶⑷⑸⑻ — 문면 개정 불요.**
- **진입조건 둘째 줄(#56 선행 판정) — 소멸.** ⑴ 을 세우지 않으면 그 불일치가 생기지 않는다(`BLOCKER-56-OPTIONS.md:23-25`).
