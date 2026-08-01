# Artifact File Map

## Final Paper Data

Use these files for plotting and for the artifact description:

- `data/final/microbenchmarks.csv`
- `data/final/weak_scaling_raw.csv`
- `data/final/repartitioning.csv`

Do not use older exploratory CSVs outside this artifact package for final
methodology claims.

## Microbenchmarks

Final file:

- `data/final/microbenchmarks.csv`

Supporting files:

- `data/raw/microbenchmarks/manifest.json`
- `data/raw/microbenchmarks/tile_sweep_publication_raw.csv`
- `data/raw/microbenchmarks/tile_sweep_publication_points.csv`
- `data/raw/microbenchmarks/tile_sweep_publication_summary_log_axis.csv`
- `data/raw/microbenchmarks/tile_sweep_publication_failures.csv`

Key facts:

- 360 final summary rows.
- 1080 raw rows.
- 0 recorded failures.
- Operations: `image`, `preimage`.
- Dimensions: `1d -> 1d`, `2d -> 2d`, `3d -> 3d`.
- Densities: dense uses `-f 1`; sparse uses `-f 5`.
- Buffer values: `1, 2, 3, 4, 5, 7, 10, 15, 20, 25, 30, 40, 50, 75, 100`.
- Repetitions: 3.
- Elements: 1D uses `1000000`, 2D uses `1000 x 1000`, 3D uses `100 x 100 x 100`.
- Field mode: block-random with `block_volume=1024`.
- CPU timing source: normal run, use `cpu_us`.
- GPU timing source: `-dp:noisectopt` run, use `gpu_us`.
- Microbenchmark collection used `-nocheck`; timings do not include host-to-device
  input copies or scratch allocation.

## Application-Derived Weak Scaling

Final file:

- `data/final/weak_scaling_raw.csv`

Supporting files:

- `data/raw/weak_scaling/manifest.json`
- `data/raw/weak_scaling/weak_scaling_all_apps_median_summary.csv`
- `data/raw/weak_scaling/weak_scaling_circuit_median_summary.csv`
- `data/raw/weak_scaling/weak_scaling_pennant_median_summary.csv`
- `data/raw/weak_scaling/weak_scaling_miniaero_median_summary.csv`

Key facts:

- 36 raw rows.
- Apps: Circuit, Pennant, MiniAero.
- Scales: `p = 1, 2, 3, 4`.
- Repetitions: 3.
- One Perlmutter GPU node; Realm uses `-ll:gpu p`, `-ll:util p`, and
  `-dp:workers p`.
- Buffer: `-buffer 100`.
- CPU timing source: intersection optimization enabled, use `cpu_us`.
- GPU timing source: `-dp:noisectopt`, use `gpu_us`.
- The runner does not pass `-nocheck`; the benchmark's CPU/GPU partition
  comparison runs after timing.

## Dynamic Repartitioning

Final file:

- `data/final/repartitioning.csv`

Supporting files:

- `data/raw/repartitioning/repartitioning_raw.csv`
- `data/raw/repartitioning/repartitioning_summary_with_ranges.csv`
- `data/raw/repartitioning/merge.log`

Key facts:

- 27 final summary rows.
- 162 raw rows.
- Median/min/max of 3 independent executions per interval and backend.
- Repartition intervals:
  `0, 1, 2, 5, 10, 25, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000, 1200, 1400, 1500, 1600, 1800, 2000`.
- `repartition_interval=0` is the no-repartitioning baseline.
- Solver executes on four GPUs; CPU/GPU denote the dependent-partitioning
  backend, not the solver backend.

## Plotting

Run:

```bash
./scripts/plotting/reproduce_figures.sh
```

This writes PNG and PDF outputs to `figures/`.
