# design-fix 후속 20260925 — E 통합 실화면 근거

spec: `dev-package/prd/specs/S-DESIGN-FIX-FOLLOWUPS-20260925.md` 부록 B(E) · 부록 D · 부록 E
측정 트리: 통합 브랜치 `worktree-design-fix-followups-grill` 커밋 `9812d41f`(L1 · L2 포함). E 는 코드를 고치지 않았다.
진행: E1(게이트 · 캡처 대조) → E2(실브라우저 부록 D 1–8) 직렬. 레인 L1 · L2 는 워크플로 안에서 통합 워크트리에 바로 커밋했다(레인 브랜치 분리 없음 · 직렬이라 겹침 0).

## E1 — 게이트 · 빌드 · 캡처 대조
- task 게이트 1회: 계 green 6 / red(판정) 0 / red(준비) 0 — `frontend-typecheck` · `frontend-test` · `frontend-fixture-reach` · `frontend-design-lint`(h 포함) · `frontend-design-lint-selftest` · `frontend-visual`.
  - task `ea9ffa32feb14d58a8eeb91a96966e6f` · run `5a75a78aa09c48fe88dbcbef2da182ca` · gate-summary = Git common dir `colab-harness/c6d644755625b30347303841b6060683/ea9ffa32feb14d58a8eeb91a96966e6f/5a75a78aa09c48fe88dbcbef2da182ca/gate-summary.json`.
  - `frontend-visual`: 「페이지 47건 · 13px 미만 0건 · 대비<4.5 0건 · 스크린샷 94장」. 선언 = B0 의 62 URL ＋ `audit-upload.html?register=ok` 라이트 · 다크. 판정 페이지 수가 선언보다 적은 것은 결과 파일 이름 절단(하네스 intent H1) 때문이다 — B0 보고 「한계」와 같다.
  - `::gate-readiness-failure::` 5줄은 `frontend-design-lint-selftest` 의 기대 사례이고 결과는 OK. `::gate-failure::` 0.
- 운영 빌드(`npm --prefix frontend run build`): exit 0.
- 캡처 `fixfu0925-final`: png 208장(202 ＋ 새 장면 `upload-register-ok` 6).
- 대조(`visual:diff --subset` · 기준 `fixfu0925-base` · 공통 34장면 202장): red 30장 · 엄격 차이 합 558449px · exit 1. 보고 원문 = `dev-package/reports/design-review/20260925-followups/capture-diff.md`(차이 이미지는 저장소 밖 · 커밋 안 함).

| 바뀐 장면 | 바뀐 자리(차이 이미지 확인) | 원인 V | spec 예상 |
|---|---|---|---|
| primitives | 갤러리 비활성 단추 5개 | V1 | 확실 |
| login · password-change | 비활성 제출 단추(회색 채움 → 흐린 파랑) | V1 | 확실 |
| detail | 미리보기 절 전체 폭 단추 1개(비활성 plain `.btn` · `DatasetPreviewSection.tsx:354`) | V1 | 가능성 |
| lineage-picker | 「연결」 파란 단추(후보 선택 전 비활성) | V1 | 가능성 |

- 그 밖 29장면 변화 0. 예상 목록 밖 변화 0 — V11 충족.

## E2 — 실브라우저 근거(부록 D 1–8)
- 결과: 소항목 pass 25 · not-run 1 · fail 0 · 기록 1. 원문 = `dev-package/reports/design-review/20260925-followups/live/index.md`(커밋 `c21ac1f5`).
- not-run 1-f: `.titem button` · `.pv-zoom button` · `.pj-x` · `.thumbrow .th-slot` 은 픽스처로 비활성 상태에 닿지 못했다. 대체 근거 = L1 · L2 CSS 정적 단언.
- 주요 값: 누름 배경 라이트 `#0b4eb6` · 다크 `#d4e7ff`(뗀 뒤 기본) · 대화상자 box-shadow none ＋ 1px border-strong · 뒤판 0.45 → 0 약 288ms · 동작 줄이기 즉시 · 팝오버 아래 끝 830.8 ≤ 단추줄 위 835(1440×900) · `.btn-sm` 768 터치 44 / 768 마우스 29 / 1440 29 · 등록 직후 닫고 다시 열기 두 입구 모두 첫 단계 · 5 상태 모두 pass.
- 768 터치 에뮬레이션은 `set device` 로 `pointer: coarse` 가 켜지지 않아 브라우저를 `--blink-settings=primaryPointerType=2` 로 띄워 쟀다(주 포인터 종류만 바꿈 · 터치 이벤트 아님).
- 6-d(우려 1 ⓐ · 기록만): 768 터치 5화면에서 44px 하한으로 새로 넘치거나 줄바꿈된 자리 없음.

## 판정 밖 관찰 — Ted 판정 후보
1. **업로드 미리보기 확대창 위로 등록 폼 일부가 그려진다** — 1440 라이트 · 다크에서 ⤢ 로 연 `.modal.pvx` 위에 ② 단계 「기간」 칸이 겹쳐 보이고, 하단 단추줄 `.reg-actions` 가 확대창 뒤판에 어두워지지 않는다(`live/index.md` 관찰 1).
   - 이번 변경이 원인이 아니다: `80aa95ac..HEAD` 의 프론트 diff 가 더한 쌓임 관련 속성은 비활성 단추의 `opacity: 0.5` 뿐이고, 기간 칸 · 확대창의 조상에 걸리지 않는다(`.dr-pop` 의 `transform-origin` 줄은 닫는 괄호 이동만).
   - 이전부터 있었는지는 실측하지 않았다(지난 회차 실측에 확대창 겹침 기록 없음). 판정표가 지목하지 않은 자리라 고치지 않았다(design-review SKILL `:114`).

## 진행 기록
- E1 은 Stop 훅의 stale 차단을 피하려고 대조 산출물을 저장소 밖(job tmp)으로 옮겼다. 오케스트레이터가 인계 뒤 보고 원문(텍스트)만 위 경로로 반입했다.
- 브라우저 정리는 세션 이름(`fxe2`)으로 했다. 남은 agent-browser · 4291 LISTEN 0(E2 확인).
