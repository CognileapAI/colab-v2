# 카탈로그 필터 디자인 검토 — 2026-09-12

상태: 수정안 초안 · 사용자 선택 대기 · 제품 코드 변경 없음.
입력: 사용자가 첨부한 카탈로그 화면 두 장과 “폰트 이상하고 … 어케할까?” 요청.
기준: HEAD c329c32. 최근 이력과 대장 WU-B7(done)을 대조했다. 기존 기능 완료를 재판정하지 않고 이번에 지목된 필터 표시를 검토한다.

## 진행과 근거

- [x] 화면과 관련 코드·토큰 확인
- [x] catalog.css 정적 검사 실행
- [ ] 제안한 치수·배치의 구현 범위 확정
- [ ] 승인 범위 구현
- [ ] 타입·기존 필터 회귀 시험·정적 계측·실화면 검증

| 항목 | 판정 | 근거 | 처리 |
|---|---|---|---|
| 3축 필터의 전용 스타일 누락 | 있음 | `frontend/src/components/catalog/AxisFilterBar.tsx`의 `.axis-bar`, `.axis-pick`, `.axis-k`에 대응하는 CSS 정의가 frontend/src에 없다 | 즉시 수정 후보 |
| 지도 상태가 다른 필터와 분리됨 | 있음 | `frontend/src/routes/DatasetsPage.tsx`에서 지도 상태 label이 AxisFilterBar 밖의 형제다 | 같은 필터 컨테이너에 배치하는 수정안 |
| 선택 상자의 본문 글꼴 상속 | 있음 | 해당 select의 font 지정과 전역 select의 font-family 상속 선언이 없다. body에는 font-family가 있다 | font-family 상속 명시 후보 |
| 실제 브라우저가 사용한 폰트 | 미상 | `frontend/src/main.tsx`에서 로컬 Pretendard CSS를 import하고 `shell/tokens.css`에 폰트 스택이 있지만 브라우저 로딩은 미측정 | 실화면 계측 |
| 조건 줄의 작은 글자 선언 | 있음 | `frontend/src/components/catalog/catalog.css`의 `.fchips .fl`, `.fchips .fc`, `.fchips .fall`은 11px | 최종 computed 크기 확인 후 13px 정리 후보 |

정적 검사 명령: `python3 .claude/skills/design-review/scripts/css_audit.py --root frontend/src frontend/src/components/catalog/catalog.css`.
실행 종료코드 0. 이는 감사 스크립트 실행 성공이며 제품 게이트 통과가 아니다. 출력은 13px 미만 선언 13건, 음수 margin 0건, 미정의 토큰 0건이다. 선언 수는 최종 렌더링 결함 수가 아니며 이번 범위 밖 항목을 일괄 수정하지 않는다.

## 사용자에게 제안할 범위

1. 기존 Pretendard를 유지하고 필터에 명시적으로 상속한다.
2. 데스크톱 필터 값 14px, 높이 36px, 기존 surface·border·radius 토큰을 사용한다. 모바일은 기존 입력 16px 규칙과 충돌하지 않게 한다.
3. 분류·유형·가공 단계·지도 상태를 하나의 여백 있는 묶음에 놓고 좁은 폭에서는 줄바꿈한다.
4. 적용된 조건은 아래 줄에 유지하고 설명·칩·해제 글자는 13px 이상으로 정리한다.
5. 키보드 선택·포커스와 필터 조회 동작은 기존 회귀 시험 및 브라우저로 확인한다.

대안은 글꼴 전체 교체이나, 코드에서 확인한 직접 원인이 필터 스타일 누락이므로 우선안으로 권하지 않는다. 새 색상·새 필터 기능·전체 사이트 개편은 제안하지 않는다.

## 미실행과 다음 진입조건

제품 수정·커밋·배포 0건. 브라우저 computed font·반응형·키보드 동작과 제품 게이트는 미실행이다. 이번 질문에는 원인과 구체적 수정 방향을 제시한다. 일반 화면 상담에 디자인 감사 스킬의 커밋 절차를 일률 적용해 추가 승인을 요구하지 않는다. 구현 시 현재 대화의 승인 범위를 기준으로 판단한다.

## 독립 검토 반영

advisor ②: approve-with-changes. 진단과 수정 방향은 수용하되 일반 화면 상담보다 큰 절차가 되지 않도록 필수 커밋·승인 대기 조건을 제거했다. 36px/14px는 제안이며 실제 폰트 로딩은 미상이다. migration 변경은 없고 main 동일성을 수용 근거로 사용하지 않았다.
