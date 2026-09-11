# I3 cron 실행 전 준비 실측

실측 시각: 2026-09-11 KST. 실제 cron 설치, dirty marker 생성, pipeline 실행, 배포, 서비스/DB 변경은 0건이다. 비밀 값은 읽거나 출력하지 않았다.

## 고정 대상

- 최종 main/remote: `30f5adf6774771c9ca34e2c3a0b92a0648b9cc76`; `origin/main`과 일치.
- 전용 worktree: `/home/ttlhi10/colab-v2-staging-deploy`, branch `staging/auto-deploy`.
- 시작 HEAD: 최종 main의 직접 부모 `e90e5c2553a7795176cfcc218d8957b74da5869e`.
- worktree는 생성 직후 clean. cron 조건을 흉내 낸 최소 환경에서 `git fetch --quiet origin main` exit 0, LOCAL=`e90e5c…`, REMOTE=`30f5adf…`를 확인했다.
- 최종 main 부모와 최종 main 사이 및 기존 ops-runtime 기준 `620f406…`과 부모 사이의 `infra/staging/pipeline/**` 차이는 0개다.

## 실제 cron 환경 readiness

- 최소 환경: `HOME=/home/ttlhi10`, `USER/LOGNAME=ttlhi10`, `SHELL=/bin/sh`, `PATH=/usr/local/bin:/usr/bin:/bin`.
- 위 PATH에서 `bash git docker python3 psql pg_dump aws crontab flock curl sha256sum sed grep date mktemp` 전부 탐색 성공.
- `~/.colab-v2-staging.env` 존재, mode 0600. 내용은 출력하지 않았다.
- staging target approval check exit 0. `watch.sh`와 `install-schedule.sh` mode 0755.
- 현행 crontab 읽기 exit 0, SHA-256 `d554b72cb92947d038b9495577fe5fcdfe0adbf90026f2b724cdb9f7da25dbd4`, 비공백 36줄, backup 시작/끝 각 1, deploy 시작/끝 각 0.

## 현재 서빙·복구

- staging 컨테이너 8개 전부 healthy, 서빙 이미지 6종은 `09e2b9b2db1a`.
- 즉시 rollback 이미지 `09e2b9b2db1a`: 6/6 존재.
- 이전 fallback `a8541b7c3c33`: 6/6 존재.
- `DEPLOY-FAILED.txt` 없음, `LAST-SUCCESS.txt`와 release ledger 존재.

## 승인 뒤 정확한 호출 순서

```bash
# 1. 설치 직전 remote를 다시 봉인하고 main 변경을 GREEN 종료까지 동결한다.
env -i HOME=/home/ttlhi10 USER=ttlhi10 LOGNAME=ttlhi10 SHELL=/bin/sh \
  PATH=/usr/local/bin:/usr/bin:/bin \
  git -C /home/ttlhi10/colab-v2-staging-deploy fetch --quiet origin main
git -C /home/ttlhi10/colab-v2-staging-deploy rev-parse origin/main \
  > /home/ttlhi10/colab-v2-releases/I3-REMOTE-SHA.txt
sha256sum /home/ttlhi10/colab-v2-releases/I3-REMOTE-SHA.txt

# 2. 승인된 RED marker를 하나 만들고 cron 블록을 설치한다.
touch /home/ttlhi10/colab-v2-staging-deploy/TEST-I3-DIRTY-RED
/home/ttlhi10/colab-v2-staging-deploy/infra/staging/pipeline/install-schedule.sh install

# 3. 첫 실제 5분 회차가 checkout 단계 exit 65인지 확인한 뒤 marker 하나만 제거한다.
unlink /home/ttlhi10/colab-v2-staging-deploy/TEST-I3-DIRTY-RED

# 4. 다음 실제 5분 회차 GREEN 뒤 remote 봉인값, HEAD, ledger, serving tag를 대조한다.
git -C /home/ttlhi10/colab-v2-staging-deploy rev-parse HEAD
/home/ttlhi10/colab-v2-staging-deploy/infra/staging/verify/verify-deploy.sh
/home/ttlhi10/colab-v2-staging-deploy/infra/staging/verify/verify-chains.sh
```

`install` 전 crontab snapshot 경로/hash를 기록한다. RED 전후에는 public health, 8개 컨테이너 image ID, migration heads, ledger, LAST-SUCCESS를 대조한다. RED가 fast-forward 전에 끝나지 않으면 marker를 제거하지 않는다. GREEN 실패 시 자동 rollback하지 않고 증거를 보존한 뒤 `09e2b9b2db1a` 복구 승인을 적용한다.

## 검증

- 전용 worktree의 `infra/staging/pipeline/selftest.sh`: GREEN, pipeline 54건과 verify 22건. 실패 fixture가 실제 red를 냈다.
- lifecycle 첫 선언의 `pipeline-selftest`는 등록되지 않은 gate 이름이라 0/1/0으로 실패했다. 성공으로 재사용하지 않았다.
- 새 lifecycle에는 등록된 `exec-bit`를 선언해 실행 파일 모드와 현재 보고서 hash를 검증한다.
