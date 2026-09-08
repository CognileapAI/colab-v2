# H12 픽스처 원천 — 재현 명령

원천 = intent 로스터 (라)형 대조 H12 · 시험 `frontend/test/css-residual-rc11.test.ts:79-87` · `catalog.css:136` 제거 사본

```bash
git show 7a97259:frontend/src/components/catalog/catalog.css > catalog.css
git show 7a97259:frontend/src/components/catalog/CatalogTable.tsx > CatalogTable.tsx
```

- **결함은 심은 것이다.** 현재 `catalog.css:134-136` 은 `.lvl-3` 규칙과 그 주석 두 줄이다.
  사본을 뜬 뒤 `sed '134,136d'` 로 그 세 줄을 지웠다(주석까지 지운 이유 = 주석이 답을 그대로 적고 있다).
  결과 사본은 179행이고 `.lvl-2` 가 133행이다.
- `CatalogTable.tsx:162` 가 `lvl lvl-${displayLevel(row)}` 를 내므로 4단째(`.lvl-3`)가 무색이 된다.
- 제품 파일은 고치지 않았다.
