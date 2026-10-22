#!/usr/bin/env python3
"""Function catalog for VIRTUAL.EXE: pcrecomp disasm32.

    py -3 tools/catalog.py            # -> work/functions_virtual.json

The entry point is the seed; the rest is recursive descent, prologues and a
data scan. The catalog is derived from the game binary, so it lives in work/
and is never committed.
"""
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# pcrecomp: $PCRECOMP, else a checkout at ../tools, else ../pcrecomp (where the installer puts it)
_PC = os.environ.get('PCRECOMP') or next(
    (d for d in (os.path.join(_HERE, '..', 'tools'), os.path.join(_HERE, '..', 'pcrecomp'))
     if os.path.isdir(os.path.join(d, 'tools', 'lift'))), os.path.join(_HERE, '..', 'pcrecomp'))
TOOLS = os.path.join(_PC, 'tools')
GAME = os.path.join(_HERE, 'game', 'virtual')

os.makedirs(os.path.join(_HERE, 'work'), exist_ok=True)     # gitignored, so absent in a fresh copy
subprocess.run([sys.executable, os.path.join(TOOLS, 'disasm', 'disasm32.py'),
                os.path.join(GAME, 'VIRTUAL.EXE'), '-o',
                os.path.join(_HERE, 'work', 'functions_virtual.json')], check=True)
