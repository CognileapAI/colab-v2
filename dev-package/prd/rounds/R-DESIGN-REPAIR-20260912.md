> spec: dev-package/prd/specs/S-DESIGN-REPAIR-20260912.md

# 디자인 누락 복구 실행

- [x] 전체 검수 및 사용자 수정 승인 확인
- [x] 기존 변경 보존, 별도 로컬 브랜치 생성
- [x] 모달 키보드 회귀 시험 RED — 기존 3건 실패 확인
- [x] 필터·홈·설정·로그인·프로젝트·상세 및 승인 스타일 수정
- [x] 모달 포커스 및 잠긴 행 키보드 진입 수정
- [x] 375/768/1440 1차 브라우저 검사. 검색창 추가 넘침 발견·보정; 최종 재계측은 gate/manual 참고
- 검증 상태: frontend-typecheck / frontend-test / frontend-fixture-reach / frontend-visual 결과는 아래 작업별 gate-summary.json이 판정한다.
- 결과 및 제한 기록: 아래 gate/result.md에서 최종 증거와 함께 인계한다.

순서: RED → 구현 → 현재 소스 검증 → 인계. 단일 작성자.
관련 파일: shell/shell.css, catalog/catalog.css, dashboard/dashboard.css,
project/project.css, lab/lab.css, auth/login.css, approval/approval.css,
routes/DatasetsPage.tsx, routes/LabSettingsPage.tsx, common/useDialogFocus.ts 및 해당 모달.

검수 보고서 커밋 조건의 예외: 사용자가 현재 로컬 검수 결과를 승인했고 수정 실행을 요청했다.
검사를 위해 임의 커밋하지 말라는 dual-agent.md 지침에 따라 미커밋 파일 hash와 lifecycle 검증을 사용한다.
이를 원래 커밋 조건을 충족한 것으로 보고하지 않는다. D17 전면 재편은 advisor 권고로 제외.

## 검증 정본
- task: 4b517115943a4d1f801b499273954621
- dev-package/reports/design-repair/20260912/gate/gate-summary.json
- dev-package/reports/design-repair/20260912/gate/result.md
- 1차 전체 시험의 project card box-shadow 선언 기대 실패는 `box-shadow: none`으로 카드 무그림자 의도를 명시해 수정했다. 기존 시험 기대를 삭제하지 않았다.
- pending Verified는 취소선·회색·aria-disabled를 보존하고 회색 글자를 기존 text-muted 토큰으로 보정했다. 상태 정책을 바꾸지 않았다.
- 실서비스 배포, 데이터 저장, 모든 권한별 라이브 E2E를 완료로 확대하지 않는다.
