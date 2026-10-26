# Troubleshooting

Read the JSON line every script prints: it names the problem. Then this list.

## Nothing on a channel I expect to hear

- **A decaying envelope on a held note**: `env=C2` dies in 22 frames; a chord cycle or a pad needs step 0 (`90`, `A0`,
  `C0`) or the slow `C7`. The probe then shows `pulse2.active_ratio` near 0.
- **Wave `vol` too low**: 0 is off, 1-4 is the quarter level; use 11-13 for a bass.
- **An SFX hold that never ends**: `music_sfx(channels, frames)` with a huge `frames` keeps the driver off the channel.
- **The song never started**: `music_init(&song)` was not called, or `music_tick()` is not in the frame loop, or the APU
  was never powered (`NR52 = 0x80` first, then NR50 / NR51).
- **Pulse 2 silent in the echo section**: that is the design (`echo:` replaces the chord with a delayed copy of the lead)
  until `echo:off`; if the lead rests, the echo rests.

## Clicks and glitches

- **Clicks on every note of a pad**: tremolo (`%`) on a pulse re-strikes every step; put tremolo on the wave lane or use
  rate >= 6; a wave sequence at rate 1 rewrites wave RAM every frame (use rate >= 2, 4-6 for pads).
- **A zipper on a bend**: at C2 a semitone is 90 period units; a long low bend in few frames steps audibly. Use 4-6
  frames and keep bends to 1-2 semitones low down.
- **The lead and the chord fight**: give the chord 25% or 12.5% duty (`duty=25`), one volume step under the lead.
- **Out of tune**: a `detune` of 2 or more, or detune on a single voice. Default is exact unison or an octave pair.

## The compiler refuses the score

- `bar 3 row 5: cell 'F#4~^2' has two effects`: one effect per cell. `'@' needs an instrument name`: `@lead` must name
  an `inst` line. `unknown chord`: see `compose.py styles` or add a `chord` line. `a bend starts 1..3 semitones away and
  resolves in 1..15 frames`: bends are small and resolving by rule; a raw slide is `/-4` without a comma.
- `at most 16 wave shapes`: a wave sequence uses one slot per table; share tables between instruments.
- `two scores share a song name`: set `name:` in one of them (`song_rom.py` renames duplicates by itself).
- Warnings (not errors) in the report: out-of-range notes are clamped; read them, the clamp changes the tune.

## The build fails

- `GBDK_HOME is not set` / `GBDK not found`: export `GBDK_HOME` to the GBDK-2020 directory that contains `bin/lcc`
  (`song_rom.py` also tries `lcc` on PATH and the usual install locations).
- `make is not installed`: install build tools (`xcode-select --install` on macOS).
- `Undefined Global '_song_main'`: the game includes `music_data.h` but `src/music_data.c` was not regenerated or has
  another `name:`; recompile the score with `--out <project>/src/music_data.c`.
- A `song_rom.py` failure keeps the project at the path it prints (or `--project <dir>`): open `build.log` there.

## I hear no panning

- **The handheld speaker is mono**: NR51 pans are heard on headphones, in `song_wav.py`'s stereo WAV / MP3 and in a
  two-core duet only. Check the probe instead: `pan_events` > 0 and a channel's `stereo.side` L / R / moving.
- **The game still writes `NR51 = 0xFF` itself** (an old `sfx_init`): replace it with `music_set_pan_base(0xFF)`;
  a per-frame NR51 write from game code undoes every music pan and makes `solo_reliable` false.
- **The pan is on the bass or the kit**: the compiler refuses it (`pan markers belong on the lead and arp lanes`);
  pans belong to echoes, answers and pads.
- **`--pan echo` did nothing**: the score has no echo section (plain textures have none; `--texture fusion`, the
  fusion style and its AABA / verse-chorus forms do). `--pan call` needs a form with phrases (stage, verse-chorus,
  aaba, blues12); the fusion loop has none.
- **A marker next to an effect** (`C5~<`) is refused: one cell holds a note + one effect or a note + a pan. Put the
  marker on the row before (`.` -> `<`); the switch then lands one 16th early, during the rest or the previous tail.
- **The probe's solo passes are approximate** (`solo_reliable: false`): the ROM rewrote NR51 in more than 5% of the
  frames, usually an auto-pan (`pan=LR:N`) flipping every N frames. The channel numbers are still measured on the
  channel alone (the probe follows the ROM's own side for the soloed channel); only the write frames can leak.

## The probe disagrees with my ears

- `samples: false`: this PyBoy build cannot sample sound; only NR52 activity is reported. Use the PyBoy in
  `tools/pyenv` (sound emulation on).
- `solo_reliable: false`: the ROM rewrote NR51 in more than 5% of the frames (`pan_events` counts them, `pan_leak_frames`
  the frames over the four passes in which another channel could leak in), so the per-channel passes are approximate.
  Game code must never write NR51 itself (`music_set_pan_base` instead); music pans from the score are rare by design,
  an auto-pan is the one texture that pushes the count up.
- `music_detected: false` on `play` but the song is audible: the play window starts 60 frames after START; a game
  that restarts music later, or ducks it to 0, or whose START does not reach gameplay, has silence there. For the
  player ROM use `--pre wait:60` (music starts at boot).
- Pitch tracking misses the wave bass: it reaches 32 Hz; the probe widens its window on that channel, but a very low
  drone at low level may read as inactive. Raise `vol` or the octave.
- `distinct_pitches` on pulse 2 looks huge: chord cycling counts every chord tone; that is the arpeggio, and
  `arpeggio.detected` with `step_frames` 3-4 confirms it.

## MIDI sounds wrong in the DAW

- **Arpeggios as a blur**: they are 3-frame notes (50 ms) by design; mute track 2 or raise the DAW's instrument
  attack. **Bends too wide**: the file sets the bend range to 12 semitones with RPN 0; a synth that ignores RPN
  assumes 2 and bends six times too far. **Drums on the wrong sounds**: channel 10 GM mapping; load a GM kit.
- **Tempo reads 112.5 instead of 120**: the Game Boy quantises to whole frames per row (`LIMITS.md`); the MIDI carries
  the true tempo.

## WAV is silent or short

- `silent: true` in the report: the ROM made no sound in the window (see "Nothing on a channel"). The WAV is trimmed
  to the first sample, so a late start shortens it; use `--seconds`.
- `--mp3 needs lame or ffmpeg`: install one of them.

