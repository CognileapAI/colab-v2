# H16 픽스처 원천 — 재현 명령

원천 = intent 로스터 (다) · `.claude/skills/colab-v2-work/SKILL.md:67`(기본값이 관대한 쪽으로 떨어지는가 · `${VAR:-1}`)

```bash
git show 7a97259:.claude/skills/colab-v2-work/SKILL.md | sed -n '61,70p'   # 다섯 모양 정본(대조용)
```

- 픽스처 파일 = **check-coverage.sh ＋ cases.txt**.
- ⚠ 이 파일들은 제품 파일의 사본이 **아니다.** (다) 묶음의 원천은 `SKILL.md` 의 **모양 서술 다섯 줄**이고,
  파일 사본이 아니라서 `git show` 로 뜰 실물이 없다. 그래서 그 모양 하나씩을 담은 셸 파일을 새로 썼다
  (라운드 §2 WU-D6 「(다)는 다섯 모양을 각각 한 셸 파일로」).
- 제품 파일은 한 자도 고치지 않았다. 이 셸들은 `gates/` 밖에 있고 어떤 게이트도 실행하지 않는다.
