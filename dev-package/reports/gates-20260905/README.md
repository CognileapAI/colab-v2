# 게이트 전수 로그 — 2026-09-05 프론트 버그 4건 통합 회차

`./gates/run.sh all -j 1` · `~/.colab-v2-test.env` source · 통합 브랜치 `integration/bf-11-8`(병합 뒤 `main` `179c949`).

| 파일 | 트리 | 판정 |
|---|---|---|
| `gates-all-integ1.log` | `ece6d95` (bf-9 병합 전 · 서비스 venv 전) | green 40 · red(판정) 0 · red(준비) 10 — 워크트리 `.venv`·postgres 대기 |
| `gates-all-integ2.log` | `7358439` (venv 뒤) | green 49 · red(판정) 0 · red(준비) 1 — `rls-effect-selftest` 임시 서버 오탐 → `§9 〈332〉` |
| `gates-all-integ3.log` | `6bb3a9b` (대기 정밀화 뒤) | green 50 · red 0 (한 실행) |
| `gates-all-integ4.log` | `768fccc` (수용 검토 반영 최종) | green 50 · red 0 (한 실행) |

⚠ `*.log` 는 `.gitignore`(`*.log`) 대상이라 **이 체크아웃에만 남는다**(추적 0건 선례). 추적되는 기록은 위 표와 `§9` 값이다.

`status-map-20260905.md` = 회차 착수 전 상태 지도(대장·인계 문서 실측). 값·근거의 정본은 `PLAN-SoT §9 〈327〉~〈333〉`.
