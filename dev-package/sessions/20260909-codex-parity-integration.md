# Codex parity 통합 복제본 조립

## 기준과 범위

- 쓰기 checkout: `<repo-root>`
- 브랜치: `codex-parity-integration`
- 새 base: `95c85bef7f2c65875812c88647f9dadf4f4c315d`
- 원본: `source-repo` (읽기 전용 원본 label)
- 후보 목록 98개와 통합 산출물 4개, 합계 102개를 manifest에 기록하고 source/target SHA-256과 mode를 구분했다.
- 외부 최종 수용 요약을 `eval/harness/results/codex-40-final-acceptance-20260909.json`으로 compact 보존했다.
- 위치 정보가 있던 원본 증거 10개는 저장소 밖 `external-raw:` label 아래 SHA-256과 함께 보존하고, 저장소 증거는 portable token을 쓴 compact/sanitized JSON으로 유지한다.
- `.gitignore`에는 `/.codex/worktrees/`만 추가했다.

## 포함과 제외

포함 범위는 Codex/Claude bridge, 공통 훅·규칙·스킬, 역할 설정, parity 문서, 결정적 harness 결과 요약, runner와 회귀검사다. `CLAUDE.md`는 원본의 bridge 안내 3줄 외 제품 변경이 없음을 확인하고 복사했다.

원본 Git status의 후보 밖 164개 경로는 제외했다. 제품 파일과 제품 세션, DB/Alembic, `dev-package/03-HANDOFF.md`, `dev-package/work-items.yaml`, `R-PRODUCT-FINISH.md`, `.codex/artifacts`, `.codex/environments`, `.codex/worktrees`, raw JSONL/stderr/txt, active-a/active-b 원로그 및 pending 결과를 포함하지 않았다. 후보의 `eval/harness/results/agent-browser-core-0.27.0.txt`는 실행 원로그가 아니라 agent-browser 스킬 원문을 고정한 bridge 입력이므로 포함했다.

## 수용 상태

Codex **40/40**은 기존 `gpt-6-astra` 전체 평가 이력이다. 이번 통합은 full40 모델 실행을 하지 않았으며, 새 Sol/Astra 역할 행동 증거를 만들거나 주장하지 않는다. 전체 parity 수용은 미완료다. Claude 신규 전체40회, Claude 실제 개발 E2E, 데스크톱 앱 재시작 후 최신 코드 검증이 남아 있다.

Alembic은 **N/A**다. 이번 통합에는 제품 코드·DB schema·migration 변경이 없다.

## 빠른 검증

- `python3 scripts/agent-bridge.py check`: 역할 4, 스킬 12, 훅 9 / 이벤트 5, exit 0.
- `python3 -m unittest discover -s scripts/tests -v`: 111 통과, 플랫폼 제외 10, 실패 0, exit 0.
- `bash eval/harness/tests/run-selftest.sh`: 15/15 기대 일치, 모델 호출 0, exit 0.
- manifest 102 entries의 source/target hash 오류 0, `git diff --check` 통과를 부모가 독립 확인했다.
- native Windows Codex `0.153.4` strict-config version은 exit 0이고 `WindowsLauncherTests`는 10/10 통과했다.
- native Windows 전체 discover 한 시도에서는 관련 없는 Linux 전용 CI schema test가 Windows shell 때문에 실패했다. 전체 Windows green으로 확대하지 않는다. 해당 Linux test는 WSL 111개 실행에서 통과했다.

## Sol/Astra 역할 활성화 probe

native CLI `0.153.4`, strict config, ephemeral, workspace-write 조건에서 저장소 수정 금지 프롬프트로 named role probe를 수행했다. controller thread는 `01a08510-53d3-7862-82fa-53d5320736b5`, process exit은 0이며 probe에 따른 저장소 변경은 0개다.

현재 CLI에서 사용 가능한 spawning tool은 named custom agent인 `researcher`와 `advisor`를 선택할 수 없다고 보고했고 shell read도 policy에 차단됐다. 두 역할은 호출되지 않았고 generic agent로 대체하지 않았다. 따라서 named-role 실행은 **사용 불가(unavailable)**였고, TOML의 `researcher = gpt-5.6-sol`, `advisor = gpt-6-astra` 모델 매핑과 strict parse/회귀는 green이지만 actual custom-role runtime model은 **미확인**이다. desktop restart 또는 새 named-role-capable path에서 해소해야 한다. compact 증거는 `eval/harness/results/role-model-activation-probe-20260909.json`이다.

기존 Codex 40/40은 Astra 전체 평가 이력으로 유지한다. 이 probe를 Sol/Astra 역할 배치의 실행 증거나 새 full40으로 재분류하지 않는다.

## 최신 main 이후 평가 확인

최종40 동결 snapshot과 현재 평가 동작 파일 110개를 SHA-256으로 다시 비교해 mismatch 0을 확인했다. parity 변경 경로의 부모 독립 비교는 exact 46, whitespace-only 28, content-changed 12, new 16이다. 하네스 task·fixture·judge·runner의 실제 내용 변경은 0이므로 전체 40회는 재실행하지 않았다.

최신 main `95c85bef7f2c65875812c88647f9dadf4f4c315d` 기준 H01 기본 `never` 2회와 recover-native-env 2회는 모두 같은 읽기 정책 차단으로 각각 0/2였다. 지원되는 `--approve-for-me` 경로의 probe 2·3 응답을 `expect.sh` 표준입력으로 재채점해 모두 rc 0, 합계 2/2 green을 확인했다. 두 실행 runtime model은 `gpt-6-astra`이고 저장소 변경은 없었다. 원시 JSONL·stderr는 외부 evidence에만 보존하고 저장소에는 compact 결과 `eval/harness/results/post-main-evaluation-check-20260909.json`만 둔다.

source-side 통합은 수용 가능하다. 전체 parity 완료는 Claude 신규 40회, Claude 실제 개발 E2E, 데스크톱 재시작 후 named custom-role 실행 검증이 끝날 때까지 주장하지 않는다.
