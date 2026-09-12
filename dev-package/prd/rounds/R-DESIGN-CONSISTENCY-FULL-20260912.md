> spec: dev-package/prd/specs/S-DESIGN-CONSISTENCY-FULL-20260912.md
# 전체 화면 디자인 확장 Implementation Plan
> **For agentic workers:** executing-plans를 사용한다. 부모 한 명이 쓰며 조사·검토는 읽기 전용이다.
**Goal:** 승인 대표안의 typography·여백·색상을 모든 화면에 적용한다.
**Architecture:** tokens.css + 공통 디자인 CSS와 테마 제어 모듈. 기존 업무 컴포넌트/source 유지.
**Tech Stack:** React, TypeScript, Vite, CSS, agent-browser.
**Spec:** `dev-package/prd/specs/S-DESIGN-CONSISTENCY-FULL-20260912.md`.

## Global Constraints
- 글자13px 이상, 텍스트 대비4.5:1 이상, 카드 그림자0.
- 두 테마·모바일 모든 기능, 기존 계약·권한·업무 상태 유지.
- API/제품 데이터/배포 미접촉. 실제 저장 검증은 새 테마 설정에 한정.

## 의존·진행
- [x] 대표 화면 확인 수용: Ted “와 너무좋은데”.
- [x] 전체 사양·계획 작성.
- [x] 전체 스타일 및 fixture 경계 조사·계획 검토. advisor: 공통 CSS 순서 고정, production build 대조, 전 캡처 직접 시각 검토 요구 수용.
- [x] 테마 동작 RED → 구현 → GREEN. 5개 동작 시험 통과.
- [x] 공통 토큰·대표안 제품 연결.
- [x] 상세·프로젝트·검색·미리보기·업로드·승인·설정·로그인 확장.
- [ ] 전 장면 계측 및 실제 테마 지속성·키보드 검증.
- [ ] 독립 수용 검토, 필수 게이트4개, build, 실제 파일 hash 확인.
- [ ] 전체 결과 인계.

## 테마 동작
**Files:** `frontend/src/shell/theme.ts`, `frontend/src/shell/ThemeSwitcher.tsx`, `frontend/test/theme.test.tsx`, `frontend/index.html`, `frontend/src/main.tsx`, `frontend/src/shell/Gnb.tsx`, `frontend/src/auth/LoginPage.tsx`.
- [x] 시스템 선호, 사용자 선택·저장·복구, 저장 거부, OS 변화, 다른 탭의 변경, 컨트롤 접근성 행위 테스트 작성 후 RED 확인.
- [x] 초기 HTML 테마 적용과 runtime 동기화 구현, 작은 공통 선택 컨트롤을 셸·로그인에 연결.
- [ ] 해당 테스트 GREEN 및 첫 로드/새로고침/키보드 실제 조작.

## 공통·화면 스타일
**Files:** `frontend/src/shell/tokens.css`, `frontend/src/shell/design-system.css`, `frontend/src/shell/shell.css`, `frontend/design-preview.css`, 대상 `frontend/src/components/**/*.css`, `frontend/src/auth/login.css`.
- [x] 대표 CSS를 제품 공통 파일로 승격하고 독립 preview도 같은 파일을 소비한다.
- [x] 의미별 배경·글자·경계·상태색 토큰을 정리하고 전 화면의 literal/fallback과 native controls를 연결한다.
- [x] 기존 화면 순서·문구·업무 상태를 유지하고 부모 컨테이너가 여백을 소유하게 한다.

## 전체 장면 검증
**Files:** `frontend/audit-design.tsx`, `dev-package/reports/design-consistency/20260912/full/`.
- [ ] 실제 routes 9개 및 로그인/업로드/승인/모달 상태를 fixture에 연결하고 상태 목록을 기록한다.
- [ ] 각 상태의 375/768/1440 × light/dark 렌더·콘솔·폰트·대비·넘침 검사.
- [ ] 대표 사용자 조작: 테마 저장/새로고침/OS, 필터, 모달 초점·오류·푸터, 파일 미리보기 및 반응형 스크롤.
- [ ] 기존 frontend 테스트·typecheck·fixture-reach·visual 및 build 실행. 보고서 실제 hash 검증 후 완료.
- [ ] 원한 결과 항목별 미달/초과와 실제 미실행 축을 인계에 기록한다.

- [ ] 모든 화면·상태 캡처를 직접 시각 검토하고 디자인 판단을 기록한다(자동 계측으로 대체하지 않음).
- [ ] production build의 로그인·실제 셸과 fixture의 계산 스타일·테마 동작 대조.

## 검증 실행 상태 정본
소스 변경 후 hash 검증이 요구되므로 아래 별도 보고서에서 최종 게이트·캡처·수용·인계 상태를 갱신한다.
- `dev-package/reports/design-consistency/20260912/full/execution-status.json`
- `dev-package/reports/design-consistency/20260912/full/result.md`
계획의 미체크 검증 항목은 위 실행 상태의 실측 결과와 대조한다. 최종 소스 검토 approve, 테마 단위 5건 및 built-shell 브라우저 11단계 통과. 추가 시각 수정 후 30장면×6=180 캡처와 필수 게이트 실행 중.
