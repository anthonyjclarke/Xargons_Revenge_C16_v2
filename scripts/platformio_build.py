"""PlatformIO adapter for the same audited source build as build.sh."""

import subprocess
import sys
from pathlib import Path

from SCons.Script import Default, DefaultEnvironment

env = DefaultEnvironment()
root = Path(env.subst('$PROJECT_DIR'))
build = Path(env.subst('$BUILD_DIR'))
dependencies = list((root / 'scripts').glob('*.py')) + list((root / 'config').glob('*'))
dependencies += [p for p in (root / 'Original Source Recovered').rglob('*')
                 if p.is_file() and p.suffix.lower() not in ('.log',) and p.name != '.DS_Store']


def assemble(source, target, env):
    subprocess.run([sys.executable, str(root / 'scripts/restore_c16.py'),
                    '--build-dir', str(build)], check=True, cwd=str(root))


# Every environment builds both game versions; custom_game_version picks which
# one the upload target runs.
version = env.GetProjectOption('custom_game_version', '1')


def launch(source, target, env):
    subprocess.run([sys.executable, str(root / 'scripts/run_vice.py'),
                    str(build / f'xargons-revenge-v{version}.prg')], check=True, cwd=str(root))


outputs = [str(build / f'xargons-revenge-v{v}.prg') for v in (1, 2)]
program = env.Command(outputs, [str(p) for p in dependencies],
                      env.VerboseAction(assemble, "Assembling and checking original Xargon's Revenge source"))
env.Replace(PROGNAME=f'xargons-revenge-v{version}', PROGPATH=str(build / f'xargons-revenge-v{version}.prg'))
env.Alias('buildprog', program)
env.AddCustomTarget('upload', program, env.VerboseAction(launch, "Launching Xargon's Revenge in VICE"),
                    title='Run in VICE', description=f'Run game v{version} on an emulated 16 KB PAL C16')
Default(program)
