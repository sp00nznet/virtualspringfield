# Architecture

## The game

*The Simpsons: Virtual Springfield* (Fox Interactive, 1997; the intro
credits Vortex Media Arts, whose installer and file layer it uses) is one PE image built with MSVC 4.2 (linker 4.20, timestamp
1997-08-14). No packer, no copy protection, no DLLs of its own.

| File | What it is |
|---|---|
| `VIRTUAL.EXE` | The whole program: 197 KB, 160 KB of code. A plain `WinMain` with a `PeekMessage` loop, DirectDraw for the picture, DirectSound for speech and effects, a `midiStream` player for the music, and 109 imports from 7 system DLLs. It also exports 17 `v*` functions (`vOpen`, `vRead`, `vRegisterCollection`...): Vortex Media Arts' file layer, which nothing outside the exe calls |
| `DATA\*.VSA`, `VSP0NN\*.VSB`, `MASTER.VSP` | Vortex's own containers (magic `VSA_`, `VSB_`, `VSP_`): animation frames as FLIC-style chunks (frame chunk `0xF1FA`) with sound chunks interleaved, tagged by their sample rate (`0x5622` = 22,050 Hz). About 4,200 files, 590 MB |
| `DATA\VS3D\*.VSS`, `OPENING.VSS`, `VIRTUAL.VSS` | Small tables, one per place and facing (`1-01E`, `1-01S`...), and the opening sequence's. Not decoded here: the lifted code reads them as it always did |
| `DATA\TRACK*.MID` | The music, played through `midiStream*` |
| `SAVE\VS1.SAV`...`VS12.SAV` | Twelve save slots, written in place |
| `DATA\QUICKTIM\`, `REDIST\` | QuickTime for the Mac side of the hybrid disc, and DirectX 3a. Neither is used |

The original installer put `VIRTUAL.EXE`, the MIDI and `SAVE\` on the hard
disk and recorded two paths in the registry (`HDPATH`, `CDPATH`); `DATA\`
stayed on the CD. Here the whole `VIRTUAL` folder is copied to
`game\virtual`, and the host answers both paths with it ([host.md](host.md)).

## The pipeline

```
your disc / .cue / .zip ─ tools\gamefiles.py ─ game\virtual\VIRTUAL.EXE ─ tools\catalog.py ─ work\functions_virtual.json
                          (pcrecomp iso_peek)                            (pcrecomp disasm32)          │
                                                                                                    run_lift.py
                                                                                     (pcrecomp generate + lift32)
                                                                                                       │
src\runtime\host.c + ddraw.c + pcrecomp runtime\native32 ─── build.cmd ──── src\recomp\gen\recomp_000N.c, recomp_dispatch.c
                                                                │
                                                     build\virtualspringfield.exe
```

1. **`tools/gamefiles.py`** copies the disc's `VIRTUAL` folder (less
   `REDIST`) into `game\virtual`, from a drive, a folder, a zip, or a
   BIN/CUE/ISO read with pcrecomp's ISO9660 walker. The disc is a Mac/PC
   hybrid whose directory lists some files twice; the larger twin is the data.
2. **`tools/catalog.py`** runs pcrecomp `disasm32`: the entry point and the 17
   exports are the seeds, the rest is recursive descent, prologues and a data
   scan. 793 functions, 68.4% of the code bytes; the rest is the CRT's unused
   parts, data in `.text`, and padding.
3. **`run_lift.py`** lifts every catalogued function with pcrecomp
   `generate` + `lift32` into one dispatch table. A direct branch to an
   address the catalog lacks becomes an entry of the next round (39 of them),
   so every `RECOMP_ITAIL` resolves: 832 functions, 0 errors, 201K lines of C.
4. **`build.cmd`** compiles the generated C, the host and pcrecomp's
   `native32`, `image_loader` and `recomp_trace` into one 32-bit executable,
   linked at `0x60000000` so the guest's `0x00400000` is free.

The lift needs no toolkit change: pcrecomp `main` as it stands.

## At run time

`build\virtualspringfield.exe` is a 32-bit process holding `VIRTUAL.EXE` at
its own base, mapped by hand, and running only lifted code (the guest `.text`
is mapped non-executable).

- **Guest → Windows.** A lifted `call [iat]` reaches native32's bridge, which
  calls the real function with the guest's stack slots. 99 of the 109 imports
  go straight to Windows; 10 are shimmed in the host (11 headless).
- **Windows → guest.** The window procedure and the `midiStream` callback
  fault on the non-executable guest code, and native32's handler enters the
  lifted function.
- **DirectDraw** is the host's own ([display.md](display.md)): the game's
  `DirectDrawCreate` gets an object implemented in `src/runtime/ddraw.c` over
  memory surfaces, so the 8-bit fullscreen mode becomes a window, a
  recording, or nothing at all.
- **DirectSound and MIDI** go to the real devices, through the same bridge
  (COM methods included: native32 measures each callee's stack purge).

Everything the host changes about the game's view of the world is in
`src/runtime/host.c` and `src/runtime/ddraw.c`, and why is in
[host.md](host.md) and [display.md](display.md).
