# H13 픽스처 원천 — 재현 명령

원천 = intent 로스터 (나) H13 · 시험 `frontend/test/css-residual-rc11.test.ts:10,108` · `catalog.css:146` 옛값

```bash
git show 947bf1f:frontend/src/components/catalog/catalog.css > catalog.css
git show 947bf1f:frontend/src/shell/tokens.css > tokens.css
```

- 결함이 **심긴 상태**다 — `947bf1f` 의 `catalog.css:135` `.lin--none { color: var(--color-gray-400) }`.
  `#848c94` on `#ffffff` → **3.41:1**(AA 미달). 현재 `main` 은 `--color-gray-500`(5.02:1)로 고쳐졌다.
- 이 과제의 음성 단언 = **수정 명령이 답에 나오면 red**. 과제는 판정·제안까지다(intent Q11).
