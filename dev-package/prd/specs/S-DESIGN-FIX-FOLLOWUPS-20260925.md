# Spec: design-fix 후속 20260925 — 승인 intent 판정 28건 중 레인 몫
출처 intent: `dev-package/intent/2026-09-25-design-fix-followups.md`(승인 2026-09-25 · Ted 「좋아 확인완료 스펙가자」 · 재개봉 금지: 예).
판정 인용: intent 「설계트리」 Q1a–Q8e 와 「처분 요약」 표. 이 spec 은 판정을 다시 열지 않는다. 레인 몫 = 처분 요약에서 자리가 「레인」인 행 ＋ ⑦-17 행.
기준 트리: develop `80aa95ac` ＋ 브랜치 `worktree-design-fix-followups-grill` 의 intent 커밋(문서만). 레인 워크트리는 **이 spec 을 더한 커밋에서** 딴다(main 아님).
용어: B0 = 기준 측정 단계 · L1 = CSS·문서 레인 · L2 = 업로드 레인 · E = 통합 실화면 근거 단계. 「값 n」은 `dev-package/prd/specs/S-DESIGN-FIX-20260924.md` 확정 값 번호다.

## 문제 진술
- 비활성이 될 수 있는 단추 70곳(btn 계열 58 · 로그인 제출 3 · 그 밖 9)에 공통 비활성 모양이 없다. btn 계열 `:disabled` 규칙 0 — 58 중 56 이 활성과 같은 모양(cursor pointer · opacity 1). 로그인 제출은 회색 채움 ＋ cursor default(활성 파랑과 명도비 1.01:1).
- 파란 채움 단추 3종의 누름 = hover = primary-700(1.00:1). 정본 누름 규칙 문장이 「한 단 진한 값」과 「primary-700」을 함께 적어 스스로 어긋난다.
- 641px 이상 터치 기기는 29px 작은 단추 · 40px 컨트롤을 받는다(`pointer: coarse` 선례 0).
- 업로드 모달: 닫기 확인창 · 미리보기 확대창만 전역 모달 그림자를 받는다(다크 가장자리 1.19:1) · 뒤판은 전환 없이 한 프레임에 사라진다 · 1440×900 에서 달력 팝오버 아래 끝 1014.8px 가 하단 단추줄 밑 약 180px 가려진다 · 팔레트 0개에도 「3종과 달라요」 안내가 나오고 조회 실패 뒤 재조회 경로가 없다.
- 정리 잔여: 계보 CSS 죽은 규칙 1 · 실제 이동량과 다른 시험 제목 1 · 업로드 모달 부모 조건 주석 없음. 로컬 픽스처는 등록이 실패하고 닫기 부모가 비어 「등록 직후 닫고 다시 열기」를 재지 못했다. 재지 못한 상태 5개 · 병합 트리 `frontend-visual` 재계측이 남아 있다.

## 원한 결과 (V-id)
- V1 비활성 단추 70곳(btn 계열 58 · 로그인 제출 3 · 그 밖 9)이 opacity .5 · cursor not-allowed 로 보인다. 상세 삭제 단추의 겹치는 규칙이 없다. 업로드 미리보기 격자 칸 hover 테두리가 비활성에서 나오지 않는다 — 확인 방법: L1·L2 CSS 정적 단언(부록 C) · E computed 값(부록 D 1) · 캡처 대조 예상 장면(부록 E).
- V2 파란 채움 단추 3종(`.btn-primary` · `.btn-strong` · `.gnb-upload`)의 누름 배경 = `--color-primary-800` — 확인 방법: CSS 단언 3곳 ＋ 두 테마 글자 대비 · E 마우스 누른 채 computed 배경(부록 D 2).
- V3 `pointer: coarse` 기기에서 `--control-height` 44px · 작은 단추 하한 44px, 마우스 기기 변화 0 — 확인 방법: CSS 단언(토큰 블록 · 매체 조건) · E 768 터치 에뮬레이션 44 대 마우스 1440 · 768 29(부록 D 6) · 캡처 대조에서 V3 원인 변화 0.
- V4 업로드 닫기 확인창 · 미리보기 확대창 = 그림자 0 ＋ 1px `--color-border-strong` — 확인 방법: CSS 단언 · E computed(부록 D 3).
- V5 업로드 모달 뒤판 배경색이 열기 · 닫기 모두 0.3s `cubic-bezier(0.2, 0, 0, 1)` 로 전환, 동작 줄이기에서 즉시 — 확인 방법: CSS 단언 · E computed transition ＋ 닫는 중 스크린샷 2장(부록 D 4).
- V6 1440×900 에서 달력 팝오버를 열면 팝오버 전체가 하단 단추줄 위에 보인다(열 때 본문 스크롤) — 확인 방법: RTL 스크롤 호출 단언 · E 팝오버 아래 끝 ≤ 단추줄 위 끝(부록 D 5).
- V7 팔레트 안내는 목록이 1개 이상이면서 3개가 아닐 때만. 0개 · 조회 실패는 `UNAVAILABLE` 문장만(안내 없음) ＋ 조회 실패 때 「다시 시도」 단추가 팔레트를 다시 조회(0개 포함 · 우려 4 ⓐ) — 확인 방법: RTL(0 · 1 · 2 · 3 · 4 · 실패 → 재시도).
- V8 정본 기록: 합격선 두 곳 비활성 예외 · `docs/design-system.md` btn 행 disabled · 누름 규칙 옆 비활성 한 줄 · 누름 primary-800 문구 · ⑦-17 행 · 생성 표 재생성 — 확인 방법: L1 문서 문장 단언 · `frontend-design-lint` h(`design-docs.mjs --check`) green.
- V9 정리: 계보 CSS 죽은 규칙 삭제 · 시험 제목 정정(단언 불변) · 업로드 모달 머리 주석 「새 부모 = `useUploadModalPresence` 필수」 — 확인 방법: 원문 단언 · 기존 시험 green.
- V10 로컬 실브라우저에서 등록 직후 0.3초 안에 닫고 다시 열면 두 입구(UploadEntry · GridAttachEntry) 모두 첫 단계가 보인다 — 등록 성공 픽스처 ＋ 실제 닫기 부모 장면(`scenes.json` 1장면 추가 · 회귀 캡처). 재지 못한 상태 5개 1회 계측(영구 장면은 하네스 intent H11) — 확인 방법: E 스크린샷 · computed 값(부록 D 7 · 8) · 새 장면 캡처 존재.
- V11 B0 가 develop HEAD 트리에서 `frontend-visual` ＋ 캡처 기준을 먼저 잰다. 최종 캡처 대조에서 예상 장면 목록 밖 픽셀 변화 0 — 확인 방법: B0 보고 · E `visual:diff` 결과와 「바뀐 장면 → 원인 V」 표.
- 식별자 V1–V11 은 PR 요약 「원한 결과 ↔ 실제 ↔ 근거」 표의 행 이름으로 그대로 쓴다.

## 해법 개요
- 4단계 직렬 B0 → L1 → L2 → E · PR 1. 게이트는 호스트 단독으로 한 번에 하나씩 돈다.
- 사용자 관점 새 흐름 0: 비활성 · 누름 · 터치 높이 · 대화상자 테두리 · 뒤판 전환은 모양만 바뀐다. 팔레트 재시도는 상세 근거 편집의 기존 「다시 시도」 작은 단추와 같은 문구 · 크기다. 달력 팝오버는 그대로 열리고 본문만 스크롤된다.
- 새 토큰 0 · 새 hex 0 · 새 문구 0. 값은 모두 기존 값이다: primary-800(기존 토큰) · 44px(기존 640px 이하 값) · 0.3s 곡선(모달 본체 값) · 88px(우려 2 ⓐ · 등록 본문 기존 아래 여백).
- 레인마다 시험 작성 단계(RED) → 구현 단계(GREEN). 기존 시험 수정은 시험 작성 단계에서만 한다.

## 사용자 스토리
1. 연구원으로서 누를 수 없는 단추가 흐리게 보이길 원한다, 팔레트 도착 전 「미리보기 그리기」를 눌러도 반응이 없어 고장으로 읽히기 때문에.
2. 연구원으로서 비활성 단추 위 커서가 금지 모양이길 원한다, 손가락 커서는 누를 수 있다는 신호이기 때문에.
3. 로그인하는 사용자로서 입력 전 제출 단추가 다른 단추와 같은 방식으로 흐려지길 원한다, 회색 채움은 활성 파랑과 명도비 1.01:1 이라 색상으로만 구분되기 때문에.
4. 비밀번호를 바꾸는 사용자로서 제출 단추가 로그인 화면과 같은 비활성 모양이길 원한다, 같은 단추 모양이 화면마다 다르게 꺼지면 규칙을 다시 익혀야 하기 때문에.
5. 운영자로서 계정 관리의 제출 단추도 같은 비활성 모양이길 원한다, 계정 생성 중 두 번 누르는지 알 수 있어야 하기 때문에.
6. 교수로서 대시보드 할 일의 승인 · 반려 단추가 처리 중에 흐리게 보이길 원한다, 처리 중인지 단추만 보고 알 수 있어야 하기 때문에.
7. 연구원으로서 연구실 구역 제목 단추가 열 수 없을 때 흐리게 보이길 원한다, 화살표 `›` 가 남아 열 수 있는 것처럼 보이기 때문에.
8. 연구원으로서 미리보기 확대 단추가 원본 해상도 한계에서 흐리게 보이길 원한다, 글자 안내만으로는 단추가 꺼졌는지 보이지 않기 때문에.
9. 연구원으로서 프로젝트 모달 닫기 × 가 제출 중 흐리게 보이길 원한다, 제출 중에는 닫히지 않기 때문에.
10. 연구원으로서 업로드 미리보기의 고를 수 없는 격자 칸에 hover 테두리가 나오지 않길 원한다, 테두리가 고를 수 있다는 신호이기 때문에.
11. 연구원으로서 아직 갈 수 없는 등록 단계가 흐리게 보이길 원한다, 지금은 갈 수 있는 비선택 단계와 같은 모양이기 때문에.
12. 연구원으로서 파란 단추를 누르는 순간 hover 보다 한 단 진한 색을 보길 원한다, 지금은 hover 와 누름이 같아 눌렸는지 모르기 때문에.
13. 연구원으로서 상단 「업로드」 단추와 업로드 모달 강조 단추도 같은 누름 색이길 원한다, 파란 채움 3종이 같은 규칙을 따라야 하기 때문에.
14. 태블릿 사용자로서 작은 단추 · 입력칸 · 닫기 × 가 44px 이상이길 원한다, 641px 이상 터치 기기에서 29px 단추는 손가락으로 맞히기 어렵기 때문에.
15. 마우스 사용자로서 화면 크기 · 배치가 그대로이길 원한다, 29px 작은 단추 값은 데스크톱 밀도로 확정됐기 때문에.
16. 연구원으로서 업로드 닫기 확인창의 가장자리가 다크에서도 보이길 원한다, 그림자는 다크에서 1.005:1 이라 창이 뒤판에 묻히기 때문에.
17. 연구원으로서 미리보기 확대창이 다른 가운데 대화상자 11개와 같은 테두리 모양이길 원한다, 두 창만 합격선 「카드 그림자 0」 밖이기 때문에.
18. 연구원으로서 업로드 모달을 열고 닫을 때 뒤판이 본체와 함께 서서히 어두워지고 밝아지길 원한다, 지금은 닫을 때 뒤판이 한 프레임에 사라져 밝기가 급히 바뀌기 때문에.
19. 동작 줄이기를 켠 사용자로서 뒤판이 전환 없이 즉시 바뀌길 원한다, 움직임이 불편하기 때문에.
20. 1440×900 화면의 연구원으로서 기간 달력을 열면 「적용」 단추까지 보이길 원한다, 지금은 스크롤해야 보이기 때문에.
21. 좁은 화면의 연구원으로서 하단 시트 달력 위치가 그대로이길 원한다, 스크롤 보정이 시트를 옮기면 안 되기 때문에.
22. 연구원으로서 팔레트가 0개일 때 받은 목록을 표시한다는 안내 대신 「미리보기를 만들 수 없어요」 문장을 보길 원한다, 받은 목록을 표시한다는 문장이 0개와 맞지 않기 때문에.
23. 연구원으로서 팔레트가 1–2개 또는 4개 이상이면 받은 선택지와 안내를 함께 보길 원한다, 고를 수 있는 선택지는 쓸 수 있기 때문에.
24. 연구원으로서 팔레트 조회가 실패하면 「다시 시도」로 다시 조회하길 원한다, 지금은 모달을 닫고 다시 열어야 하기 때문에.
25. 연구원으로서 그리기 실패 오류에는 팔레트 「다시 시도」가 나오지 않길 원한다, 누르면 그리기가 아니라 목록 조회만 다시 하기 때문에.
26. 연구원으로서 등록 직후 0.3초 안에 모달을 닫고 다시 열면 첫 단계부터 보길 원한다, 끝난 등록의 입력이 새 업로드에 섞이면 안 되기 때문에.
27. 디자인 검수자(Ted)로서 비활성 대비가 합격선 밖이라는 문장이 정본 두 곳에 같게 적히길 원한다, 흐린 단추 대비(라이트 2.12–3.46 · 다크 3.24–4.61)가 다음 회차에 결함으로 다시 올라오지 않아야 하기 때문에.
28. 디자인 검수자로서 빨간 삭제 단추 hover · 누름 없음이 정본 ⑦ 17 행에 보이길 원한다, 다음 회차 판정 대기로 남아야 하기 때문에.
29. 디자인 검수자로서 레인 뒤 캡처 대조에서 예상 장면 밖 변화가 0 이길 원한다, 판정하지 않은 화면이 바뀌지 않았음을 보여야 하기 때문에.
30. 디자인 검수자로서 병합 트리의 `frontend-visual` 결과를 레인 앞 기준으로 보길 원한다, 레인 뒤 결과와 비교할 출발점이 필요하기 때문에.
31. 디자인 검수자로서 재지 못한 상태 5개의 실측 값을 한 번 보길 원한다, 지난 회차 판정이 실측 없이 남아 있기 때문에.
32. 개발자로서 업로드 모달 파일 머리에서 「새 부모는 닫기 훅 필수」를 보길 원한다, 훅 없이 붙이면 완료된 닫기 경계가 깨지기 때문에.
33. 개발자로서 쓰는 곳 없는 계보 규칙이 없고 시험 제목이 실제 이동량(11 · 1 · 1px)과 맞길 원한다, 다음 수정의 근거를 잘못 읽지 않아야 하기 때문에.

## 구현 결정
- 모듈 · 인터페이스:
  - 단추 프리미티브: 기본 단추 규칙에 비활성 선언 하나(opacity .5 · cursor not-allowed). 화면 층의 파생(파란 강조 · 빨간 삭제)은 배경만 정하므로 규칙을 더하지 않는다(층 순서상 opacity · cursor 는 프리미티브 규칙이 닿는다). 기존 hover 비활성 제외 형태 불변.
  - btn 밖 9곳: 화면 층 CSS 가 cursor pointer 를 정하는 선택자마다 같은 두 값의 비활성 규칙(기존 선택자보다 명시도가 높은 `:disabled` 결합). 격자 칸 hover 는 프리미티브의 비활성 제외 형태를 따른다.
  - 로그인 제출: 비활성 규칙의 회색 채움 · default 커서를 버리고 같은 두 값. 상세 삭제 단추의 비활성 규칙은 지운다(프리미티브 규칙이 대신).
  - 누름: 파란 채움 3종 누름 배경만 primary-800. hover 값 · 다른 누름 규칙 불변.
  - 터치 하한: 토큰 층에 입력 방식 조건 블록 1개(coarse pointer)에서 컨트롤 높이 토큰만 44px. 여백 토큰 불변. 작은 단추 하한 매체 조건에 같은 조건을 OR 로 더한다.
  - 대화상자 두 곳: 업로드 화면 층 두 선택자에 그림자 none ＋ 1px border-strong. 전역 모달 기본값 불변(회귀 잠금 유지).
  - 뒤판: 배경색만 전환(본체와 같은 시간 · 곡선) · 시작 모양 = 투명 · 닫는 중 = 투명. 닫기 타이머 · JS 불변(뒤판 시간 = 본체 시간). 동작 줄이기는 전역 규칙이 즉시로 만든다.
  - 달력 팝오버: 마운트 직후 1회 자기 루트를 가장 가까운 위치로 스크롤(block nearest · 즉시). 단추줄 여백은 우려 2. jsdom 에 스크롤 API 가 없으므로 optional call(선례: 포인터 capture). 640px 이하 하단 시트 위치 불변.
  - 팔레트: 안내 조건 = 목록 1개 이상이면서 3개가 아님. 0개 = 조회 실패와 같은 오류 상태. 「다시 시도」 = 팔레트 조회 실패 · 0개일 때(우려 4 ⓐ) 오류 문장 옆 작은 단추 · 누르면 팔레트 재조회 카운터 증가 ＋ 오류 해제. 오류 상태는 그리기와 공유하므로 단추 표시는 팔레트 상태로만 정한다. 같은 컴포넌트의 기존 「다시 불러오기」 카운터 형태를 재사용한다.
  - 등록 성공 픽스처: 기존 업로드 audit 진입점에 질의 분기 1개(등록 성공 모의 응답 ＋ 실제 닫기 부모 두 입구). 분기가 없으면 기존 동작(등록 실패 · 빈 닫기) 그대로 → 기존 업로드 장면 캡처 불변. 서버 호출 0.
  - 정리: 쓰는 곳 0 계보 규칙 삭제 · 시험 제목 정정 · 업로드 모달 머리 주석 한 줄.
  - 정본: 손글 줄 수정 ＋ 생성 표 재생성(부록 F).
- 스키마 · 마이그레이션: 없음.
- API 계약: 변경 없음(프론트 CSS · TSX · 픽스처 · 문서만).

## 시험 결정
- seam 구성: **확인됨** 2026-09-25 — Ted 「권고대로」(to-spec 2단계 · ⓐ = 아래 기존 seam 5종 ＋ 신설 1).
- 외부 행위 기준 검증 항목: 사용자가 보는 computed 값(opacity · cursor · 배경 · 테두리 · 높이 · 박스 위치) · 보이는 문장 · 단추 유무 · 조회 호출 수 · 닫고 다시 연 뒤 단계. 구현 세부(상태 변수 이름 · 카운터)는 단언하지 않는다.
- 재사용 seam:
  - 실브라우저 측정 — audit 픽스처 빌드 ＋ agent-browser(선례 `dev-package/reports/design-review/20260924/fix/live/index.md` §0).
  - 캡처 대조 — `visual:capture` · `visual:diff` ＋ 예상 변화 장면 목록.
  - RTL — 팔레트 안내 0 · 1 · 2 · 3 · 4 · 재시도 재조회 · 팝오버 열 때 스크롤 호출 · 기존 닫고 다시 열기 시험(수정 없이 green).
  - CSS 정적 단언 — 주석을 걷고 선택자 블록을 잘라 잰다(선례 `frontend/test/design-fix-20260924-F-css.test.ts` 도우미).
  - `frontend-design-lint` ＋ `design-docs.mjs --check`(게이트 h).
- 신설 seam: 기존 audit 픽스처 메커니즘 안의 등록 성공 장면 1개뿐.
- 게이트 이름: `frontend-typecheck` · `frontend-test` · `frontend-fixture-reach` · `frontend-design-lint` · `frontend-design-lint-selftest`(L1) · `frontend-visual`(부록 E).
- green-by-skip 방지: 새 시험은 대상 목록 길이를 먼저 단언한다(L1 비활성 선택자 4 · 파란 채움 2 / L2 비활성 선택자 2 · 파란 채움 1 · 팔레트 경우 6). 선택자 블록을 못 찾으면 빈 문자열이 아니라 실패. `COLAB_VISUAL_URLS` 장면 목록 비지 않음 · 결과 0건 red(게이트 규칙). 캡처 예상 장면 목록 비지 않음. 부록 D 행마다 값 또는 미실행 사유.

## 정책 대조 (작성 시점 제약)
- `.agents/rules/product.md` §2 도메인: 프론트는 독립 배포 단위 — 저촉 없음.
- §3 #8 문서에 절대경로 금지 — spec · 레인 보고 · 실화면 index · 정본에 저장소 상대 경로만.
- §4 게이트 우회 · 비활성 금지 · 대상 축소로 green 금지 — `frontend-visual` 은 URL 선언, CSS 변경 레인에서 `COLAB_VISUAL_EXEMPT=1` 금지 · 장면 목록 축소 금지.
- §5 금지: 범위 늘리기 — 레인은 intent 판정 행만 집행한다. 「나중에」로 남기기 — 넘기는 항목은 모두 intent 처분 요약에 자리 이름이 있다(아래 범위 밖 표). 생성물 손편집 — 정본 생성 표는 `design-docs.mjs` 재생성.
- §5-b: CSS 주석 걷고 측정 · 표 안 빈 줄 금지 · 한 레인 한 일 · 대기 루프 금지.
- `.agents/skills/design-review/SKILL.md` `:113` 새 토큰 이름은 Ted 판정 뒤 — 새 토큰 0(primary-800 · 44px 는 기존 값). `:114` 판정표가 지목하지 않은 자리는 고치지 않는다(우려 1). `:116` staging · dev 쓰기 금지 — 등록 성공 장면은 로컬 모의 응답. `:108` TSX 를 CSS 레인에 섞지 않는다 — L1 TSX 0, L2 는 `upload.css` 까지 소유한 TSX 레인.
- 새 문구 0(intent 제약): `UNAVAILABLE` · 「다시 시도」 재사용.
- 계약 동결 해제 필요: 아니오. 서비스 · 스키마 · 계약 변경 0.
- PR 게시 · 병합 · 배포 · 결정 번호 발급은 이 spec 이 주지 않는다. dev 배포는 병합 뒤 Ted 승인 범위(Q7a).

### 디자인 제약 확인 (화면마다 한 표)
정본 `frontend/src/shell/tokens.css` · `.agents/skills/design-review/SKILL.md` §0 · `.agents/skills/apple-design/SKILL.md`. 행 기호 a–h 는 이 표 안의 기호다(게이트 검사 기호와 무관). 대비 행의 비활성 예외: 4.5:1 합격선은 활성 컨트롤에 적용하고 비활성은 WCAG 1.4.3 · 1.4.11 비활성 예외로 합격선 밖이다(V8 이 정본 두 곳에 적는다) — 흐린 단추 글자 대비 라이트 2.12–3.46 · 다크 3.24–4.61(intent Q1a).

공통 프리미티브 · 토큰(`shell/tokens.css` · `primitives.css` · `shell.css`)

| 항목 | 판정 | 근거 |
|---|---|---|
| a 토큰만 사용 | 충족 | primary-800 기존 토큰 · 44px 기존 값 · 파일별 `:root` 신설은 토큰 파일 안 매체 블록뿐 |
| b 글자 13px 이상 | 해당 없음 | 글자 크기 변경 0 |
| c 대비 4.5:1 | 충족 · 비활성 예외 | on-primary 대 primary-800 라이트 7.56 · 다크 12.56 |
| d 카드 그림자 0 | 해당 없음 | 그림자 변경 0 |
| e 여백은 컨테이너 소유 | 해당 없음 | 여백 토큰 불변 |
| f 누름 피드백 | 충족 | hover → 누름 명도비 라이트 1.38 · 다크 1.24 |
| g 중단 가능 전환 · reduced-motion | 해당 없음 | 전환 변경 0 |
| h 터치 하한 | 충족 | coarse 44px · 마우스 불변 |
| 캡처 장면 | — | primitives · catalog(GNB) · projects |

로그인 · 비밀번호 · 계정 관리(`auth/login.css`)

| 항목 | 판정 | 근거 |
|---|---|---|
| a 토큰만 사용 | 충족 | 회색 채움 제거 · 색 리터럴 0 · opacity 는 토큰 체계 밖 수치(Q1a 판정 값) |
| b 글자 13px 이상 | 해당 없음 | 변경 0 |
| c 대비 4.5:1 | 충족 · 비활성 예외 | 활성 불변 |
| d 카드 그림자 0 | 해당 없음 | 변경 0 |
| e 여백은 컨테이너 소유 | 해당 없음 | 변경 0 |
| f 누름 피드백 | 해당 없음 | 변경 0 |
| g 중단 가능 전환 · reduced-motion | 해당 없음 | 기존 배경 전환 유지 |
| h 터치 하한 | 충족 | 제출 단추가 `--control-height` 를 쓰면 coarse 44px(E 확인) |
| 캡처 장면 | — | login · password-change · account-admin |

상세(`detail/deletion.css`)

| 항목 | 판정 | 근거 |
|---|---|---|
| a 토큰만 사용 | 충족 | 규칙 삭제만 |
| b · d · e · g | 해당 없음 | 변경 0 |
| c 대비 4.5:1 | 충족 · 비활성 예외 | 활성 불변 |
| f 누름 피드백 | 해당 없음 | 빨간 삭제 단추 누름은 ⑦-17(다음 회차) |
| h 터치 하한 | 충족 | 프리미티브 규칙 경유 |
| 캡처 장면 | — | detail |

대시보드 · 연구실(`dashboard/dashboard.css`)

| 항목 | 판정 | 근거 |
|---|---|---|
| a 토큰만 사용 | 충족 | 두 값만 |
| b · d · e · f · g | 해당 없음 | 변경 0 |
| c 대비 4.5:1 | 충족 · 비활성 예외 | 활성 불변 |
| h 터치 하한 | 해당 없음 | 크기 변경 0 |
| 캡처 장면 | — | lab(구역 제목) · 대시보드 장면 없음 → CSS 단언 ＋ 부록 D 1 |

미리보기 확대(`preview/preview.css`)

| 항목 | 판정 | 근거 |
|---|---|---|
| a 토큰만 사용 | 충족 | 두 값만 |
| b · d · e · f · g | 해당 없음 | 변경 0 |
| c 대비 4.5:1 | 충족 · 비활성 예외 | 글자 안내 「원본 해상도까지 봤어요」 불변 |
| h 터치 하한 | 해당 없음 | 640px 이하 44 기존 |
| 캡처 장면 | — | preview · preview-done |

프로젝트 모달(`project/project.css`)

| 항목 | 판정 | 근거 |
|---|---|---|
| a 토큰만 사용 | 충족 | 두 값만 |
| b · d · e · f · g | 해당 없음 | 변경 0 |
| c 대비 4.5:1 | 충족 · 비활성 예외 | 활성 불변 |
| h 터치 하한 | 충족 | 닫기 × 40 → 44(coarse · Q3c) |
| 캡처 장면 | — | project-dialog · project-close |

계보(`lineage/lineage.css`)

| 항목 | 판정 | 근거 |
|---|---|---|
| a–h | 해당 없음 | 쓰는 곳 0 규칙 삭제 · 렌더 변화 0 |
| 캡처 장면 | — | lineage-picker(변화 0 기대) |

업로드 모달(`upload/upload.css` · 미리보기 · 기간 팝오버 · 모달 주석)

| 항목 | 판정 | 근거 |
|---|---|---|
| a 토큰만 사용 | 충족 | primary-800 · border-strong · 본체 곡선 · 88px(우려 2 ⓐ) 모두 기존 |
| b 글자 13px 이상 | 충족 | 「다시 시도」 = 기존 작은 단추 |
| c 대비 4.5:1 | 충족 · 비활성 예외 | 대화상자 가장자리 다크 2.53:1 · 라이트 2.32:1(글자 아님 · 비교: 이전 1.19:1) |
| d 카드 그림자 0 | 충족 | 두 대화상자 그림자 0 |
| e 여백은 컨테이너 소유 | 충족 | 스크롤 여백은 팝오버가 아닌 스크롤 조정 값 |
| f 누름 피드백 | 충족 | 강조 단추 누름 primary-800 |
| g 중단 가능 전환 · reduced-motion | 충족 | 뒤판 전환은 CSS 전환(도중 반전) · 전역 동작 줄이기 즉시 |
| h 터치 하한 | 충족 | 등록 단추줄 `--control-height` coarse 44 |
| 캡처 장면 | — | upload · upload-classify · upload-metadata · upload-link · 새 upload-register-ok |

## 우려 항목 (판정 필요)
| # | 항목 | ⓐ | ⓑ | 권고 |
|---|---|---|---|---|
| 1 | 터치가 주 입력인 기기에서 작은 단추 · 입력칸 높이 하한이 44px 로 오른다(마우스 기기는 그대로). 768px 폭 태블릿에서 이 높이 때문에 어떤 화면의 줄 · 표 · 도구 막대가 넘치거나 줄바꿈될 수 있다. 판정표는 그런 화면을 지목하지 않았고, 검수 절차는 지목되지 않은 자리를 고치지 않는다 | 규칙은 그대로 두고 넘치는 자리를 레인 보고 「후속」 절에 화면 · 폭 · 스크린샷으로 기록한다 — 이번 PR 변경 파일 불변 · 넘침은 다음 회차까지 남는다 | 레인이 넘치는 자리를 함께 고친다 — 넘침은 사라지지만 판정 밖 화면 CSS 가 PR 에 들어오고 그 값은 Ted 판정을 거치지 않는다 | ⓐ |
| 2 | 1440×900 에서 달력 팝오버를 열 때 본문을 스크롤해 팝오버 전체를 보이게 한다. 등록 화면 아래에는 고정 단추줄이 있어 팝오버를 화면 아래 끝까지만 올리면 아랫부분이 여전히 가린다. 스크롤할 때 단추줄만큼 여백을 두어야 한다 | 등록 화면 본문이 이미 두는 아래 여백 88px 을 팝오버 스크롤 여백으로 재사용한다 — 새 값 0 · CSS 한 줄 · 단추줄 높이가 바뀌면 두 값을 함께 고친다 | 열 때 스크립트가 단추줄 실제 높이를 재서 더 스크롤한다 — 높이 변화를 따라가지만 TSX 에 측정 코드가 늘고 jsdom 에서 높이가 0 이라 시험이 약해진다 | ⓐ |
| 3 | 재지 못한 상태 5개를 로컬 시험 화면에서 한 번 잰다. 일부는 지금 시험 화면 자료로 그 상태를 열 수 없다 — 처리 수준 불일치 표시가 붙은 행이 목록에 없을 수 있고, 열 메뉴 · 계정 관리 창 · 닫는 중 상태는 클릭 같은 조작이 필요하다 | 시험 화면에 그 상태를 여는 최소 자료만 질의 매개변수로 켜지게 더하고 조작은 측정 도구로 한다. 캡처 장면 목록은 바꾸지 않는다 — 5개 모두 값이 남고 기존 캡처 영향 0 | 열 수 없는 상태는 미측정으로 기록한다 — 파일 변경 0 이지만 그 상태는 실측 없이 다음 회차로 넘어간다 | ⓐ |
| 4 | 업로드 미리보기에서 팔레트 조회가 실패하면 「지금 미리보기를 만들 수 없어요. 잠시 뒤 다시 시도해 주세요.」 옆에 「다시 시도」 단추를 둔다(승인된 판정). 조회는 성공했지만 팔레트가 0개로 온 경우에도 같은 문장이 나오도록 이미 정했다. 승인 기록은 「조회 실패 뒤」만 적고 있어, 0개일 때 단추를 둘지가 기록에 없다 | 0개일 때도 단추를 둔다 — 같은 문장 옆에는 늘 같은 단추가 있어 「다시 시도」를 요청하는 문장에 방법이 따른다 · 서버가 0개를 계속 주면 눌러도 같은 결과다 | 조회 실패일 때만 둔다 — 0개는 서버 설정 문제로 보고 문장만 남긴다 · 문장은 「다시 시도」를 요청하지만 방법이 없는 상태가 0개에 남는다 | ⓐ |

- 판정 2026-09-25: 우려 1–4 모두 ⓐ — Ted 원문 「권고대로」. 우려 4 ⓐ 는 intent 설계트리 Q8a 에 줄 추가로 기록했다.

## 범위 밖
| 항목 | 처분 | 자리 |
|---|---|---|
| 파일 고른 뒤 503 실패에서 × 확인 없이 닫힘 | 결함 아님 · 현행 유지(Q2e) | 닫힘 |
| 빨간 삭제 단추 hover · 누름 | 다음 회차(Q3b) · ⑦-17 행만 L1 | 다음 design-review §0 「이월 · 판정 대기」 |
| 확대 · 관성 끌기 dev 확인 | 에이전트 마우스 · 휠 · Ted 실제 터치(Q7a · Q7b) | 병합 뒤 dev 배포 |
| 드롭 영역 dragover 모양 | Ted 수동(Q7b) | dev 배포 뒤 |
| 루트 글자 ≠16px · 768 실기 터치 | 에이전트 에뮬레이션 · Q3c 검증 겸함 | dev 배포 뒤 |
| 캡처 잔차 3 | 닫힘 — 증거 소실(Q7d) | 닫힘 |
| `routes/**` 편차 집행 | 기판정 그대로 | 다음 design-review |
| px 글자 리터럴 → rem | 별건 intent(Q6) | 루트 글자 확인 뒤 |
| 미리보기 원본 격자 시험 대기 초과 | 하네스 intent H15(Q8c) · 재현되면 로그만 | 하네스 intent |
| 포인터 끌기 경계(수용된 손실 5) | 실제 터치 끌기 결과 뒤 판정(Q8d) | dev 배포 뒤 |
| 5 상태 영구 캡처 장면 | H11 판정(Q7c) | 하네스 intent |
| 전환 중 fixed 기준 변화 | 유지(Q2c) | 닫힘 |
| 전역 `.modal` 기본 그림자 | 기각(Q2a · 회귀 잠금) | 닫힘 |
| 입력칸 · 선택칸 비활성 모양 | 가지 밖(Q1 가정) | 해당 없음 |
| 모달 쪽 완료 세션 거르기 | 기각(Q8e) | 닫힘 |

## 산출 계획
- spec 1(이 파일) · 레인 보고 4 `dev-package/sessions/design-fix-followups-20260925-{B0,L1,L2,E}.md` · 새 시험 2 · 기존 시험 수정 4파일 · 실화면 근거 폴더 1 · 캡처 라벨 2 · PR 1(게시는 사용자).
- 라운드 파일은 만들지 않는다(선례 흐름 intent → spec → advisor ①② → 레인 → PR).
- 예상 레인 수: 4단계 직렬(B0 · L1 · L2 · E). 코드 레인은 L1 · L2 둘.
- 커밋 트레일러: `Intent-Ref: dev-package/intent/2026-09-25-design-fix-followups.md`.
- ⑦-17 은 정본 ⑦ 표와 L1 보고 「후속」 절 두 곳에 적는다(Q5).

## 부록 A 범위 표
| V-id | intent 판정 | 변경 | 파일(`frontend/src/` 기준 file:line) | 레인 |
|---|---|---|---|---|
| V1 | Q1a · Q1b | 단추 비활성 규칙 1개(opacity .5 · cursor not-allowed) · btn 계열 58 | `shell/primitives.css`(hover 제외 `:31` · `:35` 옆) | L1 |
| V1 | Q1c | 로그인 제출 비활성 = 두 값(회색 채움 · default 제거) | `auth/login.css:88`–`91` | L1 |
| V1 | Q1d | 상세 삭제 단추 겹치는 규칙 삭제(지우는 값 = `opacity: 0.5` · `cursor: not-allowed` · 새 규칙과 같아 모양 변화 0) | `components/detail/deletion.css:41`–`44` | L1 |
| V1 | Q1e | 할 일 단추 3 | `components/dashboard/dashboard.css:301`–`314`(cursor `:308`) ← `TodoInbox.tsx:189` · `:201` · `:204` | L1 |
| V1 | Q1e | 연구실 구역 제목 | `dashboard.css:48`–`63`(cursor `:62`) ← `LabPage.tsx:59` | L1 |
| V1 | Q1e | 미리보기 확대 | `components/preview/preview.css:339`–`346` ← `PreviewZoomControls.tsx:20` | L1 |
| V1 | Q1e | 프로젝트 모달 닫기 | `components/project/project.css:365`–`372` ← `ProjectCloseModal.tsx:45` · `ProjectFormModal.tsx:112` | L1 |
| V1 | Q1e | 격자 칸 비활성 ＋ hover 제외 | `components/upload/upload.css:418`–`424` ← `PreviewPanel.tsx:368` | L2 |
| V1 | Q1e | 등록 단계 | `upload.css:203`–`209` · `:598` ← `RegisterArea.tsx:1175` | L2 |
| V2 | Q3a | 누름 primary-800 ＋ 주석 문장(「primary 는 primary-700 유지」) | `shell/primitives.css:36` · 주석 `:28` · `shell/shell.css:249` | L1 |
| V2 | Q3a | 강조 단추 누름 primary-800 ＋ 주석 문장 | `components/upload/upload.css:321` · 주석 `:320` | L2 |
| V3 | Q3c | coarse 블록 ＋ 머리 주석 구조 문장 | `shell/tokens.css:197`–`198` 사이 · `:6` | L1 |
| V3 | Q3c | 작은 단추 하한 조건 ＋ 주석 문장(「640px 이하는」) | `shell/primitives.css:41` · 주석 `:38` | L1 |
| V4 | Q2a | 두 대화상자 | `upload.css:310` · `:560` | L2 |
| V5 | Q2b | 뒤판 전환 · 시작 · 닫는 중 | `upload.css:9`–`17` · `:30`–`32` 옆 · `:35` | L2 |
| V6 | Q2d | 열 때 스크롤 | `components/upload/PeriodCalendarPopover.tsx:122`–`128`(import `:13`) · 여백 값 `upload.css:610` | L2 |
| V7 | Q2f | 안내 조건 · 0개 = 오류 | `components/upload/PreviewPanel.tsx:519`–`523` · 조회 `:155`–`175` | L2 |
| V7 | Q8a | 「다시 시도」 | `PreviewPanel.tsx:175`(deps) · 오류 `:588`–`592` · 선례 `:122` · `:565` · 문구 `components/detail/SearchEvidenceEditor.tsx:209` | L2 |
| V8 | Q1f · Q1d · Q3a · Q3c · Q5 | 정본 손글 · 재생성 | `docs/design-system.md:173` · `:240` · `:280` · `:281` · ⑦ `:310` 뒤 · 생성 `:40`–`165` · `:180`–`232` · `.agents/skills/design-review/SKILL.md:17` | L1 |
| V9 | Q8b | 죽은 규칙 삭제 | `components/lineage/lineage.css:266` | L1 |
| V9 | Q8b | 시험 제목 | `frontend/test/design-fix-20260924-F-preview.test.tsx:342` | L2 |
| V9 | Q8e | 머리 주석 | `components/upload/UploadModal.tsx:1`–`11`(훅 `:185`) | L2 |
| V10 | Q4 | 등록 성공 분기 · 장면 1 | `frontend/audit-upload.tsx:26` · `:43` · `frontend/scripts/visual-baseline/scenes.json`(upload `:690` 뒤) | L2 · 측정 E |
| V10 | Q7c | 5 상태 1회 계측(우려 3) | 부록 D 8 | E(자료는 L2) |
| V11 | Q7e | 기준 · 최종 대조 | — | B0 · E |

## 부록 B 레인 · 순서
| 단계 | 소유 파일(이 단계만 쓴다) | 종류 | V |
|---|---|---|---|
| B0 | `dev-package/sessions/design-fix-followups-20260925-B0.md` · 게이트 보고 `dev-package/reports/design-fix-followups-20260925/B0/` | 측정 · 코드 0 | V11 |
| L1 | `frontend/src/shell/{tokens,primitives,shell}.css` · `frontend/src/auth/login.css` · `frontend/src/components/{detail/deletion,dashboard/dashboard,preview/preview,project/project,lineage/lineage}.css` · `docs/design-system.md` · `.agents/skills/design-review/SKILL.md` · `frontend/test/design-fix-followups-20260925-L1.test.ts` · `frontend/test/design-fix-20260924-L1.test.ts` · 레인 보고 | CSS · 문서 · TSX 0 | V1 · V2 · V3 · V8 · V9 |
| L2 | `frontend/src/components/upload/{upload.css,PreviewPanel.tsx,PeriodCalendarPopover.tsx,UploadModal.tsx}` · (여는 쪽에 둘 때만) `upload/RegisterArea.tsx` · `frontend/audit-upload.tsx` · (우려 3 = ⓐ) `frontend/audit-design.tsx` 질의 분기 · `frontend/scripts/visual-baseline/scenes.json` · `frontend/test/design-fix-followups-20260925-L2.test.tsx` · `frontend/test/design-fix-20260924-{L2,F-ci,F-preview}.test.tsx` · 레인 보고 | TSX ＋ `upload.css` · 픽스처 | V1 · V2 · V4–V7 · V9 · V10 |
| E | `dev-package/reports/design-review/20260925-followups/live/` · 레인 보고 · 게이트 보고 | 측정 · 코드 0 | V1–V7 · V10 · V11 |

- 겹침 0: `upload/` 폴더의 CSS · TSX 는 L2 만, 정본 문서는 L1 만 쓴다. L1 은 L2 의 `.btn-strong` 누름 값(primary-800)도 정본 문장에 적는다(같은 PR).
- 순서: advisor ① → B0 → L1 → L2 → E → advisor ③ → PR 요약(게시는 사용자).
  - B0: 레인 워크트리 준비(`frontend/` 에서 `npm ci` · capture 브라우저 확인 · 실패는 78 로 보고하고 멈춤) → `frontend-visual`(`scenes.json` 34장면 · 부록 E) → `visual:capture` 라벨 `fixfu0925-base`(전체 장면 · `scenes.json` 변경 전). 프론트 트리가 develop HEAD 와 같은지 SHA 로 적는다.
  - L1: 시험 작성(RED) → 구현(GREEN) → 게이트(부록 E) → 보고.
  - L2: L1 결과 커밋에서 시작 → RED → GREEN → 게이트 → 보고.
  - E: L2 결과에서 audit 빌드 → 게이트 → `visual:capture` 라벨 `fixfu0925-final` → 대조 → 실화면 근거 → 보고. 결함을 찾으면 소유 레인으로 돌린다(E 는 코드를 고치지 않는다).
- 게이트 · audit 서버는 호스트 단독으로 한 번에 하나씩 돈다(`frontend-test` serial · 호스트 뮤텍스). 겹쳐 돈 결과는 판정에 쓰지 않는다.
- 직렬 이유: L1 이 프리미티브를 바꿔 L2 장면 기준이 바뀐다 · B0 기준은 `scenes.json` 변경 전이어야 한다 · 레인당 파일 수가 작다.
- 레인마다 `lifecycle begin` 으로 task 를 열고 산출물을 선언한다. 보고서 골격을 먼저 쓴다(턴 한도).

## 부록 C 수용 기준
- CSS 단언은 원문에서 주석을 걷고 선택자 블록을 잘라 잰다(도우미는 `frontend/test/design-fix-20260924-F-css.test.ts:17`–`122` 형태를 새 파일에 복제). 대비는 WCAG 휘도 · 라이트 `:root` · 다크 `:root[data-theme="dark"]` 값.

L1(`frontend/test/design-fix-followups-20260925-L1.test.ts`)

| V | 단언 |
|---|---|
| 개수 | L1 비활성 대상 선택자 목록 길이 = 4 · 파란 채움 목록 길이 = 2(`.btn-primary:active` · `.gnb-upload:active`) |
| V1 | `primitives.css` 에 `.btn:disabled` 블록 1개 · 선언 = opacity 0.5(`.5` · `0.5` 표기 동치 · 선례 `deletion.css:42`) · `cursor: not-allowed` · `!important` 0 · 기존 `:where(:not(… :disabled))` hover 원문 불변 |
| V1 | `login.css` `.login-submit:disabled` 선언 = 두 값만(background 0 · `cursor: default` 0) |
| V1 | `deletion.css` 에 `:disabled` 0 |
| V1 | `.titem button` · `.dash-section-label` · `.pv-zoom button` · `.pj-x` 각각 `:disabled` 블록에 두 값 |
| V2 | `.btn-primary:active` · `.gnb-upload:active` 배경 = `var(--color-primary-800)` · on-primary 대 primary-800 두 테마 ≥ 4.5 |
| V3 | `tokens.css` 에 `@media (pointer: coarse)` 블록 1 · 안의 선언 = `--control-height: 44px` 1개 · 640px 블록 · `:121` 40px 원문 불변 · `.btn-sm` 하한 블록 매체 조건에 `(max-width: 640px)` 와 `(pointer: coarse)` 둘 다 |
| V8 | `docs/design-system.md` 와 SKILL `:17` 에 비활성 예외 문장 · btn 행 `disabled` · 누름 규칙 옆 「비활성 = opacity .5 · cursor not-allowed」 · 「파란 채움은 primary-800」 · 누름 문장 안 primary-700 0 · ⑦ 표 17 행 · `:240` 편차 칸 `(:disabled)` 0 |
| V9 | `lineage.css` 에 `.lin-unknown-why` 0 |
| 문서 | `design-docs.mjs --check` 는 게이트 h 가 잰다(시험에서 부르지 않는다) |

- 기존 시험 수정(시험 작성 단계): `frontend/test/design-fix-20260924-L1.test.ts:176`–`177`(primary-700 → 800) · `:217`–`218`(매체 조건) · `:364`(`.gnb-upload:active` → 800).
- 감시(수정 없이 green 확인 · 깨지면 RED 단계에서 사유와 함께 수정): `L1.test.ts:244`–`247`(`.modal` · `.modal--dialog` 그림자 잠금) · `F-css.test.ts:231`–`243` · `:332`–`355`(합격선 줄 `:active` · 「예외」 부분 일치 · 누름 줄 `--color-surface-pressed` 포함 · 「미적용 · 레인 보고서 · 아직」 0) · `F-final.test.ts:68`–`86`(누름 줄 「판정 대기」 0 · ⑦ 달력 누름 행 0) · `auth.test.tsx:165` · `:203` · `:206` · `dashboard.test.tsx:109` · `lineage-unknown-20260907.test.tsx:194`.
- 정본 문장 시험은 모두 부분 일치다 — 부록 F 의 문장 추가만으로는 깨지지 않는다. 누름 줄에 「미적용」 · 「아직」 · 「판정 대기」를 쓰지 않는다.

L2(`frontend/test/design-fix-followups-20260925-L2.test.tsx`)

| V | 단언 |
|---|---|
| 개수 | L2 비활성 대상 선택자 = 2 · 파란 채움 = 1(`.btn-strong:active`) · 팔레트 경우 = 6(0 · 1 · 2 · 3 · 4 · 실패) |
| V1 | `.thumbrow .th-slot:disabled` · `.regsteps button:disabled` 두 값 · `.th-slot:hover` 선택자가 비활성 제외 · `upload.css` `.btn-strong` 블록에 cursor · opacity 0 |
| V2 | `.btn-strong:active` 배경 = `var(--color-primary-800)` |
| V4 | `.confirm-back .modal` · `.modal.pvx` 에 `box-shadow: none` · `border: 1px solid var(--color-border-strong)` · `primitives.css` `.modal` 원문 불변 |
| V5 | `.modal-back.mb-takeover` transition = background-color 0.3s `cubic-bezier(0.2, 0, 0, 1)` · `@starting-style` 안 같은 선택자 배경 transparent · closing 규칙 배경 transparent ＋ `pointer-events: none` 유지 · 본체 transition 원문 불변 |
| V6 | RTL: `scrollIntoView` 스텁 → 기간 칸 누름 → 팝오버 → 1회 호출 · `block: 'nearest'` · smooth 아님 · 다시 렌더에 추가 호출 0 · 스텁 없는 jsdom 에서 예외 0 · (우려 2 ⓐ) `.dr-pop` 스크롤 여백 = 88px |
| V7 | 0 → 안내 없음 · `up-preview-error` = `UNAVAILABLE` · 「다시 시도」 1(우려 4 ⓐ) · 그리기 비활성 / 1 · 2 · 4 → 안내 있음 · 「다시 시도」 0 / 3 → 안내 0 / 실패 → 「다시 시도」 → 조회 2회 · 성공(3) 뒤 오류 0 · 그리기 활성 / 그리기 실패 오류에는 「다시 시도」 0 |
| V9 | F-preview 제목에 「16ms 마다 1px 씩」 0 · `UploadModal.tsx` 머리 주석에 `useUploadModalPresence` 필수 문장 |
| V10 | 픽스처 분기가 typecheck · fixture-reach 를 통과 · F-int 1 두 시험 수정 없이 green |

- 기존 시험 수정: `design-fix-20260924-L2.test.tsx:226`(→ 800) · `design-fix-20260924-F-ci.test.tsx:124`–`132`(0개 = `UNAVAILABLE` 만) · `design-fix-20260924-F-preview.test.tsx:342`(제목만).
- 감시: `L2.test.tsx:173` · `:178`–`190` · `upload-transfer.test.tsx:294` · `F-int.test.tsx:209` · `:241` · `register-steps-20260907.test.tsx:480`–`487` · `close-guard-20260905.test.tsx:181` · `F-ci.test.tsx:113`.

## 부록 D 실화면 근거 (E · 판정은 사람)
- 대상 = audit 빌드(`frontend/` 에서 `npm run audit:build` → `npm run audit:preview -- --port 4291 --strictPort`) · `/audit-design.html?design=full&scene=<장면>` · `/audit-upload.html?<질의>`. 픽스처 화면이라고 보고서에 적는다. staging · dev 연결 0.
- 도구 = agent-browser(`get styles` · `mouse down` · 스크린샷) ＋ 읽기 전용 init 스크립트(선례 `probe-init.js`) · eval 미사용. 1440×900 기본 · 라이트/다크. 끝나면 서버 · 세션 종료를 확인한다.
- 산출 = `dev-package/reports/design-review/20260925-followups/live/`(index.md ＋ 스크린샷 커밋). 임시 파일은 저장소 밖.

| # | 측정 | 대상 | 기대 |
|---|---|---|---|
| 1 | 비활성 computed opacity · cursor — 계열 대표(plain · primary · secondary · ghost · danger · strong · login-submit) ＋ btn 밖 9곳 | primitives(비활성 5) · upload 계열 · login · 도달 가능한 장면 | 0.5 · not-allowed. 장면 없음(대시보드)은 미실행 ＋ CSS 단언 근거. 다른 클래스가 이미 흐리게 하는지 자리마다 적는다 |
| 2 | 누른 채 400ms 배경 | `.btn-primary` · `.btn-strong` · `.gnb-upload` 두 테마 | primary-800 계산값 · 뗀 뒤 기본 |
| 3 | 대화상자 computed | 닫기 확인창 · 미리보기 확대창 | box-shadow none · border 1px border-strong |
| 4 | 뒤판 transition-property · 닫는 중 배경 ＋ × 뒤 약 100 · 200ms 스크린샷 2장 · reduced-motion 에뮬레이션 | 업로드 모달 | background-color 0.3s · 닫는 중 값이 투명 쪽으로 이동 · 동작 줄이기에서 즉시 |
| 5 | 팝오버 박스 아래 끝 대 `.reg-actions` 위 끝(열고 전환 끝난 뒤) · 375 시트 위치 | 등록 화면 1440×900 · 375 | 아래 끝 ≤ 단추줄 위 끝 · 375 위치 B0 과 같음 |
| 6 | `.btn-sm` computed 높이 | 768 터치 에뮬레이션 · 768 마우스 · 1440 마우스 | 44 · 29 · 29. 넘치는 화면은 우려 1 |
| 7 | 등록 성공 → 0.3초 안 × → 입구 다시 누름 → 단계 | `audit-upload.html` 등록 성공 분기 · 두 입구 | 두 입구 모두 첫 단계 스크린샷 |
| 8 | 5 상태: 계정 관리 모달 층 · 「불일치」 글자 · 다크 「필수」 · 열 메뉴 라벨 자간 · 닫는 중 누름 차단 | account-admin · catalog · 등록 화면 다크 · catalog 열 메뉴 · 업로드 닫는 중 | z-index 200 · 13px · 대비 ≥ 4.5 · `--tracking-label` 값 · `inert` 참 ＋ 도구 패널 누름 무반응 |
| 9 | `frontend-visual` 최종 ＋ 캡처 대조 | 부록 E | 부록 E 기준 |

## 부록 E 게이트
- 실행 = 저장소 루트에서 `COLAB_GATE_REPORT_DIR=dev-package/reports/design-fix-followups-20260925/<단계> bash gates/run.sh <게이트>` 를 하나씩. 3계수(green · red 판정 · red 준비 78)를 보고한다.

| 게이트 | B0 | L1 | L2 | E |
|---|---|---|---|---|
| `frontend-typecheck` | — | ○ | ○ | ○ |
| `frontend-test` | — | ○ | ○ | ○ |
| `frontend-fixture-reach` | — | ○ | ○ | ○ |
| `frontend-design-lint`(h 포함) | — | ○ | ○ | ○ |
| `frontend-design-lint-selftest` | — | ○(새 시험이 정본 문서를 읽는다) | — | ○ |
| `frontend-visual` | ○ URL 선언 | ○ URL 선언 | ○ URL 선언 | ○ URL 선언 |
| production build | — | — | — | ○ |

- `frontend-visual`: `COLAB_VISUAL_URLS` 선언 필수 · CSS 변경 레인에서 `COLAB_VISUAL_EXEMPT=1` 금지 · 서버가 없으면 red(준비 78)를 그대로 보고. 동작(actions)이 필요한 장면은 첫 화면만 잰다 — 그 상태는 캡처 대조와 부록 D 가 본다.
  - B0 · L1 = `frontend/scripts/visual-baseline/scenes.json` 34장면 전체 — 프리미티브 · 토큰 변경은 모든 화면에 닿는다(catalog · lab · empty · projects · project-table · project-detail · project-dialog · project-close · detail · settings · members · lab-dialog · search · search-empty · search-down · search-degraded · preview · preview-done · preview-expired · access · pending · approval · approval-dialog · lineage-picker · login · not-found · upload · upload-classify · upload-metadata · upload-link · account-admin · password-change · gnb-more · primitives)
  - L2 = upload · upload-classify · upload-metadata · upload-link · upload-register-ok(L2 가 추가)
  - E = 34 ＋ upload-register-ok = 35장면
  - 장면 이름은 `scenes.json` 에 있는 것만 쓴다. 다크는 `&theme=dark` URL 을 따로 선언할지 첫 실행에서 확인한다.
- 캡처 대조: `scenes.json` 이 바뀌어 manifest sha 가 다르므로 E 는 `visual:diff --subset` 으로 `fixfu0925-base` 대 `fixfu0925-final` 을 잰다. 새 장면은 대조 없이 존재 · 스크린샷만 보고한다.
  - 예상 변화(확실): primitives · login · password-change(V1).
  - 예상 변화(원인 = 그 장면에 보이는 비활성 단추 · V1): detail · approval-dialog · lab-dialog · upload-classify · upload-metadata · upload-link · lineage-picker · account-admin 등. 장면마다 바뀐 자리가 비활성 단추인지 보고 표에 적는다. 상세 삭제 단추 자체는 값이 같아 변화 0.
  - 그 밖 장면 변화 0 — V2(누름) · V4–V6(열린 상태) · V5(전환 고정)는 정적 캡처에 없고, V3 은 마우스 기준이다. 픽스처 팔레트 1개 → 안내 유지 · 그리기 실패 오류에 「다시 시도」 0 이므로 V7 변화도 0.
  - 보고에 「바뀐 장면 → 원인 V」 표. 원인 없는 변화가 있으면 멈춘다.
- 단계 완료 = 위 게이트 green ＋ 단계 보고(before → after · 수용 기준 · 「하지 않은 것」 · 「후속」 · 미실행).

## 부록 F `docs/design-system.md` · design-review SKILL 갱신 (L1)
- 손글 줄(표지 밖):
  - `:173` btn 행: 작은 단추 설명을 「640px 이하 또는 터치가 주 입력인 기기에서는 `--control-height`」로, 수식자에 `disabled`(opacity .5 · cursor not-allowed).
  - `:240` 편차 칸: `.detail-page .btn-danger(:disabled)` → `.detail-page .btn-danger`.
  - `:280` 합격선: 「비활성(`:disabled`) 컨트롤은 합격선 밖 — WCAG 1.4.3 · 1.4.11 비활성 예외」.
  - `:281` 누름 규칙: 「파란 채움은 primary-700」 → 「파란 채움은 primary-800」 ＋ 옆에 「비활성 = opacity .5 · cursor not-allowed」.
  - ⑦ 시각 값 표(열 `# | 항목 | 오늘 렌더 | 선택지 | 출처`) 10 행 `:310` 뒤 17 행: 빨간 삭제 단추 hover · 누름 없음 · 오늘 렌더 = 기본 = hover = 누름 · 선택지 = 새 빨간 단계 토큰 · 전역 `.btn-danger` · 출처 = 이 intent(열 구성은 기존 표를 따른다).
- 생성 표: 입력 = `tokens.css` · `primitives.css` · 게이트 목록 3개(`frontend/scripts/design-docs.mjs:40`–`44`) — `upload.css` 는 입력이 아니라 L2 는 게이트 h 에 영향 0. L1 이 두 CSS 를 바꾼 뒤 `node frontend/scripts/design-docs.mjs` 로 다시 쓴다(손으로 고치지 않는다). 예상 변화 — 토큰 매체 칸에 `(pointer: coarse)` · `.btn` 규칙 수 ＋1 · 작은 단추 매체 조건 · 입력 sha256 갱신. 확인 = `--check` 0(게이트 h).
- `.agents/skills/design-review/SKILL.md:17` 합격선 칸에 같은 비활성 예외 문장. 프론트매터 · 다른 절 불변.

## 부록 G 위험
| # | 위험 | 대응 |
|---|---|---|
| 1 | agent-browser 가 coarse pointer · reduced-motion 에뮬레이션을 지원하지 않을 수 있다 | 지원 여부를 먼저 적고, 없으면 미실행 · dev 768 터치 확인(Q7b)으로 넘긴다. 성공으로 보고하지 않는다 |
| 2 | 캡처 브라우저가 어떤 폭에서 coarse 로 잡히면 마우스 기준 장면이 바뀐다 | B0 에서 `.btn-sm` 높이로 매체 상태를 적는다 · V3 원인 변화가 나오면 멈춘다 |
| 3 | `frontend-design-lint` 가 토큰 파일의 폭 아닌 매체 블록을 받아들이는지 미확인 | L1 RED 단계에서 게이트를 먼저 돈다 · red 면 게이트 규칙 판정으로 올린다(게이트 목록 임의 수정 금지) |
| 4 | 정본 문장을 잠근 기존 시험(F-css · F-final)이 합격선 · 누름 줄 수정으로 깨질 수 있다 | 두 시험은 부분 일치다(부록 C) · `:active` 예외 문구 · `--color-surface-pressed` 보존 · 금지어 미사용 |
| 5 | 화면 층 규칙이 `.btn-strong` · `.btn-danger` 에 cursor · opacity 를 정하면 프리미티브 규칙이 진다 | L2 단언(`.btn-strong` 블록 cursor · opacity 0) · E computed 확인 |
| 6 | 640px 이하 하단 시트에서 스크롤 호출이 위치를 바꿀 수 있다 · 여는 순간 scale .96 박스로 스크롤 양이 줄 수 있다 | E 375 시트 위치 B0 대조 · 1440 은 전환 끝난 뒤 박스를 잰다 · 바뀌면 L2 로 돌린다 |
| 7 | `scenes.json` 바이트 변경으로 전체 대조가 78 | B0 기준을 변경 전에 찍고 E 는 `--subset` 대조 |
| 8 | 픽스처 분기가 기본 업로드 장면을 바꿀 수 있다 | 질의 없는 기본 동작 불변 단언 · upload 계열 캡처 변화 0 확인 |
| 9 | 주석 문장이 새 값과 어긋난 채 남는다(`primitives.css:28` 「primary 는 primary-700 유지」 · `:38` 「640px 이하는」 · `upload.css:320` · `tokens.css:6` 구조 문장) | 부록 A 에 주석 줄을 넣었다 · 레인이 값과 함께 고친다 |
| 10 | 흐린 단추가 이미 흐린 컨테이너 안이면 이중으로 흐려진다 | E 가 자리마다 적는다 · 판정 밖이면 「후속」 |
| 11 | `--control-height` 사용처 17(intent) 대 grep 18줄(조사) 불일치 | L1 보고가 목록으로 맞춘다 |
| 12 | 게이트 겹침 실행 · 레인 워크트리 기준이 main | 호스트 단독 순차 · 스폰 전 기준 커밋 확인 |
| 13 | 미리보기 원본 격자 시험 부하 대기 초과 | 재현되면 로그만 남긴다(H15) · 진단하지 않는다 |
