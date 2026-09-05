# `BF-12` 원장 등재 초안 — 앱 로그 설정 (`§9 〈N〉` 자리 미정)

> ⚠ **번호를 예약하지 않는다.** 병합 직전 `origin/main` 최대 번호 ＋1 로 재실측해 박는다.
> 이 파일은 `PLAN-SoT §9` 에 들어갈 **초안**이고, 값과 근거만 미리 적어 둔다.

## 〈N〉 `BF-12` 집행 — `colab_viz` 로거의 INFO 가 stdout 으로 나온다 (⑴⑵⑷ 충족 · ⑶ 미충족)

**판정 ＋ 실측 (2026-09-05 · 워크트리 `agent-ac6173ae` · 기준 `main` = `59b1c13` ·
계약 개정 0 · 마이그레이션 0 · infra 0 · staging 접촉 0 · 배포 0).**

**㉮ 무엇을 고쳤나** — `services/viz-render/src/colab_viz/kernel/logging_setup.py`(신규)의
`configure_logging()` 을 `app/main.py:create_app()` **첫 줄**에서 부른다. 설정 자리는
`colab_viz` 로거 **하나**다 — `basicConfig` 로 루트를 갈아엎지 않는다(uvicorn·써드파티의
줄까지 우리 포맷이 되고, 그것이 「두 갈래로 갈리는 길」이다). 포맷은 **uvicorn 계열**
(`INFO:     …` · `levelname` 뒤를 9칸으로 맞추는 것까지 같다) · `propagate=False` ·
처리기에 표식(`_colab_viz_stdout_handler`)을 달아 **멱등**이다(시험이 앱을 수백 번 세운다).

**㉯ RED 선실측** — 새 시험 `services/viz-render/tests/test_app_logging.py` **4건**이
구현 전에 전부 실패했다(축자):

```
FAILED tests/test_app_logging.py::test_앱을_세우면_INFO_가_stdout_으로_나온다 - AssertionError: assert '관측 한 줄' in ''
FAILED tests/test_app_logging.py::test_회수_요약과_트리거_집행_줄이_둘_다_나온다 - AssertionError: 회수 요약이 stdout 에 없다
FAILED tests/test_app_logging.py::test_앱을_두_번_세워도_줄이_겹치지_않는다 - AssertionError: assert 0 == 1
FAILED tests/test_app_logging.py::test_로그에_비밀값이_실리지_않는다 - AssertionError: assert '지도 타일 회수' in ''
4 failed in 3.96s
```

**GREEN** — 같은 파일 `4 passed in 0.30s`.

⭑ **`caplog` 를 쓰지 않았다.** pytest 는 자기 처리기를 루트에 달아 두므로 `caplog` 로 재면
「로그 설정이 없어도 잡힌다」가 되고, **그것이 이 결함이 시험을 통과했던 이유**다. 시험은
루트를 **미설정 상태로 되돌린 뒤**(처리기 0 · WARNING) 진짜 stdout 을 잡는다.

**㉰ 형제 자리를 같이 잠갔다**(`〈324〉`-㉰) — 회수 요약(`지도 타일 회수 …`)과 트리거 집행
줄(`트리거 집행 N건`)이 **둘 다** stdout 에 난다는 것을 한 시험이 함께 단언한다.
**회수 하나만 고치면 절반만 고친 것이다.**

**㉱ 완료 정의 대조**
- ⑴ **충족** — 앱을 세우면 `colab_viz.*` INFO 가 stdout 으로 난다 · 포맷 uvicorn 동일 계열
- ⑵ **충족** — RED 4건 → GREEN 4건(위 축자)
- ⑶ **미충족** — **staging 배포 뒤 첫 바퀴 요약 1줄 실물.** 이 회차는 staging 접촉 0 이라
  **잴 수 없다.** 해소 조건 = **다음 배포 창**에서 `docker logs colab_v2_staging_viz_render` 에
  `지도 타일 회수 — …` 1줄. ⟹ **`BF-12` 는 `open` 으로 둔다**
- ⑷ **충족** — 시험이 서비스 토큰·타일 서명 비밀 두 값이 로그에 **없음**을 단언한다.
  ⚠ 잰 것은 **회수 요약 경로와 기동 경로**다. 「어떤 줄에도 영영 안 실린다」를 증명한 것이
  아니다 — 무엇을 싣는지는 부르는 쪽의 책임이다 `[미확인]`

**㉲ 환경변수를 새로 만들지 않았다.** 수준은 **INFO 고정**이다. `Settings` 에 수준 자리가
없었고, 새로 내면 `infra/staging/compose.i2.yml` 에 줄을 더해야 하는데(`infra` 는 이 레인의
소유가 아니다) 그 줄이 없으면 **「홈 env 에 무엇을 적어도 영영 꺼짐」**이 된다
(`#20`·`#49`·`COLAB_VIZ_TILE_BRANCH` 와 같은 무늬). 필요해지면 그때 한 자리를 낸다 `[미확인]`.

**㉳ 레포 전체에 로그 설정 선례가 없다** — `services/` 전수 grep 에서 `basicConfig`·
`dictConfig`·`logging.config`·`setLevel` **0건**이다(core-api 도 없다). 따라서 **따라 쓸 무늬가
없었고**, 이 파일이 첫 자리다. 다른 배포 단위(core-api·pipeline-worker·ai-service)도 같은
결손을 안고 있을 가능성이 크지만 **이 회차는 재지 않았다** `[미확인]`.

## 게이트 실측 (`./gates/run.sh all -j 1` · 1회 · 재실행 0)

- **선언 50 · green 34 · red(판정) 1 · red(준비) 15**
- `service-tests-viz-render` **green** — 수집 330 · 실행 330 · skipped 0 · deselected 40 ·
  failed 0(종전 326 ＋ 이번 4)
- `service-tests-selftest` **green**
- ⛔ **red(판정) 1 = `generated-up-to-date`** — 원인은 이 회차의 변경이 아니라 **체크아웃 환경**이다:
  축자 `[fe-core-ts] 재생성 실패 (exit 127): bash: line 1: frontend/node_modules/.bin/openapi-typescript: No such file or directory`.
  이 워크트리에 `frontend/node_modules` 가 없다. 생성물은 **한 글자도 고치지 않았다**
- red(준비) 15 = venv 부재(core-api·ai-service·pipeline-worker) · `node_modules` 부재 ·
  staging DB URL 미선언 · 원천 마운트 부재. **판정이 아니라 준비다**

## 파일

- 신규 `services/viz-render/src/colab_viz/kernel/logging_setup.py`
- 신규 `services/viz-render/tests/test_app_logging.py`
- 수정 `services/viz-render/src/colab_viz/app/main.py` (import 1줄 ＋ `create_app` 첫 줄)
- 수정 `dev-package/work-items.yaml` — `BF-12` **evidence 만**(status 는 `open` 유지)
- ⛔ `infra/` · `Dockerfile` · `contracts/` · 마이그레이션 **0줄**
