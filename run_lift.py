#!/usr/bin/env python3
"""Virtual Springfield lift driver: VIRTUAL.EXE -> src/recomp/gen/.

Virtual Springfield is one PE image (MSVC 4.2 CRT, linker 4.20, no
protection, no DLLs of its own): DirectDraw, DirectSound and a MIDI stream
are all it asks of Windows (docs/architecture.md). One module, lifted whole:
every catalogued function, no closure limit.

    py -3 tools/catalog.py      # work/functions_virtual.json
    py -3 run_lift.py

docs/architecture.md has the whole pipeline.
"""
import argparse
import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
# PCRECOMP picks the toolkit checkout, the same knob CMakeLists.txt has: the
# lifter and the runtime header must come from the same tree.
_TOOLS = os.path.join(os.environ.get('PCRECOMP', os.path.join(_HERE, '..', 'tools')), 'tools')
sys.path.insert(0, os.path.join(_TOOLS, 'lift'))
sys.path.insert(0, os.path.join(_TOOLS, 'pe'))

from capstone import Cs, CS_ARCH_X86, CS_MODE_32          # noqa: E402
from generate import (EXTENT_REACH, find_splits, true_extent,  # noqa: E402
                      linear_disassemble_function, lift_function_linear, write_chunk)
from lift32 import Lifter                                  # noqa: E402
from pe_analyze import analyze_pe, build_iat_map           # noqa: E402

GAME = os.path.join(_HERE, 'game', 'virtual')
EXE = 'VIRTUAL.EXE'
CATALOG = os.path.join(_HERE, 'work', 'functions_virtual.json')
OUT = os.path.join(_HERE, 'src', 'recomp', 'gen')
STATS = os.path.join(_HERE, 'work', 'lift_stats.json')

# Source patches on the generated C: (VA, what the lifter wrote, what to write
# instead). Each is applied to every copy of that instruction, and a patch
# that matches nothing stops the lift, so a lifter change cannot silently drop
# one.
PATCHES = []
PATCH_DECLS = ''


def apply_patches(out):
    hits = {va: 0 for va, _, _ in PATCHES}
    for fn in sorted(os.listdir(out)):
        if not (fn.startswith('recomp_0') and fn.endswith('.c')):
            continue
        path = os.path.join(out, fn)
        lines = open(path, encoding='utf-8').read().split('\n')
        changed = False
        for i, line in enumerate(lines):
            for va, old, new in PATCHES:
                if ('/* 0x%08X:' % va) not in line:
                    continue
                # A flag-setting instruction is a comment line with its
                # address, then the C that computes the flags: look there too.
                for j in (i, i + 1):
                    if j < len(lines) and old in lines[j]:
                        lines[j] = lines[j].replace(old, new, 1)
                        hits[va] += 1
                        changed = True
                        break
        if changed:
            open(path, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
    missing = [va for va, n in hits.items() if not n]
    if missing:
        sys.exit('patches matched nothing at %s: the lifter output changed, update PATCHES'
                 % ', '.join('0x%08X' % va for va in missing))
    print('[*] %d patches applied at %d sites' % (len(PATCHES), sum(hits.values())))


def lift(path, catalog, md, out, split):
    info = analyze_pe(path)
    iat = build_iat_map(info)
    cs, ce = info.code_start, info.code_end
    cat = json.load(open(catalog))
    byaddr = {f['address']: f for f in cat['functions'] if cs <= f['address'] < ce}
    print('[*] %s: base=0x%08X code=0x%08X-0x%08X IAT=%d catalog=%d'
          % (os.path.basename(path), info.image_base, cs, ce, len(iat), len(byaddr)))

    text = [s for s in info.sections if s.name == '.text'][0]
    code = open(path, 'rb').read()[text.raw_offset:text.raw_offset + text.raw_size]
    # Known targets become RECOMP_CALL; anything else a decoded `call` names
    # becomes RECOMP_ICALL, which reports at run time instead of failing the build.
    lifter = Lifter(iat_map=iat, lifted=set(byaddr))
    starts = {a for a in byaddr if byaddr[a].get('entry_kind') != 'alias'}
    starts -= find_splits(md, code, cs, ce, starts)

    stats = {'lifted': 0, 'errors': 0, 'no_terminator': 0, 'files': 0}
    entries, chunk = [], []
    # A direct branch that leaves a body to an address nothing catalogued is a
    # tail call the catalog missed or a jump into a neighbour's shared code.
    # Either way the target has to be dispatchable, so each round's outside
    # targets become entries of the next.
    todo, added = sorted(byaddr), 0
    while todo:
        outside = set()
        for addr in todo:
            name = 'sub_%08X' % addr
            reached, behind = set(), set()
            end, clean = true_extent(md, code, cs, addr, min(addr + EXTENT_REACH, ce), starts,
                                     reached=reached, behind=behind)
            outside |= {t for t in behind if t not in reached}
            stats['no_terminator'] += not clean
            try:
                lo = min(reached) if reached else addr   # a chunk can sit below the entry
                insns, leaders = (linear_disassemble_function(md, code, cs, lo, end, reached=reached)
                                  if end > addr else ([], None))
                if leaders is not None:
                    leaders.add(addr)
                body = (lift_function_linear(lifter, name, insns, leaders, addr) if insns
                        else 'void %s(void) { }\n' % name)
            except Exception as e:                  # noqa: BLE001 -- counted, not hidden
                body = '/* ERROR %s: %s */\nvoid %s(void) { }\n' % (name, e, name)
                stats['errors'] += 1
            chunk.append((body, addr, name))
            entries.append((addr, name))
            if len(chunk) >= split:
                write_chunk(out, stats['files'], chunk)
                stats['files'] += 1
                chunk = []
        todo = sorted(t for t in outside if cs <= t < ce and t not in byaddr)
        for t in todo:
            byaddr[t] = {'address': t}
        added += len(todo)
    if chunk:
        write_chunk(out, stats['files'], chunk)
        stats['files'] += 1
    stats['lifted'] = len(byaddr)
    print('[*]   %d outside branch targets added' % added)
    return entries, info.image_base + info.entry_point_rva, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', default=GAME, help='folder holding VIRTUAL.EXE')
    ap.add_argument('--out', default=OUT)
    ap.add_argument('--split', type=int, default=400, help='functions per .c file')
    args = ap.parse_args()
    if not os.path.exists(CATALOG):
        sys.exit('no catalog at %s -- run tools/catalog.py first (README, Step by step)' % CATALOG)

    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    os.makedirs(args.out, exist_ok=True)
    for fn in os.listdir(args.out):                 # a smaller lift must not leave stale chunks
        if fn.startswith('recomp_') and fn.endswith('.c'):
            os.remove(os.path.join(args.out, fn))

    t0 = time.time()
    entries, oep, stats = lift(os.path.join(args.game, EXE), CATALOG, md, args.out, args.split)

    with open(os.path.join(args.out, 'recomp_funcs.h'), 'w', newline='\n') as f:
        f.write('/* Virtual Springfield - AUTO-GENERATED by run_lift.py */\n#pragma once\n#include <stdint.h>\n\n')
        f.write('/* host hooks the PATCHES call (src/runtime/mp.c) */\n' + PATCH_DECLS + '\n')
        for a, n in entries:
            f.write('void %s(void);\n' % n)
    with open(os.path.join(args.out, 'recomp_dispatch.c'), 'w', newline='\n') as f:
        f.write('/* Virtual Springfield - AUTO-GENERATED by run_lift.py */\n'
                '#include "recomp_types.h"\n#include "recomp_funcs.h"\n\n'
                'const recomp_dispatch_entry_t recomp_dispatch_table[] = {\n')
        for a, n in sorted(entries):
            f.write('    { 0x%08Xu, %s },\n' % (a, n))
        f.write('};\nconst uint32_t recomp_dispatch_count = %d;\n'
                'const uint32_t vs_entry_va = 0x%08Xu;\n' % (len(entries), oep))

    apply_patches(args.out)
    stats['lines'] = sum(sum(1 for _ in open(os.path.join(args.out, fn), encoding='utf-8',
                                             errors='replace'))
                         for fn in os.listdir(args.out))
    json.dump(stats, open(STATS, 'w'), indent=1)
    print('=' * 60)
    print('  lifted %(lifted)d   errors %(errors)d   no terminator %(no_terminator)d' % stats)
    print('  %s lines of C in %d files, %.1fs' % (format(stats['lines'], ','), stats['files'],
                                                 time.time() - t0))
    print('=' * 60)


if __name__ == '__main__':
    main()
