"""artifact-ownership 게이트의 계수기 — **판정 규칙을 여기서 다시 적지 않는다.**

판정 규칙의 정본은 `services/viz-render/.../d7_visualization/ownership.py` 하나다.
이 파일은 그 모듈을 **경로로 그대로 실어** 쓴다 — 게이트가 자기 사본을 들면 그것이 세 번째
규칙이 되고, 그때부터 게이트와 런타임이 다른 답을 낸다(`03-HANDOFF §4 #20` 의 무늬).

⚠ **패키지로 import 하지 않는다** — `colab_viz` 를 import 하면 numpy·rasterio 가 딸려 오고
  게이트 환경에는 그것이 없다. `ownership.py` 는 **표준 라이브러리만** 쓰도록 지어져 있어
  파일 하나만 실을 수 있다. 그 성질이 깨지면 여기서 즉시 드러난다(ImportError).

입출력 — stdin 없음. 인자 넷:
  1 자리(미리보기 루트) · 2 d3_file.id 목록 파일 · 3 d5_upload_file.id 목록 파일 · 4 스냅숏 출력 경로
출력 — `::계수::<등급>\t<건수>` · `::고아::<키>` · `::구판::<건수>` · `::스냅숏::<줄수>`
"""
from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC = REPO_ROOT / "services/viz-render/src/colab_viz/domains/d7_visualization/ownership.py"


def _load_rule():
    if not _SRC.is_file():
        print(f"::error::판정 규칙 정본이 없다: {_SRC.relative_to(REPO_ROOT)}", file=sys.stderr)
        raise SystemExit(2)
    spec = importlib.util.spec_from_file_location("colab_ownership_rule", _SRC)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    # ⚠ `sys.modules` 에 먼저 꽂아야 한다 — `dataclasses` 가 필드 타입을 풀 때 모듈을
    #   이름으로 되찾아 본다. 안 꽂으면 `@dataclass` 정의에서 AttributeError 가 난다.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)      # 의존이 붙었으면 여기서 터진다 — 조용히 넘어가지 않는다
    return mod


def _ids(path: str) -> frozenset[str]:
    return frozenset(x.strip() for x in Path(path).read_text(encoding="utf-8").splitlines()
                     if x.strip())


def main(argv: list[str]) -> int:
    slot, d3_path, d5_path, snap_path = argv[1], argv[2], argv[3], argv[4]
    own = _load_rule()

    ledger = own.Ledger(dataset_files=_ids(d3_path), upload_files=_ids(d5_path))
    if ledger.is_structurally_empty():
        # 부르는 쪽(셸)이 이미 막지만 **두 번 막는다** — 이 0 을 「없다」로 읽은 오판이 실재했다.
        print("::원장공백::1")
        return 0

    groups = own.scan(Path(slot))
    tiles = [g for g in groups if g.is_map_tile()]
    subjects = [g for g in groups if not g.is_map_tile()]

    try:
        t = own.tally(subjects, ledger)
    except own.SidecarContractViolation as e:
        print(f"::규약위반::{e}")
        return 0

    for name in own.GRADES:
        print(f"::계수::{name}\t{t.counts[name]}")
    print(f"::대상::{len(subjects)}")
    print(f"::지도타일::{len(tiles)}")     # **대상이 아니다** — `kept` 로 산다 (완료 정의 ⑷)
    for key in own.orphan_keys(subjects, ledger):
        print(f"::고아::{key}")

    # **회수보다 먼저** 남긴다 — 지운 뒤에 「무엇이 있었나」를 답할 유일한 기록이다 (완료 정의 ⑸)
    rows = own.snapshot_rows(groups, ledger)
    out = Path(snap_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["cache_key", "extension", "size_bytes",
                                           "source", "grade"], delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    print(f"::스냅숏::{len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
