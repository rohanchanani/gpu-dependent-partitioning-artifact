# Artifact Description Writing Context

This file is for the writing agent. It summarizes factual context only; it is
not a polished artifact description.

## Artifact Scope

The artifact supports the evaluation section of the paper on GPU-accelerated
Realm dependent partitioning. It contains the data, plotting scripts, run
scripts, source snapshots, and provenance for:

1. image/preimage microbenchmarks;
2. application-derived weak scaling for Circuit, Pennant, and MiniAero;
3. dynamic repartitioning in LegionSolvers/kdrsolvers.

The artifact should be described as one computational artifact unless the final
public release is intentionally split into multiple DOI-backed archives.

## Contributions to Connect

Use contribution labels that match the actual paper, but the artifact supports
at least:

- implementation of GPU-accelerated dependent partitioning in Realm;
- performance evaluation of individual dependent-partitioning operations;
- performance evaluation of application-derived dependent-partitioning kernels;
- dynamic repartitioning experiment showing that lower partitioning cost enables
  online repartitioning inside an iterative solver.

## Hardware

All experiments were collected on NERSC Perlmutter GPU nodes. Each node contains
a 64-core AMD EPYC 7763 CPU and four NVIDIA A100 40GB GPUs.

## Software and Build Provenance

Realm benchmark provenance:

- Realm repository path at collection time: `/pscratch/sd/r/rchanani/realm`.
- Recorded Realm commit: `9b026a46941f95a3115d8b2fb4dd43d2ca532323`.
- Recorded branch: `review-tiling`.
- Local diff was present; include `provenance/realm_local_benchmark_patches.diff`.
- Build: `build_pm_deppart`.
- CMake build type: `Release`.
- Release flags: C++ `-O3 -DNDEBUG`, CUDA `-O3 -DNDEBUG`.
- CUDA architecture: 80.
- CUDA compiler: NVIDIA HPC SDK 25.5 CUDA 12.9 `nvcc`.
- Cray compiler wrappers: `CC` and `cc`.

Legion provenance for LegionSolvers:

- Legion repository path at collection time: `/pscratch/sd/r/rchanani/legion`.
- Recorded Legion commit: `26dc03e562c62b218a318b45a57d5f756afe3614`.
- Recorded branch: `gpudeppart`.

LegionSolvers provenance:

- LegionSolvers path at collection time:
  `/pscratch/sd/r/rchanani/LegionSolvers`.
- Recorded LegionSolvers commit: `eea439021fca3714134bdc782a38ccddec77d765`.
- Recorded branch: `main`.
- Local diff was present; include `provenance/legionsolvers_local_diff.diff`.
- Build cache reports `CMAKE_BUILD_TYPE=RelWithDebInfo`; release flags are still
  recorded as `-O3 -DNDEBUG`, while RelWithDebInfo flags are `-O2 -g -DNDEBUG`.

If drafting text about optimized builds, be precise:

- Realm microbenchmarks/application-derived benchmark build was Release
  optimized.
- LegionSolvers build provenance says RelWithDebInfo; do not call that strict
  Release unless the paper/source confirms otherwise.

## Statistical Methodology

Use one methodology across all three final data sets:

- plotted points are medians of three independent executions;
- where raw data is included, min/max ranges are available for audit;
- current figures do not show error bars unless the paper explicitly adds them.

## Microbenchmarks

Final graph input:

- `data/final/microbenchmarks.csv`

Configuration:

- operations: point-valued `image` and `preimage`;
- dimensions: 1D to 1D, 2D to 2D, 3D to 3D;
- 1 million field elements in every dimension:
  - 1D: `1000000`;
  - 2D: `1000 x 1000`;
  - 3D: `100 x 100 x 100`;
- dense subspaces use `-f 1`;
- sparse subspaces use `-f 5`, meaning 5 percent point retention;
- field generation uses block-random mode with `block_volume=1024`;
- scratch-buffer values:
  `1, 2, 3, 4, 5, 7, 10, 15, 20, 25, 30, 40, 50, 75, 100`;
- buffer value `b` means
  `S_lower + (b/100) * (S_upper - S_lower)`;
- each Perlmutter shard used one exclusive GPU node with one GPU visible;
- common flags include `-ll:gpu 1 -ll:cpu 1 -ll:fsize 8192 -dp:workers 1 -dp:hpool 256 -nocheck -block_random -block_volume 1024`.

Timing boundary:

- input construction happens before timing;
- GPU input field instances are copied into GPU framebuffer memory before timing;
- scratch allocation happens before timing;
- GPU warmup call happens before timed GPU measurement;
- timed interval starts immediately before the Realm dependent-partitioning API
  call and ends after waiting on the returned event;
- Realm internal scheduling, tiling/retry/backoff, BVH/canonicalization work
  performed by the operation, and output publication are included;
- host-device copies into GPU input instances and scratch allocation are not
  included.

Correctness:

- final microbenchmark collection used `-nocheck`, so this timing run did not
  compare GPU output partitions against CPU output partitions.
- The benchmark source contains check routines, but they were disabled for this
  final timed data collection.

## Application-Derived Weak Scaling

Final graph input:

- `data/final/weak_scaling_raw.csv`

Configuration:

- apps: Circuit, Pennant, MiniAero;
- scale: `p = 1, 2, 3, 4` on one Perlmutter GPU node;
- each point has 3 independent repetitions;
- Realm uses `-ll:gpu p`, `-ll:util p`, and `-dp:workers p`;
- memory flags: `-ll:fsize 32000 -ll:csize 32768 -ll:zsize 4096`;
- buffer: `-buffer 100`;
- CPU timing source: run with intersection optimization enabled, use `cpu_us`;
- GPU timing source: run with `-dp:noisectopt`, use `gpu_us`.

Problem sizes:

- Circuit: `-n p -e 4500000*p -p p`.
- Pennant: `-nzx 675*p -nzy 2096 -p p`.
- MiniAero: `-gx p -gy 1202 -gz 1202 -p p`.

Operation sequences from copied `source/realm/benchmark.cc`:

- Circuit: by-field for nodes by subcircuit; preimage for edges by input-node
  partition; one-to-one image over edge partitions; differences, union, and two
  intersections for ghost/shared/private node sets.
- Pennant: by-field to identify bad sides; conditional image to bad zones;
  conditional difference to good zones; by-field for zones by color; preimage
  for sides; one-to-one image for points.
- MiniAero: by-field for cells by block; preimage for faces by left-cell
  partition; one by-field per block for face types; if more than one block,
  one-to-one image for ghost cells.

Correctness:

- weak-scaling runner does not pass `-nocheck`; benchmark default CPU/GPU
  partition comparison runs after timing.

## Dynamic Repartitioning

Final graph input:

- `data/final/repartitioning.csv`

Configuration:

- benchmark modifies LegionSolvers/kdrsolvers conjugate-gradient solver;
- 2000 CG iterations;
- CSR discretization of the one-dimensional negative Laplacian with
  `100000000` unknowns and approximately `300000000` nonzeros;
- four GPUs and four vector pieces;
- solver executes on GPUs in both configurations;
- CPU/GPU refer only to dependent-partitioning backend;
- `repartition_interval=0` disables repartitioning and is the baseline;
- for interval `k > 0`, the benchmark repartitions every `k` iterations except
  after the final iteration.

Intervals:

`0, 1, 2, 5, 10, 25, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000, 1200, 1400, 1500, 1600, 1800, 2000`

Timing boundary:

- problem construction, vector initialization, solver setup, and initial
  partitioning occur before timing;
- timed interval covers the complete CG iteration loop, including periodic
  repartitioning and dependent-partitioning work, through completion.

Aggregation:

- median/min/max of 3 independent executions per interval and backend.

## Expected Artifact Sections

The AD template asks for:

- Overview of Contributions and Artifacts;
- Paper's Main Contributions;
- Computational Artifacts and DOI(s);
- Artifact Identification;
- relationship to contributions;
- expected result;
- time to reproduce;
- hardware/software/datasets/install;
- experiment workflow;
- expected outputs.

Use `templates/sc26-artifact-description.zip` for the template source.

## Publication Notes

The artifact is published as a tagged GitHub release archived by Zenodo.

- GitHub: https://github.com/rohanchanani/gpu-dependent-partitioning-artifact
- DOI: https://doi.org/10.5281/zenodo.21741212

Do not cite local paths like `/pscratch` or `~/Downloads` as artifact locations
in the final AD. They are provenance only.
