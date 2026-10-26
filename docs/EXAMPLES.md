# Twelve worked examples

Each example is a complete command sequence from an empty directory (`export SKILL=/path/to/skills/gbc-music`
first; `python` = a Python with numpy, pyboy and Pillow for the WAV and probe steps), the numbers it produced when
this page was written, and what to listen for. `docs/check_examples.py` runs every block.

## 1. The fusion theme (the house style) and all three outputs

```
export SKILL=/path/to/skills/gbc-music
mkdir ex1 && cd ex1
python $SKILL/scripts/compose.py generate --style fusion --key F# --bpm 100 --bars 32 --seed 7 --out main.txt --report gen.json
python $SKILL/scripts/song_rom.py main.txt --out main.gbc
python $SKILL/scripts/song_midi.py main.txt --out main.mid --report midi.json
python $SKILL/scripts/song_wav.py main.txt --out main.wav --mp3 --report wav.json
python $SKILL/scripts/audio_probe.py --rom main.gbc --out probe --pre wait:60 --seconds 10
```
Produced: 32 bars, 9 frames per row, 1025 note cells, 5754 ROM bytes, loop 76.8 s; MIDI 3041 notes in 25.9 KB;
WAV 77.3 s (10.1 MB), MP3 1.86 MB; probe: four channels active in both windows, 317 pitch changes and 59 drum hits
in the play window, pulse 2 arpeggio at 3.0 frames per step.
Listen for: pulse 2 is a chord (a dense zig-zag on the piano roll), not a melody; the lead opens phrases with a
mordent and lands on a trill; the bass pops (staccato octave bounces) and bends into a downbeat once in a while,
always landing; bars 17-24 drop the chord for the echo (pulse 2 a few frames behind pulse 1, quieter); the key
moves from F# to D at bar 17.

## 2. A stage loop for an action game (rock, stage form, organic)

```
export SKILL=/path/to/skills/gbc-music
mkdir ex2 && cd ex2
python $SKILL/scripts/compose.py generate --style rock --key E --bpm 146 --bars 24 --seed 3 --organic 2 --out stage.txt --report gen.json
python $SKILL/scripts/compose.py compile stage.txt --out music_data.c --report compile.json
python $SKILL/scripts/song_rom.py stage.txt --out stage.gbc --title "Stage Demo"
python $SKILL/scripts/song_midi.py stage.txt --out stage.mid
```
Produced: 24 bars at 6 frames per row (A 8, B 8, C 8, loop at bar 1), progressions `stage_a | stage_b | stage_c`
(Em Em C D / Em Em Am D / Em A D Em), 671 note cells, 1167 MIDI notes, 38.6 s per loop. The report's `plan` lists
the sections and `organic_moves` what the layer changed (varied repeats, breaths, fills, dropped hats).
Listen for: the riff on wave + pulse 2 in bar 1 and the lead answering in bar 2 (call and response); B keeps the
drive through iv; C lifts the lead an octave over the major IV with the open kit; the loop is seamless.

## 3. A verse-chorus pop song with a hook

```
export SKILL=/path/to/skills/gbc-music
mkdir ex3 && cd ex3
python $SKILL/scripts/compose.py generate --style pop --key C --bpm 120 --bars 48 --seed 1 --progression axis --organic 2 --out pop.txt --report gen.json
python $SKILL/scripts/song_rom.py pop.txt --out pop.gbc
python $SKILL/scripts/song_wav.py pop.txt --out pop.wav --seconds 30
```
Produced: 48 bars (intro 4, verse 8, pre-chorus 4, chorus 8, verse 8, pre-chorus 4, chorus 8, outro 4), chorus
`I V vi IV` (C G Am F), verse rotated to start on vi, loop at bar 5, 8 frames per row (112.5 bpm: the chip quantises
tempo to whole frames per row).
Listen for: the verse pad is short bursts on pulse 2 and the chorus a continuous chord cycle; the hook (a 2-bar
motif three times, then a cadence) comes back note for note an octave above the verse on a brighter duty; the
pre-chorus climbs a step per bar over a snare build; verse 2 differs from verse 1 by one note and an octave-up
ending; a crash opens each chorus.

## 4. The twelve-bar blues

```
export SKILL=/path/to/skills/gbc-music
mkdir ex4 && cd ex4
python $SKILL/scripts/compose.py generate --style rock --key A --bpm 112 --bars 40 --seed 5 --form blues12 --out blues.txt --report gen.json
python $SKILL/scripts/song_rom.py blues.txt --out blues.gbc
python $SKILL/scripts/song_midi.py blues.txt --out blues.mid
```
Produced: 40 bars (intro 4 = the turnaround, head 12, head an octave up 12, solo 12), `blues12` numerals, dominant
sevenths on pulse 2, 8 frames per row.
Listen for: the swung boogie bass; the aab head (call in bars 1-2, 5-6, 9-10, the bass answering); the solo chorus;
the turnaround into each twelve.

## 5. Fusion texture on a stage form (the house blend) and a quiet ambient bed

```
export SKILL=/path/to/skills/gbc-music
mkdir ex5 && cd ex5
python $SKILL/scripts/compose.py generate --style rock --key E --bpm 146 --bars 28 --seed 3 --texture fusion --out blend.txt --report blend.json
python $SKILL/scripts/compose.py generate --style ambient --key D --bpm 70 --bars 16 --seed 2 --out bed.txt --report bed.json
python $SKILL/scripts/song_rom.py blend.txt bed.txt --out two.gbc --title "Two Songs"
python $SKILL/scripts/audio_probe.py --rom two.gbc --out probe --pre wait:60 --seconds 8
```
Produced: `blend.txt` = the 28-bar stage plan (intro 4 + A B C) with the fusion idioms laid on it (maj7 / m9 colour
on the pulse-2 cycle, mordents and trills, slap bass, the 16th-note kit, the echo in B); `bed.txt` = 16 bars at 70 bpm,
18 note cells, a drone and a slow arpeggio. The two-song player boots into the blend; START switches to the bed
(the probe's play window then hears the bed: fewer pitch changes, almost no drum hits).
Listen for: the difference texture makes on the same form; and how little an ambient bed needs (four channels still
sound, but 18 cells for 56 seconds).

## 6. A hand-written score, edited, split into a duet

```
export SKILL=/path/to/skills/gbc-music
mkdir ex6 && cd ex6
cat > duo.txt <<'EOF'
name: song_duo
title: Duo
bpm: 120
inst lead pulse duty=50 env=C7 vib=2:3
inst pad  pulse duty=25 env=90
inst bass wave vol=12 shape=rsaw
inst bass2 wave vol=6 shape=rsaw
bar 1
lead: E5@lead . . . G5 . . . B5 . . . - . . .
arp:  E4:min@pad . . . . . . . . . . . . . . .
bass: E2@bass . E3@bass2!3 . E2@bass . E3@bass2!3 . E2@bass . E3@bass2!3 . E2@bass . E3@bass2!3 .
drum: KH . H . SH . H . KH . H . SH . H h
bar 2
lead: C5@lead . . . E5 . . . G5~ . . . . . - .
arp:  C4:maj . . . . . . . . . . . . . . .
bass: C2@bass . C3@bass2!3 . C2@bass . C3@bass2!3 . C2@bass . C3@bass2!3 . C2@bass . B1@bass/-2,4 .
drum: KH . H . SH . H . KH . H . SH h sh H
EOF
python $SKILL/scripts/compose.py compile duo.txt --out music_data.c --report compile.json
python $SKILL/scripts/compose.py split duo.txt --part a=lead,arp --part b=bass,drum:KSH --out-dir parts --report split.json
python $SKILL/scripts/song_rom.py parts/duo_a.txt --out duo_a.gbc
python $SKILL/scripts/song_rom.py parts/duo_b.txt --out duo_b.gbc
python $SKILL/scripts/song_midi.py duo.txt --out duo.mid
```
Produced: a 2-bar score with the bass alternating two instruments (`@bass` on the beats, `@bass2` at half level on
the octave bounces: the measured cartridge habit), a resolving bend into the last bass note, a vibrato cell on the
lead's held G5; `split` writes `parts/duo_a.txt` (lead + chord) and `parts/duo_b.txt` (bass + the K S H letters of the
kit only: the ghost `h` and `sh` are dropped), each with the same tempo, bars and loop, so two Game Boys started in
lockstep play the duet.
Listen for: the bass's level change on the bounces (the wave channel's click-free NR32 step), the bend landing on
B1, and that `duo_a.gbc` and `duo_b.gbc` together are the whole `duo.txt`.

## 7. Phrase-level composition (the motif banks) on the house blend

```
export SKILL=/path/to/skills/gbc-music
mkdir ex7 && cd ex7
python $SKILL/scripts/compose.py generate --style rock --key E --bpm 146 --bars 28 --seed 3 --texture fusion --phrases 2 --organic 2 --out blend.txt --report gen.json
python $SKILL/scripts/compose.py generate --style pop --key C --bpm 120 --bars 48 --seed 1 --progression axis --phrases 2 --out pop.txt --report pop.json
python $SKILL/scripts/song_rom.py blend.txt --out blend.gbc --title "Phrase Demo"
python $SKILL/scripts/song_midi.py pop.txt --out pop.mid
```
Produced: the stage form with the fusion texture, composed from a bank of three ideas per section (the report's
`banks` lists each section's statement / answer / departure as eight beat cells of `x . -`), rests written into
the lead, the C section quoting B's answer a step away; the pop song with its verse answered by pulse 2
(`pulse2_answers` in the report) and verse 2 re-ordering the bank. The header comment names the banks and the
answer count.
Listen for: the lead breathing inside phrases, not only at their ends; the answer phrases on the narrower `lead2`
voice; pulse 2 stepping out of its pad to answer a short phrase; the second verse recognisably the same material in
a new order; the hook still the hook.

## 8. A pop song with a designed hook (`--hook 2`) and all three outputs

```
export SKILL=/path/to/skills/gbc-music
mkdir ex8 && cd ex8
python $SKILL/scripts/compose.py generate --style pop --key C --bpm 120 --bars 48 --seed 1 --progression axis --hook 2 --organic 2 --out hook.txt --report gen.json
python $SKILL/scripts/song_rom.py hook.txt --out hook.gbc --title "Hook Demo"
python $SKILL/scripts/song_midi.py hook.txt --out hook.mid
python $SKILL/scripts/song_wav.py hook.txt --out hook.wav --seconds 30
```
Produced: the 48-bar verse-chorus plan of example 3 with its chorus hook designed first: a falling contour over
8 semitones, rhythm `x..x .... x... x.x. x... x... x... ..-.` (8 onsets, the anticipation on the 16th before beat
2, the landing on beat 3 of bar 2, a breath), the leap at note 5, the hum test `G5 G5 F5 F5 C5 B4 C5 C5`; the
report's `hook.metrics`: a 2-bar cell heard 5 times note for note (2.9 a minute), first at 4.3 s (the intro), range
8, steps 0.75, song climax at bar 21 (the first chorus's third statement), 11 metrics in the corpus band, 1 near
(`leap_ratio`), 1 out (`climax_pos`: a falling hook peaks on its first note). 1130 note cells.
Listen for: the intro's chord voice tapping the hook's rhythm before anyone sings it; the verse as the hook's
skeleton on fewer, lower notes; the chorus saying the hook twice, lifting its top note the third time (the
highest note of the song, once per chorus), then cadencing; the outro repeating the hook's second bar twice.

## 9. The earworm surprise (`--hook 3`) on the house blend and on a 64-bar song with a bridge

```
export SKILL=/path/to/skills/gbc-music
mkdir ex9 && cd ex9
python $SKILL/scripts/compose.py generate --style rock --key E --bpm 146 --bars 28 --seed 3 --texture fusion --phrases 2 --hook 3 --organic 2 --out blend.txt --report blend.json
python $SKILL/scripts/compose.py generate --style pop --key D --bpm 128 --bars 64 --seed 2 --phrases 2 --hook 3 --out long.txt --report long.json
python $SKILL/scripts/song_rom.py blend.txt long.txt --out two.gbc --title "Hook Demo 2"
python $SKILL/scripts/song_midi.py long.txt --out long.mid
```
Produced: `blend.txt` = the stage form (intro 4, A B C) with the fusion texture and the motif banks, A stating a
falling 12-semitone hook (`B4 D5 B4 B4 D4 E4 G4 A4 B4`: the leap at note 5 is a major sixth down resolved by step,
the surprise), B previewing its skeleton, C lifting it with the top note; the hook is first heard at 3.2 s and 3
times note for note (4.0 a minute), 12 metrics in band, 1 near, 0 out. `long.txt` = 64 bars (two verses,
pre-choruses, choruses, a bridge, a final chorus, outro) on an arch hook of 9 semitones (`D5 B5 A5 A5 G5 F#5 E5 D5`,
a sixth up at note 2 resolved by step), heard 7 times note for note (3.5 a minute), the wave bass quoting it two
octaves down in bars 45-46 (the bridge), the final chorus's third statement landing an 8th late; 10 metrics in
band, 3 near, 0 out. 792 and 1476 note cells.
Listen for: the sixth in the hook (it is the one interval you remember); the bass singing the hook alone under
the bridge; the last chorus leaning on its final note; and that every chorus states the hook with the same
pitches, so the ear can hum along by the second one.

## 10. Call and response on two sides (`--pan call`)

```
export SKILL=/path/to/skills/gbc-music
mkdir ex10 && cd ex10
python $SKILL/scripts/compose.py generate --style rock --key A --bpm 112 --bars 40 --seed 5 --form blues12 --pan call --out call.txt --report gen.json
python $SKILL/scripts/compose.py compile call.txt --out music_data.c --report compile.json
python $SKILL/scripts/song_rom.py call.txt --out call.gbc
python $SKILL/scripts/song_midi.py call.txt --out call.mid --report midi.json
python $SKILL/scripts/song_wav.py call.txt --out call.wav --seconds 20
python $SKILL/scripts/audio_probe.py --rom call.gbc --out probe --pre wait:60 --seconds 40
```
Produced: the twelve-bar blues of example 4 (40 bars, 858 note cells, 2566 ROM bytes) with 6 pan events on pulse 1
(sides C, L, R: the call of each head on the left, its answer on the right, the turnaround lick and the solo centre;
the generate report's `pan` block lists the moves, the compile report `pan_events` / `pan_sides`); MIDI 2656 notes
in 22.4 KB with 6 CC10 events on the lead track and none elsewhere; a 20 s stereo WAV whose channels differ (left
3178 RMS, right 2980: the first call sits left); probe over 40 s: `pan_events` 4, `solo_reliable` true, pulse 1
`stereo.side` moving (305 frames left, 100 right, 269 centre, balance -0.22), wave and noise `side` C, music
detected. Without `--pan call` the same command writes a byte-identical score to example 4's.
Listen for (headphones; the handheld speaker is mono): the call phrase on the left, the answer line over V-IV from
the right, the lick back in the middle, the boogie bass and the kit never moving; one register write per change, so
no click at the switch.

## 11. Ska: the skank, a walking bass, a horn-line hook

```
export SKILL=/path/to/skills/gbc-music
mkdir ex11 && cd ex11
python $SKILL/scripts/compose.py generate --style ska --key C --bpm 168 --bars 48 --seed 2 --organic 2 --out ska.txt --report gen.json
python $SKILL/scripts/song_rom.py ska.txt --out ska.gbc --title "Ska Demo"
python $SKILL/scripts/song_midi.py ska.txt --out ska.mid
python $SKILL/scripts/audio_probe.py --rom ska.gbc --out probe --pre wait:60 --seconds 10
```
Produced: 48 bars (intro 4, verse 8, pre-chorus 4, chorus 8, verse 8, pre-chorus 4, chorus 8, outro 4) on the
`skank` progression (I IV V V = C F G G), 5 frames per row (the chip plays 168 as 180), 1159 note cells, 4248 ROM
bytes, 64 s per loop; MIDI 2332 notes in 20 KB; probe: four channels active in the play window (pulse 1 at 77%,
pulse 2 at 47% = the chops, wave at 99%, 39 drum hits in 10 s). The report's `syncopation` reads lead 1.3,
**chords 6.5 with every strike off the beat**, bass 0.3, kick+snare 0.05: ska's syncopation is the skank.
Listen for: the chord chops on every off-8th (`@skank`, 25% duty, a 9-frame decay) against kick 1 and 3 and the
cross-stick on 2 and 4; the walking quarter bass (root, 3rd, 5th, 6th) turning into 8ths with octave jumps in the
chorus; the horn hook on pulse 1 pushing the and-of-4 over the bar line; the stop-time fill (`S . S T`) closing
each phrase; the open hats when the chorus arrives.

## 12. A 2010s pop hit (tropical groove) and its straight twin

```
export SKILL=/path/to/skills/gbc-music
mkdir ex12 && cd ex12
python $SKILL/scripts/compose.py generate --style pop --groove tropical --key F --bpm 100 --bars 48 --seed 3 --organic 2 --out hit.txt --report gen.json
python $SKILL/scripts/compose.py generate --style pop --groove tropical --key F --bpm 100 --bars 48 --seed 3 --organic 2 --syncopation 0 --out hit_straight.txt --report gen_straight.json
python $SKILL/scripts/song_rom.py hit.txt hit_straight.txt --out hit.gbc --title "Pop Hit Demo"
python $SKILL/scripts/song_wav.py hit.txt --out hit.wav --seconds 30
```
Produced: the same 48-bar verse-chorus plan as example 3 on `axis` (F C Dm Bb), 9 frames per row, 904 note cells,
4852 ROM bytes, 115 s per loop, 12 instruments (the `hook` is the pluck: 25% duty, `env=E3`, `penv=12,1`; `pluck2`
the 12.5% chord pluck on pulse 2). `syncopation`: lead 3.9 (58% of its onsets off the beat), chords 5.6, bass 1.5
(the tresillo), kick+snare 0.05 by the index and 35% off the beat (the dembow snare on the and-of-2). The straight
twin (`--syncopation 0`, same seed) scores lead 1.2 / chords 0.6 / bass 0.3 with 2% of the lead off the beat: the
same melody, the same chords, the same form, only the placement moved. The two-song player boots into the hit;
START switches to the twin.
Listen for: the sparse verse (kick on 1, snare on 4, the bass root once a bar, the pad hinting two off-beat rows of
the hook); the pre-chorus build (16th hats, the snare lift, the bass walking the tresillo); the chorus as a drop
(dembow kick and snare, the 0-6-12 bass, the plucked hook on pulse 1 anticipating the next downbeat on the last
16th, pulse 2 plucking the chord on the hook's off-beat rows); then the twin, which has the notes and none of the
bounce.
