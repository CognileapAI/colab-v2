# 하네스에 훅 등록 누락·ADR·홈 경로·줄 상한·Intent-Ref 검사와 레인 범위 대조를 붙인다

Plan-Ref: dev-package/prd/specs/S-EXTERNAL-HARNESS-GAP-20260925.md
Head-SHA: (게시 때 PR head 40자리로 채운다)
검증 상태: 부분 검증

## 목적
외부 하네스 `sungwooHa/ai-sdlc-harness`(커밋 `78b2d0f`)와 장치 30개를 대조해, 우리에게 없던 검사를 새 훅 없이 붙인다(intent `dev-package/intent/2026-09-25-external-harness-gap.md` · Ted 판정 "권고대로").

## 범위
- 채택: 훅 등록 누락 · ADR 게이트 · 홈 절대경로 · 자동 로드 줄 상한 · Intent-Ref 트레일러와 승인 intent 보존(판정 red) · 레인 범위 선언·인계 대조 · PR 가치 표 · intent/spec 틀 · 하네스 판정 질문·변경 절차 문서.
- 새 Claude/Codex 훅 0 · `/hooks` 재신뢰 0.
- 보류 7(재검토 조건 기록 · `docs/development/dual-agent.md`) · 불채택 4(로컬 전용 이력 · 해시 승인 · 셸 차단 · PR 형태 훅).

## 계획
- 레인 K(검사·게이트) · 레인 L(레인 범위·틀·문서) 병렬 → 병합 보정(K3 홈 경로) → 반증 검토 4회차 → 모두 수정. 회차별 확정 결함: 1회차 16 · 2회차 8(+ 한 명 유지 1건 함께 수정 · 비평 신규 ADR 1건) · 3회차 3 · 4회차 8. 로컬 검증 상태는 「부분 검증」 — CI 는 게시 뒤에 돈다.
- 검토 기록: `dev-package/reports/harness/20260925-external-harness-gap/REVIEW.md`.

## 결정
- ADR-0007(accepted) — 커밋은 Intent-Ref 로 intent 를 가리키고 승인 intent 는 줄 추가만 허용한다(`docs/decisions/0007-intent-ref-trailer-and-append-only-approved-intents.md` · 승인 = intent 질문 4 ⓐ).
- 나머지 검사는 ADR-0003(판정은 CLI·게이트 · 훅 없음) · ADR-0005 개정(조용한 exit 0 없음)에 맞춰 게이트로만 붙였다. ADR-0004 는 줄 참조만 갱신했다. ADR-0006 은 줄 참조 갱신과 함께 「검토한 대안」에 symlink 미러 미채택 사유 1항목을 더했다(intent 원한 결과 8).

## 검증
게이트(이 브랜치 · 로컬): harness-contract · harness-contract-selftest · agent-bridge · adr-records · exec-bit · planning-freshness · work-item-consistency · intent-ref 각각 green 1 / red(판정) 0 / red(준비) 0 · ci-filter-check green · 단위 시험 130 OK(skip 10 · Windows 전용) · PR 계약 `pr_contract.py --mode draft` PASS(게시 절차대로 Head-SHA 채움).
`gates/run.sh all` 1회(최종 트리 `4a3a046a`): **green 76 / red(판정) 0 / red(준비) 0**. (1회차 트리 `cf0114d7` 에서는 green 75 / red(판정) 1 — `frontend-test` 부하 시간 초과 · 단독 재실행 1613/1613 통과.)
단독 `harness-contract-selftest` 1회는 다른 프로세스가 호스트 게이트 잠금을 900초 넘게 쥐어 red(준비) 였고, 기본 대기 상한 그대로 재실행해 green 1/0/0.

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
- 기존 열린 PR·브랜치는 트레일러가 없으면 `intent-ref` 가 red 다. 소급 경로 = 그 PR 의 intent 를 가리키는 빈 커밋 1개. 예: `git commit --allow-empty -m "intent 연결" -m "Intent-Ref: dev-package/intent/2026-09-25-external-harness-gap.md"`(규칙 `.agents/skills/colab-v2-work/SKILL.md`).
- 후속(이 변경과 무관한 기존 문서 차이): `gates/README.md` harness-eval 행의 비밀·모델 호출 서술 · spec 틀과 to-spec 템플릿의 나머지 차이.
- 30·31 저장소가 같은 게이트 잠금 경로를 쓰면 #130 의 잠금 수정이 없는 쪽 데몬이 잠금을 쥘 수 있다(레인 L 관측 · 별건).

## 게시 절차 (사용자)
전제: PR #131(`claude/agent-model-tiering`)이 develop 에 먼저 병합돼야 한다(intent 판정 ⑧). 병합 전에 열면 #131 커밋 6개가 이 PR 에 섞인다 — `git log origin/develop..origin/claude/agent-model-tiering` 이 비어 있는지 먼저 본다.
Head-SHA 는 게시 시점 head 로 채우고 저장소 PR 계약을 통과시킨 뒤 연다:
저장소 안 어느 체크아웃에서나 돈다(브랜치를 꺼내지 않는다). 계약 검사가 실패하면 PR 을 열지 않고 멈춘다:
```bash
set -e
git fetch origin
test -z "$(git log --oneline origin/develop..origin/claude/agent-model-tiering)"   # #131 병합 확인
HEAD_SHA=$(git rev-parse origin/claude/harness-external-gap)
git show "$HEAD_SHA:dev-package/reports/harness/20260925-external-harness-gap/PR-BODY.md" \
  | sed "s/^Head-SHA: .*/Head-SHA: $HEAD_SHA/" > /tmp/pr-body.md
CHECK=$(mktemp -d)
git archive "$HEAD_SHA" scripts/harness .agents/harness.yaml | tar -x -C "$CHECK"
python3 "$CHECK/scripts/harness/pr_contract.py" --head "$HEAD_SHA" --mode draft /tmp/pr-body.md
gh pr create --base develop --head claude/harness-external-gap --title "하네스에 훅 등록 누락·ADR·홈 경로·줄 상한·Intent-Ref 검사와 레인 범위 대조를 붙인다" --body-file /tmp/pr-body.md
```

## 병합 뒤
- 새 훅이 없으므로 `/hooks` 재신뢰는 필요 없다.
- 열린 PR 은 위 소급 경로로 트레일러 커밋을 하나 얹는다.
