# H07 픽스처 원천 — 재현 명령

원천 = intent 로스터 (나) H07 · `p3-design-audit-20260905.md:15`(판정표 7행) · `lineageGraph.css`

```bash
git show 947bf1f:frontend/src/components/lineage/lineageGraph.css > lineageGraph.css
```

- 결함이 **심긴 상태**다 — 13px 미만 `font-size` 선언 **13건**(주석 제거 후 실측), 최소 **10px**.
  행 = `:10 :14 :31 :44 :45 :58 :72 :76 :81 :82 :83 :85 :95`.
- 소수점 선언(`10.5px`·`12.5px`)이 두 건 섞여 있어 정수만 세면 11 건으로 모자란다.
