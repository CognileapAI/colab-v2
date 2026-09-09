> 최신(2026-09-09 09:35 KST): stage6 복구 인계·관련9개9/0/0 완료. 모델40회38/40, H12 판정 오류 수정 및 H08 범위 미해결. 아래 이전 실패 기록은 이력이며 현재 전체 현황은 `20260909-codex-parity-acceptance.md`를 따른다.

# 정상 개발 흐름 인수

상태: Codex 단계별 사이클 완주. 최신 launcher 재검증·새 advisor·named gate-runner 보완이 남으며, Claude는 주간 한도로 미실행이다.

## 고정 과제

격리된 연구 표시명 저장 화면에서 앞뒤 공백을 제거하고 Unicode codepoint 2~40개를 허용한다. 제어문자는 trim 전 거절한다. 잘못된 입력은 이전 저장값을 보존하고 정상 저장은 새로고침 뒤에도 유지한다.

- 공통 시작 fixture: 상위 `.parity-20260909/resources/e2e-fixture`.
- 별도 사본: `.parity-20260909/codex-e2e`, `.parity-20260909/claude-e2e`의 `eval/parity-display-name`.
- 진행자 전용 승인 응답은 fixture 밖 `resources/e2e-controller-scenario.md`에 둔다. 미래 승인 문장은 모델 사본에 복사하지 않았다.
- 질문 → 확인/초안 → 시험 intent 승인/spec → 시험 spec 승인/구현의 네 메시지를 순서대로 전달한다. 제품 승인·커밋 승인으로 쓰지 않는다.
- 테스트는 각 모델이 외부 행위 기준으로 직접 작성하고 실제 RED를 관측한 뒤 구현한다. 설치 실패나 테스트 0건은 RED 행동 증거가 아니다.
- 관련 게이트는 기존 frontend-test의 COLAB_FRONTEND_DIR seam과 별도 frontend-visual이다. 게이트 자체의 판정을 바꾸지 않는다.

## 준비 실측

- Codex fixture WSL npm ci: exit 0, 82 packages. 정상 환경 준비이며 테스트 성공이 아니다.
- 로컬 URL `http://127.0.0.1:18761`, WSL 정적 서버, 제품 데이터와 분리.
- 새 agent-browser session에서 snapshot → textbox fill → 저장 click → 읽기 전용 관측을 수행했다.
- 입력 `  한강 연구  `의 저장값/화면값이 모두 공백을 포함한 원문 그대로였다. 요구사항의 trim이 없는 시작 상태를 실제로 확인했다.
- PowerShell에서는 ref를 `'@e2'`처럼 인용해야 한다. 인용 없는 첫 시도는 splatting으로 인자가 누락되어 실패했고 성공으로 세지 않았다.
- 기준 동작 확인 후 브라우저 session을 닫았다. 최종 행동 검증에는 새 session을 쓴다.

## 외부 의존

Claude 신규 모델 호출은 주간 한도 API 429로 준비 실패다. 리셋 안내는 2026-09-11 03:00 Asia/Seoul. Claude 흐름은 미실행이며 Codex나 과거 결과로 대체하지 않는다.

## Codex 단계별 실측

- 외부 `evidence/codex-e2e-stage1`: 지정 요구사항 조사·질문 후 코드/문서 변경 0건.
- `stage2`: 확인 응답 후 intent 초안 1개만 작성, 미승인 표시와 인계 hash 확인. spec/구현 없음.
- `stage3`: 시험 승인 메타를 명시하고 spec 작성. 부모가 researcher 제한 경로로 specs를 등록하려던 시도는 거절됐고, 일반 부모 문서 작성과 researcher 역할 계약을 구분하도록 공통 설명을 보강했다. 권한 확대 없음.
- `stage4`: 계획·실제 행동 RED 20실패/4통과 → 구현 → DOM GREEN 24/24 → 브라우저 12/12 → 코드/시각 리뷰 → 최종 두 게이트 2통과/판정 0/준비 0 → 인계까지 모델 exit 0.
- 시작 및 최종 앱 hash, 원 RED 로그, 초기 실행 준비 실패, CR/LF 입력 정규화 한계, 최종 tree 검증은 사본 `dev-package/reports/parity-display-name/final/handoff.md`에 보존했다. HTML/CSS/요구사항과 검사기는 무수정이다.
- 부모도 최종 light/dark PNG 두 파일(각 1440×900)을 열어 확인했다. fixture에는 dark 테마 분기가 없어 두 이미지 hash가 같다. 다크 테마 구현 성공으로 세지 않는다.
- 최초 수용 리뷰는 계획 advisor를 재사용했으며 named gate-runner는 이 단계에서 호출되지 않았다. 마지막 source 재검증에서 새 advisor와 gate-runner를 별도 호출해 보완해야 한다.

## 기록 파서 결함과 원 증거 보존

stage4에는 실제 U+0085가 담긴 JSON 문자열이 있어 Python `splitlines()`가 정상 JSONL 레코드를 잘랐다. 모델은 정상 완료했지만 controller의 최초 결과에는 evidence_error가 남았다. runner의 raw/session 파서를 LF 구분으로 수정하고 literal NEL/U+2028/U+2029 회귀를 추가했다. Windows·WSL 각 15개 검사 통과. 원 로그 hash는 변하지 않았으며 새 parser로 레코드 201개·완료 1개·오류 0개·실제 Astra를 회수했다. 이는 모델 재실행이 아니다. 증거: 상위 `.parity-20260909/evidence/jsonl-parser-fix/stage4-reextracted.json`.
# 최종 후속 실행 상태 (2026-09-09)

stage5 새 advisor/gate-runner 후속 실행은 usage-limit error/turn.failed, exit 1로 중단됐다. 생성된 보고서는 부분 산출물이며 부모의 최종 source 검증·인계는 완료되지 않았다. 외부 `../.parity-20260909/evidence/codex-e2e-stage5-final-source`의 원로그를 보존한다. 아래 stage4 성공과 구분하며, 전체 수용 현황은 `20260909-codex-parity-acceptance.md`를 따른다.
