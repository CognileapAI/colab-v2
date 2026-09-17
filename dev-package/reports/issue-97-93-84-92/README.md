# 이슈 #97·#93·#84(+#54)·#92 전후 화면

변경 전은 각 이슈에 기획자·QA가 올린 스크린샷을 그대로 받아 두었다(재구성하지 않았다).
변경 후는 로컬 stub API(127.0.0.1:8001) + vite(5199) 위에서 이 브랜치를 실제 브라우저(agent-browser)로 촬영했다.
촬영 후 제품 화면 코드는 바꾸지 않았다.

| 이슈 | 변경 전 | 변경 후 | 촬영 조건 |
|---|---|---|---|
| #93 팔레트·구간 수 위치 | [전](images/93-preview-before.png) | [후](images/93-preview-after.png) | 접기(`선택값 전체 보기`) 닫힌 상태 · 1280×720 |
| #84 계정 생성 폼 | [전](images/84-account-before.png) | [후 · 뷰포트 700](images/84-account-after-vh700.png) · [후 · 뷰포트 1400](images/84-account-after-vh1400.png) · [후 · 관리자 체크](images/84-account-after-operator-checked.png) · [후 · 다크](images/84-account-after-dark.png) | 두 높이에서 제출 버튼 문서 y 동일 — `84-submit-y.json`(700·1400 모두 929.546875, Δ 0) |
| #97 Lv0 원천 블록 | [전](images/97-register-before.png) | 미촬영 | 승인된 연구실 쓰기 계정 없음 — jsdom 시험으로만 잠금 |
| #92 지도용 선택지 | 이슈 본문 이미지 | 미촬영 | stub 하네스가 `renderable: true` 고정 — jsdom 시험으로만 잠금 |

수정 전·후 실측 근거 원본은 task runtime `191842c824144a449457936fed239976/screenshots/` 와 `visual-audit/`(frontend-visual 계측 probe.json 포함)에 있다.

- intent: `dev-package/intent/2026-09-17-issue-{97,93,84,92}-*.md`
- spec: `dev-package/prd/specs/2026-09-17-issue-97-93-84-92-ui-fixes.md`
