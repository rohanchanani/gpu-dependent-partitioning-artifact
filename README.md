# GPU Dependent Partitioning Artifact Package

This directory is the curated artifact package for the SC/PAW-ATM submission on
GPU-accelerated Realm dependent partitioning. It is intended to be archived as a
versioned public artifact, ideally through a tagged GitHub release plus Zenodo
DOI.

Archived DOI: https://doi.org/10.5281/zenodo.21741212

The package contains the data used for the paper's three evaluation sections:

- microbenchmarks of `image` and `preimage`;
- application-derived weak scaling for Circuit, Pennant, and MiniAero;
- dynamic repartitioning in LegionSolvers/kdrsolvers.

## Quick Reproduction Path

To regenerate figures from the supplied CSVs:

```bash
python3 -m pip install pandas matplotlib
./scripts/plotting/reproduce_figures.sh
```

The generated figures are written to `figures/`.

## Data

Final graph inputs are in `data/final/`:

- `microbenchmarks.csv`: 360 summary rows for image/preimage buffer sweeps.
- `weak_scaling_raw.csv`: 36 raw weak-scaling rows, three repetitions per app
  and scale.
- `repartitioning.csv`: 27 summary rows for dynamic repartitioning throughput.

Raw and supporting data are in `data/raw/`:

- `microbenchmarks/`: raw parsed benchmark output, per-invocation point rows,
  log-axis summary, empty failures CSV, and manifest.
- `weak_scaling/`: raw rows and per-app median summaries.
- `repartitioning/`: raw rows, min/median/max summary, graph CSV, and merge log.

## Source and Provenance

- `source/realm/` contains copied source files relevant to Realm dependent
  partitioning and the benchmark harness.
- `source/legionsolvers/` contains copied LegionSolvers source/build context.
- `provenance/` contains git commits/status, local diffs, CMake caches, and
  build metadata.
- `scripts/perlmutter/` contains the run scripts used or preserved from the
  Perlmutter experiments.

The recorded Realm benchmark build was an optimized Release build with
`CMAKE_BUILD_TYPE=Release`, `CMAKE_CXX_FLAGS_RELEASE=-O3 -DNDEBUG`,
`CMAKE_CUDA_FLAGS_RELEASE=-O3 -DNDEBUG`, CUDA architecture 80, and CUDA 12.9.
See `provenance/perlmutter_provenance.txt` and
`provenance/realm_build_pm_deppart_CMakeCache.txt`.

## Hardware

Experiments were collected on NERSC Perlmutter GPU nodes. Each node has one
64-core AMD EPYC 7763 CPU and four NVIDIA A100 40GB GPUs.

## License

The top-level artifact scripts, plotting code, data files, and documentation
are distributed under the Apache License, Version 2.0. Copied source snapshots
and patches from Realm, Legion, and LegionSolvers remain subject to their
original upstream project licenses.

## Publication

GitHub repository:
https://github.com/rohanchanani/gpu-dependent-partitioning-artifact

Zenodo DOI:
https://doi.org/10.5281/zenodo.21741212
