# 계정 기능 추가 점검

사용자 요청: 더 검사할 부분 확인. 제품 코드·실제 계정·운영 데이터 변경 없음.

## 통과한 추가 검사

- stage core-api의 db_credentials.py, authn.py, accounts.py, session_token.py, deps.py가 작업 사본과 바이트 일치. core/frontend 태그 stage3-password-confirm-20260912 확인.
- 격리 DB에서 같은 version으로 두 변경을 동시 실행: 성공 1, 거절 1, 최종 version 2.
- version 확인 뒤 첫 비밀번호 변경을 커밋시키는 결정적 경합: 저장소는 갱신된 자격을 반환했으나 실제 authenticator가 must_change_password 불일치로 이전 토큰 거절. 인증 우회 재현 안 됨.
- 비운영자 교수의 계정 생성 POST 403. 계정·자격 행 수 불변.
- 실험 스크립트: /home/ttlhi10/colab-stage3-test-env/.codex/artifacts/account-test-env/.env.race.py. 종료코드 0. 소유 시험 DB와 비밀 환경 파일 정리 완료.

## 확인된 결함 — 미수정

화면은 JavaScript String.length 및 HTML maxlength의 UTF-16 길이, 서버 Pydantic은 Unicode 코드포인트 길이를 사용한다. 배포된 실제 PasswordChange 모델로 재현했다.

| 입력 | 화면 계산 | 화면 길이 통과 | 서버 통과 |
|---|---:|---|---|
| 😀 5개 | 10 | 예 | 아니오 |
| 😀 257개 | 514 | 아니오 | 예 |

10~512자 조건의 길이 단위를 통일하고 비BMP 문자의 양끝 경계 시험을 보완해야 한다. 이번은 검사 요청이므로 제품·배포 변경 없이 발견 사항을 남겼다.

## 추가 검토 의견

비밀번호 변경 커밋 뒤 find 재조회가 실패하면 변경은 반영됐지만 응답은 실패할 수 있다. 독립 검토에서 확인한 실패 지점이며 이번에 장애 주입 재현은 하지 않았다. 이를 실제 인증 우회 또는 재현된 장애로 주장하지 않는다.
