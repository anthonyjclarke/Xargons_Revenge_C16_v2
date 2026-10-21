#!/usr/bin/env python3
"""Probe isolated original routines in VICE without modifying game instructions.

A short caller in free workspace ($0BE8, listed as free in EXTRA-MEMORY)
invokes a routine with controlled state. This verifies selected arithmetic and
data-selection behavior, not complete gameplay or timing.
"""

import argparse
import json
from pathlib import Path

from restore_c16 import ROOT, digest
from verify_vice import labels_of, run_monitor, stops

CALLER = 0x0BE8


def caller(address, accumulator=0):
    # SEI; CLD; LDA #value; JSR routine; NOP (the break address).
    return [0x78, 0xD8, 0xA9, accumulator, 0x20, address & 255, address >> 8, 0xEA]


def poke(address, values):
    return f'> {address:x} ' + ' '.join(f'{v:02x}' for v in values) + '\n'


def probe(build):
    build = build.resolve()
    labels = labels_of(build)
    output = build / 'rule-probes'
    output.mkdir(parents=True, exist_ok=True)
    stop = CALLER + 7
    source = build / 'xargons-revenge-v1.prg'
    reference = build / 'reference-unpacked.prg'
    if not reference.is_file():
        raise ValueError('Run verify_vice.py before probing the running version')

    def run_to(name, program, symbol, accumulator, fields, targets):
        """Call a routine and stop at the first of several addresses; report which."""
        capture = output / (name + '.bin')
        capture.unlink(missing_ok=True)
        commands = f'load "{program}" 0\n'
        for address, values in fields:
            commands += poke(address, values)
        commands += poke(CALLER, caller(labels[symbol], accumulator))
        commands += ''.join(f'break {s:x}\n' for s in targets)
        commands += f'g {CALLER:x}\nbsave "{capture}" 0 0000 3fff\nquit\n'
        reached = stops(run_monitor(output, name, commands))
        if len(reached) != 1 or reached[0] not in targets:
            raise ValueError(f'Probe {name} reached {reached}, expected exactly one of {targets}')
        return capture.read_bytes(), reached[0]

    def call(name, program, symbol, accumulator, fields):
        return run_to(name, program, symbol, accumulator, fields, [stop])[0]

    checks = []
    score_cases = [
        ('score-49999-plus-1', [0, 0, 0, 4, 9, 9, 9, 9], 0, 1, '00050000', 4, 5),
        ('score-50000-repeat', [0, 0, 0, 5, 0, 0, 0, 0], 5, 1, '00050001', 3, 5),
        ('score-99999-plus-1', [0, 0, 0, 9, 9, 9, 9, 9], 5, 1, '00100000', 4, 0),
        ('score-149999-plus-1', [0, 0, 1, 4, 9, 9, 9, 9], 0, 1, '00150000', 4, 5),
    ]
    for name, digits, xtra, amount, expected, lives, cached in score_cases:
        mem = call(name, source, 'SCORE', amount,
                   [(labels['SCRBUF'], digits), (labels['XTRA'], [xtra]), (labels['LIVES'], [3])])
        result = {'probe': name, 'version': 'source', 'before': ''.join(map(str, digits)),
                  'xtra_before': xtra, 'lives_before': 3, 'added': amount,
                  'after': ''.join(str(b) for b in mem[labels['SCRBUF']:labels['SCRBUF'] + 8]),
                  'lives_after': mem[labels['LIVES']], 'xtra_after': mem[labels['XTRA']]}
        assert (result['after'], result['lives_after'], result['xtra_after']) == (expected, lives, cached), result
        checks.append(result)

    # ALIDEF copies 64 bytes from ALDATA+(SHEET&15)*64 into characters $3EA8-$3EE7.
    alien_rows = []
    for sheet in range(16):
        row = {'sheet': sheet, 'aldata_offset': f'${sheet * 64:03X}'}
        for version, program in (('source', source), ('running', reference)):
            mem = call(f'alidef-{version}-{sheet:02d}', program, 'ALIDEF', 0,
                       [(labels['SHEET'], [sheet])])
            row[version + '_sha256'] = digest(mem[0x3EA8:0x3EE8])
            row[version + '_bytes'] = mem[0x3EA8:0x3EE8].hex()
        row['identical'] = row['source_bytes'] == row['running_bytes']
        alien_rows.append(row)
    assert [r['identical'] for r in alien_rows] == [True] * 4 + [False] * 12
    checks.append({'probe': 'alien-characters-per-sheet', 'routine': 'ALIDEF',
                   'target': '$3EA8-$3EE7', 'identical_sheets': [r['sheet'] for r in alien_rows if r['identical']],
                   'different_sheets': [r['sheet'] for r in alien_rows if not r['identical']],
                   'rows': alien_rows})

    # COMPLE ends a wave: SHEET wraps at 16 into LEVEL, and LEVCTL runs when
    # SHEET returns to 0. LEVEL 5 jumps to the game-completion screen.
    endings = {labels['STLOOP']: 'next wave (STLOOP)', labels['ENDLVL']: 'completion screen (ENDLVL)'}
    for sheet, level in ((0, 0), (15, 0), (15, 3), (15, 4)):
        mem, reached = run_to(f'complete-level{level}-sheet{sheet:02d}', source, 'COMPLE', 0,
                              [(labels['SHEET'], [sheet]), (labels['LEVEL'], [level]),
                               (labels['FUEL'], [0])], list(endings))
        commes = labels['COMMES']
        checks.append({'probe': 'wave-completion', 'routine': 'COMPLE', 'sheet_before': sheet,
                       'level_before': level, 'sheet_after': mem[labels['SHEET']],
                       'level_after': mem[labels['LEVEL']], 'attak_after': mem[labels['ATTAK']],
                       'message': mem[commes:commes + 24].decode('ascii'), 'reached': endings[reached]})
    completion = [c for c in checks if c['probe'] == 'wave-completion']
    assert [c['reached'] for c in completion] == [endings[labels['STLOOP']]] * 3 + [endings[labels['ENDLVL']]]
    assert [c['attak_after'] for c in completion] == [1, 16, 64, 80]

    # SETIRQ points the RAM copies of the NMI and RESET vectors at RESET ($1FDB,
    # "THAT WAS A VERY SILLY THING TO DO"). Reset during play and see where
    # execution resumes: the trap, or the ROM reset routine at $F2A4.
    for mode, kind in ((0, 'soft'), (1, 'hard')):
        name = f'reset-{kind}'
        commands = (f'load "{source}" 0\nbreak {labels["TITTER"]:x}\ng 1800\n'
                    f'> {labels["JFIRE"]:x} 80\ndelete 1\nbreak {labels["LOOP"]:x}\nx\n'
                    f'> {labels["JFIRE"]:x} 00\ndelete 1\n'
                    f'bsave "{output / (name + "-vectors.bin")}" 0 fffa ffff\n'
                    f'break {labels["RESET"]:x}\nbreak f2a4\nreset {mode}\nx\nquit\n')
        # A machine reset ends VICE's command playback, so the closing quit is
        # not run and VICE exits at its cycle limit; the stop list is the evidence.
        hits = stops(run_monitor(output, name, commands, cycles=60000000, check=False))
        vectors = (output / (name + '-vectors.bin')).read_bytes()
        assert hits[:2] == [labels['TITTER'], labels['LOOP']] and len(hits) == 3, hits
        checks.append({'probe': 'reset-during-play', 'reset': f'VICE monitor "reset {mode}" ({kind})',
                       'ram_vectors_before': {'nmi': f'${int.from_bytes(vectors[0:2], "little"):04X}',
                                              'reset': f'${int.from_bytes(vectors[2:4], "little"):04X}'},
                       'resumed_at': f'${hits[2]:04X}',
                       'reached_trap': hits[2] == labels['RESET']})

    report = {'method': 'isolated routine calls from a workspace caller at $0BE8; SEI/CLD; '
                        'controlled RAM; original game instructions unchanged',
              'source_prg_sha256': digest(source.read_bytes()),
              'running_unpacked_prg_sha256': digest(reference.read_bytes()),
              'emulator': 'VICE xplus4, PAL C16, 16 KB, sound off',
              'scope': 'four score/extra-life observations, the alien character selection for all '
                       '16 sheets, four wave-completion transitions and two resets during play; '
                       'not full gameplay, timing, collisions or sound',
              'checks': checks}
    (output / 'rule-probes.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'checks'}, indent=2))
    for check in checks:
        print(check['probe'], {k: v for k, v in check.items() if k not in ('rows', 'probe')})
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path, default=ROOT / 'build')
    probe(parser.parse_args().build_dir)
