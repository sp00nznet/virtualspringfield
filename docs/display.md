# The display: the host's own DirectDraw

`src/runtime/ddraw.c` answers the game's `DirectDrawCreate` with an
`IDirectDraw` implemented in the host. Nothing of the system's `ddraw.dll`
is loaded.

## Why not the real one

The game asks for what a 1997 card did well and a 2026 desktop does badly:

```
[ddraw] SetCooperativeLevel(..., 00000011)        DDSCL_EXCLUSIVE | DDSCL_FULLSCREEN
[ddraw] SetDisplayMode(640x480x8)
[ddraw] CreateSurface(caps 00000218, 640x480x8, 1 back buffer)   primary + flip chain
[ddraw] CreateSurface(caps 00004040, 640x240x8)                  off-screen, system memory
[ddraw] CreateSurface(caps 00000040, 320x200x8)                  off-screen
```

On current Windows an exclusive 8-bit mode is emulated by the compatibility
layer at best, takes over every monitor, and cannot be captured: from an RDP
session with no display it does not exist at all. Headless recording
(REPO_RULES section 10) and a window you can move both need the picture to be
in memory the host owns.

## What it is

Every surface is a DIB section in the host process. Guest and host share one
32-bit address space (native32 maps the guest 1:1), so the pointer `Lock`
returns is one the lifted code writes through directly, and `GetDC` works on
any surface because GDI already understands a DIB.

- **Flip** swaps the front and back buffers' pixels, as the hardware swapped
  scan-out addresses.
- **Blt / BltFast**: copies, colour fills, source colour keys, and a
  nearest-neighbour stretch (8-bit).
- **Palette**: `SetEntries` on the primary's palette is a present of its
  own, because the game fades by palette alone.
- **SetDisplayMode** accepts 640x480 at 8 or 16 bits and only remembers it.
- **WaitForVerticalBlank** sleeps to the next 60 Hz tick.

Every method the game does not call logs `[ddraw] Name: not implemented`
and fails. The conformance harness counts those lines, so a new call shows up
as a regression rather than as a fault somewhere else. Today the count is 0.

## Presenting

A present (a flip, a blit or unlock on the primary, a palette change, a GDI
draw on the primary) converts the primary through its palette into a 640x480
BGRA shadow. From there:

- **Windowed** (`--run`): `StretchDIBits` into the game's window. The window
  was a borderless popup the size of the screen; the host gives it a caption
  and a client area of 640x480 times the scale (the largest that fits the
  work area, or `--scale N`), and divides mouse coordinates back down, so
  the game still sees 640x480.
- **`--record out.mp4`**: the shadow goes to ffmpeg at a fixed 30 fps against
  the wall clock, from a thread of its own, so a still picture waiting for a
  click still advances the video.
- **`--headless`**: the window is cloaked (DWM composes it nowhere, an RDP
  session included), never activated, and kept off the taskbar. Nothing is
  drawn to it; the shadow is the picture.
- **`--shot N:file.bmp`** saves present N; **`--diff A,B`** prints how much
  of the screen changed between A and B milliseconds after start. By the
  clock, not by frame: the game presents in bursts while an animation runs
  and not at all while it waits.

## Limits

- 8-bit and RGB565 surfaces only; the game uses 8-bit.
- The stretch blit is 8-bit and unclipped beyond the surfaces' edges. The
  game's stretches are all on screen.
- The window is scaled by `StretchDIBits` with nearest-neighbour sampling,
  so a fractional scale would be uneven. The automatic scale is a whole
  number.
