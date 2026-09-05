"""앱 로그 한 자리 — **INFO 를 stdout 으로 낸다** (`BF-12` · `PLAN-SoT §9 〈324〉`).

**왜 이 파일이 생겼는가** — `services/viz-render/src` 전수에 `basicConfig`·`dictConfig`·
`setLevel` 이 **0건**이었다. 루트 로거에 처리기가 없으면 `logging.lastResort` 가
**WARNING 이상만** stderr 로 흘리고, uvicorn 의 기본 설정은 `uvicorn.*` 로거만 건드린다.
그래서 `trigger_loop.py` 의 `log.info(result.summary())` 와 「트리거 집행 N건」 줄이
**둘 다** 버려졌고, staging 에서 98분이 지나도 `docker logs` 에 한 줄도 안 나왔다.
**관측 전용의 관측이 안 되는 상태**였고, 그것은 기구의 결손이 아니라 로그의 결손이다.

**세 가지를 지킨다** —
  ⑴ **자리는 `colab_viz` 로거 하나다.** 루트를 건드리지 않는다(`basicConfig` 를 쓰면
     uvicorn·써드파티의 줄까지 우리 포맷으로 갈아엎고, 그것은 두 갈래로 갈리는 길이다)
  ⑵ **멱등이다.** 시험이 앱을 수백 번 세우므로 처리기가 겹치면 줄이 배로 늘어난다 —
     표식 하나를 달고 이미 달린 자리를 다시 달지 않는다
  ⑶ **포맷은 uvicorn 계열이다** — `INFO:     …`. 한 컨테이너의 로그가 두 모양으로
     갈리면 읽는 쪽이 grep 을 두 벌 들고 다녀야 한다

⚠ **환경변수를 새로 만들지 않았다.** 수준은 INFO 고정이다 — 켜는 자리를 새로 내면
  `infra/` 에 줄을 더해야 하고(`infra` 는 이 레인의 소유가 아니다), 그 줄이 없으면
  「홈 env 에 무엇을 적어도 영영 꺼짐」이 된다(`#20`·`#49`·`COLAB_VIZ_TILE_BRANCH` 무늬).
  수준 조절이 필요해지면 그때 `kernel/config.Settings` 의 규칙대로 한 자리를 낸다.
⚠ **비밀은 여기서 거르지 않는다** — 로그에 무엇을 싣는지는 부르는 쪽의 책임이고,
  이 파일은 실린 것을 그대로 낸다. 회수 요약이 비밀을 안 싣는다는 사실은
  `tests/test_app_logging.py` 가 잰다.
"""
from __future__ import annotations

import logging
import sys

#: 우리 로거의 뿌리. 앱·도메인·커널이 전부 `colab_viz.*` 아래에 산다.
LOGGER_NAME = "colab_viz"

#: 처리기에 다는 표식 — **멱등의 근거**다. 이름으로 짐작하지 않고 명시로 표시한다.
_MARK = "_colab_viz_stdout_handler"


class UvicornStyleFormatter(logging.Formatter):
    """`INFO:     메시지` — uvicorn 기본 포맷과 **같은 계열**(`levelprefix` 자리맞춤)."""

    def format(self, record: logging.LogRecord) -> str:
        prefix = f"{record.levelname}:".ljust(9)
        return prefix + super().format(record)


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """`colab_viz` 로거에 stdout 처리기를 **한 번만** 단다.

    돌려주는 것은 그 로거다. 이미 달려 있으면 **수준만 맞추고 그대로 돌려준다** —
    새 처리기를 달지 않는다(줄이 배로 늘어나는 것을 막는다).
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    # **루트로 올려보내지 않는다** — 배포가 루트에 무엇을 달든 우리 줄은 한 번만 난다.
    logger.propagate = False
    for handler in logger.handlers:
        if getattr(handler, _MARK, False):
            handler.setLevel(level)
            # 지금의 stdout 을 가리키게 맞춘다 — 처리기는 만들 때의 스트림 객체를 붙들고
            # 있어서, stdout 이 바뀐 뒤(시험의 캡처 등)에는 **없는 자리로 쓴다.**
            if handler.stream is not sys.stdout:
                handler.setStream(sys.stdout)
            return logger
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(UvicornStyleFormatter("%(message)s"))
    setattr(handler, _MARK, True)
    logger.addHandler(handler)
    return logger
