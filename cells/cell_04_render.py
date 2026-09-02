"""CELL 04 - Render coordinator (outer Python, orchestrates Blender).

Writes the BPY driver script (from cell 03) to a temp file, then executes:
    blender --background --python driver.py

with environment variables pointing at the config, blend, and output. Render is
single-image (still) or frame-by-frame (animation); user combines frames to a
video later, which is out of scope.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from ._state import CTX, ROOT
from . import cell_03_bpy_bootstrap as bootstrap


def _write_driver() -> str:
    fd, path = tempfile.mkstemp(suffix=".py", prefix="bpy_driver_")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(bootstrap.build_script())
    return path


def _inner_env() -> dict:
    return {
        "RENDERER_CONFIG_PATH": str(CTX["config_src_path"]),
        "RENDERER_BLEND_PATH": str(CTX["blend_path"]),
        "RENDERER_OUTPUT_DIR": str(CTX["output_dir"]),
    }


def ensure_config_src_path() -> Path:
    """Track where config.json actually lives (drive root or repo)."""
    p = CTX.get("config_src_path")
    if not p:
        p = CTX.get("drive_root", ROOT / "config") / "config.json"
        CTX["config_src_path"] = p
    return p


def render(preview: bool = False) -> dict:
    blender_exe = CTX.get("blender_exe")
    if not blender_exe:
        raise RuntimeError("Call cell 02 (install blender) before cell 04.")
    ensure_config_src_path()

    driver = _write_driver()
    env = dict(os.environ)
    env.update(_inner_env())

    cmd = [blender_exe, "--background", "--python", driver]
    if preview:
        cmd += ["--render-output", str(CTX["output_dir"]), "--render-frame", "1"]
    print(f"[cell04] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"Blender render failed with code {result.returncode}")
    return {"output_dir": str(CTX["output_dir"])}


if __name__ == "__main__":
    import json
    result = render()
    print(json.dumps(result, indent=2))
