"""Compatibility import and CLI for the shared lifecycle implementation."""
from pathlib import Path
import runpy

_source = Path(__file__).resolve().parents[2] / "scripts/harness/hooks/lifecycle_contract.py"
globals().update(runpy.run_path(str(_source), run_name=__name__))
