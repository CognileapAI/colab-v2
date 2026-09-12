# R-BUGFIX-260912 — dev 배포 체크리스트 (DRAFT · 미승인)

- 성격 = 조사 산출 1건. 추적 파일 편집 0 · 커밋 0 · 원격 행위 0 · 원장 번호 발급 0.
- 근거 = `.claude/rules/deploy.md`(전문) · `docs/DEPLOY.md §1·§6-1·§6-2·§9` · `docs/BRANCHING.md §1·§2·§5` · `infra/dev/README.md` · `infra/releases/README.md` · `infra/dev/tag-release.sh` · `infra/dev/up.sh:39`.
- 표기 = 「사람 실행」 = 자격증명·SSH·원격 비가역 행위가 걸려 에이전트가 대행하지 않는 단계.

---

## 0. 실측 전제 (이 회차 · 2026-09-12 측정)

| 값 | 실측 | 측정 명령 |
|---|---|---|
| 통합 브랜치 HEAD | `fa2f67a12aec` | `git rev-parse HEAD` |
| `origin/main` | `6fcc065f` | 지시문 기재 · 조상 확인 완료 |
| ff 가능 여부 | 가능 — `6fcc065f` 는 HEAD 조상 | `git merge-base --is-ancestor 6fcc065f HEAD` exit 0 |
| 직전 dev 태그 | `dev-20260912-1` → `fc45a9aa` (HEAD 조상) | `git tag -l 'dev-*' \| sort \| tail -3` |
| **다음 dev 태그** | **`dev-20260912-2`** (N = 같은 날 기존 태그 1건 ＋1) | `git tag -l 'dev-20260912-*' \| wc -l` |
| 다음 결정 번호 | `〈391〉` (현재 최대 390) | `bash dev-package/prd/tools/max-decision.sh` |

### 0-1. 배포 범위 — 프런트 전용 아님

`dev-20260912-1..HEAD` 변경 실측(`git diff --name-only`, 최상위 2단 집계):
`services/core-api` 23 · `infra/notifications` 25 · `infra/ops` 5 · `infra/staging` 3 · `infra/dev` 1 · `frontend/src` 11 · `frontend/test` 7 · `db/platform` 5.

⟹ **전체 DV 배포**(이미지 5종 빌드 → 반입 → 기동 → 웹 번들)다. `infra/releases/README.md` 의 「프런트만 바꾸면 이미지/DB 단계는 필요 없다」 예외에 해당하지 않는다.

### 0-2. 마이그레이션 — 신규 1건

- platform 체인 신규 리비전 = **`0027_operator_audit`** 1건. `git ls-tree --name-only dev-20260912-1 db/platform/versions/` 는 `0026_login_sessions` 까지이고, `0027` 은 `948cd2a5`(origin/main)에서 들어왔다.
- ai 체인 변경 0 — head `0007_merge_topic_vocab_and_rc7_category` 유지.
- ⚠ **지시문의 「0027–0030」 은 실물과 다르다** — 레포 `db/platform/versions/` 에 `0028` 이상은 없다. 대조 대상은 `0027` 하나다.
- 이 통합 브랜치 자체의 db 변경은 0(`git diff --name-only 6fcc065f..HEAD` 에 `db/` 0건) — 마이그레이션은 전부 `main` 에서 온 것이다.

---

## 1. `main` ff — 사람 실행 (Ted)

`docs/BRANCHING.md §2` 표 — `integration/r-N` 의 `main` 병합은 **Ted**, 브랜치 삭제는 오케스트레이터.

```bash
# 통합 워크트리에서
git fetch origin
git merge-base --is-ancestor origin/main integration/r-bugfix-260912 && echo FF-OK
git push origin integration/r-bugfix-260912:main
```

- 사전 검사(2행)가 exit 0 이어야 push 한다. 「FF-OK」 가 안 찍히면 push 하지 않는다.
- **거절될 때** — `origin/main` 이 그 사이 앞섰다는 뜻이다. 처치 = ⑴ 통합 브랜치에서 `git merge origin/main` 1회(레인 규약 `.claude/rules/colab-rules.md §4-1` 과 같은 이유) ⑵ 결정 번호 `〈391〉` 을 `max-decision.sh` 재실측값으로 다시 채번 ⑶ 게이트 `work-item-consistency` 1회 green ⑷ 다시 ①. ⛔ `--force`·`-f` 를 쓰지 않는다.
- `main` 직접 push 금지 규약(`docs/BRANCHING.md §2` 비고)의 예외는 이 ff 한 줄뿐이다.

---

## 2. dev 배포 — 사람 실행

### 2-1. 실행 자리

- **로컬 WSL(개발 기계)에서 실행한다.** GitHub Actions 워크플로 디스패치 경로는 없다 — `docs/DEPLOY.md §10` 이 CI 자동 배포를 「아직 안 한 것」으로 두고 현행 반입은 `scp` 다(`.claude/rules/deploy.md` 「확장하려면」).
- 진입점 = `python3 scripts/deploy_release.py run --plan <계획> [--check]` (`infra/releases/README.md`). `build.sh`·`ship.sh`·`up.sh`·`deploy_web.py` 단독 실행을 배포 완료로 세지 않는다.
- ⚠ 전수 게이트와 동시 실행 금지(`.claude/rules/colab-rules.md §9` — 12GB 호스트 OOM 선례).

### 2-2. 환경값·자격 (사람 실행)

```bash
export COLAB_DEV_SSH=ec2-user@<EIP>          # 정본 = EC2 요약의 「탄력적 IP 주소」 칸
export COLAB_DEV_KEY_FILE=~/.config/colab-platform/dev-key.pem
```

- EC2 `dev.env`(`/opt/colab-v2/dev.env`, 0600)는 **EC2 위에서만** 편집한다(로컬 작성 시 CRLF · `docs/DEPLOY.md §9`).
- 운영자 키는 `deploy_doctor` 의 `--env-file /tmp/op.env` 로 잠깐 넘기고 **실행 직후 지운다**.
- 계획 JSON 에 비밀번호·접속 문자열·토큰을 넣지 않는다(`infra/releases/README.md`).

### 2-3. 계획 JSON — DV 전체 배포

자리 = `~/colab-deploy/r-bugfix-260912/release.json`(레포 밖 · 검토 뒤 고정). `targets` 는 `dv` 하나. `deploy` 배열 순서:

1. `["bash","infra/dev/build.sh"]` — 5 이미지 `buildx linux/arm64` → 아키텍처 실측 → `dist/colab-v2-dev-<sha>.tar`
2. `["bash","infra/dev/ship.sh"]` — 반입. **여기에 `main` 조상 게이트가 있다**(비조상 exit 65 · `origin` 조회 실패 exit 78). `/opt/colab-v2/MAIN_SHA` 에 `main=… candidate=… ancestor=yes` 한 줄을 적는다.
3. 원격 `/opt/colab-v2/up.sh` — `migrate-platform`(→ `0027_operator_audit`) → `migrate-ai`(변경 0) → `up -d` → 4 단위 healthy 대기(fail-closed) → 헬스 본문
4. `["python3","services/core-api/ops/deploy_web.py", …]` — 프런트 정적 번들 → `colab-platform-web-dev`

⛔ `COLAB_SHIP_ALLOW_NONMAIN=1` 을 쓰지 않는다. 이 회차는 ①에서 `main` ff 를 먼저 끝내므로 우회 사유가 없고, 우회하면 `deploy_doctor` ⑮ 가 `ancestor=bypass` 로 ✗ 를 낸다.

빌드 사전 조건(WSL) — `docker buildx` 에 `linux/arm64` 가 없으면 `build.sh` 가 `no match for platform in manifest` 로 죽는다. 선행 1회:

```bash
docker run --privileged --rm tonistiigi/binfmt --install arm64
```

### 2-4. `deploy_doctor` 전 EC2 레포 동기화 (사람 실행 · 선행 필수)

`deploy_doctor` 는 `--repo` 트리의 `db/<체인>/versions` 와 `gates/tools` 를 읽는다. 레포가 낡으면 ⑥⑦ 이 **옛 head 를 정답으로 삼아 조용히 틀린다**(`infra/dev/README.md` · 실측 `〈361〉`-㉯).

```bash
tar czf /tmp/repo.tgz --exclude=__pycache__ --exclude=.venv db gates services/core-api/ops infra
scp -i "$COLAB_DEV_KEY_FILE" /tmp/repo.tgz "$COLAB_DEV_SSH":/tmp/
ssh -i "$COLAB_DEV_KEY_FILE" "$COLAB_DEV_SSH" 'sudo tar xzf /tmp/repo.tgz -C /opt/colab-repo --overwrite'
```

판정 = 개발 기계와 EC2 의 `services/core-api/ops/deploy_doctor.py` **md5 동일**.

### 2-5. `deploy_doctor` 15/15 — 한 번의 실행

`verify` 배열에 넣는다(EC2 위 · `docs/DEPLOY.md §6-1` 축자 명령):

```bash
docker run --rm --network host --env-file /tmp/op.env \
  -v /opt/colab-repo:/repo:ro \
  -v /opt/colab-v2:/state:ro \
  -v /etc/colab/core-database.url:/s/core.url:ro \
  -v /etc/colab/ai-db.url:/s/ai.url:ro \
  colab-v2/core-api:dev python /repo/services/core-api/ops/deploy_doctor.py --env dev \
    --endpoint https://d31zgpff2091oh.cloudfront.net \
    --app-base http://127.0.0.1:8000 --worker-base http://127.0.0.1:8001 \
    --viz-base http://127.0.0.1:8100 --ai-base http://127.0.0.1:8200 \
    --db-url-file /s/core.url --ai-db-url-file /s/ai.url \
    --bucket colab-platform-data-dev --web-bucket colab-platform-web-dev
```

- **`-v /opt/colab-v2:/state:ro` 를 빼면 ⑮ 가 항상 ✗ 다.** 위 명령 그대로 쓴다.
- 합격 = **✓ 15 · ✗ 0 · ─ 0 이 한 번의 실행에서**. `--allow-skip` 을 쓰지 않는다. 부분 실행 둘을 합쳐 green 이라 하지 않는다(`CLAUDE.md §0` 완료 조건 · `.claude/rules/deploy.md` 「고치기 전에 돌릴 것」).
- ⑮ = `/state/CURRENT_SHA` 와 `/state/MAIN_SHA` 문자열 대조. 기대 = `ancestor=yes` · `candidate` 가 이번 반입 sha.
- ⚠ 맥 SSH 터널로 돌리면 ⑫ 가 red 다 — 위 EC2 내부 방식으로 돌린다.

### 2-6. dev 배포 자체의 「green」

| 대상 | 확인 | 기대 |
|---|---|---|
| 4 단위 헬스(EC2 내부) | `up.sh:39` — `curl -fsS http://127.0.0.1:{8000,8001,8100,8200}/healthz` | 4건 전부 200 · `up.sh` 가 fail-closed 로 대기 |
| 공개 진입 | `curl -sI https://d31zgpff2091oh.cloudfront.net/` | 200 · `index.html` 은 긴 캐시 아님 |
| API 라우팅 | `curl -s -o /dev/null -w '%{http_code}' https://d31zgpff2091oh.cloudfront.net/api/v1/me` | **401 JSON**(doctor ⑭ 의 판정 대상과 같은 자리) |
| 저장 모드 | doctor ⑬ | `storageMode`/`sourceMode` = `s3` |
| 번들 hash | 검증 패킷의 공개 `index`/`assets` hash 대조 | 계획 manifest 와 일치 |
| 최종 | `deploy_doctor` | ✓ 15 · ✗ 0 · ─ 0 (한 번) |

### 2-7. 로그가 남는 자리

- 실행기 기록 = Git **common directory** 의 `deploy-releases/<id>/`(`plan.json` 포함 · 워크트리 공유 잠금 · `infra/releases/README.md`). 레포 추적 대상이 아니다.
- 회차 로그 사본 = `dev-package/reports/bugfix-260912/deploy/`(선례 `dev-package/reports/R-C/deploy/`). `deploy_doctor` 출력 전문과 `MAIN_SHA` 한 줄을 여기에 둔다.
- 종료코드 판독 — 0 성공 / 1 배포·검증 실패(알림 없음) / **20 배포·검증 성공 · 알림만 실패** / 75 다른 배포 실행 중 / 78 계획·입력 확인 불가. **exit 20 에서 배포를 다시 실행하지 않는다** — `--retry-notification` 만.

---

## 3. 태그 `dev-20260912-2` — 사람 실행

부르는 때 = **`deploy_doctor` 전건 통과 뒤**(`infra/dev/README.md` 「태그」).

```bash
bash infra/dev/tag-release.sh dev          # 로컬 태그만 생성 · push 없음 · 대상 sha = dist/colab-v2-dev.sha
git push origin dev-20260912-2             # 원격 반영은 사람이 한 줄로 (비가역)
```

- 스크립트가 `git merge-base --is-ancestor <sha> origin/main` 을 다시 검사한다(비조상 exit 65 · `origin` 조회 실패 exit 78 · 태그 중복 exit 65).
- ⛔ `git push origin --tags` 금지(`docs/BRANCHING.md §3` ⑸ — `archive/*` 잡태그가 함께 나간다). 개별 push 만.
- 출력된 태그명이 `dev-20260912-2` 가 아니면(같은 날 다른 태그가 생겼다는 뜻) **출력값을 그대로 쓴다**.

### 3-1. `PLAN-SoT §9 〈391〉` 초안 (번호는 병합 직전 재실측)

```
- **⭑ ⟨신설 2026-09-12 · 배포 창 집행⟩ 〈391〉 R-BUGFIX-260912 dev 배포** — `main` ff = `integration/r-bugfix-260912` `fa2f67a12aec` 한 줄(`origin/main` `6fcc065f` 조상 확인). dev 실적용 sha `<반입 12자리>` · 태그 `dev-20260912-2` · EC2 `<인스턴스 id>`. `deploy_doctor` **✓ 15 · ✗ 0 · ─ 0(한 번의 실행)** · ⑮ `ancestor=yes`. 마이그레이션 platform 신규 1건 `0027_operator_audit` 적용(head `0027`) · ai 변경 0(head `0007_merge_topic_vocab_and_rc7_category`). 내용물 = 프런트 버그개선 12건(`BF-14`~`BF-17`) ＋ `main` 반입분(운영 알림 · 로그인 강화). 로그 `dev-package/reports/bugfix-260912/deploy/`.
```

- `<반입 12자리>` 는 `dist/colab-v2-dev.sha` 앞 12자리로 채운다. `<인스턴스 id>` 는 배포 시점 콘솔 실물로 채운다(`03-HANDOFF.md:83` 의 2026-09-08 선례 값은 이 회차 근거가 아니다 · `[미확인]`).
- ⚠ 번호 `391` 은 **임시**다. 병합 직전 `bash dev-package/prd/tools/max-decision.sh` 재실측 +1(`.claude/rules/colab-rules.md §4-1`).

### 3-2. `03-HANDOFF.md` 「배포 창」 한 줄 초안

```
⭑ **⟨증보 2026-09-12 · 배포 창 집행⟩ dev `<반입 12자리>` · 태그 `dev-20260912-2` · `deploy_doctor` 항목 15 — ✓ 15 · ✗ 0 · ─ 0 · 등재 `PLAN-SoT §9 〈391〉` · 마이그레이션 platform `0027_operator_audit` 1건 적용(head `0027`) · ai 변경 0 · 로그 `dev-package/reports/bugfix-260912/deploy/`.**
```

- 자리 = `03-HANDOFF.md` 상단 「최종 갱신 · 현재 단계 · 다음 WU」 갱신과 같은 회차(`CLAUDE.md §6` ①②③).

---

## 4. 병합 뒤 정리 — 오케스트레이터

`.claude/rules/colab-rules.md §2-1` 3종 ＋ `docs/BRANCHING.md §2`.

```bash
git worktree remove ".claude/worktrees/bugfix-survey-260912"
git worktree prune
git branch -d integration/r-bugfix-260912
git push origin --delete integration/r-bugfix-260912
git worktree list
git branch -a
```

- `-d`(소문자)를 먼저 쓴다 — 병합 확인을 겸한다. `-D` 선사용 배제.
- 미커밋 변경이 남아 있으면 삭제를 보류한다. 이 조사 산출물(`dev-package/reports/bugfix-260912/**`)이 미추적이면 **먼저 승인된 경로로 회수**한 뒤 워크트리를 제거한다.
- `lane/*` 브랜치가 남아 있으면 함께 삭제(통합에 얹힌 즉시 삭제 규약).
- 원격 브랜치 삭제는 **비가역**이다 — 게이트 ③ 뒤 오케스트레이터가 집행한다.

### 4-1. `planning-applied --sync` — **아니요**

- 실행하지 않는다. 근거 = 이 회차의 입력은 GitHub 이슈 · Ted 판정 · intent · spec 이고 `40 COLAB-기획/10_적용전/` 기획 문서를 **소비한 라운드가 아니다**. 소비 문서 0건이라 게이트 `planning-freshness` 의 대조 대상(㈎ `30_적용완료/<라운드>/` 사본 ㈏ 매니페스트 등재)이 생기지 않는다.
- 출처 = `dev-package/reports/bugfix-260912/closing-draft.md §7`.
- 병합 뒤 게이트 = `bash gates/run.sh work-item-consistency` 1회 green(대장 ＋ `CLAUDE.md §0` 괄호 대조).

---

## 5. 「깨뜨리면 안 되는 것 11」 — 이 회차가 닿는 항목

`.claude/rules/deploy.md` 의 11 중, `dev-20260912-1..HEAD` 변경 실측으로 접촉면이 있는 것만.

| # | 항목 | 이 회차의 접촉 | 확인 |
|---|---|---|---|
| 3 | CloudFront 를 걷어내지 않는다 | 프런트 번들 재배포(`deploy_web.py`) — 배포 대상은 S3 웹 버킷이고 배포판 자체는 무변 | 배포 뒤 `https://d31zgpff2091oh.cloudfront.net/` 200 · 폴더 드롭이 보안 컨텍스트 안(HTTPS) |
| 4 | `/api/*` 원본 요청 정책 `AllViewer` 유지 · 캐시 미사용 | 백엔드 23파일 변경(로그인·운영 알림) · `infra/dev` 1파일 변경 — 정책 파일 포함 여부를 먼저 확인한다 | `curl … /api/v1/me` = **401 JSON**(200·403 이면 `Authorization` 절단) · doctor ⑭ |
| 5 | `index.html` 에 긴 캐시 금지 | 프런트 번들 교체 — 옛 화면 잔존 위험이 있는 자리 | 배포 뒤 공개 `index` hash 가 계획 manifest 와 일치 · `assets/*` 만 `immutable` |
| 6 | 관대한 기본값 도입 금지 | 운영 알림 설정값 신설(`infra/notifications` 25파일) — 필수값 누락 시 **기동 실패가 의도된 동작** | `up.sh` 의 4 단위 healthy 대기(fail-closed) green · 기동 실패를 기본값으로 무마하지 않는다 |
| 7 | 배포 환경 저장 모드는 `s3` | 업로드 경로 프런트 변경(이어서 하기·버리기) | doctor ⑬ `storageMode`/`sourceMode` = `s3` |
| 8 | DB 와 저장 백엔드를 따로 바꾸지 않는다 | `dev.env` 를 손대는 단계가 이 회차에 없다 | env 파일 부분 수정 0 — 필요하면 통째로 교체 |
| 9 | 정리 잡·백업은 cron | `infra/ops` 5파일 변경 — 앱 내부 백그라운드 태스크로 옮기지 않았는지 확인 | doctor ⑭ 「백업 24h」 ✓ · `/var/log/colab-backup.log` |
| — | 마이그레이션(규칙 5 계열) | platform `0027_operator_audit` 1건 신규 적용 | `up.sh` 의 `migrate-platform` 성공 · doctor ⑥⑦ head 대조 = `0027` / `0007_merge_topic_vocab_and_rc7_category` · **되돌리지 않는다** |

닿지 않는 것 — ①(NAT 생성 0) ②(EC2 env 에 액세스 키 추가 0) ⑩(백업 롤 변경 0) ⑪(`purge_datasets.py` 실행 0 · 이 회차에 데이터셋 행 삭제 없음).

---

## 6. 「사람 실행」 목록

| 순서 | 단계 | 사유 |
|---|---|---|
| 1 | `integration/r-bugfix-260912` → `main` ff push | `main` ff 는 Ted(`docs/BRANCHING.md §2`) · 원격 비가역 |
| 2 | `COLAB_DEV_SSH`·`COLAB_DEV_KEY_FILE` 설정 · EC2 `dev.env` 확인 | SSH 개인키·EC2 접속 자격 |
| 3 | `/tmp/op.env` 운영자 키 준비·실행 직후 삭제 | AWS 운영자 자격증명 |
| 4 | `deploy_release.py run --plan …`(build·ship·up·web) | AWS 자원 변경 · 비가역 |
| 5 | EC2 `/opt/colab-repo` tar 동기화(`ssh`·`scp`·`sudo`) | 원격 쓰기 |
| 6 | `deploy_doctor` 실행 | EC2 위 · 운영자 자격 |
| 7 | `git push origin dev-20260912-2` | 태그 원격 push(비가역 · `--tags` 금지) |
| 8 | `git push origin --delete integration/r-bugfix-260912` | 원격 브랜치 삭제(비가역 · 게이트 ③ 뒤) |
| 9 | `gh issue comment` 12건 게시 | 외부 공개 · Ted 결정 |

---

## 7. 미확인

| 항목 | 상태 | 해소 |
|---|---|---|
| EC2 인스턴스 id·EIP | `[미확인]` — 이 세션은 EC2 를 접촉하지 않았다 | 배포 시점 콘솔 「탄력적 IP 주소」 칸 실물 |
| dev 현재 alembic 스탬프 | `[미확인]` — EC2 미접촉 | 배포 전 실측 1건(`0026_login_sessions` 기대) |
| `infra/dev/` 변경 1파일의 정체 | `[미확인]` — 상위 2단 집계만 수행 | `git diff --name-only dev-20260912-1..HEAD -- infra/dev/` |
| 배포 계획 JSON 실물 | 미작성 | 사람이 검토 뒤 레포 밖에 고정 · `--check` 선행 |
| 통합 트리 전수 게이트 결과 | `[미확인]` | `closing-draft.md §9` 와 같은 미결 |
