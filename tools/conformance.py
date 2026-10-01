#!/usr/bin/env python3
"""Virtual Springfield conformance harness (REPO_RULES section 9).

Two fixed corpora, one pass/fail count each, compared against the committed
baseline in conformance.json; a regression fails the run:

* **Milestones**: one headless run of build/virtualspringfield.exe with a
  scripted click, scored by the lines the host prints at each stage. Boot:
  the install check, the window, the DirectDraw mode and surfaces, and the
  first frames, in this order. The logos and the title play by themselves and
  Town Square is up (Troy McClure talking) by about 70 s. At 75 s the run
  clicks MAP, and the host compares the screen at 74 s with 80 s: Troy alone
  changes about 2% of it, the area map opening about 37%. At 95 s the game
  has to be idle in its own message loop, not stuck or faulted.
* **Lift health**: from the generated tree and the same run. Lift errors,
  bodies with no terminator, RECOMP_ITAIL targets that cannot resolve at run
  time, UNIMPLEMENTED instructions, and DirectDraw methods the game called
  that the host does not implement.

The game is not in the repo. Without game/virtual and the built host this
skips with a message and exits 0, so it can sit in CI without the corpus.

    py -3 tools/conformance.py              # run, compare, print the table
    py -3 tools/conformance.py --update     # ...and accept the result as the baseline
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = os.path.join(ROOT, 'build', 'virtualspringfield.exe')
GEN = os.path.join(ROOT, 'src', 'recomp', 'gen')
BASELINE = os.path.join(ROOT, 'conformance.json')

# (name, what the host prints when it is reached). Order is boot order.
MILESTONES = [
    ('image mapped, every import bound', r'\[bind\] 0x00400000: .* 0 unresolved'),
    ('install check passes (HDPATH, CDPATH)', r'\[registry\] HDPATH -> '),
    ('game window created', r'CreateWindowExA\("Virtual Springfield"'),
    ('DirectDraw 640x480x8', r'SetDisplayMode\(640x480x8\)'),
    ('flipping primary surface', r'CreateSurface\(caps 00000218, 640x480x8, 1 back buffer\)'),
    ('first frame presented', r'\[capture\] frame 1 presented'),
    ('100 frames (the logos)', r'\[capture\] frame 100 presented'),
    ('1000 frames (title, Town Square)', r'\[capture\] frame 1000 presented'),
    ('click MAP', r'\[input\] click 450,445 '),
    ('the area map opens', r'\[diff\] ([2-9]\d|100)% of the screen changed'),
    ('idle in the message loop at 95 s, no fault', r'\[watchdog\] 95 s: in sub_00411550'),
]

RUN = ['--headless', '--run', '--watchdog', '95', '--click', '450,445@75000', '--diff', '74000,80000']


def boot():
    try:
        p = subprocess.run([HOST] + RUN, cwd=ROOT, capture_output=True, text=True, errors='replace',
                           timeout=180)
        out, code = p.stdout + p.stderr, p.returncode
    except subprocess.TimeoutExpired as e:
        out, code = (e.stdout or '') + (e.stderr or ''), 'timeout'
        out = out if isinstance(out, str) else out.decode(errors='replace')
    # A fault prints its report and stops: no later milestone can match.
    if '=== fault' in out:
        out = out[:out.index('=== fault')]
    passed = [name for name, pat in MILESTONES if re.search(pat, out)]
    last = [l for l in out.splitlines() if l.startswith(('===', '[diff]', '[callback]', '[native32]'))]
    return passed, code, last[:4], out


def lift_health(out):
    stats = json.load(open(os.path.join(ROOT, 'work', 'lift_stats.json')))
    disp = set(re.findall(r'\{ 0x([0-9A-F]{8})u,', open(os.path.join(GEN, 'recomp_dispatch.c')).read()))
    unresolved = unimplemented = 0
    for fn in glob.glob(os.path.join(GEN, 'recomp_0*.c')):
        text = open(fn).read()
        unresolved += sum(1 for t in re.findall(r'RECOMP_ITAIL\(0x([0-9A-F]{8})u\)', text) if t not in disp)
        unimplemented += text.count('UNIMPLEMENTED:')
    return {'lifted': stats['lifted'], 'errors': stats['errors'],
            'no_terminator': stats['no_terminator'], 'unresolved_itail': unresolved,
            'unimplemented': unimplemented,
            'ddraw_unimplemented': len(set(re.findall(r'\[ddraw\] (\w+): not implemented', out)))}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--update', action='store_true', help='accept this run as the baseline')
    args = ap.parse_args()
    if not (os.path.exists(HOST) and os.path.isfile(os.path.join(ROOT, 'game', 'virtual', 'VIRTUAL.EXE'))):
        print('conformance: skipped -- needs game/virtual (your copy of Virtual Springfield) and '
              'build/virtualspringfield.exe (README, Building from source)')
        return 0

    passed, code, last, out = boot()
    health = lift_health(out)
    now = {'milestones': len(passed), 'of': len(MILESTONES), **health}
    base = json.load(open(BASELINE)) if os.path.exists(BASELINE) else None

    print('milestones: %d/%d  (exit %s)' % (len(passed), len(MILESTONES), code))
    for name, _ in MILESTONES:
        print('  [%s] %s' % ('x' if name in passed else ' ', name))
    for l in last:
        print('  ' + l)
    print('lift: %(lifted)d functions, %(errors)d errors, %(no_terminator)d with no terminator, '
          '%(unresolved_itail)d unresolvable ITAIL targets, %(unimplemented)d UNIMPLEMENTED '
          'instructions; %(ddraw_unimplemented)d DirectDraw methods called but not implemented' % health)

    worse = []
    if base:
        if now['milestones'] < base['milestones']:
            worse.append('milestones %d -> %d' % (base['milestones'], now['milestones']))
        for k in ('errors', 'no_terminator', 'unresolved_itail', 'unimplemented', 'ddraw_unimplemented'):
            if now[k] > base.get(k, now[k]):
                worse.append('%s %d -> %d' % (k, base[k], now[k]))
    if args.update or not base:
        json.dump(now, open(BASELINE, 'w'), indent=1)
        print('baseline written to conformance.json')
    if worse:
        print('REGRESSION: ' + '; '.join(worse))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
