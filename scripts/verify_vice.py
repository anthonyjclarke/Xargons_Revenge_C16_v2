#!/usr/bin/env python3
"""Check title, gameplay entry, and the supplied packed game in PAL C16 VICE."""

import argparse
import json
import re
import subprocess
from pathlib import Path

from restore_c16 import (ROOT, REFERENCE, ENTRY, LOAD, TOP, digest, mos_hex,
                         prepare_sources, tool)

TITLE_PASSES = 24   # TITTER passes (about 32 delay units each) before input


def labels_of(build):
    return {name: int(address, 16) for address, name in re.findall(
        r'^al ([0-9A-Fa-f]+) \.(\w+)$', (build / 'revenge.labels').read_text(), re.MULTILINE)}


def run_monitor(build, stem, commands, cycles=200000000):
    """Run VICE headless with audio off, warp and a fixed cycle limit."""
    commands_file = build / (stem + '.mon')
    commands_file.write_text(commands)
    log = build / (stem + '-monitor.log')
    log.unlink(missing_ok=True)
    result = subprocess.run([
        tool('xplus4'), '-default', '+saveres', '-model', 'c16pal', '-ramsize', '16',
        '+sound', '-initbreak', 'ready', '-moncommands', str(commands_file),
        '-logfile', str(build / (stem + '-vice.log')), '-monlog', '-monlogname', str(log),
        '-warp', '-limitcycles', str(cycles),
    ], cwd=str(ROOT), capture_output=True, timeout=120)
    (build / (stem + '-console.log')).write_bytes(result.stdout + result.stderr)
    result.check_returncode()
    return log.read_text()


def play(build, labels, program, stem, entry):
    """Reach the title, inject one fire press at the original BIT test, reach LOOP."""
    for name in (f'{stem}-title.png', f'{stem}-gameplay.png', f'{stem}-memory.bin'):
        (build / name).unlink(missing_ok=True)
    log = run_monitor(build, stem,
        f'load "{program}" 0\n'
        f'break {labels["TITTER"]:x}\nignore 1 {TITLE_PASSES}\ng {entry:x}\n'
        f'screenshot "{build / (stem + "-title.png")}" 2\n'
        f'> {labels["JFIRE"]:x} 80\ndelete 1\n'
        f'break {labels["LOOP"]:x}\nx\n'
        f'> {labels["JFIRE"]:x} 00\ndelete 2\n'
        f'break {labels["LOOP"]:x}\nignore 3 400\nx\n'
        f'screenshot "{build / (stem + "-gameplay.png")}" 2\n'
        f'bsave "{build / (stem + "-memory.bin")}" 0 0000 3fff\nquit\n')
    memory = (build / (stem + '-memory.bin')).read_bytes()
    reached = f'C:${labels["LOOP"]:04x}'.lower() in log.lower()
    for name in (f'{stem}-title.png', f'{stem}-gameplay.png'):
        if not (build / name).read_bytes().startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError(f'Missing VICE screenshot: {name}')
    return log, memory, reached


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
    program = build / 'xargons-revenge.prg'
    log, memory, reached = play(build, labels, program, 'restored', ENTRY)
    if not reached:
        raise ValueError('VICE did not reach the main game loop')
    if memory[labels['TITLE']] != 0 or memory[labels['LIVES']] != 5 or memory[labels['DEAD']] != 0:
        raise ValueError('Gameplay state is not TITLE=0 / LIVES=5 / DEAD=0')

    # The packed reference has BASIC SYS 4109 ($100D). Stop at the game's entry
    # before initialization so the comparison excludes mutable gameplay state.
    reference_dump = build / 'reference-memory.bin'
    reference_dump.unlink(missing_ok=True)
    log = run_monitor(build, 'reference',
        f'load "{REFERENCE}" 0\nbreak {ENTRY:x}\ng 100d\n'
        f'bsave "{reference_dump}" 0 {LOAD:04x} {TOP - 1:04x}\nquit\n')
    if f'C:${ENTRY:04x}'.lower() not in log.lower():
        raise ValueError('Packed reference did not reach $1800')
    reference = reference_dump.read_bytes()
    restored = program.read_bytes()[2:]
    if len(reference) != len(restored):
        raise ValueError('Unexpected decompressed reference size')
    reference_prg = build / 'reference-unpacked.prg'
    reference_prg.write_bytes(LOAD.to_bytes(2, 'little') + reference)
    _, ref_play, ref_reached = play(build, labels, reference_prg, 'reference-run', ENTRY)

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
        'title_rendered': True, 'title_passes_before_input': TITLE_PASSES,
        'gameplay_loop_reached': reached, 'title_flag': memory[labels['TITLE']],
        'lives': memory[labels['LIVES']], 'sheet': memory[labels['SHEET']], 'level': memory[labels['LEVEL']],
        'input': 'scripted JFIRE=$80 at the original TITTER BIT test, cleared at LOOP; no instruction patches',
        'manual_keyboard_joystick_sound_and_full_playthrough': 'not verified',
        'reference_sha256': digest(REFERENCE.read_bytes()),
        'reference_compared_at': '$1800 before the first game instruction',
        'reference_unpacked_sha256': digest(reference),
        'reference_reached_gameplay_loop': ref_reached,
        'reference_lives': ref_play[labels['LIVES']],
        'object_listing_bytes_compared': len(obj),
        'initialized_code_differences': len(code_differences),
        'total_memory_differences': len(differences),
        'differences_by_region': summary,
        'alien_pages_in_reference': alien_shift(restored, reference),
        'byte_identical_to_running_version': not differences,
    }
    (build / 'vice-verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path, default=ROOT / 'build')
    verify(parser.parse_args().build_dir)
