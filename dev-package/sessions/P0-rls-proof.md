# WU-P0 산출물 #2 — 스코프 커널 음성 4종 · `body_access` 실효 2종 (레인 A2)

> P0 의 마지막 조각. **경계가 실제로 막는지**를 red→green 으로 증명한 기록이다.
> `P0.md §5` 완료 판정 **#4**(cross-tenant 음성 4종)와, `P0-schema.md §4` 가 「P0 의 다음 조각」으로
> 남긴 **`body_access` 음성/양성 2종**(`PLAN-SoT §9-㉖` · `PERMISSION-PRINCIPLES §D3 게이트 2종`)을 함께 닫는다.
>
> `gates/` · `contracts/` · `db/` · `frontend/` 는 **한 글자도 고치지 않았다.** 산출은 전부 `services/core-api/tests/` 안이다.

---

## ① 무엇을 증명했는가 — 6종

각 줄은 **훼손 → red → 원복 → green** 을 실제로 돌린 결과다. 훼손은 일회용 DB 안에서만 일어난다.
재실행: `CONTAINER=a2_pg services/core-api/tests/fixtures/red-proof.sh`

| # | 케이스 | 무엇을 막는가 | red 만드는 법 (실행함) | 결과 |
|:--:|---|---|---|:--:|
| 1 | **읽기** | 다른 연구실 행이 아예 보이지 않는다. 경계 테이블 **18개 전부**를 훑어 `lab_id = 남의 연구실` 행이 0인지 본다 | `ALTER POLICY lab_boundary ON d3_dataset USING (true) WITH CHECK (true)` — 스코프 한 줄 누락(`P0.md §6` 의 함정 그대로) | 🟢 red→green |
| 2 | **자식** | 남의 데이터셋 **ID 를 알고 있어도** 그 자식·부속 행(파일·설명·자동메타·프로젝트 연결·계정·역할·계보)이 0행. 조인으로 우회해도 같다 | `ALTER POLICY lab_boundary ON d3_dataset_description USING (true) WITH CHECK (true)` — 부모는 그대로 두고 **자식에서만** 경계를 빠뜨린 형태. 목록 테스트로는 안 잡힌다 | 🟢 red→green |
| 3 | **미스코프** | GUC 를 **세팅하지 않은 접속은 한 행도 못 본다**(기본 거부 — `P0-schema §4` 설계판단 3). 정규 ID 가 아닌 GUC 도 같다 | `current_lab_id()` 의 `ELSE NULL` 을 고정 연구실 ID 로 바꾼다 — 「기본값을 주자」는 유혹. 그 순간 미스코프가 전체 열람이 된다 | 🟢 red→green |
| 4 | **쓰기 (WITH CHECK)** | 남의 `lab_id` 를 써 넣는 경로가 없다. INSERT 3종(`d6_project`·`d1_account`·`d8_activity`) + 자기 행을 남의 연구실로 **옮기는** UPDATE | `ALTER POLICY lab_boundary ON d6_project USING (lab_id = current_lab_id()) WITH CHECK (true)` — 읽지는 못하는데 **쓸 수는 있는** 구멍 | 🟢 red→green |
| 5 | **본체 음성** | 허용자 목록에 **없는 사람**, 그리고 **만료된** 허용 줄 → 파일 본체가 **DB 층에서 0행** | ⓐ `DROP POLICY body_access ON d3_file` ⓑ 정책에서 `g.expires_at > now()` **만** 제거 — 만료 검사만 빠뜨린 형태 | 🟢 red→green (2방향) |
| 6 | **메타 양성** | **잠긴 데이터셋의 메타는 반드시 조회된다** (`P-13`). 이름·주제·자동메타·접근상태·Verified·계보까지 | `d3_dataset` 에 본체와 같은 조건의 RESTRICTIVE 정책을 하나 더 건다 = 「잠김을 RLS 로 통째로 얹는」 그 실수(`P-34` 가 금지한 형태) | 🟢 red→green |

실행 요약 — **red 증명 9회 전부 기대대로 red**, 훼손 없는 DB 에서 **pytest 106 passed**
(A1 이 남긴 86 + A2 가 더한 20).

**5번에는 대조 항이 하나 더 있다.** 만료 줄만 있을 때 0행인 것을 본 뒤, **같은 트랜잭션에서 유효한 줄을
하나 더 넣어 1행이 되는 것**까지 확인한다. 그래야 그 0 이 「원래 0이라 0」이 아니라 **정책이 만든 0**이다.
이어서 같은 트랜잭션에서 주체만 바꿔 다시 0이 되는 것도 본다 — 허용은 **사람마다** 다르다.

**6번은 구조로도 못 박았다.** 행 개수만 보는 시험은 시드가 마침 열려 있으면 통과해 버린다.
그래서 `pg_policies` 자체를 오라클로 삼아 ⓐ `d3_dataset`·`_description`·`_autometa` 에는
`lab_boundary`(PERMISSIVE) **하나뿐**이고 ⓑ `d3_file` 만 두 층이며 두 번째 층이 **RESTRICTIVE** 임을 고정했다.
앞으로 어떤 시드가 와도 `P-13` 회귀는 이 줄에서 잡힌다.

### 만든 파일

| 경로 | 무엇 |
|---|---|
| `services/core-api/tests/test_cross_tenant.py` | 음성 4종 (11 케이스). DB 층 + HTTP 층 |
| `services/core-api/tests/test_body_access.py` | 본체 음성 2방향 · 메타 양성 3종 (6 케이스) |
| `services/core-api/tests/test_pool_no_leak.py` | `SET LOCAL` 누수 없음 + **탐지기 자신에 대한 시험** (3 케이스) |
| `services/core-api/tests/fixtures/seed.sql` | 두 연구실 시드. A1 이 임시로 쓰고 남기지 않은 자리를 레포 안으로 들였다 |
| `services/core-api/tests/fixtures/subjects.json` | 심어 둔 토큰 표 (`P-17`) |
| `services/core-api/tests/fixtures/setup-db.sh` | 일회용 DB 구성 — 소유자로 스키마 적용 → `ops/app-role.sql` → superuser 로 시드 |
| `services/core-api/tests/fixtures/red-proof.sh` | **red 증명 자동화 9회.** 이 문서 ①의 「red 만드는 법」이 곧 이 스크립트다 |
| `services/core-api/tests/conftest.py` | 공용 픽스처(`session_factory`·`live_client`·`scoped_ro`) 추가. 기존 내용은 그대로 |

> **시드를 레포에 들인 이유.** A1 의 `test_live_endpoints.py` 는 시드를 전제하는데 그 시드가 레포에 없었다
> (`P0-core-api.md §1` 목록에도 빠져 있다). 재현할 수 없는 오라클은 오라클이 아니다.
> 이 시드로 A1 의 86 케이스가 **한 줄도 안 고치고 전부 green** 이 되는 것을 먼저 확인한 뒤 A2 를 얹었다.

---

## ② 앱 롤이 NOBYPASSRLS · 비소유자임의 실물 확인

**이 확인이 이 WU 에서 가장 무너지기 쉬운 자리다.** 소유자나 superuser 로 테스트를 돌리면 FORCE RLS 가
무력해지고 위 6종의 green 이 **전부 거짓**이 된다.

실측 (`ops/app-role.sql` 로 만든 롤, 일회용 DB):

| 확인 | 값 |
|---|---|
| `pg_roles` — `colab_app` | `rolsuper=f` · `rolbypassrls=f` · `rolcreatedb=f` · `rolcreaterole=f` |
| `pg_tables` 소유자 | `public` 20개 **전부 `colab_owner`** — `colab_app` 소유 **0건** |
| `has_schema_privilege('colab_app','public','CREATE')` | `f` — 앱은 스키마를 바꿀 수 없다 |
| FORCE RLS 켜진 테이블 | **18개** = 경계 테이블 전부 (`d1_lab`·`alembic_version_*` 3건은 면제) |

세 성질은 **테스트 안에서도 매번 다시 본다** — `test_cross_tenant.py::test_the_app_role_cannot_bypass_anything`
(그리고 A1 의 `test_scope_kernel.py` 와 이중으로). 롤 성질이 바뀌면 음성이 조용히 거짓 green 이 되는 대신 red 가 난다.

**거짓 green 이 실제로 어떤 모습인지도 돌려서 확인했다.** 같은 테스트 묶음을 **superuser 롤**로 붙여 돌리면
**13 failed / 4 passed** 다. 실패한 13 이 음성 전부이고, 통과한 4 는 양성 계열이다 —
양성은 「보인다」를 주장하므로 우회 롤에서도 통과한다. 즉 **거짓 green 을 잡아 주는 것은 음성 쪽뿐이고,
그래서 롤 성질 확인이 별도 오라클로 서 있어야 한다.**

---

## ③ `SET LOCAL` 이 풀 커넥션을 타고 새지 않는다

A1 이 그렇게 지었다는 사실만으로는 증명이 아니다. `test_pool_no_leak.py` 는

1. **커넥션 하나짜리 풀**(`pool_size=1, max_overflow=0`)을 만들어 요청 A 와 B 가 반드시 같은 백엔드를 잡게 하고,
   `pg_backend_pid()` 가 같은지 **먼저 확인한다** — 다르면 「증명하려는 상황이 아니다」로 red 를 낸다.
2. 요청 A(연구실 A, 2건) → 요청 B-1(**GUC 미설정**) → `current_lab_id()` NULL · `d3_dataset` **0행**
   → 요청 B-2(연구실 B) → **B 의 1건만**.
3. HTTP 층에서도 같은 순서로 확인한다 — `a1-prof` → `b1-prof` → `a1-prof`, 그리고 **401 로 끝난 요청 뒤**에도
   다음 요청이 온전한지 본다(트랜잭션이 열리지 않은 경로가 커넥션 상태를 남기지 않는지).
4. **탐지기 자신에 대한 시험** — 같은 순서를 비-LOCAL `set_config(..., false)` 로 돌리면
   다음 세션이 `current_lab_id() = 연구실 A` 를 물려받고 2행을 본다. 이것이 green 이라는 것이
   「위 테스트가 누수를 잡을 수 있다」는 증명이다. 여기가 통과하지 않으면 3번의 green 은 아무 말도 하지 않는다.

**결과: 누수 없음.** 4번의 대조군에서는 실제로 샌다 — 즉 이 시험은 눈을 뜨고 있다.

---

## ④ HTTP 층까지 덮은 것과 DB 층에만 있는 것

`A1` 이 고른 **실질의 5**(`getCurrentAccount`·`getLab`·`listDatasets`·`listDatasetFiles`·`createProject`)가
HTTP 층에서 닿는 범위다.

| 케이스 | DB 층 | HTTP 층 | HTTP 층에서 무엇으로 |
|---|:--:|:--:|---|
| ① 읽기 | ✅ 18 테이블 전수 | ✅ | `listDatasets` 가 자기 연구실만 · 남의 데이터셋 파일은 **404**(존재를 알리지 않는다 — `P-9`·`P-10`) |
| ② 자식 | ✅ 8종 + 조인 | 🟨 부분 | `listDatasetFiles` 404 로 간접 확인. 나머지 자식 테이블은 노출 엔드포인트가 아직 없다 |
| ③ 미스코프 | ✅ 18 테이블 + 비정규 GUC 4종 | ⛔ 없음 | **HTTP 에는 미스코프 경로가 존재하지 않는다** — 인증 없는 요청은 401 이라 트랜잭션 자체가 안 열린다. 그것이 정상이다 |
| ④ 쓰기 | ✅ INSERT 3 + UPDATE 1 | ✅ | `createProject` — `labId` 를 실어 보내면 **400**(계약에 없는 필드), 정상 생성분은 반드시 자기 `lab_id` |
| ⑤ 본체 음성 | ✅ | ✅ | 잠긴 데이터셋 파일 목록 **403**(404 아님 — 존재는 인정하고 접근만 막는다) |
| ⑥ 메타 양성 | ✅ + 정책 목록 | ✅ | `listDatasets` 에 잠긴 데이터셋이 **이름·주제와 함께** 서고 `accessState=잠김`·`bodyAccessible=false` |

**DB 층에만 있는 것**은 ③의 대부분과 ②의 나머지다. 둘 다 「그 경로를 HTTP 로 열지 않았기 때문」이고,
P1 이 엔드포인트를 늘릴 때 같은 케이스를 HTTP 층으로 승격하면 된다.

---

## ⑤ 이 증명이 여전히 못 잡는 것

추측으로 메우지 않았다. 아래는 전부 다음 사람이 판단해야 한다.

1. **[D3b 로 넘긴다] 이건 테스트지 게이트가 아니다.**
   `red-proof.sh` 는 사람이 손으로 돌린다. `gates/` 수정이 이 작업의 금지 범위라 **게이트로 승격하지 않았다.**
   `PERMISSION-PRINCIPLES §D3 게이트 2종` 이 요구한 것은 「게이트」이므로, **B3(D3b)이 이 두 시험을
   `gates/run.sh` 에 걸고 red fixture 로 fail-closed 를 증명하는 일**이 남는다. 재료(시드·훼손 SQL·테스트)는 전부 여기 있다.

2. **[구조적 한계] 양성 시험은 우회 롤을 잡지 못한다.**
   ②에서 실측한 대로 superuser 로 돌리면 양성 4건은 그대로 통과한다. 「보인다」를 주장하는 시험의 성질이다.
   그래서 롤 성질 확인이 **별도 오라클**로 서 있어야 하고, 그 줄이 지워지면 이 문서의 증명 전체가 무너진다.

3. **[못 잡음] 새로 생기는 테이블.**
   `TENANT_TABLES` 는 지금의 18개를 **손으로 적은 목록**이다. P2·P3 가 D5·D7 테이블을 더하면서 정책을
   빠뜨려도 이 테스트는 조용히 통과한다. 그 자리를 막는 것은 `rls-coverage` 게이트(allow-list 밖 테이블에
   RLS+FORCE+정책 누락 시 red)이고, **완료 판정 #5 는 그 게이트의 몫**이다 — 이 문서가 아니다.

4. **[정본 미결 — 그대로 남는다] 잠긴 데이터의 본체를 소유자·교수가 볼 수 있는가.**
   `P0-schema.md §7-③` 이 이미 올린 물음이고, 여기서도 답하지 않았다. 시험은 **정본에 적힌 것만**
   고정했다 — 열림이거나, 만료되지 않은 허용 줄. 그 결과 **자기가 올린 데이터를 잠그면 소유자 본인도
   본체를 못 받는다.** 이 시험들은 그 형태를 「맞다」고 못 박은 것이 아니라 **지금 스키마가 그렇다**를 고정한 것이다.
   E-06 이 값을 주면 정책과 이 테스트를 함께 고쳐야 한다.

5. **[못 잡음] 애플리케이션이 만드는 노출.**
   RLS 는 **행**을 막는다. 집계·에러 메시지·타이밍으로 남의 연구실 존재를 알아내는 경로는 이 시험의 범위 밖이다.
   `fileCount` 가 잠긴 데이터셋에서 0으로 내려가는 것(`P0-core-api.md §5-1`)이 그 부류의 실물 사례이고, 아직 열려 있다.

6. **[못 잡음] 동시성·시간.**
   만료 판정은 `now()`(트랜잭션 시작 시각) 기준이다. 긴 트랜잭션 안에서 만료가 지나가는 경계는 시험하지 않았다.
   P0 범위에서는 문제가 되지 않지만, 다운로드처럼 오래 붙잡는 경로(P2)가 생기면 다시 봐야 한다.

7. **[남은 흔적 없음]** 일회용 postgres 는 `a2_pg` **하나**였고 **포트를 하나도 공개하지 않았으며**(컨테이너 IP 로만 접속)
   작업 뒤 삭제했다. 다른 레인의 `a1_`·`b1_`·`c1_`·`c2_`·`d1_` 컨테이너와 staging 두 컨테이너는 건드리지 않았다.
   `https://www.colab-hydro.com/healthz` = **200**(작업 종료 시각 확인).

---

## ⑥ P0 완료 판정과의 대응

| # | 판정 | 지금 |
|:--:|---|---|
| **4** | cross-tenant 음성 테스트 — 읽기·자식·미스코프·쓰기 4종 **red→green** | ✅ **충족.** ① 표 1~4 행. red 증명은 `red-proof.sh` 로 재현된다 |
| **5** | RLS 커버리지 게이트 — allow-list 밖 테이블에 RLS+FORCE+정책 누락 시 red | ✅ **충족(기존분).** 게이트는 `P0-schema §5` 에서 green(조사 21건)이고, fail-closed 는 `gates/tools/db-selftest.sh` 가 red fixture **11종**으로 이미 증명한다 — RLS 없음 · ENABLE 만 · 정책 0건 · 경계 정책 이름 없음 · 본체 정책 누락(`P-34 ③`) · 테이블 0건(green-by-skip 금지) · 낡은 면제 등. **A2 는 이 게이트를 건드리지 않았다**(`gates/` 는 금지 범위) — 이 문서가 더한 것은 판정 #4 와 ㉖ 다 |
| ㉖ | `body_access` 음성/양성 2종 (`P0-schema §4` 가 남긴 「다음 조각」) | ✅ **닫았다.** ① 표 5~6 행. **게이트 승격만 D3b 로 남는다**(⑤-1) |
