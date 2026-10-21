#!/usr/bin/env python3
"""Assemble Xargon's Revenge from preserved sources, recording every dependency."""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

from d64_image import D64Image
from source_converter import convert, flatten

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / 'Original Source Recovered'
IMAGE = INPUTS / "2026/Xargon'sRevenge-C16.d64"
EXTRACTED = INPUTS / '2026/Xargons-Revenge-C16-Side2'
SCREEN_IMAGE = INPUTS / '2026/XargonsRevenge-C16.d64'
SCREEN_EXTRACTED = INPUTS / '2026/Xargons-Revenge-C16-Side1'
OLDER = INPUTS / '1992/DISK9'
ARCHIVE = INPUTS / "1992/DISK9 - Xargon's Revenge.ZIP"
REFERENCE = ROOT / 'xargons_revenge.prg'
MAIN = 'REVENGE'
LOAD, ENTRY = 0x0400, 0x1800
# Two playable game versions share every assembled byte except ALDATA:
#   v1 development: BJH copied whole to $0400, as LOADER on the source disk does.
#   v2 cassette release: the release tape loader's copy loop advances the low
#   byte of its source address, so page p of $0400 holds BJH[p : p+256].
GAME_VERSIONS = {1: 'development', 2: 'cassette release'}
# The dev boot (C16 -> LOADER) puts BJH at ALDATA, LANDSCAPE-2 at $1000 and
# FRAK! at $3800 around the OBJ code; these are the matching fixed origins.
ALIEN_BASE, LAND_BASE, FONT_BASE, TOP = 0x0400, 0x1000, 0x3800, 0x4000
HOST_METADATA = {'.DS_Store'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def rel(path):
    return path.relative_to(ROOT).as_posix()


def tool(name):
    found = shutil.which(name)
    if found:
        return found
    for directory in ('/opt/homebrew/bin', '/usr/local/bin'):
        candidate = Path(directory) / name
        if candidate.is_file():
            return str(candidate)
    raise FileNotFoundError(f'{name} not found; install the cc65/VICE tools described in README.md')


def cbm_lines(data):
    """Disk SEQ text is CR-separated ASCII with rare PETSCII bytes in comments.

    Latin-1 keeps every byte; split only on CR because str.splitlines() would
    also break on bytes such as $85 and $1C-$1E.
    """
    return data.decode('latin-1').split('\r')


def pc_lines(data):
    """1992 exports are lower-case ASCII with CRLF; restore upper-case CBM text."""
    text = data.decode('ascii')
    if re.search('[A-Z]', text):
        raise ValueError('1992 export contains upper-case text; case folding would be lossy')
    return text.upper().replace('\r\n', '\r').split('\r')


def verify_extraction(image, folder):
    """Check every live disk file against the preserved 2026 extraction."""
    files = D64Image(image).files()
    manifest = json.loads((folder / 'manifest.json').read_text())
    if manifest['source_sha256'] != digest(image.read_bytes()):
        raise ValueError(f'{image.name} does not match its extraction manifest')
    extracted = {bytes.fromhex(f['petscii_name_hex']).rstrip(b'\xa0').decode('ascii'): f
                 for f in manifest['files']}
    if len(extracted) != len(files):
        raise ValueError(f'{image.name}: disk and extraction file counts differ')
    for file in files:
        record = extracted.get(file.name)
        if record is None or file.data != (folder / record['output']).read_bytes():
            raise ValueError(f'Disk and preserved 2026 extraction differ: {file.name}')
        if digest(file.data) != record['sha256']:
            raise ValueError(f'Extraction hash mismatch: {file.name}')
    return files, extracted


def compare_archive():
    """The 1992 ZIP and the extracted DISK9 folder must hold identical bytes.

    The 1992 archive uses PKZIP 1.x Implode and Shrink, which Python's zipfile
    cannot expand. Info-ZIP unzip expands them for a byte comparison; without
    it, only the stored CRC-32 and length are checked, and the report says so.
    """
    unzip = shutil.which('unzip')
    with zipfile.ZipFile(ARCHIVE) as archive:
        infos = {Path(i.filename).name: i for i in archive.infolist()
                 if not i.is_dir() and Path(i.filename).name not in HOST_METADATA}
    folder = {p.name: p.read_bytes() for p in OLDER.iterdir()
              if p.is_file() and p.name not in HOST_METADATA}
    differing = []
    for name in sorted(infos.keys() & folder.keys()):
        info, data = infos[name], folder[name]
        if zipfile.crc32(data) != info.CRC or len(data) != info.file_size:
            differing.append(name)
        elif unzip:
            expanded = subprocess.run([unzip, '-p', str(ARCHIVE), info.filename],
                                      check=True, capture_output=True).stdout
            if expanded != data:
                differing.append(name)
    members = infos
    report = {'archive': rel(ARCHIVE), 'archive_sha256': digest(ARCHIVE.read_bytes()),
              'method': 'byte comparison via unzip -p' if unzip else 'CRC-32 and length only',
              'compression': sorted({zipfile.compressor_names.get(i.compress_type, str(i.compress_type))
                                     for i in infos.values()}),
              'members': len(members), 'folder_files': len(folder),
              'only_in_archive': sorted(members.keys() - folder.keys()),
              'only_in_folder': sorted(folder.keys() - members.keys()),
              'differing': differing, 'excluded_host_metadata': sorted(HOST_METADATA)}
    report['identical'] = not (report['only_in_archive'] or report['only_in_folder'] or differing)
    if not report['identical']:
        raise ValueError(f'1992 ZIP and DISK9 folder differ: {report}')
    return report


def older_index():
    """INDEX maps each original CBM name to its truncated 8.3 PC export."""
    entries = {}
    for name, kind, stem, ext in re.findall(
            r'^\d+\s+"([^"]+)"\s+(SEQ|PRG)\s+(\S+)\s+(TXT|BIN|BAS)\b',
            (OLDER / 'INDEX').read_text(), re.MULTILINE):
        path = OLDER / f'{stem}.{ext}'
        if not path.is_file():
            raise ValueError(f'INDEX refers to missing file: {path.name}')
        if name in entries:
            raise ValueError(f'Duplicate INDEX name: {name}')
        entries[name] = (kind, path)
    return entries


def prepare_sources(build):
    """Prefer fresh disk bytes; INDEX supplies only modules absent from the disk."""
    build.mkdir(parents=True, exist_ok=True)
    files, extracted = verify_extraction(IMAGE, EXTRACTED)
    screen_files, _ = verify_extraction(SCREEN_IMAGE, SCREEN_EXTRACTED)
    archive = compare_archive()
    index = older_index()
    sources, binaries, provenance, older_comparison = {}, {}, [], []
    for file in files:
        record = extracted[file.name]
        provenance.append({'name': file.name, 'kind': file.kind, 'source': rel(IMAGE),
                           'sha256': digest(file.data), 'bytes': len(file.data),
                           'closed': file.closed, 'extracted_copy': rel(EXTRACTED / record['output']),
                           'fallback': False})
        if file.kind == 'SEQ':
            sources[file.name] = cbm_lines(file.data)
        else:
            binaries[file.name] = file.data
        if file.name in index:
            kind, path = index[file.name]
            old = path.read_bytes()
            if path.suffix == '.TXT':
                ours, theirs = sources[file.name], pc_lines(old)
                changed = [n + 1 for n, (a, b) in enumerate(zip(ours, theirs)) if a != b]
                same = not changed and len(ours) == len(theirs)
                entry = {'name': file.name, 'older': rel(path), 'comparison': 'normalized text',
                         'identical': same, 'differing_lines': changed}
                if changed:
                    entry['detail'] = [{'line': n, 'disk': ours[n-1], 'export_1992': theirs[n-1]}
                                       for n in changed]
            elif path.suffix == '.BIN':
                entry = {'name': file.name, 'older': rel(path), 'comparison': 'bytes',
                         'identical': old == file.data}
            else:
                entry = {'name': file.name, 'older': rel(path), 'comparison': 'not compared',
                         'note': 'BASIC listing text versus tokenized PRG'}
            older_comparison.append(entry)
    for name, (kind, path) in index.items():
        if name in sources or name in binaries or kind != 'SEQ':
            continue
        data = path.read_bytes()
        sources[name] = pc_lines(data)
        provenance.append({'name': name, 'kind': 'SEQ', 'source': rel(path), 'sha256': digest(data),
                           'bytes': len(data), 'fallback': True,
                           'normalization': 'ASCII upper case; CRLF to CR (in memory only)'})
    manifest = {'image': rel(IMAGE), 'image_sha256': digest(IMAGE.read_bytes()),
                'extraction_manifest_sha256': digest((EXTRACTED / 'manifest.json').read_bytes()),
                'loading_screen_image': rel(SCREEN_IMAGE),
                'loading_screen_image_sha256': digest(SCREEN_IMAGE.read_bytes()),
                'loading_screen_files': [{'name': f.name, 'sha256': digest(f.data), 'bytes': len(f.data),
                                          'load_address': f'${int.from_bytes(f.data[:2], "little"):04X}'}
                                         for f in screen_files],
                'index_sha256': digest((OLDER / 'INDEX').read_bytes()),
                'archive_comparison': archive, 'older_comparison': older_comparison,
                'files': provenance}
    (build / 'recovery-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return sources, binaries, manifest


def mos_hex(lines):
    """Decode MOS Technology hex records, validating checksums and terminator."""
    memory, records, terminal = {}, 0, False
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if terminal:
            raise ValueError('Data after MOS hex terminator')
        if not line.startswith(';'):
            raise ValueError(f'Invalid MOS hex record: {line}')
        raw = bytes.fromhex(line[1:])
        if len(raw) < 5:
            raise ValueError('MOS hex record is too short')
        count = raw[0]
        if len(raw) != count + 5 or sum(raw[:-2]) != int.from_bytes(raw[-2:], 'big'):
            raise ValueError('MOS hex length/checksum mismatch')
        address = int.from_bytes(raw[1:3], 'big')
        if not count:
            if address != records:
                raise ValueError('MOS hex record count mismatch')
            terminal = True
            continue
        records += 1
        for offset, byte in enumerate(raw[3:-2]):
            if address + offset in memory:
                raise ValueError('Overlapping MOS hex records')
            memory[address + offset] = byte
    if not terminal:
        raise ValueError('Missing MOS hex terminator')
    return memory


def prg_payload(data, address):
    if int.from_bytes(data[:2], 'little') != address:
        raise ValueError(f'Expected PRG load address ${address:04X}')
    return data[2:]


def assemble(build, sources, name, stem, regions):
    """Use one linker region for each original fixed-origin block."""
    assembly = build / (stem + '.s')
    lines = flatten(sources, name)
    assembly.write_text(convert(lines), encoding='latin-1')
    config = build / (stem + '.cfg')
    memories, segments = [], []
    for address, size, output in regions:
        filename = (build / output).as_posix() if output else ''
        memories.append(f'    M_{address:04X}: start = ${address:04X}, size = ${size:04X}, file = "{filename}";')
        kind = 'zp' if address < 0x100 else ('ro' if output else 'bss')
        segments.append(f'    AT_{address:04X}: load = M_{address:04X}, type = {kind};')
    config.write_text('# Generated by scripts/restore_c16.py; see config/c16.cfg.\n'
                      'MEMORY {\n' + '\n'.join(memories) + '\n}\nSEGMENTS {\n' + '\n'.join(segments) + '\n}\n')
    obj = build / (stem + '.o')
    subprocess.run([tool('ca65'), '-g', '-l', str(build / (stem + '.lst')),
                    '-o', str(obj), str(assembly)], check=True)
    subprocess.run([tool('ld65'), '-C', str(config), '-o', str(build / (stem + '.bin')),
                    '-m', str(build / (stem + '.map')),
                    '-Ln', str(build / (stem + '.labels')), '--dbgfile', str(build / (stem + '.dbg')),
                    str(obj)], check=True)
    return list(dict.fromkeys(module for module, _, _ in lines))


def main_regions():
    """Read the fixed-origin layout from config/c16.cfg so there is one definition."""
    regions = []
    for name, start, size, filename in re.findall(
            r'^\s*(\w+):\s*start\s*=\s*\$([0-9A-F]+),\s*size\s*=\s*\$([0-9A-F]+),\s*file\s*=\s*("[^"]*"|%O)',
            (ROOT / 'config/c16.cfg').read_text(), re.MULTILINE):
        regions.append((int(start, 16), int(size, 16), 'recovered-code.bin' if filename == '%O' else None))
    return regions


def version_aliens(bjh, version):
    if version == 1:
        return bjh
    return b''.join(bjh[page:page + 0x100] for page in range(4))


def alien_source(bjh, version):
    """ca65 source for ALDATA, one 64-byte alien per sheet, with provenance."""
    data = version_aliens(bjh, version)
    lines = [f'; ALDATA for game v{version} ({GAME_VERSIONS[version]}). Generated by scripts/restore_c16.py.',
             '; Bytes come only from BJH on the 2026 source disk.']
    if version == 2:
        lines.append('; Page p ($0400 + p*256) = BJH offset p .. p+255: the release tape loader\'s copy rule.')
    lines += ['.segment "AT_0400"', '.org $0400']
    for sheet in range(16):
        start = sheet * 64
        page, inside = divmod(start, 0x100)
        origin = start if version == 1 else page + inside
        lines.append(f'; sheet {sheet + 1}: chars 213-220 come from BJH offset ${origin:03X}')
        for row in range(0, 64, 16):
            chunk = data[start + row:start + row + 16]
            lines.append('.byte ' + ','.join(f'${b:02X}' for b in chunk))
    return '\n'.join(lines) + '\n'


def build_game(build):
    build = build.resolve()
    build.mkdir(parents=True, exist_ok=True)
    sources, binaries, manifest = prepare_sources(build)
    used = assemble(build, sources, MAIN, 'revenge', main_regions())
    code = (build / 'recovered-code.bin').read_bytes()
    if ENTRY + len(code) > FONT_BASE:
        raise ValueError('Assembled code overlaps the character set')
    used += assemble(build, sources, 'ASSEM-GRAPHS', 'landscape', [
        (0x1000, 0x600, 'landscape-1000.bin'), (0x1600, 0x200, 'landscape-1600.bin')])
    bottom = (build / 'landscape-1000.bin').read_bytes()
    top = (build / 'landscape-1600.bin').read_bytes()

    landscape = prg_payload(binaries['LANDSCAPE-2'], LAND_BASE)
    landscape_1 = prg_payload(binaries['LANDSCAPE-1'], LAND_BASE)
    font = prg_payload(binaries['FRAK!'], FONT_BASE)
    aliens = binaries['BJH'][2:]
    album8 = prg_payload(binaries['ALIBUM8'], 0x2000)
    album5 = prg_payload(binaries['ALIBUM5'], 0x2000)
    if len(landscape) != 0x800 or len(font) != 0x800 or len(aliens) != 0x400:
        raise ValueError('Unexpected graphics file layout')

    def differences(assembled, base, binary):
        return [f'${base + i:04X}' for i, b in enumerate(assembled) if binary[base - LAND_BASE + i] != b]

    land_report = {
        'source_bytes': {'$1000': len(bottom), '$1600': len(top)},
        'differences_vs_LANDSCAPE-2': differences(bottom, 0x1000, landscape) + differences(top, 0x1600, landscape),
        'differences_vs_LANDSCAPE-1': differences(bottom, 0x1000, landscape_1) + differences(top, 0x1600, landscape_1),
        'LANDSCAPE-1_vs_LANDSCAPE-2': [f'${LAND_BASE + i:04X}' for i, (a, b)
                                       in enumerate(zip(landscape_1, landscape)) if a != b],
    }
    o_ali = mos_hex(sources['O.ALI'])
    o_ali = bytes(o_ali[i] for i in range(0x400))
    alien_report = {
        'BJH_load_header': f'${int.from_bytes(binaries["BJH"][:2], "little"):04X}',
        'BJH_equals_ALIBUM8_first_1024': aliens == album8[:0x400],
        'O.ALI_equals_ALIBUM5_first_1024': o_ali == album5[:0x400],
        'O.ALI_vs_BJH_differences': sum(a != b for a, b in zip(o_ali, aliens)),
    }

    outputs, version_report = {}, {}
    for version in GAME_VERSIONS:
        stem = f'aliens-v{version}'
        (build / (stem + '.s')).write_text(alien_source(aliens, version))
        (build / (stem + '.cfg')).write_text(
            'MEMORY {\n    M_0400: start = $0400, size = $0400, file = "%O";\n}\n'
            'SEGMENTS {\n    AT_0400: load = M_0400, type = ro;\n}\n')
        subprocess.run([tool('ca65'), '-l', str(build / (stem + '.lst')), '-o', str(build / (stem + '.o')),
                        str(build / (stem + '.s'))], check=True)
        subprocess.run([tool('ld65'), '-C', str(build / (stem + '.cfg')), '-o', str(build / (stem + '.bin')),
                        str(build / (stem + '.o'))], check=True)
        version_data = (build / (stem + '.bin')).read_bytes()
        if version_data != version_aliens(aliens, version):
            raise ValueError(f'Assembled {stem} differs from its rule')
        memory = bytearray(TOP - LOAD)

        def place(address, data):
            memory[address - LOAD:address - LOAD + len(data)] = data
        place(ALIEN_BASE, version_data)
        place(LAND_BASE, landscape)
        place(ENTRY, code)
        place(FONT_BASE, font)
        output = build / f'xargons-revenge-v{version}.prg'
        output.write_bytes(LOAD.to_bytes(2, 'little') + memory)
        outputs[version] = output
        version_report[f'v{version}'] = {
            'name': GAME_VERSIONS[version], 'file': output.name, 'bytes': output.stat().st_size,
            'sha256': digest(output.read_bytes()), 'aliens_sha256': digest(version_data)}
    v1, v2 = (outputs[v].read_bytes()[2:] for v in (1, 2))
    differing = [a + LOAD for a, (x, y) in enumerate(zip(v1, v2)) if x != y]
    if not differing or min(differing) < ALIEN_BASE + 0x100 or max(differing) >= ALIEN_BASE + 0x400:
        raise ValueError('Game versions must differ only in alien pages 1-3')
    version_report['differences'] = {'bytes': len(differing), 'first': f'${differing[0]:04X}',
                                     'last': f'${differing[-1]:04X}',
                                     'sheets_affected': sorted({(a - ALIEN_BASE) // 64 + 1 for a in differing})}
    output = outputs[1]

    obj = mos_hex(sources['OBJ'])
    obj_differences = [a for a, b in obj.items()
                       if not ENTRY <= a < ENTRY + len(code) or code[a - ENTRY] != b]
    manifest['used_modules'] = list(dict.fromkeys(used))
    manifest['assets'] = [
        {'name': 'BJH', 'source': rel(IMAGE), 'sha256': digest(binaries['BJH']),
         'address': f'${ALIEN_BASE:04X}', 'bytes': len(aliens), 'included_in_prg': True,
         'placement': 'v1: dev LOADER copies BJH to ALDATA ($0400); v2: release tape-loader rule'},
        {'name': 'LANDSCAPE-2', 'source': rel(IMAGE), 'sha256': digest(binaries['LANDSCAPE-2']),
         'address': f'${LAND_BASE:04X}', 'bytes': len(landscape), 'included_in_prg': True,
         'placement': 'loaded by the C16 boot program; compared with ASSEM-GRAPHS output'},
        {'name': 'FRAK!', 'source': rel(IMAGE), 'sha256': digest(binaries['FRAK!']),
         'address': f'${FONT_BASE:04X}', 'bytes': len(font), 'included_in_prg': True,
         'placement': 'loaded by the C16 boot program; no surviving source'},
        {'name': 'ASSEM-GRAPHS', 'source': 'assembled CHAR#1-BOT and CHAR#1-TOP',
         'address': '$1000/$1600', 'bytes': len(bottom) + len(top), 'included_in_prg': False,
         'placement': 'comparison only; see landscape_comparison'},
    ]
    (build / 'recovery-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    report = {
        'load_address': f'${LOAD:04X}', 'entry_address': f'${ENTRY:04X}',
        'code_bytes': len(code), 'code_end': f'${ENTRY + len(code) - 1:04X}',
        'output_bytes': output.stat().st_size, 'sha256': digest(output.read_bytes()),
        'game_versions': version_report,
        'object_listing_bytes': len(obj), 'object_listing_differences': len(obj_differences),
        'first_object_differences': [f'${a:04X}' for a in obj_differences[:30]],
        'landscape_comparison': land_report, 'alien_comparison': alien_report,
        'padding': {'$0800-$0FFF': 'zero; colour and screen RAM, initialized by the game',
                    f'${ENTRY + len(code):04X}-$37FF': 'zero; unused gap below the font'},
        'packed_reference_sha256': digest(REFERENCE.read_bytes()) if REFERENCE.exists() else None,
        'packed_reference_comparison': 'run scripts/verify_vice.py for runtime comparison',
    }
    (build / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    if obj_differences or min(obj) != ENTRY or max(obj) + 1 != ENTRY + len(code):
        raise ValueError('Assembled code differs from original OBJ listing')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path, default=ROOT / 'build')
    args = parser.parse_args()
    build_game(args.build_dir)
