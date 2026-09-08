---
name: to-spec
description: "Turn the current conversation into a spec file: no interview, just synthesis of what you've already discussed."
disable-model-invocation: true
---

This skill takes the current conversation context and codebase understanding and produces a spec. Do NOT interview the user; just synthesize what you already know.

승인된 `dev-package/intent/<날짜>-<주제>.md` 가 입력이다. 없으면 `/grill-me` 를 먼저 돌려야 한다고 알리고 멈춘다.

## Process

1. Explore the repo to understand the current state of the codebase, if you haven't already. Use the project's domain glossary vocabulary throughout the spec, and respect any ADRs in the area you're touching.

   이 레포의 용어 정본은 `dev-package/DOMAINS.md`, 결정 이력은 `dev-package/PLAN-SoT.md §9` 다(grep 한 줄로 해당 절만).

2. Sketch out the seams at which you're going to test the feature. Existing seams should be preferred to new ones. Use the highest seam possible. If new seams are needed, propose them at the highest point you can. The fewer seams across the codebase, the better - the ideal number is one.

Check with the user that these seams match their expectations.

3. Write the spec to **`dev-package/prd/specs/<회차>.md`** using the template below (`dev-package/prd/specs/TEMPLATE.md` 와 같은 형식). 파일 배출로 끝난다 — 이슈트래커 발행·라벨 부여 단계는 이 레포에 없다.

4. **정책 대조 절과 우려 항목 절이 비어 있으면 advisor ① 계획 검토에 올리지 않는다.** 두 절이 이 스킬의 차단 게이트다.

<spec-template>

# Spec: \<회차·제목\>   ← intent.md 로부터 합성. 재인터뷰 없음
출처 intent: `dev-package/intent/<파일>` (승인 \<날짜\>)

## 문제 진술
- \<intent 문제절을 개발 언어로 1~3행\>

## 해법 개요
- \<사용자 관점 서술. 「사용자 관점 동일 행위는 기존 흐름 재사용」 원칙 적용\>

## 사용자 스토리
1. \<행위자\>로서 \<기능\>을 원한다, \<이유\> 때문에.
2. ...

## 구현 결정
- 모듈 · 인터페이스:
- 스키마 · 마이그레이션: (Alembic 포함 시 revision 체인 명시 → advisor ② 항목)
- API 계약: 파괴 / 비파괴
- 코드 조각은 산문보다 결정을 정확히 담을 때만 (상태기계·타입 형태)

## 시험 결정
- 외부 행위 기준 검증 항목:
- 재사용 seam: / 신설 seam:
- 해당 서비스 단독 게이트 이름:
- green-by-skip 방지: 대상 0건이 아님을 무엇으로 보이나

## 정책 대조 (작성 시점 제약)
- CLAUDE.md §2 도메인 / §3 불변 규칙 중 저촉 항목: 없음 / \<항목\>
- CLAUDE.md §5 「절대 하지 않는 것」 중 저촉 항목: 없음 / \<항목\>
- 계약 동결 해제 필요: 예(Ted 서명) / 아니오

### 디자인 제약 확인 (`frontend/` 를 건드리는 spec 은 필수)
바꾸는 **화면마다** 아래를 적는다. 정본 = `frontend/src/shell/tokens.css`
(판정 기준 `.claude/skills/design-review/SKILL.md §0` · 인터랙션 `.claude/skills/apple-design/SKILL.md`).
- 토큰: `tokens.css` 의 토큰만 쓴다 (파일별 `:root` 전역 신설 없음)
- 글자 **13px 이상** · 대비 **4.5:1 이상**
- 카드 그림자 **0** (팝오버 허용) · 여백은 **컨테이너가 소유**
- 인터랙션 하한: pointer-down 즉시 피드백 · 전환 중단 가능 · 움직임엔 `prefers-reduced-motion` 분기
- 화면 없음(백엔드 전용)이면 「해당 없음」 한 줄로 끝낸다
**적을 수 없는 항목은 아래 「우려 항목」에 올린다** — 판정 없이 구현으로 넘기지 않는다.

## 우려 항목 (판정 필요)
| # | 항목 | ⓐ | ⓑ | 권고 |
|---|---|---|---|---|
| 1 | \<ELI5 로 풀어 쓴 항목\> | \<선택지\> | \<선택지\> | ⓐ |

## 범위 밖
- \<intent 에서 승계 + 확장\>

## 산출 계획
- 라운드 파일: `prd/rounds/R-*.md` (≤300행, 이 spec 을 첫 줄에서 링크)
- 예상 레인 수: \<n\> (진짜 독립일 때만 병렬, 기본 직렬 1)

</spec-template>

## 절별 작성 지침 (원문 유지)

**사용자 스토리** — A LONG, numbered list of user stories. Each user story should be in the format of `As an <actor>, I want a <feature>, so that <benefit>`. This list of user stories should be extremely extensive and cover all aspects of the feature.

**구현 결정** — modules built/modified, their interfaces, technical clarifications from the developer, architectural decisions, schema changes, API contracts, specific interactions. Do NOT include specific file paths or code snippets. They may end up being outdated very quickly.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts, not a working demo, just the important bits.

**시험 결정** — what makes a good test (only test external behavior, not implementation details), which modules will be tested, prior art for the tests (i.e. similar types of tests in the codebase).

**우려 항목** — 항목번호·WU 코드·내부 약어를 쓰지 않는다. 기능과 코드로 풀어 쓰고, 고르면 달라지는 것을 각 선택지에 적는다(`.claude/rules/colab-rules.md §5-2`).

Before reporting, check each claim against this session's tool results.
