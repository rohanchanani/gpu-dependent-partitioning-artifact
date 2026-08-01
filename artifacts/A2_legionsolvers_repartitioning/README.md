# A2: Modified LegionSolvers Repartitioning App

Relationship to paper:

This artifact supports the dynamic repartitioning experiment. It contains the
LegionSolvers/kdrsolvers application context used to evaluate periodic
dependent repartitioning inside a conjugate-gradient solver.

Contents:

- `source/`: copied LegionSolvers source tree.
- `patches/legionsolvers_local_diff.diff`: local LegionSolvers patch recorded
  at collection time.
- `scripts/repart`, `scripts/repart_initial_sweep`,
  `scripts/run_repart_initial_sweep.sbatch`: repartitioning sweep scripts.
- `provenance/`: LegionSolvers build and git provenance.

Recorded provenance:

- LegionSolvers path: `/pscratch/sd/r/rchanani/LegionSolvers`.
- LegionSolvers commit: `eea439021fca3714134bdc782a38ccddec77d765`.
- LegionSolvers branch: `main`.
- Build cache path:
  `/pscratch/sd/r/rchanani/LegionSolvers/scratch/LegionSolversBuild/pm_a100_ofi_cuda_release/CMakeCache.txt`.
- Build type recorded by CMake: `RelWithDebInfo`.
- CUDA architecture: `80`.
- CUDA compiler: NVIDIA HPC SDK 25.5 CUDA 12.9 `nvcc`.

Experiment summary:

- 2000 conjugate-gradient iterations.
- Four GPUs and four vector pieces.
- CPU/GPU labels in the result data refer to the dependent-partitioning backend,
  not the solver backend.
- `repartition_interval=0` disables periodic repartitioning and is the baseline.
