# Changelog

All notable changes to the Xargon's Revenge C16 preservation project. Dates are DD-MM-YYYY.

---

## [1.0.0] 21-10-2026

Preservation checkpoint: the surviving Xargon's Revenge source reassembled for the Commodore 16 and Plus/4.

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
