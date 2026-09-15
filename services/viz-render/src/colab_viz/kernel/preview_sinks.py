"""미리보기 싱크 두 벌 — 로컬(no-op) · S3 (`ports/preview_sink.py` · `〈342〉-㉮`).

키 = `{prefix}/{파일명}` 이고 파일명은 `preview._write` 가 정한 `{cache_key}{suffix}` 그대로다 —
그래야 `COLAB_VIZ_PREVIEW_URL_BASE=/previews` 의 상대 URL 이 CloudFront 를 거쳐 그 객체에 닿는다.
`Cache-Control` 은 staging nginx `location /previews/` 와 같은 값이다.
"""
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .storage_layout import preview_index_key

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

    def index(self, pairs: Iterable[tuple[str, str]]) -> None:
        """표식은 **S3 목록 조회를 대신하는 장치**다. 로컬은 디렉터리를 그대로 훑으므로
        되묻는 길이 이미 있다 — 자리를 하나 더 만들지 않는다."""
        return None

    def remove(self, names: Iterable[str], *,
               index_pairs: Iterable[tuple[str, str]]) -> None:
        """로컬 파일은 `invalidation.apply()` 가 unlink 한다 — 지우는 문을 늘리지 않는다."""
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

    def index(self, pairs: Iterable[tuple[str, str]]) -> None:
        """파일별 표식을 **0바이트 객체**로 놓는다 — 자리 자체가 사실이라 담을 값이 없다.

        자리는 `storage_layout.preview_index_key` 가 정한다. **싱크 접두(`self.prefix`)를
        타지 않는다** — 표식은 `previews/` 의 형제이지 그 아래가 아니다(그 접두는 flat 이어야
        하고 CloudFront 가 그것만 노출한다). PUT 은 멱등이라 같은 그림을 두 렌더가 동시에
        끝내도 경합이 없다. `Cache-Control` 은 붙이지 않는다 — 바깥에 노출되지 않는다.
        """
        for file_id, content_key in pairs:
            self.client.put_object(preview_index_key(file_id, content_key), b"",
                                   "application/json")

    def remove(self, names: Iterable[str], *,
               index_pairs: Iterable[tuple[str, str]]) -> None:
        """산출물 키와 표식 키를 **한 번의 `delete_objects`** 로 보낸다.

        ⚠ **이름에 경로 구분자가 섞이면 거절한다** — 지울 자리를 모르는 것을 관대하게
        무시하면 그 객체는 영원히 남고, 그 실패는 「지웠다」는 계수 뒤에 숨는다.
        ⚠ **지울 것이 하나도 없으면 호출도 하지 않는다** — 빈 삭제 요청을 보내지 않는다.
        """
        keys: list[str] = []
        for name in names:
            text = str(name)
            if "/" in text or "\\" in text or not text.strip():
                raise ValueError(f"미리보기 산출물의 이름이 아니다: {name!r}")
            keys.append(f"{self.prefix}/{text}")
        keys.extend(preview_index_key(f, k) for f, k in index_pairs)
        if not keys:
            return None
        self.client.delete_objects(keys)


__all__ = ["CACHE_CONTROL", "CONTENT_TYPES", "LocalPreviewSink", "S3PreviewSink"]
