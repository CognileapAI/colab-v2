# schema-diff 게이트 검증 — 2026-08-23

> 목적: `dev-package/sessions/P0-schema.md §7-①` 이 남긴 한계 —
> "`schema-diff` 는 적용 DB URL 을 하나만 받아 두 체인을 비교하므로 한 번의 실행으로는 green 이 될 수 없다"
> — 가 `gates/tools/schema-diff.sh` 재작성(`COLAB_APPLIED_DB_URL_PLATFORM` / `_AI` 분리)으로 실제 해소됐는지
> **실측으로만** 확인한다. 이 세션은 검증 전용이며 `gates/`·`db/` 어느 파일도 고치지 않았다.

## 0. 결론 먼저

**`schema-diff` 는 이제 두 체인 URL 을 각각 넘긴 단일 실행에서 green 이다.** 증거는 §2.

---

## 1. 확인한 것 (읽기)

- `gates/tools/schema-diff.sh` — `COLAB_APPLIED_DB_URL_PLATFORM` · `COLAB_APPLIED_DB_URL_AI` 를 체인별로 받고,
  구 변수 `COLAB_APPLIED_DB_URL` 단독 지정 시 red 로 막는 로직이 실제로 들어가 있음을 확인.
- `gates/tools/_pg.sh` — 일회용 postgres 컨테이너는 이름 `colab_v2_gatepg_<pid>_<rand>`, 포트 미공개(전부 `docker exec`),
  `PGDATA` tmpfs, `trap` 정리.
- `db/platform/env.py` · `db/ai/env.py` — 각각 `COLAB_PLATFORM_DB_URL` · `COLAB_AI_DB_URL` 로만 접속 URL을 받는
  alembic env. autogenerate 미사용, `version_table` 이 체인별로 다름(`alembic_version_platform` / `_ai`).
- `dev-package/sessions/D3-db.md §3` — CI 설계: 체인마다 postgres 를 띄우고 `alembic upgrade head` 로 적용한 뒤
  그 URL을 체인별 변수로 게이트에 넘기는 것이 의도된 형태.

## 2. 재현 절차 (실행한 명령)

두 개의 일회용 postgres 컨테이너를 **포트 미공개**로 띄우고, docker 브리지 네트워크 내부 IP로만 접속했다
(레포 관례 그대로 — `curl`/게이트 컨테이너가 호스트 포트를 거치지 않고 `docker exec` 로만 통신).

```bash
docker run -d --rm --name colab_v2_verify_platform \
  --tmpfs /pgdata:uid=70,gid=70 -e PGDATA=/pgdata/db \
  -e POSTGRES_PASSWORD=gate -e POSTGRES_HOST_AUTH_METHOD=trust postgres:16-alpine
docker run -d --rm --name colab_v2_verify_ai \
  --tmpfs /pgdata:uid=70,gid=70 -e PGDATA=/pgdata/db \
  -e POSTGRES_PASSWORD=gate -e POSTGRES_HOST_AUTH_METHOD=trust postgres:16-alpine

docker exec colab_v2_verify_platform createdb -U postgres colab_platform
docker exec colab_v2_verify_ai       createdb -U postgres colab_ai

# 각 체인을 alembic 으로 head 까지 적용 (venv 에 alembic·sqlalchemy·psycopg2-binary 설치, 스크래치패드에서만)
IP_P=$(docker inspect -f '{{(index .NetworkSettings.Networks "bridge").IPAddress}}' colab_v2_verify_platform)
IP_A=$(docker inspect -f '{{(index .NetworkSettings.Networks "bridge").IPAddress}}' colab_v2_verify_ai)

cd db/platform && COLAB_PLATFORM_DB_URL="postgresql://postgres:gate@$IP_P:5432/colab_platform" alembic upgrade head
cd db/ai       && COLAB_AI_DB_URL="postgresql://postgres:gate@$IP_A:5432/colab_ai"             alembic upgrade head

# 단일 실행에서 두 체인 모두 검사
COLAB_APPLIED_DB_URL_PLATFORM="postgresql://postgres:gate@$IP_P:5432/colab_platform" \
COLAB_APPLIED_DB_URL_AI="postgresql://postgres:gate@$IP_A:5432/colab_ai" \
./gates/run.sh schema-diff
```

### 실측 출력

```
── db/platform ────────────────────────────────────────────
db/platform green — 드리프트 없음.
── db/ai ────────────────────────────────────────────
db/ai green — 드리프트 없음.
schema-diff green — 두 체인 각각 선언 = 적용.
```
종료 코드 0. **한 번의 실행에서 두 체인 모두 green.** 이전 세션(§7-①)이 기록한 "체인별로는 green, 한 번의 실행으로는 red"
상태가 더 이상 재현되지 않는다 — 게이트 쪽 수정이 실효했다.

같은 방식(alembic upgrade head, 위와 동일한 두 임시 DB)으로 나머지 DB 게이트도 재확인했다:

| 게이트 | 결과 | 비고 |
|---|:--:|---|
| `schema-diff` | 🟢 green | 위 §2. 두 체인 모두 드리프트 0 |
| `migration-single-head` | 🟢 green | 두 체인 각각 head 1개(`0001_p0_platform`, `0001_p0_ai`) |
| `rls-coverage` | 🟢 green | 조사 21건. allow-list 3건(면제) 제외 전부 FORCE RLS + `lab_boundary`, `d3_file` 은 정책 2개(본체 정책 포함) |
| `db-selftest` | 🟢 green | 38 케이스 전부 의도대로(migration-single-head 13 · rls-coverage 코어 11 + e2e 7 · schema-diff 7) |
| `planning-freshness` | 🟢 green | 15개 임베드 블록 전부 원본과 일치 |
| `contract-lint` | 🟢 green | seam 3건, 룰 위반 0 |
| `contract-selftest` | ⚪ **미완** | 아래 §3 |
| `boundary-selftest` | ⚪ **미실행** | 아래 §3 |
| `banned-import` | ⚪ **미실행** | 아래 §3 |
| `import-boundary` | ⚪ **미실행** | 아래 §3 |
| `ai-no-lineage-write` | ⚪ **미실행** | 아래 §3 |

## 3. 중단한 항목과 사유

`contract-selftest` 를 백그라운드로 돌리던 중, 코디네이터로부터 **다른 에이전트들이 `services/`·`db/ai/`·`gates/`·`infra/`
에서 동시에 작업 중이므로 이 시점부터 레포를 mutating 상태로 취급하라**는 지시가 들어왔다. `contract-selftest` 는
node 서브프로세스(spectral)를 다수 케이스에 걸쳐 반복 기동해 원래도 느린 게이트인데, 이 시점 이후의 결과는
동시 편집에 오염될 수 있어 **신뢰할 수 없는 증거가 된다.** 그래서:

- `contract-selftest` — **미완, 실행 시간 초과.** 다른 에이전트가 이후 세션(D2b)에서 이 계열 게이트를 다시 돌린다.
- `boundary-selftest` · `banned-import` · `import-boundary` · `ai-no-lineage-write` — 같은 이유로 **실행하지 않았다.**
  (참고: `D3-db.md §6`·`§7` 에 따르면 세션 시점 기준 `ai-no-lineage-write` 는 ⑨⑩⑪⑫ green, ⑧(services/ai-service 코드 0건)만
  red 였다 — 이 red 는 **예상된 것**이다. `banned-import`·`import-boundary` 도 `services/` 코드가 아직 없어 사실상 대상
  0건에 가까운 상태로 알려져 있었다. 다만 이번 세션에서 실측하지 않았으므로 현재 상태를 단정하지 않는다.)

이번 세션이 확보한 유효 증거는 **DB 3종 게이트(schema-diff·migration-single-head·rls-coverage) + db-selftest +
planning-freshness + contract-lint** 로 한정한다. 나머지는 이번 산출물에서 판정하지 않는다.

## 4. 정리 확인

- 이번 세션이 만든 컨테이너(`colab_v2_verify_platform`, `colab_v2_verify_ai`) `docker rm -f` 로 제거 완료.
  다른 에이전트의 `a1_`/`c1_` 접두사 컨테이너에는 손대지 않았다.
- `docker ps` — `colab_v2_staging_nginx`, `colab_v2_staging_cloudflared` 무변경으로 확인.
- `curl -s -o /dev/null -w '%{http_code}' -I https://www.colab-hydro.com/healthz` → **200**.

## 5. 다음이 알아야 할 것

- `dev-package/sessions/P0-schema.md §7-①` 의 "게이트 쪽 결손" 항목은 **해소로 기록해도 된다** — 이 리포트가 그 실측 근거다.
- `contract-selftest`·`boundary-selftest`·`banned-import`·`import-boundary`·`ai-no-lineage-write` 재검증은
  동시 편집이 끝난 뒤(D2b 또는 그 이후) 다시 돌려야 유효한 증거가 된다. 이번 리포트의 범위 밖이다.
