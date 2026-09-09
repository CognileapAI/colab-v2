# 작업별 시작·검증·인계 증거

Claude와 Codex는 `.claude/hooks/lifecycle_contract.py`의 같은 판정을 사용한다.
이 계약은 작업 증거 검증이다. OS 쓰기 차단이나 증거 서명을 제공하지 않는다.
기존 H6의 모든 미추적 파일 차단과 H7의 mtime 선택·깨진 JSON/준비 실패 허용은
2026-09-09 승인된 동등성 수용 기준에 따라 아래 계약으로 대체한다.

## 시작

`researcher` 또는 `lane-worker` 역할의 작업은 수정 전에 지정 사본 루트에서 시작 기록을 만든다.
이 역할 계약을 일반 부모 문서 작성자의 권한으로 해석하지 않는다. 부모가 승인된 intent로 spec을
직접 작성할 때 `researcher`로 가장해 등록하지 않는다. researcher의 산출물 경로는 sessions/reports/intent로
제한되며 specs를 추가해 통과시키지 않는다. 부모의 spec 인계는 승인 범위·파일 경로·실제 내용 hash를 확인한다.
Windows에서는 `scripts/dev.ps1 bridge lifecycle <인자>`로 같은 WSL 경로를 쓴다.
Linux에서는 `python3 scripts/agent-bridge.py lifecycle <인자>`다.
시작 기록은 해당 checkout의 private Git 디렉터리에 보관하므로 제품 파일이나 승인 문서를 쓰지 않는다.

```bash
python3 scripts/agent-bridge.py lifecycle begin --role researcher
python3 scripts/agent-bridge.py lifecycle begin --role researcher --artifact dev-package/intent/new-draft.md
python3 scripts/agent-bridge.py lifecycle begin --role lane-worker --gate contract-lint --report dev-package/reports/<회차>/<레인>/gate-summary.json
```

위 명령은 서로 다른 작업 예시다. 자신의 작업에 맞는 명령 하나를 실행하고 반환된 `task_id`를 보존한다.
부모가 필수 산출물·게이트·사본을 지정하며, 작업자가 이를 줄여 성공시키지 않는다.
`--agent-id`를 실제로 알고 있으면 함께 제공한다. 이 값이 있으면 종료 이벤트의 ID도 대조한다.
등록 자체가 자동 시작 기록 생성을 뜻하지 않는다. 역할은 이 명령을 실제로 실행해야 한다.
시작 뒤 baseline을 재설정해 이 작업의 미인계 파일을 기존 파일처럼 만들지 않는다.
이전 작업 기록을 새 작업에 재사용하지 않는다. 실제 런타임의 agent_id 제공 여부는 별도 검증 대상이다.

## 게이트

```bash
COLAB_TASK_ID=<task_id> COLAB_GATE_REPORT_DIR=dev-package/reports/<회차>/<레인> bash gates/run.sh contract-lint
python3 scripts/agent-bridge.py verify-report --task <task_id> --report dev-package/reports/<회차>/<레인>/gate-summary.json --gate contract-lint
```

복수 필수 게이트는 `begin --gate A --gate B --report ...`로 선언하고
`COLAB_TASK_ID=<task_id> bash gates/run.sh task` 한 명령으로 실행한다.
Windows에서는 환경값을 설정한 뒤 `scripts/dev.ps1 gate task`다. 이 실행은 선언된 게이트를 각각 한 번만 실행하고 한 run_id 아래 전수 결과를 낸다.
독립된 부분 실행들을 사후 합산하지 않는다. 기존 `gates/run.sh <게이트>`와 `all` 인터페이스도 유지한다.

보고서는 시작 시 선언한 새 디렉터리에만 쓴다. 다른 보고서를 찾아서 쓰지 않는다.
매 실행 시작에 새 run_id를 기록하고 이전 보고서는 private Git 디렉터리에 보존하며 활성 위치에서 제거한다.
배출이 실패해도 이전 green을 읽을 수 없고, 옛 JSON을 되돌려 놓아도 run_id 불일치로 차단한다.
실행기는 게이트 시작 전과 종료 후의 추적/미추적 비무시 파일 전체를 hash로 묶는다.
지정 보고서 디렉터리와 Git이 무시하는 런타임 의존·생성물은 입력에서 제외한다.
검사 코드·fixture는 제외하지 않는다. 최대 8개 파일을 병렬로 읽되 매 검사마다 전체 내용 hash를 다시 계산한다. 숨겨진 외부 입력·실행 도구 버전의 동일성을 이 hash만으로 주장하지 않는다.
파일이 검사 중 또는 검사 후 바뀌었거나 필수 게이트·유효한 3계수·성공 종료코드가 없으면 H7은 차단한다.
미커밋 작업도 실제 파일 내용으로 검증되므로 검사를 위해 임의 커밋할 필요가 없다.
`--task` 없는 기존 `verify-report`는 clean checkout과 HEAD tree 대조를 유지한다.

## 인계

```bash
python3 scripts/agent-bridge.py lifecycle handoff --task <task_id> --mode read-only --summary '실제 조사 결과와 근거'
python3 scripts/agent-bridge.py lifecycle handoff --task <task_id> --mode draft-return --summary '미승인 초안 내용과 열린 질문'
python3 scripts/agent-bridge.py lifecycle handoff --task <task_id> --mode artifacts --summary '작성한 파일, 미승인 상태, 전달 대상'
python3 scripts/agent-bridge.py lifecycle handoff --task <task_id> --mode complete --summary '구현 결과와 실제 검증 결과'
```

해당하는 명령 하나를 실행한다. 출력된 `COLAB_HANDOFF {…}` 한 줄을 최종 메시지에 그대로 포함한다.
`read-only`와 `draft-return`은 작업 파일 무변경을 요구한다. 초안 본문도 부모가 사용할 수 있게 반환한다.
`artifacts`는 시작 시 선언한 파일의 실존·현재 hash와 이 작업 변경 파일을 대조한다.
기존 무관한 미추적 파일은 허용하고 이 작업의 누락·미인계 산출물과 범위 밖 변경은 차단한다.
파일 인계는 승인이나 커밋이 아니다. 다음 사본에 파일을 복사하면 부모가 hash를 대조한다.
`complete`는 lane-worker의 현재 작업 게이트 증거를 요구한다.
시험 fixture의 승인 응답은 시험 데이터다. 실제 제품 승인 기록으로 옮기지 않는다.
