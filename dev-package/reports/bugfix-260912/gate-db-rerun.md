# DB 의존 게이트 4건 red 원인 · 재실행 배선 (2026-09-12 · 조사)

## 0. 결론

- 원인 둘 — ⑴ psql 3건 = `~/.colab-v2-test.env` 의 staging DB IP 가 낡음(IP 드리프트) ⑵ `schema-diff` = 공유 적용 DB 가 형제 사본의 리비전 `0030_merge_audit_and_backoffice` 를 이고 있음.
- 실행기 분류는 **4건 다 `red(판정)`**(exit 1)이었다 — 지시문의 「red(준비)」와 갈린다. 근거 = `/tmp/gates-all-run.log:2674·2680·2685·2686`.
- 원인은 둘 다 배선(환경)이고 검사 대상 결함이 아니다 — 실행기가 exit 1 을 준비로 가르지 못한다(`gates/run.sh:80-85` `gate_state_of` = 78·111·표식만 준비).

## 1. 게이트별 해결자 변수 · 인용

| 게이트 | 변수 | 축자 |
|---|---|---|
| autometa-loss | `COLAB_AUTOMETA_STAGING_DB_URL` | `gates/tools/autometa-loss.sh:68-69` — `PSQL="${COLAB_AUTOMETA_PSQL:-psql}"` / `URL="${COLAB_AUTOMETA_STAGING_DB_URL:-}"` |
| preview-tile-slot | `COLAB_PREVIEW_TILE_DB_URL` · `_BOUNDARY_ROLE` · `COLAB_PREVIEW_TILE_DIR` | `gates/README.md:25` — `대조 정본(COLAB_PREVIEW_TILE_DB_URL = staging 실물 platform DB · 읽기 전용)` |
| artifact-ownership | `COLAB_ARTIFACT_OWNER_DB_URL` | `gates/tools/artifact-ownership.sh:60` — `URL="${COLAB_ARTIFACT_OWNER_DB_URL:-}"` |
| schema-diff | `COLAB_APPLIED_DB_URL_PLATFORM` · `_AI` | `gates/tools/schema-diff.sh:67-68` — `URL_PLATFORM="${COLAB_APPLIED_DB_URL_PLATFORM:-}"` / `URL_AI="${COLAB_APPLIED_DB_URL_AI:-}"` |

- 값의 자리는 한 곳 — `~/.colab-v2-test.env`. 실행기가 스스로 읽는다: `gates/run.sh:149-153` — `COLAB_TEST_ENV_FILE="${COLAB_TEST_ENV_FILE:-${HOME:-}/.colab-v2-test.env}"` … `set -a; . "$COLAB_TEST_ENV_FILE"; set +a`.
- ⚠ `set -a; .` 는 호출자가 export 한 같은 이름 값을 **덮는다.** 덮이지 않게 하려면 `COLAB_TEST_ENV_SOURCED=1` 을 미리 export 한다(같은 블록의 조건).
- `172.18.0.2` 의 출처 = 런타임 `docker inspect` 아님 · 컴포즈 서비스명 아님 · **env 파일에 박힌 옛 IP**. 근거 = 파일 mtime `2026-09-12 21:08:41` > 로그 mtime `21:07:32` — 회차 종료 1분 뒤 누군가 `172.18.0.8` 로 고쳤다. 현재 `172.18.0.2` 는 `colab_v2_staging_ai_service`(5432 미청취 → Connection refused).

## 2. schema-diff 의 DB 두 벌

- 일회용 = **선언 스키마 쪽만**. `gates/tools/schema-diff.sh:144-145` — `. _pg.sh` / `pg_start schema-diff`. 정책 축자 `gates/tools/_pg.sh:9-12` — `컨테이너 이름은 colab_v2_gatepg_<pid>_<rand>` · `포트를 하나도 publish 하지 않는다` · `PGDATA 는 tmpfs` · `trap 으로 반드시 지운다`.
- 적용 DB = **공유·상주**. 세우는 법 축자 `dev-package/RESTART.md:198-202` — `docker exec <플랫폼 컨테이너> createdb -U postgres colab_platform_applied` / `docker exec <ai 컨테이너> createdb -U postgres colab_ai_applied` / `cd db/platform && COLAB_PLATFORM_DB_URL='<위 DB 의 psycopg URL>' <core-api venv>/bin/alembic upgrade head`.
- 함정 축자 `dev-package/RESTART.md:207-209` — `alembic 에는 postgresql+psycopg:// 로, 게이트 변수에는 postgresql:// 로` · `이 두 DB 는 기본 브리지에 둔다`. `COLAB_PG_NETWORK` 전역 선언 금지(같은 절).
- `upgrade head` 는 이제 게이트가 스스로 돈다(`gates/tools/schema-diff.sh:109-146`) — 새 적용 DB 는 `createdb` 까지만 하면 된다.

## 3. 컨테이너 실측 (2026-09-12 조사 시점 · `docker ps` · `docker inspect`)

- postgres 컨테이너 **12개**(지시문의 4개와 갈린다). 기본 브리지 172.17.x 11개 · staging 망 1개.
- `172.18.0.8` = `colab_v2_staging_pg`(망 `colab-v2-staging_default`) = **psql 3건의 의도 대상**. 현재 env 값과 일치, 접속 성공(`select current_user` → `postgres`).
- `172.17.0.7` = `colab_lane_applied` = `COLAB_APPLIED_DB_URL_PLATFORM`/`_AI` 의 현재 대상. **다른 세션 소유.**
- `172.17.0.3` = `colab_stage12_tl2_final_gates_pg`(지시문이 env 값이라 한 IP — 현재 env 에 없다). `172.17.0.10` = `colab_v2_lanepg`(= `COLAB_CORE_TEST_DATABASE_URL`).
- `colab_lane_applied` 의 `colab_platform_applied.alembic_version_platform` = **`0030_merge_audit_and_backoffice`** (표 이름은 `alembic_version` 이 아니다). `colab_ai_applied.alembic_version_ai` = `0007_merge_vocab_and_category`.
- 이 트리가 아는 head = `0026_login_sessions`(`db/platform/versions/` 최종 · `migration-single-head` 출력 `리비전 30건 · head 1개 (0026_login_sessions)`). `0030…` 은 트리 전체 grep 0건 → **적용 DB 가 앞서 있다**(형제 사본 소행).

## 4. 재실행 배선 (다른 세션 컨테이너 무접촉)

```bash
# (a) 이 회차 전용 일회용 적용 postgres — 기본 브리지 · 포트 미공개 · tmpfs · --rm
PW=$(openssl rand -hex 12)
docker run -d --rm --name colab_applied_bugfix260912 \
  --tmpfs /var/lib/postgresql/data:rw,size=512m \
  -e PGDATA=/var/lib/postgresql/data/pg -e POSTGRES_PASSWORD="$PW" postgres:16-alpine
sleep 5
docker exec colab_applied_bugfix260912 createdb -U postgres colab_platform_applied
docker exec colab_applied_bugfix260912 createdb -U postgres colab_ai_applied
IP=$(docker inspect colab_applied_bugfix260912 --format '{{.NetworkSettings.IPAddress}}')

# (b) 환경 — env 파일을 먼저 읽고, 적용 DB 두 줄만 덮어쓴 뒤 재source 를 막는다
set -a; . ~/.colab-v2-test.env; set +a
export COLAB_TEST_ENV_SOURCED=1
export COLAB_APPLIED_DB_URL_PLATFORM="postgresql://postgres:$PW@$IP:5432/colab_platform_applied"
export COLAB_APPLIED_DB_URL_AI="postgresql://postgres:$PW@$IP:5432/colab_ai_applied"

# (c) 재실행 — 게이트 목록 인자는 없다(usage: gates/run.sh <gate> | all [-j N] · gates/run.sh:752)
bash gates/run.sh schema-diff
bash gates/run.sh autometa-loss
bash gates/run.sh preview-tile-slot
bash gates/run.sh artifact-ownership

# (d) 회수 — 이 회차가 만든 것 하나만 지운다
docker rm -f colab_applied_bugfix260912
```

- 한 실행으로 묶으려면 `begin --gate schema-diff --gate autometa-loss … --report <dir>` 뒤 `COLAB_TASK_ID=<id> bash gates/run.sh task`(`gates/run.sh:29-33`). 네 게이트를 한 run_id 로 낸다.
- psql 3건은 (a) 불필요 — (b) 의 `set -a; . ~/.colab-v2-test.env` 만으로 현재 `172.18.0.8` 을 집는다.

## 5. 미확인

- `/tmp/gates-all-bQsaae/{,}.out`·`.rc` — **디렉터리 부재**(요약 JSON 경로만 로그 끝줄에 남음). 판독은 `/tmp/gates-all-run.log` 로 했다.
- 재실행 후 4건이 green 이 되는지 — 이 조사에서 게이트를 돌리지 않았다(지시).
- `0030_merge_audit_and_backoffice` 를 쓴 형제 사본의 위치 — 조사 범위 밖.

## 6. 후속 항목 (고치지 않음)

- `colab_lane_applied` 처럼 **여러 사본이 공유하는 적용 DB** 가 `schema-diff` 를 서로 깬다 — 회차별 일회용 적용 DB 를 게이트가 스스로 세우는 안(=`gates/tools/ci-schema-diff.sh:33-34` 의 CI 배선을 로컬에도) 검토.
- staging 스택 재기동 때 env 의 IP 세 줄이 조용히 낡는다 — `docker inspect` 로 매 회차 재해석하거나 컨테이너 이름으로 붙는 안 검토.
