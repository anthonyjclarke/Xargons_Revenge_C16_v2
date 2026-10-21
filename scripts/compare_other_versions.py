#!/usr/bin/env python3
"""Compare the graphics of downloaded Xargon's Revenge copies with game v1 and v2.

Reads the files in `Other Versions/` (never modifies them), the two rebuilt
game versions and the preserved Side 2 graphics files, then writes a single
self-contained page, docs/analysis/other-versions.html, that decodes the
aliens, landscape bank, font bank, title banner and ship of every copy.

VICE screenshots of each copy, and the memory of both tapes at the game's
entry ($1800), are captured into build/other-versions/ the first time (or with
--recapture). The packed running version is read from build/reference-memory.bin,
which scripts/verify_vice.py writes.

Tapes: VICE's -autostart doesn't press Play on the C16 datasette, so each tape
is attached with -1, LOAD is typed from -keybuf and the monitor's `tapectrl 1`
starts the datasette.
"""

import argparse
import base64
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from d64_image import D64Image  # noqa: E402
from restore_c16 import tool  # noqa: E402

OTHER = ROOT / 'Other Versions'
SIDE2 = ROOT / 'Original Source Recovered/2026/Xargons-Revenge-C16-Side2'
BUILD = ROOT / 'build'
SHOTS = BUILD / 'other-versions'
OUTPUT = ROOT / 'docs/analysis/other-versions.html'
IMAGES = ROOT / 'docs/images/other-versions'

# Plus/4 World entry the downloads came from; SHA-256 matched on 22-10-2026
# (docs/OTHER_VERSIONS.md, Appendix A).
SITE = 'https://plus4world.powweb.com/software/Xargons_Revenge'
DL = 'https://plus4world.powweb.com/'

ORIGINAL = OTHER / 'xargons_revenge - original release.tap'
TAP = OTHER / 'xargons_revenge_c16_classics_ii.tap'
VSF = OTHER / 'xargons_revenge_c16_classics_ii.vsf'
DISK = OTHER / 'xargons_revenge_disk.d64'
PICTURE = OTHER / 'xargons_revenge_loader_picture.d64'
EARLY = OTHER / 'xargons_revenge_early_stages_g1800.prg'

CODE_END = 0x379E          # code $1800-$379D must match OBJ
VSF_RAM = 0xB9             # PLUS4MEM module: 22-byte header, 4 config bytes, then RAM


def digest(data):
    return hashlib.sha256(data).hexdigest()


def prg(data):
    return data[0] | data[1] << 8, data[2:]


def place(memory, data):
    address, body = prg(data)
    memory[address:address + len(body)] = body
    return address, address + len(body)


def side2(name):
    return prg((SIDE2 / name).read_bytes())[1]


def disk_files(path):
    return {f.name: f.data for f in D64Image(path).files()}


# ---------------------------------------------------------------- memory images

def build_version(n):
    memory = bytearray(0x10000)
    place(memory, (BUILD / f'xargons-revenge-v{n}.prg').read_bytes())
    return memory


def running_version():
    memory = bytearray(0x10000)
    memory[0x0400:0x4000] = (BUILD / 'reference-memory.bin').read_bytes()
    return memory


def disk_version():
    """Single ,8,1 file from $0322 to $3FFF; its loader loads BJH to $0C00 and
    copies four pages to $0400 with an unrolled, correct loop."""
    files = disk_files(DISK)
    main = next(data for name, data in files.items() if name.startswith('XARGONS'))
    memory = bytearray(0x10000)
    place(memory, main)
    assert bytes((0xBD, 0x00, 0x0C, 0x9D, 0x00, 0x04)) in memory[0x0322:0x0400], 'unexpected disk loader'
    bjh = prg(files['BJH'])[1]
    memory[0x0C00:0x1000] = bjh
    memory[0x0400:0x0800] = memory[0x0C00:0x1000]
    return memory


def picture_version():
    """LOADER ($0300) loads P1-P4 from device 8; P4's header is $0800. Its copy
    loop increments both high bytes ($0371, $0374), so $0800-$0BFF lands at
    $0400-$07FF unchanged."""
    files = disk_files(PICTURE)
    memory = bytearray(0x10000)
    loader = prg(files['LOADER'])
    assert loader[0] == 0x0300 and bytes((0xEE, 0x71, 0x03, 0xEE, 0x74, 0x03)) in loader[1], \
        'unexpected picture-disk loader'
    for name in sorted(files):
        if name.startswith(('P3', 'P4')):
            place(memory, files[name])
    memory[0x0400:0x0800] = memory[0x0800:0x0C00]
    return memory


def tape_version(stem):
    memory = bytearray(0x10000)
    memory[0x0000:0x4000] = (SHOTS / f'{stem}-entry.bin').read_bytes()
    return memory


def snapshot_ram():
    """RAM of the VICE snapshot of the Classics II tape, taken at the title screen."""
    data = VSF.read_bytes()
    assert data.startswith(b'VICE Snapshot File\x1a') and data[0x9F:0xA7] == b'PLUS4MEM'
    return bytearray(data[VSF_RAM:VSF_RAM + 0x10000])


def early_version():
    memory = bytearray(0x10000)
    place(memory, EARLY.read_bytes())
    return memory


# ---------------------------------------------------------------- captures

def vice(args, cycles, shot):
    subprocess.run([tool('xplus4'), '-default', '+saveres', '+sound', '-TEDfilter', '0', '-warp',
                    '-limitcycles', str(cycles), '-exitscreenshot', str(shot), *args],
                   cwd=str(SHOTS), capture_output=True, timeout=300)
    if not shot.is_file():
        raise RuntimeError(f'VICE did not write {shot.name}')


def capture(force):
    SHOTS.mkdir(parents=True, exist_ok=True)
    c16 = ['-model', 'c16pal', '-ramsize', '16']
    jobs = {
        'disk-title.png': (c16 + ['-autostart', str(DISK)], 250_000_000),
        'picture-loading.png': (c16 + ['-autostart', str(PICTURE)], 25_000_000),
        'picture-title.png': (c16 + ['-autostart', str(PICTURE)], 250_000_000),
        'early-title.png': (c16 + ['-initbreak', 'ready', '-moncommands', 'early.mon'], 250_000_000),
    }
    (SHOTS / 'early.mon').write_text(f'load "{EARLY}" 0\ng 1800\n')
    (SHOTS / 'play.mon').write_text('tapectrl 1\nx\n')
    for stem, tape in (('original', ORIGINAL), ('classics', TAP)):
        load = c16 + ['-1', str(tape), '-keybuf', 'load\n', '-initbreak', 'ready', '-moncommands']
        # Novaload screen part-way through; then memory at $1800 and the title.
        jobs[f'{stem}-loading.png'] = (load + ['play.mon'], 150_000_000)
        (SHOTS / f'{stem}.mon').write_text(f'tapectrl 1\nbreak exec 1800\nx\n'
                                           f'bsave "{SHOTS / (stem + "-entry.bin")}" 0 0000 3fff\ndelete 1\nx\n')
        jobs[f'{stem}-title.png'] = (load + [f'{stem}.mon'], 600_000_000)
    for name, (args, cycles) in jobs.items():
        if force or not (SHOTS / name).is_file():
            vice(args, cycles, SHOTS / name)
    for stem in ('original', 'classics'):
        if not (SHOTS / f'{stem}-entry.bin').is_file():
            raise RuntimeError(f'{stem} tape did not reach $1800')
    IMAGES.mkdir(parents=True, exist_ok=True)
    for name in jobs:
        (IMAGES / name).write_bytes((SHOTS / name).read_bytes())


def png(path):
    return 'data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode()


# ---------------------------------------------------------------- comparison

def glyph_diffs(a, b):
    return sorted({i // 8 for i in range(len(a)) if a[i] != b[i]})


def byte_diffs(a, b):
    return sum(1 for x, y in zip(a, b) if x != y)


def tape_rule(bjh):
    """Release tape loader: page p of $0400 gets BJH[p:p+256]."""
    padded = bjh + bytes(4)
    return b''.join(padded[p:p + 256] for p in range(4))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--recapture', action='store_true', help='rerun VICE for every screenshot')
    args = parser.parse_args()

    capture(args.recapture)
    assets = json.loads((ROOT / 'docs/analysis/asset-data.json').read_text())
    tables = assets['tables']
    palette = json.loads((ROOT / 'docs/verification/ted-palette.json').read_text())['rgb']
    bjh, land1, land2, frak = (side2('089_BJH.prg'), side2('082_LANDSCAPE-1.prg'),
                               side2('083_LANDSCAPE-2.prg'), side2('081_FRAK~21.prg'))
    v1 = build_version(1)
    code_v1 = bytes(v1[0x1800:CODE_END])

    downloads = {
        'disk': ('Disk version', DL + 'dl/games/x/xargons_revenge_disk.zip'),
        'picture': ('With loading screen', DL + 'dl/games/x/xargons_revenge_loader_picture.zip'),
        'prg': ('Download (main entry)', DL + 'dl/games/x/xargons_revenge.prg'),
        'original': ('Download (tape)', DL + 'tap/xargons_revenge.zip'),
        'classics': ('C16 Classics II', DL + 'tap/xargons_revenge_c16_classics_ii.zip'),
        'early': ('Early stages', DL + 'dl/games/x/xargons_revenge_early_stages_g1800.prg'),
    }
    sources = [
        dict(id='v1', name='Game v1', file='build/xargons-revenge-v1.prg', memory=v1,
             origin='Rebuilt here from your 2026 source disk (development loader).',
             shots=[('Title', BUILD / 'restored-title.png'),
                    ('Sheet 5 in play', ROOT / 'docs/images/versions/v1-sheet05.png')]),
        dict(id='disk', name='Disk version', file='Other Versions/xargons_revenge_disk.d64',
             memory=disk_version(), shots=[('Title', SHOTS / 'disk-title.png')],
             origin='Downloaded. One ",8,1" file from $0322 plus BJH; a loader at $0340 loads BJH to $0C00 '
                    'and copies it to $0400 correctly.'),
        dict(id='picture', name='Loading-picture disk', file='Other Versions/xargons_revenge_loader_picture.d64',
             memory=picture_version(),
             shots=[('Loading screen', SHOTS / 'picture-loading.png'), ('Title', SHOTS / 'picture-title.png')],
             origin='Downloaded. LOADER, P1 and P2 are byte-identical to your 2026 Side 1 disk; this copy also '
                    'has P3 (game, $1000-$3FFF) and P4 (aliens = BJH). The loader copies correctly.'),
        dict(id='v2', name='Game v2', file='build/xargons-revenge-v2.prg', memory=build_version(2),
             origin='Rebuilt here from your source, with BJH placed by the release tape loader\'s copy rule.',
             shots=[('Title', BUILD / 'restored-v2-title.png'),
                    ('Sheet 5 in play', ROOT / 'docs/images/versions/v2-sheet05.png')]),
        dict(id='original', name='Original release tape', file='Other Versions/xargons_revenge - original release.tap',
             memory=tape_version('original'),
             shots=[('Novaload loading', SHOTS / 'original-loading.png'), ('Title', SHOTS / 'original-title.png')],
             origin='Downloaded tape of the 1985 Gremlin cassette (Novaload A100001, "ZARGON REVENGE"). Loaded in '
                    'VICE and read at $1800. Its loader at $0C00 loads BJH to $0800 and makes the faulty copy.'),
        dict(id='prg', name='Running version', file='xargons_revenge.prg', memory=running_version(),
             origin='Downloaded packed PRG (same bytes as Other Versions/xargons_revenge.prg). Decompressed in '
                    'VICE; a cassette loader reading P1-P4 from device 1 is still at $0C00.',
             shots=[('Title', BUILD / 'reference-run-title.png')]),
        dict(id='classics', name='C16 Classics II tape', file='Other Versions/xargons_revenge_c16_classics_ii.tap / .vsf',
             memory=tape_version('classics'),
             shots=[('Novaload loading', SHOTS / 'classics-loading.png'), ('Title', SHOTS / 'classics-title.png')],
             origin='Downloaded compilation tape (Novaload A100001, "XARGONS REVENGE"). Loaded in VICE and read at '
                    '$1800; same $0C00 loader as the original release. The .vsf snapshot of it agrees.'),
        dict(id='early', name='Early stages', file='Other Versions/xargons_revenge_early_stages_g1800.prg',
             memory=early_version(), shots=[('Title', SHOTS / 'early-title.png')],
             origin='Downloaded. One file $1000-$3FFF, started with G 1800. No alien data: $0400 is not in the file.'),
    ]
    other_copy = OTHER / 'xargons_revenge.prg'
    assert other_copy.read_bytes() == (ROOT / 'xargons_revenge.prg').read_bytes()

    hashes = {
        'disk': digest(DISK.read_bytes()), 'picture': digest(PICTURE.read_bytes()),
        'prg': digest((ROOT / 'xargons_revenge.prg').read_bytes()), 'early': digest(EARLY.read_bytes()),
        'original': digest(ORIGINAL.read_bytes()),
        'classics': digest(TAP.read_bytes()) + ' (tap)<br>' + digest(VSF.read_bytes()) + ' (vsf)',
        'v1': digest((BUILD / 'xargons-revenge-v1.prg').read_bytes()),
        'v2': digest((BUILD / 'xargons-revenge-v2.prg').read_bytes()),
    }

    # The tape loaders must be the one disassembled in docs/verification/release-tape-loader.s.
    loader = (BUILD / 'release-tape-loader.bin').read_bytes()
    for s in sources:
        if s['id'] in ('original', 'classics'):
            assert bytes(s['memory'][0x0C00:0x0C60]) == loader, f"{s['id']}: different $0C00 loader"
    snap = snapshot_ram()
    classics = next(s for s in sources if s['id'] == 'classics')['memory']
    assert snap[0x0400:0x0800] == classics[0x0400:0x0800] and snap[0x3800:0x3FF0] == classics[0x3800:0x3FF0]

    rows = []
    for s in sources:
        m = s['memory']
        aliens = bytes(m[0x0400:0x0800])
        land = bytes(m[0x1000:0x1800])
        font = bytes(m[0x3800:0x4000])
        code = bytes(m[0x1800:CODE_END])
        if s['id'] == 'early':
            alien_status, alien_kind = 'Not in file', 'none'
        elif aliens == bjh:
            alien_status, alien_kind = 'BJH as stored: 16 designs', 'v1'
        elif aliens == tape_rule(bjh):
            alien_status, alien_kind = 'BJH by tape rule: 4 designs', 'v2'
        else:
            alien_status, alien_kind = 'Different', 'diff'

        def against(data, refs):
            best = min(refs, key=lambda r: byte_diffs(data, r[1]))
            return best[0], glyph_diffs(data, best[1]), byte_diffs(data, best[1])
        land_name, land_glyphs, land_bytes = against(land, [('LANDSCAPE-2', land2), ('LANDSCAPE-1', land1)])
        font_name, font_glyphs, font_bytes = against(font, [('FRAK!', frak)])
        code_bytes = byte_diffs(code, code_v1)

        tables_here = {}
        for name in ('BANNER', 'SHPDT1', 'CHR87', 'CHR91'):
            ref = v1[tables[name]['address']:tables[name]['address'] + tables[name]['bytes']]
            at = m.find(ref, 0x1000, 0x4000)
            tables_here[name] = None if at < 0 else at - tables[name]['address']
        rows.append(dict(
            id=s['id'], name=s['name'], file=s['file'], origin=s['origin'], sha=hashes[s['id']],
            aliens=aliens.hex() if alien_kind != 'none' else None, alien_status=alien_status, alien_kind=alien_kind,
            land=land.hex(), land_name=land_name, land_glyphs=land_glyphs, land_bytes=land_bytes,
            font=font.hex(), font_name=font_name, font_glyphs=font_glyphs, font_bytes=font_bytes,
            code_bytes=code_bytes, tables=tables_here, download=downloads.get(s['id']),
            shots=[(title, png(path)) for title, path in s['shots']],
        ))

    shared = dict(banner=v1[tables['BANNER']['address']:][:320].hex(),
                  ship=v1[tables['SHPDT1']['address']:][:64].hex(),
                  bjh=bjh.hex(), land1=land1.hex(), land2=land2.hex(), frak=frak.hex(),
                  regs=assets['gameplay_capture']['registers'])
    page = TEMPLATE.replace('/*DATA*/', json.dumps(dict(palette=palette, rows=rows, shared=shared, site=SITE)))
    OUTPUT.write_text(page)
    print(f'Wrote {OUTPUT.relative_to(ROOT)} ({len(page) // 1024} KiB)')
    for r in rows:
        print(f"{r['id']:9} aliens: {r['alien_status']:28} land: {r['land_name']} +{r['land_bytes']}B "
              f"font: {r['font_name']} +{len(r['font_glyphs'])} glyphs  code vs OBJ: {r['code_bytes']}B  "
              f"tables moved: {r['tables']}")


TEMPLATE = (Path(__file__).with_name('other_versions_template.html')).read_text()

if __name__ == '__main__':
    main()
