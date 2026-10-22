# Quick Start

## Build

Install Python 3.9 or later, cc65 and VICE. From the project folder:

```bash
./build.sh
python3 scripts/run_vice.py --game-version 1
python3 scripts/run_vice.py --game-version 2
```

The outputs are `build/xargons-revenge-v1.prg` (game v1, development) and `build/xargons-revenge-v2.prg` (game v2, cassette release); [Game Versions](docs/GAME_VERSIONS.md) explains the difference. Both load at `$0400` and start at `$1800`. Use the launcher, because the PRGs have no BASIC stub.

---

## PlatformIO and VS Code

Open this folder in VS Code, install the recommended PlatformIO extension and run the default build task. From a PlatformIO terminal:

```bash
pio run -e c16
pio run -e c16 -t upload
pio run -e c16_v2 -t upload
```

The first upload runs game v1 and the second game v2. `pio run -e c16_debug` gives the same game bytes. Outputs go to `build/platformio/<environment>/`.

---

## Controls and Checks

Fire starts the game. Keys are **S** up, **X** down and **Return** fire, or use a joystick; SPACE pauses, G resumes and ESC returns to the title. On the title page J and K choose joystick or keyboard, and S and Q sound on or off.

```bash
make test
make verify
make run-original
```

[Build and Run](docs/BUILD_AND_RUN.md) and [Testing](TESTING.md) have the details.
