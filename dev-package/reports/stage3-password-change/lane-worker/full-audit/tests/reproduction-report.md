# 로그인 추가 결함 재현

제품 파일 변경 없이 보고서 디렉터리의 임시 시험으로 현재 실제 모듈을 불러 검사했다. 운영 DB 및 사용자 계정 접촉 없음.

- 로그인 요청의 네트워크 실패: TypeError가 전파되고 로그인 버튼이 계속 비활성, 확인하는 중 문구 유지, 오류 안내 없음.
- 비밀번호 변경 요청의 네트워크 실패: TypeError가 전파되고 변경 버튼이 계속 비활성, 변경하는 중 문구 유지, 오류 안내 없음.
- 오래된 요청이 새 로그인 후 401을 반환: 새 토큰도 삭제됨.
- 다른 탭의 로그아웃 storage 이벤트: localStorage는 비어 있지만 getToken()의 메모리 값은 이전 토큰 유지.

재현 시험 4 passed는 결함 4건을 실제 관측했다는 뜻이며 제품 정상 판정이 아니다. UI 두 시험은 실제 컴포넌트를 렌더링하고 필드를 변경한 뒤 React form onSubmit을 직접 호출·await했다. fetch는 네트워크 거부 대역이며 실제 브라우저 E2E는 아니다. 이전 401은 대기 가능한 fetch 응답 대역, 탭 동기화는 실제 StorageEvent로 재현했다.

최초 임시 설정 실행은 react/jsx-dev-runtime 해석 오류로 수집 0건 준비 실패였다. 보고서 전용 설정의 해석 경로를 바로잡은 뒤 4건 실행에 성공했다. 제품 설정은 변경하지 않았다.

근거: adversarial.test.tsx, audit.config.mjs, adversarial.log, reproduction-source-hashes.json.

## 기존 회귀검사 재실행

frontend-typecheck 오류 0, frontend-test 95파일 1207 passed, core-api 1082 passed / failed 0 / errors 0 / skipped 0 / deselected 6(not e2e), core 소요 197.83초. core 게이트가 자체 tmpfs 일회용 PostgreSQL을 생성하고 종료 후 정리했다. 운영 DB 접촉 없음.

Task fd200c4e08a54d8f93e4fa3876943324, gate-summary.json: green 3 / red(판정) 0 / red(준비) 0. 세 게이트를 동시에 지정한 verify-report는 현재 파일과 일치하여 exit 0. 별도 E2E 6건은 not e2e 선택자에 따라 미실행이며 브라우저 검사는 부모 담당이다. 기존 회귀검사 통과는 위 결함이 없다는 뜻이 아니다.
