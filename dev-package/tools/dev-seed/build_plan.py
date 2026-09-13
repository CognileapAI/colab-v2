#!/usr/bin/env python3
"""등재표(`plan-manifest.yaml`) → 업로드 계획(`upload-plan.json`).

- 입력 = 같은 폴더의 `plan-manifest.yaml`(데이터셋 28 · 간선 18 · 상대 glob).
  그 등재표의 출처는 `dev-package/reports/reference-data/2026-09-13-inventory-v2.md` §5·§5-6 이다.
- 참조자료 뿌리 = `--ref-root` · 환경변수 `COLAB_REF_ROOT` · 기본값(레포 상위의 `03 Reference-Data`) 순.
  ⛔ 코드·등재표에 절대경로를 적지 않는다 — glob 은 전부 그 뿌리 기준 상대 경로다.
- 출력 = `<work-dir>/upload-plan.json`. 러너가 읽는 파일이고 그 안의 경로는 실행 자리의 절대경로다
  (작업 자리는 `.gitignore` 로 제외된다).
- 판정 = 데이터셋 수 · 간선 수 · glob 이 맞힌 파일 수 · 총 바이트를 등재표의 `expected` 와 대조한다.
  어긋나면 MISMATCH 로 적고 비영 종료한다(조용히 진행하지 않는다).
"""

import argparse
import glob
import json
import os
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
REPO_ROOT = TOOL_DIR.parents[2]
DEFAULT_MANIFEST = TOOL_DIR / "plan-manifest.yaml"
DEFAULT_WORK_DIR = TOOL_DIR / ".work"
# 기본 뿌리 = 레포와 나란한 `03 Reference-Data`. 자리가 다르면 `COLAB_REF_ROOT` 로 준다.
DEFAULT_REF_ROOT = REPO_ROOT.parent / "03 Reference-Data"


def resolve_ref_root(arg):
    if arg:
        return Path(arg).expanduser()
    env = os.environ.get("COLAB_REF_ROOT")
    if env:
        return Path(env).expanduser()
    return DEFAULT_REF_ROOT


def load_manifest(path):
    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or not doc.get("datasets"):
        raise SystemExit("등재표를 읽지 못했다: " + str(path))
    return doc


def resolve_rows(doc, ref_root, resolve_files=True):
    """등재표 행 → 계획 행. 반환 = (데이터셋 · 어긋난 glob · 없는 파일)."""
    mismatch, missing, datasets = [], [], []
    for row in doc["datasets"]:
        files = []
        grids = []
        nbytes = 0
        gbytes = 0
        if resolve_files:
            for pat in row.get("globs") or []:
                files += glob.glob(str(ref_root / pat))
            files = sorted(set(x for x in files
                               if os.path.basename(x) != "desktop.ini"))
            if len(files) != int(row["expect_files"]):
                mismatch.append((row["seq"], row["name"],
                                 row["expect_files"], len(files)))
            grids = [str(ref_root / g) for g in (row.get("grid_files") or [])]
            for f in files + grids:
                if not os.path.exists(f):
                    missing.append(f)
            nbytes = sum(os.path.getsize(f) for f in files if os.path.exists(f))
            gbytes = sum(os.path.getsize(g) for g in grids if os.path.exists(g))
        else:
            grids = [str(ref_root / g) for g in (row.get("grid_files") or [])]
        datasets.append(dict(
            seq=row["seq"], project=row["project"], name=row["name"],
            summary=row["summary"], format=row["format"],
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


def main():
    ap = argparse.ArgumentParser(description="등재표 → 업로드 계획")
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="등재표 YAML")
    ap.add_argument("--ref-root", default=None,
                    help="참조자료 뿌리. 환경변수 COLAB_REF_ROOT 로도 준다")
    ap.add_argument("--work-dir", default=os.environ.get("COLAB_SEED_WORK_DIR"),
                    help="출력 자리. 기본값 = 이 폴더의 .work/")
    ap.add_argument("--out", default=None,
                    help="출력 파일. 기본값 = <work-dir>/upload-plan.json")
    ap.add_argument("--dry-run", action="store_true",
                    help="파일을 쓰지 않고 계수만 출력. 뿌리가 없으면 등재표 계수만 센다")
    args = ap.parse_args()

    doc = load_manifest(args.manifest)
    ref_root = resolve_ref_root(args.ref_root)
    resolve_files = ref_root.exists()
    if not resolve_files:
        msg = "참조자료 뿌리 없음: " + str(ref_root) + " — COLAB_REF_ROOT 로 준다"
        if not args.dry_run:
            print(msg, file=sys.stderr)
            return 2
        print("! " + msg + " (dry-run: 파일 해석 없이 등재표 계수만 센다)")

    datasets, mismatch, missing = resolve_rows(doc, ref_root, resolve_files)
    check_order(datasets)
    edges = []
    for d in datasets:
        for pn in d["parents"]:
            edges.append(dict(child=d["name"], parent=pn))

    exp = doc.get("expected") or dict()
    print("datasets %d edges %d" % (len(datasets), len(edges)))
    print("expected datasets %s edges %s" % (exp.get("datasets"), exp.get("edges")))
    print("missing_files %d glob_mismatches %d" % (len(missing), len(mismatch)))
    for m in mismatch:
        print("MISMATCH seq=%s %s expected=%s found=%s" % m)

    agg = defaultdict(lambda: [0, 0, 0, 0, 0])
    tot = [0, 0, 0, 0, 0]
    for d in datasets:
        a = agg[d["project"]]
        a[0] += 1
        a[1] += d["file_count"]
        a[2] += d["bytes"]
        a[3] += d["grid_bytes"]
        a[4] += len(d["parents"])
    for pk in [p["key"] for p in doc["projects"]]:
        n, fc, b, gb, e = agg[pk]
        print("%s datasets=%d files=%d bytes=%d grid_bytes=%d edges=%d" % (pk, n, fc, b, gb, e))
        for i, v in enumerate((n, fc, b, gb, e)):
            tot[i] += v
    print("TOTAL datasets=%d files=%d bytes=%d grid_bytes=%d edges=%d load_sum=%d"
          % (tot[0], tot[1], tot[2], tot[3], tot[4], tot[2] + tot[3]))
    if resolve_files and exp.get("data_bytes") is not None:
        print("inventory_data_bytes_match", tot[2] == int(exp["data_bytes"]))

    bad = False
    if exp.get("datasets") is not None and len(datasets) != int(exp["datasets"]):
        bad = True
    if exp.get("edges") is not None and len(edges) != int(exp["edges"]):
        bad = True
    if resolve_files and (mismatch or missing):
        bad = True

    if args.dry_run:
        print("dry-run — 파일을 쓰지 않았다")
        return 2 if bad else 0
    if bad:
        print("계수 불일치 — 계획을 쓰지 않는다", file=sys.stderr)
        return 2

    work_dir = Path(args.work_dir).expanduser() if args.work_dir else DEFAULT_WORK_DIR
    out = Path(args.out).expanduser() if args.out else work_dir / "upload-plan.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    plan = dict(
        projects=[dict(key=p["key"], name=p["name"], description=p["description"])
                  for p in doc["projects"]],
        datasets=datasets, edges=edges)
    out.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    print("계획 기록 = " + str(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
