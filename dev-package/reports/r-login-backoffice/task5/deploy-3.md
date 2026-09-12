# R-LOGIN-BACKOFFICE 작업 5 — dev 배포 3차 시도 (`6ff0eecd2cba`) · **중단**

- 작성 2026-09-13 · 레인 `worktree-agent-af0cf96be3c0a8056` · 작업 id `03deced5e8a648ee86ef221dc0a8df3f`
- 결론 = **배포를 완주하지 않았다. `deploy_doctor` 를 돌리지 않았고 태그도 찍지 않았다.**
  원인 = **같은 sha(`6ff0eecd2cba`)를 같은 dev 호스트에 넣는 배포가 다른 작업 사본에서 동시에 돌고 있다.**
- 이 보고에 접속 문자열·비밀번호·토큰을 적지 않는다.

## 0. 지시문 전제의 정정 — 착수 시 dev 는 `71ee15757737` 이 아니었다

| 항목 | 지시문 전제 | 실물(착수 시 관측) |
|---|---|---|
| dev 실적용 sha | `71ee15757737` | **`321bdaef1201`** (`/opt/colab-v2/CURRENT_SHA`) |
| 이미 찍힌 태그 | `dev-20260913-1` 미사용 | **`dev-20260913-1` → `321bdaef1201` 사용됨**(커밋 `b0ebd4c6` · 원장 〈394〉) |

⟹ 이번 회차의 코드 델타는 `71ee1575..6ff0eecd` 가 아니라 **`321bdaef..6ff0eecd`**(142파일)이고,
태그를 찍었다면 `tag-release.sh` 규약상 **`dev-20260913-2`** 다(N = 같은 날 기존 태그 수 ＋1).

## 1. 착수 시점 실물 (2026-09-13 03:1x KST)

| 항목 | 값 | 관측 |
|---|---|---|
| 기준 | `git fetch origin && git merge --ff-only origin/main` → `Already up to date` · HEAD = `origin/main` = `6ff0eecd2cba7...` | 로컬 |
| `CURRENT_SHA` | `321bdaef1201` | EC2 `cat` |
| `MAIN_SHA` | `main=321bdaef1201 candidate=321bdaef1201 ancestor=yes` | EC2 `cat` |
| 컨테이너 4종 | `:dev-321bdaef1201` · 전부 healthy · `/healthz` 200 ×4 | EC2 |
| platform head | **`0030_merge_audit_and_backoffice`**(지시문 기대치와 일치) | 살아 있는 DB |
| ai head | `0007_merge_vocab_and_category` | 살아 있는 DB |
| 신규 마이그레이션 | **1건 — `db/platform/versions/0031_search_evidence.py`** (`db/ai/versions` 신규 0건) | `git diff --name-status 321bdaef 6ff0eecd -- db/` |
| 디스크 | 14G 사용 · 6.7G 여유 · 67% | EC2 `df` |
| `dev.env` | `ec2-user:ec2-user` 0600 · `COLAB_IMAGE_TAG=dev-321bdaef1201` | EC2 `ls -l` |
| 변경 서비스 | `core-api` · `ai-service` 소스 변경 있음 · `frontend/src` 변경 있음 | `git diff --name-only 321bdaef 6ff0eecd -- services frontend/src` |

## 2. 집행 — 공통 실행기 1회, 3단계에서 중단

진입점 = `python3 scripts/deploy_release.py run --plan <계획>`(`infra/releases/README.md` 축자).
계획 = `dist/release-r-login-260913-dv/release.json`(id `r-login-260913-dv-6ff0eecd2cba` · gitignore).
계획 JSON 에 비밀값 0. `--check` green 후 실행.

| 단계 | 시각(UTC) | exit | 내용 |
|---|---|---|---|
| deploy 0 — `01-build.sh` | 18:29:19 | 0 | `infra/dev/build.sh` — 5 이미지 `linux/arm64` 실측 통과 · `dist/colab-v2-dev-6ff0eecd2cba.tar` **298,765,312 B** |
| deploy 1 — `02-ship.sh` | 18:29:48 | 0 | `infra/dev/ship.sh` — 반입 게이트 `ancestor=yes` · `docker load` 5단위 · `ops source green — manifest 전건 일치` · `CURRENT_SHA`·`MAIN_SHA` 기록 |
| deploy 2 — `03-image-tag.sh` | 18:29:50 | **1** | `cp: cannot open '/opt/colab-v2/dev.env' for reading: Permission denied` |
| deploy 3~7 · verify 0~5 | — | 미실행 | 백업 · `up.sh` · 배포 레포 트리 · 프런트 · `deploy_doctor` **전부 돌지 않았다** |

`deployment: failed`. 기록 = `<git-common-dir>/deploy-releases/r-login-260913-dv-6ff0eecd2cba/`.

## 3. 중단 사유 — 같은 호스트에 배포가 둘이다 (판정 근거)

`dev.env` 는 착수 시 `ec2-user:ec2-user` 였고(§1), 3단계가 읽지 못한 시점에는 **`root:root` · mtime 18:29** 였다.
이 레인은 그 파일을 건드리지 못했으므로 **다른 주체가 그 사이에 `sudo` 로 고쳤다.**

실물 대조 — 다른 작업 사본 `30 CoLAB-v2` 의 배포 기록(읽기만 함):

| 기록 id | 시작(UTC) | 단계·종료코드 |
|---|---|---|
| `ai-search-dev-6ff0eecd2cba` | 18:26:56 | `predeploy` 0 · **`infra/dev/ship.sh` 0**(18:27:34) · `activate` **1** |
| `ai-search-dev-6ff0eecd2cba-recovery1` | 18:29:33 | `activate` **0**(18:30:02) · `grants` 1 |
| `ai-search-dev-6ff0eecd2cba-recovery2` | 18:31:12 | `grants` 0 · `web` **1**(`KeyError: 'SessionToken'`) |
| `ai-search-dev-6ff0eecd2cba-recovery3` | 18:32 | 관측 시점에 **진행 중** |

⟹ **이 레인의 `ship.sh`(18:29:07~18:29:48)와 저쪽의 `activate`(18:29:33~18:30:02)가 실제로 겹쳤다.**
저쪽 대상 sha 도 `6ff0eecd2cba` 로 같다(계획 `version`).

겹침의 흔적 3건 —

1. 이 레인의 `docker load` 출력 축자 — `The image colab-v2/core-api:dev-6ff0eecd2cba already exists, renaming the old one with ID sha256:7f5f2f5d7400…` · 같은 문장이 `viz-render`(`15f246076f60`)에도 나왔다. **이 sha 의 이미지가 반입 전에 이미 EC2 에 있었다** = 저쪽 `ship.sh`(18:27:34)의 것.
2. 그래서 지금 `docker ps` 의 `core_api`·`viz_render` 는 **태그가 떨어진 이미지 ID**(`7f5f2f5d7400`·`15f246076f60`)로 돌고 있다 — 저쪽 빌드이고, 이 레인의 `docker load` 가 그 태그를 가져갔다.
3. `pipeline_worker`·`ai_service` 만 `:dev-6ff0eecd2cba` 를 표시한다.

**중단 판정** — 한 배포 대상에 실행 주체가 둘이면 어느 쪽 결과도 그 호스트의 상태를 설명하지 못한다.
`deploy_release.py` 의 배포 잠금은 **각 작업 사본의 git common directory** 에 있어(`state_directory()` → `git rev-parse --git-common-dir`)
**다른 clone 의 배포를 막지 못한다.** 이 레인은 잠금을 잡고 있었고 저쪽도 자기 잠금을 잡고 있었다 — 둘 다 「단독」이라고 믿은 채 겹쳤다.

## 4. 중단 시점의 dev 실물 (읽기만 · 2026-09-13 03:33 KST)

| 항목 | 값 | 누가 만들었나 |
|---|---|---|
| `CURRENT_SHA` | `6ff0eecd2cba` | **이 레인**(`ship.sh`) |
| `MAIN_SHA` | `main=6ff0eecd2cba candidate=6ff0eecd2cba ancestor=yes` | **이 레인** |
| `dev.env` | `root:root` 0600 · `COLAB_IMAGE_TAG=dev-6ff0eecd2cba` | 저쪽 |
| 컨테이너 | 4종 healthy · `core_api`·`viz_render` 는 태그 없는 ID · `pipeline_worker`·`ai_service` 는 `:dev-6ff0eecd2cba` | 저쪽 기동 ＋ 이 레인 load |
| `/healthz` | 8000·8001·8100·8200 **전부 200** | — |
| platform head | **`0031_search_evidence`** (적용됨) | 저쪽 `activate` |
| ai head | `0007_merge_vocab_and_category`(무변) | — |
| `/opt/colab-repo/db/platform/versions` | 최신 `0030_merge_operator_audit_and_backoffice.py` — **`0031` 없음 · 낡음** | 아무도 안 밂 |
| CloudFront `index.html` md5 | `c484e6ea64e9f7af04c06cbfb6a0febb` (직전 판 `0badd9b537be392124331a3e35d58e4c` 와 다름) | 저쪽 web 단계 |
| 디스크 | 14G 사용 · 6.4G 여유 · 69% | — |

⚠ **`0031_search_evidence` 는 적용 전 백업 없이 올라갔다.** `/var/log/colab-backup.log` 의 마지막 행은
`2026-09-11T190001Z … GREEN` 이고 2026-09-13 세대가 없다. 이 레인의 백업 단계(deploy 3)는 3단계 실패로 **실행되지 않았다.**

### 무자격 API 확인 (지시문 요구분 — 상태 코드만, 본문·토큰 미출력)

| 호출 | 실측 | 판독 |
|---|---|---|
| `GET /` | **200** | 진입 정상 |
| `GET /api/v1/me` | **401** | 인증 앞단 동작 |
| `GET /api/v1/admin/accounts` | **401** | 경로 존재 |
| `GET /api/v1/datasets/01M1SCC27AN4NZD3K978YFDCVD`(실재 id) | **401** | 경로 존재 |
| `GET /api/v1/no-such-route-control` | **404** | **대조군** — 위 401 이 「존재」를 뜻한다는 근거 |

실재 id 의 출처 = `colab_app` 롤로 `app.current_lab` 을 건 뒤 `d3_dataset` 조회(읽기만). 경계 롤 자격은 쓰지 않았다.

## 5. 이 레인이 호스트에 남긴 것 (되돌리지 않았다 — 되돌리는 것도 배포다)

1. `/opt/colab-v2/images/colab-v2-dev-6ff0eecd2cba.tar`(298,765,312 B) ＋ `colab-ops-source-6ff0eecd2cba.tar.gz`·`.manifest`.
2. 이 레인 빌드의 5단위 이미지 — `:dev-6ff0eecd2cba` 와 `:dev` 태그를 갖고 있다. 저쪽 빌드 2건은 태그를 잃었고 컨테이너가 잡고 있다.
3. `/opt/colab-v2/CURRENT_SHA`·`MAIN_SHA` = `6ff0eecd2cba`(값 자체는 두 배포의 목표가 같아 동일하다).

⛔ **DB 쓰기 0 · 마이그레이션 실행 0 · `purge_datasets.py` 미실행 · `main` push 0 · 태그 push 0 · 로컬 태그 0.**

## 6. 다음에 필요한 것 (오케스트레이터 판정 사항)

1. **어느 한 쪽으로 실행 주체를 정한다.** 저쪽(`30 CoLAB-v2` · `ai-search-dev-*`)이 더 진행돼 있고(마이그레이션·grants·프런트 완료) 프런트 자격 오류 하나만 남아 있다. 이 레인이 이어받으려면 저쪽을 먼저 멈춰야 한다.
2. 어느 쪽이 완주하든 **남은 것은 같다** — ⑴ `/opt/colab-repo` 를 `6ff0eecd2cba` 트리로 밀기(안 밀면 `deploy_doctor` ⑥ 이 `0030` 을 정답으로 삼아 조용히 틀린다) ⑵ `deploy_doctor --env dev` **한 번의 실행** ⑶ `dev-20260913-2` 로컬 태그.
3. **`0031` 적용 전 백업이 없다.** 되돌릴 수 없는 상태이므로 지금 `sudo /opt/colab-v2/backup.sh` 로 **적용 후 세대**를 세워 두는 것이 차선이다(적용 전 세대는 `_ops/backups/dev/` 의 직전 일일분 ＋ RDS 자동 백업 1일뿐이다).

## 7. 원한 결과 대조 (미달 · 초과)

지시문 기준.

| 항목 | 판정 |
|---|---|
| 기준 맞추기(`ff-only`) · 범위 판정 | 충족 |
| 선행 점검(healthy · `alembic_version_platform` · 신규 마이그레이션 유무) | 충족 |
| 백업 후 마이그레이션 | **미달** — 3단계 실패로 백업 미실행. 마이그레이션은 저쪽이 백업 없이 적용 |
| 이미지 빌드·반입 | 충족(반입까지) |
| 교체(`up.sh`)·healthy | **미달** — 이 레인은 실행하지 않음. 호스트는 저쪽 기동으로 healthy |
| 프런트 `deploy_web.py` · CloudFront hash 대조 | **미달** — 이 레인 미실행 |
| 배포 레포 트리 동기화 | **미달** — 미실행. 호스트 트리는 `0030` 세대 |
| `CURRENT_SHA`/`MAIN_SHA` | 충족 |
| `deploy_doctor` 15/15 한 번의 실행 | **미달** — 돌리지 않았다. 부분 결과도 없다 |
| 무자격 탐침 401 2건 | 충족(§4) |
| 로컬 태그 | **미달** — 찍지 않았다(완주하지 않은 배포에 태그를 찍지 않는다). 찍을 이름은 `dev-20260913-1` 이 아니라 **`dev-20260913-2`** |
| 보고·HANDOFF·커밋 | 충족 |

- **미달 7건**(위 표) — 전부 같은 원인 하나(동시 배포)로 막혔다.
- **초과 0건.**

## 8. 후속 항목 (이 레인은 고치지 않았다)

1. **`deploy_release.py` 의 배포 잠금이 작업 사본을 넘지 못한다.** `state_directory()` 가 `git rev-parse --git-common-dir` 로 잠금 자리를 정하므로 **같은 레포의 다른 clone 두 벌이 같은 호스트에 동시에 배포한다.** ⟹ **걸리는 검사 = 없다.** 게이트에도 `deploy_doctor` 15항목에도 「지금 다른 배포가 이 호스트에 붙어 있는가」를 보는 자리가 없다. 고칠 자리 = 잠금을 **배포 대상(EC2)** 위에 두는 것(예 `ship.sh`·`up.sh` 가 `/opt/colab-v2/deploy.lock` 을 잡는다).
2. **`/opt/colab-v2/dev.env` 소유자가 배포마다 `root:root` 로 표류한다.** 착수 시 `ec2-user`(2026-09-12 회차가 복원해 둔 값) → 이번 회차 중 다시 `root`. 원장 〈394〉⑪ 가 이미 항목화 후보로 올린 건이고 **이번에 재현됐다.** 걸리는 검사 = 없다(`deploy_doctor` 에 파일 소유권 항목 없음) — 드러나는 자리는 `up.sh` 의 `permission denied` 하나다.
3. **`db/platform/versions/0031_search_evidence.py` 의 머리말이 실물과 다르다.** 축자 `Revises: 0027_operator_audit` 인데 코드는 `down_revision = "0030_merge_audit_and_backoffice"` 다. **걸리는 검사 = 없다** — `migration-single-head` 는 `down_revision` 만 읽고 docstring 을 보지 않는다.
4. **배포 레포 트리(`/opt/colab-repo`) 어긋남을 잡는 검사가 여전히 없다** — `deploy-2.md §6`③ 과 같은 항목이고 이번에도 실제로 어긋나 있다(`0031` 부재).
