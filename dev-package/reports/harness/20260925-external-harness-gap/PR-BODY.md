# 하네스에 훅 등록 누락·ADR·홈 경로·줄 상한·Intent-Ref 검사와 레인 범위 대조를 붙인다

Plan-Ref: dev-package/prd/specs/S-EXTERNAL-HARNESS-GAP-20260925.md
Head-SHA: (게시 때 PR head 40자리로 채운다)
검증 상태: 로컬 게이트 green · CI 는 게시 뒤

## 목적
외부 하네스 `sungwooHa/ai-sdlc-harness`(커밋 `78b2d0f`)와 장치 30개를 대조해, 우리에게 없던 검사를 새 훅 없이 붙인다(intent `dev-package/intent/2026-09-25-external-harness-gap.md` · Ted 판정 "권고대로").

## 범위
- 채택: 훅 등록 누락 · ADR 게이트 · 홈 절대경로 · 자동 로드 줄 상한 · Intent-Ref 트레일러와 승인 intent 보존(판정 red) · 레인 범위 선언·인계 대조 · PR 가치 표 · intent/spec 틀 · 하네스 판정 질문·변경 절차 문서.
- 새 Claude/Codex 훅 0 · `/hooks` 재신뢰 0.
- 보류 7(재검토 조건 기록 · `docs/development/dual-agent.md`) · 불채택 4(로컬 전용 이력 · 해시 승인 · 셸 차단 · PR 형태 훅).

## 계획
- 레인 K(검사·게이트) · 레인 L(레인 범위·틀·문서) 병렬 → 병합 보정(K3 홈 경로) → 반증 검토 2회차 → 확정 결함 16 + 9 수정.
- 검토 기록: `dev-package/reports/harness/20260925-external-harness-gap/REVIEW.md`.

## 결정
- 새 ADR 없음. ADR-0003(adr_gate 는 훅 없이) · ADR-0005 개정(「조용한 exit 0 없음」)에 맞춰 게이트로만 붙였다. ADR-0004·0006 은 줄 참조만 갱신.

## 검증
게이트(이 브랜치 · 로컬): harness-contract · harness-contract-selftest · agent-bridge · adr-records · exec-bit · planning-freshness · work-item-consistency · intent-ref 각각 green 1 / red(판정) 0 / red(준비) 0 · ci-filter-check green · 단위 시험 129 OK(skip 10 · Windows 전용).
`gates/run.sh all` 1회(1회차 검토 중): green 75 / red(판정) 1 / red(준비) 0 — red 1 은 `frontend-test` 부하 시간 초과(단독 재실행 1613/1613 통과 · frontend 무변경).

| 원한 결과 (intent) | 실제 | 근거 | 가치 상태 |
|---|---|---|---|
| 1 훅 등록 누락이 red | 매처는 두고 명령 1줄 뺀 settings → red | `sources.hook_registrations` · `scripts/harness/config.py` · 시험 `test_harness_config` | 확인됨 |
| 2 ADR 게이트가 CI 에서 돈다 | `adr-records` · dev-package 필터(ADR·판정기·설정) · PR base 대비 승인 ADR 보존 · 0건 red | `gates/run.sh` · `ci.yml` planning-gates · 시험 `test_harness_record_gates` | 확인됨 |
| 3 홈 절대경로 red | 대상 6뿌리 · fixture red · 트리 0건 | `config.check_home_paths` · `agent-bridge.yml` 경로 | 확인됨 |
| 4 자동 로드 줄 상한 120 | 121행 fixture red · 현재 87행 | `hygiene.always_on_max_lines` | 확인됨 |
| 5 PR 가치 표 · intent/spec 틀 | 이 표 · V-id · 목업 선택 줄 | `.github/pull_request_template.md` · 틀 2개 · to-spec | 확인됨 |
| 6 레인 범위 대조 | 범위 밖 변경(작업 파일·커밋·스테이징) 인계 거부 · 출구 2개 · 옛 스키마 거부 | `lifecycle_contract.py` · 시험 `test_task_runtime` | 확인됨 |
| 7 Intent-Ref · 승인 intent 보존 | 트레일러 없음 red · 기준·분기 승인 intent 의 줄 변경 red(원본 바이트 순서 비교) | `scripts/harness/intent_ref.py` · CI `intent-ref` 잡 · 시험 | 확인됨 |
| 8 판정 질문·변경 절차·문서 정비 | dual-agent 판정 질문 5 · 보류 7 · 스킬 수 · VENDORED SHA | `docs/development/dual-agent.md` · `.agents/skills/VENDORED.md` | 확인됨 |

Evidence-Ref: 로컬 — 게이트별 gate-summary(작업 기록) · CI 는 게시 뒤
Evidence-SHA256: 게시 뒤 CI 증거로 채운다
CI-Ref: 게시 뒤

## 남은 제약
- 기존 열린 PR·브랜치는 트레일러가 없으면 `intent-ref` 가 red 다. 소급 경로 = `git commit --allow-empty -m "…" -m "Intent-Ref: dev-package/intent/<파일>.md"` 1개(`.agents/skills/colab-v2-work/SKILL.md`).
- 후속(이 변경과 무관한 기존 문서 차이): `gates/README.md` harness-eval 행의 비밀·모델 호출 서술 · spec 틀과 to-spec 템플릿의 나머지 차이.
- 30·31 저장소가 같은 게이트 잠금 경로를 쓰면 #130 의 잠금 수정이 없는 쪽 데몬이 잠금을 쥘 수 있다(레인 L 관측 · 별건).

## 게시 절차 (사용자)
```bash
gh pr create --base develop --head claude/harness-external-gap --title "하네스에 훅 등록 누락·ADR·홈 경로·줄 상한·Intent-Ref 검사와 레인 범위 대조를 붙인다" --body-file dev-package/reports/harness/20260925-external-harness-gap/PR-BODY.md
```

## 병합 뒤
- 새 훅이 없으므로 `/hooks` 재신뢰는 필요 없다.
- 열린 PR 은 위 소급 경로로 트레일러 커밋을 하나 얹는다.
