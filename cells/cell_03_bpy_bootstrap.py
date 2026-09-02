"""CELL 03 - Headless scene bootstrap (runs INSIDE Blender).

Design: Blender renders best in --background mode with a standalone .py script.
Cells 03 + 04 together BUILD that script (as a string -> .py file), then execute
`blender --background --python <script>` as a subprocess.

This cell is the BPY-side driver: it loads the .blend, applies config, and sets up
the render job. It reads everything from environment variables passed in by the
subprocess (config path, blend path, output dir).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

# - Expose results to the outer coordinator.
RENDER_META = {}


def _load_config() -> dict:
    cfg_path = os.environ["RENDERER_CONFIG_PATH"]
    with open(cfg_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def build_script() -> str:
    """Return the full Python source that Blender runs headless.

    Marked as the BPY driver. On Colab this same string is written to a temp .py
    and invoked with `blender --background --python script.py`.
    """
    return _BPY_SCRIPT


_BPY_SCRIPT = r'''
"""Runs inside Blender (--background). Loads scene, configures renderer, renders."""
import json
import os
from pathlib import Path

import bpy

cfg_path = os.environ["RENDERER_CONFIG_PATH"]
blend_path = os.environ["RENDERER_BLEND_PATH"]
out_dir = os.environ["RENDERER_OUTPUT_DIR"]

with open(cfg_path, "r", encoding="utf-8") as fh:
    cfg = json.load(fh)

render_cfg = cfg["render"]
engine = render_cfg["engine"]
mode = render_cfg["mode"]

# - Load the scene.
if os.path.exists(blend_path):
    bpy.ops.wm.open_mainfile(filepath=blend_path)
    print(f"[bpy] loaded scene from {blend_path}")
else:
    raise FileNotFoundError(f"blend not found: {blend_path}")

scene = bpy.context.scene
rd = scene.render

# - Set the resolution.
rd.resolution_percentage = int(render_cfg.get("resolution_percentage", 100))

# - Set the render engine.
if engine == "cycles":
    rd.engine = "CYCLES"
else:
    for eevee_engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            rd.engine = eevee_engine
            break
        except TypeError:
            continue
    else:
        raise RuntimeError("This Blender build does not provide an Eevee engine")

ismetabolic = rd.engine == "CYCLES"
if ismetabolic:
    cy = scene.cycles
    cy.samples = int(render_cfg.get("samples", 128))
    # - Select the GPU device.
    use_gpu = render_cfg.get("use_gpu", True)
    prefs = bpy.context.preferences.addons["cycles"].preferences
    try:
        prefs.compute_device_type = "CUDA" if use_gpu else "NONE"
    except Exception:
        prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for dev in prefs.devices:
        dev.use = use_gpu
    try:
        scene.cycles.device = "GPU" if use_gpu else "CPU"
    except Exception:
        pass
    rd.use_file_extension = True
else:
    # - Configure Eevee.
    samples = int(render_cfg.get("samples", 64))
    for property_name in ("taa_render_samples", "taa_samples"):
        if hasattr(scene.eevee, property_name):
            setattr(scene.eevee, property_name, samples)
            break

# - Configure output.
Path(out_dir).mkdir(parents=True, exist_ok=True)
fmt = render_cfg.get("file_format", "PNG")
rd.filepath = str(Path(out_dir) / "frame_")

if mode == "still":
    # - Set the still-render frame.
    scene.frame_set(int(render_cfg.get("frame_start", 1)))
    rd.filepath = str(Path(out_dir) / "render")
    rd.image_settings.file_format = fmt
    if "color_mode" in render_cfg:
        rd.image_settings.color_mode = render_cfg["color_mode"]
    bpy.ops.render.render(write_still=True)
    print(f"[bpy] rendered still frame {scene.frame_current}")
else:
    # - Render animation frames as PNG files.
    fstart = int(render_cfg.get("frame_start", scene.frame_start))
    fend = int(render_cfg.get("frame_end", scene.frame_end))
    fstep = int(render_cfg.get("frame_step", 1))
    rd.image_settings.file_format = fmt
    if "color_mode" in render_cfg:
        rd.image_settings.color_mode = render_cfg["color_mode"]
    for f in range(fstart, fend + 1, fstep):
        scene.frame_set(f)
        rd.filepath = str(Path(out_dir) / f"frame_{f:05d}.{fmt.lower()}")
        bpy.ops.render.render(write_still=True)
        print(f"[bpy] rendered frame {f}")

print("[bpy] DONE")
'''


def run_outer() -> None:
    """Outer-side helper: not used when executing inside Blender."""
    print("This module installs the BPY render driver. Run via 04_render.py.")
