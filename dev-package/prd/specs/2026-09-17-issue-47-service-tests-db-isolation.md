# Spec: 되돌릴 표에 계정 계열을 올리고 손수 purge 를 배선으로 흡수한다 (#47)
출처 intent: `dev-package/intent/2026-09-17-issue-47-service-tests-db-isolation.md` (승인 2026-09-17 · `## 승인 (2026-09-17)`·`## advisor 검토 결과` 가 구속력이다)

## 문제 진술
- 매 시험 되돌리기가 훑는 표 목록 `_CLEANUP`(`services/core-api/tests/conftest.py:136-171`, 21개)에 **계정 계열이 없다** — `d1_account`·`d2_member_role`·`d2_permission_switch` 셋 다 없다.
- 그래서 계정을 만드는 시험은 되돌리기를 손으로 적는다. `services/core-api/tests/test_lab_members.py:245-251` `_purge_member` 가 `d2_permission_switch` → `d2_member_role` → `d1_account` 순으로 직접 지운다.
- 그 손수 되돌리기에 **누수창이 있다.** `test_lab_members.py:260-261`의 `_make_inactive_member` 두 호출이 `try:`(`:262`) **밖**이다. 두 번째 호출 안의 `assert made.status_code == 201`(`:236`) 또는 `assert turned.status_code == 200`(`:241`)이 깨지면 `finally`(`:273-275`)가 아예 서지 않고 첫 계정이 A 연구실에 영구히 남는다.
- 남은 계정 행은 곧바로 절대 계수 오라클을 틀리게 한다. `memberCount` 의 원천은 `services/core-api/src/colab_core/domains/d1_identity.py:39` = `SELECT count(*) FROM d1_account WHERE lab_id = current_lab_id()` 한 줄이다. `services/core-api/tests/test_live_endpoints.py:57` `a["memberCount"] == 2` 와 `services/core-api/tests/test_lab_members.py:58` `set(rows) == {ACC_A_PROF, ACC_A_RES}` 가 그 값을 그대로 센다.
- `--dist loadfile`(`gates/tools/service-tests.sh:92-94`)은 파일을 worker 에 고정할 뿐 파일마다 DB 를 갈지 않는다. worker 수가 바뀌면 오염원 파일과 피해자 파일의 동거 여부가 바뀐다 — worker 4 green · worker 12 red 의 차이는 부하가 아니라 배분이다.

## 해법 개요
- `_CLEANUP`(`conftest.py:136-171`) 끝에 `d2_permission_switch`·`d2_member_role`·`d1_account` 를 **이 순서로** 올린다. 되돌리기가 계정 계열을 배선으로 줍는다.
- `_purge_member`(`test_lab_members.py:245-251`)를 지우고, 그것을 부르던 세 시험(`:254`·`:278`·`:293`)의 `try/finally` 를 없앤다. 손수 되돌리기가 사라지면 누수창도 함께 사라진다 — 닫는 것이 아니라 없앤다.
- 되돌리기 픽스처 `_rollback_p2_rows`(`conftest.py:425-460`)의 대상 판정(`:440`)은 **손대지 않는다.** 세 시험은 이미 `p2_client` 를 받으므로 되돌리기가 이미 돈다.
- 절대 계수 오라클은 이번에 좁히지 않는다. 이 수정 뒤 전수에서 남는 것만 다음 판단 대상이다.

## 사용자 스토리
1. 개발자로서 계정을 만드는 시험이 끝나면 그 계정 행이 사라지길 원한다, 다음 파일의 `memberCount` 오라클이 시험 순서에 흔들리면 안 되기 때문에.
2. 개발자로서 계정 생성이 중간에 실패해도 이미 만든 계정이 지워지길 원한다, 실패 한 건이 뒤따르는 파일들을 연쇄로 깨뜨리면 실패 집합이 실행마다 달라지기 때문에.
3. 개발자로서 되돌리기가 시험의 자발적 선언이 아니라 배선의 성질이길 원한다, 손으로 적는 순간 새 시험이 조용히 빠지기 때문에.
4. 개발자로서 시드 계정 3건이 되돌리기에 지워지지 않길 원한다, 시드가 사라지면 모든 오라클이 함께 사라지기 때문에.
5. 개발자로서 되돌리기가 FK 로 막혀 트랜잭션 전체가 무효가 되지 않길 원한다, 그러면 삭제도 `_RESTORE` 도 함께 사라져 지금보다 나빠지기 때문에.
6. 개발자로서 `service-tests-core-api` 가 내부 worker 4 와 12 에서 같은 판정을 내길 원한다, 판정이 병렬도에 걸리면 게이트가 사실을 말하지 않기 때문에.
7. 개발자로서 이 수정 뒤에도 남는 실패가 무엇인지 이름으로 남길 원한다, 먼저 오라클을 좁히면 무엇이 고쳐졌는지 알 수 없기 때문에.

## 구현 결정
- **이 변경은 `gates/run.sh` 의 `summary_gate_row()` 와 `gates/tools/gate_summary_json.py` 를 건드리지 않는다.** 그 둘은 형제 레인 #55·#56 의 것이고, 만지면 충돌한다. 이번 PR 의 diff 에 `gates/` 아래 파일이 한 건도 없는 것이 정상이다.
- 표 추가 (`conftest.py:136-171`): 튜플 **맨 끝**, 현재 마지막 원소 `"d3_dataset"`(`:170`) 뒤에 세 줄을 더한다. 순서는 `"d2_permission_switch"` → `"d2_member_role"` → `"d1_account"`.
- 삭제 순서의 근거: `purge_test_rows`(`conftest.py:336-347`)는 `for table in _CLEANUP` 로 **선언 순서대로** DELETE 한다. FK 순서는 이 목록이 쥔다(`:337` 축자). `d1_account` 를 참조하는 표 중 이미 목록에 있는 것은 `d2_dataset_access_grant`·`d2_dataset_access_request`·`d2_verification_request`·`d3_dataset`·`d3_search_evidence`·`d3_lab_default_grid`·`d4_lineage_edge`·`d4_lineage_unknown`·`d5_upload`·`d5_pipeline_event` 이고 전부 `d3_dataset`(`:170`) 이전에 있다. 그러므로 **`d1_account` 는 튜플의 마지막 원소여야 한다.** `d2_permission_switch`·`d2_member_role` 는 아무도 참조하지 않으므로 `d1_account` 직전이면 충분하다(`db/platform/schema.sql:185`·`:196` — 둘 다 `REFERENCES d1_account(id)`, CASCADE 없음).
- `d2_permission_switch` 를 함께 올리는 근거: 승인 문면은 두 표를 적었으나 같은 문단이 「손수 purge 를 배선으로 흡수한다」를 함께 못 박았고, `_purge_member`(`test_lab_members.py:246-247`)가 실제로 지우는 것은 **세 표**다. 이 표를 빼면 권한 저장 경로(`services/core-api/src/colab_core/domains/d2_access.py:106-112` `_UPSERT_SWITCH`)를 탄 계정의 `d1_account` DELETE 가 FK 로 막히고, 막히는 순간 되돌리기 **트랜잭션 전체**가 무효가 된다(`conftest.py:433-436` 축자 — 2026-09-13 에 실제로 겪은 형태다). 표 2개가 아니라 3개인 것은 범위 확대가 아니라 흡수의 최소 형태다.
- 기본키 스냅숏은 **자동으로 따라온다.** `_PK_SQL`(`conftest.py:175-184`)이 `c.relname IN (...)` 를 `_CLEANUP` 에서 만들고, `_key_exprs`(`:301-316`)가 DB 에서 PK 열을 읽는다. `d1_account.id`·`d2_member_role.account_id` 는 단일 키, `d2_permission_switch` 는 `(account_id, switch)` 복합키이고 `:315`가 복합키를 한 값으로 접는다. 표 이름을 오타내면 `:309-313`이 「기본키를 못 읽은 표가 있다」로 즉시 멈춘다 — 조용히 통과하지 않는다.
- `snapshot_test_rows`(`conftest.py:319-333`)의 UNION 가지가 21개에서 24개로 는다. 시드 계정 3건(`services/core-api/tests/fixtures/seed.sql:22-25`)·역할 3건(`:27-30`)·스위치 4건(`:32-`)은 스냅숏에 들어가므로 DELETE 에서 빠진다.
- `_RESTORE`(`conftest.py:189-289`)에 **문장을 더하지 않는다.** 이번 변경이 잠그는 것은 「시험이 만든 계정 행의 삭제」뿐이다. 시드 계정 행의 값 변경(`test_admin_role_scope.py:20-22`, `test_operator_transition.py:69-70`·`:134`·`:154`)은 각 시험이 postgres 슈퍼유저 픽스처로 스스로 되돌리고 있고, 그 책임을 이번에 옮기지 않는다.
- 경계와 권한: 되돌리기는 A 연구실 교수 경계에서 돈다(`conftest.py:292-298` `_cleanup_scope`). `d1_account`·`d2_member_role`·`d2_permission_switch` 셋 다 `lab_boundary` RLS 가 걸려 있어(`db/platform/schema.sql:1372-1385`) **A 연구실 밖 행은 스냅숏에도 DELETE 에도 안 걸린다.** 백오피스 시험이 만드는 계정은 LAB_C(`test_operator_designation.py:28`·`:79`) 또는 무소속(`lab_id IS NULL`)이라 이 경계 밖이다 — 이번 변경의 사정권이 아니다.
- DELETE 권한은 앱 롤의 것이고 이미 있다. 시험 세션의 URL 은 `conftest.py:47-49` `app_db_url`(`COLAB_CORE_TEST_DATABASE_URL`)이고 `conftest.py:61-64` `session_factory` 가 그 URL 로만 엔진을 만든다. 되돌리기 픽스처(`:426`)도 `sql` 픽스처(`:394`)도 이 factory 하나를 쓴다. 앱 롤 권한은 `services/core-api/ops/app-role.sql:40` = `GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public`. DELETE 가 없는 것은 **계정 관리자 롤**이며(`services/core-api/ops/account-admin-role.sql:49-52` — `d1_account`·`d2_member_role` 에 SELECT·INSERT 만) 이 롤은 되돌리기 경로에 없다. 실증은 더 강하다 — 현행 `_purge_member`(`test_lab_members.py:250`)가 이미 `sql` 픽스처로 `DELETE FROM d1_account` 를 돌고 green 이다.
- `account_admin.login_credential` 은 `d1_account` 에 `ON DELETE CASCADE` 로 달려 있다(`db/platform/schema.sql:135`). `account_admin.service_operator`(`:156`)·`account_admin.login_session`(`:161`)도 같다. 앱 롤에는 `account_admin` 스키마 권한이 없지만(`:136` `REVOKE ALL ON SCHEMA account_admin FROM PUBLIC`) **참조 무결성 동작은 소유자 권한으로 돈다** — 현행 `_purge_member` 가 green 인 것이 그 증거다. 이 세 표를 `_CLEANUP` 에 올리지 않는다.
- 누수창 제거 (`test_lab_members.py:245-300`): `_purge_member`(`:245-251`) 함수를 지운다. 세 시험에서 `try:`/`finally:` 블록을 없애고 본문을 한 단계 내린다 — `:262`·`:273-275`(2건 purge), `:282`·`:289-290`, `:297`·`:299-300`. `_make_inactive_member` 호출(`:260-261`·`:281`·`:296`)은 그대로 둔다. 되돌리기는 픽스처가 한다.
- 세 시험의 인자에서 `sql` 을 뺀다(`:254`·`:278`·`:293`). 되돌리기 발동 조건은 `conftest.py:440`의 `{"p2_client", "sql", "live_client"}` 교집합이고 **`p2_client` 만으로 이미 참이다.** 린트가 미사용 인자를 문제 삼지 않도록 남기지 않는다. `:440`의 집합 자체는 고치지 않는다.
- `_make_inactive_member`(`:227-242`)의 `assert` 두 줄(`:236`·`:241`)은 그대로 둔다. 생성 실패를 조용히 넘기지 않는 것이 그 줄의 요점이고, 실패해도 이제 픽스처가 줍는다.
- 잔존 위험 — 드러내 둔다: `d1_account` 를 참조하면서 `_CLEANUP` 에 없고 CASCADE 도 아닌 표가 넷 남는다 — `d2_permission_change`(`schema.sql:212-213`, append-only 트리거가 DELETE 거부)·`d2_verified`(`:337`·`:339`)·`d5_upload_transfer`(`:1192`)·`d8_activity`(`:1327`)·`d8_download`(`:1342`). A 연구실 안에서 **새로 만든 계정이 행위자로 남는** 시험이 생기면 그 계정의 DELETE 가 FK 로 막히고 되돌리기 트랜잭션 전체가 무효가 된다. 현행 시험 중 그런 조합은 없다(백오피스 계정은 LAB_C·무소속이고, `test_admin_role_scope.py:148-159`가 만드는 LAB_A 교수 계정은 `isolate_created_accounts`(`:11-24`)가 teardown 에서 LAB_C 로 되돌린다 — autouse 인 `_rollback_p2_rows` 보다 **먼저** 도는 순서다). 이 성질은 실행으로 확인한다(아래 검증 계획 ㈐).
- 제품 코드(`services/core-api/src/**`)·계약·스키마·마이그레이션·시드 무변경. `gates/**` 무변경. `gates/config/parallelism.toml:164`의 `"serial"` 선언과 `COLAB_SERVICE_TEST_JOBS` 기본값(`gates/tools/service-tests.sh:69`)을 고치지 않는다.
- 커밋·PR 단위: **커밋 1개 · 단독 PR 1건.** #55·#56 과 묶지 않는다(승인 intent `## 승인 (2026-09-17)` PR 단위 항목).

## 시험 결정
- 외부 행위 기준 검증 항목 ⑴ 계정을 만드는 시험이 끝난 뒤 A 연구실 계정 수가 **2** 로 돌아온다(시드 `seed.sql:22-25` 기준). ⑵ 생성이 중간에 실패한 경우에도 이미 만든 계정이 남지 않는다. ⑶ 시드 계정 3건·역할 3건·스위치 4건은 되돌리기 뒤에도 그대로 있다. ⑷ 되돌리기가 예외 없이 끝난다(FK 로 막히지 않는다). ⑸ `test_lab_members.py` 세 시험의 단언 내용이 수정 전과 같다.
- red → green 순서: `services/core-api/tests/test_cleanup_purge.py` 에 시험 1건을 **먼저** 더한다 — `sql` 로 A 연구실에 계정 1건＋역할 1건을 넣고, `snapshot_test_rows`/`purge_test_rows`(`conftest.py:319-347`)를 직접 불러 그 두 행이 사라지고 시드 3건이 남음을 센다. 표를 올리기 전에는 계정 행이 남아 red 여야 한다. red 를 실제로 관측한 기록을 남긴 뒤 `_CLEANUP` 을 고쳐 green 으로 간다.
- red → green 순서(누수창): `_purge_member` 를 지우기 **전에** 위 red→green 을 끝낸다. 배선이 서지 않은 상태에서 손수 purge 를 먼저 빼면 그 사이 커밋이 누수를 늘린다.
- green-by-skip 방지: 새 시험은 **양성·음성 쌍**으로 센다 — 되돌리기 전 A 연구실 계정 수가 3(시드 2 ＋ 시험 1), 되돌리기 후 2 임을 둘 다 단언한다. 「0 건이라 통과」 형태를 쓰지 않는다. 시드 3건이 남음을 같은 시험에서 함께 센다.
- 새 시험은 기존 seam 위에 선다 — `test_cleanup_purge.py` 가 이미 `session_factory`·`sql`·`_cleanup_scope`·`snapshot_test_rows`·`purge_test_rows` 를 직접 부르는 자리다(`:17-28`). 새 픽스처·새 도우미·새 목 계층을 만들지 않는다.
- 이번 이슈가 지목한 절대 계수 오라클 4건에 대한 판정(실행 없이 정적으로 가른 것이다):
  - `services/core-api/tests/test_live_endpoints.py:57` `a["memberCount"] == 2 and b["memberCount"] == 1`: **㈏ 만으로 결정적이 된다.** 잔존 `d1_account` 행 → `d1_identity.py:39` 의 `count(*)` → 이 단언으로 이어지는 인과가 한 줄로 이어진다. 좁히기 대상이 아니다.
  - `services/core-api/tests/test_live_endpoints.py:63`·`:65`(`ids == {DS_A1, DS_A2}` · `totalCount == 2`): **판정 보류.** 셈의 원천은 `d3_dataset` 이고 그 표는 이미 `_CLEANUP:170` 에 있다. 계정 누수에서 이 단언으로 가는 경로가 정적으로는 없다. 이 수정 뒤 남으면 좁히기 후보다.
  - `services/core-api/tests/test_scope_kernel.py:46` `count(*) FROM d3_dataset == 2`: **판정 보류 — 이 수정으로 고쳐질 근거가 없다.** 이 파일은 쓰기 0건이고 피해자다. 원인은 `d3_dataset` 을 남긴 다른 파일이며 그 표는 이미 되돌리기 대상이다. 남는 설명은 되돌리기가 돌지 않은 파일(옵트인 — 이번 범위 밖) 또는 되돌리기 트랜잭션 실패다. 좁히기 후보로 올린다. 돌지 않고는 가를 수 없다.
  - `services/core-api/tests/test_dataset_facets.py:45-49`(`f["주제"] == {"강우·강수": 2}` 등): **판정 보류 — 이 수정으로 고쳐질 근거가 없다.** 쓰기 0건 파일이다. 더해서 `Verified` 면이 읽는 `d2_verified` 는 `_CLEANUP` 에 **없다**(`schema.sql:337-339`) — 이번 범위와 무관한 별도 누수원일 수 있다. 좁히기 후보다.
  - `services/core-api/tests/test_access_state_three.py:148-160`(`d2_dataset_access` 전체 불변식): **판정 보류.** `d2_dataset_access`·`d2_dataset_access_grant` 둘 다 이미 `_CLEANUP:140-146` 에 있다. 계정 누수와의 연결이 정적으로 없다. 같은 파일 `:208-211` 의 `mine >= 2` 는 이미 하한 형태라 대상이 아니다.
  - 덧붙임 — `services/core-api/tests/test_lab_members.py:58` `set(rows) == {ACC_A_PROF, ACC_A_RES}` 도 같은 인과의 피해자이고 **㈏ 가 직접 지킨다.** 이슈가 이름을 적지 않았을 뿐이다.
- 좁히기는 이번에 하지 않는다. 승인 문면 = 「절대 계수 오라클 축소는 되돌리기 수정 뒤 남는 것만 대상으로 한다. 지금 좁히지 않는다.」

## 검증 계획
- 해당 서비스 단독 게이트 이름: **`service-tests-core-api` 하나다.** 프런트 게이트·계약 게이트·배포 게이트를 선언하지 않는다(프런트·계약·인프라 무변경).
- 명령: `COLAB_GATE_REPORT_DIR=dev-package/reports/<회차>/<레인> bash gates/run.sh service-tests-core-api` (저장소 루트에서). 배선은 `gates/run.sh:534` → `gates/tools/service-tests.sh core-api "not e2e"`.
- 준비 조건: 이 게이트는 `services/core-api/.venv/bin/python` 을 요구하고 없으면 **준비 실패 78** 이다(`gates/tools/service-tests.sh:65-67`). 레인 워크트리에 venv 를 세운 뒤 돌린다. 준비 실패를 green 으로 세지 않는다.
- ㈎ **단독 게이트가 증명하는 것**: 내부 worker **4** 에서의 판정뿐이다. `COLAB_SERVICE_TEST_JOBS` 도 `COLAB_GATE_INNER_JOBS` 도 없으면 기본값 4 가 선다(`service-tests.sh:69`). 여기서 얻는 것은 ⑴ 새 시험이 green ⑵ `test_lab_members.py` 3건이 green ⑶ 되돌리기가 FK 로 막히지 않음 ⑷ 요약줄의 `failed 0 · errors 0`. **worker 12 의 판정은 여기서 증명되지 않는다.**
- ㈏ **단독 게이트를 worker 12 로 한 번 더 돌린다**: `COLAB_SERVICE_TEST_JOBS=12` 를 붙여 같은 명령을 돈다. 이것이 이 이슈의 축자 증상(worker 4 green · worker 12 red)에 직접 대응하는 최소 재현이고, 호스트 단독 전수 예산을 쓰지 않는다. 여기서 남는 실패 이름이 「좁히기 후보」의 확정 목록이 된다.
- ㈐ **되돌리기 FK 무사고 확인**: ㈎·㈏ 양쪽에서 `_CLEANUP` DELETE 가 예외를 내지 않았음을 확인한다. 나면 pytest 출력에 teardown error 로 뜬다 — `errors` 계수가 0 이 아니면 그것이 신호다. FK 로 막혔다면 되돌리는 것이 아니라 막은 표를 `_CLEANUP` 에 올리거나 그 시험이 계정을 A 연구실 밖에 만들게 고친다. 표를 빼서 green 을 만들지 않는다.
- ㈑ **호스트 단독 전수**(`gates/run.sh all -j 4`)가 필요한 것: 이 게이트와 다른 게이트가 한 판에서 같은 판정을 내는지, 그리고 **수집 1221 ↔ 1222 불일치**의 기전. 전수 예산은 **총 3회**이고 #55 와 공유한다. 이 레인의 몫은 1회로 잡는다.
- ㈒ 수집 1221/1222 는 **이번 범위에서 기전을 발명하지 않는다.** `service-tests.sh:232`의 `tot != selected` 비교는 출처가 다른 두 수를 견준다 — `selected` 는 직렬 `--collect-only`(`:166-167`)의 선택 수, `tot` 는 junit `testsuite/@tests` 합(`:202` 부근)이다. 전수 예산 안에서 재현되면 그 회차의 junit 을 읽어 원인을 적고, 재현되지 않거나 예산이 끝나면 **미증명으로 남기고 별도 이슈로 낸다.** 오라클(`:232`) 자체를 이번에 고치지 않는다 — 게이트가 자기 red 를 무디게 하는 방향이다.
- 3계수(green / red(판정) / red(준비))와 종료코드(0 / 1 / 78)를 그대로 회수한다. 미실행·준비 실패를 성공으로 보고하지 않는다.

## 완료 조건
- [ ] `services/core-api/tests/conftest.py:136-171` 의 `_CLEANUP` 마지막 세 원소가 `"d2_permission_switch"`, `"d2_member_role"`, `"d1_account"` 이고 `"d1_account"` 가 튜플의 끝이다.
- [ ] `conftest.py:440` 의 옵트인 집합과 `_RESTORE`(`:189-289`)가 수정 전과 문자 그대로 같다.
- [ ] `services/core-api/tests/test_lab_members.py` 에 `_purge_member` 정의와 호출이 0건이다(`grep -c _purge_member` == 0).
- [ ] `test_lab_members.py` 의 `test_an_inactive_account_is_marked_and_locked`·`test_saving_a_permission_of_an_inactive_account_is_refused`·`test_an_inactive_account_never_crosses_the_lab_boundary` 세 시험에 `try:`/`finally:` 가 없고 인자는 `p2_client` 하나다. 단언 내용은 수정 전과 같다.
- [ ] `services/core-api/tests/test_cleanup_purge.py` 에 계정 계열 되돌리기를 재는 시험 1건이 늘었고, 그 시험이 되돌리기 전 3 · 후 2 를 **둘 다** 센다.
- [ ] 그 새 시험의 red 를 `_CLEANUP` 수정 전에 실제로 관측한 기록이 남았다(출력 발췌).
- [ ] `COLAB_GATE_REPORT_DIR=… bash gates/run.sh service-tests-core-api` 가 종료코드 0 이고 요약줄이 `failed 0 · errors 0` 이다.
- [ ] 같은 명령을 `COLAB_SERVICE_TEST_JOBS=12` 로 돌린 결과와 그 요약줄이 기록에 남았다. red 면 남은 실패 이름이 전부 나열됐다.
- [ ] 변경 파일이 `services/core-api/tests/conftest.py`·`services/core-api/tests/test_lab_members.py`·`services/core-api/tests/test_cleanup_purge.py` **셋뿐**이다. `git diff --name-only` 에 `gates/` 도 `services/core-api/src/` 도 없다.
- [ ] `gates/run.sh` 의 `summary_gate_row()` 와 `gates/tools/gate_summary_json.py` 가 무변경이다.
- [ ] 절대 계수 오라클을 좁힌 편집이 0건이다(`test_live_endpoints.py`·`test_scope_kernel.py`·`test_dataset_facets.py`·`test_access_state_three.py` 무변경).
- [ ] 수집 계수 불일치를 봤든 못 봤든, 본 그대로 적었고 기전을 지어내지 않았다.

## 정책 대조 (작성 시점 제약)
대조 원본은 `.agents/rules/product.md` §3(불변 규칙 8항)·§5(절대 하지 않는 것)다.
- §3-1 도메인은 자기 테이블 ＋ 공용 커널만 참조: **저촉 없음.** 시험 배선만 바꾸고 도메인 코드 무변경.
- §3-2 AI → 계보 쓰기 경로 없음 / §3-3 AI 마이그레이션 체인 분리 / §3-4 core-api 에 geo import 금지: **저촉 없음.**
- §3-5 모든 조회에 연구실 경계 자동 주입: **준수.** 되돌리기는 `_cleanup_scope`(`conftest.py:292-298`) 경계 안에서만 지운다. 경계를 우회하는 admin 롤로 올리지 않는다.
- §3-6 정규 ID 타입 / §3-7 생성물 손수정: **저촉 없음.**
- §3-8 문서에 절대경로를 적지 않는다: **준수.** 이 spec 의 모든 경로는 저장소 상대다.
- §5 게이트 우회·비활성화: **저촉 없음.** `parallelism.toml:164` serial 선언·`service-tests.sh` 판정부·worker 기본값을 고치지 않는다.
- §5 범위 늘리기: **드러내 둔다.** 승인 문면의 두 표에 `d2_permission_switch` 한 건이 는다. 근거는 같은 문면의 「손수 purge 를 배선으로 흡수한다」와 `_purge_member:246-247` 의 실물이다. 아래 우려 항목 ①에 올린다.
- §5 「나중에」로 남기기: **부분 해당 — 드러내 둔다.** 절대 계수 오라클 4건의 처분과 수집 1221/1222 기전은 승인이 명시로 뒤로 미룬 항목이고, 이 spec 은 그것을 완료로 세지 않는다.
- 계약 동결 해제 필요: **아니오.**
- 결정 로그 대조: 신규 legacy 결정번호를 발급하지 않는다(승인 문면 그대로).
- 용어: `dev-package/DOMAINS.md` 표기(연구실 · 계정 · 되돌리기)를 그대로 쓴다.

### 디자인 제약 확인
**해당 없음.** 화면 변경 0건이다. `frontend/**` 무접촉이며 `frontend-visual`·`agent-browser` 는 선언하지 않는다 — 실제 브라우저로 잴 사용자 동작이 이번 변경에 없다.

## 우려 항목 (판정 필요)
| # | 항목 | ⓐ | ⓑ | 권고 |
|---|---|---|---|---|
| 1 | 승인 문면은 표 **2개**(`d1_account`·`d2_member_role`)를 적었는데 `_purge_member` 가 실제로 지우는 것은 **3개**다(`test_lab_members.py:246-247` `d2_permission_switch` 포함). 2개만 올리면 권한을 저장한 계정의 삭제가 FK 로 막히고 되돌리기 트랜잭션 전체가 죽는다. | 세 표를 함께 올리고 이 spec 에 근거를 적어 드러낸다 | 문면대로 두 표만 올린다 | ⓐ — ⓑ 는 지금보다 나쁜 상태(전체 무효)를 만든다. 흡수 지시의 최소 형태다 |
| 2 | `d1_account` 를 참조하면서 되돌릴 수 없는 표가 남는다 — `d8_activity`·`d2_permission_change` 는 append-only 트리거가 DELETE 를 거부한다. A 연구실 안에서 **새 계정이 행위자로 남는** 시험이 생기면 그날부터 되돌리기가 통째로 죽는다. | 잔존 위험을 spec 에 적고, 게이트 출력의 `errors` 계수로 감시한다. 발생 시 해당 시험이 계정을 A 연구실 밖에 만들게 고친다 | 적지 않고 넘어간다 | ⓐ — 이 경로가 열리는 날 원인을 아무도 못 찾는다 |
| 3 | 이슈가 지목한 실패 4건 중 **1건만** 이 수정과 인과가 이어진다. 나머지 3건은 이미 되돌리기 대상인 표를 센다. 「고쳤다」로 보고하면 남은 red 가 회귀로 읽힌다. | 4건을 항목별로 갈라 적고, 3건은 「이 수정으로 고쳐질 근거 없음 · 좁히기 후보」로 명시한다 | 4건을 한 덩어리로 「이 수정이 고친다」로 적는다 | ⓐ — ⓑ 는 실행 근거 없는 주장이다 |
| 4 | 단독 게이트는 기본 worker **4** 로 돈다. 그 green 은 이 이슈의 증상(worker 12 red)을 반증하지 못한다. | 단독 게이트를 `COLAB_SERVICE_TEST_JOBS=12` 로 한 번 더 돌려 축자 증상 자리에서 판정한다 | worker 4 green 으로 완료를 주장한다 | ⓐ — ⓑ 는 「4 에서 green 이니 됐다」이고 승인 intent Q8 이 금지한 무늬다 |
| 5 | 세 시험에서 `sql` 인자를 빼면 되돌리기 발동 조건(`conftest.py:440`)에서 한 이름이 빠진다. | `p2_client` 만으로 조건이 참임을 확인했으므로 뺀다. `:440` 집합 자체는 고치지 않는다 | `sql` 을 미사용 인자로 남긴다 | ⓐ — 미사용 인자는 다음 사람이 지우고, 지우는 순간 조건을 다시 확인하지 않는다 |
| 6 | 「손수 purge 를 `try:` 안으로 옮기기」와 「손수 purge 를 통째로 없애기」 둘 다 누수창을 닫는다. | 통째로 없앤다 — 배선이 하는 일을 손으로 한 번 더 적지 않는다 | `try:` 안으로 옮겨 이중으로 지운다 | ⓐ — ⓑ 는 배선이 도는지 아닌지를 영원히 못 재게 만든다(손수 purge 가 가려 준다) |

## 범위 밖
- **`conftest.py:440` 의 옵트인 집합 제거(㈎).** 승인이 명시로 기각했다. 근거 세 가지 — ⑴ 진단한 누수의 원인이 아니다(누수 시험 `test_lab_members.py:254` 는 이미 `p2_client`·`sql` 을 받아 되돌리기가 이미 돈다) ⑵ 무조건화하면 DB 를 만지지 않는 시험까지 약 1,221건 전부에 DB 세션 ＋ 21표 PK 스냅숏 ＋ `_RESTORE` 가 붙는다 ⑶ 기준선 77.0초 대비 증가분이 **미측정**이다. 필요하면 별도 이슈로 낸다. 재개봉 금지 대상이다.
- **절대 계수 오라클의 선제적 축소.** 이 수정 뒤 전수에서 **남는 것만** 다음 판단 대상이다. 지금 좁히면 경계 누출 탐지력만 잃고 무엇이 고쳐졌는지 알 수 없다.
- **수집 1221/1222 기전의 확정.** 호스트 단독 전수 `-j 4` 예산(총 3회 · #55 와 공유) 안에서만 본다. 그 안에서 확정되지 않으면 **미증명으로 남기고 별도 이슈**로 낸다. 기전을 지어내지 않는다.
- **`gates/**` 전부.** `run.sh` `summary_gate_row()`·`gate_summary_json.py` 는 #55·#56 레인의 것이다. `service-tests.sh:232` 의 `tot != selected` 비교, `parallelism.toml:164` 의 `serial`, `COLAB_SERVICE_TEST_JOBS` 기본값·상한, `_pg.sh` 의 `COLAB_PG_MAX_CONCURRENT` 전부 무변경.
- **파일당 DB · 매 시험 truncate · 되돌리기의 admin 롤 승격.** 승인이 물린 후보들이다. 마지막 것은 경계 증명 시험(`test_cross_tenant.py`·`test_body_access.py`)이 재는 대상 자체를 무디게 한다.
- **`_RESTORE` 에 계정 계열 복원 문장 추가.** 시드 계정 행의 **값 변경**을 되돌리는 일은 이번 범위가 아니다(현재 각 시험이 스스로 한다).
- `services/core-api/src/**` 제품 코드·계약·DB 스키마·마이그레이션·시드 변경.
- core-api 외 `service-tests-ai-service`·`viz-render`·`pipeline-worker`. 이 셋은 일회용 DB 를 세우지 않는다(`gates/tools/service-tests.sh:95-150` 의 `case` 에 `core-api` 만 있다).
- 다른 이슈 구현, 커밋 push·PR 게시·배포·이슈 댓글·이슈 종결. PR 게시는 사용자가 수행하고 에이전트는 로컬 PR 요약과 실제 검증 근거만 제공한다.

## 산출 계획
- 예상 레인 수: **1 (직렬).** 한 체크아웃의 쓰기 주체는 하나다. `conftest.py` 는 core-api 시험 전체의 공용 배선이라 다른 레인과 겹치면 안 된다.
- 커밋 1개 · PR 1건. #55·#56 과 묶지 않는다.
- 게이트 3계수와 종료코드, worker 4 / worker 12 두 회차의 요약줄, red 선관측 발췌, 남은 실패 이름 목록, 사용자 게시용 로컬 PR 요약을 남긴다.
- 라운드 파일: 신규 발급하지 않는다. 신규 legacy 결정번호도 발급하지 않는다.

## 미확인 (이 spec 작성 중 확인하지 못한 것)
- **게이트와 pytest 를 한 번도 돌리지 않았다.** 이 워크트리에 `services/core-api/.venv` 가 없다. 아래 네 가지는 전부 정적 판단이며 실측이 아니다.
- 되돌리기 비용 증가분. 표 21 → 24 로 스냅숏 UNION 가지와 DELETE 문이 각각 3 늘지만 초 단위 증가분은 재지 않았다. 기준선은 이슈 축자 77.0초(worker 4)다.
- 픽스처 teardown 순서. `isolate_created_accounts`(`test_admin_role_scope.py:11-24`)의 복원이 autouse `_rollback_p2_rows` 보다 먼저 돈다는 판단은 pytest 의 autouse 우선 설치 규칙에서 추론한 것이고 실행으로 확인하지 않았다. 어긋나면 그 파일에서 FK 실패가 난다 — 우려 항목 ②의 감시 대상이다.
- 이슈가 지목한 실패 4건 중 3건의 진짜 원인. 이 수정과의 인과가 없다는 것까지가 정적으로 말할 수 있는 전부다.
- 「worker 12 는 이 호스트의 `ncpu`」는 이슈 수치에서 추론한 값이고 읽어서 확인한 값이 아니다(승인 intent advisor [주의] 항목 그대로).
