# History and Credits

## Xargon's Revenge

Xargon's Revenge is a 1985 game for the Commodore 16 and Plus/4, written at Micro Projects and published by Gremlin Graphics Software Ltd. of Sheffield. It's the sequel to my earlier game Xargon Wars.

The main source file opens with:

```text
; XARGON II WRITTEN BY THE MEGA
; BEING HIMSELF !!!
;
; (C) MICRO PROJECTS 1985
;
; STARTED ON A DRIZZLY SATURDAY
; AFTERNOON 30/MARCH AT 5.00 PM
```

The year isn't written next to the start date, but 30 March 1985 was a Saturday, which fits the 1985 notice. The cassette inlay carries "© 1985 Gremlin Graphics Software Limited".

---

## My Recollections

These are what I remember, as I recorded them on 21 October 2026:

- I wrote Xargon Wars, and this game is its sequel.
- I was always a fan of Scramble, so I wanted to write a scrolling game.
- "The Mega" in the source header is, I think, a pseudonym for me (see the open questions below).
- I'm not sure who else helped on this game. When I had help, it would normally be credited in the source, and this source names nobody else.
- I don't remember when it was finished or released. Games typically took 60 to 90 days.
- I don't recall the loading screen on the second disk being used.

Later the same day, after seeing the two game versions, I added:

- I have no recollection of why there might be two versions. Maybe Gremlin Graphics, who published the game, gave us some feedback and wanted a different version. This is speculation; [Game Versions](GAME_VERSIONS.md) sets out what the evidence shows.
- I'm no longer sure that "The Mega" was me.

Beyond that I don't remember much about making it. Anything else in this repository comes from the source, the disks or the packaging, not from memory.

---

## The Gremlin Archive and the Book

Mark Hardisty's book *A Gremlin in the Works* (Bitmap Books), the officially endorsed history of Gremlin Graphics, tells the Micro Projects story, and I contributed to it. His [Gremlin Graphics Archive](https://www.gremlinarchive.com/) publishes my 1992 export of the development disks, including this game's `DISK9`, and introduces my part in [A Gremlin in the Works – Anthony Clarke](https://www.gremlinarchive.com/index.php/2017/07/31/a-gremlin-in-the-works-anthony-clarke/). [Gremlin Archive and the Book](GREMLIN_ARCHIVE.md) has the references and the archive's disk list.

---

## What the Evidence Shows

The two development disks are labelled "Revenge of Xargon (Xargon Wars II) (c) Micro Projects 1985" and "Xargon's Revenge (c) Micro Projects '85". The first suggests the working title. I don't know which label belongs to which 2026 disk image.

The scrolling message in the game credits "Xargon's Revenge © Micro Projects 1985", advertises other Gremlin C16/Plus 4 games (Xargon Wars, Petals of Doom, Tycoon Tex, Dork's Dilemma and Sword of Destiny) and thanks "all those who helped in the production and design of this game" without naming anyone. The sound module's header says it is "an attempt to write a nice routine like our mate Robbie does"; the source doesn't say who Robbie is.

The game was sold on cassette for £6.95 and later appeared on the *C16/Plus 4 Classics II* compilation from Gremlin Graphics, with Blagger, Monkey Magic and Timeslip. The packaging says "96 levels – 16 waves – 3 lives". The surviving source ends the game after 80 waves and starts with 5 lives, as [Codebase Analysis](../CODEBASE_ANALYSIS.md#waves-levels-and-completion) explains; I can't say whether the packaging describes an earlier plan or another release.

---

## Open Questions

**Who was "The Mega"?** The `REVENGE` header says "XARGON II WRITTEN BY THE MEGA BEING HIMSELF !!!". The word recurs as a nickname-style label throughout this source: the `FIRING-MEGA/CODE` module, "MEGA TABLES", "DO MEGA CODE", "TIME FOR A MEGA PLANET" and the completion message "CONGRATULATIONS MEGA PERSON!". The `MEGA-SUPER` hex loader on this disk is also on the Tycoon Tex disk. In my Tycoon Tex source, which credits the programming to Micro Projects, the title-page module says "(C) MEGA-CODER OF M.P.L" (presumably Micro Projects Ltd), and there are modules called `FIRING/MEGACODE` and `DEMO-MEGA/CODE`. No other name appears in this source. That points to the programmer who wrote both games, but it doesn't prove who used the name.

**Which disk is which?** I need to plug in the hardware to check which labelled disk in the photo was captured as which 2026 disk image.

**Why two versions, and why does the packaging say 3 lives and 96 levels?** Neither game version matches the packaging, and nothing on the disks explains it.

---

## Dates

| Date            | Event                                      |
| :-------------- | :----------------------------------------- |
| 30 March (1985) | Development started, per the source header |
| 1985            | Copyright on the source, disks and inlay   |
| 7 October 1992  | Source disk exported to PC and zipped      |
| October 2026    | Disks captured and extracted again         |
| 21 October 2026 | This reassembly and documentation          |

The 1992 and 2026 dates belong to copies of the disks, not to the game's development.

---

## Recovery Background and Build Template

My original C64/1541 development set-up and the later recovery of these disks are written up in the companion [Dorks Dilemma C16 repository](https://github.com/anthonyjclarke/Dorks_Dilemma_C16), especially its [Development History](https://github.com/anthonyjclarke/Dorks_Dilemma_C16/blob/main/docs/DEVELOPMENT_HISTORY.md), which also has the recovery-tool acknowledgements. I haven't repeated that story here.

This project adapts the disk reader, source converter, ca65/ld65 build, PlatformIO integration, VICE-monitor checks and handbook generator from the Dorks Dilemma and Tycoon Tex restorations. Xargon's Revenge's own inputs, memory layout, graphics choices, object listing and comparison with the running version are worked out and checked separately here.

---

## Tool Acknowledgements

The modern build uses the [cc65 toolchain](https://cc65.github.io/), the [VICE emulator](https://vice-emu.sourceforge.io/), [PlatformIO](https://platformio.org/), [Visual Studio Code](https://code.visualstudio.com/), Python, Pillow and Node.js, with [Marked](https://marked.js.org/) and [Mermaid](https://mermaid.js.org/) for the handbook.

The original disk also holds the Commodore 64 editor (© 1982 Commodore Business Machines) and "DOS V5.2 (C) Bugga-Soft 1984", which were part of the 1985 tool set. All historical notices are kept. See [Rights and Preservation](../RIGHTS.md).
