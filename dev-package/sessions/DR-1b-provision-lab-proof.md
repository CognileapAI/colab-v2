# DR-1b 로컬 증명 — `infra/staging/provision-lab.sql` 을 소유자 롤로 돌린다

- 목적 = `dev-package/sessions/DR-1a-local-proof.md §8` 의 후속 1건을 닫는다. 축자 = 「`infra/staging/provision-lab.sql` 이 소유자 롤로는 안 든다」.
- 근거 결함 = FORCE RLS 아래의 `lab_boundary` 정책이 `d1_lab_profile`·`d1_account`·`d2_member_role` 에 걸리고, 그 정책이 읽는 `current_lab_id()` 의 입력(`app.current_lab`)을 이 파일이 걸지 않았다.
- **어느 검사에 걸리는가** = **걸리는 게이트가 0건이다.** 이 파일을 `NOBYPASSRLS` 롤로 돌려 보는 자리가 레포에 없어, WU-R3 선행 ① 을 실제로 밟을 때 처음 드러난다. staging 에서 통했던 것은 실행기 `infra/staging/provision-lab.sh` 가 psql 을 **`postgres` 슈퍼유저**로 부르기 때문이고, dev(RDS)에는 그 롤이 없다.
- ⛔ **dev·staging 실환경과 호스트 공용 DB 를 하나도 건드리지 않았다.** 전부 일회용 컨테이너 안이고 AWS 호출 0건이다.
- 일시 = 2026-09-13 · 레인 `lane/wu-r1b-ledger`.

---

## 1. 준비 — 일회용 postgres

호스트 포트를 하나도 공개하지 않고 `PGDATA` 를 tmpfs 에 둔다(`dev-package/RESTART.md` 「이 호스트에서는
`--tmpfs` ＋ `PGDATA` 를 반드시 준다」).

```bash
docker network create colab_r1b_net
docker run -d --rm --name colab-v2-r1b-pg --network colab_r1b_net \
  --tmpfs /pgdata:uid=70,gid=70 -e PGDATA=/pgdata/db \
  -e POSTGRES_PASSWORD=<임의값> -e POSTGRES_HOST_AUTH_METHOD=trust postgres:16-alpine
```

| 확인 | 출력 |
|---|---|
| `docker exec colab-v2-r1b-pg pg_isready -U postgres` | `/var/run/postgresql:5432 - accepting connections` |

접속 문자열은 레포 밖 0600 파일 2개(`platform.url`·`ai.url`)로만 뒀다. 표기는 `postgresql+psycopg://` 다.

---

## 2. 부트스트랩 · 마이그레이션 · 권한

| # | 명령 | 출력 요지 |
|---|---|---|
| ① | `PG_CONTAINER=colab-v2-r1b-pg COLAB_OWNER_PASSWORD=… COLAB_APP_PASSWORD=… COLAB_AI_APP_PASSWORD=… COLAB_ACCOUNT_ADMIN_PASSWORD=… bash infra/staging/db-bootstrap.sh roles` | `roles/databases: ok` |
| ② | `docker build -f infra/dev/migrator/Dockerfile -t colab-v2/migrator:r1b-proof .` | exit 0 |
| ③ | `docker run --rm --network colab_r1b_net -e COLAB_PLATFORM_DB_URL_FILE=/s/platform.url … -w /chain/platform colab-v2/migrator:r1b-proof upgrade head` | `alembic_version_platform = 0031_search_evidence` · `public` 표 **42** |
| ④ | 같은 모양으로 `-w /chain/ai` ＋ `COLAB_AI_DB_URL_FILE` | `alembic_version_ai = 0007_merge_vocab_and_category` |
| ⑤ | `bash infra/staging/db-bootstrap.sh app-grants` | `app role grants: ok (colab_app@platform · colab_ai_app@ai · SELECT only)` |

롤 속성 실측 — 판정의 전제다.

    rolname     | rolsuper | rolbypassrls
    postgres    | t        | t
    colab_owner | f        | f
    colab_app   | f        | f

`colab_owner` 가 `NOBYPASSRLS` 라 FORCE RLS 정책에 그대로 걸린다. dev(RDS)의 소유자 롤과 같은 성질이다.

---

## 3. RED — 고치기 전 파일을 `colab_owner` 로

고치기 전 파일은 `git show HEAD:infra/staging/provision-lab.sql` 로 꺼냈다(수정본과 섞이지 않게).

```bash
docker exec -e PGPASSWORD=… colab-v2-r1b-pg \
  psql -U colab_owner -h 127.0.0.1 -d colab_platform -f /tmp/before.sql
```

출력 축자 —

    BEGIN
    INSERT 0 1
    psql:/tmp/before.sql:27: ERROR:  new row violates row-level security policy for table "d1_lab_profile"

- **psql 종료코드 = `3`** (`\set ON_ERROR_STOP on` 이 트랜잭션을 세운다).
- 첫 문장(`d1_lab`)만 들었다 — 그 표에는 RLS 가 없다. 두 번째(`d1_lab_profile`)부터 정책에 걸린다.
- 롤백 뒤 실측 = `d1_lab=0 d1_lab_profile=0 d1_account=0 d2_member_role=0` — **부분 적용이 남지 않는다.**

---

## 4. 고침 — 두 자리에 경계를 건다

| 자리 | 문장 | 왜 |
|---|---|---|
| `BEGIN;` 직후 | `SET LOCAL app.current_lab = '00000000000000000000HYMETS';` | 네 INSERT 가 `lab_boundary` 정책을 통과하게 한다. `SET LOCAL` 이라 `COMMIT` 과 함께 풀린다(`ops/purge_datasets.py` 와 같은 규율) |
| `COMMIT;` 뒤 · 계수 블록 앞 | `SET app.current_lab = '00000000000000000000HYMETS';` | 계수를 **경계 안에서** 읽는다. 안 걸면 행이 있는데도 0 으로 보인다(아래 §5) |

⚠ **두 번째 자리를 빼면 이 파일이 스스로 거짓말을 한다.** 첫 자리만 고친 판의 실측 —

    COMMIT
    -- 삽입 후 계수 (연구실 C 한정)
     d1_account           |  0
     d1_lab               |  1
     d1_lab_profile       |  0
     d2_member_role       |  0

같은 시점에 슈퍼유저로 센 값은 `d1_lab=1 d1_lab_profile=1 d1_account=1 d2_member_role=1` 이다.
즉 **INSERT 는 성공했는데 계수가 0 을 찍는다** — `.claude/rules/deploy.md` 「깨뜨리면 안 되는 것」 10번이
말하는 「경계 없이 세면 행이 있어도 0 으로 보인다」가 이 파일 안에서 그대로 일어난다. 종전에는 실행기가
슈퍼유저로만 불러서 드러나지 않았다.

---

## 5. GREEN — 고친 파일을 `colab_owner` 로

빈 상태(`d1_lab=0`·`d1_lab_profile=0`)에서 1회 —

    BEGIN
    SET
    INSERT 0 1
    INSERT 0 1
    INSERT 0 1
    INSERT 0 1
    COMMIT
    SET
    -- 삽입 후 계수 (연구실 C 한정)
              표          | 행
    ----------------------+----
     d1_account           |  1
     d1_lab               |  1
     d1_lab_profile       |  1
     d2_member_role       |  1
     d2_permission_switch |  0
    (5 rows)

- **psql 종료코드 = `0`.**
- 판정값 = **`d1_lab` 1 · `d1_lab_profile` 1**(＋`d1_account` 1 · `d2_member_role` 1).
- **멱등 재실행** — 같은 명령을 한 번 더 내면 `INSERT 0 0` ×4 · `COMMIT` · 종료코드 `0` · 계수 무변.
  전 문장이 `ON CONFLICT DO NOTHING` 이라는 파일 머리말의 규약이 소유자 롤에서도 그대로 선다.

---

## 6. 정리

```bash
docker rm -f colab-v2-r1b-pg
docker network rm colab_r1b_net
docker rmi colab-v2/migrator:r1b-proof
```

`--rm` ＋ tmpfs 라 컨테이너와 함께 데이터가 사라진다. 호스트에 남긴 것은 레포 밖 임시 디렉터리의
0600 URL 파일 2개뿐이고 함께 지웠다.

---

## 7. 남은 것 · 후속 항목

- **RDS 실측은 남는다** — 이 증명은 로컬 PostgreSQL 16 한 벌이다. dev(RDS)에서 소유자 롤로 이 파일을
  돌리는 것은 WU-R3 선행 ① 이 처음 밟는다.
- **이 파일을 `NOBYPASSRLS` 롤로 돌려 보는 게이트가 여전히 0건이다.** 이번 고침은 결함 하나를 닫았고
  **검사를 세우지는 않았다** — 같은 종류의 다음 결함은 또 실행해 봐야만 드러난다.
  후속 후보 = `infra/staging/*.sql` 을 일회용 DB에서 소유자 롤로 1회 돌리는 게이트.
- **형제 파일도 같은 함정을 갖는다** — `services/core-api/ops/provision-service-operator.sql` 은 그 사실을
  이미 문서화해 두었다(`dev-package/reports/r-login-backoffice/task1-deploy/operator.md §7` · 라운드 §5 WU-R3 ④).
  이 레인은 그 파일을 고치지 않았다(DR-1b 범위 밖).
- **`infra/staging/provision-lab.sh`(실행기)는 무수정이다** — 슈퍼유저로 부르는 경로도 고친 SQL 에서 그대로 돈다
  (`SET LOCAL` 은 슈퍼유저에게 무해하다).
