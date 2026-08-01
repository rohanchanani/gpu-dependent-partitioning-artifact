# GPU Dependent Partitioning Artifacts

This package contains three computational artifacts for the SC/PAW-ATM
submission on GPU-accelerated Realm dependent partitioning.

All three artifacts are archived together. The SC artifact template allows
multiple computational artifacts to be archived under a single DOI.

Current public repository:
https://github.com/rohanchanani/gpu-dependent-partitioning-artifact

Current archived DOI:
https://doi.org/10.5281/zenodo.21741212

## Artifacts

### A1: Modified Legion/Realm Runtime

Path:

`artifacts/A1_legion_realm_runtime/`

This artifact contains source snapshots and patches for the modified Realm and
Legion runtime support used by the dependent-partitioning experiments. It also
contains build and git provenance for the runtime.

Important contents:

- `source/realm/`: copied Realm benchmark and dependent-partitioning source
  files relevant to the evaluation.
- `patches/realm_local_benchmark_patches.diff`: local runtime/benchmark patch
  set recorded at collection time.
- `provenance/`: Realm/Legion commits, build cache highlights, and installed
  Legion CMake metadata.

### A2: Modified LegionSolvers Repartitioning App

Path:

`artifacts/A2_legionsolvers_repartitioning/`

This artifact contains the LegionSolvers/kdrsolvers source snapshot and scripts
used for the dynamic repartitioning experiment.

Important contents:

- `source/`: copied LegionSolvers source tree.
- `patches/legionsolvers_local_diff.diff`: local LegionSolvers patch recorded
  at collection time.
- `scripts/`: repartitioning sweep scripts.
- `provenance/`: LegionSolvers build and git provenance.

### A3: Scripts, Data, and Provenance

Path:

`artifacts/A3_scripts_data_provenance/`

This artifact contains the final and raw data, plotting scripts, Perlmutter
runner scripts, and provenance tying the runtime and application artifacts to
the paper figures.

Important contents:

- `scripts/plotting/`: scripts that regenerate the paper figures from CSV data.
- `scripts/perlmutter/`: Perlmutter runners and benchmark collection scripts.
- `data/raw/`: raw and summary CSVs, manifests, and merge logs.
- `provenance/`: full copied provenance bundle.

For convenience, the final graph input CSVs are also mirrored at top level in
`data/final/`:

- `microbenchmarks.csv`
- `weak_scaling_raw.csv`
- `repartitioning.csv`

## Quick Figure Reproduction

From the package root:

```bash
python3 -m pip install pandas matplotlib
./artifacts/A3_scripts_data_provenance/scripts/plotting/reproduce_figures.sh
```

Figures are written under `artifacts/A3_scripts_data_provenance/figures/` when
using the packaged scripts directly. If needed, the scripts can be adjusted to
write to the top-level `figures/` directory.

## Hardware

Experiments were collected on NERSC Perlmutter GPU nodes. Each node contains a
64-core AMD EPYC 7763 CPU and four NVIDIA A100 40GB GPUs.

## License

The top-level artifact scripts, plotting code, data files, and documentation
are distributed under the Apache License, Version 2.0. Copied source snapshots
and patches from Realm, Legion, and LegionSolvers remain subject to their
original upstream project licenses.
