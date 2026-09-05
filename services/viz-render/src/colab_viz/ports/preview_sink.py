"""미리보기 산출물을 **서빙되는 자리**로 내보내는 Port (`PLAN-SoT §9 〈342〉-㉮`).

`preview._write` 는 산출물을 `preview_dir` 에 쓰고 `url = {preview_url_base}/{name}` 을 낸다.
로컬·staging 은 그 디렉터리를 nginx 가 그대로 서빙하므로 싱크가 할 일이 없다. dev(AWS) 는
EC2 디스크가 일회용이라 산출물을 데이터 버킷 `previews/{name}` 에 올리고 CloudFront 가
`/previews/*` 를 그 버킷으로 보낸다 — **URL 은 어느 쪽이든 같다**(FE 무변경).
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class PreviewSinkPort(Protocol):
    def publish(self, artifacts: Iterable[Any]) -> None:
        """산출물(`preview.Artifact` — `path` 를 가진 것)을 서빙 자리로 내보낸다. 실패는 예외."""
        ...
