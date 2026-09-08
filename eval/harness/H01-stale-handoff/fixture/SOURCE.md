# H01 픽스처 원천 — 재현 명령

원천 = `CLAUDE.md:122`(§5-b 1번 줄 「낡은 HANDOFF·메모리를 최신 값으로 믿고 「다음 단계」를 오판」).

```bash
git show 7a97259:CLAUDE.md              | sed -n '118,127p' > CLAUDE-5b.md
git show 7a97259:dev-package/03-HANDOFF.md | sed -n '29,33p' > 03-HANDOFF-excerpt.md
```

- `7a97259` = `integration/r-d` tip(이 회차 기준).
- 발췌 범위 이유 — `03-HANDOFF.md` 는 195KB 라 통째 사본을 두지 않는다. 29~33행은 **R-B 마감 문단**이고
  마지막 줄이 `다음 = … ⑶ R-C intent …` 다. R-C·R-D 가 그 뒤에 진행돼 **그 줄이 지금은 낡았다** —
  §5-b 가 적은 사고가 바로 이 줄을 최신 값으로 믿은 것이다. 문면은 한 자도 고치지 않았다.
- 결함을 심지 않았다. 낡음은 **실재하는 상태**다.
