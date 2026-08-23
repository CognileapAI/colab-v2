# contracts — 계약 권위체 (SSoT)

도메인 간 유일한 API. **여기가 드리프트의 유일한 발원지이자 유일한 방어선이다.**

## 무엇이 계약인가

"계약"은 HTTP만이 아니다. v1(PoC)에서 실제로 터진 버그는 셋 다에서 났다.

| 종류 | 어디 | 강제 |
|---|---|---|
| **seam (sync)** | `seams/` — FE↔core · core↔viz · core↔ai | 손작성 OpenAPI. 스펙 린트 + 파괴적 변경 탐지 |
| **이벤트 (async)** | `events/` — core↔pipeline | JSON-Schema 봉투 + 멱등 키 + DLQ 재처리 규칙 |
| **DB 스키마** | `schemas/` + `../db/` | 정규 ID 타입 1곳 정의 · 스키마 diff · single-head |

## 규칙

1. **seam은 손으로 쓴다.** 안정적이고 수가 적고 값이 높다.
2. **도메인 내부 엔드포인트는 code-first로 emit**하고, emit 결과가 frozen seam과 충돌하면 **CI가 거부**한다.
3. **생성물은 커밋한다.** `codegen/` 산출물이 최신인지는 `generated-up-to-date` 게이트가 검증할 자리다 — **아직 미구현 red 다** (`gates/README.md` · `SEAM-AUDIT.md` I-21). 구현 전까지 이 규칙은 관례로만 서 있다.
4. **소비자는 생성물만 쓴다.** 손수정 금지.
5. `contracts/` 변경은 **필수 리뷰**(CODEOWNERS).

## seam 목록

| seam | 성격 | 특이사항 |
|---|---|---|
| FE ↔ core-api | sync | 역사적으로 드리프트가 가장 많이 나는 곳 |
| core-api ↔ viz-render | sync | |
| **core-api ↔ ai-service** | sync | **degraded 응답 규격 필수** — AI 장애가 제품을 멈추면 안 된다 |
| core-api ↔ pipeline-worker | async | 이벤트 봉투. 가장 활발한 드리프트 면 |

## AI seam이 반드시 담아야 하는 것

정본(260818)이 못 박은 규칙을 **타입으로** 옮긴다. 관례로 두지 않는다.

- 확신도는 `확실 | 애매 | 모름` **enum**. 숫자·퍼센트 필드 없음
- 근거 필드 **필수**(nullable 아님)
- 검색 응답에 **탐색 범위** 필드 필수, 근거는 **한 줄** 길이 제약
- **배치 승인 엔드포인트 없음**
- 빈 결과가 정상 응답
