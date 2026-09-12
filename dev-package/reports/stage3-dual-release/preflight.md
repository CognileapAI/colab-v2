# Stage와 dev 배포 후보

사용자 2026-09-12 “st,dv다올려” 승인. 후속 답변: dev는 기능만 배포하고 기존 계정 유지; 운영자/연구실 생성 및 stage 비밀번호 복사 없음.

- 격리 로컬 후보 `fc45a9aa7c64`, main은 `b63c9e8a0d40`. 로컬 소스 고정 커밋만 만들었고 main 병합·원격 push 없음. 명시적 비-main 배포로 `ancestor=bypass`를 기록한다. 기존 doc/probe 검사15는 red로 남으며 이를 green으로 바꾸지 않는다.
- 이전 검증된 로그인 구현과 현재 stage 디자인을 합쳤다. frontend1253건 통과·type오류0·dbboundary390위반0·generated13일치·계약lint3위반0. 단일 실행5green/기수용contractred1/준비실패0. 계약 red는 기존 b63 대비 oneOf 요청 변경이며 후보 커밋 생성으로 해소됐다고 하지 않는다.
- dev 신규 변경은 compose 인증 DB 파일/mount와 bootstrap 위임이다. 서버 소스는 이전1111시험/14게이트 검증과 동일하다. arm64 image와 후보 core 소스66파일 byte hash가 일치한다.
- arm64 native core `80cbebba35d573cb53c6f00bb2811e94e23ba3dc1bd888ff15f6105f4f725c22`, migrator `005fcc03ba88cdc7f011fa6ceab63de90c48425e26330b6fc9e928e82dafc845`. WSL 교차 빌드는 exec format error로 실패했고 EC2 native build로 성공했다.
- dev 사전 doctor 단일15통과/실패0/미검사0. platform0024·ai0007, account_admin없음. master는 rds_superuser 구성원이며 colab_backup은 BYPASSRLS, statement logging none 확인.
- 두 dev DB 백업을 격리 복원 후 데이터38표(플랫폼버전표 제외32+ai6)의 원문행 hash 일치를 확인했다. DB별 정렬 locale 차이를 제거하기 위해 양쪽 모두 Python Unicode 정렬을 적용했다. 복원 DB에0025/26과 최소권한grant를 적용해 app의 세션표SELECT거절/auth롤SIU허용/DELETE거절 확인.
- 실제 arm64 API를 복원 DB에 연결해 운영자 발급201→첫로그인201→강제변경→변경200/원래sid·만료유지→옛token401→종료204/회수401/별도200을 검증했다. 해당 데이터는 격리 복원 DB에만 있고 dev 원본계정은 수정하지 않았다.
- dev 기존 웹134파일 백업, 새 웹96파일과 점검용 복구97파일을 hash로 고정했다. 복구는 같은 인증을 유지하는 기능 점검 화면이며 인증 코드 자체의 이전 버전 롤백이 아니다. ARM서버/마이그레이터 이미지 아카이브도 dev에 보관했다.

## 적용 순서

1. candidate git archive로 생성한 운영 소스/manifest를 독립 불변 경로에 설치·검증한다. core/migrator의 native build 입력 일치 증거를 확인해 후보 태그를 고정한다. 변경 없는 worker/viz/ai는42cff와후보소스diff0을 확인해 기존 image ID를 재사용하고 컨테이너는 유지한다.
2. 기존 dev.env·서명비밀·자격 파일·서비스 IDs를 보존한다. platform0025/26만 적용하고 dev전용 account-admin role과0600/uid10001 URL파일을 구성한다. 기존 계정·암호·소속·역할은 수정하지 않는다.
3. compose와기존env의이미지태그를후보로연결하고 core만 `up -d --no-deps --no-build`한다. 비-main 후보/정상 main의 차이를 CURRENT_SHA/MAIN_SHA와별도manifest에명시한다. 자동운영probe의source는실제후보commitarchive와일치시킨다.
4. core상태/S3/인증확인후새웹을index마지막으로배포한다. 기존무상태core/옛웹으로자동복귀하지않는다.
5. st현재core/source와designbundle이후보와같으면불필요한재생성없이확인한다. 두환경 실제로그인·회수·별도세션유지·계정관리권한거절·번들hash를검증한다. dev는기존테스트자격만사용하고새계정을만들지않는다.
6. dev최종doctor는全15항목실행하고main미반영red1을숨기지않는다. 기존데이터·자격파일·나머지서비스보존을확인한다. 양환경계정은독립임을보고한다.
