#!/usr/bin/env python3
"""Generate a source/symbol catalogue, asset data and indexed graphics atlases.

Read-only analysis of the preservation inputs, a previously built PRG and the
VICE captures written by verify_vice.py. This is a static catalogue, not a
control-flow or 6502-cycle emulator.
"""

import argparse
import ast
import collections
import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import quote

from restore_c16 import ROOT, LOAD, ENTRY, prepare_sources, mos_hex
from source_converter import OPCODES, flatten, split_comment

BRANCHES = {'JSR', 'JMP', 'BCC', 'BCS', 'BEQ', 'BMI', 'BNE', 'BPL', 'BVC', 'BVS'}
STORES = {'STA', 'STX', 'STY', 'INC', 'DEC', 'ASL', 'LSR', 'ROL', 'ROR'}
# Tables exported for graphics, ports and tests: symbol -> byte length.
TABLES = {
    'SHPDT1': 64, 'FUELDA': 48, 'CHR87': 32, 'CHR91': 32, 'BANNER': 320, 'SHTABL': 128,
    'TOKILL': 6, 'MPGVIL': 6, 'ALSC1': 8, 'ALSC2': 8, 'ALSC3': 8, 'STTDIR': 4, 'EXPCHR': 8,
    'BONUNT': 6, 'BONTEN': 6, 'CONVTB': 16, 'YSHIP': 12, 'SHPCHR': 12, 'YVAL1': 8,
    'HITTBL': 20, 'LUMINX': 16, 'STCOLS': 4, 'SPDTOP': 4, 'SPDBOT': 4, 'STARCL': 4,
    'TESCO': 36, 'PRSSTR': 19, 'ROSS1': 14, 'ROSS2': 14, 'ENDBIT': 8, 'BOTST': 6, 'YHIL': 4,
    'LOOKUP': 16, 'SCRPOS': 32, 'TIM20': 34, 'TIM24': 2, 'TIM9': 4, 'TIM5': 5, 'TIM32': 4,
    'TIM6': 6, 'BTD': 3, 'RWD': 3, 'FRAK1': 2, 'SCORCL': 4, 'PLANNM': 30, 'FUELCH': 6,
    'FUELYP': 6, 'PINK': 4, 'FLOYD': 4, 'FLID1': 2, 'FLID2': 2, 'TPBUFF': 40, 'TPCOLS': 40,
    'SNDTOG': 8, 'CTLTOG': 16, 'COMMES': 24,
}


def table(headers, rows):
    rows = [[str(c).replace('|', '/') for c in row] for row in [headers] + rows]
    widths = [max(3, max(len(row[i]) for row in rows)) for i in range(len(headers))]
    if max(widths) > 45:
        raise ValueError('Markdown table cell exceeds 45 characters')
    fmt = lambda row: '| ' + ' | '.join(v.ljust(widths[i]) for i, v in enumerate(row)) + ' |'
    return '\n'.join([fmt(rows[0]), fmt(['-' * w for w in widths])] + [fmt(r) for r in rows[1:]])


def parse_line(line):
    code, comment = split_comment(line)
    code = code.strip()
    definition = None
    if code and not code.startswith('.') and not code.startswith('*'):
        first, *rest = code.split(None, 1)
        match = re.match(r'^([A-Z][A-Z0-9_]*)\s*=', code)
        if match:
            definition = match[1]
            code = code[len(definition):].lstrip()
        elif first not in OPCODES and re.fullmatch(r'[A-Z][A-Z0-9_]*', first):
            definition = first
            code = rest[0] if rest else ''
    return definition, code, comment.lstrip(';* ')


def listing_owners(path, end):
    """Use printed PC changes so abbreviated long data lines retain full size."""
    owners, owner, address, pending = {}, None, None, None
    for line in path.read_text('latin-1').splitlines():
        match = re.match(r'^([0-9A-F]{6})[ r]', line)
        if not match:
            continue
        current = int(match[1], 16)
        if address is not None and current != address:
            if pending and 0 < current - address <= 0x2000:
                for a in range(max(address, ENTRY), min(current, end)):
                    owners[a] = pending
            pending = None
        address = current
        source = re.search(r'; SOURCE: (.+):\d+$', line)
        if source:
            owner = source[1]
        if address >= ENTRY and re.fullmatch(r'(?:(?:[0-9A-F]{2}|xx)\s*)+', line[11:23].strip()):
            pending = owner
    if pending:
        for a in range(address, end):
            owners[a] = pending
    return owners


def atlas(path, title, data, start, mode, first_code, columns=16, note=None):
    """Decode original glyph bits to SVG; colours are index keys, not a TED palette."""
    count = len(data) // 8
    cell_w, cell_h, scale = 60, 70, 5
    height = 75 + ((count + columns - 1) // columns) * cell_h
    colors = ['#111827', '#ef4444', '#38bdf8', '#fef08a']
    note = note or 'Raw glyph bytes; neutral index colours; not the in-game palette.'
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{columns*cell_w}" height="{height}" viewBox="0 0 {columns*cell_w} {height}">',
           '<rect width="100%" height="100%" fill="#f8fafc"/>',
           f'<text x="12" y="24" font-family="monospace" font-size="16">{html.escape(title)}</text>',
           f'<text x="12" y="45" font-family="monospace" font-size="12">{html.escape(note)}</text>']
    for i in range(count):
        x, y = (i % columns) * cell_w + 10, (i // columns) * cell_h + 65
        glyph = data[i * 8:(i + 1) * 8]
        for row, byte in enumerate(glyph):
            width = 4 if mode == 'multicolor' else 8
            for col in range(width):
                value = (byte >> (6 - col * 2)) & 3 if mode == 'multicolor' else (byte >> (7 - col)) & 1
                color = colors[value] if mode == 'multicolor' else ['#111827', '#e2e8f0'][value]
                w = scale * 2 if mode == 'multicolor' else scale
                out.append(f'<rect x="{x+col*w}" y="{y+row*scale}" width="{w}" height="{scale}" fill="{color}"/>')
        out.append(f'<text x="{x}" y="{y+53}" font-family="monospace" font-size="10">{first_code+i:03d} {start+i*8:04X}</text>')
    out.append('</svg>')
    path.write_text('\n'.join(out) + '\n')


def running_aliens(aliens):
    """The running version's tape loader copies page p from source offset p."""
    return b''.join(aliens[p:p + 0x100] for p in range(4))


def analyze(build, output):
    output.mkdir(parents=True, exist_ok=True)
    sources, binaries, manifest = prepare_sources(build / 'analysis-inputs')
    provenance = {r['name']: r for r in manifest['files']}
    labels = {name: int(address, 16) for address, name in re.findall(
        r'^al ([0-9A-Fa-f]+) \.(\w+)$', (build / 'revenge.labels').read_text(), re.M)}
    roots = ['REVENGE', 'ASSEM-GRAPHS']
    stages = {name: list(dict.fromkeys(row[0] for row in flatten(sources, name))) for name in roots}
    main = set(stages['REVENGE'])
    code = (build / 'recovered-code.bin').read_bytes()
    owners = listing_owners(build / 'revenge.lst', ENTRY + len(code))
    if set(owners) != set(range(ENTRY, ENTRY + len(code))):
        raise ValueError('Listing ownership does not cover the complete assembled region')
    sizes = collections.Counter(owners.values())
    definitions, modules, transfers, variables, patches = {}, [], [], [], []
    for name, lines in sources.items():
        if name in ('OBJ', 'O.ALI'):
            continue
        instruction_lines, pending = 0, None
        for number, line in enumerate(lines, 1):
            definition, body, comment = parse_line(line)
            if definition:
                kind = 'equate' if body.startswith('=') else 'label'
                if '*=*+' in body:
                    kind = 'reserved'
                elif body.upper().startswith(('.BYTE', '.BYT', '.WORD')):
                    kind = 'data'
                definitions[definition] = {'symbol': definition, 'module': name, 'line': number,
                                           'address': labels.get(definition) if name in main else None,
                                           'kind': kind, 'comment': comment,
                                           'expression': body[1:].strip() if kind == 'equate' else None}
                pending = definition if kind == 'label' and not body else None
            reserve = re.match(r'^\*=\*\+(\$?[0-9A-F]+)', body)
            if reserve and name in ('VARS', 'EXTRA-MEMORY'):
                symbol = definition or pending
                text = reserve[1]
                size = int(text[1:], 16) if text.startswith('$') else int(text)
                definitions[symbol]['kind'] = 'reserved'
                variables.append({'symbol': symbol, 'address': labels[symbol], 'bytes': size,
                                  'module': name, 'comment': comment or definitions[symbol]['comment'],
                                  'source_line': definitions[symbol]['line']})
                pending = None
            elif body and not definition:
                pending = None if not body.startswith(';') else pending
            op = body.split(None, 1)
            if op and op[0] in OPCODES:
                instruction_lines += 1
            if name in main and op and op[0] in BRANCHES and len(op) == 2:
                transfers.append({'module': name, 'line': number, 'operation': op[0], 'operand': op[1].split(';')[0].strip()})
            if name in main and op and op[0] in STORES and len(op) == 2:
                patches.append({'module': name, 'line': number, 'operation': op[0],
                                'operand': op[1].split(';')[0].strip()})
        modules.append({'name': name, 'path': provenance[name]['source'], 'fallback': provenance[name]['fallback'],
                        'raw_bytes': provenance[name]['bytes'],
                        'extracted_copy': provenance[name].get('extracted_copy'), 'logical_lines': len(lines),
                        'instruction_lines': instruction_lines, 'main_region_bytes': sizes[name],
                        'stages': [r for r in roots if name in stages[r]]})

    def constant(expression):
        expression = re.sub(r'\$([0-9A-F]+)', r'0x\1', expression)
        expression = re.sub(r'%([01]+)', r'0b\1', expression)
        expression = re.sub(r'^([<>])', '', expression)

        def walk(node):
            if isinstance(node, ast.Constant) and isinstance(node.value, int):
                return node.value
            if isinstance(node, ast.Name):
                value = definitions[node.id]['address']
                if value is None:
                    raise ValueError(node.id)
                return value
            if isinstance(node, ast.BinOp):
                left, right = walk(node.left), walk(node.right)
                if isinstance(node.op, ast.Add):
                    return left + right
                if isinstance(node.op, ast.Sub):
                    return left - right
                if isinstance(node.op, ast.Mult):
                    return left * right
            raise ValueError('Unsupported equate expression')
        return walk(ast.parse(expression, mode='eval').body)

    for _ in range(4):
        for definition in definitions.values():
            if definition['kind'] == 'equate' and definition['address'] is None:
                try:
                    definition['address'] = constant(definition['expression'])
                except (KeyError, ValueError, SyntaxError):
                    pass
    # Plain forward labels are classified by their following non-comment statement.
    for definition in definitions.values():
        if definition['kind'] != 'label':
            continue
        for later in sources[definition['module']][definition['line'] - 1:]:
            _, body, _ = parse_line(later)
            if body and not body.startswith(';'):
                head = body.split()[0]
                definition['kind'] = ('instruction-label' if head in OPCODES else
                                      'data' if head.upper().startswith(('.BYT', '.WORD')) else
                                      'reserved' if head.startswith('*=*+') else 'other-label')
                break
    for transfer in transfers:
        target = re.match(r'^([A-Z][A-Z0-9_]*)', transfer['operand'])
        dest = definitions.get(target[1]) if target else None
        transfer['target_module'] = dest['module'] if dest and dest['module'] in main else None
        try:
            transfer['target_address'] = constant(transfer['operand'])
        except (KeyError, ValueError, SyntaxError):
            transfer['target_address'] = None
    # Stores whose target lies inside assembled instructions modify code at run time.
    instruction_bytes = {a for a in range(ENTRY, ENTRY + len(code))}
    data_symbols = {d['address'] for d in definitions.values() if d['kind'] == 'data' and d['address']}
    self_modifying = []
    for patch in patches:
        operand = re.sub(r',[XY]$', '', patch['operand'])
        if operand.startswith('#') or operand.startswith('('):
            continue
        try:
            address = constant(operand)
        except (KeyError, ValueError, SyntaxError):
            continue
        symbol = re.match(r'^([A-Z][A-Z0-9_]*)', operand)
        target = definitions.get(symbol[1]) if symbol else None
        if address in instruction_bytes and target and target['kind'] == 'instruction-label':
            self_modifying.append({**patch, 'target_address': address, 'target_symbol': target['symbol']})
    symbols = sorted([d for d in definitions.values() if d['module'] in main], key=lambda d: d['symbol'])
    prg = (build / 'xargons-revenge.prg').read_bytes()
    payload = prg[2:]
    data = {
        'method': 'Static module catalogue and direct symbolic transfers; not a complete call graph or cycle profile',
        'source_image_sha256': manifest['image_sha256'],
        'prg_sha256': hashlib.sha256(prg).hexdigest(),
        'assembly_roots': stages, 'modules': modules, 'symbols': symbols,
        'variables': variables, 'direct_transfers': transfers, 'self_modifying_stores': self_modifying,
        'counts': {'available_source_records': len(sources), 'main_modules': len(main),
                   'active_modules': len(set(n for names in stages.values() for n in names)),
                   'main_logical_lines': sum(len(sources[n]) for n in main),
                   'main_instruction_lines': sum(m['instruction_lines'] for m in modules if m['name'] in main),
                   'main_symbol_definitions': len(symbols), 'direct_transfers': len(transfers),
                   'self_modifying_stores': len(self_modifying),
                   'zero_page_bytes': sum(v['bytes'] for v in variables if v['module'] == 'VARS'),
                   'extra_memory_bytes': sum(v['bytes'] for v in variables if v['module'] == 'EXTRA-MEMORY'),
                   'main_region_bytes': sum(sizes.values())}}
    (output / 'codebase-index.json').write_text(json.dumps(data, indent=2) + '\n')

    module_map = {m['name']: m for m in modules}
    text = ('# Generated Code Reference\n\n## Scope and Method\n\n'
            'Generated by `scripts/analyze_codebase.py` from the verified build and preserved sources. '
            'Logical source-line numbers count CR-separated lines in each preserved module, starting at 1. '
            'Module byte counts are spans of the assembled `$1800–$379D` region and include embedded '
            'tables and text; they are not function sizes. Direct transfers omit fall-through, the '
            'self-modified IRQ dispatch, `RTS`-based returns and stack manipulation. Symbols may name '
            'internal branch points or data rather than callable routines.\n\n')
    text += '---\n\n## Main Modules in Assembly Order\n\n'
    text += table(['Module', 'Bytes', 'Lines', 'Origin'],
                  [(f'`{n}`', sizes[n], len(sources[n]), '1992' if provenance[n]['fallback'] else '2026')
                   for n in stages['REVENGE']]) + '\n\n'
    text += ('Modules with zero bytes hold only equates, zero-page or `$0200` reservations, or '
             '(for `REVENGE`) the includes themselves.\n\n')
    text += '---\n\n## Source Locations\n\n'
    for name in sorted(n for n in sources if n in module_map):
        m = module_map[name]
        path = m['extracted_copy'] if not m['fallback'] else m['path']
        text += f"`{name}` – [preserved input](../../{quote(path, safe='/')}); {m['raw_bytes']} raw bytes, {m['logical_lines']} logical lines.\n\n"
    text += '---\n\n## Zero-Page and Extra-Memory Variables\n\n'
    text += table(['Symbol', 'Address', 'Bytes', 'Module', 'Line'],
                  [(f"`{v['symbol']}`", f"`${v['address']:04X}`", v['bytes'], f"`{v['module']}`", v['source_line'])
                   for v in variables]) + '\n\n'
    text += '---\n\n## Self-Modifying Stores\n\n'
    text += ('Stores into assembled instruction bytes, found statically from symbolic operands. '
             'Writes through pointers are not detected.\n\n')
    text += table(['Module', 'Line', 'Store', 'Target'],
                  [(f"`{p['module']}`", p['line'], f"`{p['operation']} {p['operand']}`",
                    f"`${p['target_address']:04X}` in `{p['target_symbol']}`") for p in self_modifying]) + '\n\n'
    text += '---\n\n## Symbols by Module\n\n'
    for name in stages['REVENGE']:
        defs = [s for s in symbols if s['module'] == name]
        if not defs:
            continue
        text += f'### {name}\n\n'
        text += table(['Symbol', 'Address', 'Line', 'Kind'],
                      [(f"`{s['symbol']}`", f"`${s['address']:04X}`" if s['address'] is not None else 'unresolved',
                        s['line'], s['kind']) for s in defs]) + '\n\n'
    (output / 'CODE_REFERENCE.md').write_text(text.rstrip() + '\n')

    aliens = payload[0:0x400]
    running = running_aliens(aliens)
    reference_dump = build / 'reference-memory.bin'
    if reference_dump.is_file() and reference_dump.read_bytes()[0:0x400] != running:
        raise ValueError('Running-version alien rule does not match the VICE reference dump')
    landscape_source = (build / 'landscape-1000.bin').read_bytes() + (build / 'landscape-1600.bin').read_bytes()
    capture = (build / 'restored-later-memory.bin').read_bytes()
    title = (build / 'restored-title-memory.bin').read_bytes()
    capture_report = json.loads((build / 'vice-verification.json').read_text())

    def zp(symbol):
        return capture[labels[symbol]]
    assets = {
        'note': 'Hex payloads keep raw bytes in memory order. Glyphs are 8 bytes, top row first; '
                'bit 7 is the leftmost pixel; multicolour pairs are bits 7-6 leftmost.',
        'prg_sha256': data['prg_sha256'],
        'aliens': {'address': ALIEN, 'bytes': 1024, 'source': 'BJH (2026 source disk)', 'layout':
                   '16 aliens x 64 bytes: frame 0 = 32 bytes for chars 213-216, frame 1 = 32 bytes for chars 217-220',
                   'hex': aliens.hex()},
        'aliens_running_version': {'address': ALIEN, 'bytes': 1024, 'source':
                                   'derived: page p = BJH[p : p+256]; confirmed against the VICE dump of xargons_revenge.prg',
                                   'hex': running.hex()},
        'landscape': {'address': 0x1000, 'glyphs': 256, 'source': 'LANDSCAPE-2 (2026 source disk)', 'hex': payload[0xC00:0x1400].hex()},
        'landscape_source_variant': {'address': 0x1000, 'glyphs': 256, 'source': 'ASSEM-GRAPHS (CHAR#1-BOT, CHAR#1-TOP)',
                                     'hex': landscape_source.hex(), 'included_in_prg': False},
        'font': {'address': 0x3800, 'glyphs': 256, 'source': 'FRAK! (2026 source disk)', 'hex': payload[0x3400:].hex()},
        'tables': {},
        'gameplay_capture': {
            'source': 'build/restored-later-memory.bin from scripts/verify_vice.py',
            'state': f"LOOP after {capture_report['main_loop_passes_before_capture']} passes with no input",
            'memory_sha256': hashlib.sha256(capture).hexdigest(),
            'screenshot': 'docs/images/restored-later.png',
            'registers': {name: zp(name) for name in ('BAKCOL', 'LANCL1', 'LANCL2', 'LANCL3', 'SHIPC1',
                                                       'SHIPC2', 'TOPLX', 'BOTLX', 'MESSX', 'SHEET')},
            'colour_ram_hex': capture[0x0800:0x0C00].hex(),
            'screen_ram_hex': capture[0x0C00:0x1000].hex(),
            'landscape_ram_hex': capture[0x1000:0x1800].hex(),
            'font_ram_hex': capture[0x3800:0x4000].hex(),
        },
        'title_capture': {
            'source': 'build/restored-title-memory.bin from scripts/verify_vice.py',
            'state': f"TITTER after {capture_report['title_passes_before_input']} passes",
            'memory_sha256': hashlib.sha256(title).hexdigest(),
            'screenshot': 'docs/images/restored-title.png',
            'registers': {name: title[labels[name]] for name in ('BAKCOL', 'COLVAR', 'SHIPC1', 'SHIPC2', 'LANCL1')},
            'colour_ram_hex': title[0x0800:0x0C00].hex(),
            'screen_ram_hex': title[0x0C00:0x1000].hex(),
        },
    }
    for symbol, length in TABLES.items():
        address = labels[symbol]
        raw = payload[address - LOAD:address - LOAD + length]
        assets['tables'][symbol] = {'address': address, 'bytes': length, 'hex': raw.hex()}
    patterns = {}
    for n, sheet in enumerate('123456789ABCDEFG'):
        symbol = 'PATD' + sheet
        start = labels[symbol] - LOAD
        end = payload.index(0xFF, start) + 1
        patterns[symbol] = {'address': labels[symbol], 'bytes': end - start, 'hex': payload[start:end].hex()}
    assets['movement_patterns'] = patterns
    # COMPACTOR (BASIC) packs TITLE-DATA's 640 nibbles at $8000 into 320 bytes.
    title_data = binaries['TITLE-DATA'][2:]
    packed = bytes((title_data[c * 2] * 16 + title_data[c * 2 + 1]) & 255 for c in range(320))
    banner = bytes.fromhex(assets['tables']['BANNER']['hex'])
    assets['banner_provenance'] = {
        'method': 'COMPACTOR rule x = 16*peek(32768+2c) + peek(32769+2c), c = 0-319, applied to TITLE-DATA',
        'title_data_sha256': hashlib.sha256(binaries['TITLE-DATA']).hexdigest(),
        'matching_bytes': sum(a == b for a, b in zip(packed, banner)),
        'differences': [{'offset': i, 'banner': f'${b:02X}', 'compacted_title_data': f'${a:02X}'}
                        for i, (a, b) in enumerate(zip(packed, banner)) if a != b]}
    (output / 'asset-data.json').write_text(json.dumps(assets, indent=2) + '\n')
    atlas(output / 'landscape-multicolor.svg', 'LANDSCAPE-2 bank at $1000: character codes 000-255',
          payload[0xC00:0x1400], 0x1000, 'multicolor', 0)
    atlas(output / 'font-hires.svg', 'FRAK! bank at $3800: character codes 000-255, 1-bit view',
          payload[0x3400:], 0x3800, 'hires', 0)
    atlas(output / 'font-multicolor.svg', 'FRAK! bank at $3800: character codes 000-255, 2-bit view',
          payload[0x3400:], 0x3800, 'multicolor', 0)
    atlas(output / 'aliens-source.svg', 'BJH aliens at $0400: one row per alien (frame 0 = 213-216, frame 1 = 217-220)',
          aliens, 0x0400, 'hires', 213, columns=8,
          note='Codes shown are the play-area codes each glyph is copied to by ALIDEF.')
    print(json.dumps(data['counts'], indent=2))
    print(f'Wrote {output}')


ALIEN = 0x0400

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path, default=ROOT / 'build')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'docs/analysis')
    args = parser.parse_args()
    analyze(args.build_dir.resolve(), args.output_dir.resolve())
