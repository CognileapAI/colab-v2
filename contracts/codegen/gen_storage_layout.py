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


#: 지도 타일의 내용 키 접두사. **한 슬롯 안에서 두 규칙을 눈으로도 가른다** —
#: 렌더 산출물은 접두사가 없고, 지도 타일은 이것으로 시작한다.
MAP_TILE_KEY_PREFIX = {tile_prefix!r}

#: 규칙 자신의 판. 재료의 뜻이 바뀌면 이 값을 올린다 — 그러면 옛 키와 새 키가 갈린다.
MAP_TILE_KEY_VERSION = {tile_version!r}

#: 지도 타일 키를 짓는 재료. **전부 필수다.** 기본값을 두지 않는 이유는
#: `layout.json` 의 `fieldsWhy` 에 있다 — 빠진 재료를 관대한 기본값으로 메우면
#: 서로 다른 산출물이 같은 키를 얻는다.
MAP_TILE_KEY_FIELDS = {tile_fields}

#: 좌표가 파일 안에 있어 기준 격자를 쓰지 않은 경우의 `gridDigest` 명시값.
#: **빈 값이 아니다** — 「격자가 없다」와 「안 물어봤다」를 가른다.
GRID_DIGEST_EMBEDDED = '내장'

#: **변환 설정 — 키 재료 셋의 정본**(`layout.json` `contentKeys.지도 타일.conversionSettings`).
#: 승격 이전에는 `pipeline-worker` 안에만 있었고 **굽는 쪽만 키를 지을 수 있었다.**
#: 읽는 쪽(D7)이 같은 자리를 찾으려면 같은 값이어야 하므로 규약이 정본을 갖는다
#: (`PLAN-SoT §9 〈294〉`). 사유 전문은 `conversionSettingsWhy`.
MAP_TILE_CONVERSION_KIND = {tile_conversion_kind!r}

#: `DR-12` 정본 분기 — **값이 아니라 표다.** `conversionKind` 로 골라 쓴다.
MAP_TILE_OVERVIEW_RESAMPLING = {tile_overview_resampling}

MAP_TILE_COMPRESSION = {tile_compression!r}


def map_tile_grid_digest(grid_dir, used_reference_grid: bool) -> str:
    """`gridDigest` 재료 하나 — **좌표를 준 것의 다이제스트.**

    파일 안 좌표를 썼으면 명시값(`GRID_DIGEST_EMBEDDED`)이다. 빈 값으로 두면
    「격자가 없다」와 「안 물어봤다」가 같은 키를 얻는다(`fieldsWhy`).

    ⚠ **굽는 쪽과 읽는 쪽이 같은 함수를 부른다.** 같은 규칙을 두 곳에 적으면
    갈라지고, 갈라진 순간 읽는 쪽은 자리를 영영 못 찾는다 — 그 실패는 에러가 아니라
    「값 없음」으로 위장한다(`CLAUDE.md §3` 불변규칙 1 · `〈294〉`).
    """
    import hashlib as _hashlib

    if not used_reference_grid or grid_dir is None:
        return GRID_DIGEST_EMBEDDED
    h = _hashlib.sha256()
    for f in sorted(Path(grid_dir).iterdir()):
        if not f.is_file():
            continue
        h.update(f.name.encode("utf-8"))
        fh_digest = _hashlib.sha256()
        with open(f, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                fh_digest.update(chunk)
        h.update(fh_digest.hexdigest().encode("ascii"))
    return h.hexdigest()


def map_tile_content_key(**fields) -> str:
    """지도 타일 하나의 **내용 키** — 파이프라인이 실제로 가진 재료만으로 짓는다.

    ⚠ **렌더 산출물의 키 규칙(`render_cache_key`)을 쓰지 않는다.** 그 규칙의 입력은
    렌더 파라미터이고 파이프라인에는 그 값이 없다 — 부르는 순간 D5 가 D7 의 개념을 갖는다.
    두 규칙은 같은 슬롯(`미리보기 산출물`)에 산출물을 놓지만 **키가 서로를 침범하지 않는다.**

    재료가 하나라도 빠지거나 비면 **짓지 않고 예외다.** 지어낸 기본값으로 키를 만들면
    서로 다른 산출물이 같은 자리를 차지한다.
    """
    import hashlib
    import json as _json

    missing = [f for f in MAP_TILE_KEY_FIELDS if fields.get(f) in (None, "")]
    if missing:
        raise ValueError(
            f"지도 타일 내용 키의 재료가 없다: {{missing}} — 기본값으로 메우지 않는다")
    unknown = [f for f in fields if f not in MAP_TILE_KEY_FIELDS]
    if unknown:
        raise ValueError(f"지도 타일 내용 키가 모르는 재료다: {{unknown}} — 규약은 layout.json 이다")
    material = [MAP_TILE_KEY_VERSION] + [str(fields[f]) for f in MAP_TILE_KEY_FIELDS]
    digest = hashlib.sha256(
        _json.dumps(material, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return MAP_TILE_KEY_PREFIX + digest


def is_map_tile_key(content_key: str) -> bool:
    """한 슬롯에 함께 사는 둘 중 어느 규칙이 지은 키인가."""
    return str(content_key).startswith(MAP_TILE_KEY_PREFIX)


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
    tile = spec["contentKeys"]["지도 타일"]
    rendered = TEMPLATE.format(
        tile_prefix=tile["prefix"],
        tile_version=tile["version"],
        tile_fields="(\n" + "".join(f"    {f!r},\n" for f in tile["fields"]) + ")",
        tile_conversion_kind=tile["conversionSettings"]["conversionKind"],
        tile_overview_resampling=(
            "{\n" + "".join(
                f"    {k!r}: {v!r},\n"
                for k, v in tile["conversionSettings"]["overviewResampling"].items()) + "}"),
        tile_compression=tile["conversionSettings"]["compression"],
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
    # 지도 타일 키 — ⓐ같은 재료면 같은 키 ⓑ재료 하나가 바뀌면 갈린다 ⓒ렌더 키와 섞이지 않는다
    #                ⓓ재료가 빠지면 **짓지 않는다**(기본값 금지)
    material = {f: f"v-{i}" for i, f in enumerate(tile["fields"])}
    k1 = ns["map_tile_content_key"](**material)
    assert k1 == ns["map_tile_content_key"](**material), k1
    changed = dict(material, **{tile["fields"][0]: "다른-원본"})
    assert ns["map_tile_content_key"](**changed) != k1
    assert ns["is_map_tile_key"](k1) and not ns["is_map_tile_key"](digest)
    assert ns["preview_key"](k1, ".tif") != ns["preview_key"](digest, ".tif")
    for f in tile["fields"]:
        try:
            ns["map_tile_content_key"](**dict(material, **{f: None}))
        except ValueError:
            continue
        raise AssertionError(f"재료 {f} 가 없는데 지도 타일 키가 지어졌다 (관대한 기본값)")
    return rendered


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    Path(argv[1]).write_text(render(), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
