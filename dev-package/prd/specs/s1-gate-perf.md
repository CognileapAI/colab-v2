# G10 게이트 내부 병렬화

출처: `work-items.yaml` G10, `stage1-stage2-closeout.md`. 빠르게 돌기 위해 보는 범위나 세 상태 판정을 줄이지 않는다.

## 계약

- 게이트 사이 `serial` 선언은 그대로다. 병렬화는 각 단독 게이트 안에서만 일어난다.
- 서비스 pytest는 기본 4 worker, `COLAB_SERVICE_TEST_JOBS`로 1~32를 명시할 수 있다. 1은 전후 비교용 직렬 경로다.
- core-api는 worker마다 별도 일회용 DB를 구성한다. 같은 seed DB를 공유하는 xdist는 허용하지 않는다.
- xdist 또는 worker DB 준비가 없으면 종료 78이다. 병렬화를 조용히 직렬로 낮춰 green을 만들지 않는다.
- pytest 선택자, strict marker, 프로젝트 설정, 수집·실행·skip·deselect·fail/error 판정은 기존과 같다.
- frontend vitest의 기존 내부 worker를 보존한다. 별도 프로세스 중첩은 하지 않는다.
- 상태를 공유하는 shell selftest는 독립 fixture 단위가 확인된 경우만 병렬화한다. 격리를 증명하지 못한 케이스는 범위를 줄이지 않고 직렬로 둔 뒤 G10을 닫지 않는다.

## 완료 증거

- 같은 tree에서 jobs=1과 jobs=4의 네 서비스 계수 대조.
- core-api worker별 DB 이름과 준비 건수는 노출하되 URL·비밀번호는 출력하지 않는다.
- `service-tests-selftest`의 green/red/준비 red 픽스처 전건 통과.
- 전체 `gates/run.sh all -j 4` 전후 실측은 같은 선언 수와 세 계수를 가져야 한다.
