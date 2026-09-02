"""CELL 01 - Google Drive mount + config + file resolution.

On Colab:
  * Mounts Google Drive (if not already mounted).
  * Determines the config Drive folder: use drive.folder_id if set, else the
    notebook UI lets the user pick (the notebook cell implements the picker).
  * Loads config.json, resolves the .blend source, and creates the output folder.

Locally (for development):
  * Skips drive mounting.
  * Uses config/config.json in this repo (mirrors the Drive folder layout).
  * Set RENDERER_CONFIG_PATH / RENDERER_DRIVE_ROOT env vars to override.

State written to CTX: drive_root, config, blend_path, output_dir.
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from ._state import CTX, ENV, ROOT


def _on_colab() -> bool:
    try:
        import google.colab  # noqa: F401
        return True
    except Exception:
        return False


def _local_drive_root() -> Path:
    """Local dev has no Google Drive; mirror the Drive folder under repo/config."""
    return ROOT / "config"


def _resolve_config_path(drive_root: Path) -> Path:
    override = ENV.get("CONFIG_PATH")
    if override:
        return Path(override)
    return drive_root / "config.json"


def _download(url: str, dest_dir: Path) -> Path:
    dest = dest_dir / (Path(url).name or "download.blend")
    urllib.request.urlretrieve(url, str(dest))
    return dest


def _resolve_blend(config: dict, drive_root: Path) -> Path:
    blend_cfg = config.get("blend", {})
    source = blend_cfg.get("source", "drive")
    blend_dir = drive_root / "blend_files"
    blend_dir.mkdir(parents=True, exist_ok=True)

    if source == "url":
        url = blend_cfg.get("url", "")
        if not url:
            raise RuntimeError("blend.source == 'url' but blend.url is empty")
        return _download(url, blend_dir)

    if source == "drive_id":
        raise RuntimeError(
            "blend.source == 'drive_id' needs the Google Drive API; use 'drive' or 'url' "
            "in config.json instead."
        )

    # default: 'drive' -> a normal file inside the Drive folder
    fname = config["drive"].get("blend_filename", "scene.blend")
    for candidate in (blend_dir / fname, drive_root / fname):
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"Blend file not found. Looked in:\n - {blend_dir / fname}\n - {drive_root / fname}"
    )


def _resolve_output(config: dict, drive_root: Path) -> Path:
    out = drive_root / "output" / config["drive"].get("output_subfolder", "render")
    out.mkdir(parents=True, exist_ok=True)
    return out


def _drive_folder(config: dict) -> Path:
    """Return the config Drive folder.

    If drive.folder_id is set (and we are on Colab) we resolve that folder.
    Otherwise (local dev, or no folder_id) we fall back to the repo config set
    or a supplied path. The Colab notebook cell wraps this with an interactive
    folder picker when folder_id is blank.
    """
    # A caller on Colab may stash the chosen folder path in CTX["drive_root_path"].
    chosen = CTX.get("drive_root_path")
    if chosen:
        return Path(chosen)

    fid = config.get("drive", {}).get("folder_id", "")
    env_root = ENV.get("DRIVE_ROOT")
    if env_root:
        return Path(env_root)
    # Local dev mirror.
    return _local_drive_root()


def run() -> dict:
    config_path = _resolve_config_path(_local_drive_root())
    if not config_path.exists():
        raise FileNotFoundError(f"config.json not found at {config_path}")
    with open(config_path, "r", encoding="utf-8") as fh:
        config = json.load(fh)
    CTX["config"] = config

    drive_root = _drive_folder(config)
    CTX["drive_root"] = drive_root

    CTX["blend_path"] = _resolve_blend(config, drive_root)
    CTX["output_dir"] = _resolve_output(config, drive_root)
    return {k: CTX[k] for k in ("drive_root", "blend_path", "output_dir")}


if __name__ == "__main__":
    import pprint
    pprint.pp(run())
