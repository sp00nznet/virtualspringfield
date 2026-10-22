# Changelog

All notable changes to this project. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [SemVer](https://semver.org/).

## [Unreleased]

## [0.1.0-alpha.1] - 2026-10-22

The first release.

### Added
- **An installer** (`VirtualSpringfield-Recomp-Installer-windows-x64.exe` on
  each release): recomp-launcher 0.3.0 with `launcher/launcher.json`, the
  same as gunman and Theme Park. Point it at the CD, or a folder holding the
  game, its `.cue`/`.iso` or a zip of it; it downloads this repository and
  pcrecomp, runs the setup, and leaves a Play button and desktop shortcuts.
- `Setup.cmd` runs unattended for it: `-Yes` installs what is missing and
  stops with a reason instead of asking where the game is, `-Game`/`-GameDir`
  takes the game, and `RECOMP_LAUNCHER=1` skips the final pause. pcrecomp is
  found at `$PCRECOMP`, `../tools` or `../pcrecomp` (CMake, `run_lift.py` and
  `catalog.py` too).
- `tools/gamefiles.py` takes a folder holding the zip, `.cue` or `.iso`.
- The presenter (`src/runtime/present.c`): the picture in a resizable
  Direct3D 11 window with a Video menu and `virtualspringfield.ini`. Sharp,
  smooth, nearest and integer scaling, a CRT look and dithering from Hover!
  and gunman; Scale2x and glow from SimCity 2000; borderless fullscreen (F11,
  Alt+Enter); clicks mapped back to 640x480 at any size; an option to keep
  running in the background.
- The whole of `VIRTUAL.EXE` recompiled to C with pcrecomp (`disasm32`,
  `generate`, `lift32`): 832 functions, 0 lift errors, on pcrecomp
  `86fe9f5` with no toolkit change.
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

### Changed
- pcrecomp is pinned to `86fe9f5`, the commit the 11/11 baseline was made
  on: the installer fetches it, and `Setup.cmd` checks it out when it clones.
- The lift and the build run on every setup, so an update reaches the exe.

### Fixed
- The game stalled after the logos when its folder had a long path (a
  144-character one scored 9/11). The host hands it the folder's 8.3 name
  ([docs/host.md](docs/host.md)).

[Unreleased]: https://github.com/sp00nznet/virtualspringfield/compare/v0.1.0-alpha.1...HEAD
[0.1.0-alpha.1]: https://github.com/sp00nznet/virtualspringfield/releases/tag/v0.1.0-alpha.1
