# DEPLOY-CURRENT — 현행 PoC 배포 실물 기록 (2026-08-22 정찰)

> v2가 **물려받는 것**의 기록이다. 설계 문서가 아니라 **지금 돌고 있는 것의 사실 기록**이며, 정찰은 읽기 전용으로 수행했다(무엇도 변경·중지·재시작하지 않았다. 비밀값은 키 이름만 기록).
> 이 문서가 낡으면 실물을 다시 점검해 **이 문서를 먼저 바로잡는다.**

**대상** `colab-hydro.com` (CoLAB PoC) · **호스트** WSL2 머신 1대 · **정찰 시각** 2026-08-22

---

## 1. 경로 한 장

```
브라우저
  → Cloudflare 엣지 (www.colab-hydro.com, TLS 종료)      ← 엣지
  → Cloudflare Tunnel (원격 관리형, 토큰) → cloudflared 컨테이너   ← 유입
  → nginx:80 (컨테이너)                                   ← 라우팅
        /api/         → FastAPI backend:8000
        /health       → backend:8000/health
        /viz/         → viz:8100
        /colab-data/  → MinIO:9000 (presigned 다운로드 프록시)
        /             → Vite 빌드 정적 파일
  → postgres · redis · celery · processor worker · ElasticMQ   ← 뒷단
```

## 2. 엣지 (DNS · TLS)

| 항목 | 실물 |
|---|---|
| 네임서버 | Cloudflare (`javon.ns.cloudflare.com` / `dns.cloudflare.com`) |
| `www.colab-hydro.com` | A/AAAA = Cloudflare anycast 프록시 IP → **HTTP/2 200 정상 서비스** |
| `colab-hydro.com` (apex) | **A/AAAA/CNAME 없음(NODATA)** → 강제 접속 시 **HTTP/2 530**. 죽어 있다 |
| TLS | **전량 Cloudflare 엣지 종료.** 오리진은 터널 내부 평문 HTTP |
| 로컬 인증서 | **없음.** certbot·Let's Encrypt 디렉터리 자체가 없다 |

인증서 만료 리스크는 없다. 대신 **Cloudflare 계정과 터널 토큰이 단일 실패점**이다.
실서비스 진입점은 `www` 하나뿐이므로, v2 전환 시 apex/www 정책을 먼저 정해야 한다.

> **측정 조건** — 이 셸은 로컬 DNS 해석이 막혀 있어 DoH + `curl --resolve` 로 확인했다.
> 값 자체는 확실하지만, 재확인할 때 같은 방법이 필요할 수 있다.

## 3. 유입 (Cloudflare Tunnel)

- 터널은 **remotely-managed** — 설정이 Cloudflare 대시보드에 있다. 호스트에 `cloudflared` 설정 디렉터리도 로컬 ingress yml도 **없다**.
- 컨테이너 실행 커맨드는 `--token ${CF_TUNNEL_TOKEN}`. 토큰이 프로세스 목록에 평문 노출된다(운영 위생 이슈).
- ngrok·포트포워딩·호스트 nginx/caddy는 **없다.** 외부 노출 경로는 터널 하나뿐이다.

## 4. 라우팅 · 뒷단 컨테이너

Docker Compose 프로젝트 **`colab-poc`**, running 10개.

| 컨테이너 | 역할 | 포트(호스트) |
|---|---|---|
| nginx | 프론트 정적 + 리버스 프록시 | 3000→80 |
| backend | FastAPI (gunicorn+uvicorn) | 8000 |
| viz | viz-service (uvicorn) | 8100 |
| celery_worker | `-Q processing` | 내부 |
| worker | `python -m app.workers.processor` | 내부 |
| postgres | PostGIS/pgvector 계열 | 5432 |
| redis | redis:7-alpine | 내부 |
| minio | 오브젝트 스토리지 | 루프백 9000/9001 |
| elasticmq | SQS 대체 | 9324 |
| cloudflared | 터널 | 아웃바운드만 |

정지 상태: localstack, dev-postgres (모두 Exited). nginx·postgres·cloudflared는 **전부 컨테이너 안**이며 호스트 서비스가 아니다.

> **의도와 실물의 불일치** — prod compose는 5432를 노출하지 않고 8100을 내부화하도록 적혀 있으나, **실제로는 5432가 `0.0.0.0`에, 8100이 외부에 노출**되어 있다.

## 5. 데이터

호스트 바인드 마운트(WSL2 ext4 데이터 디스크). named volume은 있으나 prod 데이터는 **전부 바인드 마운트**다.

| 위치 | 크기 | 내용 |
|---|---|---|
| `postgres/` | 122MB (DB `colab` 실제 32MB) | 메타데이터 |
| `minio/` | **2.0GB** | 업로드 원본·산출물 |
| `backups/` | **13GB** | 사실상 전부 MinIO 미러 |

## 6. 소스 트리가 둘로 갈라져 있다

| | 경로(홈 기준) | 브랜치 | 마지막 커밋 |
|---|---|---|---|
| **실제 기동 트리** | 홈의 `projects/CoLAB-PoC` | `chore/env-examples-cleanup` | `671b2cf` 2026-07-09 |
| 자동배포 크론이 보는 트리 | 홈의 `colab` | `main` | `0528fdb` 2026-05-02 |

- 원격은 둘 다 동일(`CognileapAI/CoLAB-PoC`).
- 매일 04:00 자동배포 크론은 **2026-08-16 이후 `PULL_FAIL (non-ff? diverged?)`로 계속 실패** — 자동배포는 사실상 죽어 있다.
- 지금 떠 있는 컨테이너는 **8주 전 수동 빌드 이미지**다. 따라서 "지금 서비스되는 코드"를 git 커밋으로 특정할 수 없다.

## 7. AWS

**배포된 것이 없다.** 홈에 `.aws` 디렉터리 자체가 없어 credentials·config·프로필 미설정이다.
코드의 `AWS_*` 변수는 전부 MinIO/ElasticMQ를 가리키는 로컬 호환 엔드포인트이며, prod compose 주석에 "AWS 이관 시 minio·elasticmq 제거" 절차가 이미 적혀 있다.

## 8. 백업 사건 — 2026-07-11 ~ 08-17 백업 전량 무효

**증상.** `backups/postgres/` 의 `*.sql.gz` 가 **전부 20바이트(gunzip 결과 0바이트)**. 로그에는 매일 "Dumping..."만 남았다. 즉 **해당 기간 복구 가능한 Postgres 백업이 하나도 없었다.**

**원인은 셋이 겹쳤다.**

| # | 원인 |
|---|---|
| ① | 크론이 **죽은 트리**의 스크립트를 돌려 compose가 다른 프로젝트를 못 찾았다 |
| ② | `gzip -c > $FILE` 리다이렉션이 pg_dump보다 **먼저 파일을 만들고**, `set -e` 가 가드에 닿기 전에 스크립트를 죽였다 |
| ③ | 가드가 **압축 파일 크기(`[[ -s ]]`)와 `gzip -t`만** 검사해 20바이트 빈 gzip을 통과시켰다 |

**조치.** 임시파일로 받고 → `PIPESTATUS[0]` 로 pg_dump 종료코드를 확인하고 → **복원된 `CREATE TABLE` 개수**를 검사한 뒤에야 `mv` 한다. 크론은 **실제 기동 트리**로 재지정했다.

**검증(fail-closed 증명).**

| 경로 | 결과 |
|---|---|
| 정상 | 32 테이블 / 752K 확인 |
| 잘못된 디렉터리에서 실행 | **exit 1 · 잔여물 없음** |

> 이 사건이 게이트 정책(`CLAUDE.md §4`)의 근거를 다시 확인해 준다. **크기만 보는 가드는 green-by-skip과 같다.** 검사 대상이 "산출물이 실제로 쓸모 있는가"가 아니면 가드가 아니다.

## 9. 확정된 방향

| 항목 | 결정 |
|---|---|
| WSL + Cloudflare Tunnel 호스트 | v2의 **staging으로 재사용** |
| prod | **AWS** (`CLAUDE.md` 완료 조건 유지) |
| `colab-hydro.com` 공개 주소 | 최종적으로 **AWS를 가리킨다** |

*2026-08-22 Ted 결정.*

## 10. 컷오버 — 이점과 위험

### 이점

- **엣지가 터널이라 DNS를 건드리지 않는다.** 터널 라우팅만 바꾸면 공개 주소가 새 오리진을 향한다.
- **롤백이 되돌리기 한 번이다.** DNS 전파를 기다릴 필요가 없다.
- 오리진 인증서 개념이 없어 TLS 작업이 컷오버 경로에서 빠진다.

### 위험

| # | 위험 | 성격 |
|---|---|---|
| 1 | **라우팅 정본이 Cloudflare 대시보드에만 있다.** 레포에 재현본이 없어 컷오버가 수작업에 의존한다 | v2에서 **IaC로 끌어와야 한다** |
| 2 | **MinIO 스냅샷 13GB의 복원 가능성이 미검증**이다. 크기만 확인했고 복원해 본 적이 없다 | §8과 같은 종류의 함정 |
| 3 | **PoC 데이터가 v2 이전의 유일한 입력**이다. 이 데이터를 잃으면 대체물이 없다 | 비가역 |
| 4 | 서비스가 WSL2 머신 1대에 얹혀 있어 **호스트 재부팅·Windows 업데이트가 곧 서비스 중단**이다 | staging 재사용 시에도 유효 |

## 11. 후속 WU 후보

각 항목은 **무엇을 막는지**와 함께 적는다.

| 후보 | 작업 | 이것이 없으면 막히는 것 |
|---|---|---|
| **터널 라우팅 IaC화** | Cloudflare 대시보드의 터널 ingress 규칙을 레포의 `infra/` 에 선언형으로 재현하고, 대시보드와의 diff를 게이트로 검사 | 컷오버 전부. 정본이 레포 밖이면 I2·I5가 수작업이 된다 |
| **MinIO 스냅샷 복원 리허설** | 13GB 백업을 별도 MinIO 인스턴스에 실제 복원하고, 객체 수·체크섬을 원본과 대조 | I4(복구 리허설) · PoC 데이터 이관 |
| **PoC 데이터 이관 규격 확정** | 현행 DB 32MB·MinIO 2.0GB를 `DATAMODEL-BASELINE.md` 기준표로 매핑하는 변환 규격 작성 | v2 초기 적재. C3(HARVEST) 입력이기도 하다 |
| **apex/www 정책 결정** | apex 530 해소 여부와 최종 공개 주소 형태를 확정 | I5 prod 전환 |
| **노출 포트 정합화** | 5432·8100 호스트 노출을 prod 의도(내부화)에 맞춘다 | staging 재사용의 전제. 지금은 DB가 `0.0.0.0`에 열려 있다 |
| **터널 토큰 취급 개선** | 프로세스 목록 평문 노출을 제거(파일·시크릿 주입 방식으로 전환) | staging 재사용. 토큰 유출 = 오리진 장악 |
| **기동 트리 일원화** | 두 트리를 하나로 합치고 자동배포 크론의 `PULL_FAIL` 해소 | "지금 도는 코드"의 추적성. 이게 없으면 컷오버 기준선이 없다 |

---

## 부록 — 스택 요약 (v2 참조용, 코드는 계승하지 않는다)

백엔드 FastAPI + SQLAlchemy/Alembic + Celery · geo 계열 rasterio/xarray/GDAL/titiler(GRIB·NetCDF·COG) · 프론트 React18 + Vite + Cesium + Leaflet · DB Postgres(PostGIS/pgvector) · 오브젝트 MinIO · 큐 ElasticMQ.

> `CLAUDE.md §5` — 참조는 **지식**이지 코드가 아니다. 이 절은 도메인 지식·방법론 참조용이며 코드 계승 근거가 아니다.
