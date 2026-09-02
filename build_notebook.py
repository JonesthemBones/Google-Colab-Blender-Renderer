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
            "metadata": {"language": "python"}, "outputs": [],
            "source": src.splitlines(keepends=True)}


def _md(src: str) -> dict:
    return {"cell_type": "markdown", "metadata": {"language": "markdown"},
            "source": src.splitlines(keepends=True)}


def build() -> dict:
    cells = []
    cells.append(_md(HEADER_MD))
    cells.append(_code(MOUNT_CELL))
    cells.append(_code(PICKER_CELL))
    cells.append(_code(REVIEW_CELL))
    cells.append(_code(RUN_CELL))
    for index, cell in enumerate(cells, start=1):
        cell["metadata"]["id"] = f"blender-renderer-{index:02d}"
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

## How to use

1. Set the Colab runtime to **GPU**.
2. Run **Step 1** and authorize your own Google Drive.
3. Run **Step 2** and leave the default workspace path unless you want another folder.
4. Upload your `.blend` file to the workspace root or its `blend_files` folder.
5. Run **Step 3**, set the render options, and check the summary.
6. Run **Step 4** to install Blender and start the render.
7. Find the result in the workspace `output` folder.

To use a Blender version not listed in Step 3, enter its version number and paste
its direct Linux x64 `.tar.xz` download URL into the custom fields. Leave both
custom fields blank to use the version dropdown.

The notebook creates this workspace in your Drive:

```text
MyDrive/BlenderCloudRenderer/
- config.json
- blend_files/
- output/
```

Each user authorizes and uses their own Google Drive. The notebook does not use
the publisher's Drive.

> To add a brand-new Blender version, edit the `BLENDER_DOWNLOADS` dict in cell 02 (or set `blender.custom_tar_url` in your config.json).
"""

MOUNT_CELL = """# @title Step 1 - Authorize your Google Drive
# Run this step first, then approve the Google Drive permission request.
# - Mounts the Drive account authorized by the user.
# - Does not access the publisher's Drive.
from google.colab import drive
drive.mount('/content/drive')
print('Drive mounted at /content/drive')
"""

PICKER_CELL = """# @title Step 2 - Choose your workspace and upload your .blend file
# Leave the default path unless you already created another workspace.
# After this step, upload your .blend file to the workspace root or blend_files/.
import json
from pathlib import Path

DRIVE_ROOT = Path('/content/drive/MyDrive')
DEFAULT_WORKSPACE = DRIVE_ROOT / 'BlenderCloudRenderer'

# Enter a folder inside your MyDrive.
workspace_path = '/content/drive/MyDrive/BlenderCloudRenderer'  # @param {type:"string"}

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

print('Workspace folder:')
print('- Leave the default path to use MyDrive/BlenderCloudRenderer.')
print('- To use another folder, replace it with a full path under /content/drive/MyDrive.')
print('- The folder must contain config.json and your .blend file.')
print('- Put the .blend file in blend_files/, or next to config.json.')

CFG_FOLDER = Path(workspace_path).expanduser()
if not CFG_FOLDER.is_relative_to(DRIVE_ROOT):
    raise ValueError('workspace_path must be inside /content/drive/MyDrive')

CFG_FOLDER.mkdir(parents=True, exist_ok=True)
(CFG_FOLDER / 'blend_files').mkdir(exist_ok=True)
(CFG_FOLDER / 'output').mkdir(exist_ok=True)
config_path = CFG_FOLDER / 'config.json'
if not config_path.exists():
    with open(config_path, 'w', encoding='utf-8') as fh:
        json.dump(DEFAULT_CONFIG, fh, indent=2)
    print('Created a new workspace in:', CFG_FOLDER)
    print('Upload your .blend file to:', CFG_FOLDER / 'blend_files')

print("Selected config folder:", CFG_FOLDER)

with open(CFG_FOLDER / 'config.json', 'r', encoding='utf-8') as fh:
    CONFIG = json.load(fh)
print("Loaded config.")
"""

REVIEW_CELL = """# @title Step 3 - Set your render options
print()
print('Set the render options below. These changes apply to this run only.')
print('- File name: the .blend file inside your workspace blend_files folder.')
print('- Output folder: a subfolder inside your workspace output folder.')
print('- Cycles uses the GPU when GPU rendering is enabled.')
print('- Animation renders numbered image files for the selected frame range.')
print('- Custom Blender fields: fill in both fields only when the version is not in the dropdown.')

blend_filename = "scene.blend"  # @param {type:"string"}
output_subfolder = "my_first_render"  # @param {type:"string"}
render_engine = "cycles"  # @param ["cycles", "blender_eevee", "eevee_next"]
render_mode = "still"  # @param ["still", "animation"]
blender_version = "4.2"  # @param ["3.6", "4.0", "4.1", "4.2", "4.3", "4.4", "4.5", "5.0", "5.1", "5.2"]
custom_blender_version = ""  # @param {type:"string"}
custom_blender_url = ""  # @param {type:"string"}
resolution_percentage = 100  # @param {type:"integer"}
samples = 128  # @param {type:"integer"}
frame_start = 1  # @param {type:"integer"}
frame_end = 250  # @param {type:"integer"}
frame_step = 1  # @param {type:"integer"}
use_gpu = True  # @param {type:"boolean"}
file_format = "PNG"  # @param ["PNG", "JPEG", "OPEN_EXR", "TIFF"]

CONFIG['drive']['blend_filename'] = blend_filename
CONFIG['drive']['output_subfolder'] = output_subfolder
CONFIG['render']['engine'] = render_engine
CONFIG['render']['mode'] = render_mode
CONFIG['render']['resolution_percentage'] = resolution_percentage
CONFIG['render']['samples'] = samples
CONFIG['render']['frame_start'] = frame_start
CONFIG['render']['frame_end'] = frame_end
CONFIG['render']['frame_step'] = frame_step
CONFIG['render']['use_gpu'] = use_gpu
CONFIG['render']['file_format'] = file_format
CONFIG['blender']['major_minor'] = blender_version
CONFIG['blender']['custom_tar_url'] = custom_blender_url.strip()
if bool(custom_blender_version.strip()) != bool(custom_blender_url.strip()):
    raise ValueError('Enter both custom_blender_version and custom_blender_url, or leave both blank.')
if custom_blender_version.strip():
    CONFIG['blender']['major_minor'] = custom_blender_version.strip()
print()
selected_blender_version = CONFIG['blender']['major_minor']
print('Selected:', render_engine, '|', render_mode, '| Blender', selected_blender_version)
print('Custom Blender:', custom_blender_version.strip() or '(none; using selected version)')
print('File:', blend_filename, '| Output:', output_subfolder)
print('Resolution:', resolution_percentage, '% | Samples:', samples)
print('Run Cell 4 to install Blender and start the render.')
"""

RUN_CELL = """# @title Step 4 - Render your Blender file
# Run this step after Step 3. Blender is downloaded into the temporary Colab runtime.
import json, os, subprocess, tempfile, tarfile, urllib.request, shutil
from pathlib import Path

CFG_FOLDER = Path(CFG_FOLDER)
BLEND_DIR = CFG_FOLDER / 'blend_files'
blend_filename = CONFIG['drive']['blend_filename']
BLEND_PATH = BLEND_DIR / blend_filename
if not BLEND_PATH.exists():
    root_blend_path = CFG_FOLDER / blend_filename
    if root_blend_path.exists():
        BLEND_PATH = root_blend_path
OUT_DIR = CFG_FOLDER / 'output' / CONFIG['drive'].get('output_subfolder', 'render')

if not BLEND_PATH.exists():
    print("WARNING: blend file not found:", blend_filename)
    print("Accepted locations:")
    print("-", BLEND_DIR / blend_filename)
    print("-", CFG_FOLDER / blend_filename)
    print("Upload the file to either location, then re-run Cell 4.")
    raise SystemExit

print("Using blend file:", BLEND_PATH)

OUT_DIR.mkdir(parents=True, exist_ok=True)

# - Blender version download map.
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

version = mm if custom_url else Path(url).name.split('-')[1]
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

# - Blender Python driver.
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
