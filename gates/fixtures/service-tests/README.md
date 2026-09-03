# service-tests 픽스처 — `service-tests-selftest` 가 쓰는 red/green 트리

이 자리의 트리는 **게이트가 red 를 낼 수 있는지**를 재기 위한 것이다. 어느 서비스의 시험도 아니고,
어떤 CI 잡도 이것을 서비스 묶음으로 돌리지 않는다 — 서비스의 `testpaths` 는 각 `pyproject.toml` 이
`tests` 로 못박고 rootdir 도 서비스 자리다. 이 폴더는 그 밖이다.

셀프테스트는 이 트리를 **`mktemp -d` 로 복사한 뒤** 거기서 돈다. 레포 안에서 pytest 를 돌리면
`__pycache__` 가 남고, 그것이 스캔 게이트의 대상이 된다.

| 트리 | 무엇을 재나 | 기대 |
|---|---|---|
| `pass/` | 통과 시험 1건 — 이것이 green 이 아니면 아래 red 들은 아무 말도 하지 않는다 | green |
| `fail/` | 실패 시험 1건 — 실패를 못 잡으면 게이트가 아니다 | red |
| `empty/` | 시험 파일 0건 — **수집 0건을 통과로 세지 않는다**(green-by-skip 금지) | red |
| `allskip/` | 수집은 되는데 **전부 skip** — 수집만 하고 안 돈 것도 판정이 아니다 | red |
