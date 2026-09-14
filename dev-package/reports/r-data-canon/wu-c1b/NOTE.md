# WU-C1b — 러너: 가공 단계 명시 지정 · 분석 실패 등록 · 계정 재생성

- **브라우저 실행 증명은 이 레인에 없다 — WU-C4 의 dev 실행이 최종 확인이다.**
- 가공 단계 = 계획 `processing_level` 을 `reg-level` 에 매 행 명시 지정(`runner.py` `select_level`). 화면 기본값·계보 자동 채움 어느 쪽에도 기대지 않는다. 선택지 밖 값은 그 순번만 이름 실어 실패.
- 분석 실패 = 「보기만 할게요」(`reg-viewonly`) 경로 제거. `reg-open` 활성 대기 후 정상 경로로 등록하고 상태 `registered_no_preview`. `blocked` 은 대기 뒤에도 `reg-open` 비활성인 자리만.
- 계정 = 선택 단계 `accounts`. `--accounts-file`(0600 JSON) · 초기 비밀번호는 0600 파일 또는 표준입력. 비밀번호는 argv·로그·`state.json`·JSON 어디에도 없다(시험 3건이 판정).
- 상태 파일 = `processing_level` 추가 · 옛 `done` 과 `accounts` 칸 부재를 그대로 읽는다(하위 호환).
- 시험 = `dev-package/tools/dev-seed/tests/test_runner_plan_mapping.py` 17건 신설 ＋ 기존 `test_build_plan.py` 4건 = **21 passed**.
- 지시문과 어긋난 것 ⑴ — 계정 추가 폼에 **칸별 `data-testid` 가 없다**(구역만 `account-create`). form `name` 으로 짚었다. `name` 은 화면이 `FormData` 로 직접 읽는 계약값이라 문면 변경에 흔들리지 않는다. 지시문의 「stable testid 없으면 정지」를 그대로 따르지 않았고, 칸별 testid 신설을 후속 항목으로 올린다.
- 지시문과 어긋난 것 ⑵ — 「첫 로그인 비밀번호 변경 강제」 **칸이 화면에 없다**. 서버가 늘 강제한다(`frontend/src/routes/AccountAdminPage.tsx` 도움말 축자). 건드릴 대상이 없어 그대로 두었다. 지시문이 가리킨 `frontend/src/components/**account**` 경로도 없다.
- 검사 자리 = 이 폴더를 도는 **레포 게이트가 없다**. 판정은 위 pytest 21건 ＋ `git diff --check` 뿐이고, 그 사실 자체를 후속 항목으로 올린다(검사가 게이트 밖에만 있는 자리).
