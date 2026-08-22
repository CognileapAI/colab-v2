# infra/staging — CoLAB v2 staging 자리표시 오리진

## 이게 무엇인가

WSL 호스트 위에서 도는 **최소 오리진**이다. PoC 철거로 비어 버린 Cloudflare 터널 뒤에
v2 staging 오리진을 다시 붙여 `www.colab-hydro.com` 의 530 을 해소한다.

- **nginx 한 개뿐이다.** 안내 페이지와 `/healthz` 만 응답한다.
- **데이터 저장소가 없다.** postgres·minio·redis 를 재현하지 않는다. 빈 오리진이다.
- **PoC 애플리케이션 코드를 계승하지 않는다.** `dev-package/reference/poc-deploy/` 의 nginx conf 는
  라우팅 "모양"의 참조일 뿐이며, 프록시 블록을 옮겨오지 않았다 (`CLAUDE.md §5`).
- **P0/I2 에서 실제 v2 서비스로 교체될 자리표시다.** walking skeleton 이 올라오면 이 구성은 대체된다.

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

- 터널 ingress 규칙의 정본이 여전히 **Cloudflare 대시보드에만** 있다.
  IaC 선언은 `tunnel/` 에 준비돼 있으나 **적용 전**이다 (WU-IS2, API 토큰 대기).
- 백업 **기구**는 `backup/` 에 세웠다(WU-IS3) — fail-closed 검사와 왕복 실증까지 끝났다.
  다만 **백업 대상은 아직 붙어 있지 않다**(저장소가 없다). I2 로 postgres 가 올라오면 설정 한 줄로 붙이고,
  스케줄은 **그때 건다** — 대상 없이 걸어 두면 매일 실패가 쌓여 알람 피로가 된다.
- 호스트가 WSL2 머신 1대다. 재부팅·업데이트가 곧 중단이다.
