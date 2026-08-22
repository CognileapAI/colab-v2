# infra/staging — CoLAB v2 staging

## 지금 서빙되는 것 (WU-I2 이후)

**walking skeleton 이다.** 5개 배포 단위(core-api · pipeline-worker · viz-render · ai-service · frontend)
+ postgres(두 체인) + 엣지 nginx. 절차·근거·증거는 `dev-package/sessions/I2.md`.

```bash
./deploy.sh      # 자리표시 → walking skeleton  (compose.i2.yml)
./rollback.sh    # walking skeleton → 자리표시   (compose.yml, 직전 서빙 상태)
```

두 스크립트가 같은 프로젝트·같은 컨테이너 이름을 쓴다 — 앞뒤 교체가 대칭이고 DNS·터널을 건드리지 않는다.
`rollback.sh` 는 pgdata 를 지우지 않는다.

공개 헬스 경로: `/healthz`(엣지) · `/healthz/{core-api,pipeline-worker,viz-render,ai-service,frontend}`.

아래 절은 **직전 릴리스(자리표시 오리진, `compose.yml`)** 의 기록이다. 롤백 대상이라 남겨 둔다.

---

## 자리표시 오리진 — 이게 무엇인가

WSL 호스트 위에서 도는 **최소 오리진**이다. PoC 철거로 비어 버린 Cloudflare 터널 뒤에
v2 staging 오리진을 다시 붙여 `www.colab-hydro.com` 의 530 을 해소한다.

- **nginx 한 개뿐이다.** 안내 페이지와 `/healthz` 만 응답한다.
- **데이터 저장소가 없다.** postgres·minio·redis 를 재현하지 않는다. 빈 오리진이다.
- **PoC 애플리케이션 코드를 계승하지 않는다.** `dev-package/reference/poc-deploy/` 의 nginx conf 는
  라우팅 "모양"의 참조일 뿐이며, 프록시 블록을 옮겨오지 않았다 (`CLAUDE.md §5`).
- **P0/I2 에서 실제 v2 서비스로 교체될 자리표시다.** → **I2 에서 실제로 대체됐다**(`compose.i2.yml`).
  이 파일은 지우지 않는다 — 롤백 대상이기 때문이다.

## 터널 연결 구조

기존 터널은 원격 관리형이고, 대시보드의 ingress 규칙이
`www.colab-hydro.com → http://nginx:80` 을 가리킨다.
그래서 **compose 의 서비스 이름을 `nginx` 로 고정**했다. 이름을 바꾸면 터널이 오리진을 못 찾는다.
DNS·터널 설정은 건드리지 않는다.

그 ingress 규칙을 레포로 끌어오는 작업이 **WU-IS2** 이고, 선언과 절차는 `tunnel/` 에 있다
(`tunnel/README.md` — 모드 근거 · 필요한 API 토큰 권한 · import→plan→apply→검증→롤백 순서).
**아직 apply 는 실행되지 않았다.**

## 토큰은 어디에 있나

레포에 넣지 않는다. 홈 디렉터리의 `.colab-v2-staging.env` (권한 `0600`) 한 줄:

```
CF_TUNNEL_TOKEN=<값>
```

PoC 철거 때 보관한 홈의 `.colab-poc-env.prod.bak` 에서 해당 줄만 추출한 것이다.
토큰은 커맨드 인자가 아니라 `TUNNEL_TOKEN` 환경변수로 주입한다 — PoC 에서 프로세스 목록에
평문 노출되던 문제를 반복하지 않기 위해서다.

## 올리기 / 내리기

```bash
cd infra/staging
docker compose --env-file ~/.colab-v2-staging.env up -d      # 올리기
docker compose --env-file ~/.colab-v2-staging.env ps         # 상태
docker compose --env-file ~/.colab-v2-staging.env logs -f    # 로그
docker compose --env-file ~/.colab-v2-staging.env down       # 내리기 (= 롤백)
```

내리면 커넥터가 사라지고 공개 주소는 다시 **530** 이 된다. 올리면 **200** 으로 돌아온다.
롤백 경로는 이 한 쌍이 전부다 — DNS 전파를 기다릴 일이 없다.

## 확인

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3000/healthz     # 로컬
```

셸에서 로컬 DNS 해석이 막혀 있으면 Cloudflare 프록시 IP 로 직접 친다:

```bash
IP=$(curl -s -H 'accept: application/dns-json' \
  'https://1.1.1.1/dns-query?name=www.colab-hydro.com&type=A' \
  | grep -oE '"data":"[0-9.]+"' | head -1 | cut -d'"' -f4)
curl -s -o /dev/null -w '%{http_code}\n' --resolve www.colab-hydro.com:443:$IP \
  https://www.colab-hydro.com/healthz
```

## 노출 정책

호스트 포트는 `127.0.0.1:3000` 으로만 연다. 외부 노출 경로는 터널 하나뿐이다.
PoC 에서 5432·8100 이 의도와 달리 `0.0.0.0` 에 열려 있던 문제를 반복하지 않는다.

## 아직 남은 것

- 터널 ingress 규칙의 정본은 이제 `tunnel/` 이다 (WU-IS2 적용 완료 · `terraform plan` = No changes.).
- 백업 **기구**는 `backup/` 에 세웠다(WU-IS3). **대상은 I2 로 열렸다** — `colab_v2_staging_pg` 의
  `colab_platform`. 붙이는 설정 4줄은 `dev-package/sessions/I2.md §6`. 붙이기·스케줄은 IS3 의 몫이다.
- 비밀·환경값은 홈의 `.colab-v2-staging.env`(0600) 하나에 모인다 — 터널 토큰 · Cloudflare 3종 ·
  DB 비밀 3종 · postgres 데이터 디렉터리 경로.
- 호스트가 WSL2 머신 1대다. 재부팅·업데이트가 곧 중단이다.
