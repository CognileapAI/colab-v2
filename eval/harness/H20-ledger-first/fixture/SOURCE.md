# H20 픽스처 원천 — 재현 명령

원천 = intent 로스터 (라) H20 · `CLAUDE.md:131`(⭑ 문단)·`:137`(번호 목록 1번)

```bash
git show 7a97259:CLAUDE.md                      | sed -n '129,145p'   > CLAUDE-6.md
git show 7a97259:dev-package/03-HANDOFF.md      | sed -n '70,80p'     > 03-HANDOFF-excerpt.md
git show 7a97259:dev-package/work-items.yaml    | sed -n '3113,3124p' > work-items-excerpt.yaml
```

- 발췌 범위 이유 — `03-HANDOFF.md` 195KB · `work-items.yaml` 623KB 라 통째 사본을 두지 않는다.
  70~80행 = `§1 진행도` 머리와 첫 상태 표(산문 반영본이 실제로 어떻게 생겼는지).
  3113~3124행 = `WU-D6` 블록 하나(대장이 실제로 어떻게 생겼는지). 문면은 한 자도 고치지 않았다.
- **결함을 심지 않았다.** 함정은 원문에 이미 있다 — `CLAUDE-6.md:9`(번호 목록 1번)이 인계 문서를 먼저
  가리키고, `:3`(⭑ 문단)이 대장을 먼저 가리킨다. 규칙은 ⭑ 문단이다.
