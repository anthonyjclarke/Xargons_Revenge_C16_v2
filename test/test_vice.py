"""Emulator checks; skipped (never passed) when VICE xplus4 is unavailable."""

import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from restore_c16 import build_game

XPLUS4 = shutil.which('xplus4') or next(
    (p for p in ('/opt/homebrew/bin/xplus4', '/usr/local/bin/xplus4') if Path(p).is_file()), None)


@unittest.skipUnless(XPLUS4, 'VICE xplus4 not installed: title, gameplay and reference checks NOT run')
class ViceTests(unittest.TestCase):
    def test_title_gameplay_and_running_version(self):
        from verify_vice import verify
        with tempfile.TemporaryDirectory(prefix='xargon-vice-') as temp:
            build = Path(temp)
            with contextlib.redirect_stdout(io.StringIO()):
                build_game(build)
                report = verify(build)
            self.assertTrue(report['gameplay_loop_reached'])
            self.assertTrue(report['reference_reached_gameplay_loop'])
            self.assertEqual((report['title_flag'], report['lives']), (0, 5))
            self.assertEqual(report['initialized_code_differences'], 0)
            self.assertEqual(set(report['differences_by_region']),
                             {'alien graphics (ALDATA)', 'colour/screen RAM work area',
                              'padding below the font'})
            self.assertEqual([p['equals_BJH_offset'] for p in report['alien_pages_in_reference']],
                             ['$000', '$001', '$002', '$003'])
            for name in ('restored-title.png', 'restored-gameplay.png'):
                self.assertTrue((build / name).read_bytes().startswith(b'\x89PNG'))


if __name__ == '__main__':
    unittest.main()
