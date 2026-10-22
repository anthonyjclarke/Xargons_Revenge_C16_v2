# Source Inventory

## Preserved Collections

| Path                                         | Contents                          |
| :------------------------------------------- | :-------------------------------- |
| `Original Source Recovered/2026 - 1st Copy/` | Two disk images and extractions   |
| `…/2026 - 2nd Copy/`                         | Three disks: copies, photos, 1992 |
| `Original Source Recovered/1992/DISK9/`      | My 1992 PC export, extracted      |
| `Original Source Recovered/1992/*.ZIP`       | The same export as a 1992 ZIP     |
| `Original Artifacts/`                        | Packaging, scans, leaflet, photo  |
| `xargons_revenge.prg`                        | Compressed running version        |
| `Other Versions/`                            | Plus/4 World downloads, compared  |

`Xargon's Revenge/Xargon's Revenge.d64` is the source disk: 94 files in its live directory, 69 sequential and 25 program files. `Xargon's Revenge - Extracted/` is its 2026 extraction, with one file per directory entry and a `manifest.json` of hashes. Both 2026 images have the disk name `TITLE`, ID `ID`. The 1992 `INDEX` lists the same disk as `XARGON'S REVENGE`, ID `MP`, with 100 files. The blank header shows these images are CBMXfer rebuilds, file by file, not sector copies; CBMXfer drops files whose names are 15 or 16 characters long, which is why six modules are missing ([Development Disks](DEVELOPMENT_DISKS.md#what-the-copying-tools-did)).

`Xargons Revenge - 5 Lives/Xargons Revenge - 5 Lives (partial).d64` and its `- Extracted/` folder hold three files: `LOADER` at `$0300`, `P1/$0C00-$1000` and `P2/$0800-$0C00`. They make a loading screen that says "written by micro projects limited", and the loader expects `P3` and `P4`, which aren't there. They are byte-identical to the first three files of my 5 Lives disk (1992 `DISK10`), which has read errors from `P3` on. The build checks this disk against its extraction but doesn't use it.

`DISK9 - Xargon's Revenge.ZIP` is a PKZIP 1.x archive (Implode and Shrink) dated 7 October 1992. It is also published as `DISK9.ZIP` in Mark Hardisty's Gremlin Graphics Archive, with the same CRC-32 and size ([Gremlin Archive and the Book](GREMLIN_ARCHIVE.md#in-this-project)). Its 101 members are byte-identical to the 101 files in `DISK9/`, ignoring `.DS_Store`. The build checks this with `unzip -p`, or by CRC-32 and length when `unzip` isn't installed, and says which method it used. Text exports in `DISK9/` are lower case with CRLF line endings; the build normalises them in memory only.

`Other Versions/` holds six copies downloaded from Plus/4 World, including a tape of the original release, and a VICE snapshot of one of them. They are compared only, never used to build. [Other Versions](OTHER_VERSIONS.md) gives the source link and hash of each file.

`2026 - 2nd Copy/` holds the second copy of all three development disks, made on 22 October 2026: for each, a photo, the 1992 export, a `d64copy` sector image and a CBMXfer export. The CBMXfer `.d64` files are blank. `scripts/verify_second_copy.py` checks them; [Development Disks](DEVELOPMENT_DISKS.md) reports what they show. They are verified, never build inputs.

On 22 October 2026 the first-copy files were renamed, contents unchanged, so their names match the disks and the second copy. All three disks are single-sided; "Side 1" and "Side 2" only told the two working disks apart. Each `manifest.json` still records the original capture path.

| Old name (`2026/`)           | New name (`2026 - 1st Copy/`)                        |
| :--------------------------- | :--------------------------------------------------- |
| `Xargon'sRevenge-C16.d64`    | `Xargon's Revenge/Xargon's Revenge.d64`              |
| `Xargons-Revenge-C16-Side2/` | `Xargon's Revenge/Xargon's Revenge - Extracted/`     |
| `XargonsRevenge-C16.d64`     | `Xargons Revenge - 5 Lives/… (partial).d64`          |
| `Xargons-Revenge-C16-Side1/` | `Xargons Revenge - 5 Lives/… (partial) - Extracted/` |

Host metadata (`.DS_Store`) is left out of every manifest and comparison.

---

## Active Assembly Sets

| Assembly root  | Modules | From 2026 | From 1992 | Output          |
| :------------- | :------ | :-------- | :-------- | :-------------- |
| `REVENGE`      | 68      | 62        | 6         | `$1800–$379D`   |
| `ASSEM-GRAPHS` | 3       | 3         | 0         | Comparison only |

`REVENGE` counts itself and the 67 modules it includes. `ASSEM-GRAPHS` assembles `CHAR#1-BOT` and `CHAR#1-TOP` into a landscape bank that is compared with `LANDSCAPE-2` and not put in the PRG.

---

## Fallback Modules

These six modules aren't in the first 2026 image. Each is chosen explicitly through the 1992 `INDEX`, which maps the original name to the shortened PC filename. The second 2026 copy, a `d64copy` sector copy of the same disk, does hold all six, and each matches its 1992 export line for line, so the fallback changes no byte of the build ([`second-copy.json`](verification/second-copy.json)).

| Commodore module   | 1992 file      | Bytes |
| :----------------- | :------------- | :---- |
| `ALI-PRINT&CLEAR`  | `ALIPRINT.TXT` | 478   |
| `COMPLETED-SHEET`  | `COMPLETE.TXT` | 3,746 |
| `DATA-LAND/CHARS`  | `DATALAND.TXT` | 398   |
| `FIRING-MEGA/CODE` | `FIRINGME.TXT` | 1,466 |
| `RASTER-ROUTINES`  | `RASTERRO.TXT` | 2,592 |
| `WHOOPPEE-MESSAGE` | `WHOOPPEE.TXT` | 528   |

Their combined 36 blocks are exactly the extra free space on the 2026 disk.

---

## Filename Encoding

The 2026 extraction escapes characters that aren't safe in host filenames as `~` plus two hex digits: `~2F` is `/`, `~23` is `#`, `~2E` is `.` and `~21` is `!`. So `027_PAUSE~2FESCAPE.seq` is `PAUSE/ESCAPE` and `081_FRAK~21.prg` is `FRAK!`. The build doesn't rely on that encoding: it reads names from the disk directory, and the extraction manifest records each name's PETSCII bytes.

---

## Graphics and Data Binaries

| File          | Load    | Role                                    |
| :------------ | :------ | :-------------------------------------- |
| `BJH`         | `$2000` | Aliens; copied to `$0400` (in the PRG)  |
| `LANDSCAPE-2` | `$1000` | Landscape bank (in the PRG)             |
| `FRAK!`       | `$3800` | Font and actor bank (in the PRG)        |
| `LANDSCAPE-1` | `$1000` | Earlier landscape, 22 bytes differ      |
| `ALIBUM5`–`8` | `$2000` | Alien sets; `ALIBUM8` begins with `BJH` |
| `HILLS`       | `$3800` | Hill glyphs used by `COLOUR-SETTER`     |
| `XARG-SCREEN` | `$4000` | 1-bit title lettering design            |
| `TITLE-DATA`  | `$8000` | Banner nibbles before `COMPACTOR`       |
| `MEGA-SUPER`  | `$3C00` | C16 hex loader for `OBJ`                |
| `SUPER-LOAD`  | `$1800` | Earlier hex loader                      |
| `LOADER`      | `$033C` | Loads `BJH`, starts the game            |

`OBJ` is the MOS hex object listing of the main program, 338 data records covering `$1800–$379D`. `O.ALI` is a hex listing of an alien set at offset 0; it equals the first 1 KB of `ALIBUM5`.

---

## Unused Sources and Development Utilities

| Item                    | Status                                    |
| :---------------------- | :---------------------------------------- |
| `PLANETS`               | Source on disk, not included              |
| `BLOB-MOVE`             | Source on disk, not included              |
| `CHAR#1-BOT/TOP`        | Earlier landscape source, comparison only |
| `C16`, `BOOT ALL`       | BASIC boot programs                       |
| `BIG-PRINT`, `DESIGNER` | Title design helpers (C64 BASIC)          |
| `COMPACTOR`             | Packs `TITLE-DATA` into banner bytes      |
| `DOUBLE-WIDTH`          | Double-width letter generator             |
| `DOUBLE-GENERATOR`      | Double-width letters and digits           |
| `COLOUR-SETTER`         | TED colour tester                         |
| `EDITOR64`              | Commodore 64 editor, CBM 1982             |
| `DOS5.2`                | DOS wedge, "Bugga-Soft 1984"              |
| `ASM.C64`               | C64 assembler                             |

The tools are described in [Codebase Analysis](../CODEBASE_ANALYSIS.md#original-and-modern-development-tools). `EDITOR64` and `DOS5.2` are third-party programs kept because they were on the disk.

---

## Generated Audit Trail

Each build writes `build/recovery-manifest.json`. It records the hash of both disk images and the `INDEX`, the ZIP comparison, the comparison of every module present in both collections, and for every source file its origin, bytes, hash and whether it is a fallback. `used_modules` lists the active modules and `assets` the binaries placed in the PRG. The [committed manifest](verification/source-manifest.json) is the one for this release.

[Source and Validation](SOURCE_AND_VALIDATION.md) explains the comparisons.
