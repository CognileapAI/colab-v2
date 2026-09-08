# H06 픽스처 원천 — 재현 명령

원천 = intent 로스터 (나) H06 · `p3-design-audit-20260905.md:14`(판정표 6행) · `catalog.css:31` · 시험 `frontend/test/design-fix-20260908.test.ts:74-80`

```bash
git show 947bf1f:frontend/src/components/catalog/catalog.css > catalog.css
```

- 결함이 **심긴 상태**다 — `947bf1f` 시점의 `catalog.css:31` 에 `box-shadow: var(--shadow-sm)` 이 살아 있다.
  현재 `main` 에서는 이미 제거됐으므로 옛 사본을 쓴다.
- 옳은 답 = 판정 「있음」 · 근거 `catalog.css:31` · 예외 `.colmenu`(팝오버) 유지.
