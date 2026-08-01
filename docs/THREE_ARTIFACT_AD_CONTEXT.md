# Three-Artifact AD Context

Use this context for an AD that mirrors the sample structure with multiple
computational artifacts.

All three artifacts are archived in one public repository/archive:

- Repository: https://github.com/rohanchanani/gpu-dependent-partitioning-artifact
- Three-artifact release tag: `v2.2-sc26-ad-three-artifacts`
- DOI: fill in after publishing the `v2.2-sc26-ad-three-artifacts` release on
  GitHub/Zenodo.

The older DOI `https://doi.org/10.5281/zenodo.21741212` corresponds to the
earlier one-artifact packaging and should not be used for the final
three-artifact AD unless Zenodo explicitly aliases it to the new version.

## Artifact IDs

### A1: Modified Legion/Realm Runtime

Path in archive:

`artifacts/A1_legion_realm_runtime/`

Description:

This artifact contains the modified Realm/Legion runtime context used for
GPU-accelerated dependent partitioning, including copied source snapshots,
patches, commit provenance, and optimized Realm benchmark build metadata.

Supports:

- implementation contribution;
- microbenchmark and application-derived dependent-partitioning evaluation.

Related paper elements:

- image/preimage microbenchmark figures;
- Circuit/Pennant/MiniAero weak-scaling figures;
- dynamic repartitioning figure indirectly through the Legion runtime used by
  LegionSolvers.

### A2: Modified LegionSolvers Repartitioning App

Path in archive:

`artifacts/A2_legionsolvers_repartitioning/`

Description:

This artifact contains the modified LegionSolvers/kdrsolvers application context
used for the dynamic repartitioning experiment, including source snapshot,
local patch, run scripts, and build provenance.

Supports:

- dynamic repartitioning contribution and evaluation.

Related paper elements:

- dynamic repartitioning figure.

### A3: Scripts, Data, and Provenance

Path in archive:

`artifacts/A3_scripts_data_provenance/`

Description:

This artifact contains the final paper data, raw data, manifests, plotting
scripts, Perlmutter runner scripts, and provenance that tie A1 and A2 to the
paper's evaluation results.

Supports:

- all evaluation figures;
- reproducibility of plotted results from supplied CSVs;
- auditability of the collection methodology.

Related paper elements:

- image/preimage microbenchmark figures;
- Circuit/Pennant/MiniAero weak-scaling figures;
- dynamic repartitioning figure.

## Computational Artifacts Section Sketch

```latex
\begin{description}
\item[$A_1$] TODO_NEW_THREE_ARTIFACT_DOI % Modified Legion/Realm runtime
\item[$A_2$] TODO_NEW_THREE_ARTIFACT_DOI % Modified LegionSolvers repartitioning app
\item[$A_3$] TODO_NEW_THREE_ARTIFACT_DOI % Scripts, data, and provenance
\end{description}
```

The AD template allows multiple computational artifacts to be archived under a
single DOI. Use the DOI minted for the `v2.2-sc26-ad-three-artifacts` release
for all three entries unless the artifacts are split into separate archives.

## Artifact Table Sketch

```latex
\begin{center}
\begin{tabular}{rll}
\toprule
Artifact ID & Contributions & Related Paper Elements \\
\midrule
$A_1$ & Runtime implementation & Microbenchmarks; weak scaling; repartitioning \\
$A_2$ & Dynamic repartitioning & Dynamic repartitioning figure \\
$A_3$ & Evaluation data/scripts & All evaluation figures \\
\bottomrule
\end{tabular}
\end{center}
```

Use the actual paper contribution labels and figure numbers when drafting.
