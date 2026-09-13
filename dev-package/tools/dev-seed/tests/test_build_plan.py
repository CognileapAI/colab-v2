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
| 1 | {name} | {level} | — | `{glob}` | {t_count} | {t_bytes} | 없음 | bin | 미측정 | 없음 |

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
    preview_expected: "미측정"
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
