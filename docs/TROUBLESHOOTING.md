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

## The probe disagrees with my ears

- `samples: false`: this PyBoy build cannot sample sound; only NR52 activity is reported. Use the PyBoy in
  `tools/pyenv` (sound emulation on).
- `solo_reliable: false`: the game rewrites NR51 every frame, so the per-channel passes are approximate; write NR51
  once at boot.
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

