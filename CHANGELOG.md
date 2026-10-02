# Changelog

All notable changes to this project. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [SemVer](https://semver.org/).

## [Unreleased]

### Added
- The presenter (`src/runtime/present.c`): the picture in a resizable
  Direct3D 11 window with a Video menu and `virtualspringfield.ini`. Sharp,
  smooth, nearest and integer scaling, a CRT look and dithering from Hover!
  and gunman; Scale2x and glow from SimCity 2000; borderless fullscreen (F11,
  Alt+Enter); clicks mapped back to 640x480 at any size; an option to keep
  running in the background.
- The whole of `VIRTUAL.EXE` recompiled to C with pcrecomp (`disasm32`,
  `generate`, `lift32`): 832 functions, 0 lift errors. Needs pcrecomp `main`,
  no toolkit change.
- A 32-bit host on pcrecomp `native32` that maps the original exe, binds its
  109 imports (10 shimmed) and runs only lifted code.
- The host's own DirectDraw (`src/runtime/ddraw.c`): the game's exclusive
  640x480x8 mode becomes an ordinary window scaled to fit, a recording, or
  nothing at all (`--headless`).
- The install check passes with no installer and no registry: the host
  answers `HDPATH` and `CDPATH` with the game folder.
- `--headless`, `--record`, `--shot`, `--diff`, `--click`, `--key`,
  `--watchdog`, `--scale`.
- `tools/gamefiles.py`: the game from a CD, a folder, a zip, or a BIN/CUE/ISO
  (the hybrid disc's doubled directory entries handled).
- `Setup.cmd`: checks and offers to install the prerequisites, copies the
  game, lifts, builds, and leaves a shortcut.
- Conformance harness: 11/11 milestones, from boot to the area map opening
  on a scripted click.
