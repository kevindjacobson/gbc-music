# Six worked examples

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
