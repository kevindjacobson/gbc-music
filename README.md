# gbc-music

Four-channel music for the Game Boy Color, from a one-line idea to a cartridge ROM, a MIDI file and a WAV.

- A **driver** in C (GBDK-2020) that plays tracker-style song tables on the four hardware voices: arpeggiated
  chords, echo, trills, resolving bends, portamento, duty and wavetable sequences, level envelopes, a drum kit,
  and a contract that lets sound effects borrow a channel and hand it back.
- A **plain-text score format** (one block per bar, four lanes of sixteenth-note cells) and a **compiler** that turns
  a score into C tables.
- A **deterministic generator**: style, key, tempo, bar count and seed in; a whole song out, with song forms
  (stage loop, verse-chorus, AABA, twelve-bar blues), a progression library in Roman numerals, two textures and an
  "organic" layer that keeps a machine-written song from sounding like one.
- **Three outputs from one score**: a `.gbc` player ROM for real hardware or any emulator, a General MIDI `.mid`
  for a DAW, and a `.wav` / `.mp3` rendered through a cycle-exact emulation of the chip.
- A **listener** that runs the ROM headlessly, isolates each channel and reports what actually sounds, plus an
  interactive piano roll for web pages.

Fair warning: this skill is opinionated, and it was written by a simpleton. Every rule in it is a measured fact
or a listening verdict, stated as a default rather than a menu. The score is plain text and the scripts are small,
so when your ears disagree, change the score. MIT licensed.

## Dependencies

| for | you need |
|---|---|
| `compose.py` (generate, compile, split, events), `song_midi.py` | Python 3.11 or newer; standard library only |
| `song_rom.py` (the player ROM), building a game | [GBDK-2020](https://github.com/gbdk-2020/gbdk-2020) 4.x with `GBDK_HOME` set to the directory that contains `bin/lcc`, and `make` |
| `song_wav.py`, `audio_probe.py` | `pip install pyboy numpy` (PyBoy is the emulator that renders and listens) |
| `audio_probe.py --out` piano-roll PNG | `pip install Pillow` |
| `song_wav.py --mp3` | `lame` or `ffmpeg` on PATH |

Linux, macOS and Windows (WSL or a native Python with GBDK's Windows build) all work; the scripts shell out only
to `make` and the GBDK compiler.

## Installation

```
git clone https://github.com/kevindjacobson/gbc-music.git
export SKILL=$PWD/gbc-music                     # the scripts are addressed as $SKILL/scripts/<name>.py
export GBDK_HOME=/path/to/gbdk                  # the directory that holds bin/lcc (GBDK-2020 4.x)
python -m venv .venv && . .venv/bin/activate
pip install pyboy numpy Pillow                  # only for the WAV output and the listener
python $SKILL/scripts/compose.py styles         # lists styles, forms, progressions, waves and drums: the install works
```

The scripts find each other next to themselves. If you copy them somewhere else, set `GBC_MUSIC_DIR` to the skill
directory (or its `scripts/`), or keep them in a `scripts/` directory under your working directory. `song_rom.py`
looks for GBDK in `$GBDK_HOME`, then `lcc` on PATH, then `/opt/gbdk`, `/usr/local/gbdk`, `~/gbdk`, `~/gbdk-2020`.

## Quick start: a song, a ROM, a MIDI file and a WAV in five commands

```
mkdir demo && cd demo
python $SKILL/scripts/compose.py generate --style fusion --key F# --bpm 100 --bars 32 --seed 7 --organic 2 --out main.txt
python $SKILL/scripts/song_rom.py main.txt --out main.gbc
python $SKILL/scripts/song_midi.py main.txt --out main.mid
python $SKILL/scripts/song_wav.py main.txt --out main.wav --mp3
python $SKILL/scripts/audio_probe.py --rom main.gbc --out probe --pre wait:60 --seconds 10
```

You get `main.txt` (the score, yours to edit), `main.gbc` (32 KB; boots into the song with a title screen and a
live bar counter, START/SELECT cycle songs), `main.mid` (one track per voice, chords expanded, bends as pitch bend),
`main.wav` and `main.mp3` (the chip itself at 32768 Hz), and `probe/audio_report.json` plus `probe/pianoroll.png`
(four channels active, a few hundred pitch changes in ten seconds). Every script prints a final JSON line with its
numbers, so a pipeline or an agent can read them.

## Usage examples

**Put a song in your own GBDK game.** Copy `scripts/music.c` and `music.h` into your `src/`, compile the score next
to them, call the driver from your loop:

```
python $SKILL/scripts/compose.py generate --style rock --key E --bpm 146 --bars 24 --seed 3 --organic 2 --out music/main.txt
python $SKILL/scripts/compose.py compile music/main.txt --out src/music_data.c      # also writes src/music_data.h
```
```c
#include "music.h"
#include "music_data.h"                 /* extern const Song song_main; */
/* at boot, once: */   NR52_REG = 0x80; NR50_REG = 0x77; NR51_REG = 0xFF;
/* on the title: */    music_init(&song_main);
/* every frame: */     wait_vbl_done(); /* your effects */ music_tick();
/* in a sound effect, before writing registers: */ music_sfx(MUSIC_CH1 | MUSIC_CH4, 18);
/* under a sting: */   music_set_volume(6);   /* back to 15 afterwards; music_stop() silences everything */
```
Then listen to the build: `python $SKILL/scripts/audio_probe.py --rom build/game.gbc --out qa/audio --seconds 10`
must report at least two channels active and real pitch changes after START. `docs/INTEGRATION.md` is the full
contract (what the game owns, what the driver owns, the SFX hand-over, memory).

**Choose a form and a progression.** Form and texture are independent knobs; `compose.py styles` lists everything.

```
python $SKILL/scripts/compose.py generate --style pop  --key C --bpm 120 --bars 48 --seed 1 --progression axis --out song.txt      # verse-chorus, I V vi IV
python $SKILL/scripts/compose.py generate --style rock --key E --bpm 146 --bars 28 --seed 3 --texture fusion --out stage.txt       # a stage loop with fusion idioms
python $SKILL/scripts/compose.py generate --style rock --key A --bpm 112 --bars 40 --seed 5 --form blues12 --out blues.txt
python $SKILL/scripts/compose.py generate --style fusion --key F# --bpm 100 --bars 32 --seed 7 --form aaba --out title.txt
python $SKILL/scripts/compose.py generate --style ambient --key D --bpm 84 --bars 16 --seed 2 --bend none --out bed.txt            # a quiet bed
python $SKILL/scripts/compose.py generate --style pop --key G --bpm 128 --bars 48 --seed 9 --progression "I bVII IV I" --out own.txt   # your own numerals
```

**Make it breathe, then edit it.** `--organic 2` varies repeats, adds rests, fills, accents and per-section timbre
changes deterministically; the score it writes is the starting point for a hand edit (let the lead sit out a bar,
change the second ending, reshape a fill). `docs/SCORE_FORMAT.md` has every cell; `SKILL.md` §2 the ones you will
actually touch.

**A player cartridge with several songs.** Up to nine scores on one ROM; START/SELECT cycle them, A restarts,
B ducks:

```
python $SKILL/scripts/song_rom.py title.txt stage.txt bed.txt --out jukebox.gbc --title "MY SONGS"
```

**MIDI for a DAW, WAV for a release note.**

```
python $SKILL/scripts/song_midi.py song.txt --out song.mid            # GM programs per lane, bends as pitch bend, arpeggios expanded
python $SKILL/scripts/song_wav.py song.txt --out song.wav --mp3 --loops 2
```

**A piano roll that follows the audio on a web page.** `compose.py events` writes every note with its time in
seconds; `scripts/pianoroll.js` draws it as an animated, zoomable roll whose playhead follows an `<audio>` element.

```
python $SKILL/scripts/compose.py events song.txt --out song_events.json --offset 0
```
```html
<audio id="a1" controls src="song.mp3"></audio>
<figure data-pianoroll data-events="#ev1" data-audio="#a1" data-offset="0"></figure>
<script type="application/json" id="ev1">{ ...song_events.json... }</script>
<script src="pianoroll.js"></script><script>GbcPianoRoll.mountAll();</script>
```
`docs/PIANOROLL.md` has the API; a page that holds several songs should pause the others when one plays.

**Split a piece across two Game Boys.** `compose.py split` writes one score per part (for example lead + chord on
one cartridge, bass + drums on another) that share tempo, length and loop exactly, so two consoles or two emulator
cores run in lockstep. `docs/OUTPUTS.md` has the details.

## Using it as an agent skill

`SKILL.md` is the instruction file a coding agent reads; it follows the Agent Skills layout (a directory with a
`SKILL.md` whose front matter carries `name` and `description`, scripts under `scripts/`, documents under `docs/`).
Install by placing or symlinking this directory where your harness looks for skills:

| harness | where |
|---|---|
| Claude Code | `.claude/skills/gbc-music/` in the project, or `~/.claude/skills/gbc-music/` for every project |
| OpenCode | `.opencode/skills/gbc-music/` in the project (or the global OpenCode config directory's `skills/`) |
| Codex CLI | `~/.codex/skills/gbc-music/` |
| anything else (Cursor, Gemini CLI, Aider, a chat window) | point the agent's rules file (`AGENTS.md`, `.cursor/rules`, a system prompt) at `SKILL.md`, or paste it; the scripts need only Python and the dependencies above |

`SKILL.md` refers to `$SKILL` as the directory it lives in and uses generic project paths (`music/main.txt`,
`src/music_data.c`, `build/<game>.gbc`, `qa/`); tell the agent where those are in your project, or let it map them.

## Documentation

`docs/README.md` is the index. In short: `SCORE_FORMAT.md` (the complete grammar), `CLI.md` (every flag, generated
from `--help`), `OUTPUTS.md` (ROM integration, player ROM, MIDI mapping, WAV), `INTEGRATION.md` (the driver's
contract), `DESIGN_NOTES.md` (the measured facts behind the rules), `EXAMPLES.md` (worked examples with the numbers
they produced; `docs/check_examples.py` runs them), `TROUBLESHOOTING.md`, `LIMITS.md`, `PIANOROLL.md`,
`PRESENTATION.md` (a ten-minute demo script), `LICENSE.md` (provenance).

## Layout

```
SKILL.md          the agent-facing skill
scripts/          compose.py, audio_probe.py, music.c, music.h, song_rom.py, song_midi.py, song_wav.py,
                  player__Makefile, player__src__main.c (the player ROM template), pianoroll.js
docs/             the documents, build_cli_md.py (regenerates CLI.md), check_examples.py (runs the examples)
LICENSE           MIT
```

## Provenance and licence

The design rules were measured: register traffic of commercial cartridges the author owns, logged frame by frame
in an emulator; soundtracks transcribed and counted by the author; every generation round listened to. No audio,
code or data from any existing work is included; wave tables are register images, drums are register pairs,
progressions are Roman numerals, corpus figures are counts. No existing work is named here. MIT License, copyright
2026 Kevin Jacobson.
