#!/usr/bin/env python3
"""Validate the shared harness contract and its repository surface."""

import argparse
from pathlib import Path
import sys

from config import ContractError, check_contract, load_contract


ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--contract", type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    contract = args.contract or root / ".agents/harness.yaml"
    try:
        value = load_contract(contract)
    except ContractError as exc:
        print(f"::gate-readiness-failure:: harness-contract: {exc}", file=sys.stderr)
        return 78
    errors = check_contract(root, value)
    if errors:
        for error in errors:
            print(f"red(판정): {error}", file=sys.stderr)
        return 1
    print(
        "green: shared harness contract; "
        f"required gates {len(value['gates']['required'])}, "
        f"adapters {len(value['adapters']['required_files'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
