# Stage 3 계정 기능 — WSL stage 배포

2026-09-12 KST. 사용자 승인: stage(WSL) 서버에만 검증용 배포.

- 주소: https://www.colab-hydro.com / 로컬 http://127.0.0.1:3000
- 배포 사본: /home/ttlhi10/colab-stage3-staging-deploy
- 브랜치: codex/stage3-staging-deploy
- 태그: b63c9e8a0d40-dirty. 미커밋 변경 41개를 기존 명시적 --allow-dirty 절차로 배포했다. 커밋·push 없음.
- 현재 stage 기반 b63c9e8의 최신 알림 개선을 보존하고 계정 입력 파일 37개를 기존 검증본과 바이트 대조했다. 추가 staging 배선 4파일 검증.

## 결과

배포 명령 exit 0. 필수 설정 21건 통과, 서비스 판정 15건 통과, 두 DB 체인 판정 2건 통과, 면제 0건. platform은 0025_stage3_accounts, ai는 0007_merge_vocab_and_category. 기존 PostgreSQL 컨테이너 ID 유지.

배포 전후 두 DB 백업 성공. 실제 stage 백업 사용자 postgres로 account_admin 신규 두 테이블 dump 가능함을 추가 확인했다. 기존 colab_backup role은 이 stage에 없으므로 신규 역할을 임의로 만들지 않았다.

계정용 연결 파일은 기존 DB와 동일한 대상이며 0600·uid 10001·읽기 전용 마운트. 새 bootstrap은 일회용 PostgreSQL에서 계정 생성과 실제 비밀번호 인증 성공을 검증한 후 적용했다. 실제 앱 컨테이너에서도 전용 colab_account_admin 연결 및 신규 두 테이블 조회 성공. 운영자 0건, DB 로그인 자격 0건: 기존 사용자 자동 승격 없음.

브라우저에서 신규 로그인 화면 확인. /api/v1/admin/account-options 및 /api/v1/me 비로그인 요청은 각각 401. 최초 확인 명령의 URL 누락(/api/v1) 및 psycopg용 URL scheme 변환 누락은 수정하여 다시 검증했으며 제품 실패로 오인하거나 최초 실행을 통과로 세지 않았다.

## 미완료와 복구

사용자에게 서비스 운영자로 지정할 기존 로그인 이메일을 질문했고 답변 대기 중이다. stage에서 운영자 로그인→발급→첫 비밀번호 변경 여정은 아직 미실행이다. 이전 격리 DB E2E 통과와 이번 stage 검증을 구분한다.

직전 b63c9e8a0d40 이미지가 보존돼 있다. 복구는 이전 앱 이미지로 수행하고 신규 schema·자격·접속 파일은 보존한다. 실제 롤백은 실행하지 않았다.

stage 자동 배포 감시는 기존대로 유지된다. 이후 origin/main에 새 커밋이 생기면 기존 배포 사본이 재배포하여 이번 미병합 계정 기능을 덮을 수 있다. AWS dev/prod에는 접근하거나 배포하지 않았다.

[배포 로그](deploy.log) · [배포 후 백업](post-backup.log) · [배포 전 이미지 신원](before.json)

## 후속 — 사용자 지정 운영자 등록

사용자가 ttlhi10@gmail.com을 서비스 운영자로 지정하고 임시 연구실 생성을 승인했다. 기존 stage DB 및 로그인 파일에 해당 이메일이 없음을 확인한 후 한 트랜잭션으로 임시 연구실·프로필·계정·연구원 역할·DB 자격·운영자 등기를 각 1건 생성했다. 기존 행 수정·삭제 없음.

- labId: 01M28J03BQE2DJ1YA1BJ0F676N
- accountId: 01M28J03BQX1V2RDB77YT98Q1V
- 로그인 API 201, /me의 임시 연구실 소속과 canManageServiceAccounts=true, mustChangePassword=true 확인.
- 초기 비밀번호 변경 전 계정관리 요청 403 확인. 사용자 자신의 비밀번호 변경은 사용자가 수행하도록 남겼다.
- 신규 계정 포함 두 DB 백업 exit 0. [백업 로그](operator-backup.log)
- 초기 비밀번호는 저장소 밖 소유자 전용 0600 전달 파일로 제공했고 보고서·로그에 기록하지 않았다.

## 후속 — 비밀번호 조건 안내

사용자 요청으로 초기 비밀번호·새 비밀번호 입력란에 10~512자, 문자 조합 필수 아님, 새 비밀번호는 초기 비밀번호와 달라야 함을 안내했다. aria-describedby로 안내를 입력란에 연결했다. 기존 정책·DB 변경 없음. 배포 사본의 TSX 2파일 수정, frontend 이미지 stage3-password-help-20260912만 교체(나머지 앱은 b63c9e8a0d40-dirty 유지). Docker build 내 typecheck·Vite build 통과, 실제 제공 JS 번들에서 두 안내 확인, 서비스 판정 15건 통과·면제0. 최초 재기동 직후 starting 판정은 정상 기동 후 다시 확인했다. 이전 frontend 이미지 보존.
