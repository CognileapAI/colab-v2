# 실패 업로드3건 exact 삭제·복구 패킷

사용자 2026-09-11 명시 삭제 승인. 이번 패킷은 과거의 「그대로 둔다」 결정을 바꾸며 Stage 보류 해소 기록을 따른다. 새 대상을 찾아 넓히는 정리 명령이 아니다.

대상은 staging `colab_v2_staging_pg/colab_platform/public.d5_upload`의 다음3개 ID다. dev에는 전수권한 읽기에서3ID가 없었다.

- `01M0Y1XND62XV5EKYZHFGNVJGS`
- `01M0YTT4VJKMGV2FXZZE12SEA4`
- `01M0YTT941XPYHH10RT3S2V9YY`

3건 모두 연구실 `00000000000000000000HYMETS`, 등록시각은 남아 있고 실패분류는 영구·형식 인식 실패다. 삭제는 부모행3개에만 걸며 기존 FK cascade로 업로드 파일6행·이벤트9행이 함께 제거된다. grid_profile0·early-preview transfer참조0. D3의 출처 열과 JSON payload에 해당3ID의 숨은 참조는 발견되지 않았다.

## 보존

정상 D3 dataset3/file6 및 설명·자동메타·변수 등 전체D3, 대상 외 D5, 물리파일6개를 보존한다. D5의 과거저장key6개는 이미 없다. **S3/로컬 객체 삭제 명령은 없다.** 두 D5/D3 계층의 파일 ID가 같지만 실제 저장key가 다르므로 storage maintenance나 dataset purge를 쓰지 않는다.

보호자료는 `/home/ttlhi10/colab-v2-releases/deferred-closeout-20260911`(dir0700/files0600)이다.

- `predelete-backup-proof.json`: 기존 staging 백업 실행기의 새 platform·AI 두 DB 백업과 hash. platform 백업34704B, AI5570B. 운영물리파일은 변경하지 않는다.
- `failed3-exact-rows.before.json`: 복구할3+6+9행 전체. SHA256 `ebe5dea3b728b18d36e6afa7b6d88f90114797908b1f7e151c3b9dc0501f037f`.
- `files.before.json`: 정상6파일 실제 크기/SHA256 및 실패key6개 부재.
- `delete-failed3.sql`: SHA256 `d230551e43e37a3d3cc5b781c50f74c1256663185553fa05c282cdf34ddecb87`.
- `restore-failed3.sql`: SHA256 `a0e1af1685e38cad1267b9f34b515efad841875d5db0cccd9acad07231e32092`.

## 정확한 실행

cwd는 `/tmp/colab-stage12-execution-prep`다. 기존 staging container·이미지·DB head, 파일봉인과 SQL hash를 재확인한 후 다음을 **1회만** 실행한다. 승인 재질문은 하지 않는다.

```bash
docker exec -i colab_v2_staging_pg psql -X -At -v ON_ERROR_STOP=1   -U postgres -d colab_platform   < /home/ttlhi10/colab-v2-releases/deferred-closeout-20260911/delete-failed3.sql
```

한 트랜잭션 안에서 exact18행 JSON일치·들어오는 FK집합·추가grid/transfer참조0을 확인한다. D3전테이블과 비대상D5 등14테이블의 count/hash를 전후 비교한다. 실패·변동·반환삭제수가3이 아니면 commit하지 않는다. 관련테이블 쓰기가 트랜잭션 동안 잠깐 기다릴 수 있으며 lock_timeout5초·statement_timeout30초다. 성공 후 exact대상0, D3정상6파일 hash/크기불변을 다시 확인한다.

## 복구

복구는 같은 DB에서 **지운18행만 다시 넣는다**. 운영 DB 전체 덮어쓰기·정상데이터셋 삭제·물리파일 변경은 없다. 아래 스크립트는 대상행이 생겼으면 충돌로 멈추고 overwrite/upsert하지 않는다.

```bash
docker exec -i colab_v2_staging_pg psql -X -At -v ON_ERROR_STOP=1   -U postgres -d colab_platform   < /home/ttlhi10/colab-v2-releases/deferred-closeout-20260911/restore-failed3.sql
```

upload3→file6→event9 순서로 복원한 뒤 exact JSON과 보존14테이블을 대조한다. 현재 이미지·스키마에서 검증한 절차이므로 이후 schema/대상변동이 있으면 재검토한다.

## 관련 시험

새 platform 전체백업을 network none·호스트포트0·tmpfs의 일회용 PostgreSQL에 복원했다. 변경된target차단·정상삭제3/6/9·반복실행차단·exact18행복구의4경우가 통과했고 각 변경에서 보존14테이블 불변을 확인했다. 초기 시험준비에서 허용되지 않는 failure_reason 문자열은 기존 CHECK로 거절됐으며, 제약을 바꾸지 않고 허용된 failed_at시각 변동으로 음성 시험을 구성했다. 실제서비스DB 쓰기는 이 리허설에서0이다.

## 집행 결과

2026-09-11 보류 해소: 실패 업로드3건 실제 삭제·정상 파일6개 보존. BF-10·PA-G는 단계 미정 backlog/open으로 이동(미구현, 자동 착수 없음). Stage1 완료62/미완료0/보류0, Stage2 완료94/미완료1(I4)/보류0, 백로그2건. 근거 `sessions/20260911-deferred-closeout.md`, `reports/deferred-closeout/results.json`.
직전 추가 백업 해시는 `results.json.final_backup`, 실제 적용 종료0·COMMIT과 보존 결과는 `results.json.apply/postcheck`에 기록했다. 삭제 SQL은 봉인한 동일 해시로 한 번 실행했다.
