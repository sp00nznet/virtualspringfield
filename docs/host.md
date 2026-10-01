# The host

`src/runtime/host.c` is everything the recompiled game needs from its host
apart from the display ([display.md](display.md)). It maps `VIRTUAL.EXE` at
`0x00400000`, binds its imports through pcrecomp `native32`, and enters the
lifted `WinMain` startup at `0x0041CE00`. Ten imports are answered here
instead of by Windows; this file is why.

## The guest is VIRTUAL.EXE, not the host

`GetModuleHandleA(NULL)`, `GetModuleFileNameA` and `GetCommandLineA` answer
for `game\virtual\VIRTUAL.EXE`: the game loads its icon and strings from its
own `hInstance`, and the real answers would name the host.

## The install check, without an install

At startup the game opens `HKLM\SOFTWARE\Fox Interactive\Virtual Springfield`
and reads the default values of two subkeys with `RegQueryValueA`:

| Subkey | Installer wrote | The game appends |
|---|---|---|
| `HDPATH` | the install folder | `\SAVE\`, the MIDI |
| `CDPATH` | the CD's `VIRTUAL` folder | `\DATA\` |

Then it reads `xFile002`, `xFile003`... and reopens each file named there with
`_lopen`, stopping at the first value that is missing. A value that names a
file it cannot open, or a missing key, ends in *"Installation Error, please
Reinstall. Exiting."* (the check is at `0x00411761`).

The host answers that key itself (`shim_RegOpenKeyA`, `shim_RegQueryValueA`):
both paths are the game folder, and the `xFile` list is empty, which passes.
Nothing is read from or written to the real registry, so a player's own
install of the original, if they have one, is left alone, and no setup step
is needed.

## Active, or waiting

The main loop (`0x00411550`) runs a frame only while the flag at
`0x0042CF80` is set, and otherwise sits in `WaitMessage`. The window
procedure sets it from `WM_ACTIVATEAPP` (message `0x1C`, handled at
`0x00410B4C`). A windowed run gets that from Windows as usual. Headless, the
window is cloaked and never activated, so the first headless run parked in
`WaitMessage` with one frame drawn:

```
[watchdog] 40 s: in sub_00411550, last native call USER32.dll!WaitMessage, 361 indirect calls, 1 frames
```

`ddraw.c` posts one `WM_ACTIVATEAPP(TRUE)` after creating the window, and
drops the deactivations a headless window would otherwise get.

## Input

The game takes the mouse from window messages and polls the keyboard with
`GetAsyncKeyState`. Scripted input follows that:

- `--click X,Y@MS` posts a `WM_MOUSEMOVE`, then `WM_LBUTTONDOWN` and
  `WM_LBUTTONUP` 80 ms apart, at a 640x480 position, MS milliseconds after
  entry, and holds `VK_LBUTTON` for `GetAsyncKeyState` in between.
- `--key NAME@MS[+HOLD]` posts the key down and up and holds it for
  `GetAsyncKeyState`.
- Headless, `GetAsyncKeyState` never reads the real keyboard, so typing on
  the machine cannot steer a recording; windowed, only while the game's
  window has the focus.

## Timing

Animations are paced by the game itself: a busy loop on `timeGetTime` until
the frame's delay from the file has passed (`0x00401F5D`). Some frames hold
for many seconds (a pause in a scene), which shows up in a watchdog dump as
millions of `timeGetTime` calls from `sub_00401D80`. That is the game
waiting, not a hang. The loop is left as it is: it is how the original kept
the speech and the pictures together.

## Faults and stalls

A fault prints `=== fault`, the address read or written, the lifted function
it happened in, the last Windows call, the registers and the last indirect
calls, and stops. None has happened in this port yet.

`--watchdog S` stops a run after S seconds and prints every thread's host
return addresses and the last indirect calls. `py -3 tools\addr2line.py
ADDR...` names host addresses (the generated C and the line). The
conformance run ends this way on purpose: its last milestone is the
watchdog finding the game idle in its message loop at 95 s.
