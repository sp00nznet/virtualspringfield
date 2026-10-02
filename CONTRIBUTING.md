# Contributing

This is a recompilation project, which changes what a useful contribution looks
like. Three rules matter more than the rest.

## No game files, ever

Nothing from Virtual Springfield goes in the repository, in any form. That
means no executable, animation, sound, MIDI or save file, and nothing
regenerated from one: no lifted source, disassembly listing, function
catalog, reconstructed header or format dump, or test file with a lifted
function in it.

The tool ships; the game does not. Everyone brings their own copy, and
`Setup.cmd` points the tools at it. `.gitignore` covers `game/`, `work/` and
`src/recomp/gen/`. If something slips past it, that is a bug worth reporting
on its own.

Screenshots and recordings of the game running are fine, and are the point of
the README.

## Where your code comes from

Contributions have to be your own work or under a licence compatible with MIT.
The live risk is a fix ported from a GPL or LGPL project, which would
relicense it by accident and is very hard to untangle later. The ones most
likely to be open next to this are **Wine** (LGPL), whose `ddraw` covers the
same ground as `src/runtime/ddraw.c`, and **DxWnd** (GPL), which wraps old
DirectDraw games in a window. Reading such code to understand a behaviour is
fine; copying code from it is not. If something in your PR came from
somewhere, say where.

## Claims are measured, not assumed

`py -3 tools\conformance.py` has to pass before and after your change. A
change that fixes a behaviour should say what the original does in the same
scenario: a `--headless --record` run with `--click` input shows both. A
change to the lifter or the runtime it shares belongs in
[pcrecomp](https://github.com/sp00nznet/pcrecomp), as a PR there.

## The usual

- Imperative commit subjects; the body explains *why* when it is not obvious.
- Community pull requests are merged with a merge commit, never squashed or
  rebased, so your commits stay yours. Anything the maintainer adds goes in
  separate commits on top.
- Comments explain the reasoning, not the syntax: a comment recording how
  something was found out is worth more than one restating the line under it.
- AI-assisted contributions are welcome, provided a human understood and
  verified the change: ran it, and can say what it does.
