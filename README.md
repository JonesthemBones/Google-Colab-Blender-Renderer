# Google Colab Eevee-Compatible Blender Cloud Renderer

A Google Colab-based **Blender cloud renderer** that:
- Renders `.blend` files on a Colab GPU.
- Supports **both Eevee and Cycles** engines.
- Renders a **single still image** OR **frame-by-frame animation**.
- Is configured entirely from a **Google Drive folder** (config.json + your `.blend`).
- Lets you pick which **Blender version** to use, and **add new versions** easily.

The UX/UI is delivered inside the Colab notebook itself. This repo is the *local
development* home, structured as **cells** (one Python module per Colab code cell)
so you can build and test the pipeline locally before deploying to Colab.

## Structure

```
├── cells/                        # one module = one Colab "cell"
│   ├── _state.py                 # shared CTX dict threaded across cells
│   ├── cell_01_drive_config.py   # Drive mount + config.json + resolve .blend/output
│   ├── cell_02_blender.py        # Blender version manager (tar download/install)
│   ├── cell_03_bpy_bootstrap.py  # BPY driver script (runs inside Blender)
│   ├── cell_04_render.py         # render coordinator (headless subprocess)
│   └── cell_05_runner.py         # local orchestrator (mirrors Colab cell order)
├── build_notebook.py             # generates the .ipynb for Colab (UI)
├── notebooks/                    # generated Blender_Cloud_Renderer.ipynb
├── config/                       # LOCAL mirror of your Drive config folder
│   ├── config.json               # all user customization lives here
│   ├── blend_files/              # drop your .blend here (locally for testing)
│   └── output/                   # renders land here (locally for testing)
└── output/                       # (optional) alt local output location
```

## The config.json (user customization)

Everything the user tweaks lives in one `config.json` stored in a Google Drive
folder. It controls:

| Section | What it sets |
|---|---|
| `drive.folder_id` | (optional) hardcode your Drive folder ID to skip picking |
| `drive.blend_filename` | name of your `.blend` file |
| `drive.output_subfolder` | subfolder under `output/` for this render |
| `blend.source` | `drive` / `url` / `drive_id` |
| `render.engine` | `cycles` \| `blender_eevee` \| `eevee_next` |
| `render.mode` | `still` or `animation` |
| `render.frame_start/end/step` | animation frame range |
| `render.samples` | Cycles/EEVEE samples |
| `blender.major_minor` | Blender version, e.g. `"4.2"` |
| `blender.custom_tar_url` | add a custom/new Blender build |

## Local development (build here first)

> Requires Python 3 and, for an actual render, a Blender binary. On Windows the
> downloader uses the Linux tar (for Colab), so to render *locally* install
> Blender yourself and ensure a `blender` binary is on PATH (see below).

1. **Set up the local config mirror** so the pipeline can run without Drive:
   - Edit `config/config.json` (it doubles as your local config).
   - Put your `.blend` at `config/blend_files/scene.blend` (or change `blend_filename`).

2. **Dry-run the pipeline** (verifies cell order + config resolution):
   ```
   python -c "import sys; sys.path.insert(0,'.'); from cells import cell_05_runner as r; print(r.run())"
   ```
   This runs cells 01→04. It will stop with a clear message at whatever stage
   needs a real asset (e.g. missing blend, or missing local Blender).

3. **Local render with a real Blender**: point the downloader/runner at a local
   Blender binary instead of the Colab tar. The cleanest way is to install
   Blender and add it to PATH, then run:
   ```
   python -c "import sys; sys.path.insert(0,'.'); from cells import cell_05_runner as r; r.run()"
   ```
   (Cells 02–04 already pick up any `blender` on PATH for local runs.)

### Adding a new Blender version
Open `cells/cell_02_blender.py` → `BLENDER_DOWNLOADS` and add a line, e.g.:
```python
"4.5": "https://download.blender.org/release/Blender4.5/blender-4.5.0-linux-x64.tar.xz",
```
or set `blender.custom_tar_url` in `config.json`. The same map is embedded in the
generated Colab notebook.

## Publishing and using in Google Colab

The notebook is designed to be shared publicly. It never uses the publisher's
Google Drive. Each person runs it with their own Colab session and authorizes
their own Google account when the mount cell runs.

### Publish the notebook

1. Build the notebook locally:
   ```
   python build_notebook.py
   ```
2. Commit `notebooks/Blender_Cloud_Renderer.ipynb` to GitHub.
3. Open it in Colab with:
   `https://colab.research.google.com/github/OWNER/REPOSITORY/blob/main/notebooks/Blender_Cloud_Renderer.ipynb`
4. Share that Colab link or the GitHub notebook link. Do not share your personal
   Drive folder as part of the application.

### User workflow

1. Open the notebook in Colab and choose a **GPU runtime**.
2. Run the authorization/mount cell and authorize the user's Google account.
3. Run the workspace cell. If no renderer workspace exists, it creates:
   `MyDrive/BlenderCloudRenderer/` with `config.json`, `blend_files/`, and `output/`.
4. Upload the user's `.blend` file into `blend_files/`. Change `blend_filename` in
   `config.json` if it is not named `scene.blend`.
5. Run the review cell, then the render cell. Results are written to that user's
   own Drive under `output/`.

Users can also prepare their own folder and `config.json` first; the workspace
cell lists all matching folders in their `MyDrive` and lets them select one.

Animation frames come out as numbered PNGs; combine them into a video yourself
later (out of scope, as requested).
