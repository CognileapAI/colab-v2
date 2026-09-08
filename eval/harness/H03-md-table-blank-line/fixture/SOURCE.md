# H03 픽스처 원천 — 재현 명령

원천 = `CLAUDE.md:124`(§5-b 3번 줄 「마크다운 표 사이에 빈 줄이 끼어 행이 표 밖으로 떨어짐 · `VENDORED.md` 2회」).

```bash
git show 7a97259:.claude/skills/VENDORED.md | sed -n '1,14p' | sed '12a\
' > VENDORED-excerpt.md
```

- `7a97259` = `integration/r-d` tip.
- **결함은 심은 것이다.** 현재 `VENDORED.md` 의 표는 성해 있으므로(사고는 이미 고쳐졌다),
  사고 당시 모양을 재현하려고 12행 뒤에 빈 줄 한 줄을 넣었다 — `sed '12a\'` 가 그 한 줄이다.
- 결과 = 빈 줄 **13행** · 그 뒤 **14·15행 두 줄**이 표 밖으로 떨어진다.
- 제품 파일은 고치지 않았다(사본만).
