"""바이트를 **어디서 읽는가** — 저장처를 가리는 이음매 하나.

⭑ ⟨신설 2026-09-02 · `ST-1` · Ted 판정 「지금 볼륨을 그대로 쓴다」⟩

**왜 이 파일이 있는가.** 저장처의 형태(볼륨 / 객체 저장소)는 이번 회차에 **볼륨**으로
정해졌다. 그 판정이 뒤집힐 때 고쳐야 하는 자리를 **한 곳으로 못 박기 위해** 이 모듈을
둔다 — 내려받기 라우트는 `FileStore` 말고 아무것도 모른다(경로도 · 루트도 · 볼륨이라는
사실도). 객체 저장소로 바꾸는 일은 **이 파일에 구현 하나를 더하고 `build()` 의 분기를
한 줄 늘리는 것**이고, `routes/catalog.py` 는 한 글자도 바뀌지 않는다.

**두 갈래를 가른다.**
  · `open(key)` — 바이트를 우리가 직접 읽는다 (볼륨).
  · `delivery_location(own_url)` — 바이트가 **다른 곳**에 있으면 그 자리를 URL 로 준다
    (객체 저장소의 presigned URL). 볼륨 구현은 「우리에게 다시 오라」를 돌려준다 —
    계약(`fe-core.yaml downloadDataset`)이 302 ＋ `Location` 을 요구하기 때문이다.

**저장 키는 여기서 짓지 않는다.** 키는 원장(`d3_file.storage_key`)이 들고 있고, 그 배치의
정본은 `contracts/storage/layout.json`(→ `kernel/storage_layout.py`)이다. 규칙을 두 곳에
적지 않는다 — 그것이 `#20` 이 난 자리다.
"""
from __future__ import annotations

import dataclasses
import pathlib
import tempfile
from typing import BinaryIO, Protocol


class FileStore(Protocol):
    #: 저장처의 종류. 로그·시험이 「무엇으로 서 있는가」를 값으로 말할 때 쓴다.
    kind: str

    def exists(self, key: str) -> bool: ...

    def open(self, key: str) -> BinaryIO: ...

    def size(self, key: str) -> int: ...

    def delivery_location(self, *, own_url: str) -> str: ...


#: 볼륨 저장처가 `Location` 에 붙이는 표식. **자기에게 되돌아오는 한 바퀴**를 만든다 —
#: 계약이 302 를 요구하는데 바이트가 우리 손에 있기 때문이다. 표식이 붙은 요청도
#: **접근 판정을 처음부터 다시 한다**(`routes/catalog.py`) — 이 값은 자격증명이 아니다.
DELIVER_MARK = "deliver"


@dataclasses.dataclass(frozen=True)
class VolumeFileStore:
    """접수 볼륨 위의 바이트. 키가 곧 루트 기준 상대 경로다(`_store()` 와 같은 규칙)."""

    root: pathlib.Path
    kind: str = "볼륨"

    def _path(self, key: str) -> pathlib.Path:
        # 키는 원장이 준 값이지만 **경로 탈출을 그대로 믿지 않는다.** 루트 밖으로 나가는
        # 키는 없는 것으로 친다 — 조용히 고쳐 쓰지 않는다.
        root = self.root.resolve()
        candidate = (root / key).resolve()
        if candidate != root and root not in candidate.parents:
            raise FileNotFoundError(key)
        return candidate

    def exists(self, key: str) -> bool:
        try:
            return self._path(key).is_file()
        except (FileNotFoundError, OSError):
            return False

    def open(self, key: str) -> BinaryIO:
        return self._path(key).open("rb")

    def size(self, key: str) -> int:
        return self._path(key).stat().st_size

    def delivery_location(self, *, own_url: str) -> str:
        joiner = "&" if "?" in own_url else "?"
        return f"{own_url}{joiner}{DELIVER_MARK}=1"


def resolve_upload_root(settings, state) -> pathlib.Path:
    """접수한 바이트를 두는 자리. **`routes/ingestion._storage_root` 가 쓰던 규칙 그대로다** —
    쓰는 쪽과 읽는 쪽이 같은 함수를 봐야 자리가 갈리지 않는다(`#20` 의 교훈).

    설정이 없으면 프로세스마다 한 번 만드는 임시 디렉터리를 쓴다 — 바이트를 버리고
    201 을 내리지 않기 위해서다.
    """
    configured = getattr(settings, "upload_storage_dir", None)
    if configured:
        root = pathlib.Path(configured)
    else:
        cached = getattr(state, "upload_storage_fallback", None)
        if cached is None:
            cached = tempfile.mkdtemp(prefix="colab-uploads-")
            state.upload_storage_fallback = cached
        root = pathlib.Path(cached)
    root.mkdir(parents=True, exist_ok=True)
    return root


def build(settings, state) -> FileStore:
    """**저장처를 고르는 유일한 자리.** 객체 저장소가 오면 분기가 여기 한 줄 는다."""
    return VolumeFileStore(root=resolve_upload_root(settings, state))
