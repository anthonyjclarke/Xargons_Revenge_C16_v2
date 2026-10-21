#!/usr/bin/env python3
"""Capture both game versions in play on every sheet, for side-by-side evidence.

For each version and sheet: start the game with one scripted fire press, stop
at STLOOP (after REPLAY has set sheet 0), set SHEET to the wanted sheet so the
original SETSHT and ALIDEF set the wave up, then run 128 main-loop passes with
no input and save a screenshot and memory. Only SHEET and JFIRE are written;
no instruction is changed. Pillow is needed for the pixel comparison.
"""

import argparse
import json
from pathlib import Path

from restore_c16 import ROOT, GAME_VERSIONS, digest, version_aliens
from verify_vice import TITLE_PASSES, labels_of, run_monitor, stops

LOOP_PASSES = 48  # aliens drawn, before any collision on any sheet
FONT_ALIENS = 0x3EA8  # chars 213-220


def capture(build):
    build = build.resolve()
    labels = labels_of(build)
    output = build / 'versions'
    output.mkdir(parents=True, exist_ok=True)
    bjh = (build / 'aliens-v1.bin').read_bytes()
    rows = []
    for sheet in range(16):
        row = {'sheet': sheet + 1, 'SHEET': sheet}
        for version in GAME_VERSIONS:
            stem = f'v{version}-sheet{sheet + 1:02d}'
            shot, dump = output / (stem + '.png'), output / (stem + '.bin')
            for path in (shot, dump):
                path.unlink(missing_ok=True)
            log = run_monitor(output, stem,
                f'load "{build / f"xargons-revenge-v{version}.prg"}" 0\n'
                f'break {labels["TITTER"]:x}\nignore 1 {TITLE_PASSES:x}\ng 1800\n'
                f'> {labels["JFIRE"]:x} 80\ndelete 1\nbreak {labels["STLOOP"]:x}\nx\n'
                f'> {labels["SHEET"]:x} {sheet:02x}\ndelete 1\nbreak {labels["LOOP"]:x}\nx\n'
                f'> {labels["JFIRE"]:x} 00\ndelete 1\nbreak {labels["LOOP"]:x}\nignore 1 {LOOP_PASSES - 1:x}\nx\n'
                f'screenshot "{shot}" 2\nbsave "{dump}" 0 0000 3fff\nquit\n')
            expected = [labels['TITTER'], labels['STLOOP'], labels['LOOP'], labels['LOOP']]
            if stops(log) != expected:
                raise ValueError(f'{stem}: unexpected stops {stops(log)}')
            memory = dump.read_bytes()
            glyphs = memory[FONT_ALIENS:FONT_ALIENS + 64]
            want = version_aliens(bjh, version)[sheet * 64:(sheet + 1) * 64]
            if memory[labels['SHEET']] != sheet or glyphs != want:
                raise ValueError(f'{stem}: SHEET or alien characters are not the expected ones')
            if memory[labels['LIVES']] != 5 or memory[labels['DEAD']]:
                raise ValueError(f'{stem}: the ship died before the capture; use fewer passes')
            aliens = [(memory[labels['ALIXPS'] + i], memory[labels['ALIYPS'] + i], memory[labels['ALSTAT'] + i])
                      for i in range(16)]
            row[f'v{version}'] = {'screenshot': shot.name, 'screenshot_sha256': digest(shot.read_bytes()),
                                  'alien_chars_sha256': digest(glyphs), 'lives': memory[labels['LIVES']],
                                  'aliens_x_y_status': aliens}
        try:
            from PIL import Image, ImageChops
            a, b = (Image.open(output / row[f'v{v}']['screenshot']).convert('RGB') for v in GAME_VERSIONS)
            difference = ImageChops.difference(a, b).convert('L').point(lambda x: 255 if x else 0)
            row['differing_pixels'] = sum(1 for p in difference.getdata() if p)
            row['same_game_state'] = row['v1']['aliens_x_y_status'] == row['v2']['aliens_x_y_status']
            if sheet >= 4 and not row['differing_pixels']:
                raise ValueError(f'Sheet {sheet + 1}: versions should differ on screen')
            if sheet < 4 and row['differing_pixels']:
                raise ValueError(f'Sheet {sheet + 1}: versions should be identical on screen')
        except ImportError:
            row['differing_pixels'] = 'not measured: Pillow not installed'
        rows.append(row)
        print(f"sheet {sheet + 1:2d}: differing pixels {row['differing_pixels']}")
    report = {'method': __doc__.strip().splitlines()[0],
              'state': f'STLOOP with SHEET set, then {LOOP_PASSES} main-loop passes without input',
              'emulator': 'VICE xplus4, PAL C16, 16 KB, sound off, -TEDfilter 0',
              'loop_passes': LOOP_PASSES, 'sheets': rows}
    (output / 'game-versions.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path, default=ROOT / 'build')
    capture(parser.parse_args().build_dir)
