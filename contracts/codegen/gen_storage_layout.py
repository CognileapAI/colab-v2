#!/usr/bin/env python3
"""`contracts/storage/layout.json` → 세 단위가 함께 쓰는 저장 배치 모듈.

**같은 규칙이 세 곳에 적혀 있다는 사실 자체가 갈라질 자리다** — 실제로 갈라졌고,
그 대가가 `03-HANDOFF §4 #20`(격자가 렌더러에 영영 안 닿는다)이다. 그래서 규칙을
한 곳(`layout.json`)에만 적고 세 단위에 **같은 바이트**를 생성해 내린다.
드리프트는 `generated-up-to-date` 게이트가 잡는다 — 사람이 지키는 관례가 아니다.

산출물은 **세 파일 모두 바이트 동일**하다. 다르면 그것은 「단위마다 다른 규칙」이고,
이 파일이 막으려는 것이 정확히 그것이다.

사용: python3 contracts/codegen/gen_storage_layout.py <out-path>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "contracts" / "storage" / "layout.json"

TEMPLATE = '''"""접수한 바이트가 어디에 놓이는가 — **세 단위가 공유하는 유일한 규약**.

⚠ auto-generated — 손으로 고치지 않는다 (CLAUDE.md 규칙 7).
정본 = `contracts/storage/layout.json` · 생성 = `contracts/codegen/gen_storage_layout.py`
`core-api`(쓴다) · `pipeline-worker`(연다) · `viz-render`(그린다)가 **같은 바이트**를 받는다.

배치
{layout_doc}

**루트가 둘이다** — 접수분(원본)과 미리보기 산출물은 **다른 저장 루트**에 산다.
{previews_root_doc}

**`targetId` 가 무엇인가**
{target_id_doc}

**왜 격자만 이름을 보존하는가**
{grid_why}

**왜 미리보기 산출물이 규약에 있는가**
{preview_why}
"""
from __future__ import annotations

from pathlib import Path, PurePosixPath

#: 접수분이 사는 한 층. 저장소 루트 바로 아래에 이 이름으로 모인다.
UPLOADS_PREFIX = {uploads_prefix!r}

#: 기준 격자 파일이 사는 하위 디렉터리 이름.
GRID_DIRNAME = {grid_dirname!r}

#: 종류 → 저장 키 템플릿. **여기가 배치의 정본이다.**
#: ⚠ 앞의 둘만 `common.json#FileKind` 이자 `d3_file.kind` CHECK 의 값이다.
#: **미리보기 산출물은 원장에 행이 없다** — 사용자가 올린 파일이 아니라 다시 만들 수 있는
#: 산출물이라 `FileKind` 를 넓히지 않고 CHECK 도 건드리지 않는다(마이그레이션 0).
KEY_TEMPLATES = {key_templates}

BODY_KIND = {body_kind!r}
GRID_KIND = {grid_kind!r}
PREVIEW_KIND = {preview_kind!r}

#: 저장 루트의 이름 — **둘이다.** 실물도 볼륨 둘로 갈려 있고(`uploads`·`previews`),
#: 백업이 둘을 따로 뜬다. 규약이 실물을 따라간다.
UPLOAD_ROOT = {upload_root!r}
PREVIEW_ROOT = {preview_root!r}

#: 종류 → 그 종류가 사는 루트. **원본과 산출물을 가르는 자리**다 —
#: 원본은 사용자 것이고 산출물은 다시 만들 수 있다. 섞이면 백업·복원·삭제가 둘을 못 가른다.
ROOTS = {roots}


class UnsafeFileName(ValueError):
    """이름을 배치에 쓰는 것은 격자뿐이라, 그 이름은 **반드시 한 조각**이어야 한다."""


def safe_file_name(file_name: str) -> str:
    """경로가 아니라 **이름 한 조각**만 남긴다.

    `fileId` 는 ULID 라 경로 탈출이 성립하지 않지만 격자의 `fileName` 은 사람이 준 값이다.
    윈도 구분자까지 접은 뒤 마지막 조각만 취하고, 남는 것이 없거나 `.`·`..` 면 거절한다 —
    **조용히 고쳐 쓰지 않는다.** 고쳐 쓰면 사용자가 올린 이름과 원장이 적은 이름이 갈린다.
    """
    candidate = PurePosixPath(str(file_name).replace("\\\\", "/")).name.strip()
    if not candidate or candidate in (".", ".."):
        raise UnsafeFileName(f"저장 배치에 쓸 수 없는 파일 이름이다: {{file_name!r}}")
    return candidate


def is_grid(kind: str) -> bool:
    return kind == GRID_KIND


def storage_key(target_id: str, *, file_id: str, kind: str,
                file_name: str | None = None) -> str:
    """저장 키 — **키가 곧 경로다.** 돌려주는 것은 저장소 루트 기준 상대 POSIX 키다."""
    template = KEY_TEMPLATES.get(kind)
    if template is None:
        raise ValueError(f"모르는 파일 종류다: {{kind!r}} — 배치를 지어내지 않는다")
    if ROOTS[kind] != UPLOAD_ROOT:
        # **루트가 다른 것을 이 함수로 부르지 않는다.** 조용히 접수분 루트 아래로
        # 새어 들어가면 백업·복원·삭제가 원본과 산출물을 못 가른다 — `preview_key()` 를 쓴다.
        raise ValueError(
            f"{{kind!r}} 은 접수분 루트에 놓이지 않는다 (루트 {{ROOTS[kind]!r}}) — preview_key() 를 쓴다")
    name = "" if file_name is None else safe_file_name(file_name)
    if is_grid(kind) and not name:
        raise ValueError("기준 격자 파일은 이름이 있어야 자리가 정해진다 (짝짓기·확장자)")
    return template.format(uploadsPrefix=UPLOADS_PREFIX, gridDirname=GRID_DIRNAME,
                           targetId=target_id, fileId=file_id, fileName=name)


def preview_key(content_key: str, extension: str) -> str:
    """미리보기 산출물 하나의 자리. **내용 주소**라 같은 입력이면 같은 키다.

    `content_key` 는 렌더 파라미터 전부를 접은 다이제스트다(viz-render
    `d7_visualization/cache.py` `render_cache_key`). 그래서 **이미 구운 것이 있으면
    같은 키가 나와 찾아 쓰고**, 입력이 하나라도 바뀌면 키가 갈려 무효화가 저절로 된다.
    여기서 다이제스트를 만들지 않는다 — 만드는 자리는 하나여야 한다.

    돌려주는 것은 **미리보기 루트 기준** 상대 키다. 접수분 루트가 아니다.
    """
    key = str(content_key).strip()
    if not key or "/" in key or "\\\\" in key or key in (".", ".."):
        raise ValueError(f"미리보기 산출물의 내용 키로 쓸 수 없다: {{content_key!r}}")
    ext = str(extension)
    if ext and not ext.startswith("."):
        raise ValueError(f"확장자는 점으로 시작한다: {{extension!r}}")
    if "/" in ext:
        raise ValueError(f"확장자에 경로 구분자를 넣지 않는다: {{extension!r}}")
    return KEY_TEMPLATES[PREVIEW_KIND].format(contentKey=key, extension=ext)


def preview_path(previews_root, content_key: str, extension: str) -> Path:
    """`previews_root` 는 **접수분 루트가 아니다** — 배포가 주는 별도 볼륨의 자리다."""
    return Path(previews_root) / preview_key(content_key, extension)


def storage_path(root, target_id: str, *, file_id: str, kind: str,
                 file_name: str | None = None) -> Path:
    return Path(root) / storage_key(target_id, file_id=file_id, kind=kind,
                                    file_name=file_name)


def uploads_root(root) -> Path:
    """저장소 루트 아래 접수분이 모이는 자리. **한 층을 손으로 세지 않는다.**"""
    return Path(root) / UPLOADS_PREFIX


def target_dir(root, target_id: str) -> Path:
    """한 대상의 본체 파일들이 놓인 디렉터리.

    `target_id` 는 **등록 전 `uploadId` · 등록 뒤 `datasetId`** 다 (모듈 서두 참조).
    """
    return uploads_root(root) / target_id


def grid_dir(root, target_id: str) -> Path:
    """그 대상의 기준 격자 파일들이 놓인 디렉터리. **존재 여부는 묻지 않는다.**"""
    return target_dir(root, target_id) / GRID_DIRNAME
'''


def render() -> str:
    spec = json.loads(SOURCE.read_text(encoding="utf-8"))
    keys: dict[str, str] = spec["keys"]
    roots: dict[str, str] = spec["roots"]
    upload_root = roots["본체"]
    preview_root = next(r for r in roots.values() if r != upload_root)
    upload_kinds = [k for k in keys if roots[k] == upload_root]
    preview_kinds = [k for k in keys if roots[k] == preview_root]
    if len(upload_kinds) != 2 or len(preview_kinds) != 1:
        raise SystemExit(f"루트별 종류 수가 규약과 다르다: {upload_kinds} / {preview_kinds}")
    body_kind, grid_kind = upload_kinds
    preview_kind = preview_kinds[0]
    layout_doc = "\n".join(
        f"  · {kind} — `{{{roots[kind]} 루트}}/{tpl}`" for kind, tpl in keys.items())
    layout_doc = (layout_doc
                  .replace("{uploadsPrefix}", spec["uploadsPrefix"])
                  .replace("{gridDirname}", spec["gridDirname"]))
    grid_why = "  " + spec["why"][grid_kind]
    rendered = TEMPLATE.format(
        layout_doc=layout_doc,
        target_id_doc="  " + spec["targetId"],
        previews_root_doc="  " + spec["previewsRoot"],
        grid_why=grid_why,
        preview_why="  " + spec["why"][preview_kind],
        uploads_prefix=spec["uploadsPrefix"],
        grid_dirname=spec["gridDirname"],
        key_templates="{\n" + "".join(f"    {k!r}: {v!r},\n" for k, v in keys.items()) + "}",
        roots="{\n" + "".join(f"    {k!r}: {v!r},\n" for k, v in roots.items()) + "}",
        body_kind=body_kind,
        grid_kind=grid_kind,
        preview_kind=preview_kind,
        upload_root=upload_root,
        preview_root=preview_root,
    )
    # **자기 검증** — 템플릿이 정본이 아니게 되면 생성 자체가 실패해야 한다.
    ns: dict = {}
    exec(compile(rendered, "<generated>", "exec"), ns)
    sample_body = ns["storage_key"]("T1", file_id="F1", kind=body_kind)
    sample_grid = ns["storage_key"]("T1", file_id="F1", kind=grid_kind, file_name="LAT_x.npy")
    expect_body = keys[body_kind].format(uploadsPrefix=spec["uploadsPrefix"],
                                         gridDirname=spec["gridDirname"],
                                         targetId="T1", fileId="F1", fileName="")
    expect_grid = keys[grid_kind].format(uploadsPrefix=spec["uploadsPrefix"],
                                         gridDirname=spec["gridDirname"],
                                         targetId="T1", fileId="F1", fileName="LAT_x.npy")
    assert sample_body == expect_body, (sample_body, expect_body)
    assert sample_grid == expect_grid, (sample_grid, expect_grid)
    # 미리보기 — ⓐ같은 입력이면 같은 키 ⓑ원본 키와 갈린다 ⓒ접수분 루트를 안 탄다
    digest = "0" * 64
    sample_preview = ns["preview_key"](digest, ".png")
    assert sample_preview == ns["preview_key"](digest, ".png"), sample_preview
    assert sample_preview == keys[preview_kind].format(contentKey=digest, extension=".png")
    assert not sample_preview.startswith(spec["uploadsPrefix"]), sample_preview
    assert sample_preview != sample_body
    try:
        ns["storage_key"]("T1", file_id="F1", kind=preview_kind)
    except ValueError:
        pass
    else:  # pragma: no cover — 생성 자체를 세우는 자리다
        raise AssertionError("접수분 배치 함수가 미리보기 산출물을 받아 버렸다")
    return rendered


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    Path(argv[1]).write_text(render(), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
