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
from verify_vice import labels_of, run_monitor

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
    source = build / 'xargons-revenge.prg'
    reference = build / 'reference-unpacked.prg'
    if not reference.is_file():
        raise ValueError('Run verify_vice.py before probing the running version')

    def call(name, program, symbol, accumulator, fields):
        capture = output / (name + '.bin')
        capture.unlink(missing_ok=True)
        commands = f'load "{program}" 0\n'
        for address, values in fields:
            commands += poke(address, values)
        commands += poke(CALLER, caller(labels[symbol], accumulator))
        commands += f'break {stop:x}\ng {CALLER:x}\nbsave "{capture}" 0 0000 3fff\nquit\n'
        log = run_monitor(output, name, commands)
        if f'c:${stop:04x}' not in log.lower():
            raise ValueError(f'Probe {name} did not return to its caller')
        return capture.read_bytes()

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

    report = {'method': 'isolated routine calls from a workspace caller at $0BE8; SEI/CLD; '
                        'controlled RAM; original game instructions unchanged',
              'source_prg_sha256': digest(source.read_bytes()),
              'running_unpacked_prg_sha256': digest(reference.read_bytes()),
              'emulator': 'VICE xplus4, PAL C16, 16 KB, sound off',
              'scope': 'four score/extra-life observations and the alien character selection '
                       'for all 16 sheets; not full gameplay, timing, collisions or sound',
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
