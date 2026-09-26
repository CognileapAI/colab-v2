VERDICT: ACCEPT-WITH-CHANGES

인용 대조: VENDORED.md:34·36·57 · design-review/SKILL.md:8·69·97 · grill-me/SKILL.md:16 — 7곳 모두 원문과 일치. `.claude/agents/researcher.md` = `model: opus`·`effort: medium`(hunk 3 전제 확인) · `measurement-lane.md` 존재. Opus 5.5 시각 근거 migration.md L2035·L2045 확인. 단 F6 의 「text-only 조기 종료」 근거는 migration.md **L1490(Fable 5.1 절)** 이고 Opus 5.5 절(L1864~)에서는 grep 으로 확인되지 않았다 — 문서 귀속이 틀렸으나 레포 실측(메모리 turn 한도 절단)이 keep list 5·11 을 채운다.

- VENDORED.md:34,36 (F1·hunk 1) — 조정 — 제목의 「Fable 5.1」은 이행 스펙(`harness-fable51-design.md`)과 묶인 **변경 이력 기록**이지 모델에 닿는 프롬프트가 아니다. 제목은 그대로 두고 항목 1 에만 이유 병기: `…지시를 뺀다(thinking 상시 모델 — Fable 5.1 · Opus 5.5 — 에서 reasoning_extraction 거절을 부를 수 있다).`
- VENDORED.md:57 vs grill-me:16 (F2·hunk 2) — 유지 — 실물과 개조표가 정반대(커밋=승인 vs 커밋≠승인). keep list 8 의 「실제로 어긋날 때만」에 해당. Opus 5.5 와 무관한 정합 수정이지만 대조 절차(L99 「목록에 없는 차이 = 결함」)를 오작동시키므로 적용.
- design-review:69 (F3·hunk 3) — 조정 — 정본 위임은 맞다. 단 (a) 「Codex 는 브리지 기본 모델…」은 미검증 주장이고 AGENTS.md 에 이미 「`.claude/agents` 의 모델·격리는 Codex 자동 미적용」이 있어 중복(정보는 한 곳) (b) `measurement-lane` 이 design-review 판정 레인에 맞는지 미확인 · 선택지 둘은 「기본 1 ＋ 탈출구 1」 위반. 대체문: `모델·effort 는 \`.claude/agents/researcher.md\` 의 기본값을 따른다. 계수·추출만인 레인은 \`model: sonnet\` 을 넘긴다.`
- design-review:97 (F4·hunk 4) — 조정 — 패턴·근거 유효(코드는 모델이 판정하는데 스크린샷만 사람에게 넘기는 비대칭 = 시각 스캐폴드). 단 §2-5 는 레인 전용 절이 아니고(주체 미지정), 「잠정 판정」은 §2-3 에 없는 새 어휘다. 기존 표 어휘로 대체: `…\`screenshot\` 순서로 찍는다. 계측한 쪽이 전후 스크린샷을 직접 보고 판정(있음/없음/[미상])과 관찰한 차이를 「근거」에 스크린샷 경로와 함께 적되, 「처리」는 **Ted 판정** 으로 둔다(즉시 수정 후보로 올리지 않는다). 스크립트는 판정하지 않는다.`
- design-review:8 (F5·hunk 5) — 유지 — 규율 두 문장은 보존, WU 번호만 제거. 행동 변화 0 · Codex 중립.
- design-review §2-2 (F6·hunk 6) — 조정 — 항목 10 은 「지시문에 반드시 넣는 것」 목록인데 뒷문장(「메인은 그것을 보고로 읽고…새 세션으로 잇는다」)은 메인 지시라 자리가 틀렸다. 분리: 항목 10 = `산출 파일을 먼저 만들고 채운다. 턴 한도에 닿으면 채운 데까지 쓰고 남은 파일 목록을 파일 끝에 적는다. 다음 단계 예고·확인 대기만 남기고 끝내는 것은 완료가 아니다.` / L69 문단 뒤 별도 1행 = `파일 없이 텍스트만 돌아온 레인은 진행 보고로 읽고, 남은 파일 목록으로 좁혀 새 세션으로 잇는다.` 근거 표기는 「Opus 5.5 문서」가 아니라 「레포 실측(turn 한도 절단) ＋ migration.md L1490」로 고친다. 적용 전 `.agents/roles/researcher.md`·`colab-v2-work/SKILL.md` 에 같은 취지 문장이 이미 있는지 grep — 있으면 포인터 1행으로 축소.
- design-review §2-2 시간 예산 (F7) — 유지(flag) — 미측정 · diff 제외 그대로.
- 대조 1행 ×5 (F8) — 기각 — migration.md L1474 「progress claims 를 tool results 에 대조시키면 조작 상태 보고가 거의 사라진다」가 **유지** 근거다. 재검 후보로도 올리지 않는다.
- agent-browser:238-240,388-395 heredoc (F9) — 유지(flag) — vendored 본문 불수정 · 레포 wrapper 쪽 1행이 맞는 자리. Opus 5.5 무관.
- dev-reseed:82,186 (F10) — 유지(flag) — 파괴적 절차 파일 · 편집 없음.
- VENDORED:1,5 「10종/8종」 (F11) — 유지(flag) — 문서 drift 만.
- design-review:41 「현재 16종」 (F12) — 유지(flag).

감사자가 놓친 것:
1. design-review:18·90·92 — 「Playwright 대신」·「(Playwright 아님)」·「Playwright·puppeteer 를 새로 들이지 않는다」 3회 반복(Group 1c 반복 강화). §2-5 첫 문장 한 번에 이유(전역 npm 도구 · 게이트 `frontend-visual` 이 같은 스크립트를 돈다)를 붙이고 :18·:90 제목의 괄호는 뺀다. Medium.
2. design-review:17 정적 합격선 행 — `design-fix 20260924 값 20`·`20260925 Q1f`·`#15`·`#13` 는 예외 항목마다 붙은 결정 번호(Group 2 이력 서술). 예외의 **이유**(WCAG 1.4.3·1.4.11 · 장식 글리프)는 이미 병기돼 있어 번호만 걷어도 규칙이 선다. Low — flag 로만.
3. hunk 6 의 중복 검사 누락 — 메모리 `subagent-turn-limits-truncate-results` 의 처방(산출물부터 · 좁혀서 재개)이 `.agents/roles/researcher.md` 또는 `colab-v2-work` 에 이미 들어갔는지 감사가 확인하지 않았다(정보는 한 곳). 위 F6 조정에 포함.