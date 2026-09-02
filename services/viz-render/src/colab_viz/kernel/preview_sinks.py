"""미리보기 싱크 두 벌 — 로컬(no-op) · S3 (`ports/preview_sink.py` · `〈178〉-㉮`).

키 = `{prefix}/{파일명}` 이고 파일명은 `preview._write` 가 정한 `{cache_key}{suffix}` 그대로다 —
그래야 `COLAB_VIZ_PREVIEW_URL_BASE=/previews` 의 상대 URL 이 CloudFront 를 거쳐 그 객체에 닿는다.
`Cache-Control` 은 staging nginx `location /previews/` 와 같은 값이다.
"""
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

CACHE_CONTROL = "public, max-age=300"
CONTENT_TYPES: dict[str, str] = {
    ".webp": "image/webp",
    ".png": "image/png",
    ".json": "application/json",
    ".pgw": "text/plain",
}


class LocalPreviewSink:
    """`preview_dir` 를 nginx 가 서빙한다 — 할 일이 없다."""

    def publish(self, artifacts: Iterable[Any]) -> None:
        return None


class S3PreviewSink:
    def __init__(self, client: Any, prefix: str = "previews") -> None:
        self.client = client
        self.prefix = prefix.strip("/")

    def publish(self, artifacts: Iterable[Any]) -> None:
        items = list(artifacts)
        # 하나라도 모르는 확장자면 아무것도 올리지 않는다 — 반쪽 미리보기를 서빙 자리에 두지 않는다.
        plan: list[tuple[Path, str]] = []
        for a in items:
            path = Path(a.path)
            ctype = CONTENT_TYPES.get(path.suffix)
            if ctype is None:
                raise ValueError(f"미리보기 산출물의 확장자를 모른다: {path.name}")
            plan.append((path, ctype))
        for path, ctype in plan:
            self.client.put_object(f"{self.prefix}/{path.name}", path.read_bytes(), ctype,
                                   cache_control=CACHE_CONTROL)


__all__ = ["CACHE_CONTROL", "CONTENT_TYPES", "LocalPreviewSink", "S3PreviewSink"]
