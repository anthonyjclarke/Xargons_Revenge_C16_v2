# Source Navigation

## Build Inputs

The game's source is kept under `Original Source Recovered/`, exactly as recovered. The build reads the 2026 source disk image first and takes the six modules it lacks from the 1992 export. A later sector copy of the same disk confirms those six are identical to the 1992 text. `REVENGE` is the main assembly file; the 1992 `INDEX` maps its `.LIB` names to the shortened PC filenames.

The ca65 source is generated as `build/revenge.s`, with the landscape comparison in `build/landscape.s`. Both keep `; SOURCE: module:line` markers, so any converted line can be traced back. Listings, labels, maps and debug files are written next to them.

---

## Why This Folder Is Empty

I haven't kept a hand-edited copy of the game here. The direct build, Makefile, PlatformIO, tests and VS Code tasks all use the same source selection and conversion, and editing generated assembly changes nothing on the next build.

[Source Inventory](../docs/SOURCE_INVENTORY.md) lists the active inputs, [Build and Run](../docs/BUILD_AND_RUN.md) covers the tools and [Source and Validation](../docs/SOURCE_AND_VALIDATION.md) the checks. To change the game, start with the [Porting Guide](../docs/PORTING_GUIDE.md#protect-the-preservation-build), because the preservation tests fail on purpose when the output changes.
