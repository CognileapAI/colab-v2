# schemas — 공통 모델

모든 도메인이 공유하는 최소 집합. **여기 있는 것만 shared kernel이다.**

- `common.json` — 정규 ID 타입 등

## 정규 ID 타입

v1(PoC)은 `users.id`를 `String(20)`·`String(30)`·`String(36)`으로 제각각 선언해 스키마가 갈라졌다.
v2는 **여기 한 곳에서만 정의**하고 pydantic·TS·ORM 전부 이 정의에서 생성한다. 발산이 구조적으로 불가능해진다.
