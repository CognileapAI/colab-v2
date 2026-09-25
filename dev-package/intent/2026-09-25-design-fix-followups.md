# Intent: design-fix 20260924(PR #141) 뒤 디자인 후속 — Ted 판정 후보 · dev 실데이터 확인 · 구현 후속 · 관찰
메타 — 발의자: agent(PR #141 병합 뒤 잔여 수집 · 초안) · 작성 2026-09-25 · 승인 2026-09-25(Ted · grill-me 판정 28건)

## 문제
- PR #141(병합 커밋 `a808a56f` · 2026-09-25)이 design-review 20260924 판정 21건 · 값 17건을 반영했다. 판정표 밖 관찰과 브라우저로 확인하지 못한 항목은 PR 본문(「Ted 판정 후보」·「알려진 한계」·「배포 전에 할 일」·「하지 않은 것」)과 레인 보고(`dev-package/sessions/design-fix-20260924-*.md`)에 흩어져 있다. 정본 목록 `docs/design-system.md` ⑦ 에는 10–16 만 있다.
- 승인 intent `dev-package/intent/2026-09-25-design-fix-20260924.md` 는 「재개봉 금지: 예(판정 21건 · 값 17건)」다. 확정 값을 다시 여는 후보는 새 intent(이 문서)로만 다룰 수 있다.
- 사용자에게 보이는 결함 후보가 있다. 비활성 단추가 활성과 똑같이 보인다 · 파란·빨간 채움 단추를 눌러도 hover 와 같다 · 641–1024px 터치 기기는 29px `.btn-sm` 을 받는다.

## 원한 결과 (proposed outcome)
- (a) 후보마다 Ted 판정(채택 · 현행 유지 · 다음 회차)이 이 문서에 기록되고, 채택한 항목은 별건 spec·레인으로 넘어간다.
- (b) 확인 항목마다 dev(또는 로컬)에서 pass / fail / not-run 과 증거 경로가 남는다.
- (c) 구현 후속마다 담당 자리(다음 design-review 회차 · 별건 intent · 이 intent 의 레인)가 정해진다.
- PR #141 이후 디자인 잔여가 이 문서 한 곳에서 추적된다(PR 본문·레인 보고를 다시 뒤지지 않는다).

## 가치 가설
- Ted 는 흩어진 잔여를 한 장에서 판정해, 다음 회차 입력을 다시 모으는 비용을 줄인다.
- 사용자는 비활성·누름 표시가 구분되면 누를 수 없는 단추를 누르는 헛동작이 준다.
- 확인 방법: (a) 판정 기록 건수 · (b) 확인 행의 pass/fail · 채택 항목 별건 PR 요약의 「원한 결과 ↔ 실제 ↔ 근거」 표.

## 영향 범위
- 사용자 / 화면(판정 결과): 비활성이 될 수 있는 단추 70곳(btn 계열 58 · 로그인 제출 3 · 그 밖 9)의 비활성 모양 · 파란 채움 단추 3종의 누름 색 · 업로드 모달(닫기 확인창 · 미리보기 확대창 테두리 · 뒤판 전환 · 달력 팝오버 열 때 스크롤 · 팔레트 안내 조건 · 팔레트 재시도 단추) · 터치가 주 입력인 기기의 컨트롤 하한(`--control-height` 를 쓰는 17곳) · 계보 죽은 CSS 규칙 1개. 마우스 기기의 크기 변화 0.
- 파일 면(예정 · spec 에서 확정): 토큰·프리미티브·셸 CSS(`frontend/src/shell/`) · `frontend/src/auth/login.css` · 업로드 · 상세 · 대시보드 · 미리보기 · 프로젝트 · 연구실 · 계보 화면의 CSS·TSX · 시험 장면(audit 픽스처) · 정본 `docs/design-system.md`(⑤ · ⑦-17 · 합격선) · `.agents/skills/design-review/SKILL.md:17`(합격선).
- 서비스 · 스키마 · 계약: 없음(프론트 CSS·TSX·문서만).
- 계약 파괴 여부: 아니오.
- 이 intent 자체는 문서만 바꾼다. 코드 변경은 spec · 레인에서 한다.

## 제약
- 확정 값(값 1–17 · 추가 확정 값 18–21 · `dev-package/prd/specs/S-DESIGN-FIX-20260924.md`)을 다시 여는 항목은 이 intent 의 Ted 승인 뒤에만 바꾼다. 승인 intent `2026-09-25-design-fix-20260924.md` 는 고치지 않는다(ADR-0007 `docs/decisions/0007-intent-ref-trailer-and-append-only-approved-intents.md` · 줄 추가만 허용).
- 새 토큰 이름·값은 Ted 판정 뒤에만 쓴다(`.agents/skills/design-review/SKILL.md` §4).
- 새 문구(빈 팔레트 안내 등)는 기획 판정 뒤에만 쓴다(`dev-package/sessions/design-fix-20260924-F-ci.md` §8). 이번 판정은 새 문구 0이다(Q2f 기존 `UNAVAILABLE` · Q8a 기존 「다시 시도」).
- (b)-1 · (b)-2 · (b)-4 · (b)-5 의 선행 = 이 intent 의 레인이 병합된 뒤 develop 의 dev 배포(Q7a). 배포는 Ted 승인 범위이고, 배포 범위는 EC2 SHA 실측과 범위 PR 본문의 선행 절차 대조로 확인한다. PR #141 「배포 전에 할 일」의 선행 단계 = 없음(프론트 정적 빌드만 바뀜).
- dev 확인은 읽기 전용이다. (b)-3 은 로컬 장면으로 확인해 dev 제품 데이터 쓰기가 없다(Q4). 에이전트의 dev 확인은 dev 재생성 승인 계정 중 교수 계정을 쓴다(Q7b).
- 게이트는 호스트 단독 순차로 돌린다.

## 후속 목록

### (a) Ted 판정 후보
1. **버튼 계열 비활성 스타일 없음** — `.btn`·`.btn-strong`·`.btn-ghost` 에 `:disabled` 규칙이 없어 비활성 단추가 활성과 똑같이 보인다(cursor pointer · opacity 1). hover 는 `:where(:not(:disabled))` 로 막혀 있다. F-ci(`PreviewPanel.tsx` 변경 커밋 `2398cd2d`·`5b51a00e` · 실브라우저 증거 커밋 `783095c7`)가 `up-preview-draw`·`up-preview-without-grid` 를 팔레트 도착 전 비활성으로 바꾸면서 보이는 빈도가 늘었다(F-ci 가 만든 결함은 아니다).
   - develop 선례 2개(서로 다름): 선례 A `frontend/src/auth/login.css:88`–`91` `.login-submit:disabled` = `--color-gray-500` 채움 · `cursor: default` / 선례 B `frontend/src/components/detail/deletion.css:41`–`44` `.detail-page .btn-danger:disabled` = `opacity: 0.5` · `cursor: not-allowed`.
   - 선택지: ⓐ 선례 A 방식 ⓑ 선례 B 방식 ⓒ 새 값(토큰 판정 필요). 전역 규칙 자리 = `primitives.css`.
   - 근거: `dev-package/reports/design-review/20260924/fix/live-ci/index.md`(fail) · `fix/live/index.md` §4-2 · PR #141 「추가 — CI 실패 대응」 알려진 한계 · `dev-package/sessions/design-fix-20260924-acceptance.md` A2·A5·A13.
2. **가운데 대화상자 그림자** — #13 적용 뒤에도 `.confirm-back .modal`(`frontend/src/components/upload/UploadModal.tsx:1882` 닫기 확인 · spec 작성 당시 `:1751`)과 `.modal.pvx`(`frontend/src/components/upload/PreviewExpandOverlay.tsx:40`)가 `--shadow-sm` 을 가진다. 판정표 밖이다.
   - 선택지: #13 과 같이 그림자 제거 · 현행 유지.
   - 근거: PR #141 「Ted 판정 후보」 · `dev-package/prd/specs/S-DESIGN-FIX-20260924.md` §2 · §7 위험 8 · `dev-package/sessions/design-fix-20260924-L1.md` §5 · 승인 intent 「미해결 질문」.
3. **업로드 모달 닫기 때 뒤판 어둡힘** — 닫기 전환 0.3초 동안 뒤판 어둡힘이 남았다가 한 번에 사라진다. 같은 0.3초 동안 `.modal-takeover` transform 아래의 `.reg-actions` 와 640px 이하 `.dr-pop` 의 fixed 기준이 모달로 바뀐다. 값 1 은 모달 본체만 다뤘다(뒤판 전환 없음 · 열기도 즉시).
   - 선택지: 뒤판 전환 추가 · 현행 유지.
   - 근거: PR #141 「알려진 한계」 · `dev-package/sessions/design-fix-20260924-L2.md` §5·§6 · `fix/live/index.md` §4-1.
4. **`.dr-pop` 1440 넘침** — 1440×900 에서 `.dr-pop` 아래 끝(1014.8px)이 뷰포트 밖으로 나가 모달 발판에 가린다. 결함 여부 판정.
   - 근거: PR #141 「알려진 한계」 · `fix/live/index.md` §4-3.
5. **503 실패 뒤 × 가 확인 없이 닫힘** — 파일을 고른 뒤 503 실패 상태에서 × 가 확인 없이 닫힌다(`hasHumanInput` 판정의 결과). 결함 여부 판정. 결함이면 별건 구현.
   - 판정: 결함 아님 · dev 재현 확인 생략(설계트리 Q2e).
   - 근거: PR #141 「알려진 한계」 · `fix/live/index.md` §4-6.
6. **빈 팔레트 문면** — 팔레트 목록이 0개여도 「…받은 목록을 표시하고 있어요」가 그대로 나온다. F-ci 는 새 문구 금지 조건이라 그대로 두었다. 기획 판정 대상.
   - 근거: `dev-package/sessions/design-fix-20260924-F-ci.md` §8.
7. **재개봉 후보 — 채움 단추 누름 = hover** — `.btn-primary`·`.btn-strong`·`.gnb-upload` 는 hover 와 누름이 모두 primary-700(1.00:1)이다. `.btn-danger`(`frontend/src/components/approval/approval.css`·`frontend/src/components/detail/deletion.css` 범위)는 screens 층 배경이 primitives `:active` 를 이겨 누름 표시가 없다(종전과 같음). `docs/design-system.md:281` 「누름 피드백 = hover 의 한 단 진한 값」과 어긋난다.
   - **확정 값 10·14·15·17 의 귀결이다. 승인 intent 가 재개봉 금지라, 바꾸려면 이 새 intent 의 승인이 필요하다.**
   - 대안 예: 값 15 대안 primary-800(흰 글자 L 7.56 · D 12.56:1).
   - 근거: PR #141 「Ted 판정 후보」 · advisor ③ 조건 4 · `fix/live/index.md` a2(fail) · `dev-package/sessions/design-fix-20260924-integration.md` 「실브라우저」·「Fable advisor ③」 ⑤ · `dev-package/sessions/design-fix-20260924-F-css.md` §5.
8. **재개봉 후보 — `.btn-sm` 터치 하한 폭 기준** — 44px 하한이 `@media (max-width: 640px)` 에만 걸린다(`frontend/src/shell/primitives.css:41`–`43`). 641–1024px 터치 기기(세로 768 태블릿)는 29px 단추를 받는다. `pointer: coarse` 는 적용하지 않았다.
   - **Ted 확정 값 11(승인 intent 「확인」 — `.btn-sm` 「29px (v2 목업값)」)의 적용 범위를 다시 여는 일이다. 바꾸려면 이 새 intent 의 승인이 필요하다.**
   - 판정: 채택(설계트리 Q3c). (b)-5 의 768 터치 확인이 44px 하한의 검증을 겸한다(Q7a).
   - 근거: PR #141 「Ted 판정 후보」 · advisor ③ 조건 5 · `dev-package/sessions/design-fix-20260924-integration.md` 「Fable advisor ③」 ④.

### (b) dev 배포 뒤 실데이터 확인
선행((b)-1 · 2 · 4 · 5) = 이 intent 의 레인 병합 뒤 develop 의 dev 배포(설계트리 Q7a · Ted 승인 범위 · EC2 SHA 실측으로 범위 확인). (b)-3 · (b)-6 은 로컬(Q4 · Q7c), (b)-7 은 닫힘(Q7d), (b)-8 은 레인 첫 단계(Q7e).
1. **(a) 창 크기를 바꾸기 전 확대** — 실제 데이터셋 미리보기에서 창 크기를 바꾸기 전에도 확대가 되는지. 픽스처에서는 리사이즈 전까지 `maxScale` 이 1 에 머물렀다(1 → 1.615). 이번 diff 는 `maxScale` 초기화를 건드리지 않았다. 재현되면 별건 구현.
   - 근거: PR #141 「배포 전에 할 일」(a) · advisor ③ 조건 2 · `fix/live/index.md` §4-4.
2. **(b) 관성 끌기 경계** — 빠르게 끌고 놓으면 미끄러지다 경계에서 넘치지 않고 서는지. 마우스·터치 기기 각 1회(휠 확대 포함). 실브라우저 계측은 개발 모드 픽스처 `audit-selected-preview.html` 에서 마우스로만 했다(audit 장면엔 `[data-zoom-scale]` 0). 터치·펜은 RTL 뿐 · 휠 확대 미계측 · StrictMode 멈춤 자리(FP-1)는 renderHook 뿐.
   - 근거: PR #141 「배포 전에 할 일」(b) · `fix/live/index.md` f·g·§4-5 · `dev-package/sessions/design-fix-20260924-L3.md`·`-F-preview.md` 「하지 않은 것」.
3. **(c) 등록 직후 닫고 다시 열기(d5 not-run)** — 등록 후 0.3초 안에 × 를 누르고 업로드를 다시 열면 ① 단계가 뜨는지. UploadEntry · 격자 반영(GridAttachEntry) 두 경로. 근거는 jsdom RTL 2건뿐이다.
   - 선행: 없음 — 로컬 픽스처 장면으로 확인, dev 쓰기 0(설계트리 Q4).
   - 근거: PR #141 「배포 전에 할 일」(c) · `fix/live/index.md` d5 · `dev-package/sessions/design-fix-20260924-F-int.md` §2·§6.
4. **dragover 드롭 영역 모양(#4 · 값 21)** — 파일을 끌어 오는 동안 드롭 영역 모양. agent-browser 에 OS 파일 끌기가 없어 Ted 수동 확인. 현재 근거 = RTL(`is-dragover`) · CSS 단언.
   - 근거: PR #141 「배포 전에 할 일」 · spec §4 · `fix/live/index.md` h(not-run).
5. **루트 글자 ≠16px 1회 · 폭 768px 터치 1회** — rem 토큰(#8)과 px 고정 높이 상자의 조합. 잘릴 수 있는 상자: `.btn` 40px(`height: 32px` 보다 `min-height: var(--control-height)` 가 이긴다) · `.btn-sm` 29px · `.chip` 24px · `.dr-cal-d` 32px. 16px 루트에서 픽셀이 바뀌지 않는 것만 확인했다. 결과는 (c)-3 별건 intent 의 입력이고, 768 터치는 Q3c 44px 하한의 검증을 겸한다(Q7a).
   - 근거: PR #141 「배포 전에 할 일」·「알려진 한계」 · spec §7 위험 1 · `dev-package/sessions/design-fix-20260924-L1.md` §6.
6. **재지 못한 상태** — 여는 장면이 없어 캡처·실브라우저 모두 재지 못했다: #14 계정 관리 모달 층 200(관리자 계정 필요) · #16 「불일치」 13px · #17 다크 「필수」 표식 · #7 `.colmenu` 라벨 자간 · 닫는 중 모달 안 도구 패널 누름 차단(`inert` · A17 · jsdom 은 `inert` hit-test 를 계산하지 않음).
   - 선택지: dev 에서 눈으로 확인 · 캡처 장면 보강(하네스 intent `2026-09-25-harness-design-round-residuals.md` H11)으로 대체.
   - 근거: PR #141 「하지 않은 것」 · `fix/capture-diff.md` §6 · `dev-package/sessions/design-fix-20260924-F-upload.md` §6.
7. **(로컬) 캡처 잔차 3건(추정 · 브라우저 미확인)** — upload-metadata 768 입력칸 모서리 11px · detail 1440 단추 모서리 12px · upload-link 768 입력칸 경계. 모두 #12 배치 이동 옆의 채널 ±1–2 차이라 원인을 추정만 했다. 전체 캡처 세트 `frontend/.visual/fix0924-{base,final,report}`(무시 파일)는 통합 워크트리와 함께 지워져 0개다(설계트리 Q7d 닫힘).
   - 근거: PR #141 「검증」 캡처 대조 「잔차」 · `fix/capture-diff.md` §5.
8. **(로컬) 병합 트리의 `frontend-visual` 재계측 없음** — PR #141 의 `frontend-visual` green 은 `407fbcab` 기준 run `fd95a6a1` 이다. F-ci 뒤 로컬 run `18ea79f9`(커밋 `2398cd2d`)는 4게이트(typecheck · test · fixture-reach · design-lint)이고, CI 는 `frontend-visual-selftest` 만 돈다. F-ci 는 `PreviewPanel.tsx` 에 disabled 속성만 넣어(CSS 0) 판정이 바뀔 가능성은 낮지만, 「최종 트리 `frontend-visual` green」을 주장할 근거는 없다.
   - 선행: 주 체크아웃 develop pull · A37 우회(`theme=dark` URL 별도 선언).
   - 근거: `dev-package/sessions/design-fix-20260924-F-ci.md:77` · `dev-package/sessions/design-fix-20260924-integration.md` 「게이트」 · `.github/workflows/ci.yml:763`.

### (c) 구현 후속
1. **#21 `routes/**` 집행(다음 회차)** — Ted 가 이미 ⓐ(다음 회차 `routes/**` 담당 레인에 재판정 배정)로 판정했다. 판정 항목이 아니라 **다음 회차 집행 항목**이다. 대상 = `pd-closedbar`·`pd-linkempty`(ProjectDetailPage) · D15 `NotFoundPage.tsx:12` `<Link>` · 실화면 D23(로컬 스택)과 함께. 입력 자리 = 다음 회차 `.agents/skills/design-review/SKILL.md` §0 「이월·판정 대기」.
   - 근거: `dev-package/sessions/design-review-20260924.md` §7 #21(ⓐ) · §11 · spec §2 #21 · `dev-package/sessions/design-fix-20260924-L1.md` §5.
2. **팔레트 조회 실패 뒤 재조회 경로 없음** — `useEffect([source])` 1회뿐이다. 실패하면 단추는 비활성으로 남고 오류 문면만 보인다. 원래 동작이며 F-ci 범위 밖이지만, F-ci 가 단추를 비활성으로 바꾸면서 막힌 상태가 더 뚜렷해졌다. 재시도 UX 판단이 선행.
   - 근거: `dev-package/sessions/design-fix-20260924-F-ci.md` §8.
3. **남은 px 글자 크기 리터럴 194건 → rem** — #8 ⓐ 는 `--text-*` 6개만 바꿨다(「나머지 px 리터럴은 별건」). px 고정 높이 상자와의 조합도 함께 다룬다. 선행: (b)-5 결과 · Ted 착수 승인.
   - 근거: `dev-package/sessions/design-review-20260924.md` §7 #8 · spec §2 「그 밖」 · 승인 intent 「범위 밖」.
4. **`.lin-unknown-why` 죽은 규칙 · A30 시험 제목** — `frontend/src/components/lineage/lineage.css:266` `.lin-unknown-why` 는 거는 TSX 가 0건이다(주석 `:166` 에만 적고 지우지 않음 · 재는 게이트 없음). A30 시험 제목 「16ms 마다 1px 씩」이 실제 이동(11·1·1px)과 다르다(단언은 실제 값으로 계산되므로 제목만 고친다).
   - 근거: PR #141 「알려진 한계」 · `dev-package/sessions/design-fix-20260924-F-css.md` §5 · `-acceptance.md` A1 · `-F-preview.md` §5.
5. **`dataset-preview` 시험 부하 시 대기 초과(원인 미진단)** — 부하가 걸리면 `frontend/test/dataset-preview-source-grid.test.tsx` 의 `findByTestId('preview-map')` 이 1000ms 를 넘긴다 · 합친 트리 unhandled error 1. 단독 실행과 최종 run 은 green 이다. 게이트에서는 `frontend-test` red 로만 드러나 flake 와 구분되지 않는다. 부하 재현 측정이 먼저다.
   - 근거: `dev-package/sessions/design-fix-20260924-F-upload.md` §5·§6 · `-acceptance.md` 머리(병합 검사) · PR #141 「알려진 한계」 마지막 줄.
6. **포인터 끌기 경계(수용된 작은 손실)** — `setPointerCapture` 가 NotFoundError 외 이유로 던지면 그 끌기가 시작되지 않는다 · 두 번째 포인터는 `pointerId` 로만 무시(`isPrimary` 미사용 — jsdom 기본값이 false 라 시험이 모두 깨짐) · 첫 포인터의 up/cancel 이 끝내 오지 않으면 다른 포인터가 계속 무시된다 · `settled` 를 한 프레임 늦게 읽어 빈 프레임 1개가 더 돈다 · StrictMode rebase 경로 시험 없음. 선행(권장): (b)-2 터치 결과를 보고 필요하면 별건.
   - 근거: PR #141 「알려진 한계」 · `dev-package/sessions/design-fix-20260924-F-int.md` §6 · `-F-preview.md` §5 · 수정 라운드 「하지 않은 것」.
7. **「완료된 닫기」 경계** — 데이터셋 생성 뒤 대표 이미지 실패로 남은 모달을 사람이 닫으면(「나가기」 포함) 미완 세션으로 보아, 다시 열 때 되살아난다. `useUploadModalPresence` 없이 `open` 만 되돌리는 새 부모는 끝난 모달을 되살린다(현재 부모 2곳은 이 hook 을 쓴다). F-int 가 재시도 입력을 보존하려고 정한 경계이므로, 새 부모를 추가할 때 가드하거나 모달 쪽에서 completed 를 거르는 구현 후속으로 둔다.
   - 근거: PR #141 「알려진 한계」 · `dev-package/sessions/design-fix-20260924-F-int.md` §2·§6.

### (d) 관찰(차단 아님)
Ted 가 확정한 값의 귀결이다. 판정 항목이 아니며, 다시 보려면 새 intent 가 필요하다.
- **약한 구분 3건** — 값 19: 다크 `.dr-nav button` 누름 중 테두리 = 누름 면(#45566a) · 값 18: 라이트 `.chip--off` 윤곽 대 페이지 1.23:1 · 값 21: 드롭 아이콘 원 대 영역 L 1.11 / D 1.36:1. 장식·상태 경계라 대비 합격선 대상이 아니고, 재는 게이트도 없다.
  - 근거: PR #141 「알려진 한계 · 관찰(차단 아님)」 · spec 값 18(:247) · 추가 확정 값 19–21(:379–383) · `dev-package/sessions/design-fix-20260924-F-final.md` §5 · `fix/live/index.md` a6·c1 · `-F-css.md` §5.
- **`@starting-style` 미지원 브라우저** — Chrome<117 · Firefox<129 · Safari<17.5 는 여는 전환만 생략되고 기능은 같다.
  - 근거: PR #141 「알려진 한계」.

### (e) 기존 판정 대기(참조 · 복제하지 않음)
- `docs/design-system.md` ⑦ 의 10(화면 편차 통일)과 11–16(범위·절차)은 정본에 그대로 남는다. 1–9 는 같은 절 「닫힘 — design-review 20260924」 표로 옮겨졌다. 이 intent 는 그 행을 복제하지 않는다.
- 다음 design-review 회차의 실화면 계측 잔여와 감사 축은 `dev-package/sessions/design-review-20260924.md` §9 · §11 이 정본이다. 이 intent 는 복제하지 않는다.

## 설계트리 (grill-me 결과)
- 진행 중 — 2026-09-25 부터 가지별로 채운다. 각 가지의 「사실」은 develop `80aa95ac` 에서 조사·재계산한 값이다.
- Q1 (a)-1 비활성 단추 모양
  - 사실: `frontend/src/shell/primitives.css` 의 btn 계열 `:disabled` 규칙 0(hover 제외만 `:31`·`:35`) · btn 계열이면서 `disabled` 를 가진 단추 58(흰 단추 plain·secondary·ghost 34 · 채움 primary 14 · `.btn-strong` 8 · `.btn-danger` 2) 중 56 이 활성과 같은 모양 · 층 순서 `tokens, base, primitives, patterns, screens`(`frontend/src/shell/layers.css:1`) — `.btn-strong`(`frontend/src/components/upload/upload.css:315`)·`.btn-danger`(`deletion.css:36` · `approval.css:15`)는 screens 층에서 배경을 정해 primitives 의 배경 규칙이 닿지 않고 opacity·cursor 는 닿는다 · 비활성 모양 정본·토큰 0 · apple-design 지침에 비활성 규칙 없음 · `frontend-design-lint` 는 opacity·cursor 를 보지 않는다.
  - Q1a 구분 방식 → A 흐리게 — `opacity: .5`, `primitives.css` 규칙 하나로 58 전부 (권장안 수용)
    - 글자 대비가 라이트 2.12(파란 채움)–3.46(흰 단추) · 다크 3.24–4.61 로 내려간다. WCAG 1.4.3·1.4.11 은 비활성 컴포넌트를 제외하지만 저장소 합격선(`.agents/skills/design-review/SKILL.md:17` · 예외 = `:active` 뿐)에는 없으므로 비활성 예외 문구를 함께 넣는다.
    - 기각 — 회색 채움(`frontend/src/auth/login.css:88` 방식): gray-500 대 활성 primary-600 명도비 1.01:1(라이트·다크)이라 색상만 다르고, 흰 단추 34 의 모양이 따로 필요하며, screens 층 3파일에 반복해야 한다. 새 값: 새 토큰 이름·값 판정이 필요하다.
  - Q1b 비활성 단추 위 커서 → A `cursor: not-allowed` (권장안 수용) — 선례 `deletion.css:41` · `frontend/src/components/lineage/lineage.css:257`. 기각: `default`(선례 `login.css:88` 1곳).
  - Ted 원문(Q1a·Q1b 에 대한 답 · 2026-09-25): "권고"
  - 사실(2라운드): 비활성이 될 수 있는 단추 70 = btn 계열 58 + 밖 12(로그인 제출 `.login-submit` 3 · 비활성 모양 없음 9) · 대비 합격선은 두 곳(`.agents/skills/design-review/SKILL.md:17` · `docs/design-system.md:280`)에 같은 문장 · 감사 도구 `css_audit.py`·`live_probe.js` 는 opacity 를 읽지 않아 흐린 단추 대비를 잡지 않는다(수치는 spec·PR 에 손으로 적는다) · 캡처 변화 확실 = 프리미티브 갤러리 장면(`frontend/audit-design.tsx:175`–`179` 비활성 5개), 가능성 = 상세·업로드 계열·계보 선택 장면.
  - Q1c 로그인 제출 단추 3곳(`LoginPage.tsx:161` · `PasswordChangePage.tsx:55` · `AccountAdminPage.tsx:267`) → A 같은 모양으로 맞춘다 — `frontend/src/auth/login.css:88`–`91` 을 `opacity: .5` · `cursor: not-allowed` 로 (권장안 수용). 이유 = 회색 채움 기각 사유(명도비 1.01:1)가 같다. 로그인·비밀번호 변경 캡처가 바뀐다.
  - Q1d 상세 삭제 단추의 겹치는 규칙 `frontend/src/components/detail/deletion.css:41`–`44` → A 지운다 · `docs/design-system.md:240` 편차 칸의 `(:disabled)` 표기를 함께 고친다 (권장안 수용). 참조하는 시험·게이트 픽스처·주석 0.
  - Q1e btn 계열 밖 비활성 단추 9곳 → A 이번에 포함 — 같은 두 값을 각 화면 CSS 에 두고, 업로드 미리보기 격자 칸은 hover 에서 비활성을 뺀다 (권장안 수용). 대상: 대시보드 할 일 단추 `TodoInbox.tsx:189`·`:201`·`:204` · 미리보기 확대 단추 `PreviewZoomControls.tsx:20` · 프로젝트 모달 닫기 `ProjectCloseModal.tsx:45`·`ProjectFormModal.tsx:112` · 업로드 미리보기 격자 칸 `PreviewPanel.tsx:368` · 등록 단계 `RegisterArea.tsx:1175` · 연구실 구역 제목 `LabPage.tsx:59`. 자리마다 다른 클래스가 이미 비활성을 표현하는지는 레인이 실브라우저로 확인한다. 기각: base 층 `button:disabled` 전역 규칙(뒤 층 `cursor: pointer` 가 이겨 커서가 안 바뀐다).
  - Q1f 정본 기록 자리 → A 네 곳 — 합격선 두 곳에 「비활성(`:disabled`) 컨트롤은 합격선 밖 — WCAG 1.4.3·1.4.11 비활성 예외」 · `docs/design-system.md:173` btn 행 수식자에 `disabled` · `:281` 누름 규칙 옆에 「비활성 = opacity .5 · cursor not-allowed」 (권장안 수용). 자동 생성 표(`:198`·`:204`)는 `node frontend/scripts/design-docs.mjs` 재생성(게이트 h)을 spec 절차로 둔다.
  - Ted 원문(Q1c–Q1f 에 대한 답 · 2026-09-25): "권고대로"
  - 가정(이의 없으면 유지): 입력칸·선택칸(`.inp`·`.sel`)의 비활성 모양은 이 가지 밖이다 — 이번 판정은 단추만 다룬다.
- Q2 (a)-2 ~ (a)-6 판정 후보 다섯 항목
  - Q2a (a)-2 업로드 닫기 확인창·미리보기 확대창 그림자 → A 채택 — 그림자를 없애고 1px `--color-border-strong` 테두리(다른 가운데 대화상자 `.modal--dialog` 모양) · `frontend/src/components/upload/upload.css:310`·`:560` 2곳 (권장안 수용)
    - 사실: 두 곳만 전역 `.modal` 기본 그림자(`frontend/src/shell/primitives.css:138`)를 받고, 다른 가운데 대화상자 11개는 그림자 0 · 합격선 「카드 그림자 0」 허용 목록 밖 · 그림자 효과 라이트 1.18:1 · 다크 1.005:1 · 테두리 없이 다크 가장자리(면 대 뒤판) 1.19:1 → border-strong 으로 2.53:1(라이트 2.32:1).
    - 기각: 그림자만 제거(다크 1.19:1 유지) · 현행 유지 · 전역 `.modal` 기본값 변경(`dev-package/prd/specs/S-DESIGN-FIX-20260924.md:113` 회귀 잠금을 깬다).
  - Q2b (a)-3 업로드 모달 뒤판 어둡힘 → A 채택 — 열기·닫기 모두 뒤판 배경색 전환 · `upload.css` 3곳(`.modal-back.mb-takeover` `transition: background-color` · 닫는 중 투명 · `@starting-style` 투명) · 본체와 같은 0.3s `cubic-bezier(0.2, 0, 0, 1)`(새 값 0) · JS 변경 0 (권장안 수용)
    - 사실: 뒤판(`upload.css:9`–`17`)은 전환 없음 · 닫을 때 본체만 0.3초 흐려지고 뒤판은 언마운트 한 프레임에 사라진다 · 닫기 타이머는 본체 전환 시간만 읽는다(`UploadModal.tsx:1038`·`:1045`) · 모달이 뒤판의 자식이라 opacity 가 아니라 background-color 를 전환한다 · 동작 줄이기는 전역 규칙(`shell.css:433`–`435`)으로 즉시.
    - 근거: `.agents/skills/apple-design/SKILL.md:142`(들어온 길로 나간다) · `:212`(급격한 밝기 변화 회피). 기각: 닫기만 전환(비대칭) · 현행 유지.
  - Q2c (a)-3 전환 0.3초 동안 fixed 요소(`.reg-actions` `upload.css:611` · 640px 이하 `.dr-pop` `:682`)의 기준이 모달로 바뀌는 현상 → A 그대로 둔다 (권장안 수용). 사라지는 중인 모달과 함께 움직이고(900px 높이에서 최대 27px), 닫는 중 뒤판은 이미 누름을 통과시킨다. 기각: transform 을 빼고 opacity 만(열고 닫는 이동을 잃는다).
  - Q2d (a)-4 1440×900 `.dr-pop` 가림 → A 결함 · 열 때 팝오버가 보이도록 본문을 스크롤(가장 가까운 위치 · 하단 단추줄 여백 포함) · TSX 1파일 · 모양·값 변화 0 (권장안 수용)
    - 사실: 아래 끝 1014.8px(549.8 + 465 · `dev-package/reports/design-review/20260924/fix/live/index.md` §3-e) · 900 높이에서 하단 단추줄(약 65px · 계산값) 아래 약 180px 가려 「적용」 단추가 스크롤 전에 안 보인다 · 위로 뒤집어도 −11.8px · 앱의 팝오버는 위치 계산 없음(640px 이하만 하단 시트) · 스크롤하면 보인다는 실측(§4-3).
    - 기각: 높이 상한·내부 스크롤(900 에서 약 285px) · 낮은 화면 하단 시트(데스크톱 모양 변경) · 결함 아님.
  - Q2e (a)-5 파일 고른 뒤 503 실패에서 × 확인 없이 닫힘 → A 결함 아님 · 현행 유지 · dev 재현 확인 생략 (권장안 수용). 근거: 확인 조건 = 제출 중 · 만든 데이터셋 · 사람이 적은 입력(`UploadModal.tsx:786`·`:1020`) · 기획 `dev-package/prd/PRD-260905-적용전기획.md:411`(PRD-14)·`:821`(PRD-34) 「파일만 올림 → 닫기 → 되묻지 않는다」 · 시험 `frontend/test/close-guard-20260905.test.tsx:181`. 503 이면 파일도 올라가지 않아 잃을 입력이 없다.
  - Q2f (a)-6 빈 팔레트 문면 → A 채택 — 안내(`PreviewPanel.tsx:519`–`523`) 조건을 「1개 이상이면서 3개가 아님」으로 좁히고, 0개면 조회 실패와 같이 기존 `UNAVAILABLE`(`:36` 「지금 미리보기를 만들 수 없어요. 잠시 뒤 다시 시도해 주세요.」)만 보인다 · 새 문구 0 (권장안 수용)
    - 사실: 지금은 0개일 때도 「…받은 목록을 표시하고 있어요」가 나오고, 조회 실패(`:164`–`169`) 때는 이 문장과 `UNAVAILABLE` 이 함께 나온다 · 상세 페이지(`DatasetPreviewSection.tsx:313`)는 0개면 안 낸다. 「다시 시도」 경로 없음은 (c)-2 에서 따로 다룬다.
  - Ted 원문(Q2a–Q2f 에 대한 답 · 2026-09-25): "싹다 권고대로"
- Q3 (a)-7 · (a)-8 확정 값 재개봉 후보 — 이 intent 의 승인으로 연다(승인 intent `2026-09-25-design-fix-20260924.md` 는 고치지 않는다 · ADR-0007)
  - 비교 근거: Artifact 「CoLAB 단추 비교판」 https://claude.ai/artifact/XP7bJ4CXnafAEJYjo3dfaY (비공개 · 토큰 값 그대로 · 라이트/다크 · 실제 px).
  - Q3a (a)-7 파란 채움 단추(`.btn-primary` · `.btn-strong` · `.gnb-upload`) 누름 → A `--color-primary-800`(라이트 `#0b4eb6` · 다크 `#d4e7ff` · 기존 토큰) · 선언 3곳 `frontend/src/shell/primitives.css:36` · `frontend/src/components/upload/upload.css:321` · `frontend/src/shell/shell.css:249` + `docs/design-system.md:281` 문구 (권장안 수용)
    - 사실: 지금 hover = 누름 = primary-700(1.00:1). hover → 누름 명도비 ⓐ 라이트 1.38 · 다크 1.24(기본 → hover 1.10 · 1.18) · 흰 글자 대비 7.56 · 12.56. 정본 `:281` 은 「누름 = hover 의 한 단 진한 값」과 「파란 채움은 primary-700」이 함께 있어 스스로 어긋났다.
    - 다시 여는 확정 값: 누름을 정한 값 14·15·17 의 파란 채움 부분(값 15 대안 = primary-800). 기각: 현행 유지 + 예외 문구.
  - Q3b (a)-7 빨간 삭제 단추(`.detail-page .btn-danger` · `.approval-dialog .btn-danger`) hover·누름 없음 → A 다음 디자인 리뷰 회차 (권장안 수용). 이유: 빨간 채움 토큰이 한 단계뿐(`#a3222b` · `#ffadb6`)이라 새 토큰 이름·값 판정과 전역 `.btn-danger` 여부(`deletion.css:28`–`35` 주석)가 함께 걸린다. 입력 자리 = 다음 회차 `.agents/skills/design-review/SKILL.md` §0 「이월·판정 대기」. 기각: 이번에 새 토큰 · 관찰만.
  - Q3c (a)-8 작은 단추 터치 하한 → A 터치가 주 입력인 기기(`pointer: coarse`)에서 `--control-height` 44px — `frontend/src/shell/tokens.css` 에 별도 `@media (pointer: coarse)` 블록(여백 토큰은 건드리지 않는다) + `primitives.css:41` 조건에 `(pointer: coarse)` 추가 · 새 값 0 (권장안 수용)
    - 사실: `.btn-sm` 16개 파일 59회 · `pointer: coarse` 선례 0 · 640px 초과 `--control-height` 40px(`tokens.css:121`) · 이 토큰을 쓰는 17곳이 터치 기기에서 40 → 44px(입력칸 · 기본 단추 · 닫기 × `.pj-x` 40 → 44 등). 마우스 기기 변화 0 · 29px 확정 값 유지.
    - 다시 여는 확정 값: 값 11 의 적용 범위(폭 640px 이하 → 폭 640px 이하 또는 터치 기기). 태블릿 폭 배치 변화는 spec 검증 항목(터치 에뮬레이션 768 캡처)으로 둔다. 기각: 작은 단추만(태블릿 40px) · 768 실기기 뒤 재판정.
  - Ted 원문(Q3a–Q3c 에 대한 답 · 2026-09-25): "비교 보여줘 판단하기헴들다" → 비교판 게시 뒤 "권고대로"
- Q4 (b)-3 등록 직후 0.3초 안에 닫고 다시 열기 확인의 자리 → A 로컬 실브라우저 장면 추가 · dev 쓰기 0 (권장안 수용)
  - 방법: 픽스처에 등록 성공 응답과 실제 닫기 부모(`useUploadModalPresence`)를 둔 시험 장면을 만들고 agent-browser 로 UploadEntry · GridAttachEntry 두 경로를 잰다. 회귀 캡처로 남긴다. 하네스 intent `2026-09-25-harness-design-round-residuals.md` H11(캡처 장면 보강)과 겹치는 부분은 그 intent 와 대조해 한쪽에만 둔다.
  - 사실: 지금 로컬 픽스처는 등록이 실패하고 닫기 부모가 비어 등록 성공에 닿지 못한다(`dev-package/reports/design-review/20260924/fix/live/index.md:35`·`:78`) · UI 삭제는 데이터셋 묘비 행 · 활동 행 · 감사 행을 남긴다(`services/core-api/src/colab_core/app/routes/deletion.py:164`–`210`) · 행 삭제는 `services/core-api/ops/purge_datasets.py` 뿐(계획 행 + 명시 GO · `.agents/rules/deploy.md:40`–`42`) · dev 재생성 상시 승인은 빈 dev 만(`.agents/skills/dev-reseed/SKILL.md:113`).
  - 기각: dev 쓰기 + UI 삭제(묘비 잔존 · 다음 재생성 정지 가능) · dev 쓰기 + 재생성 정리(실행마다 GO·토큰) · dev 쓰기 + purge.
  - Ted 원문(Q4 에 대한 답 · 2026-09-25): "권고대로"
- Q5 `docs/design-system.md` ⑦ 판정 대기 목록에 올릴 범위 → A 시각 값 표에 1행만 — 17 · 빨간 삭제 단추 hover · 누름 없음(오늘 렌더 = 기본 = hover = 누름 · 선택지 = 새 빨간 단계 토큰 · 전역 `.btn-danger` · 출처 = 이 intent) · 레인 보고 「후속」 절에도 적는다 (권장안 수용)
  - 사실: ⑦ 은 시각 값 10 · 범위·절차 11–16 · 닫힘 1–9 · 다음 번호 17(`docs/design-system.md:302`–`337`) · 다음 design-review 회차의 이월 입력은 직전 audit/fix 산출물의 「하지 않은 것」·「후속」 절이다(`.agents/skills/design-review/SKILL.md:21` — ⑦ 을 직접 읽지 않는다). 판정 후보 8 중 채택 6 · 결함 아님 1 · 다음 회차 1.
  - 채택한 규칙(비활성 모양 · 누름 primary-800 · 터치 하한)은 레인이 정본 ⑤ 에 적으므로 ⑦ 에 겹쳐 적지 않는다. 기각: ⑦ 에 올리지 않음(정본에서 안 보임) · 8건 모두(이 intent · spec · ⑤ 와 세 겹).
  - Ted 원문(Q5 에 대한 답 · 2026-09-25): "이것도 권고대로"
- Q6 (c)-3 남은 px 글자 크기 리터럴 → rem → A 별건 intent (권장안 수용). dev 「루트 글자 ≠16px」 확인((b)-5) 뒤 리터럴 전환과 px 고정 높이 상자(`.btn` 40(`min-height`) · `.btn-sm` 29 · `.chip` 24 · `.dr-cal-d` 32) 처리를 함께 판정한다. 이 intent 의 레인은 판정 항목만 다룬다.
  - 사실: `font-size: Npx` 리터럴 193곳 · CSS 16파일(업로드 47 · 프로젝트 31 · 상세 21 …) — 194 는 병합 전 수치(`.lvl-mismatch` 1곳 토큰화) · 검색 px 폴백 11 · `shell/shell.css:431` `max(16px, 1em)` 1 · 16px 루트에서 N/16 rem 은 픽셀 변화 0 · 글자 크기 리터럴을 재는 게이트 없음(`docs/design-system.md:300`) · 지난 판정 #8 ⓐ = 토큰 6개만(`dev-package/sessions/design-review-20260924.md:300`–`302` · `:370`).
  - 기각: 이번에 기계 전환(잘림 위험 그대로) · 이번에 전환 + 토큰화 + 게이트 조건.
  - Ted 원문(Q6 에 대한 답 · 2026-09-25): "궏고대로"
- Q7 (b) 확인의 시점 · 수행자 · 로컬 항목
  - Q7a dev 배포 시점 → A 이 intent 의 레인 병합 뒤 1회 배포하고 (b)-1 · (b)-2 · (b)-4 · (b)-5 를 확인한다 (권장안 수용). 배포는 Ted 승인 범위이고, 실측 EC2 SHA 와 범위 PR 본문의 선행 절차 대조를 먼저 한다. (b)-5 의 768 터치는 Q3c 44px 하한의 검증을 겸한다. 기각: 지금 develop 배포(배포 2회).
  - Q7b dev 확인 수행자 → A 나눈다 — 에이전트는 agent-browser 로 마우스 · 휠 확대 · 루트 글자 변경 · 768 터치 에뮬레이션을 확인하고 증거를 남긴다(dev 재생성 승인 계정 중 교수 계정 사용 허용). Ted 는 실제 터치 기기 끌기((b)-2)와 OS 파일 끌어 놓기((b)-4)를 한다. 로그인이 막히면 에이전트 몫도 Ted 체크리스트로 넘긴다 (권장안 수용). 기각: Ted 전부 수동.
  - Q7c (b)-6 재지 못한 상태 5개(계정 관리 모달 층 200 · 「불일치」 13px · 다크 「필수」 표식 · `.colmenu` 라벨 자간 · 닫는 중 `inert` 누름 차단) → A 이 intent 의 레인에서 로컬 픽스처로 상태를 열어 agent-browser 1회 계측 · 영구 캡처 장면 여부는 하네스 intent H11 판정에 맡긴다 (권장안 수용). 기각: dev 눈 확인 · H11 로 넘김.
  - Q7d (b)-7 캡처 잔차 3건 → A 닫는다 — 사유: 대조 캡처 세트 `frontend/.visual/fix0924-*` 가 통합 워크트리와 함께 지워져 0개 · 채널 ±1–2 추정 · 이 레인의 캡처 대조에서 같은 장면에 차이가 다시 나오면 그때 본다 (권장안 수용). 기각: PR #141 전후 캡처 재촬영.
  - Q7e (b)-8 병합 트리 `frontend-visual` 재계측 → A 이 intent 의 레인 첫 단계에서 develop HEAD 기준 `frontend-visual` 을 돌려 기준으로 남긴다(재계측을 겸한다) (권장안 수용). 기각: 측정 레인 별도.
  - Ted 원문(Q7a–Q7e 에 대한 답 · 2026-09-25): "권고대로"
- Q8 (c) 구현 후속의 담당 자리
  - (c)-1 `routes/**` #21 집행 → 기존 판정 그대로 — 다음 design-review 회차의 `routes/**` 레인 · 입력 자리 = `.agents/skills/design-review/SKILL.md` §0 「이월·판정 대기」(Ted 기판정 ⓐ · `dev-package/sessions/design-review-20260924.md` §7 #21). 이번에 묻지 않았다. (c)-3 은 Q6(별건 intent).
  - Q8a (c)-2 업로드 미리보기 팔레트 조회 실패 뒤 재조회 경로 없음 → A 이 intent 의 레인에서 오류 문장 옆 작은 단추 「다시 시도」(기존 문구 `frontend/src/components/detail/SearchEvidenceEditor.tsx:209` 재사용 · 새 문구 0) · 누르면 팔레트 목록을 다시 조회 (권장안 수용). 기각: 별건 intent(재시도 UX) · 현행 유지.
  - Q8b (c)-4 `frontend/src/components/lineage/lineage.css:266` `.lin-unknown-why`(쓰는 곳 0) 삭제 · 시험 제목 「16ms 마다 1px 씩」을 실제 이동(11·1·1px)에 맞게 고침(단언은 그대로) → A 이 intent 의 레인 (권장안 수용). 기각: 다음 회차.
  - Q8c (c)-5 `frontend/test/dataset-preview-source-grid.test.tsx` 부하 시 대기 초과(원인 미진단) → A 하네스 intent `2026-09-25-harness-design-round-residuals.md` 에 H15 로 추가(따질 것 · 모을 증거 = 부하 재현 측정) · 이 레인은 재현되면 로그만 남긴다 (권장안 수용). 이유 = 게이트 판정이 flake 와 결함을 가르지 못하는 문제. 기각: 이 레인에서 진단 · 별건 제품 intent.
  - Q8d (c)-6 포인터 끌기 경계(수용된 작은 손실 5개) → A dev 실제 터치 끌기 확인((b)-2 · Q7b Ted 몫) 결과 뒤 판정 — 결함이면 별건, 아니면 「수용된 손실」로 닫는다 (권장안 수용). 기각: 이 레인에서 가드 보강.
  - Q8e (c)-7 「완료된 닫기」 경계 → A 경계 유지 · `UploadModal` 머리 주석에 「새 부모는 `useUploadModalPresence` 필수」 명시 (권장안 수용). 사실: 부모 2곳 `frontend/src/components/upload/UploadEntry.tsx:94` · `GridAttachEntry.tsx:55` 모두 훅을 쓴다. 기각: 모달 쪽 완료 세션 거르기(대표 이미지 실패 뒤 재시도 입력 보존 의도를 바꾼다) · 기록 없음.
  - Ted 원문(Q8a–Q8e 에 대한 답 · 2026-09-25): "권로대로"
- 처분 요약(후속 목록 항목 → 처분 → 자리)

  | 항목 | 처분 | 자리 |
  |---|---|---|
  | (a)-1 비활성 단추 | 채택 — `opacity: .5` · `cursor: not-allowed` · 70곳 · 정본 4곳(Q1a–Q1f) | 이 intent 의 레인 |
  | (a)-2 가운데 대화상자 그림자 | 채택 — 그림자 0 · 1px `--color-border-strong`(Q2a) | 레인 |
  | (a)-3 업로드 모달 뒤판 | 채택 — 열기·닫기 배경색 전환(Q2b) · fixed 기준 변화는 유지(Q2c) | 레인 |
  | (a)-4 `.dr-pop` 1440 가림 | 채택 — 열 때 본문 스크롤(Q2d) | 레인 |
  | (a)-5 503 뒤 × | 결함 아님 · 현행 유지(Q2e) | 닫힘 |
  | (a)-6 빈 팔레트 문면 | 채택 — 조건 좁힘 · 0개 = `UNAVAILABLE`(Q2f) | 레인 |
  | (a)-7 파란 채움 누름 | 채택 — primary-800(Q3a) | 레인 |
  | (a)-7 빨간 삭제 단추 | 다음 회차 · ⑦-17(Q3b · Q5) | 다음 design-review · ⑦ 행은 레인이 추가 |
  | (a)-8 작은 단추 터치 하한 | 채택 — `pointer: coarse` 44px(Q3c) | 레인 |
  | (b)-1 확대 · (b)-2 관성 끌기 | dev 확인 — 에이전트 마우스·휠 · Ted 실제 터치(Q7a · Q7b) | 레인 병합 뒤 dev 배포 |
  | (b)-3 등록 직후 닫고 열기 | 로컬 실브라우저 장면(Q4) | 레인 |
  | (b)-4 dragover 모양 | Ted 수동(Q7b) | dev 배포 뒤 |
  | (b)-5 루트 글자 ≠16px · 768 터치 | 에이전트 에뮬레이션(Q7b) · Q3c 검증 겸함 · 결과는 px 전환 별건 intent 입력 | dev 배포 뒤 |
  | (b)-6 재지 못한 상태 5 | 로컬 1회 계측(Q7c) | 레인 |
  | (b)-7 캡처 잔차 3 | 닫힘 — 증거 소실(Q7d) | 닫힘 |
  | (b)-8 병합 트리 `frontend-visual` | 레인 첫 단계 기준 측정(Q7e) | 레인 |
  | (c)-1 `routes/**` #21 | 다음 회차(기판정) | 다음 design-review |
  | (c)-2 팔레트 재시도 | 채택 — 「다시 시도」(Q8a) | 레인 |
  | (c)-3 px → rem | 별건 intent(Q6) | (b)-5 뒤 |
  | (c)-4 죽은 규칙 · 시험 제목 | 채택(Q8b) | 레인 |
  | (c)-5 시험 대기 초과 | 하네스 intent H15(Q8c) | 하네스 intent |
  | (c)-6 포인터 끌기 경계 | (b)-2 결과 뒤 판정(Q8d) | dev 배포 뒤 |
  | (c)-7 완료된 닫기 경계 | 유지 · 주석(Q8e) | 레인 |

## 미해결 질문
- 없음

## 범위 밖 (명시 제외)
- 승인 intent `2026-09-25-design-fix-20260924.md` 의 판정 21건 · 값 17건 자체의 변경. 다시 여는 것은 파란 채움 누름(Q3a)과 작은 단추 하한의 적용 범위(Q3c)뿐이다.
- 빨간 삭제 단추 hover · 누름(Q3b) — 다음 design-review 회차(⑦-17).
- 남은 px 글자 크기 리터럴 전환(Q6) — 별건 intent.
- `routes/**` 단추 편차 #21((c)-1) — 다음 design-review 회차.
- 미리보기 시험 대기 초과 진단(Q8c) — 하네스 intent H15.
- 입력칸 · 선택칸(`.inp` · `.sel`)의 비활성 모양(Q1 가정).
- 하네스 잔여 — `dev-package/intent/2026-09-25-harness-design-round-residuals.md`.
- 워크트리 · 브랜치 · 임시물 정리.
- `docs/design-system.md` ⑦ 10–16 의 판정(정본에서 진행).

## 확인
- 프론티어 공집합 확인: 2026-09-25 — Q1–Q8(가지 판정 28건) 완료 · 미해결 질문 0
- Ted 확인 문장(원문 그대로): "좋아 확인완료 스펙가자"
- 재개봉 금지: 예(판정 28건 · 설계트리 Q1a–Q8e). 바꾸려면 새 intent 로만 연다(ADR-0007 · 이 문서는 이제 줄 추가만 허용).

## 참조
- PR #141 — 병합 커밋 `a808a56f`(2026-09-25) · 본문 사본 `~/.claude/pr-bodies/PR-BODY-design-fix-20260924.md`(저장소 밖)
- 승인 intent: `dev-package/intent/2026-09-25-design-fix-20260924.md`
- spec: `dev-package/prd/specs/S-DESIGN-FIX-20260924.md`
- 판정표: `dev-package/sessions/design-review-20260924.md`(§7 · §9 · §11)
- 레인 보고: `dev-package/sessions/design-fix-20260924-{integration,acceptance,L1,L2,L3,F-css,F-upload,F-preview,F-final,F-int,F-ci}.md`
- 증거: `dev-package/reports/design-review/20260924/fix/{live,live-ci}/index.md` · `fix/capture-diff.md` · `fix/build-log.txt`
- 정본: `docs/design-system.md` ⑤ · ⑦
- 비교판(Q3 근거): https://claude.ai/artifact/XP7bJ4CXnafAEJYjo3dfaY (비공개)
- 결정: 신규 legacy 결정번호 발급 없음(AGENTS.md).
