# R-BUGFIX-260912 — dev 배포 기록 (`321bdaef1201`)

- 작성 2026-09-13 · 워크트리 `.claude/worktrees/bugfix-deploy-260912` · 브랜치 `worktree-bugfix-deploy-260912`
- 결론 = **`deploy_doctor --env dev` 항목 15 — ✓ 15 · ✗ 0 · ─ 0 · 한 번의 실행 · exit 0**(2026-09-13 01:10:58 KST). 재시도 0 · 부분 실행 합산 0 · `--allow-skip` 미사용.
- 대상 sha = **`321bdaef1201`** — 착수 시 `git rev-parse --short HEAD origin/main` 양쪽 `321bdaef`(ff 불필요).
- 이 보고에 접속 문자열·비밀번호·토큰·키 값을 적지 않는다.

## 0. 착수 시점 실물

| 항목 | 값 | 관측 |
|---|---|---|
| 로컬 HEAD · `origin/main` | `321bdaef` · `321bdaef` | `git fetch origin` 뒤 `rev-parse` |
| 착수 시 dev `CURRENT_SHA` | `71ee15757737` | EC2 `cat` |
| 착수 시 dev `MAIN_SHA` | `main=71ee15757737 candidate=71ee15757737 ancestor=yes` | EC2 `cat` |
| 착수 시 컨테이너 4종 | `:dev-71ee15757737` · 전부 healthy | EC2 `docker ps` |
| `71ee15757737` → `321bdaef1201` 의 `db/` diff | **0파일** — 이 회차에 신규 마이그레이션 없음 | `git diff --name-only 71ee15757737..HEAD -- db/` |
| platform head(적용 전·후 동일) | `0030_merge_audit_and_backoffice` | doctor ⑥ |
| ai head(적용 전·후 동일) | `0007_merge_vocab_and_category` | doctor ⑦ |

## 1. staging 리허설 — 재실행하지 않았다(같은 sha 로 이미 green)

판정처가 아니다(`CLAUDE.md §0` — staging = 리허설). **같은 sha 의 green 배포가 착수 직전에 이미 있었다.**

| 항목 | 값 |
|---|---|
| 원장 행 | `~/colab-v2-releases/release-ledger.tsv` — `2026-09-13T00:55:56+0900 deploy 321bdaef1201 321bdaef1201 green 별칭재부착GREEN digest이력=6종 배포전백업GREEN 워킹트리변경=0 브랜치=staging/auto-deploy` |
| 이미지 | 앱 5종 전부 `colab-v2/<단위>:321bdaef1201` |
| 컨테이너 | **8/8 healthy**(`nginx`·`cloudflared`·`pg`·`core_api`·`frontend`·`pipeline_worker`·`viz_render`·`ai_service`) |
| 헬스(`RESTART.md ②-③` 지정 명령) | **6/6 200** — root ＋ `core-api`·`frontend`·`pipeline-worker`·`viz-render`·`ai-service` 단위별 `/healthz/<unit>` |
| 자동 파이프라인 | `2026-09-13T01:00:06 새 커밋 없음 (321bdaef1201) — 돌지 않는다` |

⟹ `approve.sh` ＋ `deploy.sh --target staging` 을 다시 치면 **같은 트리를 다시 굽고 원장에 중복 green 행을 더할 뿐 근거를 더하지 않는다**(`.claude/rules/colab-rules.md §3-2` 와 같은 판단기준). 어드바이저 게이트 ③ 도 같은 판정.

## 2. 집행 전 해소한 차단 2건

### 2-1. EC2 디스크 92% — 전송 산출물 tar 19건 삭제

- 착수 실측 = `/dev/nvme0n1p1 20G 19G 1.8G 92%` · `du /opt/colab-v2/images` **5.6G**.
- 삭제 대상 = `/opt/colab-v2/images/colab-v2-dev-*.tar` 중 **실행 중 sha `71ee15757737` 것을 뺀 19건**. `colab-ops-source-*.tar.gz`·`*.manifest` **무수정**(`ship.sh` 의 `verify-reimport.sh` 가 읽는 자리).
- 근거 = tar 소비자는 `infra/dev/ship.sh` 의 `docker load -i` **한 자리뿐**이고, 되돌리기는 `docs/DEPLOY.md §6-2`(`COLAB_IMAGE_TAG=dev-<직전 sha>` ＋ `up.sh`)라 **로컬 도커 이미지**를 쓴다. 삭제 대상 19 sha 전부 5단위 이미지가 남아 있음을 삭제 전에 계수(`images=5` ×19).
- 결과 = **14G 사용 · 7.0G 여유 · 66%**.
- 어드바이저 게이트 ③ = approve.

### 2-2. EC2 `dev.env` 의 `COLAB_IMAGE_TAG` 고정 — 계획에 단계 1개 추가

- 실측 = `/opt/colab-v2/dev.env` 에 **`COLAB_IMAGE_TAG=dev-71ee15757737`** 고정. 계획 `notes` 는 「움직이는 `:dev` 를 쓴다」를 전제했으나 실물이 다르다.
- 방치했을 때 = `ship.sh` 가 `CURRENT_SHA`·`MAIN_SHA` 를 새 sha 로 적고 `up.sh` 는 **옛 이미지를 다시 띄운다.** `deploy_doctor` ⑮ 는 문자열 대조라 **green 인 채로 제품이 안 바뀐다** — green-by-skip 형제다.
- 처치 = 계획 `deploy` 배열의 **`ship.sh` 뒤·`up.sh` 앞**에 한 단계 삽입. 직전 파일은 `/opt/colab-v2/dev.env.bak-before-321bdaef1201` 로 보존.
- 반영 뒤 `--check` 재실행 green.

## 3. 집행 — 실행기 2회(1차 실패 · 복구 성공)

진입점 = `python3 scripts/deploy_release.py run --plan <계획>` 하나. `build.sh`·`ship.sh`·`up.sh`·`deploy_web.py` 단독 실행을 배포 완료로 세지 않았다. 계획 JSON 에 비밀값 0.

| 배포 기록 id | 결과 | 단계 |
|---|---|---|
| `r-bugfix-260912-dv` | `deployment: failed` (deploy 3 exit 14) | build ✓ · ship ✓ · dev.env 태그 ✓ · **`up.sh` ✗** |
| `r-bugfix-260912-dv-2` | **`deployment: verified`** | 배포 5/5 · 검증 7/7 전부 exit 0 |

실행 기록 = `.git/deploy-releases/<id>/`(레포 추적 대상 아님) · 회차 로그 사본 = 이 폴더.

### 3-1. 1차 실패 — `dev.env` 소유자가 `root` 라 `up.sh` 가 못 읽는다

```
① 마이그레이션 — 소유자 롤로, 체인마다 따로
open /opt/colab-v2/dev.env: permission denied
```

- 원인 = `/opt/colab-v2/dev.env` 가 **`root:root` 0600** 인데 `up.sh` 는 **`ec2-user`** 로 돌고 `docker compose --env-file` 로 읽는다.
- **이 회차가 만든 것이 아니다** — 같은 폴더의 `dev.env.pre-tl2-d56428d6945d`(2026-09-06)·`dev.env.bak-before-medium`(2026-08-31)은 **`ec2-user:ec2-user`** 다. 2026-09-12 회차가 `sudo` 로 편집하며 소유자를 바꿔 놓았고, 그 회차는 `up.sh` 를 실행기 밖에서 쳤기 때문에 드러나지 않았다.
- 처치 = `sudo chown ec2-user:ec2-user /opt/colab-v2/dev.env` ＋ `chmod 0600` — 문서화된 호출(`infra/dev/README.md:67` 축자 `/opt/colab-v2/up.sh`)과 2026-09-06 이전 상태로 되돌린 것이다. `up.sh` 를 `sudo` 로 바꾸는 우회는 쓰지 않았다.
- **서비스 영향 0** — 실패 지점이 마이그레이션 앞이라 컨테이너를 내리지 않았고, 그 시점까지 dev 는 `71ee15757737` 로 계속 서 있었다.

### 3-2. 복구 계획 — 끝난 단계는 다시 치지 않는다

`infra/releases/README.md` 축자 「동일 id 에 다른 계획/버전/입력을 넣으면 거부한다」 ＋ 「같은 id 로 무조건 재배포하지 않는다」 ⟹ 새 id `r-bugfix-260912-dv-2`. 1차에서 exit 0 으로 끝난 `build.sh`·`ship.sh`·`dev.env` 태그 단계를 뺐다(뺀 이유를 계획 `notes` 에 축자 기록).

| 단계 | 시각(UTC) | exit |
|---|---|---|
| deploy 0 — 원격 `up.sh` | 16:09:43 | 0 |
| deploy 1 — EC2 `/opt/colab-repo` tar 동기화 | 16:09:45 | 0 |
| deploy 2 — `npm ci --prefix frontend` | 16:10:29 | 0 |
| deploy 3 — `npm run build --prefix frontend` | 16:10:46 | 0 |
| deploy 4 — `ops/deploy_web.py` → `colab-platform-web-dev` | 16:10:53 | 0 |
| verify 0~6 | 16:10:54 ~ 16:10:58 | 0 ×7 |

## 4. 단계별 증거

### ① 빌드·반입 (1차에서 완료)

- `infra/dev/build.sh` — 5 이미지 **`linux/arm64` 실측 통과**(`core-api`·`pipeline-worker`·`viz-render`·`ai-service`·`migrator` 전부 `→ arm64 ✓`) · `dist/colab-v2-dev-321bdaef1201.tar` **298,747,904 B**.
- `infra/dev/ship.sh` — 반입 게이트 통과 · `ops source green — CURRENT_SHA 321bdaef1201 · manifest 전건 일치` · `loaded: dev-321bdaef1201` · 5단위 `:dev` 재태그.
- `COLAB_SHIP_ALLOW_NONMAIN` 미사용.

### ② 마이그레이션 — 신규 0건

`up.sh` ① 단계가 두 체인을 그대로 쳤고 신규 리비전이 없어 head 무변(`0030_merge_audit_and_backoffice` · `0007_merge_vocab_and_category`). `db/` diff 0파일이므로 **적용 전 별도 백업을 세우지 않았다** — doctor ⑭ 가 기존 세대를 「1.9시간 전 · 객체 55건」으로 확인한다.

### ③ 기동 — 4 단위 healthy · 모드 s3

```
③ healthy 대기 (4 단위 · 최대 120 s)
   colab_v2_dev_core_api              healthy
   colab_v2_dev_pipeline_worker       healthy
   colab_v2_dev_viz_render            healthy
   colab_v2_dev_ai_service            healthy
④ 헬스 본문 (모드가 s3 인지 — 조용한 local 을 여기서 잡는다)
{"unit":"core-api","status":"alive","implemented":true}
{"unit": "pipeline-worker", "status": "alive", "implemented": true, "storageMode": "s3"}
{"unit":"viz-render","status":"alive","implemented":true,"sourceMode":"s3","previewSink":"s3","tileBranch":"꺼짐"}
{"unit":"ai-service","status":"alive","implemented":true}
up: ok (sha 321bdaef1201)
```

### ④ 배포 레포 트리 동기화 — doctor ⑥⑦ 앞

`deploy_doctor` 가 `--repo` 트리의 `db/<체인>/versions` 와 `gates/tools` 를 읽는다. 동기화 뒤 판정 = **`deploy_doctor.py` md5 로컬 = EC2 `a2d5651512ff786f0a71eeb36e51ed9c`**(검증 0단계, exit 0).

### ⑤ 프런트 정적 번들

- `npm ci` → `npm run build`(`tsc --noEmit && vite build`) → `ops/deploy_web.py`(실행기 자식) — **96 파일 · 6,551,451 B · `index.html` 마지막 · `no-cache`** · 해시 자산 `immutable`.
- **CloudFront `index.html` md5 = 로컬 빌드 md5 `0badd9b537be392124331a3e35d58e4c`** — 일치(검증 6단계).
- 직전 판은 `f59709d887d84af9f919ce860385511e` 였다 — 값이 바뀌었으므로 갱신이 실제로 반영됐다.
- 새 자산 = `assets/index-CcgJwgbA.js` · `assets/index-TrDdINPa.css`.

### ⑥ `deploy_doctor --env dev` — 한 번의 실행

전문 = `doctor.txt`. 축자 요약줄 —

```
  항목 15 — ✓ 15 · ✗ 0 · ─ 0
  전 항목 통과 (─ 0 — 15 항목이 실제로 돌았다)
```

- 실행 1회(2026-09-12 16:10:57Z = 2026-09-13 01:10:57 KST) · 재시도 0 · `--allow-skip` 미사용 · 부분 실행 합산 0.
- 집행 방식 = `docs/DEPLOY.md §6-1` 축자 명령(EC2 위 컨테이너 격리 · `-v /opt/colab-v2:/state:ro` 포함 · 이미지 `colab-v2/core-api:dev`).
- 주요 항목 — ⑥ `0030_merge_audit_and_backoffice (DB = 레포)` · ⑦ `0007_merge_vocab_and_category` · ⑧ 테이블 **50건** 전부 FORCE RLS ＋ 경계 정책 · ⑨ `colab_app` 소유 0(전체 41: `colab_owner` 41) · ⑪ 앱 자격 출처 **`imds`**(328분 남음) · ⑬ `/api/v1/me` 401 JSON · `/previews/*` 403 비-HTML · ⑭ 백업 **1.9시간 전 · 객체 55건**.
- ⑮ 축자 = `321bdaef1201 ∈ main (origin/main=321bdaef1201 · 반입 시 조상 확인됨)`.

### ⑦ 상태 파일·공개 진입 (검증 2~5단계)

```
MAIN_SHA=main=321bdaef1201 candidate=321bdaef1201 ancestor=yes
CURRENT_SHA=321bdaef1201
root=200
api/v1/me=401
```

공개 진입 = `https://d31zgpff2091oh.cloudfront.net`.

### ⑧ 운영자 키 취급

- `/tmp/op.env`(EC2, `umask 077` · **0600** · 3줄)를 **표준입력으로만** 심었다 — 값이 argv·쉘 이력·로그에 남지 않는다. 출처는 이 호스트의 `~/.aws/credentials` 프로필 `colab-dev`.
- `deploy_doctor` 실행 직후 **`shred -u /tmp/op.env`** — 사후 확인 `OP_ENV_GONE`.
- `deploy_web.py` 의 자격은 `kernel/aws_credentials.py` 사슬(env→ECS→IMDS)의 **로컬 도구 분기**로만 넘겼다(env 변수 · 파일 미생성). EC2 env 에는 액세스 키를 넣지 않았다(`.claude/rules/deploy.md` 「깨뜨리면 안 되는 것」 2).

## 5. 태그

- `bash infra/dev/tag-release.sh dev` → **`dev-20260913-1` → `321bdaef1201`**. 같은 날 기존 `dev-20260913-*` **0건**이라 N=1(자정 지난 KST).
- 대상 sha 는 로컬 `dist/colab-v2-dev.sha` 이고 EC2 를 읽지 않는다(스크립트 규약). 이번에는 **실적용 sha 와 같다**.
- **원격 반영 완료** — `git push origin dev-20260913-1` · `* [new tag] dev-20260913-1 -> dev-20260913-1`. 개별 push 만 사용(`git push origin --tags` 미사용).

## 6. 소요

| 구간 | 시각(KST) | 소요 |
|---|---|---|
| staging 리허설 | 00:55:56 (자동 파이프라인 · 이 세션 밖) | — |
| 디스크·`dev.env` 차단 해소 | 01:03 ~ 01:06 | 약 3분 |
| 1차 실행(build·ship·태그 · `up.sh` 실패) | 01:06:50 ~ 01:07:35 | 45초 |
| 소유자 정정 | 01:08 | 약 1분 |
| 복구 실행(기동 ~ 검증 7/7) | 01:09:16 ~ 01:10:58 | **1분 42초** |
| dev 집행 계 | 01:01 ~ 01:11 | 약 10분 |

빌드는 이 워크트리의 buildx 캐시가 더워 약 2분에 끝났다(선례 50분은 찬 캐시 기준).

## 7. 읽기 전용·비가역 규율

- 사용자 데이터에 `SELECT` 외 조작 0. `DELETE`·`UPDATE`·손 DDL 0. `ops/purge_datasets.py` 미실행.
- `main` push 0. 태그 push 1건(승인 범위 · `dev-20260913-1`). 원격 브랜치 삭제 0. PR 조작 0.
- 삭제한 것 = EC2 전송 산출물 tar 19건 하나뿐(어드바이저 게이트 ③ approve · 이미지·되돌리기 경로 무손상).
- 접속 문자열·비밀번호·토큰·키를 화면·레포·보고 어디에도 적지 않았다.
- 이 폴더의 파일은 **커밋하지 않았다**(원장 행은 오케스트레이터 몫).

## 8. 원장 행 문안 (오케스트레이터가 `PLAN-SoT §9` 에 옮긴다 · 번호는 병합 직전 재실측)

> dev 배포 — 2026-09-13. 실적용 코드 sha `321bdaef1201`(= `origin/main` · ff 불필요). 태그 `dev-20260913-1` → `321bdaef1201`(push 완료).
> 마이그레이션 신규 0건 — platform head `0030_merge_audit_and_backoffice` · ai head `0007_merge_vocab_and_category` 무변(`71ee15757737..321bdaef1201` 의 `db/` diff 0파일).
> 프런트 번들 96파일 · `index.html` md5 `0badd9b537be392124331a3e35d58e4c` = CloudFront 본문 일치.
> `deploy_doctor --env dev` **항목 15 — ✓ 15 · ✗ 0 · ─ 0 · 한 번의 실행 · exit 0**(2026-09-13 01:10:58 KST) · ⑮ `ancestor=yes`.
> 집행 창 = 2026-09-13 01:01~01:11 KST. 실행기 기록 `r-bugfix-260912-dv`(1차 실패) · `r-bugfix-260912-dv-2`(verified).
> staging 리허설은 같은 sha 의 자동 배포 green(원장 `2026-09-13T00:55:56+0900` · 8/8 healthy · 헬스 6/6 200)으로 갈음했다.
> ⚠ 집행 전 차단 2건 해소 — EC2 디스크 92%(전송 tar 19건 삭제 → 66%) · `dev.env` 의 `COLAB_IMAGE_TAG` 고정(계획에 갱신 단계 1개 추가).
> ⚠ `/opt/colab-v2/dev.env` 소유자가 `root` 라 문서화된 `up.sh` 호출이 실패했다 — 2026-09-06 이전 상태(`ec2-user`)로 되돌려 해소(후속 항목).

## 9. 후속 항목 (이 회차는 고치지 않았다)

1. **`/opt/colab-v2/dev.env` 소유자가 표류한다.** 문서화된 `up.sh` 는 `ec2-user` 로 돌고 `--env-file` 로 그 파일을 읽는데, 소유자를 `root` 로 바꾸는 편집이 있으면 **다음 배포가 마이그레이션 앞에서 죽는다.** 걸리는 검사 = 없다(`deploy_doctor` 15항목에 파일 소유자 대조 0건). 고칠 자리 = `up.sh` 진입부의 읽기 가능 여부 확인, 또는 `ship.sh` 가 `dev.env` 소유자를 정렬.
2. **`ship.sh` 가 전송 tar 를 보존 정책 없이 쌓는다.** 17세대 5.6G 가 디스크 92% 의 원인이었다. `install-cron.sh` 의 잡 2개(백업·reap)에 정리가 없다. 고칠 자리 = `docker load` 뒤 tar 삭제 또는 최근 N세대 보존.
3. **디스크 여유를 보는 검사가 없다.** `deploy_doctor` 15항목·`infra/ops/probes` 어디에도 `df` 항목이 0건이다. 성격은 green-by-skip 이 아니라 **검사 부재** — 15/15 가 green 인 채로 다음 반입이 ENOSPC 로 죽을 수 있다.
4. **배포 레포 트리 어긋남을 잡는 검사가 여전히 없다**(`task1-deploy/release.md §6` · `task5/deploy-2.md §6` 과 같은 항목 · 이번에는 계획 단계로 덮었으나 게이트는 아니다).
5. **`account-admin-role.sql` 의 RDS 미성립**(`task5/deploy-2.md §6-1`)은 그대로 열려 있다 — 이 회차는 롤 SQL 을 다시 치지 않았다.
