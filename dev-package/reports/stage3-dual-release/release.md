# Stage·dev 기능 배포 — 2026-09-12

사용자 “st, dv 다 올려” 및 “기능만 배포하고 dev 계정은 유지” 승인에 따라 완료했다. 로컬 후보 `fc45a9aa7c64`, main `b63c9e8a0d40`; main 병합·push 없음.

## 적용 결과

- Stage https://www.colab-hydro.com/: 현재 API 소스66파일과 화면 번들이 후보와 같아서 기존 컨테이너를 유지하고 재검증했다. 로그인 hardening API와 현재 디자인이 함께 동작한다. 자동배포 watcher hold 유지.
- Dev https://d31zgpff2091oh.cloudfront.net/: platform0024→0026, 인증 전용 DB 역할과 URL 파일0600/uid10001, core API ARM 이미지 교체, 웹95파일 배포(index 마지막, source map 제외). 저장모드S3·IMDS 유지.
- dev 기존 계정5·연구실2 유지. 원래 platform32표와 ai6표의 모든 행 hash가 일치한다(변경 대상 platform 버전표 제외). 로그인 자격·운영자 신규 행0, 기존 subjects/credentials 파일 hash 동일. dev.env는 이미지태그 외 원문 동일. worker/viz/ai의 기존 컨테이너 ID 동일.
- dev 전용 DB 접속 역할 생성은 서비스 운영자 계정 생성이 아니다. 일반 앱의 세션표 SELECT 거절, 인증 역할 SELECT/INSERT/UPDATE 허용·DELETE 거절 확인.

## 검증

- 후보 gate 단일 실행: frontend1253시험 통과, type오류0, DB경계390위반0, generated13일치, 계약lint3위반0. 5 green/기수용 contract red1/준비 실패0. 공식 verifier도 gate failures remain으로 종료1. 계약의 기존 b63 대비 POST /sessions oneOf 변경을 새 커밋으로 숨기지 않았다.
- dev doctor 실제15항목: 14 green/실패1/미검사0. 실패는 선언한 non-main 후보(`ancestor=bypass`); 기능 오류와 구분한다. RLS42표, DB양체인head, 전체서비스와S3·라우팅 정상.
- 실제 ARM 서버+dev 복원 DB: 발급→첫 변경→동일sid/만료→옛 토큰 거절→세션 종료 및 별도 세션 유지 통과. 이 발급 시험은 격리 복원 DB에서만 수행했다.
- 양환경 실제 HTTPS API: 로그인201, me200, 비운영자403, 로그아웃204, 종료 토큰401, 별도 세션200.
- agent-browser 실제 입력·클릭: 양환경 비밀번호 로그인, 새로고침 유지, 두 탭 세션 공유, 로그아웃 후 두 탭 로그인 화면, 옛 토큰401. 테스트 세션 종료. 사용자 본인 비밀번호 변경0.
- 두 HTTPS 배포가 같은 `index-YdOxNYzp.js`를 제공하며 SHA256 `8d65f49f470b20f6f27e2291bdc095e19c3c3040eab9c94d104d8cce1c0d7938`이 로컬 후보와 일치.
- 게이트 후 제품 코드 수정0. 이후 대장과 본 보고서만 갱신했으므로 기존 전체트리 snapshot을 문서 갱신 후 트리까지 검증한 값으로 부르지 않는다.

## 실행 중 조정

RDS에서 ALTER ROLE NOSUPERUSER는 실제 superuser만 허용되어 첫 역할 적용 트랜잭션이 rollback됐다. 독립 검토 후 해당 ALTER문의 NOSUPERUSER만 제외했다. CREATE NOSUPERUSER와 최종 속성 검증은 동일 트랜잭션에 유지했다. 다음 시도는 master URL의 기본 DB(postgres)를 사용해 schema 부재로 rollback됐고, colab_platform을 명시한 뒤 성공했다. 원본·실행 SQL 템플릿 hash와 정확한 차이는 rds-role-adaptation.json에 있다. 원본 bootstrap SQL의 RDS ALTER 구문 호환성은 별도 재사용 전 개선이 필요한 제한이며 이번 적용은 기록한 조정본이다.

초기 API 검증의 GET /admin/accounts는 실제 제공되지 않는 메서드여서405를 받았다. 실제 조회계약 GET /admin/account-options로 수정해403을 검증했다. Stage의 Python 기본 User-Agent 요청은 edge403이었고 브라우저와 명시 User-Agent의 HTTPS 요청으로 재검증했다. 웹 사전검사에서 source map1개를 발견해 공개 배포본에서 제외한 뒤95파일 업로드 성공했다.

## 의도 대조와 복구

이번 승인 범위(st·dv 기능 배포, dev 계정 유지)의 미달0·초과0. 기존 로그인 intent8정책의 구현·장애·경합 검증은 ../stage3-login-hardening/final/release.md의 항목별 근거를 이어받고, 같은 서버66파일과 새 디자인 통합후1253시험 및 본 배포 실측으로 연결했다. 모든 장애 주입이나 실제12시간 대기를 dev에서 새로 수행했다고 주장하지 않는다.

원본DB 두 벌·기존웹134파일·기존env/compose/metadata·호환ARM이미지·점검웹97파일을 보호된 릴리스 저장소에 보관했다. 원격 /opt/colab-v2/stage3-dual-20260912, WSL /home/ttlhi10/colab-v2-releases/stage3-dual-20260912 및 stage 기존 보호 릴리스 디렉터리. 복구는 같은 인증을 유지하는 점검 화면이며 옛 무상태 인증/DB downgrade로 돌아가지 않는다. main 미반영 red와 기수용 계약 red는 서로 다른 실패이고 전체 green이 아니다.

최종 정리: WSL 복원 DB·EC2 시험 API·역방향 터널15433·시험 브라우저 종료 및 임시 자격파일 삭제 확인. 영구 백업 경로의 DB/웹 파일 존재 확인. 독립 advisor 최종 배포 수용. 최종 doctor 종료코드1(14/1/0) 실측.

## 사용자 정정 후 main 반영 — 2026-09-12

사용자 “main 병합하고해야지 배포하자고 하면”을 반영했다. 배포 요청은 검증→main 병합·push→main 기준 배포·검증까지 포함하는 것으로 유지한다. 이전 비-main 배포 판단은 잘못이었음을 사용자에게 정정했다.

독립 GO 검토 후 원격 main이 b63인지 재확인하고 검증된 fc45a9aa7c649062ff4641a05322f026b5e8bf1c로 fast-forward push했다. 원격 ls-remote로 실제 반영을 확인했다. dev MAIN_SHA는 실제 원격 근거에 따라 main=candidate=fc45a9aa7c64 ancestor=yes로 갱신했다. 기존 바이너리가 같은 후보이므로 불필요한 재빌드·재시작 없이 재검증했다. Stage API66소스파일과 양환경 HTTPS JS hash가 병합한 제품 산출물과 일치한다.

dev doctor 새 단일실행 종료0, 15 green/실패0/미검사0. 앞선 non-main red는 해소됐다. 원래 b63 대비 계약 변경 red1의 로그와 수용 기록은 유지한다. main 반영이 해당 과거 판정을 없앤 것은 아니다. Stage watcher는 자동 파이프라인의 별도 호환성 검증 전까지 hold하며 이번 수동 배포의 main 일치와 구분한다. 신규 계정·암호 변경0.
