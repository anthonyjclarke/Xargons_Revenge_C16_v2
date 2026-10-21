# Xargon's Revenge C16

This project reassembles the surviving **Xargon's Revenge** source for the Commodore 16 and Plus/4 using PlatformIO, VS Code and the cc65 toolchain. I wrote the game at Micro Projects as the sequel to my Xargon Wars, and Gremlin Graphics published it in 1985.

![Xargon's Revenge cassette artwork](Original%20Artifacts/Xargons%20Revenge%20Image.jpg)

## Verified Build

The assembled code matches all **8,094 bytes in the original `OBJ` object listing**, with zero differences. The PRG is 15,362 bytes. It loads at `$0400`, where the alien graphics live, and the game starts at `$1800`. The landscape characters at `$1000` and the font at `$3800` are the surviving binaries that my own development boot program loads.

In VICE, on a PAL C16 with 16 KB RAM, the rebuild draws its title and gets into gameplay. The running version I have is compressed. After decompression its code, landscape and font are byte-identical to the rebuild. Its alien graphics are not: a cassette loader in that copy shifts three of the four alien pages by one, two and three bytes, so the aliens on sheets 4–15 differ. The rebuild keeps the source layout. The evidence is in [`docs/verification/`](docs/verification/).

![Restored title in VICE](docs/images/restored-title.png) ![Restored gameplay in VICE](docs/images/restored-gameplay.png)

---

## Build and Run

You need Python 3.9 or later and the cc65 tools (`ca65` and `ld65`), plus VICE (`xplus4`) to run the game. On macOS with Homebrew:

```sh
brew install cc65 vice
./build.sh
python3 scripts/run_vice.py
```

The output is `build/xargons-revenge.prg`. After the C16 finishes resetting, the launcher loads it at its saved address and jumps to `$1800`. The PRG has no BASIC `RUN` stub. `python3 scripts/run_vice.py --original` runs the compressed running version through its own `SYS 4109`.

With PlatformIO Core installed:

```sh
pio run -e c16
pio run -e c16 -t upload
```

PlatformIO writes `build/platformio/c16/xargons-revenge.prg`, and the upload target launches VICE. The `c16_debug` environment produces identical game bytes. Every entry point runs the same `scripts/restore_c16.py` pipeline.

The source reads **S** for up, **X** for down and **Return** for fire. On the title page **J** and **K** choose joystick or keyboard, and **S** and **Q** turn sound on and off. That matches the cassette inlay. I still need to test the keyboard and a joystick by hand.

---

## Preserved Inputs

`Original Source Recovered/2026/` holds two 2026 disk images and their extractions. `Xargon'sRevenge-C16.d64` is the source disk and the primary build input. `XargonsRevenge-C16.d64` holds a loading screen and a loader and isn't used in the build. `Original Source Recovered/1992/` holds my 1992 PC export of the source disk, both as the original ZIP and extracted. The six modules missing from the 2026 disk come from there, through its original `INDEX`.

`Original Artifacts/` holds the cassette inlay, my scans, the *C16 Classics II* leaflet and a photo of the two development disks. The running PRG, `xargons_revenge.prg`, sits in the project root. Generated files go into `build/`, and the original inputs stay byte for byte as they were.

---

## Recovery Background

The recovery story, my original development setup and the recovery-tool acknowledgements are in my companion [Dorks Dilemma C16 repository](https://github.com/anthonyjclarke/Dorks_Dilemma_C16), especially its [Development History](https://github.com/anthonyjclarke/Dorks_Dilemma_C16/blob/main/docs/DEVELOPMENT_HISTORY.md). This project reuses that restoration's build approach.

---

## Tests

```sh
python3 -m unittest discover -s test -p 'test_*.py' -v
python3 scripts/verify_vice.py
python3 scripts/probe_gameplay_rules.py
```

The tests cover the PRG hash and header, every `OBJ` byte, source selection and fallbacks, graphics provenance, unchanged input hashes, syntax conversion and malformed inputs. The VICE test skips, and says so, when `xplus4` isn't installed. I haven't yet tested sound, the keyboard, a joystick, a full play-through or real hardware. [`CHANGELOG.md`](CHANGELOG.md) records each release.
