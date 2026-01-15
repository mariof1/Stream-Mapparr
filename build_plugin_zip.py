#!/usr/bin/env python3
"""Build a Dispatcharr plugin zip for Stream-Mapparr.

This repo's source lives in the `Stream-Mapparr/` folder, but Dispatcharr expects:
- plugin.json at the root of the imported zip
- a Python package folder matching plugin.json's `module` (stream_mapparr/)

This script produces a zip under ./dist/ that you can import via Dispatcharr UI.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
SRC_DIR = REPO_ROOT / "Stream-Mapparr"
DIST_DIR = REPO_ROOT / "dist"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _detect_version(plugin_py: Path) -> str | None:
    try:
        text = _read_text(plugin_py)
    except FileNotFoundError:
        return None

    m = re.search(r"^\s*PLUGIN_VERSION\s*=\s*\"([^\"]+)\"", text, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return None


def _should_include(filename: str) -> bool:
    # Keep this intentionally conservative.
    if filename in {"plugin.py", "fuzzy_matcher.py", "__init__.py"}:
        return True
    if filename.endswith("_channels.json"):
        return True
    if filename in {"networks.json", "channels.txt"}:
        return True
    return False


def build_zip(out_path: Path, verbose: bool) -> None:
    if not SRC_DIR.exists():
        raise RuntimeError(f"Source directory not found: {SRC_DIR}")

    plugin_json_src = SRC_DIR / "plugin.json"
    if not plugin_json_src.exists():
        raise RuntimeError(f"Missing plugin.json at: {plugin_json_src}")

    version = _detect_version(SRC_DIR / "plugin.py")

    # Ensure output directory exists
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Dispatcharr expects the python module `stream_mapparr.*`
    package_dir_in_zip = Path("stream_mapparr")

    files = []
    for child in sorted(SRC_DIR.iterdir()):
        if not child.is_file():
            continue
        if _should_include(child.name):
            files.append(child)

    if not files:
        raise RuntimeError(f"No plugin files found to include from {SRC_DIR}")

    # Write zip
    with zipfile.ZipFile(out_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # plugin.json must be at zip root
        zf.write(plugin_json_src, arcname="plugin.json")

        for file_path in files:
            arcname = str(package_dir_in_zip / file_path.name)
            zf.write(file_path, arcname=arcname)

    if verbose:
        print(f"Created: {out_path}")
        if version:
            print(f"Detected plugin version: {version}")
        with zipfile.ZipFile(out_path, mode="r") as zf:
            for name in zf.namelist():
                print(name)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Build Stream-Mapparr Dispatcharr plugin zip")
    ap.add_argument(
        "--out",
        default=None,
        help="Output zip path (default: dist/Stream-Mapparr-<version>.zip or dist/Stream-Mapparr.zip)",
    )
    ap.add_argument("--verbose", action="store_true", help="Print file list")

    args = ap.parse_args(argv)

    version = _detect_version(SRC_DIR / "plugin.py")
    default_name = f"Stream-Mapparr-{version}.zip" if version else "Stream-Mapparr.zip"
    out_path = Path(args.out) if args.out else (DIST_DIR / default_name)

    try:
        build_zip(out_path=out_path, verbose=bool(args.verbose))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
