# Gremlin Archive and the Book

## About This Chapter

The first five sections are written to be reused unchanged in each of my Micro Projects C16 reconstructions (Xargon Wars, Xargon's Revenge, Dork's Dilemma, Tycoon Tex). Only [In This Project](#in-this-project) is specific to Xargon's Revenge. I checked the links and the archive contents on 22 October 2026.

---

## A Gremlin in the Works

*A Gremlin in the Works* by Mark Hardisty, published by [Bitmap Books](http://www.bitmapbooks.co.uk/products/a-gremlin-in-the-works), is the officially endorsed history of Gremlin Graphics, endorsed by founder Ian Stewart. The 572-page book follows the company from Monty Mole and Thing on a Spring to its purchase by Infogrames in 1999, with interviews, letters, photographs and design documents. Mark announced it on the archive in the post [A Gremlin in the Works – The Book](https://www.gremlinarchive.com/index.php/2016/05/22/a-gremlin-in-the-works-the-book/) (22 May 2016).

I contributed to the book and to the archive. Mark's post [A Gremlin in the Works – Anthony Clarke](https://www.gremlinarchive.com/index.php/2017/07/31/a-gremlin-in-the-works-anthony-clarke/) (31 July 2017) introduces my part. In 1985 I joined Gremlin with Jason Perkins and Mark Rogers as Micro Projects Limited. Micro Projects wrote many of Gremlin's C16 games, as well as Thing on a Spring on the C64 and its port of Monty on the Run. The book tells the Micro Projects story in full.

---

## The Gremlin Graphics Archive

[The Gremlin Graphics Archive](https://www.gremlinarchive.com/) is Mark Hardisty's companion site to the book. It collects Gremlin's games, box art, adverts, letters, royalty statements, staff photographs and source code. Posts relevant to Micro Projects include:

| Post                                             | Date         |
| :----------------------------------------------- | :----------- |
| [Micro Projects Source Code][ga-src]             | 25 May 2016  |
| [Micro Projects Royalty Statements][ga-roy]      | 24 May 2016  |
| [Compliment Slip / Royalty Notes][ga-slip]       | 24 May 2016  |
| [Early Tradeshow Leaflet][ga-trade]              | 23 May 2016  |
| [Anthony Clarke Photograph][ga-photo]            | 2 June 2016  |
| [A Gremlin in the Works – Anthony Clarke][ga-me] | 31 July 2017 |

Each game also has its own post: for example [Xargon's Revenge (C16/Plus4)][ga-xr] (1 November 2016) and [Xargon Wars – Trade Promotion][ga-xw] (24 May 2016). The compilations have theirs too: [C16 Classics][ga-classics] (13 February 2021) and [C16 Omnibus][ga-omnibus] (20 December 2021).

---

## My Development Disks in the Archive

The [Micro Projects Source Code][ga-src] post holds the Oric and C16 assembler source I donated for many of the company's games, including the unreleased Ultra. Its download, [Old-Development-Disks.zip][ga-zip] (1,894,396 bytes, 846 entries), is my 1992 PC export of the original Commodore disks, re-zipped in 2014. It has two folders, `Disk 1-6/` and `Disk 7-11/`. Each disk is there both as my 1992 PKZIP file (for example `DISK9.ZIP`) and as an extracted folder, with a `READ.ME` from 1992 that names them:

| Disk     | Contents (from `READ.ME`)      |
| :------- | :----------------------------- |
| `DISK1A` | Tycoon Tex C64                 |
| `DISK1B` | Dorks Dilemma C64              |
| `DISK2`  | Utilities                      |
| `DISK3`  | Thingy                         |
| `DISK4A` | Graphics Editor                |
| `DISK4B` | Graphic2                       |
| `DISK5`  | Dorks Dilemma C16              |
| `DISK6`  | Tycoon Tex C16                 |
| `DISK7A` | Xargon Wars C16                |
| `DISK7B` | Xargon Wars C16 (Hack Version) |
| `DISK8`  | Revenge of Xargon (Xargon II)  |
| `DISK9`  | Xargon's Revenge               |
| `DISK10` | Xargon's Revenge – 5 lives     |
| `DISK11` | `LOAD "*",8,1`                 |

Each disk ZIP includes an `INDEX` listing the original Commodore directory next to the PC file names. One thing to watch: in the extracted `Disk 7-11/DISK9/` folder, `LOADER.BIN` is 0 bytes, while `DISK9.ZIP` itself holds the full file. Compare against the disk ZIPs, not the extracted folders.

---

## Plus/4 World and the Archive

[Plus/4 World](https://plus4world.powweb.com/) has entries for these games. Its [Xargon's Revenge entry](https://plus4world.powweb.com/software/Xargons_Revenge) says the early-stages and disk versions were rebuilt from source files on disks I gave to Mark Hardisty, which are the 1992 export above. Check each game's entry for similar notes. Copies labelled "early stages", "disk version" or "with loading screen" are then not independent releases. They come from my own development disks, and only the original cassettes show what was actually sold.

---

## How to Cite

> Mark Hardisty, *A Gremlin in the Works*, Bitmap Books. Officially endorsed history of Gremlin Graphics.

> Mark Hardisty, "Micro Projects Source Code", The Gremlin Graphics Archive, 25 May 2016, <https://www.gremlinarchive.com/index.php/2016/05/25/micro-projects-source-code/>. Download: `Old-Development-Disks.zip`.

> Mark Hardisty, "A Gremlin in the Works – Anthony Clarke", The Gremlin Graphics Archive, 31 July 2017, <https://www.gremlinarchive.com/index.php/2017/07/31/a-gremlin-in-the-works-anthony-clarke/>.

---

## In This Project

The 1992 source in `Original Source Recovered/1992/` is the archive's `DISK9`. `DISK9 - Xargon's Revenge.ZIP` has the same CRC-32 (`c2a053f4`) and size (94,636 bytes) as `Disk 7-11/DISK9.ZIP` in the archive. The 101 extracted files match the archive's `DISK9/` folder, except the empty `LOADER.BIN` noted above.

Two other archive disks are earlier stages of this game. Both are now in `Original Source Recovered/2026 - 2nd Copy/`, with a 2026 sector copy of the physical disk; their 1992 folders match the archive's file for file ([Development Disks](DEVELOPMENT_DISKS.md)):

- **`DISK8`**, "Revenge of Xargon (Xargon II)", is the early build with 3 lives. Its `OBJ` is the code of Plus/4 World's "early stages" download. In this disk's 1992 export, `LANDSCA2.BIN` has the same bytes as `LANDSCA1.BIN`; the disk itself holds the real `LANDSCAPE-2`.
- **`DISK10`**, "Xargon's Revenge – 5 lives", is the source of Plus/4 World's loading-picture disk. Its `LOADER.BIN`, `P10C0010.BIN`, `P208000C.BIN`, `P3100040.BIN` and `P4040008.BIN` are byte-identical to that disk's `LOADER` and `P1`–`P4`. Its `P3` is the build with 5 lives and harder waves. The physical disk now has 40 unreadable sectors, so the 1992 export is the complete copy.

The Plus/4 World disk version's `BJH` is byte-identical to `DISK9/BJH.BIN`.

[ga-src]: https://www.gremlinarchive.com/index.php/2016/05/25/micro-projects-source-code/
[ga-zip]: http://agremlinintheworks.co.uk/archive/wp-content/uploads/2016/05/Old-Development-Disks.zip
[ga-roy]: https://www.gremlinarchive.com/index.php/2016/05/24/micro-projects-royalty-statements/
[ga-slip]: https://www.gremlinarchive.com/index.php/2016/05/24/compliment-slip-royalty-notes/
[ga-trade]: https://www.gremlinarchive.com/index.php/2016/05/23/early-tradeshow-leaflet/
[ga-photo]: https://www.gremlinarchive.com/index.php/2016/06/02/anthony-clarke-photograph/
[ga-me]: https://www.gremlinarchive.com/index.php/2017/07/31/a-gremlin-in-the-works-anthony-clarke/
[ga-xr]: https://www.gremlinarchive.com/index.php/2016/11/01/xargons-revenge-c16plus4/
[ga-xw]: https://www.gremlinarchive.com/index.php/2016/05/24/xargon-wars-trade-promotion/
[ga-classics]: https://www.gremlinarchive.com/index.php/2021/02/13/c16-classics/
[ga-omnibus]: https://www.gremlinarchive.com/index.php/2021/12/20/c16-omnibus/
