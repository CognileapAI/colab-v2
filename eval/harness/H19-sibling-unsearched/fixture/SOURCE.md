# H19 픽스처 원천 — 재현 명령

원천 = intent 로스터 (라) H19 · `catalog.css:140` · `project.css:528` `.verified--pending`

```bash
git show 7a97259:frontend/src/components/catalog/catalog.css > catalog.css
git show 7a97259:frontend/src/components/project/project.css > project.css
git show 7a97259:frontend/src/shell/tokens.css > tokens.css
```

- **결함을 심지 않았다.** 현재 트리의 값 그대로이고, 미달은 **실재한다** —
  `--color-gray-500`(#697077) on `--color-gray-100`(#e8ecf2) → **4.23:1**(AA 4.5 미달).
- 같은 모양이 두 자리에 있다 — `catalog.css:140` · `project.css:528`. 한 곳만 고치면 나머지가 남는다.
- ⚠ 이 미달을 잡는 검사는 지금 **어디에도 없다** — `design-fix-20260908.test.ts`·`css-residual-rc11.test.ts`
  는 `.verified--pending` 을 단언하지 않고, `css_audit.py` 의 대비 계산은 `color`·`background` 가
  **리터럴 hex** 일 때만 돈다(`css_audit.py:117-122`). 두 선언은 `var()` 참조라 계산에서 빠진다.
  게이트·Dockerfile·배포 어디에도 걸리지 않는 결함이므로 후속 항목으로 올린다.
- `tokens.css` 는 `--color-gray-500` hex 를, `catalog.css` 의 `:root` 는 `--color-gray-100` hex 를 준다.
