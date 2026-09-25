# Intent: design-fix 20260924(PR #141) 뒤 디자인 후속 — Ted 판정 후보 · dev 실데이터 확인 · 구현 후속 · 관찰
메타 — 발의자: agent(PR #141 병합 뒤 잔여 수집 · 초안) · 작성 2026-09-25 · 승인 미승인(초안)

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
- 사용자 / 화면: 판정 뒤에 정해진다. 후보 면 = 단추 프리미티브(`frontend/src/shell/primitives.css`) · 업로드 모달(`frontend/src/components/upload/*`) · 미리보기 끌기(`frontend/src/components/preview/*`) · 업로드 달력 팝오버 `.dr-pop` · 계보(`frontend/src/components/lineage/lineage.css`).
- 서비스 · 스키마 · 계약: 없음(프론트 CSS·TSX·문면 후보만).
- 계약 파괴 여부: 아니오.
- 이 초안 자체는 문서만 바꾼다. 코드 변경 0.

## 제약
- 확정 값(값 1–17 · 추가 확정 값 18–21 · `dev-package/prd/specs/S-DESIGN-FIX-20260924.md`)을 다시 여는 항목은 이 intent 의 Ted 승인 뒤에만 바꾼다. 승인 intent `2026-09-25-design-fix-20260924.md` 는 고치지 않는다(ADR-0007 `docs/decisions/0007-intent-ref-trailer-and-append-only-approved-intents.md` · 줄 추가만 허용).
- 새 토큰 이름·값은 Ted 판정 뒤에만 쓴다(`.agents/skills/design-review/SKILL.md` §4).
- 새 문구(빈 팔레트 안내 등)는 기획 판정 뒤에만 쓴다(`dev-package/sessions/design-fix-20260924-F-ci.md` §8).
- (b) 1–6 의 공통 선행 = develop `a808a56f` 의 dev 배포. 배포는 Ted 승인 범위이고, 배포 범위는 EC2 SHA 실측으로 확인한다. PR #141 「배포 전에 할 일」의 선행 단계 = 없음(프론트 정적 빌드만 바뀜).
- (b)-3 은 dev 에 데이터셋을 새로 등록(제품 데이터 쓰기)하므로 dev 쓰기에 대한 Ted 승인이 따로 필요하다.
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
   - 선행(권장): 픽스처 503 이 아닌 dev 실데이터에서 재현 확인.
   - 근거: PR #141 「알려진 한계」 · `fix/live/index.md` §4-6.
6. **빈 팔레트 문면** — 팔레트 목록이 0개여도 「…받은 목록을 표시하고 있어요」가 그대로 나온다. F-ci 는 새 문구 금지 조건이라 그대로 두었다. 기획 판정 대상.
   - 근거: `dev-package/sessions/design-fix-20260924-F-ci.md` §8.
7. **재개봉 후보 — 채움 단추 누름 = hover** — `.btn-primary`·`.btn-strong`·`.gnb-upload` 는 hover 와 누름이 모두 primary-700(1.00:1)이다. `.btn-danger`(`frontend/src/components/approval/approval.css`·`frontend/src/components/detail/deletion.css` 범위)는 screens 층 배경이 primitives `:active` 를 이겨 누름 표시가 없다(종전과 같음). `docs/design-system.md:281` 「누름 피드백 = hover 의 한 단 진한 값」과 어긋난다.
   - **확정 값 10·14·15·17 의 귀결이다. 승인 intent 가 재개봉 금지라, 바꾸려면 이 새 intent 의 승인이 필요하다.**
   - 대안 예: 값 15 대안 primary-800(흰 글자 L 7.56 · D 12.56:1).
   - 근거: PR #141 「Ted 판정 후보」 · advisor ③ 조건 4 · `fix/live/index.md` a2(fail) · `dev-package/sessions/design-fix-20260924-integration.md` 「실브라우저」·「Fable advisor ③」 ⑤ · `dev-package/sessions/design-fix-20260924-F-css.md` §5.
8. **재개봉 후보 — `.btn-sm` 터치 하한 폭 기준** — 44px 하한이 `@media (max-width: 640px)` 에만 걸린다(`frontend/src/shell/primitives.css:41`–`43`). 641–1024px 터치 기기(세로 768 태블릿)는 29px 단추를 받는다. `pointer: coarse` 는 적용하지 않았다.
   - **Ted 확정 값 11(승인 intent 「확인」 — `.btn-sm` 「29px (v2 목업값)」)의 적용 범위를 다시 여는 일이다. 바꾸려면 이 새 intent 의 승인이 필요하다.**
   - 선행(권장): (b)-5 「폭 768px 터치 1회」 결과를 판정 입력으로 쓴다.
   - 근거: PR #141 「Ted 판정 후보」 · advisor ③ 조건 5 · `dev-package/sessions/design-fix-20260924-integration.md` 「Fable advisor ③」 ④.

### (b) dev 배포 뒤 실데이터 확인
선행(1–6 공통) = develop `a808a56f` 의 dev 배포(Ted 승인 범위 · EC2 SHA 실측으로 범위 확인).
1. **(a) 창 크기를 바꾸기 전 확대** — 실제 데이터셋 미리보기에서 창 크기를 바꾸기 전에도 확대가 되는지. 픽스처에서는 리사이즈 전까지 `maxScale` 이 1 에 머물렀다(1 → 1.615). 이번 diff 는 `maxScale` 초기화를 건드리지 않았다. 재현되면 별건 구현.
   - 근거: PR #141 「배포 전에 할 일」(a) · advisor ③ 조건 2 · `fix/live/index.md` §4-4.
2. **(b) 관성 끌기 경계** — 빠르게 끌고 놓으면 미끄러지다 경계에서 넘치지 않고 서는지. 마우스·터치 기기 각 1회(휠 확대 포함). 실브라우저 계측은 개발 모드 픽스처 `audit-selected-preview.html` 에서 마우스로만 했다(audit 장면엔 `[data-zoom-scale]` 0). 터치·펜은 RTL 뿐 · 휠 확대 미계측 · StrictMode 멈춤 자리(FP-1)는 renderHook 뿐.
   - 근거: PR #141 「배포 전에 할 일」(b) · `fix/live/index.md` f·g·§4-5 · `dev-package/sessions/design-fix-20260924-L3.md`·`-F-preview.md` 「하지 않은 것」.
3. **(c) 등록 직후 닫고 다시 열기(d5 not-run)** — 등록 후 0.3초 안에 × 를 누르고 업로드를 다시 열면 ① 단계가 뜨는지. UploadEntry · 격자 반영(GridAttachEntry) 두 경로. 근거는 jsdom RTL 2건뿐이다.
   - **선행: dev 배포 · dev 쓰기(데이터셋 등록)에 대한 Ted 승인 · 쓰기 가능한 계정 · 시험 데이터 정리 방법.**
   - 근거: PR #141 「배포 전에 할 일」(c) · `fix/live/index.md` d5 · `dev-package/sessions/design-fix-20260924-F-int.md` §2·§6.
4. **dragover 드롭 영역 모양(#4 · 값 21)** — 파일을 끌어 오는 동안 드롭 영역 모양. agent-browser 에 OS 파일 끌기가 없어 Ted 수동 확인. 현재 근거 = RTL(`is-dragover`) · CSS 단언.
   - 근거: PR #141 「배포 전에 할 일」 · spec §4 · `fix/live/index.md` h(not-run).
5. **루트 글자 ≠16px 1회 · 폭 768px 터치 1회** — rem 토큰(#8)과 px 고정 높이 상자의 조합. 잘릴 수 있는 상자: `.btn` 32px · `.btn-sm` 29px · `.chip` 24px · `.dr-cal-d` 32px. 16px 루트에서 픽셀이 바뀌지 않는 것만 확인했다. 결과는 (a)-8 과 (c)-3 의 입력이다.
   - 근거: PR #141 「배포 전에 할 일」·「알려진 한계」 · spec §7 위험 1 · `dev-package/sessions/design-fix-20260924-L1.md` §6.
6. **재지 못한 상태** — 여는 장면이 없어 캡처·실브라우저 모두 재지 못했다: #14 계정 관리 모달 층 200(관리자 계정 필요) · #16 「불일치」 13px · #17 다크 「필수」 표식 · #7 `.colmenu` 라벨 자간 · 닫는 중 모달 안 도구 패널 누름 차단(`inert` · A17 · jsdom 은 `inert` hit-test 를 계산하지 않음).
   - 선택지: dev 에서 눈으로 확인 · 캡처 장면 보강(하네스 intent `2026-09-25-harness-design-round-residuals.md` H11)으로 대체.
   - 근거: PR #141 「하지 않은 것」 · `fix/capture-diff.md` §6 · `dev-package/sessions/design-fix-20260924-F-upload.md` §6.
7. **(로컬) 캡처 잔차 3건(추정 · 브라우저 미확인)** — upload-metadata 768 입력칸 모서리 11px · detail 1440 단추 모서리 12px · upload-link 768 입력칸 경계. 모두 #12 배치 이동 옆의 채널 ±1–2 차이라 원인을 추정만 했다. 전체 캡처 세트 `frontend/.visual/fix0924-{base,final,report}`(무시 파일)는 통합 워크트리에만 있으므로 지우기 전에 본다.
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

## 미해결 질문
- Q1 (a)-1 비활성 모양: 방식·커서는 판정 완료(설계트리 Q1a·Q1b). 남음 — 로그인 제출 단추를 같은 방식으로 맞출지 · `deletion.css:41`–`44` 의 겹치는 규칙 정리 · 합격선 비활성 예외 문구의 자리.
- Q2 (a)-2 ~ (a)-6: 항목별로 채택 · 현행 유지 · 다음 회차 중 무엇인지.
- Q3 (a)-7 · (a)-8: 확정 값을 다시 열지. 연다면 이 intent 를 승인하고 별건 spec 으로 진행한다.
- Q4 (b)-3: dev 쓰기 승인 범위와 시험 데이터 정리 방법.
- Q5 (a) 후보 중 어느 것을 `docs/design-system.md` ⑦ 정본 목록에 올릴지(문서만 · 값 무변). 지금 ⑦ 에는 10–16 만 있고, 이번 후보는 PR 본문·레인 보고·이 문서에만 있다.
- Q6 (c)-3 px 리터럴 전환을 이 intent 에서 착수할지, 별건 intent 로 뺄지.

## 범위 밖 (명시 제외)
- 승인 intent `2026-09-25-design-fix-20260924.md` 의 판정 21건 · 값 17건 자체의 변경. (a)-7 · (a)-8 만 재개봉 후보로 올린다.
- 하네스 잔여 — `dev-package/intent/2026-09-25-harness-design-round-residuals.md`.
- 워크트리 · 브랜치 · 임시물 정리.
- `docs/design-system.md` ⑦ 10–16 의 판정(정본에서 진행).

## 확인
- 프론티어 공집합 확인: (미실시)
- Ted 확인 문장(원문 그대로): (없음 — 미승인 초안)
- 재개봉 금지: 아니오(초안)

## 참조
- PR #141 — 병합 커밋 `a808a56f`(2026-09-25) · 본문 사본 `~/.claude/pr-bodies/PR-BODY-design-fix-20260924.md`(저장소 밖)
- 승인 intent: `dev-package/intent/2026-09-25-design-fix-20260924.md`
- spec: `dev-package/prd/specs/S-DESIGN-FIX-20260924.md`
- 판정표: `dev-package/sessions/design-review-20260924.md`(§7 · §9 · §11)
- 레인 보고: `dev-package/sessions/design-fix-20260924-{integration,acceptance,L1,L2,L3,F-css,F-upload,F-preview,F-final,F-int,F-ci}.md`
- 증거: `dev-package/reports/design-review/20260924/fix/{live,live-ci}/index.md` · `fix/capture-diff.md` · `fix/build-log.txt`
- 정본: `docs/design-system.md` ⑤ · ⑦
- 결정: 신규 legacy 결정번호 발급 없음(AGENTS.md).
