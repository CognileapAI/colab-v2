# WU-D3b — RLS 실효 증명의 **게이트 승격** (레인 B3)

> A2 가 `P0-rls-proof.md §⑤-1` 에서 넘긴 자리를 닫는다. 그때는 **테스트**였고 사람이 손으로 돌렸다.
> `PERMISSION-PRINCIPLES §D3 게이트 2종` 과 `WORK-UNITS §6 D3b` 가 요구한 것은 **게이트**다.
>
> 손댄 범위는 `gates/**` · `.github/**` 둘뿐이다. `contracts/` · `db/` · `services/` · `frontend/` 는 **한 글자도 고치지 않았다**
> (I2 레인이 `services/` 를 쓰는 중이라 읽기만 했다). 커밋하지 않았다.

---

## ① `db-selftest` 결함 — 진단은 맞았다

`./gates/run.sh db-selftest` 가 red 였다. 받은 진단이 **정확했다.** 실측으로 확인한 것:

```
[selftest] rls-coverage: 관례를 지킨 기준 facts → red (기대 green) ✗
   - db/ai — allow_no_rls 의 'd9_method_term' 가 실제 스키마에 없다 …
   - db/ai — allow_no_rls 의 'd9_place_alias' …
   - db/ai — allow_no_rls 의 'd9_topic_synonym' …
```

무슨 일이 있었나 —

1. selftest 의 **기준 케이스(baseline-green)** 는 `facts`/`mkschema` 로 **합성 스키마**를 짓는다. 거기엔 `d9_*` 표가 없다.
2. 그런데 판정 코어(`rls_coverage.py`)는 `COLAB_RLS_ALLOWLIST` 가 없으면 **레포 정본**
   `gates/config/rls-allowlist.toml` 을 읽는다.
3. C1(WU-K1)이 `d9_method_term`·`d9_topic_synonym`·`d9_place_alias` 를 `[ai].allow_no_rls` 에 넣었다 —
   **정당하고 옳은 변경**이다(`db/ai/schema.sql` 에 세 표가 실제로 있고, `K1.md §3` 이 면제 근거를 적었다).
4. 「낡은 면제」 검사(목록엔 있는데 스키마엔 없는 표 → red)가 합성 스키마를 상대로 그 세 줄을 걸었다.

**즉 게이트는 옳고, selftest 의 배선이 틀렸다.** 픽스처 케이스가 살아 있는 레포 설정을 읽으면,
누군가 allow-list 를 옳게 고칠 때마다 증명이 깨진다. 게이트가 사람의 정당한 작업에 걸려 넘어지는 구조다.

### 고친 방식 — 픽스처가 자기 allow-list 를 들고 다닌다

`gates/tools/db-selftest.sh` 에 픽스처 allow-list 를 만들어 `COLAB_RLS_ALLOWLIST` 로 못 박았다
(그 override 는 원래 있었고, 케이스 하나만 쓰고 있었다). 이제 픽스처 케이스는 hermetic 이다.

**하지 않은 것 — 여기가 핵심이다.**

- 「낡은 면제」 검사를 **약화하지 않았다.** 이 검사는 이번에 진짜 드리프트를 잡아 자기 값어치를 증명했다.
  검사 대상을 줄여 green 을 만드는 것은 `CLAUDE.md §4` 가 금지한 바로 그 짓이다.
- allow-list 에서 `d9_*` 세 줄을 **지우지 않았다.** 그 줄들은 옳다.
- 레포 정본에 대한 판정은 **게이트 본체**(`./gates/run.sh rls-coverage`)가 본다. selftest 가 볼 자리가 아니었다.
  실제 DB 로 확인 — 조사 21건, **green**(`d9_*` 3표가 「RLS 면제(allow-list)」로 정상 인식된다).

### 다른 selftest 에도 같은 결합이 있는가 — 조사함

| 셋 | 레포 파일을 읽는가 | 판단 |
|---|---|---|
| `contract-selftest` | `contracts/schemas/common.json` · `contracts/.spectral.yaml` 을 픽스처로 **복사**한다 | 🟨 **약한 결합, 이번엔 손대지 않았다.** 규칙 파일(`.spectral.yaml`)과 공통 스키마는 「검사 규칙」이지 「검사 대상 목록」이 아니다. 게다가 `contracts/` 는 **동결**이라(`NIGHT §2-4`) 조용히 바뀌지 않는다. 다만 계약 해동 시 같은 방식으로 터질 수 있는 자리이므로 여기 기록해 둔다 |
| `event-selftest` | `contracts/events` 경로를 읽는다 | 🟨 위와 같다. 동결 대상이라 지금은 위험이 실현되지 않는다 |
| `boundary-selftest` | 레포 설정을 읽지 않는다 | ✅ 결합 없음 |
| `db-selftest` | **읽었다** → 고쳤다 | ✅ |

> 판별 기준: 픽스처가 읽는 것이 **「검사 규칙」이면 결합이 아니고, 「검사 대상의 목록」이면 결합이다.**
> allow-list 는 후자였다 — 대상이 바뀔 때마다 목록이 자란다.

---

## ② 승격한 게이트 — `rls-effect`

| | |
|---|---|
| 이름 | **`rls-effect`** (판정) · **`rls-effect-selftest`** (자기 증명) |
| 파일 | `gates/tools/rls-effect.sh` · `gates/tools/rls-effect-selftest.sh` |
| 배선 | `gates/run.sh` 에 두 케이스 추가 · `selftest` 묶음에 `rls-effect-selftest` 편입 · `.github/workflows/ci.yml` 의 `schema-gates` 잡에 `rls-effect` 추가(다른 DB 게이트 바로 옆) |
| 재료 | A2 가 남긴 것을 **그대로** 쓴다 — `db/platform/schema.sql` · `services/core-api/ops/app-role.sql` · `services/core-api/tests/fixtures/seed.sql`. 게이트가 자기 시드를 따로 들면 시드가 두 벌이 되어 갈라진다 |
| 격리 | 자기 일회용 postgres 를 띄운다. 컨테이너 이름 `b3_rlseffect_<pid>_<rand>` · **포트 publish 0** · PGDATA 는 tmpfs · trap 으로 삭제. `colab_v2_*`(staging 포함)는 건드리지 않는다 |
| 스타일 | `db-selftest.sh` 의 `expect green|red <라벨> <명령>` 을 **그대로** 따랐다. 두 번째 방식을 만들지 않았다 |

`rls-coverage` 와 무엇이 다른가 — **`rls-coverage` 는 「정책이 걸려 있는가」를 보고, `rls-effect` 는 「행이 실제로 안 보이는가」를 본다.**
`USING (true)` 인 정책도 걸려 있기는 하다. 그 구멍이 이 게이트의 존재 이유다.

### 오라클 3종과 각각의 red fixture

red 를 만드는 방법이 가짜 스키마를 짓는 것이 아니라 **진짜 보호 장치를 떼는 것**이라는 점이 이 셋의 성격이다
(A2 의 `red-proof.sh` 와 같은 훼손 목록 — 그때는 사람이, 지금은 게이트가 돌린다).
훼손은 게이트가 띄운 일회용 DB 안에서만 일어나고 `db/` · `services/` 는 바뀌지 않는다.

| 오라클 | 판정 (green 실측) | red fixture |
|---|---|---|
| **① 본체 음성** — 허용자 아님·만료됨 두 경우 본체가 **DB 층에서 0행** | 허용자 아닌 A 교수 → `d3_file(DSA2)` **0행**, 대조로 열린 `DSA1` **2행**. 만료된 허용 줄 넣어도 **0행**, 같은 트랜잭션에 유효한 줄을 더하면 **1행**(그 0 이 「원래 0」이 아님의 증거), 주체만 바꾸면 다시 **0행** | ⓐ `DROP POLICY body_access ON d3_file` ⓑ 정책에서 `expires_at > now()` **만** 제거 ⓒ 둘째 층을 `PERMISSIVE` 로(두 층이 OR 로 무너진다) — **3방향 전부 red** |
| **② 메타 양성** — 잠긴 데이터셋의 **메타는 반드시 조회됨**(P-13) | `d3_dataset`·`_description`(이름)·`_autometa`·`d2_dataset_access(잠김)`·`d2_verified`·`d4_lineage_edge` 전부 조회됨. **구조로도 못 박았다** — `pg_policies` 를 오라클로 삼아 메타 3표는 `lab_boundary:PERMISSIVE` **하나뿐**, `d3_file` 만 두 층이고 둘째 층이 `RESTRICTIVE` | ⓐ `d3_dataset` 에 본체와 같은 조건의 RESTRICTIVE 정책 추가(= 잠김을 RLS 로 통째로 얹는 그 실수) ⓑ 메타 표에 정책 하나 더 추가(행 수로는 안 보인다) — **2방향 전부 red** |
| **③ cross-tenant** — 남의 연구실 0행 | **`lab_id` 를 가진 표 18개 전수**를 훑어 `lab_id <> current_lab_id()` 0행(목록을 손으로 적지 않는다 — 새 표가 생기면 판정도 늘어난다). ID 를 알고 직접 집어도 0행. **GUC 없는 접속 0행**(기본 거부). 반대편 B 로 붙으면 B 것 1행 | ⓐ `lab_boundary ON d3_dataset USING (true)` ⓑ **자식 표에서만** 경계 누락(부모는 멀쩡 — 목록 검사로는 안 잡힌다) ⓒ `current_lab_id()` 의 `ELSE NULL` 을 고정 연구실 ID 로(「기본값을 주자」는 유혹) — **3방향 전부 red** |

인프라 red 도 같이 못 박았다 — 선언 스키마 부재 · 시드 부재 · 앱 롤 부트스트랩 부재 · 적용되지 않는 스키마 ·
**도커 부재**. 전부 skip 이 아니라 red 다. 「검사를 못 했다」를 통과로 세지 않는다.

**`rls-effect-selftest` 결과: 18 케이스 전부 기대대로** (green 1 · red 17).

---

## ③ 잘못된 롤로 돌면 red — 임의 증명

이 게이트에서 가장 무너지기 쉬운 자리다. superuser·소유자로 붙으면 FORCE RLS 가 무력해지고
위 오라클 셋이 **전부 거짓 green** 이 된다. 실측 근거는 `P0-rls-proof §②` — 같은 묶음을 superuser 로 돌리면
**13 failed / 4 passed** 이고, 통과한 4 는 전부 양성 계열이다(「보인다」를 주장하는 시험은 우회 롤에서도 통과한다).

그래서 게이트가 **판정 전에 접속 롤의 성질을 자기 손으로 확인**하고, 틀리면 red 를 낸다. 세 겹이다.

1. `pg_roles` — `rolsuper` · `rolbypassrls` 가 하나라도 `t` 면 red
2. `pg_tables` — 그 롤이 `public` 의 테이블을 하나라도 소유하면 red
3. 판정 세션 **안에서 한 번 더** — `current_user` 가 우회 롤이면 SQL 이 `RAISE EXCEPTION` (docker `-U` 가 무시되는 사고 대비)

실행 결과 —

```
$ COLAB_RLS_EFFECT_ROLE=postgres ./gates/run.sh rls-effect
::error::rls-effect red — 판정 롤 'postgres' 이 RLS 를 우회한다 —
        rolsuper=t · rolbypassrls=t · public 소유 테이블 0개.
   이 롤로 낸 green 은 **아무것도 증명하지 않는다.** …
```

정상 실행에서는 반대로 이 줄이 먼저 찍힌다 —
`# 판정 롤 colab_app — rolsuper=f · rolbypassrls=f · public 소유 테이블 0개 (우회 불가)`

selftest 는 이 자리를 **4방향**으로 건다: superuser 롤 주입 · `ALTER ROLE colab_app BYPASSRLS` ·
`ALTER TABLE d3_file OWNER TO colab_app` · 존재하지 않는 롤. 전부 red 다.

---

## ④ 전 게이트 스윕

`2026-08-23`, 이 레포 워킹트리 기준.

| 게이트 | 결과 |
|---|:--:|
| `planning-freshness` | 🟢 green |
| `contract-lint` | 🟢 green |
| `contract-breaking` | 🟢 green |
| `event-lint` | 🟢 green |
| `event-breaking` | 🟢 green |
| `import-boundary` | 🟢 green |
| `banned-import` | 🟢 green |
| `ai-no-lineage-write` | 🟢 green |
| `migration-single-head` | 🟢 green |
| `rls-coverage` | 🟢 green (조사 21건) |
| **`rls-effect`** (신규) | 🟢 green |
| `contract-selftest` | 🟢 green (15) |
| `event-selftest` | 🟢 green (33) |
| `boundary-selftest` | 🟢 green (30) |
| `db-selftest` | 🟢 green (43 — e2e 포함) |
| **`rls-effect-selftest`** (신규) | 🟢 green (18) |

**red 는 하나도 없다.** 증명 다섯 셋은 **개별로** 돌려 전부 green 이었다.

> **묶음 실행(`./gates/run.sh selftest`) 한 번이 도중에 멈춘 일이 있다 — 게이트 결함이 아니다.**
> `contract-selftest` 의 `oasdiff` 컨테이너가 응답을 멈췄다. 같은 시각 다른 레인(I2 staging 배포)의
> `oasdiff` 컨테이너도 두 시간째 같은 상태로 매달려 있었고, 그 사이 `postgres` 컨테이너는 정상이었다 —
> 즉 도커 데몬이 배포 부하에 눌린 것이지 판정 로직의 문제가 아니다.
> **재실행한 `contract-selftest` 는 green** 이다(위 표). 매달린 컨테이너 중 내 것은 지웠고,
> 다른 레인 것은 건드리지 않았다.

`schema-diff` 와 `generated-up-to-date` 는 이번 스윕 대상이 아니었다 — 전자는 적용 DB URL 두 개를 요구하는
배포 시점 게이트이고(없이 돌리면 **설계대로 red**), 후자는 미구현이라 **설계대로 red** 다(B2 레인의 몫).

---

## ⑤ 이 게이트가 여전히 못 잡는 것

추측으로 메우지 않는다.

1. **HTTP 층은 보지 않는다.** `rls-effect` 는 **DB 층만** 판정한다(순수 SQL — 파이썬 venv·앱 기동에 의존하지 않아
   인프라 사고에 걸려 넘어지지 않는다는 이점과 맞바꾼 것이다). A2 의 HTTP 층 확인(403/404 구분·카탈로그 노출)은
   여전히 `services/core-api/tests/` 의 pytest 에 있고 **게이트가 아니다.** 승격하려면 앱을 띄우는 게이트가 하나 더 필요하다.
2. **시드가 오라클의 일부다.** 판정 숫자(2행·1행·18표)는 `tests/fixtures/seed.sql` 을 전제한다.
   시드가 바뀌면 게이트가 red 를 내는데, 그게 「경계가 깨졌다」인지 「시드가 바뀌었다」인지는 사람이 읽어야 한다.
   대신 시드는 **레포 안 한 벌**이고 `services/` 소유다 — 게이트가 사본을 들지 않은 이유가 그것이다.
3. **`db/ai` 체인은 판정하지 않는다.** D9 는 연구실 공통 지식이라 경계 대상이 아니고(`K1.md §3`),
   RLS 면제의 **근거**가 옳은지는 `rls-coverage` 의 allow-list 가 본다. 이 게이트는 `db/platform` 만 본다.
4. **애플리케이션이 만드는 노출.** RLS 는 **행**을 막는다. 집계·에러 메시지·타이밍으로 남의 연구실 존재를
   알아내는 경로는 범위 밖이다(`P0-rls-proof §⑤-5` 의 `fileCount` 사례가 아직 열려 있다).
5. **동시성·시간.** 만료 판정은 `now()`(트랜잭션 시작 시각) 기준이다. 긴 트랜잭션 안에서 만료가 지나가는 경계는
   시험하지 않았다. 다운로드처럼 오래 붙잡는 경로(P2)가 생기면 다시 봐야 한다.
6. **[정본 미결 — 그대로 남는다]** 잠긴 데이터의 본체를 소유자·교수가 볼 수 있는가(`P0-schema §7-③`).
   게이트는 **지금 스키마가 그렇다**를 고정했을 뿐 「맞다」고 못 박은 것이 아니다. E-06 이 값을 주면
   정책과 이 게이트의 기대값을 **함께** 고쳐야 한다.
7. **남은 흔적 없음.** 일회용 컨테이너는 `b3_rlseffect_*` 뿐이고 포트를 하나도 공개하지 않았으며 매 회 삭제된다.
   `colab_v2_staging_*` 를 포함해 `colab_v2_*` 는 건드리지 않았다.
