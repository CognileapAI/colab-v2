# Stage 1·2 배포 후 검사 실패 해결

사용자 2026-09-11 요청: 「실패해결」. 대상은 직전 보고의 artifact-ownership과 frontend-visual 두 판정 실패다. 이전 main push·AWS dev 배포 승인 범위를 이어 적용하되 제품/캐시 삭제·Terraform apply·cron 설치·외부 통지·prod는 포함하지 않는다.

기준: main `d78c6e0`, 실제 AWS dev 제품 `9e3ff19f6d27`. 기존 CLAUDE.md 변경과 미추적 검사 산출물은 보존한다. 최초 전체 검사와 보정 결과는 `20260911-stage12-deploy.md`에 그대로 남긴다.

## 실행 계획

- [x] 캐시 19벌의 원장 연결·생성 경위·기존 보존 9키와 교집합을 읽기 전용으로 확인한다. 기존 9와 신규 시험 10을 구분했다. 현재 판정은 증거 보존으로 처리하며 구버전 staging 재발 원인 해결과 구분한다.
- [x] 로그인 비활성 버튼 대비 3.41:1 실패를 재현하고 기존 색 토큰으로 수정한다. 비활성 동작 유지·실화면 대비·관련 프론트 검사를 확인한다.
- [x] 수정과 보존 판단을 독립 검토하고 실제 해당 검사 결과로 수용한다. 원본 삭제·검사기 변경 없이 정확키 보존을 명시했다.
- [ ] 승인된 변경을 커밋·반영·필요한 dev 정적 자산 배포 후 실제 화면을 다시 검사한다. PR 설명/HTML·대장·인계를 실제 결과로 갱신한다.

캐시 조사자는 공유 사본에서 읽기만, 로그인 구현자는 격리 사본을 사용한다. 부모가 통합·기록을 맡는다. 전체 Stage 완료와 이번 두 실패 해결은 구분한다.

## 현재 근거

- 캐시: `20260911-stage12-cache-retention.md`와 `../reports/stage12-failure-fix/cache-retention-evidence.json`. 신규 10키·22파일·551,809바이트, 원본 파일 삭제·이동·DB 쓰기 0. exact-key 보존 선언 외 검사기 코드는 바꾸지 않았다. 기존 로컬 staging의 구버전 reaper 재발 위험은 남는다.
- 로그인: 격리 작업 사본의 이번 실행에서 3.41:1 RED 재현. `--color-gray-400`→`--color-gray-500` 한 줄 변경 뒤 실제 전달 CSS와 5.02:1 대비 확인. 브라우저 시각 검사 GREEN, 전체 프론트 검사 진행 중.
- Vite/NTFS 캐시로 처음 수정 후 측정에도 옛 CSS가 제공된 실행은 실패로 남겼다. 개발 서버를 재기동해 실제 제공 CSS가 바뀐 뒤에만 GREEN으로 측정했다. 제품 서버 재기동은 아니다.
- dev 정적 웹 백업: `.codex/artifacts/stage12-login-web-rollback/` 128파일, 기존 index SHA256 `35cd00d9dc361cc95a3cf3b1282d17b4fb2de516a77f6ef862f9d41d2e55248c`. 정본 웹 배포 도구로 되돌릴 수 있는 파일 사본이며 현재 웹은 아직 그대로다.
- 새 사전 dev doctor 첫 실행은 진단 컨테이너의 DB 자격 파일 읽기 권한 때문에 9/2/4였다. 실패 로그를 보존하고 읽기 전용 마운트의 진단 컨테이너만 올바른 사용자로 실행한 별도 단일 검사에서 **15/0/0, exit 0**을 확인했다. `.codex/artifacts/stage12-fix-doctor-before{,-root}.log`.

## 반영 전 수용

- 로그인 격리 task의 단일 검사: **4/0/0**. frontend-typecheck 오류 0, frontend-test 94파일/1204시험 성공, frontend-fixture-reach 도달 179/금지 0, frontend-visual 페이지 1/작은 글자 0/대비 실패 0/캡처 2장. `../reports/20260911-login-disabled-contrast/gate-summary.json`. 부모가 결과 JSON을 직접 읽고 CSS와 회수 파일의 바이트·세션 hash를 대조했다.
- 로그인 task `16a97e72aab24f46bcbf89cd32b85a27`의 격리 verify-report는 성공했다. SubagentStop 훅은 부모 Git 디렉터리에서 이 격리 task를 찾아 실패했다. 상태를 부모 디렉터리에 복사하거나 기준선을 재등록하지 않았고, 반복 종료 시도만 중단했다. 이 훅 실패를 제품 시험 실패나 훅 통과로 바꾸지 않는다.
- 부모의 artifact-ownership 단독: **1/0/0**, 대상 158/살아 있음 120/접수분 0/고아 19/판정 불가 19/지도 타일 146/삭제 0. 정확키 보존 19와 구판 보류 19가 경고로 출력됐다. `../reports/stage12-failure-fix/after/artifact-ownership/`.
- 생산 프론트 빌드 성공. CSS `index-C77HYNgp.css`, JS `index-B1MJ4QbM.js`. 기존 500kB 초과 청크 경고는 남는다. 검사한 worker CSS와 통합 CSS는 동일하며 서버·계약·DB 제품 코드 diff 0이다.
- 독립 검토의 조건(영속 보존 근거, 관련 4게이트·부모 캐시 검사·빌드 성공)을 충족했다. main 반영과 **dev 정적 웹만** 배포할 수용 근거이며 백엔드·DB·로컬 staging 변경은 포함하지 않는다.
