# Design notes: the measured facts and the rules they produced

Every rule below came from a measurement or from the author listening, not from taste alone. The sources are
described generically; the numbers are the real ones.

## How the measurements were made

All of it was measured by the author on cartridges the author owns and through the author's own transcription and
disassembly research. Nothing was copied from those works: the wave tables and drum presets below are register
images (what the hardware was told to do), the progressions are Roman-numeral patterns, the corpus figures are
counts. The licence is MIT (`LICENSE.md`).

- **Register logs**: four commercial Game Boy Color cartridges (a handheld action-adventure, a handheld puzzle game,
  a handheld treasure platformer and the RPG cartridge) were run for two minutes each in a headless emulator with a
  per-frame log of every sound register write (NR10-NR52, wave RAM). Instrument identities were derived from the
  (duty, envelope) pairs on the pulses and the (table, NR32 level) pairs on the wave channel.
- **Transcriptions**: a classic action-platformer's nine looping stage themes and a classic handheld RPG's 23 looping
  songs were transcribed to bars and chords and counted: section lengths, progressions, how the second pulse relates
  to the first, what the bass does, how many drum hits per bar.
- **A fusion reference**: a late-80s console title theme (100 bpm, F#/C# centre, maj7/add9/m9 voicings, modulations
  every 8-16 bars, about 14 notes per second on the chord voice, 2790 drum hits in four minutes) is the model for
  the `fusion` style.
- **The author's ear**: each generation round was played to the author, whose verdicts became rules ("less pitch
  bending, or have the bends resolve nicely"; "be careful with detuned"; "one song at a time on a page").
- **Organicness metrics**: the generator's output was scored against the transcriptions on bar-rhythm reuse (0.9 vs
  0.44 of bars), phrase novelty (0.3-0.4 vs 0.84), rest ratio (0.03-0.10 vs 0.24) and density flatness; the `--organic`
  layer targets exactly those gaps.

## Register truths (Pan Docs, confirmed in emulation) and what they allow

| fact | rule |
|---|---|
| NRx1 duty bits change any frame without a re-strike | duty sequences are free and click-free: `duty=50,25 rate=2` is one shimmering voice, `12,25,50,25 rate=4` a slow PWM for a chorus lift |
| NRx2 (pulse / noise envelope) only loads on a trigger | every pulse volume change is a re-strike: `v` accents per note, tremolo on pulses only at rate >= 6 and only on pads |
| NR32 (wave level: full / half / quarter / off) changes silently | the wave channel is the only voice with click-free dynamics: `decay=` bells and plucks, `attack=` swells, `%` tremolo live there |
| wave RAM is rewritten behind NR30 = 0 and the note re-triggered | a wavetable step clicks a little: rate 4-6 for pads, 2-3 only for a two- or three-table attack; looping sequences are textures for pads and drones, not bass lines |
| NR10 hardware sweep exists on pulse 1 only and keeps running across notes | the driver zeroes it and does every pitch movement in software on all three tonal channels alike |
| 75% duty = 25% inverted (identical in mono) | the RPG cartridge uses 75% on 90% of its pulse frames; the others use 50% on 60-100% and 25% for the second voice; 12.5% is thin and distant (echo voices) |
| the 7-bit LFSR (NR43 bit 3) is a tone | 7-bit for anything that should ring (tings, toms, the kick body: every tonal hit in the RPG kit, 15 of the action-adventure's 25 intro drum hits); 15-bit for air (snares, hats) |
| the wave channel sounds an octave below the pulse table | the driver adds 12 semitones for wave notes; write the pitch you want to hear |

## Timbre and modulation (measured on the cartridges)

- **Instrument per section, not per note.** Leads carry 6-11 instrument identities per piece and switch 3-19 times
  a minute, almost always at a phrase or section boundary (the action-adventure: 8 switches in 2.5 min, 12 s apart,
  runs of 112 notes; the treasure platformer: 16 of 48 runs are 8+ notes). Rule: `@leadB` on a section's first note.
- **Articulation pairs change the envelope, not the duty.** The note-to-note switches that exist keep the duty and
  change only NRx2: loud/quiet `91`/`61`, hold/decay `A0`/`A7`, stab/sustain `82`/`30` (the puzzle game's chord voice
  alternates them on 86 of 179 runs). A duty change means a new section or a new voice.
- **Basses alternate two tables or two levels.** The action-adventure's bass switches between two square-in-wave
  widths 82 times in 2.5 min. Rule: `@bass` on beats, `@bass2` on the octave bounces (a second table, or the same at
  half level).
- **Noise is a kit.** 2-3 hats/snares alternate per bar; a crash on the section's downbeat; the RPG kick is a two-stage
  hit (a 1.4 kHz 7-bit buzz, then a hiss).
- **Vibrato is delayed and shallow.** The RPG's house values: delay 8-32 frames, depth 1-4 period units, 3-8 frames per
  half period. Rule: `vib=2:3` (depth 2 after 12 frames) on leads, held notes only; a sixteenth-note run never
  vibrates; wide undelayed vibrato (`vib=4:1`) is a special effect (a siren, a ghost), not a style.
- **Panning is static in practice.** NR51 stayed `FF` for two minutes on every cartridge except the RPG's intro (36
  writes, hard solos). SFX own NR51; stereo is not the music's tool.
- **Exact unison, not detune.** The RPG's intro doubles its lead in exact unison; a one-unit period offset is the rare
  exception. Rule (author): default is exact unison or an octave pair; `detune=1` only on the doubling voice, never on
  the lead, never on both, never on the bass, only for a section that wants a wobble; 2 or more reads as out of tune
  on the speaker.

## Pitch motion (the author's rules)

- **Bends are rare and always resolve.** "Less pitch bending, or have the bends resolve nicely." A bend starts a
  semitone or a tone away, never more than a minor third, lands exactly on the written note within 4-6 frames, and
  that note is held long enough to be heard as the arrival. Never on a 32nd. The bass bends only on a downbeat of an
  even bar; the lead only into a phrase's target note. `--bend sparse` (default) does this; `none` turns bends off;
  `normal` is the upper limit. The raw slide (`/-4`) is synth sound design, not music.
- **Portamento sparingly, and it must land**: one step of a phrase (the arrival), never a run. Portamento and the
  resolving bend are the two legal pitch moves.
- **Pitch envelopes make percussion and plucks, never melodic bends**: `penv=12,5` is a kick, `5,3` a tom, `12,1` a
  pluck's attack.

## Song form (the transcriptions)

- **The grain is 4-bar phrases in 8-bar sections**; a phrase repeats with its ending changed; a new harmony or a
  lifted lead when the section changes.
- **Stage loops**: of the action-platformer's nine looping themes, 5 are 24-bar A B C loops, 2 are 16-bar A B, 2 are
  8 bars; 7 of 9 start straight in; median 146 bpm; 8 of 9 minor. Each 8-bar section is a 4-bar phrase and its
  varied repeat (A A' B B' C C'); the contrast between sections is harmonic (VII -> i is the most common move, then
  i -> iv and i -> IV), not a key change; C sits an octave up with the open kit. That is `--form stage` and the
  `stage_a / stage_b / stage_c` progressions.
- **The lift**: 20 of the RPG's 23 looping songs raise the lead in the second section. That is the chorus an octave up
  on a brighter duty.
- **Counter-line, not parallel thirds**: in the RPG corpus the second pulse is a counter-melody in 18 of 24 looping
  songs and parallel thirds in only 3; the bass is arpeggiated figures and walking lines. In the stage corpus the bass
  walks or bounces octaves under a ~15-hit-per-bar kit and pulse 2 is a counter line, never a held chord.
- **Cadential major**: I-V-I is the most common move in the RPG corpus (`cadential`, `town`).
- **Repetition with one change**: the chorus (AAAB hook) comes back note for note and only the kit opens on the last
  one; verse 2 is verse 1 with one note different and an octave-up ending; the pre-chorus sequences the hook's first
  bar up a step per bar over a snare build; fills close every 4 bars and land on beat 1.

## The fusion idioms (the reference, in register terms)

- **Pulse 2 is the chord, not a melody**: a 3-4 note voicing cycled one note every 3-4 frames (`arp: 3`) reads as a
  chord at frame rate; colour tones (7th, 9th), drop the fifth; a sustaining envelope (step 0) or the chord vanishes.
- **Pulse 1 is a lead that moves**: sixteenth-note runs (lydian over maj7, dorian over m7), a 2-frame mordent on the
  first note of a phrase, a trill or vibrato where it lands, rests so the echo and the chord breathe; range E3..A5.
- **Echo section**: for 8 bars the chord drops and pulse 2 replays pulse 1 four to six frames later, 3-4 steps quieter.
- **Wave is a slap bass**: a bright table, B1..A2, eighths with sixteenth octave bounces, a chromatic approach note into
  the next chord, a rare downbeat bend from a tone below, staccato pops (`!3`).
- **Noise is a fusion kit on a sixteenth grid**: hats on every sixteenth (quiet ones between), kick on 1 and 3 plus a
  syncopated one, snare on 2 and 4 with ghosts, stacks, a fill in bar 8.
- **Harmony**: 8-bar sections of four two-bar chords voiced with the top note moving least; modulate down a major third
  or up a minor sixth every 8-16 bars.

## Mix rules (so the lead reads on a tiny speaker)

Lead loudest (`env=C2`..`F2`), chord one step under (`90` / `A0`), bass `vol=11..13`, hats quiet (`61`), kick and
snare full; ambient everything at 5..9. One effect per cell; one chord per voice; never two melodies at once; if the
lead and the chord fight, give the chord 25% or 12.5% duty. Duck, do not stop, under a sting.

## Organicness (what a straight generator gets wrong, measured)

Compared with the transcriptions a straight generator reuses its bar rhythms twice as much (0.9 vs 0.44 of bars),
writes phrases that are copies (novelty 0.3-0.4 vs 0.84), hardly rests (0.03-0.10 vs 0.24) and only at phrase ends,
and keeps a flat density. `--organic 2` fixes the cheap half (varied repeats, breaths, fills, dropped hats, a bar
without pulse 2, accents, bass anticipations). What it cannot do and a human (or the agent, after listening) should:
let the lead sit out a whole bar once per section; put a new idea in the second time round; shape accents by
phrase; thin the ornaments to one mordent per phrase; reshape the fill rather than append it.

## Listening pages

One song at a time: a page with more than one player pauses every other `<audio>` when one starts; a page that
mixes live emulator audio with a reference clip pauses one when the other starts. Every claim about sound on a
page is next to the audio that proves it and the piano roll that shows it.
