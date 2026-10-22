# Changelog

All notable changes to the Xargon's Revenge C16 preservation project. Dates are DD-MM-YYYY.

---

## [1.4.1] 22-10-2026

README context. Game v1 and v2 are unchanged.

### Added

- README badges (release, rights, target, CPU, assembler, build, emulator, `OBJ` match).
- README sections up front: "Two Versions of One Game", summarising why two versions exist and how the evidence settled it, and "Related Repositories", linking Xargon Wars C16 and explaining how this repository differs from the first restoration, Xargons_Revenge_C16.

### Changed

- `scripts/build_docs.mjs` shows shields.io badges as text labels in the offline handbook instead of rejecting them as remote images.

---

## [1.4.0] 22-10-2026

Second 2026 copy of all three development disks, verified and documented (commit `a76a1ae`, annotated tag `v1.4.0`). Game v1 and v2 are unchanged (SHA-256 `32c13c88…adce33` and `0ee0a823…397665`).

### Added

- `Original Source Recovered/2026 - 2nd Copy/`: the Xargon's Revenge (`DISK9`), Revenge of Xargon (`DISK8`) and 5 Lives (`DISK10`) disks, each with a photo, `d64copy` sector images, CBMXfer output and the matching 1992 export. Preserved as supplied; verified, never a build input.
- `docs/DEVELOPMENT_DISKS.md`: what each disk holds, what the copying tools did, the damaged 5 Lives disk sector by sector, and how the builds fit together (`DISK8` → `DISK10` → `DISK9` → the 1985 cassette).
- `scripts/verify_second_copy.py` and `docs/verification/second-copy.json`: tolerant D64 reading with error maps, 1992 comparison (text, bytes, detokenized BASIC), deleted entries, `OBJ` remnants in free sectors, and a merged 5 Lives image in `build/second-copy/` for analysis.
- A regression test for the second copy (skipped when the folder or `Other Versions/` is absent).

### Changed

- The six fallback modules are confirmed on a 2026 sector copy of the source disk, identical to their 1992 text. The first 2026 images are CBMXfer rebuilds that drop 15- and 16-character file names; the build keeps its inputs and output.
- The disk labels are matched to the disks and 1992 exports, closing that open question. The first 2026 "Side 1" image is the start of the 5 Lives disk, and "Side 2" is the source disk; all three disks are single-sided.
- Renamed the first 2026 copies, contents byte-identical, into `Original Source Recovered/2026 - 1st Copy/` with the second copy's disk names: `Xargon's Revenge/Xargon's Revenge.d64` and `- Extracted/` (were `2026/Xargon'sRevenge-C16.d64` and `Xargons-Revenge-C16-Side2/`), and `Xargons Revenge - 5 Lives/Xargons Revenge - 5 Lives (partial).d64` and `(partial) - Extracted/` (were `2026/XargonsRevenge-C16.d64` and `Xargons-Revenge-C16-Side1/`). Build paths, tests, generated references and docs updated; the build output is unchanged.
- Plus/4 World's "early stages" is traced to the `DISK8` build (`OBJ`, `FRAK!`, `LANDSCAPE-1`), and its loading-picture disk to `DISK10`.
- The packaging's "3 lives" is explained by the earlier `DISK8` build; "96 levels" remains open.
- Game Versions, Other Versions, Gremlin Archive, Source Inventory, Source and Validation, Artifacts, History and Credits, Graphics, Codebase Analysis, README, `src/README.md`, TESTING and `CLAUDE.md` updated to match, and the comparison page regenerated.

### Known limits

- The 5 Lives disk has 40 unreadable sectors in both reads and nine decayed ones; the 1992 export is its complete copy.
- The source of the cassette's tape loader isn't on any development disk.

---

## [1.3.0] 22-10-2026

Comparison with copies of the game downloaded from Plus/4 World, including a tape of the original 1985 cassette, and the Gremlin Archive reference (commit `bc16973`, annotated tag `v1.3.0`). Game v1 and v2 are unchanged (SHA-256 `32c13c88…adce33` and `0ee0a823…397665`).

### Added

- `docs/OTHER_VERSIONS.md`: what each of six downloaded copies contains, compared with game v1 and v2 and with `BJH`, `LANDSCAPE-1`, `LANDSCAPE-2` and `FRAK!`. The original release tape is byte-identical to game v2 when the game starts, and its own `$0C00` loader was traced making the faulty alien copy. Appendix A gives the Plus/4 World link, mirrors and SHA-256 for every file, plus the Gremlin Archive source of the development copies; Appendix B lists the site's entries not yet examined.
- `docs/GREMLIN_ARCHIVE.md`: Mark Hardisty's book *A Gremlin in the Works* and his Gremlin Graphics Archive, the 1992 disk list from the archive's `READ.ME`, how to cite them, and how this project's files match the archive's `DISK9` and `DISK10`. The first five sections are written for reuse in the other Micro Projects reconstructions.
- `scripts/compare_other_versions.py` and `scripts/other_versions_template.html`: place each copy in memory as its own loader would, load both tapes in VICE to the game's entry, and write `docs/analysis/other-versions.html`, a self-contained page decoding the aliens, landscape, font, banner and ship of every copy.
- VICE captures of every copy, including both Novaload loading screens, in `docs/images/other-versions/`.
- The `Other Versions/` folder as a read-only comparison input (`CLAUDE.md`, Source Inventory), and a `CLAUDE.md` note on loading C16 tapes in VICE.
- History: a section on the Gremlin Archive and the book.

### Changed

- Game Versions: v2 is now confirmed as the released game from the original cassette, not just inferred from the running version. Open questions updated, including the archive's "Xargon's Revenge – 5 lives" disk.
- Artifacts: the running version is byte-identical to Plus/4 World's main download, and a packed copy of the original release.
- Source Inventory: the 1992 ZIP is also the archive's `DISK9.ZIP`.

### Known limits

- My own original disks, the archive's `DISK8` and `DISK10`, the Omnibus II and OPI copies haven't been examined yet.
- Plus/4 World lists two Gremlin cassette releases; which one the tape image is isn't recorded.

---

## [1.2.0] 21-10-2026

Two playable game versions, built from the same preserved source (commit `11b5b37`, annotated tag `v1.2.0`). Game v1 (development) is unchanged (SHA-256 `32c13c88…adce33`).

### Added

- Game v2 (cassette release), `build/xargons-revenge-v2.prg` (SHA-256 `0ee0a823…397665`): the alien data placed as the release tape loader copied it, derived from `BJH` by rule. In VICE it equals the decompressed running version in the aliens, landscape, code and font.
- Generated alien data sources `build/aliens-v1.s` and `build/aliens-v2.s`, assembled into the PRGs with per-sheet provenance comments.
- `docs/GAME_VERSIONS.md`: how the versions arise, the tape loader's copy loop, the sheet-by-sheet effect, what is the same, and open questions.
- `scripts/capture_versions.py` and `make versions`: VICE captures of both versions on all 16 sheets with identical game state (`docs/images/versions/`, `docs/verification/game-versions.json`); sheets 1–4 are pixel-identical and sheets 5–16 differ.
- Figures `versions-sheets-01-08.png`, `versions-sheets-09-16.png` and `versions-detail.png`.
- `docs/verification/release-tape-loader.s`, a disassembly of the loader left at `$0C00` in the running version (evidence only).
- PlatformIO environment `c16_v2` (upload runs game v2), `run_vice.py --game-version`, `make run-v2`, VS Code tasks for both versions, and a test of the v2 rule.
- History: answers of 21 October 2026, and open questions on "The Mega", the disk labels and the packaging.

### Changed

- Outputs renamed from `build/xargons-revenge.prg` to `build/xargons-revenge-v1.prg` and `-v2.prg`. CI compares both versions in all three PlatformIO environments.
- `asset-data.json` key `aliens_running_version` renamed `aliens_v2`.

### Fixed

- v1.1.0 said the running version's aliens on sheets 5–16 were their own designs "shifted". In fact each page copies from `BJH` offset *p*, so sheets 5–16 show the sheet 1–4 designs raised 1–3 rows, and twelve designs never appear. Corrected in the analysis, graphics, validation and README.

### Known limits

- No original cassette has been examined; that v2 is the released game rests on the downloaded copy carrying a tape loader.
- The packaging's "3 lives" and "96 levels" match neither version.

---

## [1.1.0] 21-10-2026

Documentation, analysis, graphics and handbook release (commit `5336112`, annotated tag `v1.1.0`). The game PRG is unchanged (SHA-256 `32c13c88…adce33`).

### Added

- `CODEBASE_ANALYSIS.md`: states, memory map, raster interrupt chain, input, ship, laser, aliens, fuel, waves, scoring, death, landscape, title, sound, tools, self-modifying code, concurrency, dormant code, statistics, modification map and reading order.
- `docs/PORTING_GUIDE.md`: compatibility contracts, a proposed portable state model and interfaces, timing domains, a compatibility-choice table, milestones, trace format and conformance tests.
- `docs/GRAPHICS.md` and `docs/analysis/graphics/`: decoded aliens (source against running version), ship, landscape, title banner and screen composition, an alien animation and `graphics-manifest.json` with input and output hashes and pixel checks.
- `docs/analysis/`: generated `CODE_REFERENCE.md`, `codebase-index.json`, `asset-data.json` (graphics, 56 tables, movement patterns, VICE captures, banner provenance) and four SVG glyph atlases.
- Guides: `QUICKSTART.md`, `TESTING.md`, `RIGHTS.md`, `CLAUDE.md`, `src/README.md`, and under `docs/` the Artifact Catalogue, Build and Run, History and Credits, Source and Validation, Source Inventory, Sharing on GitHub and HTML documentation guide.
- `docs/XARGONS_REVENGE.html`: offline handbook of 17 chapters, generated by `scripts/build_docs.mjs` from `docs/handbook.json` with the Tycoon Tex templates (now parameterised) and vendored Marked 17.0.5 and Mermaid 10.9.3.
- `scripts/analyze_codebase.py`, `scripts/render_game_graphics.py` (Pillow 10.1 or later), `test/test_docs.mjs`, and Makefile targets `docs`, `docs-html`, `docs-watch`, `docs-check` and `test-docs`.
- Rule probes for wave completion (the game ends after wave 80) and for resets during play (VICE resumes in ROM at `$F2A4`, not at the reset trap).
- VICE captures of title RAM, gameplay after 256 main-loop passes, the Side 1 loading screen in both flash phases, and the measured 128-entry TED palette (`docs/verification/ted-palette.json`).
- CI steps that check the handbook is current and run the generator tests.

### Changed

- `scripts/verify_vice.py`: the rendering filter is set explicitly to none (`-TEDfilter 0`), which left the title capture byte-identical; breakpoint hits are read from VICE's stop messages, because the `BREAK:` lines that echo a set breakpoint had made the v1.0.0 "reached" checks vacuous; loop counts written as hex, the monitor's default radix (v1.0.0's `ignore 1 24` meant 36 passes); a second gameplay capture after 256 passes.
- `docs/images/restored-gameplay.png` is now taken at the first main-loop pass (v1.0.0's was the second, through the checkpoint error above); added `restored-later.png` and the loading-screen captures.
- `README.md` expanded to link the handbook, analysis, graphics and porting guide.

### Known limits

- Still not tested: keyboard and joystick by hand, sound, a whole wave in play, the completion screen in play, a full play-through and real hardware.
- Alien scoring by wave (50–350) is read from tables, not observed in play.
- The packaging's "3 lives" and "96 levels" disagree with the code (5 lives, 80 waves); the reason is unknown.

---

## [1.0.0] 21-10-2026

Preservation checkpoint (commit `8327b9c`, annotated tag `v1.0.0`): the surviving Xargon's Revenge source reassembled for the Commodore 16 and Plus/4.

### Added

- Preserved inputs, byte for byte: `Original Source Recovered/` (two 2026 disk images and their extractions, the 1992 ZIP and its extracted folder), `Original Artifacts/` (inlay, scans, *C16 Classics II* leaflet, disk photo) and the running `xargons_revenge.prg`.
- `scripts/restore_c16.py`, the single build pipeline. It reads the source disk, checks all 94 live files against the 2026 extraction, checks the loading-screen disk the same way, compares the 1992 ZIP with its folder, takes six missing modules from the 1992 export through `INDEX`, expands the original `.LIB` order of `REVENGE` and assembles with ca65 and ld65.
- `scripts/d64_image.py` (disk reader) and `scripts/source_converter.py` (MOS assembler to ca65 syntax), adapted from the Tycoon Tex restoration, plus `config/c16.cfg` for the memory layout.
- Verified output: all 8,094 bytes of the original `OBJ` listing match with zero differences. The PRG is 15,362 bytes, loads at `$0400`, starts at `$1800` and has SHA-256 `32c13c8867ea97bb4fd60ac9a73e5d7a600c04ece5699ac37680143c12adce33`.
- PlatformIO project with `c16` and `c16_debug` environments (pinned to `platformio/native@1.2.1`) that produce identical game bytes, plus `build.sh`, a `Makefile`, VS Code tasks, settings and recommended extensions.
- `scripts/run_vice.py` launcher with an `--original` option, `scripts/verify_vice.py` (title, gameplay entry and running-version comparison) and `scripts/probe_gameplay_rules.py` (extra lives and alien selection).
- `scripts/tool_check.py`, which records tool versions.
- `test/test_restoration.py` (ten tests) and `test/test_vice.py`, which skips when VICE isn't installed.
- GitHub Actions workflow that runs the tests, builds both PlatformIO environments and checks their bytes against the direct build.
- Verification evidence in `docs/verification/` and VICE screenshots in `docs/images/`.

### Known limits

- The running version's alien graphics differ from the source build in 735 bytes at `$0501–$07FF`. Its tape loader copies alien page *n* from source offset *n* instead of *n* × 256. The build keeps the source layout.
- `$0800–$0FFF` and `$379E–$37FF` hold loader and assembler residue in the running version and zeros in the rebuild.
- Not yet tested: keyboard, joystick, sound, scoring over a full game, level transitions, a full play-through and real C16 hardware.
