"""접수한 바이트가 어디에 놓이는가 — **세 단위가 공유하는 유일한 규약**.

⚠ auto-generated — 손으로 고치지 않는다 (CLAUDE.md 규칙 7).
정본 = `contracts/storage/layout.json` · 생성 = `contracts/codegen/gen_storage_layout.py`
`core-api`(쓴다) · `pipeline-worker`(연다) · `viz-render`(그린다)가 **같은 바이트**를 받는다.

배치
  · 본체 — `{root}/uploads/{targetId}/{fileId}`
  · 기준 격자 파일 — `{root}/uploads/{targetId}/grid/{fileName}`

**왜 격자만 이름을 보존하는가**
  격자만 이름을 보존한다. ① 종류가 배치로 읽혀야 한다 — 격자를 여는 마지막 소비자인 D7 에는 원장이 없고(불변규칙 1 로 D5 표를 못 본다) 배치 말고 종류를 알 길이 없다. ② 이름이 자료다 — 짝짓기(§5.4.1 가-2·가-3)와 축 판별 사다리 ④가 파일명을 읽고, 격자 판독은 확장자(.npy/.nc)로 갈린다. ULID 로 덮으면 그 정보가 사라지고 그 실패는 에러가 아니라 「격자 없음」으로 위장한다. ③ 축(위도/경도)은 배치에 넣지 않는다 — 축은 워커가 나중에 정하고 원장 행이 기록한다(〈79〉-㈎). 배치가 축을 담으면 그 판정 전에는 자리를 못 정한다. ④ 데이터셋당 0~2건(〈58〉)이 한 디렉터리에 나란히 있어야 짝짓기가 성립한다.
"""
from __future__ import annotations

from pathlib import Path, PurePosixPath

#: 접수분이 사는 한 층. 저장소 루트 바로 아래에 이 이름으로 모인다.
UPLOADS_PREFIX = 'uploads'

#: 기준 격자 파일이 사는 하위 디렉터리 이름.
GRID_DIRNAME = 'grid'

#: 파일 종류(`common.json#FileKind`) → 저장 키 템플릿. **여기가 배치의 정본이다.**
KEY_TEMPLATES = {
    '본체': '{uploadsPrefix}/{targetId}/{fileId}',
    '기준 격자 파일': '{uploadsPrefix}/{targetId}/{gridDirname}/{fileName}',
}

BODY_KIND = '본체'
GRID_KIND = '기준 격자 파일'


class UnsafeFileName(ValueError):
    """이름을 배치에 쓰는 것은 격자뿐이라, 그 이름은 **반드시 한 조각**이어야 한다."""


def safe_file_name(file_name: str) -> str:
    """경로가 아니라 **이름 한 조각**만 남긴다.

    `fileId` 는 ULID 라 경로 탈출이 성립하지 않지만 격자의 `fileName` 은 사람이 준 값이다.
    윈도 구분자까지 접은 뒤 마지막 조각만 취하고, 남는 것이 없거나 `.`·`..` 면 거절한다 —
    **조용히 고쳐 쓰지 않는다.** 고쳐 쓰면 사용자가 올린 이름과 원장이 적은 이름이 갈린다.
    """
    candidate = PurePosixPath(str(file_name).replace("\\", "/")).name.strip()
    if not candidate or candidate in (".", ".."):
        raise UnsafeFileName(f"저장 배치에 쓸 수 없는 파일 이름이다: {file_name!r}")
    return candidate


def is_grid(kind: str) -> bool:
    return kind == GRID_KIND


def storage_key(target_id: str, *, file_id: str, kind: str,
                file_name: str | None = None) -> str:
    """저장 키 — **키가 곧 경로다.** 돌려주는 것은 저장소 루트 기준 상대 POSIX 키다."""
    template = KEY_TEMPLATES.get(kind)
    if template is None:
        raise ValueError(f"모르는 파일 종류다: {kind!r} — 배치를 지어내지 않는다")
    name = "" if file_name is None else safe_file_name(file_name)
    if is_grid(kind) and not name:
        raise ValueError("기준 격자 파일은 이름이 있어야 자리가 정해진다 (짝짓기·확장자)")
    return template.format(uploadsPrefix=UPLOADS_PREFIX, gridDirname=GRID_DIRNAME,
                           targetId=target_id, fileId=file_id, fileName=name)


def storage_path(root, target_id: str, *, file_id: str, kind: str,
                 file_name: str | None = None) -> Path:
    return Path(root) / storage_key(target_id, file_id=file_id, kind=kind,
                                    file_name=file_name)


def uploads_root(root) -> Path:
    """저장소 루트 아래 접수분이 모이는 자리. **한 층을 손으로 세지 않는다.**"""
    return Path(root) / UPLOADS_PREFIX


def target_dir(root, target_id: str) -> Path:
    """한 대상(업로드 또는 데이터셋)의 본체 파일들이 놓인 디렉터리."""
    return uploads_root(root) / target_id


def grid_dir(root, target_id: str) -> Path:
    """그 대상의 기준 격자 파일들이 놓인 디렉터리. **존재 여부는 묻지 않는다.**"""
    return target_dir(root, target_id) / GRID_DIRNAME
