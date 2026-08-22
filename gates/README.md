# gates — 경계를 기계가 지킨다

v1(PoC)에서 터진 버그는 전부 **"관례로 지키기로 했던 것"** 이었다. v2는 관례를 두지 않는다.

| 게이트 | 무엇을 막나 |
|---|---|
| `contract-lint` | seam 스펙 오류 |
| `contract-breaking` | emit된 스펙이 frozen seam과 충돌 |
| `generated-up-to-date` | 생성물이 계약보다 낡음 |
| `import-boundary` | 도메인 간 직접 참조 |
| `banned-import` | core-api의 geo 라이브러리 |
| **`ai-no-lineage-write`** | **D10 → D4 쓰기 경로 존재** (음성) |
| `migration-single-head` | 마이그레이션 head 분기 (platform / ai 각각) |
| `schema-diff` | 선언 스키마 ↔ 적용 DB 드리프트 (**체인별로 각각** — `COLAB_APPLIED_DB_URL_PLATFORM` · `_AI` 둘 다 필요) |
| `rls-coverage` | allow-list 밖 테이블의 RLS 누락 |
| `planning-freshness` | 기획 패키지 HTML의 임베드 md가 원본 md보다 낡음 (정본 미마운트 포함) |
| `selftest` | **위 게이트들이 실제로 red를 낼 수 있는지** (contract · boundary · db 증명 셋) |

## selftest가 있는 이유

"전부 green"과 "전부 무력"은 구분되지 않는다. v1 CI는 DB 없이 돌아 RLS 테스트를 **green-by-skip** 했다.
각 게이트는 red fixture로 자신이 fail-closed임을 증명해야 한다.

## 현재 상태 (2026-08-23)

**미구현 게이트는 red 를 낸다.** 우회하거나 끄지 않는다.

| 게이트 | 상태 | 지금 red 인 이유 |
|---|---|---|
| `planning-freshness` | ✅ 구현 (WU-G1) | — green |
| `contract-lint` · `contract-breaking` | ✅ 구현 (WU-D2) | — green |
| `import-boundary` · `banned-import` · `ai-no-lineage-write` | ✅ 구현 (WU-D3) | **red — `services/` 에 코드가 없다** |
| `migration-single-head` · `rls-coverage` | ✅ 구현 (WU-D3) | — green (P0 이 `db/` 를 채웠다) |
| `schema-diff` | ✅ 구현 (WU-D3) · 체인별 URL 로 수정 | 체인별 적용 DB URL 을 **둘 다** 주면 green. 하나라도 없으면 red |
| `generated-up-to-date` | ⬜ 미구현 | red |

> **red 인 것이 정상인 게이트가 있다.** "AI 가 계보에 쓰지 않는다"와 "AI 가 아직 없다"는 다른 사실이라, 검사 대상 0건을 green 으로 세지 않는다. 이 게이트들은 P0 이 코드를 만들면 비로소 green 이 될 수 있다.

## 자기 증명 (selftest)

각 게이트가 **자기가 fail-closed 임을 red fixture 로 증명**한다. 증명 셋은 셋으로 나뉘어 있다 — 서로의 인프라 사고에 걸리지 않게 하기 위해서다.

| 셋 | 케이스 | 의존 |
|---|---|---|
| `contract-selftest` | **15** | docker(oasdiff) · spectral |
| `boundary-selftest` | **30** | python venv |
| `db-selftest` | **43** | docker(postgres) — 24 는 docker 없이도 돈다 |
| `selftest` | 위 셋 전부 | |

`planning-freshness` 의 증명은 `dev-package/tools/check-package-freshness.py --selftest`(3 케이스).
