# 격리 로그인 E2E 독립 리뷰 — 2026-09-08

검토 대상은 이 격리 작업 사본의 scripts/e2e-login.py·e2e-login.sh와 gates/tools/_pg.sh 변경이다.
코드를 수정하거나 E2E를 재실행하지 않았다. 실제 로그인 통과와 stderr RED→GREEN은 메인 실행 증거다.

## 초기 발견 및 수용 조건

1. 고정 포트 8000/43173의 readiness가 HTTP 200만 확인하면 이미 실행 중인 다른 서버를
   신규 자식 프로세스의 bind 실패가 드러나기 전에 통과시킬 수 있다. 메인이 추가 예정인
   per-run backend 응답 header 검증이 필요하다. 브라우저 진입 URL을 통한 API 응답도
   같은 run을 가리키는지 확인해야 frontend의 잘못된 proxy 대상도 잡힌다.
2. 초기 코드의 browser close는 returncode를 무시하며 timeout도 경고만 한다.
   정상 PASS 출력 후 브라우저가 남아도 exit 0일 수 있다. 회수 실패는 실패로 보고하되
   app 종료와 임시 파일 회수는 끝까지 수행하는 수정이 필요하다.

## 확인한 경계

- shell wrapper가 _pg.sh로 새 이름의 일회용 PostgreSQL을 생성하고 fixture setup에 그
  컨테이너 이름만 전달한다. 기존 서버나 운영 URL 환경 파일을 source하지 않는다.
- Python 앱 환경은 좁은 allowlist로 새로 구성한다. 새 session secret·비밀번호와
  임시 credential 파일(0600), 임시 uploads를 사용한다. 비밀번호 입력은 browser batch stdin이다.
- temporary directory 안의 credential/uploads/log만 자동 제거된다. 원본 seed·subjects·frontend는
  읽기 입력이며 이 코드에 원본 삭제 명령은 없다.
- frontend HEAD 일치와 tracked diff 검사는 있으나 untracked 파일/ignored 의존성 동일성까지
  증명하는 것은 아니다. 따라서 해당 확인을 '완전 동일 트리'로 확대해서 설명하지 않는다.
- 정상 및 Python 예외 경로는 finally에서 browser session close, 직접 실행한 앱 프로세스
  terminate→timeout kill, log close, temporary directory cleanup 순서다.
  SIGTERM/SIGKILL 같은 외부 강제 중단까지 자동 회수 보장으로 말할 수는 없다.
- _pg.sh 변경은 exec의 stderr 리디렉션을 brace group으로 한정해 이후 셸 stderr를 복구한다.
  PostgreSQL 데이터·슬롯 판정 범위를 줄이는 변경이 아니다.
- DB fixture는 schema.sql에서 만든다. 이 로그인 E2E는 migration upgrade 검증을 대신하지 않는다.
- 로그인 invalid→valid→reload→logout만 판정한다. inspect-upload는 진입 조사이며 실제 업로드
  완료를 주장하지 않는 출력이 있다.

## 보완 재검토

실제 수정 파일을 다시 읽었다. backend health 및 frontend proxy `/api/v1/me`의
`X-CoLAB-E2E-Run`을 회차 값과 비교하고 불일치는 즉시 거부한다. 예상 비인증 401도 header를 확인한다.
초기 발견 1의 다른 backend 접속 위험은 보완됐다. frontend 자체의 프로세스 소유권 marker는
없으므로 같은 backend로 proxy하는 기존 frontend까지 암호학적으로 구분하는 검사는 아니다.
strictPort와 자식 생존 확인을 함께 사용하며, 현재 확인한 실제 실행 근거 범위를 넘어
모든 포트 경쟁을 완전히 배제했다고 보고하지 않는다.

browser close는 check=True와 timeout으로 실패를 보존하고, 오류를 미뤄 앱 프로세스 회수를
진행한 다음 예외를 낸다. PASS는 Python finally 뒤로 이동했다. 초기 발견 2는 보완됐다.
다만 PASS의 `cleanup completed` 시점은 TemporaryDirectory context 종료와 shell DB cleanup보다
앞이다. 전체 자원 회수 증거는 wrapper 종료 코드와 종료 후 컨테이너/프로세스 조회를 함께 쓴다.

Python SIGTERM을 KeyboardInterrupt로 바꿔 finally를 수행하고, shell EXIT trap이 살아 있는
Python 자식에게 TERM을 전달하고 wait한 뒤 DB를 회수한다. 정상 종료 코드는 보존한다.
SIGKILL 및 반복 강제 신호까지 회수 보장을 확대하지 않는 한 새 cleanup 방향은 타당하다.
이 신호 전달 버전은 본 리뷰에서 강제 중단 시험을 재실행하지 않았다.

두 요청 항목은 코드상 수용한다. 위 범위 제한을 반영하면 추가 차단 사항은 없다.
원격 CI·전체 제품 E2E 완료 판정은 이 리뷰 범위 밖이다.

## 실제 업로드 추가분 검토

`--upload`는 pipeline Python을 필수로 받고 같은 회차 임시 디렉터리에 실제 GeoTIFF를 생성한다.
worker의 DB·uploads·previews·event spool은 기존 일회용 DB와 회차 임시 경로를 가리킨다.
worker도 processes 목록에 포함되므로 기존 finally 종료 대상이다. 사용자가 별도 제공한
`--upload-file`은 읽기 입력이고 임시 디렉터리 밖 원천 파일을 삭제하지 않는다.

처리 후 다음 버튼 활성화를 기다리고, 설명 미입력 시 오류 표시를 확인한 뒤 설명을 채워 등록한다.
고유 session을 포함한 이름, 설명, EPSG:4326, 300x300, 파일명을 상세 새로고침 뒤 대조하므로
기존 seed 화면이나 단순 접수 성공만으로 PASS하는 구조는 아니다. worker 생존도 다시 확인한다.
지도 서비스/render 완료는 실행하지 않으며 출력에서 미검증을 명시하는 것이 정확하다.

**음성 범위 정정:** 빈 파일 거절은 Python fixture 사전검사의 size=0 거절이다.
실제 UI/서버에 빈 파일을 전달한 사용자 여정 E2E가 아니다. 실제 음성 E2E는 잘못된 로그인과
설명 없는 등록 시 오류 표시이며, 손상 파일 처리 실패 시나리오는 아직 별도다.

이 추가분에서 수용을 막는 오탐·원천 삭제 문제는 발견하지 못했다. 실제 `--upload` 결과는
메인의 실행 완료 로그로 판정해야 하며 이 독립 리뷰에서는 해당 E2E를 중복 실행하지 않았다.
