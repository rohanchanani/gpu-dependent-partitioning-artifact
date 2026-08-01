# SC26 Reproducibility Notes

Use the official SC26 pages for current process language:

- AD/AE Process and Badges:
  https://sc26.supercomputing.org/program/papers/reproducibility-appendices-badges/
- AD/AE Appendices:
  https://sc26.supercomputing.org/program/papers/ad-ae-appendices/

Relevant facts from the SC26 process page:

- Artifact Description is mandatory for submitted papers.
- Artifact Evaluation is optional for accepted papers.
- Artifact Identification should connect paper contributions `C_i` to
  computational artifacts `A_j`.
- The AD Appendix should provide information needed to reproduce the artifacts,
  including input datasets, source-code links, software dependencies, and
  hardware dependencies.

For persistent artifact hosting, use a DOI-backed archival repository. Older SC
guidance explicitly notes that GitHub by itself does not mint a DOI and should
be paired with Zenodo or FigShare for DOI-backed releases. The practical path is
a tagged GitHub release archived through Zenodo.
