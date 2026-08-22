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
| `selftest` | **위 게이트들이 실제로 red를 낼 수 있는지** |

## selftest가 있는 이유

"전부 green"과 "전부 무력"은 구분되지 않는다. v1 CI는 DB 없이 돌아 RLS 테스트를 **green-by-skip** 했다.
각 게이트는 red fixture로 자신이 fail-closed임을 증명해야 한다.

## 현재 상태

`run.sh`는 골격이며 **미구현 게이트는 red를 낸다.** WU-D3에서 채운다.
