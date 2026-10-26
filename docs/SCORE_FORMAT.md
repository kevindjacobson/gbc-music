# The score format

One song per file. Plain text. A `#` at the start of a line or after a space starts a comment (so `F#4` is a note and
`F#4 # the top` is a note with a comment). Blank lines are ignored. Lines come in three groups: the **header**, the
**library** (instruments, waves, chords, drums) and the **bars**.

```
# Fusion theme                               <- comments: the generator writes its plan here
name: song_main                              <- C symbol: music_init(&song_main)
title: Fusion theme
bpm: 100                                     <- or  tempo: 9  (frames per row)
rows: 16
arp: 3
loop: 0

inst lead  pulse duty=50 env=C7 vib=2:3
inst arp   pulse duty=25 env=90
inst bass  wave  vol=13 shape=saw
chord v0_2_4_11 0 2 4 11

bar 1
lead: . . . . F#4@lead'2 G#4 A#4 C5 C#5 D#5 F5/-1,4 . F5~2,3 . - .
arp:  F#4:maj7@arp . . . . . . . . . . . . . . .
bass: F#2@bass/-2,6 . F#3!3 . F#2 . F#3!3 . F#2 . F#3!3 F#3!2 F#2 F#3!2 F#3!3 .
drum: KH . H h SH h KH . KH h H sh SH h KH h
```

## Header

| line | meaning | range / default |
|---|---|---|
| `name: song_main` | C identifier of the `Song`; `music_init(&song_main)` | default `song_<file stem>` |
| `title: Fusion theme` | free text; shown by the player ROM and in reports | optional |
| `bpm: 100` | tempo in beats per minute; frames per row = round(3600 / bpm / rows-per-beat): 4 rows per beat on the 16-row grid (100 -> 9, 120 -> 8, 146 -> 6), 3 on the 12-row grid (140 -> 9) | 40..240 on the generator; any value that gives 1..255 frames |
| `tempo: 9` | frames per row, directly (the row is a sixteenth note) | 1..255 |
| `rows: 16` | rows per bar | 1..64, default 16 (a 4/4 bar of sixteenths); `rows: 12` with `beats: 4` is the triplet grid of swing and shuffle (three rows per beat, the late 8th on the third row) |
| `beats: 4` | beats per bar; `bpm:` is beats per minute on any grid (frames per row = round(3600 / bpm / (rows / beats))) | must divide `rows`; default rows / 4 (16 -> 4), the generator writes it only when rows != 4 x beats |
| `arp: 3` | frames per arpeggio step for `:chord` cells | 1..15, default 3 (3-4 reads as a chord) |
| `loop: 0` | bar the song restarts from, 0-based (the generator points it past the intro) | 0..bars-1 |

A bar of 16 rows at 9 frames per row lasts 144 frames = 2.41 s; 32 bars = 77 s.

## Instruments (`inst`)

At most 15 per song. A cell selects one with `@name`; the instrument stays on the channel until another `@`.

### Pulse (pulse 1 and pulse 2 lanes)

`inst <name> pulse duty=<d> env=<hex> [vib=<depth>:<delay>] [rate=<1..7>] [detune=<-8..7>] [penv=<semitones>,<frames>] [pan=C|L|R|LR[:<frames>]]`

| key | meaning |
|---|---|
| `duty=50` | duty cycle: `12` (12.5%, thin), `25`, `50`, `75` (75% = 25% inverted, identical in mono). Two to four comma-separated values (`duty=50,25` or `duty=12,25,50,25`) make a **duty sequence** stepped every `rate` frames without re-striking: a shimmer (`50,25 rate=2`) or a slow PWM sweep (`12,25,50,25 rate=4`) |
| `env=C7` | NRx2 byte, hex: volume nibble (0-F), direction bit (8 = up), step (0 = hold, 1 fast .. 7 slow). `C7` = volume 12 decaying slowly (1.3 s); `C2` dies in 22 frames (busy lines); `90` / `A0` = hold (a chord cycle needs step 0 or it vanishes); `0B` = volume 0 rising at pace 3 (a 0.7 s swell); `F1` = a pluck |
| `vib=2:3` | auto-vibrato on held notes: depth in period units, delay in 4-frame units (2:3 = depth 2 after 12 frames, at 3 frames per step). A sixteenth-note run never vibrates; a held note does |
| `rate=2` | frames per duty-sequence step (needs a duty list) |
| `detune=1` | fixed period offset added to every pitch; use on a doubling voice only, at most 1 (`DESIGN_NOTES.md`) |
| `penv=12,5` | pitch envelope on every note: start N semitones (1..15) above and fall onto the note in M frames (1..15). `12,5` kick, `5,3` tom, `12,1` pluck attack |
| `pan=R` | every note of the instrument on one side (`L` / `R`; `C` = both, the default): the NR51 bits of the channel, hard left / right, written once per change. `pan=LR:10` is an **auto-pan**: while a note is held the channel alternates left / right every 10 frames (1..63; default 8; `rate=` is taken as the period when the instrument has no duty sequence). A texture for pads and the chord cycle, never a lead. Pulse instruments only: the wave bass is never panned |

### Wave (bass lane)

`inst <name> wave vol=<0..15> shape=<wave>[,<wave>...] [rate=<1..7>] [loop] [decay=<frames>|attack=<frames>] [vib=..] [detune=..] [penv=..]`

| key | meaning |
|---|---|
| `vol=13` | 0..15, mapped to the wave channel's NR32 levels: 1-4 quarter, 5-9 half, 10-15 full, 0 off |
| `shape=saw` | a 32-sample table by name (built-ins below, or a `wave` line). A comma list is a **wavetable sequence** stepped every `rate` frames from the note start, one-shot (holds the last table) or `loop`; each step rewrites wave RAM and re-triggers (a small click; rate >= 2, 4-6 for pads) |
| `decay=8` | NR32 level steps full -> half -> quarter -> off every N frames: the note ends by itself (bells, plucks), click-free |
| `attack=8` | the reverse: quarter -> half -> full, then hold (a pad swell) |

Built-in waves: `saw tri square soft organ sine bell pwm50 pwm37 pwm25 pwm12` (synthesised), `rsaw rsaw2 dark tri2
tridip organ2 reed spiky buzz thin` (the RPG corpus's bass and lead tables) and `jagged` (its jagged town buzz).
`compose.py styles` lists them; the wave channel sounds an octave below the pulse table for the same period, the
driver adds the octave, so write the pitch you want to hear.

### Custom waves, chords, drums

| line | meaning |
|---|---|
| `wave <name> <32 hex nibbles>` | a custom 16-byte table; at most 16 distinct tables per song (a sequence uses one slot per table) |
| `chord <name> <i> <i> [<i> [<i>]]` | semitone offsets from the written note (0..36), up to four; the generator writes voicings as `v0_2_4_11` |
| `drum <letter> env=<hex NR42> poly=<hex NR43> [then=<hex>,<hex>]` | a custom drum letter; `then` = a second stage struck 2 frames later (the RPG kick: a 7-bit buzz, then a hiss). NR43 bit 3 (`poly=x8..xF`) = 7-bit LFSR, tonal; otherwise white noise |

Built-in chord qualities: `maj min m dim aug sus2 sus4 5 maj7 m7 7 dim7 m7b5 6 m6 7sus4 add9 madd9 m9 maj9 9 69 maj7#11 m11`
(five-note colours drop the fifth; the driver cycles at most four slots).

Built-in drums: `K` kick `S` snare `H` hat `O` open hat `T` tom `C` crash, ghost / quiet `k s h`; the RPG kit `B` buzz
kick (two-stage) `Q` tight snare `P` bright snare `N` soft snare `M` metal ting (7-bit) `t` 7-bit tom (two-stage)
`X` cymbal `c` crash (two-stage) `D` snap; `Z` a tonal 7-bit buzz (a noise "note"). At most 15 distinct drums per song.

## Bars and lanes

`bar N` (numbered from 1) opens a block; then up to four lane lines, each with up to `rows` cells separated by
spaces (missing cells and missing lanes are `.`). Lane names: `lead:` (or `ch1: p1: pulse1:`) = pulse 1,
`arp:` (`ch2: p2: pulse2: echo:`) = pulse 2, `bass:` (`ch3: wave:`) = wave, `drum:` (`drums: ch4: noise:`) = noise.
A bar lane that repeats another is stored once; a missing bar is silent. At most 255 bars and 255 distinct bar lanes.

## Cells on a tonal lane

`.` nothing (the previous note continues). `-` (or `off`) key off. A note is `C#4`, `Db3`, `A5`: MIDI 36..107 (C2..B7)
on the pulse lanes, 24..95 (C1..B6) on the wave lane; out-of-range notes are clamped with a warning. A note takes one
optional `@inst` and **at most one effect**:

| cell | effect | what the driver does |
|---|---|---|
| `F#4:maj7` | arpeggio | cycle F#4 A#4 C#5 F5 one note every `arp:` frames, no re-trigger (the chord voice); `:name` of a `chord` line works too |
| `C#6~` / `C#6~2,3` | vibrato (depth, rate) | period +/- depth every `rate` frames, from the note start (the instrument's `vib=` is the delayed, automatic version) |
| `G#5^2` | trill | alternate note / note+2 every frame for the whole row |
| `G#5'2` | mordent | the same for the first 2 frames only |
| `F#2/-2,6` | resolving bend | start 2 semitones below, land on F#2 in 6 frames, hold. At most 3 semitones away, 1..15 frames; needs a note |
| `F#2/-4` | raw slide | period changes by 4 units every frame and never stops (synth sound design, not music) |
| `C5>D5` | 32nd pair | D5 struck at the middle of the row |
| `A4v6` | volume | this note (and the following ones until an `@inst`) at volume 6 of 15 |
| `F#3!3` | cut | silence after 3 frames (staccato pops) |
| `C3%4,8` | tremolo | volume dips by 4 steps every 8 frames. Click-free on the wave lane (NR32); a re-strike on pulses, so pads only and rate >= 6 (the compiler warns) |
| `G4=6` | portamento | glide from the previous note's pitch onto G4 in 6 frames (1..255), then hold |
| `C3@bell` | instrument | select an instrument; its own motion (`decay=`, `penv=`, sequences) applies to every note |
| `C5<` `E5>` `G5^` | pan marker | this note and the following ones on the left (`<`) / right (`>`) / both (`^`, the default) output: NR51, hard left or right, one register write per change, no re-strike. Lead and arp lanes only; a marker rides on a plain note or next to `@inst` but not next to another effect (one cell holds a note + one effect, or a note + a pan): put it on the row before as an effect-only cell, the switch then lands one 16th early |

Effect-only cells (no note; they act on the held note or the lane): `~`, `v6`, `<` / `>` / `^` (a pan change while
the note holds), `echo:5,3` / `echo:off` (pulse 2 lane only: pulse 2 replays pulse 1 five frames late, 3 volume
steps quieter, until `echo:off` or a real pulse-2 note), `echo:5,3,R` (the same with the echo voice on the right
(`L` left) for the echo's duration; `echo:off` or the next real pulse-2 note puts it back to both), `arpspeed:4` (new
arpeggio rate for the whole song).

**Panning rules** (NR51 is the only pan control: hard left / right / both per channel, mono on the handheld speaker,
stereo on headphones, in the WAV and in a duet; the measured cartridges keep it static, so a pan is a special
effect): everything is centre by default; pans belong to echoes, answers and pads; never the wave bass (`bass:`) or
the kit (`drum:`), the compiler refuses them there. `compose.py generate --pan echo|call|wide` writes them for you.

## Cells on the drum lane

One or two drum letters: `K`, `SH`. Two letters are a **stack**: the first drum, then the second 3 frames later
(`KH` = kick, then the hat). `.` nothing, `-` key off. (`v` cells are accepted on the drum lane but the presets carry
their own volume.) No pan markers: the kit stays centre.

## Tiny complete example

```
name: song_demo
bpm: 120
inst lead pulse duty=50 env=C7 vib=2:3
inst pad  pulse duty=25 env=90
inst bass wave vol=12 shape=rsaw
bar 1
lead: E5@lead . . . G5 . . . B5 . . . - . . .
arp:  E4:min@pad . . . . . . . . . . . . . . .
bass: E2@bass . E3!3 . E2 . E3!3 . E2 . E3!3 . E2 . E3!3 .
drum: KH . H . SH . H . KH . H . SH . H h
bar 2
lead: C5@lead . . . E5 . . . G5~ . . . . . - .
arp:  C4:maj . . . . . . . . . . . . . . .
bass: C2 . C3!3 . C2 . C3!3 . C2 . C3!3 . C2 . B1/-2,4 .
drum: KH . H . SH . H . KH . H . SH h sh H
```
`python scripts/compose.py compile demo.txt --out music_data.c` reports 2 bars, 8 bar lanes (8 unique patterns),
3 instruments, 2 chords, 1 wave, 5 drums, 43 notes (drum hits count), effects arp 2 / vib 1 / cut 7 / bend 1, and
508 ROM bytes.
Every compile report also carries `syncopation` (the Longuet-Higgins & Lee index per bar for the lead, chords
(pulse 2), bass and kick/snare lanes over the loop, plus each lane's off-beat onset share; `SKILL.md` §10).
