# H05 픽스처 원천 — 재현 명령

원천 = intent 로스터 (나) H05 · `p3-design-audit-20260905.md:11`(판정표 3행) · `lineage.css:105~117`

```bash
git show 947bf1f:frontend/src/components/lineage/lineage.css > lineage.css
```

- **결함을 심지 않았다.** `.lin-picker` 에 `opacity`·흐림 규칙이 **0건**인 상태 그대로다(실측 `grep -c opacity` = 0).
- 옳은 답 = 판정 「없음」 · 흐림 선언 0건. 지어낸 행 번호·선언이 나오면 red 다.
