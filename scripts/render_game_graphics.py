#!/usr/bin/env python3
"""Reconstruct explanatory graphics from Xargon's Revenge's exported original bytes.

Requires Pillow 10.1 or later. Uses asset-data.json, the TED palette measured
from VICE (ted-palette.json) and the verified gameplay screenshot. This is an
asset decoder and diagram generator, not a TED/raster emulator.
"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
INK = '#142c45'
MUTED = '#52677c'
PAPER = '#f4f7fb'
BLUE = '#1768a4'
LINE = '#bdcbd9'
ORIGIN = (32, 40)  # 40 x 25 character matrix in a 384 x 288 VICE capture


def digest(data):
    return hashlib.sha256(data).hexdigest()


def font(size=20):
    return ImageFont.load_default(size=size)


def label(im, xy, text, size=20, fill=INK):
    ImageDraw.Draw(im).text(xy, text, font=font(size), fill=fill)


def canvas(title, subtitle, height, width=1200):
    im = Image.new('RGB', (width, height), PAPER)
    label(im, (32, 22), title, 30)
    label(im, (32, 65), subtitle, 18, MUTED)
    ImageDraw.Draw(im).line((32, 99, width - 32, 99), fill=LINE, width=2)
    return im


def enlarged(im, scale):
    return im.resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST)


def tile_grid(im, xy, width, height, scale):
    d = ImageDraw.Draw(im)
    x, y = xy
    for c in range(width + 1):
        d.line((x + c * 8 * scale, y, x + c * 8 * scale, y + height * 8 * scale), fill=BLUE)
    for r in range(height + 1):
        d.line((x, y + r * 8 * scale, x + width * 8 * scale, y + r * 8 * scale), fill=BLUE)


def code_grid(im, xy, rows, cell=(48, 36)):
    x, y = xy
    d = ImageDraw.Draw(im)
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            box = (x + c * cell[0], y + r * cell[1], x + (c + 1) * cell[0], y + (r + 1) * cell[1])
            d.rectangle(box, fill='white', outline=LINE)
            label(im, (box[0] + 7, box[1] + 8), str(value), 17)


class Graphics:
    def __init__(self, assets, palette):
        self.assets = assets
        self.palette = [tuple(c) for c in palette]
        self.landscape = bytes.fromhex(assets['landscape']['hex'])
        self.font = bytes.fromhex(assets['font']['hex'])
        self.aliens = bytes.fromhex(assets['aliens']['hex'])
        self.running = bytes.fromhex(assets['aliens_v2']['hex'])
        self.capture = assets['gameplay_capture']
        self.reg = self.capture['registers']
        assert len(self.landscape) == len(self.font) == 2048 and len(self.aliens) == 1024

    def table(self, name):
        return bytes.fromhex(self.assets['tables'][name]['hex'])

    def pen(self, index):
        return self.palette[index & 0x7F]

    def glyph(self, bank, code, attribute, background, multi1, multi2):
        """TED rules used by the game: attribute bit 3 selects multicolour.

        Hires: 0 = background, 1 = attribute & $7F. Multicolour pairs:
        00 background, 01 MULTI1, 10 MULTI2, 11 attribute & $77.
        """
        out = Image.new('RGB', (8, 8))
        data = bank[code * 8:code * 8 + 8]
        mc = bool(attribute & 8)
        pens = [self.pen(background), self.pen(multi1), self.pen(multi2), self.pen(attribute & (0x77 if mc else 0x7F))]
        for y, byte in enumerate(data):
            for x in range(8):
                if mc:
                    index = (byte >> (6 - 2 * (x // 2))) & 3
                else:
                    index = 3 if byte & (0x80 >> x) else 0
                out.putpixel((x, y), pens[index])
        return out

    def render(self, rows, bank, attributes, background, multi1, multi2):
        out = Image.new('RGB', (len(rows[0]) * 8, len(rows) * 8))
        for r, row in enumerate(rows):
            for c, code in enumerate(row):
                attribute = attributes[r][c] if isinstance(attributes, list) else attributes
                out.paste(self.glyph(bank, code, attribute, background, multi1, multi2), (c * 8, r * 8))
        return out

    def alien_bank(self, data, alien):
        bank = bytearray(self.font)
        bank[213 * 8:221 * 8] = data[alien * 64:(alien + 1) * 64]
        return bytes(bank)


ALIEN_ATTR = 0x47     # illustrative: game uses random hue 1-7 with luminance 4-7
ALIEN_BACK = 0x31     # BAKCOL for sheets 1-8; sheets 9-16 use $00


def alien_rows(frame):
    # PRTALI writes ALCHR, ALCHR-1 ... to YVAL1[3], [2], [1], [0] = 41, 40, 1, 0.
    base = 213 + frame * 4
    return [[base, base + 1], [base + 2, base + 3]]


def aliens(g, output):
    im = canvas('Aliens: game v1 (development) against game v2 (cassette release)',
                'ALIDEF copies 64 bytes per sheet from ALDATA ($0400) to characters 213-220 ($3EA8).', 1180)
    assert list(g.table('YVAL1')[:4]) == [0, 1, 40, 41]
    for half, (title, data) in enumerate((('Game v1: BJH as stored', g.aliens),
                                          ('Game v2: tape-loader copy', g.running))):
        x0 = 40 + half * 580
        label(im, (x0, 118), title, 24)
        for alien in range(16):
            col, row = alien % 4, alien // 4
            x, y = x0 + col * 135, 165 + row * 215
            bank = g.alien_bank(data, alien)
            for frame in range(2):
                sprite = g.render(alien_rows(frame), bank, ALIEN_ATTR, ALIEN_BACK, 0, 0)
                im.paste(enlarged(sprite, 3), (x + frame * 56, y))
            same = g.aliens[alien * 64:(alien + 1) * 64] == g.running[alien * 64:(alien + 1) * 64]
            label(im, (x, y + 56), f'sheet {alien + 1}', 17)
            label(im, (x, y + 80), f'${0x400 + alien * 64:04X}', 15, MUTED)
            if half:
                page, base = divmod(alien, 4)
                text = 'same as v1' if same else f'= sheet {base + 1}, up {page}'
                label(im, (x, y + 102), text, 15, MUTED if same else '#b42318')
    label(im, (40, 1040), 'Game v2: page p ($0400 + p*256) holds BJH from offset p, so sheets 5-16 reuse the', 19)
    label(im, (40, 1070), 'sheet 1-4 designs raised 1-3 pixel rows; the other 12 designs never appear.', 19)
    label(im, (40, 1110), 'Colour $47 on $31 is illustrative: each alien gets a random hue 1-7 and luminance 4-7.', 17, MUTED)
    im.save(output / 'alien-waves.png')
    frames = []
    for frame in range(2):
        pair = Image.new('RGB', (40, 16), g.pen(ALIEN_BACK))
        for half, data in enumerate((g.aliens, g.running)):
            pair.paste(g.render(alien_rows(frame), g.alien_bank(data, 4), ALIEN_ATTR, ALIEN_BACK, 0, 0), (half * 24, 0))
        frames.append(enlarged(pair, 8))
    frames[0].save(output / 'alien-animation.gif', save_all=True, append_images=frames[1:], duration=250,
                   loop=0, disposal=2, optimize=False)


def ship(g, output):
    im = canvas('The ship: twelve characters redrawn for every pixel position',
                'PRSHIP copies SHPDT1 (4 columns x 16 rows, multicolour) into chars 124-135 at offset YPIX.', 690)
    rows = [list(g.table('SHPCHR')[r * 4:(r + 1) * 4]) for r in range(3)]
    assert rows == [[124, 127, 130, 133], [125, 128, 131, 134], [126, 129, 132, 135]]
    assert list(g.table('YSHIP')) == [0, 1, 2, 3, 40, 41, 42, 43, 80, 81, 82, 83]
    data = g.table('SHPDT1')
    reg = g.reg
    for i, ypix in enumerate((0, 2, 4, 6)):
        bank = bytearray(g.font)
        bank[124 * 8:136 * 8] = bytes(96)
        for x in range(16):
            for column in range(4):
                bank[0x3BE0 - 0x3800 + column * 24 + ypix + x] = data[column * 16 + x]
        sprite = g.render(rows, bytes(bank), 0x2A, reg['BAKCOL'], reg['SHIPC1'], reg['SHIPC2'])
        x0 = 40 + i * 285
        im.paste(enlarged(sprite, 6), (x0, 130))
        tile_grid(im, (x0, 130), 4, 3, 6)
        label(im, (x0, 290), f'YPIX = {ypix}', 20)
    label(im, (40, 345), 'Screen codes (column-major, so each column is one 24-byte strip)', 22)
    code_grid(im, (40, 390), rows, (60, 40))
    label(im, (330, 395), 'SHIPCH = $3BE0 = code 124; column c starts at $3BE0 + 24c.', 19)
    label(im, (330, 435), 'YPIX moves 2 pixels per frame; at 8 the ship moves one row (SHIPY).', 19)
    label(im, (330, 475), 'CHKSHP reads the 12 cells: 180-185 fuel pod, 186-220 fatal.', 19)
    label(im, (40, 560), f"Colours from the gameplay capture: background ${reg['BAKCOL']:02X}, "
                         f"MULTI1 ${reg['SHIPC1']:02X}, MULTI2 ${reg['SHIPC2']:02X}, cell $2A.", 18, MUTED)
    label(im, (40, 600), 'SHIPC2 cycles with the score colour, and the ink flashes red when fuel is low.', 18, MUTED)
    im.save(output / 'ship-character.png')


def land_column(block, top):
    """Character codes for one landscape motif in screen order."""
    if top:   # HARTOP: row 3 gets TOPCHR, row 2 gets TOPCHR+1, 4 columns per motif
        return [[block + c * 2 + 1 for c in range(4)], [block + c * 2 for c in range(4)]]
    # HARBOT: rows 23, 22, 21, 20 get BOTCHR, +1, +2, +3; 8 columns per motif
    return [[block + c * 4 + 3 - r for c in range(8)] for r in range(4)]


def landscape(g, output):
    im = canvas('Landscape: roof and ground motifs streamed in from the right',
                'TOPNEW picks 1 of 8 four-column roof motifs; BOTNEW 1 of 6 eight-column ground motifs.', 1000)
    reg = g.reg
    bank = bytes.fromhex(g.capture['landscape_ram_hex'])
    args = (reg['LANCL1'], reg['BAKCOL'], reg['LANCL2'], reg['LANCL3'])
    label(im, (40, 115), 'Roof motifs: base codes 192 + 8k', 22)
    for k in range(8):
        rows = land_column(192 + 8 * k, True)
        x0 = 40 + k * 140
        im.paste(enlarged(g.render(rows, bank, *args), 4), (x0, 155))
        label(im, (x0, 225), f'{192 + 8 * k}-{199 + 8 * k}', 16, MUTED)
    label(im, (40, 275), 'Ground motifs: BOTST = 0, 32, 64, 96, 128, 160', 22)
    for k, base in enumerate(g.table('BOTST')):
        rows = land_column(base, False)
        x0 = 40 + (k % 3) * 380
        y0 = 320 + (k // 3) * 190
        im.paste(enlarged(g.render(rows, bank, *args), 4), (x0, y0))
        tile_grid(im, (x0, y0), 8, 4, 4)
        label(im, (x0, y0 + 138), f'{base}-{base + 31}', 16, MUTED)
    label(im, (40, 715), 'First ground motif, screen order (rows 20-23)', 22)
    code_grid(im, (40, 755), land_column(0, False), (46, 36))
    label(im, (450, 760), 'Each column is 4 consecutive codes, bottom row first.', 18)
    label(im, (450, 800), 'CHAR-ANIM rewrites codes 87 and 91 from CHR87/CHR91 (4 frames).', 18)
    label(im, (450, 840), 'TV-PICTURE draws the ship height into codes 166-170.', 18)
    label(im, (40, 930), f"Rendered from the captured landscape RAM; attribute ${reg['LANCL1']:02X}, "
                         f"MULTI1 ${reg['LANCL2']:02X}, MULTI2 ${reg['LANCL3']:02X}, background ${reg['BAKCOL']:02X}.", 17, MUTED)
    im.save(output / 'landscape-motifs.png')


def pixel_check(g, capture, cells, screen_ram, colour, bank, background, m1, m2, cause):
    """Compare rebuilt cells with a VICE capture; every difference must have a known cause."""
    matches = total = 0
    causes = {}
    for r, c in cells:
        code = screen_ram[r * 40 + c]
        cell = g.glyph(bank, code, colour[r * 40 + c], background, m1, m2)
        wrong = 0
        for y in range(8):
            for x in range(8):
                total += 1
                same = capture.getpixel((ORIGIN[0] + c * 8 + x, ORIGIN[1] + r * 8 + y)) == cell.getpixel((x, y))
                matches += same
                wrong += not same
        if wrong:
            key = cause(r, c, code)
            causes[key] = causes.get(key, 0) + wrong
    if causes.get('unexplained'):
        raise ValueError(f'Unexplained pixel differences {causes}')
    return {'pixels': total, 'matching_pixels': matches, 'differing_pixels_by_cause': causes}


def banner_code(data, row, column):
    """CALCBY: even columns use the high nibble, odd the low; 0 becomes a space."""
    byte = data[row * 20 + column // 2]
    nibble = byte >> 4 if column % 2 == 0 else byte & 15
    return 32 if nibble == 0 else 136 + nibble


def scroll_on(data, row, direction):
    """SCRLIT/BRING on a cleared row. Leftward: 38 steps (JOURNY compares 38),
    each placing column k at 39 then shifting left. Rightward: 40 steps placing
    column 39-k at 0 then shifting right."""
    line = [32] * 40
    if direction == 'left':
        for k in range(38):
            line[39] = banner_code(data, row, k)
            line[0:39] = line[1:40]
    else:
        for k in range(40):
            line[0] = banner_code(data, row, 39 - k)
            line[1:40] = line[0:39]
    return line


def banner(g, screenshot, output):
    title = g.assets['title_capture']
    reg = title['registers']
    im = canvas('Title: 320 bytes of nibbles become a 40 x 16 block picture',
                'SCRLIT scrolls each of 16 rows on from a random side; nibble n selects code 136+n (0 = space).', 660)
    data = g.table('BANNER')
    assert len(data) == 320
    rows = [[banner_code(data, r, c) for c in range(40)] for r in range(16)]
    screen_ram = bytes.fromhex(title['screen_ram_hex'])
    colour = bytes.fromhex(title['colour_ram_hex'])
    captured = [list(screen_ram[(4 + r) * 40:(5 + r) * 40]) for r in range(16)]
    directions, stars = [], 0
    for r in range(16):
        # Stars run on the title page and overwrite blank cells with codes 102-105.
        star_cells = [c for c in range(40) if 102 <= captured[r][c] <= 105]
        stars += len(star_cells)
        mask = lambda line: [32 if c in star_cells else v for c, v in enumerate(line)]
        found = [d for d in ('left', 'right') if mask(scroll_on(data, r, d)) == mask(captured[r])]
        if not found:
            raise ValueError(f'Title row {r} matches neither SCRLIT direction')
        directions.append(found[0])
    attributes = [list(colour[(4 + r) * 40:(5 + r) * 40]) for r in range(16)]
    im.paste(enlarged(g.render(rows, g.font, attributes, reg['BAKCOL'], reg['SHIPC1'], reg['SHIPC2']), 3), (40, 120))
    shot = Image.open(screenshot).convert('RGB')
    check = pixel_check(g, shot, [(r, c) for r in range(5, 19) for c in range(1, 39)], screen_ram, colour,
                        g.font, reg['BAKCOL'], reg['SHIPC1'], reg['SHIPC2'],
                        lambda r, c, code: 'MULTI1 pulse (PULSAT in RAST3)' if code != 32 else
                        'star moved one step (STARS in RAST5)')
    label(im, (40, 520), 'Shown as stored. Every captured title row equals the SCRLIT simulation (stars aside), which', 18)
    label(im, (40, 546), 'lands each row one column right of this layout: column 0 repeats and stored column 39 is lost.', 18)
    label(im, (40, 580), f"Pixel check rows 5-18: {check['matching_pixels']} of {check['pixels']} identical; "
                         'differences are the pulsing MULTI1 colour and moving stars.', 17, MUTED)
    label(im, (40, 608), f"Captured colours: background ${reg['BAKCOL']:02X}, cells ${attributes[0][0]:02X} / "
                         f"${attributes[8][0]:02X}, MULTI1 ${reg['SHIPC1']:02X}, MULTI2 ${reg['SHIPC2']:02X}; "
                         'TITCLS picks a new hue each cycle.', 17, MUTED)
    im.save(output / 'title-banner.png')
    return {'band': 'Title banner', 'rows': '5-18', 'columns': '1-38', **check,
            'captured_rows_equal_scrlit_simulation': True, 'star_cells_excluded': stars,
            'first_matching_direction_per_row': directions}


PLAY = (ORIGIN[0], ORIGIN[1] + 32, ORIGIN[0] + 320, ORIGIN[1] + 160)  # rows 4-19


def versions_overview(g, captures, report, output, first):
    """Side-by-side VICE captures of both game versions on eight sheets."""
    sheets = report['sheets'][first:first + 8]
    im = canvas(f'Game v1 and v2 in play: sheets {first + 1}-{first + 8}',
                f"VICE, same scripted start; SHEET set at STLOOP, then {report['loop_passes']} passes without input.",
                150 + 8 * 150, 820)
    label(im, (130, 112), 'Game v1 (development)', 20)
    label(im, (470, 112), 'Game v2 (cassette release)', 20)
    for i, row in enumerate(sheets):
        y = 145 + i * 150
        label(im, (32, y + 40), f"Sheet {row['sheet']}", 20)
        diff = row['differing_pixels']
        label(im, (32, y + 70), 'identical' if not diff else f'{diff} px differ', 15, MUTED if not diff else '#b42318')
        for v, x in ((1, 130), (2, 470)):
            shot = Image.open(captures / row[f'v{v}']['screenshot']).convert('RGB').crop(PLAY)
            im.paste(shot, (x, y))
    im.save(output / f"versions-sheets-{first + 1:02d}-{first + 8:02d}.png")


def versions_detail(g, captures, report, output):
    """Zoom on one alien per shift: sheet 1, 5, 9, 13 share a design in v2."""
    im = canvas('One alien, four sheets: what the tape loader did',
                'Crops from the VICE captures (x6) beside the decoded frame-0 glyphs for each version.', 820)
    label(im, (220, 115), 'v1 capture', 18)
    label(im, (380, 115), 'v2 capture', 18)
    label(im, (560, 115), 'v1 glyphs', 18)
    label(im, (720, 115), 'v2 glyphs', 18)
    chosen = []
    for k, sheet in enumerate((1, 5, 9, 13)):
        row = report['sheets'][sheet - 1]
        y = 150 + k * 150
        page = (sheet - 1) // 4
        label(im, (32, y + 20), f'Sheet {sheet}', 22)
        label(im, (32, y + 52), 'v2 = v1 sheet 1' + (f', up {page}' if page else ''), 16, MUTED)
        index = next(i for i, (x, yy, s) in enumerate(row['v1']['aliens_x_y_status'])
                     if s in (0, 1) and 1 <= x <= 37 and yy <= 14)
        x, yy, s = row['v1']['aliens_x_y_status'][index]
        chosen.append({'sheet': sheet, 'alien': index, 'column': x, 'window_row': yy})
        box = (PLAY[0] + x * 8, PLAY[1] + yy * 8, PLAY[0] + x * 8 + 16, PLAY[1] + yy * 8 + 16)
        for v, x0 in ((1, 220), (2, 380)):
            crop = Image.open(captures / row[f'v{v}']['screenshot']).convert('RGB').crop(box)
            im.paste(enlarged(crop, 6), (x0, y))
        for data, x0 in ((g.aliens, 560), (g.running, 720)):
            bank = g.alien_bank(data, sheet - 1)
            sprite = g.render(alien_rows(0), bank, 0x71, 0x00, 0, 0)
            im.paste(enlarged(sprite, 6), (x0, y))
            tile_grid(im, (x0, y), 2, 2, 6)
    label(im, (32, 760), 'Live crops include whichever animation frame and colour the alien had at capture time.', 16, MUTED)
    im.save(output / 'versions-detail.png')
    return chosen


def screen(g, screenshot, output):
    """Rebuild the captured frame's play window from RAM and compare pixel classes."""
    capture = Image.open(screenshot).convert('RGB')
    if capture.size != (384, 288):
        raise ValueError('Expected the verified 384 x 288 VICE capture')
    reg = g.reg
    colour = bytes.fromhex(g.capture['colour_ram_hex'])
    screen_ram = bytes.fromhex(g.capture['screen_ram_hex'])
    font_ram = bytes.fromhex(g.capture['font_ram_hex'])
    land_ram = bytes.fromhex(g.capture['landscape_ram_hex'])
    bands = [  # rows, bank, background, multi1, multi2, compared columns
        ('Status', range(0, 2), font_ram, 0x01, reg['LANCL2'], reg['LANCL3'], range(0, 40)),
        ('Play window', range(5, 19), font_ram, reg['BAKCOL'], reg['SHIPC1'], reg['SHIPC2'], range(1, 39)),
    ]
    def cause(r, c, code):
        # RAM was saved after the frame was drawn; these change every frame.
        if r < 2 and 6 <= c <= 13:
            return 'score colour cycle (SCORPT)'
        if 124 <= code <= 135:
            return 'ship MULTI2 colour cycle (SCORPT)'
        if 102 <= code <= 105 or code == 32:
            return 'star moved one step (STARS in RAST5)'
        return 'unexplained'
    results = []
    for name, rows, bank, background, m1, m2, columns in bands:
        check = pixel_check(g, capture, [(r, c) for r in rows for c in columns], screen_ram, colour,
                            bank, background, m1, m2, cause)
        results.append({'band': name, 'rows': f'{rows.start}-{rows.stop - 1}',
                        'columns': f'{columns.start}-{columns.stop - 1}', **check})
    im = canvas('From graphics bytes to the displayed game',
                'Verified PAL C16 capture (no input, 256 main-loop passes) with the five raster bands.', 1050)
    xy = (32, 130)
    im.paste(enlarged(capture.crop((ORIGIN[0], ORIGIN[1], ORIGIN[0] + 320, ORIGIN[1] + 200)), 2), xy)
    info = [
        (0, 2, 'RAST5 | rows 0-1 | status', '$3800 font; 40 columns; background $01'),
        (2, 4, 'RAST1 | rows 2-3 | roof', '$1000 landscape; TOPLX fine scroll; reads input'),
        (4, 20, 'RAST2 | rows 4-19 | play window', '$3800 font; ship colours; scroll, fuel, score'),
        (20, 24, 'RAST3 | rows 20-23 | ground', '$1000 landscape; BOTLX fine scroll; laser'),
        (24, 25, 'RAST4 | row 24 | message', '$3800 font; MESSX fine scroll; background $32'),
    ]
    d = ImageDraw.Draw(im)
    centers = (150, 205, 330, 460, 530)
    for (start, end, title, detail), cy in zip(info, centers):
        y = xy[1] + start * 16
        d.rectangle((32, y, 672, xy[1] + end * 16), outline='#e6edf5', width=1)
        mid = xy[1] + (start + end) * 8
        d.line((672, mid, 692, mid, 705, cy + 10), fill=BLUE, width=2)
        label(im, (715, cy - 6), title, 19)
        label(im, (715, cy + 22), detail, 16, MUTED)
    label(im, (32, 600), 'Pixel check: the band cells rebuilt from captured screen RAM, colour RAM, the font', 20)
    label(im, (32, 630), 'RAM and the captured TED colour variables, against the screenshot above:', 20)
    for i, r in enumerate(results):
        label(im, (52, 670 + i * 32),
              f"{r['band']} rows {r['rows']}, columns {r['columns']}: {r['matching_pixels']} of {r['pixels']} pixels identical", 19, BLUE)
    label(im, (52, 734), 'Every difference is a score/ship colour cycle or a star that moved after the frame was drawn.', 17, MUTED)
    for i, text in enumerate([
        'Screen RAM $0C00 + 40*row + column holds a character code; colour RAM sits $0400 lower.',
        'Attribute bit 3 selects multicolour; aliens and stars are hires, ship, fuel pod and land multicolour.',
        'The raster bands switch character bank, colours and fine scroll; nothing uses sprites (TED has none).',
        'Excluded from the check: the band edges, the 38-column mask and the scrolling land and message rows,',
        'whose fine-scroll values at capture time may differ from those used for the displayed frame.',
    ]):
        label(im, (32, 780 + i * 32), text, 17, MUTED)
    label(im, (32, 960), 'Band borders are explanatory overlays drawn on the enlarged capture.', 17, MUTED)
    im.save(output / 'screen-composition.png')
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path, default=ROOT / 'docs/analysis/asset-data.json')
    parser.add_argument('--palette', type=Path, default=ROOT / 'docs/verification/ted-palette.json')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'docs/analysis/graphics')
    parser.add_argument('--screenshot', type=Path, default=ROOT / 'docs/images/restored-later.png')
    parser.add_argument('--title-screenshot', type=Path, default=ROOT / 'docs/images/restored-title.png')
    parser.add_argument('--versions', type=Path, default=ROOT / 'docs/verification/game-versions.json')
    parser.add_argument('--captures', type=Path, default=ROOT / 'docs/images/versions')
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    assets = json.loads(args.assets.read_text())
    palette = json.loads(args.palette.read_text())
    if len(palette['rgb']) != 128:
        raise ValueError('A TED palette must contain 128 RGB entries')
    g = Graphics(assets, palette['rgb'])
    aliens(g, args.output_dir)
    ship(g, args.output_dir)
    landscape(g, args.output_dir)
    check = screen(g, args.screenshot, args.output_dir)
    version_report = json.loads(args.versions.read_text())
    for first in (0, 8):
        versions_overview(g, args.captures, version_report, args.output_dir, first)
    detail = versions_detail(g, args.captures, version_report, args.output_dir)
    check.append(banner(g, args.title_screenshot, args.output_dir))
    manifest = {'method': 'Original glyph bits and tables; nearest-neighbour enlargement; schematic diagrams.',
                'asset_data_sha256': digest(args.assets.read_bytes()),
                'palette_sha256': digest(args.palette.read_bytes()),
                'palette_source': palette['method'],
                'screenshot_sha256': digest(args.screenshot.read_bytes()),
                'title_screenshot_sha256': digest(args.title_screenshot.read_bytes()),
                'pixel_check': check,
                'game_versions_sha256': digest(args.versions.read_bytes()),
                'version_capture_sha256': {p.name: digest(p.read_bytes())
                                           for p in sorted(args.captures.glob('*.png'))},
                'version_detail_aliens': detail,
                'gif_frame_order': [0, 1], 'gif_frame_duration_ms': 250,
                'gif_timing': 'Illustration only; aliens change frame every ALISPD (5-8) main-loop passes.',
                'images': {p.name: {'size': list(Image.open(p).size), 'sha256': digest(p.read_bytes())}
                           for p in sorted(args.output_dir.iterdir()) if p.suffix in ('.png', '.gif')}}
    (args.output_dir / 'graphics-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(check, indent=2))
    print(f'Wrote {len(manifest["images"])} images and graphics-manifest.json')


if __name__ == '__main__':
    main()
