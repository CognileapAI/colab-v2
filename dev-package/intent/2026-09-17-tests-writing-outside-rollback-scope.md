# Intent: 되돌리기 경계 밖 쓰기를 소리 나게 만들어 #47 의 잔여 원인을 끊는다
메타 — 발의자: Ted · 방향 결정: Ted · 작성 2026-09-17 · 승인: 미승인 — Ted 승인 대기

## 문제
- 되돌리기 경계는 A 연구실 한 곳이다. `services/core-api/tests/conftest.py:292-298` 의 `_cleanup_scope()` 가 `Subject(account_id=ACC_A_PROF, lab_id=LAB_A)` 로 `apply_scope` 한다. 독스트링 축자 — 「되돌리기가 서는 자리 — A 연구실 교수. 스냅숏과 삭제가 **같은 경계**여야 한다.」
- 기본키 스냅숏(`conftest.py:319-333`)과 DELETE 패스(`conftest.py:336-347`)가 둘 다 그 경계에서 돈다. `:322-323` 주석이 요건을 축자로 적는다 — 「보이지 않는 행은 스냅숏에도 없고 DELETE 에도 안 걸리므로, 경계가 다르면 남을 행을 지우게 된다.」
- 그래서 **경계 밖 쓰기는 조용히 산다**. RLS 가 A 경계에서 가리는 행(= `LAB_B`·`LAB_C` 행)은 `:328-329` 의 UNION 스냅숏에 안 잡히고 `:344` 의 `DELETE ... WHERE (key) <> ALL(:keys)` 에도 안 걸린다. 커밋된 채로 같은 xdist worker 의 다음 시험 파일로 샌다. `#47` 의 계정 표 수정이 끝난 뒤에도 남은 실제 원인이 이것이다.
- 구멍이 하나 더 있다. autouse 훅 `conftest.py:425-460` 은 `:440-442` 에서 `{"p2_client", "sql", "live_client"}` 를 하나도 안 쓰는 시험에 대해 되돌리기를 **통째로 건너뛴다**. 그 시험들은 정리의 수혜자도 아니다.

### 누가 경계 밖에 쓰는가 (B 연구실 데이터셋 3건 — 관측 잔존물과 건수 일치)
- `services/core-api/tests/test_admin_actor_visibility.py:38` — `_register(client, {**auth(token), "X-CoLAB-Target-Lab": LAB_B})`. 이 시험은 `:24` 의 `@pytest.mark.parametrize("labless", [False, True])` 로 **2회** 돈다. 등록 경로는 `:12-21` 의 `POST /api/v1/uploads` → `POST /api/v1/datasets` 이고 API 가 커밋한다. `:51-57` 은 `postgres` 슈퍼유저로 `lab_id == LAB_B` 를 **확인만** 한다. 파일 전체에 그 데이터셋을 지우는 자리가 없다.
- `services/core-api/tests/test_admin_actor_visibility.py:62` — `_register(client, auth("b1-prof-token"))`. **1회**. 회수 없음. `:64-66` 이 그 위에 `d4_lineage_edge` 까지 하나 더 얹는다.
- 합계 3건이며 셋 다 `lab_id = LAB_B` 다. `_cleanup_scope`(LAB_A)의 스냅숏·DELETE 양쪽에서 보이지 않는다.

### 왜 하필 `test_pool_no_leak.py` 의 2건인가
- `services/core-api/tests/test_pool_no_leak.py` 의 세 시험은 `app_db_url`·`subjects_file` 만 받는다(`:26`·`:53`·`:82`). `p2_client`·`sql`·`live_client` 를 하나도 안 쓰므로 `conftest.py:440-442` 가 되돌리기를 건너뛴다.
- 이 파일의 오라클은 **절대 집합**이다. `:48` `== {DS_B1}` · `:99` `== {DS_B1}` · `:106` `== {DS_B1}`. B 연구실에 데이터셋이 1건이라도 더 있으면 즉시 깨진다.
- 셋 중 B 를 절대 집합으로 재는 것은 `:26`(`test_set_local_does_not_bleed_into_the_next_request`)과 `:82`(`test_no_bleed_across_http_requests_on_one_connection`) **둘**이다. 가운데 `:53` 은 A 만 `count == 2` 로 재므로(`:74`) A 경계 정리가 지킨다. 보고된 「`test_pool_no_leak.py` — 2 tests」 red 와 건수·자리가 정확히 일치한다.
- `COLAB_SERVICE_TEST_JOBS=12`(기본 4 — `gates/tools/service-tests.sh:69`)에서 3회 중 1회만 red 인 것도 이 기전과 맞는다. 누출 파일과 피해 파일이 같은 worker 에 같은 순서로 떨어져야 터진다. 배분이 달라지면 같은 트리가 green 을 낸다.

### 규율은 있는데 기계가 강제하지 않는다
- `services/core-api/tests/test_project_name_duplicate.py:69-70` 축자 주석 — 「B 연구실 행은 `p2_client` 정리가 닿지 않는다. 시험이 스스로 되돌린다.」 `:100-118` 의 다른 시험도 같은 주석(`:103`)과 `finally` 회수(`:116-118`)를 단다.
- `services/core-api/tests/test_operator_designation.py:539-572` 의 `_own_lab_dataset` 은 `LAB_C` 스코프로 `d3_dataset`·`d3_dataset_description` 을 커밋하고(`:554`·`:557`) `finally`(`:570-572`)에서 지운다.
- 즉 「경계 밖에 쓰면 스스로 지운다」는 관행이 이미 존재한다. 빠뜨린 파일이 조용히 새는 것이 문제다. 관행을 지킨 파일과 어긴 파일을 **가르는 장치가 없다**.

### 별건 — 수집계수 불일치(1221 vs 1222)는 재현되지 않았다
- 이슈가 보고한 수집계수 불일치를 재현한 회차가 없다. 현 트리는 1383건을 수집하고 모든 회차에서 `collect == run` 이었다(전수 회차를 돌린 레인의 보고). 이 intent 는 그 기전을 만들어 내지 않는다.
- 직렬 단일 DB 전수 회차를 `#47` 계정 표 수정 **전후**로 각각 돌렸을 때 실패 11건의 집합이 **동일**했다. 그러므로 11건은 선행 결함이고 계정 표 수정과 무관하다. 집합은 `test_cross_tenant`(3) · `test_dashboard`(1) · `test_grid_convenience`(1) · `test_live_endpoints`(2) · `test_operator_designation`(1) · `test_pool_no_leak`(2) · `test_search_execution`(1) 이다.

## 원한 결과 (proposed outcome)
- 되돌리기 경계 밖에 커밋된 행이 남으면 **그 시험이 자기 이름으로 실패한다.** 다음 파일의 개수 오라클이 대신 깨지지 않는다.
- `test_pool_no_leak.py:26`·`:82` 가 worker 배분과 무관하게 같은 판정을 낸다. `COLAB_SERVICE_TEST_JOBS=12` 3회 연속 green.
- 경계 밖 쓰기를 하는 시험은 계속 허용된다. cross-tenant 증명은 경계 밖 쓰기 없이는 공허해진다 — 금지가 아니라 **회수 의무의 기계화**가 목표다.
- 수집계수 불일치는 이번에 고치지 않는다. 재현되지 않았다는 사실을 기록으로 남긴다.

## 영향 범위
- 시험 하네스: `services/core-api/tests/conftest.py`(가드 fixture 추가 · `:425-460` 훅 조건 조정).
- 시험 파일: `services/core-api/tests/test_admin_actor_visibility.py:38`·`:62`(자기 회수 추가).
- 서비스 · 스키마 · 계약: 없음. 제품 코드·마이그레이션·계약을 건드리지 않는다.
- 게이트: `gates/run.sh service-tests-core-api` 의 판정만 바뀐다. 게이트 스크립트는 안 고친다.
- 계약 파괴 여부: 아니오.

## 제약
- **경계를 넓히는 것(a)은 앱 롤로 기계적으로 불가능하다.** `services/core-api/tests/test_operator_designation.py:446-483` 이 그 오라클이다 — 운영자 읽기 스코프(`:460` `operator_read=True`)를 연 상태에서도 타 연구실 `UPDATE`·`DELETE` 는 `rowcount == 0`(`:466-469`)이고 `INSERT` 는 `row-level security` 로 거절된다(`:475-480`). 정리 세션은 앱 롤이다(`conftest.py:62-64` → `app_db_url`, `:48` 주석 「앱 롤(NOBYPASSRLS·비소유자)」). 넓히려면 `admin_db_url`(`conftest.py:51-53`)로 갈아타야 하고, 그 순간 정리 경로가 RLS 를 우회해 **시험이 증명하려는 경계 자체를 무효화**한다.
- **파일마다 DB(d)는 비용이 맞지 않는다.** 대상이 113 파일이고 슬롯은 호스트 전역으로 제한된다. `gates/tools/service-tests.sh:69` 의 `JOBS` 는 1~32 를 받지만(`:71`) DB 프로비저닝은 그 수를 따라가지 않는다.
- 가드는 `d8_activity` 를 셀 수 없다. `conftest.py:117` 축자 — 「**`d8_activity` 는 없다** — append-only 트리거가 DELETE 를 거부한다」. 가드의 대상 표는 `_CLEANUP`(`conftest.py:136-171`)과 같은 18개로 둔다.
- 가드가 볼 수 있어야 경계 밖을 잴 수 있는데, 앞 항목대로 앱 롤은 볼 수 없다. **가드 읽기는 운영자 읽기 스코프로 연다** — `test_operator_designation.py:531-533` 과 `:640-641` 의 선례가 정확히 그 용도이고, 그 스코프는 읽기만 열고 쓰기는 열지 않음이 `:446-483` 으로 증명돼 있다. 읽기 전용이므로 가드가 새 누출을 만들지 않는다.
- 흔들림을 눈금으로 덮지 않는다. `gates/run.sh:761` 축자 규율 — 「상한 연장·재시도·병렬도 축소·건너뛰기로 green 을 만들지 않는다.」 `-j` 를 낮춰 green 을 만드는 선택지는 이 문장에 걸린다.
- 이번 회차에 게이트·pytest 실행이 금지돼 있어 이 intent 의 모든 판정은 정적 독해다. 실측은 레인 몫이다.

## 설계트리 (grill-me 결과)
- Q1 「경계 밖」이 정확히 무엇인가 → A `_cleanup_scope`(`conftest.py:292-298`)가 심는 `LAB_A` RLS 경계에서 `SELECT` 가 못 보는 행. 스냅숏(`:328-329`)과 DELETE(`:344`)가 같은 세션을 쓰므로 「안 보인다 = 안 지워진다」가 항등이다.
- Q2 누가 쓰는가 → A 확정 3건은 `test_admin_actor_visibility.py:38`(파라미터라이즈 2회)·`:62`(1회). 셋 다 `LAB_B` 데이터셋이고 회수 코드가 없다. 관측된 잔존물 3건과 정확히 일치한다.
- Q3 왜 `test_pool_no_leak.py` 만 터지나 → A 그 파일만 B 연구실을 **절대 집합**으로 재기 때문이다(`:48`·`:99`·`:106`). 다른 파일은 A 연구실만 세고, A 는 정리가 닿는다. 그리고 그 파일 자신은 `conftest.py:440-442` 때문에 정리 대상도 아니다.
- Q4 왜 2건이고 3건이 아닌가 → A 가운데 시험(`:53`)은 A 연구실만 `count == 2` 로 잰다(`:74`). B 를 재는 것은 `:26`·`:82` 둘뿐이다. 보고된 red 건수가 이 계산을 검증한다.
- Q5 (a) 경계 확대인가 → A 아니다. 앱 롤로는 타 연구실 DELETE 가 0 행이다(`test_operator_designation.py:466-469`). 관리자 롤로 바꾸면 정리 경로가 RLS 를 우회해 경계 증명이 무효가 된다.
- Q6 (d) 파일별 DB 인가 → A 아니다. 113 파일 × DB 는 호스트 슬롯을 넘는다. 원인이 아니라 증상을 격리하는 값비싼 방법이다.
- Q7 (c) 개별 시험 수정만인가 → A 부족하다. 3건을 고쳐도 **다음에 쓰는 사람을 막는 것이 없다**. `test_project_name_duplicate.py:69-70` 의 주석이 이미 규율을 적어 뒀는데도 `test_admin_actor_visibility.py` 가 어겼다. 주석은 게이트가 아니다.
- Q8 그러면 (b) 가드 fixture 인가 → A **그렇다. 권고안은 (b) ＋ (c) 다.** (b) 가 기전을 끊고 (c) 가 현재 red 를 끈다. (b) 단독이면 3건이 즉시 red 로 바뀌므로 둘을 같은 PR 에 넣는다.
- Q9 (b) 가 왜 매력적인가 → A **조용한 누출을 이름 있는 실패로 바꾼다.** `#55` 가 게이트 요약에 적용한 원리와 같다 — `#55` 는 실패 시험 이름이 요약에서 사라지는 것을 고쳤고(`dev-package/intent/2026-09-17-issue-55-frontend-test-failure-naming.md` 문제 1·2항), 여기서는 누출의 **원인 시험**이 이름을 남기게 한다. 지금은 원인이 `test_admin_actor_visibility.py` 인데 red 는 `test_pool_no_leak.py` 에 뜬다. 진단이 매번 처음부터 시작되는 이유가 이것이다.
- Q10 가드의 구체 형태는 → A `conftest.py:425-460` 의 autouse 훅 뒤에 붙는 두 번째 autouse fixture. 시험 시작 전·종료 후로 **운영자 읽기 스코프**에서 `_CLEANUP` 18표의 기본키 집합을 뜨고(기존 `snapshot_test_rows`·`_key_exprs` 재사용 · `conftest.py:301-333`), 차집합에서 `_cleanup_scope` 로도 보이던 키를 뺀 나머지가 비어 있지 않으면 표·키를 적어 `pytest.fail` 한다.
- Q11 가드를 어디에 거나 → A 전 시험. `:440-442` 의 조건을 그대로 쓰면 `test_pool_no_leak.py` 가 또 빠진다. 다만 전 시험에 걸면 회차당 스냅숏 질의가 두 배가 된다 — 실측이 필요하다(미해결 질문).
- Q12 수집계수 불일치는 → A 재현 0회. 기전을 지어내지 않고 「미재현」으로 남긴다.

## 미해결 질문
- 나머지 8건의 red 는 누가 만드는가. 확인한 잔존 생산자는 B 연구실 데이터셋 3건뿐이고, 그것으로 설명되는 것은 `test_pool_no_leak` 2건이다. 나머지 9건(`test_cross_tenant` 3 · `test_dashboard` 1 · `test_grid_convenience` 1 · `test_live_endpoints` 2 · `test_operator_designation` 1 · `test_search_execution` 1)이 같은 기전인지 다른 기전인지 정적 독해로 가르지 못했다. 레인이 열어야 할 자리 — `services/core-api/tests/test_cross_tenant.py:104-111`(B 연구실 절대 0 개수 오라클 7줄) · `services/core-api/tests/test_search_execution.py:83-84`(`ids == [DS_B1]`) · `:154-155` · `:178-180` · `services/core-api/tests/test_grid_convenience.py:252-254`(`all(item["datasetId"] == DS_B1 ...)`) · `services/core-api/tests/test_dashboard.py:157-172`(`TOKEN_B` 로 세는 대시보드 3종) · `services/core-api/tests/test_live_endpoints.py:112`·`:126-128`(B 목록 절대 집합). **이 일곱 자리 전부가 B 연구실을 절대값으로 재므로 같은 기전일 가능성이 높으나, 직렬 단일 DB 회차에서도 11건이 red 였다는 사실과는 아직 조립되지 않았다** — 직렬이면 누출 순서가 고정이므로 「3회 중 1회」가 아니라 항상 red 여야 한다. 그 차이를 설명하기 전에는 원인 동일성을 주장하지 않는다.
- `test_operator_designation.py` 의 red 1건이 어느 시험인지 미확인. 후보는 `:575-593`(`_download_rows` 절대 증분 오라클, `:586`·`:592`)과 `:630-681`(`_lab_b_state` 대조). 레인은 `services/core-api/tests/test_operator_designation.py:575` 부터 연다.
- 가드를 전 시험에 걸 때의 회차 시간 증가폭. `conftest.py:328-329` 의 UNION 은 18표 전수 스캔이고, 이것이 시험마다 2회 더 돈다. 미측정.
- 운영자 읽기 스코프가 `_CLEANUP` 18표 **전부**에 대해 타 연구실 행을 보여 주는지 미확인. `test_operator_designation.py:461-463` 은 `d3_dataset` 한 표에 대해서만 증명한다. `0029` 마이그레이션이 표마다 다른 읽기 정책을 걸었을 수 있다 — `services/core-api/tests/test_operator_designation.py:518-523` 주석이 `d8_download` 를 그 예로 든다. 레인은 마이그레이션 `0029` 를 열어 표별 정책을 대조한다.
- 수집 1221 vs 1222 를 무엇이 결정지을 것인가 → 이슈 보고자의 회차 로그(pytest `collected N items` 줄과 그 회차의 트리 SHA). 그것 없이는 현 트리 1383 과 대조할 기준이 없다. 로그가 없으면 미재현으로 종결한다.

## 범위 밖 (명시 제외)
- `_cleanup_scope` 를 관리자 롤·운영자 스코프로 갈아 끼우는 것(선택지 a). 경계 증명 자체를 무효화한다.
- 파일별·worker 별 DB 분리(선택지 d). 별도 검토 대상이며 이번 PR 에 넣지 않는다.
- 수집계수 불일치(1221 vs 1222)의 기전 수정. 미재현이다.
- `#47` 이 이미 처리한 계정 표 정리. 이 intent 는 그 위에 남은 잔여 원인만 다룬다.
- 게이트 스크립트(`gates/tools/service-tests.sh`) 변경, `-j` 기본값 조정, 재시도·플레이크 재실행 도입.
- 제품 코드·마이그레이션·계약 변경.
- 다른 이슈 구현, 커밋·push·PR 게시·배포·이슈 댓글·종결.

## 확인
- Ted 확인 문장: 대기 중.
- 승인 필요 지점:
  - ⑴ 고침 형태를 (b) 가드 fixture ＋ (c) 3건 자기 회수로 확정할지. 권고안이다.
  - ⑵ 가드를 **전 시험**에 걸지, `conftest.py:440-442` 의 기존 조건(`p2_client`·`sql`·`live_client`)만 걸지. 권고는 전 시험 — 후자는 `test_pool_no_leak.py` 를 또 빠뜨린다.
  - ⑶ 가드 읽기를 운영자 읽기 스코프로 여는 것을 허용할지. 읽기 전용이며 선례는 `test_operator_designation.py:531-533` 이다.
  - ⑷ 미해결 질문의 나머지 9건 red 조사를 이 PR 에 포함할지, 후속 레인으로 분리할지.
  - ⑸ 회차 시간 증가폭 실측을 위한 `COLAB_SERVICE_TEST_JOBS=12` 전수 회차 3회를 레인에 배정할지.
  - ⑹ 수집계수 불일치를 미재현으로 종결할지, 보고자 로그를 받을 때까지 열어 둘지.
- 재개봉 금지: 해당 없음(미승인).

## 참조
- 이슈: https://github.com/CognileapAI/colab-v2/issues/47
- 선행 intent: `dev-package/intent/2026-09-17-issue-47-service-tests-db-isolation.md`
- 원리 선례: `dev-package/intent/2026-09-17-issue-55-frontend-test-failure-naming.md` (조용한 실패를 이름 있는 실패로)
- 하네스: `services/core-api/tests/conftest.py:136-171`·`:292-298`·`:301-316`·`:319-333`·`:336-347`·`:425-460`
- 누출 생산자: `services/core-api/tests/test_admin_actor_visibility.py:12-21`·`:24`·`:38`·`:62`
- 피해 시험: `services/core-api/tests/test_pool_no_leak.py:26`·`:48`·`:82`·`:99`·`:106`
- 기존 규율 선례: `services/core-api/tests/test_project_name_duplicate.py:69-70`·`:100-118`, `services/core-api/tests/test_operator_designation.py:539-572`
- 경계 오라클: `services/core-api/tests/test_operator_designation.py:446-483`·`:518-536`
- 게이트: `gates/tools/service-tests.sh:36`·`:69`·`:71`, `gates/run.sh:761`
- spec: 미작성. Ted 승인 뒤 합성한다.
- 결정: 신규 legacy 결정번호 발급 없음.
