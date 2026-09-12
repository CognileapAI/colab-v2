# HE-1 세션 프롬프트 — 하네스 평가 과제 4건 설계 수리

- 용도 — 별도 체크아웃 `31 CoLAB-v2` 에서 `HE-1` 을 착수할 때 그대로 붙여 넣는 지시문.
- 작성 2026-09-12 (버그개선 회차 마감 · Ted 판정 ⓐ 「이번 회차는 red 를 안고 병합·배포 · 과제 수리는 별도 세션」).
- 대장 `HE-1` — `dev-package/work-items.yaml` 의 `note` 에 같은 문면이 축자 수록돼 있다.

---

```
31 CoLAB-v2 에서 하네스 평가 과제 4건(H14-silent-skip · H15-zero-targets · H16-lenient-default · H18-three-states)의 설계 결함을 고친다.
- 근거: eval/harness/results/20260912-211809/summary.md (green 16 / 실패 4) 와 20260908-161538 (같은 과제 실패) · R-D 라운드 결정 ㉴(방치) · PLAN-SoT 〈389〉(이번에 ⓐ 로 넘김)
- 과제 정의: eval/harness/H14* H15* H16* H18* · 러너 eval/harness/run.sh · README 의 선언값(TIMEOUT 93 · BUDGET 2.01)
- 실행은 구독(로그인 claude -p) 경로다. API 키·예산 승인을 묻지 않는다.
- 순서: 과제별로 「기대(expect)가 잘못됐는가 / 지시문이 실제로 안 지켜지는가」를 먼저 가르고, 기대 오류면 과제를 고치고, 지시문 미준수면 CLAUDE.md·스킬 문안을 고친다. 고친 뒤 COLAB_HARNESS_EVAL=1 COLAB_EVAL_TIMEOUT=93 COLAB_EVAL_BUDGET=2.01 bash gates/run.sh harness-eval 로 재실행.
- 완료 = 20/20 green 1회 ＋ 승격 조건(3회 연속 2/2 green · intent 2026-09-08-harness-evals Q10) 계수 시작. 대장 항목 HE-1 을 done 으로.
- 라운드 파일·03-HANDOFF 통독 금지(grep 한 줄만).
```
