# Maintaining the HTML Documentation

## Source of Truth

The [complete HTML handbook](XARGONS_REVENGE.html) gathers the repository's Markdown guides, artifact catalogue, validation notes, code analysis, graphics, porting guide and generated reference into one reading copy. It embeds the images, styling, reader controls and Mermaid diagram renderer, so you can open it straight from disk in a browser with no internet connection.

**Edit the Markdown, never the generated HTML.** The generator keeps no second copy of the prose. Each chapter links to its Markdown source, and links between included documents become links within the page. Links to source code, JSON files, SVG atlases and other repository files are relative, so they work only when the handbook sits in `docs/` inside a checkout of the repository.

The page has a contents sidebar, chapter search, image enlargement and print support. Search filters chapters by their full text.

---

## Regeneration

The generator needs **Node.js 20 or later**. Its Markdown parser and the browser diagram renderer are kept in `scripts/vendor/` with their licences, and generation doesn't use npm, install packages or download anything.

| Command           | What it does                                |
| :---------------- | :------------------------------------------ |
| `make docs`       | Build, refresh the analysis, write the HTML |
| `make docs-html`  | Write the HTML from the current Markdown    |
| `make docs-watch` | Rewrite the HTML whenever an input changes  |
| `make docs-check` | Fail if the saved HTML is missing or stale  |
| `make test-docs`  | Run the generator's own tests               |

`node scripts/build_docs.mjs` is the direct equivalent of `make docs-html`; add `--check` or `--watch` for the other modes. If Node isn't on your path, pass it to Make, for example `make docs-html NODE=/path/to/node`.

`make docs` refreshes the code reference, codebase index and asset data from the build, but not the VICE evidence or the graphics. Those need VICE and Pillow, so run them first when they've changed:

```bash
make probes
.venv/bin/python scripts/render_game_graphics.py
make docs
```

The watcher reacts to Markdown, images, configuration and templates. It doesn't rebuild the game or the analysis. Commit the regenerated `docs/XARGONS_REVENGE.html` with the Markdown and assets that produced it.

---

## Chapter Selection and Presentation

`docs/handbook.json` sets the output path, the title and brand text, and the chapter order in two groups: the project guide (history, artwork, quick start, build, testing, validation, analysis, graphics, porting) and the reference and maintenance material. Every chapter is listed explicitly, so a new guide has to be added there before it appears. Machine instructions such as `CLAUDE.md` aren't chapters.

`scripts/build_docs.mjs` gives each heading an ID namespaced by its document, rewrites links to included Markdown files, embeds local images as data URIs and fails on any broken link, missing section, missing file or remote image. Raw HTML in Markdown is escaped. Mermaid code blocks become diagrams in the browser, with their source in a collapsible block.

The page shell is `scripts/docs/handbook.html`, `handbook.css` and `handbook.js`, shared with the Tycoon Tex handbook; the game-specific wording comes from `handbook.json`. The text reads without JavaScript, but search, image enlargement and diagrams need it.

Generation is deterministic and has no timestamp. The source revision shown in the header is a SHA-256 digest of the hashes of every input file, and a `source-provenance` JSON block in the page lists them. It describes the documentation snapshot only; it adds nothing to the game's verification.

---

## Third-Party Renderers

The generator uses [Marked](https://marked.js.org/) 17.0.5 to convert Markdown, and the page embeds [Mermaid](https://mermaid.js.org/) 10.9.3 for the diagrams. Both are pinned, their licence files sit beside them, and both licences are reproduced in the page's notices. Changing either means regenerating the handbook and checking it in a browser.
