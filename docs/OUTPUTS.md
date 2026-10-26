# Outputs: a Game Boy Color ROM, a MIDI file, a WAV

One score, three targets. The GBC output is the real thing (the driver on the chip); MIDI is for a DAW or a
collaborator; WAV/MP3 is the chip's actual sound, rendered headlessly, for a page or a listening test.

## 1. GBC: the song inside your own GBDK-2020 project, step by step

The driver is two files and the song is two generated files. Nothing else is required.

1. Copy `scripts/music.c` and `scripts/music.h` into your project's `src/`.
2. Compile the score: `python scripts/compose.py compile main.txt --out <project>/src/music_data.c` (writes
   `music_data.h` next to it: `extern const Song song_main;`). Several scores in one call share the file.
3. Power the APU once at boot, before any sound (the driver never touches these three registers):
   ```c
   NR52_REG = 0x80;  /* APU on, first */
   NR50_REG = 0x77;  /* master volume L/R */
   NR51_REG = 0xFF;  /* every channel to both speakers */
   ```
4. Start the song and tick the driver every frame:
   ```c
   #include "music.h"
   #include "music_data.h"
   ...
   music_init(&song_main);          /* at the title screen, or when play starts */
   while (1) {
       /* game logic */
       wait_vbl_done();
       music_tick();                /* once per frame, right after vblank */
   }
   ```
5. Make every sound effect announce the channels it borrows before writing registers, so the music yields and comes
   back: `music_sfx(MUSIC_CH1 | MUSIC_CH4, 18);` for a jump that uses pulse 1 and noise for 18 frames. Short effects
   belong on pulse 1 and noise; leave pulse 2 (the chord) and the wave bass to the music unless the sound needs them.
6. Duck instead of stopping under a sting or a dialogue: `music_set_volume(6)`, then `music_set_volume(15)`.
   `music_stop()` silences everything; `music_playing()`, `music_bar()`, `music_row()` let the picture follow the
   music (a palette step per bar, a pulse on row 0).

Build as usual (a GBDK Makefile that compiles every `src/*.c` picks the new file up). The song's bytes are in the compile report
(`rom_bytes`); a 32-bar theme is 5-6 KB in bank 0. Verify by listening: `python scripts/audio_probe.py --rom game.gbc
--out qa/audio --seconds 10` must report four channels active and real pitch changes after START
(`play.music_detected`). The full contract (what happens on `music_sfx`, volume scaling, what `music_init(NULL)` does)
is in `INTEGRATION.md`.

## 2. GBC: the standalone player ROM (`song_rom.py`)

```
python scripts/song_rom.py main.txt [more.txt ...] --out player.gbc [--title "MUSIC PLAYER"] [--project keep/dir]
```

Assembles a minimal GBDK project (the player template `player__Makefile` + `player__src__main.c`, the driver, the
compiled tables, a generated `songs.h` with the song table and titles), runs `make`, copies the ROM out. Toolchain:
`$GBDK_HOME`, else `lcc` on PATH, else the usual install locations. Up to 9 scores; two scores with the same `name:`
are kept apart (`song_main`, `song_main_2`).

The ROM boots straight into song 1 and shows: the player title, the song title (from `title:`), `SONG n/m`, the bar
count / bpm / length, a live `BAR xx ROW yy` counter, and the controls. **START** next song, **SELECT** previous,
**A** restart, **B** duck / unduck (volume 6 / 15, the same call a game uses). 32 KB, GBC header, MBC5; runs on
hardware (flash cart), in any emulator, and through `audio_probe.py`:

```
python scripts/audio_probe.py --rom player.gbc --out probe --pre wait:60 --seconds 10
```
(`--pre wait:60`: the music starts at boot, so the title window needs no long wait; START restarts song 1 or moves to
song 2, so the play window has music too.) Measured on the fusion example: four channels active in both windows,
317 pitch changes and 59 drum hits in the 10 s play window, arpeggio detected at 3 frames per step.

## 3. MIDI (`song_midi.py`)

```
python scripts/song_midi.py main.txt --out main.mid [--loops 1] [--vibrato cc|bend|none] [--report r.json]
```

A format-1 Standard MIDI File, five tracks, replayed frame by frame the way the driver plays the score.

| track | MIDI channel | program | content |
|---|---|---|---|
| 0 | - | - | conductor: title, tempo, time signature |
| 1 pulse 1 lead | 1 | 80 Lead 1 (square) | the lead lane |
| 2 pulse 2 arp/echo | 2 | 81 Lead 2 (sawtooth) | the arpeggio lane with every chord cycle expanded into its notes; echo copies of pulse 1 while `echo:` is on |
| 3 wave bass | 3 | by table: 38 Synth Bass 1 (saw, rsaw, reed, buzz, pwm...), 39 Synth Bass 2 (tri, tri2, tridip, sine, soft), 14 Tubular Bells (bell), 16 Drawbar Organ (organ, organ2) | the bass lane; the program changes when the table family changes |
| 4 noise drums | 10 | GM percussion | the drum lane |

| score | MIDI |
|---|---|
| tempo | 4 rows per quarter note; microseconds per quarter = 4 x frames_per_row / 59.7275 x 10^6 (9 frames per row = 100.0 bpm); PPQ = 32 x frames_per_row, so one frame is exactly 8 ticks |
| `rows:` | time signature `rows/4` over 4 (16 -> 4/4), or `rows` over 16 when not a multiple of 4 |
| `F#4:maj7` with `arp: 3` | notes F#4, A#4, C#5, F5 of 3 frames each, cycling for the cell's length |
| `^2` trill / `'2` mordent | the alternation per frame, as 1-frame notes |
| `C5>D5` | D5 from the middle of the row |
| `/-2,6` bend, `=6` portamento, `penv=` | pitch-bend events per frame along the driver's period-linear glide; bend range 12 semitones (RPN 0 at the track start), centred again when the note ends |
| `/-4` raw slide | pitch bend per frame until the next note (clamped at the 12-semitone range) |
| `~`, `vib=` | CC1 modulation (depth x 16) at the note (default), or pitch-bend events (`--vibrato bend`), or dropped |
| `v9`, instrument volume | velocity = 8 x volume + 7 (15 -> 127, 6 -> 55) |
| `!3` cut, wave `decay=N` | the note ends after 3 frames / after 3 x N frames |
| `echo:5,3` | pulse-1 notes copied onto track 2, 5 frames late, velocity 3 steps lower, until `echo:off` or a pulse-2 note |
| drums | K k 36, S s P N 38, H h 42, O 46, T 45, C c 49, B 36, Q 40, M 56, t 47, X 51, D 37, Z 54; a stack strikes the second drum 3 frames later; velocity from the preset's volume; a custom letter not in the table is 38 |
| `%` tremolo | not exported |

The report says `cells` (note cells in the score; equals the compile report's `notes`) and `midi_notes` (after
expansion). Measured: the 32-bar fusion example has 1025 cells and 3041 MIDI notes (77.2 s); the stage example 671
and 1167. The file round-trips through `mido` with equal note-on and note-off counts.

## 4. WAV and MP3 (`song_wav.py`)

```
python scripts/song_wav.py main.txt --out main.wav [--seconds N] [--loops 1] [--mp3] [--rate 32768] [--rom keep.gbc]
```

Builds the player ROM (so the sound is the driver on the chip, nothing approximated), boots it in headless PyBoy with
sound emulation using `audio_probe.py`'s capture code, cuts the emulator's boot chime and the silence after it (the
clip starts on the song's first sounding sample; the report's `trimmed_s` says how much went, about 1.2 s), and
writes 16-bit stereo PCM at 32768 Hz (the emulated APU's native rate; `--rate` resamples in the
emulator). Length: the song once (`loop:` body repeated for `--loops 2`) plus half a second, or `--seconds`. With
`--mp3`, `<out>.mp3` is encoded with `lame` at 192 kb/s (`ffmpeg` + libmp3lame when lame is missing). The fusion
example renders 77.3 s in about 4 s wall clock: 10.1 MB WAV, 1.86 MB MP3.

Several scores on the command line build a multi-song ROM but only song 1 is rendered; pass one score per WAV.

## 5. Events JSON and the interactive piano roll (for a page)

```
python scripts/compose.py events main.txt --out main_events.json --offset 0
```
writes every note with its time in seconds, so a page can draw the song against its audio: inline `pianoroll.js`,
the events JSON and the clip (`main.mp3` from `song_wav.py`), add a `<figure data-pianoroll ...>` and call
`GbcPianoRoll.mountAll()` (`ARCHITECTURE.md` §5 has the markup, `PIANOROLL.md` the full API). `--offset` is the
second of the clip at which the song's frame 0 sounds: 0 for `song_wav.py` output (the clip starts on the song's
first sounding sample, which is frame 0 whenever row 0 of the score sounds), about 0.711 for a game ROM rendered
from boot.
