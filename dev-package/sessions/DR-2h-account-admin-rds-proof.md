# DR-2h — 계정 관리자 롤 SQL 을 RDS 마스터에서 돌린다 (로컬 red/green 증명)

- 회차 = `R-DEV-RESET` · 레인 `lane/wu-dr2h-account-admin-rds` · 기준 `origin/main`
- 대상 파일 = `services/core-api/ops/account-admin-role.sql` 한 개
- 발견 자리 = `DR-2` A 단계(dev 초기화 실행 · 2026-09-13) — `dev-package/sessions/DR-2-run-2026-09-13.md`
- 증명 일자 = 2026-09-13 · dev·staging·공용 DB 무접촉 · AWS 호출 0건

---

## 1. 결함

`infra/dev/db-bootstrap.sh account-admin` → `infra/staging/db-bootstrap.sh` 의 `account-admin` 단계가
`services/core-api/ops/account-admin-role.sql` 을 RDS 마스터로 돌리다 **exit 3** 로 멈춘다.

- 멈추는 문 = `ALTER ROLE %I NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT BYPASSRLS PASSWORD %L`
- 축자 =
  ```
  ERROR:  permission denied to alter role
  DETAIL:  Only roles with the SUPERUSER attribute may change the SUPERUSER attribute.
  ```
- 원인 = PostgreSQL 16 의 `AlterRole` 은 **`SUPERUSER`/`NOSUPERUSER` 를 적었다는 사실만으로** 거절한다.
  값이 현재 값과 같아도 마찬가지다. RDS 마스터는 `rds_superuser` 의 멤버일 뿐 `rolsuper=f` 다.
- 결과 = 그 문이 **모든 GRANT 앞**에 있어 실패 시 계정 관리자 롤에 표 권한이 **0건**이다 → 로그인 경로가 서지 않는다.
- 로컬·staging 에서 잠복한 이유 = 그 경로의 실행자가 진짜 슈퍼유저(`postgres`)라 같은 문이 그냥 통과한다.

## 2. 고친 내용 (한 문 → 두 문)

- ⑴ 비밀번호는 무조건 — `ALTER ROLE %I PASSWORD %L`
- ⑵ 나머지 속성은 **실제로 어긋났을 때만** — `ALTER ROLE %I NOCREATEDB NOCREATEROLE NOINHERIT BYPASSRLS`
  를 `FROM pg_roles WHERE rolname=:'admin' AND (rolcreatedb OR rolcreaterole OR rolinherit OR NOT rolbypassrls)` 로 감싼다.
- `NOSUPERUSER` 는 어느 `ALTER ROLE` 에도 남기지 않는다. `CREATE ROLE … WHERE NOT EXISTS` 분기는 무수정이다.
- fail-closed 는 파일 끝의 기존 검사(`계정 관리자 롤이 superuser다` RAISE)가 그대로 맡는다 — 속성 다섯을 전부 본다.

## 3. 증명 환경

- 일회용 `postgres:16-alpine`(실측 `PostgreSQL 16.15`) · `--rm` · `--tmpfs /var/lib/postgresql/data` ＋ `PGDATA`
  · **호스트 포트 미공개**(`dev-package/RESTART.md §④` 의 호스트 제약).
- 스키마 = `db/platform/schema.sql` 을 `colab_owner` 로 적용. 이 파일이 체인 head 의 선언 정본이고
  `migration-drift` 가 그 동일성을 판정한다(`DR-1c`). `account_admin.*` 3표와 `d1_*`·`d2_member_role` 이 여기서 선다.
- 롤 배치 = dev 실물을 그대로 흉내낸다.

| 롤 | 속성(실측) | 대응하는 dev 실물 |
|---|---|---|
| `bootstrapper` | `rolsuper=f` `rolcreatedb=t` `rolcreaterole=t` `rolbypassrls=f` | RDS 마스터(`rds_superuser` 멤버) |
| `colab_owner` | `rolsuper=f` `rolbypassrls=f` | 소유자 롤 · DB·객체 소유 |
| `colab_account_admin` | `rolsuper=f` `rolcreatedb=f` `rolcreaterole=f` `rolinherit=f` `rolbypassrls=t` | dev 에 **이미 올바른 속성으로 존재**한다 |

- `GRANT colab_owner TO bootstrapper` = `infra/dev/db-bootstrap.sh prep` 이 실제로 하는 것.
- `GRANT colab_account_admin TO bootstrapper WITH ADMIN OPTION` = dev 에서 그 롤을 만든 것이 마스터라 마스터가 갖는 권한.
- `rolbypassrls=f` 는 `infra/dev/db-bootstrap.sh` 의 `backup-role` 주석이 적은 dev 실측(「RDS 마스터조차 `rolbypassrls=f` 다」)과 같다.
- 비밀번호는 전부 일회용 리터럴이고 컨테이너와 함께 사라진다. 실제 자격은 이 증명에 쓰지 않았다.

## 4. 실행 결과

### ① RED — 원본(HEAD `8d5ae5e4` 판)을 `bootstrapper` 로

```
psql:<stdin>:25: ERROR:  permission denied to alter role
DETAIL:  Only roles with the SUPERUSER attribute may change the SUPERUSER attribute.
exit=3 (as bootstrapper · original.sql)
```

- dev 실측과 **같은 문 · 같은 메시지 · 같은 종료코드**다.
- 직후 계정 관리자 롤의 표 권한 = **0건** → 「GRANT 앞에서 죽는다」가 값으로 확인된다.

### ② GREEN — 고친 판을 같은 롤로 (1회차)

```
ALTER ROLE
REVOKE ×3 · GRANT ×9
exit=0 (as bootstrapper · account-admin-role.sql)
```

- `ALTER ROLE` 이 **한 번만** 찍힌다 = 비밀번호 문만 발화. 조건부 속성 문은 속성이 이미 맞아 발화하지 않는다.
  이것이 dev 의 모양이다.

### ③ 멱등 — 같은 명령 2회차

```
exit=0 (as bootstrapper · account-admin-role.sql)
```

### ④ 권한 실측

```
account_admin | login_credential | table | colab_owner=arwdDxt/colab_owner
                                         | colab_account_admin=arw/colab_owner
```

`arw` = INSERT · SELECT · UPDATE. 전체 표 권한 6표 14행:

| 표 | 권한 |
|---|---|
| `account_admin.login_credential` | INSERT, SELECT, UPDATE |
| `account_admin.login_session` | INSERT, SELECT, UPDATE |
| `account_admin.service_operator` | DELETE, INSERT, SELECT |
| `d1_account` | INSERT, SELECT |
| `d1_lab` | SELECT |
| `d2_member_role` | INSERT, SELECT |

- `CONNECT=true` · 롤 속성 = `rolsuper=f rolcreatedb=f rolcreaterole=f rolinherit=f rolbypassrls=t rolcanlogin=t`
- 파일 끝의 superuser 검사가 통과했다(exit 0 이 그 증거다 — 걸리면 RAISE 로 죽는다).

### ⑤ 속성이 어긋난 자리 — 조건부 문이 실제로 발화하는가

`NOINHERIT` 를 `INHERIT` 로 일부러 어긋나게 한 뒤:

- ⑤-a `bootstrapper` 로 = **exit 3** · 축자 `DETAIL:  Only roles with the BYPASSRLS attribute may change the BYPASSRLS attribute.` · `rolinherit` 미복구
- ⑤-b `postgres`(진짜 슈퍼유저)로 = **exit 0** · `rolinherit=false` 로 복구 → 조건부 문이 실제로 발화한다

⑤-a 는 **후속 항목**이다(§6).

### ⑥ 로컬·staging 경로 회귀 없음 — 슈퍼유저로

- 롤을 지운 자리(`admin_role_rows=0`)에서 `CREATE ROLE … WHERE NOT EXISTS` 분기까지 태워 **exit 0**
- 만들어진 롤 속성 = `f f f f t t` (위 ④ 와 같다) · 표 권한 14행 복원

### ⑦ fail-closed 유지

계정 관리자 롤을 `SUPERUSER` 로 만든 뒤 다시 돌리면:

```
psql:<stdin>:51: ERROR:  계정 관리자 롤이 superuser다
exit=3 (as postgres · account-admin-role.sql)
```

- `NOSUPERUSER` 를 ALTER 에서 뺐어도 **superuser 인 채로 지나가지 않는다.**

## 5. 게이트 — 이 레인에서 돌리지 않았다

- 범위 축소 지시(오케스트레이터 2026-09-13)로 `service-tests-core-api`·`exec-bit`·`work-item-consistency` 는
  **마감 때 오케스트레이터가 돌린다.** 이 레인이 낸 계수는 없다 — **돌리지 않은 게이트를 green 으로 적지 않는다.**
- 같은 지시로 대장 `DR-2h` 블록과 라운드 §11 줄도 이 레인 밖이다(§6 에 넘길 값이 있다).

## 6. 후속 항목 (이 레인이 고치지 않는다)

- ⭑ **조건부 속성 ALTER 는 RDS 마스터에서 여전히 못 돈다** — 실측 ⑤-a 축자
  `Only roles with the BYPASSRLS attribute may change the BYPASSRLS attribute.`
  PostgreSQL 16 은 `CREATEDB`·`CREATEROLE`·`BYPASSRLS`·`REPLICATION` 에도 `SUPERUSER` 와 같은 규칙을 건다 —
  **그 속성을 가진 롤만 그 속성을 바꾼다.** RDS 마스터는 `rolbypassrls=f` 라 `BYPASSRLS` 를 적은 ALTER 를 못 낸다.
  **지금 dev 는 속성이 이미 맞아 그 문이 발화하지 않으므로 이번 초기화는 막히지 않는다.**
  **어느 검사에 걸리는가** = 게이트에는 없다. `infra/staging/db-bootstrap.sh account-admin` 의 종료코드 하나가
  유일한 검사이고, 그것은 **속성이 어긋난 뒤에야** 울린다. 고칠 자리 = 같은 문을 속성별로 더 쪼개거나
  드리프트 시 `ALTER ROLE` 대신 RAISE 로 사람에게 넘기는 것. 범위 밖이라 이 레인은 고치지 않았다.
- 계정 관리자 롤의 속성 드리프트를 정기적으로 보는 자리가 없다 — `deploy_doctor` 15 항목에 없고
  `db-bootstrap.sh verify` 는 `colab_app`·`colab_owner` 두 롤만 찍는다.

## 7. 마감 때 오케스트레이터가 처리할 것

- 대장 `dev-package/work-items.yaml` 에 `DR-2h` 블록(`status: done` · `stage: after_stage2` · `depends_on: [DR-2]`).
- ⚠ **`stage: after_stage2` 로 등재하면 `CLAUDE.md` 의 `<!-- work-items:after_stage2 -->` 괄호에 `DR-2h` 를 같이 넣어야 한다** —
  넣지 않으면 `work-item-consistency` ㈕ 가 red 다(축자 `㈕ \`DR-2h\`: 대장 \`stage: after_stage2\` 인데 \`CLAUDE.md\` 표지에 없다`).
  같은 줄의 항목 수도 25 → 26 으로 바뀐다.
- 라운드 `dev-package/prd/rounds/R-DEV-RESET.md` §11 에 §6 첫 항목(RDS 속성 제약 · 발견 = `DR-2` A 단계).
- 게이트 `service-tests-core-api` · `exec-bit` · `work-item-consistency`.
