# Security

## What the program touches

- **Files.** `build\virtualspringfield.ini` beside the exe (the presenter's
  settings). The game reads its data from `game\virtual` and writes its
  twelve save slots in place, in `game\virtual\SAVE`, as the original did.
  `tools\gamefiles.py` reads the disc, image or zip you give it and writes
  only under `game\virtual` and a temporary folder in `work\`, which it
  deletes.
- **The registry.** Nothing. The game's own registry reads (its install
  paths) are answered by the host, so the real registry is neither read for
  them nor written ([docs/host.md](docs/host.md)).
- **Processes.** `--record` starts `ffmpeg` from `PATH`. `Setup.cmd` asks
  before it installs anything (Python, two pip packages, the Visual Studio
  Build Tools, a clone of pcrecomp) and says what each is.
- **The network.** The program itself makes no connections. `Setup.cmd` uses
  the network only for the installs and the clone above, after asking.

It handles no credentials.

## How it runs code

The game's code is recompiled C running in-process, and it calls the real
Win32 API with the game's own arguments. The animation, script and save
files are parsed by the game's 1997 code, so treat those files from
untrusted sources, a save slot included, with the caution due any old
program.

## Reporting

Report a problem privately through GitHub's *Report a vulnerability* on this
repository, rather than in a public issue.
