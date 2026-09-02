"""Shared state bucket threaded through all cells.

On Colab, executing the notebook top-to-bottom is enough (global namespace persists).
Local development mirrors that by importing each cell as a module that reads/writes
this single `CTX` dict. Keeps every cell importable and testable in isolation.
"""
from __future__ import annotations

import os
from pathlib import Path

# Root of this project (repo root).
ROOT = Path(__file__).resolve().parent.parent

# Cell 01 fills these. Every later cell reads them.
CTX = {
    # --- drive (cell 01) ---
    "drive_root": None,        # Path to the config Drive folder on the local mount
    "config": None,            # parsed config.json as dict
    "blend_path": None,        # resolved Path to the .blend file
    "output_dir": None,        # resolved Path where renders are written

    # --- blender install (cell 02) ---
    "blender_exe": None,       # Path to the installed blender executable
    "blender_version": None,   # normalized e.g. "4.2"

    # --- scene / rendering (cell 03-04) ---
    "bpy": None,               # the bpy module (only set while blender is running)
    "scene": None,
}

# Optional env override so the same code can run on Colab and locally.
# On Colab the drive mount path is a runtime value; on local we default to
# repo/config/config.json unless TESTS set these.
ENV = {
    "CONFIG_PATH": os.environ.get("RENDERER_CONFIG_PATH"),
    "DRIVE_ROOT": os.environ.get("RENDERER_DRIVE_ROOT"),
}
