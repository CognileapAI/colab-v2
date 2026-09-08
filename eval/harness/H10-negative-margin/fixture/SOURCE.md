# H10 픽스처 원천 — 재현 명령

원천 = intent 로스터 (나) H10 · `p3-design-audit-20260905.md:18`(판정표 10행) · `detail.css:93`·`shell.css:58`

```bash
git show 947bf1f:frontend/src/components/detail/detail.css > detail.css
git show 947bf1f:frontend/src/shell/shell.css > shell.css
```

- 결함이 **심긴 상태**다 — 음수 margin 선언 **2건**(주석 제거 후 실측):
  `detail.css:93` `margin: -12px 0 var(--space-6)` · `shell.css:58` `margin-left: -7px`.
- 한 파일만 훑으면 1건으로 끝난다. 두 파일을 다 보게 하려고 둘 다 사본으로 둔다.
