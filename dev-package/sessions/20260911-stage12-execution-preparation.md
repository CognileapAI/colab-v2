# Stage 1·2 미완료 5건 실행 준비

> 후속 실행 기록: 사용자가 이후 전체 실행을 명시적으로 승인했다. 아래 미승인·입력 대기는 **준비 당시 이력**이다. 실제 결과와 U-2 새 버전 재업로드 복구 대안은 [승인된 실행 기록](20260911-stage12-execution.md)을 따른다. 이미 적용한 plan·삭제 명령을 재실행하지 않는다.

상태: 조사·로컬 준비 진행 중. 실제 실행 승인 전. 사용자 원본 수정은 보존하고 origin/main `c329c32d2f6d469deb12d64f6cb89e60994b1d3d`에서 격리 사본을 만들었다.

## 범위와 승인 경계

2026-09-11 이번 요청은 읽기 전용 조사, 로컬 보완·빌드·시험, 실행 자료 준비를 허용한다. 과거 패킷의 승인 문구를 이번 권한으로 사용하지 않는다. 실제 데이터 삭제, Terraform apply, IAM 변경, cron 설치, 서버 배포, 외부 알람 전송은 미승인이다. 서버 env·보호된 URL 파일·장부 volume 생성·최초 장부 발행도 실행 승인 묶음에 넣는다.

보류 3건(격자선·눈금, Google 로그인, 실패 업로드 3건 처분)은 범위 밖이다.

## 전체 계획과 의존 관계

| 항목 | 최신 대장 | 준비 | 의존·완료 증거 |
|---|---|---|---|
| U-2 | partial | 대상·보존 목록 재관측, 직전 백업·정확한 삭제·복구 명령 | 독립. 승인 뒤 실제 회수·보존 검증 전 done 금지 |
| IS4 | partial | saved plan·hash·drift·apply 시도 여부 재확인 | 독립. 승인된 plan 적용·no-change·health 확인 전 done 금지 |
| I3 | partial | 후보 c329c32, 시작 d56428d, 별도 이미지 빌드 사본 | TL-2 최초 장부·실제 viz 읽기 → 실제 5분 dirty 차단 → 같은 후보 배포 |
| I4 | open | 운영자 이름·알람 경로 질문, 최소 IAM·자동 probe 재확인 | IAM 사전조회·승인 → IMDS 단일 15/0/0 → cron 및 별도 raise/clear 승인 |
| TL-2 | partial | 후보 이미지·DB 읽기 권한·URL·장부 volume·viz UID/GID | 최초 발행 → I3 → dev/staging 매시간 발행 및 staging 정기 소비 증거 |

- [x] 사용자 수정 보존·원격 main fetch·깨끗한 격리 사본 확인.
- [x] 최신 대장 계수: Stage 1 done61/partial1/deferred1, Stage 2 done90/partial3/open1/deferred2.
- [x] d564→c329 변경 16개 모두 dev-package 문서·보고서. 제품 코드·배포 스크립트 동일.
- [x] 필요한 운영자 프로필 이름·알람 수신처 또는 보호된 파일 경로 질문. 비밀값은 요청하지 않음.
- [x] U-2·IS4 현재 실물 재확인과 실행 패킷 보완.
- [x] I3·TL-2 현재 실물 재확인과 후보 이미지 6종 빌드.
- [x] I4 실제 자동 점검 재실행·최소 정책 확인. 운영자 프로필·알람 경로는 입력 대기.
- [x] 정확한 대상·명령·영향·복구·중단 조건 통합. 독립 검토의 U-2 복구 자격·I3 cron 제거·dev hourly 명령 보완 반영.
- [x] 기존 검증 재사용 범위와 관련 문서 검사 3개(contract-lint/work-item-consistency/planning-freshness) 고정. 실제 결과는 `../reports/stage12-execution-preparation/gates/gate-summary.json`에 기록한다.
- [ ] 운영자·수신처 입력 확인 후 A/D 준비 종료. B/C는 최종 검토 결과를 붙여 실행 승인 요청.

## 검증 재사용 경계

d564 제품 전체검사 단일 61/0/0 및 해당 SHA의 dev 수용 기록은 기존 근거다. c329에서 전체 제품검사를 새로 실행했다고 하지 않는다. 제품 변경이 없으므로 제품 전수 재실행 대신 후보 이미지 빌드와 바뀐 문서의 관련 검사를 수행한다. 서버 환경·삭제 대상·Terraform drift는 새로 재확인한다. 운영자 doctor 15/0/0과 IMDS 자동 doctor 13/2/0은 별도 결과다.

## 이번에 다시 확인한 것

현재 관측 요약은 [fresh-observations.json](../reports/stage12-execution-preparation/fresh-observations.json), [I4 단일 실행](../reports/stage12-execution-preparation/i4-observation.json), [후보 및 이미지 고정](../reports/stage12-execution-preparation/i3-candidate.json)에 있다.

| 항목 | 된 것 | 안 된 것 | 막힌 이유·다음 행동 |
|---|---|---|---|
| U-2 | 10:57:50 UTC 같은 파일 1개·12,599,296B·완료 기록 7개, 대상 hash 불변 | 실제 삭제·직전 새 백업 | 승인 후 백업하고 같은 목록만 실행 |
| IS4 | 현재 원격에서 새 plan 준비, update1·설정값 변화0·drift0 | 실제 apply·최종 no-change | 새 hash 승인 필요 |
| I3 | 후보6이미지 빌드, 시험 사본 부모 유지, 직전 정상 이미지6/6 | 실제5분 RED→GREEN | TL-2 최초 장부 및 cron/배포 승인 필요 |
| I4 | 현재 IMDS 점검13/2/0, service/backup 각exit0, 설치 source 검증 성공 | IAM 사전조회·자동15/0/0·cron·알람 | 운영자 프로필/보호된 수신처 입력 + 실행 승인 필요 |
| TL-2 | 후보 사용자10001:999, 기존 postgres 전수 읽기 가능, 준비 순서 고정 | staging URL/volume/최초발행·정기실행, dev 매시간 발행 | 서버 준비·cron 승인 필요 |

## 실행 승인 묶음 A — 파일 정리 (U-2, 복구 자격 입력 대기)

**실행 선행 조건:** 복구에 쓸 운영자 프로필과 exact-key 버전 조회·DeleteObjectVersion 권한 확인이 아직 없다. I4와 함께 질문한 운영자 입력을 받은 뒤 복구 실행 경로까지 검증하기 전에는 삭제하지 않는다. 삭제 대상 준비와 복구 자격 준비를 구분한다.

정확한 대상과 전체 CLI는 [U-2 실행 패킷](../reports/stage12-tl2-deploy/u2-apply-packet.md)을 사용한다. 이번 관측으로 대상 목록과 semantic hash가 그대로임을 재확인했다.

- 버킷 `colab-platform-data-dev`, 리전 `ap-northeast-2`.
- key `uploads/01M24KWBG3M37A0WYBX22VJ94P/01M24KWBG3MZGEBFGBGTST9BZJ`, 12,599,296B.
- semantic hash `3031054b040d75fd8e0f7192e94712010e9e50ce0cbeaec1b957d79931fc340c`.
- 완료 기록7개는 링크된 패킷과 새 관측 JSON의 `completedTransferIds` 정확한 목록으로 고정한다. 만료 열린 전송0, B 대상0.
- 보존: A dataset25/file448/registered upload40, B dataset1/file2/registered upload1, 보류 실패 업로드3건.
- 실행 코드 d564 전체 SHA 및 실제 core image `sha256:d14a7121b96fe2f95d7d0da284a77a7830d213a187592474875fa9a8db630003`을 실행 직전 다시 대조한다.
- private 입력은 기존 `/tmp/colab-stage12-u2-approval-d564/u2-plan.json`, 파일0600·디렉터리0700. 파일 바이트 hash `e448ee61592311b48b814fbc5cdb572b8833de29bc195baac539da1008b39a51`과 semantic hash를 구분한다.

승인 후 dev에서 `sudo -n /opt/colab-v2/backup.sh`를 실행하고 두 DB 백업 key·크기·HEAD를 봉인한다. 과거 백업을 직전 백업으로 대신하지 않는다. 백업 불일치면 삭제0으로 중단한다. private plan을 패킷의 소유자·권한 검증 절차로 전달한 뒤 아래 명령을 실행한다.

```bash
docker exec \
 -e COLAB_RUNNING_IMAGE_CONFIG_ID=sha256:d14a7121b96fe2f95d7d0da284a77a7830d213a187592474875fa9a8db630003 \
 -e COLAB_RELEASE_SHA=d56428d6945d \
 colab_v2_dev_core_api python -m colab_core.app.storage_maintenance_cli \
 --apply-approved --plan /tmp/colab-u2-approval/u2-plan.json \
 --plan-sha256 3031054b040d75fd8e0f7192e94712010e9e50ce0cbeaec1b957d79931fc340c \
 --lab-id 0000000000000000000000000A --account-id 00000000000000000000000AP1 \
 --environment dev --expected-bucket colab-platform-data-dev --expected-region ap-northeast-2 \
 --expected-code-sha d56428d6945d677cae013d6bff25cb61727f3166 \
 --expected-image-config-id sha256:d14a7121b96fe2f95d7d0da284a77a7830d213a187592474875fa9a8db630003
```

성공 조건: reclaimedUploads1/prunedCompletedTransfers7/reapedOpenTransfers0과 보존 계수가 일치해야 한다. 실패 시 대상을 넓히지 않는다.

복구는 원본 version `zc8Ym1jp05uAkWiAJfLQuEVGr2Ywm8LY`가 남았는지 exact key로 확인하고, 이번 삭제가 만든 **delete marker 한 개만** 제거한다. 아래 변수는 실행 후 실제 관측으로만 채우며 원본 version ID를 넣으면 안 된다.

```bash
: "${COLAB_AWS_OPERATOR_PROFILE:?validated operator profile}"
: "${U2_DELETE_MARKER_VERSION_ID:?exact marker created by this execution}"
aws --profile "$COLAB_AWS_OPERATOR_PROFILE" --region ap-northeast-2 s3api delete-object \
 --bucket colab-platform-data-dev \
 --key uploads/01M24KWBG3M37A0WYBX22VJ94P/01M24KWBG3MZGEBFGBGTST9BZJ \
 --version-id "$U2_DELETE_MARKER_VERSION_ID"
```

DB 기록은 실행 직전 platform 백업을 별도 tmpfs PostgreSQL에 먼저 복원하여 대상 행을 대조한다. 운영 DB 전체 덮어쓰기·downgrade는 이 승인에 포함하지 않는다. 실제 DB 재삽입이 필요하면 동시 변경과 FK를 검토한 별도 복구 승인을 받는다. S3 파일 복구만으로 DB 기록까지 복구됐다고 하지 않는다.

## 실행 승인 묶음 B — 설정 기록 복구 (IS4)

기존 계획은 존재하고 옛 hash `6e752d0d…`도 불변이었다. 그러나 현재 원격에서 새로 import·scratch refresh-only·full plan을 만들었으므로 **이번 승인 대상은 새 계획 하나**다. 옛 파일은 이력으로 보존한다.

- private bundle `/tmp/colab-stage12-prep-u2-is4` (0700, 파일0600).
- `final.tfplan` 4918B, SHA256 `05eec879b7458524cbeef795ed6a57dcccce2907841e53130b8cef5aa419f8b4`.
- resource `cloudflare_zero_trust_tunnel_cloudflared_config.staging` 하나, update1. before=after이고 sensitivity metadata만 변화. resource drift0, public health200.
- state SHA256 `dae32582177ea803bfb75979f177443060111e758c5d71f14e918d81f0b25152`.
- provider lock SHA256 `fe7c09121a6463901177cc0dbdf896bf56ee1dd170805ec940feb187a656ff7b`.
- Terraform1.9.8, image `hashicorp/terraform@sha256:18f9986038bbaf02cf49db9c09261c778161c51dcc7fb7e355ae8938459428cd`.
- prepare exit78은 승인 대기이며 apply 성공이 아니다. 원격 apply0, apply-attempt 표식0.

후보 c329의 저장소 루트에서 승인 후 한 번만:

```bash
bash infra/staging/tunnel/rehearse-state-recovery.sh \
 --apply-approved /tmp/colab-stage12-prep-u2-is4 \
 --plan-sha256 05eec879b7458524cbeef795ed6a57dcccce2907841e53130b8cef5aa419f8b4
```

실행기는 apply 직전 remote/state drift0·선언·provider lock·image·hash·health를 다시 확인한다. 불일치면 적용하지 않고 새 계획을 준비한다. 성공 조건은 apply 뒤 detailed plan exit0 (`No changes`)와 public health200이다. 실패·재시도 표식이 생기면 같은 bundle을 재사용하지 않는다. `terraform state push`는 복구로 사용하지 않는다. 복구는 현재 remote를 다시 읽어 별도 plan과 hash를 준비하고 승인받는다.

## 실행 승인 묶음 C — 최초 장부·자동 배포·정기 발행 (I3/TL-2)

| 고정점 | 값 |
|---|---|
| 후보 전체 SHA | `c329c32d2f6d469deb12d64f6cb89e60994b1d3d` |
| 시험 시작 SHA | `d56428d6945d677cae013d6bff25cb61727f3166` |
| 이미지 준비 사본 | `/tmp/colab-i3-tl2-build.omrci2`, clean c329 |
| 자동 배포 시험 사본 | `/home/ttlhi10/colab-v2-staging-deploy`, clean d564 |
| 직전 정상 버전 | `09e2b9b2db1a`, 복구 이미지6/6 |
| 한 단계 더 오래된 보존 버전 | `a8541b7c3c33`, 이미지6/6 |
| 후보 이미지 | 6종 amd64, 정확한 ID는 후보 JSON |
| 기존 사용자 cron | SHA256 `d554b72cb92947d038b9495577fe5fcdfe0adbf90026f2b724cdb9f7da25dbd4`, 비공백36줄·백업표식2·배포0 |

후보 파일은 격리 사본의 `.codex/artifacts/stage12-tl2-deploy/i3-final-candidate.json`에 새로 준비했고 공유 가능한 동일 내용은 위 후보 JSON에 있다. 기존 원본 사본의 오래된 파일은 수정하지 않았다. 이 준비 문서를 병합하려고 후보를 바꾸지 않는다.

1. 승인된 실행 창 동안 main에 다른 push/merge를 하지 않는다. 실행 직전 `git ls-remote origin refs/heads/main`을 후보와 대조한다. RED 앞과 GREEN 뒤 다시 확인하고, GREEN 실제 서빙 SHA도 대조한다. 값이 달라지면 같은 후보 시험으로 수용하지 않는다. 로컬 조회는 다른 사람의 push를 막는 잠금이 아니므로 실행 창 조율도 필요하다.
2. [staging 상세 명령](../reports/stage12-tl2-staging-packet/staging-execution-packet.md)의 env snapshot·ownership 값0/999/7200·root0600 psycopg URL·runner 설치·volume-init·최초 발행을 **빌드 사본**에서 실행한다. 기존 `postgres` 백업 자격을 사용하며 새 DB 권한은 부여하지 않는다. `colab_owner` URL은 전수 권한이 없어 사용할 수 없다.
3. 실제 후보 viz 기본 사용자10001:999로 새 장부를 읽고 loader 검증한다. root 읽기 성공으로 대신하지 않는다. 디렉터리0:999/0550, 파일0:999/0440, max-age7200. 장부가 없거나 오래되면 배포하지 않는다.
4. 시험 사본 HEAD=d564·clean, remote=c329를 확인하고 빈 `TEST-I3-DIRTY-RED` 하나만 만든다. 기존 crontab을 snapshot·hash 보존한 뒤 해당 사본에서 `bash infra/staging/pipeline/install-schedule.sh install`을 실행한다. 첫 실제5분 cron이 fast-forward 전 exit65·dirty1로 차단돼야 한다.
5. RED 때 `DEPLOY-FAILED.txt` 생성, LAST-SUCCESS·서빙 image·DB head·릴리스 장부 불변, 전후health200을 확인한다. 원격 후보 증거를 별도로 봉인한다. 이 조건이 아니면 marker를 지우지 말고 중단한다.
6. **그 marker 하나만 제거**하고 다음 실제5분 cron을 기다린다. 같은 후보c329 배포, backup 두 체인·migration·verify-deploy·verify-chains 성공, 8/8 healthy·health200, 실패표식 제거, LAST-SUCCESS·릴리스 장부·실제 태그 일치를 확인한다. 배포 과정에서 재빌드하면 최종 image ID를 다시 봉인한다.
7. 승인된 매시간 publisher를 dev와 staging에 설치하고 실제 예약 시각의 발행 증거를 각각 남긴다. staging은 그 뒤 실제3600초 정기 분류 한 바퀴에서 장부시각/count/hash·ownership4등급·legacy3등급·unreachable·deleted0을 연결한다. 시작 직후 로그나 수동 실행을 정기 주기로 세지 않는다.

staging의 보호된 URL, 장부 volume, runner는 이번 조회 시 없다. 따라서 실제 사용자 읽기는 아직 미실행이다. 174벌 분류는 이전 dev 기동 직후 결과이며, 오늘 실제 정기 주기로 바꾸어 기록하지 않는다. DB·S3·캐시 삭제0을 유지한다.

중단·복구: GREEN 실패 시 자동 재시도·자동 rollback을 추정하지 않고 실패 로그를 보존한다. 후보 파이프라인의 rollback 절차로 직전09e2를 우선 검토한다. crontab은 이번 설치 직전 snapshot으로 복원하고 백업표식2·hash를 확인한다. DB downgrade0. 장부·URL·runner는 증거를 보존하고 무조건 삭제하지 않는다. 신규 cron만 제거/복구하며 기존 백업 예약을 덮어쓰지 않는다.

### 개발 서버 매시간 장부 발행 — 이번 승인 제안

현재 dev runner는 root:root0755, SHA256 `7b18396555d252a1ed372989ed0a1aad2efce16c39e00da4c4ea7075f4af0dcd`다. 전용 URL은 root:root0600이다. dev의 실제 태그는 `colab-v2/core-api:dev-d56428d6945d`이며, image ID `sha256:d14a7121b96fe2f95d7d0da284a77a7830d213a187592474875fa9a8db630003`이 현재 실행 core와 일치함을 부모가 직접 확인했다. staging 태그 형식과 혼용하지 않는다. 아래 wrapper/cron 목적지는 현재 둘 다 없고 symlink도 없다. 기존 `/etc/cron.d/colab-dev`는 수정하지 않는다.

승인 후 dev의 독점 실행 창에서 실행한다. `OPS_SNAPSHOT_DIR`은 root0700의 이번 실행 전용 증거 디렉터리로 정한다. snapshot을 먼저 만들고 아래 두 대상의 부재를 재확인한다. root shell에서 실행하는 명령이다.

```bash
set -euo pipefail
: "${OPS_SNAPSHOT_DIR:?root0700 execution evidence directory}"
test "$(stat -c '%u:%a' "$OPS_SNAPSHOT_DIR")" = 0:700
cp -p /etc/cron.d/colab-dev "$OPS_SNAPSHOT_DIR/colab-dev.before"
sha256sum /etc/cron.d/colab-dev > "$OPS_SNAPSHOT_DIR/colab-dev.sha256"
test ! -e /opt/colab-v2/publish-ownership-hourly
test ! -L /opt/colab-v2/publish-ownership-hourly
test ! -e /etc/cron.d/colab-ownership-snapshot
test ! -L /etc/cron.d/colab-ownership-snapshot
umask 077
cat > "$OPS_SNAPSHOT_DIR/publish-ownership-hourly" <<'WRAPPER'
#!/usr/bin/env bash
set -euo pipefail
exec env COLAB_OWNERSHIP_COMPOSE_PROJECT=colab-v2-dev \
 COLAB_OWNERSHIP_CORE_IMAGE=colab-v2/core-api:dev-d56428d6945d \
 COLAB_OWNERSHIP_DB_URL_FILE=/etc/colab/ownership-platform-db.url \
 COLAB_OWNERSHIP_VIZ_GID=999 /opt/colab-v2/publish-ownership-snapshot.sh
WRAPPER
install -o root -g root -m 0700 "$OPS_SNAPSHOT_DIR/publish-ownership-hourly" /opt/colab-v2/publish-ownership-hourly
cat > "$OPS_SNAPSHOT_DIR/colab-ownership-snapshot" <<'CRON'
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
17 * * * * root /opt/colab-v2/publish-ownership-hourly >>/var/log/colab-v2-dev-ownership.log 2>&1
CRON
install -o root -g root -m 0644 "$OPS_SNAPSHOT_DIR/colab-ownership-snapshot" /etc/cron.d/colab-ownership-snapshot
sha256sum -c "$OPS_SNAPSHOT_DIR/colab-dev.sha256"
sha256sum /opt/colab-v2/publish-ownership-hourly /etc/cron.d/colab-ownership-snapshot > "$OPS_SNAPSHOT_DIR/installed.sha256"
```

설치 후 첫 실제 매시17분 로그·새 장부시각/count/hash와 실제 viz 사용자 읽기를 확인한다. 설치 성공만으로 매시간 발행 성공이라고 하지 않는다. 실패 시 설치한 두 파일의 hash가 이번 설치본과 같은지 대조하고, 새 cron 파일만 cron 디렉터리 밖 증거 디렉터리로 이동해 예약 실행을 중단한다. 복구 root shell 명령은 다음과 같다.

```bash
sha256sum -c "$OPS_SNAPSHOT_DIR/installed.sha256"
test ! -e "$OPS_SNAPSHOT_DIR/colab-ownership-snapshot.disabled"
mv /etc/cron.d/colab-ownership-snapshot "$OPS_SNAPSHOT_DIR/colab-ownership-snapshot.disabled"
sha256sum -c "$OPS_SNAPSHOT_DIR/colab-dev.sha256"
```

현재 진행 중인 publisher 종료를 확인한다. 기존 colab-dev hash를 다시 확인한다. wrapper·장부·로그는 보존한다. 후속 배포 시 고정 이미지 태그도 검토·갱신해야 한다.

### 테스트 서버 복구 명령

GREEN 실패 후 시험 사본이 후보까지 전진했는지 확인하고 승인된 복구 범위에서만 실행한다.

```bash
test "$(git rev-parse --short=12 HEAD)" = c329c32d2f6d
export COLAB_PIPELINE_STATE_DIR=/home/ttlhi10/colab-v2-releases
bash infra/staging/pipeline/install-schedule.sh remove
# 기존 backup 예약 보존과 진행 중 watch/deploy 프로세스 종료를 확인한 뒤 다음 명령 실행.
COLAB_STAGING_ENV=/home/ttlhi10/.colab-v2-staging.env \
 bash infra/staging/rollback.sh --to-tag 09e2b9b2db1a
```

cwd는 자동 배포 시험 사본이다. 배포 cron 블록을 먼저 제거하여 복구 직후 후보를 다시 배포하지 않게 한다. 진행 중 실행이 있으면 끝나기 전 rollback하지 않는다. `--to-last-green`으로 대상을 다시 고르지 않는다. 실제 image/health/릴리스 기록을 확인하며 DB schema·pgdata downgrade는 하지 않는다. cron 복원은 봉인한 설치 전 snapshot의 `crontab <snapshot>`이며, 이미 실행 중인 배포 종료를 확인한 뒤 복구한다.

## 실행 승인 묶음 D — 자동 점검 권한·알람 (I4, 입력 대기)

[최소 IAM 정책과 명령](../reports/stage12-i4-minimal-iam/execution-packet.md)의 오래된 probe 버전을 이번에 d564로 고쳤다.

- 계정606175197146, role `colab-platform-app-dev-role`, 새 inline policy `ColabDevPublicWebDoctorRead`.
- JSON SHA256 `b5e04c4a09fa6a1329d54aa652f83d90ac41bdf729239e6812baba62ea183157`.
- 허용은 `colab-platform-web-dev/index.html`의 GetObject, `assets/` prefix로 제한한 ListBucket 두 개뿐이다. 쓰기·삭제 권한0. 같은 role을 쓰는 앱도 이 읽기 권한을 얻는다.
- 현재 AWS 프로필 이름은 `colab-dev` 하나이나 IAM 정책 부재 확인 권한이 없다. **권한 있는 운영자 프로필 이름은 질문했고 답변 대기**다. 계정·role·기존 policy 목록/문서 hash·동일 이름 부재 확인 전 put하지 않는다. NoSuchEntity만 부재이며 AccessDenied는 준비 실패다.
- 외부 알람 **수신처 이름 또는 서버 root0600 파일 경로도 질문했고 답변 대기**다. 비밀키/webhook URL은 채팅에 요청하지 않는다. 입력 없이 경로를 지어내거나 알람을 보내지 않는다.

IAM 적용은 독점 실행 창에서 부재를 재확인한 뒤 정확한 새 정책 한 개만 put하고 canonical 내용/기존 정책 불변을 대조한다. IAM 전파 후 운영자 자격을 주입하지 않고 서버 IMDS 자격으로 아래 실제 probe를 실행한다.

```bash
sudo -n /opt/colab-ops/bin/dispatch-current.sh --check
sudo -n /opt/colab-ops/versions/d56428d6945d/infra/ops/probes/deploy-verification.sh
```

**같은 단일 실행15/0/0·exit0 전에는 cron/알람을 시작하지 않는다.** 현재 재실행은13/2/0·exit1이다. service와 backup 각exit0을 합쳐 통과로 만들지 않는다.

권한·수신처·승인 준비 뒤 아래 `<ROOT_0600_WEBHOOK_FILE>`을 사용자가 지정한 실제 경로로 고정하여 별도 승인 묶음에 넣는다. 아직 이 단계의 정확한 실행 입력은 미완료다.

```bash
sudo -n /opt/colab-ops/versions/d56428d6945d/infra/ops/install-schedule.sh \
 --env dev --webhook-file <ROOT_0600_WEBHOOK_FILE> install
```

[무중단 알람 시험 절차](20260911-i3-i4-approval-packet.md)의 격리 `acceptance-deploy-verification` target/state/probe-input을 사용한다. 운영 CURRENT_SHA는 바꾸지 않는다. 실패3회는 통지0→발생1→추가0, 실제 SHA로 회복1회는 해제1이어야 한다. runner JSON과 실제 수신처 양쪽에서 합계2건을 확인한다. 알람 cron 실제 실행 로그는 격리 수동 시험과 따로 기록한다.

복구: cron 설치 전 snapshot·기존 `/etc/cron.d/colab-dev` hash를 보존하고 ops 전용 cron만 검증 후 제거한다. IAM은 현재 canonical policy hash가 이번 설치본과 같을 때 새 이름 한 개만 delete한다. 타인이 바꿨으면 삭제하지 않는다. 상태·로그는 보존한다. 경로 입력이 없으므로 이 묶음은 실행 승인 준비 완료로 보고하지 않는다.

## 요구 대비 미달·초과와 검증 제한

- 이번 요청 대비 남은 입력: 운영자 프로필·알람 수신처/보호 경로. 운영자 입력 없이는 U-2의 버전 복구 권한 및 I4의 IAM 사전조회를, 수신처 입력 없이는 I4 수신처 검증을 끝낼 수 없다.
- 승인 뒤에만 가능한 실제 동작은 준비 실패를 숨기지 않고 각 묶음에 명시했다. 제품 항목 5건은 모두 기존 상태 유지다.
- 범위 초과 제품 변경0, 실제 삭제/apply/IAM/cron/서버배포/외부전송0. 로컬 후보6이미지 빌드와 새로운 private Terraform 준비만 수행했다.
- 조사 에이전트의 기존 read-only lifecycle 기록은 부모 문서 편집으로 무효가 되어 성공 인계로 사용하지 않았다. 부모가 U2를 새로 관측·저장하고 IS4 plan·hash·drift·후보 HEAD/clean·6이미지 ID 및 I4 probe를 직접 확인했다.

## 실행 후보 승인 범위

B는 새 plan hash 한 번의 적용·후속 no-change/health 확인이다. C는 준비된 c329 후보의 staging 최초 장부·5분 RED/GREEN 배포 및 dev/staging 매시간 발행 설치·실제 주기 관측이다. C 복구 승인에는 새 cron 해제·직전09e2 복구만 포함하며 DB downgrade나 데이터 삭제는 없다. A와 D는 입력·권한 검증 전 실행 요청 대상으로 올리지 않는다. 원격 후보·대상·계획 hash가 바뀌면 영향을 받는 묶음만 다시 준비한다.

문서 검사 범위: work-item-consistency는 기존 파싱 대상 밖9건과 항목표가 아닌 표2건을 별도로 공개하며 그 자리를 검사했다고 하지 않는다. planning-freshness는 임베드15개·적용상태4건이며 화면 검증이 아니다. 이번 제품 전체검사 재실행0, 기존 d564 61/0/0 재사용이다.
