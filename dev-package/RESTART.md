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
