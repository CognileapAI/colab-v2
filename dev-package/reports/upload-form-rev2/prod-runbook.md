# prod 임시 검증 배포 — 실행 런북 (레인 커밋을 prod 에 굽는 절차)

⛔ **완료 판정이 아니다.** `CLAUDE.md §0` 의 완료 조건(dev 배포 green ＋ `deploy_doctor` 15/15 를
한 번의 실행으로)과 다른 절차다. 이 런북은 `dev-package/reports/dl-2/prod-test-20260913.md`
(`DL-2` 1·2차)와 같은 방식 — **레인 커밋을 임시로 굽고 삭제 대신 이번엔 업로드 화면을 눌러 본다.**

기점 = `feature/rtf400_upload_form` HEAD `f3761526c8345132e87d5934ab9bffc18efc85e0`.

```
git reset --hard feature/rtf400_upload_form
```

비밀값(키·비밀번호·접속 문자열·호스트 IP)은 이 문서 어디에도 적지 않는다 — 변수 이름과
파일 경로만 적는다.

---

## 1. 전제 — 이 브랜치에 없는 것 / 낡은 것

`feature/rtf400_deploy_prod`(브랜치 HEAD `915ccaaa3c9e`)를 배포 도구의 정본으로 삼는다.
실측(`git ls-tree` 대조, 두 브랜치 모두 `git show <브랜치>:<경로>` 로 읽었다) —

| 경로 | 이 브랜치(`f3761526`) | 필요한 조치 |
|---|---|---|
| `infra/prod/` (21 파일) | **없음**(`git ls-files` 0) | 전부 신규 복사 |
| `infra/_lib/`(`ship-gate.sh`·`ops-bundle.sh`, 2 파일) | **없음**(0) | 전부 신규 복사 |
| `infra/dev/tag-release.sh` | **있음 · 낡음** — `MODE` 별 sha 파일 분기(`colab-v2-$MODE.sha`)·prod 같은 날 재실행 시 같은 sha 재사용 허용 로직이 없다 | 덮어쓰기 |
| `services/core-api/ops/deploy_doctor.py` | **있음 · 낡음** — ⑮(실행 sha ∈ main) 항목 자체는 이미 있으나, **데이터 버킷 CORS 검사가 `--env` 와 무관하게 `localhost:5173` 고정**이다. `S3.md §1`(prod 는 와일드카드·개발 오리진 금지)대로 prod CORS 를 두면 이 낡은 판이 **② 를 거짓 ✗ 로 낸다**(dev 실측 근거 · 정본 커밋 diff) | 덮어쓰기 — 안 하면 doctor 결과가 왜곡된다 |
| `services/core-api/ops/s3_doctor.py` | **있음 · 낡음** — `check_bucket(origin: str)` 이 `None` 을 못 받아 위 CORS 분기와 짝이 안 맞는다 | 덮어쓰기(위 항목과 쌍) |
| `scripts/deploy_release.py` | **있음 · 낡음** — 배포 대상이 `dv`·`st` 만 허용, **`pr`(prod) 미지원** | 덮어쓰기 — 없으면 §2-ⓔ 가 `ReleaseError` |
| `scripts/slack_completion.py` | **있음 · 동일**(diff 0) | 조치 없음 |
| `infra/notifications/{install-runtime-cron,run-runtime-job}.sh` | **있음 · 소폭 다름**(prod 갈래 추가) | 이번 임시 검증은 크론 설치를 하지 않으므로(§1 참조 · `DL-2` 선례도 미설치) **범위 밖** — 실제 반입 회차에서만 갱신 |

**복사 방법** — 대상 경로가 신규(디렉터리째 없음)인 `infra/prod`·`infra/_lib` 는

```
git show feature/rtf400_deploy_prod:infra/prod/<파일명> > infra/prod/<파일명>   # 21개 반복
git show feature/rtf400_deploy_prod:infra/_lib/ship-gate.sh > infra/_lib/ship-gate.sh
git show feature/rtf400_deploy_prod:infra/_lib/ops-bundle.sh > infra/_lib/ops-bundle.sh
chmod +x infra/prod/*.sh infra/prod/tests/*.sh
```

기존 파일을 덮어쓰는 넷은

```
git show feature/rtf400_deploy_prod:infra/dev/tag-release.sh > infra/dev/tag-release.sh
git show feature/rtf400_deploy_prod:services/core-api/ops/deploy_doctor.py > services/core-api/ops/deploy_doctor.py
git show feature/rtf400_deploy_prod:services/core-api/ops/s3_doctor.py > services/core-api/ops/s3_doctor.py
git show feature/rtf400_deploy_prod:scripts/deploy_release.py > scripts/deploy_release.py
```

**복사 파일 수 = 27**(신규 23 ＋ 덮어쓰기 4).

**삭제 규약** — 위 파일은 이 브랜치의 정식 변경물이 아니다(`DL-2` 와 같은 **미추적 오버레이**).
`git add`·커밋하지 않는다. 검증이 끝나면 `git clean -f infra/prod infra/_lib` ＋ 덮어쓴 4파일을
`git checkout -- <경로>` 로 원복한다. `main` 반입은 PR 병합으로만 한다(`docs/BRANCHING.md` 규칙 1).

---

## 2. 순서

### ⓐ 빌드 — 누가: 사용자(개발 기계) · 명령: `infra/prod/build.sh [dist]`

- 대상 sha = 그 워크트리 `HEAD`(옵션 인자 없음 · `git -C "$REPO" rev-parse --short=12 HEAD`) →
  §1 의 `git reset --hard` 를 먼저 해 둬야 `f3761526c834` 가 찍힌다.
- 이미지 태그 = `colab-v2/<unit>:prod` ＋ `colab-v2/<unit>:prod-f3761526c834`(불변).
- **5 유닛 전부** 짓는다 — `core-api`·`pipeline-worker`·`viz-render`·`ai-service`·`migrator`.
  선택 빌드 옵션이 없다(§4 참조 — `pipeline-worker`·`ai-service` 는 이번 계약 변경과 무관해도 같이 굽는다).
- 기대 출력 = 유닛마다 `아키텍처 ✓`, 끝에 `dist/colab-v2-prod-f3761526c834.tar` 와 `colab-v2-prod.sha`.
- 실패 시 = arm64 휠 없는 geo 스택 임포트가 빌드 실패로 드러난다(주석 그대로) — 탈출구는 README §탈출구(EC2 위 빌드), 이 런북 범위 밖.

### ⓑ 로컬 임시 태그 — 누가: 사용자 · 명령: `git tag`(push 금지)

- `infra/dev/tag-release.sh prod` 는 **`origin/main` 조상만** 태그하므로 이 레인 커밋(비조상)에는
  쓸 수 없다 — `DL-2` 도 같은 이유로 `git tag` 를 직접 썼다.
- `git tag prod-<YYYYMMDD>-<label> f3761526c8345132e87d5934ab9bffc18efc85e0`
  (`<label>` 은 이 검증을 식별할 짧은 문자열, 예 `upload-rev2-test`).
- **push 하지 않는다.** `infra/prod/ship.sh` 의 태그 검사(`ship_gate_require_prod_tag`)는
  `git tag --points-at`(로컬 조회)만 보므로 로컬 태그로 통과한다.

### ⓒ ship — 누가: **사용자가 터미널에서 직접 실행**(지난 `DL-2` 회차에 자동 분류기가 이 단계를 막았다) · 명령: `infra/prod/ship.sh [dist]`

- 필요 env: `COLAB_PROD_SSH`·`COLAB_PROD_KEY_FILE`(§3) ＋ **`COLAB_SHIP_ALLOW_NONMAIN=1`**(선언 —
  반입 게이트 ⑴ 비조상 검사를 명시 우회. 이 값이 없으면 exit 65).
- 태그 검사 ⑵ 는 ⓑ 의 로컬 태그로 통과. 통과하면 출력에 `MAIN_SHA main=… candidate=f3761526c834 ancestor=bypass` 가 찍힌다.
- 기대 출력 = 이미지 5 개 `docker load`·판정 레포(`REPO_SYNC_PATHS` = `db gates services/core-api/ops infra contracts`) 동기화·
  `prod.env COLAB_IMAGE_TAG=prod-f3761526c834` 갱신·`/opt/colab-v2/MAIN_SHA` 갱신.
- 실패 시 = exit 65(비조상·태그 없음, 우회·태그 누락 확인) · exit 78(`origin` 조회 실패, 네트워크 확인) · exit 2(tar 없음 — ⓐ 재실행).

### ⓓ `up.sh` — 누가: 사용자(EC2 SSH 안에서) · 명령: `/opt/colab-v2/up.sh`

- 마이그레이션 **0건 기대** — 이 브랜치는 `db/` 변경이 없다(`git diff origin/main feature/rtf400_upload_form -- db/` 결과 없음). prod 는 이미 `0031_search_evidence`(platform)·`0007_merge_vocab_and_category`(ai) 상태(`docs/DEPLOY.md §5-10` 실측표)이므로 `dc --profile migrate run --rm migrate-platform`·`migrate-ai` 는 **적용 대상 0건**으로 끝나야 한다. 0건이 아니면 브랜치 전제가 틀린 것이므로 멈추고 보고한다.
- 4 유닛 healthy 대기 · `curl .../healthz` 4포트 200.

### ⓔ 웹 배포 — 누가: 사용자(개발 기계) · 실행기: `scripts/deploy_release.py run --plan <plan.json>`(대상 `pr`)

- `<plan.json>` 형태는 `DL-2` 선례(`release.json`, 이 세션 스크래치 `release-dl2/`)를 그대로 따른다 —
  `targets[0].name = "pr"`, `deploy`/`verify` 에 프런트 빌드(`npm run build`) → `deploy_web.py --bucket colab-platform-web-prod` → 자산 해시 대조 스크립트를 각각 셸 명령 배열로 지정.
- `deploy_web.py` 실행 전에 `~/.config/colab-platform/prod.env` 를 `set -a; . …; set +a` 로 로드해야 AWS 자격이 실린다(변수 이름만 — 값은 §3 참조).
- **실행기 종료코드 78 은 실패가 아니다** — Slack 웹훅 비밀 파일(`~/.config/colab/slack-webhook`) 부재로 알림 단계 "준비"가 실패한 것이고, 배포·검증 단계 자체는 exit 0 일 수 있다(`docs/DEPLOY.md §4-1c` 1차 재배포 실측과 동일 갈래). 78 을 받으면 **배포·검증 두 단계의 개별 종료코드**를 로그에서 다시 확인한다.

### ⓕ doctor — 누가: 사용자(EC2 SSH 안에서, sudo) · 명령: `sudo bash /opt/colab-v2/deploy-doctor.sh`

- 준비 = 판정 레포 `/opt/colab-repo` 최신화(ⓒ 가 이미 했다) ＋ 운영자 AWS 키를 `/root/colab-boot/ops.env` 에 `export ` 접두어 **뗀** 형태로 배치(스크립트 머리말 rsync/sed 예시 그대로 — 값은 `~/.config/colab-platform/prod.env` 의 `AWS_ACCESS*`·`AWS_SECRET*` 키 이름만 참조).
- **기대치 = 14/15**(⑮ ✗ 가 정답) — `MAIN_SHA` 의 `ancestor=bypass` 때문이다. 15/15 를 목표로 재시도하지 않는다(`DL-2` 판정과 동일 근거).
- 끝나면 **`/root/colab-boot/ops.env` 를 반드시 삭제**한다(§5 의 「깨뜨리면 안 되는 것 2」).

### ⓖ 검증(업로드 화면) — 누가: 사용자(브라우저)

- CloudFront 주소로 로그인 → 업로드 모달 → 이번 계약 변경(`RenderTarget.fileNames`) 이 걸리는 화면 = 데이터셋 상세의 미리보기 변수 고르개(`.npy` 등 파일 안에 변수 이름이 없는 포맷에서 원래 파일 이름이 뜨는지). 표시가 ULID 26자가 아니라 업로드한 파일 이름으로 나오면 통과.

### ⓗ 되돌림 — 누가: 사용자(EC2 SSH) · 대상 = `docs/DEPLOY.md` 원장에 적힌 직전 정식 태그

- `/opt/colab-v2/set-image-tag.sh <직전 정식 태그>`(ⓒ 가 함께 실어 둔 스크립트) 또는 `prod.env` 의 `COLAB_IMAGE_TAG` 를 직전 값으로 직접 되돌린다. 「지금 무엇이 도는가 / 직전 정식이 무엇인가」는 이 문서가 값으로 못박지 않는다 — **원장 `docs/DEPLOY.md §4-0b`(prod 배포 원장 표)의 최신 행을 실행 직전에 다시 읽어 확정한다**(오케스트레이터가 준 값은 `[미확인]` — 이 조사 세션이 직접 SSH 로 재본 것이 아니다).
- `up.sh` 재적용 → 웹 재배포(ⓔ 와 같은 실행기, 되돌린 버전으로) → `deploy_doctor` **15/15 를 한 번의 실행으로**(⑮ 가 ✓ 로 돌아오는 것이 되돌림의 판정 — `ancestor` 가 이전 정식 반입의 `yes` 값으로 남아 있어야 한다).
- 로컬 임시 태그(ⓑ) 삭제 — `git tag -d prod-<YYYYMMDD>-<label>`(원격에는 애초에 없다).

---

## 3. SSH 접속 정보의 자리

- 변수 이름 = `COLAB_PROD_SSH`(`ec2-user@<탄력적 IP>` 형태) · `COLAB_PROD_KEY_FILE`(개인키 경로, 0600).
  선언 위치는 `infra/prod/ship.sh` 머리말 주석 · 값 자체는 레포에 없고 로컬 `~/.config/colab-platform/prod-ssh.env` 자리를 문서(`docs/DEPLOY.md` 4-0b 표)가 가리킨다.
- 운영자 AWS 키(§2-ⓕ) 는 `~/.config/colab-platform/prod.env` 의 `AWS_ACCESS*`·`AWS_SECRET*` 키.
- 접속 가능 확인(비밀 미출력) —

```
set -a; . ~/.config/colab-platform/prod-ssh.env; set +a
ssh -o BatchMode=yes -o ConnectTimeout=8 -i "$COLAB_PROD_KEY_FILE" -o IdentitiesOnly=yes "$COLAB_PROD_SSH" 'echo ok'
```

---

## 4. 이 회차 특이점 — 계약 변경과 재빌드 범위

`contracts/seams/core-viz.yaml` 에 `RenderTarget.fileNames`(선택 필드) 신설 ＋ 기존 파일 이름
필드 설명 갱신(`git diff origin/main feature/rtf400_upload_form -- contracts/seams/core-viz.yaml` 실측).
소비하는 서비스 —

- **core-api** — 요청에 `fileNames` 를 실어 보낸다(`services/core-api/src/colab_core` 쪽 변경, diff stat 확인).
- **viz-render** — `readers.py`·`jobs.py`·`routes/renders.py`·`routes/describe.py` 가 그 값을 읽어 표시 이름을 정한다(diff stat 확인).
- **frontend** — 업로드·미리보기 컴포넌트 다수 변경(`RegisterArea.tsx`·`PreviewPanel.tsx` 등).
- **pipeline-worker** — 이 계약·diff 어디에도 걸리지 않는다(`git diff … --stat -- services/pipeline-worker` 결과 없음).

**재빌드 범위** = 계약이 바뀌었으므로 **core-api·viz-render·frontend 세 이미지 재빌드**. 다만
`infra/prod/build.sh` 는 **선택 빌드 옵션이 없어 5 유닛(위 셋 ＋ pipeline-worker·ai-service·migrator)
을 항상 전부 굽는다** — pipeline-worker 는 기능적으로 무변경이지만 빌드 스크립트 구조상 같이
구워진다. 이것이 결함은 아니다(§2-ⓐ).

---

## 5. 「깨뜨리면 안 되는 것 11」(`.claude/rules/deploy.md`) 중 이 회차에 걸리는 항목

| # | 항목 | 이 회차 적용 |
|---|---|---|
| 2 | EC2 env 에 AWS 액세스 키를 넣지 않는다 | §2-ⓕ 의 `/root/colab-boot/ops.env` 는 **판정 직전에만** 만들고 **판정 직후 삭제**한다. 상시로 두지 않는다 |
| 6 | 관대한 기본값 도입 금지 | `COLAB_SHIP_ALLOW_NONMAIN` 기본값은 0(거절)이고 이번 우회는 `=1` **명시 선언**으로만 성립한다 — 자동으로 열리는 값이 아니다 |
| 7 | 배포 환경의 저장 모드를 로컬 파일로 바꾸지 않는다 | `up.sh` ④ 「헬스 본문」 단계가 모드 `s3` 인지를 확인한다 — 이 단계를 건너뛰지 않는다 |

11번(데이터셋 행 삭제 전용 도구)·10번(백업 롤)은 이 회차가 삭제·백업을 수행하지 않으므로 해당 없음.

---

## 6. 이 조사에서 [미확인]으로 남긴 것

- prod 에 **현재 실행 중인 이미지 태그**와 **직전 정식 태그** — 오케스트레이터 지시문이 값을 줬으나
  이 세션이 SSH 로 직접 재지 않았다. §2-ⓗ 실행 직전에 `docs/DEPLOY.md §4-0b` 원장 최신 행으로
  재확인한다.
- `infra/notifications/{install-runtime-cron,run-runtime-job}.sh` 갱신 필요 여부 — 이번 임시
  검증은 크론을 설치하지 않으므로 실측하지 않았다.
