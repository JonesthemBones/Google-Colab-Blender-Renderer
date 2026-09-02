"""CELL 04 - Render coordinator (outer Python, orchestrates Blender).

Writes the BPY driver script (from cell 03) to a temp file, then executes:
    blender --background --python driver.py

with environment variables pointing at the config, blend, and output. Render is
single-image (still) or frame-by-frame (animation); user combines frames to a
video later, which is out of scope.
"""
from __future__ import annotations

import os
import platform
import re
import shutil
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


def _run_blender(cmd: list, env: dict) -> int:
    """Relay Blender output and summarize its per-sample progress."""
    sample_pattern = re.compile(r"Rendering\s+(\d+)\s*/\s*(\d+)\s+samples")
    process = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None
    for line in process.stdout:
        line = line.rstrip()
        match = sample_pattern.search(line)
        if match:
            current, total = (int(value) for value in match.groups())
            print(f"[render] Samples: {current}/{total} ({total - current} remaining)", flush=True)
        elif line:
            print(line, flush=True)
    return process.wait()


def render(preview: bool = False) -> dict:
    blender_exe = CTX.get("blender_exe")
    if not blender_exe:
        raise RuntimeError("Call cell 02 (install blender) before cell 04.")
    ensure_config_src_path()

    driver = _write_driver()
    env = dict(os.environ)
    env.update(_inner_env())

    cmd = [blender_exe, "--background", "--python", driver]
    engine = str((CTX.get("config") or {}).get("render", {}).get("engine", "eevee")).strip().lower()
    render_config = (CTX.get("config") or {}).get("render", {})
    if engine == "cycles" and render_config.get("use_gpu", True):
        cmd += ["--", "--cycles-device", "CUDA"]
    if platform.system() == "Linux" and engine in {"eevee", "blender_eevee", "eevee_next"}:
        env["__NV_PRIME_RENDER_OFFLOAD"] = "1"
        env["__GLX_VENDOR_LIBRARY_NAME"] = "nvidia"
        xvfb = shutil.which("xvfb-run")
        if xvfb:
            cmd = [xvfb, "-a", "-s", "-screen 0 1920x1080x24"] + cmd
    if preview:
        cmd += ["--render-output", str(CTX["output_dir"]), "--render-frame", "1"]
    print(f"[cell04] Running: {' '.join(cmd)}")
    print(f"[cell04] Engine: {engine}")
    if platform.system() == "Linux" and engine in {"eevee", "blender_eevee", "eevee_next"}:
        print("[cell04] Eevee GPU routing: NVIDIA OpenGL via xvfb")
    print(f"[cell04] Output: {CTX['output_dir']}")
    print("[cell04] Rendering; Blender progress will be shown below.", flush=True)
    returncode = _run_blender(cmd, env)
    if returncode != 0:
        raise RuntimeError(f"Blender render failed with code {returncode}")
    return {"output_dir": str(CTX["output_dir"])}


if __name__ == "__main__":
    import json
    result = render()
    print(json.dumps(result, indent=2))
