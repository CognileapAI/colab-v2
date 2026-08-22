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
| `schema-diff` | 선언 스키마 ↔ 적용 DB 드리프트 |
| `rls-coverage` | allow-list 밖 테이블의 RLS 누락 |
| `planning-freshness` | 기획 패키지 HTML의 임베드 md가 원본 md보다 낡음 (정본 미마운트 포함) |
| `selftest` | **위 게이트들이 실제로 red를 낼 수 있는지** |

## selftest가 있는 이유

"전부 green"과 "전부 무력"은 구분되지 않는다. v1 CI는 DB 없이 돌아 RLS 테스트를 **green-by-skip** 했다.
각 게이트는 red fixture로 자신이 fail-closed임을 증명해야 한다.

## 현재 상태

`run.sh`는 아직 골격이 남아 있고 **미구현 게이트는 red를 낸다.** 남은 것은 WU-D3의 뒷절반에서 채운다.

| 구현됨 | WU | 실행체 |
|---|---|---|
| `planning-freshness` | G1 | `dev-package/tools/check-package-freshness.py` (표준 라이브러리만) |
| `contract-lint` · `contract-breaking` · `contract-selftest` | D2 | `gates/tools/contract-*.sh` |
| `import-boundary` · `banned-import` · `ai-no-lineage-write` · `boundary-selftest` | D3 | `gates/tools/import-boundary.sh` · `banned-import.py` · `ai-no-lineage-write.sh` · `boundary-selftest.sh` |

경계 게이트 3종의 판정 방식·모듈 경로 관례·한계는 `dev-package/sessions/D3-boundary.md`.
설정은 `gates/config/boundaries.toml`(배포 단위·금지 목록)과 `gates/config/importlinter.ini`(경계 계약),
도구 버전은 `gates/requirements.txt`가 고정한다(`gates/.venv`는 게이트가 스스로 만든다).

예외로 **`planning-freshness` 는 구현돼 있다** (WU-G1). 실행체는 `dev-package/tools/check-package-freshness.py` —
표준 라이브러리만 쓰고, `--selftest` 로 변조 fixture·정본 부재 두 경우 모두 red 를 냄을 증명한다.
