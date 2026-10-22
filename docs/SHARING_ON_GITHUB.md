# Sharing on GitHub

## Repository

The public repository is [anthonyjclarke/Xargons_Revenge_C16_v2](https://github.com/anthonyjclarke/Xargons_Revenge_C16_v2). I work on `dev` and merge verified checkpoints into `main`. Annotated tags mark releases, from `v1.0.0`, the verified preservation build, to `v1.4.1`; the [Version Tags](#version-tags) section lists them. [`CHANGELOG.md`](../CHANGELOG.md) records the commit for each, and a published tag is never moved.

`.gitignore` leaves out `build/`, PlatformIO caches, the Python virtual environment, caches and macOS metadata. It keeps every original `.prg`, `.seq`, `.d64`, `.ZIP`, text export and image. `.gitattributes` turns off line-ending and whitespace changes for `Original Source Recovered/`, `Original Artifacts/` and `Other Versions/`, so the 1992 CRLF exports and the CR-only disk extractions stay byte for byte. `.editorconfig` does the same for editors.

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

---

## Clone or Update

```bash
git clone https://github.com/anthonyjclarke/Xargons_Revenge_C16_v2.git
cd Xargons_Revenge_C16_v2
git switch dev
```

For later work, use `dev`, run the checks above, then commit with a `type(scope): description` message. Merge into `main` only when a checkpoint is verified.

---

## Version Tags

| Tag      | Release                                         |
| :------- | :---------------------------------------------- |
| `v1.0.0` | Verified preservation build                     |
| `v1.1.0` | Analysis, graphics, porting guide and handbook  |
| `v1.2.0` | Game v1 and game v2, with comparison captures   |
| `v1.3.0` | Plus/4 World copies and the original tape       |
| `v1.4.0` | Second copy of the three development disks      |
| `v1.4.1` | README context and related repositories         |

Later verified checkpoints get new annotated tags on `main`. Leave published tags alone, so their source, documentation and recorded evidence can still be reproduced.
