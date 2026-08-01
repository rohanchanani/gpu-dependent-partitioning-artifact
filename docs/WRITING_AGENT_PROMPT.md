# Prompt for the AD Writing Agent

You are writing the Artifact Description / Artifact Evaluation appendix for a
Supercomputing submission on GPU-accelerated Realm dependent partitioning.

Inputs I am providing:

- the full paper draft;
- the SC26 AD/AE template;
- this artifact package directory;
- the sample AD from last year, if included separately.

Your task:

1. Produce a ready-to-submit AD appendix in the conference template.
2. Do not invent methodology details. Use the factual context in
   `docs/AD_WRITING_CONTEXT.md`, `docs/ARTIFACT_FILE_MAP.md`, the manifests,
   and the provenance files.
3. Use one computational artifact unless the supplied public DOI information
   explicitly splits the artifact into multiple DOIs.
4. If the DOI is not supplied, leave a clearly marked `TODO_DOI` placeholder.
5. Tie the artifact to the paper's actual contribution labels. If the paper's
   contribution labels differ from the suggested context, follow the paper.
6. State that final plotted points use the median of three independent
   executions.
7. Distinguish final data from raw/supporting data:
   - final graph inputs are in `data/final/`;
   - raw/summary audit data are in `data/raw/`;
   - provenance is in `provenance/`.
8. Describe the quick reproduction path as regenerating figures from supplied
   CSVs with the plotting scripts.
9. Describe full experimental reproduction as Perlmutter-specific and requiring
   NERSC allocation/GPU nodes.
10. Be precise about timing boundaries:
    - microbenchmarks/application-derived benchmarks exclude input construction,
      host-to-device copies, and scratch allocation;
    - repartitioning includes the CG loop plus periodic repartitioning work.
11. Be precise about builds:
    - Realm benchmark build was Release optimized;
    - LegionSolvers provenance says RelWithDebInfo, so do not call it pure
      Release unless the paper separately confirms that.
12. Keep the AD concise and practical, similar in level of detail to the sample
    AD: hardware, software, build/deploy notes, workflow, expected outputs, and
    runtime estimates.

Important files:

- `README.md`
- `docs/AD_WRITING_CONTEXT.md`
- `docs/ARTIFACT_FILE_MAP.md`
- `docs/PUBLICATION_STEPS.md`
- `data/final/microbenchmarks.csv`
- `data/final/weak_scaling_raw.csv`
- `data/final/repartitioning.csv`
- `data/raw/*`
- `provenance/perlmutter_provenance.txt`
- `provenance/realm_local_benchmark_patches.diff`
- `provenance/legionsolvers_local_diff.diff`
- `templates/sc26-artifact-description.zip`

Output:

- a complete AD/AE appendix TeX file ready to paste into the submission;
- a short list of any unresolved placeholders, especially DOI, license, or
  public repository URL.
