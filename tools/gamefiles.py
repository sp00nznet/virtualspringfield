#!/usr/bin/env python3
r"""Put your copy of Virtual Springfield's files in game/virtual/, from wherever they are.

    py -3 tools/gamefiles.py E:\                         # the CD in a drive
    py -3 tools/gamefiles.py "Virtual Springfield.cue"   # a BIN/CUE dump, or a 2048-byte ISO
    py -3 tools/gamefiles.py VirtualSpringfield.zip      # a zip holding the folder or the disc image
    py -3 tools/gamefiles.py D:\games\VIRTUAL            # a folder holding VIRTUAL.EXE and DATA\
    py -3 tools/gamefiles.py                             # look in every drive

The game is the disc's VIRTUAL folder: VIRTUAL.EXE, DATA\ (about 610 MB of
animation, sound and MIDI) and SAVE\. The original installer copied only
VIRTUAL.EXE, the MIDI and SAVE\ to the hard disk and read DATA\ from the CD;
here everything sits in one folder, and the host tells the game so (no
installer, no registry). REDIST\ (DirectX 3) is not needed and not copied.

The disc is a Mac/PC hybrid, and its ISO directory lists some files twice:
the larger entry is the data, the other a stub. Disc images are read with
pcrecomp's ISO9660 walker (tools/assets/iso_peek.py), so nothing is mounted.

It supplies your own copy to the local build; nothing is downloaded, and none
of it is ever committed (README, "What is not in this repo").
"""
import os
import shutil
import string
import sys
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'game', 'virtual')
NEEDED = ('VIRTUAL.EXE', 'DATA/MASTER.VSP', 'DATA/OPENING.VSS', 'DATA/VIRTUAL.VSS')
SKIP = ('REDIST/',)


def complete(files):
    """Does this set of relative paths (any case, '/' separated) hold the game?"""
    have = {f.upper() for f in files}
    return all(n in have for n in NEEDED)


def pick(paths):
    """The prefix ('' or 'a/b/') under which the game sits, or None."""
    for p in sorted(paths, key=len):
        if p.upper().endswith('VIRTUAL.EXE'):
            pre = p[:-len('VIRTUAL.EXE')]
            if complete(q[len(pre):] for q in paths if q.upper().startswith(pre.upper())):
                return pre
    return None


def wanted(rel):
    return not rel.upper().startswith(SKIP)


def write(rel, data):
    dst = os.path.join(OUT, *rel.split('/'))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, 'wb') as f:
        f.write(data)


def from_image(path):
    sys.path.insert(0, os.path.join(os.environ.get('PCRECOMP', os.path.join(ROOT, '..', 'tools')),
                                    'tools', 'assets'))
    import iso_peek

    class RawReader(iso_peek.Reader):
        """ISO offsets over a raw MODE1/2352 BIN: sector n's 2048 bytes sit 16
        bytes into raw sector n (12 sync + 4 header), 2352 bytes apart."""

        def read(self, off, size):
            out = bytearray()
            while size > 0:
                sec, within = divmod(off, 2048)
                take = min(size, 2048 - within)
                self.fh.seek(sec * 2352 + 16 + within)
                out += self.fh.read(take)
                off += take
                size -= take
            return bytes(out)

    if path.lower().endswith('.cue'):
        for line in open(path, errors='replace'):     # the data track is the first FILE line
            if line.strip().upper().startswith('FILE'):
                path = os.path.join(os.path.dirname(path), line.split('"')[1])
                break
    size = os.path.getsize(path)
    raw = size % 2352 == 0 and size % 2048 != 0
    reader = (RawReader if raw or path.lower().endswith(('.bin', '.img')) else iso_peek.Reader)(path)
    files = {}
    for p, off, n in iso_peek.walk(reader):
        if p not in files or n > files[p][1]:          # hybrid disc: the larger twin is the data
            files[p] = (off, n)
    pre = pick(list(files))
    if pre is None:
        return False
    take = [p for p in files if p.startswith(pre) and wanted(p[len(pre):])]
    print('reading %d files (%d MB) from %s at %s' % (
        len(take), sum(files[p][1] for p in take) >> 20, path, pre or '/'))
    for p in take:
        off, n = files[p]
        write(p[len(pre):], reader.read(off, n))
    return True


def from_zip(z, label):
    names = [n for n in z.namelist() if not n.endswith('/')]
    pre = pick(names)
    if pre is not None:
        take = [n for n in names if n.startswith(pre) and wanted(n[len(pre):])]
        print('reading %d files from %s%s' % (len(take), label, '!' + pre if pre else ''))
        for n in take:
            write(n[len(pre):], z.read(n))
        return True
    # archive.org keeps the disc as a BIN/CUE or ISO inside the zip. A disc
    # image needs seeking, so it is unpacked to a temporary folder first.
    images = [n for n in names if n.lower().endswith(('.bin', '.iso', '.img'))]
    for n in sorted(images, key=lambda n: -z.getinfo(n).file_size):
        tmp = tempfile.mkdtemp(prefix='vs-disc-', dir=os.path.join(ROOT, 'work'))
        try:
            print('unpacking %s from %s (%d MB)' % (n, label, z.getinfo(n).file_size >> 20))
            path = z.extract(n, tmp)
            if from_image(path):
                return True
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return False


def from_folder(src):
    for top, dirs, files in os.walk(src):
        if top[len(src):].count(os.sep) > 3:   # a few levels down is enough (E:\VIRTUAL)
            dirs[:] = []
            continue
        if any(f.upper() == 'VIRTUAL.EXE' for f in files):
            rel = [os.path.relpath(os.path.join(t, f), top).replace(os.sep, '/')
                   for t, _, fs in os.walk(top) for f in fs]
            if complete(rel):
                print('copying %s' % top)
                shutil.copytree(top, OUT, dirs_exist_ok=True,
                                ignore=lambda d, names: [n for n in names if n.upper() == 'REDIST'])
                return True
    return False


def main():
    src = sys.argv[1].strip('"') if len(sys.argv) > 1 else ''
    os.makedirs(os.path.join(ROOT, 'work'), exist_ok=True)
    if not src:
        drives = ['%s:\\' % c for c in string.ascii_uppercase if os.path.exists('%s:\\' % c)]
        for d in drives:
            if os.path.isfile(os.path.join(d, 'VIRTUAL', 'VIRTUAL.EXE')) and from_folder(os.path.join(d, 'VIRTUAL')):
                break
        else:
            sys.exit('no drive holds the Virtual Springfield CD; pass a drive, folder, zip or disc image')
    elif os.path.isdir(src):
        if not from_folder(src):
            sys.exit('%s does not hold VIRTUAL.EXE with DATA\\ beside it (an installed copy has no DATA\\: '
                     'use the CD or a disc image)' % src)
    elif zipfile.is_zipfile(src):
        with zipfile.ZipFile(src) as z:
            if not from_zip(z, src):
                sys.exit('%s is a zip, but Virtual Springfield is not in it' % src)
    elif os.path.isfile(src):
        if not from_image(src):
            sys.exit('%s is not a disc image holding Virtual Springfield' % src)
    else:
        sys.exit('no such drive, folder or file: %s' % src)
    if not complete(os.path.relpath(os.path.join(t, f), OUT).replace(os.sep, '/')
                    for t, _, fs in os.walk(OUT) for f in fs):
        sys.exit('copied, but %s is still missing a file the game needs' % OUT)
    print('done: %s' % OUT)


if __name__ == '__main__':
    main()
