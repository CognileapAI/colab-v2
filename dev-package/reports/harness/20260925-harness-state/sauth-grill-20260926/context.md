# S-auth intent — 맥락(권고 없음)


## 메타 · 출처
메타 — 발의자: Ted · 작성 2026-09-26 · 승인 미승인(초안 · /grill-me 판정 예정)
- 출처: 부모 intent `dev-package/intent/2026-09-25-harness-improvement.md` 판정 기록 — 5라운드 설계 원칙(`:600` 「동작과 제약은 시스템으로 · 최종 결정(병합·배포·삭제)은 사람」) · 7라운드 Q-C ⓐ(`settings.json` ask 후보 7종은 deny 로 · 사람 인가는 TTY + 1회용 토큰 + `authorized_at` 기록) · Q-E ⓐ(인가 범위를 `infra/dev/ship.sh` 반입까지 · `tag-release.sh` 제외)(`:607`) · 8라운드 ⑩(S-auth 가 손대는 `services/core-api/ops/*.py` · `infra/dev/ship.sh` 는 부모 intent 「제품 코드 0」 밖 → 별도 intent)(`:610`).
- 총괄 계획 `dev-package/prd/specs/S-HARNESS-IMPROVEMENT-PLAN-20260926.md` S-auth 행(`:131`) · S 병합 조건(`:133`) · 순서표 행 9(PR 4 병합 뒤)(`:26`) · §6 #10(`:203`)의 실행 단위다. 줄 번호 기준 = 브랜치 `claude/harness-improvement` HEAD `e1e34ed6` · 2026-09-26 재열람.
- 표기: 「〈판정 대기〉」 = /grill-me 에서 Ted 가 정한다. 이 초안의 권고는 판정이 아니다.


## 문제
- 에이전트가 purge · reset · ship 스크립트를 부를 수 있다. 오늘 이를 막는 것은 규칙 문장(`.agents/rules/deploy.md:40-45` 「명시 GO 없이 실행하지 않는다」 · `AGENTS.md` 「제품 데이터 삭제·배포·main push 의 권한은 현재 대화의 사용자 승인 범위」)과 PR 3 에 예정된 `permissions.deny`(3-1 · 현재 `.claude/settings.json` 에 `permissions` 키 0건)뿐이다. deny 는 Claude Code 전용이다 — Codex(`scripts/agent-bridge.py` 경유) · bypass 세션(Workflow 레인 · `--dangerously-skip-permissions` · 적용 여부는 T14 실측 대기 · 총괄 계획 `:199`) · `bash -c` 감싸기(git-guard 머리말의 알려진 한계)에는 닿지 않는다. 로컬 hook · deny 는 마찰 장치이지 보안 경계가 아니다(부모 intent A3 · `README.md:116` · `AGENTS.md` 「명시적 guard 호출은 자동 보안 경계가 아니다」).
- 사람 인가 장치가 있는 경로는 dev reseed 의 reset 정지 게이트 하나다(커밋 `82853609` · `de424165` · `968d16a1`): 비어 있지 않은 dev 에 한해 원격 challenge nonce + 1회용 토큰(`sha256(계수 ‖ "\n" ‖ nonce)` · 만료 1800초 · 1회 소진 · `dev-package/tools/dev-reseed/stages.sh:211-223`) · 토큰은 stdout 이 터미널일 때만 출력(`[ -t 1 ]` · `:227-241`) · 판정·근거는 `reset-ack.json`(`:281-287`) · 사용자가 자기 터미널에서 `COLAB_RESEED_ACK_NONEMPTY` · `COLAB_RESEED_ACK_BASIS` 를 넣어 `--from reset` 으로 다시 연다(`.agents/skills/dev-reseed/SKILL.md:138-139`) · 에이전트의 값 할당은 git-guard ⑹ 이 거부(`scripts/harness/hooks/git-guard.sh:171-184`).
- 나머지 셋은 TTY · 토큰 · 인가 기록이 없다 — 인가는 「누가 실행했는가」와 무관하게 플래그 존재로 판정된다.
  - `services/core-api/ops/purge_datasets.py` — `--yes-delete`(`:99`) + ULID `--actor-id`(`:101-105`) 만 요구. 기록은 DB 삭제 스냅샷(`append_deletion_snapshots` · `:158-160`)과 stdout.
  - `services/core-api/ops/reset_dev_environment.py` — 게이트 다섯(`deploy.md:48-52`) · 거부 = `_REFUSE = 2`(`:198`). `--ack-sha256`(`:824`)은 reseed 정지 게이트 판정의 전달값이지 이 도구 자체의 인가가 아니다. 런북대로 손으로 부르면(`SKILL.md:148`) reseed 게이트를 거치지 않는다.
  - `infra/dev/ship.sh` — `COLAB_RELEASE_PRE_EVIDENCE` 부재 78(`:12-14`) · sha 부재 78(`:15`) · 조상 게이트 통과·65·78(`infra/_lib/ship-gate.sh:10`) 뒤 곧장 ssh/scp(`:50-55`). 사람인지 묻는 자리가 없다.
- 2026-09-15 · 16 · 24 세 번 사람이 만든 자료를 지웠다(`deploy.md:74-75`). 2026-09-24 사고의 주체는 상시 승인 아래의 에이전트였고 권고 문장만으로는 막히지 않았다(`git-guard.sh:176`).
- 인가 기록이 없어 사후 감사·게이트가 「사람이 인가했는가 · 언제 · 무엇에」를 읽을 수 없다. reseed 만 `reset-ack.json` 이 있고 purge · reset · ship 은 실행 기록에 인가 필드가 없다.

## 원한 결과 (proposed outcome)
- 대상 4 경로 — `purge_datasets.py --yes-delete` · `reset_dev_environment.py` 파괴 phase(`schema` · `s3-apply` 등 · 정확한 phase 집합은 spec) · dev-reseed reset 정지 게이트(기존 유지 · 같은 기제로 통합) · `infra/dev/ship.sh` 실반입(dry-run 제외) — 가 다음 셋을 모두 만족할 때만 행위한다. ⓐ stdin · stdout 이 TTY 다(`[ -t 0 ]` · `[ -t 1 ]` / `sys.stdin.isatty()`). ⓑ 이번 실행 대상에 결속된 1회용 토큰이 제시되고 일치한다(만료 · 1회 소진). ⓒ 인가 기록(`authorized_at` · operator · script · target 지문 · token sha256 · nonce sha256 · 결과)이 행위 전에 써진다.
- 비 TTY 호출(에이전트 · 파이프 · `bash -c` · Codex bridge · Workflow 레인)은 자격증명 · 네트워크 · DB 접속 전에 거부한다 — 종료코드는 〈판정 대기〉(Q4) · stderr 1줄(토큰 값 없음 · 사람이 밟을 절차 이름만).
- 토큰은 터미널에만 나온다 — 단계 로그 · stderr 리다이렉트 · 실행 기록 · 저장소에는 sha256 만 남는다(reseed `968d16a1` 과 같은 기준).
- 인가 기록의 스키마는 하나이고 시험이 필드를 고정한다. 기록 자리는 게이트·CI·`deploy_doctor` 가 읽을 수 있는 곳이다(Q7).
- 에이전트가 거부를 만나면 재시도하지 않고 사람에게 넘긴다 — `handoff --mode blocked`(PR 2 2-4 이후) 또는 최종 메시지에 사람 실행 절차 1줄(Q8).
- 검증 가능 문장: ⑴ 에이전트 세션(Claude Bash · Codex bridge · `bash -c`)에서 대상 4 경로를 부르면 모두 같은 종료코드로 거부되고 ssh · scp · DELETE · DROP 호출 0 ⑵ 사람이 자기 터미널에서 같은 명령을 토큰과 함께 부르면 진행되고 기록 파일에 `authorized_at` 이 있다 ⑶ 지난 토큰 · 다른 대상의 토큰 · 만료 토큰은 TTY 에서도 거부된다 ⑷ `dev-package/tools/dev-reseed/tests/reset-gate.sh` 는 무변경 green.

## 가치 가설
- Ted 는 파괴·외부 반영 행위가 「자기 터미널 + 이번 대상의 토큰」 없이는 일어나지 않게 되어, 문서·역할 정의·지난 GO 가 새 권한이 되지 않는다는 `AGENTS.md` 원칙을 장치로 얻는다.
- 에이전트는 거부 종료코드와 출구 절차를 얻어, 「승인 있음」을 추정해 실행하거나 거부 출력을 읽어 값을 채우는 경로를 잃는다.
- 감사·게이트는 인가 기록으로 「누가 · 언제 · 무엇에」를 읽어 사고 회차의 주체 판정을 문서 대조가 아니라 기록으로 한다.
- 확인 방법: 병합 뒤 PR 요약 「원한 결과 ↔ 실제 ↔ 근거」 표로 센다 — ⑴ 비 TTY 호출 3형태(Claude Bash · Codex bridge · `bash -c`) × 대상 4 경로의 종료코드 · 메시지 · 자격증명/네트워크 호출 0 ⑵ 사람 TTY 실행 1회(ship.sh dev 반입 1건 · purge dry-run 1건 · 총괄 계획 `:133`)의 진행과 기록 파일 ⑶ 시험 `scripts/tests/test_ops_authorization.py` · `infra/dev/tests/ship-gate.sh` pty 사례 · `reset-gate.sh` green ⑷ 이후 회차에서 「사람 자료 삭제 사고」 건수(기준 3회 · `deploy.md:74-75`) ⑸ 인가 기록 건수 == 대상 스크립트 실행 건수(불일치 = 우회 경로 존재).

## 영향 범위
- 사용자 / 화면: 없음 — 운영 스크립트 · 개발 하네스.
- 서비스 · 스키마 · 계약: `services/core-api/ops/purge_datasets.py` · `services/core-api/ops/reset_dev_environment.py` · 새 공통 모듈(자리 〈판정 대기〉 Q1) · `infra/dev/ship.sh`(+ `infra/_lib/` 공통 함수 후보) · `dev-package/tools/dev-reseed/stages.sh`(정지 게이트 — 확장만) · `.agents/skills/dev-reseed/SKILL.md` 승인 절(`:120-152` → 정본 포인터) · `.agents/rules/deploy.md:40-45` 1줄(「명시 GO 없이 실행하지 않는다」 → 「TTY 토큰이 요구한다」) · `scripts/harness/hooks/git-guard.sh` ⑹ 이름 목록(Q9) · 시험(`scripts/tests/test_ops_authorization.py` 신설 · `infra/dev/tests/ship-gate.sh` · `dev-package/tools/dev-reseed/tests/reset-gate.sh` · `scripts/tests/test_harness_release_evidence.py:96-104`) · 문서(`infra/dev/README.md` · `docs/DEPLOY.md` 해당 줄). 제품 코드(`frontend/src` · `services/*/colab_core` · `contracts/**`) 무변경 — ops · infra 스크립트가 부모 intent 「제품 코드 0」 밖이라 이 intent 로 분리했다(총괄 계획 `:166`).
- 계약 파괴 여부: 아니오 — 제품 API · 스키마 · `contracts/**` 무변경. 바뀌는 것은 스크립트의 실행 전제(TTY · 토큰)와 기록 파일이며, 규칙은 새 ADR 로 기록한다(Q11).

## 제약
- 기존 reset nonce 흐름을 깨지 않는다 — 토큰식 `sha256(지문 ‖ "\n" ‖ nonce)` · TTL 1800초 · `[ -t 1 ]` 출력 · `reset-ack.json` schema `colab-reseed-reset-ack/3` · `COLAB_RESEED_ACK_*` 이름을 유지하고 확장한다. 복제본(두 번째 토큰 기제)을 만들지 않는다(`ship-gate.sh:4-7` 「한 벌」 원칙).
- Codex · `bash -c` · bypass 세션을 덮는다 — 검사는 스크립트 안(`[ -t 0 ]`/`isatty`)에 있고 hook · `permissions` · frontmatter 에 의존하지 않는다. PR 3 3-1 deny 는 이 intent 의 전제가 아니라 겹치는 마찰 장치다.
- 저장소 · 로그 · 기록에 비밀 없음 — nonce · 토큰 평문 0 · sha256 만. 붙여 넣을 완성 명령을 찍을지는 Q8.
- 종료코드 — 게이트(시험 · selftest)는 0/1/78(`AGENTS.md`). 스크립트의 인가 거부 코드는 게이트 코드와 별개이며 Q4 에서 정한다. 시험은 「거부 = 기대 동작」 이므로 green.
- 훅 정의 무변경(`.claude/settings.json` hooks · `.codex/hooks.json` · 재신뢰 0). git-guard ⑹ 본문의 이름 목록 확장은 정의 변경이 아니다.
- 무인 실행 경로 — `infra/dev/install-cron.sh` 는 `backup.sh` 만 건다(`:49`). ship.sh · purge · reset 의 cron · CI 호출은 저장소 grep 0건(주석 2건 제외). `docs/DEPLOY.md:536` 「이 도구의 deploy 단계는 build.sh → ship.sh → …」 의 실제 호출부는 spec 단계에서 재확인한다(총괄 계획 `:189`).
- 기존 시험이 비 TTY 로 스크립트를 돌린다 — `test_harness_release_evidence.py:96-104`(`COLAB_RELEASE_DRY_RUN=1` · 증거 부재 78) · `infra/dev/tests/ship-gate.sh:31`(가짜 ssh · scp). 인가 검사 위치 · 면제 경로(Q5)는 이 시험을 깨지 않거나 pty(`reset-gate.sh:433` 선례)로 옮긴다.
- 파일 소유 · 순서 — `deploy.md` 는 E0 → S-red → PR 2 → PR 3 → S-auth 순차(총괄 계획 `:165`). 이 PR 은 PR 4 병합 뒤 착수(`:26`) · 단독 lane · `deploy.md` 선독 · dev 1회 실측 · 게시 T16 · 병합 T13(`:133`).
- ADR 이력 무수정 · 새 규칙 = 새 ADR. 승인 intent append-only.
- 이 intent 는 「자동 보안 경계」를 주장하지 않는다 — pty 로 stdout 받기 · 같은 사용자 파일로 토큰 재계산 · env 파일 · Write 도구 주입은 reseed 와 같이 남는 경로다(`deploy.md:69-72`). 어디까지 좁힐지는 Q2a.

## 미해결 질문(초안이 남긴 7건 — 판정 대상)
- pty · 같은 사용자 파일 재계산 경로를 어디까지 좁힐지(Q2a) — 원격 nonce 가 없는 purge 는 로컬 nonce 가 유일한 자리인지, DB 안 challenge 표를 둘 가치가 있는지.
- `docs/DEPLOY.md:536` 「이 도구」 의 deploy 단계가 `ship.sh` 를 비 TTY 로 부르는지(저장소 grep 0건 · 주석 2건) — 부르면 그 도구가 사람 TTY 안에서 도는지 확인 뒤 면제 · 편입 결정.
- T14 실측 결과(bypass 세션 deny 적용 O/X) — X 면 이 intent 의 스크립트 검사가 bypass 세션의 유일한 경계가 된다(총괄 계획 `:199`).
- `harness-contract-selftest` vs `dev-reseed-selftest` 등록 자리 · `services/core-api` venv 가 필요한 시험이 contract-gates 잡 환경에서 도는지(`run.sh:743` 면제 선례).
- `infra/prod/ship.sh` 편입 시점(Q6-1 ⓑ) — dev 1회 실측 뒤.
- `deploy_doctor` 가 인가 기록을 항목으로 읽을지(15/15 표 변경 = 별도 판정).
- `reset_dev_environment.py` 의 파괴 phase 집합(`schema` · `s3-apply` 외)과 `count` · `s3-plan` 의 면제 여부.

## 범위 밖 (명시 제외)
- `infra/dev/tag-release.sh` — push 하지 않고 명령만 출력 · 원격 반영은 사람 1줄(`:10` · `:62` · `:76`) · Q-E ⓐ 확정 제외.
- prod 배포 — `infra/prod/ship.sh` · `prod-YYYYMMDD` 태그 · product ruleset · 수동 절차(`docs/DEPLOY.md §5-9` · `deploy.md:7`). Q6-1 ⓑ 편입은 후속 판정.
- GitHub 에이전트 전용 PAT(T11 · 대기) · develop ruleset(T1 · 적용 완료).
- `.claude/settings.json` `permissions.deny`(PR 3 3-1 소유) — ask 후보 7종 중 스크립트가 아닌 항목(`lifecycle prune --apply` · `git push * --tags` · `Edit(.claude/settings.json)`)은 deny · git-guard 담당이며 이 intent 의 토큰 대상이 아니다.
- `services/core-api/ops/reset_product_environment.py`(Q6-2 ⓐ 기준) · `dev-reseed/reseed.sh` 의 reset 외 단계.
- `audit.jsonl`(PR 2 P2 · hook 판정 로그) 자체 · X 측정(`metrics.py`) — 인가 기록은 그 입력이 될 뿐 이 intent 가 집계기를 만들지 않는다.
- S-dep(dependency-audit) · 제품 삭제 op 개방(`deploy.md:42` 「범위 늘리기」 금지 유지).

## 참조
- 기획 원본: 없음 — 원천은 부모 intent 「판정 기록」(5라운드 설계 원칙 `:600` · 7라운드 Q-C ⓐ · Q-E ⓐ `:607` · 8라운드 ⑩ `:610`).
- 부모 intent: `dev-package/intent/2026-09-25-harness-improvement.md`(A3 `:119-125` 경계 표기 · 제약 `:42` 권한은 Ted).
- 총괄 계획: `dev-package/prd/specs/S-HARNESS-IMPROVEMENT-PLAN-20260926.md` — §0 `:10` · §1 행 9 `:26` · 3-1 `:103` · 4-4 `:120` · S-auth 행 `:131` · S 병합 조건 `:133` · §3 `:165-166` · §5 `:189` · §6 #6 `:199` · #10 `:203` · T13 `:85` · T16 `:88`.
- 저장소 밖 근거: `~/.claude/reports/harness-state-20260925/system-first-recut/recut.md`(Q6 ⓐ) · `playbook-gap-20260926/direction.md`(격차 4 · governance layer 3 「human gate — a specific person must authorize」).
- 선례 · 코드: `dev-package/tools/dev-reseed/stages.sh:211-241` · `:262-370`(정지 게이트 · 토큰식 · 기록) · `dev-package/tools/dev-reseed/tests/reset-gate.sh:421-440`(pty 시험) · `gates/tools/dev-reseed-selftest.sh:78` · `.agents/skills/dev-reseed/SKILL.md:120-152` · `.agents/rules/deploy.md:40-75` · `scripts/harness/hooks/git-guard.sh:171-184`(⑹) · 커밋 `82853609` · `de424165` · `968d16a1` · `infra/dev/ship.sh:12-21` · `:47-55` · `infra/_lib/ship-gate.sh:10` · `infra/dev/tests/ship-gate.sh:31` · `services/core-api/ops/purge_datasets.py:99-105` · `:152-160` · `services/core-api/ops/reset_dev_environment.py:198` · `:824-837` · `scripts/tests/test_harness_release_evidence.py:96-104` · `infra/dev/install-cron.sh:49` · `docs/DEPLOY.md:536`.
- ADR: `docs/decisions/0003-human-approval-machine-checks-form.md`(승인은 사람 · 기계는 형식 판정) · ADR-0011 후보 ①(총괄 계획 4-4) · 새 ADR 후보(Q11).
- spec: `dev-package/prd/specs/S-HARNESS-SAUTH-<날짜>.md`(승인 뒤 작성 · 총괄 계획 §2 S 블록을 V-id · 시험 · 레인 지시로 확장).
- 라운드 파일: `dev-package/prd/rounds/R-HARNESS-PR-CENTRIC.md`
- 결정: 〈N〉 (병합 시 기입)
