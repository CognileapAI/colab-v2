> spec: dev-package/prd/specs/S-DESIGN-CONSISTENCY-20260912.md
# 전체 디자인 일관성 Implementation Plan

> **For agentic workers:** executing-plans로 이 세션에서 직접 수행한다. 같은 사본의 쓰기 주체는 부모 한 명이다.

**Goal:** 대표 화면 3종을 밝음·어두움 및 모바일에서 확인 가능한 상태로 제공한다.
**Architecture:** 실제 React 컴포넌트를 기존 fixture로 구동하고 preview class로 시각 제안을 한정한다. 사용자 확인 이후 전역 확장한다.
**Tech Stack:** React, TypeScript, CSS tokens, Vite, agent-browser.
**Spec:** `dev-package/prd/specs/S-DESIGN-CONSISTENCY-20260912.md`

## Global Constraints
- 13px 이상, 텍스트 대비 4.5:1 이상, 카드 그림자 0.
- 기존 메뉴·기능·계약 유지. 상태색 의미 보존.
- 페이지 외곽 32px/모바일 16px, 카드 내부 24px/모바일 20px.
- 미리보기의 데이터는 예시. 실제 서버 저장 검증과 구분.

## 진행·의존 상태
- [x] intent 명시 승인 기록 및 사양 합성.
- [x] 기존 디자인 규칙·fixture 조사 및 계획 검토. advisor 수정 수용: 실제 프로젝트 생성 버튼으로 포커스 복귀 검증, 375px 어두운 필터 팝업·오류·Tab·푸터 도달 추가.
- [x] 대표 화면 미리보기 구현.
- [ ] 현재 소스의 24장면 및 상호작용 검증.
- [ ] 검증된 대표 화면 인계.
- [ ] 사용자 대표 화면 확인 — 이후 전체 확장의 선행 조건.
- [ ] 확인된 기준을 전체 화면에 확장하고 전수검사 — 현 단계 미착수.

## 대표 화면 구현
**Files:** `frontend/design-preview.html`, `frontend/design-preview.js`, `frontend/design-preview.css`, `frontend/audit-design.tsx`, `frontend/src/shell/tokens.css`.
**Interfaces:** 기존 audit의 scene 쿼리와 실제 source 인터페이스 유지. `design=calm&theme=light|dark`만 추가.
- [ ] 미리보기 제어 UI에서 목록·연구실·빈 연구실·입력 모달 및 기존/제안·테마·기기 폭을 선택한다.
- [ ] audit entry의 명시 쿼리가 있을 때만 body class와 토큰·preview CSS를 활성화한다.
- [ ] 기존 화면에 기능 변경 없이 typography·여백·표·카드·모달 스타일을 적용한다.
- [ ] iframe 내 모달을 닫은 뒤 다시 열 수 있도록 제어 화면에 초기화 동작을 둔다.

## 검증
**Files:** `dev-package/reports/design-consistency/20260912/representative/` 아래 증거 저장.
- [ ] 기존 frontend-typecheck/frontend-test/frontend-fixture-reach/frontend-visual 실행, 이전 보고서 재사용 금지.
- [ ] agent-browser로 4상태 × 3폭 × 2테마를 열어 document.fonts.ready 이후 캡처, DOM 넘침·글자·대비 계측.
- [ ] 목록 필터 변경 → 결과 변화; 모달 빈 이름 오류 → 유형 전환 → Escape → 복귀 확인.
- [ ] 375px 어두운 테마의 필터 팝업·선택·모달 오류 대비 및 실제 ProjectsPage 생성 버튼에서 열기 → Tab 순환 → 본문 마지막 입력 → 푸터 → Escape 복귀를 검사한다.
- [ ] 대표 장면과 실제 UI를 직접 보고 발견한 잘림·위계·대비 문제 수정 후 해당 장면 재검증.
- [ ] 보고서에는 대표 화면 준비와 전체 intent 완료를 분리한다. 실제 서비스 저장 E2E는 미실행으로 명시한다.

## 전체 확장 단계
- 대표 화면 확인 시 구체적인 토큰·공통 레이아웃 기준을 고정하고 기존 화면별 적용 목록을 작성한다.
- 카탈로그·연구실·프로젝트·상세·검색·업로드·승인·설정·로그인 및 오류/빈/권한 상태를 대조한다.
- 각 화면의 기능 유지·두 테마·모바일·접근성 및 실제 사용자 여정을 검증하고 intent 미달/초과를 기록한다.
- 사용자 확인 전 이 단계의 완료를 선언하지 않는다.

## 대표 화면 실행 기록
- 구현: 기존 fixture 진입점에 명시적인 제안 쿼리만 추가하고 토큰·CSS를 preview body 범위로 한정했다.
- 수용 검토: advisor 계획 검토의 실제 opener, 모바일 메뉴·오류 대비·푸터 도달 지적을 검증에 추가했다.
- 시각 반복: 목록 메타데이터 줄 구분, 모달 배경 스크롤 잠금, 모바일 필터 메뉴의 화면 하단 고정 표시를 적용했다.
- 검증과 인계 상태 정본: `dev-package/reports/design-consistency/20260912/representative/result.md` 및 같은 폴더의 `gate-summary.json`. 이 계획의 미확인 체크는 보고서의 실제 결과로 판정하며, 보고서 생성 전 성공을 가정하지 않는다.
- 전체 intent 상태: 대표 화면 사용자 확인과 전체 확장은 남아 있다.

- 회귀 검사 정밀도 보완: `frontend/test/css-residual-rc11.test.ts`의 기본 팔레트 해석을 `:root` 선언으로 한정한다. scoped dark 토큰을 전역 값으로 잘못 읽은 2건 실패를 재현했고, 테마 토큰 혼입 방지 fixture를 추가했다. 기존 밝기·대비 판정 기준은 유지한다.
