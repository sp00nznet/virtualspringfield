# The presenter

`src/runtime/present.c`. The game's 640x480 picture in its window, scaled on
the GPU: any window size, borderless fullscreen, five filters, a CRT look,
glow, retro dithering and a vivid colour look. It is what every windowed run
uses; headless runs have no window to draw in and skip it.

It is [Hover!](https://github.com/sp00nznet/hover)'s presenter (which is
[gunman](https://github.com/sp00nznet/gunman)'s), with two passes from
[SimCity 2000](https://github.com/sp00nznet/simcity2000)'s frontend added:
Scale2x and glow.

## Why it draws into the game's own window

Hover!'s game fought any resize of its frame, so its presenter is a second
window that the game never sees. Here there is nothing to fight: the game's
window was a fullscreen popup made for a 640x480 display, and the host's
DirectDraw ([display.md](display.md)) already owns what it shows. So the
presenter turns that window into an ordinary resizable one with a **Video**
menu, and draws into it:

- **Picture.** `ddraw.c` converts the primary surface through its palette
  into a 640x480 BGRA shadow at every present and hands a copy to
  `present_frame`. The presenter's thread uploads it and draws with
  Direct3D 11: WARP when there is no GPU, one GDI `StretchDIBits` when there
  is no Direct3D at all. The game thread never waits on the GPU.
- **Mouse.** The picture is letterboxed at 4:3 (pillarboxed in fullscreen
  on a 16:9 screen). Every mouse message is mapped from the window's client
  area back to 640x480 before the game sees it, so clicks land where the
  pointer is at any size.
- **Keys.** F11 or Alt+Enter toggles borderless fullscreen; Esc leaves it.
  The game sees every other key as before.
- **Focus.** The game stops when it loses activation, as the original did on
  alt-tab. *Video > Pause when in the background* off keeps it running (the
  host drops the deactivation, as it does headless).

## Options

*Video* menu, or `[video]` in `build\virtualspringfield.ini` (written with
these defaults on the first windowed run):

| Option | Values | |
|---|---|---|
| `filter` | `sharp` (default), `smooth`, `nearest`, `integer`, `scale2x` | sharp-bilinear keeps pixels crisp and blends only their edges (gunman); integer scales by whole multiples only; Scale2x (EPX) rounds diagonal staircases on line art (SimCity 2000) |
| `scale` | 0-8 | window size, times 640x480; 0 = the largest whole number that fits the work area. `--scale N` overrides it for one run |
| `fullscreen` | 0/1 | borderless on the window's monitor |
| `crt` | 0/1 | scanlines (fading in from 1.5x to 3x, where they stop beating against the pixel grid), an aperture-grille mask, vignette |
| `curvature` | 0/1 | the CRT's barrel |
| `glow` | 0/1 | bright, saturated colours bloom a little |
| `dither` | `off`, `16bit`, `8bit` | ordered (Bayer 4x4) dithering per game pixel: a High Color desktop, or the 216-colour web palette |
| `vivid` | 0/1 | more saturation and a little contrast |
| `pause_in_background` | 0/1 | the original's stop when the window loses the focus |

## Glow, in one pass

SimCity 2000 blurs a bright-pass texture in two separate passes. This
picture is 640x480, so the presenter does it in the one pixel shader: 24
taps on three rings around each pixel, of the bright, saturated part of the
picture only. The ceiling is a wide or very soft glow, which would need the
two-pass blur back.

## Checked

The shaders compile with `d3dcompiler_47` (vs_4_0, ps_4_0); the headless
conformance run is unchanged at 11/11 (headless never starts the
presenter). Windowed, on a 1920x1080 offstage monitor at the console, each
run to Town Square with a scripted click on MAP at 75 s:

| Settings | Result |
|---|---|
| fullscreen, sharp, CRT + curvature | pillarboxed 4:3, scanlines and barrel; the click opens the area map |
| windowed, sharp, glow | about 2x (the fractional fit to the work area); the click opens the area map |
| windowed, Scale2x, vivid | the same size; the click opens the area map |

Two things those runs taught:

- **Scripted clicks are in game coordinates.** `--click X,Y` used to post
  X,Y as they were, and the presenter then mapped them a second time as
  window coordinates: in fullscreen the pointer landed top-left and the map
  never opened. `present_unmap` now puts a scripted click where a real one
  would be.
- **The background pause is real.** With `pause_in_background=1` a run
  stopped after 82 frames, in `WaitMessage`: the game window lost the focus
  (most likely to someone using another screen at the time) and the game
  paused, exactly as the original would have. Unattended runs set it to 0.
