"""Shared state bucket threaded through all cells.

On Colab, executing the notebook top-to-bottom is enough (global namespace persists).
Local development mirrors that by importing each cell as a module that reads/writes
this single `CTX` dict. Keeps every cell importable and testable in isolation.
"""
from __future__ import annotations

import os
from pathlib import Path

# - Project root.
ROOT = Path(__file__).resolve().parent.parent

# - Cell 01 fills these shared values.
CTX = {
    # - Drive state.
    "drive_root": None,        # Path to the config Drive folder on the local mount
    "config": None,            # parsed config.json as dict
    "blend_path": None,        # resolved Path to the .blend file
    "output_dir": None,        # resolved Path where renders are written

    # - Blender state.
    "blender_exe": None,       # Path to the installed blender executable
    "blender_version": None,   # normalized e.g. "4.2"

    # - Scene and render state.
    "bpy": None,               # the bpy module (only set while blender is running)
    "scene": None,
}

# - Optional environment overrides support Colab and local runs.
ENV = {
    "CONFIG_PATH": os.environ.get("RENDERER_CONFIG_PATH"),
    "DRIVE_ROOT": os.environ.get("RENDERER_DRIVE_ROOT"),
}
