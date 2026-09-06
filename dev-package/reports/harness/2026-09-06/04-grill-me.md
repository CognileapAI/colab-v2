# "Grill Me" → intent.md → spec 워크플로우 조사

## 출처 확인 상태
- YouTube video (rGaSkBWjoHA, t=357s): WebFetch could not retrieve description/transcript/chapters (YouTube page returned only boilerplate/footer, no substantive content extracted). **미확인** — could not directly confirm the video content. However web search strongly and consistently ties this exact pattern ("grill me", intent.md, spec) to **Matt Pocock's "skills" repo** (github.com/mattpocock/skills, "Skills for Real Engineers. Straight from my .agents directory."). Treating this as the source the video demonstrates, based on convergent search evidence, but the video itself was not read — mark as inferred, not directly verified.

## 1. 정체: Matt Pocock's Claude Code skill family
Repo: https://github.com/mattpocock/skills

Chain confirmed via raw SKILL.md fetches:
- `skills/productivity/grilling/SKILL.md` — the core reusable interview primitive.
- `skills/productivity/grill-me/SKILL.md` — thin wrapper: "A relentless interview to sharpen a plan or design." `disable-model-invocation: true`; body just invokes Skill tool with param `"grilling"`. Stateless, no repo needed, writes no files, subject doesn't have to be code.
- `skills/engineering/grill-with-docs/SKILL.md` — stateful variant: invokes `"grilling"` then `"domain-modeling"`, and **writes intent.md, CONTEXT.md, and ADRs** (exact field contents not retrieved — page summarized, not full text).
- `skills/engineering/to-spec/SKILL.md` — converts the *already-discussed* conversation (post-grilling) into a spec, **no further interview**. Explores codebase for context, decides testing seams (prefer existing, minimize new), then emits a spec with template: Problem Statement, Solution, User Stories ("As a [actor], I want [feature], so that [benefit]", numbered), Implementation Decisions (module/interface/schema/API changes, code snippets only when they encode decisions more precisely than prose — e.g. state machines, reducers, type shapes), Testing Decisions (external-behavior focus, prior art), Out of Scope, Further Notes. Publishes to issue tracker with `ready-for-agent` triage label.
- Full pipeline per README: **`/grill-with-docs` → `/to-spec` → `/to-tickets` → `/implement` → `/code-review`**, with `/wayfinder` above it for multi-session/multi-decision work.

## 2. "Grill me" 핵심 메커니즘 (grilling primitive)
- Builds a **design tree**: decisions branch into dependent sub-decisions.
- Works in **rounds**; each round only asks about the **"frontier"** — decisions whose prerequisites are already resolved. A question whose answer depends on another still-open question in the same round is deferred to a later round (no circular/premature asks).
- Each round: numbered questions, each with a **recommended answer** offered, awaiting user response before advancing (i.e., not fully open-ended — closer to multiple-choice-with-a-default).
- Rule: "finding facts is your job, never the user's" — sub-agents should look up environment/codebase facts rather than asking the user anything look-uppable.
- **Exit criterion**: session ends when the frontier is empty — every branch resolved, nothing silently assumed — and explicitly, **no action is taken until the user confirms shared understanding has been reached.**

## 3. vs. superpowers:brainstorming
| | grill-me / grilling | superpowers:brainstorming |
|---|---|---|
| Question style | Numbered, one round of parallel "frontier" questions, each with a suggested default answer | One question at a time, strictly sequential |
| Structure | Explicit design-tree + round/frontier algorithm; formal graph of dependencies | Looser exploratory dialogue toward a design doc |
| Artifact | Stateless base (`grill-me`: nothing written) vs. stateful (`grill-with-docs`: intent.md + CONTEXT.md + ADRs) | design doc → spec file → writing-plans (single linear artifact chain) |
| Exit criterion | Formal: frontier empty + user confirms "shared understanding reached" | Implicit: design doc reads as complete, ready to spec |
| Handoff | Separate skill (`to-spec`) synthesizes *no new interview*, just converts prior discussion | Same session continues into spec/plan writing |

Distinguishing traits of grill-me worth porting: (a) adversarial/systematic tree-completeness check rather than free-form Q&A, (b) hard stop rule ("don't act until confirmed"), (c) clean separation between the *interview* artifact (intent.md) and the *synthesis* artifact (spec) — two different skills/agents, not one continuous pass.

## 4. What a Claude Code skill implementing this needs
- **Trigger**: explicit slash command (`/grill-me`), not auto-fired — matches this user's existing skill-invocation discipline (see graphify precedent: explicit-only).
- **Questioning rules**: build the dependency tree first (even informally); ask only frontier items per round; offer a recommended default per question; never ask what can be looked up (delegate fact-finding to a sub-agent/tool call); defer any question whose answer depends on an unresolved sibling.
- **Stop criterion**: frontier empty AND user explicitly confirms understanding — this confirmation line should be captured verbatim in intent.md as the acceptance record.
- **intent.md sections**: see template below.
- **Handoff to spec**: a *separate* step/skill that only synthesizes intent.md (no new questions) into spec.md — mirrors `to-spec`'s "no interview" rule.

## 5. Minimal intent.md template (<40 lines)
```markdown
# Intent: <one-line title>

## Trigger
<what prompted this — user request, decision ledger 〈N〉 ref, round file ref>

## Design tree (resolved)
- Q1: <question> → A: <answer> (default accepted / overridden)
- Q2: <question> → A: <answer>
  - Q2a: <dependent question> → A: <answer>
...

## Assumptions made explicit
- <anything the tree exposed that was previously silent>

## Out of scope (explicitly excluded)
- <item>

## Confirmation
"Shared understanding reached" — confirmed by <user> on <date>.
Quote: "<verbatim user confirmation line>"

## Refs
- Round file: prd/rounds/<N>.md
- Decision ledger: 〈N〉
```

## 6. Minimal spec.md template (<40 lines)
```markdown
# Spec: <title>  (from intent.md, no re-interview)

## Problem statement
<user-centric, 1-3 lines>

## Solution
<user-centric overview>

## User stories
1. As a <actor>, I want <feature>, so that <benefit>.
2. ...

## Implementation decisions
- Module/interface changes: ...
- Schema/API contract: ...
- (code snippet only if it encodes a decision more precisely than prose)

## Testing decisions
- External behavior to verify: ...
- Existing seam reused: ... / new seam: ...

## Out of scope
- <carried over from intent.md, expanded if needed>

## Ted brief mapping
- ⓐ/ⓑ decision points requiring sign-off: <list, ref 〈N〉>

## Further notes
<anything else>
```

## 7. Full skill inventory (README, engineering + productivity)
Repo: https://github.com/mattpocock/skills — "Skills for Real Engineers, straight from my .agents directory."
Stated purpose: targets 4 failure modes — intent/output misalignment, verbosity from missing shared domain language, non-functional code from weak feedback loops, architectural decay.

**Engineering / user-invoked:**
- `ask-matt` — router to the right skill.
- `grill-with-docs` — interview + writes CONTEXT.md/domain model/ADRs (uses `grilling` + `domain-modeling`).
- `triage` — moves issues through a state machine.
- `improve-codebase-architecture` — scans for architecture "deepening" opportunities.
- `to-spec` — synthesizes conversation → formal spec, no re-interview.
- `to-tickets` — breaks a spec/plan into "tracer-bullet" tickets with blocking declarations.
- `implement` — executes tickets/spec with TDD + code review baked in.
- `wayfinder` — multi-session mapping via "decision tickets" on the issue tracker.
- `setup-matt-pocock-skills` — one-time repo config (issue tracker, triage vocabulary).

**Engineering / model-invoked (reusable disciplines):**
`prototype`, `diagnosing-bugs` (red→minimize→hypothesize→instrument→fix), `research` (cited, primary-source), `tdd` (red-green-refactor), `domain-modeling`, `codebase-design` ("small interfaces, clean seams"), `code-review` (dual-axis: standards + spec compliance), `resolving-merge-conflicts` (intent-based), `wizard` (interactive bash setup).

**Productivity / user-invoked:**
- `grill-me` — "Get relentlessly interviewed about a plan or design until every branch of the design tree is resolved." (stateless, no repo needed)
- `handoff` — compacts conversation into a handoff doc for another agent.
- `teach` — teaches a skill/concept over multiple sessions using cwd as stateful workspace.
- `to-questionnaire` — turns an undecidable question into a Markdown questionnaire for the person who can decide.
- `wait-what` — fires when a message "doesn't land"; re-pitches with missing context.

**Productivity / model-invoked:**
- `grilling` — the reusable interview primitive underlying grill-me/grill-with-docs/triage/wayfinder/improve-codebase-architecture.
- `writing-for-agents` — how to write skills/AGENTS.md/CLAUDE.md for agent consumption.

**Full chain, as the repo frames it**: `/grill-with-docs → /to-spec → /to-tickets → /implement (TDD + code-review inside) → /code-review`; `/wayfinder` sits above this for multi-session/multi-decision efforts; `grill-me`/`grilling` is the shared primitive several of these call into rather than a distinct pipeline stage.

## 8. Verbatim rules retrieved (best effort — see caveat)
Caveat: WebFetch here summarizes fetched pages through a small intermediate model rather than returning raw text, so exact verbatim SKILL.md text could not be pulled through this channel for grill-me/to-spec/grill-with-docs beyond short quoted fragments below (the raw.githubusercontent.com fetch was still passed through the same summarizer). Treat non-quoted lines as close paraphrase, not verbatim.

- `grill-me` frontmatter/behavior: `disable-model-invocation: true` (i.e., **user-invoked only**, never auto-triggered by the model); one-line description: **"Get relentlessly interviewed about a plan or design until every branch of the design tree is resolved."** Body: calls the Skill tool with param `"grilling"`. No repo required, writes no files.
- `grilling` (the primitive) — key quoted lines: **"finding facts is your job, never the user's"**; **"A question whose answer depends on another question still open in this round belongs to a *later* round, not this one."** Mechanism: design tree → rounds → "frontier" (only decisions whose prerequisites are resolved) → numbered questions each with a recommended answer → repeat until frontier is empty → **no action until the user confirms shared understanding has been reached.**
- `grill-with-docs`: same `disable-model-invocation: true` pattern; body calls Skill tool twice: `"grilling"` then `"domain-modeling"`; writes **intent.md, CONTEXT.md, ADRs** (exact section headers inside intent.md not retrieved verbatim — likely lightweight, single-purpose per PR/session; could not confirm structure beyond the file's existence and role as the interview's durable record).
- `to-spec`: no interview — synthesizes what's already been discussed. Steps: (1) explore codebase for context/glossary/ADR compliance, (2) pick testing seams (prefer existing, minimize new, place at highest sensible architectural level), (3) emit spec using template: **Problem Statement, Solution, User Stories (numbered, "As a [actor], I want [feature], so that [benefit]"), Implementation Decisions (module/interface/schema/API changes; code snippets only when they encode a decision more precisely than prose — state machines, reducers, type shapes), Testing Decisions (behavior over implementation, prior art), Out of Scope, Further Notes.** Publishes directly with `ready-for-agent` triage label, requires `/setup-matt-pocock-skills` prerequisite for issue tracker + label vocabulary.

## 9. License / distribution / footprint / hooks
- **License**: MIT (per repo metadata fetch).
- **Star count**: fetch reported "252.8k stars" — **flagged as almost certainly unreliable/fabricated** by the summarizing fetch model (a niche personal skills repo at that count would be implausible, comparable to major frameworks); do not treat as verified. Recommend spot-checking directly if star count matters for the decision.
- **Install methods**: (a) Claude Code plugin marketplace — `claude plugins install mattpocock-skills` or in-session `/plugin install mattpocock-skills` (managed, auto-updating); (b) copy/vendor — `npx skills@latest add mattpocock/skills` (editable local files). Repo explicitly warns against using both at once (duplicate skills). One-time `/setup-matt-pocock-skills` wires up issue-tracker + triage-label config per repo.
- **Session-start injection size**: not directly measurable from fetched summaries — each skill exposes only a one-line description for model-invoked discovery (SKILL.md frontmatter pattern, same convention as Claude Code skills generally); full body loads only on invocation. Could not get an exact byte count for the aggregate description block; likely small (roughly a dozen one-liners across engineering, more the productivity set) but this is an estimate, not measured.
- **Always-on hooks**: no evidence of any hook-based automation — every user-invoked skill in the inventory explicitly requires a slash command or explicit Skill-tool call; model-invoked skills trigger only via description-matching, not hooks. `disable-model-invocation: true` on grill-me/grill-with-docs specifically forces manual-only triggering. No hooks referenced anywhere in the fetched content.

## 10. Comparison: mattpocock chain vs. superpowers brainstorming→plans→execute→TDD→verify
| Axis | mattpocock (grill-me/grill-with-docs → to-spec → to-tickets → implement → code-review) | superpowers (brainstorming → writing-plans → executing-plans → TDD → verification-before-completion) |
|---|---|---|
| Interview style | Formal design-tree + round/frontier algorithm, questions batched per round with recommended defaults | Strictly one question at a time, more conversational |
| Artifact of the interview | intent.md / CONTEXT.md / ADRs (grill-with-docs only; grill-me itself writes nothing) | a design doc within the same session, feeding directly into a spec file |
| Spec synthesis | separate skill (`to-spec`), explicitly *no* re-interview, fixed template, ties into issue tracker + triage label | folded into `writing-plans`, no separate spec-vs-plan skill split |
| Ticket breakout | dedicated `to-tickets` (tracer-bullet tickets, blocking declarations) — no direct superpowers equivalent found in this chain | plans are the unit; no separate ticket-breakout skill surfaced |
| Implementation | `implement` bundles TDD + code review together | `executing-plans` (session-with-checkpoints) + `subagent-driven-development` for independent tasks, `test-driven-development` and `requesting-code-review`/`receiving-code-review` are separate skills |
| Multi-session/large work | `wayfinder` — decision tickets on the issue tracker | not directly covered by the five named superpowers skills (closer to this project's own round-file + 〈N〉 ledger convention already) |
| Domain glossary / architecture hygiene | `domain-modeling`, `codebase-design`, `improve-codebase-architecture` — no superpowers equivalent | none in the named chain |
| Debugging discipline | `diagnosing-bugs` (red→minimize→hypothesize→instrument→fix) | `systematic-debugging` — functionally overlapping, both formal loops |
| Merge conflicts | `resolving-merge-conflicts` (intent-based) | not covered by superpowers' named set (worktree finishing/using-git-worktrees is adjacent but different concern) |
| Verification gate | code-review inside `implement`, plus standalone `code-review` skill (dual-axis: standards + spec compliance) | `verification-before-completion` (evidence-before-assertion) + `requesting-code-review`/`receiving-code-review` — more general-purpose, not spec-bound |
| Trigger discipline | explicit-only (`disable-model-invocation: true`) on the interview skills — matches this user's existing "explicit invocation only" preference (cf. graphify policy) | brainstorming is described as required "before any creative work" — closer to auto-triggered, which conflicts with this user's stated preference for explicit-only triggers on heavy/branching-risk skills |

**Overlaps**: grilling ≈ brainstorming (both: interview until ambiguity resolved, no premature action); to-spec/to-tickets ≈ writing-plans; implement ≈ executing-plans + TDD + code-review combined; diagnosing-bugs ≈ systematic-debugging; code-review skills overlap directly.

**Gaps each side fills**: mattpocock adds domain-modeling/codebase-design/architecture-hygiene, ticket-breakout with blocking declarations, and wayfinder for multi-session decision-tracking via an issue tracker — none of which superpowers' five named skills cover explicitly. Superpowers adds worktree isolation/finishing-branch mechanics and a stricter "verification before completion" independent of spec-matching.

**Fit for this project** (round files ≤300 lines, decision ledger 〈N〉, worktree lanes, advisor gate): the project **already has** its own issue-tracker-equivalent (round files + 〈N〉 ledger) and its own multi-session mapping (planning-folder lifecycle, HANDOFF docs) and its own gate (advisor). mattpocock's `to-tickets`/`triage`/`wayfinder` assume an issue tracker (GitHub Issues/Linear/`.scratch/`) this project doesn't use in that shape — adopting them wholesale would create a second, competing ledger system. But `grill-me`'s round/frontier interview algorithm and `to-spec`'s fixed spec template are tracker-agnostic and slot cleanly on top of existing round files without disrupting 〈N〉.

## 11. Recommendation
**Hybrid, narrow vendor**: vendor only `grilling` + `grill-me` (+ optionally `grill-with-docs`'s intent.md-writing behavior, adapted to write into `prd/rounds/*.md` instead of a fresh CONTEXT.md) and `to-spec` (adapted: skip its issue-tracker/triage-label publish step, instead output a `spec.md` that a round file or Ted ⓐ/ⓑ brief can absorb). Keep superpowers' `writing-plans`, `executing-plans`, `subagent-driven-development`, `test-driven-development`, `systematic-debugging`, `verification-before-completion`, `using-git-worktrees`, `finishing-a-development-branch` as-is — they already fit the worktree-lane + advisor-gate structure and there is no reason to replace working infra.

Reasons:
1. `grilling`'s round/frontier algorithm and explicit stop criterion (frontier empty + user confirmation) is a strictly better front-door for this project's decision-heavy 〈N〉 process than superpowers' one-at-a-time brainstorming — batching by "frontier" reduces round-trips, which matters given the project's existing round-file cadence.
2. `to-spec`'s fixed template (Problem/Solution/User Stories/Implementation Decisions/Testing Decisions/Out of Scope) is a clean, small addition that doesn't require adopting mattpocock's issue-tracker assumption — it can emit into this project's own file conventions.
3. `to-tickets`, `triage`, `wayfinder` assume an external issue tracker or `.scratch/` state machine this project doesn't run; vendoring them whole would fork the project's existing 〈N〉 ledger and round-file discipline into two parallel systems — net cost, not benefit.
4. superpowers' execute/TDD/verify/worktree skills are already integrated with this project's worktree-lane and advisor-gate workflow (per memory: subagent-worktree-isolation-pin, narrow-gates-one-at-a-time); nothing in mattpocock's `implement`/`code-review` clearly supersedes that, so replacing them is unjustified churn.
5. Both interview skills (`grill-me`, `grill-with-docs`) are `disable-model-invocation: true` — explicit-only triggering matches this user's own stated policy of not letting heavy skills auto-fire (cf. graphify carve-out in CLAUDE.md), so vendoring just these is low-risk to existing session behavior.

## 결론 (≤12 lines)
1. "grill me" = Matt Pocock's `mattpocock/skills` repo (MIT, github.com/mattpocock/skills) — confirmed via repo/SKILL.md fetches, not the video (video transcript/description remained inaccessible).
2. Mechanism (`grilling` primitive, underlying `grill-me`): decision tree → rounds → only "frontier" (prerequisite-resolved) questions asked, each with a recommended default → repeat until frontier empty → **no action until user confirms shared understanding**. Rule: "finding facts is your job, never the user's."
3. `grill-me` is stateless/no-files (`disable-model-invocation: true`, user-invoked only); `grill-with-docs` is the stateful sibling that writes **intent.md + CONTEXT.md + ADRs** (exact intent.md section layout not retrieved verbatim — summarized fetch only).
4. `to-spec` does NOT re-interview — it synthesizes prior discussion into a fixed template (Problem/Solution/User Stories/Implementation Decisions/Testing Decisions/Out of Scope/Further Notes), publishes to an issue tracker with a triage label.
5. Full chain per repo: `/grill-with-docs → /to-spec → /to-tickets → /implement (TDD+review inside) → /code-review`, with `/wayfinder` above for multi-session work.
6. Reported "252.8k stars" is almost certainly a fetch-summarizer artifact/unreliable — flagged, not usable as-is.
7. Install: Claude Code plugin (`claude plugins install mattpocock-skills`) or vendor copy (`npx skills@latest add mattpocock/skills`); no hooks found anywhere — every heavy skill is explicit-trigger only.
8. vs. superpowers: mattpocock batches "frontier" questions per round (not strictly one-at-a-time), has an explicit tree-completeness + confirmation stop rule, and splits interview (intent.md) from synthesis (spec.md) into separate skills; superpowers integrates tighter with worktrees/TDD/verification already used here.
9. Recommendation: **hybrid narrow vendor** — take `grilling`+`grill-me` and `to-spec` (adapted to emit into round files/spec.md instead of an issue tracker), keep superpowers' writing-plans/executing-plans/TDD/verification/worktree skills untouched; do NOT vendor `to-tickets`/`triage`/`wayfinder` (they assume an external issue tracker that would fork the existing 〈N〉 ledger).
10. intent.md and spec.md minimal templates (≤40 lines each, matching round-file/〈N〉/Ted ⓐ/ⓑ conventions) are drafted in the file, sections 5–6.

Sources:
- https://github.com/mattpocock/skills
- https://raw.githubusercontent.com/mattpocock/skills/main/skills/productivity/grilling/SKILL.md
- https://raw.githubusercontent.com/mattpocock/skills/main/skills/productivity/grill-me/SKILL.md
- https://raw.githubusercontent.com/mattpocock/skills/main/skills/engineering/grill-with-docs/SKILL.md
- https://raw.githubusercontent.com/mattpocock/skills/main/skills/engineering/to-spec/SKILL.md
- https://mcpmarket.com/tools/skills/grill-me
- https://skillselion.com/skills/mattpocock/skills/grill-me
