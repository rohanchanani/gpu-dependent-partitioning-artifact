# A1: Modified Legion/Realm Runtime

Relationship to paper:

This artifact supports the paper's implementation contribution: GPU-accelerated
dependent partitioning in Realm/Legion.

Contents:

- `source/realm/`: copied Realm benchmark and dependent-partitioning source
  files relevant to the evaluation.
- `patches/realm_local_benchmark_patches.diff`: local runtime/benchmark patch
  set recorded at collection time.
- `provenance/perlmutter_provenance.txt`: git commits, branch names, dirty
  status, and build cache highlights.
- `provenance/realm_build_pm_deppart_CMakeCache.txt`: CMake configuration for
  the Realm benchmark build.
- `provenance/legion_repo_provenance.txt`: Legion git provenance.
- `provenance/legion_install_cmake/`: installed Legion CMake metadata.

Recorded runtime provenance:

- Realm path: `/pscratch/sd/r/rchanani/realm`.
- Realm commit: `9b026a46941f95a3115d8b2fb4dd43d2ca532323`.
- Realm branch: `review-tiling`.
- Legion path: `/pscratch/sd/r/rchanani/legion`.
- Legion commit: `26dc03e562c62b218a318b45a57d5f756afe3614`.
- Legion branch: `gpudeppart`.

Build provenance:

- Realm benchmark build type: `Release`.
- C++ release flags: `-O3 -DNDEBUG`.
- CUDA release flags: `-O3 -DNDEBUG`.
- CUDA architecture: `80`.
- CUDA compiler: NVIDIA HPC SDK 25.5 CUDA 12.9 `nvcc`.
- Cray compiler wrappers: `CC` and `cc`.
