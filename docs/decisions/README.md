# 결정과 PR 인계

새 ADR은 필요한 결정에만 선택적으로 작성한다. 파일명은 `0001-lowercase-slug.md`,
제목은 `# ADR-0001: 결정 제목`이다. `_template.md`를 사용한다.

- `proposed`: 검토 중인 제안. 문서 작성이나 검사 통과가 승인이 아니다.
- `accepted`: 현재 대화 또는 연결된 실제 승인 근거가 있는 결정.
- `superseded`: 후속 결정으로 대체된 이력. 기존 파일을 삭제하거나 proposed로 되돌리지 않는다.

대체 시 옛 ADR의 `대체됨`과 새 ADR의 `대체함`을 각각
`[ADR-0002](0002-new-choice.md)` 형식으로 서로 연결한다. ID 중복·없는 대상·순환은 허용하지 않는다.
기존 `dev-package/PLAN-SoT.md`의 승인·번호·이력은 그대로 보존하며 필요할 때 링크한다.
새 ADR의 도입으로 기존 승인을 소급 재심사하거나 새로운 승인을 만들어내지 않는다.

```bash
python3 scripts/harness/adr_gate.py --all
python3 scripts/harness/adr_gate.py --staged
```

이 명령은 구조와 상호 링크만 검사한다. 실제 결정의 타당성이나 동의를 인증하지 않는다.
자동 Stop/PreToolUse/UserPromptSubmit 훅은 등록하지 않는다.

## 합의본 보존

기존 승인된 로컬 초안 폴더의 `intent.md`, `spec.md`, `plan.md`, `scope.json`과
`deliverables/*.html` 중 존재하는 파일을 `agreements/<revision>`에 보존할 수 있다.
`spec.md` 또는 `plan.md`가 필요하고 파일은 비어 있지 않아야 한다.
이미 있는 revision을 덮어쓰지 않으며 hash·경로·symlink를 검사한다.
이 선택적 보존 도구는 기존 작업에 새로운 승인 절차를 부과하지 않는다.
`--approval-ref`에는 현재 대화의 기존 승인 참조를 기록한다. 문자열 기록은 동의 인증이 아니다.
작업 runtime의 선언되지 않은 하위 파일을 만드는 데 사용하지 않는다. 별도로 지정한 로컬 초안 폴더에서 실행한다.

```bash
python3 scripts/harness/agreement_snapshot.py <초안폴더> --repo <저장소루트> --revision 001 --approval-ref '<기존 승인 참조>'
python3 scripts/harness/agreement_snapshot.py <초안폴더>/agreements/001 --check
```

## PR 초안과 완료 판정

`.github/pull_request_template.md`의 목적·범위·계획·결정·검증·남은 제약 여섯 절을 짧게 채운다.
그림·세 상자·가치 확인·볼 곳·증거 별도 절은 선택이다. 검증 절의 기대→실제→근거 한 문단으로도 충분하다.
Plan-Ref, 전체 Head-SHA와 실제 검증 상태를 적는다. 초안은 미검증 상태로 검사할 수 있다.
완료 판정 및 Draft의 ‘검증됨’ 주장에는 head가 일치하는 CI evidence와 실제 producer artifact 묶음이 필요하다.
등록표의 producer/check 집합·SHA/tree/run/attempt·필터 적용·실제 gate 행과 종료값을 재검사한다.
합성 job/green 요약이나 파일 hash만으로 통과하지 않는다. 로컬 내용 검증은 GitHub 출처 인증이 아니므로
지정한 실제 Actions run에서 가져온 묶음을 사용해야 한다.
CLI에 전달한 evidence 파일의 SHA-256을 본문의 `Evidence-SHA256`과 대조한다.

```bash
python3 scripts/harness/pr_contract.py <PR본문.md> --head <40자리SHA> --mode draft
python3 scripts/harness/pr_contract.py <PR본문.md> --head <40자리SHA> --mode complete --evidence <ci-evidence.json> --artifact-root <producer-artifacts>
```

통과는 로컬 문서·증거 정합 판정이다. push·Draft PR·Issue는 게시 대상과 내용을 먼저 보여주고
현재 대화의 사용자 승인을 받아야 한다. 병합·배포·기존 기록 삭제는 별도 승인이다.

## 출처

순수 ADR 판정과 합의본 보존은
`sungwooHa/ai-sdlc-harness@fc424e8f21f5d4479a43780e41ce9883ed1dbc7f`의
`scripts/adr-gate.py`, `scripts/harness/agreement-snapshot.py`를 재사용했다.
PR 표현 구조는 같은 revision의 `docs/changes/_templates/pr.md`를 적용했다.
CoLAB의 기존 승인 경계·제품 검사·역할/훅 등록은 이 참조로 변경하지 않는다.
