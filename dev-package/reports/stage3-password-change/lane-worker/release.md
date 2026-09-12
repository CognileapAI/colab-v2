# 첫 로그인 비밀번호 변경 개선 — stage 반영

사용자 승인: 초기 비밀번호 재입력 없이 새 비밀번호와 확인 두 칸으로 변경.

API는 인증된 최초 변경 세션과 newPassword를 사용한다. DB 행 잠금 안에서 변경 의무와 세션 버전을 재검증하고, 초기 비밀번호 재사용을 거절한다. 변경 후 버전 증가로 이전 세션을 무효화한다. UI는 두 값 불일치 및 10~512자 범위 밖 제출을 막는다.

검증: [task gate](gate-summary.json) 5/0/0, 누락 선언했던 contract-breaking은 [독립 증거](contract-breaking/gate-summary.json) 1/0/0. 서버 1082 passed, 프론트 1207 passed. 부모가 task 2db02ea884ef4104809fea8efb11883e의 현재 파일 및 선언된 5개 게이트를 함께 검증했다. 독립 코드 검토 승인. 자동 종료 훅은 원본 checkout에서 task를 찾지 못한 cwd mismatch로 통과하지 못했고, 올바른 사본에서 부모 검증 후 인계했다.

실제 브라우저: 격리 DB에서 계정 생성→초기 로그인→새/확인 두 칸→불일치 차단→일치 제출→연구실 이동→새로고침→로그아웃→새 비밀번호 재로그인 통과. 모의 응답 0. 사용자 실제 계정 비밀번호 변경 없음.

WSL stage의 core-api와 frontend만 stage3-password-confirm-20260912 이미지로 교체했다. 이전 이미지는 보존했다. DB migration 및 데이터 변경 없음. 제공 번들에서 확인 입력란을 확인했고 배포 판정 15건 통과, 면제 0건. 다른 서비스는 기존 이미지 유지. AWS dev/prod 접근·배포 및 git commit/push 없음.
