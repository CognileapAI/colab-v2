# WU-D4 판정 보조 사실 — 5건 실측 (2026-09-08)

- 배경 = `dev-package/sessions/WU-D4-branches-20260908.md` §1·§4·§5·§8·§9 가 레인이 측정하지 못했다고 적은 값 셋(dev EC2 인스턴스 유형 · dev 호스트 compose 배선 · `gh-pages` 상태)과, 그 문서 밖에서 병행 확인이 필요한 둘(PR #4·#5·#6 · U-2 정정의 `main` 부재)을 대조한다.
- 범위 = 읽기 전용. `git` 쓰기·브랜치/태그 변경·`docker` 상태 변경·`ssh` 원격 상태 변경 없음. 원격은 IMDSv2 토큰 조회 1회 · `grep -c` 1회 · `md5sum` 1회만 실행.

## 1. dev EC2 인스턴스 유형

- 값 = **`t4g.medium`** (실물 조회).
- 명령 = `ssh -i ~/.config/colab-platform/dev-key.pem $COLAB_DEV_SSH 'TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"); curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-type'` (호스트 = `~/.config/colab-platform/dev-operator.env` 의 `COLAB_DEV_SSH`, 키 = 같은 디렉터리 `dev-key.pem`).
- 대조 = `main:docs/DEPLOY.md:160` — `colab-platform-app-dev` · `i-0bf4fad1ead85071d` (`t4g.small`, arm64). `feature/rtf400_dev_scale_up` 문면(`t4g.medium`)이 실물과 일치하고, `main` 문서가 낡았다.
- `aws ec2 describe-instances` 는 미실행 — `aws sts get-caller-identity` 가 `NoCredentials`(자격 증명 미설정, `aws configure list` 전항목 `<not set>`). ssh 경로로 대체 측정.
- 부수 확인 = `main:docs/DEPLOY.md:406` 「인스턴스를 크게 잡는 게 낫지 않나 | `t4g.medium` | Free Plan 이 막았다」 — `main` 문서 자체가 `t4g.medium` 검토 사실은 이미 담고 있고, **실제 변경만 미반영**.

## 2. dev compose 트리거 스풀 배선

- 값 = 호스트가 실행 중인 `/opt/colab-v2/compose.yml` 은 **`main` 과 바이트 동일**(`w9-rebase` 아님). `spool`/`viz-events` 문자열 0건.
- 명령·결과 —
  - `ssh … 'grep -c -i "spool\|viz-events" /opt/colab-v2/compose.yml'` → `0`
  - `ssh … 'md5sum /opt/colab-v2/compose.yml'` → `171a957eb355a177b4aa241ddda35d84`
  - `git show main:infra/dev/compose.yml | md5sum` → `171a957eb355a177b4aa241ddda35d84` (일치)
  - `git show w9-rebase:infra/dev/compose.yml | md5sum` → `671287020efca32a4fbfe219de4abd41` (불일치)
- 결론 = 호스트는 `main` 의 compose 를 그대로 돌리고 있고, `w9-rebase` 전용 스풀/`viz-events` 배선은 **실물에 적용돼 있지 않다**. `WU-D4-branches-20260908.md §8-4` 의 「compose 스풀 배선이 실물에 살아 있는가 = `[미상]`」을 **미적용**으로 닫는다.

## 3. `gh-pages`

- `curl -sI https://cognileapai.github.io/colab-v2/` → `HTTP/2 200` · `last-modified: Thu, 03 Sep 2026 07:37:40 GMT`.
- `curl -s … | head -c 600` → `<title>Co-Lab v2 — 기획 전달본</title>`, `<meta name="robots" content="noindex">`.
- `gh api repos/CognileapAI/colab-v2/pages` → `status: built` · `source: {branch: gh-pages, path: /}` · `html_url: https://cognileapai.github.io/colab-v2/` · `cname: null`.
- 레포 내 연결 = `grep -rn 'github.io\|gh-pages' README.md docs .github` 결과 1건 — `docs/BRANCHING.md:61`(이 판정을 이미 기록한 참조 문장, WU-D4 레인 산출). README·`.github` 워크플로우에는 없음 — **자동 배포 파이프라인이 레포 안에 없고**, 페이지는 `gh-pages` 브랜치 자체의 정적 파일로만 서빙됨.
- `WU-D4-branches-20260908.md §7` 판정(가동 중 · 보류)과 일치. 추가 발견 없음.

## 4. PR #4 · #5 · #6

| PR | 제목 요지 | 작성자 | 생성 | 리뷰 상태 | mergeable | 파일수 |
|---|---|---|---|---|---|---|
| #4 | dev EC2 를 `t4g.medium` 으로 · 「인스턴스만 키우면 안 고쳐진다」 대장 기록 | `rtf400` | 2026-09-06T09:10:03Z | (없음) | `UNKNOWN` | 1 |
| #5 | `U-2` 근거 정정 — 업로드 만료 정리기 운영 호출 이력 없음 · prod 첫 고아 실측 〈368〉 | `rtf400` | 2026-09-06T09:45:04Z | (없음) | `UNKNOWN` | 3 |
| #6 | prod 개통 — AWS prod 한 벌 · `deploy_doctor` 14/14 · 시점 복구 실증(〈372〉) | `rtf400` | 2026-09-06T10:17:11Z | (없음) | `UNKNOWN` | 39 |
- 명령 = `gh pr view <n> --json title,author,createdAt,reviewDecision,mergeable,files --jq '{...}'`.
- `reviewDecision` 빈 문자열 = 승인·변경요청 리뷰 0건(3건 공통). `mergeable: UNKNOWN` = GitHub 이 아직 mergeability 를 계산하지 않은 상태(머지 시도 전 흔한 값, 충돌 여부 별도 확인 필요 — `[미확인]`).
- `gh pr view <n> --comments | tail -20` = 3건 전부 **댓글 0건** — 병합을 요청하는 리뷰 코멘트 없음.
- 파일수는 `WU-D4-branches-20260908.md` §4·§5·§2(prod 39파일)의 밖 파일 수와 일치(1·3·39).

## 5. U-2 정리기 근거 — `main` 부재 확인

- `git diff --stat main...origin/feature/rtf400_upload_reaper` → 3파일: `dev-package/PLAN-SoT.md`(+1) · `dev-package/WORK-UNITS.md`(±1) · `dev-package/work-items.yaml`(±4). `WU-D4-branches-20260908.md §5` 수치와 일치.
- `git grep -n 'reap_expired' main -- dev-package` → 7건, 전부 **기존 조사 문서**(`arch-facts.md`·`P2-api-report.md`·`PV-WIRING-SCOPE.md`·`S1-upload-path-audit.md`·`WU-V2-INPUTS.md`)이며 「core-api 에 생산 호출자 0건」이라는 **관찰**은 이미 `main` 에 있음(`WU-V2-INPUTS.md:78,301`).
- `git grep -n '고아 8건'` · `〈368〉` 을 `main` 에서 검색 → 「고아 8건」 0건. 〈368〉 은 `main` 에 **다른 결정**(하네스 재설계 확정 판정)으로 이미 점유돼 있어, 이 브랜치의 〈368〉(prod 고아 실측)과 **번호가 충돌**한다 — 병합 시 재번호 필수(규칙 `.claude/rules/colab-rules.md §4-1`).
- 결론 = 「정리기가 운영에서 호출되지 않는다」는 관측 자체는 `main` 문서 여러 곳에 이미 있으나, **prod 고아 8건 3.00 MB 실측치와 그 결론(work-items.yaml 갱신)은 `main` 에 없다** — `WU-D4-branches-20260908.md §5` 판정(정정 미반영) 확인.

## 참조

- `dev-package/sessions/WU-D4-branches-20260908.md` §1·§2·§4·§5·§7·§8·§9
- `docs/DEPLOY.md:160,236,240,392,406`
- `docs/BRANCHING.md:61`
- `infra/dev/README.md`
