# Limits: what the chip and the driver cannot do

## The chip (Game Boy Color APU)

- **Four voices, fixed roles**: two pulse channels (4 duty cycles: 12.5 / 25 / 50 / 75%), one 4-bit 32-sample wave
  channel, one noise channel (15-bit white noise or 7-bit "tonal" LFSR). No more voices, no sample playback at a
  usable rate from this driver, no filters, no reverb.
- **Pulse volume = envelope only**: 16 levels, loaded only on a trigger (a volume change is a re-strike with a phase
  reset: a click). The hardware envelope moves one step every n/64 s; there is no real attack-decay-sustain-release.
- **Wave volume = four levels** (full / half / quarter / off), click-free but coarse. The wave channel has no
  envelope of its own; `decay=` / `attack=` step those four levels.
- **Pitch**: 11-bit periods; the pulse range used here is C2..B7, wave C1..B6; the high end is coarse (a semitone
  is 2-3 period units at C7, 90 at C2), so bends and vibrato in period units sound wider low and narrower high.
- **Noise has no pitch** beyond its clock divider and shift (NR43); a "tonal" 7-bit buzz is the nearest thing.
- **Panning is hard left / right / both** per channel (NR51), no pan law, no in-between positions; one register
  write per change, click-free. Mono on the handheld speaker: pans are heard on headphones, in the WAV and in a duet
  only. The music pans the two pulse channels (echoes, answers, pads); the wave bass and the kit stay centre.
- **One wave table in RAM**: swapping it needs the DAC off (NR30 = 0) and a re-trigger: a small click per step.
- **Mono speaker in practice** (stereo only on headphones): 75% and 25% duty are identical, detune of two or more
  units reads as out of tune.

## The driver

- One effect per cell, one instrument change per cell, 3 bytes per cell, 16th-note rows (`rows:` can change the
  grid but every row has the same length: no triplets inside a bar except by `tempo:` choice and row count). A pan
  marker shares a cell with a plain note or with `@inst`, not with another effect (put it on the row before).
- The echo voice replays pulse 1 from a 16-frame ring: delay 1..15 frames, no feedback, no second echo.
- Arpeggio = up to four chord slots at one global rate (`arp:`, changeable with `arpspeed:`), not per-voice rates.
- No per-note envelopes beyond the instrument's NRx2 / NR32 steps; no LFO other than vibrato (triangle, period
  units) and tremolo (level steps); no sample channel; no pulse-width modulation finer than the 4 duties (a duty
  sequence steps between them).
- Hardware sweep (NR10) is unused on purpose; every glide costs one division at note-on and an add per frame.
- No real-time control from the game except `music_set_volume`, `music_sfx`, `music_init`, `music_stop`.
- Timing is frame-locked (59.7275 Hz): tempos are quantised to whole frames per row (bpm 100 = 9, 112.5 = 8, 128.6 =
  7, 150 = 6, 180 = 5). `bpm: 120` is actually 112.5 bpm (8 frames per row); the MIDI export carries the true tempo.

## Hard numbers (enforced by the compiler)

| what | limit |
|---|---|
| instruments per song | 15 |
| distinct chords / bar lanes (patterns) / bars | 255 each |
| wave tables per song (a sequence uses one slot per table) | 16 |
| drums per song | 15 |
| rows per bar / frames per row / arp rate | 1..64 / 1..255 / 1..15 |
| bend | 1..3 semitones away, 1..15 frames, needs a note |
| portamento / cut | 1..255 frames |
| echo | delay 1..15 frames, drop 0..15 steps, side L / R / C |
| pan | `<` `>` `^` on the lead and arp lanes only, one marker per cell, not next to another effect on a note cell; `pan=LR:N` 1..63 frames per side |
| vibrato / tremolo | depth 0..15, rate 0..15 (tremolo on a pulse: rate >= 6 or a warning) |
| detune | -8..7 period units (rule: at most 1, on a double) |
| pitch envelope | 1..15 semitones, 1..15 frames |
| duty sequence / wave sequence rate | 1..7 frames per step |
| pulse notes / wave notes | MIDI 36..107 / 24..95 (clamped with a warning) |
| songs per player ROM | 9 |

## The generator

- Deterministic by design: no "make it better" knob beyond seed, style, form, progression, texture, organic and
  bend rate. It does not read audio, lyrics or a brief; the agent (or a human) chooses the arguments from the brief.
- Bar counts snap to the form's plans (stage 16 / 24 / 28; verse-chorus 32 / 48 / 64; aaba 32 / 40; blues12 28 / 40 / 52).
- `ambient` is loop-only; `fusion` takes loop, aaba and verse-chorus; stage and blues12 forms go through `rock` / `pop`
  / `chip` with `--texture fusion` for the fusion idioms.

## The outputs

- MIDI: tremolo is not exported; per-frame trills become 1-frame notes; wave tables map to four GM programs; the
  noise kit maps to GM percussion by role, not by sound.
- WAV: rendered from the player ROM at boot, song 1 only per run; `--seconds` is capped at 600.
- The player ROM's screen is dark with light text (an ink ratio under 15%), so a generic "blank screen" heuristic
  that expects a busy game picture will call it blank; the probe's audio numbers are what matters for it.
