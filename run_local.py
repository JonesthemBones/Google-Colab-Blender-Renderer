"""Convenience entry point for local runs.

Usage:
    python run_local.py
    python run_local.py --engine cycles --mode animation --samples 64
    python run_local.py --major-minor 4.2
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cells.cell_05_runner import parse_overrides, run  # noqa: E402

if __name__ == "__main__":
    overrides = parse_overrides(sys.argv[1:])
    result = run(overrides)
    print(json.dumps(result, indent=2, default=str))
