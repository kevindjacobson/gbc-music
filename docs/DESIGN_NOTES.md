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
  layer targets the cheap half of those gaps (varied repeats, breaths, fills, accents) and the `--phrases` grammar the
  structural half (banks of three ideas per section with rests as cells, cross-section quotes, pulse-2 answers, a
  written-in density arc): with it the stage form enters the corpus bands on all four measures and the verse-chorus
  form on three (its chorus returns note for note by rule).
- **Syncopation index**: the same transcriptions and the generator's scores were measured with the Longuet-Higgins &
  Lee index per lane (below); the `--groove` / `--syncopation` knobs target those bands.

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
  writes, hard solos). NR51 is the only pan control: hard left / right / both per channel, no pan law, and the
  handheld speaker is mono; the trackers of the platform expose it as one command per step. Rule (author, after
  listening to the detune lesson): a pan is a special effect. Everything defaults to centre; pans belong to echoes
  (the ping-pong echo: lead left, echo voice right), answers (call and response: the answer on one side, alternating
  per phrase pair; the blues call left and answer right) and pads (an L/R auto-pan texture), never the wave bass or the
  kit, never a lead for a whole song. The driver owns NR51 through a shadow byte and writes it only when the value
  changes, so a panned song costs one register write per pan and the listener's channel isolation stays reliable
  (`pan_events` under 5% of the frames). `compose.py generate --pan none` is byte-identical to an unpanned run.
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

## Hooks and melodies (measured, and what the literature says)

Measured with the research metric on the two reference corpora (the stage corpus's 19 themes, the handheld RPG's
53 songs, 58 hooks found) plus a desert-stage theme from a 1998 console adventure the author picked as "catchy and
syncopated". The lead is the highest-register melodic stream after dropping strums (over 10 top-note onsets per
bar) and the bass; the hook is the most repeated 1-, 2- or 4-bar cell with exact rhythm and intervals (3+ notes,
3+ pitches, 2+ occurrences; score = bars of re-hearing). Pooled interquartile bands (p10..p90 in brackets):

| metric | band | the desert theme |
|---|---|---|
| hook length, bars | 2..4 (1..4), median 4 | 2 |
| exact hearings per file | 2..5.75 (2..8), median 4 | 4 (its variations recur far more) |
| hearings per minute | 2.0..5.1 (1.2..8.2), median 3.5 | 1.5 |
| first heard, s | 1.7..15.5 (0..32), median 7 | 16 |
| hook range, semitones | 7..13 (5..19), median 9.5 | 8 |
| lead range, semitones | 15..26, median 19 | 24 |
| step ratio, steps / (steps + leaps) | 0.20..0.75, median 0.52 | 0.53 |
| largest leap | 5..11, median 7 | 8 (a minor sixth) |
| big leaps (a sixth or more, or a tritone) per hook | 0..1 (p90 3), median 0 | 1, at a quarter of the cell |
| climax position inside the hook | 0.14..0.78, median 0.45 | 0.2 |
| the song's top note, position in the piece | 0.10..0.44, median 0.27 | 0.02 |
| last beat silent | 0..0.5, median 0 | 0 |
| onsets per bar in the hook | 3.5..8, median 6 | 8 |
| distinct pitches in the hook | 4..8, median 6 | 5 |
| tempo | 125..167, median 138 | 120 |

Contour classes of the 58 hooks (first note, mean, last note): rising 17, falling 15, bowl 8, arch 8, flat-rise 6,
rise-flat 2, flat-fall 1, flat 1. Game hooks are directional lines more often than arches; the rise-then-fall of the
earworm literature is one shape among four. The song's highest note arrives in the first half (the lift section
is B or C, not the end), hooks rarely breathe at their end (the kit and bass run on), one leap of a sixth per hook
is normal and none is the median. The desert theme's hook is a two-bar guitar figure of eight onsets per bar: a
rising line, one leap of a fourth up then a sixth down, a fixed three-note tail whose first note moves with the
chord, and a tresillo rhythm.

**The author's picks** (thirteen songs the author called catchy, measured the same way; pop and rock singles,
a funk single, two console themes): a sung hook is 2-4 bars, heard 4-6 times in a 3-4 minute song (1.2-1.9 a
minute), 5-11 semitones wide (median 7, narrower than the game corpora's 9.5), half steps half leaps, mostly
falling or bowl-shaped, first heard 14-53 s in. The **riff hook** is a case of its own: in a late-1960s rock single
the two-bar blues-scale riff on guitar and bass in unison is the hook (17 hearings, 3.3 a minute, 9 semitones, an
arch) and the voice answers it; a 1960s funk single carries a 4-bar bass figure 9 times under a horn stab that
breathes a whole beat; a 1990s alternative-rock single rides a one-bar riff 13 times; the desert-stage theme's
guitar figure returns 19 times (7 a minute). **A 2004 pop-rock single from the melodic-math school**, by lyric
section, is the ground truth for `--hook 2`: the verse sits in a 7-semitone box (mean MIDI 59.8, 23% steps, a third
of its rows rests), the pre-chorus widens to 12 semitones and lifts, the chorus sits 10.6 semitones higher (mean
70.4, range 8, 91% stepwise, fewer and longer notes), the song's top note is in the bridge, and the title is sung
on one four-8th rhythm from beat 3 at the end of every verse and at both ends of every chorus, first at 13.6 s.
On a pop brief that lift says `--lift octave`; the game corpora's fifth is the loop default.

**One hook or several?** Counting the distinct repeated cells of each piece (find the most repeated cell, remove
the bars it occupies, find the next, until nothing repeats twice; capped at six): the stage corpus's themes carry a
median of 2 distinct repeated cells (quartiles 0.5-4; five of nineteen have none that repeats exactly, their
sections are through-composed over a riff), the handheld RPG's songs 3 (1-5), and the author's thirteen catchy
picks 5 (4-6): a three-minute song has a verse figure, a pre-chorus climb, a chorus hook and a tag or two; the
melodic-math single has six, the late-1960s riff single exactly one (the riff), the console storefront theme and
the beat-em-up stage theme three. Within a song the distinct cells span 3 contour classes in the RPG and the
picks (mode), 1 in the stage loops. Rule: a 24-bar stage loop wants one hook (or three, one per section, as the
stage corpus's A B C does by harmony); a verse-chorus song wants two or three; a four-minute song four.
`--hooks 2|3|all` gives each section family its own, under the contrast rules in SKILL §11.

What the literature adds (the pop-writing school known for its "melodic math", the earworm studies, the melody
craft texts; `research_notes` keep the citations): melody first and lyrics fitted to it syllable by syllable;
lines that mirror each other in syllable count and rhythm (an ABAB four-line chorus is the school's most common
chorus shape, "primarily stepwise motion, short phrases, small leaps"); three or four melodic parts per song,
recycled; the chorus the focal point, reached inside the first 50 seconds; the chorus melody previewed in the
verse at a lower energy so "once the chorus comes you feel you have heard it before"; the highest note saved for
the second half of a section; a stark contrast between adjacent sections with one element carried over; growing
choruses (the last the biggest); a post-chorus that repeats the hook's motives (13% of 1,335 Top-40 songs
2010-2015 had one). The 2017 earworm study (129 earworm tunes vs matched controls, 82 melodic features): tunes with a
common global contour were earworms about 80% of the time; among the less common, an unusual average slope between
turning points helped; earworms were faster (124 vs 116 bpm); the pilot's "longer notes, smaller intervals" did
not replicate. Folk-song statistics: phrases arch, with stable starts and descending ends; the arch is largely a
rising first phrase and a falling last one.

What `--hook` does with it, and why: the hook is designed first (one of the four corpus contour classes, 7-10
semitones, mostly steps with one placed leap, a rhythm with one anticipation landing on beat 3 and a breath) and
never re-snapped, so it repeats note for note (the metric found the baseline chorus "hook" repeating only as a
1-bar cell: strong-beat snapping and the organic layer changed a note per statement); the third statement
changes; the verse, pre-chorus, intro and outro derive from it (few parts, recycled; the preview); level 2
mirrors the answers and makes the chorus the registral peak once per chorus; level 3 adds the surprise interval,
the late final note and the bass quote. Measured on 42 generated songs (seven forms, six seeds) at level 3: 468 of
546 band verdicts `in`, 71 `near`, 7 `out` (`climax_pos` on falling hooks, whose peak is their first note).

## Syncopation, groove and catchiness (the research and the corpus bands)

- **The measure**: Longuet-Higgins & Lee (1984) metric weights on the row grid (0 downbeat, -1 half bar, -2 beats,
  -3 off-8ths, -4 off-16ths; 0 / -1 / -2 / -3 on the 12-row triplet bar); an onset followed, before the next onset,
  by a rest or tie on a stronger position scores the weight difference; summed over the loop and divided by its
  bars. It correlates best with listener ratings of syncopation among the published measures (Sioros & Guedes
  2014) and is what the groove study used. Per lane: lead, chords (pulse 2's strikes), bass, kick+snare (hats are
  texture). The off-beat onset share is printed next to it because the index gives zero to an off-8th note that
  runs straight into the next beat (the dancehall snare on the and-of-2 before the kick on 3).
- **Medium syncopation moves people most**: Witek et al. (2014, PLoS ONE), funk drum breaks scored with LHL, a web
  survey of 60+ listeners: medium syncopation gave the most wanting-to-move and pleasure, an inverted U, strongest
  for people who like dancing; audio entropy predicted little. Sioros et al. (2014, Frontiers in Psychology):
  synthesised melodies whose events were moved from strong to weak positions; moderate syncopation rated higher
  for groove than none or maximal, no simple monotonic relation. Madison et al. (2011): across 100 recordings beat
  salience, event density and fast metrical levels correlate with groove, tempo only weakly; microtiming does
  not add groove (Davies et al. 2013). Rule: a clear kick and bass, pushes around them, level 2 by default.
- **Swing is a grid, not a push**: measured ride-cymbal swing ratios run from about 3.5:1 at slow tempos to near
  1:1 at fast ones, 2:1 around 200 bpm (Friberg & Sundström 2002; Honing & de Haas 2008). Rule: a 12-row bar
  (`rows: 12`, `beats: 4`) for swing and shuffle, never displaced 16ths.
- **Catchiness**: the fastest-recognised songs in the large-scale hook study (12,000+ players) repeat a short,
  rhythmically distinctive figure with a simple structure (Burgoyne et al. 2013); earworms are faster than
  average, use common global contours and a few unusual intervals (Jakubowski et al. 2017). Rule: the hook repeats
  its rhythm exactly, anticipates the downbeat once per two bars, and sits over a kit and bass that keep the grid.
- **The corpus bands** (the index per bar, p25 / median / p75 over the looping songs; `offbeat` = share of onsets
  off the beat):

  | lane | stage corpus (9 loops) | RPG corpus (28 loops) |
  |---|---|---|
  | lead | 0.62 / 3.25 / 3.85 (max 4.29) | 0.01 / 0.22 / 0.93 (max 3.29) |
  | chords (second pulse) | 0.0 / 0.18 / 2.97 | 0.07 / 0.38 / 0.91 |
  | bass | 2.15 / 4.0 / 4.5 (max 6.62) | 0.03 / 0.28 / 0.81 |
  | kick + snare | 1.0 / 1.38 / 3.29 | 0.05 / 0.65 / 1.12 |
  | offbeat lead / bass / kick+snare | 0.68 / 0.67 / 0.57 | 0.44 / 0.47 / 0.61 |

  Thirteen further reference files (a desert-stage theme from a 1998 console adventure, a 1960s funk single, a
  late-1960s rock single, a late-1990s Eurodance single, a 1990s alternative-rock single with an odd-meter riff,
  the pop theme of a 2004 console puzzle-action game, a 1992 console beat-em-up stage theme, a 2006 console
  storefront theme and five pop / pop-rock singles from 1985-2007), measured whole with roles by stream
  statistics, widen the picture by genre: rock leads 0.2-2.8 (median 0.7) over basses 0.2-3.3 (median 1.3); pop
  leads 0.0-2.8 (median 2.2) over basses 0.2-1.3; the funk single lead 2.5 / bass 2.1 / kick+snare 0.9 with the kick
  on the one and every and; the Eurodance single bass 1.5 (octave 8ths) under a kick on every beat; action game
  music leads 0-5.8, median 3.3 (the desert theme's strummed lead at 5.8 with 80% of its onsets off the beat is the top of
  everything measured). The medium band the knob aims at (lead 1-4, bass 1-4, kick+snare up to 2.5) covers all of
  them except the RPG calm.

  The two favourite corpora sit at the two ends of the scale: the stage corpus is a syncopated funk-rock corpus
  (octave-bounce and anticipation basses at 4 per bar, leads with two thirds of their onsets off the beat), the
  RPG corpus is near-classical. The straight generator's pop song scores lead 1.27, bass 0, drums 0, below both
  on the bass and the kit; `--syncopation 2` takes it to lead 4.5, kit pushes and bass leans; the grooves score
  (pop, same seed) ska lead 1.2 / chords 7.0 (every skank off the beat), one-drop 2.6 / 2.0 / 2.8 / 2.6, funk
  4.2 / 6.1 / 5.6 / 0.7, tropical 4.6 / 6.1 / 1.2 / 0 (dembow: a third of the kick+snare off the beat).

## Listening pages

One song at a time: a page with more than one player pauses every other `<audio>` when one starts; a page that
mixes live emulator audio with a reference clip pauses one when the other starts. Every claim about sound on a
page is next to the audio that proves it and the piano roll that shows it.
