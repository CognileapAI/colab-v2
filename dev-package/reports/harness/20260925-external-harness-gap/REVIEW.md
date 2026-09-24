# 수용 검토 기록 — 외부 하네스 대비 개선 (claude/harness-external-gap)

기준: intent `dev-package/intent/2026-09-25-external-harness-gap.md` · spec `dev-package/prd/specs/S-EXTERNAL-HARNESS-GAP-20260925.md`.
advisor ② 자리를 반증 워크플로 네 회차가 맡았다(검토자 → 결함마다 독립 검증자 반박 → 비평). 확정 결함이 나오지 않을 때까지 돌린다.

## 1회차 — 레인 K·L + 병합 보정(0a3b9923..cf0114d7)
- 검토자 6명(intent-ref · 계약 검사 · CI·게이트 배선 · 레인 범위 · 문서 · 회귀) · 후보 29건.
- 반증: 중요·차단급 후보는 3명 · 사소 후보는 1명. 과반 유지만 확정 → **확정 16(중요 5 · 사소 11) · 기각 13**.
- 게이트 측정(같은 워크플로): `gates/run.sh all` 1회 `── 계 : green 75 / red(판정) 1 / red(준비) 0` — red 1 = `frontend-test` 부하 시간 초과(단독 재실행 1613/1613 통과 · 이 브랜치는 frontend 무변경).
- 비평 1명은 주간 사용 한도로 실패(재실행은 2회차에 포함).
- 수정 커밋 `df090a03` — 확정 16건 전부. 수정 전 코드에서 red 를 보인 시험 8건.

## 2회차 — 수정 재검증(df090a03)
- 재검토자 3명(intent-ref · 범위·계약 · CI·문서) · 후보 14건 · 검증자 2명씩.
- 두 검증자 모두 유지 = **확정 8** · 한 명 유지 3 · 기각 3.
- 확정 8: ① intent-ref 줄 비교가 `--`/`---` 줄 삭제를 놓치고 끝 줄바꿈 없는 순수 추가를 red 로 봄(1회차 수정이 만든 회귀) ② `-diff` 속성·색상 설정·바이너리 판정이 삭제를 가림 ③ UTF-8 아닌 이름의 승인 intent 비보호 ④ 옛 스키마 레인의 범위 우회 ⑤ 첫 경로 앞 공백 제거로 범위 오판 ⑥ harness-contract 가 UTF-8 아닌 파일 이름에서 죽음 ⑦⑧ ADR-0004·0006 줄 참조.
- 한 명 유지 3 중 「스테이징만 된 변경」은 비용이 작아 함께 고쳤다. 나머지 2건(gates/README 의 harness-eval 행 · spec 틀과 to-spec 의 기존 차이)은 이 변경과 무관한 기존 문서 차이라 후속으로 남긴다.
- 비평(원한 결과 1~8): 충족 6 · 부분 2(6 레인 범위 · 7 Intent-Ref — 위 확정 결함 때문) · 신규 1: `adr-records` 가 기록 0건에도 green 이고 CI 기준이 HEAD 라 승인 ADR 보존 검사가 돌지 않음.
- 수정: 위 8건 + 스테이징 변경 + ADR 신규 1건. 수정 전 코드에서 red 를 보인 시험 10건(9 실패 · 1 오류).

## 절차 빈틈(비평 지적)과 처리
- 로컬 PR 요약 부재 → `PR-BODY.md` 작성.
- 수정 전 red 인용이 커밋 메시지에만 있음 → 이 문서와 PR 요약에 옮김.
- `gates/run.sh all` 증거 → 1회차 게이트 측정(위)을 인용.
- PR 은 #131 병합 뒤 연다(intent 판정 ⑧).

## 3회차 — 2회차 수정 재검증(7fce70c3)
- 재검토자 3명 · 후보 8건 · 검증자 2명씩 → 두 명 모두 유지 **3** · 한 명 유지 1 · 기각 4.
- 확정 3: ① [중요] 2회차에 넣은 스테이징 대조가 begin 이전부터 스테이징된 부모 작업을 레인 범위 위반으로 셈(2회차 회귀) ② [중요] 이 PR 요약이 저장소 PR 계약(`scripts/harness/pr_contract.py --mode draft`)을 통과하지 못함 ③ [사소] 게시 절차에 「#131 먼저 병합」 조건 누락.
- 비평: 원한 결과 충족 7 · 부분 1(6 — 위 ①) · 빈틈 — ADR-0004 의 gates/README 줄 참조(브랜치 이전부터 낡음) · 전수 실행 증거가 1회차 트리 기준 · 항목별 수정 전 red 인용 부재 · 새 「ADR 남길 때」 기준에 Intent-Ref 게이트가 해당.
- 수정: 범위 task 는 begin 때 index 트리(`git write-tree`)를 기록하고 인계 때 그것과 비교 · PR 요약을 계약에 맞춤(검증 상태 값 · 자리표시자 제거 · 게시 때 Head-SHA 채우고 계약 검사) · 게시 전제 명시 · ADR-0004 줄 참조를 인용 문구 기준으로 재측정 · ADR-0007(Intent-Ref) 신설 · 최종 트리에서 `gates/run.sh all` 재실행.

## 항목별 수정 전 red 인용
| 항목 | 수정 전(red) | 수정 후 |
|---|---|---|
| K1 훅 등록 누락 | `[] != ['hook not registered … test-file-guard.sh (event PreToolUse, matcher Edit\|Write)']` (레인 K) | green |
| K2 adr-records | `gates/run.sh has no adr-records case` · ci-filter-check `㈕ docs/decisions/0001-… 가 dev-package 필터에 안 잡힌다` rc=1 (레인 K) | green |
| K3 홈 절대경로 | `AttributeError: module 'harness_config' has no attribute 'check_home_paths'` (K3 이전 config · 오케스트레이터) | green |
| K4 줄 상한 | `KeyError: 'hygiene'` → 121행 fixture red (레인 K) | green |
| K5 intent-ref | `FileNotFoundError`(모듈 없음) · 트레일러 없는 범위 `트레일러가 0개다` rc=1 (레인 K) | green |
| L1 레인 범위 | `TypeError: begin() got an unexpected keyword argument 'scope'` · `unrecognized arguments: --scope src/**` (레인 L) | green |
| 1회차 수정 | 새 시험 8건이 이전 코드에서 red — 분기 뒤 승인 intent · UTF-8 경로 · 준비 실패 시 판정 누락 · 커밋 뒤 복원 우회 · 범위 형태 2 · ci-filter ㈕ 2 | green |
| 2회차 수정 | 새 시험 10건 red(9 실패 · 1 오류) — `---`/`--` 줄 · 끝 줄바꿈 · `-diff`·색상 · UTF-8 이름 intent · 옛 스키마 범위 · 앞 공백·스테이징 · 0건 ADR · ADR 보존 · UTF-8 파일 이름 | green |
| 3회차 수정 | `ValueError: changes outside declared lane scope: notes/parent.md …` (begin 이전 스테이징) | green |

## 최종 측정(4a3a046a)
- `gates/run.sh all`: green 76 / red(판정) 0 / red(준비) 0.
- 게이트 합집합 8개 green(단독 `harness-contract-selftest` 1회는 다른 프로세스의 잠금 점유로 red(준비) → 기본 상한 재실행 green) · ci-filter-check green · 단위 시험 130 OK(skip 10).

## 4회차 — 3회차 수정 재검증(a65b15b3)
- 재검토자 3명 · 후보 11건 · 검증자 2명씩 → 두 명 모두 유지 **8(중요 1 · 사소 7)** · 기각 3.
- 확정 8: ① [중요] PR 요약 게시 명령이 계약 검사 실패에도 PR 을 열고, 브랜치를 쥔 작업 사본 밖에서 `git switch` 가 실패함 ② begin 이 index 트리 기록 실패를 원인과 무관하게 「충돌」로 안내(`index.lock` 도) ③ 그 거부 분기·`started_index` 부재에 시험 없음 ④ lifecycle-evidence 에 begin 시점 index 기준 설명 없음 ⑤ ADR-0007 의 CI 범위 서술(product 가 아닌 모든 대상) ⑥ PR 요약의 ADR-0006 서술(대안 항목 추가 누락) ⑦ 2회차 건수 불일치 ⑧ REVIEW 머리의 회차 수.
- 비평: 원한 결과 충족 7 · 부분 1(6 — ②③④) · PR 준비 = 위 수정 뒤.
- 수정: 충돌은 `git ls-files -u` 로 먼저 가리고 그 밖의 실패는 git 메시지를 그대로 담는다(수정 전 `AssertionError: "index.lock" does not match "… resolve conflicts first"` → 수정 후 green) · 문서·기록 5곳 정정 · 게시 명령은 `set -e` 와 브랜치를 꺼내지 않는 `git show` 방식.

