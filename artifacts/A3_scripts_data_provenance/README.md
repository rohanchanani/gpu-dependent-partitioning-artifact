# A3: Scripts, Data, and Provenance

Relationship to paper:

This artifact ties the runtime and application artifacts to the evaluation
figures. It contains final CSV data, raw audit data, plotting scripts, runner
scripts, manifests, and provenance.

Final graph data:

- Top-level mirror: `../../data/final/`
- Raw/supporting data in this artifact: `data/raw/`

Final CSVs:

- `microbenchmarks.csv`
- `weak_scaling_raw.csv`
- `repartitioning.csv`

Plotting:

```bash
python3 -m pip install pandas matplotlib
./scripts/plotting/reproduce_figures.sh
```

Methodology summary:

- All plotted points use the median of three independent executions.
- Microbenchmark final data includes image/preimage, dense/sparse, and
  1D/2D/3D buffer sweeps.
- Weak scaling final data includes Circuit, Pennant, and MiniAero for
  `p = 1, 2, 3, 4`.
- Repartitioning final data includes 27 repartition intervals from no
  repartitioning through 2000 iterations.
