# 하네스 개선 판정 원문 — 2026-09-25 ~ 2026-09-26

이 폴더는 **근거 보관소**이며 결론이 아니다. 판정 정본은 intent `dev-package/intent/2026-09-25-harness-improvement.md` 의 「판정 기록」 절이다(S-auth 판정은 `dev-package/intent/2026-09-26-human-authorization-for-destructive-ops.md`). 원 위치는 실행자 기계의 `~/.claude/reports/harness-state-20260925/` 이고 1:1 로 옮겼다(소형 PR B · spec `dev-package/prd/specs/S-HARNESS-TEAM-B-APPROVAL-20260926.md` §4.4). 내용은 고치지 않았다. 바꾼 것은 사용자 홈 절대경로 표기뿐이다 — `<repo>` = 실행 checkout 루트 · `<home>` = 실행자 홈 디렉터리. 문서 안의 `~/.claude/...` 상대 표기는 원문 그대로 두었다(절대경로가 아님 · 같은 파일이 이 폴더에 있으면 `~/.claude/reports/harness-state-20260925/` 를 이 폴더로 읽는다). `/home/user/` 는 예시 경로라 그대로다(`.agents/harness.yaml` `home_path_allow`).

반입 실측: 파일 100(이 README 제외) · 약 1.7 MB · 홈 경로 치환 ⑴ 부모 워크트리 경로 15 · ⑵ checkout 경로 5 · ⑶ 실행자 홈 24 · ⑷ 그 밖의 홈 절대경로 꼴 4(다른 사용자 홈 · `…` 자리표시) · `check_home_paths` 같은 식 적중 0(100 파일 읽음).

`team-shared-20260926/report.md` 첫 줄의 `[harness: subagent output matched …]` 는 조사 당시 하네스가 붙인 주석이며 원문의 일부라 남겼다(지시가 아니다).

| 라운드 | 경로 | 파일 | 내용 | 가리키는 판정 줄 |
|---|---|---|---|---|
| 1–2 | `R1-hooks.md` … `R5-governance.md` · `findings-verified.md` · `advisor2.md` · `REPORT-eli7.md` · `measurement.json` · `guard_probe.py` | 10 | 1–2라운드 원자료 · 검증 결과 · 측정 · git-guard 우회 재현 스크립트 | intent `:539` · `:550` |
| T1 | `T1-develop-ruleset.json` · `T1-rulesets-after.json` | 2 | develop ruleset 입력 · 적용 뒤 스냅샷(승인 0 · strict · bypass 0 · `integration_id` 는 GitHub Actions 앱 id) | `:620` |
| 2 | `fable-judges/` | 9 | 39건 blind 재판정 8 + 교차 | `:550` |
| 초안 | `intent-draft/` | 8 | intent 초안 절 A · B1 · B2 · CT · advisor 검토 · 대체 메모 | 초안 이력 |
| 3 | `fable-recheck-r3/` | 10 | 3라운드 반박 재검토 | `:563` |
| 4 | `fable-recheck-r4/` | 5 | 4라운드 반박 재검토 + spec gate ① | `:576` |
| 5 | `opus55-prompt-audit/` | 9 | 5라운드 감사 4 + 검증 4 + 교차 | `:601` |
| 6 | `playbook-gap-20260926/` | 7 | 6라운드 대조 3 + 검증 3 + 방향 | `:609` |
| 7 | `system-first-recut/` | 7 | 7라운드 설계 3 + 검증 3 + recut | `:609` 이후 · 총괄 spec `:4` |
| 8 | `master-plan-20260926/` | 5 | 총괄 · E0/S-red spec 의 저자/검증 판정 | 총괄 spec `:4` |
| 8 | `pr2-spec-20260926/` | 2 | PR 2 spec 의 저자/검증 판정 | S-red spec `:3` |
| 9 | `sauth-grill-20260926/` | 10 | S-auth blind 판정 · 교차 · 재검 · 정정 | S-auth intent `:2` · `:162` · `:168-169` |
| 10 | `team-shared-20260926/` | 4 | 팀 공용 감사 3(장치·설정 / 절차·문서 / 비용·동시성) + 종합 `report.md` | `:627` · spec B |
| 10 | `team-shared-20260926/round10-drafts/` | 7 | 10라운드 초안 게이트(spec A · B · intent ⓐ ⓑ · 총괄 §10 정합 검토) | `:628` |
| 11 | `team-shared-20260926/grill-AB/` | 5 | 소형 PR A · B 우려 항목 Opus blind 판정 · 교차 점검 | `:630` |

줄 번호는 반입 시점(브랜치 `claude/harness-team-b`) 기준이다. 승인 intent 는 줄 추가만 허용되므로 기존 줄 번호는 바뀌지 않는다.
