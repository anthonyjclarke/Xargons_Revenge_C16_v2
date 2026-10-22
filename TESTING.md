# Testing

## Regression Tests

```bash
make test
```

This runs `python3 -m unittest discover -s test -p 'test_*.py' -v`. `test/test_restoration.py` builds into a temporary folder and checks:

| Test                        | What it protects                         |
| :-------------------------- | :--------------------------------------- |
| PRG baseline                | Size, `$0400` header, SHA-256            |
| Game v2                     | Hash, loader rule, only 735 bytes differ |
| Object records              | All 8,094 `OBJ` bytes, padding           |
| Fresh modules and fallbacks | 94 disk files, exactly six fallbacks     |
| Older export agreement      | One comment byte, ZIP equals folder      |
| Graphics provenance         | `BJH`, `LANDSCAPE-2`, `FRAK!` placement  |
| Second disk copy            | 100 files, early build, 5 Lives sectors  |
| Inputs unchanged            | Hashes of every preserved file           |
| Includes                    | Missing, ambiguous, recursive fail       |
| Historical syntax           | Labels, equates, strings, reservations   |
| Conversion hazards          | CR-only splitting, case folding          |
| Malformed inputs            | Bad hex records, cyclic or short disks   |

The second-copy test runs `scripts/verify_second_copy.py` checks against `Original Source Recovered/2026 - 2nd Copy/` and is skipped when that folder or `Other Versions/` is absent.

`test/test_vice.py` builds into a temporary folder and runs the whole VICE verification. When `xplus4` isn't installed it is reported as **skipped**, never as passed, and the skip message says the title, gameplay and reference checks weren't run.

---

## PlatformIO Agreement

```bash
./build.sh
pio run -e c16 -e c16_debug
cmp build/xargons-revenge-v1.prg build/platformio/c16/xargons-revenge-v1.prg
cmp build/xargons-revenge-v2.prg build/platformio/c16_v2/xargons-revenge-v2.prg
```

All entry points produce identical bytes for both game versions: `build.sh`, `make`, `pio run -e c16`, `pio run -e c16_debug` and `pio run -e c16_v2`. The GitHub workflow compares both versions in every environment.

---

## VICE Verification

```bash
make verify
```

`scripts/verify_vice.py` runs `xplus4` headless as a PAL C16 with 16 KB, with sound off, warp, no rendering filter and a fixed cycle limit, and drives it from monitor command files.

1. It loads the rebuild, waits for 36 passes of the title's fire test, screenshots and saves memory, and sets `JFIRE` to `$80`.
2. At the first main-loop pass it clears `JFIRE`, screenshots and saves memory, and checks `TITLE=0`, `LIVES=5` and `DEAD=0`.
3. It runs 256 more main-loop passes with no input, screenshots again and checks the game is still playing.
4. It lets the running version decompress, stops at `$1800`, saves `$0400–$3FFF` and classifies every difference.
5. It plays the decompressed running version through the same steps.
6. It shows the loading-screen disk's files and measures the TED palette.

The commands, monitor logs, memory dumps, screenshots and `vice-verification.json` are left in `build/`. The screenshots need no window on macOS; on a Linux machine without a display VICE may need a virtual X server. This was only run on macOS.

---

## Rule Probes

```bash
make probes
```

`scripts/probe_gameplay_rules.py` calls single original routines with controlled memory: four score and extra-life cases, `ALIDEF` for every sheet in both versions, `COMPLE` at four points in the game, and resets during play. The results are in [`rule-probes.json`](docs/verification/rule-probes.json) and summarised in [Source and Validation](docs/SOURCE_AND_VALIDATION.md#rule-probes).

---

## Game Version Captures

```bash
make versions
```

`scripts/capture_versions.py` plays game v1 and game v2 on each of the 16 sheets: one scripted fire press, `SHEET` set at `STLOOP`, then 48 main-loop passes without input. It fails unless the alien characters in memory are the expected ones for that version and sheet, the ship is still alive, sheets 1–4 are pixel-identical and sheets 5–16 differ. The results are in [`game-versions.json`](docs/verification/game-versions.json) and the screenshots in `docs/images/versions/`.

---

## Documentation Tests

```bash
make test-docs
make docs-check
```

`test/test_docs.mjs` checks the handbook generator: link rewriting, embedded images, failure on broken links and remote images, escaping of raw HTML, deterministic output and watch mode. `make docs-check` fails if `docs/XARGONS_REVENGE.html` is out of date with its Markdown, images or templates.

---

## Verification Limits

What has been verified, and how, is in [Source and Validation](docs/SOURCE_AND_VALIDATION.md). Not yet done:

- Keyboard and joystick tested by hand
- Sound listened to
- A whole wave played, alien scoring confirmed in play
- Level transitions and the completion screen reached in play
- A full play-through
- Real C16 or Plus/4 hardware

Scripted input was limited to one fire press at the title; everything after it ran without input.
