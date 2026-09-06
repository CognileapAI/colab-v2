# P-S 스킬 vendoring — 실행 기록 (2026-09-06)

근거 스펙 = `docs/superpowers/specs/2026-09-06-harness-fable51-design.md` **B-2**(개조표·폴더 배치·intent 소유)
· **F**(파이프라인 1.5 grill-me · 3 intent.md · 3.5 to-spec · 라운드 파일 = spec 의 실행 뷰) · **H 7행**(P-S 검증)
· **L**(템플릿 L-1·L-2) · **K**(문서 인용 검증). 조사 원본 = `04-grill-me.md` · `05-playbook-gap.md`.

## 1. 무엇을 들여왔나 — 8종

| 스킬 | 출처 | 판본·날짜 | 명시 호출 전용 |
|---|---|---|---|
| `grilling` | mattpocock/skills (MIT) | `main` tarball · package 1.2.3 · **2026-09-06** | 모델 호출 가능(원문 그대로) |
| `grill-me` | mattpocock/skills (MIT) | 〃 | **예**(`disable-model-invocation: true`) |
| `to-spec` | mattpocock/skills (MIT) | 〃 | **예**(〃) |
| `writing-plans` | superpowers (MIT) | 설치본 **6.3.0** · 파일 스탬프 2026-08-17 | 아니오 |
| `executing-plans` | superpowers (MIT) | 〃 | 아니오 |
| `test-driven-development` | superpowers (MIT) | 〃 | 아니오 |
| `verification-before-completion` | superpowers (MIT) | 〃 | 아니오 |
| `receiving-code-review` | superpowers (MIT) | 〃 | 아니오 |

- 자리 = `.claude/skills/<name>/`. 출처·라이선스·개조 목록 정본 = **`.claude/skills/VENDORED.md`**.
- 참조 파일 2건(`test-driven-development/writing-good-tests.md` · `writing-plans/plan-document-reviewer-prompt.md`)은
  **무수정**(diff 0). mattpocock 3종의 `agents/openai.yaml` 도 원문 그대로 승계.
- **훅 0개** — 8종 어디에도 자동 발동 장치가 없다.
- ⚠ mattpocock 은 커밋 SHA 가 아니라 **브랜치 tarball** 로 받았다(`git clone` 미사용). 재현 기준은
  「1.2.3 + 2026-09-06」이고 정확한 SHA 가 필요하면 그 날짜의 `main` 을 다시 받아 대조한다.

## 2. 개조 — 공통 3종 + 스킬별

**공통(8종 전부 · Fable 5.1 문안 교정)** — ⑴ 사고 재현 지시 제거(실삭 4건: `Announce at start` 2 ·
`Announce: "I'm using the finishing…"` 1 · `pushing back out loud` 1) ⑵ 앞 절을 되풀이하는 나열만 축약
(TDD Red Flags 13→7 · verification 「Rule applies to」 4→1 · code-review 감사 표현 4→2)
⑶ 끝에 `Before reporting, check each claim against this session's tool results.` 1행.
⛔ 하드 게이트·체크리스트·근거 삭제 **0건**.

**스킬별**
- `grilling` — 원문 **삭제 0행**(diff 가 순수 증보 11행). 설계트리·라운드·프론티어·권장 답·
  「finding facts is your job, never the user's」 전부 유지. 증보 = 사실 조회는 `researcher` 로,
  Ted 질문은 라운드 단위로 묶어 각 건에 ⓐ/ⓑ + 권고, 질문문에 내부 약어 노출 금지.
- `grill-me` — 명시 호출 전용 유지. 종료 시 `dev-package/intent/<날짜>-<주제>.md` 초안 작성 절 신설.
  **확인 문장 원문 그대로 · 미해결 질문 0건 · 초안은 Ted 교정·커밋 대기(커밋 = 승인)**.
- `to-spec` — 「재인터뷰 없음」·시험 seam 선정 유지. 이슈트래커 발행·`ready-for-agent` 라벨·
  `/setup-matt-pocock-skills` 전제 **삭제**. 산출 = `dev-package/prd/specs/<회차>.md`(템플릿 L-2).
  **정책 대조 절**(CLAUDE.md §2·§3·§5·계약 파괴 여부)과 **우려 항목(ⓐ/ⓑ) 절**이 비면 advisor ① 에 올리지 않는다.
- `verification-before-completion` — **intent 대조 절 신설**: proposed outcome 의 **미달·초과**를 열거한
  뒤에만 완료를 주장한다. 둘 다 0건이어야 충족.
- `writing-plans` — 산출 경로가 `dev-package/prd/rounds/R-*.md`(≤300행 · 첫 줄에 spec 링크)로 바뀌었다.
  `docs/superpowers/plans/` 경로 잔존 0건.
- `executing-plans`·`test-driven-development`·`receiving-code-review` — 공통 3종만.

**미채택** = `brainstorming`(superpowers) · `grill-with-docs`·`to-tickets`·`triage`·`wayfinder`(mattpocock).
사유는 `VENDORED.md` 말미(자동 발동 충돌 · 원장 이중화 · 외부 이슈트래커 전제).

## 3. 신설 폴더·템플릿

| 경로 | 내용 |
|---|---|
| `dev-package/intent/README.md` | 3줄 — 용도 · 명명 `<YYYY-MM-DD>-<주제>.md` · 승인 = 커밋 · 개정 금지·신규 발행 [추론] |
| `dev-package/intent/TEMPLATE.md` | 스펙 **L-1** 원문(29행 · 코드펜스만 제거) |
| `dev-package/prd/specs/README.md` | 3줄 — 용도 · 명명 · spec 우선 |
| `dev-package/prd/specs/TEMPLATE.md` | 스펙 **L-2** 원문(31행 · 코드펜스만 제거) |

⛔ **실제 intent 는 아직 만들지 않았다** — 첫 `grill-me` 는 Ted 가 다음 세션에서 직접 돌린다(스펙 F 1.5).

## 4. 슬리밍

| 파일 | 전 | 후 | 상한 | 한 방법 |
|---|---|---|---|---|
| `CLAUDE.md` | 219 | **157** | ≤200 | 「업로드(S3)」·「배포」 두 운영 절의 본문을 **`paths` 프런트매터 규칙 파일**로 이동, 자리에 §9 포인터 6줄 |
| `.claude/skills/colab-v2-work/SKILL.md` | 169 | **110** | ≤110 | 훅·규칙이 강제하게 된 규칙문을 한 줄 포인터로 치환 |

**신설 경로 스코프 규칙 2건** — 문면 무변경(diff 로 대조 완료).
- `.claude/rules/s3-upload.md` (28행 · `paths: ["services/core-api/**"]`)
- `.claude/rules/deploy.md` (60행 · `paths: ["infra/**","docs/DEPLOY*.md","services/core-api/ops/**"]`)
  — 이동 시 바뀐 것은 헤딩 레벨(`###`→`##`)과 `§5` → `CLAUDE.md §5` 한정 표기 둘뿐.

`paths` 는 문서로 확인됨 — "Rules can be scoped to specific files using YAML frontmatter with the `paths`
field. These conditional rules only apply when Claude is working with files matching the specified patterns."
(`https://code.claude.com/docs/en/memory.md`). 글로브는 **프로젝트 루트 기준**, 값은 **YAML 리스트**.
같은 문서가 "Rules without `paths` frontmatter are loaded at launch with the same priority as
`.claude/CLAUDE.md`" 를 그대로 싣는다 — `colab-rules.md` 가 `paths` 를 붙이지 않는 이유가 이것이다.

`colab-v2-work` 에서 포인터로 바뀐 것 = 부트스트랩 순서(`§1-4` · 훅 `bootstrap-diet.sh`) ·
워크트리 격리·env 구성(`§2-3`·`§2-4` · 훅 `worktree-setup.sh`) · 전수 env source·병렬도(`§3-1`·`§3-4` ·
`run.sh` 자체 source) · 〈N〉 재번호(`§4-1` · `renumber-decisions.sh`) · 대장 충돌(`§4-2`) · 보고 문체(`§5`).
**존치** = 레인 프로토콜 5항 · 어드바이저 게이트 3항(② 고정 3항 명시) · 검사기 정책 · green-by-skip ·
수치 규율 · 운영 접촉 경계 · HANDOFF 5줄 · 마무리 수용 체크리스트 3항.

## 5. 검증 결과 (실측)

| 항목 | 기준 | 실측 |
|---|---|---|
| `CLAUDE.md` | ≤200행 | **157** ✅ |
| `colab-v2-work/SKILL.md` | ≤110행 | **110** ✅ |
| `.claude/skills/` 스킬 수 | 9 (vendored 8 + colab-v2-work) | **9** ✅ |
| 9종 frontmatter YAML 파싱 | 전건 성공 | **9/9** ✅ |
| vendored 8 의 `description` | ≤2문장 | **8/8**(`grilling` 2 · 나머지 1) ✅ |
| 절대경로(`/mnt/`·`/home/`) | `.claude/skills`·`.claude/rules`·`dev-package/intent`·`dev-package/prd/specs` 에서 0 | **0** ✅ |
| 게이트 | `work-item-consistency` green | **green — 대장과 산문의 불일치 0**(㈕ CLAUDE.md stage 3 대조 15건 포함) ✅ |
| 참조 파일 2건 | 무수정 | **diff 0** ✅ |

각 SKILL.md 행수 — `grill-me` 19 · `grilling` 39 · `to-spec` 83 · `executing-plans` 63 ·
`receiving-code-review` 204 · `test-driven-development` 316 · `verification-before-completion` 130 ·
`writing-plans` 173 · `colab-v2-work` 110.

## 6. 다음 세션의 실전 확인 (P-S 검증의 나머지 절반)

스펙 H 7행이 요구하는 「grill-me 1회 실전」은 **Ted 가 직접 답해야 성립**하므로 이 회차에서 하지 않았다.
다음 세션 첫 발의에서 아래 순서로 한 번 돌리고 결과를 이 파일에 증보한다.

1. `/grill-me` **1회** — 프론티어가 빌 때까지 라운드를 돈다. 사실 조회는 `researcher` 로 내리고
   Ted 에게는 ⓐ/ⓑ + 권고가 붙은 묶음 질문만 간다.
2. → `dev-package/intent/<날짜>-<주제>.md` **1건** 산출. **Ted 확인 문장이 원문 그대로** 실렸는지,
   **미해결 질문이 0건**인지 확인. Ted 가 교정·커밋하면 승인이다.
3. `/to-spec` **1회**(재인터뷰 없음) → `dev-package/prd/specs/<회차>.md` **1건** 산출.
   **정책 대조 절과 우려 항목 절이 채워졌는지**가 advisor ① 진입 조건이다.
4. 라운드 파일 `dev-package/prd/rounds/R-*.md` **첫 줄에 그 spec 링크**가 있는지 확인(≤300행).

통과 판정 = 1~4 가 전부 파일로 남고 4의 링크가 실존 파일을 가리키는 것.
