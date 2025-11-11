# Dataset Artifacts

The `analysis/datasets/` directory stores curated waveform corpora and benchmarking
artifacts generated during Phase 4 acceleration work. Datasets are typically
materialised by running `tools/datasets/curate_waveforms.py` against collections
of simulation runs. Each dataset receives its own subdirectory containing:

- `manifest.json` – machine readable index of samples and metadata fields.
- `samples/` – waveform CSV files renamed using stable sample identifiers.
- Optional benchmarking reports or governance attestations tied to the dataset.

To create a new dataset:

```bash
python tools/datasets/curate_waveforms.py <path-to-runs> <dataset-name>
```

The script accepts `--overwrite` and `--dry-run` flags to simplify iterative
updates. Ensure any sensitive metadata is scrubbed before committing manifests
and always coordinate with the data governance lead when exporting data outside
of the repository.
