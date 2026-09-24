# Intent: dev reset 이 비어 있지 않은 dev 를 사용자 회차별 GO 없이 지우지 않는다
메타 — 발의자: 사용자 · 작성 2026-09-25 · 승인 2026-09-25(Claude Code 세션 https://claude.ai/code/session_01Ft79rxkNTe5AYcQ6wukTax)

## 문제
- 2026-09-24 08:33Z `reseed.sh --from reset` 이 사람이 만든 자료가 있는 dev 의 DB 행과 S3 객체를 지웠다.
- reset 단계는 계수 파일의 존재만 확인했고, 그 계수는 연구실 경계가 걸리지 않는 롤로 세어 비어 있지 않은 dev 를 0 으로 읽었다.

## 원한 결과 (proposed outcome)
- dev reset 은 비어 있지 않은 dev 의 자료를 **그 회차 사용자 GO 없이** 지우지 않는다.
  - 비어 있지 않으면 앱 정지·DROP·S3 전에 비영 종료하고 표별 계수를 보인다.
  - 넘기는 값은 그 회차의 1회용 토큰(만료 30분 · 1회 소진)과 GO 근거이고 사용자가 자기 터미널에서 넣는다.
  - 도구는 DROP 직전에 같은 프로세스에서 다시 세고, S3 계획은 이번 reset 의 DROP 직전 계수와 지금 DB 참조 키 0 에 묶인다.
- 빈 dev 의 상시 승인은 유지한다.

## 영향 범위
- 사용자 / 화면: 없음(dev 운영 도구)
- 서비스 · 스키마 · 계약: `services/core-api/ops/reset_dev_environment.py` · `dev-package/tools/dev-reseed/**` · `.agents/rules/deploy.md` 11번 · `.agents/skills/dev-reseed/SKILL.md` · 공용 Bash 훅 `scripts/harness/hooks/git-guard.sh` ⑹. `db/**` 무변경.
- 계약 파괴 여부: 아니오

## 제약
- dev·S3 에는 병합 전 아무것도 실행하지 않는다.
- 훅 ⑹ 과 토큰의 터미널 한정 출력은 우발적 읽기·주입 경로를 줄일 뿐 자동 보안 경계가 아니다(`AGENTS.md`). 남는 경로 — 의사 터미널(pty)로 stdout 받기 · 실행 자리 `count-before.json` ＋ 원격 challenge nonce 로 토큰 로컬 재계산 · env 파일·Write 도구로 값 주입. 지키는 것은 deploy.md 11번 규칙이다.

## 검증 계획
- 병합 전: 선언 게이트(`dev-reseed-selftest` · `service-tests-core-api` · `harness-contract` · `agent-bridge` · `exec-bit` · `harness-contract-selftest`)와 `frontend-test` 로컬 실행.
- 병합 후(사용자 실행 · dev):
  - ② `--preflight-only`
  - ③ `--rehearse`
  - ④ 직전에 BYPASSRLS 백업을 새로 뜬 뒤 토큰 없이 실제 `--from reset` 1회 — **거부가 기대값**(파괴 호출 0 · 표별 계수 출력).
- dev 재시드 동결 해제는 ④ 의 표별 계수를 사용자가 보고 GO 를 준 뒤에만 한다.

## 미해결 질문
- 없음

## 범위 밖 (명시 제외)
- k3-resume 의 다른 재시드 도구 변경(임시 운영자 창 · verify/미리보기 흐름 · 격자 대기 · 업로드 분류 서명)
- K3/K4 제품 코드 · eval fixture · 보고서
- staging·prod 승인 정책(무변 · 매회 GO)

## 확인
- 승인 항목(사용자 · 2026-09-25 · Claude Code 세션 https://claude.ai/code/session_01Ft79rxkNTe5AYcQ6wukTax):
  - deploy.md 11번 개정 문면
  - 이 PR(`reseed-reset-gate-develop` → develop)
  - 병합 후 단계 ②③④
- 재개봉 금지: 아니오

## 참조
- RCA: `dev-package/reports/corpus-expansion/dev-reseed-rca-2026-09-25.md` §0′(브랜치 k3-resume)
- 규칙: `.agents/rules/deploy.md` 11번 ⟨개정 2026-09-25⟩
