# Roadmap

The port boots, plays its intro and lets you walk Springfield, in a window
or headless. What follows is in rough order. Each item lands with a
conformance milestone where one can check it.

## Next

- **Play it through.** Walk every location, collect the cards, open and
  close each building, save and load a slot. Each place reached becomes a
  scripted conformance run (`--click` chains), so a regression in a
  location nobody visits by hand still shows.
- **Saves outside the game folder.** The game writes `SAVE\VSn.SAV` in
  place. An option to keep them under `%APPDATA%` would let `game\virtual`
  stay a pristine copy of the disc.
- **Listen to it.** DirectSound and the MIDI stream open and play without an
  error, but nobody has checked them by ear in this port: speech in sync
  with the mouths, music at the right tempo.
- **Headless audio.** A headless run still plays sound on the machine's
  device. It should be silent (or recorded alongside the video).

## Later

- **More presenter.** SimCity 2000's per-effect sliders (CRT strength, glow
  threshold), and xBR next to Scale2x.
- **Upstream the DirectDraw.** `ddraw.c` knows nothing about this game: any
  native32 title written for DirectX 3 to 5 that draws in 8-bit could use
  it. If a second title needs it, it moves to pcrecomp as
  `runtime/native32/ddraw` through a PR.
- **Decode the formats** (`VSA_`, `VSB_`, `VSP_`, the `.VSS` tables) in a
  doc of their own, if a feature ever needs them. The lifted code reads them
  today, so nothing does yet.

## Out of scope

- The Mac version on the same disc.
- Anything from the disc in this repository, ever (REPO_RULES section 3).
