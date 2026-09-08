# H02 픽스처 원천 — 재현 명령

원천 = `CLAUDE.md:123`(§5-b 2번 줄 「정적 계측기가 CSS 주석을 코드로 읽어 오탐 3건 · `css_audit.py`」).

```bash
git show 7a97259:.claude/skills/design-review/scripts/css_audit.py > css_audit.py
```

- `7a97259` = `integration/r-d` tip.
- `css_audit.py` 는 **고쳐진 뒤의 판본**이다(`strip_comments` 보유 · `css_audit.py:76-78`).
  과제는 「계측기가 주석을 세는가」를 판정시키는 것이고, 옳은 답은 **주석분 0건**이다.
- 계측기 사본을 픽스처 안에 두는 이유 = `eval/harness/allowed.txt` 의
  `Bash(python3 {FIXTURE}/css_audit.py --root {FIXTURE}:*)` 가 **경로를 픽스처로 고정**하기 때문이다
  (advisor ① · spec 우려 10). 자유 경로 인자를 허용하면 읽기 전용이 깨진다.
- `sample.css` 는 원천 파일의 사본이 아니라 **이 과제를 위해 새로 쓴 표본**이다 —
  주석 2곳에 `font-size: 9px`·`font-size: 10px` 를, 코드에 `font-size: 11px` 1건을 둔다.
  옳은 계수 = 13px 미만 **1건**(주석분 2건 제외).
