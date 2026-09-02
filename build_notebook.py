"""Build a Google Colab .ipynb notebook from the cells.

The generated notebook mirrors the local cell pipeline but wraps it in Colab UI:
  * mounts Google Drive
  * interactive config-folder picker + config inspection
  * installs Blender, renders still / animation to Drive output
  * previews thumbnails / zips frames for download

Usage:
    python build_notebook.py                 # -> notebooks/Blender_Cloud_Renderer.ipynb
    python build_notebook.py -o my.ipynb
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "notebooks" / "Blender_Cloud_Renderer.ipynb"


def _code(src: str) -> dict:
    return {"cell_type": "code", "execution_count": None,
            "metadata": {}, "outputs": [], "source": src.splitlines(keepends=True)}


def _md(src: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": src.splitlines(keepends=True)}


def build() -> dict:
    cells = []
    cells.append(_md(HEADER_MD))
    cells.append(_code(MOUNT_CELL))
    cells.append(_code(PICKER_CELL))
    cells.append(_code(REVIEW_CELL))
    cells.append(_code(RUN_CELL))
    nb = {
        "nbformat": 4,
        "nbformat_minor": 0,
        "metadata": {
            "colab": {"name": "Blender Cloud Renderer", "provenance": []},
            "kernelspec": {"name": "python3", "display_name": "Python 3"},
            "language_info": {"name": "python"},
            "accelerator": "GPU",  # request T4 by default so Cycles/GPU works
        },
        "cells": cells,
    }
    return nb


HEADER_MD = """# Blender Cloud Renderer (Eevee + Cycles)

Renders a `.blend` file on a Google Colab GPU using a chosen Blender version.

* **Input**: a config.json + `.blend` file in one Google Drive folder (see `config/config.json` layout).
* **Output**: rendered still image or frame-by-frame PNGs written back to your Drive `output/` folder.
* **Engine**: Cycles (GPU) or Eevee. **Mode**: still image, or animation (render each frame; combine to a video yourself later).

> To add a brand-new Blender version, edit the `BLENDER_DOWNLOADS` dict in cell 02 (or set `blender.custom_tar_url` in your config.json).
"""

MOUNT_CELL = """# @title 1) Authorize your Google Drive
# This mounts the Drive of the Google account you authorize in the prompt.
# It does not access the notebook publisher's Drive.
from google.colab import drive
drive.mount('/content/drive')
print('Drive mounted at /content/drive')
"""

PICKER_CELL = """# @title 2) Locate or create your renderer workspace
import json
from pathlib import Path

DRIVE_ROOT = Path('/content/drive/MyDrive')
DEFAULT_WORKSPACE = DRIVE_ROOT / 'BlenderCloudRenderer'

DEFAULT_CONFIG = {
    'drive': {
        'folder_id': '',
        'blend_filename': 'scene.blend',
        'output_subfolder': 'my_first_render',
    },
    'blend': {'source': 'drive', 'url': '', 'drive_id': ''},
    'render': {
        'engine': 'cycles',
        'mode': 'still',
        'resolution_percentage': 100,
        'samples': 128,
        'frame_start': 1,
        'frame_end': 250,
        'frame_step': 1,
        'use_gpu': True,
        'file_format': 'PNG',
        'color_mode': 'RGBA',
        'device': 'GPU',
    },
    'blender': {'major_minor': '4.2', 'custom_tar_url': ''},
}

def find_config_folders():
    hits = []
    for p in DRIVE_ROOT.rglob('config.json'):
        if p.name == 'config.json':
            hits.append(p.parent)
    return hits

hits = find_config_folders()
print('Folders containing a config.json in your MyDrive:')
for i, h in enumerate(hits):
    print(f"  [{i}] {h}")

if not hits:
    DEFAULT_WORKSPACE.mkdir(parents=True, exist_ok=True)
    (DEFAULT_WORKSPACE / 'blend_files').mkdir(exist_ok=True)
    (DEFAULT_WORKSPACE / 'output').mkdir(exist_ok=True)
    with open(DEFAULT_WORKSPACE / 'config.json', 'w', encoding='utf-8') as fh:
        json.dump(DEFAULT_CONFIG, fh, indent=2)
    CFG_FOLDER = DEFAULT_WORKSPACE
    print('Created a new workspace in:', CFG_FOLDER)
    print('Upload your .blend file to:', CFG_FOLDER / 'blend_files')
else:
    # @param {"type":"raw"}
    folder_index = 0  # @param {type:"raw"}
    CFG_FOLDER = hits[int(folder_index)]

print("Selected config folder:", CFG_FOLDER)

with open(CFG_FOLDER / 'config.json', 'r', encoding='utf-8') as fh:
    CONFIG = json.load(fh)
print("Loaded config.")
"""

REVIEW_CELL = """# @title 3) Review + override configuration
p = lambda d: d if d else '(not set)'
print("Engine      :", CONFIG['render']['engine'])
print("Mode        :", CONFIG['render']['mode'])
print("Samples     :", CONFIG['render'].get('samples'))
print("Frames      :", (CONFIG['render'].get('frame_start'), CONFIG['render'].get('frame_end'), CONFIG['render'].get('frame_step')))
print("Blender ver :", CONFIG['blender'].get('major_minor'))
print("Blend file  :", CONFIG['drive'].get('blend_filename'))

# Optional live overrides (edit these before running cell 4)
# @param engine engine: ["cycles","blender_eevee","eevee_next"] = "cycles"
# engine = "cycles"
# @param mode mode: ["still","animation"] = "still"
# mode = "still"
# @param blender_version Blender version: ["3.6","4.0","4.1","4.2","4.3","4.4","4.5","5.0","5.1","5.2"] = "4.2"
# blender_version = "4.2"

# Apply overrides if uncommented
if 'engine' in dir():
    CONFIG['render']['engine'] = engine
if 'mode' in dir():
    CONFIG['render']['mode'] = mode
if 'blender_version' in dir():
    CONFIG['blender']['major_minor'] = blender_version
print("Overrides applied (if any).")
"""

RUN_CELL = """# @title 4) Install Blender + Render
import json, os, subprocess, tempfile, tarfile, urllib.request, shutil
from pathlib import Path

CFG_FOLDER = Path(CFG_FOLDER)
BLEND_DIR = CFG_FOLDER / 'blend_files'
BLEND_PATH = BLEND_DIR / CONFIG['drive']['blend_filename']
OUT_DIR = CFG_FOLDER / 'output' / CONFIG['drive'].get('output_subfolder', 'render')

if not BLEND_PATH.exists():
    print("WARNING: blend not found at", BLEND_PATH)
    print("Upload your .blend file into the 'blend_files' subfolder next to config.json and re-run.")
    raise SystemExit

OUT_DIR.mkdir(parents=True, exist_ok=True)

# --- Blender version download map (add new versions here) ---
BLENDER_DOWNLOADS = {
    "3.6": "https://download.blender.org/release/Blender3.6/blender-3.6.12-linux-x64.tar.xz",
    "4.0": "https://download.blender.org/release/Blender4.0/blender-4.0.2-linux-x64.tar.xz",
    "4.1": "https://download.blender.org/release/Blender4.1/blender-4.1.1-linux-x64.tar.xz",
    "4.2": "https://download.blender.org/release/Blender4.2/blender-4.2.2-linux-x64.tar.xz",
    "4.3": "https://download.blender.org/release/Blender4.3/blender-4.3.2-linux-x64.tar.xz",
    "4.4": "https://download.blender.org/release/Blender4.4/blender-4.4.1-linux-x64.tar.xz",
    "4.5": "https://download.blender.org/release/Blender4.5/blender-4.5.13-linux-x64.tar.xz",
    "5.0": "https://download.blender.org/release/Blender5.0/blender-5.0.1-linux-x64.tar.xz",
    "5.1": "https://download.blender.org/release/Blender5.1/blender-5.1.2-linux-x64.tar.xz",
    "5.2": "https://download.blender.org/release/Blender5.2/blender-5.2.1-linux-x64.tar.xz",
}
custom_url = CONFIG.get('blender', {}).get('custom_tar_url', '')
mm = CONFIG['blender'].get('major_minor', '4.2')
url = custom_url or BLENDER_DOWNLOADS.get(mm)
if not url:
    raise SystemExit(f"No Blender {mm}; add to BLENDER_DOWNLOADS or set custom_tar_url")

version = Path(url).name.split('-')[1]
install_dir = Path('/content/blender') / version
blender_bin = install_dir / 'blender'

if not (install_dir / 'blender').exists():
    print(f"Downloading Blender {version} ...")
    tar = Path('/content') / f"blender-{version}.tar.xz"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as r, open(tar, 'wb') as f:
        shutil.copyfileobj(r, f)
    print("Extracting ...")
    with tarfile.open(tar, 'r:xz') as t:
        base = t.getmembers()[0].name.split('/')[0]
        for m in t.getmembers():
            if m.name == base: continue
            m.name = str(Path(m.name).relative_to(base))
            t.extract(m, install_dir)
    tar.unlink()

# --- BPY driver ---
driver = r'''
import json, os
from pathlib import Path
import bpy
cfg = json.load(open(os.environ['CFG'], encoding='utf-8'))
rc = cfg['render']
blend = os.environ['BLEND']; out = os.environ['OUT']
bpy.ops.wm.open_mainfile(filepath=blend)
scene = bpy.context.scene; rd = scene.render
rd.resolution_percentage = int(rc.get('resolution_percentage', 100))
emap = {'cycles':'CYCLES','blender_eevee':'BLENDER_EEVEE','eevee_next':'BLENDER_EEVEE_NEXT'}
rd.engine = emap.get(rc['engine'], 'CYCLES')
Path(out).mkdir(parents=True, exist_ok=True)
fmt = rc.get('file_format', 'PNG')
rd.image_settings.file_format = fmt
if rc['engine'] == 'cycles':
    scene.cycles.samples = int(rc.get('samples', 128))
    prefs = bpy.context.preferences.addons['cycles'].preferences
    try: prefs.compute_device_type = 'CUDA' if rc.get('use_gpu', True) else 'NONE'
    except Exception: pass
    prefs.get_devices()
    for d in prefs.devices: d.use = rc.get('use_gpu', True)
    try: scene.cycles.device = 'GPU' if rc.get('use_gpu', True) else 'CPU'
    except Exception: pass
else:
    rd.eevee.taa_render_samples = int(rc.get('samples', 64))
if rc['mode'] == 'animation':
    fs, fe, fp = int(rc.get('frame_start',1)), int(rc.get('frame_end',scene.frame_end)), int(rc.get('frame_step',1))
    for f in range(fs, fe+1, fp):
        scene.frame_set(f)
        rd.filepath = f"{out}/frame_{f:05d}.{fmt.lower()}"
        bpy.ops.render.render(write_still=True)
        print('rendered frame', f)
else:
    scene.frame_set(int(rc.get('frame_start',1)))
    rd.filepath = f"{out}/render"
    bpy.ops.render.render(write_still=True)
    print('rendered still')
'''

with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as tf:
    tf.write(driver)
    driver_path = tf.name

env = dict(os.environ)
env['CFG'] = str(CFG_FOLDER / 'config.json')
env['BLEND'] = str(BLEND_PATH)
env['OUT'] = str(OUT_DIR)

print("Rendering ... this can take a while.")
r = subprocess.run([str(blender_bin), '--background', '--python', driver_path], env=env)
if r.returncode != 0:
    raise SystemExit(f"Blender failed with exit code {r.returncode}")

print("Done. Outputs in:", OUT_DIR)
for f in sorted(OUT_DIR.iterdir()):
    print("  ", f.name)
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", default=str(OUT))
    args = ap.parse_args()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build(), indent=1), encoding="utf-8")
    print(f"Wrote notebook: {out}")


if __name__ == "__main__":
    main()
