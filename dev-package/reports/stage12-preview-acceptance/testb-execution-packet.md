# TEST B 경계 수용 픽스처 실행 패킷 — 검토용, 미실행

## 고정 사실

- 대상은 dev의 기존 `B 연구실` (`0000000000000000000000000B`)뿐이다.
- 읽기 전용 실측에서 B의 계정·역할·유효 데이터셋은 각각 0건이다.
- 저장된 브라우저 자격은 `admin`, `colab`, `pi`뿐이며 모두 연구실 A다.
- core 이미지는 `colab-v2/core-api:dev-f8ac7ee07ff6`, 실행 image id는 `sha256:a02d4ab76ae97478ffe77fc5d35d8b7db769360f778419786d98dc389203bf04`였다.
- `CredentialStore.from_file`은 core 기동 시 한 번 읽는다. `set-password.py`는 rename하므로 바인드 마운트도 옛 inode를 본다. 새 자격 적용에는 core만 recreate해야 한다.

## 승인된 변경 상한

- 새 TEST 연구원 한 명: `d1_account` 1행, `d2_member_role` 1행, `d2_permission_switch` 4행.
- 기존 자격 JSON을 private snapshot한 뒤 새 이름 한 건만 추가한다. 기존 이름, subject, hash는 byte-for-byte 보존하고 최종 모드는 `0600`이다.
- 기존 286,683-byte NetCDF TEST 본체 한 건을 B 계정의 정상 제품 여정으로 등록한다.
- DDL, DELETE, 기존 계정 비밀번호 변경, 기존 사용자 데이터 변경, S3 삭제는 0이다.
- viz-render와 pipeline-worker는 재기동하지 않는다.

## 실행 변수

실행자는 private shell에서 lab/account/name/email/role 변수를 둔다. account ID는 저장소 `colab_core.kernel.ids.Ulid.generate()`로 새로 생성한다. 비밀번호는 파일·명령행·로그에 쓰지 않고 stdin으로 한 번 받는다.

## 실행 순서

1. 변경 전 계수를 owner/backup 경로로 고정한다. B의 계정 0, 역할 0, 스위치 0, 유효 데이터셋 0이어야 하며 다르면 중지한다.
2. 원격 실제 자격 파일을 같은 private 디렉터리에 timestamp snapshot하고 파일 hash, 모드, 기존 이름별 JSON 객체 hash를 비밀 출력 없이 메모리에서 고정한다.
3. owner DB 접속으로 기존 `services/core-api/ops/provision-account.sql`을 `account_id=<새 ULID>`, `lab_id=0000000000000000000000000B`, `name=TEST-stage12-labB-20260911`, `.invalid` email, `role=연구원` 변수와 `ON_ERROR_STOP=1`로 한 번 실행한다.
4. 새 ID에 정확히 account 1, role `연구원` 1, switches 4(`업로드·편집=true`, `프로젝트 생성=true`, `승인 위임=false`, `연구실 설정=false`)만 생겼는지 다시 읽는다.
5. `ops/set-password.py --file <실제 private credentials> --name TEST-stage12-labB-20260911 --account-id <새 ULID> --lab-id 0000000000000000000000000B`를 비밀번호 stdin으로 실행한다. `chmod 600`을 재확인한다. 이전 이름의 각 JSON 객체 hash가 snapshot과 같고 새 이름 하나만 추가됐는지 검사한다.
6. agent-bridge worker guard 뒤 실제 dev compose 파일과 env를 사용해 `docker compose ... up -d --no-deps --force-recreate core-api`만 수행한다. 서비스명은 compose config에서 읽고 추측하지 않는다.
7. `docker inspect`에서 core tag와 image id가 위 고정값인지 확인한다. viz/pipeline 컨테이너 ID와 시작 시각이 변경 전과 같아야 한다. 단일 dev doctor 15/0/0 뒤에만 계속한다.
8. 새 B 로그인 `/me`가 B lab과 새 account ID를 돌려주고 기존 A 로그인 `/me`도 200인지 대조한다.
9. 기존 286,683-byte NetCDF TEST fixture를 B에서 정상 UI/API 경로로 `initiate → S3 PUT → file complete → transfer complete → LST 선택/렌더 → POST /datasets` 수행한다. 이름은 `TEST Stage12 OtherLab Boundary 20260911`이다.
10. B subject에서 새 dataset ID의 detail/files가 각각 200, A admin에서 같은 두 요청이 각각 404인지 확인한다. 응답/HAR은 Authorization, Cookie, presigned query를 제거한 뒤 저장한다.

## 중지 조건과 보존

- 사전 계수가 다르거나 core가 고정 image id로 뜨지 않으면 즉시 중지한다.
- doctor가 15/0/0이 아니면 제품 여정을 시작하지 않는다.
- 생성 TEST 계정·자료는 유지한다. 별도 삭제 승인 없이는 정리하지 않는다.
- 결과에는 새 account ID, dataset ID, 200/404 네 상태, doctor 세 계수, viz/pipeline 시작 시각 불변만 기록한다. 암호와 자격 hash 본문은 출력하지 않는다.
