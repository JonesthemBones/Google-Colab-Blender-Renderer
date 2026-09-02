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
    cells.append(_code(BASIC_SETTINGS_CELL))
    cells.append(_code(QUALITY_SETTINGS_CELL))
    cells.append(_code(BLENDER_SETTINGS_CELL))
    cells.append(_code(SUMMARY_CELL))
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
            "accelerator": "GPU",
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
5. Run **Step 3A**, set the basic render options.
6. Run **Step 3B**, set quality and animation options.
7. Run **Step 3C**, choose Blender or enter a custom version and URL.
8. Run **Step 3D** and check the summary.
9. Run **Step 4** to install Blender and start the render.
10. Find the result in the workspace `output` folder.

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

Use the custom Blender fields in **Step 3C** to add a version without editing code.
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
        'engine': 'eevee',
        'mode': 'still',
        'resolution_percentage': 100,
        'samples': 64,
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

BASIC_SETTINGS_CELL = """# @title Step 3A - Set basic render options
print()
print('These settings apply to this run only.')
print('- File name: the .blend file inside your workspace blend_files folder.')
print('- Output folder: a subfolder inside your workspace output folder.')

blend_filename = "scene.blend"  # @param {type:"string"}
output_subfolder = "my_first_render"  # @param {type:"string"}
render_engine = "eevee"  # @param ["cycles", "eevee"]
render_mode = "still"  # @param ["still", "animation"]
resolution_percentage = 100  # @param {type:"integer"}

CONFIG['drive']['blend_filename'] = blend_filename
CONFIG['drive']['output_subfolder'] = output_subfolder
CONFIG['render']['engine'] = render_engine
CONFIG['render']['mode'] = render_mode
CONFIG['render']['resolution_percentage'] = resolution_percentage
print()
print('Basic settings saved:', blend_filename, '|', render_engine, '|', render_mode, '|', resolution_percentage, '%')
print('Run Step 3B next.')
"""

QUALITY_SETTINGS_CELL = """# @title Step 3B - Set quality and animation options
print()
print('Quality and animation settings:')
print('- Samples: higher values improve quality but take longer.')
print('- Frame range is used only when mode is animation.')
print('- GPU applies to Cycles rendering; Eevee uses the selected Blender display backend.')

samples = 64  # @param {type:"integer"}
frame_start = 1  # @param {type:"integer"}
frame_end = 250  # @param {type:"integer"}
frame_step = 1  # @param {type:"integer"}
use_gpu = True  # @param {type:"boolean"}
file_format = "PNG"  # @param ["PNG", "JPEG", "OPEN_EXR", "TIFF"]

CONFIG['render']['samples'] = samples
CONFIG['render']['frame_start'] = frame_start
CONFIG['render']['frame_end'] = frame_end
CONFIG['render']['frame_step'] = frame_step
CONFIG['render']['use_gpu'] = use_gpu
CONFIG['render']['file_format'] = file_format
print()
print('Quality settings saved. Run Step 3C next.')
"""

BLENDER_SETTINGS_CELL = """# @title Step 3C - Choose or add a Blender version
print()
print('Choose a listed version, or fill in both custom fields.')
print('- Listed version: choose from the dropdown and leave custom fields blank.')
print('- Custom version: enter the version number and a direct Linux x64 .tar.xz URL.')

blender_version = "4.2"  # @param ["3.6", "4.0", "4.1", "4.2", "4.3", "4.4", "4.5", "5.0", "5.1", "5.2"]
custom_blender_version = ""  # @param {type:"string"}
custom_blender_url = ""  # @param {type:"string"}

if bool(custom_blender_version.strip()) != bool(custom_blender_url.strip()):
    raise ValueError('Enter both custom Blender fields, or leave both blank.')
CONFIG['blender']['major_minor'] = custom_blender_version.strip() or blender_version
CONFIG['blender']['custom_tar_url'] = custom_blender_url.strip()
print()
print('Blender selected:', CONFIG['blender']['major_minor'])
print('Run Step 4 next.')
"""

SUMMARY_CELL = """# @title Step 3D - Check settings
print('Render settings ready:')
print('- File:', CONFIG['drive']['blend_filename'])
print('- Output:', CONFIG['drive'].get('output_subfolder', 'render'))
print('- Engine:', CONFIG['render']['engine'])
print('- Mode:', CONFIG['render']['mode'])
print('- Resolution:', CONFIG['render'].get('resolution_percentage', 100), '%')
print('- Samples:', CONFIG['render'].get('samples', 128))
print('- Blender:', CONFIG['blender']['major_minor'])
print()
print('If these settings look correct, run Step 4.')
"""

RUN_CELL = """# @title Step 4 - Render your Blender file
# Run this step after Step 3D. Blender is downloaded into the temporary Colab runtime.
import json, os, re, subprocess, tempfile, tarfile, urllib.request, shutil
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
engine = str(rc.get('engine', 'eevee')).strip().lower()
blend = os.environ['BLEND']; out = os.environ['OUT']
bpy.ops.wm.open_mainfile(filepath=blend)
scene = bpy.context.scene; rd = scene.render
rd.resolution_percentage = int(rc.get('resolution_percentage', 100))
if engine == 'cycles':
    rd.engine = 'CYCLES'
elif engine in ('eevee', 'blender_eevee', 'eevee_next'):
    for eevee_engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
        try:
            rd.engine = eevee_engine
            break
        except TypeError:
            continue
    else:
        raise RuntimeError('This Blender build does not provide an Eevee engine')
else:
    raise ValueError(f'Unsupported render engine: {engine!r}')
if (engine == 'cycles') != (rd.engine == 'CYCLES'):
    raise RuntimeError(f'Requested {engine!r}, but Blender selected {rd.engine!r}')
print('Blender render engine:', rd.engine)
output_root = Path(out)
output_root.mkdir(parents=True, exist_ok=True)
fmt = rc.get('file_format', 'PNG')
rd.image_settings.file_format = fmt
if engine == 'cycles':
    scene.cycles.samples = int(rc.get('samples', 128))
    prefs = bpy.context.preferences.addons['cycles'].preferences
    try: prefs.compute_device_type = 'CUDA' if rc.get('use_gpu', True) else 'NONE'
    except Exception: pass
    prefs.get_devices()
    for d in prefs.devices: d.use = rc.get('use_gpu', True)
    print('Cycles device backend:', prefs.compute_device_type)
    print('Cycles devices:', [d.name for d in prefs.devices if d.use])
    try: scene.cycles.device = 'GPU' if rc.get('use_gpu', True) else 'CPU'
    except Exception: pass
else:
    samples = int(rc.get('samples', 64))
    for property_name in ('taa_render_samples', 'taa_samples'):
        if hasattr(scene.eevee, property_name):
            setattr(scene.eevee, property_name, samples)
            break
if rc['mode'] == 'animation':
    animation_dir = output_root / 'animation'
    for index in range(1, 10000):
        candidate = output_root / f'animation_{index:03d}'
        if not animation_dir.exists():
            break
        animation_dir = candidate
    animation_dir.mkdir(parents=True, exist_ok=True)
    fs, fe, fp = int(rc.get('frame_start',1)), int(rc.get('frame_end',scene.frame_end)), int(rc.get('frame_step',1))
    for f in range(fs, fe+1, fp):
        scene.frame_set(f)
        rd.filepath = str(animation_dir / f"frame_{f:05d}.{fmt.lower()}")
        bpy.ops.render.render(write_still=True)
        print('rendered frame', f)
else:
    scene.frame_set(int(rc.get('frame_start',1)))
    suffix = f'.{fmt.lower()}'
    still_path = output_root / f'render{suffix}'
    for index in range(1, 10000):
        if not still_path.exists():
            break
        still_path = output_root / f'render_{index:03d}{suffix}'
    rd.filepath = str(still_path.with_suffix(''))
    bpy.ops.render.render(write_still=True)
    print('rendered still')
'''

with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as tf:
    tf.write(driver)
    driver_path = tf.name

env = dict(os.environ)
runtime_config_path = Path('/content/renderer_runtime_config.json')
with open(runtime_config_path, 'w', encoding='utf-8') as fh:
    json.dump(CONFIG, fh, indent=2)
env['CFG'] = str(runtime_config_path)
env['BLEND'] = str(BLEND_PATH)
env['OUT'] = str(OUT_DIR)

print("Rendering with engine:", CONFIG['render']['engine'])
print("Rendering ... Blender progress and remaining samples will appear below.")
engine = str(CONFIG.get('render', {}).get('engine', 'eevee')).strip().lower()
cmd = [str(blender_bin), '--background', '--python', driver_path]
render_config = CONFIG.get('render', {})
if engine == 'cycles' and render_config.get('use_gpu', True):
    cmd += ['--', '--cycles-device', 'CUDA']
    subprocess.run(['apt-get', 'install', '-y', 'libtcmalloc-minimal4'], check=True)
    tcmalloc = '/usr/lib/x86_64-linux-gnu/libtcmalloc_minimal.so.4'
    if os.path.exists(tcmalloc):
        env['LD_PRELOAD'] = tcmalloc
if engine in ('eevee', 'blender_eevee', 'eevee_next'):
    env['__NV_PRIME_RENDER_OFFLOAD'] = '1'
    env['__GLX_VENDOR_LIBRARY_NAME'] = 'nvidia'
    subprocess.run(['apt-get', 'update'], check=True)
    subprocess.run(['apt-get', 'install', '-y', 'xvfb', 'libegl1-mesa', 'libgles2-mesa-dev'], check=True)
    cmd = ['xvfb-run', '-a', '-s', '-screen 0 1920x1080x24'] + cmd
sample_pattern = re.compile(r'Rendering\s+(\d+)\s*/\s*(\d+)\s+samples')
process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, bufsize=1)
assert process.stdout is not None
for line in process.stdout:
    line = line.rstrip()
    match = sample_pattern.search(line)
    if match:
        current, total = (int(value) for value in match.groups())
        print(f'[render] Samples: {current}/{total} ({total - current} remaining)', flush=True)
    elif line:
        print(line, flush=True)
r = process.wait()
if r != 0:
    raise SystemExit(f"Blender failed with exit code {r}")

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
