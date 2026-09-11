# U2 실제 회수 승인 대상 — d564 배포 후 재봉인

상태: **승인 대기 · 실제 삭제0**. 사용자에게 아래 정확한 대상을 제시한 뒤 승인받아야 실행한다.

## 봉인한 대상

- 코드·배포: `d56428d6945d677cae013d6bff25cb61727f3166`.
- 실행 core config ID: `sha256:d14a7121b96fe2f95d7d0da284a77a7830d213a187592474875fa9a8db630003`.
- 연구실 A `0000000000000000000000000A`, 계정 `00000000000000000000000AP1`.
- semantic plan SHA256: `3031054b040d75fd8e0f7192e94712010e9e50ce0cbeaec1b957d79931fc340c`.
- private plan: `/tmp/colab-stage12-u2-approval-d564/u2-plan.json`, 디렉터리0700·파일0600 실측. 최초 `/mnt/f` 사본은 요청한0600과 달리 실제0777로 보여 private 입력으로 사용하지 않는다. 파일을 만든 것은 실행 승인이 아니다.
- 만료·미등록 업로드 `01M24KWBG3M37A0WYBX22VJ94P` 하나, 객체 `uploads/01M24KWBG3M37A0WYBX22VJ94P/01M24KWBG3MZGEBFGBGTST9BZJ` 하나, **12,599,296 B**.
- HEAD ETag `11285dc69fb39fcfe92aac6b935998f8`, versionId `zc8Ym1jp05uAkWiAJfLQuEVGr2Ywm8LY`, 버저닝 Enabled 재확인.
- 완료 후7일 지난 전송 메타7개: `01M1BXC86M3RKY37G6D17JZBRK`, `01M1BXJ5975SPV2B9P9SPX8THT`, `01M1C0EJV06P0R79NDZ8DAM2ZJ`, `01M1FSEQ0P3ZZGR64K25WS02YG`, `01M1GR9A7MXZBHN5A93KEZP0V9`, `01M1H2DFAFVJDXRAMFHKMPBZN0`, `01M1H4VR2X80TYG394ERG6RAYS`.
- 만료 열린 전송0, B 회수 대상0. B TEST 자료와 미완료 TEST 전송은 이 계획에 없다.

## 최신 읽기 전용 확인

`2026-09-11T10:03:25.217262+00:00`, 실제d564 core에서 DB `REPEATABLE READ, READ ONLY`와 연구실 scope로 확인했다. A dataset25/file448/registered upload40, B dataset1/file2/registered upload1은 보존한다. `u2-observation.json` SHA256은 실제 파일로 확인한다.

관측 도구는 이 단발 프로세스에서 후보 SELECT3개의 잠금 절만 제거했다. PostgreSQL READ ONLY가 쓰기를 막으며 S3 facade는 exact-key HEAD만 허용한다. 제품 파일·서버 코드 수정0, DB쓰기0, S3삭제0, 버킷목록0. 이 관측은 동시성 시험이나 실제 apply 검증이 아니다. 실제 apply는 원래 코드로 다시 잠근 뒤 semantic plan 전건이 일치할 때만 실행한다.

## 승인 후 실행 순서

1. 실행 직전 현재d564 이미지로 `/opt/colab-v2/backup.sh`를 실행하고 platform/AI 백업 두 객체의 실제 HEAD 크기를 확인해 실행 기록에 봉인한다. 마지막 확인 백업은 `2026-09-11T095249Z` platform111275B/AI5519B지만, 이를 미래 실행 직전 백업으로 대신하지 않는다.
2. 봉인한 로컬 plan만 SSH stdin으로 core 내부 `/tmp/colab-u2-approval/u2-plan.json`에 생성한다. 디렉터리0700, 파일0600, **실제 CLI 실행 UID 소유**를 lstat로 확인한다. symlink/기존 내용 불일치면 중단한다. 파일 SHA를 다시 대조한다.
3. 실행 컨테이너 image ID와 CURRENT_SHA를 아래 값과 대조한 뒤에만 아래 CLI를 호출한다.

```bash
docker exec \
  -e COLAB_RUNNING_IMAGE_CONFIG_ID=sha256:d14a7121b96fe2f95d7d0da284a77a7830d213a187592474875fa9a8db630003 \
  -e COLAB_RELEASE_SHA=d56428d6945d \
  colab_v2_dev_core_api python -m colab_core.app.storage_maintenance_cli \
  --apply-approved --plan /tmp/colab-u2-approval/u2-plan.json \
  --plan-sha256 3031054b040d75fd8e0f7192e94712010e9e50ce0cbeaec1b957d79931fc340c \
  --lab-id 0000000000000000000000000A \
  --account-id 00000000000000000000000AP1 \
  --environment dev --expected-bucket colab-platform-data-dev \
  --expected-region ap-northeast-2 \
  --expected-code-sha d56428d6945d677cae013d6bff25cb61727f3166 \
  --expected-image-config-id sha256:d14a7121b96fe2f95d7d0da284a77a7830d213a187592474875fa9a8db630003
```

환경값을 적어 넣는 것만으로 실제 이미지 확인이 되지는 않는다. 직전 `docker inspect colab_v2_dev_core_api --format '{{.Image}}'`와 `/opt/colab-v2/CURRENT_SHA`의 실측값을 비교·기록한다.

4. 기대 결과는 reclaimedUploads1/prunedCompletedTransfers7/reapedOpenTransfers0. 등록 원본과 B 자료 보존을 별도 read-only 재조회한다. 대상이나 plan이 달라지면 새 관측·새 승인을 받는다.

## 실패와 복구

- S3 삭제 실패 시 해당 업로드 D5 행은 남는다. 실패를 성공으로 세거나 더 넓은 목록으로 재시도하지 않는다.
- S3 원본 버전은 버저닝으로 남는다. 실행 후 생성된 **해당 exact key의 delete marker version ID만** 확인해 그 marker를 삭제하면 원본을 다시 노출할 수 있다. 복구 명령의 version ID를 추정하지 않는다.
- DB 복원은 실행 직전 봉인한 platform 백업을 별도의 일회용 tmpfs PostgreSQL에 먼저 복원해 대상 행을 대조한다. 운영 DB 전체 덮어쓰기는 승인 범위가 아니다.
- 직전 green30f5와 추가 f8 앱 rollback 이미지 보존은 데이터 복구를 대신하지 않는다. DB downgrade·옛 migrator 실행0.
