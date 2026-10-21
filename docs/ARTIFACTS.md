# Artifact Catalogue

## Packaging and Artwork

All the images in `Original Artifacts/` show Xargon's Revenge. I checked each one by its content, not its filename, and none is mislabelled or belongs to another game. Apart from the gameplay screenshot and the title picture, they're my own scans and photos.

![Cassette inlay, opened flat](../Original%20Artifacts/Xargon's%20Revenge%20Cassette%20Inlay.jpg)

**`Xargon's Revenge Cassette Inlay.jpg`** (2,444 × 1,204) is the whole inlay opened flat. It has the cover painting with the £6.95 price flash, the back-cover text, two gameplay screenshots, the barcode 5 013658 036029 and the instructions: "C16/Plus 4, 96 levels – 16 waves – 3 lives", the J, K, S and Q title keys, S up, X down, Return fire and Esc abort, the scoring (aliens 50, fuel pods 250, a bonus for fuel left, an extra life every 50,000) and "Type Load Press Return". The publisher is Gremlin Graphics Software Limited, Alpha House, 10 Carver Street, Sheffield S1 4FS, © 1985.

![Cover painting](../Original%20Artifacts/Xargons%20Revenge%20Image.jpg)

**`Xargons Revenge Image.jpg`** (820 × 924) is the front-cover painting on its own, with the price flash.

![Cover and back, second layout](../Original%20Artifacts/xargons_revenge_front.jpg)

**`xargons_revenge_front.jpg`** (740 × 501, file dated 2003) shows the cover and the back in a different layout from the inlay above: the back has the blurb above three gameplay screenshots and the barcode, and the spine reads "Commodore C16/Plus 4". The screenshots differ from those on the inlay. I don't know why there were two layouts.

---

## Screens

![Gameplay screenshot](../Original%20Artifacts/xargons_revenge_main.jpg)

**`xargons_revenge_main.jpg`** (320 × 200) is a gameplay screenshot: score 800, three lives showing, a wave of arrow-shaped aliens, and the message bar ending "VENGE © MICRO PROJECTS 1985". It is a screen capture rather than a scan. It matches the rebuild's [gameplay capture](images/restored-later.png) in layout and graphics.

![Title screen picture](../Original%20Artifacts/Xargons_Revenge.png)

**`Xargons_Revenge.png`** (1,486 × 774) is a soft, enlarged picture of the title screen with joystick and sound on, a brown window, the banner, and the message "C16/PLUS4 GAMES FROM GREMLIN GRAPHICS". The softness suggests it was taken from video.

---

## Disks and Leaflet

![The two development disks](../Original%20Artifacts/Xargon's%20Revenge%20Disks.jpg)

**`Xargon's Revenge Disks.jpg`** (2,016 × 1,512, added 21 October 2026) shows two 5¼-inch disks with handwritten labels. One, in front of a Control Data sleeve, reads "Revenge of Xargon (Xargon Wars II) (c) Micro Projects 1985"; the other, a Memorex disk, reads "Xargon's Revenge (c) Micro Projects '85". Which label belongs to which 2026 disk image isn't recorded.

**[`C16_Classics_II_English.pdf`](../Original%20Artifacts/C16_Classics_II_English.pdf)** is a one-page scan of the folded instruction leaflet for Gremlin's *C16/Plus 4 Classics II*, which collected Xargon's Revenge with Blagger, Monkey Magic and Timeslip. Its Xargon's Revenge panel repeats the inlay text with © 1985 Gremlin Graphics Software Limited. The other three panels belong to the other games and their publishers. The PDF wrapper was generated on 21 October 2026; the scan inside is the historical item.

---

## Running Version and Loading Screen

`xargons_revenge.prg`, in the project root, is the compressed running version. I downloaded it and don't know who prepared it; its file is dated 10 August 2014. It is byte-identical to the main download on the [Plus/4 World entry](https://plus4world.powweb.com/software/Xargons_Revenge) for the game, checked by SHA-256 on 22 October 2026 ([Other Versions, A1](OTHER_VERSIONS.md#a1-download)). Decompressed, it matches the original release tape at the game's entry apart from 19 bytes of screen RAM, so it is a packed copy of the released game. It runs in VICE, and [Source and Validation](SOURCE_AND_VALIDATION.md#comparison-with-the-running-version) compares it with the rebuild.

The [loading screen](images/loading-screen.png) is rendered from the second 2026 disk image in VICE; it isn't a separate artifact file. See [Illustrated Graphics](GRAPHICS.md#loading-screen).

---

## Preservation and Attribution

These files are kept byte for byte: `.gitattributes` turns off line-ending and whitespace changes for everything in `Original Artifacts/` and `Original Source Recovered/`, and the tests check their hashes. The packaging, artwork and leaflet remain the property of their rights holders; see [Rights and Preservation](../RIGHTS.md).
