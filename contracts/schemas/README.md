# schemas — 공통 모델

모든 도메인이 공유하는 최소 집합. **여기 있는 것만 shared kernel이다.**

- `common.json` — 정규 ID 타입 등

## 정규 ID 타입

v1(PoC)은 `users.id`를 `String(20)`·`String(30)`·`String(36)`으로 제각각 선언해 스키마가 갈라졌다.
v2는 **여기 한 곳에서만 정의**하고 pydantic·TS·ORM 전부 이 정의에서 생성한다. 발산이 구조적으로 불가능해진다.

## 값 집합 (enum)

`common.json` 은 정규 ID 외에 **정본이 열거한 값 집합 전부**를 담는다 (`PLAN-SoT §9-⑲`).
seam·이벤트·DB CHECK·프런트 타입이 전부 여기서 생성된다 — **seam 안에서 enum 을 다시 선언하지 않는다.**

- **표기 규칙** — 속성 이름은 영문, **enum 값은 정본 한국어 표기 그대로**. 근거·대가는 `dev-package/sessions/D2.md §1`.
- **파생값 2종**(`LineageState` · `ProcessingLevel`)은 `readOnly` 다. 저장 필드·요청 바디에 두지 않는다 (`PLAN-SoT §9-⑳`).
- **AI 규격** — 확신도는 3값 enum이고 숫자·퍼센트 필드가 없다. 근거(`AiRationale`)는 필수·nullable 아님. 배치 승인 타입을 만들지 않는다.
- 정본이 값을 주지 않아 비워 둔 항목 7건은 `dev-package/sessions/D2.md §3`.
