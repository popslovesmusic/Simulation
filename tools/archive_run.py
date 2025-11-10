#!/usr/bin/env python3
"""Archive SATP analysis outputs for reproducibility."""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import shutil
from pathlib import Path
from typing import Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Move all files and directories from the analysis directory into a "
            "timestamped archive folder and update the archive manifest."
        )
    )
    parser.add_argument(
        "run_name",
        help="Identifier for the archived run (will be sanitized for the folder name).",
    )
    parser.add_argument(
        "--analysis-root",
        default="analysis",
        help="Path to the analysis directory containing result artifacts (default: analysis).",
    )
    parser.add_argument(
        "--archive-root",
        default="archive",
        help="Path to the archive directory where runs are stored (default: archive).",
    )
    parser.add_argument(
        "--manifest",
        default=None,
        help=(
            "Path to the archive manifest file (default: <archive-root>/manifest.json)."
        ),
    )
    return parser.parse_args()


def sanitize_name(name: str) -> str:
    sanitized = "_".join(part for part in name.strip().split())
    sanitized = sanitized.replace(os.sep, "_").replace("..", "_")
    return sanitized or "run"


def load_manifest(manifest_path: Path) -> list[dict]:
    if manifest_path.exists():
        with manifest_path.open("r", encoding="utf-8") as fh:
            try:
                data = json.load(fh)
                if isinstance(data, list):
                    return data
            except json.JSONDecodeError as exc:  # noqa: PERF203 - clarity is preferred
                raise ValueError(
                    f"Manifest file {manifest_path} is not valid JSON"
                ) from exc
        raise ValueError(f"Manifest file {manifest_path} is not a JSON list")
    return []


def save_manifest(manifest_path: Path, manifest: Iterable[dict]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as fh:
        json.dump(list(manifest), fh, indent=2)
        fh.write("\n")


def archive_run(
    run_folder_name: str,
    run_label: str,
    analysis_root: Path,
    archive_root: Path,
    manifest_path: Path,
) -> Path:
    if not analysis_root.exists():
        raise FileNotFoundError(f"Analysis directory {analysis_root} does not exist")

    items_to_move = [item for item in analysis_root.iterdir() if item.name != ".gitignore"]
    if not items_to_move:
        raise FileNotFoundError(f"No result artifacts found in {analysis_root}")

    datestamp = _dt.date.today().strftime("%Y%m%d")
    dest_dir = archive_root / f"{datestamp}_{run_folder_name}"
    if dest_dir.exists():
        raise FileExistsError(f"Archive destination {dest_dir} already exists")

    dest_dir.mkdir(parents=True)
  
    # Write SATP manifest stub if not exists
    manifest_path_singlerun = dest_dir / "manifest.satp.json"
    if not manifest_path_singlerun.exists():
     manifest = {
      "protocol_version":"SATP_v2",
      "engine_mode":"igsoa_complex",
      "N":4096,
      "R_c":1.0,
      "profile_type":"gaussian",
      "amplitude_A":100.0,
      "width_sigma":256,
      "translation_cycles":10,
      "translation_per_cycle":100,
      "field_mode":"BLEND_MODE",
      "blend_weight_function":{
         "type":"linear",
         "start":0.30,
         "end":0.60,
         "cycles":10
      },
      "results":{
         "final_measured_shift":None,
         "final_drift":None,
         "integrated_exotic_cost":None
      }
    }
    with open(manifest_path_singlerun,"w") as mf:
        json.dump(manifest, mf, indent=2)


    moved_items = []
    for item in items_to_move:
        target = dest_dir / item.name
        shutil.move(str(item), target)
        moved_items.append(target.name)

    manifest = load_manifest(manifest_path)
    manifest.append(
        {
            "run_name": run_label,
            "folder": dest_dir.name,
            "datestamp": datestamp,
            "files": moved_items,
        }
    )
    save_manifest(manifest_path, manifest)

    return dest_dir


def main() -> None:
    args = parse_args()

    analysis_root = Path(args.analysis_root).resolve()
    archive_root = Path(args.archive_root).resolve()
    manifest_path = Path(args.manifest) if args.manifest else (archive_root / "manifest.json")

    run_folder_name = sanitize_name(args.run_name)

    try:
        archive_path = archive_run(
            run_folder_name,
            args.run_name,
            analysis_root,
            archive_root,
            manifest_path,
        )
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(str(exc)) from exc

    print(f"Archived analysis artifacts to {archive_path}")


if __name__ == "__main__":
    main()
