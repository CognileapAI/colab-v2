# H04 픽스처 원천 — 재현 명령

원천 = intent 로스터 (나) H04 · `dev-package/sessions/p3-design-audit-20260905.md:9`(판정표 1행) · `detail.css:53`

```bash
git show 947bf1f:frontend/src/components/detail/detail.css > detail.css
git show 947bf1f:frontend/src/shell/tokens.css > tokens.css
```

- `947bf1f` = `origin/integration/r-a` — `p3-design-audit-20260905.md:3` 이 실측 기준으로 적은 트리다.
- **결함을 심지 않았다.** 판정표가 「없음」 으로 닫은 자리이고, 과제는 그 「없음」 을 다시 낼 수 있는지를 잰다.
- 옳은 답 = `.lvl-2,.lvl-3`(`detail.css:53`) `#0f62e0` on `#e2eeff` → **4.66:1**(AA 통과) → 판정 「없음」.
- 토큰 hex 는 `tokens.css` 와 `detail.css` 의 `:root` 두 곳에 있어 둘 다 사본으로 둔다.
