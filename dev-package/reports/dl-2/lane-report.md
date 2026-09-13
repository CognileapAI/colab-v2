# `DL-2` 레인 보고 — 미리보기 산출물 회수 (2026-09-13)

브랜치 `lane/wu-dl-2` · 기점 `origin/main` `7446eb7d` · `DL-1` 커밋 10 ＋ `DL-2` 커밋 6.
**병합·push·`PLAN-SoT` 기입·`〈N〉` 발급은 이 레인이 하지 않는다.**

---

## 1. 커밋

| # | sha | 무엇 | 레인 |
|---|---|---|---|
| D0 | `f7a433c0` | Ted 회부문 ⓓ1~ⓓ7 ＋ 대장 `DL-2` 문면 | A |
| D1 | `b1235a16` | 표식 자리 `preview-index/` (계약 `layout.json` ＋ 생성물 3) ＋ 싱크 `index`·`remove` | A |
| D2 | `6a5860d7` | `invalidation.deletion_plan` ＋ `reclaim_on_delete.run` ＋ 발행 시 `index` ＋ S3 삭제 잠금 문면 범위 분리 | A |
| D3 | `10ad5115` | 계약 22차 `reclaimPreviews`(`POST /reclaims`) ＋ viz 라우트 ＋ `main.py` 8 op | B |
| D4 | `86defbbf` | core Port·중계 ＋ 삭제 트랜잭션 ⑧-c 호출 | B |
| D5 | (이 커밋) | 백필 ops ＋ 대장 evidence ＋ HANDOFF ＋ 보고서 | B |

앞선 `DL-1` 커밋 10(`5ffc1a6f`~`e41deb19`)은 `dev-package/reports/dl-1/lane-report.md` 가 잰다.

### 1-1. 레인 A 요지 (B 가 회수한 사실만)

- 산출물 = 위 D0~D2 세 커밋. 보고서 파일은 남기지 않았다 — 아래는 **커밋 실물에서 읽은 것**이다.
- 표식 자리 = `preview-index/by-file/{fileId}/{contentKey}`(0바이트) · 계약
  `contracts/storage/layout.json` 의 **별도 top-level `previewIndex`** · 생성물 3벌 재생성.
- 회수 한 바퀴 = `reclaim_on_delete.run(*, client, sink, previews_root, target_id, file_ids,
  previews_prefix) -> ReclaimResult{stale, kept, unindexed, removed, kept_reasons}`.
- 잠금 = 「`delete_objects(`·`.remove(` 호출자는 `preview_sinks.py`·`s3.py`·`reclaim_on_delete.py`
  셋뿐」을 음성 시험이 판정한다(`tests/test_reclaim_on_delete.py:237`).
- ⚠ **A 의 리베이스 충돌 7사건·게이트 3계수는 이 레인이 재지 않았다** — `[미측정]`.
  `DL-1` 재리베이스의 충돌 5파일 7사건은 `dl-1/lane-report.md §10` 에 있고 그것과 다른 값이다.

---

## 2. 계약 — 동결 해제 22차 ㉯ (Ted 승인 대기)

- 값 = `contracts/seams/core-viz.yaml` 에 `reclaimPreviews`(`POST /reclaims`) 1건 ＋ 스키마 2건
  (`PreviewReclaimRequest`·`PreviewReclaimResult`). **core-viz op 총계 7 → 8**
  (`fe-core` 무변 — core 는 삭제 트랜잭션 안에서 부르고 FE 표면을 늘리지 않는다).
- 응답 집합 = **200/400/401/503**. 422 를 적지 않은 근거 = viz 가 `RequestValidationError` 를
  400 으로 바꾸고(`app/main.py`) `require_caller` 는 401 만 낸다.
- `X2-FREEZE-PROTOCOL.md §1` 에 22차 행을 세웠다(승인 「대기」 · `〈N〉` 임시).

### 2-1. 게이트 출력 (축자)

| 게이트 | 출력 |
|---|---|
| `contract-lint` | `contract-lint green — seam 3건, 룰 위반 0.` |
| `contract-breaking` | `contract-breaking green — 기준 origin/main (       3건) 대비 파괴적 변경 없음.` (oasdiff `No breaking changes to report, but the specs are different.` = 순수 가산) |
| `seam-consistency` | `seam-consistency green — G-e 503건 · G-b 10건 · ㉠ 10건 · ㉡ 18건.` |
| `generated-up-to-date` | `generated-up-to-date green — 등기부 13건 전부 재생성 일치, 등기부 밖 자칭 생성물 0건.` |
| `import-boundary` | `import-boundary green — 계약 전부 통과.` (`Contracts: 8 kept, 0 broken.`) |
| `banned-import` | `banned-import green — .py 183건, 금지 import 0.` |
| `db-boundary` | `db-boundary: green — 단위 8개 · 스캔 대상 417건 · 위반 0` |
| `work-item-consistency` | `work-item-consistency: green — 대장과 산문의 불일치 0` |
| `exec-bit` | `exec-bit green — `.sh` 211건 전부 인덱스 모드 100755 (100644 = 0건).` |

`contract-breaking` 은 `COLAB_BREAKING_BASE_REF=origin/main` 으로 돌렸다.
`generated-up-to-date` 는 `core-viz.yaml` 이 **등기부 밖**이라 TS 생성물이 무변임을 확인한 값이다.

### 2-2. 3계수

**green 9 / red(판정) 0 / red(준비) 0** — 이 레인이 선언한 게이트 집합 기준.
`service-tests-viz-render`·`service-tests-core-api` 는 이 맥에서 무판정 매달림(대장
`gate-pg-reach`)이라 **직접 pytest 로 갈음**했다(§3).

---

## 3. 시험

### 3-1. viz-render

- 신설 `tests/test_reclaims_route.py` **10건** — red 먼저 확인(`10 failed` · 축자
  `AssertionError: {"detail":"Not Found"}` / `assert 404 == 200`) → 구현 → `10 passed`.
  잰 것 = 401(무토큰) · 400 넷(빈 `fileIds` · 비ULID 둘 · 모르는 칸) · 400(경계 헤더 부재 ·
  `TENANT_SCOPE_MISSING`) · 200 본문 5칸 ＋ 로컬 unlink ＋ 싱크 통지 · 멱등(2회째 `stale 0`) ·
  일부 생존 → `kept` · s3 모드에서 표식 목록 조회 **파일당 1회** ＋ 싱크 삭제.
- 신설 `tests/test_backfill_preview_index.py` **3건** — red 먼저(`ModuleNotFoundError:
  No module named 'colab_viz.ops'`) → 구현 → `3 passed`.
- `DL-2` 관련 6파일 묶음 = **78 passed / 0 failed**
  (`test_reclaim_on_delete` ＋ `test_reclaims_route` ＋ `test_backfill_preview_index` ＋
  `test_preview_sink` ＋ `test_storage_layout` ＋ `test_auto_invalidation`).
- **전수 = 490 passed / 41 failed.** 41 은 전부 **준비 red** 다 — 축자
  `Failed: COLAB_REFERENCE_DATA 가 원천 디렉터리를 가리키지 않는다 — 성능 시험은 skip 하지 않는다`
  (`test_e2e_real` 11 ＋ `test_e2e_storage_layout_real` 5 ＋ `test_perf_render_latency` 25).
  이 맥에 원천 데이터 마운트가 없다 · `~/.colab-v2-test.env` 가 그 값을 **의도적으로 선언하지
  않는다**(파일 머리말 축자). 레인 A 와 **같은 집합**이다(같은 워크트리·같은 env).

### 3-2. core-api

- `tests/test_dataset_deletion.py` = **26 passed / 0 failed**(신설 3 포함).
  red 먼저 확인 = `3 failed`(`assert 0 == 1` · `PREVIEW_RECLAIM_FAILED` 부재 · 호출 0회).
- `tests/test_preview_relay.py` 신설 2건 — **구현 뒤에 쓴 시험이라 red 선행이 없다.**
  대신 **변이 증명**: 중계의 `/reclaims` 경로를 `/renders` 로 바꾸면 `1 failed`
  (`src/colab_core/app/relay.py:241: RelayUnavailable`) — 단언이 공허하지 않다.
- 전수(`-m "not e2e"`) 계수는 §5 에 있다.

---

## 4. 시험 환경 — 이 맥에서 손본 것

⚠ **로컬 시험 DB `colab_platform_test` 가 이 브랜치의 선언 스키마보다 낡아 있었다.**

- 증상 = 모든 core-api 시험의 teardown 이 `psycopg.errors.UndefinedTable: relation
  "d3_search_evidence" does not exist` 로 죽고(`conftest._CLEANUP`), 죽은 트랜잭션이
  뒤 시험으로 번졌다. 최초 전수 = `297 failed / 923 passed / 801 errors`.
- 실측 = 선언(`db/platform/schema.sql`) 대비 **표 1건**(`d3_search_evidence` · `:813`)과
  **제약 1건**(`d3_file_lab_dataset_id_unique` · `:800`)이 DB 에 없었다.
  `alembic_version_platform` 은 **0행** — 이 DB 는 마이그레이션이 아니라 옛 `schema.sql` 로
  세워졌다.
- 조치 = 그 둘만 **선언 원문 그대로** 적용했다(표·색인·RLS 2정책·`colab_app` GRANT).
  삭제 0건 · 데이터 변경 0건 · 다른 객체 무접촉.
- **어느 검사에 걸리는가** — `service-tests-core-api` 게이트에는 걸린다(판정 red 를 낸다).
  `schema-diff` 게이트는 **적용 DB(dev·staging) URL** 을 보므로 이 로컬 시험 DB 는 보지 않는다.
  ⟹ **후속 항목 ①**(§7).

---

## 5. core-api 전수 계수 — 기준선 대조

같은 호스트·같은 DB·같은 명령(`pytest -q -m "not e2e" -p no:randomly`)으로 **두 번** 돌렸다.

| 트리 | passed | failed | errors |
|---|---|---|---|
| 기준선 = `6a5860d7` 의 `services/core-api`(＝ DL-2 착수 전) | **998** | **217** | 26 |
| 이 레인 = `86defbbf` | **1003** | **217** | 26 |

- **failed 집합이 글자까지 같다** — 두 실행의 `FAILED` 줄을 정렬해 `diff` 한 결과 차이 0.
- **passed 차이 ＋5 = 이 레인이 신설한 시험 5건**(삭제 3 ＋ 중계 2).
- ⟹ **이 레인이 만든 red 는 0건**이다. 「main 과 같다」로 넘기지 않고 **다시 재서** 그렇게 말한다.

### 5-1. 그 217 은 무엇인가 — 그리고 **어느 검사에 걸리는가**

- 원인 = §4 와 **같은 계열**의 로컬 시험 DB 드리프트다. 오류형 분포 =
  `sqlalchemy.exc.ProgrammingError` 31 · `psycopg.errors.InsufficientPrivilege` 27 ·
  `IntegrityError`/`UniqueViolation` 각 10 · `UndefinedColumn` 4 — 전부 스키마·롤 드리프트이고
  코드 결함의 모양이 아니다. 걸린 파일도 이 레인과 무관하다(`test_operator_designation` 26 ·
  `test_storage_maintenance` 16 · `test_search_relay` 12 · `test_approval` 10 …).
  `tests/test_dataset_deletion.py`(26/26)·`tests/test_preview_relay.py`(18/18) 는 **둘 다 0 failed** 다.
- **걸리는 검사** = `service-tests-core-api` 게이트 하나뿐이고, 그 게이트는 이 맥에서 무판정
  매달림이라(대장 `gate-pg-reach`) **실제로는 아무도 안 본다.** `schema-diff` 는 적용
  DB(dev·staging)만 보므로 시험 DB 를 보지 않는다. ⟹ 후속 항목 ①.
- ⚠ **이 계수를 「전수 green」으로 바꿔 적지 않는다** — 판정에 쓸 수 있는 것은 이 레인이
  바꾼 두 파일의 계수(26/26 · 18/18)와 위의 기준선 대조뿐이다.

---

## 6. `intent` 대조 — 원한 결과

기준 = 대장 `DL-2` 완료 정의 ⑴~⑹ ＋ 계획서 「설계 결정 4·5」.

| # | 항목 | 판정 |
|---|---|---|
| ⑴ | `reclaimPreviews` 등재 ＋ 생성물 재생성 ＋ 응답 200/400/401/503 | **충족** — §2 |
| ⑵ | `deletion_plan` ＋ viz 단위 시험 ＋ `unindexed` 계수 | **충족**(레인 A · B 가 라우트에서 재확인) |
| ⑶ | 싱크 `remove`·`index` ＋ 발행 순서 | **충족**(레인 A) |
| ⑷ | core 가 커밋 전 릴레이를 부르고 실패 시 500·무변경 · 미설정 갈래 로그 | **충족** — §3-2 |
| ⑸ | dev compose 기배선 · prod 는 이 PR 범위 밖 | **충족**(코드 변경 0) |
| ⑹ | **dev 실측** | **미달 — 이 레인의 범위 밖**(오케스트레이터 별건 · 배포 창) |

### 초과분 (요청되지 않은 변경)

1. `services/viz-render/src/colab_viz/app/main.py` 에 `app.state.s3_client` 한 줄.
   근거 = 라우트가 자기 S3 클라이언트를 세우면 버킷·리전을 읽는 자리가 둘이 되고,
   `main` 을 import 하면 순환이 된다. **표면 변경 0 · 기존 객체를 그대로 노출한다.**
2. `services/viz-render/src/colab_viz/ops/__init__.py` 신설(패키지 자리).
3. §4 의 로컬 시험 DB 보정 — **레포 파일 변경 0건**(환경 조작).

---

## 6-1. 대장 `DL-2` 를 `open` → `partial` 로 바꾼 근거

- **`partial` 은 이 대장에서 정의된 상태값이다** — 사용 중인 값 6종(`open` 48 · `done` 167 ·
  `partial` 6 · `conflict` 6 · `deferred` 4 · `in_progress` 4). `work-item-consistency` 가
  `partial` 을 받아 green 을 냈다(§2-1).
- **선례 3건이 「닫지 않는다」의 표기로 쓰고 있다.**
  `T-I` — 축자 「⛔ 그래서 닫지 않는다 — `status: partial` 유지. 「부분 완료로 닫지 않는다」」 ·
  `R-1` — 축자 「⟹ **부분 충족으로 닫지 않는다.**」(`conflict` → `partial` 로 갈아 온 이력) ·
  `P5` — `partial` 로 서 있다가 Ted 판정 뒤 `done`.
- **`CLAUDE.md §5` 와 양립한다.** 그 규율이 금지하는 것은 **`done`**(＝ 닫기)이고,
  `partial` 은 그 금지를 **지키는** 표기다. 반대로 `open` 으로 두면 「착수 전」과 「코드·시험은
  끝났고 Ted 판정과 dev 실측만 남았다」가 같은 값이 되어, 다음 세션이 무엇이 남았는지를
  `evidence` 를 열기 전에는 못 읽는다.
- **매핑** = `03-HANDOFF §1` 의 🟧 ↔ 대장 `partial`. 대장을 먼저 고치고 HANDOFF 를 그 반영본으로
  맞췄다(`CLAUDE.md §6`).
- ⚠ **되돌릴 조건** — 오케스트레이터가 「레인은 상태를 바꾸지 않는다」로 판정하면 한 줄로
  `open` 복구 ＋ HANDOFF ⬜ 복구 ＋ `work-item-consistency` 재실행이면 된다.

---

## 7. 후속 항목

1. **로컬 시험 DB 의 스키마 드리프트를 어느 게이트도 안 본다.** `schema-diff` 는 적용
   DB(dev·staging)만 보고, 시험 DB 가 낡으면 `service-tests-*` 가 **판정 red 처럼 생긴 준비
   red** 를 낸다(§4 · 최초 전수 297 failed 의 전부가 그것이었다). 시험 DB 도 선언 스키마와
   대조하는 자리가 필요하다.
2. **`dev-package/sessions/X2-FREEZE-PROTOCOL.md §1` 표가 빈 줄로 끊겨 있다** —
   18차 행과 20차 행 사이에 빈 줄이 있어 20차·22차가 별도 표로 렌더된다. 이 레인은 22차 행을
   20차 행 바로 뒤에 붙였고 빈 줄은 건드리지 않았다(범위 밖).
3. **21차(`〈376〉`)·19차(`〈346〉`)가 §1 표에 행이 없다** — 회차의 정본 발급처는 `PLAN-SoT §9`
   이지만 §1 표가 회차 이력으로 인용되므로 결번이 계속 쌓인다.
4. **표식 백필의 `--apply` 는 아직 안 돌렸다** — Ted ⓓ5 GO 전제. dev dry-run 계수도 이 레인이
   재지 않았다(`[미측정]`).
5. `pyhdf` 가 이 맥에서 빌드되지 않는다(`fatal error: 'hdf.h' file not found`) — viz venv 는
   그 패키지만 빼고 구성했다. HDF4 경로를 쓰는 시험은 §3-1 의 준비 red 41 에 포함된다.
