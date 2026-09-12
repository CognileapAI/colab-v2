# R-LOGIN-BACKOFFICE 작업 5 — dev 배포 3차 **사후 검증**(읽기 전용)

- 작성 2026-09-13(UTC 2026-09-12 18:53~19:0x) · 레인 `worktree-agent-a208f4d69f32a7f1e` · 기준 `origin/main` `acf2532f`(`merge --ff-only` → `Already up to date`)
- 성격 = **읽기 전용 실측.** 배포·재기동·`docker load`·`up.sh`·DB 쓰기 0. 접속 문자열·비밀번호·토큰 미기재.
- 결론 = **dev 실적용 sha `6ff0eecd2cba` · 4 단위 healthy · 상세 읽기 전용 수정은 CloudFront 번들에 실재.**
  **`deploy_doctor --env dev` 는 한 번의 실행에서 `✓ 14 · ✗ 1 · ─ 0`(exit 1)** — 15/15 아님.

## 1. 실물 계수

| 항목 | 실측값 | 관측 경로 |
|---|---|---|
| `CURRENT_SHA` | `6ff0eecd2cba` | EC2 `cat /opt/colab-v2/CURRENT_SHA` |
| `MAIN_SHA` | `main=6ff0eecd2cba candidate=6ff0eecd2cba ancestor=yes` | EC2 `cat /opt/colab-v2/MAIN_SHA` |
| 컨테이너 | 4종 전부 `Up 21 minutes (healthy)` | `docker ps` |
| 컨테이너 이미지 표기 | `pipeline_worker`·`ai_service` = `colab-v2/*:dev-6ff0eecd2cba` · **`core_api`=`7f5f2f5d7400` · `viz_render`=`15f246076f60`(태그 없는 ID)** | `docker ps --format` |
| 2시간 내 변경(`/opt/colab-v2`) | `images/colab-v2-dev-6ff0eecd2cba.tar` · `colab-ops-source-6ff0eecd2cba.tar.gz`·`.manifest` · `up.sh` · `CURRENT_SHA` · `MAIN_SHA` · `dev.env` · `compose.yml` — 전부 2026-09-12 18:29 UTC | `find -mmin -120` |
| 배포 잠금 파일 | `/opt/colab-v2/.stage3-deployment.lock`(09-12 01:52) · `/tmp/colab-v2-dev-deploy.lock`(09-10 02:20) — **둘 다 2시간 밖**, 진행 중 잠금 0 | `find -iname '*.lock'` |
| platform head(살아 있는 DB) | **`public.alembic_version_platform = 0031_search_evidence`** | `colab_owner` 로 `SELECT` 1회(읽기 전용) |
| ai head(살아 있는 DB) | `public.alembic_version_ai = 0007_merge_vocab_and_category` | 같은 경로 |
| EC2 `/opt/colab-repo` platform versions 최신 | **`0030_merge_operator_audit_and_backoffice.py`**(`0031` 부재) | EC2 `ls` |
| 디스크 | 14G 사용 · 6.4G 여유 · 69% | EC2 `df` |

## 2. `deploy_doctor --env dev` — 한 번의 실행

진입점 = EC2 `sudo bash /opt/colab-repo/infra/ops/probes/deploy-verification.sh`(`--allow-skip` 미사용 · 재시도 0 · 부분 실행 합산 0).

```
항목 15 — ✓ 14 · ✗ 1 · ─ 0
RED (실패 1건) · 고치는 법: dev-package/S3.md §1 · infra/dev/README.md
DOCTOR_EXIT=1
```

- 유일한 `✗` = **⑥ 스키마 head (platform)**. 나머지 14 항목 `✓`(⑦ `0007_merge_vocab_and_category` · ⑩ 5 단위 헬스 · ⑪ 자격 출처 `imds` · 만료 283분 · ⑬ `/api/v1/me` 401 JSON · `/previews/*` 403 · ⑭ 백업 0.4시간 전 · 객체 57건 · ⑮ `6ff0eecd2cba ∈ main (origin/main=6ff0eecd2cba · 반입 시 조상 확인됨)`).
- **원인 = 판정 기준이 되는 EC2 배포 레포 트리가 낡았다.** 살아 있는 DB `0031_search_evidence` ↔ `/opt/colab-repo/db/platform/versions` 최신 `0030`. `infra/dev/README.md` 「⭑ 선행 단계 — `deploy_doctor` 전에 `/opt/colab-repo` 를 배포 sha 로 맞춘다」를 동시 배포 측이 밟지 않았다(`deploy-3.md` 「남은 것」 ⑴ 과 같은 항목).
- **DB 쪽 결함이 아니다** — 실행 중 코드(`6ff0eecd2cba`)에 `0031_search_evidence` 가 들어 있고 DB 도 `0031` 이다. 어긋난 것은 **대조용 레포 트리 하나**다.
- `deploy_doctor.py` md5(EC2) = `a2d5651512ff786f0a71eeb36e51ed9c` — `deploy-2.md` ④ 기록값과 동일.

## 3. 프런트 — 상세 읽기 전용 수정의 실재 확인

| 항목 | 실측값 |
|---|---|
| `index.html` | HTTP 200 · 953 B · md5 `c484e6ea64e9f7af04c06cbfb6a0febb`(`deploy-3.md` 기록값과 동일) |
| 주 번들 | `assets/index-DuCCGbNb.js` · HTTP 200 · 754,387 B · md5 `861700d847515a5e46ddf8e9141f885b` |
| `다른 연구실 데이터` | **1건** — 축자 `다른 연구실 데이터 — 읽기 전용` |
| `전체 연구실` | 2건 |

- 번들 축자가 `frontend/src/routes/DatasetDetailPage.tsx:238` 과 일치한다 ⟹ **커밋 `d538a064`(관리자가 보는 남의 연구실 데이터셋 상세 = 읽기 전용)가 dev 에 실재한다.**

## 4. 무자격 탐침 (상태 코드만 · 본문 미출력)

| 호출 | 실측 |
|---|---|
| `GET /api/v1/admin/accounts` | **401** · `application/json` · 본문 78 B |
| `GET /api/v1/me` | 401 |

## 5. 원한 결과 대조

| 지시문 항목 | 판정 |
|---|---|
| `CURRENT_SHA`·`MAIN_SHA`·`docker ps`·2시간 내 잠금/기록 파일·alembic head 2종 | 충족 |
| `deploy_doctor --env dev` 1회 | 충족(결과는 `✓14 ✗1`) |
| CloudFront 번들 문구 2종 계수 | 충족 |
| 무자격 `/api/v1/admin/accounts` 401 | 충족 |
| 보고서·HANDOFF 1행·커밋(미push) | 충족 |

- 초과분 = **0건**(배포·태그·코드 수정 0).
- 미달분 = **0건**. 단, **완료 조건(`CLAUDE.md` §0 「15/15 를 한 번의 실행으로」)은 미충족** — 이 레인의 산출이 아니라 dev 의 현 상태다.
- 절차 미달 1건 = alembic head 를 한 ssh 안에서 읽지 못해 **ssh 3회**를 썼다(1회차 = 앱 롤로 조회 실패 · 2회차 = 소유자 URL 경로 오인 · 3회차 성공). 지시문의 「ssh 1회」 대비 초과.

## 6. 후속 (「기존」이라 적지 않고 걸리는 검사를 적는다)

1. **⑥ `✗` 는 배포 레포 트리 동기화 누락이다.** 걸리는 검사 = `deploy_doctor` ⑥ 하나뿐이고, **동기화를 강제하는 자리는 없다**(`ship.sh` 에 단계 없음 · 게이트 없음 · 사람이 `infra/dev/README.md` 선행 단계를 기억해야 함). 고칠 자리 = `ship.sh` 가 ops 소스 번들과 같은 회차에 `/opt/colab-repo` 트리를 밀도록 단계화.
2. **`core_api`·`viz_render` 가 태그 없는 이미지 ID 로 동작한다.** 동시 배포의 `docker load` 가 같은 태그를 다른 빌드 결과에 재부착해 실행 중 컨테이너가 태그를 잃은 상태다. **걸리는 검사 = 없다** — `deploy_doctor` ⑩ 은 `/healthz` 만 보고, ⑮ 는 `CURRENT_SHA`/`MAIN_SHA` 문자열만 본다. 필요한 자리 = 실행 중 컨테이너의 이미지 ID ↔ `colab-v2/<서비스>:dev-<sha>` ID 대조 항목.
3. **배포 잠금이 호스트에 없다** — `deploy-3.md` 후속 1 과 같은 항목. 이번 실측에서 `/opt/colab-v2` 에 진행 중 잠금 파일이 0 인 것도 그 결과다(잠금은 각 작업 사본의 git common dir 에만 선다).

## 7. `[미확인]`

- **⑥ 항목의 상세 출력 축자** — 요약 블록만 회수했다(`✗` 한 건이 ⑥ 이라는 것은 요약 표에서 읽었다). 축자 대조가 필요하면 `deploy_doctor` 전문을 한 번 더 받아야 한다.
- **실행 중 `core_api`·`viz_render` 컨테이너가 `6ff0eecd2cba` 빌드인지** — 태그가 떨어져 문자열 대조가 불가능하다. 프런트 번들·`/api/v1/admin/accounts` 401 로 간접 확인될 뿐이다.
- **`0031_search_evidence` 적용 전 백업** — 부재(`deploy-3.md` 후속 3). 이 레인은 백업을 만들지 않았다(읽기 전용 지시).
