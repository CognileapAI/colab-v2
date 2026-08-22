# D3 — DB 게이트 3종 (`migration-single-head` · `schema-diff` · `rls-coverage`)

D3 의 나머지 절반. 경계 게이트 3종은 `sessions/D3-boundary.md` 에 있고, 이 문서는 **DB 쪽 3종과 그 증명**이다.

`db/`·`services/`·`contracts/` 에는 **한 글자도 쓰지 않았다.** 게이트가 검사할 대상을 게이트 세션이 만들면
그 게이트는 자기가 만든 것을 검사하는 셈이 된다 — `D3-boundary.md` 와 같은 판단이다.

**세 게이트는 지금 전부 red 다. 그게 정상이다.** `db/platform`·`db/ai` 에는 README 밖에 없다.
완료 판정은 "게이트 green" 이 아니라 **"red fixture 로 fail-closed 증명"** 이다(`WORK-UNITS.md §6`).

---

## 1. 무엇이 어디에 있는가

| 파일 | 역할 |
|---|---|
| `gates/tools/migration_single_head.py` | head 분기 검출 (표준 라이브러리 `ast` 만. DB·alembic 불필요) |
| `gates/tools/_pg.sh` | **일회용 postgres** 확보. 도커 부재는 skip 이 아니라 red |
| `gates/tools/schema-diff.sh` | 선언 스키마 ↔ 적용 DB 드리프트 |
| `gates/tools/rls-coverage.sh` | 스키마를 실제 엔진에 적용해 카탈로그 사실(facts)을 뽑는다 |
| `gates/tools/rls_coverage.py` | **판정 코어.** facts ↔ allow-list 대조 (도커 불필요) |
| `gates/config/rls-allowlist.toml` | **allow-list 의 유일한 정의처** + 정책 이름 관례 + 본체 테이블 목록 |
| `gates/tools/db-selftest.sh` | 세 게이트의 fail-closed 증명 (38 케이스) |

`gates/run.sh` 에 `migration-single-head` · `schema-diff` · `rls-coverage` · `db-selftest` 를 배선하고,
`selftest` 를 **증명 셋(contract·boundary·db)의 집합체**로 구현했다. 남은 미구현은 `generated-up-to-date` 하나뿐이다.

---

## 2. `migration-single-head` — 도구 선택의 근거

**alembic 을 설치해 쓰지 않는다. `down_revision` 그래프를 `ast` 로 직접 파싱한다.** 이유 셋.

1. **DB 접속 없이 판정 가능해야 한다.** v1 CI 가 DB 없이 돌아 RLS 테스트를 green-by-skip 한 실패의 반대편을
   세우려면, 인프라가 없어도 **항상 실제 판정을 내는 게이트**가 하나는 있어야 한다.
   head 분기는 파일만으로 결정되는 사실이므로 이 게이트가 그 자리다.
2. **alembic 의 head 계산은 마이그레이션 모듈을 import 해서 실행한다.** 게이트가 검사 대상 코드를 실행하면
   검사 대상이 게이트를 좌우할 수 있다(`env.py` 의 side effect, DB 접속 시도). 게이트는 대상을 읽되 실행하지 않는다.
3. `ast` 는 표준 라이브러리다 — `banned-import.py` 와 같은 판단. 핀할 도구가 하나 줄면
   게이트가 조용히 바뀔 경로가 하나 준다. `gates/requirements.txt` 는 손대지 않았다.

**판정 항목** (체인마다 독립으로 — `CLAUDE.md §3-3`)

| red 조건 | 왜 |
|---|---|
| `alembic.ini` 부재 | 체인이 alembic 체인임을 선언하는 자리다 |
| `versions/*.py` 0건 | **대상 0건 = red.** "head 가 하나다"와 "마이그레이션이 없다"는 다른 사실이다 |
| head 2개 이상 | 본래 목적. 어느 쪽을 먼저 적용할지 정해지지 않은 스키마는 스키마가 아니다 |
| head 0개 (순환) | 적용 순서가 없다 |
| `revision` 중복 | 같은 이름 두 개면 그래프가 갈라진다 |
| `down_revision` 이 이 체인에 없는 값 | 고아 참조. **체인을 넘는 참조라면 `§3-3` 위반이다** |
| `revision`·`down_revision` 미선언 / 동적(리터럴 아님) | 정적으로 판정할 수 없는 것을 통과로 세지 않는다 |
| 파싱 불가 | 읽지 못한 파일을 통과로 세지 않는다 |

`down_revision` 이 튜플/리스트인 **머지 리비전은 정상으로 본다** — 분기를 합치는 정규 수단이 그것이다.
selftest 가 "분기 → red, 머지 리비전 추가 → green" 을 둘 다 증명한다.

### `version_table` 중복은 여기서 보지 않는다 — 역할 분담

두 체인이 같은 `version_table` 을 쓰면 red 인데, 그 조건은 **이미 `ai-no-lineage-write` ⑪ 이 본다**
(`D3-boundary.md §5`). 중복 구현하면 한쪽만 고쳐졌을 때 두 게이트가 다른 말을 한다.

| 게이트 | 보는 것 |
|---|---|
| `migration-single-head` | **한 체인 안**의 그래프 형태 — head 개수·중복·고아·순환 |
| `ai-no-lineage-write` ⑪⑫ | **두 체인 사이**의 격리 — `version_table` 동일·미선언, 체인 상호 참조 |

경계는 "안이냐 사이냐" 하나로 갈린다.

---

## 3. `schema-diff` — DB 가 필요한 검사다

비교하는 두 대상: **선언** = `db/<체인>/schema.sql` (SoT) · **적용** = 실제로 마이그레이션이 돌아간 DB.

판정 경로 — 선언 `schema.sql` 을 **일회용 postgres** 에 적용해 `pg_dump --schema-only` 하고,
적용 DB 도 같은 방식으로 덤프해 정규화 후 `diff`. 차이가 한 줄이라도 있으면 red.

정규화는 **스키마와 무관한 줄만** 걷어낸다(주석·`SET`·`set_config`·빈 줄·`\restrict`/`\unrestrict` 난수 토큰).
정규화를 늘릴수록 검사 대상이 줄어든다 — 게이트를 green 으로 만들려고 대상을 줄이는 짓과 같아진다(`CLAUDE.md §4`).

### DB 가 없을 때: skip 이 아니라 red

`COLAB_APPLIED_DB_URL` 이 없으면 red. 접속 실패도 red. 도커가 없어 일회용 postgres 를 못 띄워도 red.
**여기서 skip 하는 것이 정확히 v1 의 실패다** — 없는 검사는 통과가 아니다.

### CI 에서 실제로 판정하게 하는 경로 (설계)

이 호스트에서 도커로 postgres 를 띄우는 경로를 **실제로 시도해 통과시켰다**(selftest §5 의 e2e 2케이스).
CI 도 같은 형태다.

1. postgres 서비스 컨테이너를 띄운다 (`postgres:16-alpine`).
2. `db/platform` · `db/ai` 를 각각 `alembic upgrade head` 로 적용한다 — **적용 DB 를 만드는 것은 게이트의 일이 아니라
   파이프라인의 일이다.** 게이트가 마이그레이션을 돌리면 게이트가 alembic 에 묶이고, 2번 이유(대상 실행)가 되살아난다.
3. 그 DB 의 URL 을 `COLAB_APPLIED_DB_URL` 로 넘겨 `gates/run.sh schema-diff` 를 돌린다.

**이 호스트의 staging 컨테이너(`colab_v2_staging_*`)는 건드리지 않는다.** `_pg.sh` 는
① 이름을 `colab_v2_gatepg_<pid>_<rand>` 로 짓고 ② **포트를 하나도 publish 하지 않으며**(모든 질의가 `docker exec`
로 컨테이너 안에서 돈다 → 포트 충돌이 원천적으로 없다) ③ `PGDATA` 를 tmpfs 에 두고(호스트에 아무것도 남기지 않고,
WSL 바인드 마운트의 `chmod` 제약도 피한다) ④ `trap` 으로 반드시 지운다.
게이트 스크립트가 `exec` 로 끝나지 않는 것도 이 때문이다 — `exec` 하면 `trap` 이 돌지 않아 컨테이너가 남는다.

---

## 4. `rls-coverage` — 이 프로젝트의 핵심 보험

강제하는 것: `CLAUDE.md §3-5`(모든 조회에 연구실 경계가 자동 주입된다) ·
`PLAN-SoT §9-㉖` / `PERMISSION-PRINCIPLES P-34`(잠금 두 층 — 경계도 RLS, **파일 본체도 RLS**).

**선언 스키마를 실제 postgres 엔진에 적용해 카탈로그를 본다.** grep 이 아니다. 이유가 selftest 로 증명돼 있다 —
`ALTER TABLE … NO FORCE ROW LEVEL SECURITY` 가 파일 **뒤쪽**에 한 줄 있으면 앞의 `FORCE` 는 무효인데,
텍스트 검사는 그것을 보지 못한다. 카탈로그(`pg_class.relforcerowsecurity`)는 본다.

적용 DB 가 아니라 선언 스키마를 대상으로 보는 이유: RLS 는 스키마의 성질이고, 선언과 적용이 갈라졌는지는
`schema-diff` 의 일이다. **두 게이트가 같은 사실을 두 번 보지 않는다.**

### 판정 규칙 (정본 = `gates/config/rls-allowlist.toml` 하나뿐)

| red 조건 |
|---|
| allow-list 밖 테이블에 RLS 가 꺼져 있다 |
| RLS 는 켰는데 **FORCE 가 아니다** — 테이블 소유자로 접속하면 정책이 통째로 무시된다. ENABLE 만으로는 경계가 아니다 |
| 연구실 경계 정책(`lab_boundary`)이 없다 — `§3-5` |
| **본체 테이블**(`d3_file` · `d7_viz_source`)에 본체 정책(`body_access`)이 없다 — `㉖ ③` · `P-34` |
| allow-list 에 적었으나 실제 스키마에 없는 **낡은 면제** — 같은 이름의 테이블이 생기는 순간 조용한 구멍이 된다 |
| 어느 체인이든 테이블 0건 |
| facts 형식 오류 · allow-list 설정 부재 |

allow-list 초기값은 참조·전역 테이블만 둘씩이다(`alembic_version_*`, `d1_lab` — 테넌트 루트는 자기가 경계다).
D9 온톨로지 테이블은 이름이 아직 없으므로 **비워 뒀다** — 비어 있다는 것은 "ai 체인의 모든 테이블에 RLS 를 요구한다"는
fail-closed 기본값이다. 접두사 면제는 넣지 않았다. 접두사는 나중에 아무 테이블이나 숨는 문이 된다.

### 판정 코어를 파이썬으로 떼어 놓은 이유

`rls_coverage.py` 는 TSV facts 만 받는다. **판정 로직 자체의 증명이 도커 사고에 걸려 넘어지면 안 되기 때문이다.**
selftest 는 합성 facts 로 판정 코어를 직접 때리고(11 케이스), 별도로 도커 e2e 를 돌린다(7 케이스).

---

## 5. `db-selftest` 가 증명하는 것 — 38 케이스

`./gates/run.sh db-selftest` (전부 green = 세 게이트가 fail-closed). fixture 는 전부 `mktemp -d` 아래이며
실제 `db/`·`services/`·`contracts/` 는 건드리지 않는다. 주입은 환경변수
(`COLAB_DB_DIR` · `COLAB_RLS_ALLOWLIST` · `COLAB_APPLIED_DB_URL` · `COLAB_PG_IMAGE` · `COLAB_PG_FORCE_UNAVAILABLE`) —
`boundary-selftest`·`contract-selftest` 와 같은 형태다.

| 게이트 | 케이스 | 기대 |
|---|---|---|
| migration-single-head | 두 체인 선형 / 머지 리비전으로 합친 분기 | green ×2 |
| | platform head 2개 · ai head 2개 · 체인 넘는 참조 · revision 중복 · 순환 · ini 부재 · 마이그레이션 0건 · 체인 부재 · 파싱 불가 · 동적 revision · down 미선언 | red ×11 |
| rls-coverage (판정 코어) | 관례를 지킨 기준 facts | green |
| | RLS 없음 · FORCE 없음 · 정책 0건 · 경계 정책 이름 없음 · 본체 정책 누락 · 체인 테이블 0건 · 전체 0건 · 낡은 면제 · 형식 오류 · facts 부재 · 설정 부재 | red ×11 |
| rls-coverage (e2e, 도커) | 관례대로 만든 스키마 | green |
| | RLS 없는 새 테이블 · FORCE 누락 · **뒤에서 NO FORCE** · schema.sql 0건 · 적용 안 되는 SQL · 도커 부재 | red ×6 |
| schema-diff | **선언 = 적용** (실제 postgres 2대를 띄워 확인) | green |
| | 적용 DB 에만 있는 컬럼(드리프트) · 선언 0건 · 적용 DB 미지정 · 접속 불가 · 도커 부재 | red ×5 |

**green 케이스가 있어야 증명이 성립한다.** 전부 red 를 내는 게이트는 fail-closed 가 아니라 그냥 고장이다.

### `boundary-selftest` 에 합치지 않은 이유

경계 게이트는 파이썬 venv 에, DB 게이트는 **도커**에 의존한다. 합치면 도커 없는 환경에서 경계 증명까지 같이 죽는다 —
증명은 서로의 인프라 사고에 걸려 넘어지면 안 된다(`D3-boundary.md §1` 이 계약/경계를 나눈 것과 같은 근거).

**같은 근거를 이 파일 안에도 적용했다.** `migration-single-head` 는 외부 의존이 0인데 그 증명을 도커 뒤에 두면
정확히 그 안티패턴이다. 그래서 `COLAB_DB_SELFTEST_ONLY` 로 섹션을 쪼갤 수 있게 했다 —
`migration`(도커 불필요: 24 케이스) · `db`(도커 필요: 14 케이스) · 기본값 `all`.

---

## 6. 지금의 실행 결과와 그 근거

| 게이트 | 지금 | 이유 |
|---|---|---|
| `migration-single-head` | 🔴 red | 두 체인 모두 `alembic.ini` 부재 · `versions/*.py` 0건 |
| `schema-diff` | 🔴 red | `db/<체인>/schema.sql` · `versions/` 0건 (적용 DB 이전 단계에서 멈춘다) |
| `rls-coverage` | 🔴 red | `db/<체인>/schema.sql` 0건 |
| `db-selftest` | 🟢 green | 38 케이스 전부 의도대로 |
| `planning-freshness` · `contract-lint` · `boundary-selftest` · `contract-selftest` | 🟢 green | 기존 게이트를 깨지 않았음을 확인 |

**red 3개는 버그가 아니라 설계다**(`CLAUDE.md §4`). P0 가 `db/<체인>/{alembic.ini, versions/, schema.sql}` 을 놓고
CI 가 적용 DB 를 넘기는 순간 셋 다 green 으로 돌아설 수 있다 — 그 전환이 이 게이트들의 인수 시험이다.

**P0 가 맞춰야 할 관례** — ① 체인마다 `alembic.ini`(`version_table` 을 서로 다르게 명시) ·
`versions/*.py`(`revision`·`down_revision` 은 리터럴) · `schema.sql`(선언 SoT) ② RLS 정책 이름은
`lab_boundary` · `body_access` ③ 면제가 필요한 테이블은 `gates/config/rls-allowlist.toml` 에만 적는다.

---

## 7. 남은 한계 (다음이 알아야 할 것)

1. **`schema-diff` 는 적용 DB 를 한 URL 로 본다.** 체인이 둘인데 적용 DB 가 하나면 두 체인 스키마가 한 DB 에
   있다고 가정하게 된다. 체인별로 DB 를 분리해 배포한다면 URL 도 체인별로 받도록 고쳐야 한다
   (`COLAB_APPLIED_DB_URL_PLATFORM` 식). **배포 형태가 정해지는 WU 에서 정한다.**
2. **마이그레이션 ↔ `schema.sql` 의 동치는 아무도 안 본다.** `schema-diff` 는 선언 ↔ 적용 DB 만 본다.
   "마이그레이션을 다 돌린 결과 = `schema.sql`" 은 CI 가 적용 DB 를 alembic 으로 만들 때 **자동으로 같이 증명된다** —
   그 파이프라인을 만드는 것이 남은 일이다(§3 의 3단계). 파이프라인 없이 손으로 만든 적용 DB 를 물리면 이 성질은 없다.
3. **DB 없이 판정 못 하는 것** — RLS 실효(FORCE 포함), 정책 존재, 스키마 드리프트 셋 다.
   그래서 이 셋은 도커/DB 부재를 red 로 못 박았다. 판정 못 하는 것을 통과로 세는 순간 v1 이 된다.
4. **RLS 정책의 *내용* 은 보지 않는다.** `lab_boundary` 라는 이름의 정책이 걸렸는지까지만 본다.
   `USING (true)` 인 가짜 정책은 이 게이트를 통과한다. `㉖`·`P-34` 가 요구하는 **실효 증명**(허용자 아님·만료됨에
   대해 본체 조회가 0행 · 잠긴 데이터셋 메타는 조회됨)은 **음성/양성 테스트의 몫**이고, 그 테스트는 아직 없다.
   커버리지 게이트는 "정책이 있는가", 테스트는 "정책이 맞는가" — 둘 다 있어야 `§3-5` 가 성립한다.
   **이것이 D3 에 남은 가장 큰 구멍이다.**
5. **만료일은 스키마로 강제되는지 확인하지 않는다.** `body_access` 정책이 만료일을 실제로 보는지는 4번과 같은 이유로
   테스트의 몫이다.
6. **`migration-single-head` 는 alembic 이 아니다.** `branch_labels` 로 의도적으로 연 분기, `depends_on` 을 쓴
   그래프는 alembic 과 다르게 볼 수 있다. v2 는 체인마다 single-head 를 강제하므로 둘 다 쓸 일이 없지만,
   쓰기 시작하면 이 게이트를 먼저 고쳐야 한다.
7. **뷰·파티션 부모·물리적으로 상속된 테이블은 RLS 검사 대상이 아니다**(`relkind='r'` 만 본다).
   파티션 테이블을 도입하면 자식 파티션의 RLS 를 따로 봐야 한다.
