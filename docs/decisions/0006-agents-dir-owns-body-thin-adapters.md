# ADR-0006: 공통 본문은 .agents/ 가 소유하고 도구별 파일은 얇은 어댑터다

- 상태: accepted
- 날짜: 2026-09-17
- 대체함: 없음
- 대체됨: 없음

## 배경
Claude와 Codex 두 도구가 같은 규칙·역할·스킬을 읽는다. 각 도구 디렉터리에 본문을 따로 두면 두 벌이 갈린다.
전환 방향은 공통 경로 소유로 이미 적혀 있다 — `docs/development/dual-agent.md:18` 「규칙·역할·스킬과 훅의 공통 본문은 공통 경로에 두고 기존 Claude 진입점은 어댑터로 유지한다.」
같은 전환의 인계 기록도 같은 말을 한다 — `docs/development/harness-transition-handoff.md:8` 「develop 변경과 하네스의 충돌 6곳 해소. 공통 규칙 원본과 얇은 Claude 어댑터 유지.」
소유·어댑터 대응표는 `docs/development/dual-agent.md` 「원본과 도구별 연결」 절(15행 이하)에 이미 상세하다. 이 ADR은 그 표를 복제하지 않는다.

## 결정
규칙·역할·스킬·판정부의 본문은 `.agents/`와 `scripts/harness/`가 단독 소유한다.
`.claude/`·`.codex/`는 등록과 payload 변환만 소유하며 본문을 복제하지 않는다.
소유·어댑터 목록의 기계 정본은 `.agents/harness.yaml`의 `sources`(39-50행)와 `adapters`(51-61행)이고,
`harness-contract` 게이트가 그 구조를 검사한다 — `gates/README.md:9` 「`.agents/harness.yaml`의 공통 원본·adapter·필수 gate·0/1/78 계약 누락과 경로 이탈」.
전환 순서 제약을 결정에 포함한다 — `docs/development/dual-agent.md:19-20` 「실행 중인 훅 이전은 원본 복사 → 소비자 경로 전환 → 기존 진입점 어댑터화 순서로 한다.
기존 진입점을 먼저 없애면 PreToolUse 자체가 실패하여 복구 도구까지 차단된다.」
자세한 대응은 `docs/development/dual-agent.md` 「원본과 도구별 연결」 절을 본다.
승인 근거: `docs/development/harness-transition-handoff.md:26` 「## 현재 운영 범위 — 2026-09-15 사용자 승인」.
게이트 통과가 승인이 아니라는 전제는 [ADR-0003](0003-human-approval-machine-checks-form.md)을 따른다 — `harness-contract` green은 구조 판정이다.

## 검토한 대안
- 도구별로 규칙 본문을 복제해 유지 — 배제. 두 벌이 갈리는 순간 어느 쪽이 정본인지 판정할 자리가 없어진다. 어댑터 파일이 본문을 복제하지 않는다는 규약은 실물에 남아 있다 — `.claude/rules/colab-rules.md:5` 「이 파일의 Claude frontmatter는 도구별 등록 정보이며 공통 본문을 복제하지 않는다.」, `CLAUDE.md:6` 「진입·인계 절차는 `AGENTS.md`가 우선하며, 이 파일에는 제품 본문을 복제하지 않는다.」
- 한쪽 도구만 지원하고 다른 쪽을 포기 — 배제. 두 도구를 함께 쓰기로 한 전환 자체가 무의미해진다.
- 어댑터 등록이 서로에게 자동 적용된다고 가정 — 배제. `AGENTS.md:34` 「Claude의 paths 메타데이터가 Codex에서 자동 적용된다고 가정하지 않는다.」 본문 소유를 한쪽에 둔다고 등록까지 공유되지는 않는다.
- 어댑터를 먼저 지우고 공통 경로로 한 번에 옮기기 — 배제. 위 전환 순서 제약대로 복구 도구까지 막힌다.
- `.claude/skills/<이름>`을 `.agents/skills/<이름>` symlink 로 미러(외부 `sungwooHa/ai-sdlc-harness` 방식) — 미채택. Windows/NTFS 체크아웃과 Codex 스킬 로딩의 symlink 호환을 확인하지 않았고 텍스트 어댑터는 두 환경에서 동작한다(재검토 조건: `docs/development/dual-agent.md` 「보류 중인 외부 장치」).

## 결과와 감수한 비용
- 얻는 것: 규칙 한 곳을 고치면 두 도구에 같은 본문이 적용된다. 정본 판정 자리가 하나다.
- 부담: 도구별 등록·권한·모델·격리는 여전히 각 어댑터가 따로 소유하고 자동 적용되지 않는다. 그 차이는 `docs/development/dual-agent.md`가 관리한다.
- 어댑터 파일이 한 단계 더 붙으므로 본문에 닿기까지 읽을 파일이 하나 늘어난다.
- 전환 중에는 옛 진입점을 어댑터로 남긴 기간이 생긴다. 그 기간의 중복은 순서 제약이 요구하는 비용이다.

## 재검토 조건
- 도구가 하나로 줄거나 세 번째 도구가 추가되어 `adapters.required_files` 집합이 바뀔 때.
- 본문 경로 소유가 `.agents/` 밖으로 옮겨질 때(`.agents/harness.yaml`의 `sources` 변경).
- 실행 중인 훅 이전이 끝나 옛 진입점 어댑터가 더는 필요 없어질 때 — 그때 순서 제약의 적용 대상이 사라진다.
- `harness-contract` 게이트가 이 구조 검사를 더는 수행하지 않게 될 때.

## 근거
- `docs/development/dual-agent.md:15-20`(「원본과 도구별 연결」 절 머리와 전환 순서 제약). ⚠ 표 본문은 이 ADR에 복제하지 않는다.
- `.agents/harness.yaml:39-50`(`sources`) · `:51-61`(`adapters`, `required_files` 5건).
- `gates/README.md:9`(`harness-contract` 게이트가 검사하는 범위).
- `AGENTS.md:34`.
- `docs/development/harness-transition-handoff.md:8` · `:26`(2026-09-15 사용자 승인).
- 관련: [ADR-0003](0003-human-approval-machine-checks-form.md) · [ADR-0005](0005-harness-controls-are-declarative.md).
