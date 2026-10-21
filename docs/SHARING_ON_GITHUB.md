# Sharing on GitHub

## Repository

The public repository is [anthonyjclarke/Xargons_Revenge_C16_v2](https://github.com/anthonyjclarke/Xargons_Revenge_C16_v2). I work on `main`. Annotated tags mark releases: `v1.0.0` is the verified preservation build and `v1.1.0` the documentation, analysis and handbook release. [`CHANGELOG.md`](../CHANGELOG.md) records the commit for each, and a published tag is never moved.

`.gitignore` leaves out `build/`, PlatformIO caches, the Python virtual environment, caches and macOS metadata, and my local working brief. It keeps every original `.prg`, `.seq`, `.d64`, `.ZIP`, text export and image. `.gitattributes` turns off line-ending and whitespace changes for `Original Source Recovered/` and `Original Artifacts/`, so the 1992 CRLF exports and the CR-only disk extractions stay byte for byte. `.editorconfig` does the same for editors.

---

## Continuous Integration

`.github/workflows/build.yml` runs on every push and pull request, on Ubuntu with Python 3.11, cc65 from apt and PlatformIO 6.1.19. It:

1. records tool versions;
2. builds from the preserved sources;
3. runs the regression tests (the VICE test is skipped, because the runner has no `xplus4`);
4. builds the three PlatformIO environments and compares both game versions in each with the direct build;
5. checks the HTML handbook is up to date with Node 20;
6. uploads both game PRGs, the generated alien sources, reports, generated source, labels, map and debug file.

The VICE verification, rule probes and graphics are run locally and their results committed under `docs/`. CI doesn't repeat them.

---

## Final Local Checks

```bash
./build.sh
make test
pio run -e c16 -e c16_debug
make verify
make probes
make docs-check
make test-docs
git status --short
```

If you change the source, refresh the evidence in `docs/verification/`, `docs/images/` and `docs/analysis/` only after reviewing the changed bytes and rerunning the checks, and add a new changelog entry and tag rather than moving an old one.
