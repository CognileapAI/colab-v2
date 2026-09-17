# Intent: 되돌릴 표에 계정 계열을 올리고 누수창을 닫아 worker 수가 판정을 바꾸지 않게 한다
메타 — 발의자: sungwooHa · 방향 결정: Ted · 작성 2026-09-17 · 승인 2026-09-17(advisor 검토 결과 제시 후 Ted 명시 승인)

## 문제
- 이슈 축자 증상 = "전수 게이트(`gates/run.sh all -j 4` · 내부 worker 12)에서 `service-tests-core-api` 가 red 를 낸다." / "같은 트리를 단독 실행(worker 4)하면 **1,221건 전건 통과**."
- 배선 확인 결과 이슈의 기전 기술은 맞다. `gates/tools/service-tests.sh:127-142`가 `for ((worker=0; worker<JOBS; worker++))` 로 **worker 수만큼** DB `colab_platform_gw<N>` 를 만들고, `:92-94`가 `PYTEST_PARALLEL=(-n "$JOBS" --dist loadfile)` 를 건다. `--dist loadfile` 은 **한 파일의 시험이 한 worker 에 머문다**만 보장하고 파일마다 DB 를 갈지 않는다. DB 는 worker 당 1개이고 시험 파일마다가 아니다.
- DB 배정 주체는 `gates/tools/xdist_core_db.py:10-40`이다. worker 의 `pytest_configure` 에서 `workerid` 로 파일을 읽어 `os.environ["COLAB_CORE_TEST_DATABASE_URL"]` 를 덮어쓴다. 여기까지는 worker 간 격리가 실제로 선다 — **깨지는 곳은 한 worker 안에서 파일이 바뀌는 지점**이다.
- 시험 간 되돌리기는 있다. `services/core-api/tests/conftest.py:425-460`의 autouse 픽스처 `_rollback_p2_rows` 가 매 시험 뒤 기본키 스냅숏 차집합을 지우고 시드를 되돌린다. 그런데 **두 겹으로 선언적이다.**
  - ⑴ **대상이 옵트인이다.** `conftest.py:440` = `if not {"p2_client", "sql", "live_client"} & set(request.fixturenames):` → 되돌리기를 건너뛴다. 모듈 스코프로 자기 `TestClient` 를 세우는 파일(`tests/test_live_endpoints.py:24-33`, `tests/test_dataset_facets.py:22-29`, `tests/test_lab_members.py:26-33`, `tests/test_dataset_detail.py`, `tests/test_scope_kernel.py:26-31`)의 픽스처 이름은 `client`·`factory` 라 이 집합에 걸리지 않는다.
  - ⑵ **표 목록이 손으로 적혀 있다.** `conftest.py:136-171`의 `_CLEANUP` 21개 표에 **계정 계열이 없다**(`d1_account`·`d2_member_role` 부재). 그 표를 쓰는 시험은 되돌리기를 `try/finally` 로 직접 적는다 — `tests/test_lab_members.py:245-250`의 `_purge_member`.
- 그 손수 되돌리기에 **누수창이 있다.** `tests/test_lab_members.py:260-262`에서 `_make_inactive_member` 두 번이 `try:` **밖**에 있다. 두 번째 호출의 `assert made.status_code == 201`(`:236`)이 깨지면 첫 계정은 영구히 남는다. `d1_account` 는 `_CLEANUP` 에 없으므로 autouse 되돌리기도 줍지 않는다.
- 그 잔존 행이 곧바로 이슈가 지목한 실패 이름으로 나타난다.
  - `tests/test_live_endpoints.py:57` = `assert a["memberCount"] == 2 and b["memberCount"] == 1` — A 연구실 계정이 하나라도 남으면 깨진다. `:65` = `a["totalCount"] == 2`, `:63` = `ids == {DS_A1, DS_A2}` 도 같은 계열의 절대 계수다.
  - `tests/test_scope_kernel.py:46` = `SELECT count(*) FROM d3_dataset ... == 2`, `:37` = 경계 없이 `== 0`. 이 파일은 쓰기가 0건이다 — 순수 피해자다.
  - `tests/test_dataset_facets.py:45-49` = `f["주제"] == {"강우·강수": 2}` 등 **DB 전체 값별 건수**. 이 파일도 쓰기 0건이다.
  - `tests/test_access_state_three.py:148-160` = `d2_dataset_access` 전체를 훑는 불변식(`WHERE a.state = '잠김' AND EXISTS ...`), `:208-211` = `SELECT count(*) FROM d2_dataset_access`. 자기 데이터셋으로 좁히지 않는다.
- **worker 수가 바뀌면 파일→worker 배분이 바뀐다.** 그래서 어느 오염원과 어느 피해자가 같은 DB 에 앉는지가 4 와 12 에서 달라진다. 코드 회귀가 아니라는 이슈의 근거("문제 트리와 green 이던 레인 트리의 `services/core-api` 해시가 **완전 동일**")와 정확히 일치한다.
- 이슈 제안 ⑶("전수의 내부 worker 12 가 `-j 4` 와 곱해져 호스트 한도를 넘는 점")은 **배선상 성립하지 않는다.** `gates/config/parallelism.toml:164`가 `service-tests-core-api` 를 `"serial"` 로 선언하고, `gates/run.sh:733`이 단독 게이트를 `run_one "$g" "$solo_inner"` 로 하나씩 돈다. `solo_inner` 는 `gates/run.sh:666`에서 `ncpu` 이고 `-j` 로 나누지 않는다(나누는 쪽은 `:665`의 `inner=$(( ncpu / jobs_n ))` 로, 병렬 풀 전용이다). 즉 단독 구간에는 다른 게이트가 돌지 않으므로 12×4 의 곱은 없다. 12 는 이 호스트의 `ncpu` 이고 4 는 `gates/tools/service-tests.sh:69`의 기본값이다. **worker 4 green / worker 12 red 의 유일한 차이는 배분이지 부하가 아니다.**
- 이슈 제안 ⑵(수집 1221/1222 불일치)도 **독립 원인으로 보이지 않는다.** 이슈가 적은 두 요약줄에서 불일치는 `failed 6 · errors 1` 인 회차에서만 났고 `failed 0 · errors 0` 회차에서는 1221=1221 이었다. 수집 시점에 DB·환경을 읽는 자리를 `services/core-api/tests/**` 에서 찾지 못했다 — `pytest_generate_tests`·`pytest_collection*`·`collect_ignore`·`importorskip`·`skipif` 는 0건이고, 동적 파라미터화는 `tests/test_e2e_s3_real.py:39-45`의 고정 리터럴 `_REAL_FILES`(`:32` `pytestmark = pytest.mark.e2e` 로 항상 deselect 6)와 계약 YAML 을 읽는 `tests/test_not_implemented.py:268` 뿐이라 worker 수와 무관하다. 남는 설명은 판정부 자체다 — `gates/tools/service-tests.sh:232`가 비교하는 두 수의 **출처가 다르다**: `selected` 는 직렬 `--collect-only`(`:166-167` · `-p xdist_core_db` 없음 · 공유 `colab_platform` DB)의 선택 건수이고, `tot` 는 junit `testsuite/@tests`(`:202`)다. 후자는 한 시험이 call 실패와 teardown 오류를 함께 내면 testcase 노드가 둘로 갈리는 자리가 있다. **미측정이다 — 아래 미해결 질문 ①로 둔다.**

## 원한 결과 (proposed outcome)
- `service-tests-core-api` 의 판정이 내부 worker 수에 걸리지 않는다. worker 1·4·12 에서 같은 집합이 green 이다.
- 한 시험이 남긴 행이 **다음 시험 파일**로 넘어가지 않는다. 되돌리기가 시험의 자발적 선언이 아니라 배선의 성질이 된다.
- 한 시험의 실패가 뒤따르는 파일들을 연쇄로 깨뜨리지 않는다. 실패 집합이 실행마다 달라지지 않는다.
- 수집 계수와 실행 계수의 불일치가 나면 그것이 **오라클의 자리 문제인지 대상 집합 문제인지** 요약줄에서 갈린다.

## 영향 범위
- 사용자 / 화면: 없음. 게이트·시험 배선만이다. 제품 코드(`services/core-api/src/**`) 무접촉.
- 서비스 · 스키마 · 계약: 계약·DB 스키마·마이그레이션 변경 0건. 시드(`services/core-api/tests/fixtures/seed.sql`)와 구성(`services/core-api/tests/fixtures/setup-db.sh`)은 읽기만 한다.
- 계약 파괴 여부: 아니오.
- 바뀌는 자리 후보 = `gates/tools/service-tests.sh:92-148`, `gates/tools/xdist_core_db.py:10-40`, `services/core-api/tests/conftest.py:136-171`·`:425-460`, `services/core-api/tests/test_lab_members.py:260-262`.
- 게이트 소요 시간이 늘어난다. 단독 77.0초(이슈 축자)가 기준선이다. 늘어나는 폭은 고른 안에 따라 다르고 미측정이다.

## 제약
- 되돌리기의 기본키 스냅숏 방식은 **2026-09-13 에 시계 의존을 제거하며 들어온 것**이다(`conftest.py:120-125`·`:433-436`, 커밋 `1e48a64b`). 오라클은 `services/core-api/tests/test_cleanup_purge.py` 다. 시각 기준으로 되돌아가지 않는다.
- 되돌리기 경계는 A 연구실 교수로 고정돼 있다(`conftest.py:292-298` `_cleanup_scope`). RLS 때문에 **보이지 않는 행은 스냅숏에도 DELETE 에도 안 걸린다**(`:322-324` 축자 경고). 앱 롤로 도는 되돌리기는 구조적으로 전수가 될 수 없다 — 전수 되돌리기를 원하면 admin URL(`COLAB_CORE_TEST_ADMIN_DATABASE_URL` · `service-tests.sh:119`)쪽이어야 한다.
- 게이트는 fail-closed 다. 수집 0건·실행 0건·준비 실패는 전부 red 이고 종료코드는 판정 실패 1 / 준비 실패 78 이다(`service-tests.sh:16-28`·`:51`). 어떤 안도 「건너뛰어 green」으로 가지 않는다.
- 일회용 postgres 컨테이너는 호스트 전역 슬롯 4개를 나눠 쓴다(`gates/tools/_pg.sh:64-65` · `COLAB_PG_MAX_CONCURRENT` 기본 4). 컨테이너 **수**는 늘리지 않는다 — 늘릴 수 있는 것은 한 컨테이너 안의 DB 수다.
- `parallelism.toml:164`의 `"serial"` 선언은 건드리지 않는다. 같은 파일 `:20` 축자 = "⚠ 값을 `serial` → `parallel` 로 바꾸는 편집은 **격리 요구를 없앤 결정**이지 속도 튜닝이 아니다."
- `COLAB_SERVICE_TEST_JOBS` 는 1~32 canonical 정수만 받는다(`service-tests.sh:70-71`). 전수에서는 `gates/run.sh:726`이 `COLAB_GATE_INNER_JOBS` 로 넘긴 값이 `service-tests.sh:69`의 기본값 자리를 차지한다.
- 이 조사에서 게이트·pytest 를 **한 번도 돌리지 않았다**(지시된 제약). 이 워크트리에 `services/core-api/.venv` 가 없어서 실행 가능한 상태도 아니다. 아래 수치 주장은 전부 이슈 축자 또는 정적 근거다.

## 설계트리 (grill-me 결과)
- Q1 진짜 원인이 「DB 가 worker 당 1개」인가, 「되돌리기가 옵트인」인가 → A **후자가 원인이고 전자는 증폭기다.** DB 가 파일당이어도 `conftest.py:440`의 옵트인은 그대로 남고, 한 파일 안에서 순서 의존이 그대로 산다(`test_lab_members.py` 가 한 파일 안에서 계정을 만들고 지운다). 다만 worker 수가 판정을 바꾸는 성질은 전자에서 온다.
- Q2 이슈 제안 ⑴(worker 당 격리 DB 를 실제로 세운다)을 그대로 받는가 → A **아니다. 이미 서 있다.** `xdist_core_db.py:10-40`이 worker 마다 다른 URL 을 주입하고 `service-tests.sh:127-142`가 DB 를 그만큼 만든다. 이슈의 문면은 배선 결함을 말하지만 배선은 선언대로 동작한다 — 결함은 **한 worker 안**이다.
- Q3 이슈 제안 ⑶(12×4 곱)을 받는가 → A 아니다. `parallelism.toml:164` serial ＋ `run.sh:666`·`:733`이 곱을 막는다. 이슈 발의 시점의 추정이고 배선이 반증한다.
- Q4 수집 1221/1222 를 독립 결함으로 세우는가 → A 아니다. 실패 0 회차에는 안 났다. 계수 파생으로 보고 **미해결 질문 ①**로 남긴다. 다만 `service-tests.sh:232`가 이질적인 두 수를 비교하는 것 자체는 사실이다.
- Q5 (a) worker 당 DB ＋ 매 시험 truncate 를 고르는가 → A **아니다.** 전수 truncate 는 앱 롤 경계 때문에 서지 않고(`conftest.py:322-324`), admin 롤로 올리면 되돌리기가 RLS 를 우회하는 자리가 되어 **경계 증명 시험들이 자기 우회로를 얻는다**(`test_cross_tenant.py`·`test_body_access.py` 가 재는 것이 정확히 그 경계다). 매 시험 시드 재적용은 1221건×스키마·시드 왕복이라 77.0초 기준선을 자릿수로 넘긴다.
- Q6 (b) `--dist loadfile` → 파일당 DB 를 고르는가 → A **아니다.** core-api 시험 파일은 114개다(`services/core-api/tests/test_*.py`). 한 컨테이너에 DB 114개를 세우고 각각 `setup-db.sh` 로 스키마·롤·시드를 적용하면 준비 구간이 판정 시간을 압도하고, `_pg.sh` 슬롯 4개를 쥔 채 도는 시간이 길어져 다른 게이트의 준비 실패(78)를 늘린다. 이슈가 쓴 "DB 는 **worker 당 1개이고 시험 파일마다가 아니다**"는 진단은 맞지만 처방으로 뒤집으면 비용이 안 맞는다.
- Q7 (c) 문제 시험을 자기 격리형으로 고치는가 → A **이것을 권한다.** 두 갈래다. ㈎ **누수창을 닫는다** — `test_lab_members.py:260-262`의 `_make_inactive_member` 두 호출을 `try:` 안으로 넣거나 픽스처로 올려 생성 실패에도 purge 가 돌게 한다. ㈏ **절대 계수 오라클을 자기 소유로 좁힌다** — `test_live_endpoints.py:57`·`:65`, `test_scope_kernel.py:37`·`:46`, `test_dataset_facets.py:45-49`·`:58`·`:63-66`, `test_access_state_three.py:148-160`·`:208-211`. 다만 ㈏ 는 **오라클의 세기를 낮춘다** — 이 시험들이 절대 계수인 것은 우연이 아니라 경계 누출을 재기 위해서다(`test_live_endpoints.py:57` 축자 "구성원 수가 경계를 넘어 세어졌다.").
- Q8 (d) 내부 worker 를 4로 캡하는가 → A **단독으로는 아니다.** `service-tests.sh:69`에 상한을 두면 전수가 green 으로 돌아오지만 원인은 그대로 있고, 파일이 늘거나 순서가 바뀌면 worker 4 에서도 같은 일이 난다. 다만 **근본 수정과 함께라면** 재발 탐지를 위해 값을 고정하는 의미가 있다. 「4 에서 green 이니 4로 못 박는다」는 병렬도를 낮춰 red 를 덮는 것이고 `parallelism.toml:9-11` 이 명시로 금지한 무늬다.
- Q9 그러면 권고는 무엇인가 → A **(c) ＋ 배선 한 줄.** ㈎ `conftest.py:440`의 옵트인 집합을 없애고 되돌리기를 **무조건 돌게** 한다(픽스처 이름으로 가르지 않는다 — 가르는 순간 새 시험 파일이 조용히 제외된다). 되돌리기 비용은 스냅숏 질의 1회＋DELETE 21회＋`_RESTORE` 14문이라 시험당 상수다. ㈏ `test_lab_members.py:260-262`의 누수창을 닫고 `d1_account`·`d2_member_role` 을 `_CLEANUP`(`conftest.py:136-171`)에 올려 손수 purge 를 배선으로 흡수한다. ㈐ ㈎㈏ 뒤에도 남는 파일 간 의존은 **그때 측정해서** 해당 오라클만 좁힌다 — 먼저 좁히면 무엇이 고쳐졌는지 알 수 없다.

## 미해결 질문
- ① 수집 1221 ↔ 1222 의 확정 기전. 후보 둘 = ㈎ 한 시험이 call 실패 ＋ teardown 오류를 함께 내어 junit testcase 노드가 둘로 갈린다 ㈏ xdist worker 가 죽어 항목이 재배정되며 두 번 실행된다. **게이트를 돌지 않고는 가를 수 없다.** 실행 제약 때문에 미측정으로 남긴다. 이슈 제안 ⑵("원인 확정")는 이 질문이다.
- ② 되돌리기를 무조건 실행으로 바꿨을 때의 실제 소요. 기준선은 이슈 축자 77.0초(worker 4)다. 되돌리기를 건너뛰던 시험이 몇 건인지 — 정적으로는 모듈 스코프 `client` 를 받는 시험 57건(`grep "^def test_.*(client: TestClient)"`)이 후보다.
- ③ `d1_account`·`d2_member_role` 을 `_CLEANUP` 에 올릴 때 FK 순서와 앱 롤 권한. `test_lab_members.py:222-225` 축자 = "`login_credential` 은 `d1_account` 에 `ON DELETE CASCADE` 로 달려 있고(schema.sql:135), 계정 관리자 롤에는 애초에 DELETE 권한이 없다(`ops/account-admin-role.sql`)." 앱 롤이 `d1_account` 를 지울 수 있는지 미확인.
- ④ `service-tests.sh:232`의 `tot != selected` 비교를 그대로 둘지. 두 수의 출처가 다르다는 점은 확인했으나, 오라클을 손대는 것은 **게이트가 자기 red 를 무디게 하는 방향**이라 별도 판단이 필요하다.
- ⑤ worker 12 를 유지할지 4로 고정할지. Q8 결론은 「근본 수정과 함께라면 의미 있음」이고 단독 캡은 반대다.

## 범위 밖 (명시 제외)
- 게이트 실행·전수 실행·pytest 실행. 이 조사는 정적 대조만 했다. 이 워크트리에 `services/core-api/.venv` 가 없다.
- `parallelism.toml` 의 `"serial"` 선언 변경. `:20` 축자가 근거 없는 변경을 금지한다.
- `_pg.sh` 의 `COLAB_PG_MAX_CONCURRENT` 상한 인상. `parallelism.toml:117` 축자 = "슬롯 한도를 올려 green 을 만들지 않는다 — 한도는 이 호스트가 감당하는 값이다."
- 되돌리기를 admin 롤로 올려 RLS 를 우회하는 방식. 경계 증명 시험이 재는 대상 자체를 무디게 한다.
- `services/core-api/src/**` 제품 코드 변경. 이 이슈는 시험·게이트 배선 결함이고 제품 회귀가 아니다(이슈 축자 = "코드 회귀 아님").
- core-api 외 `service-tests-ai-service`·`viz-render`·`pipeline-worker`. 이 셋은 일회용 DB 를 세우지 않는다(`service-tests.sh:95-150`의 `case` 에 `core-api` 만 있다).
- 다른 이슈 구현, 커밋·push·PR 게시·배포·이슈 댓글·종결.

## 확인
- Ted 확인 문장: 대기 중.
- 승인 필요 지점:
  1. **원인 판정의 정정을 받는가.** 이슈 제안 ⑶(12×4 곱)을 배선 근거로 기각하고, 제안 ⑴(worker 당 격리 DB)을 「이미 서 있음」으로 정정하며, 진짜 원인을 `conftest.py:440`의 옵트인 되돌리기 ＋ `_CLEANUP` 표 목록 누락으로 세운다.
  2. **수정 형태를 (c) 자기 격리형으로 가는가.** 후보 (a) 매 시험 truncate · (b) 파일당 DB · (d) worker 캡 셋을 물리고, 되돌리기 무조건화 ＋ 누수창 닫기 ＋ 표 목록 보강으로 간다.
  3. **오라클을 좁히는 범위.** `test_live_endpoints.py:57`·`:65` 등 절대 계수 단언을 자기 소유로 좁히는 것은 경계 누출 탐지력을 낮춘다. ㈎ 지금 좁힌다 ㈏ 되돌리기 수정 뒤 남는 것만 좁힌다(권고) 중 택일.
  4. **미해결 질문 ①의 처리.** 게이트 1회 실행 없이는 1221/1222 기전을 확정할 수 없다. ㈎ 이번 범위에서 빼고 별도 이슈 ㈏ 레인에서 측정 허용 중 택일.
  5. **`COLAB_SERVICE_TEST_JOBS` 값의 처분.** 근본 수정 뒤 worker 12 로 둘지, 재발 탐지를 위해 값을 못 박을지.
  6. **이 이슈의 대장 처리.** 이슈 축자 = "미등재 — `dev-package/prd/rounds/R-DEV-RESET.md` §11 후속(advisor 지적)". 신규 legacy 결정번호를 발급하지 않는 것이 기본이다.
- 재개봉 금지: 해당 없음(승인 전).

## 참조
- 이슈: https://github.com/CognileapAI/colab-v2/issues/47
- 게이트 배선: `gates/tools/service-tests.sh:69`·`:70-71`·`:92-94`·`:117-121`·`:122-148`·`:166-172`·`:173-176`·`:202`·`:232-234`
- worker DB 주입: `gates/tools/xdist_core_db.py:10-40`
- 실행기: `gates/run.sh:659-673`·`:699`·`:726`·`:733`
- 병렬 선언: `gates/config/parallelism.toml:9-11`·`:20`·`:117`·`:158-167`
- pg 슬롯: `gates/tools/_pg.sh:64-65`·`:69-95`
- 되돌리기: `services/core-api/tests/conftest.py:120-125`·`:136-171`·`:193-289`·`:292-298`·`:319-347`·`:425-460`
- 되돌리기 오라클: `services/core-api/tests/test_cleanup_purge.py`
- 누수창: `services/core-api/tests/test_lab_members.py:222-225`·`:227-243`·`:245-250`·`:260-262`
- 피해 오라클: `services/core-api/tests/test_live_endpoints.py:24-33`·`:57`·`:63-65`·`:100-115`, `services/core-api/tests/test_dataset_facets.py:22-29`·`:45-49`·`:58`·`:63-66`, `services/core-api/tests/test_scope_kernel.py:26-31`·`:37`·`:46`·`:54`, `services/core-api/tests/test_access_state_three.py:148-160`·`:208-211`
- 수집 변동 후보 조사: `services/core-api/tests/test_e2e_s3_real.py:32`·`:39-45`·`:89-90`, `services/core-api/tests/test_not_implemented.py:268`·`:286`
- 핀: `services/core-api/requirements-dev.txt:15-16` (`pytest==8.4.2` · `pytest-xdist==3.8.0`)
- 이슈가 건 근거: `dev-package/reports/r-dev-reset/full-gate-diagnosis.md` A절 · `dev-package/prd/rounds/R-DEV-RESET.md` §11
- 선행 커밋: `1e48a64b` 시험 간 되돌리기를 시각 기준에서 기본키 스냅숏 기준으로 바꾼다
- spec: 미작성. Ted 승인 뒤 합성한다.
- 결정: 신규 legacy 결정번호 발급 없음.

## advisor 검토 결과 (2026-09-17, 초안 작성 후 추가)
- [정정] 권고 ㈎(옵트인 집합 제거)는 진단한 실패의 원인이 아니다. 누수 시험 `test_lab_members.py:254`
  `test_an_inactive_account_is_marked_and_locked` 는 이미 `p2_client` 와 `sql` 을 함께 받으므로
  `_rollback_p2_rows` 가 **이미 돈다**. 깨지는 것은 `_CLEANUP` 의 표 누락과 `:260-262` 누수창이다.
  즉 ㈏ 만으로 인용된 누수가 닫힌다.
- [비용] ㈎ 는 별건의 훨씬 큰 변경이다. `_rollback_p2_rows` 가 `conftest.py:62` `session_factory`
  (→ `app_db_url`)에 기대므로 무조건화하면 DB 를 만지지 않는 시험까지 포함해 약 1,221건 전부에
  DB 세션 ＋ 21표 PK 스냅샷 ＋ `_RESTORE` 가 붙는다. 기준선 77.0초 대비 증가분은 미측정이며
  초안의 「시험당 상수」 근거와 미해결 질문 ②의 57건 추정은 실측이 아니다.
- [해소] 미해결 질문 ③의 DELETE 권한 블로커는 실물 확인으로 해소됐다. 되돌리기는 **앱 롤**로 돌고
  `services/core-api/ops/app-role.sql:40` 이 `GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES`
  를 준다. DELETE 가 없는 것은 **계정 관리자 롤**이며(`ops/account-admin-role.sql:49-52` — `d1_account`
  에 SELECT·INSERT 만), 이는 시험 되돌리기 경로가 아니다. ㈏ 는 초안대로 성립한다.
- [정정] `_purge_member` 범위는 `:245-251` 이다(초안 `:245-250`).
- [주의] 「12 는 이 호스트의 ncpu」는 이슈 수치에서 추론한 것이고 읽어서 확인한 값이 아니다.
  또한 `gates/run.sh:672-673` 이 운영자가 설정한 `COLAB_GATE_INNER_JOBS` 로 `solo_inner` 를 덮게
  하므로, 초안의 모형은 그 변수가 설정되지 않은 경우에만 성립한다.
- [확인] 이슈의 「worker 12 × `-j 4` 곱」 기각은 옳다. `parallelism.toml:164` serial ·
  `run.sh:666` `solo_inner="$ncpu"` · `:733` 단독 게이트 순차 · `:726` 내부 jobs 전달로 교차 확인됐다.

## 승인 (2026-09-17)
- Ted 확인 문장(원문 그대로): "권고대로  분리해"
- 수용한 권고 — 이 intent 해당분:
  - 수정 형태는 **㈏ 만**이다. `_CLEANUP` 에 `d1_account`·`d2_member_role` 을 올리고
    `test_lab_members.py:260-262` 의 누수창을 닫는다. 손수 purge 는 배선으로 흡수한다.
  - **㈎(옵트인 집합 제거)는 이번 범위 밖이다.** 진단한 누수의 원인이 아니고, 약 1,221건 전부에
    DB 세션 ＋ 21표 스냅샷을 붙이는 미측정 비용이다. 필요하면 별도 이슈로 낸다.
  - 절대 계수 오라클 축소는 **되돌리기 수정 뒤 남는 것만** 대상으로 한다. 지금 좁히지 않는다.
    좁히면 경계 누출 탐지력이 떨어진다.
  - 수집 1221/1222 기전 확정은 호스트 단독 전수 `-j 4` 예산 안에서 확인한다(전체 3회 배정).
    그 예산 안에서 확정되지 않으면 미증명으로 남기고 별도 이슈로 낸다.
  - `COLAB_SERVICE_TEST_JOBS` 처분과 대장 처리는 초안의 판단을 그대로 둔다. 신규 legacy
    결정번호를 발급하지 않는다.
- PR 단위: **이 건은 단독 PR 1건**이다. #55·#56 과 묶지 않는다.
  근거 = `gates/run.sh` `summary_gate_row()` 를 건드리지 않는 유일한 건이라 독립이다.
- 재개봉 금지: 예. ㈎ 기각과 오라클 축소 시점을 다시 질문하지 않는다.
