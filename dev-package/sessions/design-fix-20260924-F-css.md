# design-fix 20260924 · F-css(수정 레인 · CSS) 레인 보고

- spec: `dev-package/prd/specs/S-DESIGN-FIX-20260924.md` 「통합 수정」(값 19–21 · 수정 레인 표) ＋ 「확정 값」
- 결함 원문: `dev-package/sessions/design-fix-20260924-acceptance.md`(A1 A2 A3 A4 A5 A6 A7 A8 A10 A11 A12 A13 A14 A18 A21 A22)
- 기준 HEAD: `bee7786f`(`git merge-base --is-ancestor bee7786f HEAD` 종료 0) · 레인 브랜치 `worktree-wf_808554ed-fad-1`
- lifecycle task: `05fb17fac4164f4d9e24c9a5922bd049`(role lane-worker · 선언 게이트 6)
- 준비: `frontend/` 에서 `npm ci` 종료 0

## 1. 단계 · 커밋

| 단계 | 커밋 | 내용 |
|---|---|---|
| 시험 작성(RED) | `260e73c6` | 새 `frontend/test/design-fix-20260924-F-css.test.ts` 49건 · `design-fix-20260924-L1.test.ts` 5곳 갱신 · 이 보고서 골격 |
| 구현 | `b69ea79a` | CSS 7파일 · `docs/design-system.md` · `.agents/skills/design-review/SKILL.md` §0 |
| 보고 | (이 커밋) | 이 보고서 |

RED 확인(구현 전 · 두 파일): `Tests 32 failed | 72 passed (104)`. 실패 사유 — 선택자 블록 부재(`선택자 블록 수: .mainnav a.is-active:active : expected +0 to be 1`) · 값 불일치(`expected 'var(--color-gray-100)' to be 'var(--color-surface-pressed)'`) · 다크 누름 = hover(`expected '2b3745' not to be '2b3745'`) · 단축형 잔존(`expected [ Array(1) ] to deeply equal []`) · 토큰 부재(`Error: 토큰 부재(light): --color-surface-pressed` 2건 — 새 토큰이 없어서 던진 시험 안 오류이며 import 오류가 아니다). 구현 전 통과 22건(F-css 시험) = 이미 누름 ≠ hover 인 회색 누름 자리 회귀 고정(두 테마) ＋ `.lin-scope-lv` 실제 값 · 라이트 대비 6.30.

L1 시험 갱신 5곳(시험 작성 단계에서만): `.btn-primary:hover` → `.btn-primary:where(:not(:disabled)):hover` · `.btn-sm` 네 선언 → 여섯 선언 · #19 안내 줄 주석 단언(`--color-warning-600` → `.lin-scope-lv` ＋ `--color-text-muted`) · `.mainnav a:active` gray-100 → surface-pressed · `.tbl tr.clk:active td` gray-100 → surface-pressed.

## 2. before → after (항목별)

| 항목 | 파일 | before | after | 시험(F-css describe) |
|---|---|---|---|---|
| 값 19 | `shell/tokens.css` | 토큰 없음 | `--color-surface-pressed`: 라이트 `var(--color-gray-100)`(#e8ecf2) · 다크 `var(--color-gray-200)`(#45566a) | 「값 19」 3건 |
| A3 · A10 | `components/catalog/catalog.css` | `.tbl tr.clk:active td` gray-100(다크 = hover #2b3745) | `var(--color-surface-pressed)` | 「값 19 소비처」 · 「누름 ≠ hover」 |
| A3 · A10 | `shell/shell.css` | `.mainnav a:active` gray-100(다크 = hover) | `var(--color-surface-pressed)` | 같음 |
| A8 | `shell/shell.css` | 현재 메뉴는 `.mainnav a.is-active` 가 누름을 덮음 | `.mainnav a.is-active:active { background: var(--color-surface-pressed) }`(0,3,1) | 같음 |
| A2 · A5 · A13 | `shell/primitives.css` | `.btn:where(:not(.btn-primary)):hover` · `.btn-primary:hover` — 비활성 단추도 hover 색 | `.btn:where(:not(.btn-primary, :disabled)):hover` · `.btn-primary:where(:not(:disabled)):hover` — 제외를 `:where()` 안에 두어 특이도 (0,2,0) 무변 · 뒤에 선 누름 규칙이 계속 이긴다 | 「A2 · A5 · A13」 3건 · 「누름 ≠ hover」 primitives 행 |
| A4 | `shell/primitives.css` | `.btn-sm` 네 선언(display 없음 · `label.btn-sm` 글자 위로 붙음) | `display: inline-flex; align-items: center` 추가 | 「A4」 · L1 #12 |
| A6 · A7 · A14 | `shell/primitives.css` | `.chip--off { border: 1px solid var(--color-border); … }` — 값 18 을 되돌림 | `.chip--off { color: var(--color-text-muted); }`(테두리는 `.chip` 의 border-strong) | 「A6 · A7 · A14 · A12」 앞 2건 |
| A12 | `components/search/search.css` | `.search-page .chip { … border: 1px solid var(--color-border); }` | `border` 선언 삭제(프리미티브 `.chip` 이 준다) | 같은 describe 뒤 2건(화면 CSS 전수 포함) |
| A18 · 값 21 | `components/upload/upload.css` | 끌어 오는 동안 아이콘 바탕 primary-50 = 영역 바탕 | `.dropzone.is-dragover .up-drop-icon { background: var(--color-surface); }` — 아이콘 대 영역 L 1.11:1 · D 1.36:1(같음 → 다름) | 「A18 · 값 21」 3건 |
| A22 | `components/upload/upload.css` | 주석 「같은 특이도로 한 줄 더 둔다」 | 「특이도 (0,3,0) 이 위 줄 (0,2,0) 보다 높다 · 분석 장면은 같은 (0,3,0) 에 뒤」 | 「A22」 |
| A1 | `components/lineage/lineage.css` | 「안내 줄(`.lin-over-why` · `.lin-unknown-why`) warning-600 on 흰 면 5.34:1」 | 「안내 줄(`.lin-scope-lv`) `--color-text-muted` #565c63 on `--color-surface-alt` #f5f7fa = 6.30:1」 ＋ `.lin-over-why` 는 첫 줄 5.00:1 · `.lin-unknown-why` 는 거는 TSX 0건 | 「A1」 3건 · L1 #19 |
| A11 · 값 20 | `docs/design-system.md` ⑤ · `design-review/SKILL.md` §0 | 대비 4.5:1 예외 없음 | `:active` 순간 상태 예외 · 평상시·hover·초점은 그대로 · 실측 L 4.23:1 · D 4.02:1 | 「A11 · 값 20」 2건 |
| 문서 | `docs/design-system.md` ② · ⑤ | — | ② 손글 1줄(값 19) · ⑤ 누름 규칙에 surface-pressed · 생성 표 재생성(`node frontend/scripts/design-docs.mjs` · 갈림 0) | 게이트 h |

## 3. 게이트

vitest 전체: 착수 전 `Test Files 134 passed · Tests 1732 passed` → 구현 뒤 task run 안 `통과 1781건 · 실패 0건`(+49 = F-css 새 시험).

`COLAB_TASK_ID=05fb17fac4164f4d9e24c9a5922bd049 bash gates/run.sh task`(선언 게이트 6 · 저장소 루트 · 한 번에 직렬).

| run_id | 커밋 | 계 | 증거 |
|---|---|---|---|
| `bb45511d79f64531b40829c47f6ff4f2` | `b69ea79a`(보고서 기재 전) | green 6 / red(판정) 0 / red(준비) 0 | `.git/colab-harness/6c910db74ecbb4fcf03fc8a6e0e60ed3/05fb17fac4164f4d9e24c9a5922bd049/bb45511d79f64531b40829c47f6ff4f2/gate-summary.json` · 같은 run 의 `logs/` |

- 게이트별: typecheck 오류 0 · frontend-test 1781 통과 · 실패 0 · fixture-reach 도달 207 · 금지 0 · design-lint 파일 21 · 다크 누락 0(면제 6) · 색 리터럴 0 · 프리미티브 맨 정의 밖 0 · 문서 표 갈림 0 · selftest 26건 기대대로(green 6 · red 14 · red(준비) 6) · visual 페이지 13 · 13px 미만 0 · 대비<4.5 0 · 스크린샷 26장.
- `frontend-visual` 대상 = audit 빌드(`npm run audit:build` → `audit:preview --port 4187 --strictPort`) · 장면 8(primitives · catalog · search · upload · lineage-picker · gnb-more · detail · project-detail) × (라이트 · `&theme=dark`) = URL 16. **픽스처 화면**이다. 「페이지 13」은 `live_audit.sh` 의 60자 파일 이름 절단(A37)으로 다크 URL 3개가 라이트 짝과 같은 이름이 되어 덮인 결과다 — 16 URL 을 모두 열었으나 증거 파일은 13쌍이다. 증거 폴더는 `COLAB_GATE_REPORT_DIR` 미선언이라 `/tmp/frontend-visual-4PtA6B`(커밋 안 됨).
- visual 뒤 `agent-browser --session design close` 실행. 닫기 전 `fuser` 에 이 run 의 agent-browser 데몬(pid 2284797)이 호스트 뮤텍스 fd 를 쥐고 있었고(A39 결함 재현), 닫은 뒤 그 프로세스는 사라졌다.
- 이 보고서를 적은 뒤 파일 hash 가 바뀌므로 인계(`handoff --mode complete`) 증거는 이 커밋 뒤 같은 명령을 다시 돌린 run 이며, 그 run_id 는 레인 최종 메시지의 `COLAB_HANDOFF` 줄에 있다. 제품 파일은 두 run 사이에 같다.

## 4. 하지 않은 것

- **A21(업로드 `.dr-nav button:active` · `.dr-useg button:active` 에 값 19)** — 미적용. 기존 `frontend/test/design-fix-20260924-L2.test.tsx:226` · `:228` 이 두 선택자의 값을 `var(--color-gray-100)` 으로 고정한다. 이 레인의 파일 면(spec 수정 레인 표)은 기존 시험 중 `design-fix-20260924-L1.test.ts` 만 허용하므로 L2 시험을 고치지 않았고, CSS 만 바꾸면 frontend-test 가 판정 red 가 된다. spec 의 파일 면 누락(⑶ 기획이 애매) — 오케스트레이터가 L2 시험 두 줄 변경을 이 레인 또는 다른 레인에 배정해야 한다. 그때까지 다크에서 두 단추의 누름 = hover(1.00:1)가 남는다. `docs/design-system.md` ⑤ 누름 줄에 미적용을 적었다. 적용 시 알려진 부수 효과: `.dr-nav button` 테두리(border-strong · 다크 #45566a)와 누름 면이 같은 값이 된다(A21 원문 caveat).
- 실화면 증거 · 캡처 대조(spec §5 「게이트 밖 증거」) — spec F3 대로 통합 단계 몫. 누름(`:active`) · 끌어 오는 동안(`is-dragover`) 상태는 정적 audit 장면에 없으므로 `frontend-visual` 이 재지 않는다 — 이 레인의 누름·드롭 변경은 CSS 원문 계측(vitest)으로만 확인했다. 실제 브라우저 누름 검증 미실행.
- `COLAB_FIX_LANE=1` 훅 — 이 환경에서 훅에 전달할 수단이 없어 걸리지 않았다. 규율로 지켰다: 구현 커밋 `b69ea79a` 의 변경 파일은 `frontend/src/**` 7 · `docs/design-system.md` · `.agents/skills/design-review/SKILL.md` 뿐이고 `frontend/test/**` · `gates/**` · `contracts/**` 는 0(`git show --stat b69ea79a`).
- `gates/fixtures/frontend-design-lint/*` — 새 토큰은 다크 값이 있어 `same-in-dark.txt` 변경 불요. 변경 0.

## 5. 남은 위험 · 판정 밖 발견(고치지 않음)

- 파란 채움 누름 = hover(두 테마): `.btn-primary`(primary-700 · 값 10 · 14) · `.gnb-upload` · `.btn-strong`(upload.css). 확정 값이 둘 다 primary-700 이라 값 19 범위 밖이다. 누름 피드백이 보이지 않는다 — 다음 회차 판정 후보.
- `.btn-strong:hover`(`upload.css:318` · #10)에도 비활성 제외가 없다 — A2 와 같은 종류이나 수용 검토 목록에 없어 고치지 않았다. 어느 게이트도 재지 않는다 — 후속.
- `.lin-unknown-why`(`lineage.css`)는 거는 TSX 가 0건인 규칙이다 — 주석에 적었고 삭제하지 않았다. 어느 게이트도 재지 않는다 — 후속.
- `.dropzone.is-dragover .up-drop-icon` 흰 면 대 영역 primary-50 은 L 1.11:1 · D 1.36:1 — 장식 원형이라 대비 합격선 대상은 아니나 약한 구분이다(값 21 확정값 그대로).
- A37(`live_audit.sh` 60자 절단) · A39(visual 데몬의 뮤텍스 fd 상속) · `live_probe.js` 의 `@layer` 미계수 — 이 run 에서도 재현. 하네스 후속(spec 「통합 수정」 마지막 줄).
