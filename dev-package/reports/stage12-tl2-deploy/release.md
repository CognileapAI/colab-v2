# Stage 1·2 — d564 구현·배포·최종 확인

**Stage1 완료61 / 잔여1 / 유예1, Stage2 완료90 / 잔여4 / 유예2.** 전체 종료는 아직 아니다. 이번 후속은 TL-2 자동 관측 연결을 구현하고 dev 실제 동작까지 확인한 것이다. 매시간 발행과 staging 정기 주기 확인은 남아 있어 TL-2는 partial이다.

## 코드와 시험

- 제품 SHA `d56428d6945d677cae013d6bff25cb61727f3166`, tree `2dec4313a6bcb083ca5158d2b5c2f279be8f1303`. [PR #19](https://github.com/CognileapAI/colab-v2/pull/19) 동일 SHA로 main 반영.
- 같은 SHA push CI `34586815017` 및 PR CI `34584997636` success. 경로 조건으로 미실행인 잡은 실행 통과로 세지 않는다.
- 최종 제품 `all -j4`, 내부4: **단일 실행61/0/0**, wall1215.46초. core1074 / ai138 / viz444 / pipeline275, skip0, deselect6/26/42/50, failed0.
- task `fdd8c5c8bf2e48099ef1b73eb5358468`를 실행에 전달했고 부모가 정본61개를 각각 명시해 task identity·원본 report·현재 파일을 직접 검증했다. 복사본 [all-summary.json](all-summary.json), [all-facts.json](all-facts.json)은 원문과 동일 바이트이며, 검증 명령은 원래 실행 사본에서 수행했다.
- 원본194개는 `.codex/artifacts/stage12-tl2-deploy/gates-d564.tar.gz`와 [현재 원본 manifest](gates-d564-manifest.json)에 보존. archive SHA256 `1a4d38c3d888213f555d155cf8dcfe10202dca12a843e74e753abbe5617ed86c`. 검사할 때까지 각 원본 hash 불변을 확인했다.
- 최초 bbc8 실행은 최종 통합 SHA로 맞추기 위해 약30초에 중단했다. 그 부분 실행을 성공으로 세거나 d564로 소급하지 않는다. 별도 원본 `/tmp/colab-stage12-tl2-bbc8-interrupted` 보존.
- harness 모델20과제는 명시적 면제이며 실제 Astra 평가가 아니다. 기존 G10 전후30f5 두 실행은 이전 수용 근거로 보존한다.

## 실제 배포

- ARM64 5개 이미지 tar 298709504B, SHA256 `26d8cfcf4a667536d5a00dfc1f5c07eb2f85c54903d76f883481840fa81875bf`.
- ops archive 232969B, SHA256 `4b651621f3553f374f946f75010ddd44f5e4ee12c71c6bdb4b1280380daf7c31`; manifest `072abe72b5070dc5403a780f4806d3d02b3eab8a85a4e0b120f360e5044328aa`. ship의 source136개 확인·이미지 반입 exit0.
- doctor archive SHA256 `150498d1eb6fb61b4d078f56baa660f9cfa239dfec4923a02654237b759b97eb`와 실행 파일/새 publisher runner hash를 확인한 뒤 설치했다.
- 새 백업 `2026-09-11T095249Z`, platform111275B / AI5519B. 양쪽 S3 실제 HEAD 크기 일치, backup exit0.
- 최초 장부 발행과 실제 viz 사용자 읽기를 확인한 뒤 migration/up exit0. 최종 postflight에서 4서비스 healthy·restart0, 실제 image config와 CURRENT_SHA를 대조했다. [postflight.json](postflight.json).
- core config `sha256:d14a7121b96fe2f95d7d0da284a77a7830d213a187592474875fa9a8db630003`, viz config `sha256:e4baad23d9243262c8ee47abb0905b733361982d69832a2b7f8b719dbb9d1640`.
- 공개 index HTTP200/SHA256 `091bfb83b02cfdc07622701c27e22a189bd66f2ab60285ed85b6848bd074870b`. frontend30f5→d564 변경0. 30f5에서 이미 수용된 사용자 여정을 새 전체 UI 실행으로 바꾸어 보고하지 않는다.
- 직전 green30f5 및 이전 f8 rollback 이미지 보존. DB downgrade0. 운영 cron 기존 hash 불변, 신규 ops/publisher cron 미설치.

## 실제 TL-2 결과

09:59:55.288599 UTC 전수 장부를 발행했다. D3 파일450개, D5 파일596개, 내용 SHA256 `97daa5e994047f71ed64ac05f825cca190c8f3a69045067398e41f6c99c961d3`. root:999 디렉터리0550·파일0440을 실제 viz 사용자10001/GID999가 읽고 검증했다.

서비스 기동 후 기존 자동 순회 로그에서 **174벌 = 살아 있음116 / 접수만42 / 고아16 / 판정 불가0**를 확인했다. 구판 세 등급은 각각0, 재굽기 불가0, 삭제0. 이 결과는 dev의 현재 S3 집합이며, 이전 staging 구판19벌=14+2+3과 다른 모집단이다.

이 로그는 **기동 후 자동 순회**이다. 기본3600초를 기다린 다음 주기나 실제 hourly publisher 설치로 바꾸어 세지 않는다. staging 배포와 한 정기 주기를 확인하기 전 TL-2를 done으로 올리지 않는다.

## 발견한 입력 차이와 보완

기존 dev 백업 URL은 libpq용 `postgresql://`였다. 설치된 SQLAlchemy 드라이버는 psycopg이고 psycopg2는 없어, 새 이미지에서 해당 기본 URL로 engine을 만들면 ModuleNotFoundError가 발생했다. 연결을 열지 않는 실제 이미지 시험으로 확인했다.

기존 파일을 수정하지 않고 선두만 `postgresql+psycopg://`로 바꾼 `/etc/colab/ownership-platform-db.url`을 root:root0600으로 원자 준비했다. 나머지 바이트는 보존했고 값은 출력하지 않았다. 최초 발행이 이 실제 파일로 성공했다. 주기 runner도 같은 파일을 사용해야 하며 기존 DB 자격증명 회전 때 함께 갱신해야 한다. 새 DB 역할·권한 부여, 앱 인증 파일 변경, 장기 AWS 키 설치는 없다.

초기화 wrapper의 마지막 완료 표식은 로그에 없었다. up 자체의 exit0·건강 상태 외에, 뒤따른 별도 postflight에서 실제 cron hash·image·CURRENT_SHA·snapshot을 다시 검사했다. 실행되지 않은 마지막 표식을 검증 근거로 삼지 않는다. 초기화 실패 시 보호된 env 백업을 지우고 무조건 재시도하지 않는다.

## 건강검사를 혼합하지 않는다

| 검사 | 실제 결과 |
|---|---|
| 기존 승인된 일회용 운영자 진단 | 단일15/0/0·exit0. [원문](dev-doctor-d564.txt). 기존 로컬 자격증명은 메모리/SSH stdin/일회용 진단 컨테이너만 사용. |
| IMDS 자동 deploy probe | 단일13/2/0·exit1. 공개 web HEAD/List403. [원문](automatic-doctor-d564.txt). 운영자 성공으로 대신하지 않는다. |
| resident service-health | exit0, 4개 unit 일치 |
| resident backup-freshness | exit0 |

## 잔여와 실제 실행 경계

1. **U-2**: [d564 재봉인한 삭제 패킷](u2-apply-packet.md). 12,599,296B 객체1개와 완료 메타7개. 새 읽기 전용 관측에서도 semantic3031054b 불변, B 대상0, 실제 삭제0. 실제 apply 직전에는 다시 새 백업을 만든다.
2. **IS4**: 기존 저장 계획 `6e752d0d…` 단일 apply와 최종 no-change 확인. [패킷](../../sessions/20260911-is4-approval-packet.md). 아직 apply0.
3. **I3**: 최신 문서 main 후보를 별도 봉인한 뒤 실제5분 cron RED→GREEN staging 배포. [실행 절차](../../sessions/20260911-i3-i4-approval-packet.md). 기존 운영 서빙은09e2, 아직 cron설치0.
4. **I4**: 최소 IAM 읽기 정책을 적용할 실제 운영자·승인, 자동 probe15/0/0, cron과 외부 알람2건 수신. 운영자 프로필과 수신 채널 입력 대기.
5. **TL-2**: 최초/매시간 발행 명령의 URL 파일을 위 전용 파일로 사용. dev 및 staging publisher 주기 설치, staging에서 새 장부를 소비한 정기 한 바퀴 실측. 현재 cron0·실제 삭제0.

유예는 격자선·눈금, Google 로그인, 실패 업로드3건 처분으로 총3건이다.

## 문서 후속의 검증 경계

이 보고서 뒤 문서만 main에 추가되어도 dev 제품 실행 SHA는 d564다. d564 제품 전체61/0/0, 문서 전용 게이트, 문서 HEAD와 d564의 **제품 내용 동일성**을 별도로 기록한다. 문서 HEAD에서 전체61개를 새로 실행했다고 하지 않는다. I3의 실제 배포 후보 SHA는 문서 main 최종값으로 별도 고정해야 하며 기존30f5 패킷으로 승인받지 않는다.

## 배포 후 인증 회귀

실제 d564 dev 화면에서 로그인201 → 새로고침 /me200 → 로그아웃204·/me401 → 재로그인201 → 새로고침 /me200을 확인했다. [실제 UI 관측](../stage12-auth-regression-d564/auth-smoke.json), [세션 기록](../../sessions/20260911-stage12-auth-regression-d564.md). 인증 셸 표시 중 주소가 /login에 남은 점은 별도 관측이며 라우팅 성공으로 확대하지 않는다. 비밀번호·계정·데이터·서비스 변경0. 부모가 별도 작업 사본의 원본 보고서를 task23a2a48d 기준 직접 검증했다.

TL-2 테스트 서버의 기존 전수 읽기 역할, psycopg URL 준비, 최초 발행과 정기 실행 순서는 [구체적 실행 패킷](../stage12-tl2-staging-packet/staging-execution-packet.md)에 기록했다. 실제 staging 변경은 아직0이다.
