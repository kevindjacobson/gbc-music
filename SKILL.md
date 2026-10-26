---
name: gbc-music
description: Put background music into a Game Boy Color ROM with the four-channel driver (music.c) — compose.py generate/compile (fusion, ambient, chip, pop, rock styles; --form stage|verse-chorus|aaba|blues12, a --progression library, --texture, --organic), music_init/music_tick wiring, the fusion idioms (chord arpeggio, echo, trills, slap bass, fusion drums) with register facts, song form (section plans, chord progressions with moods, repetition rules, four-channel section contrast), mix rules, timbre and modulation recipes (duty sequences, wave tables measured from commercial cartridges, level envelopes, pitch envelopes, detune, tremolo, portamento, the RPG kit), audio_probe.py verification, the Music table for a design document, and the player ROM / MIDI / WAV outputs
---

# gbc-music: the soundtrack is part of the game

Every ROM ships with music: a game gets a theme that keeps playing during gameplay; a synth gets a quiet
`ambient` bed or whatever texture its brief names (the brief's words win over this skill; a brief that asks for
silence or for its own generative sound gets that, and says so in the design document). Verify with
`audio_probe.py`: at least two channels sounding and real note changes after START. Music is judged by ear:
spend a build cycle on it.

This skill is opinionated: every rule below is a measured fact or a listening verdict, stated as a default rather
than a menu. `$SKILL` is the directory this file lives in, wherever it was installed (`.claude/skills/gbc-music`,
`.opencode/skills/gbc-music`, a checkout); the `README.md` at that root covers installation and dependencies.

## 1. The pipeline (ten minutes, four commands)

```
python $SKILL/scripts/compose.py generate --style fusion --key F# --bpm 100 --bars 32 --seed 7 --organic 2 --out music/main.txt --report qa/music_gen.json
python $SKILL/scripts/compose.py compile music/main.txt --out src/music_data.c --report qa/music_compile.json
make                                   # or whatever builds your GBDK project
python $SKILL/scripts/audio_probe.py --rom build/<game>.gbc --out qa/audio --seconds 10
```
Wire it in `src/main.c` (`music_tick()` once per frame, after the frame's effects update; `docs/INTEGRATION.md`):
```c
#include "music_data.h"            /* generated: extern const Song song_main; */
/* title_enter(): */  if (!music_playing()) music_init(&song_main);   /* keeps playing into PLAY */
/* gameover_enter(): */ music_set_volume(6);   /* duck under the sting; music_set_volume(15) when PLAY restarts */
```
A second song (`--name song_title`, compiled in the same `compile` call) can start in `title_enter()` and the main
theme in `play_enter()`. `music_stop()` silences the four channels. `music_bar()` / `music_row()` let the picture
follow the music (a palette step per bar, a pulse on row 0).

`--bend sparse|none|normal` sets how often the bass and lead bend into a note (§3).
Styles: `fusion` (the house style, see §3), `rock` (the stage-corpus loop by default, §7), `pop`
(a verse-chorus song, §7), `chip` (plain pop loop when the brief wants a cheerful, simple tune), `ambient` (drone +
sparse notes for synths and calm scenes). `--form stage|verse-chorus|aaba|blues12`, `--progression stage_a|axis|...`
and `--texture plain|fusion` are independent knobs on pop, rock and chip (§7): form from the brief's shape, texture
from its mood; the fusion texture on a stage form is the house blend. `--seed` changes the tune,
`--key` and `--bpm` set its mood; the same arguments always produce the same score, so note them in the design document.
Listen before you ship: generate two or three seeds, probe each, keep the one whose piano roll looks alive
and whose numbers read right (§5). Keep the chosen score in the project (`music/main.txt`): the ROM is the
deliverable; the score is how the next build changes the tune.

## 2. The score is yours to edit

`music/main.txt` is plain text: header, instruments, chords, then one block per bar with four lanes
(`lead:` pulse 1, `arp:` pulse 2, `bass:` wave, `drum:` noise), 16 cells per lane = 16th notes.
`compose.py --help` has the full grammar. The cells you will actually touch:

| cell | meaning | driver effect |
|---|---|---|
| `F#4@lead` | note with instrument | strike (NRx1 duty, NRx2 envelope, NRx3/4 period + trigger) |
| `.` / `-` | continue / key off | nothing / silence the channel |
| `F#4:maj7` | **fusion chord**: cycle F#4 A#4 C#5 F5 one note every `arp:` frames | NRx3/4 rewritten without retrigger, no click |
| `C#6~` `C#6~2,3` | vibrato (depth, rate) | period +/- depth each `rate` frames |
| `G#5^2` / `G#5'2` | trill a whole row / 2-frame mordent | note alternates every frame |
| `F#2/-2,6` | bend: start a tone below, land on F#2 in 6 frames, hold | the slap articulation; `/-4` alone is a raw slide that never stops (synth use only) |
| `C5>D5` | 32nd pair: D5 struck mid-row | two notes in one 16th |
| `F#3!3` | cut after 3 frames | staccato slap pop |
| `A4v6` | this note at volume 6 | accents, ghost notes |
| `echo:5,3` on the arp lane | pulse 2 replays pulse 1 five frames late, 3 steps quieter | the doubled-line pair of the reference |
| `G4=6` | portamento: glide from the previous note onto G4 in 6 frames | NRx3/4 rewritten per frame, no retrigger (§8) |
| `C3%4,8` on the bass lane | tremolo: volume dips 4 steps every 8 frames | NR32 level step, click-free; on a pulse it re-strikes (§8) |
| `C3@bell` | an instrument with its own motion (`decay=`, `penv=`, duty / wave sequence) | see the recipe table in §8 |
| `KH` `SH` `sh` `O` `T` `C` | kick+hat stack, snare+hat, ghost snare+quiet hat, open hat, tom, crash | NR42/NR43 presets, the stack re-strikes 3 frames later |

Tempo: rows are 16ths, `bpm: 100` = 9 frames per row. Twelve bars of unique material cost about 2 KB of ROM
(bar lanes that repeat are stored once); a 32-bar fusion theme is ~6 KB, an ambient bed ~1 KB. All of it lives
in bank 0 next to your code: if `romusage` shows bank 0 nearly full, shorten the song or raise `loop:`.

## 3. The fusion idioms (what the reference does, in register terms)

Reference: a late-80s console fusion composer's title theme. 100 bpm, F#/C# centre, maj7/add9/m9 voicings, modulations
every 8-16 bars, ~14 notes per second on the chord voice, 2790 drum hits in four minutes. On four Game Boy channels:

- **Pulse 2 = the chord, not a melody.** A 3-4 note voicing cycled one note every 3-4 frames (`arp: 3`) reads as a
  chord at frame rate. Use the colour tones (7th, 9th), drop the fifth: `maj9 = 0 4 11 14`, `m9 = 0 3 10 14`.
  Sustain it: the arp instrument's envelope must have step 0 (`env=90`), a decaying envelope dies in 8 frames and
  the chord vanishes (the probe then shows pulse2 at 0% active).
- **Pulse 1 = a lead that moves.** 16th-note scalar runs (lydian over maj7, dorian over m7), a 2-frame mordent on
  the first note of a phrase, a trill or vibrato on the note it lands on, rests between phrases so the echo and
  the chord breathe. Range E3..A5 (the reference's register); vibrato = 2 period units every 3 frames after 12 frames held (`vib=2:3`).
- **Echo section.** For 8 bars the chord drops and pulse 2 replays pulse 1 four to six frames later, 3-4 steps
  quieter (`echo:5,3`): the doubled-line pair in the reference. The ring buffer carries the lead's trills and
  arps, so the echo is exact.
- **Wave = slap bass.** Bright shape (`saw`), B1..A2, 8ths alternating with 16th octave bounces (root, root+12),
  a chromatic approach note into the next chord on the last 16th, now and then a downbeat that bends into the root
  from a tone below (`/-2,6`). Staccato with `!3`/`!4` so the pops read. The wave channel sounds an octave below the pulse
  table for the same period: the driver adds 12 semitones for you, write the pitch you want to hear.
- **Noise = a fusion kit on a 16th grid.** Hats on every 16th (quiet ones between), kick on 1 and 3 plus a
  syncopated one, snare on 2 and 4 with ghost snares on off-16ths, kick+hat and snare+hat stacks, a fill in bar 8.
  Presets: kick `NR42 F1 / NR43 5C`, snare `D2 / 46`, hat `61 / 15`.
- **Bends are rare and always resolve onto a chord tone** (the author, after listening: "less pitch bending, or have
  the bends resolve nicely"). A bend starts a semitone or a tone away, never more than a minor third, lands exactly
  on the written note within 4-6 frames and that note is then held long enough to be heard as the arrival. Never
  on a 32nd. The bass bends only on a downbeat, at most every other bar; the lead only into a phrase's target note.
  `compose.py generate --bend sparse` (default) does this, `--bend none` turns bends off for a brief that wants a
  clean sound, `--bend normal` is the upper limit. The raw `/-4` slide (no resolution) is for synth sound design.
- **Harmony.** 8-bar sections, four two-bar chords each, voiced with the top note moving least; modulate down a
  major third or up a minor sixth every 8-16 bars (F# -> D -> A -> F#).

## 4. Mix rules (so the lead reads on a tiny speaker)

- Lead loudest (`env=C2`..`F2`), chord one step under (`env=90`/`A0`), bass `vol=11..13` on the wave channel
  (its NR32 has only full/half/quarter), hats quiet (`61`), kick and snare full. Ambient: everything at 5..9.
- One effect per cell; one chord per voice; never two melodies at once. If the lead and the chord fight, give
  the chord a 25% or 12.5% duty (`duty=25`), it steps back without losing its colour.
- SFX win: every sound effect calls `music_sfx(channels, frames)` before it writes a register; the driver yields the
  channel and re-strikes its note when the effect ends. Put short SFX on pulse 1
  and noise; leave pulse 2 (the chord) and the wave bass to the music unless the sound needs them.
- Duck, do not stop: `music_set_volume(6)` under a game-over sting or a dialogue, back to 15 afterwards.

## 5. Verify by listening (`audio_probe.py`)

`python $SKILL/scripts/audio_probe.py --rom build/<game>.gbc --out qa/audio --seconds 10` runs the ROM five
times with identical input (once per isolated channel) and writes `audio_report.json`, `audio.wav` (the play
window) and `pianoroll.png` (pitch per channel over time). Read it like this:

- `play.music_detected` true and `music_during_gameplay` true: the theme survives START.
- `play.channels.pulse2.arpeggio.detected` true with `step_frames` 3-4: the fusion chord is there.
- `pulse1.distinct_pitches` >= 12 and `pitch_changes` >= 40 in 10 s: the lead moves. `wave.distinct_pitches` 6-20
  (bends widen it), `noise.hits` 40-70 per 10 s for a fusion kit, 0-5 for ambient.
- `title.music_detected` true unless you chose a silent title on purpose.
- LOOK at `pianoroll.png`: a dense zig-zag row on pulse 2 is the chord; the lead should be runs and held notes,
  not one flat line; the bass should bounce between two octaves; the noise lane should show a regular grid.
- `solo_reliable` false means your code rewrites NR51 every frame (panning); the per-channel numbers are then
  approximate. Write NR51 once in `sfx_init()`.
- Nothing on a channel you expect to hear: a decaying envelope on a held note (use step 0), a wave instrument
  whose `vol` maps to NR32 "off" (< 1), or an SFX hold that never ends (`music_sfx` frames too large).

Run the probe again after the final build and quote its numbers in the QA notes.

## 6. The design document: a Music table

Add a `## Music` section to the project's design document with a table a reviewer can read:

| what | value |
|---|---|
| style / key / tempo / seed | `fusion`, F#, 100 bpm, seed 7 (`music/main.txt`) |
| where it plays | title + play; ducked to 6 on game over |
| channels | pulse1 lead, pulse2 maj9/m9 chord cycle (3 frames) + echo in bars 17-24, wave slap bass, noise kit |
| hooks | `music_bar()` steps the background palette every bar; `music_row()==0` pulses the HUD icon |
| SFX priority | jump/pickup on pulse 1, hit on noise, select on pulse 2; `music_sfx` holds 8-40 frames |
| verification | `qa/audio/audio_report.json`: 4 channels active, arpeggio 3.0 frames, 7 onsets/s |

For a synth, the table says which parameter of the picture drives which musical parameter (chord root from
the hue, tempo from the speed, `music_set_volume` from the brightness) or that the brief's own sound replaces
the driver, and why. A song with a form adds a row `form | verse-chorus, 48 bars, axis (I V vi IV), loop at bar 5`.

## 7. Song form: sections, progressions, repetition (any style; form and texture are separate knobs)

A loop is not a song. The reference corpora (a classic action-platformer's stage loops and a classic handheld RPG's
soundtrack, transcribed and counted) and the pop/rock literature agree on the grain: 4-bar phrases stacked into 8-bar sections, a phrase repeated
with its ending changed, a new harmony or a lifted lead when the section changes. `compose.py generate` has two
independent knobs for this: `--form` (the section plan) and `--texture` (plain, or the fusion idioms of §3 laid
over whatever form). A stage form with a fusion texture is one command, not a contradiction.

```
python $SKILL/scripts/compose.py generate --style rock --key E --bpm 146 --bars 24 --seed 3 --out music/main.txt                       # rock default = the stage-corpus loop A B C
python $SKILL/scripts/compose.py generate --style rock --key E --bpm 146 --bars 28 --seed 3 --texture fusion --out music/main.txt      # the same form, fusion chord cycle / trills / slap bass / echo B
python $SKILL/scripts/compose.py generate --style pop  --key C --bpm 120 --bars 48 --seed 1 --progression axis --out music/main.txt    # verse-chorus song
python $SKILL/scripts/compose.py generate --style rock --key A --bpm 112 --bars 40 --seed 5 --form blues12 --out music/main.txt
python $SKILL/scripts/compose.py generate --style fusion --key F# --bpm 100 --bars 32 --seed 7 --form aaba --out music/main.txt
python $SKILL/scripts/compose.py styles        # forms, textures, the progression library with moods, chords, waves, drums
```

**The plan** (`--bars` picks the size: 16 / 24 / 28 for stage, 32 / 48 / 64 for verse-chorus, 32 / 40 for aaba, 28 / 40 / 52 for blues12):

| form | sections (bars) | use | where it comes from |
|---|---|---|---|
| stage 24 (rock default) | A 8, B 8, C 8, loop at A; 28 adds a 4-bar intro the loop skips; 16 = A B | stage themes, anything that must loop for minutes | the stage corpus (one transcription per theme): 5 of its 9 looping themes are 24-bar A B C loops, 2 are 16-bar A B, 2 are 8 (boss, password); 7 of 9 start straight in, median 146 bpm, 8 of 9 minor |
| verse-chorus 48 (pop default) | intro 4, verse 8, pre-chorus 4, chorus 8, verse 8, pre-chorus 4, chorus 8, outro 4 | a song with a hook; 64 adds a bridge 8, 32 drops verse 2 | pop theory (Nobile, Open Music Theory); the lift is also the RPG corpus's habit (20 of 23 looping songs raise the lead in the second section) |
| aaba 32 | A 8, A' 8, B (middle eight, new chords or key) 8, A 8 | title themes, fusion | the 32-bar song form |
| blues12 40 | intro 4 (the turnaround), head 12, head an octave up 12, solo 12 | swagger | the twelve-bar blues |

Each 8-bar section is a 4-bar phrase and its repeat with the last bar changed (the stage corpus's A A' B B' C C'); the
stage sections each get their own progression and their own motif, C sits a fifth up with the open kit (`--lift
fifth|sixth|octave`: the references lift their second section 1-8 semitones; an octave drifted the lead beyond
every corpus song when measured).

**Progressions** (Roman numerals resolved against `--key`; `--progression "I bVII IV I"` takes your own; several
separated by ` | ` go to the sections: stage A | B | C, verse-chorus chorus | verse | bridge):

| name | numerals | gives |
|---|---|---|
| stage_a / stage_b / stage_c | i i bVI bVII / i i iv bVII / i IV bVII i | the stage corpus's A, B, C sections; stage default for rock: driving aeolian minor, VII pulls home, the dorian IV lifts C |
| stage_shuttle / stage_offtonic / stage_pedal | i bVII i bVII / bVI bVI i i / i i i iv | the corpus's two-chord drive / off-tonic start / pedal riff |
| boss | i i i i IV IV ii V | the stage corpus's boss loop (8 bars) |
| cadential / town | I V V vi I V V I / I IV vi I vi IV vi V | the RPG corpus's cadential major: I-V-I is the most common move in the corpus |
| axis | I V vi IV | bright pop anthem (verse-chorus default for pop/chip) |
| sensitive | vi IV I V | the same chords from the minor: wistful |
| doowop | I vi IV V | 1950s sweetness |
| hopscotch | IV V vi I | modern pop, floats, lands by a skip |
| threechord | I IV V IV | garage rock (rock default, with mixolydian) |
| mixolydian | I bVII IV I | classic-rock swagger; bVII is the rock dominant |
| shuttle / dorian | I bVII I bVII / i IV i IV | two-chord riff rock / funk groove |
| andalusian / aeolian | i bVII bVI V / i bVI bIII bVII | dramatic or epic minor |
| plagal / puff | I IV iv I / I iii IV I | nostalgic sigh / gentle folk-pop |
| turnaround / pachelbel | I vi ii V / I V vi iii IV I IV V | jazzy turnaround / stately ballad |
| fanfare | bVI bVII I I | the fanfare cadence: victory, level clear |
| blues12 / blues12q | I I I I IV IV I I V IV I V | twelve-bar blues (q = quick change to IV in bar 2) |

The chorus plays the loop at one chord per bar and starts on the tonic; the verse takes the rotation that starts
off the tonic (vi for axis) at two bars per chord, so the chorus's I is an arrival. The pre-chorus is IV ii V V
(IV IV V V for mixolydian, bVI iv V V for minor): it ends on V, the lift. The bridge starts on a chord the song
has not used (vi or IV; bVI in minor), avoids I, ends on V. Rock plays power chords (`:5`) on pulse 2; the blues
plays dominant sevenths. In the stage form the harmony changes per section (the stage corpus's contrast is harmonic: VII->i is
its most common move, then i->iv and i->IV), not by a key change.

**Texture** (`--texture plain|fusion`): plain = triads / power chords, straight kit, vibrato on held notes.
`fusion` keeps the form and swaps the idioms: the pulse-2 chord gets colour tones (maj -> maj7, min -> m9, power
chord -> add9), the lead opens each phrase with a 2-frame mordent and lands on a trill, the wave plays the slap
bass of §3 (walk / bounce / slap / pedal with octave pops), the kit is the 16th fusion grid, and the bridge or B
section drops the chord for the echo voice (`echo:5,3`, `echo:off` at its end). Bends stay rare and resolving in
both textures (`--bend`). Pick form from the brief's shape (loops for minutes -> stage; a song -> verse-chorus)
and texture from its mood (fusion sparkle -> fusion; punchy -> plain), independently.

**Repetition rules** (what the generator does, and what to keep if you edit the score):
- A phrase repeats, its last bar changes. Verse = statement (bars 1-2), restatement with the last note changed
  (3-4), departure a step higher (5-6), conclusion that cadences on the tonic (7-8). Stage A/B/C = motif, motif
  with the last note changed, motif, motif cadencing (the stage corpus's A A' B B' C C').
- The chorus is the hook: a 2-bar motif three times, then the hook with a cadence (AAAB). Every chorus repeats
  it note for note; only the kit opens up on the last one.
- The second time through, one note is different: verse 2 = verse 1 with bar 4's last note changed and an
  octave-up ending. fusion A' = A with its last 2-bar lead phrase regenerated.
- The pre-chorus takes the hook's first bar and sequences it up a step each bar over a snare build.
- Call and response in rock: the riff speaks in bar 1 (bass + pulse 2), the lead answers in bar 2. In the
  blues the call is bars 1-2, 5-6, 9-10 (aab) and the bass answers.
- Fills close every 4 bars and land on beat 1; a crash opens the chorus; the outro ends on a crash and a hold.

**Section contrast on four channels** (no second guitar to add, so it is channels, register, duty and the grid;
in the RPG corpus the second pulse is a counter-melody in 18 of 24 looping songs, parallel thirds in only 3,
and the bass is arpeggiated figures and walking lines; in the stage corpus the bass walks or bounces octaves under a
~15-hit-per-bar kit and pulse 2 is a counter line, never a held chord):

| section | pulse 1 lead | pulse 2 | wave | noise |
|---|---|---|---|---|
| stage A | motif, mid register | full chord cycle (rock: riff +12) | octave bounce (rock: riff) | full kit, fill every 4 |
| stage B | new motif, same register | pad (fusion: echo of the lead) | walking | 16th hats, snare build into C |
| stage C | third motif an octave up | full cycle, higher voicing | bounce, rare resolving bend | full kit, crash |
| intro | rest, then the hook's first 2 bars | quiet pad (`@pad`, 12.5% duty) | roots on the beats | hats, then kick and snare |
| verse | motif, mid register, rests | pad struck on 1, `-` on 3 (rock: the riff +12) | root 8ths + fifth (rock: the riff) | kick 1/3, snare 2/4, closed 8th hats, fill every 4 |
| pre-chorus | hook's first bar, up a step per bar | pad, then full chord | walking climb to V | 16th hats, snare build |
| chorus | hook an octave up on `@hook` (brighter duty) | full chord cycle, octave re-voicing (rock: `:5`) | root/octave bounce, rare resolving bend | open hats, syncopated kick, crash |
| bridge | long low notes, new chords | low pad | held roots | half time |
| outro | hook, then the hook cadencing | full, then held | bounce, then hold | fill, crash, stop |

Listen for it: the piano roll shows the verse pad as short dotted bursts, the chorus as a continuous zig-zag,
the lead jumping an octave, the kit thickening. The fusion texture stays the house style; the forms are the frame around it.

**Organicness: run `--organic 2`, then edit the score by hand.** Measured against the stage and RPG
corpora (`docs/DESIGN_NOTES.md`), a straight generator reuses
its bar rhythms twice as much as they do (0.9 vs 0.44 of bars), writes phrases that are copies (novelty 0.3-0.4
vs 0.84), hardly rests (0.03-0.10 vs 0.24) and only at phrase ends, and keeps a flat density. `--organic 2`
(deterministic, seeded, `0` = untouched) fixes the cheap half: repeats come back with a note changed or shifted,
phrases breathe at their ends, every section closes with a fill, a bar drops its hats, pulse 2 sits out a bar,
off-beat notes get `v` accents, the bass anticipates a downbeat now and then, and the timbre plan of §8 is applied
(the lead turns 25% bright on the first note of a pre-chorus / bridge / B section, the bass takes the organ2 table
there, a repeated lead note becomes an `F3` stab with the next note restoring the lead, the anticipation is a wave
pluck, B sections get the RPG kit in the plain texture); harmony, tempo, form and bends are untouched, detune is
never added, and the probe still passes. Use it by default on games (not on `ambient`). The cartridges switch
lead identities 3-19 times a minute at phrase and section boundaries and the wave bass alternates tables on a third to
all of its notes; the layer puts us at 3-5 lead identities and about 2 bass identities per song, so a hand edit that
adds a second articulation pair is still worth it. What it cannot do, and
what you should do by hand in `music/main.txt` after listening (hand-edited scores measured this way were the
most human-sounding of the three versions compared):
- Let the lead sit out a whole bar once per section while chord and bass carry (`-` on the lead lane).
- Put a new idea in the second time round: a 32nd pair (`A5>G5`) or a different ending, not just a moved note.
- Shape the accents by phrase (`v13` on the arrival, `v9`-`v11` on pick-ups), and thin the ornaments: one mordent
  per phrase, not one per bar.
- Reshape, do not just append, the fill (`KH h H . SH . h . KH h . s S T T -`), and leave the odd hat out.
- Keep the chord cells, `loop:` and the instrument lines exactly; bends rare and resolving; no detune.

## 8. Timbre and modulation (instrument recipes, what the real cartridges do, when to modulate)

The APU has four fixed voices; the colour comes from how an instrument moves inside a note. Everything below is an
`inst` parameter or a cell effect; the driver does the per-frame work. Register truths that shape the rules (Pan Docs,
measured in PyBoy on the cartridges, the measurements in `docs/DESIGN_NOTES.md`):

- **Duty (NRx1) can change any frame without a re-strike**: a duty sequence is free and click-free. **NRx2 (volume
  envelope) only loads on a trigger**: every pulse volume change is a re-strike (a click, a phase reset). **NR32 (wave
  level: full / half / quarter / off) changes silently**: the wave channel is the only voice with click-free dynamics.
  Wave RAM is rewritten behind `NR30 = 0` and the note re-triggered (a small click per table step). Hardware sweep
  (NR10) lives on pulse 1 only, keeps running across notes and fights re-triggers: the driver zeroes it and does every
  pitch movement in software, on all three tonal channels alike.
- **75% duty = 25% inverted** (identical in mono; the RPG cartridge uses 75% on 90% of its pulse frames, the other three
  cartridges use 50% on 60-100% and 25% for the second voice). 12.5% is thin and distant (echo voices).
- **7-bit LFSR noise is a tone** (NR43 bit 3): every "tonal" hit in the RPG kit (kick body, triangles) and 15 of
  the action-adventure's 25 intro drum hits use it. 15-bit is white noise (snares, hats).
- **Panning is static in practice**: in two minutes of each cartridge NR51 stayed `FF` except the RPG cartridge's intro
  (36 writes, hard solos). SFX owns NR51 here; stereo is not the music's tool.
- **Vibrato is delayed and shallow**: the RPG corpus's house values are `delay 8-32 frames, depth 1-4 period units, 3-8 frames
  per half period`; wide undelayed vibrato is a special effect (its ghost-town theme). Our `vib=2:3` = depth 2 after 12 frames.

**Recipes by role** (`inst` line fragments; `compose.py styles` lists every wave and drum):

| role | line | what it echoes |
|---|---|---|
| lead, round | `pulse duty=50 env=C7 vib=2:3` (pace 7 = the slow RPG decay, 1.3 s; `C2` dies in 22 frames and is for busy lines) | the action-adventure's and the puzzle game's pulse 1; the RPG cartridge's `A7 B7 C7` envelopes |
| lead, bright | `pulse duty=25 env=C7 vib=2:3` | the classic console lead, the puzzle game's pulse 2 |
| lead, shimmer | `pulse duty=50,25 rate=2 env=C7` | the RPG engine's duty-cycle pattern (cries 3,3,0,0 / 2,2,1,1), LSDj W column |
| lead, chorus lift | `pulse duty=12,25,50,25 rate=4 env=C7` | a slow PWM sweep (hUGETracker duty subpattern): use it when the chorus should open up |
| pad / strings | `pulse duty=50 env=0B` (vol 0, up, pace 3: 0.7 s swell) | Furnace "up = attack"; or the wave `attack=8` below |
| pluck | `pulse duty=25 env=F1 penv=12,1` | hUGETracker "start an octave up", the RPG corpus's title pluck `12,12,1` |
| stab / staccato | `pulse duty=50 env=F3` | the RPG engine's note type 12,12,1-2 |
| unison / chorus pair | second pulse `duty=50 env=A7` on the lead's notes, `detune=0` (exact unison, what the cartridges do); `detune=1` on the double only, at most, and only when the brief asks for a wobble (the rule: be careful with detune) | the RPG cartridge's intro doubles in exact unison; its pitch offset 1 is the rare exception |
| octave pair | arp lane an octave up, `duty=12 env=80` | LSDj `PU2 TSP 12`; the action-adventure |
| bass, RPG | `wave vol=12 shape=rsaw` (`rsaw2` softer, `organ2` the city two-hump) | the RPG corpus's waves 0 / 1 / 5 |
| bass, hollow | `wave vol=12 shape=pwm50` | square-in-wave: the action-adventure's bass is this (recovered from its audio), with NR32 for dynamics |
| bass, slap | `wave vol=13 shape=saw` + `!3` pops, `/-2,6` rare bends | the fusion style (§3) |
| bass, soft | `wave vol=12 shape=tri` or `sine` | the classic console triangle; the puzzle game plays a pure sine on its wave channel |
| bell | `wave vol=15 shape=bell decay=8` | sine + 3rd partial, NR32 full -> half -> quarter -> off; the note ends by itself |
| wave pluck / harp | `wave vol=15 shape=tri decay=4 penv=12,1` | LSDj wave pluck |
| organ / drawbars | `wave vol=12 shape=organ` or `organ2` | multi-hump tables |
| pad, swell | `wave vol=12 shape=organ2 attack=8` | quarter -> half -> full over 24 frames, click-free |
| pad, PWM | `wave vol=12 shape=pwm50,pwm37,pwm25,pwm12 rate=4 loop` | LSDj synth PHASE sweep (wavetable synthesis) |
| pad, filter-close | `wave vol=12 shape=saw,soft,sine rate=6` (one-shot) | LSDj synth PLAY ONCE |
| dark / spooky | `wave vol=12 shape=jagged` or `dark` | the RPG corpus's jagged ghost-town wave, its wave 2 |
| kick on a pulse | `pulse duty=50 env=F1 penv=12,5` on the lead or arp lane | LSDj bass drum (sweep 63 at C-6), in software |
| toms on a pulse | `pulse duty=50 env=D2 penv=5,3` | LSDj `P` + PITCH DRUM |
| kick on the wave | `wave vol=15 shape=tri decay=3 penv=12,4` | LSDj wave kick |
| noise kit, RPG | drum letters `B` (buzz kick: 7-bit 1.4 kHz then hiss) `Q` tight snare `N` soft snare `P` bright snare `M` metal ting `t` 7-bit tom `X` cymbal `c` crash `D` snap | the RPG corpus's kit, decoded from register traffic to NR42/NR43 |
| noise kit, fusion | `K S H O T C` + ghosts `k s h` | §3 |
| noise "note" | `Z` (7-bit at a 74 Hz loop) | LSDj 7-bit noise notes |

**Modulation rules** (what to add, and what not to):

- **Vibrato: delayed, on held notes only.** Give every lead `vib=2:3` and let the driver add it after 12 frames; a
  16th-note run never vibrates. It needs a note that is still sounding: pair it with a pace-7 or step-0 envelope
  (`C7`, `C0`), not the 22-frame `C2` decay. Cell vibrato (`~3,2`) is for one expressive long note. Wide fast vibrato (`vib=4:1`)
  is a special effect (sirens, ghosts), not a style.
- **Tremolo: pads on the wave channel only** (`C3%4,8` = full / half every 8 frames via NR32, click-free). On a pulse it
  re-strikes every step; the compiler warns under 6 frames. Never on a lead.
- **Portamento: sparingly, and it must land.** `G4=6` glides from the previous note in 6 frames; use it on one step of a
  phrase (the arrival), never on a run. Portamento and the resolving bend (`/-2,6`) are the two legal pitch moves; the
  raw `/-4` slide is synth sound design. The rule stands: bends are rare and resolve onto the written note.
- **Duty sequences are a timbre, not an effect.** `50,25 rate=2` reads as one shimmering voice; `12,25,50,25 rate=4` is
  a slow PWM that lifts a chorus. Do not sequence the chord voice (the arpeggio already moves) or the echo.
- **Pitch envelopes make percussion and plucks**, never melodic bends: `penv=12,5` on a pulse is a kick, `5,3` a tom,
  `12,1` a pluck's attack. A kick instrument on the arp lane for the downbeats frees the noise channel for hats.
- **Wave dynamics come from NR32 steps**: `decay=` for bells and plucks (the note ends on its own, no `-` needed),
  `attack=` for a pad that swells, `%` for tremolo. Pulse dynamics are `v` accents per note.
- **Be careful with detune** (the rule). Default is exact unison or an octave pair, which is what the cartridges
  do. `detune=1` goes on the doubling voice only, never on the lead, never on both voices, never on the bass, and only
  for a section that wants a wobble. `detune=2` or more, or detune on one voice alone, reads as out of tune on a
  Game Boy speaker; everyone hears it.
- **Wave sequences re-trigger at every step** (a click): rate 4-6 for pads, 2-3 only for an attack of two or three
  tables; a looping sequence is a texture for pads and drones, not for a bass line. 16 tables per song in total.
- **7-bit noise for anything that should ring** (tings, toms, the kick body); 15-bit for air (snares, hats).
- **Timbre variety on one channel** (measured on the cartridges, `docs/DESIGN_NOTES.md`):
  leads carry 6-11 instrument identities per piece and switch 3-19 times a minute, almost always at a phrase or section
  boundary (the action-adventure: 8 switches in 2.5 min, 12 s apart, runs of 112 notes; the treasure platformer: 16 of 48 runs are 8+ notes).
  The note-to-note switches that exist keep the duty and change only the envelope: loud/quiet `91`/`61`, hold/decay
  `A0`/`A7`, stab/sustain `82`/`30` (the puzzle game's chord voice alternates them on 86 of 179 runs). A duty change means a
  new section or voice. Basses alternate two tables or two NR32 levels (the action-adventure switches between two
  square-in-wave widths 82 times in 2.5 min); the kit alternates 2-3 hats/snares per bar. Recipes:
  - *Lead by section*: `inst leadA pulse duty=50 env=C7 vib=2:3` for A, `inst leadB pulse duty=25 env=C7 vib=2:3` for B,
    `inst leadC pulse duty=12,25,50,25 rate=4 env=C7` for the lift; switch with `@leadB` on the section's first note only.
  - *Articulation pair*: same duty, two envelopes (`inst hold pulse duty=50 env=C0`, `inst stab pulse duty=50 env=F2`);
    write `@stab` on the short notes and `@hold` on the long ones, like `A4@stab . C5@hold . . .`.
  - *Bass table alternation*: `inst bass wave vol=12 shape=rsaw`, `inst bass2 wave vol=12 shape=pwm50` (or the same
    table at `vol=6` for the half level); `@bass` on beats, `@bass2` on the octave bounces.
  - *Kit by section*: hats `H`/`h` in the verse, `O` and the RPG kit's `Q`/`X` in the chorus; a crash `c` on the section's
    downbeat. Detune stays a pair's job (§ above): never use it as the "second instrument" of a lead.
- **Costs**: every pulse/wave instrument is 8 bytes, a drum 4; the per-frame driver cost is in `docs/LIMITS.md`
  (the wave-table step is the one expensive event). The cell format is unchanged: old scores compile as before.

## 9. Other outputs and the docs

The same score has three more targets, all scripts of this skill:

```
python $SKILL/scripts/song_rom.py music/main.txt --out build/<game>_music.gbc   # standalone player ROM (title screen, START/SELECT cycle songs)
python $SKILL/scripts/song_midi.py music/main.txt --out music/main.mid          # General MIDI: one track per lane, chords expanded, bends as pitch bend
python $SKILL/scripts/song_wav.py music/main.txt --out music/main.wav --mp3     # the chip rendered headlessly (PyBoy), 32768 Hz
```
Use the WAV for a listening page or a release note, the MIDI when the score is wanted in a DAW, the player
ROM when the music is the deliverable (a synth brief, a jukebox). `docs/README.md` is the index; `SCORE_FORMAT.md`
the complete grammar; `OUTPUTS.md` the integration of the driver into any GBDK project; `DESIGN_NOTES.md` the
measured facts behind every rule here; `docs/PIANOROLL.md` the interactive piano roll for a listening page.
