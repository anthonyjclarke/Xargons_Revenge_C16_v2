#!/usr/bin/env python3
"""Record the tool versions used for the build, checks and handbook."""

import argparse
import json
import platform
import re
import subprocess
import sys
from pathlib import Path

from restore_c16 import ROOT

MINIMUMS = {'python': '3.9', 'ca65': '2.18', 'ld65': '2.18', 'vice': '3.10',
            'platformio': '6.1', 'node': '18', 'pillow': '10.1'}


def version(command, pattern):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    found = re.search(pattern, result.stdout + result.stderr)
    return found[1] if found else None


def check():
    try:
        from restore_c16 import tool
        cc65 = {name: version([tool(name), '--version'], r'V(\d+\.\d+)') for name in ('ca65', 'ld65')}
    except FileNotFoundError:
        cc65 = {'ca65': None, 'ld65': None}
    try:
        import PIL
        pillow = PIL.__version__
    except ImportError:
        pillow = None
    found = {
        'python': platform.python_version(), **cc65,
        # xplus4 has no version flag; c1541 from the same VICE install reports it.
        'vice': version(['c1541', '-version'], r'VICE (\d+\.\d+(?:\.\d+)?)'),
        'platformio': version(['pio', '--version'], r'version (\d+\.\d+\.\d+)'),
        'node': version(['node', '--version'], r'v(\d+\.\d+\.\d+)'),
        'pillow': pillow,
    }
    return {'host': f'{platform.system()} {platform.machine()}', 'minimums': MINIMUMS, 'found': found}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/tool-checks.json')
    args = parser.parse_args()
    report = check()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
