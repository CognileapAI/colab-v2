# I3·TL-2 staging 실행 증거

관측 시각은 2026-09-11 20:38~20:49 KST다. 후보는
`c329c32d2f6d469deb12d64f6cb89e60994b1d3d`, 자동 배포 시험 사본의 시작점은
`d56428d6945d677cae013d6bff25cb61727f3166`, 직전 서빙 버전은 `09e2b9b2db1a`였다.
실행 직전, RED 뒤, GREEN 뒤 `origin/main`은 같은 후보 SHA였다.

## 최초 ownership 장부

- staging env를 실행 전 private 증거 디렉터리에 mode 0600으로 보존했다.
- ownership 설정은 UID 0, GID 999, max-age 7200을 각각 정확히 한 번 기록했다.
- 보호된 DB URL 파일은 root:root 0600이며 URL 값은 출력하지 않았다.
- 서버에 운영 runner 상위 디렉터리가 없음을 확인하고 root:root 0755로 새로 만들었다. publisher
  SHA-256은 `7b18396555d252a1ed372989ed0a1aad2efce16c39e00da4c4ea7075f4af0dcd`다.
- 새 `colab-v2-staging_ownership-ledger` volume의 최초 발행은 D3 파일 133건, D5 업로드 파일
  133건, content SHA-256 `8d16e35901f1984216d6de7c036b9f7d34b3251bc59656b60127e38cc18efd6f`다.
- volume은 디렉터리 0:999/0550, `current.json`은 0:999/0440이다. 후보 viz 이미지의 실제 기본
  사용자 10001:999로 max-age 7200 loader가 `snapshot_consumer_read_green`을 냈다.

## 실제 5분 RED

- 설치 전 crontab SHA-256은
  `d554b72cb92947d038b9495577fe5fcdfe0adbf90026f2b724cdb9f7da25dbd4`이고 블록 밖 비공백
  36줄을 보존했다. 설치 후 SHA-256은
  `1c9488903a3c37a98704a2c00990a9cc64c07e6ebd206d401a1e6da11ecf153a`다.
- 시험 사본은 d564 HEAD에 빈 `TEST-I3-DIRTY-RED` 한 건만 더러운 상태로 유지했다.
- 20:40:04 실제 cron이 fetch했고, 20:40:06 `워킹트리 변경 1건`으로 fast-forward 전에 exit 65를
  냈다. 실패 표식이 같은 시각 생성됐다.
- RED 전후 public health 200, 원격 SHA, 실행 중인 8개 컨테이너 이미지·상태, 두 migration head,
  release ledger, image digest ledger, `LAST-SUCCESS.txt`가 byte 단위로 같았다.

## 같은 후보 GREEN

- 부모 검토 뒤 시험 marker 하나를 20:42:06에 제거했다. 20:45 실제 cron은 같은 후보 c329를
  fast-forward하고 배포했다.
- 배포 판정은 15/0/0, migration 체인은 2/0/0, 컨테이너는 8/8 healthy, public health는 200이다.
  platform head는 `0024_s2_grid_convenience`, AI head는 `0007_merge_vocab_and_category`다.
- 실패 표식은 없어졌고 `LAST-SUCCESS.txt`는 20:45:51에 갱신됐다. release ledger와 실제 앱 태그도
  c329다. rollback용 `09e2b9b2db1a`, `a8541b7c3c33` 이미지는 각각 6/6 남아 있다.
- 파이프라인의 정상 보존 정책으로 오래된 로컬 SQL dump와 보존 집합 밖 로컬 이미지 태그가
  정리됐다. DB·S3·미리보기 cache 삭제로 계수하지 않는다. d564 배포 tar 3개는 남아 있다.

## 매시간 발행

- staging root crontab은 설치 전 비어 있었고 실행 전 snapshot을 보존했다. 매시 17분 publisher
  블록 하나를 설치했으며 wrapper는 root:root 0700, SHA-256
  `7bef9ad3b9770ed58f1252119df1cb6b4daf263c84bb57f5daf0224f6c783d5e`다.
- 최초 실제 예약 발행은 21:17:05 KST에 성공했다. D3/D5 건수는 133/133, 새 content SHA-256은
  `9f4c5a9d9e5e9ee5861c978f699598cdb9c6e20f5a17adb73a4325995d354394`다. 실행 중인 viz
  사용자 10001:999가 같은 시각·건수·hash의 장부를 loader로 읽었다. public health는 200이고
  wrapper와 root crontab hash는 설치 직후 값과 같다.
- 후보 서비스의 첫 3600초 정기 분류 판정은 기동 시각 기준 약 21:45 KST다. 기동 직후 결과를
  정기 결과로 세지 않고 실제 두 번째 회차를 계속 관측했다.
- private 원문은 `$HOME/colab-v2-releases/i3-tl2-red-20260911T2100KST/`에 mode 0600으로 보존했다.

## 실제 3600초 정기 분류

- 같은 viz 컨테이너 ID·이미지 ID·시작 시각 `2026-09-11T11:45:32.440781605Z`가 재시작 0,
  healthy 상태로 유지됐다. 실제 설정은 trigger poll 5초, reclaim 3600초, apply false, 상한 20이다.
- 기동 직후 첫 회차는 `11:45:35.136Z`였고, 정기 회차는 `12:50:29.273Z`였다. 벽시계 경과와
  컨테이너가 사용하는 monotonic 경과가 12:49:48 관측에서 각각 3856.065초, 3566.302초로
  289.763초 달랐다. suspend나 시계 보정은 확인되지 않았으므로 원인으로 단정하지 않는다.
- 실제 정기 회차는 preview 158벌, ownership `120/0/19/19`, legacy `14/2/3`, 재굽기 불가
  16벌, 삭제 0건을 기록했다. 타일은 주체 758, 146벌 중 도달 146·미도달 0,
  관측 전용 0파일 삭제다.
- 정기 회차가 읽은 장부는 21:17 예약 발행본과 같은 시각, 133/133건, content SHA-256
  `9f4c5a9d9e5e9ee5861c978f699598cdb9c6e20f5a17adb73a4325995d354394`다. 뒤 health는 200,
  배포 실패 표식은 없고 root/user crontab hash는 각각 설치 직후 값과 같다.

## 정기 발행 중단·복구 자료

- root crontab 설치 전 snapshot은 root-owned evidence 디렉터리의 `root-crontab.before`이고
  빈 crontab SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`다.
- 중단이 필요하면 현재 root crontab SHA-256이
  `6957ae580c5954481f3df2d356e753cd75acc9ca4fcf26bcf677beae24fee6cf`와 같은 경우에만
  `sudo crontab "$ROOT_CRON_SNAPSHOT"`으로 위 snapshot을 복원한다. 복원 뒤 빈 hash를 대조하고
  사용자 crontab의 자동 배포·백업 블록은 손대지 않는다. wrapper와 로그·장부는 증거로 보존한다.
