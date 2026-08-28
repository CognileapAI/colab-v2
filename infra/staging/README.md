# infra/staging — CoLAB v2 staging

## 지금 서빙되는 것 (WU-I2 이후)

**walking skeleton 이다.** 5개 배포 단위(core-api · pipeline-worker · viz-render · ai-service · frontend)
+ postgres(두 체인) + 엣지 nginx. 절차·근거·증거는 `dev-package/sessions/I2.md`.

```bash
./deploy.sh --target staging     # 배포 — 게이트 → 백업 → 마이그레이션 → 교체 → **판정**까지
./rollback.sh --to-last-green    # 직전 green 릴리스로 (릴리스 원장에서 태그를 읽는다)
./rollback.sh --to-placeholder   # 제품 이전(자리표시 오리진)으로 — 이것은 N-1 이 아니라 0 이다
```

두 스크립트가 같은 프로젝트·같은 컨테이너 이름을 쓴다 — 앞뒤 교체가 대칭이고 DNS·터널을 건드리지 않는다.
`rollback.sh` 는 pgdata 를 지우지 않고, **스키마도 되돌리지 않는다**(forward-only · `〈168〉-㉲`).

공개 헬스 경로: `/healthz`(엣지) · `/healthz/{core-api,pipeline-worker,viz-render,ai-service,frontend}`.

---

## 배포 자동화 (WU-I3)

**I3 가 만든 것은 배포를 빠르게 하는 장치가 아니라 배포를 판정하는 장치다.**
2026-08-23 P1 배포에서 `deploy.sh` 는 컨테이너가 `starting` 인 채로 `exit 0` 을 냈다. 그 배포가
green 이 된 것은 **사람이 따로 기다렸다 헬스 6종을 본** 덕이지 스크립트가 판정해서가 아니다.
**트리거 자동화는 그 사람을 지우는 일이다.** 그래서 순서가 정해져 있다 —
**판정기를 먼저 세우고, 그 다음에 트리거를 붙인다.**

### 무엇이 어디에 있나

| 자리 | 하는 일 |
|---|---|
| `pipeline/run-pipeline.sh` | 한 바퀴 — `git fetch` → fast-forward → `deploy.sh`. 트리거의 몸통 |
| `pipeline/watch.sh` | 크론 껍데기. 로그 한 줄 · 실패 표식 · 마지막 성공 3종을 남긴다 |
| `pipeline/install-schedule.sh` | 크론 설치·해제 (`*/5` — `〈168〉-㉯`) |
| `pipeline/lib.sh` | 릴리스 원장 · 표식 · 이미지 보존 · 잠금 · 판정 어휘 |
| `pipeline/approval/target.sh` | 타깃 판정. `prod` 는 **선언만 있고 실행 경로가 없다** |
| `pipeline/approval/approve.sh` | 승인 기록 (승인자 한 낱말 + **무엇을 눈으로 봤는가**) |
| `pipeline/selftest.sh` | 원장·롤백 대상·표식·거부 경로의 fail-closed 증명 |
| `verify/verify-deploy.sh` | **판정기** — 헬스 6종 + 본문 대조 + 컨테이너 8개 + `0.0.0.0` 0건 |
| `verify/verify-chains.sh` | 두 체인 head (한쪽만 확인하고 전체 성공으로 기록하지 않는다) |
| `verify/selftest.sh` | 판정기 red fixture — 죽은 단위 · 자리표시 본문 · 대상 0건 · 면제 건수 |

### 상태는 어디에 사는가

레포 밖 홈(`$COLAB_PIPELINE_STATE_DIR`, 기본 `~/colab-v2-releases`). `IS3 §10` 의 백업 표식 3종과
**같은 모양**이다(`〈168〉-㉱`).

| 파일 | 뜻 |
|---|---|
| `release-ledger.tsv` | 릴리스 원장 — 시각·종류·커밋 SHA·태그·판정·비고. **보존 30건.** 승인 기록도 **같은 파일**이다 |
| `DEPLOY-FAILED.txt` | 실패 표식. **다음 성공에서만** 사라진다 |
| `LAST-SUCCESS.txt` | 마지막 성공. **파이프라인이 아예 안 돈 경우**를 이것으로 잡는다 |
| `pipeline.log` | 누적 로그 |

### 왜 이런 모양인가 — 세 얼굴

| 얼굴 | 종전 | 지금 |
|---|---|---|
| **무엇을 굽는가**(DR-4) | 주석은 「커밋의 산출」, 코드는 **워킹트리** | 트리가 깨끗하지 않으면 **배포하지 않는다.** 태그 = 커밋 SHA. 굽겠다면 `--allow-dirty` 로 명시하고, 그 건수가 원장에 남고 태그가 `-dirty` 가 된다 |
| **무엇으로 돌아가는가**(DR-5) | 태그 `:i2` 고정 → 직전 이미지가 이름을 잃음 | **빌드 전에** `:prev` 로 보존하고, 보존본과 신규본의 **이미지 ID 가 다름을 실행 중에 확인**한다. 롤백은 원장의 「직전 green」으로 간다. 이미지 보존 3개 |
| **무엇이 성공했는가**(DR-6) | `dc ps` 로 끝 → `starting` 인 채 `exit 0` | 종료 코드의 근거가 **헬스 6종 + 본문 대조 + 컨테이너 8개 + 노출 0건 + 두 체인 head** 다. 대기 타임아웃은 **red** 다 |

### 세 상태 — 이 디렉터리의 규약

**선언되면 검사한다 / 명시적으로 면제하면 건수를 드러낸 채 넘어간다 / 아무 말도 없으면 실패한다.**
`backup/lib.sh` 의 SKIP 규약(`〈170〉-㉮`)을 그대로 물려받았다. 요약줄은 `verdict()` 한 곳에서만
나오고, 그 줄은 **건너뛴 건수를 숨길 수 없다.**

- 타깃 미지정 → 거부(기본값 `staging` 으로 떨어지지 않는다)
- 롤백 대상 미지정 → 거부(조용히 자리표시로 가지 않는다)
- 워킹트리 더러움 → 거부(`--allow-dirty` 로만 통과, 건수 노출)
- 배포 전 백업 → 두 프로파일 GREEN 아니면 중단(`--skip-backup` 으로만 면제, 원장에 남는다)
- 검사 대상 0건 → **red**

### 실패하면 무엇이 일어나나

**자동 롤백은 없다**(기본 off · `〈168〉-㉳`). 판정 red 면 **중단 ＋ 표식 파일 ＋ 사람 호출**이다.
판정기를 신뢰하기 전에 자동 되돌림을 켜면 판정 버그가 멀쩡한 릴리스를 계속 걷어내고, 원인이
코드인지 판정기인지 구분되지 않는다. `--auto-rollback` 은 **명시 옵션**으로만 있다.

⚠ **알림 통로는 `I4` 로 이관됐다**(`〈168〉-㉮`). 표식·로그는 **가서 봐야 보이는 자리**다.
자동 배포가 조용히 실패하면 **다음에 누가 볼 때까지 침묵**한다 — 사람이 부르던 때는 부른 사람이
결과를 봤다. 자동 트리거가 그 사람을 지웠고, **그래서 이 침묵의 비용이 I2 이전보다 크다.**

### prod

`prod` 는 **선언만 있고 실행 경로가 없다.** 부르면 `㊻` 을 인용하며 즉시 거부한다(조용한 no-op 아님).
증명되는 것은 **「승인 없이는 넘어가지 않는다」의 음성뿐**이고, 「승인하면 넘어간다」의 양성은
건너편이 비어 있어 증명되지 않는다. 그 사실을 지우지 않는다.

### 손으로 compose 를 부를 때

이미지 태그가 변수다. **기본값을 두지 않았다** — 기본값 `i2` 로 떨어지면 DR-5 가 그대로 살아난다.

```bash
COLAB_RELEASE_TAG=i2 docker compose -f compose.i2.yml --env-file ~/.colab-v2-staging.env ps
```

`:i2` 는 릴리스 신원이 아니라 **호환 별칭**이다(`compose.throwaway.yml` 이 그 이름으로 찾는다).
신원은 SHA 태그이고, 더 정확히는 digest 다 — `reference/IMAGE-DIGESTS.md` 참조.

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

## `load-seed.py` — S2 초기 데이터 적재 도구

명세 = `dev-package/sessions/S2-EXEC-PLAN.md §14` · 멱등 설계 = 같은 문서 `§5.4`(`〈106〉`).

```bash
python3 infra/staging/load-seed.py \
  --base-url https://www.colab-hydro.com \
  --token-file <홈의 0600 토큰 파일> \
  --manifest  <적재 매니페스트 .json> \
  --source-root <원천 데이터 루트>

python3 infra/staging/load-seed-test.py      # 시험 16건 — staging 에 접속하지 않는다
```

- **공개 API op 4건만 부른다** — `listDatasets` · `createUpload` · `createDataset` ·
  `attachUploadGridFiles`. **DB 드라이버를 import 하지 않는다** — `㊾-③`(DB 직접 INSERT 금지)
  위반을 코드로 불가능하게 만드는 수단이다.
- **멱등은 도구가 자기 재실행에 대해 보장한다.** `listDatasets` 를 `nextCursor` 가 `null` 이 될
  때까지 순회해 **이름 완전 일치**로 판정한다 — 건너뜀 / 격자만 이어붙임 / 중단. **판정을
  건너뛰는 인자(`--force` 류)를 두지 않았다.**
- **삭제 호출 0건.** `deleteDataset` 은 501 이고 삭제는 이 도구의 동작이 아니다.
- 토큰은 헤더에만 실린다 — 로그·보고서에 적지 않는다(시험이 단언한다).

> ⚠ **도구는 S-04 업로드 모달을 대체하지 않는다.** FE 코드를 지나지 않고 그 모달이 부르는
> **서버 표면**만 재현한다. 그래서 절차서 `§14.3` 은 **회차 ①(`D-01`·`D-02`)을 화면으로** 하라고
> 못 박았다 — 계보 확정 UI 가 실제로 도는 것을 그 회차가 증명한다.

> ⛔ **2026-08-26 현재 매니페스트가 없다.** 기준 격자 16건 중 일부가 **적재 제외분(`D-14` HLS)**
> 과 **범위 밖(GRIB)** 의 격자라 데이터셋 귀속을 지어내야 완성된다 — `㊴-②` 저촉이라 만들지
> 않았다. 형식은 `load-seed-test.py` 의 `MANIFEST_3` 이 보여준다. 미결은 `03-HANDOFF §4` #28.

## 아직 남은 것

- 터널 ingress 규칙의 정본은 이제 `tunnel/` 이다 (WU-IS2 적용 완료 · `terraform plan` = No changes.).
- 백업 **기구**는 `backup/` 에 세웠다(WU-IS3). **대상은 I2 로 열렸다** — `colab_v2_staging_pg` 의
  `colab_platform`. 붙이는 설정 4줄은 `dev-package/sessions/I2.md §6`. 붙이기·스케줄은 IS3 의 몫이다.
- 비밀·환경값은 홈의 `.colab-v2-staging.env`(0600) 하나에 모인다 — 터널 토큰 · Cloudflare 3종 ·
  DB 비밀 3종 · postgres 데이터 디렉터리 경로.
- 호스트가 WSL2 머신 1대다. 재부팅·업데이트가 곧 중단이다.
