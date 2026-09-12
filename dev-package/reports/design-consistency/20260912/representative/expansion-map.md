# 전체 확장 준비 목록

상태: 소스 경로 확인에 근거한 후속 적용 목록. 대표 화면 사용자 확인 전이며, 아래 화면의 디자인 적용·검증 완료를 뜻하지 않는다.

| 순서 | 화면/묶음 | 실제 소스 경계 | 함께 확인할 상태 |
|---|---|---|---|
| 1 | 공통 토큰·셸 | `frontend/src/shell/tokens.css`, `frontend/src/shell/shell.css` | 주 내비, 좁은 화면, 키보드, 테마 선택·저장·초기 적용 |
| 2 | 데이터셋 목록·연구실 | `frontend/src/routes/DatasetsPage.tsx`, `frontend/src/routes/LabPage.tsx` | 현재 대표안 확정, 빈 결과·불러오기 실패·조건 선택·긴 이름·연구실 정보 모달 |
| 3 | 프로젝트 목록·상세·모달 | `frontend/src/routes/ProjectsPage.tsx`, `frontend/src/routes/ProjectDetailPage.tsx`, `frontend/src/components/project/project.css` | 생성·수정·닫기, 기간·연결 주소, 입력 오류, 처리 중, 닫힌 프로젝트 |
| 4 | 데이터 상세·계보 | `frontend/src/routes/DatasetDetailPage.tsx`, `frontend/src/components/detail/detail.css`, `frontend/src/components/lineage/` | 잠김·권한, 파일 목록·대표 이미지, 계보 그래프, 오류·긴 정보 |
| 5 | 검색·미등록 미리보기 | `frontend/src/routes/SearchResultsPage.tsx`, `frontend/src/routes/UnregisteredPreviewPage.tsx` | 검색 결과 없음·실패, 파일 형태별 미리보기·지도·표 |
| 6 | 업로드·승인 | `frontend/src/components/upload/`, `frontend/src/components/approval/` | 파일 선택·진행·실패·완료, 접근 요청·승인 대기·취소·중첩 모달 |
| 7 | 연구실 설정·구성원·로그인·없는 경로 | `frontend/src/routes/LabSettingsPage.tsx`, `frontend/src/components/members/`, `frontend/src/auth/LoginPage.tsx`, `frontend/src/routes/NotFoundPage.tsx` | 권한별 노출, 편집·저장 오류, 인증 오류, 모바일 복귀 |

검증 축: 두 테마, 모바일/태블릿/데스크톱, 키보드 및 초점, 읽기 크기·대비, 컨테이너 넘침, 실제 저장/조회/새로고침 지속성. fixture 시각 검사와 실제 서비스 사용자 여정은 분리한다.

기존 검수 근거: `dev-package/reports/design-review/20260912/findings.md`.
실제 routes 목록 9개 및 각 화면 CSS import를 2026-09-12 확인했다. components 묶음의 전체 기능 상태는 후속 실제 화면 검수 대상이다.
