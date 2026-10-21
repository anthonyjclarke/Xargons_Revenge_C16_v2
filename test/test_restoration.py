"""Regression checks for historical syntax, provenance and assembled bytes."""

import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from d64_image import D64Image
from restore_c16 import (ROOT, IMAGE, OLDER, REFERENCE, build_game, cbm_lines, mos_hex,
                         pc_lines, prepare_sources, version_aliens)
from source_converter import convert, flatten

FALLBACKS = {'ALI-PRINT&CLEAR', 'COMPLETED-SHEET', 'DATA-LAND/CHARS',
             'FIRING-MEGA/CODE', 'RASTER-ROUTINES', 'WHOOPPEE-MESSAGE'}
PRG_SHA256 = '32c13c8867ea97bb4fd60ac9a73e5d7a600c04ece5699ac37680143c12adce33'
PRG_V2_SHA256 = '0ee0a82306583c8bf4a17f44731eaeb411f098ba9c00d20885b26879cd397665'


class RestorationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='xargon-test-')
        cls.build = Path(cls.temp.name)
        cls.before = {p: hashlib.sha256(p.read_bytes()).hexdigest()
                      for root in (ROOT / 'Original Source Recovered', ROOT / 'Original Artifacts')
                      for p in root.rglob('*') if p.is_file() and p.name != '.DS_Store'}
        cls.before[REFERENCE] = hashlib.sha256(REFERENCE.read_bytes()).hexdigest()
        with contextlib.redirect_stdout(io.StringIO()):
            cls.output = build_game(cls.build).read_bytes()
        cls.output_v2 = (cls.build / 'xargons-revenge-v2.prg').read_bytes()
        cls.manifest = json.loads((cls.build / 'recovery-manifest.json').read_text())
        cls.comparison = json.loads((cls.build / 'comparison.json').read_text())
        cls.sources, cls.binaries, _ = prepare_sources(cls.build / 'inputs')

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_complete_prg_matches_verified_baseline(self):
        self.assertEqual(len(self.output), 15362)
        self.assertEqual(self.output[:2], b'\x00\x04')
        self.assertEqual(hashlib.sha256(self.output).hexdigest(), PRG_SHA256)

    def test_game_v2_differs_only_by_the_tape_loader_rule(self):
        self.assertEqual(hashlib.sha256(self.output_v2).hexdigest(), PRG_V2_SHA256)
        bjh = self.binaries['BJH'][2:]
        self.assertEqual(self.output_v2[2:0x402], b''.join(bjh[p:p + 256] for p in range(4)))
        self.assertEqual(self.output_v2[2:0x402], version_aliens(bjh, 2))
        self.assertEqual(self.output_v2[0x402:], self.output[0x402:])
        differing = [a for a, (x, y) in enumerate(zip(self.output, self.output_v2)) if x != y]
        self.assertEqual(len(differing), 735)
        self.assertEqual((min(differing) - 2 + 0x400, max(differing) - 2 + 0x400), (0x0501, 0x07FF))
        # Pages 1-3 repeat page 0's sheet 1-4 designs, raised by 1-3 bytes.
        for sheet in range(4, 16):
            page, base = divmod(sheet, 4)
            alien = self.output_v2[2 + sheet * 64:2 + sheet * 64 + 64]
            self.assertEqual(alien, bjh[base * 64 + page:base * 64 + page + 64])
        self.assertIn('ALDATA for game v2', (self.build / 'aliens-v2.s').read_text())

    def test_all_object_records_match_assembled_code(self):
        obj = mos_hex(self.sources['OBJ'])
        self.assertEqual(len(obj), 8094)
        self.assertEqual((min(obj), max(obj)), (0x1800, 0x379D))
        for address, value in obj.items():
            self.assertEqual(self.output[2 + address - 0x400], value, hex(address))
        self.assertEqual(self.output[2 + 0x379E - 0x400:2 + 0x3800 - 0x400], bytes(0x62))

    def test_fresh_modules_and_explicit_fallbacks(self):
        files = {r['name']: r for r in self.manifest['files']}
        self.assertEqual({n for n, r in files.items() if r['fallback']}, FALLBACKS)
        self.assertEqual(sum(not r['fallback'] for r in files.values()), 94)
        used = set(self.manifest['used_modules'])
        self.assertTrue(FALLBACKS <= used)
        self.assertEqual(len(used), 71)
        self.assertFalse(files['REVENGE']['fallback'])
        self.assertIn('SOURCE: FIRING-MEGA/CODE:1', (self.build / 'revenge.s').read_text('latin-1'))

    def test_older_export_agrees_except_one_comment_byte(self):
        changed = [e for e in self.manifest['older_comparison'] if not e.get('identical', True)]
        self.assertEqual([(e['name'], e['differing_lines']) for e in changed], [('CHAR#1-BOT', [4])])
        self.assertEqual(changed[0]['detail'][0]['disk'], '; L\xaf1')
        archive = self.manifest['archive_comparison']
        self.assertTrue(archive['identical'])
        self.assertEqual(archive['members'], 101)

    def test_graphics_have_original_asset_provenance(self):
        data = self.output[2:]
        self.assertEqual(data[0:0x400], self.binaries['BJH'][2:])
        self.assertEqual(data[0x400:0xC00], bytes(0x800))
        self.assertEqual(data[0xC00:0x1400], self.binaries['LANDSCAPE-2'][2:])
        self.assertEqual(data[0x3400:], self.binaries['FRAK!'][2:])
        self.assertEqual(self.binaries['FRAK!'], (OLDER / 'FRAK.BIN').read_bytes())
        aliens = self.comparison['alien_comparison']
        self.assertTrue(aliens['BJH_equals_ALIBUM8_first_1024'])
        self.assertTrue(aliens['O.ALI_equals_ALIBUM5_first_1024'])
        land = self.comparison['landscape_comparison']
        self.assertEqual(len(land['differences_vs_LANDSCAPE-2']), 29)
        self.assertEqual(len(land['differences_vs_LANDSCAPE-1']), 7)

    def test_inputs_are_unchanged_by_build(self):
        after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.before}
        self.assertEqual(self.before, after)

    def test_missing_ambiguous_and_recursive_includes_fail(self):
        with self.assertRaisesRegex(ValueError, 'ambiguous/missing'):
            flatten({'MAIN': ['.LIB LOST*']}, 'MAIN')
        with self.assertRaisesRegex(ValueError, 'ambiguous/missing'):
            flatten({'MAIN': ['.LIB SHEET*'], 'SHEET1': [], 'SHEET2': []}, 'MAIN')
        with self.assertRaisesRegex(ValueError, 'Recursive'):
            flatten({'MAIN': ['.LIB MAIN*']}, 'MAIN')

    def test_historical_syntax_keeps_instructions_and_literals(self):
        result = convert([('TEST', 1, 'XTRCDE NOP'),
                          ('TEST', 2, 'TED    = $FF00'),
                          ('TEST', 3, "TEXT .BYTE 'A;B',0 ;* NOTE"),
                          ('TEST', 4, 'STOP    *=*+1    ;* STOP ?'),
                          ('TEST', 5, '.BYT $06,$06'),
                          ('TEST', 6, '*=$1800')])
        self.assertIn('XTRCDE: NOP', result)
        self.assertIn('TED    = $FF00', result)
        self.assertIn('TEXT: .BYTE "A;B",0 ;* NOTE', result)
        self.assertIn('STOP: .res 1 ;* STOP ?', result)
        self.assertIn('.byte $06,$06', result)
        self.assertIn('.segment "AT_1800"\n.org $1800', result)
        with self.assertRaisesRegex(ValueError, 'macro'):
            convert([('TEST', 1, '.MAC DOUBLE')])

    def test_conversion_hazards_are_handled(self):
        # CR is the only CBM line break; $85 and $1C are data, not newlines.
        self.assertEqual(cbm_lines(b'; A\x85B\rLDA #1\x1c\r'), ['; A\x85B', 'LDA #1\x1c', ''])
        self.assertEqual(pc_lines(b'lda #1\r\n.byte \'ab\'\r\n'), ['LDA #1', ".BYTE 'AB'", ''])
        with self.assertRaisesRegex(ValueError, 'upper-case'):
            pc_lines(b'lda #1\r\nLDA #2\r\n')

    def test_invalid_hex_and_malformed_disks_fail(self):
        with self.assertRaisesRegex(ValueError, 'checksum'):
            mos_hex([';011800000000'])
        with self.assertRaisesRegex(ValueError, 'terminator'):
            mos_hex([';011800000019'])
        disk = D64Image(IMAGE)
        data = bytearray(disk.data)
        # Isolated synthetic cycle on the first sector; no original file edits.
        data[0:2] = b'\x01\x00'
        disk.data = data
        with self.assertRaisesRegex(ValueError, 'Cyclic'):
            list(disk.chain(1, 0))
        with tempfile.NamedTemporaryFile(suffix='.d64') as short:
            short.write(IMAGE.read_bytes()[:1000])
            short.flush()
            with self.assertRaisesRegex(ValueError, '35-track'):
                D64Image(short.name)


if __name__ == '__main__':
    unittest.main()
