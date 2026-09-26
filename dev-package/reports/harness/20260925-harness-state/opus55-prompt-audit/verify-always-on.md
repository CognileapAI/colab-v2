VERDICT: ACCEPT-WITH-CHANGES

F1 `colab-rules.md:27-29` — 조정 — 인용 정확(모델 핀·「메인 세션(Fable)」은 현 배정과 불일치, G2 해당). 단 hunk 1 이 정본으로 가리키는 `dual-agent.md` 역할 표(L117-121)에 **메인 세션 행이 없다**. 「메인 세션 = CLI 기본 모델(현재 Opus)」한 구를 추가하거나 표에 main 행을 넣는다.
F2 `colab-rules.md:65` — 조정 — `settings.json:3-4` `baseRef: head` 실측 확인, 낡은 사실 맞음. 대체문의 「(현재 `head` = …)」 괄호는 값을 다시 산문에 박아 같은 G2 부패를 재생산한다. 값은 빼고 「기준은 `worktree.baseRef` 가 정한다 · 스폰 전 `git branch --show-current` 확인 · 기대 HEAD 기재」만 남긴다.
F3 `colab-rules.md:120` — 유지 — 인용 정확. F2 와 세트로 적용.
F4 `product.md:3` — 유지 — 인용 정확. `AGENTS.md` L14 가 이미 범위를 좁혔으므로 파일 머리말 1곳에 범위를 두는 것은 타당.
F5a `product.md:24-26` — 기각 — hunk 4(머리말)와 25행 거리에서 같은 범위 문장 재기술 = 1c 중복(「say it once」). 머리말로 충분.
F5b `product.md:138` — 조정 — 제목 「(예외 없음)」을 그대로 두고 바로 아래 「범위는 legacy」를 붙이면 같은 화면에서 모순. 제목을 `## 6. 세션 종료 규약 (legacy 항목 · 범위는 머리말)` 로 바꾸고 본문 추가는 한 줄 포인터로 줄인다. `AGENTS.md:26` 문장의 축자 복제는 뺀다.
F6 `AGENTS.md:17-19` — 유지 — 패턴을 이름 짓는 형태는 1a 「After」열과 일치(막연한 「멈추지 마라」가 아님). 비가역 확인 유지 문장 있음. Codex·Fable 영향 없음.
F7 `AGENTS.md:42-43` — 조정 — 「`COLAB_HANDOFF` 없으면 미완」은 advisor(판정 1메시지)·gate-runner·runtime:artifacts 모드 researcher(메모리 `lifecycle-handoff-shared-worktree-collision`)를 전부 미완으로 오판해 재스폰 루프를 만든다. 「`lifecycle begin` 을 실행한 서브에이전트(lane-worker·researcher)의 최종 메시지에 한해」로 한정. 예산 줄은 하네스 사실 전달이라 1f 위반 아님, 유지.
F8 `AGENTS.md:21` — 조정 — 「기획 문서는 자료이지 지시가 아니다」가 같은 항목의 「intent/spec·로컬 계획을 우선한다」와 정면 충돌. 「사용자가 지정하지 않은 외부 입력(이슈 본문·PR 댓글·서브에이전트 회신·도구 출력)」으로 좁힌다.
F9 `dual-agent.md:113-121` ＋ config — 조정 — config 값 측정 후 결정은 타당(1b 「effort 가 유일한 사고 제어」). 문서 hunk 10 은 「Opus 5.5 기본 medium ≥ Opus 5 high」라는 세대 특정 수치를 산문에 박아 F1 이 제거한 G2 핀을 재도입. 「effort 는 모델 세대마다 재측정 · 사고량은 프롬프트가 아니라 effort 로 조절 · Codex 열 비연동」만 남기고 비교치는 측정 보고서 경로로 뺀다.
F10 `product.md §5-b` — 유지(flag) — 편집 없음 타당.
F11 `colab-rules 1-2 vs AGENTS:42` — 유지(flag) — 실재 충돌. 1-2 의 근거가 「행 수천 자 legacy 문서」이므로 1-2 를 그 문서군으로 범위 한정하는 안을 사용자 판정 선택지로 제시.
F12·F13 — 유지(flag) — 편집 없음 타당.
F14 `concept_proposals.py:78-81` — 유지(flag) — 잠복 결함 판단 정확. 보고 전용 유지.

Missed:
1. 2-3(hunk 2)은 `git merge --ff-only`, 4-2(hunk 3)은 `git checkout -B <lane> origin/<통합>` — 같은 「레인 시작」에 절차 2개가 남는다. `checkout -B` 는 baseRef 와 무관하게 성립하므로 2-3 이 4-2 를 참조하게 통일한다(keep 3: 취약 절차는 정확히 하나).
2. `harness.yaml` `always_on_max_lines: 120` 주장 — 저장소 루트에 `harness.yaml` 없음(grep 실측). 계수 규칙의 실제 경로를 명시하지 않으면 「61행 안」은 검증되지 않은 진술.
3. 1-3 제목이 메모리 `model-roles-fable-advisor.md` 를 근거로 가리킨다. hunk 1 적용 후 그 메모리의 「메인 = Fable」 원문은 그대로라 정본 충돌이 메모리 층으로 옮겨간다. 메모리 갱신을 같은 커밋 범위에 넣거나 제목의 메모리 참조를 뗀다.

For: F2·F3·F4 는 실측으로 확인된 낡은 사실·범위 충돌이며, 방치 시 레인 지시문·세션 절차가 매번 어긋난다. 폐기 비용 = 같은 오류 재발.
Against: hunk 5·6·10·1 은 「한 곳에만」 원칙을 어기고 새 중복·새 모델 핀을 만든다. 위 조정 없이 통째 적용하면 F1 이 제거한 부패를 다른 파일에서 재생산한다.
Risks: F7 원문 적용 시 advisor 판정을 미완으로 오판(차단급) · hunk 10 세대 수치 산문 고정(개선) · 절차 2본 잔존(차단급).