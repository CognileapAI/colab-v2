# I3·I4 실제 실행 승인 패킷

작성 기준: 구현·origin/main·dev `30f5adf6774771c9ca34e2c3a0b92a0648b9cc76`, CI `34577478051` success. dev ship/up과 운영자 진단15/0/0 완료. **아래 I4 자동 probe는 별도 권한 문제로13/2/0이며 실행 준비 완료가 아니다.** SHA가 바뀌면 승인 대상을 다시 봉인한다.

## 현재 읽기 전용 실측

- staging: `09e2b9b2db1a`, 컨테이너 8개, `https://www.colab-hydro.com/healthz` 200.
- 현재 서빙이자 다음 배포의 직전 green rollback 대상: `09e2b9b2db1a`, 이미지 6/6 존재.
- 그보다 한 단계 오래된 보존 fallback: `a8541b7c3c33`, 이미지 6/6 존재. release ledger에도 `a8541b7c3c33` 다음 `09e2b9b2db1a` 순서로 기록되어 있다.
- staging env: `~/.colab-v2-staging.env` 0600.
- 사용자 crontab: SHA-256 `d554b72cb92947d038b9495577fe5fcdfe0adbf90026f2b724cdb9f7da25dbd4`, 비공백 36줄, backup 표식 2개, deploy 표식 0개.
- staging 상태: 실패 표식 없음, LAST-SUCCESS 존재, 마지막 green `09e2b9b2db1a`.
- 자동 배포 전용 `/home/ttlhi10/colab-v2-staging-deploy`, branch `staging/auto-deploy`를 준비했다. 시작 HEAD는 final main의 직접 부모 `e90e5c2553a7795176cfcc218d8957b74da5869e`, clean. 최소 cron PATH 도구15종과 원격 fetch 확인. 근거 `reports/stage12-i3-readiness-final/readiness.md`.
- dev I4: `/opt/colab-ops/versions/30f5adf67747`와 dispatcher 설치 완료. `/etc/cron.d/colab-ops` 미설치. 기존 `/etc/cron.d/colab-dev` SHA-256은 `ffb1cb3252e62c339a90dda3761f1d913dcb402a80b717fa7cf85be2bece64a6`.

## I3 — 실제 5분 cron RED → 같은 SHA GREEN

### 승인 대상

1. 이미 준비된 전용 clean worktree `/home/ttlhi10/colab-v2-staging-deploy`의 HEAD `e90e5c2553a7795176cfcc218d8957b74da5869e`와 원격 `30f5adf6774771c9ca34e2c3a0b92a0648b9cc76`를 재확인한다.
2. 전용 worktree 안에 빈 `TEST-I3-DIRTY-RED` 파일 하나를 둔다. 이 파일은 red 뒤 정확히 한 번 제거한다.
3. 그 worktree의 `infra/staging/pipeline/install-schedule.sh install`로 5분 deploy 블록을 설치한다.
4. 최종 후보의 main push는 이 승인과 독립해 먼저 끝낼 수 있다. 전용 worktree는 최종 main의 부모 SHA에서 시작하므로, 원격 main이 이미 최종 후보여도 첫 cron은 `LOCAL != REMOTE`와 dirty 1건을 만나 fast-forward 전에 exit 65, `DEPLOY-FAILED.txt`를 만든다. 빌드·DB·서비스에는 닿지 않는 실질 dirty-tree 안전장치 RED다.
5. `TEST-I3-DIRTY-RED` 하나만 제거하고 다음 5분 cron을 기다린다. 같은 REMOTE SHA를 fast-forward하고 전체 배포를 수행해야 한다.

### RED 판정

- RED 직전에 `git fetch origin main` 뒤 `origin/main` 전체 SHA를 별도 증거 파일에 기록하고 봉인한다. dirty-tree 분기는 REMOTE SHA를 로그에 출력하지 않으므로 pipeline 로그만으로 같은 SHA를 주장하지 않는다.
- pipeline 로그에 `워킹트리 변경 1건`·exit 65가 같은 회차로 남는다. RED 증거 봉인부터 GREEN 종료까지 main 변경을 동결하고, GREEN 뒤 실제 서빙 SHA를 위 fetch SHA와 대조한다.
- `DEPLOY-FAILED.txt`가 생기고 LAST-SUCCESS는 바뀌지 않는다.
- public health는 전/후 200, 서빙 이미지 ID·DB migration head·릴리스 원장은 red 회차 전후 불변이어야 한다.
- 일반 게이트, health, deploy doctor를 끄거나 입력을 바꾸는 실패 주입은 사용하지 않는다.

### 같은 SHA GREEN 판정

- 다음 실제 cron 회차가 red 때의 REMOTE와 정확히 같은 SHA를 배포한다.
- pipeline 자체 판정은 backup 두 체인 green, migration single head, `verify-deploy.sh`와 `verify-chains.sh` green이다. pipeline이 전체 gate나 `deploy_doctor`를 자동 실행한다고 세지 않는다.
- staging 배포 판정은 실제 `infra/staging/verify/verify-deploy.sh`와 `infra/staging/verify/verify-chains.sh`의 성공 종료·원문 및 앱/DB 8 컨테이너 healthy·노출 위반 0을 대조한다. `deploy_doctor`는 dev/prod 전용이므로 staging에서 실행하거나 dev로 위장하지 않는다. doctor 15/15는 아래 I4 dev 검증에만 적용한다.
- 코드 전체 검증은 최종 SHA의 `stage12-final-gates/after/gate-summary.json`을 별도 증거로 연결한다. 실행 SHA·필수 게이트·실제 입력·계수와 명시 면제를 확인하고, 이를 staging 런타임 검증으로 바꾸지 않는다. 같은 코드의 전체 검사를 이유 없이 반복하지 않는다. 해당 보고서가 아직 없거나 final SHA와 다르면 이 코드 검증 조건은 미충족이다.
- public health는 RED 전후와 GREEN 뒤 200이어야 한다.
- `DEPLOY-FAILED.txt` 제거, LAST-SUCCESS·release ledger·실제 서빙 tag가 같은 SHA다.
- 설치 후 crontab은 기존 36줄과 backup 표식 2개를 보존하고 deploy 표식 2개(시작/끝), 실행 줄 1개만 추가한다. 설치 전 snapshot 경로와 hash를 기록한다.

### I3 중단·복구

- 첫 RED가 fast-forward 전이 아니거나 서비스/DB에 닿으면 marker를 제거하지 않고 중단한다.
- GREEN 배포가 red면 자동 rollback하지 않는다. 실패 표식과 로그를 보존하고 기존 `rollback.sh`로 배포 직전 서빙 green `09e2b9b2db1a`를 첫 복구 대상으로 제시한다. `a8541b7c3c33`는 한 단계 오래된 보존 fallback이며 직전 서빙으로 오인하지 않는다.
- crontab 오염 시 install 전 snapshot을 `crontab <snapshot>`으로 복원하고 hash·backup 표식 2개를 재확인한다.

## I4 — dev ops source·probe·외부 수신

### 현재 후보 bundle

- source SHA `30f5adf6774771c9ca34e2c3a0b92a0648b9cc76`
- archive SHA-256 `ce56cbd88b9b0d1275ef9975758f6a983757d2cb3c09fb93c39834ebd6b48fe4`
- manifest SHA-256 `1333f19aa3da961aafacd8e55e69fb6ec40607637534600d6ddab934e6cdd7c9`
- manifest 파일 136개.
- 실제 main 조상 검사와 manifest 전건 검사 통과 후 dev에 설치했다.

### 설치 전 runtime readiness

- 로컬 반입 호스트: `git`, `tar`, `gzip`, `sha256sum`, `ssh`, `scp`, Docker build 도구가 실제 PATH에서 실행 가능하고 SSH key가 0600인지 확인한다.
- dev EC2: cron의 고정 PATH(`/usr/local/bin:/usr/bin:/bin`)에서 `bash`, `python3`, `docker`, `flock`, `sha256sum`, `stat`, `readlink`, `find`, `mktemp`를 root가 실행할 수 있는지 확인한다.
- `/etc/colab/platform-owner-db.url`, `/etc/colab/ai-owner-db.url`은 존재·root 읽기 가능 여부와 mode만 확인하고 내용을 출력하지 않는다. 현재 SHA core 이미지, AWS instance credential/region, dev data/web bucket read 권한을 read-only probe로 확인한다.
- webhook 파일은 I4 외부 알림 승인 전에는 만들거나 읽지 않는다. cron 설치 단계에서는 root:0600, HTTPS 한 줄, 실제 수신 가능성을 별도로 검사한다. webhook 미준비는 cron 설치·알림 시험을 막으며, 이미 승인된 source 설치·외부 전송 없는 probe와는 독립이다. 각 단계의 필수 입력이 실패하면 해당 단계만 중단한다.

### 서비스 배포와 source 설치

1. 최종 main SHA로 ARM64 이미지 5종과 migrator를 빌드하고 기존 배포 packet의 tar/image hash를 새로 봉인한다.
2. `COLAB_DEV_SSH`와 `COLAB_DEV_KEY_FILE`을 레포 밖 값으로 설정하고 `infra/dev/ship.sh <dist>`를 실행한다.
3. ship은 archive hash 확인 → root 소유 `/opt/colab-ops/versions/<SHA>` → manifest 136파일·source SHA·owner/mode/symlink 검사 → root 고정 dispatcher 설치 → 이미지 load → `/opt/colab-v2/CURRENT_SHA` 갱신까지 수행한다. 서비스 `up.sh`는 아직 수행하지 않는다.
4. 기존 `/etc/cron.d/colab-ops`가 이미 있는 재배포라면 CURRENT_SHA 갱신 순간부터 다음 cron 회차가 새 dispatcher/source와 새 SHA 이미지를 대상으로 실행될 수 있다. ship 전에 정확한 ops cron 파일을 snapshot·hash 보존 후 cron 디렉터리 밖으로 일시 분리하고, 이미 실행 중인 해당 세 target 회차가 모두 종료했는지 프로세스·잠금으로 확인한다. 종료 확인 전에는 ship하지 않는다. 새 서비스 `up.sh`와 doctor가 green인 뒤 같은 owner/mode/hash의 원래 cron을 복원하고 verify한다. 잠금이 잠깐 풀린 것만으로 다음 cron을 막았다고 주장하지 않는다. 이번 최초 설치는 ops cron이 없어 이 간격 영향이 없다.
5. 명시적 `COLAB_IMAGE_TAG=dev-<SHA>`로 `/opt/colab-v2/up.sh`를 실행하고 migration·4서비스 health·web index·doctor 15/15를 확인한다.
6. `/opt/colab-ops/bin/dispatch-current.sh --check`가 `CURRENT_SHA=<SHA>`와 resident manifest 전건 일치를 내야 한다.

### webhook 없이 먼저 실행할 read-only probe 3종

아래는 version source에서 직접 한 번씩 실행한다. cron state나 외부 메시지를 만들지 않는다.

```bash
sudo /opt/colab-ops/versions/<SHA>/infra/ops/probes/service-health.sh
sudo /opt/colab-ops/versions/<SHA>/infra/ops/probes/deploy-verification.sh
sudo /opt/colab-ops/versions/<SHA>/infra/ops/probes/backup-freshness.sh
```

기대값: service 4/4 unit 일치, deploy doctor 15/15·skip 0, backup의 기존 operator-credential+freshness oracle green. 세 실행의 exit와 원문은 분리 보관하고 합산 통과로 바꾸지 않는다.

### 2026-09-11 실제 probe 결과 — I4 추가 잔여

service-health와 backup-freshness는 각각 exit0. deploy-verification은 IMDS 앱 역할로 실행되어 웹 버킷 HEAD/List가403, **13/2/0·exit1**이다. 기존 승인된 일회용 운영자 진단은 같은 dev/SHA에서 **15/0/0·exit0**이지만 cron의 실패를 대신하지 않는다. 제품 앱 역할 권한 확대·장기키 설치·skip 추가는0이다. 자동 진단의 운영자 권한 경로를 확정하고 실제 probe가 통과하기 전에는 cron/raise/clear 실행 준비가 끝난 것이 아니다. 상세 `reports/stage12-release-acceptance/release.md`.

검토 가능한 최소 대안은 `reports/stage12-i4-minimal-iam/execution-packet.md`에 별도로 준비했다. 공개 `index.html` 읽기와 `assets/` 목록만 허용하는 새 inline policy2문이며, 기존 정책을 덮어쓰지 않는다. 실제 IAM 적용0. 현재 등록 AWS profile은 `colab-dev` 하나이고 IAM 사전조회 권한이 없어 새 policy 이름 부재조차 판정하지 못했다. IAM 권한을 가진 운영자 실행 경로와 사용자 선택이 필요하다. 이 대안을 승인받았다고 외부 알람 전송 승인까지 받은 것으로 보지 않는다.

### webhook·cron 연결의 현재 blocker

- 외부 수신처가 아직 지정되지 않았다. HTTPS 한 줄짜리 root:0600 webhook 파일 경로가 없으므로 `install-schedule.sh`는 readiness 78이어야 한다.
- 사용자에게 필요한 입력은 **시험 알림을 받을 채널과 EC2 위 root:0600 파일 경로 하나**다. URL 값 자체는 대화·보고서·명령줄에 싣지 않는다.
- 수신처가 정해지고 별도 실행 승인을 받은 뒤에만 `sudo .../install-schedule.sh --env dev --webhook-file <PATH> install`을 실행한다.
- 설치 전후 `/etc/cron.d/colab-dev` hash가 위 값과 같고, `/etc/cron.d/colab-ops`는 root:0644·5분 3대상이어야 한다. snapshot과 새 파일 hash를 기록한다.
- raise/clear는 실제 수신처에 메시지 2건을 보내므로 별도 승인 범위다. 연속 실패 2회에서 raise 1회, 반복 실패 추가 통지 0, 회복에서 clear 1회를 수신 측과 runner JSON 양쪽에서 대조한다.


### 실제 raise·반복·clear 무중단 시험

운영 cron과 상태를 섞지 않는 승인 후 시험이다. 실제 서비스·compose·DB는 중단하거나 바꾸지 않는다.

1. `/opt/colab-v2/ops-alerts/acceptance-<RUN>/`을 root:0700으로 만들고 state/log를 이 안에만 둔다. 운영 `/opt/colab-v2/ops-alerts/*.state.json`과 cron 파일 hash를 전후 대조한다.
2. 별도 probe 입력 디렉터리에 운영 `MAIN_SHA`를 읽기 전용 복사하고, `CURRENT_SHA`는 존재하지 않는 형식상 유효한 12자리 hex로 만든다. `COLAB_DEV_STATE=<입력디렉터리>`로 `deploy-verification.sh`를 호출하면 실제 probe가 현재 서비스에 쓰지 않고 `현재 SHA 이미지 부재`로 실패한다. 복사한 `MAIN_SHA`와 두 CURRENT 값의 hash를 기록하되 내용은 보고서에 싣지 않는다.
3. 같은 격리 state와 시험 target `acceptance-deploy-verification`로 아래 runner 명령을 실패 3회 실행한다. 1회는 통지 0, 2회는 raise 1, 3회는 추가 통지 0이어야 한다. runner JSON과 수신 채널을 함께 대조한다.
4. probe 입력의 `CURRENT_SHA`를 실제 현재 SHA로 원자 교체하고 `MAIN_SHA`는 그대로 둔 뒤 같은 runner를 한 번 실행한다. 실제 deploy doctor 15/15가 green이고 clear 1건만 전송되어야 한다.
5. 시험 디렉터리만 보존 증거로 봉인한다. 운영 cron 설치 여부와 무관하게 시험은 별도 target·state·probe-input을 사용하므로 운영 target lock이나 state에 손대지 않는다. 수신 채널에서는 `acceptance-deploy-verification`만 시험 메시지로 계수하고 같은 시각의 운영 target 메시지와 섞지 않는다. 운영 state를 복사·수정·삭제하지 않는다.

정확한 runner 형태(값은 실행 직전 봉인한다):

```bash
sudo env COLAB_DEV_STATE=/opt/colab-v2/ops-alerts/acceptance-<RUN>/probe-input \
  /opt/colab-ops/versions/<SHA>/infra/ops/alarm_runner.py \
  --state /opt/colab-v2/ops-alerts/acceptance-<RUN>/alarm.state.json \
  --target acceptance-deploy-verification --threshold 2 \
  --webhook-file <ROOT_0600_WEBHOOK_FILE> --timeout 120 -- \
  /opt/colab-ops/versions/<SHA>/infra/ops/probes/deploy-verification.sh
```

세 번째 실패 뒤 probe-input의 `CURRENT_SHA`만 실제 SHA로 바꾸고 같은 명령을 회복 1회 실행한다. webhook URL 값, DB URL, AWS credential은 명령·로그·보고서에 출력하지 않는다.

### I4 중단·복구

- source/manifest/current SHA·owner/mode/symlink 중 하나라도 어긋나면 cron 설치 전 중단한다.
- probe 하나라도 red/78이면 cron과 외부 전송을 시작하지 않는다.
- cron 설치 후 candidate 서비스 rollback이 필요하면 candidate source의 `install-schedule.sh ... remove`로 정확한 ops 파일만 제거하고 `/etc/cron.d/colab-dev` hash 불변을 확인한 뒤 앱 rollback을 수행한다. `/opt/colab-ops/versions/<SHA>`는 비활성 증거로 남기며 자동 삭제하지 않는다.

## 실행 권한과 마지막 승인 문안

현재 대화에서 이미 승인되어 자율 실행할 범위는 다음과 같다.

- 최종 main 확정·push와 그 SHA의 dev 배포.
- dev의 root-owned ops source 설치.
- 외부 전송과 cron 상태 변경이 없는 read-only probe 3종.

마지막 추가 승인이 필요한 범위는 다음 두 가지뿐이다.

1. **I3 cron·실패 drill 승인**: 전용 clean worktree 생성, crontab deploy 블록 설치, TEST marker 1개를 이용한 fast-forward 전 RED, marker 제거, 같은 최종 main SHA의 다음 5분 GREEN staging 배포.
2. **I4 외부 알림 승인**: 수신처 파일 경로가 준비된 뒤 webhook cron 설치와 실제 raise 1건·clear 1건 전송.

I3 승인 전에도 최종 main push와 이미 승인된 I4 dev 배포·source 설치·read-only probe를 독립 진행한다. 실행 직전 최종 SHA, 직전 green, crontab/dev-cron hash, bundle/archive/manifest hash가 이 문서와 달라지면 해당 패킷을 다시 봉인한다. 현재 bundle 값은 통합 후보 `205de119433119212212766cce9233644cdc786c` 기준의 임시 값이므로 최종 main SHA가 달라지는 즉시 무효다.
