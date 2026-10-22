# CLAUDE.md – Xargon's Revenge C16

## Target

PAL Commodore 16 (also Plus/4), 16 KB, 6502 + TED. Preservation reassembly of the 1985 Micro Projects / Gremlin Graphics game. Not an ESP32/CYD project: global CYD, TFT_eSPI, `config.h` and `debug.h` rules don't apply here.

- Two game versions, same code: `build/xargons-revenge-v1.prg` (development, `BJH` as stored) and `-v2.prg` (cassette release: page p of `$0400` = `BJH[p:p+256]`, the release tape loader's copy rule). Load `$0400`, entry `$1800`, no BASIC stub. Code `$1800–$379D` (8,094 bytes) must match `OBJ`.
- "Game v1/v2" are game versions, not the repo's release tags (`v1.x.y`). Never move a published tag.
- Layout: `BJH` aliens `$0400`, zero padding `$0800–$0FFF`, `LANDSCAPE-2` `$1000`, code `$1800`, `FRAK!` `$3800`.
- `xargons_revenge.prg` (project root) is the packed running version: BASIC `SYS 4109`, decruncher at `$100D`.

## Build Pipeline

Single entry point: `scripts/restore_c16.py`, which always builds both versions (alien data via generated `aliens-v1.s`/`aliens-v2.s`). `build.sh`, `make`, `pio run -e c16|c16_debug|c16_v2` all call it and must produce identical bytes; `custom_game_version` only picks what `upload` runs. `config/c16.cfg` is the ld65 layout and is also parsed by `restore_c16.py`. PlatformIO is pinned to `platformio/native@1.2.1` with `scripts/build_6502.py` replacing the builder.

## Source Priority

1. `Original Source Recovered/2026 - 1st Copy/Xargon's Revenge/Xargon's Revenge.d64`, read directly and checked against `Xargon's Revenge - Extracted/` and its `manifest.json`.
2. Only modules absent from that disk come from `Original Source Recovered/1992/DISK9/` via `INDEX` – exactly six: `ALI-PRINT&CLEAR`, `COMPLETED-SHEET`, `DATA-LAND/CHARS`, `FIRING-MEGA/CODE`, `RASTER-ROUTINES`, `WHOOPPEE-MESSAGE`.
3. Graphics: `BJH`, `LANDSCAPE-2`, `FRAK!` as chosen by the original `C16` boot program and `LOADER`. `CHAR#1-*` source is an older landscape (comparison only).
- `2026 - 1st Copy/Xargons Revenge - 5 Lives/…(partial).d64` is the first three files of the 5 Lives disk (a loading screen); verified, never a build input.
- Renamed 22-10-2026 (contents unchanged): `2026/Xargon'sRevenge-C16.d64` + `Xargons-Revenge-C16-Side2/` and `2026/XargonsRevenge-C16.d64` + `-Side1/`. All disks are single-sided; "Side 1/2" meant the two disks. Recorded in `docs/SOURCE_INVENTORY.md`.
- `2026 - 2nd Copy/` holds d64copy sector copies of DISK8, DISK9, DISK10 with photos and 1992 exports; verified by `scripts/verify_second_copy.py`, never a build input. Its DISK9 copy holds the six fallback modules, identical to the 1992 text, so the build is unaffected.

## Preservation Rules

- Never modify, rename, re-encode or tidy anything in `Original Source Recovered/`, `Original Artifacts/` or `xargons_revenge.prg`. `.gitattributes` disables text conversion there; tests hash every input.
- `Other Versions/` (Plus/4 World downloads plus a VICE snapshot) is read-only and compared only, never a build input. Its sources and hashes are recorded in `docs/OTHER_VERSIONS.md` Appendix A. `docs/GREMLIN_ARCHIVE.md` is shared with the other Micro Projects reconstructions; keep its first five sections project-neutral.
- Never copy bytes from the running version into the build. Game v2 is derived from `BJH` by rule and only compared with the running version.
- Gameplay changes go in a separate variant (not yet implemented), never into the preservation build. Tests fail on any output change by design.
- `Xargons Revenge Prompt(Claude).md` is a local brief, git-ignored.

## Gotchas

- 1992 `.TXT` exports are lower-case CRLF; 2026 SEQ files are CR-only. Split on `\r` only – `str.splitlines()` breaks on `$85`/`$1C`. Decode Latin-1 (one PETSCII `$AF` in a `CHAR#1-BOT` comment).
- The 1992 ZIP uses PKZIP Implode/Shrink; Python `zipfile` can't expand it, so the byte check uses `unzip -p`.
- `.LIB` names are prefix matches; the build must fail on missing, ambiguous or recursive includes. `LDA` can't be a label, hence `LZA` in `SHEETD`.
- VICE monitor numbers are hex (`ignore 1 24` = 36). After `delete`, the next breakpoint reuses #1. `BREAK:` lines only echo a set breakpoint; real stops are `#n (Stop on exec xxxx)`.
- `scripts/capture_versions.py` forces `SHEET` at `STLOOP` and needs ≤48 loop passes so no capture catches a death.
- VICE screenshots use `-TEDfilter 0`; colours match `docs/verification/ted-palette.json`, not any `.vpl` file.
- The `2026 - 1st Copy` images are CBMXfer rebuilds (header `TITLE`/`ID`): CBMXfer drops 15–16-character names and its folder export also drops names with `/`. The 2nd-copy CBMXfer `.d64` files are blank. Trust the d64copy images.
- 1992 exports: BASIC listings drop PETSCII control codes in strings; DISK8 `LANDSCA2.BIN` wrongly duplicates `LANDSCA1.BIN`.
- d64copy error maps: 1 = good, 0 = free sector not read, other = read error. Some sectors reported good on the 5 Lives disk are still decayed.
- VICE `-autostart` doesn't press Play for C16 tapes: attach with `-1`, type `LOAD` via `-keybuf`, then `tapectrl 1` in the monitor (`compare_other_versions.py`).
- A machine reset ends VICE command playback, so the reset probe exits on its cycle limit (`check=False`).
- Comments lie: `KEY-SCAN` says A/Z (code uses S/X), pause says HELP (code uses SPACE).
- Packaging says 3 lives / 96 levels; code gives 5 lives and ends after 80 waves (probed). The earlier DISK8 build has 3 lives.

## Docs

Markdown is the source of truth; `docs/XARGONS_REVENGE.html` is generated by `scripts/build_docs.mjs` from `docs/handbook.json`. Run `make docs-check` before committing. Graphics need Pillow in `.venv` (`.venv/bin/python scripts/render_game_graphics.py`).
