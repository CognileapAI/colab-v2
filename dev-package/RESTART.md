# RESTART — 호스트를 껐다 켠 뒤 이어 하는 법

> **재부팅·WSL 재시작 뒤 첫 세션은 이 문서를 먼저 읽는다.** `03-HANDOFF.md` 보다 먼저다.
> ⭑ **⟨2026-09-05 정리⟩ 여기 있는 것은 절차와 값의 자리뿐이다.** 긴 경위·실측 서술은 **원문 그대로** `dev-package/archive/RESTART-NOTES.md` 에 있다 — 줄 번호로 `grep`.
> 여기 적힌 것을 건너뛰면 **staging 이 죽은 채로, 또는 조용히 롤백된 채로** 작업이 시작된다.
> 그 상태에서도 루트 헬스는 200 을 내므로 **살아 있는 것처럼 보인다.** 그것이 이 문서가 있는 이유다.

---

## 1. 무엇이 죽고 무엇이 사는가 (실측)

| 대상 | 재시작 뒤 | 근거 |
|---|---|---|
| **staging 데이터** (`pgdata`) | **산다** | 홈의 바인드 마운트(`~/.colab-v2-staging/pgdata`). 컨테이너와 수명이 다르다 |
| **Cloudflare 터널 · DNS** | **산다** | 엣지 쪽 자산이라 이 호스트와 무관 |
| **terraform state** | **산다** | 레포 안 로컬 디렉터리(커밋되지 않음 — `IS4` 참조) |
| **레포 · 커밋** | **산다** | — |
| **staging 컨테이너 8개** | **안 뜬다** | `restart=unless-stopped` 이지만 **도커 데몬이 자동 기동하지 않는다** |
| **검증용 일회용 DB** (`p1_pg` 등) | **죽는다** | tmpfs. 일회용이므로 다시 만든다 |
| **서브에이전트** | **죽는다** | 그래서 **레인이 끝난 뒤에** 재시작한다 |
| **Remote Control 세션** | **죽는다** | RC 서버 프로세스가 WSL 과 함께 접힌다. 세션은 `offline` 로 남고 **약 4시간 뒤 되살릴 수 없다**(`§2-⑤`) |

---

## 2. 복구 절차

### ① 도커 데몬

```
docker ps
```

응답이 없으면 Docker Desktop 을 먼저 켠다. 데몬이 없으면 아래가 전부 실패한다.

### ② staging 8개 올리기

```
# 태그는 손으로 적지 않는다 — **원장의 마지막 green `deploy` 행**에서 읽는다.
COLAB_RELEASE_TAG="$(awk -F'\t' '$2=="deploy" && $5=="green" {t=$4} END{if(t=="")exit 1; print t}' \
  ~/colab-v2-releases/release-ledger.tsv)" \
docker compose -f infra/staging/compose.i2.yml --env-file ~/.colab-v2-staging.env up -d
```

> **이 한 줄을 쓰는 이유 = 태그를 문서에 박으면 다음 배포마다 낡기 때문이다.**
> ⭑ **⟨개정 2026-08-29 · `PLAN-SoT §9 〈185〉-㉹`⟩ `COLAB_RELEASE_TAG` 를 반드시 앞에 붙인다.**
> **`-f compose.i2.yml` 을 반드시 붙인다.**
> 빼면 기본값 `compose.yml` 이 뜨는데 그건 **I2 이전의 자리표시 오리진(nginx·cloudflared 2개)** 이다.
> 즉 되살리는 명령이 아니라 **`rollback.sh` 와 같은 일**을 한다. 그러고도 루트 헬스는 200 이라 알아채기 어렵다.

**데이터가 살아 있으므로 `deploy.sh` 를 다시 돌릴 필요가 없다.** `deploy.sh` 는 빌드·마이그레이션까지 다시 하는 배포 명령이지 복구 명령이 아니다. 코드가 바뀐 게 없다면 쓰지 않는다.

### ②-0 이미지가 없으면 — **소스에서 다시 굽는 정식 경로는 `deploy.sh` 하나다** ⟨신설 2026-08-29 · `PLAN-SoT §9 〈186〉`⟩

위 `up` 이 `No such image` 로 죽으면 그 릴리스의 이미지가 호스트에 없다는 뜻이다.
**여기서 `docker build` 를 손으로 치지 않는다.** 태그가 커밋 SHA 인데 굽는 내용이 그 커밋이 아니면 **태그가 거짓말을 하고**,
그건 `deploy.sh` 가 막으려고 만들어진 결함 그대로다(DR-4 · `deploy.sh` 머리 주석).

```
git -C <레포> status --porcelain        # 변경 0건이어야 한다 — 아니면 먼저 정리한다
infra/staging/pipeline/approval/approve.sh Ted "<무엇을 눈으로 봤는가>"
infra/staging/deploy.sh --target staging
```

- **`deploy.sh` 는 복구 명령이 아니라 배포 명령이다** — 게이트·태그보존·빌드·**배포 전 백업**·마이그레이션·판정을 전부 다시 친다.
  데이터는 살아 있으므로 **이미지가 있는 한 이 경로를 쓰지 않는다**(위 `②`).
- **새 태그가 생긴다.** 되살리는 것이 아니라 **지금 커밋을 새 릴리스로 굽는 것**이다. 원장에 green `deploy` 행이 하나 더 붙고,
  그 다음부터는 위 `awk` 한 줄이 그 태그를 읽는다.
- **`--allow-dirty`·`--skip-backup` 을 재기동 상황에서 쓰지 않는다.** 둘 다 「무엇을 굽는지/무엇을 지켰는지 모른다」를 원장에 남긴다.
- 되돌리기는 `rollback.sh` 이고 **이미지만 되돌린다 — 스키마는 되돌리지 않는다.**
  ⚠ 2026-08-29 현재 **스크립트 롤백 경로가 없다**(성공 릴리스 1건 · `03-HANDOFF §4 #43`).

### ②-1 시크릿은 어디에 사는가 — **이름과 위치만 적는다. 값은 절대 적지 않는다**

`--env-file` 이 가리키는 홈의 `0600` env 파일 하나가 staging 의 모든 비밀을 쥔다.
`compose.i2.yml` 이 `${...:?}` 로 요구하는 키는 다음과 같다 — **하나라도 없으면 `up` 이 뜨지 않는다.**

| 키 | 성격 | 비고 |
|---|---|---|
| `CF_TUNNEL_TOKEN` | **비밀** | 터널 커넥터. **compose 가 `:?` 로 요구하는 것은 이 하나뿐이다** |
| `CF_API_TOKEN` · `CF_ACCOUNT_ID` · `CF_TUNNEL_ID` | 비밀 / 식별자 | **compose 가 아니라 `infra/staging/terraform` 이 쓴다**(IS2). `up` 은 이것 없이도 뜬다 — 라우팅 IaC 를 돌릴 때 필요하다 |
| `COLAB_PG_SUPER_PASSWORD` · `COLAB_OWNER_PASSWORD` · `COLAB_APP_PASSWORD` | **비밀** | 플랫폼 DB 3롤 |
| `COLAB_AI_APP_PASSWORD` | **비밀** | `colab_ai` DB 앱 롤 |
| `COLAB_VIZ_SERVICE_TOKEN` | **비밀** | core-api ↔ viz-render **양쪽이 같은 문자열** |
| `COLAB_VIZ_TILE_SIGNING_SECRET` | **비밀** | 타일 서명 |
| `OPENAI_API_KEY` | **비밀** | ai-service |
| `COLAB_WORKER_LAB_ID` · `COLAB_WORKER_ACCOUNT_ID` | **선택 · 식별자(비밀 아님)** | 시드 ULID. 단독으로는 아무 권한도 주지 않는다 — 원장 행과 짝이라 **회전 대상이 아니다.** ⭑ **2026-08-26 부터 필수가 아니다**(`PLAN-SoT §9 〈110〉`) — 워커는 대상 연구실을 원장(`d1_lab`)에서 읽고 연구실마다 제 스코프로 돈다. `compose.i2.yml` 은 이 둘을 **걸지 않는다.** 값을 되걸면 그 연구실 하나로 다시 좁혀지고, **원장에 없는 값이면 워커가 뜨지 않는다** |
| `COLAB_STAGING_PGDATA_DIR` · `COLAB_STAGING_SUBJECTS_FILE` · `COLAB_STAGING_CREDENTIALS_FILE` | 경로 | 레포에 절대경로를 적지 않으려고 env 로 받는다 (`CLAUDE.md §3-8`) |
| `COLAB_STAGING_PREVIEWS_DIR` | 경로 (**`:?` — 없으면 `up` 이 안 뜬다**) | ⭑ **⟨신설 2026-08-31 · `PLAN-SoT §9 〈235〉` · `#49` 해소⟩ 미리보기 산출물 루트의 호스트 실체.** named volume `previews` 가 이 경로에 바인드된다 — **볼륨 이름은 그대로**라 백업 설정은 손댈 것이 없다. **WSL ext4 쪽 경로여야 한다**(Windows 드라이브에는 POSIX 퍼미션이 없어 `volume-init` 의 `chown 10001` 이 안 먹는다). 게이트 쪽 짝은 `~/.colab-v2-test.env` 의 `COLAB_PREVIEW_TILE_DIR` 이고 **같은 자리를 가리킨다** |
| `COLAB_STAGING_CORE_DB_URL_FILE` · `COLAB_STAGING_PIPELINE_DB_URL_FILE` · `COLAB_STAGING_AI_DB_URL_FILE` · `COLAB_STAGING_PLATFORM_OWNER_DB_URL_FILE` · `COLAB_STAGING_AI_OWNER_DB_URL_FILE` | 경로 (**가리키는 파일이 비밀**) | ⭑ **접속 URL 을 값이 아니라 파일로 넘긴다** (`PLAN-SoT §9 〈121〉-㉯` · `03-HANDOFF §4 #34`). 예전에는 접속 문자열이 compose 의 환경변수였고, 그래서 `docker inspect` 에 비밀번호가 통째로 나와 **작업 기록에 남았다.** 다섯 다 `:?` — 하나라도 없으면 `up` 이 뜨지 않는다. 뒤 둘은 `--profile migrate` 러너 전용이라 `up` 만 할 때는 안 쓰이지만, **없으면 마이그레이션이 안 돈다** |
| `COLAB_CORE_AI_BASE_URL` · `COLAB_MODEL_HELPER` · `COLAB_MODEL_ORCHESTRATOR` | **선택(기본값 있음)** | `W7` 배선(`c5a2fbf`)이 더한 셋. 없어도 `up` 이 뜨고 compose 의 기본값이 쓰인다 — **비밀이 아니다**(주소·모델 이름). `COLAB_CORE_AI_BASE_URL` 을 비우면 core-api 가 relay 를 만들지 않아 **검색·제안이 503 이 된다** |

> **`up` 을 막는 것과 제품을 잠그는 것은 다르다.** 위 표에서 `:?` 인 키가 없으면 컨테이너가 아예 안 뜨지만,
> **compose 안에서만 배선되는 값**(`COLAB_VIZ_SOURCE_ROOT` · `COLAB_VIZ_PREVIEW_DIR` · `COLAB_CORE_SUBJECTS_FILE`)이
> 비면 **헬스는 200 인 채로 제품이 잠긴다.** 2026-08-25 이전이 실제로 그 상태였다(`〈92〉` 계열 · `03-HANDOFF §4`).
> 이 넷은 env 파일이 아니라 `compose.i2.yml` 이 정본이므로 **호스트에서 손댈 것이 없다.**

**접속 URL 파일 다섯도 자격증명이다** (`〈121〉-㉯`). 파일 하나에 접속 문자열 **한 줄**만 넣는다 —
읽는 쪽이 끝의 공백·개행만 벗기므로 개행은 있어도 되고, **주석·빈 줄·따옴표는 넣지 않는다.**
규약은 아래 `subjects.json` 과 **완전히 같다**: `0600` · 소유자 uid `10001` · 홈 보관 ·
**제자리 덮어쓰기 후 재기동**(바인드 마운트는 inode 에 붙는다).
파일이 없거나 못 읽히거나 비면 각 단위는 **뜨지 않는다** — 조용한 폴백이 없다.

| env 키 | 컨테이너 안 자리 | 읽는 쪽 |
|---|---|---|
| `COLAB_STAGING_CORE_DB_URL_FILE` | `/etc/colab/core-database.url` | core-api `COLAB_CORE_DATABASE_URL_FILE` |
| `COLAB_STAGING_PIPELINE_DB_URL_FILE` | `/etc/colab/pipeline-db.url` | pipeline-worker `COLAB_PIPELINE_DB_URL_FILE` |
| `COLAB_STAGING_AI_DB_URL_FILE` | `/etc/colab/ai-db.url` | ai-service `COLAB_AI_DB_URL_FILE` |
| `COLAB_STAGING_PLATFORM_OWNER_DB_URL_FILE` | `/etc/colab/platform-owner-db.url` | `db/platform/env.py` `COLAB_PLATFORM_DB_URL_FILE` |
| `COLAB_STAGING_AI_OWNER_DB_URL_FILE` | `/etc/colab/ai-owner-db.url` | `db/ai/env.py` `COLAB_AI_DB_URL_FILE` |

> 앞 셋은 **앱 롤**(비소유자 · NOBYPASSRLS), 뒤 둘은 **소유자 롤**이다 — 섞으면 앱이 DDL 권한을 갖거나
> 마이그레이션이 권한 부족으로 죽는다. 두 체인의 소유자 파일도 **따로** 둔다(`CLAUDE.md §3-3`).

**심어 둔 계정 표(`COLAB_STAGING_SUBJECTS_FILE` 가 가리키는 `subjects.json`)는 자격증명이다.**

- 그 안의 키 문자열이 **곧 베어러 토큰**이다. `services/core-api/tests/fixtures/subjects.json` 의
  값을 그대로 쓰면 **레포를 읽을 수 있는 누구나 공개 staging 에 인증된다.**
  실제로 그렇게 배포된 적이 있다 — **레포 픽스처 토큰은 테스트 전용이고, staging 에는 절대 올리지 않는다.**
- 파일 권한은 **`0600`** 이고, **소유자는 컨테이너 uid `10001`** 이다(각 Dockerfile `USER colab`).
  `0644` 로 푸는 것은 고치는 것이 아니라 **노출을 넓히는 것**이다. `0600` 에서 `PermissionError` 가
  나면 답은 권한 완화가 아니라 **소유권 정렬** — `compose.i2.yml` 의 `volume-init` 이 named volume 에
  하는 일(`chown 10001`)을 호스트 바인드 파일에 손으로 해 주는 것과 같다.
- **바인드 마운트는 inode 에 붙는다.** 값을 갈 때 새 파일을 만들어 `mv` 하면 컨테이너는 **옛 파일을 계속 읽는다.**
  반드시 **제자리 덮어쓰기** 후 `docker restart colab_v2_staging_core_api` — 표는 기동 시에 한 번 읽힌다.
- 회전 검증은 **본문으로** 한다. 새 토큰으로 `/api/v1/me` 가 **200 + 옳은 주체**를 내고,
  **옛 토큰이 401 `UNAUTHORIZED` 를 내는 음성 확인**까지 봐야 회전이 먹은 증거다.

### ③ 확인 — 여기까지 해야 복구다

```
docker ps --filter name=colab_v2_staging --format '{{.Names}}\t{{.Status}}'
curl -s -o /dev/null -w 'root %{http_code}\n' -I https://www.colab-hydro.com/healthz
for u in core-api frontend pipeline-worker viz-render ai-service; do
  curl -s -o /dev/null -w "$u %{http_code}\n" https://www.colab-hydro.com/healthz/$u
done
```

- 컨테이너 **8개**(nginx·cloudflared·pg·core_api·frontend·pipeline_worker·viz_render·ai_service) 전부 `healthy`
- 헬스 **6종 전부 200**

> **루트 하나만 보고 넘어가지 않는다.** 자리표시 오리진도 루트는 200 을 낸다.
> **단위별 `/healthz/<unit>` 5개가 200 인지**가 I2 가 서 있다는 증거다.

### ④ 검증용 DB 가 필요하면 (게이트·테스트를 돌릴 때만)

```
docker run -d --name <레인>_pg \
  --tmpfs /var/lib/postgresql/data:rw,size=512m \
  -e PGDATA=/var/lib/postgresql/data/pg \
  -e POSTGRES_PASSWORD=<임시> -e POSTGRES_DB=colab_platform postgres:16-alpine

cd services/core-api && CONTAINER=<레인>_pg APP_PASSWORD=<임시> tests/fixtures/setup-db.sh
```

`setup-db.sh` 가 앱 롤 접속 URL 을 찍어 준다. 그 값을 `COLAB_CORE_TEST_DATABASE_URL` 로 쓴다.

> **이 호스트에서는 `--tmpfs` + `PGDATA` 를 반드시 준다.** 없으면 `initdb` 가
> `could not change permissions of directory` 로 죽는다. `postgres:16-alpine` 을 쓴다(staging 과 같은 이미지).
> **호스트 포트를 공개하지 않는다** — 컨테이너 IP 로만 붙는다.

#### ⭑ ⟨신설 2026-08-29 · 근거 `sessions/STAGE2-READINESS-AUDIT.md §5`⟩ 시험용 환경변수는 `COLAB_CORE_TEST_DATABASE_URL` 하나가 아니다

| 이름 | 값 출처 |
|---|---|
| `COLAB_CORE_TEST_SUBJECTS_FILE` | 레포 픽스처 `services/core-api/tests/fixtures/subjects.json` (미지정이면 `conftest.py:54` 가 같은 파일로 되돌린다) |
| `COLAB_REFERENCE_DATA` | 원천 마운트 `/mnt/f/00_Project/00 CoLAB/03 Reference-Data` — `pipeline-worker`·`viz-render` 의 실데이터 시험이 읽는다 |
| `COLAB_PIPELINE_DB_URL` | 위 ④ 의 `tests/fixtures/setup-db.sh` 가 찍는 일회용 DB URL 을 그대로 쓴다 (원장은 `core-api` 와 같은 `colab_platform`) |
| `COLAB_AI_TEST_DICT_DB_URL` | `services/ai-service/tests/fixtures/setup-db.sh` 가 찍는 일회용 DB URL (`db/ai` 체인 · DB `colab_ai`). ⭑ **⟨신설 2026-08-29⟩ 부트스트랩이 생겼다** — `core-api` 와 같은 규약이고 다른 것은 체인뿐이다 |

**다섯 값이 사는 자리 = 홈의 `~/.colab-v2-test.env`(`0600`)** ⭑ ⟨신설 2026-08-29⟩.
`~/.colab-v2-staging.env` · `~/.colab-v2-staging-backup.env` 와 **같은 관행**이다 — 레포에 두지 않는다(`CLAUDE.md §3-8`).

```
set -a; . ~/.colab-v2-test.env; set +a
cd services/<단위> && .venv/bin/python -m pytest
```

> ⚠ **DB URL 세 줄(`COLAB_CORE_TEST_DATABASE_URL` · `COLAB_PIPELINE_DB_URL` · `COLAB_AI_TEST_DICT_DB_URL`)은 일회용 컨테이너의 값이다.**
> tmpfs 라 컨테이너를 지우거나 호스트를 껐다 켜면 **죽는다.** 다시 만든 뒤 각 체인의 `setup-db.sh` 가 찍는 한 줄로 **덮어쓴다.**
> 파일 머리에 그 두 줄이 적혀 있다. **값은 그 파일 밖 어디에도 적지 않는다.**

#### ⭑ ⟨신설 2026-08-30⟩ ㉮ 게이트용 **적용 DB** 두 줄 — `schema-diff` 를 돌리는 유일한 배선

`gates/run.sh all` 이 `schema-diff` 를 판정하려면 **체인마다 적용 DB 가 하나씩** 있어야 한다.
게이트 자신이 적은 설계 그대로다 — **체인마다 DB 를 짓고 `alembic upgrade head` 한 뒤 그 URL 을 넘긴다.**

| 이름 | 값 출처 |
|---|---|
| `COLAB_APPLIED_DB_URL_PLATFORM` | 아래 절차로 지은 `db/platform` 적용 DB. `schema-diff`·`preview-tile-slot` **둘**이 같이 읽는다. ⭑ **⟨개정 2026-08-31 · `〈237〉`⟩ `autometa-loss` 는 여기서 빠졌다** — 대조 정본이 **staging 실물**로 갈렸다(아래 `㉰`). ／ 이전 표기 ~~셋이 같이 읽는다~~ |
| `COLAB_APPLIED_DB_URL_AI` | 같은 절차의 `db/ai` 적용 DB. **하나라도 빠지면 `schema-diff` 는 red(준비·입력미선언)** 다 |
| `COLAB_PREVIEW_TILE_DIR` | ⭑ **⟨신설 2026-08-31⟩ staging 미리보기 루트의 호스트 실체**(`~/.colab-v2-staging.env` 의 `COLAB_STAGING_PREVIEWS_DIR` 과 **같은 값**). `preview-tile-slot` 이 이 자리를 본다 — 없으면 red(준비) |

두 줄도 `~/.colab-v2-test.env` 에 산다(앞 절과 같은 관행 · `0600` · 값은 레포에 적지 않는다).

```
# ④ 의 일회용 컨테이너 안에 **게이트 전용 DB 를 따로 하나씩** 만든다(시험용 DB 를 건드리지 않는다)
docker exec <플랫폼 컨테이너> createdb -U postgres colab_platform_applied
docker exec <ai 컨테이너>     createdb -U postgres colab_ai_applied

cd db/platform && COLAB_PLATFORM_DB_URL='<위 DB 의 psycopg URL>' <core-api venv>/bin/alembic upgrade head
cd db/ai       && COLAB_AI_DB_URL='<위 DB 의 psycopg URL>'       <core-api venv>/bin/alembic upgrade head
```

⚠ **세 함정** — 실측으로 하나씩 걸렸다.

- **스킴이 다르다.** alembic 에는 `postgresql+psycopg://` 로, **게이트 변수에는 `postgresql://` 로** 넣는다.
  게이트는 `pg_dump`·`psql` 로 직접 붙으므로 psycopg 스킴을 못 읽는다.
- **망이 같아야 한다.** 이 두 DB 는 **기본 브리지**에 둔다. `schema-diff` 가 띄우는 일회용 postgres 도
  기본 브리지에 뜨고, **다른 도커 망의 DB 에는 닿지 않는다**(격리로 막힌다 · 실측 `Operation timed out`).
- ⛔ **`COLAB_PG_NETWORK` 를 전역에 두지 않는다.** staging 망의 DB 를 쓰려면 그 값이 필요한데,
  전역으로 두면 셀프테스트의 일회용 컨테이너가 staging 망에 뜨고 `db-selftest` 가 **red 로 뒤집힌다**(실측).
  staging 적용 DB 를 재고 싶으면 `sessions/I3-DEPLOY-AUTOMATION-PREP.md §6` 처럼 **그 게이트만 따로** 돈다.



ai 체인 일회용 DB 를 세우는 줄 (`postgres:16-alpine` · `--rm` · tmpfs · `PGDATA` · 호스트 포트 미공개):

```
docker run -d --rm --name ai_pg \
  --tmpfs /var/lib/postgresql/data:rw,size=512m \
  -e PGDATA=/var/lib/postgresql/data/pg \
  -e POSTGRES_PASSWORD=<임시> -e POSTGRES_DB=colab_ai postgres:16-alpine

cd services/ai-service && CONTAINER=ai_pg APP_PASSWORD=<임시> tests/fixtures/setup-db.sh
```

- 앱 롤은 **`colab_ai_app` 이고 `colab_app` 이 아니다** — 한 자격증명이 두 체인을 다 여는 순간을 만들지 않는다
- 그 롤은 **SELECT 뿐**이고, 쓰기 권한이 붙으면 스크립트가 그 자리에서 죽는다(`infra/staging/db-bootstrap.sh` 의 `app-grants` 와 같은 fail-closed)
- 시드 둘(`k2_ontology_seed.sql` · `k2b_concept_graph_seed.sql`)까지 적재한다 — 시험이 세는 수(사전 22 · 노드 49 · 엣지 19)의 출처다

**없이 돌리면 붕괴로 보인다** — core-api `471 errors` · pipeline-worker `23 failed·15 errors` · viz-render `8 failed`.
**전부 환경 게이트이고, skip 이 아니라 fail 로 떨구는 의도적 설계다**(green-by-skip 금지 · `CLAUDE.md §4`) — 고장으로 읽지 않는다.
**채우면 전건 통과** — core-api **471** · pipeline-worker **160** · viz-render **119** · **ai-service 98** · frontend **277**.
(앞 넷은 2026-08-29 재실측 — `~/.colab-v2-test.env` 를 source 한 뒤 각 단위 `.venv/bin/python -m pytest`.)

```
uv venv .venv && uv pip install -r requirements.txt -r requirements-dev.txt
```

#### ⭑ ⟨신설 2026-08-31 · Ted 판정 `PLAN-SoT §9 〈237〉` · `#50` 해소⟩ ㉰ `autometa-loss` 의 **대조 정본** — `COLAB_AUTOMETA_STAGING_DB_URL`

| 이름 | 값 출처 |
|---|---|
| `COLAB_AUTOMETA_STAGING_DB_URL` | **staging 실물 platform DB 의 읽기 전용 접속 URL.** 값은 `~/.colab-v2-test.env`(`0600`)에만 산다 — 앞 절과 같은 관행이다. 없으면 `autometa-loss` 는 **red(준비·입력미선언)** 다 |

- **`COLAB_APPLIED_DB_URL_PLATFORM` 으로 대신하지 않는다.** 옛 변수만 선언돼 있으면 게이트가
  **그 사실을 이름으로 지적하며** red 를 낸다 — 조용히 옛 값으로 떨어지는 경로가 없다.
  `schema-diff`·`preview-tile-slot` 은 옛 변수를 **그대로** 쓴다. 둘은 다른 질문이라 다른 정본을 본다.
- **읽기 전용이다 — 그리고 게이트가 매 회차 그것을 다시 증명한다.**
  ⑴ URL 에 `options=-c default_transaction_read_only=on` 을 단다. **안 달면 red** 다.
  ⑵ 모든 SQL 이 `BEGIN READ ONLY … ROLLBACK` 안에서 돈다 — 스크립트에 `COMMIT` 이 **한 곳도 없다.**
  ⑶ 매 회차 **쓰기 탐침**(임시 테이블)을 던지고, **거부당하지 않으면 red** 다. 탐침은 되감기므로 흔적이 0 이다.
- **롤은 `postgres`(수퍼유저)다 — 감추지 않고 이유를 적는다.** 플랫폼 테이블이 `FORCE ROW LEVEL SECURITY`
  라 **소유자도 걸러진다**(실측 = `colab_owner` 로 붙으면 `d5_pipeline_event` **0행**). 감사자는 연구실 경계
  **밖에서 전수**를 봐야 한다. 쓰기는 위 세 겹이 봉한다.
- **호스트 자리는 staging 망 컨테이너의 IP 다.** 스택을 다시 세우면 바뀔 수 있다 — 다시 얻는 한 줄:

```
docker inspect colab_v2_staging_pg --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
```

#### ⭑ ⟨신설 2026-09-01 · Ted 판정 `RULING ㉟` · `DATA-REFERENCE §0 M-9`⟩ ㉱ `autometa-loss` 의 **경계 롤** — `COLAB_AUTOMETA_BOUNDARY_ROLE`

| 이름 | 값 출처 |
|---|---|
| `COLAB_AUTOMETA_BOUNDARY_ROLE` | **경계에 걸리는 롤의 이름 하나**(접속 URL 이 아니다 · 비밀도 아니다). 값은 `~/.colab-v2-test.env`(`0600`)에만 산다 — 앞 절들과 같은 관행이고 **레포에는 값도 절대경로도 적지 않는다.** 없으면 `autometa-loss` 는 **red(준비·입력미선언)** 다 |


#### ⭑ ⟨신설 2026-09-04 · 호스트 재부팅 실측⟩ ㉲ **재부팅 후 게이트 DB** — 순서·비밀번호·IP 셋이 더 걸린다

> **없는 것을 잡는 검사 = `./gates/run.sh schema-diff` 한 줄이다.** 일회용 컨테이너가 없으면
> `pg_dump: ... connection to server at "172.17.0.3" ... Host is unreachable` 로 **red(준비)** 가 난다.
> ⚠ **staging 8개가 healthy 인 것과 무관하다** — staging 은 데몬이 돌아오면 스스로 서지만
> 이 DB 는 tmpfs 라 돌아오지 않는다(`§1` 표 「검증용 일회용 DB … 죽는다」). **전 게이트를 돌리기 전에 이 한 줄부터 친다.**

절차 자체는 위 `④` ＋ `㉮` 그대로다. **그 위에 재부팅에서만 걸리는 세 가지가 있다 — 셋 다 2026-09-04 실측으로 걸렸다.**

- **① 만드는 순서가 IP 를 정한다.** 기본 브리지는 빈 자리를 낮은 번호부터 준다 —
  `docker network inspect bridge` 가 비어 있으면 **먼저 만든 컨테이너가 `172.17.0.2`, 다음이 `.3`** 이다.
  `~/.colab-v2-test.env` 에 이미 적힌 자리와 맞추려면 **ai 체인(`ai_pg`) 을 먼저, platform 체인(`a2_pg`) 을 나중에** 만든다
  (실측 = `COLAB_APPLIED_DB_URL_AI` 가 `.2` · `COLAB_APPLIED_DB_URL_PLATFORM` 이 `.3`).
  순서를 바꾸면 IP 가 서로 바뀌고 env 두 줄을 고쳐야 한다. **고치는 것보다 순서를 지키는 쪽이 싸다.**
- **② `POSTGRES_PASSWORD` 를 새로 짓지 않는다 — env 에 이미 적힌 값이다.**
  `COLAB_APPLIED_DB_URL_*` 의 롤은 **`postgres`(수퍼유저)** 이고 게이트는 그 비밀번호로 **TCP 로** 붙는다.
  임의 값으로 컨테이너를 세우면 `setup-db.sh` 도 `alembic upgrade head` 도 **전부 통과한다**
  (둘 다 `docker exec` · 컨테이너 안 신뢰 접속이라 비밀번호를 안 본다) — 그리고 **`schema-diff` 만**
  `password authentication failed for user "postgres"` 로 red 를 낸다. **성공 신호가 셋 중 둘이라 고장으로 안 보인다.**
  같은 이유로 `APP_PASSWORD` 도 지어내지 않는다 — `COLAB_CORE_TEST_DATABASE_URL`·`COLAB_AI_TEST_DICT_DB_URL` 에 적힌 값이다.
  **값을 읽는 자리는 그 파일(`0600`) 하나이고, 어디에도 옮겨 적지 않는다.**
- **③ staging 망의 IP 는 재부팅으로 갈린다 — 위 `㉰` 의 `docker inspect` 한 줄로 다시 읽는다.**
  실측 = `colab_v2_staging_pg` 가 `172.18.0.2` → `172.18.0.6` 으로 옮겨 갔고,
  **옛 자리에는 `colab_v2_staging_frontend` 가 들어와 있었다** — 고쳐 적지 않으면 **엉뚱한 컨테이너에 붙는다.**
  갈린 값을 쓰는 키는 `COLAB_AUTOMETA_STAGING_DB_URL` · `COLAB_PREVIEW_TILE_DB_URL` 둘이고,
  `COLAB_ARTIFACT_OWNER_DB_URL` 은 앞엣것을 참조하므로 함께 따라온다. **키 이름만 적는다 — 값은 적지 않는다.**


### ⑤ Remote Control 다시 띄우기 — **시한이 있다**

**staging 이 안 뜨는 것과 뿌리가 같다.** WSL2 가 접히면 안에서 돌던 장기 연결이 조용히 끊기고,
`claude remote-control` **서버 프로세스가 사라진다.** 세션은 개별로 끊긴 것이 아니라 **물고 있던 서버가 없어진 것**이라,
남아 있던 RC 세션이 **한꺼번에 `offline`** 이 된다.

**먼저 무엇이 죽었는지 가른다.**

```
ps aux | grep '[c]laude remote-control'    # 0 이면 서버가 죽었다
ping -c 2 api.anthropic.com                # 닿으면 네트워크·인증 문제가 아니다
```

| 실측 | 뜻 | 할 일 |
|---|---|---|
| 서버 프로세스 **있다** | 링크만 끊겼다 | 해당 세션에서 `/remote-control` |
| 서버 프로세스 **0** | 서버가 죽었다 | **아래로 다시 띄운다.** `/remote-control` 로는 안 된다 |

```
claude remote-control --continue           # 마지막 세션을 잇는다
claude remote-control --session-id <id>    # 특정 세션을 집는다
```

> ⚠ **그 세션이 원래 돌던 디렉터리에서 돌린다.** 워크트리에서 돌리면 다른 세션이 뜬다.
> ⚠ **끊긴 뒤 약 4시간 안에만 되살아난다.** 그 뒤에는 새 세션만 열린다 — **호스트를 되살릴 때 같이 한다.**
> ⚠ `/remote-control` 은 **살아 있는 프로세스를 재연결하는 명령**이다. 죽은 서버를 되살리지 않는다.

**확인** — 풋터에 `/rc active` 가 뜨면 붙은 것이다. 실패하면 `/remote-control` 이 이유를 찍는다.

---

## 3. 그다음

`CLAUDE.md §1` 순서 그대로.

1. `dev-package/03-HANDOFF.md` — **지금 어디까지 왔는가.** 진입조건은 `§4.5`
2. `dev-package/DOMAINS.md`
3. `dev-package/WORK-UNITS.md`
4. `dev-package/PLAN-SoT.md`
5. `dev-package/sessions/<이번 WU>.md`

`03-HANDOFF` 와 실물이 어긋나면 **실물을 점검해 HANDOFF 를 먼저 바로잡는다.**

---

## 4. 정리 — 껐다 켜기 전에

세션을 닫고 재시작할 예정이라면 그 전에:

- [ ] 레인(서브에이전트)이 **전부 끝났는가** — 도중에 끄면 산출물이 반쯤 남는다
- [ ] 작업이 **커밋됐는가** (`git status -sb` clean)
- [ ] 원격에 **푸시됐는가** (`git status -sb` 에 ahead 없음)
- [ ] `03-HANDOFF` 가 **갱신됐는가** (`CLAUDE.md §6` 세션 종료 규약)
- [ ] 일회용 컨테이너를 **지웠는가** (`docker ps -a` 에 `*_pg` 잔재)
- [ ] **살려 둘 Remote Control 세션이 있는가** — 있다면 세션 id 를 적어 둔다. 껐다 켠 뒤 **4시간**이 시한이고, 그 안에 `--session-id` 로 집어야 이어진다(`§2-⑤`)

> 갱신하지 않고 끝낸 세션은 다음 세션의 시간을 두 배로 쓰게 만든다.
