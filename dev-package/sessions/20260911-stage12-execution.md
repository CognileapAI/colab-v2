# Stage 1·2 승인된 실행

이 회차 종료 당시 실물 판정(후속 보류 해소 이전): U-2·IS4·I3·TL-2 완료, I4 미완료. Stage1 완료62/미완료0/보류1, Stage2 완료93/미완료1/보류2. 최신 상태는 `20260911-deferred-closeout.md`를 따른다. 아래 시각별 대기 기록은 당시 이력이다.

사용자 승인: “그래 전부 실행 승인해줄게, 개발 진행하라”. 이번 대화의 준비 패킷 A/B/C/D 실행과 필요한 개발을 승인했다. 보류3건은 제외한다. 비밀값은 출력하지 않는다.

실행 기준: 준비 패킷 `20260911-stage12-execution-preparation.md`. 원격 c329, 시험 시작 d564, dev d564. 사용자 수정은 원본에 보존하고 기존 격리 사본에서 기록한다. 제품 main 변경은 I3 같은 후보 시험 종료 전 하지 않는다.

| 단계 | 의존 | 상태 | 검증 |
|---|---|---|---|
| IS4 saved plan 적용 | hash/health/drift | 완료·대장 done 반영 | apply exit0·후속 no-change·health200 |
| TL-2 staging 최초 발행 | 승인된 URL/env/volume | 완료 | 실제 viz10001:999 읽기 |
| I3 실제5분 RED | 최초 장부·부모HEAD·dirty1 | 완료 | exit65·서버/DB/장부 불변 |
| I3 같은 후보 GREEN | RED 수용 | 완료 | c329 배포·8healthy·두 verify |
| TL-2 dev/staging hourly | 준비·배포 | 완료·대장 done 반영 | 실제 예약 발행·동일 staging 컨테이너 정기 소비 |
| U-2 백업·회수 | 기존 글로벌 계정·조건부 원본 재업로드 복구 | 완료 | 정확한1파일/7기록 회수·보존 |
| I4 IAM·자동점검·알람 | 글로벌 운영자/수신설정 | 차단: 현재 글로벌 계정의 IAM 권한 부족·수신 설정 미확인 | 단일15/0/0·실제cron·raise1/clear1 |
| 대장·문서 반영 | 실제 환경 확인 | 완료4건 반영·최종 gate 확인 | 관련 gate·독립 검토 |

사용자는 필요한 운영자·알람 설정이 글로벌에 있다고 알려줬다. WSL·Windows 글로벌 설정의 경로·프로필을 비밀값 노출 없이 확인했다. 발견된 운영자 설정도 uploader 계정을 가리킨다. 12:02:11UTC IAM GetRolePolicy는 AccessDenied(exit254)였고, 실제 알람 수신 설정은 확인되지 않았다.

IS4: 최초 명령의 hash 인자 오타는 형식 검사78로 적용 전 차단됐다. 승인된 정확한 hash로 실행한 별도 시도는 apply1회 exit0·후속 plan0·health200이다. 로그 hash는 `../reports/stage12-execution/results.json`. 같은 plan 재소비0.

dev hourly: 예약 설치11:37:31UTC, 기존 cron hash불변. 최초 수동 발행450/596·실제viz10001:999읽기 exit0. 실제 매시17분 회차는 아직 대기하며 수동 발행과 구분한다.

글로벌 보완 조사: `.config/colab-platform/dev-operator.env`는 AWS_PROFILE=colab-dev를 가리킨다. 별도 dev.env의 자격으로 STS를 조회해도 같은 uploader 사용자다. IAM/GetRolePolicy·S3 버전 조회 권한 부족은 여전하며, 비밀값은 출력하지 않았다. 글로벌 위치 질문은 이미 했으므로 반복하지 않는다. 자동 점검의 기존 13/2/0과 별도 운영자 점검 15/0/0은 합치지 않는다.

Staging 최초 장부133/133·viz10001:999 읽기 성공. 실제20:40:06KST cron이 dirty1·exit65로 fast-forward 전에 멈췄고 remote/image/container/DBhead/statehash/health 전후6묶음은 부모가 바이트 동일성을 확인했다. 그 증거를 조건부 GREEN 진행 기준으로 수용했다.

## U-2 복구 경로 보완과 실행 직전 검증

기존 글로벌 uploader 계정을 사용한다. 버전 삭제 권한을 얻은 것이 아니다. 같은 key의 현재 원본을 GetObject로 사전 백업하고, 필요하면 PutObject로 **새 최신 버전의 동일 내용**을 복구하는 대안이다. 원래 version ID를 복원하는 방법과 구분한다.

백업12599296B·SHA256 `62343291f2d8e21e3c194c5b86d0e513ea16661fdee7b957c304c6a990a8f0eb`, mode0600. 불일치 If-Match PUT은 PreconditionFailed(412)로 거절됐고, 전후 current version `zc8Ym1jp05uAkWiAJfLQuEVGr2Ywm8LY`·ETag·크기가 불변이다. 레포 uploader 정책의 Put/Get 권한 선언과 과거 실제 동일 버킷 PUT smoke도 함께 확인했다. IAM 정책 원격 조회를 성공했다고 주장하지 않는다. 현재 버킷 쓰기 권한 판단은 이 증거들을 결합한 것이다.

[공식 AWS 조건부 쓰기 규약](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html): 불일치 If-Match는 객체를 교체하지 않고, If-None-Match 별표는 현재 live 객체가 있으면 거절한다. 복구는 동일 key/body/content-type(application/x-hdf)/AES256과 `--if-none-match '*' --expected-bucket-owner 606175197146`로 고정한다. 경합412면 덮어쓰지 않는다. 복구 뒤 새 version ID와 GET size/hash를 대조한다.

실행 직전 DB 백업11:53:50UTC: platform111278B, AI5521B, 각각 S3 HEAD·다운로드 크기 일치. platform dump에서 삭제 대상 업로드1개와 완료 기록7개의 실제 COPY 행 존재8건을 확인했다. DB 기록 복구는 이 백업을 일회용 DB에 복원해 대상 행만 별도 검토하는 기존 절차이며 전체 운영 DB 덮어쓰기0이다. 파일 백업으로 DB 복구까지 보장했다고 하지 않는다.

11:55:20UTC 재관측 semantic3031054b 불변, A25/448/40·B1/2/1 보존값 동일. 실제 core image와 CURRENT_SHA 재확인. 독립 검토는 위 조건과 exact-key 복구를 전제로 실행을 수용했다.

U-2 실제 apply exit0: reclaimedUploads1/prunedCompletedTransfers7/reapedOpenTransfers0. 11:57:27UTC post관측 대상0·완료기록대상0·exactHEAD404, 보존A25/448/40·B1/2/1 일치. I3는 실제동일후보 GREEN과 후속8healthy/장부/표식/두verify로 수용했다. 대장은 U-2와 I3를 done으로 먼저 반영했다.

## 실행 증거와 복구 자료 보관

원문은 `reports/stage12-execution/results.json`의 `u2.private_evidence`에 파일별 경로·SHA256으로 연결했다. 추가 보호 사본은 `/home/ttlhi10/colab-v2-releases/stage12-execution-20260911`이며 디렉터리0700·파일0600, 14개 파일 복사 뒤 hash 일치를 확인했다. `manifest.json` SHA256은 `49582149a44ea4eb5217505c3c7b15f54eff555230da8e9ce6018a02f890532c`다. 이 폴더와 로컬 원문 백업을 Git에 추가하지 않는다.

복구가 필요할 때의 정확한 파일 복구 명령은 다음과 같다. **아직 복구를 실행한 것은 아니다.** 살아 있는 동일 key가 생겼으면 412로 멈추며, 아래 명령으로 다른 변경을 덮어쓰지 않는다.

```bash
aws --profile colab-dev --region ap-northeast-2 s3api put-object \
  --bucket colab-platform-data-dev \
  --key uploads/01M24KWBG3M37A0WYBX22VJ94P/01M24KWBG3MZGEBFGBGTST9BZJ \
  --body /home/ttlhi10/colab-v2-releases/stage12-execution-20260911/u2-original.bin \
  --content-type application/x-hdf --server-side-encryption AES256 \
  --if-none-match '*' --expected-bucket-owner 606175197146
```

이 명령은 새 version ID를 만든다. 반환된 version ID를 기록하고 GET한 파일의 크기12599296·SHA256 `62343291f2d8e21e3c194c5b86d0e513ea16661fdee7b957c304c6a990a8f0eb`를 대조해야 한다. DB 복구는 별도 백업의 대상8행을 검토하는 절차이며 운영 DB 전체 복원과 구분한다.

독립 advisor는 IS4·I3의 원문을 확인해 완료 수용했다. 이어 U-2 원문10개 hash·백업권한·1/7/0 적용 결과·보존 계수·사후0/HEAD404를 확인해 완료 수용했다. 조건부 PUT412는 부모 도구 출력에만 남아 있고 별도 원문 파일은 보존하지 않았다는 제한을 공개했다. 이를 실제 복구 시험 성공이라고 기록하지 않는다.

문서 검사 중 WORK-UNITS §11의 이전 I3/IS4 상태 표시2개가 남아 불일치2건이 발생했다. 대장에 맞춰 고친 뒤 관련3게이트는 3/0/0으로 통과했다. 기존 파서 검사 대상 밖9건과 비항목표2개는 이 통과의 근거가 아니다. TL-2 실제 회차 결과 반영 뒤 최종 문서 hash로 다시 검사한다.

Dev 실제 예약 발행은 12:17:04.090313UTC에 성공했다. 장부450/595, 내용 SHA256 `658e493d370ad521f9262cd7a289acff2b7ea7de8daddd65c8d94fed073497cb`. 실행 중인 viz의 기본 UID10001/GID999로 loader 성공과 같은 시각/hash를 확인했다. 기존 백업 cron·신규 publisher cron·wrapper hash 모두 설치 시점과 동일하다. 수동 발행과 구분되는 첫 실제 매시 회차 증거이며, staging의 실제3600초 소비 검증은 여전히 대기다.

Staging 실제 예약 발행은 12:17:05.398182UTC에 성공했다. 장부133/133, 내용 SHA256 `9f4c5a9d9e5e9ee5861c978f699598cdb9c6e20f5a17adb73a4325995d354394`. 실행 중인 viz10001:999의 loader가 같은 시각/count/hash로 성공했다. 부모는 발행 원문·consumer 원문·root crontab 실제 파일 hash `6957ae580c5954481f3df2d356e753cd75acc9ca4fcf26bcf677beae24fee6cf`를 별도로 대조했다.

## TL-2 실제 정기 회차 수용

같은 staging viz 컨테이너에서 기동 회차11:45:35.136UTC와 실제 정기 회차12:50:29.273UTC를 확인했다. 기본 간격3600초, 재시작0, 수동trigger0, 간격 변경0이다. 12:49:48UTC 관측에서는 벽시계 경과3856.065초와 monotonic 경과3566.302초가 약289.763초 달랐다. 21:45라는 최초 예상 시각은 벽시계 기준이었으며, 원래 실행기는 monotonic 기준이다. 시계 차이 원인을 suspend나 특정 고장으로 확정하지 않는다.

실제 정기 계수: preview158, 소유120/0/19/19, 구판14/2/3, 재굽기불가16, 타일주체758·타일146·unreachable0, 삭제0. 원문 두 회차 로그 SHA256 `01d6b8c3d74b60379d82c98e2c8b84637e69b45a09e3268855fd5bfa9fc26999`. 기존19벌/재굽기불가16벌 대조와 정기 분류를 수용한 것이며, 이 미리보기들의 삭제 처분 완료를 뜻하지 않는다.

staging lane의 [실행 보고서](../reports/stage12-execution/staging-evidence.md)는 부모가 lifecycle task와 gate를 검증하고 파일 SHA256 `02e8d17e91c6bb2bda4f7387ad2d8f496b4f273d9af298666376b2dfa1d23cf1`을 대조해 복사했다. 별도 advisor는 기존 구현·관련 시험과 이번 실제 회차를 결합해 TL-2 done을 수용했다. 그 뒤 대장을 먼저 갱신하고 반영 문서를 맞췄다.

staging의 장부 예약을 복구해야 하면 **현재 root crontab hash가 `6957ae580c5954481f3df2d356e753cd75acc9ca4fcf26bcf677beae24fee6cf`와 같은지 먼저 확인**한 뒤 다음의 보존된 root 예약을 복원한다. 이 명령은 아직 실행하지 않았다. 사용자 계정의 배포·백업 예약과는 다른 root crontab이다.

```bash
sudo crontab /opt/colab-v2/evidence/staging-hourly-20260911T2048/root-crontab.before
```

복원 뒤 빈 원본의 SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`와 대조한다. wrapper·로그·장부는 보존한다. dev 전용 cron과 I3 배포 복구 명령은 준비 패킷의 해당 절을 따른다.

## 요청과 결과 대조

- 충족: 사용자 수정 보존, 최신 원격·실제 서버 대조, 고정된 U-2 대상과 백업/복구 자료, IS4 적용 후 확인, I3 같은 후보의 실제 예약 RED→GREEN, TL-2 최초 장부→배포→실제 예약 발행·정기 소비, 완료4건의 대장 반영.
- 미달: I4 서버 자체 계정 단일15/0/0·자동 점검 cron·실제 알람 발생1/해제1. 필요한 IAM 조회가 AccessDenied이고 실제 수신 설정이 확인되지 않아 변경·전송하지 않았다. 수동15/0/0으로 대신 닫지 않는다.
- 범위 초과: 없음. 보류3건의 구현·처분은 하지 않았다. 기존 배포 파이프라인의 로컬 백업16건·이미지태그41건 보존 정책 정리는 별도 공개했으며, TL-2 미리보기 삭제로 세지 않는다.
- 제품 코드 변경이 없어 기존 d564 전체61/0/0은 재사용했다. 새로 바뀐 환경·대상은 실행 원문으로 검증했고, 최종 문서만 관련3게이트를 다시 확인한다. 원본 체크아웃에는 쓰지 않았고 main push도 하지 않았다.

산출물 이관 제한: staging lane의 자체 task·gate·파일 hash는 부모가 해당 격리 사본에서 verify-report로 검증했다. 다만 종료 hook은 event cwd를 부모 체크아웃으로 고정해 원본 task의 checkout과 다르게 비교하는 제한이 있었다. task.checkout을 바꿔 통과시키지 않았고, 부모는 검증한 파일을 복사·hash 대조한 뒤 부모의 최종 문서 gate로 다시 확인한다. 이 hook 제한을 서버 실행 실패나 검증 성공으로 바꿔 보고하지 않는다.
