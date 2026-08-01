# Prompt for the AD Writing Agent

You are writing the Artifact Description / Artifact Evaluation appendix for a
Supercomputing submission on GPU-accelerated Realm dependent partitioning.

Inputs I am providing:

- the full paper draft;
- the SC26 AD/AE template;
- this three-artifact package directory;
- the sample AD from last year, if included separately.

Use three computational artifact IDs:

- `$A_1$`: Modified Legion/Realm Runtime.
- `$A_2$`: Modified LegionSolvers Repartitioning App.
- `$A_3$`: Scripts, Data, and Provenance.

All three artifacts are currently archived under:

https://doi.org/10.5281/zenodo.21741212

If the user supplies a newer DOI for this three-artifact layout, use that newer
DOI instead.

Your task:

1. Produce a ready-to-submit AD appendix in the conference template.
2. Mirror the multi-artifact structure of the supplied sample AD, but use the
   factual content in this package.
3. Do not invent methodology details. Use `docs/THREE_ARTIFACT_AD_CONTEXT.md`,
   artifact-local READMEs, manifests, and provenance files.
4. Tie each artifact to the paper's actual contribution labels and figure
   numbers.
5. State that final plotted points use the median of three independent
   executions.
6. Distinguish quick reproduction from full reproduction:
   - quick reproduction regenerates plots from supplied CSVs;
   - full reproduction reruns Perlmutter experiments and requires NERSC GPU
     allocation/access.
7. Be precise about builds:
   - Realm benchmark build was Release optimized;
   - LegionSolvers provenance records `RelWithDebInfo`.
8. Be precise about timing boundaries:
   - microbenchmarks/application-derived benchmarks exclude input construction,
     host-device input copies, and scratch allocation;
   - repartitioning includes the timed CG loop plus periodic repartitioning
     work.

Important files:

- `README.md`
- `docs/THREE_ARTIFACT_AD_CONTEXT.md`
- `artifacts/A1_legion_realm_runtime/README.md`
- `artifacts/A2_legionsolvers_repartitioning/README.md`
- `artifacts/A3_scripts_data_provenance/README.md`
- `data/final/microbenchmarks.csv`
- `data/final/weak_scaling_raw.csv`
- `data/final/repartitioning.csv`
- `templates/sc26-artifact-description.zip`

Output:

- a complete AD/AE appendix TeX file ready to paste into the submission;
- a short list of any unresolved placeholders, especially if figure numbers or
  final DOI differ from the package context.
