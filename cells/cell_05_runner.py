"""CELL 05 - Orchestration runner (local).

Mirrors Colab cell-by-cell execution locally. Runs cells 01..04 in order and returns
a summary. This is the entry point we use to develop/test before deploying to Colab.

Usage:
    python -m cells.run_pipeline --engine cycles --mode still --samples 64
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# - Keep repo-root imports working.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cells import _state
from cells import cell_01_drive_config as cell01
from cells import cell_02_blender as cell02
from cells import cell_03_bpy_bootstrap as cell03
from cells import cell_04_render as cell04

CELLS = [cell01, cell02, cell03, cell04]


def _apply_overrides(overrides: dict) -> None:
    if not overrides:
        return
    cfg = _state.CTX.get("config") or {}
    for section, key, value in overrides:
        cfg.setdefault(section, {})[key] = value
    _state.CTX["config"] = cfg


def run(overrides: list = None) -> dict:
    """Execute the pipeline cell-by-cell."""
    _apply_overrides(overrides or [])
    summary = {}

    # - Resolve Drive, config, and files.
    r1 = cell01.run()
    summary["cell01"] = r1

    # - Install Blender.
    r2 = cell02.install()
    summary["cell02"] = {"blender_exe": r2}

    # - Build the Blender driver.
    assert cell03.build_script()

    # - Render the scene.
    r4 = cell04.render()
    summary["cell04"] = r4

    summary["blend"] = str(_state.CTX["blend_path"])
    summary["output"] = str(_state.CTX["output_dir"])
    return summary


def parse_overrides(argv) -> list:
    """Turn CLI flags like --engine cycles into override triples."""
    p = argparse.ArgumentParser(description="Run the local Blender cloud-renderer pipeline")
    p.add_argument("--engine", choices=["cycles", "blender_eevee", "eevee_next"])
    p.add_argument("--mode", choices=["still", "animation"])
    p.add_argument("--samples", type=int)
    p.add_argument("--frame-start", type=int, dest="frame_start")
    p.add_argument("--frame-end", type=int, dest="frame_end")
    p.add_argument("--frame-step", type=int, dest="frame_step")
    p.add_argument("--major-minor", dest="major_minor")
    args = vars(p.parse_args(argv))

    specs = {
        "engine": ("render", "engine"),
        "samples": ("render", "samples"),
        "frame_start": ("render", "frame_start"),
        "frame_end": ("render", "frame_end"),
        "frame_step": ("render", "frame_step"),
        "mode": ("render", "mode"),
        "major_minor": ("blender", "major_minor"),
    }
    out = []
    for k, v in args.items():
        if v is not None and k in specs:
            sec, key = specs[k]
            out.append((sec, key, v))
    return out


if __name__ == "__main__":
    overrides = parse_overrides(sys.argv[1:])
    result = run(overrides)
    print(json.dumps(result, indent=2, default=str))
