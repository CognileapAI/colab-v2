# 공통 하네스 전환 인계

2026-09-15. 작업 브랜치 `codex/harness-pr-centric`, 대상 저장소 `CognileapAI/colab-v2`.
현재는 마지막 로컬 검증 중이다. 이 문서는 전환 전체 완료나 배포 승인을 의미하지 않는다.

## 달라진 사용법

Claude와 Codex 모두 저장소 루트의 `AGENTS.md`에서 시작한다. 규칙·스킬·역할 원본은
`.agents/`, 검사 코드는 `scripts/harness/`다. `.claude/`와 `.codex/`는 각 도구 연결을 맡는다.
새 작업은 명시한 목적·범위·로컬 계획을 사용한다. 기존 대장·세션에 새 상태를 중복 작성하지 않는다.

```sh
python3 scripts/agent-bridge.py check
python3 scripts/harness/check.py
```

작업별 gate·산출물은 [작업 증거 절차](lifecycle-evidence.md)를 따른다.
실제 역할과 필수 게이트로 begin하고 반환된 task ID를 보존한다. 검사 생략·다른 SHA·이전 run의
보고서를 완료로 사용할 수 없다. 파일이 바뀌면 이전 검증은 그 파일의 새 근거가 아니다.

PR 요약은 목적·범위·계획·결정·검증·남은 제약의 6절을 작성한다.
기본 틀은 `.github/pull_request_template.md`, 지속 결정은 `docs/decisions/`를 사용한다.
미검증 draft를 허용하지만 '검증됨' 또는 완료 주장은 실제 CI artifact bundle을 요구한다.
CLI 인자는 `python3 scripts/harness/pr_contract.py --help`에서 확인한다.
합의본 snapshot이나 ADR 파일을 생성한 것 자체는 사용자의 승인으로 간주하지 않는다.

## 기존 상태와 배포

[작업 상태 증거](work-state.md)는 명시한 Issue/PR/task 자료를 검증한다.
기존 제품 대장은 아직 `legacy-compatibility`로 읽는다. 기존 기록은 이동·삭제하지 않았다.
최신 조사: 대장 235항목(done 178, open 52, partial 3, deferred 1, blocked 1), active 57.
HANDOFF 18행은 별도 분류 대상이며 미해결 건수나 대장과 합산한 건수가 아니다.
Issue 게시·HANDOFF 분류·기존 소비자 제거 전에는 호환 종료를 주장할 수 없다.

[배포 증거 절차](release-evidence.md)는 PR/main/CI 사전 증거와 동일 실행 doctor 사후 증거를 연결한다.
dev 태그는 사후 검증 후, prod 태그는 배포 전 사전 검증 후다. prod 성공 확정은 사후 검증이 필요하다.
이번 작업은 실제 배포·태그 생성·운영 doctor 실행을 하지 않는다. 로컬 JSON 정합은 GitHub 서명 인증이 아니다.

## 검증 결과

- 최종 고정 커밋·전수 결과: 회수 중. 과거 checkpoint 결과를 현재 트리 전체 green으로 사용하지 않는다.
- 부모 실행 `python3 -m unittest discover -s scripts/tests -v`: 313개 중 303 통과·Windows 전용 10 skipped, exit 0(25.046초).
  `infra/dev/tests/ship-gate.sh` 36, `infra/prod/tests/ship-gate.sh` 48 통과. 이 둘은 명시 mock 반입 시험이다.
  실제 release 판정부·단일 doctor 증거·번들 import 회귀는 위 unittest에 포함된다.
  공통 계약·bridge 연결·CI 필터·diff 공백 검사 exit 0. 실환경 통과를 의미하지 않는다.
- 기준선 `2e009aef`: 연결 검사·실행 비트·bridge 시험 완료, 파일 무수정. bridge 77 tests 중 Windows 10 skipped.
- 당시 '실행기 없음' 진단은 정정한다. PowerShell은 존재하며, 공식 `dev.ps1`이 UNC의 unsigned-script 정책으로 차단됐다. 정책 우회는 하지 않았다.
- Claude 합성 PR 해석 2회는 기대 객체와 일치했다. 재현 입력은 `eval/harness/pr-summary-fixture.json`이다.
  모델 응답의 runtime 표기는 `claude-haiku-4-5-20251001`, `claude-opus-5[1m]`이다.
  도구 없는 해석 평가이며 native hook·Codex 평가·양방향 인계의 통과 근거가 아니다.
- 실제 GitHub Actions, Claude/Codex native hook 허용·차단, Codex 모델 평가·양방향 인계는 미확인이다.
  Codex 호스트 검증은 정상 실행 가능한 신뢰된 공식 실행기에서 재개해야 한다.

## 사용자 PR 게시 절차

1. 아래 최종 검증 대상 SHA와 `git rev-parse HEAD`, `git status --short`를 대조한다.
2. `CognileapAI/colab-v2`의 base `main`, head `codex/harness-pr-centric`로 사용자가 게시한다.
   push도 에이전트가 실행하지 않았다. 직접 게시할 때 원격 대상과 계정을 확인한다.
3. 제목 예시: `Claude·Codex 공통 PR 중심 하네스 전환`.
   본문에는 위 6절과 로컬 검증 결과, 원격 CI 미실행, 호환 종료 미완료를 그대로 적는다.
4. 게시된 정확한 SHA의 `required-gates`와 producer artifacts를 확인한다.
   로컬 시험 결과를 실제 Actions 성공으로 대체하지 않는다.
5. Issue·ruleset 적용은 내용·대상을 별도 검토한다. 제안은 `github-ruleset.json`이며 원격 미적용이다.
   병합·배포·기존 기록 삭제는 각각 별도 승인 대상이다.

기존 변경 보존용 stash `c11809dc6bfc51a9783e7f6ba5f93bf571493afe`는 복원 후에도 삭제하지 않았다.
`30 CoLAB-v2`는 접근·변경하지 않았다.
