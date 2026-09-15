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

    def index(self, pairs: Iterable[tuple[str, str]]) -> None:
        """`(fileId, contentKey)` 마다 **파일별 역인덱스 표식**을 놓는다 (`DL-2` ⓓ2·ⓓ7).

        산출물 키는 내용 주소라 `fileId` 를 담지 않는다 — 그래서 「이 파일에서 나온 산출물」을
        되묻는 길이 없었고, 데이터셋을 지워도 산출물이 남았다. 자리는
        `storage_layout.preview_index_key` 가 정한다(`previews/` 의 **형제 접두**).

        ⚠ **`publish` 보다 먼저 부른다.** 표식 없이 놓인 산출물은 회수 때 목록 조회로
        찾을 수 없고, 그 실패는 에러가 아니라 「지울 것이 없다」로 위장한다. 실패는 예외이고
        그 예외는 **렌더 실패**다 — 반쪽 상태를 「완료」로 내지 않는다.
        """
        ...

    def remove(self, names: Iterable[str], *,
               index_pairs: Iterable[tuple[str, str]]) -> None:
        """산출물 파일 이름과 그 표식을 **함께** 서빙 자리에서 지운다 (`DL-2` ⓓ2).

        `names` = `preview._write` 가 정한 파일명(`{contentKey}{suffix}`) 그대로다 —
        **이름 한 조각**이어야 하고 경로 구분자가 섞이면 예외다(관대하게 무시하지 않는다).
        `index_pairs` = 함께 걷어낼 표식의 `(fileId, contentKey)`.

        ⚠ 부르는 자리는 **`d7_visualization/reclaim_on_delete.py` 하나**다(음성 시험이 잠근다).
        자동 회수 루프는 이 문을 부르지 않는다 — 그쪽의 S3 삭제 0건은 여전히 참이다.
        """
        ...
