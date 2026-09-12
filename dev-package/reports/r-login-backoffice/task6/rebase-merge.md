# Task 6 리베이스·병합 메모

레포 이력에 이 파일이 없었다(`git log --all -- <이 경로>` 0건). 어드바이저 지적을 적을 자리가
지목돼 새로 만든다. 아래 두 줄이 이 파일의 내용 전부다.

## `deploy_doctor` 항목 수

- **15 를 유지한다.** 늘리지 않는다 — 항목 수 15 는 완료 정의(`CLAUDE.md §0` · 개정 2026-09-08 ·
  `R-D WU-D3`)가 못 박은 값이고, 라운드 파일도 「항목 수를 15 에서 늘리지 않는다」로 적었다
  (`dev-package/prd/rounds/R-LOGIN-BACKOFFICE.md:15`).
- 그러므로 이번 회차가 더한 DB 권한(아래)은 **`deploy_doctor` 항목으로 승격하지 않는다.**

## 계정 관리자 롤 GRANT 재적용

- **배포 절차의 손 단계다** — 자동 검사 대상이 아니다.
- 대상 = `services/core-api/ops/account-admin-role.sql` 재적용.
- 이번 회차가 더한 GRANT 둘 — `d2_member_role` 의 `SELECT`(계정 목록의 역할 열) ·
  `account_admin.service_operator` 의 `INSERT`·`DELETE`(운영자 지정·해제).
- 미적용 시 증상 = 계정 목록·운영자 지정이 500.
- 절차 위치 = `dev-package/prd/rounds/R-LOGIN-BACKOFFICE.md` Task 5 의 dev 반영 단계.
