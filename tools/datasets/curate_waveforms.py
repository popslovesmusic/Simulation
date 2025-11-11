#!/usr/bin/env python3
"""Utilities for packaging waveform simulation runs into ML-ready datasets."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None  # type: ignore


DATASET_ROOT = Path("analysis/datasets")
DEFAULT_SAMPLE_DIR = "samples"
DEFAULT_MANIFEST = "manifest.json"
DEFAULT_README = "README.md"


@dataclass
class WaveformSample:
    """Description of a single waveform sample packaged for ML training."""

    identifier: str
    source: str
    waveform_path: str
    metadata: Mapping[str, object]


@dataclass
class DatasetManifest:
    """Structured summary describing curated waveform datasets."""

    dataset_name: str
    created_at: str
    source_root: str
    sample_count: int
    schema: Mapping[str, object]
    samples: List[WaveformSample]

    def to_json(self) -> Dict[str, object]:
        payload = asdict(self)
        payload["samples"] = [asdict(sample) for sample in self.samples]
        return payload


def _load_metadata(run_dir: Path) -> MutableMapping[str, object]:
    """Load optional metadata JSON/YAML files describing a run."""

    candidates = [
        run_dir / "metadata.json",
        run_dir / "metadata.yaml",
        run_dir / "metadata.yml",
    ]
    for candidate in candidates:
        if not candidate.exists():
            continue
        if candidate.suffix == ".json":
            return json.loads(candidate.read_text(encoding="utf-8"))
        if candidate.suffix in {".yaml", ".yml"}:
            if yaml is None:
                raise RuntimeError(
                    f"YAML metadata requested at {candidate} but PyYAML is not installed"
                )
            loaded = yaml.safe_load(candidate.read_text(encoding="utf-8"))
            return dict(loaded or {})
    return {}


def _discover_waveform(run_dir: Path) -> Path:
    """Find the primary waveform artifact within ``run_dir``."""

    candidates = sorted(run_dir.glob("*.csv"))
    if not candidates:
        raise FileNotFoundError(
            f"No waveform CSV files found in run directory: {run_dir}"  # noqa: EM101
        )
    # Prefer files containing "waveform" in the name.
    for candidate in candidates:
        if "waveform" in candidate.stem.lower():
            return candidate
    return candidates[0]


def _build_schema(example_metadata: Mapping[str, object]) -> Mapping[str, object]:
    """Construct a lightweight schema description for the dataset manifest."""

    metadata_keys = sorted(example_metadata.keys())
    return {
        "format": "csv",
        "index_column": 0,
        "metadata_fields": metadata_keys,
    }


def _write_readme(dataset_dir: Path, dataset_name: str, manifest: DatasetManifest) -> None:
    """Create a README describing dataset provenance and usage."""

    readme_path = dataset_dir / DEFAULT_README
    metadata_fields = ", ".join(manifest.schema.get("metadata_fields", [])) or "(none)"
    content = f"""# {dataset_name} Dataset\n\n"""
    content += (
        "This dataset was curated using `tools/datasets/curate_waveforms.py` "
        "and bundles simulation waveform CSV files alongside structured metadata "
        "for surrogate model training.\n\n"
    )
    content += "## Contents\n"
    content += "- `manifest.json`: machine-readable index of curated samples\n"
    content += f"- `{DEFAULT_SAMPLE_DIR}/`: waveform CSV files renamed by sample identifier\n\n"
    content += "## Metadata Fields\n"
    content += f"The manifest captures the following metadata fields: {metadata_fields}.\n\n"
    content += "## Reproducibility\n"
    content += (
        "The manifest stores the `source_root` path for provenance and the "
        "generation timestamp in UTC. Re-run the curation tool with the same "
        "inputs to regenerate this dataset.\n"
    )
    readme_path.write_text(content, encoding="utf-8")


def curate_dataset(
    input_root: Path,
    dataset_name: str,
    output_root: Path = DATASET_ROOT,
    overwrite: bool = False,
    dry_run: bool = False,
) -> DatasetManifest:
    """Package waveform runs under ``input_root`` into a dataset folder."""

    if not input_root.exists():
        raise FileNotFoundError(f"Input root does not exist: {input_root}")  # noqa: EM101

    dataset_dir = output_root / dataset_name
    sample_dir = dataset_dir / DEFAULT_SAMPLE_DIR
    if dataset_dir.exists():
        if not overwrite:
            raise FileExistsError(
                f"Dataset directory already exists: {dataset_dir}. Use --overwrite to replace."
            )
        if not dry_run:
            shutil.rmtree(dataset_dir)

    samples: List[WaveformSample] = []
    for run_path in sorted(p for p in input_root.iterdir() if p.is_dir()):
        identifier = run_path.name.replace(" ", "_")
        metadata = _load_metadata(run_path)
        metadata.setdefault("source_run", identifier)
        waveform_path = _discover_waveform(run_path)

        samples.append(
            WaveformSample(
                identifier=identifier,
                source=str(run_path.resolve()),
                waveform_path=str(Path(DEFAULT_SAMPLE_DIR) / f"{identifier}.csv"),
                metadata=dict(metadata),
            )
        )

        if dry_run:
            continue

        sample_dir.mkdir(parents=True, exist_ok=True)
        target_path = sample_dir / f"{identifier}.csv"
        shutil.copy2(waveform_path, target_path)

    if not samples:
        raise RuntimeError(f"No run directories found in {input_root}")

    schema = _build_schema(samples[0].metadata)
    manifest = DatasetManifest(
        dataset_name=dataset_name,
        created_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        source_root=str(input_root.resolve()),
        sample_count=len(samples),
        schema=schema,
        samples=samples,
    )

    if not dry_run:
        dataset_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = dataset_dir / DEFAULT_MANIFEST
        manifest_path.write_text(
            json.dumps(manifest.to_json(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        _write_readme(dataset_dir, dataset_name, manifest)

    return manifest


def _parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_root", type=Path, help="Directory containing waveform run folders")
    parser.add_argument("dataset_name", type=str, help="Name for the curated dataset")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DATASET_ROOT,
        help="Destination root directory (defaults to analysis/datasets)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite any existing dataset with the same name",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan inputs and print summary without writing artifacts",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = _parse_args(argv)
    manifest = curate_dataset(
        input_root=args.input_root,
        dataset_name=args.dataset_name,
        output_root=args.output_root,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
    )
    print(
        json.dumps(
            {
                "dataset_name": manifest.dataset_name,
                "sample_count": manifest.sample_count,
                "output_root": str((args.output_root / manifest.dataset_name).resolve()),
                "dry_run": args.dry_run,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
