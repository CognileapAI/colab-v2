# 로그인 요청 계약 변경 수용 기록

상태: 사용자 승인으로 변경 수용. contract-breaking의 판정 red를 면제·green으로 재분류하지 않는다. 자동 lifecycle complete 및 배포 준비 완료를 뜻하지 않는다.

## 승인과 범위

사용자에게 기존 혼합 payload 허용→400 거절, 두 정상 로그인 형식 유지, 검사 결과 보존 및 소비자 영향 기록을 설명했다. 사용자는 “좋아 그렇게해”로 이 변경 수용을 승인했다. 근거 절차: dev-package/sessions/X2-FREEZE-PROTOCOL.md §5 ㉯·㉱·㉲.

- 회차/결정 번호: 병합 미승인으로 미발급. 병합 직전 PLAN-SoT §9와 원격 최신 이력을 대조해 등재한다. 이 문서는 번호 예약이나 병합 승인 기록이 아니다.
- 대상: contracts/seams/fe-core.yaml POST /sessions, SessionCredentials의 oneOf 및 accountName 최대320자. 정상 형식은 accountName+password 또는 accessCode 단독이다.
- 근거: 확정 intent/spec의 혼합 입력 차단과 로그인 이름 정합 정책. 이번 추가 승인은 호환성 변경 수용을 명시한다.
- 판정: 기준 HEAD b63c9e8a0d40563a12f815f407756d5d4e85b17e 대비 `1 changes: 1 error, 0 warning, 0 info`, `request-body-wrapped-in-one-of`. 기준 변경·옵션 완화·검사 축소 없음.
- 소비자: 저장소 검색에서 실제 제품 로그인 호출은 frontend/src/auth/LoginPage.tsx 1곳이며 accountName+password만 보낸다. client.ts 두 곳은 URL 판별, generated는 선언, 서버는 제공자다. 검색 명령과 원문은 acceptance-consumers.log. 외부 스크립트 소비자는 전수 확인하지 못했다.
- migration: Task1 추가0건(앞선 레인 기록 기준). 전체 checkout에는 기존 계정 migration0025와 schema 변경이 이미 있으므로 HEAD 대비 DB diff0이라고 주장하지 않는다. 이번 수용 작업은 계약 설명·생성 주석·문서만 변경했다.
- 승인자: 사용자 ttlhi10, 이번 대화의 명시적 “좋아 그렇게해”.
- 미검증 축: stage 실배포·실브라우저 E2E·외부 소비자·후속 세션 기능. 서버 기존 결과1099 pass/6 deselected(not e2e), 집중50 pass는 직전 Task1 실행의 증거다.

## 추가 검사 및 보완

수용 절차의 seam-consistency에서 기존 계정 API3개와 schema4개의 승인 출처 누락7건을 검출했다. 실제 기존 승인 intent 경로를 description에 연결했다. 최초 비밀번호 변경의 설명도 이미 구현된 ‘현재 비밀번호 재입력 없음’으로 바로잡았다. API 형태나 실행 코드는 바꾸지 않았다. 생성 파일은 등기부의 openapi-typescript 명령으로 재생성했다.

최종 검사 출력은 acceptance-final-contract-breaking.log, acceptance-final-contract-lint.log, acceptance-final-generated-up-to-date.log, acceptance-final-seam-consistency.log에 각각 보존한다. 독립 실행을 기존 lifecycle의 한 green 실행으로 합치지 않는다. 설명 변경 후 이전 gate-summary의 source snapshot은 현재 파일 전체를 인증하지 않는다.

## 후속 진행과 되돌림

이 승인으로 Task1의 의도된 계약 변경에 대한 사람 수용 대기를 해소한다. Task2 구현은 진행 가능하다. 자동 게이트는 red를 유지하며 후속 검증은 현재 입력으로 새로 실행한다. 이 승인은 다른 파괴 변경의 포괄 면제가 아니다. 추가 오류는 별도 조사한다.

이번 수용에서 배포·커밋·push는 하지 않는다. 제품 수정 되돌림은 Task1 시작 snapshot에서 main.py/session.py/계약/생성물/시험을 묶어 복원하는 범위이며 기존 계정 구현 전체를 HEAD로 초기화하지 않는다. stage에는 미배포라 서버 되돌림이 필요 없다.

## 현재 파일 SHA-256

- `contracts/seams/fe-core.yaml`: `cea36d3dbf8328edbff28ce485cd51f293fb1d0984826e09696484daac1173cd`
- `frontend/src/generated/fe-core.ts`: `c6cf28ed19d8df169a96351671efb0c686787faa6d9629f354e8810d0ba15de0`
- `services/core-api/src/colab_core/app/main.py`: `7cbf6f57a075a744a4e33acab7720aa44292b18055e087906e62fd23a91d2930`
- `services/core-api/src/colab_core/app/routes/session.py`: `3f6e0066ca284db90746ff5d559081108294474f5186294fca20ab3e13e51e43`
