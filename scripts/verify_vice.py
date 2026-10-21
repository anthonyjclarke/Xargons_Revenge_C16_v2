#!/usr/bin/env python3
"""Check title, gameplay entry, and the supplied packed game in PAL C16 VICE."""

import argparse
import json
import re
import subprocess
from pathlib import Path

from restore_c16 import (ROOT, REFERENCE, ENTRY, LOAD, TOP, digest, mos_hex,
                         prepare_sources, tool)

# VICE monitor numbers are hexadecimal; these are written with explicit {:x}.
TITLE_PASSES = 36   # TITTER passes (each a 32-unit DELAY) before the scripted fire
LOOP_PASSES = 256   # main-loop passes after fire, before the gameplay capture


def labels_of(build):
    return {name: int(address, 16) for address, name in re.findall(
        r'^al ([0-9A-Fa-f]+) \.(\w+)$', (build / 'revenge.labels').read_text(), re.MULTILINE)}


def stops(log):
    """Addresses where VICE actually stopped; 'BREAK:' lines only echo a set."""
    return [int(a, 16) for a in re.findall(r'^#\d+ \(Stop on\s+exec ([0-9a-fA-F]{4})\)', log, re.MULTILINE)]


def run_monitor(build, stem, commands, cycles=400000000, check=True):
    """Run VICE headless with audio off, warp and a fixed cycle limit."""
    commands_file = build / (stem + '.mon')
    commands_file.write_text(commands)
    log = build / (stem + '-monitor.log')
    log.unlink(missing_ok=True)
    result = subprocess.run([
        tool('xplus4'), '-default', '+saveres', '-model', 'c16pal', '-ramsize', '16',
        # Fix the rendering filter so captures don't depend on user settings;
        # decoded glyph colours are compared with them pixel by pixel.
        '+sound', '-TEDfilter', '0', '-initbreak', 'ready', '-moncommands', str(commands_file),
        '-logfile', str(build / (stem + '-vice.log')), '-monlog', '-monlogname', str(log),
        '-warp', '-limitcycles', str(cycles),
    ], cwd=str(ROOT), capture_output=True, timeout=120)
    (build / (stem + '-console.log')).write_bytes(result.stdout + result.stderr)
    if check:
        result.check_returncode()
    return log.read_text()


def play(build, labels, program, stem, entry):
    """Reach the title, inject one fire press at the original BIT test, then run
    the main loop with no further input. Captures title, entry and a later frame."""
    names = [f'{stem}-{n}' for n in ('title.png', 'gameplay.png', 'later.png',
                                      'memory.bin', 'later-memory.bin', 'title-memory.bin')]
    for name in names:
        (build / name).unlink(missing_ok=True)
    # After each delete the next breakpoint reuses checkpoint #1.
    log = run_monitor(build, stem,
        f'load "{program}" 0\n'
        f'break {labels["TITTER"]:x}\nignore 1 {TITLE_PASSES:x}\ng {entry:x}\n'
        f'screenshot "{build / names[0]}" 2\n'
        f'bsave "{build / names[5]}" 0 0000 3fff\n'
        f'> {labels["JFIRE"]:x} 80\ndelete 1\n'
        f'break {labels["LOOP"]:x}\nx\n'
        f'> {labels["JFIRE"]:x} 00\n'
        f'screenshot "{build / names[1]}" 2\n'
        f'bsave "{build / names[3]}" 0 0000 3fff\ndelete 1\n'
        f'break {labels["LOOP"]:x}\nignore 1 {LOOP_PASSES - 1:x}\nx\n'
        f'screenshot "{build / names[2]}" 2\n'
        f'bsave "{build / names[4]}" 0 0000 3fff\nquit\n')
    hits = stops(log)
    reached = hits[:1] == [labels['TITTER']] and hits[1:] == [labels['LOOP']] * 2
    for name in names[:3]:
        if not (build / name).read_bytes().startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError(f'Missing VICE screenshot: {name}')
    return log, (build / names[3]).read_bytes(), (build / names[4]).read_bytes(), reached


def palette(build):
    """Measure VICE's rendered RGB for all 128 TED colour indices.

    A workspace routine at $1000 fills 128 screen cells with ROM code 160 (a
    solid block) and colour RAM with indices 0-127, then waits three frames
    using the raster high bit. No game code is involved.
    """
    shot = build / 'ted-palette.png'
    shot.unlink(missing_ok=True)
    program = [0xA2, 0x7F,                    # LDX #127
               0xA9, 0xA0, 0x9D, 0x00, 0x0C,  # fill: LDA #160 / STA $0C00,X
               0x8A, 0x9D, 0x00, 0x08,        # TXA / STA $0800,X
               0xCA, 0x10, 0xF4,              # DEX / BPL fill
               0xA0, 0x03,                    # LDY #3
               0xAD, 0x1C, 0xFF, 0x29, 0x01, 0xD0, 0xF9,  # wait while raster bit 8 = 1
               0xAD, 0x1C, 0xFF, 0x29, 0x01, 0xF0, 0xF9,  # wait while raster bit 8 = 0
               0x88, 0xD0, 0xEF,              # DEY / BNE
               0xEA]                          # NOP (stop)
    stop = 0x1000 + len(program) - 1
    log = run_monitor(build, 'palette',
        '> 1000 ' + ' '.join(f'{b:02x}' for b in program) + '\n'
        f'> ff15 00\nbreak {stop:x}\ng 1000\nscreenshot "{shot}" 2\nquit\n')
    if stops(log) != [stop]:
        raise ValueError('Palette capture did not complete')
    from PIL import Image  # Pillow is needed only for this measurement
    image = Image.open(shot).convert('RGB')
    rgb = []
    for index in range(128):
        x, y = 32 + (index % 40) * 8, 40 + (index // 40) * 8
        cell = {image.getpixel((x + dx, y + dy)) for dx in range(8) for dy in range(8)}
        if len(cell) != 1:
            raise ValueError(f'TED colour {index} cell is not uniform: {cell}')
        rgb.append(list(cell.pop()))
    report = {'method': 'VICE xplus4 c16pal, -TEDfilter 0, internal palette; ROM code 160 cells '
                        'with colour RAM 0-127 at screen origin (32, 40)',
              'rgb': rgb}
    (build / 'ted-palette.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def loading_screen(build):
    """Show the Side 1 disk's P1 (screen) and P2 (colour) files as the C16 would.

    The files load at their saved addresses ($0C00 and $0800). The loader on
    that disk sets a black background and border; the text is lower case, so
    the TED character base is set to the ROM's lower-case set ($D400). IRQs are
    masked and the hardware cursor moved off screen; captures follow 3 and 19 frames.
    """
    from restore_c16 import SCREEN_EXTRACTED
    files = sorted(SCREEN_EXTRACTED.glob('00[23]_P*.prg'))
    # "now loading" has attribute $F1 (flash bit set): capture both phases.
    shots = [build / 'loading-screen.png', build / 'loading-screen-flash.png']
    wait = [0x78, 0xA0, 0x03,
            0xAD, 0x1C, 0xFF, 0x29, 0x01, 0xD0, 0xF9,
            0xAD, 0x1C, 0xFF, 0x29, 0x01, 0xF0, 0xF9,
            0x88, 0xD0, 0xEF, 0xEA]
    stop = 0x1000 + len(wait) - 1
    commands = ''.join(f'load "{f}" 0\n' for f in files)
    commands += ('> ff15 00\n> ff19 00\n> ff0c 03 ff\n> ff13 d5\n'
                 '> 1000 ' + ' '.join(f'{b:02x}' for b in wait) + '\n'
                 f'break {stop:x}\ng 1000\nscreenshot "{shots[1]}" 2\n'
                 f'> 1002 10\ng 1000\nscreenshot "{shots[0]}" 2\nquit\n')
    for shot in shots:
        shot.unlink(missing_ok=True)
    log = run_monitor(build, 'loading-screen', commands)
    if stops(log) != [stop, stop] or len(files) != 2:
        raise ValueError('Loading-screen capture did not complete')
    return [f.name for f in files]


def tape_loader(build, reference):
    """Disassemble the loader left at $0C00 in the running version (evidence only).

    These bytes come from the downloaded PRG after decompression; they are
    never placed in either game version.
    """
    from restore_c16 import tool
    raw = reference[0x0C00 - LOAD:0x0C60 - LOAD]
    (build / 'release-tape-loader.bin').write_bytes(raw)
    listing = subprocess.run([tool('da65'), '--cpu', '6502', '-S', '0x0c00', '--comments', '0',
                              str(build / 'release-tape-loader.bin')], capture_output=True, text=True, check=True).stdout
    listing = '\n'.join(line for line in listing.splitlines() if not line.startswith(('; Created', '; Input file')))
    (build / 'release-tape-loader.s').write_text(
        '; Disassembly of $0C00-$0C5F from the decompressed xargons_revenge.prg (running version).\n'
        '; Evidence only: not source, and not used in either game version.\n' + listing + '\n')
    name = raw[0x52:0x54].decode('ascii', 'replace')
    if raw[0x3C:0x42] != bytes((0xEE, 0x34, 0x0C, 0xEE, 0x38, 0x0C)):
        raise ValueError('Unexpected tape-loader copy loop')
    return {'address': '$0C00', 'bytes_sha256': digest(raw), 'device': raw[0x0C],
            'filename_after_last_load': name,
            'copy_loop': {'lda_operand_after_loop': f'${raw[0x35] << 8 | raw[0x34]:04X}',
                          'sta_operand_after_loop': f'${raw[0x38] << 8 | raw[0x37]:04X}',
                          'inc_targets': [f'${raw[0x3E] << 8 | raw[0x3D]:04X}', f'${raw[0x41] << 8 | raw[0x40]:04X}'],
                          'meaning': 'INC $0C34 bumps the LDA operand low byte (source +1 per page); '
                                     'INC $0C38 bumps the STA operand high byte (destination +256)'}}


def classify(address):
    if 0x0400 <= address < 0x0800:
        return 'alien graphics (ALDATA)'
    if 0x0800 <= address < 0x1000:
        return 'colour/screen RAM work area'
    if 0x1000 <= address < 0x1800:
        return 'landscape graphics'
    if ENTRY <= address < 0x379E:
        return 'initialized code and data'
    if 0x379E <= address < 0x3800:
        return 'padding below the font'
    return 'font graphics'


def alien_shift(restored, reference):
    """Test the cassette loader's copy: page p came from source offset p, not p*256."""
    aliens = restored[0:0x400]
    pages = []
    for page in range(4):
        got = reference[page * 0x100:(page + 1) * 0x100]
        pages.append({'page': f'${0x400 + page * 0x100:04X}',
                      'equals_BJH_offset': next((f'${o:03X}' for o in range(0x400 - 0xFF)
                                                 if aliens[o:o + 0x100] == got), None)})
    return pages


def verify(build):
    build = build.resolve()
    labels = labels_of(build)
    code = (build / 'recovered-code.bin').read_bytes()
    check = labels['TITTER']
    if code[check - ENTRY:check - ENTRY + 3] != bytes((0x24, labels['JFIRE'], 0x10)):
        raise ValueError('Cannot identify the original title fire test')
    program = build / 'xargons-revenge-v1.prg'
    log, memory, later, reached = play(build, labels, program, 'restored', ENTRY)
    if not reached:
        raise ValueError('VICE did not reach the main game loop')
    if memory[labels['TITLE']] != 0 or memory[labels['LIVES']] != 5 or memory[labels['DEAD']] != 0:
        raise ValueError('Gameplay state is not TITLE=0 / LIVES=5 / DEAD=0')
    if later[labels['TITLE']] != 0 or not 0 < later[labels['LIVES']] <= 5:
        raise ValueError('Main loop did not continue in gameplay')

    # The packed reference has BASIC SYS 4109 ($100D). Stop at the game's entry
    # before initialization so the comparison excludes mutable gameplay state.
    reference_dump = build / 'reference-memory.bin'
    reference_dump.unlink(missing_ok=True)
    log = run_monitor(build, 'reference',
        f'load "{REFERENCE}" 0\nbreak {ENTRY:x}\ng 100d\n'
        f'bsave "{reference_dump}" 0 {LOAD:04x} {TOP - 1:04x}\nquit\n')
    if stops(log) != [ENTRY]:
        raise ValueError('Packed reference did not reach $1800')
    reference = reference_dump.read_bytes()
    restored = program.read_bytes()[2:]
    if len(reference) != len(restored):
        raise ValueError('Unexpected decompressed reference size')
    reference_prg = build / 'reference-unpacked.prg'
    reference_prg.write_bytes(LOAD.to_bytes(2, 'little') + reference)
    _, ref_play, ref_later, ref_reached = play(build, labels, reference_prg, 'reference-run', ENTRY)

    sources, _, _ = prepare_sources(build / 'reference-inputs')
    obj = mos_hex(sources['OBJ'])
    code_differences = [a for a in obj if restored[a - LOAD] != reference[a - LOAD]]
    differences = [a + LOAD for a, (x, y) in enumerate(zip(restored, reference)) if x != y]
    regions = {}
    for address in differences:
        regions.setdefault(classify(address), []).append(address)
    summary = {name: {'bytes': len(found), 'first': f'${found[0]:04X}', 'last': f'${found[-1]:04X}'}
               for name, found in regions.items()}
    report = {
        'emulator': 'VICE xplus4', 'model': 'c16pal', 'ram_kib': 16, 'sound': 'off', 'warp': True,
        'rendering_filter': 'none (-TEDfilter 0), VICE internal palette',
        'title_rendered': True, 'title_passes_before_input': TITLE_PASSES,
        'main_loop_passes_before_capture': LOOP_PASSES,
        'gameplay_loop_reached': reached, 'title_flag': memory[labels['TITLE']],
        'lives': memory[labels['LIVES']], 'sheet': memory[labels['SHEET']], 'level': memory[labels['LEVEL']],
        'after_main_loop_passes': {'lives': later[labels['LIVES']], 'dead': later[labels['DEAD']],
                                   'aliens_hit': later[labels['ALIHIT']], 'fuel': later[labels['FUEL']],
                                   'score': ''.join(str(d) for d in later[labels['SCRBUF']:labels['SCRBUF'] + 8])},
        'input': 'scripted JFIRE=$80 at the original TITTER BIT test, cleared at the first LOOP; '
                 'no keyboard or joystick input; no instruction patches',
        'manual_keyboard_joystick_sound_and_full_playthrough': 'not verified',
        'reference_sha256': digest(REFERENCE.read_bytes()),
        'reference_compared_at': '$1800 before the first game instruction',
        'compared_with_reference': 'game v1 (development); see game_v2_vs_running_version for v2',
        'reference_unpacked_sha256': digest(reference),
        'reference_reached_gameplay_loop': ref_reached,
        'reference_lives': ref_play[labels['LIVES']],
        'reference_after_main_loop_passes_lives': ref_later[labels['LIVES']],
        'object_listing_bytes_compared': len(obj),
        'initialized_code_differences': len(code_differences),
        'total_memory_differences': len(differences),
        'differences_by_region': summary,
        'alien_pages_in_reference': alien_shift(restored, reference),
        'byte_identical_to_running_version': not differences,
    }
    # Game v2 (cassette release) must equal the decompressed running version
    # everywhere except loader residue and the assembler's leftover text.
    v2 = (build / 'xargons-revenge-v2.prg').read_bytes()[2:]
    v2_differences = [a + LOAD for a, (x, y) in enumerate(zip(v2, reference)) if x != y]
    v2_regions = {}
    for address in v2_differences:
        v2_regions.setdefault(classify(address), []).append(address)
    if set(v2_regions) - {'colour/screen RAM work area', 'padding below the font'}:
        raise ValueError(f'Game v2 differs from the running version in {sorted(v2_regions)}')
    _, v2_play, v2_later, v2_reached = play(build, labels, build / 'xargons-revenge-v2.prg', 'restored-v2', ENTRY)
    report['game_v2_vs_running_version'] = {
        'differences_by_region': {name: {'bytes': len(found), 'first': f'${found[0]:04X}',
                                         'last': f'${found[-1]:04X}'} for name, found in v2_regions.items()},
        'identical_regions': ['$0400-$07FF aliens', '$1000-$17FF landscape', '$1800-$379D code',
                              '$3800-$3FFF font'],
        'gameplay_loop_reached': v2_reached, 'lives': v2_play[labels['LIVES']],
        'after_main_loop_passes_lives': v2_later[labels['LIVES']]}
    report['release_tape_loader'] = tape_loader(build, reference)
    report['loading_screen_files'] = loading_screen(build)
    try:
        measured = palette(build)
        report['ted_palette_measured'] = len({tuple(c) for c in measured['rgb']})
    except ImportError:
        report['ted_palette_measured'] = 'skipped: Pillow not installed'
    (build / 'vice-verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path, default=ROOT / 'build')
    verify(parser.parse_args().build_dir)
