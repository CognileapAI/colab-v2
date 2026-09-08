# H11 픽스처 원천 — 재현 명령

원천 = intent 로스터 (나) H11 · `p3-design-audit-20260905.md:19`(판정표 11행) · `lineageGraph.css:29`·`:33`

```bash
git show 947bf1f:frontend/src/components/lineage/lineageGraph.css > lineageGraph.css
git show 947bf1f:frontend/src/shell/tokens.css > tokens.css
git show 947bf1f:frontend/src/components/detail/detail.css > detail.css
```

- 결함이 **심긴 상태**다 — `lineageGraph.css:33` `display:inline-block` 이 `:29` `display:inline-flex` 를 덮는다.
- 미정의 토큰 **참조 11건**(실측 · 토큰 정의는 `tokens.css`·`detail.css` 두 `:root`):
  `:30`(accent-50·accent-200) `:31`(accent-700) `:48`·`:49`(gray-300) `:51`(primary-800)
  `:57`(primary-200·primary-800) `:83`(accent-700·accent-50) `:84`(--color-ai).
- 토큰 **가짓수는 8**, **참조 건수는 11** 이다. 가짓수를 적으면 red 다.
