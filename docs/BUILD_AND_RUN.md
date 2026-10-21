# Build and Run

## Requirements

| Tool       | Minimum | Tested           | Needed for                   |
| :--------- | :------ | :--------------- | :--------------------------- |
| Python     | 3.9     | 3.11.7           | Everything                   |
| cc65       | 2.18    | 2.18             | `ca65` and `ld65`            |
| VICE       | 3.10    | 3.10             | Running and verification     |
| unzip      | any     | Info-ZIP (macOS) | Byte check of the 1992 ZIP   |
| PlatformIO | 6.1     | 6.1.19           | PlatformIO environments      |
| Pillow     | 10.1    | 11.3.0           | Palette and graphics figures |
| Node.js    | 20      | 26.12.0          | HTML handbook                |

The VICE minimum is the only version I've tested; older 3.x releases may work but their monitor commands and screenshot output haven't been checked. `scripts/tool_check.py` records the versions it finds, and [`tool-checks.json`](verification/tool-checks.json) is the record for this release.

On macOS with Homebrew:

```bash
brew install cc65 vice
```

Pillow is only needed for the graphics and the palette measurement. I keep it in an ignored virtual environment:

```bash
python3 -m venv .venv && .venv/bin/pip install pillow
```

---

## Direct Build

```bash
./build.sh
```

`build.sh`, `make` and both PlatformIO environments all run `scripts/restore_c16.py`, so they produce the same bytes. The script reads the disk image, checks it against the 2026 extraction, picks the fallback modules, converts the source and assembles it, places the graphics binaries and compares the result with the `OBJ` listing. It stops with an error if anything differs.

### Output Files

| File                           | Contents                            |
| :----------------------------- | :---------------------------------- |
| `build/xargons-revenge.prg`    | The game, load `$0400`, run `$1800` |
| `build/revenge.s`              | Generated ca65 source with markers  |
| `build/revenge.lst`            | Assembler listing                   |
| `build/revenge.labels`         | VICE monitor labels                 |
| `build/revenge.map`, `.dbg`    | Linker map and debug information    |
| `build/landscape.*`            | `ASSEM-GRAPHS` comparison build     |
| `build/comparison.json`        | Sizes, hashes, `OBJ` comparison     |
| `build/recovery-manifest.json` | Source selection and provenance     |

Every module in `build/revenge.s` starts with a `; SOURCE: name:line` marker, so any generated line can be traced back to its original file.

---

## PlatformIO

```bash
pio run -e c16
pio run -e c16_debug
pio run -e c16 -t upload
```

The project pins `platformio/native@1.2.1` and replaces the native builder with `scripts/platformio_build.py`. `c16` writes `build/platformio/c16/xargons-revenge.prg`. `c16_debug` produces identical game bytes in its own folder, and the debug information is the same set of listing, labels, map and `.dbg` files. The `upload` target launches VICE with the built program.

### VS Code

Open the folder in VS Code and install the recommended extensions: PlatformIO, ca65 syntax, the hex editor and EditorConfig. The tasks cover the PlatformIO builds, the direct build, running the rebuild or the original, the tests, the VICE verification and the rule probes. The settings associate `.s`, `.seq` and `.asm` files with ca65 and switch off whitespace trimming, so the historical files stay as they are.

---

## Running the Game

```bash
python3 scripts/run_vice.py
python3 scripts/run_vice.py --original
```

The launcher starts `xplus4` as a PAL C16 with 16 KB, waits for the BASIC ready prompt, loads the PRG at its saved address from the monitor and jumps to `$1800`. The rebuild has no BASIC `RUN` stub; on real hardware it would need a loader, because it loads over `$0400–$0FFF`.

`--original` runs the compressed `xargons_revenge.prg` through its own `SYS 4109`. `scripts/run_vice.sh` is a shell wrapper for the same launcher, and `make run` builds first.

### Controls

| Action         | Keyboard  | Joystick |
| :------------- | :-------- | :------- |
| Up             | S         | Up       |
| Down           | X         | Down     |
| Fire           | Return    | Fire     |
| Pause / resume | SPACE / G | –        |
| Abort to title | ESC       | –        |

On the title page J selects the joystick and K the keyboard, and S and Q turn sound on and off; the game starts with the joystick selected and sound off. Fire starts a game. VICE maps host keys to C16 keys through its keymap, so check its keyboard settings if a key doesn't respond. I haven't tested the controls by hand yet.

---

## Cleaning and Development

```bash
make clean
```

`make clean` removes `build/` and `.pio/`. The original inputs are never written. If you want to change the game, read [Protect the Preservation Build](PORTING_GUIDE.md#protect-the-preservation-build) first: the tests deliberately fail when the output changes.
