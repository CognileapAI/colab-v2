# `deploy_doctor` 출력 표본 — 손으로 적지 않는다

- 만드는 법 = `services/core-api/ops/deploy_doctor.py` 의 `DeployReport`·`verdict`·`MARKS` 를
  그대로 불러 요약 블록만 찍는다(항목 본문은 원격 자원을 건드리므로 상태만 넣는다).
- 표본 둘 —
  - `doctor-15-15.txt` = 15 항목 전건 `✓` · 요약줄 `항목 15 — ✓ 15 · ✗ 0 · ─ 0`.
  - `doctor-14-15.txt` = ⑭ 하나 `✗` · 요약줄 `항목 15 — ✓ 14 · ✗ 1 · ─ 0`.
- ⚠ **요약줄 앞에 공백 2칸이 붙는다**(`print(f"\n  {text}")`). 파서가 그 공백을 벗기지 않으면
  `^항목` 으로는 한 줄도 잡히지 않는다 — `tests/doctor-parse.sh` 가 그것을 판정한다.
