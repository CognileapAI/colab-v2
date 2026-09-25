# infra — IaC (AWS)

**콘솔 수작업 0.** 모든 리소스는 여기서 나온다.

## 배포 단위 5개

| 단위 | 담는 도메인 | 프로파일 |
|---|---|---|
| core-api | D1 D2 D3 D4 D6 D8 | 상시 가동 · 지연 민감 |
| pipeline-worker | D5 | 배치 · 스팟 · scale-to-zero |
| viz-render | D7 | 타일 + CDN |
| **ai-service** | D9 D10 | **장애가 core-api를 막지 않는 배치** |
| frontend | — | 정적 + CDN |

## 환경

⭑ **⟨개정 2026-09-24 · Ted 판정⟩ 배포 환경은 local · dev · prod 셋이다.**
- **local** = `infra/staging/`. 디렉터리·컨테이너(`colab_v2_staging_*`)·compose 프로젝트·스크립트 이름(`--target staging` 포함)은 **호환을 위해 그대로 둔다** — 이름에 staging 이 남아 있어도 staging 환경이 아니다.
- **`www.colab-hydro.com` 은 prod 다.** 관측 근거와 미확인 사항은 `prod/README.md §0`. 종전의 「`www.colab-hydro.com` = staging 터널」은 폐기(`staging/README.md` 상단).

| 환경 | 어디 · 진입 | 용도 |
|---|---|---|
| dev / test | 로컬 컨테이너 | 도메인 구현 · 게이트. **AWS 불필요** · 배포 환경 아님(아래 local 과 별개) |
| **local** (디렉터리 `infra/staging/` · 종전 명칭 staging) | 개발자 PC **WSL2**(`docker compose` · 저장 `local`) · 진입 `http://127.0.0.1:3000`(nginx) · 공개 주소 없음 | **리허설 — 판정 아님.** 배포 절차 예행 · 게이트 전수 · 마이그레이션 예행 |
| **dev** | AWS 서울(EC2 + RDS + S3 + CloudFront) · 저장 `s3` · 진입 `https://d31zgpff2091oh.cloudfront.net` | **판정처.** 완료 = dev 배포 green ＋ `deploy_doctor` 14/14 한 번의 실행 |
| **prod** | AWS · 진입 **`https://www.colab-hydro.com`**(공개 도메인) · 배포 기본 주소 `d1aje00ns2hjsl.cloudfront.net` | 운영 — product의 사람 병합 SHA와 prod 태그를 배포 기준으로 전환 중. 현재 준비 상태는 `docs/DEPLOY_PRODUCT.md` |

／ 종전 표의 ~~`| staging | **WSL2 로컬**(…) | **리허설 — 판정 아님.** … |`~~ 은 **이름만 바뀌었다** — 실물(개발자 PC 의 스택)은 같다.

⭑ **⟨정정 2026-09-05 · `PLAN-SoT §9 〈335〉`-㉵-⑵ · PR #1 병합 커밋에서 집행⟩** 종전 표의 ~~`| staging | AWS (축소) | 배포 경로 검증 |`~~ 은 **실물과 달랐다** — staging 은 AWS 가 아니라 **WSL2 머신 1대**이고 저장 모드는 `s3` 가 아니라 **`local`**(도커 볼륨 `uploads`)이다. 그래서 **staging green 이 dev 동작을 보증하지 않는다** — SigV4 서명 · 프리사인드 URL · `V-4` 커널 내려받기는 staging 에서 아예 실행되지 않는다(`〈335〉`-㉱-⑴).

로컬 DB는 관리형 DB와 **같은 엔진·같은 확장**으로 맞춘다 — RLS·테넌트 격리·공간/벡터 확장을 로컬에서 동일하게 검증하기 위해서다.

## Walking skeleton (WU-I2)

**P0 직후, 빈 서비스 5종을 staging에 한 번 올린다.** 이후 모든 WU의 완료 판정에 staging 배포 green이 붙는다.
통합 지옥은 기능이 아니라 배포 경로에서 오고, 마지막에 몰면 되돌릴 시간이 없다.

⭑ **⟨개정 2026-09-24⟩ 이 절은 이력이다.** 여기의 staging 은 지금 local 환경이고, 완료 판정처는 dev 다(위 표 · `〈335〉`).

## 반드시 들어가는 것

- 예산 알람 + 태그 기반 귀속
- 데이터 레지던시 — 국내 리전 고정. **AI 모델 호출의 처리 위치를 명시적으로 기록**
- 시점 복구 + 복원 리허설 1회
- **롤백 경로** — I2에서 배포와 함께 증명
- 객체 스토리지 VPC 엔드포인트 (NAT 데이터 요금 회피)
- 분산 추적 — AI는 운영 수동 디버그가 불가능하다
