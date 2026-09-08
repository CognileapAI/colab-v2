# H09 픽스처 원천 — 재현 명령

원천 = intent 로스터 (나) H09 · `p3-design-audit-20260905.md:17`(판정표 9행) · `detail.css:59`·`:62`

```bash
git show 947bf1f:frontend/src/components/detail/detail.css > detail.css
git show 947bf1f:frontend/src/components/catalog/catalog.css > catalog.css
git show 947bf1f:frontend/src/shell/tokens.css > tokens.css
```

- 결함이 **심긴 상태**다 — `detail.css:59`(컨테이너)와 `:62`(칸 구분선)가 둘 다 `--color-border` 다.
- `catalog.css` 는 토큰 정의(`:root`)와 바깥/안쪽선 대조용으로 함께 둔다.
