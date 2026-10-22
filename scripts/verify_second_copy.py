#!/usr/bin/env python3
"""Verify the second 2026 copy of the three development disks.

Reads `Original Source Recovered/2026 - 2nd Copy/` without modifying it:
sector copies made with OpenCBM d64copy (with error maps), CBMXfer exports,
and the matching 1992 PC exports (DISK8, DISK9, DISK10). Writes
docs/verification/second-copy.json and, for the damaged 5 Lives disk, a
merged sector image in build/second-copy/ for analysis only.

The checks are evidence for docs/DEVELOPMENT_DISKS.md: what each physical
disk holds, how it relates to the first 2026 images, to the 1992 exports and
to the copies on Plus/4 World, and in what order the builds were made.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from restore_c16 import cbm_lines, mos_hex, pc_lines, tool  # noqa: E402

INPUTS = ROOT / 'Original Source Recovered'
SECOND = INPUTS / '2026 - 2nd Copy'
XR = SECOND / "Xargon's Revenge"
ROX = SECOND / 'Revenge of Xargon (Xargon II)'
FIVE = SECOND / 'Xargons Revenge - 5 Lives'
XR_IMAGE = XR / "2026/Xargon's Revenge - d64Copy.d64"
ROX_IMAGE = ROX / '2026/Revenge of Xargon (Xargon Wars II) - d64Copy.d64'
FIVE_READS = [FIVE / '2026/Xargons Revenge - 5 Lives - d64copy - Errors.d64',
              FIVE / '2026/Xargons Revenge - 5 Lives - d64copy - Errors - 2nd Try.d64']
from restore_c16 import IMAGE as FIRST_IMAGE, SCREEN_IMAGE as FIRST_FIVE  # noqa: E402
FIRST_1992 = INPUTS / '1992/DISK9'
EARLY = ROOT / 'Other Versions/xargons_revenge_early_stages_g1800.prg'
V1 = ROOT / 'build/xargons-revenge-v1.prg'
OUTPUT = ROOT / 'docs/verification/second-copy.json'
MERGED = ROOT / 'build/second-copy/five-lives-merged.d64'

SECTORS = (0,) + (21,) * 17 + (19,) * 7 + (18,) * 6 + (17,) * 5
TYPES = {0: 'DEL', 1: 'SEQ', 2: 'PRG', 3: 'USR', 4: 'REL'}
# Modules the build takes from the 1992 export because the first 2026 image lacks them.
FALLBACK_SIX = ['ALI-PRINT&CLEAR', 'COMPLETED-SHEET', 'DATA-LAND/CHARS',
                'FIRING-MEGA/CODE', 'RASTER-ROUTINES', 'WHOOPPEE-MESSAGE']
DISK10_NAMES = {'LOADER': 'LOADER.BIN', 'P1/$0C00-$1000': 'P10C0010.BIN', 'P2/$0800-$0C00': 'P208000C.BIN',
                'P3/$1000-$4000': 'P3100040.BIN', 'P4/$0400-$0800': 'P4040008.BIN', 'S3': 'S3.BIN',
                'XARGON WARS-1C80': 'XARGONWA.BIN'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def rel(path):
    return path.relative_to(ROOT).as_posix()


def ts(t, s):
    return f'{t}/{s}'


class Disk:
    """D64 reader that tolerates error maps and broken chains (never raises)."""

    def __init__(self, data):
        self.data = data
        self.errors = data[174848:] if len(data) == 175531 else bytes([1]) * 683

    @staticmethod
    def index(t, s):
        return sum(SECTORS[:t]) + s

    def code(self, t, s):
        return self.errors[self.index(t, s)]

    def readable(self, t, s):
        # d64copy writes 1 for a good read and 0 for sectors it skipped (free, unread).
        return self.code(t, s) in (0, 1)

    def sector(self, t, s):
        i = self.index(t, s)
        return self.data[i * 256:i * 256 + 256]

    def all_sectors(self):
        return [(t, s) for t in range(1, 36) for s in range(SECTORS[t])]

    def allocated(self, t, s):
        bam = self.sector(18, 0)
        return not (bam[4 * t + 1 + s // 8] >> (s % 8)) & 1

    def header(self):
        b = self.sector(18, 0)
        return {'name': b[0x90:0xA0].rstrip(b'\xa0').decode('latin-1'), 'id': b[0xA2:0xA4].decode('latin-1')}

    def entries(self):
        out, t, s, seen = [], 18, 1, set()
        while t and (t, s) not in seen and 1 <= t <= 35 and s < SECTORS[t]:
            seen.add((t, s))
            b = self.sector(t, s)
            for o in range(0, 256, 32):
                e = b[o:o + 32]
                if e[2] == 0 and not any(e[3:]):
                    continue
                out.append({'name': e[5:21].rstrip(b'\xa0').decode('latin-1'), 'type': TYPES.get(e[2] & 7, '?'),
                            'closed': bool(e[2] & 0x80), 'start': (e[3], e[4]), 'blocks': e[30] | e[31] << 8})
            t, s = b[0], b[1]
        return out

    def chain(self, start):
        t, s = start
        data, used, bad, seen = bytearray(), [], [], set()
        while t:
            if not (1 <= t <= 35 and s < SECTORS[t]) or (t, s) in seen:
                return bytes(data), used, bad, f'broken link {ts(t, s)}'
            seen.add((t, s))
            used.append((t, s))
            if not self.readable(t, s):
                bad.append(ts(t, s))
            b = self.sector(t, s)
            data += b[2:] if b[0] else b[2:1 + b[1]]
            t, s = b[0], b[1]
        return bytes(data), used, bad, None

    def files(self):
        return {e['name']: self.chain(e['start'])[0] for e in self.entries() if e['type'] != 'DEL'}


def folder(path):
    return {p.name: p.read_bytes() for p in sorted(path.iterdir()) if p.is_file() and p.name != '.DS_Store'}


def index_1992(files):
    return re.findall(r'^\d+\s+"([^"]+)"\s+(SEQ|PRG)\s+(\S+)\s+(TXT|BIN|BAS)\b',
                      files['INDEX'].decode('latin-1'), re.MULTILINE)


def basic_listing(data, scratch):
    """Detokenize C16 BASIC 3.5 with VICE petcat; None if petcat is missing."""
    try:
        petcat = tool('petcat')
    except FileNotFoundError:
        return None
    scratch.write_bytes(data)
    text = subprocess.run([petcat, '-3', '--', str(scratch)], capture_output=True).stdout.decode('latin-1')
    return [re.sub(r'\s+', '', line.lower()) for line in text.split('\n') if line.strip() and not line.startswith(';')]


def compare_1992(disk_files, pc_files, scratch):
    """Compare every INDEX entry: SEQ as normalized text, BIN as bytes, BAS detokenized."""
    result = {'entries': 0, 'identical': [], 'differ': {}, 'missing_on_disk': []}
    for name, _, stem, ext in index_1992(pc_files):
        result['entries'] += 1
        if name not in disk_files:
            result['missing_on_disk'].append(name)
            continue
        ours, theirs = disk_files[name], pc_files[f'{stem}.{ext}']
        if ext == 'TXT':
            a, b = cbm_lines(ours), pc_lines(theirs)
            lines = [n + 1 for n, (x, y) in enumerate(zip(a, b)) if x != y]
            same = not lines and len(a) == len(b)
            detail = {'lines': lines, 'disk': [a[n - 1] for n in lines], 'export_1992': [b[n - 1] for n in lines]}
        elif ext == 'BIN':
            same = ours == theirs
            detail = {'bytes_differing': sum(x != y for x, y in zip(ours, theirs)), 'disk_sha256': digest(ours),
                      'export_1992_sha256': digest(theirs)}
        else:
            listing = basic_listing(ours, scratch)
            if listing is None:
                result['differ'][name] = {'note': 'petcat not installed; BASIC not compared'}
                continue
            export = [re.sub(r'\s+', '', line.lower()) for line in theirs.decode('latin-1').split('\r\n')
                      if line.strip() and not line.startswith('64000 REM')]
            diffs = [(x, y) for x, y in zip(listing, export) if x != y]
            # The 1992 listing exporter drops PETSCII control codes inside strings.
            control_only = all(re.sub(r'\{[^}]*\}', '', x) == y for x, y in diffs)
            same = len(listing) == len(export) and (not diffs or control_only)
            detail = {'lines_differing': len(diffs), 'control_codes_only': control_only}
            if same and diffs:
                result.setdefault('basic_control_codes_dropped_in_1992', []).append(name)
        if same:
            result['identical'].append(name)
        else:
            result['differ'][name] = detail
    return result


def deleted_entries(disk):
    out = []
    for e in disk.entries():
        if e['type'] == 'DEL':
            data, used, bad, problem = disk.chain(e['start'])
            out.append({'name': e['name'], 'directory_blocks': e['blocks'], 'chain_sectors': len(used),
                        'recoverable': len(used) == e['blocks'] and not problem})
    return out


def mos_records(text):
    """Valid MOS hex records anywhere in a text fragment (checksums verified)."""
    for match in re.finditer(r';([0-9A-F]{10,})', text):
        hexits = match.group(1)
        raw = bytes.fromhex(hexits[:len(hexits) // 2 * 2])
        count = raw[0]
        if count and len(raw) >= count + 5 and sum(raw[:count + 3]) == int.from_bytes(raw[count + 3:count + 5], 'big'):
            yield int.from_bytes(raw[1:3], 'big'), raw[3:3 + count]


def free_remnants(disk, builds):
    """Old OBJ listings left in free sectors: decode and match against known builds."""
    free = [p for p in disk.all_sectors() if p[0] != 18 and not disk.allocated(*p)]
    records = [r for p in free for r in mos_records(disk.sector(*p)[2:].decode('latin-1'))]
    matches = Counter()
    for address, data in records:
        hits = [name for name, memory in builds.items() if memory[address:address + len(data)] == data]
        matches[hits[0] if hits else 'none at the same address'] += 1
    span = (min(a for a, _ in records), max(a + len(d) for a, d in records)) if records else None
    return {'free_sectors': len(free), 'free_sectors_with_data': sum(any(disk.sector(*p)) for p in free),
            'mos_hex_records': len(records), 'bytes': sum(len(d) for _, d in records),
            'span': f'${span[0]:04X}-${span[1] - 1:04X}' if span else None, 'matches': dict(matches)}


def lives(files):
    text = cbm_lines(files['PLAY-GAME'])
    for n, line in enumerate(text):
        if re.match(r'\s*STA LIVES', line):
            return int(re.search(r'#(\d+)', text[n - 1]).group(1))
    return None


def readable_disk(image, pc_folder, cbmxfer_folder, scratch, builds):
    disk = Disk(image.read_bytes())
    files = disk.files()
    folder_files = folder(cbmxfer_folder)
    in_folder = {data for data in folder_files.values()}
    dropped = [n for n, d in files.items() if d not in in_folder]
    return disk, files, {
        'image': rel(image), 'sha256': digest(image.read_bytes()), 'header': disk.header(),
        'error_codes': dict(Counter(disk.errors)), 'live_files': len(files),
        'deleted_entries': deleted_entries(disk),
        'cbmxfer_folder': {'path': rel(cbmxfer_folder), 'files': len(folder_files),
                           'all_identical_to_sector_copy': all(d in files.values() for d in folder_files.values()),
                           'dropped': dropped,
                           'dropped_rule': 'names of 15-16 characters, or containing "/"'},
        'vs_1992': compare_1992(files, folder(pc_folder), scratch),
        'free_sector_remnants': free_remnants(disk, builds),
        'starting_lives': lives(files),
    }


def five_lives(pc_folder, merged_path):
    reads = [Disk(p.read_bytes()) for p in FIVE_READS]
    merged, emap, unreadable, unstable = bytearray(174848), bytearray(683), [], []
    for t, s in reads[0].all_sectors():
        i = Disk.index(t, s)
        good = [r for r in reads if r.code(t, s) == 1]
        if len(good) == 2 and good[0].sector(t, s) != good[1].sector(t, s):
            unstable.append(ts(t, s))
        source = good[0] if good else reads[0]
        merged[i * 256:i * 256 + 256] = source.sector(t, s)
        emap[i] = 1 if good else (reads[0].code(t, s) or reads[1].code(t, s))
        if not good and reads[0].allocated(t, s) and reads[0].code(t, s) != 0:
            unreadable.append(ts(t, s))
    merged_path.parent.mkdir(parents=True, exist_ok=True)
    merged_path.write_bytes(bytes(merged) + bytes(emap))
    disk = Disk(bytes(merged) + bytes(emap))
    pc = folder(pc_folder)
    expected = {name: pc[f] for name, f in DISK10_NAMES.items()}

    def block(name, n):
        return expected[name][n * 254:n * 254 + 254]

    # Place each readable sector: by unique content match, then along its links.
    place = {}
    for t, s in disk.all_sectors():
        if disk.code(t, s) != 1 or not disk.allocated(t, s) or t == 18:
            continue
        sec = disk.sector(t, s)
        hits = [(name, n) for name, data in expected.items() for n in range((len(data) + 253) // 254)
                if sec[2:2 + len(block(name, n))] == block(name, n)]
        if len(hits) == 1:
            place[(t, s)] = hits[0]
    for e in disk.entries():
        place.setdefault(e['start'], (e['name'], 0))
    grown = True
    while grown:
        grown = False
        for (t, s), (name, n) in list(place.items()):
            if disk.code(t, s) == 1:
                b = disk.sector(t, s)
                if b[0] and (b[0], b[1]) not in place:
                    place[(b[0], b[1])] = (name, n + 1)
                    grown = True
    per_file = {name: {'blocks_1992': (len(data) + 253) // 254, 'verified': 0, 'unreadable': 0, 'decayed': []}
                for name, data in expected.items()}
    unplaced = []
    for (t, s), (name, n) in place.items():
        if name not in expected or n >= per_file[name]['blocks_1992']:
            continue
        if disk.code(t, s) != 1:
            per_file[name]['unreadable'] += 1
            continue
        want = block(name, n)
        got = disk.sector(t, s)[2:2 + len(want)]
        if got == want:
            per_file[name]['verified'] += 1
        else:
            first = next(i for i, (x, y) in enumerate(zip(got, want)) if x != y)
            per_file[name]['decayed'].append({'sector': ts(t, s), 'block': n + 1,
                                              'bytes_differing': sum(x != y for x, y in zip(got, want)),
                                              'matches_up_to_byte': first})
    for t, s in disk.all_sectors():
        if disk.code(t, s) == 1 and disk.allocated(t, s) and t != 18 and (t, s) not in place:
            unplaced.append(ts(t, s))
    first_five = Disk(FIRST_FIVE.read_bytes()).files()
    return {
        'reads': [{'image': rel(p), 'sha256': digest(p.read_bytes()), 'error_codes': dict(Counter(r.errors))}
                  for p, r in zip(FIVE_READS, reads)],
        'merged_image': merged_path.name, 'header': disk.header(),
        'directory': [{'name': e['name'], 'type': e['type'], 'blocks': e['blocks']} for e in disk.entries()],
        'allocated_sectors_unreadable_in_both_reads': unreadable,
        'sectors_read_differently_with_good_status': unstable,
        'per_file_vs_1992_disk10': per_file, 'readable_sectors_not_placed': unplaced,
        'disk10_1992_files': {f: digest(d) for f, d in pc.items()},
        'first_2026_partial_copy_matches_disk10': {name: first_five.get(name) == expected[name]
                                            for name in ('LOADER', 'P1/$0C00-$1000', 'P2/$0800-$0C00')},
    }


def verify(work=MERGED.parent, v1=V1):
    """Run every check; scratch files and the merged 5 Lives image go in `work`."""
    work.mkdir(parents=True, exist_ok=True)
    scratch = work / 'basic.prg'

    release = bytearray(0x10000)
    v1 = v1.read_bytes()
    release[0x0400:0x0400 + len(v1) - 2] = v1[2:]
    five_p3 = bytearray(0x10000)
    p3 = (FIVE / '1992 - Disk 10/P3100040.BIN').read_bytes()
    five_p3[0x1000:0x1000 + len(p3) - 2] = p3[2:]
    builds = {'release OBJ (DISK9)': bytes(release), '5 Lives P3 (DISK10)': bytes(five_p3)}

    cbmxfer_images = sorted(SECOND.glob('*/2026/*CBMXfer*.d64'))
    first = Disk(FIRST_IMAGE.read_bytes())
    report = {
        'note': 'Generated by scripts/verify_second_copy.py. Inputs are read only.',
        'inputs': {rel(p): {'bytes': p.stat().st_size, 'sha256': digest(p.read_bytes())}
                   for p in sorted(SECOND.rglob('*')) if p.is_file() and p.name != '.DS_Store'},
        'cbmxfer_images': {'files': [rel(p) for p in cbmxfer_images],
                           'identical': len({digest(p.read_bytes()) for p in cbmxfer_images}) == 1,
                           'header': Disk(cbmxfer_images[0].read_bytes()).header(),
                           'live_files': len(Disk(cbmxfer_images[0].read_bytes()).files())},
        'first_2026_image': {'image': rel(FIRST_IMAGE), 'header': first.header(),
                             'live_files': len(first.files())},
    }

    xr_disk, xr_files, report['xargons_revenge'] = readable_disk(
        XR_IMAGE, XR / '1992 - Disk 9', XR / "2026/Xargon's Revenge - Memorex - CBMXfer", scratch, builds)
    first_files = first.files()
    report['xargons_revenge']['vs_first_2026_image'] = {
        'identical': sorted(n for n in first_files if xr_files.get(n) == first_files[n]),
        'differing': sorted(n for n in first_files if n in xr_files and xr_files[n] != first_files[n]),
        'only_on_sector_copy': sorted(set(xr_files) - set(first_files)),
        'only_on_first_image': sorted(set(first_files) - set(xr_files))}
    pc9 = folder(FIRST_1992)
    index9 = {name: pc9[f'{stem}.{ext}'] for name, _, stem, ext in index_1992(pc9)}
    report['xargons_revenge']['fallback_six_vs_1992'] = {
        name: cbm_lines(xr_files[name]) == pc_lines(index9[name]) for name in FALLBACK_SIX}
    report['xargons_revenge']['second_1992_copy_identical_to_project_DISK9'] = folder(XR / '1992 - Disk 9') == pc9

    rox_disk, rox_files, report['revenge_of_xargon'] = readable_disk(
        ROX_IMAGE, ROX / '1992 - Disk 8', ROX / '2026/Revenge of Xargon (Xargon Wars II) - CBMXfer', scratch, builds)
    obj = mos_hex(cbm_lines(rox_files['OBJ']))
    early = EARLY.read_bytes()
    early_mem = bytearray(0x10000)
    early_mem[0x1000:0x1000 + len(early) - 2] = early[2:]
    frak = rox_files['FRAK!'][2:]
    land1 = xr_files['LANDSCAPE-1'][2:]
    pc8 = folder(ROX / '1992 - Disk 8')
    report['revenge_of_xargon']['obj'] = {
        'range': f'${min(obj):04X}-${max(obj):04X}', 'bytes': len(obj),
        'equals_plus4world_early_stages_code': all(early_mem[a] == b for a, b in obj.items())}
    report['revenge_of_xargon']['early_stages_composition'] = {
        'font_$3800_equals_this_disk_FRAK!': bytes(early_mem[0x3800:0x4000]) == frak,
        'landscape_$1000_equals_LANDSCAPE-1': bytes(early_mem[0x1000:0x1800]) == land1,
        # Only $00/$FF in blocks: the emulator's power-on RAM fill, saved along with the code.
        'after_code_only_00_and_FF': set(early_mem[0x2C6E:0x3800]) <= {0x00, 0xFF},
        'shared_files_with_xargons_revenge_disk': sum(rox_files[n] == xr_files.get(n) for n in rox_files),
        'differing_from_xargons_revenge_disk': sorted(n for n in rox_files if n in xr_files and rox_files[n] != xr_files[n]),
        'only_on_this_disk': sorted(set(rox_files) - set(xr_files))}
    report['revenge_of_xargon']['1992_DISK8_landscape_exports'] = {
        'LANDSCA1_equals_LANDSCA2': pc8['LANDSCA1.BIN'] == pc8['LANDSCA2.BIN'],
        'disk_LANDSCAPE-2_equals_release_LANDSCAPE-2': rox_files['LANDSCAPE-2'] == xr_files['LANDSCAPE-2']}

    report['five_lives'] = five_lives(FIVE / '1992 - Disk 10', work / MERGED.name)
    return report


def main():
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()
    report = verify()
    OUTPUT.write_text(json.dumps(report, indent=2) + '\n')
    x, r, f = report['xargons_revenge'], report['revenge_of_xargon'], report['five_lives']
    print(f"Wrote {rel(OUTPUT)}")
    print(f"Xargon's Revenge: {x['live_files']} files, six fallback modules on disk and identical to 1992: "
          f"{all(x['fallback_six_vs_1992'].values())}; CBMXfer dropped {x['cbmxfer_folder']['dropped']}")
    print(f"Revenge of Xargon: {r['live_files']} files, OBJ {r['obj']['range']} = early stages: "
          f"{r['obj']['equals_plus4world_early_stages_code']}; lives {r['starting_lives']}")
    print(f"5 Lives: {len(f['allocated_sectors_unreadable_in_both_reads'])} unreadable sectors; "
          + ', '.join(f"{k} {v['verified']}/{v['blocks_1992']}" for k, v in f['per_file_vs_1992_disk10'].items()))


if __name__ == '__main__':
    main()
