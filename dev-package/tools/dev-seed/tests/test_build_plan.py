"""`build_plan.py` 시험 — md 4건 → 계획.

- 의존 = 표준 라이브러리 ＋ `yaml` 뿐(`pytest` 로 실행).
- 시험 뿌리는 `tmp_path` 안에 참조자료 나무와 md 4건을 직접 만든다. 실물 참조자료를 읽지 않는다.
- 판정 = 종료코드. 0 green · 2 나무 대조 실패·계수 불일치 · 3 표↔블록 불일치 ·
  4 기본값 아닌 기대값으로 생성물을 쓰려 함.
"""

import importlib.util
import json
import pathlib

import pytest

TOOL_DIR = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("build_plan", TOOL_DIR / "build_plan.py")
build_plan = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_plan)

# md 4건의 자리 — 생성기가 고정으로 찾는 경로와 같아야 한다.
LAYOUT = [
    ("precipitation", "01.level-data/01.precipitation", "01.precipitation/a.bin", 11),
    ("vegetation", "01.level-data/02.vegetation", "02.vegetation/b.tif", 22),
    ("drought", "01.level-data/03.drought", "03.drought/c.gpkg", 33),
    ("format-test", "02.File-format", "file_format_1_grib/d.grib", 44),
]

MD = """# {pid} 시험용 정본

- 유형 폴더: `{folder}/`

## 데이터셋 표

| # | 이름 | 레벨 | 부모 | 파일 글롭 | 건수 | 바이트 | 기준 격자(쌍) | 포맷 | 미리보기 기대 | 비고 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | {name} | {level} | — | `{glob}` | {t_count} | {t_bytes} | 없음 | bin | {t_preview} | 없음 |

## 기계 블록 (생성기 입력)

```yaml
# colab-datasets v1 — 이 블록이 생성기의 입력이다. 표와 어긋나면 생성기가 비영 종료한다.
project: {pid}
project_name: "{pid}"
project_description: "시험용 프로젝트"
folder: {folder}
datasets:
  - seq: {seq}
    name: "{name}"
    level: {level}
    parents: []
    summary: "시험용 한 줄"
    files: ["{glob}"]
    file_count: {b_count}
    bytes: {b_bytes}
    grid_files: []
    format: "bin"
    preview_expected: "{b_preview}"
    description: "시험용 설명"
    note: "시험용 비고"
```
"""


def build_tree(tmp_path, overrides=None):
    """참조자료 나무 ＋ md 4건을 만들고 (ref_root, md_root) 를 돌려준다."""
    overrides = overrides or dict()
    ref_root = tmp_path / "ref"
    md_root = tmp_path / "md"
    for seq, (pid, folder, glob, size) in enumerate(LAYOUT, start=1):
        data_path = ref_root / folder / glob
        data_path.parent.mkdir(parents=True, exist_ok=True)
        data_path.write_bytes(b"x" * size)
        (data_path.parent / "desktop.ini").write_bytes(b"ignored")
        values = dict(
            pid=pid, folder=folder, glob=glob, seq=seq, level="Lv0",
            name="%s-표본" % pid,
            t_count=1, t_bytes=size, b_count=1, b_bytes=size,
            t_preview="미측정", b_preview="미측정",
        )
        values.update(overrides.get(pid) or dict())
        md_path = md_root / folder / "DATASETS.md"
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(MD.format(**values), encoding="utf-8")
    return ref_root, md_root


def run(tmp_path, ref_root, md_root, extra=None):
    out = tmp_path / "upload-plan.json"
    manifest = tmp_path / "plan-manifest.yaml"
    argv = ["--ref-root", str(ref_root), "--md-root", str(md_root),
            "--out", str(out), "--manifest-out", str(manifest)]
    argv += extra if extra is not None else [
        "--expect-datasets", "4", "--expect-edges", "0", "--allow-nondefault-expect"]
    return build_plan.main(argv), out, manifest


def test_블록과_나무가_맞으면_계획을_쓴다(tmp_path, capsys):
    ref_root, md_root = build_tree(tmp_path)
    rc, out, manifest = run(tmp_path, ref_root, md_root)
    assert rc == 0, capsys.readouterr().out
    plan = json.loads(out.read_text(encoding="utf-8"))
    assert len(plan["datasets"]) == 4
    assert [d["processing_level"] for d in plan["datasets"]] == ["Lv0"] * 4
    # 러너가 읽는 칸이 그대로 있다.
    row = plan["datasets"][0]
    for key in ("seq", "project", "name", "summary", "files", "file_count",
                "bytes", "grid_files", "grid_bytes", "grid_skip", "parents"):
        assert key in row, key
    assert row["preview_expected"] == "미측정"
    assert "preview_expected: 미측정" in manifest.read_text(encoding="utf-8")
    assert manifest.read_text(encoding="utf-8").startswith("# 생성물")


def test_블록_바이트가_나무와_다르면_2로_끝난다(tmp_path, capsys):
    ref_root, md_root = build_tree(
        tmp_path, overrides={"drought": dict(t_bytes=999, b_bytes=999)})
    rc, _, _ = run(tmp_path, ref_root, md_root)
    printed = capsys.readouterr().out
    assert rc == 2, printed
    assert "drought-표본" in printed


def test_표가_블록과_다르면_3으로_끝난다(tmp_path, capsys):
    ref_root, md_root = build_tree(
        tmp_path, overrides={"vegetation": dict(t_count=7)})
    rc, _, _ = run(tmp_path, ref_root, md_root)
    printed = capsys.readouterr().out
    assert rc == 3, printed
    assert "vegetation-표본" in printed


def test_미리보기_기대가_표와_블록에서_다르면_3으로_끝난다(tmp_path, capsys):
    ref_root, md_root = build_tree(
        tmp_path, overrides={"drought": dict(t_preview="성립", b_preview="미측정")})
    rc, _, _ = run(tmp_path, ref_root, md_root)
    assert rc == 3, capsys.readouterr().out


def test_미리보기_기대_누락은_거절한다(tmp_path):
    blocks = [dict(project="one", folder=".", datasets=[dict(
        seq=1, name="one", level="Lv0", files=[], file_count=0, bytes=0,
        grid_files=[], parents=[], preview_expected="")])]
    with pytest.raises(SystemExit, match="미리보기 기대"):
        build_plan.resolve_rows(blocks, tmp_path, resolve_files=False)


def test_총계가_28_18_이_아니면_2로_끝난다(tmp_path, capsys):
    ref_root, md_root = build_tree(tmp_path)
    rc, _, _ = run(tmp_path, ref_root, md_root, extra=[])
    printed = capsys.readouterr().out
    assert rc == 2, printed
    assert "28" in printed and "18" in printed


def test_기본값_아닌_기대값으로_쓰려_하면_4로_막힌다(tmp_path, capsys):
    """기대값을 낮춰 짧은 계획을 통과시키는 길을 막는다 — 빗장 없이는 아무것도 쓰지 않는다."""
    ref_root, md_root = build_tree(tmp_path)
    rc, out, manifest = run(tmp_path, ref_root, md_root,
                            extra=["--expect-datasets", "4", "--expect-edges", "0"])
    printed = capsys.readouterr().out
    assert rc == 4, printed
    assert "--allow-nondefault-expect" in printed
    assert not out.exists()
    assert not manifest.exists()


def test_기본값_아닌_기대값도_dry_run_이면_판정만_한다(tmp_path, capsys):
    """`--dry-run` 은 아무것도 쓰지 않으므로 빗장 대상이 아니다 — 픽스처 나무 판정이 여기서 난다."""
    ref_root, md_root = build_tree(tmp_path)
    rc, out, manifest = run(tmp_path, ref_root, md_root,
                            extra=["--expect-datasets", "4", "--expect-edges", "0", "--dry-run"])
    printed = capsys.readouterr().out
    assert rc == 0, printed
    assert not out.exists()
    assert not manifest.exists()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))


@pytest.mark.parametrize('cross_row', [False, True])
def test_declared_grid_cannot_be_body_in_any_row(tmp_path, cross_row):
    folder = tmp_path / 'data'
    folder.mkdir()
    (folder / 'lon2d.npy').write_bytes(b'grid')
    (folder / 'body.bin').write_bytes(b'body')
    body = dict(seq=1, name='body', level='Lv0', files=['lon2d.npy'],
                file_count=1, bytes=4, grid_files=[] if cross_row else ['lon2d.npy'],
                preview_expected='미측정')
    blocks = [dict(project='one', folder='data', datasets=[body])]
    if cross_row:
        blocks.append(dict(project='two', folder='data', datasets=[dict(
            seq=2, name='owner', level='Lv0', files=['body.bin'],
            file_count=1, bytes=4, grid_files=['../data/lon2d.npy'],
            preview_expected='미측정')]))
    with pytest.raises(SystemExit, match='보조 격자.*본문'):
        build_plan.resolve_rows(blocks, tmp_path)


def test_grid_body_guard_preserves_distinct_body_and_shared_grid(tmp_path):
    (tmp_path / 'body.bin').write_bytes(b'body')
    (tmp_path / 'lon2d.npy').write_bytes(b'grid')
    blocks = [dict(project='one', folder='.', datasets=[dict(
        seq=i, name='row'+str(i), level='Lv0', files=['body.bin'],
        file_count=1, bytes=4, grid_files=['lon2d.npy'],
        preview_expected='미측정') for i in range(1,29)])]
    rows, mismatch, missing = build_plan.resolve_rows(blocks, tmp_path)
    assert len(rows) == 28
    assert mismatch == missing == []
    assert all([pathlib.Path(p).name for p in r['files']] == ['body.bin'] for r in rows)
    assert all([pathlib.Path(p).name for p in r['grid_files']] == ['lon2d.npy'] for r in rows)


def metadata_file(tmp_path, rows, auxiliary=None):
    path = tmp_path / "canonical-metadata.json"
    path.write_text(json.dumps({
        "schema": "colab-dev-seed-metadata/1",
        "datasets": rows,
        "auxiliaryParents": auxiliary or [],
    }, ensure_ascii=False), encoding="utf-8")
    return path


def test_canonical_metadata_requires_a_period_for_every_dataset(tmp_path):
    datasets = [{"seq": 1, "name": "one", "parents": []},
                {"seq": 2, "name": "two", "parents": []}]
    path = metadata_file(tmp_path, [
        {"seq": 1, "name": "one", "start": "2023-05", "end": "2023-05",
         "granularity": "월", "basis": "fixture"},
    ])
    with pytest.raises(SystemExit, match="기간.*two"):
        build_plan.bind_canonical_metadata(datasets, path)


def test_dem_and_aspect_keep_user_month_precision(tmp_path):
    datasets = [{"seq": 9, "name": "DEM", "parents": []},
                {"seq": 10, "name": "Aspect", "parents": ["DEM"]},
                {"seq": 12, "name": "Prediction (공간상세화)",
                 "parents": ["DEM", "Aspect"]}]
    rows = [{"seq": seq, "name": name, "start": "2023-05", "end": "2023-05",
             "granularity": "월", "basis": "사용자 제공 맥락",
             **({"registrationNote": "기준 시점은 사용자 제공 맥락에 따른 2023년 5월이며, 파일 내부 날짜 정보는 없음"}
                if name in ("DEM", "Aspect") else {})}
            for seq, name in [(9, "DEM"), (10, "Aspect"),
                              (12, "Prediction (공간상세화)")]]
    path = metadata_file(tmp_path, rows, [
        {"child": "Prediction (공간상세화)", "parent": "DEM", "role": "보조입력"},
        {"child": "Prediction (공간상세화)", "parent": "Aspect", "role": "보조입력"},
    ])
    build_plan.bind_canonical_metadata(datasets, path)
    assert [(d["period"]["start"], d["period"]["granularity"])
            for d in datasets[:2]] == [("2023-05", "월"), ("2023-05", "월")]
    assert datasets[2]["parent_roles"] == {"DEM": "보조입력", "Aspect": "보조입력"}
    assert "파일 내부 날짜 정보는 없음" in datasets[0]["summary"]


def test_auxiliary_role_rejects_the_wrong_ndvi_target(tmp_path):
    datasets = [{"seq": 9, "name": "DEM", "parents": []},
                {"seq": 10, "name": "Aspect", "parents": ["DEM"]},
                {"seq": 12, "name": "다른 결과", "parents": ["DEM", "Aspect"]}]
    rows = [{"seq": d["seq"], "name": d["name"], "start": "2023-05",
             "end": "2023-05", "granularity": "월", "basis": "fixture"}
            for d in datasets]
    path = metadata_file(tmp_path, rows, [
        {"child": "다른 결과", "parent": "DEM", "role": "보조입력"},
    ])
    with pytest.raises(SystemExit, match="보조입력 대상"):
        build_plan.bind_canonical_metadata(datasets, path)


def test_canonical_metadata_rejects_duplicate_rows_and_impossible_dates(tmp_path):
    datasets = [{"seq": 1, "name": "one", "parents": []}]
    duplicate = {"seq": 1, "name": "one", "start": "2023-05", "end": "2023-05",
                 "granularity": "월", "basis": "fixture"}
    with pytest.raises(SystemExit, match="중복"):
        build_plan.bind_canonical_metadata(
            datasets, metadata_file(tmp_path, [duplicate, dict(duplicate)]))
    impossible = dict(duplicate, start="2023-02-31", end="2023-02-31", granularity="일")
    with pytest.raises(SystemExit, match="정밀도"):
        build_plan.bind_canonical_metadata(datasets, metadata_file(tmp_path, [impossible]))
