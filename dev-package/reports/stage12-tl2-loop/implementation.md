# TL-2 정기 관측 결선

## 동작

기존 `TriggerDrainLoop`의 tile 회수 due pass 안에서 TL-2 구판 분류도 함께 돈다. 로컬 staging은
`ownership.scan`, S3 dev는 `legacy_preview_observation.observe`를 쓰며 네 소유 등급과 세 구판
등급, 재굽기 불가 수, 삭제 0건을 정본 이름으로 로그한다. 이 결과는 회수 계획에 전달되지 않는다.
지도 타일의 기존 상한 20과 로컬 apply 동작, S3 삭제 문 0은 그대로다.

D7은 DB에 연결하지 않는다. `ownership_snapshot_publisher`가 D3/D5 소유 모듈의 읽기 함수를
통해 한 `REPEATABLE READ READ ONLY` 트랜잭션을 열고 첫 DB clock을 snapshot 시작 시각으로 고정한 뒤 전수 ID를 읽는다. 현재 DB role의
`rolsuper`, `rolbypassrls`, `pg_read_all_data`를 실제 조회하며 전수 권한이 아니면 발행하지 않는다.
출력은 mode 0600 임시 파일을 fsync한 뒤 rename한다. 일반 로그에는 ID와 DB URL을 싣지 않는다.

소비자는 매 due pass마다 snapshot을 새로 연다. 일반 파일·publisher 소유·consumer 그룹·0440·부모 디렉터리 0550·64MiB 상한과 O_NOFOLLOW/fstat identity,
내부 schema v1, all-tenants scope, 권한 근거, timezone 시각, 미래 5분 제한, max-age, ULID,
중복, 비어 있지 않은 전수 집합, 배열별 count와 canonical content SHA를 전부 검증한다. SHA는
손상 검출값이며 발행자 신뢰를 대신하지 않는다. 하나라도 틀리면 `TL-2 ... red(준비)`만 남기고
0건으로 접지 않으며 다음 주기에 다시 읽는다.

## staging 실행 패킷 — 아직 실행하지 않음

1. 실행 이미지에서 publisher UID와 viz GID를 실제 `id -u/-g`로 읽는다. publisher는 root one-shot이므로 owner UID 0, viz의 실제 GID는 `VIZ_GID`로 설정한다. 숫자를 추정하지 않는다.
2. `ownership-ledger` volume을 먼저 만들고 `volume-init`으로 디렉터리를 `root:VIZ_GID` mode 0550으로 맞춘다.
3. viz-render에는 `/srv/ownership-ledger:ro`, producer 일회성 컨테이너에만 같은 volume을 rw로 준다.
4. 배포 전 최초 publisher를 먼저 성공시킨 뒤 viz-render를 기동한다. 순서가 바뀌면 첫 관측은 준비 red다.
5. 운영 호스트에는 검토 후 `infra/staging/tools/publish-ownership-snapshot.sh`를 `/opt/colab-v2/publish-ownership-snapshot.sh`로 설치하고, 스케줄러는 3600초마다 그 고정 경로를 실행한다. 소비자 max-age는 7200초다. 두 번 연속
   발행 실패하면 snapshot이 stale이 되어 다음 TL-2 관측이 준비 red로 닫힌다.
6. publisher 명령의 이미지 태그는 배포 SHA와 고정하고, backup DB URL 파일은 컨테이너에 ro로만
   마운트한다. URL 값, ID 배열, 서명 URL은 표준 출력에 나오지 않는다.

```sh
# staging 최초 발행과 매시간 같은 명령. network는 compose project의 실제 default network다.
COLAB_OWNERSHIP_COMPOSE_PROJECT=colab-v2-staging \
COLAB_OWNERSHIP_CORE_IMAGE="colab-v2/core-api:$COLAB_RELEASE_TAG" \
COLAB_OWNERSHIP_DB_URL_FILE="$COLAB_STAGING_BACKUP_DB_URL_FILE" \
COLAB_OWNERSHIP_VIZ_GID="$VIZ_GID" \
infra/staging/tools/publish-ownership-snapshot.sh

# dev는 project/image/backup URL만 dev 값으로 바꾼다.
COLAB_OWNERSHIP_COMPOSE_PROJECT=colab-v2-dev \
COLAB_OWNERSHIP_CORE_IMAGE="colab-v2/core-api:$COLAB_IMAGE_TAG" \
COLAB_OWNERSHIP_DB_URL_FILE=/etc/colab/backup-platform-db.url \
COLAB_OWNERSHIP_VIZ_GID="$VIZ_GID" \
infra/staging/tools/publish-ownership-snapshot.sh
```

실제 timer/cron 설치, staging 배포, DB 쓰기, S3 삭제는 이 브랜치에서 0건이다. staging에서
publisher 성공 후 viz-render 로그 한 주기와 snapshot 시각·count·hash를 함께 회수해야 TL-2 완료
정의 ⑤를 판정할 수 있다.

## 검증 이력

- viz RED: 신규 snapshot 모듈 부재와 due job 인자 부재를 확인했다.
- viz GREEN: 관련 44/44, 정식 `service-tests-viz-render` 443/443 통과.
- core 첫 전체: 1071 통과, D5 표 직접 접근 경계 1 실패. SQL을 D5 소유 adapter로 옮겼다.
- core 두 번째 전체: 843 통과, DB-heavy 229 실패. 환경 실패가 아니었다. 문자열 치환이 기존
  `_ADOPT_GRID_PROFILE` 정의를 잘못 바꿔 등록 경로가 500을 낸 제품 회귀였고, 별도 일회용 DB에서
  대표 실패 1건을 재현했다. 기존 상수 이름과 UPDATE SQL을 원문대로 복구했다.
- 복구 뒤 소유 일회용 PostgreSQL에서 core 전체 1074/1074가 통과했다. 실제 DB 시험은 두 연구실
  전수 ID·독립 count 대조, `transaction_read_only=on`, 쓰기 거절, app role 권한 부족 거절을 포함한다.
