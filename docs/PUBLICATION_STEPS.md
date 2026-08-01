# Publication Steps

Published artifact:

- GitHub: https://github.com/rohanchanani/gpu-dependent-partitioning-artifact
- DOI: https://doi.org/10.5281/zenodo.21741212

These are the exact external steps needed after the local package is reviewed.

## 1. Confirm License

This package currently uses Apache-2.0 for the top-level artifact scripts,
plotting code, data files, and documentation. Copied Realm, Legion, and
LegionSolvers source snapshots and patches remain under their original upstream
project licenses.

## 2. Create GitHub Repository

In GitHub:

1. Go to `https://github.com/new`.
2. Repository owner: choose your account or project organization.
3. Repository name: `gpu-dependent-partitioning-artifact`.
4. Visibility: public if allowed by the submission plan.
5. Do not add a README, `.gitignore`, or license through the web UI if you are
   going to push this prepared directory directly.
6. Click `Create repository`.

## 3. Push This Package

From this directory:

```bash
git init
git add .
git commit -m "SC26 artifact package"
git branch -M main
git remote add origin git@github.com:OWNER/gpu-dependent-partitioning-artifact.git
git push -u origin main
git tag -a v1.0-sc26-ad -m "SC26 artifact package"
git push origin v1.0-sc26-ad
```

Replace `OWNER` with the actual GitHub owner.

## 4. Archive With Zenodo

1. Go to `https://zenodo.org`.
2. Sign in.
3. Connect GitHub if not already connected.
4. Enable Zenodo archiving for `gpu-dependent-partitioning-artifact`.
5. In GitHub, create a release from tag `v1.0-sc26-ad`.
6. Wait for Zenodo to archive the release.
7. Copy the minted DOI.

## 5. Fill AD DOI

Use the Zenodo DOI as the computational artifact URL in the AD.

If the artifact must remain private during review, check the SC submission
system's current instructions for private review links. Do not rely on local
Perlmutter paths, Dropbox, or a mutable personal zip as the permanent artifact.
