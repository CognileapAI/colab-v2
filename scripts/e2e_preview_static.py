"""E2E 전용 미리보기 정적 서빙 경계."""

from pathlib import PurePosixPath

from fastapi import HTTPException
from fastapi.staticfiles import StaticFiles


class PreviewStaticFiles(StaticFiles):
    """공개 이미지와 같은 볼륨의 렌더 journal/snapshot은 내보내지 않는다."""

    async def get_response(self, path: str, scope):
        if any(part.startswith(".") for part in PurePosixPath(path).parts):
            raise HTTPException(status_code=404)
        return await super().get_response(path, scope)
