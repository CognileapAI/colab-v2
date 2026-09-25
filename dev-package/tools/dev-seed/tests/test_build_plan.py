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


SIGNED_AUX = [
    {"child": "pred_sample", "parent": "rn15_sample", "role": "보조입력"},
    {"child": "Prediction (공간상세화)", "parent": "HLS_S30_NDVI_mean_202305", "role": "보조입력"},
    {"child": "Prediction (공간상세화)", "parent": "DEM", "role": "보조입력"},
    {"child": "Prediction (공간상세화)", "parent": "Aspect", "role": "보조입력"},
    {"child": "Prediction (공간상세화)", "parent": "LULC_2023", "role": "보조입력"},
]


def lineage_fixture():
    names = [(3, "hsr_sample", []), (4, "rn15_sample", []),
             (5, "pred_sample", ["hsr_sample", "rn15_sample"]),
             (7, "GK2A_NDVI_mean_202305", []), (8, "HLS_S30_NDVI_mean_202305", []),
             (9, "DEM", []), (10, "Aspect", ["DEM"]), (11, "LULC_2023", []),
             (12, "Prediction (공간상세화)",
              ["GK2A_NDVI_mean_202305", "HLS_S30_NDVI_mean_202305", "DEM", "Aspect", "LULC_2023"])]
    datasets = [{"seq": s, "name": n, "summary": "md 요약 " + n, "parents": list(p)}
                for s, n, p in names]
    rows = [{"seq": s, "name": n, "start": "2023-05", "end": "2023-05",
             "granularity": "월", "basis": "사용자 제공 맥락",
             "topic": "강우·강수" if s <= 5 else "식생·NDVI",
             **({"registrationNote": "기준 시점은 사용자 제공 맥락에 따른 2023년 5월이며, 파일 내부 날짜 정보는 없음"}
                if n in ("DEM", "Aspect") else {})}
            for s, n, _ in names]
    return datasets, rows


def test_dem_and_aspect_keep_user_month_precision(tmp_path):
    datasets, rows = lineage_fixture()
    build_plan.bind_canonical_metadata(datasets, metadata_file(tmp_path, rows, SIGNED_AUX))
    by = {d["name"]: d for d in datasets}
    assert [(by[n]["period"]["start"], by[n]["period"]["granularity"])
            for n in ("DEM", "Aspect")] == [("2023-05", "월"), ("2023-05", "월")]
    assert "파일 내부 날짜 정보는 없음" in by["DEM"]["summary"]


def test_signed_auxiliary_roles_cover_verification_and_landcover_parents(tmp_path):
    """O4 (사용자 서명 2026-09-25) — 검증자료·토지피복은 보조입력, 주입력은 GK2A·hsr_sample 만 남는다."""
    datasets, rows = lineage_fixture()
    build_plan.bind_canonical_metadata(datasets, metadata_file(tmp_path, rows, SIGNED_AUX))
    by = {d["name"]: d for d in datasets}
    assert by["Prediction (공간상세화)"]["parent_roles"] == {
        "HLS_S30_NDVI_mean_202305": "보조입력", "DEM": "보조입력",
        "Aspect": "보조입력", "LULC_2023": "보조입력"}
    assert by["pred_sample"]["parent_roles"] == {"rn15_sample": "보조입력"}
    assert "parent_roles" not in by["Aspect"]


def test_auxiliary_role_rejects_the_pre_o4_two_edge_set(tmp_path):
    datasets, rows = lineage_fixture()
    with pytest.raises(SystemExit, match="보조입력 대상"):
        build_plan.bind_canonical_metadata(datasets, metadata_file(tmp_path, rows, SIGNED_AUX[2:4]))


def test_registration_summary_replaces_md_summary_and_keeps_note(tmp_path):
    datasets, rows = lineage_fixture()
    by_row = {r["name"]: r for r in rows}
    by_row["GK2A_NDVI_mean_202305"]["registrationSummary"] = "정본 설명 문장."
    by_row["DEM"]["registrationSummary"] = "DEM 정본 설명."
    build_plan.bind_canonical_metadata(datasets, metadata_file(tmp_path, rows, SIGNED_AUX))
    by = {d["name"]: d for d in datasets}
    assert by["GK2A_NDVI_mean_202305"]["summary"] == "정본 설명 문장."
    assert by["DEM"]["summary"] == ("DEM 정본 설명. · 기준 시점은 사용자 제공 맥락에 따른 2023년 5월이며, "
                                    "파일 내부 날짜 정보는 없음")
    assert by["hsr_sample"]["summary"] == "md 요약 hsr_sample"


def test_registration_summary_rejects_blank_and_over_limit(tmp_path):
    for bad in ("   ", "가" * 3001):
        datasets, rows = lineage_fixture()
        rows[0]["registrationSummary"] = bad
        with pytest.raises(SystemExit, match="등록 설명"):
            build_plan.bind_canonical_metadata(datasets, metadata_file(tmp_path, rows, SIGNED_AUX))


def test_repo_canonical_metadata_carries_the_dev_o4_o7_corrections():
    """커밋된 정본이 dev 보정(2026-09-25)과 같은 역할·설명을 재시드에 싣는다."""
    doc = json.loads((TOOL_DIR / "canonical-metadata.json").read_text(encoding="utf-8"))
    assert sorted((a["child"], a["parent"], a["role"]) for a in doc["auxiliaryParents"]) == \
        sorted((a["child"], a["parent"], a["role"]) for a in SIGNED_AUX)
    summaries = {r["seq"]: r.get("registrationSummary") for r in doc["datasets"]}
    assert sorted(s for s, v in summaries.items() if v) == [3, 4, 5, 6, 7, 8, 12, 13, 14]
    facts = {
        3: ["WGS84", "연구대상지", "연속 계열이 아니다"],
        4: ["WGS84", "연구대상지", "15분", "연속 계열이 아니다"],
        5: ["U-Net", "입력은 hsr_sample.npy", "검증은 rn15_sample.npy"],
        6: ["NDVI", "DQF", "2 km"],
        7: ["DQF", "경기도 남부~충청권", "2 km 를 100 m 로 균등 분할", "월 단위 평균"],
        8: ["검증자료", "HLS S30", "100 m"],
        12: ["U-Net", "검증자료", "토지피복지도"],
        13: ["시군구", "4주 SPI", "2025-12-20"],
        14: ["시군구", "4주 SPEI", "2025-12-20"],
    }
    for seq, needles in facts.items():
        for needle in needles:
            assert needle in summaries[seq], (seq, needle)


def test_canonical_topic_is_bound_to_every_plan_row(tmp_path):
    """The registration form has no topic field — the plan row carries it for the runner's PATCH."""
    datasets, rows = lineage_fixture()
    build_plan.bind_canonical_metadata(datasets, metadata_file(tmp_path, rows, SIGNED_AUX))
    by = {d["name"]: d["topic"] for d in datasets}
    assert by["pred_sample"] == "강우·강수"
    assert by["DEM"] == "식생·NDVI"


@pytest.mark.parametrize("bad", [None, "", "식생", "지형"])
def test_canonical_topic_must_be_one_of_the_db_check_values(tmp_path, bad):
    datasets, rows = lineage_fixture()
    if bad is None:
        rows[0].pop("topic")
    else:
        rows[0]["topic"] = bad
    with pytest.raises(SystemExit, match="주제.*hsr_sample"):
        build_plan.bind_canonical_metadata(datasets, metadata_file(tmp_path, rows, SIGNED_AUX))


def test_repo_canonical_topics_follow_the_reference_folder_of_each_dataset():
    """WU4 후속 (사용자 승인 2026-09-25) — dev 28건에 API 로 채운 주제와 같은 값을 재시드가 싣는다.

    규칙 = 참조자료 폴더(= `sources` 문서) → 주제. v1 적재기(`infra/staging/tools/build-manifest-refdata.py`
    `TOPIC`)와 v1 스냅샷 9건의 주제가 같은 규칙이다(서명 ① 대응으로 확인).
    """
    doc = json.loads((TOOL_DIR / "canonical-metadata.json").read_text(encoding="utf-8"))
    by_document = {
        "01.level-data/01.precipitation/DATASETS.md": "강우·강수",
        "01.level-data/02.vegetation/DATASETS.md": "식생·NDVI",
        "01.level-data/03.drought/DATASETS.md": "가뭄",
        "02.File-format/DATASETS.md": "파일 포맷 예제",
    }
    expected = {seq: by_document[s["document"]] for s in doc["sources"] for seq in s["datasets"]}
    got = {r["seq"]: r.get("topic") for r in doc["datasets"]}
    assert len(got) == 28 and got == expected
    assert set(got.values()) <= set(build_plan.TOPICS)


def test_auxiliary_role_rejects_the_wrong_ndvi_target(tmp_path):
    datasets = [{"seq": 9, "name": "DEM", "parents": []},
                {"seq": 10, "name": "Aspect", "parents": ["DEM"]},
                {"seq": 12, "name": "다른 결과", "parents": ["DEM", "Aspect"]}]
    rows = [{"seq": d["seq"], "name": d["name"], "start": "2023-05",
             "end": "2023-05", "granularity": "월", "basis": "fixture", "topic": "식생·NDVI"}
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


# ── 업로드 필수 칸 값(`upload-classify.json`) — 서명 전에는 계획을 쓰지 않는다 ─────────

def classify_row(seq, name, level="Lv0", **over):
    row = {"seq": seq, "name": name, "category": "기상·기후 인자", "dataType": "지상관측자료",
           "interval": {"value": "5", "unit": "분"},
           "source": ({"url": "https://apihub.kma.go.kr/", "downloadedOn": "2025-08-13"}
                      if level == "Lv0" else None),
           "basis": {"category": "fixture", "dataType": "fixture", "interval": "fixture", "source": "fixture"}}
    row.update(over)
    return row


def classify_file(tmp_path, rows, status="signed", signed_by="Ted", signed_on="2026-09-25"):
    path = tmp_path / "upload-classify.json"
    path.write_text(json.dumps({"schema": "colab-dev-seed-classify/1", "status": status,
                                "signedBy": signed_by, "signedOn": signed_on, "datasets": rows},
                               ensure_ascii=False), encoding="utf-8")
    return path


def plan_rows():
    return [{"seq": 1, "name": "raw", "processing_level": "Lv0", "parents": []},
            {"seq": 2, "name": "derived", "processing_level": "Lv1", "parents": ["raw"]}]


def test_서명된_값은_계획_행에_실린다(tmp_path):
    datasets = plan_rows()
    path = classify_file(tmp_path, [classify_row(1, "raw"), classify_row(2, "derived", level="Lv1")])
    build_plan.bind_upload_classify(datasets, path)
    assert datasets[0]["category"] == "기상·기후 인자"
    assert datasets[0]["data_type"] == "지상관측자료"
    assert datasets[0]["observation_interval"] == {"value": "5", "unit": "분"}
    assert datasets[0]["source"] == {"url": "https://apihub.kma.go.kr/", "downloaded_on": "2025-08-13"}
    assert "source" not in datasets[1]


def test_서명_전_제안은_거절하고_명시_허용일_때만_싣는다(tmp_path):
    rows = [classify_row(1, "raw"), classify_row(2, "derived", level="Lv1")]
    path = classify_file(tmp_path, rows, status="proposal", signed_by=None, signed_on=None)
    with pytest.raises(SystemExit, match="서명"):
        build_plan.bind_upload_classify(plan_rows(), path)
    datasets = plan_rows()
    build_plan.bind_upload_classify(datasets, path, allow_unsigned=True)
    assert datasets[1]["category"] == "기상·기후 인자"


@pytest.mark.parametrize("over,needle", [
    ({"category": None}, "분류"), ({"category": "기상 인자"}, "분류"),
    ({"dataType": "레이더자료"}, "유형"),
    ({"interval": {"value": "1", "unit": "주"}}, "관측 간격"),
    ({"interval": {"value": "0", "unit": "일"}}, "관측 간격"),
    ({"source": None}, "출처"),
    ({"source": {"url": "https://x.invalid/", "downloadedOn": "2025-02-31"}}, "출처"),
    ({"basis": {"category": ""}}, "근거"),
])
def test_값이_비었거나_사전_밖이면_행_이름을_대고_멈춘다(tmp_path, over, needle):
    path = classify_file(tmp_path, [classify_row(1, "raw", **over), classify_row(2, "derived", level="Lv1")])
    with pytest.raises(SystemExit, match=needle) as exc:
        build_plan.bind_upload_classify(plan_rows(), path)
    assert "raw" in str(exc.value)


def test_Lv0_가_아닌_행에_출처를_두면_멈춘다(tmp_path):
    path = classify_file(tmp_path, [classify_row(1, "raw"), classify_row(2, "derived", level="Lv1",
                         source={"url": "https://x.invalid/", "downloadedOn": "2025-08-13"})])
    with pytest.raises(SystemExit, match="출처"):
        build_plan.bind_upload_classify(plan_rows(), path)


def test_계획과_행_집합이_다르면_멈춘다(tmp_path):
    path = classify_file(tmp_path, [classify_row(1, "raw")])
    with pytest.raises(SystemExit, match="derived"):
        build_plan.bind_upload_classify(plan_rows(), path)


def test_커밋된_제안_파일은_계획_28행과_맞고_서명_전이면_멈춘다():
    import yaml
    manifest = yaml.safe_load((TOOL_DIR / "plan-manifest.yaml").read_text(encoding="utf-8"))
    datasets = [{"seq": d["seq"], "name": d["name"], "processing_level": d["level"],
                 "parents": list(d.get("parents") or [])} for d in manifest["datasets"]]
    doc = json.loads(build_plan.DEFAULT_CLASSIFY.read_text(encoding="utf-8"))
    if doc.get("status") != "signed":
        with pytest.raises(SystemExit, match="서명"):
            build_plan.bind_upload_classify([dict(d) for d in datasets])
    build_plan.bind_upload_classify(datasets, allow_unsigned=True)
    assert len(datasets) == 28 and all(d.get("category") and d.get("data_type") for d in datasets)
