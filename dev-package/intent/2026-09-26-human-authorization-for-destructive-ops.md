# Intent: 파괴·외부 반영 스크립트의 사람 인가 — TTY + 1회용 토큰 + `authorized_at` 기록(S-auth)
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
- 비 TTY 호출(에이전트 · 파이프 · `bash -c` · Codex bridge · Workflow 레인)은 자격증명 · 네트워크 · DB 접속 전에 거부한다 — 종료코드는 〈판정 대기〉(Q4 · 권고 77) · stderr 1줄(토큰 값 없음 · 사람이 밟을 절차 이름만).
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

## 설계트리 (grill-me 결과)
- Q1 인가 기제의 공통 자리 → 〈판정 대기〉. ⓐ 공통 모듈 1벌 — Python(`services/core-api/ops/` 안 · purge · reset 공용)과 bash(`infra/_lib/` · ship.sh · reseed stages 공용) 두 구현이 같은 스키마 · 같은 토큰식 · 같은 시험 fixture 를 공유 ⓑ 스크립트마다 개별 구현. 권고 ⓐ — `ship-gate.sh:4-7` 「복사본은 갈린다」 선례 · 기록 스키마 1개는 ⓐ 로만 고정된다.
- Q2 토큰 발급 채널 → 〈판정 대기〉. ⓐ 2단계 — 첫 실행(토큰 없음)이 거부하며 challenge 를 발급하고 토큰을 `[ -t 1 ]` 터미널에만 찍는다 · 사람이 같은 터미널에서 토큰 env 를 두고 다시 부른다(reseed `stages.sh:227-241` · `SKILL.md:136-139` 와 같은 모양) ⓑ 별도 발급 명령이 `~/.local/state/colab/auth/<id>.json`(0600) 에 토큰을 두고 스크립트가 읽어 소진 ⓒ 같은 실행 안 `/dev/tty` 프롬프트(`read -s`)에 challenge 를 되받는다. 권고 ⓐ — reseed 와 같은 기제라 복제가 아니라 확장이고, 같은 사용자 에이전트가 읽을 수 있는 파일 자리(ⓑ)를 만들지 않으며, ⓒ 는 pty 자동 응답에 ⓐ 와 같은 노출이면서 발급·소진 2단 기록이 없다.
  - Q2a nonce · 소진 상태의 보관 자리 → 〈판정 대기〉. ⓐ 원격 — ship · reset 은 dev 호스트(sudo 로만 읽힘 · reseed 선례) · purge 는 원격 자리가 없어 DB 안 표(운영자 감사 계열) ⓑ 로컬 `~/.local/state/colab/auth/`(0600 · 같은 사용자 에이전트가 읽어 재계산 가능 — reseed 문서의 「남는 경로」와 같은 수준) ⓒ 스크립트별 — 원격 자리가 있으면 원격 · 없으면 로컬. 권고 ⓒ — reseed 의 원격 nonce 를 유지하고 purge 만 로컬을 쓴다 · 남는 경로는 `deploy.md:69-72` 와 같은 문장으로 기록하고 경계라고 적지 않는다.
- Q3 토큰 결속 · 수명 → 〈판정 대기〉. ⓐ 대상 결속 — 토큰 = `sha256(지문 ‖ "\n" ‖ nonce)` · 지문 = purge(lab · `--id` 정렬 목록 · DB 호스트) / reset(target · phase · 이번 계수 sha256) / ship(FULL_SHA · environment · PRE evidence sha256) · 만료 1800초(reseed `RESET_ACK_TTL_SECONDS`) · 1회 소진 ⓑ 무결속 세션 토큰 · 만료 300초. 권고 ⓐ — 다른 대상에 재사용되는 토큰은 사고 회차(다른 id · 다른 sha)를 막지 못한다 · reseed 식과 동일해 확장이다.
- Q4 비 TTY · 토큰 불일치의 거부 종료코드 → 〈판정 대기〉. ⓐ 77(sysexits `EX_NOPERM` · 65 거절 · 78 준비 실패 · 2 인자 오류와 구분) 대상 전 스크립트 공통 ⓑ 각 스크립트의 기존 거부 코드(purge 2 · reset `_REFUSE` 2 · ship 65). 권고 ⓐ — 시험 · 게이트 · 에이전트 출구가 「인가 부재」를 「인자 오류」 · 「비조상」과 한 값으로 구분한다 · 기존 코드 의미(2 · 3 · 65 · 78)는 무변경.
- Q5 검사 위치 · 면제 경로 → 〈판정 대기〉. ⓐ 행위 직전 — 인자 · 증거 · 조상 검사 뒤 · 자격증명 · 네트워크 · DB 접속 앞(ship `:47` SSH 배열 앞 · purge `:129` connect 앞 · reset 각 phase 의 DROP/DELETE 앞) · 면제 = 행위 없는 경로(`COLAB_RELEASE_DRY_RUN=1` · `--yes-delete` 없음 · `--dry-run` · `--phase count` · `--preflight-only`) ⓑ 진입 즉시 모든 경로 TTY 요구(기존 비 TTY 시험 2곳이 깨진다 · dry-run 도 사람만 돌린다). 권고 ⓐ — dry-run 은 에이전트가 계수·계획을 보는 정당한 경로이고, 행위 없는 경로에 TTY 를 요구하면 시험과 advisor 게이트 ③ 입력을 잃는다. 시험명 선례 `test_shell_entries_fail_before_credentials_or_network_without_evidence`.
- Q6 범위의 가장자리 → 〈판정 대기〉. Q6-1 `infra/dev/ship.sh` dev 반입에 prod 와 같은 강도의 인가를 두는가: ⓐ 둔다(Q-E ⓐ 확정 범위 · dev 는 사람 자료가 있었던 환경) · `infra/prod/ship.sh` 는 이번 범위 밖(태그 + 사람 실행 + ruleset) ⓑ prod 도 같은 공통 함수를 부르게 한다(「한 벌」 원칙). 권고 ⓐ — 범위는 7라운드 확정대로 두고 prod 편입은 1회 실측 뒤 별도 판정(미해결에 둔다). Q6-2 `services/core-api/ops/reset_product_environment.py` 포함 여부: ⓐ 제외 — 승인 입력 hash 검증 · 최초 실행 경계(`deploy.md:79-87`)가 이미 별도이고 총괄 계획 S-auth 행에 없다 ⓑ 포함. 권고 ⓐ.
- Q7 인가 기록의 자리 · 스키마 · 소비자 → 〈판정 대기〉. ⓐ 실행 자리 JSON 1개(reseed `reset-ack.json` 선례 · schema `colab-ops-authorization/1` · `authorized_at`(UTC) · `operator` · `script` · `target` 지문 · `tokenSha256` · `nonceSha256` · `decision` · `exit`) · ship.sh 는 `RELEASE_PRE.json`(`:54-55`) 옆에 EC2 로도 실어 `deploy_doctor` 가 읽을 수 있게 ⓑ 로컬 append-only `~/.local/state/colab/authorizations.jsonl` 하나 ⓒ ⓐ + ⓑ. 권고 ⓐ — 게이트 · CI · doctor 는 실행 자리 · EC2 만 읽을 수 있고 홈 디렉터리는 못 읽는다 · `deploy_doctor` 항목 추가 여부(15/15 표 변경)는 미해결 · 로컬 집계는 X 측정(`metrics.py`)의 입력으로 별건.
- Q8 에이전트가 거부를 만났을 때의 출구 → 〈판정 대기〉. ⓐ 종료코드(Q4) + stderr 1줄(「사람이 자기 터미널에서 <스크립트> 를 다시 연다 — 토큰은 그 터미널에만 보인다」 · 토큰 값 · 완성 명령 없음 — reseed `SKILL.md:136` 「붙여 넣을 완성 명령은 찍지 않는다」 유지) → 에이전트는 재시도 · env 주입 없이 `handoff --mode blocked`(PR 2 2-4 이후 · 현재 `lifecycle_contract.py` 미구현)로 넘기고, 그 전에는 최종 메시지에 절차 1줄(토큰 자리는 `<token>` 표기) ⓑ stderr 에 붙여 넣을 완성 명령을 찍고 에이전트가 사용자에게 토큰을 물어 대신 넘긴다. 권고 ⓐ — ⓑ 는 git-guard ⑹ 이 막는 「에이전트가 값을 채우는」 경로 그 자체다. 역할 문서(`lane-worker` · `researcher`)에는 「거부 코드 = 정지 · 인계」 1줄만.
- Q9 git-guard ⑹ 확장 · deny 와의 관계 → 〈판정 대기〉. ⓐ 토큰은 env 이름으로 받고(`COLAB_RESEED_ACK_NONEMPTY` 와 같은 꼴 · 이름은 spec) ⑹ 의 이름 목록에 추가 · 시험 `test_harness_lifecycle_contract.py`(`de424165` 의 25줄) 갱신 · PR 3 3-1 deny 목록은 이 intent 가 손대지 않는다(소유 PR 3) ⓑ 토큰을 argv 플래그로만 받아 ⑹ 무변경(할당 꼴이 없어 hook 적용 불가 · 값이 `ps` · 셸 이력 · 단계 로그에 남는다). 권고 ⓐ — env + ⑹ 확장이 reseed 와 같은 모양이고 argv 는 sha256-only 원칙을 깬다.
- Q10 시험 · 게이트 등록 → 〈판정 대기〉. ⓐ `scripts/tests/test_ops_authorization.py` 신설(비 TTY → 거부 코드 · pty(`pty.spawn`) + 잘못된 토큰 → 거부 · pty + 토큰 → 진행(가짜 ssh · DB) · 만료 · 재사용 거부 · 기록 필드 전부 · 토큰 평문이 실행 자리 · 로그에 0건) + `infra/dev/tests/ship-gate.sh` pty 사례 + `reset-gate.sh` 무변경 green · 실행 게이트 = `harness-contract-selftest`(총괄 계획 S-auth 행) 또는 `dev-reseed-selftest`(`gates/tools/dev-reseed-selftest.sh:78` 가 `reset-gate.sh` 를 이미 돈다) — 등록 자리는 spec ⓑ 스크립트별 시험만 · 게이트 등록 없음. 권고 ⓐ — 게이트에 없는 시험은 CI 에서 조용히 빠진다(`gates/run.sh:726` 선례).
- Q11 ADR 자리 → 〈판정 대기〉. ⓐ ADR-0011(PR 4 4-4 · ① 「승인 의미 판정 ≠ 인가 토큰 존재 검사」)에 이 기제를 근거 줄로만 연결 · 새 ADR 없음 ⓑ 새 ADR(번호는 PR 4 병합 뒤 다음 번호) 「파괴·외부 반영 스크립트는 TTY + 1회용 토큰 + 인가 기록을 요구한다 · 토큰 검사는 형식 판정이며 승인이 아니다(ADR-0003)」 + ADR-0011 ① 참조. 권고 ⓑ — 부모 intent 제약 「새 규칙은 새 ADR」 · ADR-0011 은 PR 4 소유라 S-auth 가 편집하면 이력 수정이 된다.

## 미해결 질문
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

## 확인
- 프론티어 공집합 확인: 〈판정 대기〉
- Ted 확인 문장(원문 그대로): "〈판정 대기〉"
- 재개봉 금지: 〈판정 대기〉
- dev 1회 실측 기록(ship.sh 반입 1건 · purge dry-run 1건 · 비 TTY 거부 1건 · 총괄 계획 `:133`): 〈판정 대기 · 병합 전 기입〉
- 시험 · 게이트 green 기록(`test_ops_authorization.py` · `ship-gate.sh` pty · `reset-gate.sh`): 〈판정 대기 · 병합 전 기입〉

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
