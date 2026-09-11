# 로그인 비활성 버튼 대비 수정 — 2026-09-11

## 범위

- 로그인 제출 버튼의 비활성 동작은 유지한다.
- 흰 글자 배경을 `--color-gray-400`에서 `--color-gray-500`으로 바꿔 WCAG AA 대비 4.5:1 이상을 충족한다.
- 검사기 예외와 허용 목록은 추가하지 않는다.

## TDD 근거

- RED: 수정 전 `frontend-visual`은 `button.login-submit`을 3.41:1로 측정해 판정 실패했다.
- 구현: `frontend/src/auth/login.css`의 비활성 배경 토큰 한 곳만 `--color-gray-500`으로 바꿨다.
- GREEN: Vite를 다시 시작해 수정 CSS가 제공되는 것을 확인한 뒤 `frontend-visual`이 페이지 1건, 13px 미만 0건, 대비 미달 0건, 라이트·다크 스크린샷 2장으로 통과했다.
- 정적 계측: `auth/login.css`에서 13px 미만·음수 여백·미정의 토큰·로컬 토큰·대비 미달이 모두 0건이었다. 기존 카드 그림자 1건과 reduced-motion 없는 전환 선언 2건은 이번 대비 수정 범위 밖이다.
- 최종 통합 결과 정본: `dev-package/reports/20260911-login-disabled-contrast/gate-summary.json`.

## 원한 결과 대조

- 미달: 0건.
- 초과: 0건.
