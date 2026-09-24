#!/usr/bin/env python3
"""참조자료 폴더의 `DATASETS.md` 4건 → 등재표(`plan-manifest.yaml`) ＋ 업로드 계획(`upload-plan.json`).

- **원본은 md 4건이다.** 각 md 의 ```yaml 블록(첫 줄에 `colab-datasets v1`)이 생성기의 입력이고,
  같은 파일의 마크다운 표는 사람이 읽는 자리다. 둘이 어긋나면 종료코드 3 으로 멈춘다.
- 읽는 자리 = `--md-root`(기본값 = 참조자료 뿌리)의 넷 —
  `01.level-data/01.precipitation` · `01.level-data/02.vegetation` · `01.level-data/03.drought` ·
  `02.File-format` 각각의 `DATASETS.md`.
- 참조자료 뿌리 = `--ref-root` · 환경변수 `COLAB_REF_ROOT` · 기본값(본 체크아웃과 나란한
  `03 Reference-Data`) 순. 워크트리에서도 본 체크아웃 기준으로 풀린다.
  ⛔ 코드·md 에 절대경로를 적지 않는다 — 글롭은 전부 블록의 `folder` 기준 상대 경로다.
- 출력 둘 — `plan-manifest.yaml`(생성물 · 손으로 고치지 않는다) · `<work-dir>/upload-plan.json`
  (러너가 읽는 파일이고 그 안의 경로는 실행 자리의 절대경로다. 작업 자리는 `.gitignore` 로 제외된다).
- 판정 = ⑴ 표↔블록(이름·건수·바이트) ⑵ 블록↔실물 나무(글롭이 맞힌 파일 수·바이트) ⑶ 총계.
  어긋나면 그 행 이름을 적고 비영 종료한다(조용히 진행하지 않는다).

종료코드 — 0 정상 · 2 나무 대조 실패·파일 부재·총계 불일치 · 3 표↔블록 불일치 ·
  4 기본값 아닌 기대값으로 생성물을 쓰려 함(`--allow-nondefault-expect` 참조) ·
  5 `--check-manifest` 에서 커밋된 등재표가 md 재생성본과 다름.
"""

import argparse
import datetime
import difflib
import glob
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:  # 표준 라이브러리 밖 의존은 이것 하나다.
    print("PyYAML 이 없다 — `pip install pyyaml` 또는 서비스 venv 에서 실행한다.",
          file=sys.stderr)
    raise SystemExit(2)

TOOL_DIR = Path(__file__).resolve().parent
DEFAULT_MANIFEST_OUT = TOOL_DIR / "plan-manifest.yaml"
DEFAULT_WORK_DIR = TOOL_DIR / ".work"
DEFAULT_METADATA = TOOL_DIR / "canonical-metadata.json"
# 업로드 마법사 필수 칸 값(분류·유형·관측 간격·Lv0 출처). 서명 전(`status != signed`)이면 계획을 쓰지 않는다.
DEFAULT_CLASSIFY = TOOL_DIR / "upload-classify.json"
# 저장값 원본 = frontend/src/components/upload/axisDict.ts `CATEGORIES`·`DATA_TYPES` ·
# RegisterArea.tsx `INTERVAL_UNITS`. 러너(`runner.py`)도 같은 값으로 다시 검사한다.
CATEGORIES = ("수문 인자", "기상·기후 인자", "식생·탄소 인자", "사회·경제 인자", "환경 인자")
DATA_TYPES = ("지상관측자료", "위성자료", "재분석자료", "수치모형자료", "합성자료", "관측 기반 산출물")
INTERVAL_UNITS = ("초", "분", "시", "일", "월", "년")
# 등록 설명 칸 상한 = RegisterArea.tsx `reg-summary` maxLength(6705675d · 3000자). 서버·계약에는 상한이 없다.
SUMMARY_MAX_CHARS = 3000
# 보조입력 간선 정본. DEM·Aspect 는 첫 등재, 나머지 셋은 O4(사용자 서명 2026-09-25) —
# 검증자료(HLS·rn15_sample)와 토지피복(LULC)은 주입력이 아니다. 역할 enum 이 2값뿐이라
# 「검증」은 설명 칸(`registrationSummary`)에만 적는다(`db/platform/schema.sql` d4_lineage_edge).
EXPECTED_AUXILIARY = {
    ("Prediction (공간상세화)", "HLS_S30_NDVI_mean_202305", "보조입력"),
    ("Prediction (공간상세화)", "DEM", "보조입력"),
    ("Prediction (공간상세화)", "Aspect", "보조입력"),
    ("Prediction (공간상세화)", "LULC_2023", "보조입력"),
    ("pred_sample", "rn15_sample", "보조입력"),
}

# md 4건의 자리. 순서가 계획의 프로젝트 순서이고 seq 순서와 같다.
MD_RELATIVE = [
    "01.level-data/01.precipitation/DATASETS.md",
    "01.level-data/02.vegetation/DATASETS.md",
    "01.level-data/03.drought/DATASETS.md",
    "02.File-format/DATASETS.md",
]
BLOCK_MARKER = "colab-datasets v1"
LEVELS = ("Lv0", "Lv1", "Lv2", "Lv3")
NO_PREVIEW_EXPECTATION = "미성립(포맷 미지원 · 판정 표에 이름으로)"
NO_PREVIEW_DATASETS = {"SPI-4weeks", "SPEI-4weeks"}
EXPECT_DATASETS = 28
EXPECT_EDGES = 18
PERIOD_PATTERNS = {
    "년": r"\d{4}", "월": r"\d{4}-(0[1-9]|1[0-2])",
    "일": r"\d{4}-(0[1-9]|1[0-2])-([0-2]\d|3[01])",
    "시": r"\d{4}-(0[1-9]|1[0-2])-([0-2]\d|3[01])T([01]\d|2[0-3])",
    "분": r"\d{4}-(0[1-9]|1[0-2])-([0-2]\d|3[01])T([01]\d|2[0-3]):[0-5]\d",
    "초": r"\d{4}-(0[1-9]|1[0-2])-([0-2]\d|3[01])T([01]\d|2[0-3]):[0-5]\d:[0-5]\d",
}
PERIOD_FORMATS = {"년": "%Y", "월": "%Y-%m", "일": "%Y-%m-%d",
                  "시": "%Y-%m-%dT%H", "분": "%Y-%m-%dT%H:%M",
                  "초": "%Y-%m-%dT%H:%M:%S"}

MANIFEST_HEADER = """# 생성물 · 손으로 고치지 않는다 · 원본 = 참조자료 폴더의 DATASETS.md 4건.
#
# - 만드는 것 = `dev-package/tools/dev-seed/build_plan.py`. 값을 고치려면 md 를 고치고 다시 돌린다.
# - 경로는 전부 **참조자료 뿌리로부터의 상대 글롭** 이다. 뿌리는 `COLAB_REF_ROOT` 로 준다.
# - `expect_files`·`expect_bytes` = 그 글롭이 맞혀야 하는 파일 수·바이트(md 블록 값).
# - `level` = 제품 값(`Lv0`~`Lv3`). 화면·계획의 `processing_level` 과 같은 값이다.
"""


def repo_root():
    """워크트리에서도 본 체크아웃을 가리킨다 — `--git-common-dir` 의 부모."""
    try:
        out = subprocess.run(["git", "rev-parse", "--git-common-dir"],
                             cwd=str(TOOL_DIR), capture_output=True, text=True, check=True)
        common = Path(out.stdout.strip())
        if not common.is_absolute():
            common = (TOOL_DIR / common).resolve()
        return common.parent
    except Exception:
        return TOOL_DIR.parents[2]


def inside_tool_dir(path):
    """생성물이 도구 폴더(`dev-package/tools/dev-seed/`) 안을 가리키는가."""
    p = Path(path).expanduser().resolve()
    return p == TOOL_DIR or TOOL_DIR in p.parents


def guard_nondefault_expect(args):
    """기대값을 기본값에서 낮춘 채 **생성물을 쓰는** 길을 막는다.

    막는 이유 — `--expect-datasets`·`--expect-edges` 는 총계 오라클이다. 부르는 쪽이 이 둘을
    낮추면 짧은 계획이 총계 검사를 그대로 통과하고, 그렇게 만들어진 `plan-manifest.yaml` 이
    커밋되면 **검사기가 아무것도 검사하지 않은 채 통과를 보고한다**(`CLAUDE.md §4`).
    판정만 하는 `--dry-run` 은 아무것도 쓰지 않으므로 이 빗장의 대상이 아니다.

    반환 = 막을 사유 목록(빈 목록이면 통과).
    """
    if args.dry_run:
        return []
    if args.expect_datasets == EXPECT_DATASETS and args.expect_edges == EXPECT_EDGES:
        return []
    bad = []
    if not args.allow_nondefault_expect:
        bad.append("--allow-nondefault-expect 가 없다")
    if not args.out:
        bad.append("--out 이 없다 — 기본 작업 자리에 쓰지 않는다")
    for label, value in (("--out", args.out), ("--manifest-out", args.manifest_out)):
        if value and inside_tool_dir(value):
            bad.append("%s 가 도구 폴더 안을 가리킨다: %s" % (label, value))
    return bad


def resolve_ref_root(arg):
    if arg:
        return Path(arg).expanduser()
    env = os.environ.get("COLAB_REF_ROOT")
    if env:
        return Path(env).expanduser()
    return repo_root().parent / "03 Reference-Data"


def bind_canonical_metadata(datasets, path=DEFAULT_METADATA):
    """Bind checked-in period and special lineage roles to every plan row."""
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit("정본 기간 파일을 읽지 못했다: %s" % path) from exc
    if doc.get("schema") != "colab-dev-seed-metadata/1":
        raise SystemExit("정본 기간 스키마가 아니다: %s" % path)
    metadata_rows = doc.get("datasets") or []
    by_key = {(x.get("seq"), x.get("name")): x for x in metadata_rows}
    if len(by_key) != len(metadata_rows):
        raise SystemExit("기간 정본에 seq/name 중복이 있다")
    expected = {(d["seq"], d["name"]) for d in datasets}
    if set(by_key) != expected:
        missing = sorted(name for key, name in expected - set(by_key))
        extra = sorted(name for key, name in set(by_key) - expected)
        raise SystemExit("기간 정본과 계획이 다르다: 누락=%s 초과=%s" % (missing, extra))
    for d in datasets:
        row = by_key[(d["seq"], d["name"])]
        unit, start, end = row.get("granularity"), row.get("start"), row.get("end")
        pattern = PERIOD_PATTERNS.get(unit)
        try:
            dates_valid = (datetime.datetime.strptime(start, PERIOD_FORMATS[unit]).strftime(PERIOD_FORMATS[unit]) == start
                           and datetime.datetime.strptime(end, PERIOD_FORMATS[unit]).strftime(PERIOD_FORMATS[unit]) == end)
        except (KeyError, TypeError, ValueError):
            dates_valid = False
        if not pattern or not isinstance(start, str) or not isinstance(end, str) \
                or not re.fullmatch(pattern, start) or not re.fullmatch(pattern, end) or not dates_valid:
            raise SystemExit("기간 정밀도가 잘못됐다: %s" % d["name"])
        if end < start or not str(row.get("basis") or "").strip():
            raise SystemExit("기간 범위·근거가 잘못됐다: %s" % d["name"])
        d["period"] = {"start": start, "end": end, "granularity": unit,
                       "basis": row["basis"]}
        if "registrationSummary" in row:
            # O7 (사용자 서명 2026-09-25) — the md one-liner is replaced by the DATASETS.md
            # description the dev edit wrote, so a reseed reproduces the corrected dev text.
            text = row["registrationSummary"]
            if not isinstance(text, str) or not text.strip() or len(text) > SUMMARY_MAX_CHARS:
                raise SystemExit("등록 설명이 비었거나 %d자를 넘는다: %s" % (SUMMARY_MAX_CHARS, d["name"]))
            d["summary"] = text.strip()
        note = str(row.get("registrationNote") or "").strip()
        if note:
            d["summary"] = (str(d.get("summary") or "").strip() + " · " + note).strip(" ·")

    got_aux = {(x.get("child"), x.get("parent"), x.get("role"))
               for x in doc.get("auxiliaryParents") or []}
    if got_aux != EXPECTED_AUXILIARY:
        raise SystemExit("보조입력 대상은 Prediction (공간상세화)의 HLS·DEM·Aspect·LULC 네 건과 "
                         "pred_sample 의 rn15_sample 한 건이어야 한다")
    by_name = {d["name"]: d for d in datasets}
    for child, parent, role in got_aux:
        if child not in by_name or parent not in by_name[child].get("parents", []):
            raise SystemExit("보조입력 부모가 계획 계보에 없다: %s <- %s" % (child, parent))
        by_name[child].setdefault("parent_roles", {})[parent] = role
    return datasets


def _is_calendar_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d").strftime("%Y-%m-%d") == value
    except ValueError:
        return False


def bind_upload_classify(datasets, path=DEFAULT_CLASSIFY, allow_unsigned=False):
    """업로드 마법사 필수 칸 값을 계획 행에 싣는다 — 한 칸이라도 비면 행 이름을 대고 멈춘다.

    - ① 분류·유형(6705675d 부터 비어 시작 · 안 고르면 「다음 →」 비활성)
    - ② 관측 간격 숫자·단위 · ③ Lv0 출처 주소·내려받은 날(e171c5c2 부터 제출 시 필수)
    - 서명(`status: signed` ＋ `signedBy`·`signedOn`) 전이면 거절한다. `allow_unsigned` 는
      로컬 배관 시험 전용이고 `stage_seed`·preflight 는 넘기지 않는다.
    """
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit("업로드 필수 칸 값 파일을 읽지 못했다: %s" % path) from exc
    if doc.get("schema") != "colab-dev-seed-classify/1":
        raise SystemExit("업로드 필수 칸 값 스키마가 아니다: %s" % path)
    signed = (doc.get("status") == "signed" and str(doc.get("signedBy") or "").strip()
              and _is_calendar_date(doc.get("signedOn")))
    if not signed and not allow_unsigned:
        raise SystemExit("업로드 필수 칸 값이 서명 전이다(status=%s) — %s 의 표에 서명한 뒤 "
                         "status=signed·signedBy·signedOn 을 채운다: %s"
                         % (doc.get("status"), doc.get("document") or "제안 문서", path))
    rows = doc.get("datasets") or []
    by_key = {(x.get("seq"), x.get("name")): x for x in rows}
    if len(by_key) != len(rows):
        raise SystemExit("업로드 필수 칸 값에 seq/name 중복이 있다")
    expected = {(d["seq"], d["name"]) for d in datasets}
    if set(by_key) != expected:
        missing = sorted(name for _, name in expected - set(by_key))
        extra = sorted(name for _, name in set(by_key) - expected)
        raise SystemExit("업로드 필수 칸 값과 계획이 다르다: 누락=%s 초과=%s" % (missing, extra))
    bad = []
    for d in datasets:
        row = by_key[(d["seq"], d["name"])]
        name = d["name"]
        basis = row.get("basis") or {}
        interval = row.get("interval") or {}
        source = row.get("source")
        lv0 = d.get("processing_level") == "Lv0"
        if row.get("category") not in CATEGORIES:
            bad.append("%s · 분류 %r 가 5값 밖이다" % (name, row.get("category")))
        if row.get("dataType") not in DATA_TYPES:
            bad.append("%s · 유형 %r 가 6값 밖이다" % (name, row.get("dataType")))
        if not re.fullmatch(r"[1-9]\d*", str(interval.get("value") or "")) \
                or interval.get("unit") not in INTERVAL_UNITS:
            bad.append("%s · 관측 간격 %r 는 양의 정수와 %s 중 하나다" % (name, interval, "/".join(INTERVAL_UNITS)))
        if lv0:
            if not isinstance(source, dict) or not str(source.get("url") or "").strip() \
                    or not _is_calendar_date(source.get("downloadedOn")):
                bad.append("%s · Lv0 출처(주소·내려받은 날 YYYY-MM-DD)가 비었거나 틀렸다" % name)
        elif source is not None:
            bad.append("%s · Lv0 가 아닌 행에 출처를 두지 않는다(화면이 받지 않는 값)" % name)
        for axis in ("category", "dataType", "interval") + (("source",) if lv0 else ()):
            if not str(basis.get(axis) or "").strip():
                bad.append("%s · %s 근거가 비었다" % (name, axis))
    if bad:
        raise SystemExit("업로드 필수 칸 값이 틀렸다 — " + " / ".join(bad))
    for d in datasets:
        row = by_key[(d["seq"], d["name"])]
        d["category"] = row["category"]
        d["data_type"] = row["dataType"]
        d["observation_interval"] = {"value": str(row["interval"]["value"]),
                                     "unit": row["interval"]["unit"]}
        if d.get("processing_level") == "Lv0":
            d["source"] = {"url": row["source"]["url"].strip(),
                           "downloaded_on": row["source"]["downloadedOn"]}
    return datasets


def extract_block(text, where):
    """첫 줄에 `colab-datasets v1` 이 있는 ```yaml 블록 하나를 꺼낸다."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("```yaml"):
            body, j = [], i + 1
            while j < len(lines) and not lines[j].strip().startswith("```"):
                body.append(lines[j])
                j += 1
            if body and BLOCK_MARKER in body[0]:
                doc = yaml.safe_load("\n".join(body))
                if not isinstance(doc, dict) or not doc.get("datasets"):
                    raise SystemExit("기계 블록을 읽지 못했다: " + str(where))
                return doc
            i = j
        i += 1
    raise SystemExit("기계 블록(`%s`)이 없다: %s" % (BLOCK_MARKER, where))


def parse_table(text):
    """마크다운 표에서 이름 · 건수 · 바이트 · 미리보기 기대를 꺼낸다."""
    rows, idx, width = [], None, None
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if idx is None:
            if all(x in cells for x in ("이름", "건수", "바이트", "미리보기 기대")):
                idx = (cells.index("이름"), cells.index("건수"), cells.index("바이트"),
                       cells.index("미리보기 기대"))
                width = len(cells)
            continue
        if len(cells) != width or not cells[0].isdigit():
            continue
        rows.append((cells[idx[0]],
                     int(cells[idx[1]].replace(",", "")),
                     int(cells[idx[2]].replace(",", "")),
                     cells[idx[3]]))
    return rows


def cross_check(block, table, where):
    """표 ↔ 블록 — 행 수 · 이름 · 건수 · 바이트. 어긋난 행 이름을 돌려준다."""
    bad = []
    b_rows = [(str(d.get("name")), int(d["file_count"]), int(d["bytes"]),
               str(d.get("preview_expected") or "").strip())
              for d in block["datasets"]]
    if len(b_rows) != len(table):
        bad.append("%s 행 수 표=%d 블록=%d" % (where, len(table), len(b_rows)))
    for i, brow in enumerate(b_rows):
        if i >= len(table):
            bad.append("%s 표에 없는 행: %s" % (where, brow[0]))
            continue
        trow = table[i]
        if brow != trow:
            bad.append("%s 표=%s 블록=%s" % (brow[0], trow, brow))
    return bad


def resolve_rows(blocks, ref_root, resolve_files=True):
    """블록 행 → 계획 행. 반환 = (데이터셋 · 어긋난 행 · 없는 파일)."""
    mismatch, missing, datasets = [], [], []
    grid_paths = {(ref_root / b["folder"] / g).resolve()
                  for b in blocks for row in b["datasets"]
                  for g in (row.get("grid_files") or [])}
    for block in blocks:
        project = block.get("project_name") or block["project"]
        base = ref_root / block["folder"]
        for row in block["datasets"]:
            level = str(row.get("level") or "")
            if level not in LEVELS:
                raise SystemExit("제품 레벨 값이 아니다(seq %s · %s): %r"
                                 % (row.get("seq"), row.get("name"), level))
            preview_expected = str(row.get("preview_expected") or "").strip()
            if not preview_expected:
                raise SystemExit("미리보기 기대가 없다(seq %s · %s)"
                                 % (row.get("seq"), row.get("name")))
            if preview_expected == NO_PREVIEW_EXPECTATION and row.get("name") not in NO_PREVIEW_DATASETS:
                raise SystemExit("GeoPackage 미리보기 없음 기대를 다른 자료에 선언했다: %s"
                                 % row.get("name"))
            files, nbytes = [], 0
            grids = [str(base / g) for g in (row.get("grid_files") or [])]
            if resolve_files:
                for pat in row.get("files") or []:
                    files += glob.glob(str(base / pat))
                files = sorted(set(x for x in files
                                   if os.path.basename(x) != "desktop.ini"))
                mixed = [f for f in files if Path(f).resolve() in grid_paths]
                if mixed:
                    raise SystemExit("보조 격자를 본문으로 등록할 수 없다: seq=%s · %s · %s"
                                     % (row.get("seq"), row["name"], ", ".join(mixed)))
                nbytes = sum(os.path.getsize(f) for f in files if os.path.exists(f))
                if (len(files), nbytes) != (int(row["file_count"]), int(row["bytes"])):
                    mismatch.append((row["seq"], row["name"], int(row["file_count"]),
                                     len(files), int(row["bytes"]), nbytes))
                for f in files + grids:
                    if not os.path.exists(f):
                        missing.append(f)
            gbytes = sum(os.path.getsize(g) for g in grids if os.path.exists(g))
            datasets.append(dict(
                seq=int(row["seq"]), project=project, name=row["name"],
                summary=row.get("summary") or "", format=row.get("format") or "",
                processing_level=level,
                preview_expected=preview_expected,
                files=files, file_count=len(files), bytes=nbytes,
                grid_files=grids, grid_bytes=gbytes,
                grid_skip=(not (row.get("grid_files") or [])),
                parents=list(row.get("parents") or [])))
    return datasets, mismatch, missing


def check_order(datasets):
    """부모는 반드시 앞 순번 · 이름은 유일. 어긋나면 그 자리에서 멈춘다."""
    seen = dict()
    for d in sorted(datasets, key=lambda x: x["seq"]):
        for pn in d["parents"]:
            if pn not in seen:
                raise SystemExit("부모가 앞 순번에 없다: seq=%s parent=%s" % (d["seq"], pn))
        if d["name"] in seen:
            raise SystemExit("데이터셋 이름 중복: " + d["name"])
        seen[d["name"]] = d["seq"]


def build_manifest(blocks, datasets, edges, total_bytes):
    """사람이 읽는 등재표(생성물). 글롭은 참조자료 뿌리 기준으로 되돌려 적는다."""
    rows = []
    for block in blocks:
        project = block.get("project_name") or block["project"]
        folder = block["folder"]
        for row in block["datasets"]:
            rows.append(dict(
                seq=int(row["seq"]), project=project, name=row["name"],
                summary=row.get("summary") or "", format=row.get("format") or "",
                level=row["level"],
                preview_expected=str(row["preview_expected"]).strip(),
                globs=["%s/%s" % (folder, g) for g in (row.get("files") or [])],
                expect_files=int(row["file_count"]), expect_bytes=int(row["bytes"]),
                grid_files=["%s/%s" % (folder, g) for g in (row.get("grid_files") or [])],
                parents=list(row.get("parents") or [])))
    return dict(
        version=1,
        expected=dict(datasets=len(datasets), edges=len(edges), data_bytes=total_bytes),
        projects=[dict(key=b.get("project_name") or b["project"],
                       name=b.get("project_name") or b["project"],
                       description=b.get("project_description") or "")
                  for b in blocks],
        datasets=rows)


def md_declared_bytes(blocks):
    """md 블록이 선언한 총 바이트.

    생성기가 쓴 등재표의 `expected.data_bytes` 와 **같은 값이다** — 실물 합계가 블록 선언과
    다르면 생성기가 `MISMATCH` 로 비영 종료해 애초에 쓰지 않기 때문이다(`resolve_rows`).
    그래서 참조자료가 없는 자리에서도 등재표를 되만들어 대조할 수 있다.
    """
    return sum(int(row["bytes"]) for b in blocks for row in b["datasets"])


def render_manifest(blocks, datasets, edges, total_bytes):
    """등재표 파일 본문 — 쓰는 자리와 대조하는 자리가 **같은 한 줄**을 쓴다."""
    return MANIFEST_HEADER + yaml.safe_dump(
        build_manifest(blocks, datasets, edges, total_bytes),
        allow_unicode=True, sort_keys=False, width=120)


def check_manifest(blocks, manifest_path, expect_datasets, expect_edges, diff_lines=40):
    """커밋된 등재표가 md 재생성본과 같은가 — 참조자료 없이 판정한다. 아무것도 쓰지 않는다."""
    datasets, _, _ = resolve_rows(blocks, Path("."), resolve_files=False)
    check_order(datasets)
    edges = [dict(child=d["name"], parent=pn) for d in datasets for pn in d["parents"]]
    total_bytes = md_declared_bytes(blocks)
    print("datasets %d edges %d data_bytes %d" % (len(datasets), len(edges), total_bytes))
    print("expected datasets %s edges %s" % (expect_datasets, expect_edges))

    if len(datasets) != expect_datasets or len(edges) != expect_edges:
        print("COUNT-MISMATCH datasets=%d/%d edges=%d/%d"
              % (len(datasets), expect_datasets, len(edges), expect_edges))
        return 2
    if expect_datasets == EXPECT_DATASETS and expect_edges == EXPECT_EDGES:
        bind_canonical_metadata(datasets)
    if not manifest_path.exists():
        print("MANIFEST-MISSING " + str(manifest_path))
        return 5

    want = render_manifest(blocks, datasets, edges, total_bytes)
    have = manifest_path.read_text(encoding="utf-8")
    if want != have:
        print("MANIFEST-DRIFT " + str(manifest_path))
        diff = list(difflib.unified_diff(
            have.splitlines(), want.splitlines(),
            fromfile="등재표(커밋된 것)", tofile="md 로 다시 만든 것", lineterm="", n=1))
        for line in diff[:diff_lines]:
            print(line)
        if len(diff) > diff_lines:
            print("... 다른 줄 %d 개 더 있다" % (len(diff) - diff_lines))
        return 5

    print("등재표가 md 와 같다: " + str(manifest_path))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="DATASETS.md 4건 → 등재표 ＋ 업로드 계획")
    ap.add_argument("--md-root", default=None,
                    help="DATASETS.md 4건의 뿌리. 기본값 = 참조자료 뿌리")
    ap.add_argument("--ref-root", default=None,
                    help="참조자료 뿌리. 환경변수 COLAB_REF_ROOT 로도 준다")
    ap.add_argument("--work-dir", default=os.environ.get("COLAB_SEED_WORK_DIR"),
                    help="출력 자리. 기본값 = 이 폴더의 .work/")
    ap.add_argument("--out", default=None,
                    help="업로드 계획 파일. 기본값 = <work-dir>/upload-plan.json")
    ap.add_argument("--manifest-out", default=str(DEFAULT_MANIFEST_OUT),
                    help="등재표 생성물 자리")
    ap.add_argument("--expect-datasets", type=int, default=EXPECT_DATASETS,
                    help="총 데이터셋 수 기대값")
    ap.add_argument("--expect-edges", type=int, default=EXPECT_EDGES,
                    help="총 계보 간선 수 기대값")
    ap.add_argument("--check-manifest", action="store_true",
                    help="md 만으로 등재표를 되만들어 --manifest-out 의 것과 대조한다. "
                         "참조자료가 없어도 돌고 아무것도 쓰지 않는다")
    ap.add_argument("--allow-nondefault-expect", action="store_true",
                    help="기대값을 기본값에서 바꾼 채 생성물을 쓰는 것을 허용한다. "
                         "도구 폴더 밖을 가리키는 --out 과 함께 줘야 한다")
    ap.add_argument("--classify", default=str(DEFAULT_CLASSIFY),
                    help="업로드 필수 칸 값 파일(분류·유형·관측 간격·Lv0 출처)")
    ap.add_argument("--allow-unsigned-classify", action="store_true",
                    help="서명 전 제안값으로 계획을 쓴다 — 로컬 배관 시험 전용. dev 경로는 넘기지 않는다")
    ap.add_argument("--require-signed-classify", action="store_true",
                    help="--dry-run 에서도 업로드 필수 칸 값의 서명을 요구한다(preflight ⑽)")
    ap.add_argument("--dry-run", action="store_true",
                    help="파일을 쓰지 않고 계수만 출력. 뿌리가 없으면 블록 계수만 센다")
    args = ap.parse_args(argv)

    guard_bad = guard_nondefault_expect(args)
    if guard_bad:
        print("기대값이 기본값(datasets=%d edges=%d)과 다르다 — 생성물을 쓰지 않는다."
              % (EXPECT_DATASETS, EXPECT_EDGES))
        for b in guard_bad:
            print("EXPECT-GUARD " + b)
        print("판정만 하려면 --dry-run 을, 정말로 쓰려면 --allow-nondefault-expect 와 "
              "도구 폴더 밖의 --out(·--manifest-out)을 함께 준다.")
        return 4

    ref_root = resolve_ref_root(args.ref_root)
    md_root = Path(args.md_root).expanduser() if args.md_root else ref_root

    blocks, table_bad = [], []
    for rel in MD_RELATIVE:
        path = md_root / rel
        if not path.exists():
            print("DATASETS.md 가 없다: " + str(path), file=sys.stderr)
            return 2
        text = path.read_text(encoding="utf-8")
        block = extract_block(text, rel)
        table_bad += cross_check(block, parse_table(text), rel)
        blocks.append(block)

    if table_bad:
        print("표와 기계 블록이 어긋난다 — 계획을 쓰지 않는다")
        for b in table_bad:
            print("TABLE-MISMATCH " + b)
        return 3

    if args.check_manifest:
        return check_manifest(blocks, Path(args.manifest_out).expanduser(),
                              args.expect_datasets, args.expect_edges)

    resolve_files = ref_root.exists()
    if not resolve_files:
        msg = "참조자료 뿌리 없음: " + str(ref_root) + " — COLAB_REF_ROOT 로 준다"
        if not args.dry_run:
            print(msg, file=sys.stderr)
            return 2
        print("! " + msg + " (dry-run: 파일 해석 없이 블록 계수만 센다)")

    datasets, mismatch, missing = resolve_rows(blocks, ref_root, resolve_files)
    check_order(datasets)
    edges = []
    for d in datasets:
        for pn in d["parents"]:
            edges.append(dict(child=d["name"], parent=pn))
    if (len(datasets) == args.expect_datasets and len(edges) == args.expect_edges
            and args.expect_datasets == EXPECT_DATASETS and args.expect_edges == EXPECT_EDGES):
        bind_canonical_metadata(datasets)
        # 값 형상·28행 대응은 언제나 본다. **서명**은 계획을 쓸 때(seed ①)와
        # `--require-signed-classify`(preflight ⑽)에서만 요구한다 — `seed-plan-drift` 의 실물 대조
        # (`--dry-run`)는 md↔나무 판정이라 서명과 섞지 않는다.
        need_signed = (not args.dry_run) or args.require_signed_classify
        bind_upload_classify(datasets, args.classify,
                             allow_unsigned=args.allow_unsigned_classify or not need_signed)

    print("datasets %d edges %d" % (len(datasets), len(edges)))
    print("expected datasets %s edges %s" % (args.expect_datasets, args.expect_edges))
    print("missing_files %d row_mismatches %d" % (len(missing), len(mismatch)))
    for m in mismatch:
        print("MISMATCH seq=%s %s files expected=%s found=%s bytes expected=%s found=%s" % m)

    agg = defaultdict(lambda: [0, 0, 0, 0, 0])
    tot = [0, 0, 0, 0, 0]
    for d in datasets:
        a = agg[d["project"]]
        a[0] += 1
        a[1] += d["file_count"]
        a[2] += d["bytes"]
        a[3] += d["grid_bytes"]
        a[4] += len(d["parents"])
    for pk in [b.get("project_name") or b["project"] for b in blocks]:
        n, fc, b, gb, e = agg[pk]
        print("%s datasets=%d files=%d bytes=%d grid_bytes=%d edges=%d" % (pk, n, fc, b, gb, e))
        for i, v in enumerate((n, fc, b, gb, e)):
            tot[i] += v
    print("TOTAL datasets=%d files=%d bytes=%d grid_bytes=%d edges=%d load_sum=%d"
          % (tot[0], tot[1], tot[2], tot[3], tot[4], tot[2] + tot[3]))

    bad = False
    if len(datasets) != args.expect_datasets or len(edges) != args.expect_edges:
        print("COUNT-MISMATCH datasets=%d/%d edges=%d/%d"
              % (len(datasets), args.expect_datasets, len(edges), args.expect_edges))
        bad = True
    if resolve_files and (mismatch or missing):
        bad = True

    if args.dry_run:
        print("dry-run — 파일을 쓰지 않았다")
        return 2 if bad else 0
    if bad:
        print("계수 불일치 — 계획을 쓰지 않는다", file=sys.stderr)
        return 2

    manifest_out = Path(args.manifest_out).expanduser()
    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    manifest_out.write_text(
        MANIFEST_HEADER + yaml.safe_dump(
            build_manifest(blocks, datasets, edges, tot[2]),
            allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8")
    print("등재표 기록 = " + str(manifest_out))

    work_dir = Path(args.work_dir).expanduser() if args.work_dir else DEFAULT_WORK_DIR
    out = Path(args.out).expanduser() if args.out else work_dir / "upload-plan.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    plan = dict(
        projects=[dict(key=b.get("project_name") or b["project"],
                       name=b.get("project_name") or b["project"],
                       description=b.get("project_description") or "")
                  for b in blocks],
        datasets=datasets, edges=edges)
    out.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    print("계획 기록 = " + str(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
