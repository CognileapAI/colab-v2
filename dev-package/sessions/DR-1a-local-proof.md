# DR-1a 로컬 증명 — `ops/reset_dev_environment.py` 스키마 재생성

- 목적 = 라운드 `dev-package/prd/rounds/R-DEV-RESET.md` §11 의 `DROP SCHEMA` `[미확인]` 을 닫는다.
- 판정 3종(라운드 WU-R1a 「로컬 증명」) = `schema-diff` green ＋ `deploy_doctor` ⑥⑦⑧⑨ 로직 green ＋ 픽스처 행 0.
- ⛔ **dev 실환경에 대고 돌리지 않았다.** 전부 일회용 컨테이너 안이다. AWS 호출 0건.
- 일시 = 2026-09-13 · 레인 `lane/wu-r1a-reset-tool`.

---

## 0. 시험 RED 증거 (구현 전)

새 시험 파일 `services/core-api/tests/test_reset_dev_environment_guard.py` 를 먼저 쓰고 돌렸다.

| 단계 | 명령 | 결과 |
|---|---|---|
| ㄱ | `.venv/bin/python -m pytest tests/test_reset_dev_environment_guard.py -q` (도구 파일 부재) | `FileNotFoundError: … ops/reset_dev_environment.py` · `1 error during collection` |
| ㄴ | 같은 명령 (도구를 `NotImplementedError` 뼈대로 둔 뒤) | **`24 failed in 6.05s`** · 전건 `NotImplementedError` |
| ㄷ | 같은 명령 (구현 뒤) | `24 passed` |
| ㄹ | `-k public_스키마_주석` (§4 결함의 회귀 시험을 먼저 추가) | `1 failed` — `assert "comment on schema public is 'standard public schema'" in "select ns…"` |
| ㅁ | 같은 명령 (DDL 보정 뒤) | `25 passed in 1.77s` |

ㄴ 의 축자 한 줄 —

    FAILED tests/test_reset_dev_environment_guard.py::test_플래그가_없으면_거부한다 - NotImplementedError

⚠ ㄱ·ㄴ 은 `COLAB_CORE_TEST_DATABASE_URL` 을 더미로 주고 돌렸다. `tests/conftest.py:347` 의 autouse
픽스처가 `session_factory` 를 인자로 받아 DB 없는 시험도 setup 에서 멈추기 때문이다(게이트 실행에서는
`gates/run.sh` 가 시험 환경을 스스로 source 하므로 이 자리가 문제되지 않는다).

---

## 1. 준비 — 일회용 postgres

호스트 포트를 하나도 공개하지 않고 `PGDATA` 를 tmpfs 에 둔다(`dev-package/RESTART.md` 「이 호스트에서는
`--tmpfs` ＋ `PGDATA` 를 반드시 준다」). 이름에 `-dev` 를 넣는다 — 도구의 dev 식별자 ⓒ 가 **호스트**를 본다.

```bash
docker network create colab_r1a_net
docker run -d --rm --name colab-v2-dev-pg --network colab_r1a_net \
  --tmpfs /pgdata:uid=70,gid=70 -e PGDATA=/pgdata/db \
  -e POSTGRES_PASSWORD=<임의값> -e POSTGRES_HOST_AUTH_METHOD=trust postgres:16-alpine
```

| 확인 | 출력 |
|---|---|
| `docker exec colab-v2-dev-pg pg_isready -U postgres` | `/var/run/postgresql:5432 - accepting connections` |
| 초기화 완료 표식 수 | `1` |

접속 문자열은 0600 파일 2개로만 둔다(`platform.url`·`ai.url`). 표기는 **`postgresql+psycopg://`** 다 —
`postgresql://` 로 두면 alembic 이 psycopg2 를 찾다 `ModuleNotFoundError: No module named 'psycopg2'` 로 죽는다.

---

## 2. 부트스트랩 · 마이그레이션 · 권한

| # | 명령 | 출력 요지 |
|---|---|---|
| ① | `PG_CONTAINER=colab-v2-dev-pg COLAB_OWNER_PASSWORD=… COLAB_APP_PASSWORD=… COLAB_AI_APP_PASSWORD=… bash infra/staging/db-bootstrap.sh roles` | `roles/databases: ok` |
| ② | `docker build -f infra/dev/migrator/Dockerfile -t colab-v2/migrator:r1a-proof .` | 성공(exit 0) |
| ③ | `docker run --rm --network colab_r1a_net -e COLAB_PLATFORM_DB_URL_FILE=/s/platform.url … -w /chain/platform colab-v2/migrator:r1a-proof upgrade head` | `alembic_version_platform = 0031_search_evidence` |
| ④ | 같은 모양으로 `-w /chain/ai` ＋ `COLAB_AI_DB_URL_FILE` | `alembic_version_ai = 0007_merge_vocab_and_category` |
| ⑤ | `bash infra/staging/db-bootstrap.sh app-grants` | `app role grants: ok (colab_app@platform · colab_ai_app@ai · SELECT only)` |
| ⑥ | `bash infra/staging/db-bootstrap.sh account-admin` | `account admin role: ok` |

③④ 의 head 값은 라운드 §4 「실측 근거」의 두 파일과 일치한다. ai 는 **파일 이름**이
`0007_merge_topic_vocab_and_rc7_category.py` 이고 **리비전 id** 가 `0007_merge_vocab_and_category` 다
(같은 파일 62행). 두 값이 달라 보이는 것은 표기 차이이고 어긋남이 아니다.

### `pg_trgm` — `[미확인 — G6]` 에 대한 로컬 실측

| 시점 | 질의 | 값 |
|---|---|---|
| 첫 `upgrade head` 뒤 | `select extname, rolname, nspname …` | `pg_trgm / colab_owner / public` |
| 도구 실행 직후 | `select count(*) from pg_extension where extname='pg_trgm'` | `0` |
| 재-`upgrade head` 뒤(`extensions` 단계 **없이**) | 같은 질의 | `1` · 소유자 `colab_owner` |

⭑ **소유자 롤(`NOSUPERUSER`)이 `CREATE EXTENSION pg_trgm` 을 낼 수 있다** — PostgreSQL 16 로컬 실측.
체인 안의 `CREATE EXTENSION IF NOT EXISTS pg_trgm` 이 그대로 통과했고 `infra/dev/db-bootstrap.sh extensions`
를 먼저 돌리지 않아도 됐다. ⚠ **RDS 는 아직 다르다** — 이 실측은 로컬 postgres 한 벌이고, RDS 실측 1회는
WU-R2 에 남는다(`extensions` 단계를 순서에서 빼지 않는다 — 멱등이고 비용이 0 이다).

⭑ **`pg_trgm` 이 `public` 안에 산다** ⟹ `DROP SCHEMA public CASCADE` 가 확장을 같이 지운다.
그래서 ⑵ 뒤의 ⑵′·⑶ 은 **선택이 아니라 필수**다.

---

## 3. 픽스처 · 도구 실행 · 복구

| # | 명령 | 출력 |
|---|---|---|
| ⑦ | `docker exec -i colab-v2-dev-pg psql -U postgres -d colab_platform -f - < infra/staging/provision-lab.sql` | `(5 rows)` — 계수표 |
| ⑧ | 실행 전 계수 | `labs=1 · accounts=1 · profiles=1 · roles=1` |
| ⑨ | 도구 `--phase schema --dry-run` | 6줄 DDL 을 **찍기만** 함 · 직후 `d1_lab = 1`(무변) |
| ⑩ | 도구 `--phase schema` | `── 두 체인 스키마 재생성 COMMIT.` |
| ⑪ | 직후 `select count(*) from pg_tables where schemaname in ('public','account_admin')` | `0` |
| ⑫ | `upgrade head` 재실행 ×2 | `0031_search_evidence` · `0007_merge_vocab_and_category` |
| ⑬ | `app-grants` ＋ `account-admin` 재실행 | 둘 다 `ok` |
| ⑭ | 실행 후 계수 | `labs=0 · accounts=0 · profiles=0 · roles=0 · credentials=0 · pg_trgm=1` |

도구 호출 모양(⑩) — 도구는 `ops/` 파일 하나라 마이그레이터 이미지에 얹어 돌린다(psycopg 가 거기 있다).

```bash
docker run --rm --network colab_r1a_net --entrypoint python \
  -e COLAB_CORE_S3_BUCKET=colab-platform-data-dev -e COLAB_CORE_S3_REGION=<리전> \
  -v <비밀 디렉터리>:/s:ro -v <레포>/services/core-api/ops/reset_dev_environment.py:/tmp/reset.py:ro \
  -v <산출 디렉터리>:/out colab-v2/migrator:r1a-proof /tmp/reset.py \
  --target dev --yes-reset-dev --phase schema \
  --platform-url-file /s/platform.url --ai-url-file /s/ai.url --report /out/schema.json
```

⑨ 의 dry-run 보고서(`dryRun: true`)가 실행 전 스키마 집합을 그대로 적었다 —
`platform ["account_admin","public"]` · `ai ["public"]`. 도구의 선조건 조회가 실물과 맞는다는 확인이다.

---

## 4. 첫 실행에서 나온 결함 1건 — `public` 스키마 주석

첫 사이클의 `schema-diff` 는 **두 체인 다 red** 였고 차이는 한 줄뿐이었다.

    ::error::schema-diff red — db/platform 선언 스키마와 적용 DB 가 갈라졌다:
         +COMMENT ON SCHEMA public IS '';

원인 실측 —

| 대상 | `obj_description('public'::regnamespace,'pg_namespace')` |
|---|---|
| 손대지 않은 DB(`postgres`) | `standard public schema` |
| 재생성 직후 `colab_platform` | `<NULL>` |

`initdb` 가 만든 `public` 은 주석을 달고 있고 `DROP`·`CREATE` 가 그것을 지운다. `pg_dump` 는 그 차이를
`COMMENT ON SCHEMA public IS '';` 한 줄로 뽑고 게이트는 드리프트로 읽는다.

- **어느 검사에 걸리는가** = `gates/run.sh schema-diff`. 다만 dev 에서는 **초기화를 이미 돌린 뒤에야**
  드러난다(비가역 조작 다음). 로컬 증명이 없었으면 WU-R2 실행 후에 처음 보였을 결함이다.
- **조치** = 재생성 DDL 마지막에 `COMMENT ON SCHEMA public IS 'standard public schema'` 를 넣었다.
  회귀 시험 `test_재생성은_public_스키마_주석을_되돌린다` 를 **RED 확인 뒤** 추가했다(§0 ㄹ·ㅁ).
- 보정 뒤 같은 사이클을 처음부터 다시 돌렸다(⑦~⑭ 는 그 두 번째 사이클의 값이다).

---

## 5. 판정 3종

| 판정 | 명령 | 결과 |
|---|---|---|
| `schema-diff` | `COLAB_TEST_ENV_SOURCED=1 COLAB_APPLIED_DB_URL_PLATFORM=… COLAB_APPLIED_DB_URL_AI=… bash gates/run.sh schema-diff` | `db/platform green — 드리프트 없음.` · `db/ai green — 드리프트 없음.` · `schema-diff green` |
| `deploy_doctor` ⑥⑦ 스키마 head | `select version_num from alembic_version_{platform,ai}` | `0031_search_evidence` · `0007_merge_vocab_and_category` |
| `deploy_doctor` ⑧ RLS 전수 | 같은 `FACTS_SQL` 을 두 체인에서 뽑아 `python3 gates/tools/rls_coverage.py <facts.tsv>` (도구 ⑧ 이 부르는 판정기 그대로) | `rls-coverage green — allow-list 밖 테이블 전부 FORCE RLS + 연구실 경계 정책…` · rc 0 · 표 50건 |
| `deploy_doctor` ⑨ 앱 롤 속성 | `bash infra/staging/db-bootstrap.sh verify` | `colab_app`·`colab_owner` 둘 다 `rolsuper=f rolbypassrls=f` · 표 소유자 분포 `colab_owner 42` (colab_app 0) · `rls_enabled 40 / rls_forced 40 / tables 42` |
| 픽스처 행 | §3 ⑭ | `0` 전건 |

`schema-diff` 는 적용 DB 를 게이트의 일회용 postgres **안에서** `pg_dump` 한다 ⟹ 증명 DB 를 기본 브리지에도
붙여 그 IP 로 넘겼다(`docker network connect bridge colab-v2-dev-pg`). 호스트 포트는 끝까지 열지 않았다.

---

## 6. 정리

```bash
docker rm -f colab-v2-dev-pg
docker network rm colab_r1a_net
docker rmi colab-v2/migrator:r1a-proof
```

`--rm` ＋ tmpfs 라 컨테이너와 함께 데이터가 사라진다. 호스트에 남긴 것은 0600 URL 파일 2개와 보고서
JSON 뿐이고 레포 밖 임시 디렉터리에 있다.

---

## 7. 남은 것

- **RDS 에서의 `DROP SCHEMA` · `CREATE EXTENSION` 권한** — 로컬에서는 `colab_owner` 로 둘 다 됐다.
  RDS 마스터는 진짜 슈퍼유저가 아니므로 dev 실측 1회(WU-R2)가 최종 확인이다.
- **`--phase count` 는 로컬에서 재지 않았다** — 그 단계가 S3 를 함께 조회하는데 이 WU 는 AWS 호출을
  하지 않는다. DB·S3 양쪽을 가짜로 세운 시험 `test_계수_단계는_경계를_걸고_센다` 가 그 자리를 잰다.
- **`--phase s3-plan`·`s3-apply` 도 로컬에서 재지 않았다**(같은 이유). 가드·green 경로는 가짜 클라이언트로 잰다.
- **`infra/staging/provision-lab.sql` 을 `colab_owner` 로 돌리면 실패한다**(§8).

---

## 8. 후속 항목 (이 WU 에서 고치지 않는다)

- **`infra/staging/provision-lab.sql` 이 소유자 롤로는 안 든다.** 실측 —

      ERROR:  new row violates row-level security policy for table "d1_lab_profile"

  `d1_lab` 에는 RLS 가 없고 `d1_lab_profile` 부터 FORCE RLS 라, 경계(`app.current_lab`)를 걸지 않으면
  두 번째 문장에서 멈춘다. staging 에서 통했던 것은 실행기 `infra/staging/provision-lab.sh` 가 psql 을
  **`postgres` 슈퍼유저**로 부르기 때문이고, dev(RDS)에는 그 롤이 없다.
  **어느 검사에 걸리는가** = 걸리는 게이트가 없다. 이 파일을 `NOBYPASSRLS` 롤로 돌려 보는 자리가 레포에
  0건이라 WU-R3 선행 ① 을 실제로 밟을 때 처음 드러난다. `provision-service-operator.sql` 이 같은 함정을
  이미 문서화해 두었다(라운드 §5 WU-R3 ④).
- **`--phase count` 의 표별 계수가 `d1_lab` 을 경계 없이 읽는다.** `d1_lab` 에만 RLS 가 없어 성립하는
  경로이고, 그 성질이 바뀌면 계수가 조용히 0 이 된다. 지금은 맞지만 검사가 없다.

- ⛔ **공용 적용 DB 가 병합되지 않은 리비전에 찍혀 있어 `schema-diff` 가 선다.** 실측 —

      ::error::schema-diff red — db/platform 적용 DB 를 alembic upgrade head 로 올리지 못했다.
           FAILED: Can't locate revision identified by '0032_private_owner_access'

  | 측정 | 값 |
  |---|---|
  | 공용 적용 DB(`colab_platform_applied` · 시험 환경 파일이 가리키는 자리)의 stamp | `0032_private_owner_access` |
  | `origin/main` 의 `db/platform/versions/` 마지막 | `0031_search_evidence` |
  | 이 레인(`integration/r-dev-reset`)의 마지막 | `0031_search_evidence` |
  | `0032_private_owner_access` 가 사는 자리 | 커밋 `75cd069b` · **`origin/local-stage` 하나뿐** |
  | `75cd069b` 이 `origin/main` 의 조상인가 | **아니다** |

  **어느 검사에 걸리는가** = `gates/run.sh schema-diff`. 게이트의 준비 단계가 적용 DB 를
  `alembic upgrade head` 로 올리는데, 그 DB 에 찍힌 리비전이 체인에 없어 alembic 이 기동하지 못한다.
  ⚠ **이 레인은 마이그레이션을 1건도 추가하지 않았다** — `origin/main` 을 포함해 `0032` 를 갖지 않는
  **모든 브랜치**에서 같은 red 가 난다. 원인은 병합되지 않은 브랜치가 공용 적용 DB 를 앞으로 밀어 둔 것이다.
  해소(공용 DB 를 되돌리거나 `local-stage` 를 처리하는 것)는 **다른 세션이 쓰는 상태를 쓰는 일**이라
  이 레인의 경계 밖이다 — **그 DB 를 고치지 않았다.**

  **이 레인이 한 것** = 게이트가 스스로 적은 설계대로 이 트리의 적용 DB 를 **새로 세워** 같은 게이트를
  댔다(`gates/tools/schema-diff.sh` 축자 「CI 설계: 체인마다 DB 를 만들고 → db/<체인>/versions 를
  alembic 으로 upgrade head → 그 DB 의 URL 을 체인별 변수로 넘긴다」). 절차 —

  ```bash
  docker run -d --rm --name colab-v2-r1a-applied --tmpfs /pgdata:uid=70,gid=70 \
    -e PGDATA=/pgdata/db -e POSTGRES_PASSWORD=<임의값> -e POSTGRES_HOST_AUTH_METHOD=trust postgres:16-alpine
  PG_CONTAINER=colab-v2-r1a-applied … bash infra/staging/db-bootstrap.sh roles
  # 시험 환경 파일의 사본에서 COLAB_APPLIED_DB_URL_PLATFORM·_AI 두 줄만 이 DB 로 바꾼다(0600 · 레포 밖)
  COLAB_TEST_ENV_FILE=<사본> COLAB_TASK_ID=… COLAB_GATE_REPORT_DIR=… bash gates/run.sh task
  ```

  ⚠ **검사 내용은 한 줄도 바뀌지 않는다** — 같은 두 체인을 같은 방식으로 `upgrade head` 한 뒤 선언
  스키마와 `pg_dump` 로 비교한다. 바뀐 것은 **어느 DB 를 「적용」으로 보는가** 하나이고, 공용 DB 는
  이 트리의 체인으로는 `upgrade head` 자체가 불가능하므로 비교 대상이 될 수 없다. 감추는 드리프트는
  없다 — `0032` 는 `origin/main` 에 없으므로 이 트리가 뒤처진 것이 아니다.
