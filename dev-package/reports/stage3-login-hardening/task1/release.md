# Stage 3 로그인 강화 Task 1 실행 보고

## 결과

- 구현: 로그인 validation 응답에서 입력·위치·문구·문맥 제거, 기존 `details.errors` 문자열 형식 안에 오류 `type`만 JSON 직렬화.
- 입력: `accountName` 1~320자, `accountName+password` 또는 `accessCode` 한 형식만 허용, 선택하지 않은 필드의 null은 미지정 처리, 빈 문자열·알 수 없는 필드·혼합 형식은 인증기 이전 400.
- 계약: `SessionCredentials`를 두 요청 형식의 `oneOf`로 표현하고 TypeScript 생성물을 갱신.
- 마이그레이션: 0건. DB 스키마·데이터 변경 없음.
- stage 접촉: 0건. 시험은 `--rm`·tmpfs 일회용 PostgreSQL만 사용.

## RED와 GREEN

- RED: 대상 31건 중 9 failed/22 passed. 자격 marker 응답 반사, 알 수 없는 필드 201, 혼합 입력 201, 320자 400, 137자 로그인 400 재현.
- 보완 후 대상 시험: 50 passed/0 failed/0 error/0 skipped.
- 최종 `service-tests-core-api`: 1099 passed/0 failed/0 error/0 skipped, 6 deselected(`not e2e`).
- 최종 게이트 계수: green 3 / red(판정) 1 / red(준비) 0.

## 계약 판정과 소비자

- `contract-lint`: green, seam 3건·규칙 위반 0.
- `generated-up-to-date`: green, 등기부 13건 일치.
- `contract-breaking`: 판정 red 1. `[request-body-wrapped-in-one-of]` — 종전 계약이 허용하던 혼합 payload를 이제 400으로 거절하는 승인된 strict 정책의 실제 파괴 변경.
- 프런트 소비자: `frontend/src/auth/LoginPage.tsx`가 `accountName+password` 정상 형식만 전송. `accessCode` 제품 화면 소비자 0건, 시험·도구 경로 유지.
- 우회·baseline 변경: 0건. 판정 red를 green으로 재분류하지 않음.

## 되돌림과 잔여

- 되돌림 범위: `main.py` 안전 오류 직렬화, `session.py` 입력 모델, `fe-core.yaml`과 생성물, Task 1 회귀 시험을 같은 source snapshot으로 되돌려야 함.
- 현재 판정: Task 1 동작과 서버 회귀 시험 통과. 선언된 필수 게이트 중 `contract-breaking` red 1로 lifecycle complete 조건 미충족.
- 다음 판단: 승인된 파괴 변경의 병합 수용 기록 또는 계약 호환 전략 결정. 계약에서 strict 동작을 숨기는 방식은 적용하지 않음.
