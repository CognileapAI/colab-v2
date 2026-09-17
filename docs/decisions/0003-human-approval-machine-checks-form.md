# ADR-0003: 승인은 사람이 하고 기계는 형식만 판정한다

- 상태: accepted
- 날짜: 2026-09-17
- 대체함: 없음
- 대체됨: 없음

## 배경
ADR·PR을 스크립트로 검사하기 시작하면 「검사 통과 = 승인」으로 굳을 여지가 생긴다.
판정부 두 개의 docstring이 그 경계를 이미 적고 있다.
`scripts/harness/adr_gate.py:2` 「Validate ADR structure and replacement links; never infer semantic decision approval.」
`scripts/harness/pr_contract.py:1` 「Validate a local PR draft/completion contract; never publish or grant approval.」
`docs/decisions/README.md:20-21` 「이 명령은 구조와 상호 링크만 검사한다. 실제 결정의 타당성이나 동의를 인증하지 않는다.
자동 Stop/PreToolUse/UserPromptSubmit 훅은 등록하지 않는다.」
경계는 절차 문서와 주석에만 흩어져 있고 결정으로 승격된 적이 없다. 후속 ADR이 상속할 전제가 없다.

## 결정
결정 승인·PR 게시·병합은 사람이 한다. `adr_gate.py`·`pr_contract.py`는 구조·상호 링크·SHA 정합만 판정한다.
검사 green은 형식 판정이며 승인이 아니다. 이 판정에 자동 Stop/PreToolUse/UserPromptSubmit 훅을 걸지 않는다.
`proposed`/`accepted`/`superseded`의 구분 기준은 기계 통과 여부가 아니라 사람의 승인 근거 유무다
(`docs/decisions/README.md:7` 「`accepted`: 현재 대화 또는 연결된 실제 승인 근거가 있는 결정.」).
승인 근거: `dev-package/prd/rounds/R-HARNESS-PR-CENTRIC.md:24` 2026-09-15 사용자 개정 —
「**2026-09-15 사용자 개정:** PR 생성·게시는 사용자 담당, 에이전트는 로컬 요약·검증 근거·절차만 안내한다.
게시 대기를 이유로 독립 로컬 전환 작업을 중단하지 않는다. 이전 게시 승인 대기 기록은 이력으로 보존한다.」
이 ADR은 ADR 제도 자체의 전제이며 [ADR-0004](0004-gate-verdict-three-states.md) · [ADR-0005](0005-harness-controls-are-declarative.md) · [ADR-0006](0006-agents-dir-owns-body-thin-adapters.md)가 이것을 참조한다.

## 검토한 대안
- 승인 판정을 자동 훅에 위임 — 참조 저장소 `sungwooHa/ai-sdlc-harness@fc424e8f21f5d4479a43780e41ce9883ed1dbc7f`의 ADR 판정을 재사용하면서 CoLAB은 로컬 CLI만 남겼다. 배제 근거가 `scripts/harness/adr_gate.py:3-4` 주석에 있다 — 「Adapted from sungwooHa/ai-sdlc-harness @ fc424e8f21f5d4479a43780e41ce9883ed1dbc7f. / CoLAB adapter: local CLI only; no automatic approval or lifecycle hooks.」 ⚠ 참조 저장소가 lifecycle 훅을 등록한다는 사실 자체는 이 주석에 적혀 있지 않다. 주석이 말하는 것은 CoLAB 어댑터가 그것을 두지 않는다는 것뿐이다.
- 로컬 파일 hash 정합을 완료 판정으로 사용 — 배제. `docs/decisions/README.md:45-46` 「합성 job/green 요약이나 파일 hash만으로 통과하지 않는다. 로컬 내용 검증은 GitHub 출처 인증이 아니므로 / 지정한 실제 Actions run에서 가져온 묶음을 사용해야 한다.」
- ADR 파일 삭제·`proposed` 환원으로 결정을 철회 — 배제. `docs/decisions/README.md:8` 「`superseded`: 후속 결정으로 대체된 이력. 기존 파일을 삭제하거나 proposed로 되돌리지 않는다.」

## 결과와 감수한 비용
- 얻는 것: 게이트 통과가 결정의 정당성을 인증하지 않는다. 승인 없는 결정이 형식만으로 제도에 들어오지 못한다.
- 부담: ADR·PR 내용의 타당성은 기계가 잡지 못한다. 사람의 검토가 유일한 판정 자리로 남는다.
- 2026-09-17 추가 — Ted 「모두 권하는대로하자. 강제훅 좋아」로 **편집 시점** 훅 하나가 승인됐다. 결정 소유 경로를 바꿀 때 ADR 파일이 **존재하는지**만 보는 훅이다. 존재 검사이며 결정의 내용·승인 여부는 판정하지 않는다. 따라서 이 ADR과 어긋나지 않는다. 이 훅이 존재를 넘어 내용 정합을 보게 되면 그때는 이 ADR의 재검토 대상이다.
- 승인을 기계화하지 않았으므로 사람이 자리를 비우면 게시·병합이 대기한다. 그 대기는 독립 로컬 작업을 막지 않는다(위 Global Constraints 3항 축자).

## 재검토 조건
- `adr_gate.py`·`pr_contract.py`가 구조·링크·SHA를 넘어 결정 내용이나 원격 출처의 승인 의미를 판정하게 될 때.
- 승인 판정에 자동 Stop/PreToolUse/UserPromptSubmit 훅을 등록하기로 할 때, 또는 위 편집 시점 존재 검사 훅이 존재 여부를 넘어 내용 정합을 판정하게 될 때.
- `docs/decisions/README.md`의 세 상태 정의가 바뀌거나 PR 게시 주체가 사용자에서 에이전트로 옮겨질 때.

## 근거
- `scripts/harness/adr_gate.py:2-4` · `scripts/harness/pr_contract.py:1` docstring·주석.
- `docs/decisions/README.md:6-8,20-21,45-46,54-55` — 54-55 「push·Draft PR·Issue는 게시 대상과 내용을 먼저 보여주고 / 현재 대화의 사용자 승인을 받아야 한다. 병합·배포·기존 기록 삭제는 별도 승인이다.」
- `dev-package/prd/rounds/R-HARNESS-PR-CENTRIC.md:24` 2026-09-15 사용자 개정(축자 인용은 「결정」 절).
- `AGENTS.md:48-49` 「제품 데이터 삭제·배포·main push의 권한은 현재 대화의 사용자 승인 범위를 따른다. / 기존 승인은 유지하며, 문서나 에이전트 역할 정의 자체가 새 권한을 부여하지 않는다.」
- 2026-09-17 대화, Ted 「모두 권하는대로하자. 강제훅 좋아」 — 편집 시점 ADR 존재 검사 훅 승인.
