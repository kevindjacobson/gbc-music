# gbc-music: four-channel music for the Game Boy Color, from a one-line idea to a ROM, a MIDI file and a WAV

`gbc-music` is a complete, self-contained music system for the Game Boy Color sound chip:

- a **driver** (`scripts/music.c`, `music.h`): 20 KB of C source for GBDK-2020 (5.2 KB of code, 133 bytes of RAM)
  that plays tracker-style song tables on the four hardware voices (two pulse channels, a 32-sample wave channel, a noise channel), with arpeggiated chords,
  echo, trills, resolving bends, portamento, duty and wavetable sequences, level envelopes, a drum kit, and a contract
  that lets sound effects borrow a channel and hand it back;
- a **score format** (plain text, one block per bar, four lanes of sixteenth-note cells) and a **compiler**
  (`scripts/compose.py compile`) that turns a score into C tables the driver reads from ROM;
- a **generator** (`scripts/compose.py generate`) that writes a whole song deterministically from a style, a key, a
  tempo, a bar count and a seed, with song forms (stage loop, verse-chorus, AABA, twelve-bar blues), a progression
  library in Roman numerals, two textures and an organic layer that keeps a machine-written song from sounding like
  one;
- three **outputs** from the same score: a `.gbc` player ROM for real hardware or any emulator (`song_rom.py`), a
  General MIDI `.mid` for a DAW (`song_midi.py`), and a `.wav` / `.mp3` rendered through a cycle-exact emulation of the
  chip (`song_wav.py`);
- a **listener** (`scripts/audio_probe.py`): headless emulation that isolates each channel and reports what actually
  sounds (active channels, pitch changes, arpeggio runs, drum hits), plus a piano-roll picture, so a build is
  verified by ear and by numbers, never by reading the code.

## Why it sounds right

The rules in `DESIGN_NOTES.md` were measured, not guessed: the register traffic of four commercial Game Boy Color
cartridges was logged frame by frame in an emulator, a classic action-platformer's stage loops and a classic
handheld RPG's soundtrack were transcribed and counted, and the author listened to every generation round and said
what was wrong. The results are concrete and sometimes surprising: a pulse channel can change its duty any frame
without a click but every volume change is a re-strike; the wave channel is the only voice with click-free dynamics;
the cartridges switch instruments between phrases, not between notes, and when they do switch note to note they
change the envelope and keep the duty; vibrato is delayed and shallow; bends are rare and always land on the written
note; the second pulse is a counter-line, almost never parallel thirds. The generator and the skill text encode
those findings as defaults, so the first thing a game ships with already sounds like the cartridges it sits next to.
The measurements were made by the author on cartridges the author owns and through the author's own transcription and
disassembly research; no audio, code or data was copied from any of those works (`LICENSE.md`).

Licence: MIT, copyright 2026 Kevin Jacobson (`LICENSE`).

## Quick start: an empty directory to a .gbc, a .mid and a .wav in five commands

Requirements: Python 3.11+ (stdlib only for compose, song_rom and song_midi); `numpy` + `pyboy` for `song_wav.py` and
`audio_probe.py` (`Pillow` for the piano-roll PNG); GBDK-2020 with `GBDK_HOME` pointing at the directory that holds
`bin/lcc`; `make`; `lame` or `ffmpeg` for `--mp3`. Installation step by step: the `README.md` at the skill root.

```
export SKILL=/path/to/skills/gbc-music       # this directory
mkdir demo && cd demo
python $SKILL/scripts/compose.py generate --style fusion --key F# --bpm 100 --bars 32 --seed 7 --organic 2 --out main.txt
python $SKILL/scripts/song_rom.py main.txt --out main.gbc
python $SKILL/scripts/song_midi.py main.txt --out main.mid
python $SKILL/scripts/song_wav.py main.txt --out main.wav --mp3
python $SKILL/scripts/audio_probe.py --rom main.gbc --out probe --pre wait:60 --seconds 10
```

What you get: `main.txt` (the score, yours to edit), `main.gbc` (32 KB, boots into the song with a title screen; START
restarts it), `main.mid` (five tracks: conductor + one per channel), `main.wav` + `main.mp3` (the chip, 32768 Hz), and
`probe/audio_report.json` + `probe/pianoroll.png` (four channels active, a few hundred pitch changes in ten seconds).
Every script prints a final JSON line with the numbers, so a pipeline can read them.

To put the song in a game instead of the player ROM: `OUTPUTS.md` (GBC section) and `INTEGRATION.md`.

## Where to read next

| document | what it answers |
|---|---|
| `ARCHITECTURE.md` | how the pieces fit: driver, score, compiler, generator pipeline, probe, listening pages |
| `SCORE_FORMAT.md` | the complete score grammar: header, instruments, chords, waves, drums, every cell effect |
| `CLI.md` | every subcommand and flag, generated verbatim from `--help` |
| `OUTPUTS.md` | the three outputs: GBC integration step by step, the player ROM, the MIDI mapping table, WAV/MP3 |
| `INTEGRATION.md` | the driver's contract for a game: init, tick, SFX hand-over, volume, hooks |
| `DESIGN_NOTES.md` | the measured facts and the rules they produced |
| `EXAMPLES.md` | six worked examples with the exact commands and what to listen for |
| `TROUBLESHOOTING.md` | silent channels, clicks, builds that fail, probes that disagree |
| `LIMITS.md` | what the chip and the driver cannot do, and the hard numbers |
| `PRESENTATION.md` | a 5-10 minute demo script with timings and a fallback |
| `PIANOROLL.md` | the interactive piano roll: data format, API, measured clip offsets |
| `LICENSE.md` | MIT License (the text is in `LICENSE` at the skill root) and the provenance of the measured facts |

## Layout of this directory

```
SKILL.md          the agent-facing skill (what a coding agent reads to use all of this)
scripts/          compose.py, audio_probe.py, music.c, music.h, song_rom.py, song_midi.py, song_wav.py,
                  player__Makefile, player__src__main.c (the player ROM template), pianoroll.js
docs/             these documents, build_cli_md.py (regenerates CLI.md), check_examples.py (runs the examples)
```
