"""CELL 02 - Blender version manager (download + install).

Fetches a Blender Linux tar.xz from the official release server, extracts it, and
returns the path to the `blender` binary. Handles both:
  * Choosing an official version (config.blender.major_minor).
  * Adding a NEW/custom version by appending to BLENDER_DOWNLOADS or setting
    config.blender.custom_tar_url.

Official release URL pattern used by Colab (Linux x64):
  https://download.blender.org/release/Blender<MAJOR.MINOR>/blender-<VERSION>-linux-x64.tar.xz

State written to CTX: blender_exe, blender_version.
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from pathlib import Path

from ._state import CTX

# ---------------------------------------------------------------------------
# Official Blender release links (linux-x64). Calendar versions simple URL rules.
# To add a NEW version, simply append an entry here (or set custom_tar_url).
# ---------------------------------------------------------------------------
BLENDER_DOWNLOADS = {
    # key: short "major.minor" used in config.blender.major_minor
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

# Stable install location so we only download a version once per Colab session.
INSTALL_ROOT = Path("/content/blender_versions") if platform.system() != "Windows" \
    else Path(__file__).resolve().parent.parent / ".blender_install"


def _tar_url(major_minor: str, custom_tar_url: str = "") -> str:
    if custom_tar_url:
        return custom_tar_url
    url = BLENDER_DOWNLOADS.get(major_minor)
    if not url:
        raise KeyError(
            f"No known Blender {major_minor} build. Add it to BLENDER_DOWNLOADS in "
            "cells/02_blender.py or set blender.custom_tar_url in config.json."
        )
    return url


def _is_installed(root: Path) -> bool:
    return (root / "blender").exists()


def _download_tar(url: str, dest: Path) -> Path:
    """Stream download to a temp file, returning its path."""
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp, open(tmp, "wb") as fh:
        shutil.copyfileobj(resp, fh)
    tmp.rename(dest)
    return dest


def _extract(tar_path: Path, install_to: Path) -> Path:
    """Extract an official Blender tar into install_to, returning the blender dir."""
    install_to.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path, "r:xz") as tar:
        # strip the outer "blender-x.y.z" directory
        members = tar.getmembers()
        base = members[0].name.split("/")[0]
        for m in members:
            if m.name == base:
                continue
            m.name = Path(m.name).relative_to(base).as_posix()
            tar.extract(m, install_to)
    # locate blender binary
    for candidate in install_to.rglob("blender"):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"blender binary not found after extracting {tar_path}")


def _version_from_url(url: str) -> str:
    name = Path(url).name  # blender-4.2.2-linux-x64.tar.xz
    parts = name.split("-")
    return parts[1] if len(parts) > 1 else "unknown"


def install(major_minor: str = None, custom_tar_url: str = "") -> str:
    """Download (if needed) and return the absolute path to the blender binary."""
    config = CTX.get("config") or {}
    major_minor = major_minor or config.get("blender", {}).get("major_minor", "4.2")
    custom_tar_url = custom_tar_url or config.get("blender", {}).get("custom_tar_url", "")

    # Local (non-Linux) dev: prefer an existing Blender on PATH so we can render
    # locally without pulled the Colab Linux tar.
    if platform.system() != "Linux":
        on_path = shutil.which("blender")
        if on_path:
            CTX["blender_exe"] = on_path
            CTX["blender_version"] = "local"
            print(f"[cell02] Using local Blender on PATH: {on_path}")
            return on_path
        raise RuntimeError(
            "Local (non-Linux) rendering needs a Blender binary on PATH. Install "
            "Blender and add it to PATH, or set blender.custom_tar_url to a local "
            "build. The Colab/GitHub Linux flow downloads the official Linux tar."
        )

    url = _tar_url(major_minor, custom_tar_url)
    version = _version_from_url(url)
    install_to = INSTALL_ROOT / version
    blender_bin = install_to / "blender"

    if _is_installed(install_to):
        CTX["blender_exe"] = str(blender_bin)
        CTX["blender_version"] = version
        return str(blender_bin)

    print(f"[cell02] Downloading Blender {version}: {url} ...")
    with tempfile.TemporaryDirectory() as td:
        tar_path = Path(td) / f"blender-{version}.tar.xz"
        _download_tar(url, tar_path)
        print(f"[cell02] Extracting {version} ...")
        _extract(tar_path, install_to)

    if not _is_installed(install_to):
        raise RuntimeError(f"Failed to locate blender binary under {install_to}")

    CTX["blender_exe"] = str(blender_bin)
    CTX["blender_version"] = version
    print(f"[cell02] Blender {version} ready: {blender_bin}")
    return str(blender_bin)


def verify() -> str:
    """Run blender --version to confirm the install works."""
    exe = install()
    out = subprocess.run([exe, "--version"], capture_output=True, text=True)
    print(out.stdout)
    if out.returncode != 0:
        raise RuntimeError(out.stderr)
    return exe


if __name__ == "__main__":
    verify()
