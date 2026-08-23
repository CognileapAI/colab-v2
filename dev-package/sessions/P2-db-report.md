# P2 · W1 `P2-db` 실행 보고

> **레인** `P2-db` (물결 1 · 단독 실행) · **일자** 2026-08-23 · **실행 위치** 워크트리 `.claude/worktrees/p2-exec`
> **커밋하지 않았다.** 커밋·`03-HANDOFF`·`PLAN-SoT` 갱신은 메인 세션 몫이다 (`P2-EXEC §7`).
> **staging 을 건드리지 않았다.** 일회용 컨테이너는 `p2db_` 접두사이고 **호스트 포트를 하나도 열지 않았다.** 끝나고 지웠다.
> **계약을 고치지 않았다** — `contracts/` diff 0줄 (동결, `〈61〉-㉢`).
>
> **서술 규약** — `§A`·`§B`·`§C`·`§D` 는 **증거**(명령 + 실제 출력)다. `[잠정]` 이 붙은 것은 **해석**이다 (`DATA-REFERENCE §0 M-5`).
> 행 번호는 `cat -n` 으로 확인하고 옮겼다 (`M-7`). 절대경로를 적지 않는다 (`CLAUDE.md §3-8`).

---

## 0. 한 눈에

| 항목 | 결과 |
|---|---|
| 선행 실측 (`d3_file WHERE kind='기준 격자 파일'`) | **적용 대상 DB = `[미측정]`**(staging 접근 금지) · 로컬 재현 DB = **0 행** · 시드 픽스처 = **1 행** → `§A` |
| ⑴ 마이그레이션 `0004` | ✅ 두 불리언 · CHECK 2종 · 옛 인덱스 제거 · 축별 부분 유니크 2개 · **downgrade 실물 동작** |
| ⑵ `d5_*` 업로드 원장 | ✅ 3표(`d5_upload` 12열 · `d5_upload_file` 11열 · `d5_pipeline_event` 15열) · 전 표 `lab_id`+RLS+FORCE · 멱등 키 UNIQUE |
| ⑶ 드리프트 red 시험 | ✅ `db/platform/tests/0004-drift.sh` — 되돌리면 red 를 **실제로 냈다** |
| 게이트 | 요구 4종(`rls-coverage`·`rls-effect`·`migration-single-head`·`schema-diff`) **green** · `db-selftest` **green(43/43)** · 그 밖 12종 green · `planning-freshness` **red(기존 · 워크트리 부작용)** |

---

## A. 선행 실측 — `P2-EXEC §4 W1 ⑴-1`

### A. 증거

**A-1. 적용 대상 DB(staging) 는 재지 않았다.** 지시가 「staging 을 건드리는 명령을 레인이 돌리지 않는다」이고 8 컨테이너가 실서비스 중이다. **`[미측정]` 이고, 미측정을 0 으로 세지 않는다**(`M-4`).

**A-2. 대신 판정을 마이그레이션 안에 넣었다.** `0004` 의 `PRECOUNT` 블록이 적용 시점에 직접 세고, **1 행이라도 있으면 예외로 멈춘다.** 사람의 절차가 아니라 기계가 판정한다.

로컬 재현 DB(선언 스키마 + `app-role` + 시드)에서 실제로 센 값:

```
$ docker exec -i p2db_pg psql -U postgres -d preflight -c "SELECT kind, count(*) FROM d3_file GROUP BY kind ORDER BY kind;"
      kind      | count
----------------+-------
 기준 격자 파일 |     1
 본체           |     3
```

마이그레이션이 빈 DB 에 적용될 때 실제로 찍은 줄:

```
NOTICE:  [0004 선행 실측] d3_file WHERE kind=기준 격자 파일 → 0 행
```

**A-3. 그 1 행의 정체 — 시드 픽스처다.**

```
$ grep -n "기준 격자 파일" services/core-api/tests/fixtures/seed.sql
64:  ('00000000000000000000000FA2', … , '기준 격자 파일', 'a1-grid.nc',  50, 'k/a1g'),
```

### A. 해석 `[잠정]`

- **「멈추고 보고한다」의 대상은 실데이터다.** 그 규칙이 막으려는 것은 **축을 추측해 채우는 것**(`M-4`)이다. 위 1 행은 실측 대상이 아니라 **A2 가 손으로 쓴 시험 재료**이고, 값의 출처가 처음부터 저작이다.
- **그래서 둘로 갈라 처리했다** — ① 실데이터: 마이그레이션이 **0 이 아니면 무조건 멈춘다**(추측 없음) ② 픽스처: 축을 **명시**하고 그것이 측정이 아니라 저작임을 시드 파일 주석에 적었다(`§C-4`).
- ⚠ **메인 세션이 staging 에 `0004` 를 적용할 때 이 판정이 실제로 걸릴 수 있다.** 걸리면 그것이 정상 동작이다 — 축을 사람이 정한 뒤 다시 적용한다.

---

## B. ⑴ 마이그레이션 `0004` — 기준 격자 축 전환

### B-1. 좌표 확인 (`M-7` — 눈으로 세지 않았다)

```
$ cat -n db/platform/schema.sql | sed -n '286,291p'
   289	CREATE UNIQUE INDEX d3_file_one_reference_grid_per_dataset
   290	  ON d3_file (dataset_id) WHERE kind = '기준 격자 파일';

$ cat -n db/platform/versions/0001_p0_platform.py | sed -n '295,306p'
   301	CREATE UNIQUE INDEX d3_file_one_reference_grid_per_dataset
   302	  ON d3_file (dataset_id) WHERE kind = '기준 격자 파일';
```

**지시서의 `schema.sql:289-290` · `0001:301` 은 맞다.** 0001 쪽은 정확히는 `301-302` 두 줄이다.

### B-2. 만든 것 — `db/platform/versions/0004_p2_grid_axis_and_d5.py`

| 요구 (`P2-EXEC §4 W1 ⑴`) | 실물 |
|---|---|
| 선행 실측 · 0 아니면 정지 | `PRECOUNT` — `NO FORCE` → 세기 → 예외 → `FORCE` 복구 → **복구 여부를 DB 에게 되물음**(0002·0003 과 같은 방식) |
| `carries_lat` · `carries_lon` 두 불리언 | `boolean NOT NULL DEFAULT false` ×2 |
| CHECK 2종 (양쪽 반쪽) | `d3_file_grid_carries_an_axis`(격자 → 최소 하나 true) · `d3_file_body_carries_no_axis`(본체 → 둘 다 false) |
| 옛 인덱스 제거 | `DROP INDEX d3_file_one_reference_grid_per_dataset` |
| 축별 부분 유니크 2개 | `d3_file_one_lat_grid_per_dataset` · `d3_file_one_lon_grid_per_dataset` |
| `downgrade` 실제 동작 | `§D-3` 에서 **실물로 돌렸고** pg_dump 가 0003 과 **한 줄도 안 다르다** |

`db/platform/schema.sql`(선언 정본)에 **같은 차분**을 적었다 — `schema-diff` 가 둘의 일치를 판정한다(`§E`).

### B-3. 「위도1 + 결합축1」이 왜 막히는가 — 실제로 시도해 봤다

결합축 파일은 `carries_lat` 과 `carries_lon` 이 **둘 다 true** 라 **두 부분 유니크 인덱스에 동시에 걸린다.** 그래서 「위도 2건」뿐 아니라 「위도1 + 결합1」도 막힌다 — **제3값(단일 텍스트 enum)이 못 막던 자리**(`〈66〉`)다. 오라클 `0004-assertions.sql §C` 가 C3·C4·C5·C7·C8 다섯 조합을 **실제 INSERT 로** 시도해 전부 거절됨을 확인한다(카탈로그 존재 확인이 아니다).

---

## C. ⑵ `d5_*` 업로드 원장

### C-1. 만든 표 3종 (증거 — 적용된 DB 조회)

```
 table_name        | cols
-------------------+------
 d5_pipeline_event |   15
 d5_upload         |   12
 d5_upload_file    |   11
```

| 표 | 무엇 | 요구 대응 |
|---|---|---|
| `d5_upload` | 업로드 1건. `expires_at`(NOT NULL, **DEFAULT 없음**) · `ready`/`renderable`/`metadata_complete`(계약과 같은 3값 nullable) · 실패 3열 · `registered_at` | 「업로드 1건 + 만료 시각」 |
| `d5_upload_file` | **PK = 업로드가 발급한 `fileId` ULID** (`NB-A` — 등록 시 `d3_file.id` 로 그대로) · `carries_lat`/`carries_lon` + D3 와 **같은 CHECK 2종** + 업로드 안에서도 축별 부분 유니크 2개 | 「파일 N건 + 축 열」 |
| `d5_pipeline_event` | outbox. 봉투(`envelope.json`)를 열로 옮겨 적었다 — 7종 CHECK · `source` 2값 · `schema_version` 패턴 · `attempt`/`max_attempts`/`dead_lettered` · `payload jsonb` | 「이벤트/outbox + 멱등 키 유일 제약」 |

`d5_pipeline_event` 의 제약 전량:

```
 d5_pipeline_event_event_type_check
 d5_pipeline_event_idempotency_key_check
 d5_pipeline_event_idempotency_key_unique      ← 멱등 키 유일 제약
 d5_pipeline_event_schema_version_check
 d5_pipeline_event_source_check
 d5_pipeline_event_source_matches_type          ← upload.accepted ⇔ core-api
 (+ pkey · fkey 3 · attempt/max_attempts check)
```

### C-2. 경계 — `〈64〉` 를 그대로 읽었다

- **D3·D4·D6 를 가리키는 FK 가 하나도 없다.** `registered_at` 은 **시각만** 두고 `dataset_id` 를 두지 않았다 — 「이미 전환됨(409)」 판정에 필요한 것은 여부이지 대상이라서다. D5→D3 FK 는 불변규칙 1 위반이다.
- `core-api` 는 이 표를 직접 만지지 않는다 — `ports/ingestion.py`(P2-api 소관, `〈63〉-㉱`). **이 레인은 표만 세웠다.**

### C-3. RLS — 면제 0건

```
      relname      | relrowsecurity | relforcerowsecurity      tablename     |  policyname
-------------------+----------------+---------------------  -----------------+--------------
 d5_pipeline_event | t              | t                      d5_pipeline_event| lab_boundary
 d5_upload         | t              | t                      d5_upload        | lab_boundary
 d5_upload_file    | t              | t                      d5_upload_file   | lab_boundary
```

`rls-effect` 의 cross-tenant 전수 대상이 **18 → 21 표**로 늘었고 셋 다 「남의 연구실 0행」에 통과했다(`§E`).

**`body_access` 를 걸지 않은 이유는 `gates/config/rls-allowlist.toml` 주석에 남겼다**(조용히 빼지 않았다 — K1 선례): 그 정책은 `dataset_id` 로 `d2_dataset_access`·`d1_lab_profile` 을 조회하는데 **등록 전 업로드에는 데이터셋이 아직 없다**(`〈64〉-ⓓ`). → `§G-2` 에 미결로 등재.

### C-4. 시드 픽스처를 고쳤다 (범위 밖 파일 · 명시)

`services/core-api/tests/fixtures/seed.sql` 의 격자 행에 `carries_lat=true, carries_lon=true`(결합축)를 넣었다. **안 넣으면 새 CHECK 때문에 시드가 안 들어가고 `rls-effect` 가 red 가 된다.**
`.nc` 를 결합축으로 둔 근거는 `DATA-REFERENCE §1`·`〈66〉`(실물 `.nc` 격자는 한 파일에 둘 다 담는다)이고, **측정이 아니라 픽스처 저작임을 그 파일 주석에 적었다.** `hasReferenceGridFile` 은 종전과 같이 true 로 남는다.

---

## D. ⑶ 드리프트 red 시험 — RED → GREEN

**시험 실물** = `db/platform/tests/0004-drift.sh` + `db/platform/tests/0004-assertions.sql`.
오라클 파일 **하나**가 세 경우에 똑같이 돈다 — 「green 으로 시작하는 시험은 오라클이 아니다」를 파일을 나누지 않고 한 자리에서 증명한다.

### D-1. RED — 구현 **전**에 눈으로 봤다

구현 전 첫 실행 (실제 출력 전문):

```
$ ./db/platform/tests/0004-drift.sh
::error::0004-drift red — alembic 렌더 실패: upgrade 0004_p2_grid_axis_and_d5
EXIT=1
```

### D-2. 중간 RED — 오라클이 거짓 green 을 낸 것을 잡았다

구현 직후 첫 판정은 **green 이 아니었다.**

```
ERROR:  0004 오라클 실패 — 정상 조합(본체 · 위도격자 · 경도격자)이 거절됐다:
        value for domain ulid violates check constraint "ulid_crockford_base32"
```

**시험 재료의 ID 가 정규 ULID 가 아니어서** `_t_must_reject` 가 **엉뚱한 이유로 막힌 것을 「막혔다」로 세고 있었다** — 즉 그 시점의 음성 판정 4건이 **거짓 green** 이었다. 라벨을 26자로 펴고(`_t_ulid`), `SQLERRM` 에 `ulid_crockford_base32` 가 있으면 **판정이 아니라 재료 오류로 실패시키도록** 함수를 고쳤다. (`L`·`U` 는 Crockford base32 에 없다 — `PLD1` 이 그래서 걸렸다.)

### D-3. GREEN — 세 경우 전부 기대대로

```
[0004-drift] ㈎ 0004 적용 후 — 오라클 → green OK
[0004-drift] ㈏ 0004 없음 — 오라클이 red 를 내는가 → red OK
           ↳ ERROR:  0004 오라클 실패 — d3_file 에 boolean carries_lat·carries_lon 이 없다 (0/2). 0004 가 적용되지 않았다
[0004-drift] ㈐ downgrade 후 — 오라클이 red 를 내는가 → red OK
           ↳ ERROR:  0004 오라클 실패 — d3_file 에 boolean carries_lat·carries_lon 이 없다 (0/2). 0004 가 적용되지 않았다
[0004-drift] ㈐ downgrade 형태 복원(축 열 0 · 옛 인덱스 1 · d5 표 0) → OK
[0004-drift] ㈐ downgrade 결과 = 0003 상태 (pg_dump 동일) → OK
0004-drift green — ㈎ 적용 green · ㈏ 0004 없으면 red · ㈐ downgrade 실물 동작 + 0003 복원.
EXIT=0
```

**㈐ 가 downgrade 요구를 닫는다** — 「지웠다」가 아니라 「되돌렸다」를 pg_dump 대조로 판정한다(옛 인덱스 복원 포함).

### D-4. 이 시험의 성질 (정직하게)

- **실제 마이그레이션 파일을 태운다** — alembic 오프라인 모드(`--sql`)로 `versions/` 를 렌더한다. 오프라인이라 **DB 에 접속하지 않는다.** `schema.sql` 을 먹이는 방식은 「선언은 맞는데 마이그레이션이 틀린」 경우를 못 잡는다.
- **superuser 로 돈다.** CHECK·유니크 판정을 FORCE RLS 가 가리지 않게 하려는 것이고, **RLS 는 이 시험이 green 으로 세지 않는다** — `rls-coverage`·`rls-effect` 몫이다. 이 시험의 `§D` 항은 「정책이 선언돼 있는가」까지만 본다.
- **게이트가 아니다.** `gates/run.sh` 에 등재하지 않았다 — 게이트 신설은 이 레인의 범위가 아니다(`§G-1`).

---

## E. 게이트 — 판정 줄 그대로

전부 워크트리 루트에서 `./gates/run.sh <게이트>` 1회씩.

| # | 게이트 | 판정 줄 (그대로) | 판정 |
|---|---|---|:--:|
| 1 | `migration-single-head` | `migration-single-head green — 두 체인 모두 head 1개.` (`db/platform: 리비전 4건 · head 1개 (0004_p2_grid_axis_and_d5)`) | **green** |
| 2 | `schema-diff` | `schema-diff green — 두 체인 각각 선언 = 적용.` | **green** |
| 3 | `rls-coverage` | `rls-coverage green — allow-list 밖 테이블 전부 FORCE RLS + 연구실 경계 정책, 본체 테이블은 본체 정책까지.` | **green** |
| 4 | `rls-effect` | `rls-effect green — 본체 음성 · 메타 양성(P-13) · cross-tenant 셋 다 엔진이 막는다. 판정 롤은 우회 불가.` (`③ lab_id 보유 표 21개 전수 — 남의 연구실 0행`) | **green** |
| 5 | `db-selftest` | `db-selftest green — DB 게이트 3종 모두 틀린 것을 틀렸다고 말한다 (fail-closed 증명).` — **43 케이스 OK · ✗ 0건** | **green** |
| 6 | `rls-effect-selftest` | `rls-effect-selftest green — 보호 장치를 하나씩 떼면 실제로 red 가 난다. 틀린 롤도 red 다.` | **green** |
| 7 | `contract-lint` | `contract-lint green — seam 3건, 룰 위반 0.` | **green** |
| 8 | `contract-breaking` | `contract-breaking green — 기준 HEAD (3건) 대비 파괴적 변경 없음.` | **green** |
| 9 | `event-lint` | `event-lint green — 스키마 2건 컴파일 · valid 5건 통과 · invalid 8건 거부.` | **green** |
| 10 | `event-breaking` | `event-breaking green — 기준 HEAD (2건) 대비 파괴적 변경 없음.` | **green** |
| 11 | `seam-consistency` | `seam-consistency green — G-e 258건 · G-b 7건 · ㉠ 0건 · ㉡ 15건.` | **green** |
| 12 | `import-boundary` | `import-boundary green — 계약 전부 통과.` (`Contracts: 8 kept, 0 broken.`) | **green** |
| 13 | `banned-import` | `banned-import green — .py 59건, 금지 import 0.` | **green** |
| 14 | `ai-no-lineage-write` | `ai-no-lineage-write green — 계약·코드·체인 세 층 모두에서 쓰기 경로가 없다.` (`L3 체인층 db/ai 7건 · db/platform 7건`) | **green** |
| 15 | `generated-up-to-date` | `generated-up-to-date green — 등기부 1건 전부 재생성 일치, 등기부 밖 자칭 생성물 0건.` | **green** |
| 16 | `boundary-selftest` | `boundary-selftest green — 경계 게이트 3종 모두 틀린 것을 틀렸다고 말한다 (fail-closed 증명).` | **green** |
| 17 | `contract-selftest` | `contract-selftest green — 두 게이트 모두 틀린 것을 틀렸다고 말한다 (fail-closed 증명).` | **green** |
| 18 | `event-selftest` | `event-selftest green — event-lint · event-breaking 이 틀린 것을 틀렸다고 말한다 (fail-closed 증명).` | **green** |
| 19 | `seam-consistency-selftest` | `seam-consistency-selftest green — 13 케이스 전부 기대대로 (green 4 · red 9).` | **green** |
| 20 | `generated-selftest` | `generated-selftest green — 9 케이스 전부 기대대로 (green 1 · red 8).` | **green** |
| 21 | `planning-freshness` | `::error::planning-freshness red — 1건` / `  - 정본 폴더가 없다 (위치 확인 — planning/README.md §1): …/.claude/worktrees/40 COLAB-기획/…` | **red (기존)** |

**21번은 이 레인이 만든 것이 아니다** — `P2-W0-baseline §A-1` 이 착수 시점에 같은 문구로 이미 red 로 기록했고(워크트리 루트를 레포 루트로 계산하는 부작용), 내 변경은 `dev-package/` 문서 한 건(이 보고서)뿐이라 임베드 최신성과 무관하다. **메인 체크아웃에서의 확인은 여전히 메인 세션 몫이다**(baseline 이 남긴 그대로).

**`schema-diff` 재현 방법** — 체인마다 일회용 DB 를 만들어 마이그레이션을 head 까지 올리고, **호스트 포트를 열지 않고** 컨테이너 IP 로 `COLAB_APPLIED_DB_URL_PLATFORM`·`_AI` 를 둘 다 넘겼다. 하나라도 빠지면 게이트가 red 를 낸다(설계대로).

---

## F. `0004` 적용 **전 / 후** — 눈으로 본 실물

같은 컨테이너 안 두 DB. **앞은 `0003` 까지만, 뒤는 `0004` 까지.** 「마이그레이션이 성공했다」가 아니라 **관측된 차이**다.

### F-1. BEFORE (`0003_p1_topic_check`)

```
     version_num
---------------------
 0003_p1_topic_check

 column_name          |  indexname                              |  d5 표
----------------------|-----------------------------------------|--------
 id                   | d3_file_dataset_idx                     | (0 rows)
 lab_id               | d3_file_lab_idx                         |
 dataset_id           | d3_file_one_reference_grid_per_dataset  |
 kind                 | d3_file_pkey                            |
 file_name            |                                         |
 size_bytes           |                                         |
 storage_key          |                                         |
 created_at           |                                         |
(8 rows)                (4 rows)
```

### F-2. AFTER (`0004_p2_grid_axis_and_d5`)

```
       version_num
--------------------------
 0004_p2_grid_axis_and_d5

 column_name |        data_type              indexname
-------------+--------------------------    ----------------------------------
 id          | character                     d3_file_dataset_idx
 lab_id      | character                     d3_file_lab_idx
 dataset_id  | character                     d3_file_one_lat_grid_per_dataset
 kind        | text                          d3_file_one_lon_grid_per_dataset
 file_name   | text                          d3_file_pkey
 size_bytes  | bigint                       (5 rows)
 storage_key | text
 created_at  | timestamp with time zone
 carries_lat | boolean
 carries_lon | boolean
(10 rows)

      relname      | relrowsecurity | relforcerowsecurity
-------------------+----------------+---------------------
 d5_pipeline_event | t              | t
 d5_upload         | t              | t
 d5_upload_file    | t              | t
```

### F-3. 무엇이 달라졌나 (관측된 차이)

| | 전 | 후 |
|---|---|---|
| `d3_file` 열 | 8 | **10** (`carries_lat`·`carries_lon` boolean) |
| `d3_file` 인덱스 | 4 (`…one_reference_grid_per_dataset` 포함) | **5** — 옛 인덱스 **사라지고** 축별 2개 생김 |
| `d5_*` 표 | **0** | **3** (전부 `rls=t` · `force=t` · `lab_boundary`) |
| 체인 head | `0003_p1_topic_check` | `0004_p2_grid_axis_and_d5` |

---

## G. **하지 않은 것** — 범위 밖으로 남긴다

명시하지 않으면 다음 세션이 「했겠지」로 읽는다.

1. **게이트를 신설하지 않았다.** `0004-drift.sh` 는 `gates/run.sh` 에 등재하지 않았다 — 게이트 신설·`selftest` 편입은 이 레인의 범위가 아니다. **CI 에서 자동으로 돌지 않는다**(사람이 돌려야 한다). 등재할지는 메인 세션 판단.
2. **`d5_upload_file` 에 「올린 사람 말고는 못 본다」를 DB 층으로 걸지 않았다.** 경계(`lab_boundary`)까지만이다. 같은 연구실의 다른 계정은 DB 층에서는 남의 업로드 행이 보인다 — 막는 것은 현재 `ports/ingestion.py`(P2-api) 몫이다. **`〈64〉-ⓒ`(비노출) 의 시험 자리 `§6-2 음성 ㉴` 는 W2 가 닫는다.** allow-list 주석에 근거를 남겼다.
3. **reaper 를 만들지 않았다.** 만료분을 훑을 인덱스(`d5_upload_expiry_idx`)와 `ON DELETE CASCADE` 만 놨다. 실제 삭제 작업은 W2.
4. **Port(`ports/ingestion.py`)를 만들지 않았다** — `〈63〉-㉱` 가 P2-api 소관으로 배정했다.
5. **`0004` 를 staging 에 적용하지 않았다.** 로컬 일회용 DB 에서만 돌렸다.
6. **core-api pytest 를 돌리지 않았다.** 호스트에서 붙으려면 컨테이너 포트를 열어야 하는데 지시가 금지했다. 대신 **`rls-effect` 게이트가 같은 `schema.sql` + `app-role` + `seed.sql` 을 실제로 적재해 green** 이므로 시드 적재 자체는 실측으로 닫혔다. `test_file_count_drift.py:73` 의 `d3_file` INSERT 는 `'본체'` 만 넣고 축 열이 기본값 false 라 새 CHECK 에 걸리지 않는다 — **읽어서 확인했지 실행해 확인한 것은 아니다** `[잠정]`.
7. **`P2.md §2-22`·`DATA-REFERENCE §1` 의 낡은 문구(`grid_axis` 단일값)를 고치지 않았다.** `22-a` 가 이미 개정을 선언했고, 정본 문서 갱신은 메인 세션 규약(`CLAUDE.md §6`)이다.
8. **`W0-1` 축 판별 로직을 만들지 않았다** — W2 `P2-pipeline` 소관. DB 는 「축이 정해진 행만 받는다」까지다.

---

## H. 내가 판단한 것 — 정본이 정해 주지 않은 자리

| # | 판단 | 근거 / 표시 |
|---|---|---|
| **H-1** | **`expires_at` 에 DEFAULT 를 두지 않았다** — `NOT NULL` 열로만 뒀다 | **`[정본 무근거]`** — `NB-2`. 계약이 발행자에게 열어 뒀고 정본이 값을 안 줬다. **값을 발명하지 않았다.** 넣는 쪽(P2-api)이 명시해야 하고, **그 값이 정해지기 전에는 `createUpload` 가 삽입에 실패한다** — 조용히 아무 수명이나 붙는 것보다 낫다 |
| **H-2** | 시드 픽스처의 격자 행을 **결합축(둘 다 true)** 으로 저작 | `DATA-REFERENCE §1`·`〈66〉`(실물 `.nc` 격자는 한 파일에 둘 다) + `hasReferenceGridFile` 회귀 없음. **측정이 아니라 저작임을 파일 주석에 적었다** |
| **H-3** | `registered_at`(시각만) 을 뒀다 — `dataset_id` 는 두지 않았다 | 계약이 「이미 전환 409」를 요구하는데 D5→D3 FK 는 불변규칙 1 위반. **여부만 필요하고 대상은 필요 없다** `[잠정]` |
| **H-4** | 원장에도 **축별 부분 유니크**를 걸었다 (D3 와 같은 유일성) | 지시서 최소 요구에 없다. 안 걸면 접수는 통과하고 **등록 전환 때 뒤늦게 터진다**. 실패를 접수 시점으로 당겼다 `[잠정]` |
| **H-5** | `d5_pipeline_event` 에서 **`file_id` 열을 뺐다** | 처음엔 넣었다가 계약을 다시 읽고 뺐다 — **7종 페이로드 전부가 업로드 단위**이고 파일을 가리킬 때도 `fileIds` **배열**을 페이로드에 싣는다(`CrsNormalizedPayload`·`CogBuiltPayload`). 안 쓰는 열을 만들지 않는다 |
| **H-6** | `CHECK ((event_type='upload.accepted') = (source='core-api'))` 를 걸었다 | 봉투가 타입마다 `source` 를 `const` 로 못박은 것(`〈61〉` G-b 가 보는 그 성질)을 DB 로 옮겼다. **계약 재선언이 아니라 강제** `[잠정]` |
| **H-7** | 오라클을 **superuser 로** 돌린다 | CHECK·유니크 판정을 FORCE RLS 가 가리지 않게. RLS 판정은 이 시험이 하지 않는다(§D-4) `[잠정]` |

### H-8. 확인해서 **위험이 아님이 밝혀진 것** (기록으로 남긴다)

멱등 키가 `<타입>:<uploadId>` 라 **파일이 여러 개면 같은 키가 충돌하는 것 아닌가**를 의심했고, `contracts/events/core-pipeline.json` 의 페이로드 7종을 **열어서** 확인했다:

```
UploadAcceptedPayload | required: ['files']
FormatDetectedPayload | required: ['format','renderable','uniform']   (perFile 은 이 이벤트 안의 필드)
CrsNormalizedPayload  | required: [...,'fileIds']
CogBuiltPayload       | required: ['fileIds','overviewLevels']
```

**파일 단위 이벤트가 하나도 없다** — 전부 업로드 단위다. 따라서 `UNIQUE (idempotency_key)` 는 **타입 하나당 업로드 하나당 이벤트 하나**로 정확히 성립하고 충돌하지 않는다. 이 확인이 `H-5`(`file_id` 제거)의 근거이기도 하다. **인용이 아니라 열어 보고 썼다**(`M-4`).

---

## I. W2 를 막는 것 / 넘기는 것

**블로커 없음.** W2 두 레인(`P2-pipeline`·`P2-api`)의 DB 전건은 서 있다. 다만 넘기는 것 넷:

1. **`expires_at` 값** — `[정본 무근거]`(`H-1`). **P2-api 가 `createUpload` 를 쓰려면 이 값이 있어야 한다.** Ted 판정이 필요하거나, 레포 결정으로 못박고 `PLAN-SoT §9` 에 값과 근거를 남겨야 한다.
2. **staging 적용 시 선행 판정이 걸릴 수 있다** — staging 의 `d3_file` 격자 행이 0 이 아니면 `0004` 가 **의도대로 멈춘다**(`§A`). 그때 축은 사람이 정한다.
3. **staging 적용 후 `services/core-api/ops/app-role.sql` 을 다시 돌려야 한다.** `GRANT … ON ALL TABLES` 는 **그 시점의 표에만** 걸리므로, 마이그레이션이 새로 만든 `d5_*` 세 표에는 `colab_app` 권한이 없다. 그 파일은 재실행 가능하다. **마이그레이션 안에 GRANT 를 넣지 않은 이유** = 롤·GRANT 는 클러스터 객체라 `db/` 의 diff 대상이 아니라고 그 파일이 스스로 못박아 뒀다(주석 첫 문단). 관례를 레인이 뒤집지 않았다.
4. **`d5_*` 비노출의 DB 층 강제는 열려 있다**(`§G-2`) — `§6-2 음성 ㉴` 를 누가 어떤 층에서 닫을지 W2 `P2-api` 가 정한다.

---

## J. 만진 파일

| 파일 | 무엇 |
|---|---|
| `db/platform/versions/0004_p2_grid_axis_and_d5.py` | **신설** — 마이그레이션 |
| `db/platform/schema.sql` | 선언 정본에 같은 차분 (`d3_file` 축 2열·CHECK 2·인덱스 교체 · §4-b D5 3표 · RLS 3블록 · 머리말 2줄) |
| `db/platform/tests/0004-drift.sh` · `0004-assertions.sql` | **신설** — 드리프트 red 시험 |
| `services/core-api/tests/fixtures/seed.sql` | 격자 행에 축 명시 (+ 근거 주석) |
| `gates/config/rls-allowlist.toml` | `body_tables` 에 `d5_upload_file` 미등재 **근거 주석** (면제를 조용히 빼지 않는다) |
| `dev-package/sessions/P2-db-report.md` | 이 보고서 |

`contracts/` **0줄.** `services/**/src/` **0줄.**

---

## K. 재현

```bash
# 드리프트 시험 (docker + alembic 필요. 없으면 skip 이 아니라 red)
COLAB_ALEMBIC=<alembic 경로> ./db/platform/tests/0004-drift.sh

# 게이트
./gates/run.sh migration-single-head
./gates/run.sh rls-coverage
./gates/run.sh rls-effect
./gates/run.sh db-selftest
# schema-diff 는 체인별 적용 DB URL 을 둘 다 준다 (하나라도 없으면 red)
COLAB_APPLIED_DB_URL_PLATFORM=<platform DB> COLAB_APPLIED_DB_URL_AI=<ai DB> ./gates/run.sh schema-diff
```

---

## L. 추기 — advisor 지적 사후조치: ㈑ 케이스 (PRECOUNT 가드가 실제로 발동하는가)

> **일자** 2026-08-23 · **레인** 후속 단독 (본 보고서를 쓴 `P2-db` 레인과 별도 세션)
> 커밋하지 않았다. staging 을 건드리지 않았다 — 컨테이너는 전부 `p2db_` 접두사, 호스트 포트 0개, 종료 후 전부 삭제했다.
> 마이그레이션 `0004` 본체는 고치지 않았다 — 시험만 추가했다.

### L-0. 지적 요지

`0004` 의 `PRECOUNT` 가드(§A-2, 본 보고서 위쪽)는 「적용 대상 DB 에 `기준 격자 파일` 행이 1건이라도
있으면 apply 자체를 예외로 막는다」는 조항이다. 그런데 기존 `0004-drift.sh` 의 세 경우(㈎ 적용·
㈏ 미적용·㈐ downgrade) 는 전부 **빈 DB** 에서 시작한다 — 가드가 세는 값은 항상 0 이었고,
`RAISE EXCEPTION` 분기는 시험이 아니라 `NOTICE` 로그로만 관찰됐다. staging 에서 실제로 걸릴 수 있는
그 한 분기가 시험되지 않은 것 — advisor 지적대로 「green 으로 시작하는 시험은 오라클이 아니다」
(`CLAUDE.md §4`) 의 구멍이었다.

### L-1. 신설 — 케이스 ㈑

`db/platform/tests/0004-drift.sh` 에 ㈑ 를 추가했다. 기존 세 경우와 같은 컨테이너·같은 `psql_f`/`mkdb`
헬퍼를 재사용하고, 판정 방식만 다르게 했다 — ㈑ 는 오라클(`0004-assertions.sql`)로 재지 않는다.
가드가 걸리면 apply 자체가 실패해서 오라클을 돌릴 DB 가 없기 때문이다. 대신:

1. `0003` 까지만 적용한 DB(`prev.sql`)를 만들고
2. `기준 격자 파일` 행 1건을 직접 시드하고 (`d1_lab`·`d1_account`·`d3_dataset`·`d3_file`)
3. `0003→0004` 증분 마이그레이션(`upgrade $PREV_REV:$HEAD_REV`, 새로 렌더한 `step.sql`)을 적용 시도한다
4. **apply 자체가 실패해야 green** — 그리고 실패 사유가 가드의 실제 메시지
   (`축(carries_lat·carries_lon)을 채울 근거가 없다`) 인지까지 `grep` 으로 확인한다. 그냥 아무 red 나
   받아주지 않는다 — 「엉뚱한 이유로 막힌 red」도 실패로 잡는다.

(㈎/㈏/㈐ 는 전부 `head.sql`(base→head 전체 렌더)을 빈 DB 에 통으로 먹이는 방식이라 재사용이 안 됐다 —
`prev.sql` 적용 후 `head.sql` 을 또 먹이면 `alembic_version_platform` 이 이미 있어 `already exists` 로
막힌다. 이건 가드와 무관한 셋업 실수였고, `0003_p1_topic_check:0004_p2_grid_axis_and_d5` 증분 렌더로
바꿔 해결했다.)

### L-2. 관찰 — 가드가 실제로 발동했다

```
[0004-drift] ㈑ 기존 격자 1건 → apply red, PRECOUNT 가드 발동 OK
           ↳ ERROR:  기존 기준 격자 파일이 1 행 있다 — 축(carries_lat·carries_lon)을 채울 근거가 없다.
             사람이 각 행의 축을 실측으로 정한 뒤 다시 적용한다 (P2-EXEC 4 W1 1-1 · DATA-REFERENCE M-4)
```

apply 는 rc≠0 으로 실패했고, 실패 메시지는 `PRECOUNT` 블록이 던지는 바로 그 문구였다.
「DB 가 접속 불가라서 실패」·「문법 오류로 실패」 같은 무관한 red 가 아니라, 가드 조건
(`grid_rows > 0`) 자체가 걸렸다는 것을 메시지로 확인했다.

### L-3. 의도적 파손 확인 (§4 요구 — 이 시험 세트가 이미 한 번 거짓 green 을 낸 전력이 있어서)

이 시험을 신뢰하기 전에, 일부러 틀리게 만들어 red 로 안 뒤집히면 시험이 오라클이 아니라는 걸
확인했다. 시드 재료의 `kind` 를 `'기준 격자 파일'` 대신 `'본체'` 로 바꿔서(=가드가 세는 대상이
아예 없는 상태) 돌렸다:

```
[0004-drift] ㈑ 기존 격자 1건 → apply green (기대 red) ✗
::error::0004-drift red — 실패 1건:
     - ㈑ 기존 격자 1건인데 0004 적용이 통과했다 — PRECOUNT 가드가 안 걸렸다
```

기대대로 시험 전체가 red 로 뒤집혔다 — 시험이 실제로 가드의 유무를 구분하고 있다는 뜻이다.
확인 후 `git diff` 없이(임시 백업본에서) 원상 복구했고, 복구 뒤 재실행에서 다시 §L-2 와 동일한
green(전체 시험 기준)·가드 발동을 확인했다. `services/core-api` 레인이 겪었던 「ULID 도메인 위반을
막힘으로 잘못 센다」류의 함정도 직접 한 번 밟았다 — 시드 파일 이름에 `L`·`I` 를 썼다가
(`...FIL1`) `ulid_crockford_base32` 위반으로 삽입 자체가 막혀 준비 단계에서 red 가 났다.
Crockford base32 에 없는 문자라 `GRD1` 으로 바꿔 해결했다 — 판정 로직은 건드리지 않았다.

### L-4. 재실행 — 4 필수 게이트 + `db-selftest`

로컬에 `alembic` 이 없어(레포에 핀된 의존성 없음) `/tmp` 에 일회성 venv(`pip install alembic
psycopg[binary]`)를 만들어 `COLAB_ALEMBIC` 으로 넘겼다. staging 과 무관한 순수 로컬 도구이고
레포에는 아무것도 추가하지 않았다.

```
0004-drift green — ㈎ 적용 green · ㈏ 0004 없으면 red · ㈐ downgrade 실물 동작 + 0003 복원 ·
  ㈑ 기존 격자 1건이면 apply 자체가 가드로 막힌다.

migration-single-head green — 두 체인 모두 head 1개.
rls-coverage green — allow-list 밖 테이블 전부 FORCE RLS + 연구실 경계 정책, 본체 테이블은 본체 정책까지.
rls-effect green — 본체 음성 · 메타 양성(P-13) · cross-tenant 셋 다 엔진이 막는다. 판정 롤은 우회 불가.
db-selftest green — DB 게이트 3종 모두 틀린 것을 틀렸다고 말한다 (fail-closed 증명).
schema-diff green — 두 체인 각각 선언 = 적용.  (일회용 컨테이너에 두 체인 모두 alembic upgrade head 를
  적용한 뒤 COLAB_APPLIED_DB_URL_PLATFORM/COLAB_APPLIED_DB_URL_AI 로 넘겨 확인)
```

회귀 없음. 새 케이스 추가로 `0004-drift.sh` 실행 시간이 컨테이너 1개 재사용 안에서
소폭(추가 DB 1개·마이그레이션 1회) 늘었을 뿐이다.

### L-5. 하지 않은 것

- `0004` 마이그레이션 본체는 고치지 않았다 — 가드가 멀쩡히 작동하는 것을 확인했으므로 고칠 이유가 없었다.
- staging 접속·측정은 하지 않았다(`P2-EXEC` 지시, 위 §A-1 과 동일 사유).
- 커밋하지 않았다.
