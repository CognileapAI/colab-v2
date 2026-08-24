# RESTART — 호스트를 껐다 켠 뒤 이어 하는 법

> **재부팅·WSL 재시작 뒤 첫 세션은 이 문서를 먼저 읽는다.** `03-HANDOFF.md` 보다 먼저다.
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

---

## 2. 복구 절차

### ① 도커 데몬

```
docker ps
```

응답이 없으면 Docker Desktop 을 먼저 켠다. 데몬이 없으면 아래가 전부 실패한다.

### ② staging 8개 올리기

```
docker compose -f infra/staging/compose.i2.yml --env-file ~/.colab-v2-staging.env up -d
```

> **`-f compose.i2.yml` 을 반드시 붙인다.**
> 빼면 기본값 `compose.yml` 이 뜨는데 그건 **I2 이전의 자리표시 오리진(nginx·cloudflared 2개)** 이다.
> 즉 되살리는 명령이 아니라 **`rollback.sh` 와 같은 일**을 한다. 그러고도 루트 헬스는 200 이라 알아채기 어렵다.

**데이터가 살아 있으므로 `deploy.sh` 를 다시 돌릴 필요가 없다.** `deploy.sh` 는 빌드·마이그레이션까지 다시 하는 배포 명령이지 복구 명령이 아니다. 코드가 바뀐 게 없다면 쓰지 않는다.

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
| `COLAB_WORKER_LAB_ID` · `COLAB_WORKER_ACCOUNT_ID` | **식별자(비밀 아님)** | 시드 ULID. 단독으로는 아무 권한도 주지 않는다 — 원장 행과 짝이라 **회전 대상이 아니다** |
| `COLAB_STAGING_PGDATA_DIR` · `COLAB_STAGING_SUBJECTS_FILE` | 경로 | 레포에 절대경로를 적지 않으려고 env 로 받는다 (`CLAUDE.md §3-8`) |
| `COLAB_CORE_AI_BASE_URL` · `COLAB_MODEL_HELPER` · `COLAB_MODEL_ORCHESTRATOR` | **선택(기본값 있음)** | `W7` 배선(`c5a2fbf`)이 더한 셋. 없어도 `up` 이 뜨고 compose 의 기본값이 쓰인다 — **비밀이 아니다**(주소·모델 이름). `COLAB_CORE_AI_BASE_URL` 을 비우면 core-api 가 relay 를 만들지 않아 **검색·제안이 503 이 된다** |

> **`up` 을 막는 것과 제품을 잠그는 것은 다르다.** 위 표에서 `:?` 인 키가 없으면 컨테이너가 아예 안 뜨지만,
> **compose 안에서만 배선되는 값**(`COLAB_VIZ_SOURCE_ROOT` · `COLAB_VIZ_PREVIEW_DIR` · `COLAB_CORE_SUBJECTS_FILE` · `COLAB_AI_DB_URL`)이
> 비면 **헬스는 200 인 채로 제품이 잠긴다.** 2026-08-25 이전이 실제로 그 상태였다(`〈92〉` 계열 · `03-HANDOFF §4`).
> 이 넷은 env 파일이 아니라 `compose.i2.yml` 이 정본이므로 **호스트에서 손댈 것이 없다.**

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

> 갱신하지 않고 끝낸 세션은 다음 세션의 시간을 두 배로 쓰게 만든다.
