"""Compose and compile background music for the four-channel music driver (music.c / music.h).

Two modes, both deterministic and pure stdlib:

  python scripts/compose.py generate --style fusion --key F# --bpm 100 --bars 32 --seed 7 [--bend sparse|none|normal] [--form auto|loop|verse-chorus|aaba|blues12] [--progression NAME|"I V vi IV"] [--pan none|echo|call|wide] [--groove straight|swing|shuffle|ska|onedrop|funk|dance|tropical|latin|halftime] [--syncopation 0..3] --out output/music/main.txt
      Write a score (the text format below) in a style from the style library (--bend: how often the bass and lead
      bend into a note; every bend resolves onto the written tone; default sparse):
        fusion   jazz-fusion chiptune: maj7/add9/m9 voicings cycled at 32nd rate on pulse 2 (the "fusion chord"),
                 a slap-style walking bass with octave bounces on the wave channel, a lead of 16th runs with
                 32nd ornaments, trills and vibrato, an echo section, and a busy kick+hat / snare+hat drum grid;
                 modulates every 8 or 16 bars. --form aaba|verse-chorus pours the idioms into a song form.
        ambient  a slow drone, few notes, soft arpeggio, no drums to speak of (synths, calm scenes).
        chip     plain pop chiptune: triads, fast arpeggio, square bass, pentatonic lead, kick/snare/hat
                 (--form verse-chorus|aaba|blues12 gives it the pop engine below with chip instruments).
        pop      a song: intro / verse / pre-chorus / chorus / (bridge) / outro over a progression library
                 (--progression axis|sensitive|doowop|hopscotch|pachelbel|... or your own Roman numerals); the
                 verse states a two-bar motif, repeats it with one note changed, departs a step up and cadences
                 (srdc); the chorus is the hook three times plus a cadence, an octave above the verse, and comes
                 back identical; pulse 2 is a sparse pad in the verse and the full chord in the chorus; the kit
                 opens up at the chorus, lifts with a snare build in the pre-chorus, halves in the bridge.
        rock     the same forms with a riff: the wave bass and pulse 2 play a one-bar riff transposed to each
                 chord (I-IV-V or I-bVII-IV), the lead answers in bar 2 (call and response), the chorus switches
                 pulse 2 to power-chord cycles and the lead to a fat 75% duty hook. --form blues12: a shuffle,
                 boogie bass, aab head, head an octave up, a solo chorus.
        ska      a verse-chorus song on the ska groove: a horn-line hook on pulse 1, the skank (chord chops on
                 every off-8th) on pulse 2, a walking bass, kick 1 and 3 with cross-stick snares (full snare and
                 open hats in the chorus), 150-185 bpm, major keys (I IV V / I vi IV V).
      --groove straight|swing|shuffle|ska|onedrop|funk|dance|tropical|latin|halftime (default straight = as
               before): the kit, the bass rhythm, the pulse-2 stab rhythm and the hook rhythm bank of a genre, with
               a tempo band (a warning when --bpm is outside it). swing / shuffle write a 12-row bar (`rows: 12`,
               `beats: 4`: a triplet grid, the late 8th is row 2 of each beat). `pop --groove tropical` is the 2010s
               pop hit template (dembow kick and snare, tresillo bass, a sparse verse, a pre-chorus build, the
               chorus carried by an off-beat plucked hook); `latin` is the tresillo strum over a straight kit,
               `halftime` the riff-rock snare on 3. `compose.py styles` lists the grooves with their bands.
      --syncopation 0|1|2|3 (default: the groove's own level; straight = 0): how many anticipations, off-beat
               pushes and strong-beat rests the hook, the bass and the kick/snare get; 2 is the medium level the
               groove research found most danceable, 3 is funk. The report prints the syncopation index per lane.
      --form:  loop = the style's own loop (fusion/ambient/chip default); stage = the stage-corpus loop, (intro 4)
               A 8 B 8 C 8 with a progression per section (rock default; `--progression "stage_a | stage_b | stage_c"`);
               verse-chorus = 32 / 48 / 64 bars by --bars (pop default); aaba = A A' B A (+ intro/outro at 40);
               blues12 = intro + 2..4 twelve-bar choruses. The score's `loop:` points past the intro.
      --lift fifth|sixth|octave: how far the chorus / C-section lead sits above the verse (default fifth: the
               the reference corpora lift their second section 1-8 semitones; an octave drifts the lead beyond them).
      --organic 0..3: the organic layer (repeats vary, breaths, fills, accents, sit-outs, anticipations, the §8
               timbre plan per section and articulation pairs); 0 = untouched. --help of the flag has the levels.
      --texture plain|fusion: form and texture are independent. `fusion` layers the fusion idioms on any form
               (maj7/add9/m9 colour on the pulse-2 cycle, mordents and trills on the lead, slap bass with octave
               bounces, the fusion kit, the echo voice in the bridge / B section). `compose.py styles` lists the
               forms, textures and the progression library with moods.
      --pan none|echo|call|wide: stereo pans (NR51: hard left / right / both per channel; mono on the handheld
               speaker, audible on headphones, in the WAV and in a duet). none = the default, byte-identical scores;
               echo = the echo voice right and the lead left for the echo's duration (ping-pong); call = call and
               response (the rock verse's answers alternate sides per phrase, the blues call left and answer right,
               a pop / stage phrase's restatement right and conclusion left); wide = echo + call + an LR auto-pan on
               the verse pad. Pans belong to echoes, answers and pads: never the wave bass, never the kit.
  python scripts/compose.py compile output/music/main.txt [more.txt ...] --out output/game/src/music_data.c
      Compile score file(s) into C tables for the driver (+ music_data.h beside the .c, declaring
      `extern const Song <name>;` per song). The game then calls music_init(&<name>).
  python scripts/compose.py styles        List the styles, forms, progression library, chord qualities, waves, drums.
  python scripts/compose.py split output/music/main.txt --part a=lead,arp --part b=bass,drum --out-dir output/music
      Write one score per part (main_a.txt, main_b.txt; `name:` becomes <song>_<part>) that keeps only the named
      lanes of the input and silences the rest; the header, instruments, chords, waves and drums are copied, so
      the parts share tempo, bar count and loop exactly (a multi-ROM piece: one part per Game Boy, run in lockstep).
      A lane may carry a drum-letter filter: `--part b=bass,drum:KSks` keeps only those letters on the noise lane
      (a two-letter stack keeps the letter that is listed). `--pan a=L30,b=R30` writes a `# pan: L30` hint into each
      part's header: where that part's whole mix sits in a software mixer that plays the parts together (L/R + percent,
      0..100; C = centre); it is a comment the score grammar ignores, so the ROMs are unchanged.

  python scripts/compose.py events output/music/main.txt --out output/music/main_events.json [--offset 0.1]
      Note events of a compiled score as JSON for the piano-roll component (scripts/pianoroll.js):
      one entry per sounding note with ch 0..3, t/d in seconds (t = --offset + frame / 59.7275), f/fd in frames,
      bar/row, midi, vol, inst, and the pitch effects the driver applies (arp intervals + arp_f, trill, mordent,
      split, bend, porta, slide, vib, trem, penv, cut, echo copies, dec = envelope lifetime; pan -1 left / 1 right
      or "LR" + pan_f for an auto-pan, only on panned notes) and, when the song pans, a top-level `pan_changes`
      list ({ch, f, t, pan}). Several scores are chained back to back (bar numbers continue; `songs` lists each start).
Both modes print a final JSON line {"ok": true, ...} (a report), exit non-zero with a one-line reason.

Score format (one song per file; '#' after a space or at line start starts a comment; see `scripts/compose.py styles` for chord names):
  name: song_main            C symbol of the song (default: song_<file stem>)
  bpm: 100                   or  tempo: 9  (frames per row; a row is a 16th note; 3600/bpm/4)
  rows: 16                   rows per bar (default 16); rows: 12 with beats: 4 = a triplet grid (swing, shuffle)
  beats: 4                   beats per bar (default rows / 4); bpm: means beats per minute whatever the grid
  arp: 3                     frames per arpeggio step (default 3; the fusion rate is 3..4)
  loop: 0                    bar the song restarts from, 0-based (default 0)
  inst <name> pulse duty=50|25|12|75 env=<hex NRx2> [vib=<depth>:<delay>] [duty=50,25,12,25 rate=<frames>]
                                  [detune=<-8..7>] [penv=<semitones>,<frames>] [pan=C|L|R|LR[:<frames>]]
      duty with 2-4 values = a duty sequence rotated every `rate` frames (a PWM shimmer, the RPG cry timbre);
      detune = fixed period offset (two pulses a unit apart = chorus); penv = start N semitones up and fall onto the
      note in M frames (12,5 kick / 5,3 tom / 12,1 pluck); env direction up (e.g. 0B = vol 0, up, pace 3) = soft attack;
      pan=L|R puts every note of the instrument on that side (C = both, the default), pan=LR[:N] alternates left / right
      every N frames (default 8) while a note is held: an auto-pan texture for pads and the chord cycle, never a lead.
  inst <name> wave vol=<0..15> shape=<wave>|<wave>,<wave>,... [rate=<frames>] [loop] [decay=<frames>|attack=<frames>]
                                  [vib=..] [detune=..] [penv=..]
      a shape list = wavetable sequence stepped every `rate` frames from the note start (one-shot, or `loop`);
      decay = NR32 level steps full -> half -> quarter -> off every N frames (bell, pluck; click-free), attack = the reverse.
      waves: `compose.py styles` lists them (saw tri square soft organ sine bell pwm50..pwm12 + the RPG corpus tables).
  wave <name> <32 hex nibbles>          a custom wave shape (16 bytes)
  chord <name> <i> <i> [<i> [<i>]]      a chord as semitone offsets from the written note
  drum <letter> env=<hex NR42> poly=<hex NR43> [then=<hex NR42>,<hex NR43>]   a custom drum letter (then = a second
      stage struck 2 frames later: the RPG kick is a 7-bit buzz then a hiss). NR43 bit 3 (poly=x8..xF) = 7-bit LFSR, tonal.
  bar <n>                    then one line per lane (missing lanes stay silent):
  lead: <16 cells>           pulse 1    arp: <cells>   pulse 2    bass: <cells>   wave    drum: <cells>   noise
Cells (space separated, one per row): `.` nothing  `-` key off  `C#4` a note (MIDI 36..107; wave lane 24..95).
A note takes one optional `@inst` and at most one effect:
  `:maj7` arpeggio (chord quality or a `chord` name)   `~` vibrato (`~<depth>,<rate>`)   `^2` trill (whole row)
  `'2` mordent (2 frames)   `/-2,6` bend: start 2 semitones below and land on the note in 6 frames (at most a minor
  third; the rule: bends are rare and always resolve)   `/-6` raw slide (period units per frame, persists)
  `>D5` 32nd pair (second note mid-row)
  `v9` volume 0..15   `!4` cut after 4 frames   `%2,8` tremolo (dip 2 volume steps every 8 frames; click-free on the
  wave lane, a re-strike on pulses: pads only)   `=6` portamento (glide from the previous note onto this one in 6 frames).
  Pan markers (lead and arp lanes only; NR51 hard left / right): `C5<` left, `E5>` right, `G5^` centre (both), holding
  until the next marker; a marker rides on a plain note (or on `@inst`) but not next to another effect: put it on the
  row before as an effect-only cell (`<`, `>`, `^`). Never on the bass or drum lanes.
  Effect-only cells: `echo:5,3` (pulse 2 replays pulse 1 five frames late, 3 quieter; `echo:5,3,R` puts the echo voice on
  the right for the echo's duration, `echo:off` restores centre), `arpspeed:4`, `~`, `v6`, `<` `>` `^`.
Drum cells: letters from  K kick  S snare  H hat  O open hat  T tom  C crash  k s h (ghost/quiet versions);
  RPG kit: B buzz-kick (7-bit then hiss)  Q tight snare  P bright snare  N soft snare  M metal ting (7-bit)
  t 7-bit tom (two-stage)  X cymbal  c crash (two-stage)  D snap  Z tonal 7-bit buzz;
  two letters = a stack (`KH`: kick, then the hat 3 frames later).
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import random
import re
import sys
from pathlib import Path

# ----------------------------------------------------------------------------------------------- music theory

NOTE_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
PC_NAME = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTE_RE = re.compile(r"^([A-Ga-g])([#b]?)(-?\d)$")

# Chord qualities as semitone offsets; at most four notes (the driver cycles up to 4 slots). Five-note
# colours drop the fifth, the way a fusion keyboardist voices them.
CHORDS = {
    "maj": (0, 4, 7), "min": (0, 3, 7), "m": (0, 3, 7), "dim": (0, 3, 6), "aug": (0, 4, 8),
    "sus2": (0, 2, 7), "sus4": (0, 5, 7), "5": (0, 7, 12),
    "maj7": (0, 4, 7, 11), "m7": (0, 3, 7, 10), "7": (0, 4, 7, 10), "dim7": (0, 3, 6, 9), "m7b5": (0, 3, 6, 10),
    "6": (0, 4, 7, 9), "m6": (0, 3, 7, 9), "7sus4": (0, 5, 7, 10),
    "add9": (0, 4, 7, 14), "madd9": (0, 3, 7, 14), "m9": (0, 3, 10, 14), "maj9": (0, 4, 11, 14),
    "9": (0, 4, 10, 14), "69": (0, 4, 9, 14), "maj7#11": (0, 4, 11, 18), "m11": (0, 3, 10, 17),
}
SCALES = {
    "major": (0, 2, 4, 5, 7, 9, 11), "lydian": (0, 2, 4, 6, 7, 9, 11), "mixolydian": (0, 2, 4, 5, 7, 9, 10),
    "dorian": (0, 2, 3, 5, 7, 9, 10), "minor": (0, 2, 3, 5, 7, 8, 10), "pent": (0, 2, 4, 7, 9), "mpent": (0, 3, 5, 7, 10),
}
PULSE_RANGE = (36, 107)
WAVE_RANGE = (24, 95)

# Built-in wave shapes (32 samples, 4 bits each). saw and triangle are bright enough for a bass to cut through.
WAVES = {
    # synthesized
    "saw": "00112233445566778899AABBCCDDEEFF",
    "tri": "0123456789ABCDEFFEDCBA9876543210",
    "square": "FFFFFFFFFFFFFFFF0000000000000000",
    "soft": "89BCDEFFFFEDCB987643210000123467",
    "organ": "8CEFECA864310134" "68ACEFECA8643101",
    "sine": "89ACDEEFFFEEDCA98653211000112356",                      # pure tone: flute / sub bass / bell body
    "bell": "8ACDDCBBABBCDDCA8532234444432235",                      # sine + 3rd partial: a bell with `decay=`
    "pwm50": "FFFFFFFFFFFFFFFF0000000000000000",                  # square-in-wave: the pulse timbre an octave down (NR32 = fine dynamics)
    "pwm37": "FFFFFFFFFFFF00000000000000000000",                  # pwm50 -> pwm37 -> pwm25 -> pwm12 stepped = the LSDj synth PHASE sweep
    "pwm25": "FFFFFFFF000000000000000000000000",
    "pwm12": "FFFF0000000000000000000000000000",
    # the RPG corpus's wave tables (decoded from register traffic); `rsaw` is the bass of every town theme
    "rsaw": "02468ACEFFFEEDDCCBA9876544332211",     # RPG wave 0: fast rise, slow fall (rounded saw): bass / strings
    "rsaw2": "02468ACEEFFFFEEEDDCBA98765432211",    # RPG wave 1: same, flatter top (softer)
    "dark": "1369BDEEEEFFFFEDDEFFFFEEEEDB9631",     # RPG wave 2: notched hump, a dark near-square
    "tri2": "02468ACDEFFEDEFFEEDCBA9876543210",     # RPG wave 3: double-peak triangle
    "tridip": "012345678ACDEEF77FEEDCA876543210",   # RPG wave 4: triangle with a mid dip (even harmonics)
    "organ2": "0011223344332211FFEECCAA88AACCEE",   # RPG wave 5: two unequal humps, strong 2nd harmonic (the city and road bass)
    "reed": "02468ACECBA98765FFFEEDDC44332211",     # RPG wave 6: stepped saw pieces, bright and reedy
    "spiky": "C0A987F5FFFEEDDC443322F102468ACE",    # RPG wave 7: spiky, noise-like
    "buzz": "4433221F00468ACEF8FEEDDCCBA98765",     # RPG wave 8: asymmetric buzz
    "thin": "110000080013579AB4BAA99887654321",     # RPG wave 9: mostly low with a spike, thin
    "jagged": "21E23328E122FFEA1014DC10E3415173", # the RPG corpus's first-generation wave 5: the jagged ghost-town buzz
}
# Noise drum presets: env = NR42 (volume, direction, step), poly = NR43 (shift<<4 | width<<3 | divisor); a 4-tuple adds a
# second stage (NR42, NR43) struck MUSIC_DRUM_STAGE_FRAMES (2) later. Bit 3 of NR43 = 7-bit LFSR: tonal / metallic.
DRUMS = {
    "K": (0xF1, 0x5C), "S": (0xD2, 0x46), "H": (0x61, 0x15), "O": (0x72, 0x25), "T": (0xC2, 0x6A), "C": (0xA4, 0x14),
    "k": (0x91, 0x5C), "s": (0x71, 0x46), "h": (0x41, 0x15),
    # the RPG corpus's kit, decoded from register traffic to NR42/NR43
    "B": (0x88, 0x6B, 0x71, 0x00),   # Kick1: 1.4 kHz 7-bit buzz, then a 524 kHz hiss (the RPG kick)
    "Q": (0xC1, 0x33),               # Snare1: tight 10.9 kHz snare (B1/A1/81 are its softer velocities)
    "P": (0x91, 0x22),               # Snare9: brighter 32.8 kHz snare
    "N": (0x82, 0x23),               # Snare5: softer, longer snare
    "M": (0x51, 0x2A),               # Triangle1: metallic 7-bit ting
    "t": (0x41, 0x2B, 0x61, 0x2A),   # Triangle2: two-stage 7-bit tom
    "X": (0x84, 0x12),               # Crash2: cymbal
    "c": (0x88, 0x15, 0x65, 0x12),   # Crash1: 4-frame body then a slow decay
    "D": (0x91, 0x00, 0x11, 0x00),   # Drum28: bright snap at the fastest clock
    # ours
    "Z": (0xA3, 0x2F),               # tonal 7-bit buzz (9.4 kHz clock / 127-step loop ~ 74 Hz): a noise "note"
}
DUTY = {"12": 0x00, "12.5": 0x00, "25": 0x40, "50": 0x80, "75": 0xC0}
FX = {"none": 0, "arp": 1, "vib": 2, "trill": 3, "slide": 4, "split": 5, "vol": 6, "cut": 7, "echo": 8, "arpspeed": 9, "bend": 10,
      "trem": 11, "porta": 12, "pan": 13}
PAN = {"R": 1, "L": 2, "C": 3}                   # NR51 bits of a channel: 1 right, 2 left, 3 both (centre, the default)
PAN_NAME = {1: "R", 2: "L", 3: "C"}
PAN_NOTE = 0x80                                 # note byte 0x80 | side: a pan change on an effect-only cell
PAN_MARK = {"<": 2, ">": 1, "^": 3}             # cell markers: < left  > right  ^ centre
PAN_AUTO_DEFAULT = 8                            # frames per side for `pan=LR` without a rate
BEND_MAX_SEMITONES = 3   # a bend starts at most a minor third away and lands on the written note
BEND_RATES = {"none": (0.0, 0.0), "sparse": (0.5, 0.15), "normal": (1.0, 0.35)}   # (bass bars with a downbeat bend, lead phrases bending into the target)
LANES = {"lead": 0, "ch1": 0, "p1": 0, "pulse1": 0, "arp": 1, "ch2": 1, "p2": 1, "pulse2": 1, "echo": 1,
         "bass": 2, "ch3": 2, "wave": 2, "drum": 3, "drums": 3, "ch4": 3, "noise": 3}
MUSIC_OFF = 0xFE


class ScoreError(Exception):
    pass


def note_to_midi(text: str) -> int:
    m = NOTE_RE.match(text)
    if not m:
        raise ScoreError(f"bad note {text!r} (want e.g. C#4, Db3)")
    pc = NOTE_PC[m.group(1).upper()] + {"#": 1, "b": -1, "": 0}[m.group(2)]
    return 12 * (int(m.group(3)) + 1) + pc


def midi_to_note(n: int) -> str:
    return f"{PC_NAME[n % 12]}{n // 12 - 1}"


def key_pc(text: str) -> int:
    m = re.match(r"^([A-Ga-g])([#b]?)$", text.strip())
    if not m:
        raise ScoreError(f"bad key {text!r} (want e.g. F#, Bb, C)")
    return (NOTE_PC[m.group(1).upper()] + {"#": 1, "b": -1, "": 0}[m.group(2)]) % 12


def bpm_to_fpr(bpm: float) -> int:
    return max(1, min(255, round(3600.0 / bpm / 4.0)))


# ----------------------------------------------------------------------------------------------- score model


class Song:
    def __init__(self) -> None:
        self.name = "song_main"
        self.title = ""
        self.fpr = 9
        self.bpm = 100.0
        self.rows = 16
        self.beats = 4
        self.arp = 3
        self.loop = 0
        self.insts: list[tuple[str, str, dict]] = []       # (name, type, params)
        self.waves: dict[str, str] = dict(WAVES)
        self.chords: dict[str, tuple[int, ...]] = dict(CHORDS)
        self.drums: dict[str, tuple[int, int]] = dict(DRUMS)
        self.bars: dict[int, dict[int, list[str]]] = {}     # bar index -> lane -> cells
        self.warnings: list[str] = []

    def inst_index(self, name: str) -> int:
        for i, (n, _, _) in enumerate(self.insts):
            if n == name:
                return i
        raise ScoreError(f"unknown instrument {name!r}")


def _kv(parts: list[str], what: str) -> dict:
    out = {}
    for p in parts:
        if "=" not in p:
            if p.isalpha():            # a bare flag such as `loop`
                out[p.lower()] = "1"
                continue
            raise ScoreError(f"{what}: expected key=value, got {p!r}")
        k, v = p.split("=", 1)
        out[k.strip().lower()] = v.strip()
    return out


def parse_score(text: str, default_name: str) -> Song:
    s = Song()
    s.name = default_name
    bar: int | None = None
    tempo_src: tuple[str, float] | None = None          # the last bpm:/tempo: line; resolved once rows/beats are known
    beats_given = False

    def resolve_tempo() -> None:
        if not beats_given:
            s.beats = s.rows // 4 if s.rows % 4 == 0 else s.rows
        rpb = s.rows / s.beats                            # rows per beat (4.0 on the 16-row grid, 3.0 on the 12-row grid)
        if tempo_src is None:
            return
        if tempo_src[0] == "bpm":
            s.bpm = tempo_src[1]
            s.fpr = max(1, min(255, round(3600.0 / s.bpm / rpb)))
        else:
            s.fpr = int(tempo_src[1])
            s.bpm = 3600.0 / s.fpr / rpb

    for ln_no, raw in enumerate(text.splitlines(), 1):
        line = re.sub(r"(^|\s)#.*$", "", raw).rstrip()   # a comment starts a line or follows a space; F# is a note
        if not line.strip():
            continue
        try:
            head, _, rest = line.strip().partition(" ")
            key = head.rstrip(":").lower()
            if bar is None and head.endswith(":") and key in ("name", "title", "bpm", "tempo", "rows", "beats", "arp", "loop"):
                v = rest.strip()
                if key == "name":
                    if not re.match(r"^[A-Za-z_]\w*$", v):
                        raise ScoreError(f"name {v!r} is not a C identifier")
                    s.name = v
                elif key == "title":
                    s.title = v
                elif key == "bpm":
                    tempo_src = ("bpm", float(v))
                elif key == "tempo":
                    tempo_src = ("tempo", int(v))
                elif key == "rows":
                    s.rows = int(v)
                elif key == "beats":
                    s.beats = int(v)
                    beats_given = True
                elif key == "arp":
                    s.arp = int(v)
                elif key == "loop":
                    s.loop = int(v)
                continue
            if key == "inst" and not head.endswith(":"):
                parts = rest.split()
                if len(parts) < 2:
                    raise ScoreError("inst needs: inst <name> pulse|wave key=value...")
                name, typ = parts[0], parts[1].lower()
                if typ not in ("pulse", "wave"):
                    raise ScoreError(f"inst {name}: type must be pulse or wave")
                s.insts.append((name, typ, _kv(parts[2:], f"inst {name}")))
                continue
            if key == "wave" and not head.endswith(":"):
                parts = rest.split()
                if len(parts) != 2 or not re.fullmatch(r"[0-9A-Fa-f]{32}", parts[1]):
                    raise ScoreError("wave needs: wave <name> <32 hex nibbles>")
                s.waves[parts[0]] = parts[1].upper()
                continue
            if key == "chord" and not head.endswith(":"):
                parts = rest.split()
                if not 2 <= len(parts) <= 5:
                    raise ScoreError("chord needs: chord <name> <offset> [<offset> [<offset> [<offset>]]]")
                ivs = tuple(int(p) for p in parts[1:])
                if any(not 0 <= iv <= 36 for iv in ivs):
                    raise ScoreError(f"chord {parts[0]}: offsets must be 0..36 semitones")
                s.chords[parts[0]] = ivs
                continue
            if key == "drum" and not head.endswith(":"):
                parts = rest.split()
                if len(parts) < 2 or len(parts[0]) != 1:
                    raise ScoreError("drum needs: drum <letter> env=<hex> poly=<hex>")
                kv = _kv(parts[1:], f"drum {parts[0]}")
                d = (int(kv.get("env", "F1"), 16) & 0xFF, int(kv.get("poly", "5C"), 16) & 0xFF)
                if "then" in kv:
                    m2 = re.fullmatch(r"([0-9A-Fa-f]{1,2}),([0-9A-Fa-f]{1,2})", kv["then"])
                    if not m2:
                        raise ScoreError("drum then=<hex NR42>,<hex NR43>")
                    d += (int(m2.group(1), 16), int(m2.group(2), 16))
                s.drums[parts[0]] = d
                continue
            if key == "bar" and not head.endswith(":"):
                if bar is None:
                    resolve_tempo()
                bar = int(rest.strip()) - 1
                if bar < 0:
                    raise ScoreError("bars are numbered from 1")
                s.bars.setdefault(bar, {})
                continue
            if head.endswith(":") and key in LANES:
                if bar is None:
                    raise ScoreError(f"lane {key!r} before any 'bar N' line")
                cells = rest.split()
                if len(cells) > s.rows:
                    raise ScoreError(f"bar {bar + 1} {key}: {len(cells)} cells, the bar has {s.rows} rows")
                cells += ["."] * (s.rows - len(cells))
                s.bars[bar][LANES[key]] = cells
                continue
            raise ScoreError(f"unrecognised line {line.strip()!r}")
        except (ValueError, ScoreError) as exc:
            raise ScoreError(f"line {ln_no}: {exc}") from None
    if not s.bars:
        raise ScoreError("no bars")
    if not s.insts:
        s.insts = [("lead", "pulse", {"duty": "50", "env": "F2"})]
        s.warnings.append("no instruments declared: using a default 50% pulse")
    if len(s.insts) > 15:
        raise ScoreError("at most 15 instruments")
    if not 1 <= s.fpr <= 255 or not 1 <= s.rows <= 64 or not 1 <= s.arp <= 15:
        raise ScoreError("tempo 1..255 frames per row, rows 1..64, arp 1..15")
    if not 1 <= s.beats <= s.rows or s.rows % s.beats:
        raise ScoreError(f"beats {s.beats} must divide rows {s.rows}")
    n_bars = max(s.bars) + 1
    if n_bars > 255:
        raise ScoreError("at most 255 bars")
    if not 0 <= s.loop < n_bars:
        raise ScoreError(f"loop bar {s.loop} is outside 0..{n_bars - 1}")
    return s


# ----------------------------------------------------------------------------------------------- compiler

CELL_RE = re.compile(r"^([A-Ga-g][#b]?-?\d)?(.*)$")


class Compiled:
    def __init__(self, song: Song) -> None:
        self.song = song
        self.chord_list: list[tuple[int, ...]] = []
        self.wave_list: list[str] = []
        self.drum_list: list[tuple[int, int]] = []
        self.patterns: list[bytes] = []
        self.orders: list[list[int]] = [[], [], [], []]
        self.fx_count: dict[str, int] = {k: 0 for k in FX if k != "none"}
        self.notes = 0
        self.pan_sides: dict[int, set[str]] = {0: set(), 1: set()}   # lane -> sides used by cell pans / echo sides

    def chord_id(self, ivs: tuple[int, ...]) -> int:
        ivs = tuple(ivs[:4])
        if ivs not in self.chord_list:
            self.chord_list.append(ivs)
            if len(self.chord_list) > 255:
                raise ScoreError("at most 255 distinct chords")
        return self.chord_list.index(ivs)

    def wave_id(self, hexs: str) -> int:
        if hexs not in self.wave_list:
            self.wave_list.append(hexs)
            if len(self.wave_list) > 16:
                raise ScoreError("at most 16 wave shapes")
        return self.wave_list.index(hexs)

    def wave_run(self, hexes: list[str]) -> int:
        """A wavetable sequence: consecutive slots (the driver steps wave, wave+1, ...). Returns the first index."""
        if len(hexes) == 1:
            return self.wave_id(hexes[0])
        if len(self.wave_list) + len(hexes) > 16:
            raise ScoreError("at most 16 wave shapes (a wave sequence takes one slot per table)")
        first = len(self.wave_list)
        self.wave_list.extend(hexes)
        return first

    def drum_id(self, letter: str) -> int:
        d = self.song.drums.get(letter)
        if d is None:
            raise ScoreError(f"unknown drum letter {letter!r}")
        d = tuple(d) + (0, 0) if len(d) == 2 else tuple(d)
        if d not in self.drum_list:
            self.drum_list.append(d)
            if len(self.drum_list) > 15:
                raise ScoreError("at most 15 drums")
        return self.drum_list.index(d) + 1

    def pattern_id(self, data: bytes) -> int:
        if data not in self.patterns:
            self.patterns.append(data)
            if len(self.patterns) > 255:
                raise ScoreError("at most 255 distinct patterns (bar lanes)")
        return self.patterns.index(data)


def _signed(v: int) -> int:
    if not -128 <= v <= 127:
        raise ScoreError(f"slide {v} out of -128..127")
    return v & 0xFF


def compile_cell(c: Compiled, lane: int, cell: str, bar: int, row: int) -> tuple[int, int, int]:
    """One cell -> (note, inst<<4 | fx, param)."""
    s = c.song
    where = f"bar {bar + 1} row {row + 1}"
    if cell == ".":
        return 0, 0, 0
    if cell in ("-", "off"):
        return MUSIC_OFF, 0, 0
    if lane == 3:
        if cell.startswith("v") and cell[1:].isdigit():
            return 0, FX["vol"], int(cell[1:]) & 0x0F
        if any(ch in cell for ch in PAN_MARK):
            raise ScoreError(f"{where}: pan markers belong on the lead and arp lanes, never the kit")
        if not 1 <= len(cell) <= 2:
            raise ScoreError(f"{where}: drum cell {cell!r} is one or two drum letters")
        first = c.drum_id(cell[0])
        second = c.drum_id(cell[1]) if len(cell) == 2 else 0
        c.notes += 1
        return (second << 4) | first, 0, 0
    m = CELL_RE.match(cell)
    note_text, mods = m.group(1), m.group(2)
    note = 0
    if note_text:
        note = note_to_midi(note_text)
        lo, hi = WAVE_RANGE if lane == 2 else PULSE_RANGE
        if not lo <= note <= hi:
            s.warnings.append(f"{where}: {note_text} is outside the {'wave' if lane == 2 else 'pulse'} range "
                              f"{midi_to_note(lo)}..{midi_to_note(hi)}; the driver clamps it")
            note = max(lo, min(hi, note))
        c.notes += 1
    inst = 0
    fx = 0
    param = 0
    pan = 0
    seen_fx = 0
    pos = 0
    while pos < len(mods):
        ch = mods[pos]
        rest = mods[pos + 1:]
        if ch == "@":
            m2 = re.match(r"[A-Za-z_]\w*", rest)
            if not m2:
                raise ScoreError(f"{where}: '@' needs an instrument name")
            inst = s.inst_index(m2.group(0)) + 1
            pos += 1 + len(m2.group(0))
            continue
        if ch == "<" or (ch == ">" and not re.match(r"[A-Ga-g][#b]?-?\d", rest)) or (ch == "^" and not re.match(r"\d", rest)):
            if lane not in (0, 1):
                raise ScoreError(f"{where}: pan markers belong on the lead and arp lanes, never the bass")
            if pan:
                raise ScoreError(f"{where}: cell {cell!r} has two pan markers")
            pan = PAN_MARK[ch]
            pos += 1
            continue
        seen_fx += 1
        if seen_fx > 1:
            raise ScoreError(f"{where}: cell {cell!r} has two effects; the driver plays one effect per row")
        if ch == ":":
            m2 = re.match(r"[A-Za-z0-9#_]+", rest)
            if not m2 or m2.group(0) not in s.chords:
                raise ScoreError(f"{where}: unknown chord {rest!r} (see `compose.py styles`)")
            fx, param = FX["arp"], c.chord_id(s.chords[m2.group(0)])
            pos += 1 + len(m2.group(0))
        elif ch == "~":
            m2 = re.match(r"(\d+),(\d+)", rest)
            depth, rate = (int(m2.group(1)), int(m2.group(2))) if m2 else (2, 3)
            fx, param = FX["vib"], ((min(15, depth) << 4) | min(15, rate))
            pos += 1 + (len(m2.group(0)) if m2 else 0)
        elif ch == "^":
            m2 = re.match(r"\d+", rest)
            if not m2:
                raise ScoreError(f"{where}: '^' needs an interval, e.g. ^2")
            fx, param = FX["trill"], (0 << 4) | (int(m2.group(0)) & 0x0F)
            pos += 1 + len(m2.group(0))
        elif ch == "'":
            m2 = re.match(r"\d+", rest)
            if not m2:
                raise ScoreError(f"{where}: ''' needs an interval, e.g. '2")
            fx, param = FX["trill"], (2 << 4) | (int(m2.group(0)) & 0x0F)
            pos += 1 + len(m2.group(0))
        elif ch == "/":
            m2 = re.match(r"(-?\d+)(?:,(\d+))?", rest)
            if not m2:
                raise ScoreError(f"{where}: '/' needs a signed number: /-2,6 (bend from 2 semitones below, resolved in 6 frames) or /-6 (raw slide)")
            if m2.group(2):
                semis, frames_ = int(m2.group(1)), int(m2.group(2))
                if not 1 <= abs(semis) <= BEND_MAX_SEMITONES or not 1 <= frames_ <= 15:
                    raise ScoreError(f"{where}: a bend starts 1..{BEND_MAX_SEMITONES} semitones away and resolves in 1..15 frames, got {cell!r}")
                if not note_text:
                    raise ScoreError(f"{where}: a bend needs the note it resolves onto, e.g. F#2/-2,6")
                fx, param = FX["bend"], (frames_ << 4) | (semis & 0x0F)
            else:
                fx, param = FX["slide"], _signed(int(m2.group(1)))
            pos += 1 + len(m2.group(0))
        elif ch == ">":
            m2 = re.match(r"[A-Ga-g][#b]?-?\d", rest)
            if not m2 or not note_text:
                raise ScoreError(f"{where}: '>' needs a note after a note, e.g. C5>D5")
            fx, param = FX["split"], note_to_midi(m2.group(0))
            pos += 1 + len(m2.group(0))
        elif ch == "v":
            m2 = re.match(r"\d+", rest)
            if not m2:
                raise ScoreError(f"{where}: 'v' needs a volume 0..15")
            fx, param = FX["vol"], min(15, int(m2.group(0)))
            pos += 1 + len(m2.group(0))
        elif ch == "!":
            m2 = re.match(r"\d+", rest)
            if not m2:
                raise ScoreError(f"{where}: '!' needs a frame count")
            fx, param = FX["cut"], max(1, min(255, int(m2.group(0))))
            pos += 1 + len(m2.group(0))
        elif ch == "%":
            m2 = re.match(r"(\d+),(\d+)", rest)
            depth, rate = (int(m2.group(1)), int(m2.group(2))) if m2 else (2, 8)
            if lane != 2 and rate < 6:
                s.warnings.append(f"{where}: tremolo re-strikes a pulse every {rate} frames (clicks); use rate >= 6 or the wave lane")
            fx, param = FX["trem"], ((min(15, max(1, depth)) << 4) | min(15, max(1, rate)))
            pos += 1 + (len(m2.group(0)) if m2 else 0)
        elif ch == "=":
            m2 = re.match(r"\d+", rest)
            if not m2 or not note_text:
                raise ScoreError(f"{where}: '=' needs a note and a frame count, e.g. G4=6 (glide from the previous note in 6 frames)")
            fx, param = FX["porta"], max(1, min(255, int(m2.group(0))))
            pos += 1 + len(m2.group(0))
        elif mods.startswith("echo:", pos):
            arg = mods[pos + 5:]
            if lane != 1:
                raise ScoreError(f"{where}: echo belongs on the arp (pulse 2) lane")
            if arg == "off":
                fx, param = FX["echo"], 0
            else:
                m2 = re.match(r"(\d+),(\d+)(?:,([LRClrc]))?$", arg)
                if not m2:
                    raise ScoreError(f"{where}: echo:<delay 1..15>,<volume drop 0..15>[,L|R|C] or echo:off")
                fx, param = FX["echo"], (max(1, min(15, int(m2.group(1)))) << 4) | min(15, int(m2.group(2)))
                if m2.group(3):                           # the echo voice on one side for the echo's duration
                    if pan:
                        raise ScoreError(f"{where}: cell {cell!r} has two pan markers")
                    pan = PAN[m2.group(3).upper()]
            pos = len(mods)
        elif mods.startswith("arpspeed:", pos):
            m2 = re.match(r"\d+$", mods[pos + 9:])
            if not m2:
                raise ScoreError(f"{where}: arpspeed:<frames 1..15>")
            fx, param = FX["arpspeed"], max(1, min(15, int(m2.group(0))))
            pos = len(mods)
        else:
            raise ScoreError(f"{where}: cannot read {cell!r} at {mods[pos:]!r}")
    if fx:
        c.fx_count[[k for k, v in FX.items() if v == fx][0]] += 1
    if pan:
        # a pan rides on a plain note as MUSIC_FX_PAN; on an effect-only cell (or next to an echo) as the pan
        # pseudo-note 0x80 | side, so the cell's fx / param stay free. A note that already carries an effect has no
        # room for it: put the marker on the row before (`.` -> `<`), the switch then lands one 16th early.
        if note and fx:
            raise ScoreError(f"{where}: cell {cell!r} has an effect and a pan marker; a note cell holds one or the other "
                             f"(put the pan on the row before as an effect-only cell, e.g. `<`)")
        if note:
            fx, param = FX["pan"], pan
        else:
            note = PAN_NOTE | pan
        c.fx_count["pan"] += 1
        c.pan_sides[lane].add(PAN_NAME[pan])
    return note, (inst << 4) | fx, param


def compile_song(song: Song) -> Compiled:
    c = Compiled(song)
    # instruments first (their wave shapes define the wave table order)
    inst_rows = []
    for name, typ, kv in song.insts:
        vib = 0
        if "vib" in kv:
            d, _, dl = kv["vib"].partition(":")
            vib = (min(15, int(d)) << 4) | min(15, int(dl or "2"))
        detune = int(kv.get("detune", "0"))
        if not -8 <= detune <= 7:
            raise ScoreError(f"inst {name}: detune is -8..7 period units")
        penv = 0
        if "penv" in kv:
            m2 = re.fullmatch(r"\+?(\d+),(\d+)", kv["penv"])
            if not m2 or not 1 <= int(m2.group(1)) <= 15 or not 1 <= int(m2.group(2)) <= 15:
                raise ScoreError(f"inst {name}: penv=<semitones 1..15>,<frames 1..15> (start that far above the note, fall onto it)")
            penv = (int(m2.group(1)) << 4) | int(m2.group(2))
        rate = int(kv["rate"]) if "rate" in kv else 0
        if not 0 <= rate <= 7:
            raise ScoreError(f"inst {name}: rate is 1..7 frames per sequence step")
        pan_byte = 0
        if "pan" in kv:
            if typ == "wave":
                raise ScoreError(f"inst {name}: pan is for pulse instruments (the wave bass is never panned)")
            m2 = re.fullmatch(r"(?i)(C|L|R|LR)(?::(\d+))?", kv["pan"].strip())
            if not m2:
                raise ScoreError(f"inst {name}: pan=C|L|R (a side per note) or pan=LR[:frames] (alternate left / right every N frames, default {PAN_AUTO_DEFAULT})")
            side = m2.group(1).upper()
            if side == "LR":
                auto = int(m2.group(2)) if m2.group(2) else (rate if rate and "," not in kv.get("duty", "") else PAN_AUTO_DEFAULT)
                if not 1 <= auto <= 63:
                    raise ScoreError(f"inst {name}: pan=LR:<frames> is 1..63 frames per side")
                pan_byte = auto << 2
                if rate and "," not in kv.get("duty", ""):
                    rate = 0                             # `rate=` fed the auto-pan, not a duty sequence
            else:
                pan_byte = PAN[side]
        if typ == "pulse":
            duties = kv.get("duty", "50").split(",")
            codes = []
            for d in duties:
                if DUTY.get(d) is None:
                    raise ScoreError(f"inst {name}: duty must be 12, 25, 50 or 75 (or 2-4 of them, comma separated)")
                codes.append(DUTY[d] >> 6)
            if not 1 <= len(codes) <= 4:
                raise ScoreError(f"inst {name}: a duty sequence has 2..4 entries")
            env = int(kv.get("env", "F2"), 16) & 0xFF
            seq = 0
            if len(codes) > 1:
                while len(codes) < 4:
                    codes += codes[:4 - len(codes)]
                seq = (codes[0] << 6) | (codes[1] << 4) | (codes[2] << 2) | codes[3]
                rate = rate or 1
            elif rate:
                raise ScoreError(f"inst {name}: rate needs a duty sequence (duty=50,25,...)")
            mod = rate | ((detune & 0x0F) << 4)
            inst_rows.append((DUTY[duties[0]], env, pan_byte, vib, seq, mod, penv, 0, name))
        else:
            vol = max(0, min(15, int(kv.get("vol", "12"))))
            shapes = kv.get("shape", "saw").split(",")
            for shape in shapes:
                if shape not in song.waves:
                    raise ScoreError(f"inst {name}: unknown wave shape {shape!r} (see `compose.py styles`)")
            if len(shapes) > 16:
                raise ScoreError(f"inst {name}: a wave sequence has at most 16 tables")
            first = c.wave_run([song.waves[sh] for sh in shapes])
            seq = len(shapes) - 1
            if seq:
                rate = rate or 2
                if rate < 2:
                    song.warnings.append(f"inst {name}: a wave sequence rewrites wave RAM every frame (clicks); rate >= 2 is kinder")
            elif rate:
                raise ScoreError(f"inst {name}: rate needs a shape list (shape=a,b,c)")
            mod = rate | (0x08 if kv.get("loop") == "1" and seq else 0) | ((detune & 0x0F) << 4)
            wenv = 0
            if "decay" in kv and "attack" in kv:
                raise ScoreError(f"inst {name}: decay or attack, not both")
            if "decay" in kv:
                wenv = max(1, min(127, int(kv["decay"])))
            elif "attack" in kv:
                wenv = 0x80 | max(1, min(127, int(kv["attack"])))
            inst_rows.append((0, vol << 4, first, vib, seq, mod, penv, wenv, name))
    n_bars = max(song.bars) + 1
    for bar in range(n_bars):
        lanes = song.bars.get(bar, {})
        for lane in range(4):
            cells = lanes.get(lane) or ["."] * song.rows
            data = bytearray()
            for row, cell in enumerate(cells):
                data.extend(compile_cell(c, lane, cell, bar, row))
            c.orders[lane].append(c.pattern_id(bytes(data)))
    c.inst_rows = inst_rows  # type: ignore[attr-defined]
    if not c.wave_list:
        c.wave_list.append(WAVES["tri"])
    if not c.chord_list:
        c.chord_list.append((0, 4, 7))
    if not c.drum_list:
        c.drum_list.append(DRUMS["H"] + (0, 0))
    return c


def _bytes_c(data: bytes, per_line: int = 12) -> str:
    out = []
    for i in range(0, len(data), per_line):
        out.append("    " + ", ".join(f"0x{b:02X}" for b in data[i:i + per_line]) + ",")
    return "\n".join(out)


def emit_c(compiled: list[Compiled], source_names: list[str]) -> tuple[str, str, list[dict]]:
    lines = [
        f"/* music_data.c -- generated by scripts/compose.py from {', '.join(source_names)}. Do not edit: edit the",
        " * score and recompile. Format: music.h. */",
        "#include <stdint.h>",
        '#include "music.h"',
        "",
    ]
    hdr = ["/* music_data.h -- generated by scripts/compose.py; songs for music_init(). */",
           "#ifndef MUSIC_DATA_H", "#define MUSIC_DATA_H", '#include "music.h"', ""]
    reports = []
    for c in compiled:
        s = c.song
        n = s.name
        total = 0
        lines.append(f"/* ---- {n}: {s.title or 'untitled'}; {len(c.orders[0])} bars x {s.rows} rows, "
                     f"{s.fpr} frames/row ({s.bpm:.0f} bpm), arp every {s.arp} frames */")
        lines.append(f"static const Instrument {n}_inst[] = {{")
        for duty, env, wave, vib, seq, mod, penv, wenv, name in c.inst_rows:  # type: ignore[attr-defined]
            lines.append(f"    {{ 0x{duty:02X}, 0x{env:02X}, {wave}, 0x{vib:02X}, 0x{seq:02X}, 0x{mod:02X}, 0x{penv:02X}, 0x{wenv:02X} }},  /* {name} */")
        lines.append("};")
        total += 8 * len(c.inst_rows)  # type: ignore[attr-defined]
        chords = bytearray()
        for ivs in c.chord_list:
            chords.extend(list(ivs) + [0xFF] * (4 - len(ivs)))
        lines.append(f"static const uint8_t {n}_chords[] = {{\n{_bytes_c(bytes(chords), 16)}\n}};")
        total += len(chords)
        waves = bytearray()
        for w in c.wave_list:
            waves.extend(int(w[i:i + 2], 16) for i in range(0, 32, 2))
        lines.append(f"static const uint8_t {n}_waves[] = {{\n{_bytes_c(bytes(waves), 16)}\n}};")
        total += len(waves)
        lines.append(f"static const Drum {n}_drums[] = {{")
        for env, poly, env2, poly2 in c.drum_list:
            lines.append(f"    {{ 0x{env:02X}, 0x{poly:02X}, 0x{env2:02X}, 0x{poly2:02X} }},")
        lines.append("};")
        total += 4 * len(c.drum_list)
        for i, p in enumerate(c.patterns):
            lines.append(f"static const uint8_t {n}_p{i}[] = {{\n{_bytes_c(p)}\n}};")
            total += len(p)
        lines.append(f"static const uint8_t *const {n}_patterns[] = {{ " +
                     ", ".join(f"{n}_p{i}" for i in range(len(c.patterns))) + " };")
        total += 2 * len(c.patterns)
        for ch in range(4):
            lines.append(f"static const uint8_t {n}_ord{ch}[] = {{ " + ", ".join(str(x) for x in c.orders[ch]) + " };")
            total += len(c.orders[ch])
        lines.append(f"const Song {n} = {{")
        lines.append(f"    {s.fpr}, {s.rows}, {s.arp}, {len(c.orders[0])}, {s.loop},")
        lines.append(f"    {{ {n}_ord0, {n}_ord1, {n}_ord2, {n}_ord3 }},")
        lines.append(f"    {n}_patterns, {n}_inst, {n}_chords, {n}_waves, {n}_drums")
        lines.append("};")
        lines.append("")
        total += 32
        hdr.append(f"extern const Song {n};  /* {len(c.orders[0])} bars, {s.bpm:.0f} bpm */")
        pulse_names = {name for name, typ, _ in s.insts if typ == "pulse"}
        pan_insts = [r[8] + ":" + ("LR" if r[2] >> 2 else PAN_NAME[r[2] & 3]) for r in c.inst_rows if r[8] in pulse_names and r[2]]  # type: ignore[attr-defined]
        reports.append({
            "name": n, "title": s.title, "bars": len(c.orders[0]), "rows_per_bar": s.rows, "beats_per_bar": s.beats, "frames_per_row": s.fpr,
            "bpm": round(s.bpm, 1), "arp_speed": s.arp, "loop_bar": s.loop, "seconds_per_loop": round(len(c.orders[0]) * s.rows * s.fpr / 60.0, 1),
            "bar_lanes": 4 * len(c.orders[0]), "unique_patterns": len(c.patterns), "instruments": len(c.inst_rows),  # type: ignore[attr-defined]
            "chords": len(c.chord_list), "waves": len(c.wave_list), "drums": len(c.drum_list), "notes": c.notes,
            "effects": {k: v for k, v in c.fx_count.items() if v}, "rom_bytes": total, "warnings": s.warnings,
            "pan_events": c.fx_count["pan"] + len(pan_insts),
            "pan_sides": {EVENT_CHANNELS[ln].replace(" ", ""): sorted(v) for ln, v in c.pan_sides.items() if v}
                         | ({"instruments": sorted(pan_insts)} if pan_insts else {}),
            "syncopation": song_syncopation(s),
        })
    hdr += ["", "#endif", ""]
    return "\n".join(lines), "\n".join(hdr), reports


# ----------------------------------------------------------------------------------------------- generators


class Score:
    """A score under construction: header lines plus cells per bar/lane."""

    def __init__(self, name: str, title: str, bpm: float, rows: int = 16, arp: int = 3, loop: int = 0) -> None:
        self.name, self.title, self.bpm, self.rows, self.arp, self.loop = name, title, bpm, rows, arp, loop
        self.beats = 4
        self.insts: list[str] = []
        self.chords: dict[str, tuple[int, ...]] = {}
        self.bars: list[dict[int, list[str]]] = []
        self.sections: list[tuple[str, int, int]] = []        # (role, start bar, bars), filled by the form generators
        self.protected: set[int] = set()                       # bars whose lead the organic layer must not re-pitch (--hook)

    def bar(self, i: int) -> dict[int, list[str]]:
        while len(self.bars) <= i:
            self.bars.append({lane: ["."] * self.rows for lane in range(4)})
        return self.bars[i]

    def put(self, bar: int, lane: int, row: int, cell: str) -> None:
        self.bar(bar)[lane][row] = cell

    def chord_name(self, ivs: tuple[int, ...]) -> str:
        for k, v in CHORDS.items():
            if v == ivs:
                return k
        for k, v in self.chords.items():
            if v == ivs:
                return k
        name = "v" + "_".join(str(i) for i in ivs)
        self.chords[name] = ivs
        return name

    def text(self, meta: list[str]) -> str:
        out = [f"# {self.title}", *[f"# {m}" for m in meta], f"name: {self.name}", f"title: {self.title}",
               f"bpm: {self.bpm:g}", f"rows: {self.rows}", *([f"beats: {self.beats}"] if self.rows != 4 * self.beats else []),
               f"arp: {self.arp}", f"loop: {self.loop}", ""]
        out += self.insts
        out += [f"chord {k} " + " ".join(str(i) for i in v) for k, v in self.chords.items()]
        names = {0: "lead", 1: "arp", 2: "bass", 3: "drum"}
        for i, b in enumerate(self.bars):
            out.append("")
            out.append(f"bar {i + 1}")
            for lane in range(4):
                out.append(f"{names[lane]}:".ljust(6) + " ".join(b[lane]))
        return "\n".join(out) + "\n"


def voice(root_pc: int, quality: tuple[int, ...], centre: int, prev_top: int | None) -> tuple[int, tuple[int, ...]]:
    """Choose the inversion of `quality` on `root_pc` whose notes sit near `centre` and whose top note moves
    least from `prev_top`. Returns (lowest MIDI note, offsets from it)."""
    best = None
    for octave in (3, 4, 5):
        base = 12 * (octave + 1) + root_pc
        notes = [base + iv for iv in quality]
        for k in range(len(notes)):
            inv = sorted(notes[k:] + [n + 12 for n in notes[:k]])
            mean = sum(inv) / len(inv)
            cost = abs(mean - centre) + (abs(inv[-1] - prev_top) * 0.7 if prev_top is not None else 0)
            if inv[-1] > 100 or inv[0] < 48:
                continue
            if best is None or cost < best[0]:
                best = (cost, inv)
    inv = best[1] if best else sorted(60 + root_pc + iv for iv in quality)
    return inv[0], tuple(n - inv[0] for n in inv)


FUSION_PROGRESSIONS = (  # (degree semitone, quality, scale for the lead) x 4, two bars each
    ((0, "maj9", "lydian"), (5, "maj7", "lydian"), (2, "m9", "dorian"), (7, "9", "mixolydian")),
    ((0, "maj7", "lydian"), (9, "m9", "dorian"), (5, "add9", "lydian"), (7, "7sus4", "mixolydian")),
    ((0, "maj7", "lydian"), (10, "add9", "mixolydian"), (5, "maj7", "lydian"), (0, "maj9", "lydian")),
    ((2, "m9", "dorian"), (7, "9", "mixolydian"), (0, "maj7", "lydian"), (9, "m7", "dorian")),
    ((0, "maj7", "lydian"), (4, "m7", "dorian"), (9, "m9", "dorian"), (5, "69", "lydian")),
)
MODULATIONS = (0, -4, 3, 0, 5, -4)  # F# -> D -> A -> F# -> B -> G... (the fusion reference's moves: down a major third, up a minor sixth)


def gen_fusion(rng: random.Random, key: int, bpm: float, bars: int, name: str, bend: str = "sparse",
               brng: random.Random | None = None) -> tuple[Score, list[str]]:
    sc = Score(name, "Fusion theme", bpm, rows=16, arp=3 if bpm >= 95 else 4)
    sc.insts = [
        "inst lead pulse duty=50 env=C2 vib=2:3",
        "inst lead2 pulse duty=25 env=B2 vib=3:2",
        "inst arp pulse duty=25 env=90",
        "inst arp2 pulse duty=12 env=A0",
        "inst bass wave vol=13 shape=saw",
        "inst bassr wave vol=11 shape=tri",
    ]
    bars = max(8, (bars + 7) // 8 * 8)
    sections = bars // 8
    meta = []
    prev_top = None
    mod_i = 0
    section_key = key
    echo_section = sections // 2 if sections >= 3 else -1   # the middle section trades the chord for the echo
    for sec in range(sections):
        if sec and (sec % 2 == 0 or rng.random() < 0.35):
            mod_i += 1
            section_key = (key + MODULATIONS[mod_i % len(MODULATIONS)]) % 12
        prog = rng.choice(FUSION_PROGRESSIONS)
        meta.append(f"section {sec + 1}: bars {sec * 8 + 1}-{sec * 8 + 8}, key {PC_NAME[section_key]}, "
                    + " ".join(f"{PC_NAME[(section_key + d) % 12]}{q}" for d, q, _ in prog)
                    + (" (echo section)" if sec == echo_section else ""))
        lead_inst = "lead" if sec % 2 == 0 else "lead2"
        arp_inst = "arp" if sec % 2 == 0 else "arp2"
        for ci, (deg, qual, scale_name) in enumerate(prog):
            root_pc = (section_key + deg) % 12
            low, ivs = voice(root_pc, CHORDS[qual], 72, prev_top)
            prev_top = low + ivs[-1]
            cname = sc.chord_name(ivs)
            scale = [(root_pc + x) % 12 for x in SCALES[scale_name]]
            chord_pcs = [(root_pc + iv) % 12 for iv in CHORDS[qual]]
            for half in range(2):
                bar = sec * 8 + ci * 2 + half
                # ---- pulse 2: the fusion chord, or the echo of the lead in the echo section
                if sec == echo_section:
                    if half == 0 and ci == 0:
                        sc.put(bar, 1, 0, f"echo:{rng.choice([4, 5, 6])},{rng.choice([3, 4])}")
                else:
                    if half == 0:
                        sc.put(bar, 1, 0, f"{midi_to_note(low)}:{cname}@{arp_inst}")
                    elif rng.random() < 0.5:   # re-voice up an octave slot for a bar, then back
                        sc.put(bar, 1, 8, f"{midi_to_note(low + 12 if low + 12 + ivs[-1] <= 100 else low)}:{cname}")
                        sc.put(bar, 1, 15 if rng.random() < 0.3 else 12, f"{midi_to_note(low)}:{cname}")
                # ---- wave: slap-style walking bass
                _fusion_bass(sc, rng, bar, root_pc, chord_pcs, scale, next_root_pc=(section_key + prog[(ci + 1) % 4][0]) % 12,
                             last=(half == 1), accent_inst="bass" if sec % 2 == 0 else "bassr", bend=bend)
                # ---- noise: fusion kit
                _fusion_drums(sc, rng, bar, fill=(bar % 8 == 7))
            # ---- pulse 1: a two-bar lead phrase per chord
            _fusion_lead(sc, rng, sec * 8 + ci * 2, scale, chord_pcs, lead_inst, busy=(sec == echo_section), bend=bend, brng=brng)
    return sc, meta


def _nearest_in(pcs: list[int], target: int, lo: int, hi: int) -> int:
    best = None
    for n in range(lo, hi + 1):
        if n % 12 in pcs:
            d = abs(n - target)
            if best is None or d < best[0]:
                best = (d, n)
    return best[1]


def _fusion_bass(sc: Score, rng: random.Random, bar: int, root_pc: int, chord_pcs: list[int], scale: list[int],
                 next_root_pc: int, last: bool, accent_inst: str, bend: str = "sparse") -> None:
    root = 36 + root_pc if root_pc <= 9 else 24 + root_pc      # B1..A2 like the reference
    fifth = root + 7 if root + 7 <= 47 else root - 5
    pattern = rng.choice(("walk", "bounce", "slap", "pedal"))
    cells = ["."] * 16
    if pattern == "bounce":          # root / octave alternation in 8ths, extra 16th bounces
        for r in range(0, 16, 2):
            cells[r] = f"{midi_to_note(root)}" if r % 4 == 0 else f"{midi_to_note(root + 12)}!3"
        for r in rng.sample([3, 7, 11, 13], 2):
            cells[r] = f"{midi_to_note(root + 12)}!2"
    elif pattern == "walk":          # root, fifth, octave, scale steps toward the next root
        walk = [root, root + 12, fifth, root + 12, root, fifth, root + 12, root]
        for i, n in enumerate(walk):
            cells[i * 2] = f"{midi_to_note(n)}!4" if i % 2 else midi_to_note(n)
        cells[13] = f"{midi_to_note(_nearest_in(scale, root + 10, root - 2, root + 14))}!4"
    elif pattern == "slap":          # 16th pairs: thumb (root) + pop (octave) on beats 1 and 3
        for beat in (0, 8):
            cells[beat] = midi_to_note(root)
            cells[beat + 1] = f"{midi_to_note(root + 12)}!3"
            cells[beat + 4] = f"{midi_to_note(fifth)}!4"
            cells[beat + 6] = f"{midi_to_note(root + 12)}!3"
            cells[beat + 7] = f"{midi_to_note(root)}!3"
    else:                            # pedal with octave bounce on the and-of-two
        for r in (0, 4, 8, 12):
            cells[r] = midi_to_note(root)
        cells[6] = f"{midi_to_note(root + 12)}!3"
        cells[14] = f"{midi_to_note(root + 12)}!3"
    # the downbeat may bend INTO the root from a tone below and land in 6 frames (a slap articulation, never a
    # siren): only on even bars, and only as often as the --bend knob allows; it always resolves onto the root
    bass_rate = BEND_RATES.get(bend, BEND_RATES["sparse"])[0]
    draw = rng.random()   # drawn every bar (keeps the rest of a seed's tune stable whatever --bend says)
    if bar % 2 == 0 and draw < bass_rate:
        cells[0] = f"{midi_to_note(root)}@{accent_inst}/-2,6"
    else:
        cells[0] = f"{midi_to_note(root)}@{accent_inst}"
    if last:                         # approach note into the next chord on the last 16th
        nxt = 36 + next_root_pc if next_root_pc <= 9 else 24 + next_root_pc
        approach = nxt + rng.choice((-1, -2, 1))
        if 33 <= approach <= 50:
            cells[15] = f"{midi_to_note(approach)}!6"
    for r, c in enumerate(cells):
        sc.put(bar, 2, r, c)


def _fusion_drums(sc: Score, rng: random.Random, bar: int, fill: bool) -> None:
    cells = ["."] * 16
    if fill:
        seq = ["KH", "H", "S", "s", "SH", "s", "S", "S", "T", "T", "S", "S", "T", "KT", "SC", "K"]
        for r, c in enumerate(seq):
            cells[r] = c
    else:
        for r in range(16):
            cells[r] = "H" if r % 2 == 0 else ("h" if rng.random() < 0.7 else ".")
        cells[0] = "KH"
        cells[8] = "KH"
        cells[4] = "SH"
        cells[12] = "SH"
        for r in rng.sample([6, 10, 14, 3], rng.choice((1, 2))):   # syncopated kicks
            cells[r] = "Kh" if r % 2 else "KH"
        for r in rng.sample([7, 11, 15, 2], rng.choice((1, 2))):   # ghost snares
            cells[r] = "sh" if cells[r] in ("H", "h", ".") else cells[r]
        if rng.random() < 0.5:
            cells[rng.choice((2, 10))] = "O"
    for r, c in enumerate(cells):
        sc.put(bar, 3, r, c)


def _fusion_lead(sc: Score, rng: random.Random, bar0: int, scale: list[int], chord_pcs: list[int], inst: str, busy: bool,
                 bend: str = "sparse", brng: random.Random | None = None) -> None:
    """Two bars (32 rows): rest, a 16th run with 32nd ornaments, a held chord tone with vibrato or a trill."""
    cells = ["."] * 32
    row = rng.choice((0, 2, 4)) if not busy else 0
    phrases = 2 if busy or rng.random() < 0.5 else 1
    for _ in range(phrases):
        if row >= 26:
            break
        length = rng.choice((5, 6, 7, 8))
        direction = rng.choice((1, 1, -1))
        start = _nearest_in(chord_pcs, rng.choice((55, 59, 62, 67)), 52, 72)   # the reference lead lives E3..A6
        run = [start]
        n = start
        for _ in range(length - 1):
            step = direction
            n = n + step
            while n % 12 not in scale:
                n += step
            if n > 81 or n < 52:
                direction = -direction
                n = run[-1] + direction
                while n % 12 not in scale:
                    n += direction
            run.append(n)
        for i, n in enumerate(run):
            if row >= 31:
                break
            cell = midi_to_note(n)
            if i == 0:
                cell += f"@{inst}'2"                                  # mordent on the phrase start
            elif rng.random() < 0.35 and i + 1 < len(run):           # 32nd pair: two scale steps in one row
                cell += ">" + midi_to_note(run[i + 1])
            cells[row] = cell
            row += 1
        target = _nearest_in(chord_pcs, run[-1] + direction * 2, 52, 81)
        hold = rng.choice((3, 4, 5, 6))
        if row < 32:
            # the arrival note: a trill, vibrato, or (rarely) a bend from a semitone or tone below that lands on the
            # chord tone within 5 frames and then holds for the rest of the phrase
            brng = brng or random.Random(0)
            ornament = rng.random() < 0.4          # the seed's own choice between trill and vibrato
            if brng.random() < BEND_RATES.get(bend, BEND_RATES["sparse"])[1]:
                cells[row] = f"{midi_to_note(target)}/{brng.choice((-1, -2))},{brng.choice((4, 5))}"
            elif ornament:
                cells[row] = f"{midi_to_note(target)}^2"
            else:
                cells[row] = f"{midi_to_note(target)}~"
            if rng.random() < 0.4 and row + 2 < 32:
                cells[row + 2] = f"{midi_to_note(target)}~2,3"       # trill resolves into vibrato
        row += hold
        if row < 32:
            cells[row] = "-"
        row += rng.choice((1, 2, 3))
    for r, c in enumerate(cells):
        sc.put(bar0 + r // 16, 0, r % 16, c)


def gen_ambient(rng: random.Random, key: int, bpm: float, bars: int, name: str, bend: str = "sparse",
                brng: random.Random | None = None) -> tuple[Score, list[str]]:
    bpm = min(bpm, 72)
    sc = Score(name, "Ambient drone", bpm, rows=16, arp=8)
    sc.insts = [
        "inst glow pulse duty=25 env=70 vib=1:4",
        "inst haze pulse duty=12 env=50",
        "inst drone wave vol=7 shape=soft",
        "inst swell wave vol=9 shape=tri",
    ]
    bars = max(8, (bars + 3) // 4 * 4)
    quals = ("maj7", "add9", "sus2", "maj9", "m9", "69")
    degrees = (0, 5, 7, 9, 2)
    meta = []
    prev_top = None
    for ci in range(bars // 4):
        deg = degrees[0] if ci % 4 == 0 else rng.choice(degrees)
        qual = rng.choice(quals)
        root_pc = (key + deg) % 12
        low, ivs = voice(root_pc, CHORDS[qual], 76, prev_top)
        prev_top = low + ivs[-1]
        cname = sc.chord_name(ivs)
        meta.append(f"bars {ci * 4 + 1}-{ci * 4 + 4}: {PC_NAME[root_pc]}{qual}")
        b0 = ci * 4
        root = 36 + root_pc if root_pc <= 9 else 24 + root_pc
        sc.put(b0, 2, 0, f"{midi_to_note(root)}@{'drone' if ci % 2 == 0 else 'swell'}")
        if rng.random() < 0.5:
            sc.put(b0 + 2, 2, 8, f"{midi_to_note(root + (7 if root + 7 <= 47 else -5))}")
            sc.put(b0 + 3, 2, 8, midi_to_note(root))
        sc.put(b0 + rng.choice((0, 1)), 1, rng.choice((0, 4)), f"{midi_to_note(low)}:{cname}@haze")
        if rng.random() < 0.6:
            sc.put(b0 + 3, 1, 12, "-")
        # one or two long lead notes per 4 bars
        tone = low + rng.choice(ivs)
        while tone > 81:   # keep the glow in C5..A5
            tone -= 12
        while tone < 72:
            tone += 12
        bar = b0 + rng.choice((0, 1))
        sc.put(bar, 0, rng.choice((0, 2, 4, 8)), f"{midi_to_note(tone)}@glow~1,6")
        sc.put(bar + 2, 0, rng.choice((0, 8)), "-")
        if rng.random() < 0.5:
            tone2 = _nearest_in([(root_pc + x) % 12 for x in SCALES["lydian"]], tone + rng.choice((-2, 2, 5)), 72, 81)
            sc.put(bar + 2, 0, 12, f"{midi_to_note(tone2)}~1,8")
            sc.put(b0 + 3, 0, 14, "-")
        if ci % 2 == 1:
            sc.put(b0, 3, 0, "h")
    return sc, meta


def gen_chip(rng: random.Random, key: int, bpm: float, bars: int, name: str, bend: str = "sparse",
             brng: random.Random | None = None) -> tuple[Score, list[str]]:
    sc = Score(name, "Chip pop", bpm, rows=16, arp=2)
    sc.insts = [
        "inst lead pulse duty=50 env=B1 vib=2:4",
        "inst arp pulse duty=25 env=80",
        "inst bass wave vol=12 shape=square",
    ]
    bars = max(4, (bars + 3) // 4 * 4)
    prog = rng.choice((((0, "maj"), (7, "maj"), (9, "min"), (5, "maj")), ((0, "maj"), (5, "maj"), (9, "min"), (7, "maj")),
                       ((9, "min"), (5, "maj"), (0, "maj"), (7, "maj")), ((0, "maj"), (9, "min"), (2, "min"), (7, "maj"))))
    pent = [(key + x) % 12 for x in SCALES["pent"]]
    meta = [" ".join(f"{PC_NAME[(key + d) % 12]}{q}" for d, q in prog)]
    prev_top = None
    motif = [rng.choice((0, 2, 4, 7, 9, 12)) for _ in range(4)]
    for bar in range(bars):
        deg, qual = prog[bar % 4]
        root_pc = (key + deg) % 12
        low, ivs = voice(root_pc, CHORDS[qual], 74, prev_top)
        prev_top = low + ivs[-1]
        sc.put(bar, 1, 0, f"{midi_to_note(low)}:{sc.chord_name(ivs)}@arp")
        root = 36 + root_pc if root_pc <= 9 else 24 + root_pc
        for r in range(0, 16, 2):
            n = root if r % 8 in (0, 4) else (root + 7 if r % 8 == 2 else root + 12)
            sc.put(bar, 2, r, f"{midi_to_note(n)}@bass!5" if r else f"{midi_to_note(n)}@bass!6")
        for r in range(16):
            sc.put(bar, 3, r, "KH" if r in (0, 8) else ("SH" if r in (4, 12) else ("H" if r % 2 == 0 else ".")))
        if bar % 4 == 3:
            sc.put(bar, 3, 14, "S")
            sc.put(bar, 3, 15, "s")
        base = 72 + key
        if bar % 2 == 0:
            for i, m in enumerate(motif):
                n = _nearest_in(pent, base + m, 67, 91)
                sc.put(bar, 0, i * 2, f"{midi_to_note(n)}@lead" if i == 0 else midi_to_note(n))
            sc.put(bar, 0, 8, "-")
            n = _nearest_in(pent, base + motif[-1] + rng.choice((-3, 2, 5)), 67, 91)
            sc.put(bar, 0, 10, f"{midi_to_note(n)}~")
            sc.put(bar, 0, 15, "-")
        else:
            n = _nearest_in(pent, base + rng.choice(motif) + 2, 67, 91)
            sc.put(bar, 0, 0, midi_to_note(n))
            sc.put(bar, 0, 2, midi_to_note(_nearest_in(pent, n - 2, 67, 91)))
            sc.put(bar, 0, 4, f"{midi_to_note(_nearest_in(pent, n - 4, 67, 91))}~")
            sc.put(bar, 0, 12, "-")
    return sc, meta


# ----------------------------------------------------------------------------------------------- song form
# Pop / rock song form: sections (intro, verse, pre-chorus, chorus, bridge, outro; AABA; the twelve-bar blues),
# a progression library in Roman numerals resolved against --key, and repetition with controlled variation
# (a phrase repeats, its last bar changes; the chorus is the hook and comes back identical; the second verse is
# one note different; the bridge changes harmony and register). Research notes: research_notes/pop-rock-song-form/.

ROMAN_DEG = {"I": 0, "II": 2, "III": 4, "IV": 5, "V": 7, "VI": 9, "VII": 11}
ROMAN_RE = re.compile(r"^([b#]?)(VII|VI|IV|V|III|II|I|vii|vi|iv|v|iii|ii|i)(.*)$")

# name: (Roman numerals, one bar per symbol in the chorus, what it gives)
PROGRESSIONS = {
    "axis":       ("I V vi IV", "bright pop anthem, the four-chord loop of a thousand hits"),
    "sensitive":  ("vi IV I V", "wistful, bittersweet: the same four chords starting on the minor"),
    "doowop":     ("I vi IV V", "1950s rock'n'roll sweetness, the doo-wop changes"),
    "hopscotch":  ("IV V vi I", "modern pop since 2010: floats, lands on I by a skip"),
    "threechord": ("I IV V IV", "garage rock, three chords and the truth"),
    "mixolydian": ("I bVII IV I", "classic rock swagger: bVII is the rock dominant"),
    "shuttle":    ("I bVII I bVII", "two-chord rock shuttle under a riff"),
    "andalusian": ("i bVII bVI V", "dramatic descending minor; flamenco, surf, early-60s R&B"),
    "aeolian":    ("i bVI bIII bVII", "epic minor rock / power ballad (i-VI-III-VII)"),
    "dorian":     ("i IV i IV", "two-chord dorian groove: funk, latin rock, late-60s psychedelia"),
    "plagal":     ("I IV iv I", "the plagal sigh: IV turns minor on the way home; nostalgic"),
    "turnaround": ("I vi ii V", "jazz / early rock turnaround (the rhythm-changes A section)"),
    "pachelbel":  ("I V vi iii IV I IV V", "stately descending bass, baroque canon to punk ballad"),
    "fanfare":      ("bVI bVII I I", "the video-game fanfare cadence; triumphant (level clear, victory)"),
    "puff":       ("I iii IV I", "gentle folk-pop opening"),
    "blues12":    ("I I I I IV IV I I V IV I V", "the twelve-bar blues: three 4-bar phrases, aab"),
    "blues12q":   ("I IV I I IV IV I I V IV I V", "twelve-bar blues with the quick change to IV in bar 2"),
    "skank":      ("I IV V V", "ska / rocksteady drive: three chords, the V held into the turnaround"),
    # measured in the reference corpora (the stage corpus and the RPG corpus)
    "stage_a":       ("i i bVI bVII", "stage corpus A section: driving aeolian minor, VII pulls home"),
    "stage_b":       ("i i iv bVII", "stage corpus B section: the same drive through iv"),
    "stage_c":       ("i IV bVII i", "stage corpus C section: the dorian IV lift under a climbing lead"),
    "stage_shuttle": ("i bVII i bVII", "stage corpus two-chord minor shuttle"),
    "stage_offtonic":  ("bVI bVI i i", "stage corpus off-tonic start that lands home every four bars"),
    "stage_pedal":   ("i i i iv", "stage corpus pedal riff with one lean to iv"),
    "boss":    ("i i i i IV IV ii V", "stage corpus boss loop: four bars of tonic, then IV ii V back round (8 bars)"),
    "cadential":   ("I V V vi I V V I", "RPG corpus cadential major: I-V-V-vi, I-V-V-I (the healing-house theme)"),
    "town":     ("I IV vi I vi IV vi V", "RPG corpus town theme: I-IV-vi colour, V at the end of the phrase"),
}
FORMS = {
    "loop": "the style's own loop, no sections (fusion / ambient / chip as before)",
    "stage": "stage-corpus loop: (intro 4) A 8 B 8 C 8, each section a 4-bar phrase and its varied repeat, a new progression per section, loop at A (16, 24 or 28 bars)",
    "verse-chorus": "intro | verse | pre-chorus | chorus | verse | pre-chorus | chorus | bridge | chorus | outro (32, 48 or 64 bars)",
    "aaba": "A A' B A: the 32-bar song form, B is the middle eight in a new key area (+ intro/outro at 40 bars)",
    "blues12": "intro + N twelve-bar choruses: head, head an octave up, solo, head (28, 40 or 52 bars)",
}
TEXTURES = {
    "plain": "triads / power chords, straight kit, vibrato on held notes (pop, rock, chip as written)",
    "fusion": "the fusion idioms on any form: maj7/add9/m9 colour on the pulse-2 chord cycle, mordents and trills on the lead, slap bass with octave bounces, the fusion kit, the echo voice in the bridge / B section",
}
FUSION_COLOUR = {"maj": "maj7", "min": "m9", "5": "add9", "7": "9", "m7": "m9", "dim": "m7b5"}
LIFTS = {"fifth": 7, "sixth": 9, "octave": 12}   # semitones the chorus / C section / final A / head 2 lead sits above the verse
# chord quality a style prefers for a plain major / minor symbol
STYLE_QUALITY = {"pop": {"maj": "maj", "min": "min"}, "chip": {"maj": "maj", "min": "min"},
                 "rock": {"maj": "5", "min": "min"}, "blues": {"maj": "7", "min": "m7"}, "ska": {"maj": "maj", "min": "min"}}
# two-bar lead rhythms (rows 0..31; 16 rows = one bar of 16ths)
RHYTHMS = {
    "straight": (0, 2, 4, 6, 8, 12, 16, 18, 20, 24, 28),
    "sync":     (0, 3, 6, 8, 12, 14, 16, 19, 22, 24, 28),
    "long":     (0, 4, 8, 14, 16, 20, 24),
    "quick":    (0, 2, 4, 6, 8, 10, 12, 16, 18, 20, 22, 24, 28),
    "pickup":   (0, 2, 4, 6, 8, 12, 14, 16, 20, 24),
    "call":     (0, 2, 4, 8, 10, 12),                       # one bar of notes, one bar of rest
    "answer":   (16, 18, 20, 24, 26, 28),                   # the response: notes in the second bar only
}
# one-bar bass riffs for rock: (rows, semitones from the chord root)
RIFFS = {
    "chug":    ((0, 2, 4, 6, 8, 10, 12, 14), (0, 0, 0, 0, 0, 0, 10, 0)),
    "gallop":  ((0, 3, 4, 8, 11, 12), (0, 12, 0, 0, 12, 0)),
    "pent":    ((0, 2, 4, 6, 8, 10, 12, 14), (0, 3, 5, 0, 7, 5, 3, 0)),
    "descend": ((0, 3, 6, 8, 10, 12, 14), (0, 0, 3, 0, -2, -4, -5)),
    "boogie":  ((0, 3, 4, 7, 8, 11, 12, 15), (0, 4, 7, 9, 10, 9, 7, 4)),   # swung 8ths: the blues walking bass
}


def roman_chord(sym: str) -> tuple[int, str]:
    """'bVII7' -> (10, '7'); 'vi' -> (9, 'min'); 'IVmaj7' -> (5, 'maj7'). Degree in semitones above the key."""
    m = ROMAN_RE.match(sym.strip())
    if not m:
        raise ScoreError(f"bad Roman numeral {sym!r} (want e.g. I, vi, bVII, IVmaj7, V7)")
    acc, num, suf = m.groups()
    deg = (ROMAN_DEG[num.upper()] + {"b": -1, "#": 1, "": 0}[acc]) % 12
    minor = num.islower()
    if suf == "":
        qual = "min" if minor else "maj"
    elif suf == "7":
        qual = "m7" if minor else "7"
    elif suf in CHORDS:
        qual = suf
    elif minor and "m" + suf in CHORDS:
        qual = "m" + suf
    else:
        raise ScoreError(f"unknown chord suffix {suf!r} in {sym!r} (see `compose.py styles`)")
    return deg, qual


def resolve_progression(text: str) -> tuple[str, list[str]]:
    """A library name or a quoted numeral string -> (name, symbols)."""
    key = text.strip().lower().replace("-", "")
    if key in PROGRESSIONS:
        return key, PROGRESSIONS[key][0].split()
    syms = text.replace(",", " ").replace("-", " ").split()
    for s in syms:
        roman_chord(s)
    if not syms:
        raise ScoreError("empty progression")
    return "custom", syms


def resolve_progressions(text: str) -> list[tuple[str, list[str]]]:
    """'stage_a | stage_b | stage_c' -> one progression per section (stage: A, B, C; verse-chorus: chorus, verse, bridge)."""
    return [resolve_progression(part) for part in text.split("|") if part.strip()]


def numerals_to_names(syms: list[str], key: int) -> str:
    return " ".join(PC_NAME[(key + roman_chord(s)[0]) % 12] + ("m" if roman_chord(s)[1] in ("min", "m7") else "") for s in syms)


def _mode_scale(syms: list[str]) -> str:
    """The scale the lead lives in, read off the progression: minor tonic -> minor; a bVII under a major tonic
    -> mixolydian; else major."""
    first = roman_chord(syms[0])
    if first[1] in ("min", "m7"):
        return "minor"
    if any(s.startswith("bVII") for s in syms):
        return "mixolydian"
    return "major"


def _rotate_for_verse(syms: list[str]) -> list[str]:
    """The verse takes the rotation of a four-chord loop that starts on the other of {I, vi}: a verse off the
    tonic makes the chorus's I an arrival (the 'telos' chorus); a vi-led chorus gets a bright I-led verse."""
    if len(syms) != 4:
        return list(syms)
    upper = [s.upper().lstrip("B#") for s in syms]
    if syms[0] == "I" and "vi" in syms:
        i = syms.index("vi")
        return syms[i:] + syms[:i]
    if syms[0] == "vi" and "I" in syms:
        i = syms.index("I")
        return syms[i:] + syms[:i]
    if syms[0] in ("I", "i") and len(set(upper)) == 4:
        return syms[1:] + syms[:1]
    return list(syms)


def _prechorus_syms(mode: str) -> list[str]:
    return {"major": ["IV", "ii", "V", "V"], "mixolydian": ["IV", "IV", "V", "V"], "minor": ["bVI", "iv", "V", "V"]}[mode]


def _bridge_syms(mode: str, bars: int) -> list[str]:
    full = {"major": ["vi", "IV", "vi", "IV", "ii", "IV", "V", "V"],
            "mixolydian": ["IV", "bVII", "IV", "bVII", "IV", "IV", "V", "V"],
            "minor": ["bVI", "bVII", "bVI", "bVII", "iv", "bVI", "V", "V"]}[mode]
    return full if bars >= 8 else full[:2] + full[6:]


class Section:
    def __init__(self, role: str, bars: int, syms: list[str], label: str = "") -> None:
        self.role, self.bars, self.syms, self.label = role, bars, syms, label or role
        self.start = 0   # bar index, filled by the planner


def _stage_variants(a: list[str], mode: str) -> tuple[list[str], list[str]]:
    """B and C progressions for the stage form when only one is given: B swaps the third chord (iv / ii), C
    replaces the second with the major IV (the stage corpus's dorian lift) and ends on the tonic."""
    tonic = "i" if mode == "minor" else "I"
    b = list(a)
    if len(b) >= 3:
        b[2] = {"minor": "iv", "mixolydian": "IV", "major": "ii"}[mode] if b[2] not in ("iv", "ii") else ("bVI" if mode == "minor" else "vi")
    c = list(a)
    if len(c) >= 4:
        c[1] = "IV"
        c[-1] = tonic
    return b, c


def build_plan(form: str, bars: int, chorus_syms: list[str], mode: str, rng: random.Random,
               extra: list[list[str]] | None = None) -> list[Section]:
    """Sections with one chord symbol per bar. The chorus plays its loop at one bar per chord; the verse plays
    the rotated loop at two bars per chord (a slower harmonic rhythm is the first, cheapest contrast).
    `extra` = further progressions from `--progression a | b | c` (stage: B and C; verse-chorus/aaba: verse
    and bridge overrides)."""
    def loop_to(syms: list[str], n: int, bars_per: int) -> list[str]:
        out: list[str] = []
        while len(out) < n:
            for s in syms:
                out += [s] * bars_per
        return out[:n]
    extra = extra or []
    verse_syms = extra[0] if extra else _rotate_for_verse(chorus_syms)
    per_verse = 2 if len(verse_syms) <= 4 else 1
    if form == "stage":
        b_syms, c_syms = _stage_variants(chorus_syms, mode)
        if len(extra) >= 1:
            b_syms = extra[0]
        if len(extra) >= 2:
            c_syms = extra[1]
        plan = (["intro:4"] if bars >= 28 else []) + ["S1:8", "S2:8"] + (["S3:8"] if bars > 16 else [])
        sections = []
        for item in plan:
            role, n = item.split(":")
            n = int(n)
            syms = {"intro": loop_to(chorus_syms, n, 1), "S1": loop_to(chorus_syms, n, 1), "S2": loop_to(b_syms, n, 1), "S3": loop_to(c_syms, n, 1)}[role]
            sec = Section(role, n, syms, {"intro": "intro", "S1": "A", "S2": "B", "S3": "C"}[role])
            sections.append(sec)
        start = 0
        for s in sections:
            s.start = start
            start += s.bars
        return sections
    if form == "verse-chorus":
        plans = {
            32: ["intro:4", "verse:8", "prechorus:4", "chorus:8", "chorus:8"],
            48: ["intro:4", "verse:8", "prechorus:4", "chorus:8", "verse:8", "prechorus:4", "chorus:8", "outro:4"],
            64: ["intro:4", "verse:8", "prechorus:4", "chorus:8", "verse:8", "prechorus:4", "chorus:8", "bridge:8", "chorus:8", "outro:4"],
        }
        size = min(plans, key=lambda n: (abs(n - bars), -n))
        plan = plans[size]
    elif form == "aaba":
        plan = ["A:8", "A2:8", "B:8", "A3:8"] if bars < 40 else ["intro:4", "A:8", "A2:8", "B:8", "A3:8", "outro:4"]
    elif form == "blues12":
        n = max(2, min(4, round((bars - 4) / 12)))
        roles = {2: ["head", "solo"], 3: ["head", "head2", "solo"], 4: ["head", "head2", "solo", "head3"]}[n]
        plan = ["intro:4"] + [f"{r}:12" for r in roles]
    else:
        raise ScoreError(f"unknown form {form!r}")
    sections: list[Section] = []
    n_chorus = 0
    for item in plan:
        role, n = item.split(":")
        n = int(n)
        if role in ("intro", "outro"):
            syms = loop_to(chorus_syms, n, 1)
            if form == "blues12":
                syms = chorus_syms[8:12]                     # the turnaround V IV I V is the classic blues intro
            if role == "outro":
                syms = syms[:-1] + ["I" if mode != "minor" else "i"]
        elif role == "verse":
            syms = loop_to(verse_syms, n, per_verse)
        elif role == "prechorus":
            syms = _prechorus_syms(mode)
        elif role == "bridge" or role == "B":
            syms = loop_to(extra[1], n, 1) if len(extra) >= 2 else _bridge_syms(mode, n)
        elif role.startswith("A"):
            syms = loop_to(chorus_syms, n, per_verse if len(chorus_syms) <= 4 else 1)
        elif role in ("head", "head2", "head3", "solo"):
            syms = list(chorus_syms)
        else:                                                # chorus
            n_chorus += 1
            syms = loop_to(chorus_syms, n, 1)
        sec = Section(role, n, syms)
        if role == "chorus":
            sec.label = f"chorus {n_chorus}"
        sections.append(sec)
    start = 0
    for s in sections:
        s.start = start
        start += s.bars
    return sections


class Melody:
    """Scale-degree melodies: a motif is a list of (row, degree) in a two-bar frame; degrees index a sorted list
    of the scale's notes, so transposing by a degree stays in the scale and an octave is len(scale) degrees."""

    def __init__(self, key: int, scale_name: str) -> None:
        self.key = key
        self.pcs = [(key + x) % 12 for x in SCALES[scale_name]]
        self.notes = [n for n in range(PULSE_RANGE[0], PULSE_RANGE[1] + 1) if n % 12 in self.pcs]
        self.octave = len(self.pcs)

    def index_near(self, midi: int) -> int:
        return min(range(len(self.notes)), key=lambda i: abs(self.notes[i] - midi))

    def note(self, centre: int, deg: int) -> int:
        return self.notes[max(0, min(len(self.notes) - 1, centre + deg))]

    def snap(self, midi: int, chord_pcs: list[int]) -> int:
        """Nearest chord tone (any pitch class of the chord), preferring the note itself."""
        if midi % 12 in chord_pcs:
            return midi
        best = min((abs(n - midi), n) for n in range(midi - 6, midi + 7) if n % 12 in chord_pcs)
        return best[1]

    def tonic_degree_near(self, centre: int, deg: int) -> int:
        """The degree closest to `deg` whose note is the key's tonic."""
        cands = [d for d in range(deg - self.octave, deg + self.octave + 1) if self.note(centre, d) % 12 == self.key]
        return min(cands, key=lambda d: (abs(d - deg), d)) if cands else deg


def make_motif(rng: random.Random, rhythm: str, span: int = 6, R: int = 16) -> list[tuple[int, int]]:
    """A two-bar motif: mostly steps, a leap at the start of the second bar, stays within -4..+span degrees.
    `R` = rows per bar of the rhythm's grid (16, or 12 for the swing banks)."""
    rows = RHYTHMS[rhythm]
    deg = rng.choice((0, 0, 2, 4))
    second_bar = min((x for x in rows if x >= R), default=None)
    out = []
    for i, r in enumerate(rows):
        if i == 0:
            pass
        elif r == second_bar and rng.random() < 0.6:
            deg += rng.choice((-3, 3, 4, -4))                    # the second bar starts with a leap
        else:
            deg += rng.choice((-2, -1, -1, 0, 1, 1, 2))
        deg = max(-4, min(span, deg))
        out.append((r, deg))
    return out


def _note_indices(motif: list[tuple[int, int | None]]) -> list[int]:
    """Indices of the sounding items (a phrase-mode motif also carries rests as (row, None))."""
    return [i for i, (_, d) in enumerate(motif) if d is not None]


def vary_last(motif: list[tuple[int, int]], rng: random.Random) -> list[tuple[int, int]]:
    out = list(motif)
    i = _note_indices(out)[-1]
    r, d = out[i]
    out[i] = (r, d + rng.choice((-2, -1, 1, 2)))
    return out


def cadence(motif: list[tuple[int, int]], mel: Melody, centre: int) -> list[tuple[int, int]]:
    """End on the tonic by step (2 -> 1 or 7 -> 1): the phrase that closes a section."""
    out = list(motif)
    idx = _note_indices(out)
    r, d = out[idx[-1]]
    tonic = mel.tonic_degree_near(centre, d)
    out[idx[-1]] = (r, tonic)
    if len(idx) >= 2:
        r2, _ = out[idx[-2]]
        out[idx[-2]] = (r2, tonic + (1 if (len(out) % 2) else -1))
    return out


def transpose(motif: list[tuple[int, int]], k: int) -> list[tuple[int, int]]:
    return [(r, None if d is None else d + k) for r, d in motif]


def fragment(motif: list[tuple[int, int]], R: int = 16) -> list[tuple[int, int]]:
    """The first bar only (what a pre-chorus repeats and sequences)."""
    return [(r, d) for r, d in motif if 0 <= r < R] or motif[:3]


# ------------------------------------------------------------------- phrase-level composition (--phrases 1|2)
# A beat is four rows; a two-bar rhythm is eight beat cells. 'x' = onset, '.' = hold, '-' = key-off: a rest is a
# first-class cell of the rhythm (the reference corpora rest on about a quarter of their lead rows, anywhere in the
# phrase, not only at its end). The value is the cell's onset count.
BEAT_CELLS = {"x...": 1, "x.x.": 2, "x.xx": 3, "xx.x": 3, "x..x": 2, "x-x.": 2, "x.-.": 1, "x.x-": 2, "x-..": 1,
              "....": 0, "-...": 0, ".x..": 1, "..x.": 1, ".x.x": 2, "xxx.": 3}
# onsets per beat each section aims for: the density arc of the form is written in, not thinned afterwards
PHRASE_DENSITY = {"intro": 0.8, "verse": 1.0, "prechorus": 1.3, "chorus": 1.5, "bridge": 0.6, "B": 0.6, "outro": 1.2,
                  "S1": 1.3, "S2": 1.0, "S3": 1.6, "A": 1.1, "solo": 1.8, "head": 1.2}
# the answer's articulation on the lead channel: narrower duty, shorter decay (a second identity per phrase, the
# cartridges' habit, instead of a volume accent per note)
PHRASE_LEAD2 = {"pop": "inst lead2 pulse duty=25 env=C3 vib=2:4", "chip": "inst lead2 pulse duty=25 env=B2 vib=2:4",
                "rock": "inst lead2 pulse duty=25 env=D3 vib=3:3", "blues": "inst lead2 pulse duty=25 env=C3 vib=3:3",
                "fusion": "inst lead2 pulse duty=25 env=C3 vib=2:3",
                "ska": "inst lead2 pulse duty=12 env=C3 vib=1:4"}   # a thin horn-like answer voice


def _cell_state(cell: str) -> str:
    """What the beat leaves sounding: 'x' a note, '-' silence."""
    return [ch for ch in cell if ch != "."][-1] if cell.strip(".") else "."


def make_cells(rng: random.Random, density: float, rest_bias: float = 1.0, breath: float = 0.5) -> list[str]:
    """Eight beat cells for two bars: onsets per beat near `density`, rest cells weighted by `rest_bias`, the first
    cell starts on the beat, nothing is held or released straight after a rest, and the last beat is a breath
    with probability `breath`."""
    cells: list[str] = []
    for i in range(8):
        opts, weights = [], []
        for cell, c in BEAT_CELLS.items():
            if i == 0 and not cell.startswith("x"):
                continue
            if cells and _cell_state(cells[-1]) == "-" and cell[0] in ".-":
                continue
            if cell == "...." and (not cells or cells[-1] == "...."):
                continue
            w = math.exp(-((c - density) / 0.8) ** 2)
            if "-" in cell:
                w *= rest_bias
            if cell == "....":
                w *= 0.5
            opts.append(cell)
            weights.append(w)
        cells.append(rng.choices(opts, weights=weights)[0])
    if rng.random() < breath:
        cells[7] = rng.choice(("x-..", "-...", "x.-."))
        if _cell_state(cells[6]) == "-" and cells[7].startswith("-"):
            cells[7] = "x-.."
    return cells


def expand_cells(cells: list[str]) -> list[tuple[int, str]]:
    return [(i * 4 + j, ch) for i, cell in enumerate(cells) for j, ch in enumerate(cell) if ch in "x-"]


def motif_from_cells(rng: random.Random, cells: list[str], span: int, deltas: list[int] | None = None,
                     start: int | None = None) -> list[tuple[int, int | None]]:
    """Degrees on the rhythm's onsets, (row, None) on its key-offs. Free: steps with a leap where bar 2 starts
    (as make_motif); with `deltas` the contour is given (the answer inverts the statement's, the departure
    reverses it), so the bank shares one contour family."""
    deg = rng.choice((0, 0, 2, 4)) if start is None else max(-4, min(span, start))
    events = expand_cells(cells)
    second_bar = min((r for r, ch in events if r >= 16 and ch == "x"), default=None)
    out: list[tuple[int, int | None]] = []
    k = 0
    first = True
    for row, ch in events:
        if ch == "-":
            out.append((row, None))
            continue
        if first:
            first = False
        elif deltas:
            step = deltas[k % len(deltas)]
            if not -4 <= deg + step <= span:                          # the contour bounces off the compass
                step = -step
            deg += step
            k += 1
        elif row == second_bar and rng.random() < 0.6:
            deg += rng.choice((-3, 3, 4, -4))
        else:
            deg += rng.choice((-2, -1, -1, 0, 1, 1, 2))
        deg = max(-4, min(span, deg))
        out.append((row, deg))
    return out


def motif_notes(motif: list[tuple[int, int | None]]) -> list[tuple[int, int]]:
    return [(r, d) for r, d in motif if d is not None]


def motif_deltas(motif: list[tuple[int, int | None]]) -> list[int]:
    n = motif_notes(motif)
    return [b[1] - a[1] for a, b in zip(n, n[1:])] or [1, -1]


def share_cells(rng: random.Random, base: list[str], other: list[str], keep: int = 4) -> list[str]:
    """The answer keeps `keep` of the statement's eight beat cells (the same rhythmic family) and takes the rest
    from its own rhythm; then the joins are repaired (start on the beat, nothing held or released after a rest)."""
    idx = set(rng.sample(range(8), keep))
    cells = [base[i] if i in idx else other[i] for i in range(8)]
    if not cells[0].startswith("x"):
        cells[0] = base[0] if base[0].startswith("x") else "x..."
    for i in range(1, 8):
        if _cell_state(cells[i - 1]) == "-" and cells[i][0] in ".-":
            cells[i] = "x" + cells[i][1:]
    return cells


def make_bank(rng: random.Random, density: float, span: int, rest_bias: float = 1.0, low_start: bool = False) -> dict:
    """Two or three ideas per section, made together: the statement s; the answer a (keeps half of s's beat cells,
    inverts its contour, starts where s ended, sparser, rests more); the departure d (a new, denser rhythm, s's
    contour in retrograde, starts a third away). `low_start`: the statement starts at or below the centre (the
    lifted sections, so the lift stays a fifth and the register does not drift beyond the references)."""
    s_cells = make_cells(rng, density, rest_bias)
    if rng.random() < 0.35:                                     # a statement that leaves room: held note, then a beat of rest
        s_cells[6], s_cells[7] = "x...", "-..."
    s = motif_from_cells(rng, s_cells, span, start=rng.choice((-2, 0, 0, 1)) if low_start else None)
    deltas = motif_deltas(s)
    last = motif_notes(s)[-1][1]
    a_cells = share_cells(rng, s_cells, make_cells(rng, max(0.3, density - 0.6), rest_bias * 1.3))
    if rng.random() < 0.7:                                      # the answer is usually a call: it ends by the middle of bar 2
        a_cells[6], a_cells[7] = rng.choice(("x-..", "x...", "x.-.")), "-..."
    a = motif_from_cells(rng, a_cells, span, deltas=[-x for x in deltas], start=last)
    d_cells = make_cells(rng, density + 0.5, rest_bias * 0.8, breath=0.3)
    d = motif_from_cells(rng, d_cells, span, deltas=deltas[::-1], start=last + rng.choice((2, -2, 1)))
    return {"s": s, "a": a, "d": d, "cells": {"s": s_cells, "a": a_cells, "d": d_cells}}


def thin(motif: list[tuple[int, int | None]], rng: random.Random) -> list[tuple[int, int | None]]:
    """One inner note becomes a rest: the ebb inside a restatement."""
    idx = _note_indices(motif)
    if len(idx) < 4:
        return list(motif)
    i = rng.choice(idx[1:-1])
    out = list(motif)
    out[i] = (out[i][0], None)
    return out


def second_bar_only(motif: list[tuple[int, int | None]]) -> list[tuple[int, int | None]]:
    """The rock verse's answer to the riff: the lead speaks in bar 2 only."""
    return [(0, None)] + [(r, d) for r, d in motif if r >= 16]


def quote_then_new(prev: list[tuple[int, int | None]], new: list[tuple[int, int | None]], k: int) -> list[tuple[int, int | None]]:
    """Period writing across sections: bar 1 quotes the previous section's answer, moved so that it starts a step
    (`k` degrees) from where this section's own statement would have started; bar 2 is new."""
    prev_notes, new_notes = motif_notes(prev), motif_notes(new)
    if not prev_notes or not new_notes:
        return list(new)
    shift = new_notes[0][1] + k - prev_notes[0][1]
    head = [(r, None if d is None else max(-4, min(7, d + shift))) for r, d in prev if r < 16]
    tail = [(r, d) for r, d in new if r >= 16]
    return (head or [(r, d) for r, d in new if r < 16]) + tail


# ------------------------------------------------------------------- hooks and melodies (--hook 1|2|3)
# The melodic-math school of pop writing designs the hook first and derives the rest of the song from it (few
# melodic parts, recycled; the verse previews the chorus; the highest note saved for late in the section; the
# chorus is the focal point and arrives early). The earworm research (3,000 listeners' most frequent earworms
# against matched non-earworms) found a common global contour, a faster tempo and one unusual interval at a
# predictable place. The reference corpora, measured (docs/DESIGN_NOTES.md): a hook is 2-4 bars, heard 2-6
# times (2-5 a minute), 7-13 semitones wide, half steps half leaps, at most one leap of a sixth, its top note in
# the middle of the cell. Level 0 leaves every other draw untouched (byte-identical scores).

HOOK_CONTOURS = (("rising", 30), ("falling", 26), ("arch", 24), ("bowl", 20))     # the corpora's hook contour classes
# two-bar hook rhythms as eight beat cells (x onset, . hold, - key-off): one anticipation (an onset on the 16th
# before a beat whose downbeat is then held), the landing on beat 3 of bar 2, a breath before the next downbeat
HOOK_RHYTHMS = (
    ("x.x.", "x...", "x.x.", "x..x", "....", "x.x.", "x...", "..-."),
    ("x..x", "....", "x.x.", "x...", "x...", "x.x.", "x...", "..-."),
    ("x...", "x.x.", "x...", "...x", "....", "x...", "x...", "..-."),
    ("x.x.", "x.xx", "x...", "x..x", "....", "x...", "x...", "..-."),
    ("x..x", "....", "x...", "x.x.", "x...", "x...", "x...", "..-."),
    ("x..x", "..x.", "x..x", "..x.", "x...", "....", "x...", "..-."),
)
HOOK_RANGE = (7, 10)          # semitones: inside the corpora's interquartile band (7-13) and a singable fifth to a seventh
# pooled corpus bands (p10, p25, p75, p90) of the hook metrics below, from the two reference corpora (58 hooks)
HOOK_BANDS = {
    "hook_bars": (1, 2, 4, 4), "hook_repeats": (2, 2, 5.75, 8), "hook_per_minute": (1.2, 1.97, 5.14, 8.16),
    "hook_first_s": (0, 1.65, 15.5, 31.7), "range": (5, 7, 13, 19), "step_ratio": (0.0, 0.2, 0.75, 0.87),
    "leap_ratio": (0.09, 0.19, 0.57, 0.91), "max_leap": (3, 5, 10.75, 14.3), "big_leaps": (0, 0, 1, 3.3),
    "climax_pos": (0.02, 0.14, 0.78, 1.0), "end_rest": (0, 0, 0.5, 0.58), "notes_per_bar": (2.8, 3.5, 8, 9),
    "distinct_pitches": (3.7, 4, 8, 9.3),
}
HOOK_BIG_LEAP, HOOK_TRITONE = 8, 6


def _hook_interp(points: list[tuple[int, int]], n: int) -> list[int]:
    """Degrees for n onsets from a spine of (onset index, degree) points, linear between them."""
    out = []
    for i in range(n):
        for (i0, d0), (i1, d1) in zip(points, points[1:]):
            if i0 <= i <= i1:
                out.append(round(d0 + (d1 - d0) * (i - i0) / max(1, i1 - i0)))
                break
        else:
            out.append(points[-1][1])
    return out


def _nearest_degree_in(mel: Melody, centre: int, deg: int, pcs: list[int], reach: int = 2) -> int:
    cands = [d for d in range(deg - reach, deg + reach + 1) if mel.note(centre, d) % 12 in pcs]
    return min(cands, key=lambda d: (abs(d - deg), -d)) if cands else deg


def design_hook(hrng: random.Random, mel: Melody, centre: int, key: int, mode: str, level: int) -> dict:
    """The two-bar hook, designed first. A contour class from the corpora's distribution, a compass of HOOK_RANGE
    semitones, a rhythm with one anticipation that lands on beat 3 of bar 2 and breathes before the next downbeat,
    mostly steps with one leap at the class's fixed place (arch: the start; rising / bowl: before the peak;
    falling: the middle), the first and last notes on the key's tonic triad so the cell sits on every chord of the
    chorus without being re-snapped. Level 3 makes the leap an unusual interval (a sixth, now and then a tritone)
    resolved by step on the next note: the earworm surprise at a predictable place."""
    contour = hrng.choices([c for c, _ in HOOK_CONTOURS], weights=[w for _, w in HOOK_CONTOURS])[0]
    cells = list(hrng.choice(HOOK_RHYTHMS))
    events = expand_cells(cells)
    onsets = [r for r, ch in events if ch == "x"]
    n = len(onsets)
    lo = hrng.choice((-1, 0, 0))
    hi = lo + 1
    while mel.note(centre, hi) - mel.note(centre, lo) < HOOK_RANGE[0]:
        hi += 1
    if mel.note(centre, hi) - mel.note(centre, lo) > HOOK_RANGE[1] and hi - lo > 2:
        hi -= 1
    j = {"arch": 1, "rising": round(0.6 * (n - 1)), "falling": round(0.5 * (n - 1)), "bowl": round(0.6 * (n - 1))}[contour]
    j = max(1, min(n - 2, j))
    peak = max(2, round(0.4 * (n - 1)))
    spine = {
        "arch": [(0, lo), (1, lo + max(2, hi - lo - 2)), (peak, hi), (n - 1, lo + 1)],
        "rising": [(0, lo), (j - 1, lo + 1), (j, hi - 1), (n - 1, hi)],
        "falling": [(0, hi - 1), (1, hi), (j - 1, hi - 1), (j, lo), (n - 1, lo + 1)],
        "bowl": [(0, lo + 2), (j - 1, lo), (j, hi), (n - 1, lo + 2)],
    }[contour]
    spine = sorted({i: d for i, d in spine}.items())
    degs = _hook_interp(spine, n)
    # the leap is a fourth or a fifth (5 or 7 semitones), never a tritone, at levels 1-2
    leap_j = 1 if contour == "arch" else j
    size = abs(mel.note(centre, degs[leap_j]) - mel.note(centre, degs[leap_j - 1]))
    if size == HOOK_TRITONE or size > 7:
        sign = 1 if degs[leap_j] >= degs[leap_j - 1] else -1
        for d in (degs[leap_j] - sign, degs[leap_j] + sign, degs[leap_j] - 2 * sign):
            if abs(mel.note(centre, d) - mel.note(centre, degs[leap_j - 1])) in (5, 7):
                degs[leap_j] = d
                break
    tonic = [(key + x) % 12 for x in (0, 3 if mode == "minor" else 4, 7)]
    degs[0] = _nearest_degree_in(mel, centre, degs[0], tonic, 1)
    degs[-1] = _nearest_degree_in(mel, centre, degs[-1], tonic, 2)
    while max(mel.note(centre, d) for d in degs) - min(mel.note(centre, d) for d in degs) < HOOK_RANGE[0]:
        top = max(degs)                                        # the anchors narrowed the cell: the peak goes up a step
        degs = [d + 1 if d == top else d for d in degs]
    surprise = None
    if level >= 3 and j + 1 < n - 1:
        prev = mel.note(centre, degs[j - 1])
        sign = 1 if degs[j] >= degs[j - 1] else -1
        want = [HOOK_TRITONE] if hrng.random() < 0.3 else [HOOK_BIG_LEAP, HOOK_BIG_LEAP + 1]
        for size in want + [HOOK_BIG_LEAP, HOOK_BIG_LEAP + 1]:
            cands = [d for d in range(degs[j - 1] - 8, degs[j - 1] + 9) if (mel.note(centre, d) - prev) * sign == size]
            if cands:
                degs[j] = cands[0]
                degs[j + 1] = degs[j] - sign                      # resolved by step, back the way it came
                surprise = ("a tritone" if size == HOOK_TRITONE else "a sixth") + f" at note {j + 1}, resolved by step"
                break
    motif: list[tuple[int, int | None]] = []
    k = 0
    for row, ch in events:
        if ch == "-":
            motif.append((row, None))
        else:
            motif.append((row, degs[k]))
            k += 1
    notes = [mel.note(centre, d) for d in degs]
    return {"motif": motif, "cells": cells, "contour": contour, "leap_at": j + 1, "range": max(notes) - min(notes),
            "onsets": n, "surprise": surprise, "compass": (lo, hi)}


def mirror_motif(motif: list[tuple[int, int | None]]) -> list[tuple[int, int | None]]:
    """The answer: the same rhythm and note count, the contour inverted around the first note (melodic math's
    paired lines: a line, then its mirror)."""
    idx = _note_indices(motif)
    if not idx:
        return list(motif)
    pivot = motif[idx[0]][1]
    return [(r, None if d is None else max(-5, min(9, 2 * pivot - d))) for r, d in motif]


def third_time(motif: list[tuple[int, int | None]], level: int) -> list[tuple[int, int | None]]:
    """The third statement changes: level 1 lifts the last three notes a third (the ending goes up); level 2+
    lifts the climax note itself a third, so the song's top note is heard there and only there."""
    idx = _note_indices(motif)
    out = list(motif)
    if not idx:
        return out
    if level >= 2:
        top = max(motif[i][1] for i in idx)
        targets = [i for i in idx if motif[i][1] == top]
    else:
        targets = idx[-3:]
    for i in targets:
        out[i] = (out[i][0], out[i][1] + 2)
    return out


def delay_last(motif: list[tuple[int, int | None]], rows: int = 2) -> list[tuple[int, int | None]]:
    """The hook's final note arrives an 8th late (the last time): the listener leans in."""
    idx = _note_indices(motif)
    out = list(motif)
    if idx:
        r, d = out[idx[-1]]
        if r + rows <= 29:
            out[idx[-1]] = (r + rows, d)
    return out


def derive_verse(motif: list[tuple[int, int | None]]) -> list[tuple[int, int | None]]:
    """The verse previews the hook: its rhythm's skeleton (onsets on the beats and the anticipation, the
    decorations dropped) on half the compass, rendered a register lower by the section plan."""
    idx = _note_indices(motif)
    if len(idx) < 3:
        return list(motif)
    keep = {idx[0], idx[-1]} | {i for i in idx if motif[i][0] % 4 in (0, 3)}
    out = []
    for i, (r, d) in enumerate(motif):
        if d is None:
            out.append((r, None))
        elif i in keep:
            out.append((r, round(d / 2)))
    return out


def tail_twice(motif: list[tuple[int, int | None]]) -> list[tuple[int, int | None]]:
    """The post-chorus / outro figure: the hook's second bar, twice."""
    tail = [(r, d) for r, d in motif if r >= 16]
    if not motif_notes(tail):
        return list(motif)
    return [(r - 16, d) for r, d in tail] + tail


# -- the hook metrics (the same definitions as the research script hook_metrics.py; reported in the generate JSON)


def _lead_notes(sc: Score) -> list[tuple[int, int, int]]:
    """(row from the start, midi, duration in rows) of the lead lane."""
    notes: list[tuple[int, int, int]] = []
    open_note = None
    for b in range(len(sc.bars)):
        for r, cell in enumerate(sc.bars[b][0]):
            row = b * 16 + r
            m = LEAD_CELL_RE.match(cell) if cell not in (".", "-") else None
            if m and m.group(1):
                if open_note is not None:
                    notes.append((open_note[0], open_note[1], max(1, row - open_note[0])))
                open_note = (row, note_to_midi(m.group(1)))
            elif cell == "-" and open_note is not None:
                notes.append((open_note[0], open_note[1], max(1, row - open_note[0])))
                open_note = None
    if open_note is not None:
        notes.append((open_note[0], open_note[1], max(1, len(sc.bars) * 16 - open_note[0])))
    return notes


def hook_contour_class(pitches: list[int], tol: float = 0.5) -> str:
    """Nine contour classes from (first, mean, last): arch, bowl, rising, falling, flat and the half-flat ones."""
    if len(pitches) < 2:
        return "flat"
    first, last, mean = pitches[0], pitches[-1], sum(pitches) / len(pitches)
    a = "U" if mean - first > tol else "D" if first - mean > tol else "F"
    b = "U" if last - mean > tol else "D" if mean - last > tol else "F"
    return {"UD": "arch", "DU": "bowl", "UU": "rising", "DD": "falling", "FF": "flat", "UF": "rise-flat",
            "FU": "flat-rise", "DF": "fall-flat", "FD": "flat-fall"}[a + b]


def hook_find(notes: list[tuple[int, int, int]], nbars: int) -> dict:
    """The most repeated 1-, 2- or 4-bar cell (exact rhythm and intervals, transposition-invariant): score = bars
    of re-hearing, (occurrences - 1) * bars, ties to the cell heard more often; 3+ notes, 3+ pitches, 2+ occurrences."""
    best = None
    for L in (4, 2, 1):
        sigs: dict[tuple, list[int]] = collections.defaultdict(list)
        for b in range(0, nbars - L + 1):
            lo, hi = b * 16, (b + L) * 16
            cell = [n for n in notes if lo <= n[0] < hi]
            if len(cell) >= 3 and len({p for r, p, d in cell}) >= 3:
                p0 = cell[0][1]
                sigs[tuple((r - lo, p - p0) for r, p, d in cell)].append(b)
        for sig, bars in sigs.items():
            occ: list[int] = []
            for b in bars:
                if not occ or b >= occ[-1] + L:
                    occ.append(b)
            if len(occ) < 2:
                continue
            score = ((len(occ) - 1) * L, len(occ), len(sig))
            if best is None or score > best[0]:
                best = (score, L, occ)
    if best is None:
        return {"hook_bars": 0, "hook_repeats": 0, "hook_first_bar": None}
    _, L, occ = best
    return {"hook_bars": L, "hook_repeats": len(occ), "hook_first_bar": occ[0] + 1, "occurrences": [b + 1 for b in occ]}


def hook_cell_metrics(notes: list[tuple[int, int, int]], row0: int, rows: int) -> dict:
    cell = [n for n in notes if row0 <= n[0] < row0 + rows]
    names = [midi_to_note(p) for r, p, d in cell]
    if len(cell) < 2:
        return {"range": 0, "contour": "flat", "names": names}
    ps = [n[1] for n in cell]
    ivs = [b - a for a, b in zip(ps, ps[1:])]
    steps = sum(1 for x in ivs if 1 <= abs(x) <= 2)
    leaps = sum(1 for x in ivs if abs(x) >= 3)
    big = [i for i, x in enumerate(ivs) if abs(x) >= HOOK_BIG_LEAP or abs(x) == HOOK_TRITONE]
    hi = max(ps)
    half = row0 + rows // 2
    last_beat = row0 + rows - 4
    sounding = sum(max(0, min(r + d, row0 + rows) - max(r, last_beat)) for r, p, d in cell)
    return {"range": hi - min(ps), "contour": hook_contour_class(ps),
            "halves": [hook_contour_class([n[1] for n in cell if n[0] < half]), hook_contour_class([n[1] for n in cell if n[0] >= half])],
            "step_ratio": round(steps / (steps + leaps), 3) if steps + leaps else None,
            "leap_ratio": round(leaps / len(ivs), 3), "repeat_ratio": round(sum(1 for x in ivs if x == 0) / len(ivs), 3),
            "max_leap": max(abs(x) for x in ivs), "big_leaps": len(big),
            "surprise_pos": round((big[0] + 1) / len(ps), 3) if big else None,
            "climax_pos": round(ps.index(hi) / (len(ps) - 1), 3), "end_rest": round(1 - sounding / 4, 3),
            "notes_per_bar": round(len(cell) / (rows / 16), 2), "distinct_pitches": len(set(ps)), "names": names}


def hook_metrics(sc: Score) -> dict:
    """The hook metrics of a score's lead lane with each one's verdict against the corpus bands: 'in' the
    interquartile band, 'near' (inside p10..p90) or 'out'."""
    notes = _lead_notes(sc)
    nbars = len(sc.bars)
    out: dict = {"notes": len(notes)}
    if not notes or not nbars:
        return out
    fpr = bpm_to_fpr(sc.bpm)
    seconds = nbars * 16 * fpr / GB_FPS
    found = hook_find(notes, nbars)
    out.update(found)
    if found["hook_bars"]:
        row0 = (found["hook_first_bar"] - 1) * 16
        out.update(hook_cell_metrics(notes, row0, found["hook_bars"] * 16))
        out["hook_per_minute"] = round(found["hook_repeats"] / (seconds / 60), 2)
        out["hook_first_s"] = round(row0 * fpr / GB_FPS, 1)
    ps = [n[1] for n in notes]
    top = max(ps)
    out["lead_range"] = top - min(ps)
    out["song_climax_bar"] = notes[ps.index(top)][0] // 16 + 1
    out["song_climax_pos"] = round(notes[ps.index(top)][0] / (nbars * 16), 3)
    verdict = {}
    for k, (p10, p25, p75, p90) in HOOK_BANDS.items():
        v = out.get(k)
        if v is not None:
            verdict[k] = "in" if p25 <= v <= p75 else "near" if p10 <= v <= p90 else "out"
    out["bands"] = verdict
    out["in_band"] = sum(1 for v in verdict.values() if v == "in")
    out["near_band"] = sum(1 for v in verdict.values() if v == "near")
    out["out_of_band"] = sum(1 for v in verdict.values() if v == "out")
    return out


class FormComposer:
    """Writes the four lanes of a planned song, section by section, in a style flavour (pop, chip, rock, blues)."""

    def __init__(self, rng: random.Random, brng: random.Random, key: int, bpm: float, name: str, flavour: str,
                 form: str, chorus_syms: list[str], bend: str, prog_name: str, texture: str = "plain", lift: str = "fifth",
                 phrases: int = 0, prng: random.Random | None = None, hook: int = 0, hrng: random.Random | None = None,
                 groove: str = "straight", syncopation: int | None = None) -> None:
        self.rng, self.brng, self.key, self.bpm, self.flavour, self.form, self.bend = rng, brng, key, bpm, flavour, form, bend
        self.chorus_syms, self.prog_name, self.texture = chorus_syms, prog_name, texture
        self.phrases = phrases if form != "blues12" else 0            # the blues keeps its aab head and solo
        self.hook_level = hook if form != "blues12" else 0            # --hook: the hook engine (set early: bank() reads it)
        self.prng = prng or random.Random(key * 48611 + 3)             # the phrase grammar's own stream
        self.banks: dict[str, dict] = {}
        self.pad_bars: set[int] = set()
        self.responses = 0
        self.hooks_written = 0
        self.mode = _mode_scale(chorus_syms)
        self.swing = form == "blues12"
        self.groove_name = groove
        self.groove = GROOVES[groove]
        self.R = self.groove["rows"]                              # rows per bar: 16, or 12 on the swing grid
        self.beat = self.R // 4
        self.sync = self.groove["sync"] if syncopation is None else syncopation
        title = {"pop": "Pop song", "chip": "Chip pop song", "rock": "Rock song", "blues": "Blues", "ska": "Ska"}[flavour] + f" ({form}" + (", fusion texture" if texture == "fusion" else "") + (f", {groove} groove" if groove != "straight" else "") + ")"
        self.sc = Score(name, title, bpm, rows=self.R, arp=3 if flavour != "chip" else 2)
        self.sc.insts = {
            "fusion": ["inst lead pulse duty=50 env=C2 vib=2:3", "inst hook pulse duty=25 env=B2 vib=3:2",
                       "inst arp pulse duty=25 env=90", "inst pad pulse duty=12 env=A0",
                       "inst bass wave vol=13 shape=saw", "inst bassr wave vol=11 shape=tri"],
        }[texture] if texture == "fusion" else {
            "pop": ["inst lead pulse duty=50 env=C2 vib=2:4", "inst hook pulse duty=25 env=D2 vib=2:3",
                    "inst arp pulse duty=25 env=90", "inst pad pulse duty=12 env=60",
                    "inst bass wave vol=12 shape=saw", "inst bassr wave vol=11 shape=tri"],
            "chip": ["inst lead pulse duty=50 env=B1 vib=2:4", "inst hook pulse duty=25 env=C1 vib=2:3",
                     "inst arp pulse duty=25 env=80", "inst pad pulse duty=12 env=50",
                     "inst bass wave vol=12 shape=square", "inst bassr wave vol=11 shape=square"],
            "rock": ["inst lead pulse duty=50 env=D2 vib=3:3", "inst hook pulse duty=75 env=E2 vib=2:3",
                     "inst arp pulse duty=50 env=A0", "inst pad pulse duty=25 env=80",
                     "inst bass wave vol=13 shape=saw", "inst bassr wave vol=12 shape=tri"],
            "blues": ["inst lead pulse duty=50 env=C2 vib=3:3", "inst hook pulse duty=25 env=D2 vib=3:2",
                      "inst arp pulse duty=25 env=A1", "inst pad pulse duty=25 env=70",
                      "inst bass wave vol=13 shape=saw", "inst bassr wave vol=12 shape=tri"],
            "ska": ["inst lead pulse duty=25 env=C2 vib=1:4", "inst hook pulse duty=25 env=D7 vib=1:3",   # depth-1 vibrato and a plain duty: the ska lead sits high, where period-unit vibrato is deep and a 12/25 duty flicker reads flat (listened)
                    "inst arp pulse duty=25 env=90", "inst pad pulse duty=12 env=60",
                    "inst bass wave vol=12 shape=rsaw", "inst bassr wave vol=11 shape=tri"],
        }[flavour]
        if groove == "tropical" and flavour == "pop":             # the hit template: the chorus hook is a pluck
            self.sc.insts[1] = "inst hook pulse duty=25 env=E3 penv=12,1"
        if self.groove.get("stab_inst"):
            self.sc.insts.append(self.groove["stab_inst"])
        self.sc.insts += GROOVE_INSTS.get(groove, []) if not (groove == "tropical" and flavour == "pop") else []
        lead_scale = {"pop": self.mode, "chip": "pent" if self.mode == "major" else "mpent",
                      "rock": "mpent" if self.mode == "minor" else ("mixolydian" if flavour == "rock" and self.mode == "mixolydian" else "pent"),
                      "blues": "mpent", "ska": self.mode}[flavour]
        if flavour == "rock" and lead_scale == "pent":
            lead_scale = "mpent" if rng.random() < 0.6 else "pent"       # most rock leads are minor-pentatonic over major chords
        self.mel = Melody(key, lead_scale)
        base = 69 if flavour == "blues" else 64                   # the blues head sits above the boogie bass
        self.verse_centre = self.mel.index_near(base + (key if key <= 6 else key - 12))   # around E4, follows the key
        # the chorus / C-section lift: a fifth by default (the reference corpora lift their second section by
        # 1-8 semitones; an octave drifted the lead beyond every corpus song), --lift sixth|octave for more
        self.chorus_centre = self.verse_centre + max(1, round(self.mel.octave * LIFTS.get(lift, 7) / 12))
        self.bridge_centre = self.verse_centre - 3
        if groove == "straight":
            self.hook = make_motif(rng, rng.choice(("sync", "straight", "pickup")))
            self.verse_motif = make_motif(rng, rng.choice(("straight", "long", "sync")), span=5)
            self.bridge_motif = make_motif(rng, "long", span=4)
            self.answer = make_motif(rng, "answer", span=4)
            self.head = make_motif(rng, "call", span=5)
            self.stage_motifs = [make_motif(rng, rng.choice(("straight", "sync", "quick")), span=6) for _ in range(3)]
        else:                                                     # the groove's own rhythm banks, on its grid
            R = self.R
            g = self.groove
            self.hook = make_motif(rng, rng.choice(g["hooks"]), R=R)
            self.verse_motif = make_motif(rng, rng.choice(g["verse_hooks"]), span=5, R=R)
            self.bridge_motif = make_motif(rng, "long" if R == 16 else "long12", span=4, R=R)
            self.answer = make_motif(rng, "answer" if R == 16 else "answer12", span=4, R=R)
            self.head = make_motif(rng, "call" if R == 16 else "call12", span=5, R=R)
            self.stage_motifs = [make_motif(rng, rng.choice(g["hooks"]), span=6, R=R) for _ in range(3)]
        # the syncopation level: below the groove's native level the hook rhythms are straightened to the 8th
        # grid; at any level the generic pushes are added (nothing at level 0)
        native = self.groove["sync"]
        srng = random.Random(key * 311 + self.sync)

        def shape(m, lvl):
            grid = level_grid(lvl, self.R) if lvl < native else None
            if grid:
                rows = _level_rows(tuple(r for r, _ in m), grid, self.R)
                degs = [d for _, d in m]
                m = [(r, degs[min(i, len(degs) - 1)]) for i, r in enumerate(rows)]
            return syncopate_motif(m, max(0, lvl - native), srng, self.R)
        self.hook = shape(self.hook, self.sync)
        self.stage_motifs = [shape(m, self.sync) for m in self.stage_motifs]
        self.verse_motif = shape(self.verse_motif, max(0, self.sync - 1))
        self.riff = rng.choice(["chug", "pent", "descend", "gallop"]) if flavour == "rock" else "boogie"
        self.prev_top: int | None = None
        self.meta: list[str] = []
        if self.phrases:
            self.sc.insts.append(PHRASE_LEAD2["fusion" if texture == "fusion" else flavour])
            self.hook = self.bank("hook", "chorus")["s"]               # the hook comes from its bank, rests included
        # --hook: the hook is designed first and the other melodies derive from it (its own stream: level 0
        # leaves every draw above untouched)
        self.hrng = hrng or random.Random(key * 7001 + 11)
        self.design: dict = {}
        self.hook_hearings = 0
        self.peak_fixes = 0
        if self.hook_level:
            design_centre = self.chorus_centre if form == "verse-chorus" else self.verse_centre
            self.design = design_hook(self.hrng, self.mel, design_centre, key, self.mode, self.hook_level)
            self.hook = self.design["motif"]
            derived = derive_verse(self.hook)
            self.verse_motif = self.hook if form == "aaba" else derived
            self.answer = second_bar_only(derived)                    # the rock verse answers the riff with the hook's skeleton
            if form == "aaba":
                self.bridge_motif = derived
            self.stage_motifs = [self.hook, derived, self.hook]       # stage A states the hook, B previews, C lifts it
            if self.phrases:
                self.banks["hook"]["s"] = self.hook
                self.banks["hook"]["cells"]["s"] = self.design["cells"]

    # ---- phrase grammar (--phrases): motif banks per section, pulse-2 answers
    def bank(self, name: str, role: str, span: int = 6) -> dict:
        if role in ("chorus", "S3"):
            span = min(span, 4)                                    # the lifted sections keep a tighter compass
        if name not in self.banks:
            self.banks[name] = make_bank(self.prng, PHRASE_DENSITY.get(role, 1.2), span, rest_bias=1.0 + 0.15 * (self.phrases - 1),
                                         low_start=role in ("chorus", "S3"))
            if self.hook_level and name != "hook":               # the banks derive from the hook (--hook)
                bk = self.banks[name]
                if name in ("S1", "S3", "A"):
                    bk["s"] = self.hook
                elif name in ("verse", "S2"):
                    bk["s"] = derive_verse(self.hook)
                if self.hook_level >= 2 and name != "bridge":    # the answer mirrors the statement, same rhythm and count
                    bk["a"] = mirror_motif(bk["s"])
        return self.banks[name]

    def alt_inst(self, inst: str) -> str:
        """The answer's colour: the second lead identity against whatever the statement used."""
        return "lead2" if inst in ("lead", "hook") and self.phrases else inst

    def put_response(self, bar0: int, motif: list[tuple[int, int | None]], centre: int, syms: list[str]) -> None:
        """Call and response between the channels: when the lead's phrase ends early (its last onset by the middle
        of bar 2) and pulse 2 only pads that bar, pulse 2 answers with three 8ths on chord tones a fifth below the
        lead's last note, on beat 3 of bar 2 (released before the next downbeat) or on beat 3-and when the lead
        ended a beat later."""
        if not self.phrases or (bar0 + 1) not in self.pad_bars:
            return
        notes = motif_notes(motif)
        if not notes:
            return
        last_row = notes[-1][0]
        rests_after = [r for r, d in motif if d is None and r > last_row]
        if last_row <= 24:
            start, count = (8 if last_row <= 21 else 10), 3
        elif last_row <= 27 and rests_after and min(rests_after) <= 28:
            start, count = 12, 2                                   # the lead clears the last beat: a two-note answer
        else:
            return
        pcs = self.chord(syms[min(1, len(syms) - 1)])[2]
        last = self.mel.note(centre, notes[-1][1])
        n0 = self.mel.snap(last - 5, pcs)
        below = [p for p in range(n0 - 1, n0 - 8, -1) if p % 12 in pcs]
        n1 = below[0] if below else n0 - 12
        above = [p for p in range(n0 + 1, n0 + 8) if p % 12 in pcs]
        n2 = n0 if self.prng.random() < 0.5 or not above else above[0]      # back to the first note, or a step above it
        lane = self.sc.bar(bar0 + 1)[1]
        for j, n in enumerate((n0, n1, n2)[:count]):
            n = max(PULSE_RANGE[0], min(PULSE_RANGE[1], n))
            lane[start + 2 * j] = midi_to_note(n) + ("@arp" if j == 0 else "")
        if start + 2 * count < 16:
            lane[start + 2 * count] = "-"
        self.responses += 1

    # ---- harmony helpers
    def chord(self, sym: str) -> tuple[int, str, list[int]]:
        deg, qual = roman_chord(sym)
        qmap = STYLE_QUALITY[self.flavour]
        qual = qmap.get(qual, qual)
        if self.texture == "fusion":                             # colour tones on the chord cycle, the fusion way
            qual = FUSION_COLOUR.get(qual, qual)
        root_pc = (self.key + deg) % 12
        return root_pc, qual, [(root_pc + iv) % 12 for iv in CHORDS[qual]]

    def lead_scale_pcs(self, sym: str) -> list[int]:
        root_pc, qual, _ = self.chord(sym)
        name = "dorian" if qual in ("m7", "m9", "min", "madd9") else "lydian" if qual in ("maj7", "maj9", "add9") else "mixolydian"
        return [(root_pc + x) % 12 for x in SCALES[name]]

    def bass_root(self, root_pc: int) -> int:
        return 36 + root_pc if root_pc <= 9 else 24 + root_pc        # B1..A2

    def q(self, row16: int) -> int:
        """A row written for the 16-row grid, on this song's grid (identity at 16 rows)."""
        return row16 if self.R == 16 else row16 * self.R // 16

    # ---- lanes
    def put_lead(self, bar0: int, motif: list[tuple[int, int]], centre: int, syms: list[str], inst: str,
                 hold_vib: bool = True, bend_ok: bool = False, rest_row: int | None = 31) -> None:
        """Render a two-bar motif from bar0 over the two bars' chords; strong beats snap to chord tones. With
        --hook the hook itself is never re-snapped (it repeats note for note, the harmony moves under it) and
        its bars are protected from the organic layer's pitch moves."""
        chords = [self.chord(syms[min(i, len(syms) - 1)])[2] for i in range(2)]
        snap = not (self.hook_level and motif is self.hook)
        if not snap:
            self.hook_hearings += 1
            self.sc.protected.update((bar0, bar0 + 1))
        R = self.R
        cells = ["."] * (2 * R)
        pickup = None                                            # a row -1 note: the anticipation written into the previous bar
        last_row = -1
        idx = _note_indices(motif)
        first_i, last_i = (idx[0], idx[-1]) if idx else (0, len(motif) - 1)
        for i, (row, deg) in enumerate(motif):
            if row > 2 * R - 1 or row < -1:
                continue
            if deg is None:                                              # a rest written into the rhythm (--phrases)
                cells[row] = "-"
                continue
            n = self.mel.note(centre, deg)
            if snap and (row % R in (0, R // 2) or i == last_i or row < 0):
                n = self.mel.snap(n, chords[max(0, row) // R])
            n = max(PULSE_RANGE[0], min(PULSE_RANGE[1], n))
            cell = midi_to_note(n)
            fusion = self.texture == "fusion"
            if i == first_i:
                cell += f"@{inst}" + ("'2" if fusion else "")           # fusion: a 2-frame mordent opens the phrase
            if i == last_i:
                if bend_ok and self.brng.random() < BEND_RATES.get(self.bend, BEND_RATES["sparse"])[1]:
                    cell += f"/{self.brng.choice((-1, -2))},{self.brng.choice((4, 5))}"   # a rare bend that lands on the note
                elif hold_vib and fusion and self.rng.random() < 0.4:
                    cell += "^2"                                          # fusion: a trill on the arrival note
                elif hold_vib:
                    cell += "~1,3" if self.flavour == "ska" else "~"   # ska: depth 1 on the high arrival notes (listened)
            if row < 0:
                pickup = cell
                continue
            cells[row] = cell
            last_row = row
        if rest_row is not None and last_row < self.q(rest_row):
            cells[self.q(rest_row)] = "-"
        for r, c in enumerate(cells):
            self.sc.put(bar0 + r // R, 0, r % R, c)
        if pickup is not None and bar0 > 0:
            prev = self.sc.bar(bar0 - 1)[0]
            if prev[R - 1] in (".", "-"):
                prev[R - 1] = pickup

    def put_chord(self, bar: int, sym: str, style: str, centre: int = 72) -> None:
        """Pulse 2 per bar: 'pad' (struck, released at the half bar), 'full' (held chord cycle), 'stab' (beats 2
        and 4), 'riff' (doubles the bass riff an octave up), 'rest'."""
        root_pc, qual, _ = self.chord(sym)
        if qual == "5":                                          # a power chord is root-fifth-octave, never inverted
            low, ivs = 60 + root_pc - (12 if root_pc > 6 else 0), (0, 7, 12)
        else:
            low, ivs = voice(root_pc, CHORDS[qual], centre, self.prev_top)
        self.prev_top = low + ivs[-1]
        cname = self.sc.chord_name(ivs)
        if self.groove_name != "straight" and style in ("pad", "full", "stab", "riff") and self.groove.get("stab"):
            self.put_groove_stab(bar, low, cname, "full" if style == "riff" else style)
        elif style == "pad":
            self.sc.put(bar, 1, 0, f"{midi_to_note(low)}:{cname}@pad")
            self.sc.put(bar, 1, self.q(12), "-")
            self.pad_bars.add(bar)
        elif style == "full":
            self.sc.put(bar, 1, 0, f"{midi_to_note(low)}:{cname}@arp")
            if bar % 2 == 1 and low + 12 + ivs[-1] <= 100:
                self.sc.put(bar, 1, self.q(8), f"{midi_to_note(low + 12)}:{cname}")
                self.sc.put(bar, 1, self.q(14), f"{midi_to_note(low)}:{cname}")
        elif style == "stab":
            for r in (self.q(4), self.q(12)):
                self.sc.put(bar, 1, r, f"{midi_to_note(low)}:{cname}@arp")
        elif style == "riff":
            rows, semis = RIFFS[self.riff]
            root = self.bass_root(root_pc) + 12
            for r, s in zip(rows, semis):
                n = max(PULSE_RANGE[0], min(PULSE_RANGE[1], root + s))
                self.sc.put(bar, 1, r, f"{midi_to_note(n)}@pad!5" if r == 0 else f"{midi_to_note(n)}!5")
        elif style == "echo":                                    # fusion: pulse 2 replays the lead, the chord drops
            self.sc.put(bar, 1, 0, f"echo:{5},{3}")
        elif style == "echo-off":
            self.sc.put(bar, 1, self.R - 1, "echo:off")

    def put_groove_stab(self, bar: int, low: int, cname: str, style: str) -> None:
        """Pulse 2 on a groove: the chord struck on the groove's stab rows (the ska skank on the off-8ths, the
        dance / funk off-beat stabs, the swing comping) with the groove's short stab instrument; 'pad' bars (verse)
        use the sparser row set. The tropical groove strikes on the hook's own off-beat rows instead (the verse
        hints the hook's rhythm quietly, the chorus plucks it)."""
        rows = self.groove["stab"][style]
        R = self.R
        if rows == "hook":
            hook_rows = sorted({r % R for r, _ in self.hook if r >= 0})
            off = [r for r in hook_rows if r % self.beat] or hook_rows
            rows = tuple(off if style != "pad" else off[:2])
        inst = self.groove["stab_inst"].split()[1]
        native = self.groove["sync"]
        grid = level_grid(self.sync, R) if self.sync < native else None
        if grid:
            rows = tuple(r for r in _level_rows(tuple(rows), grid, R) if r < R)
        tag = f"@{inst}" if style != "pad" or self.groove_name != "tropical" else "@pad"
        for i, r in enumerate(rows):
            if r < R:
                self.sc.put(bar, 1, r, f"{midi_to_note(low)}:{cname}" + (tag if i == 0 else ""))

    def put_groove_bass(self, bar: int, sym: str, style: str, next_sym: str | None, bend_bar: bool) -> None:
        """Wave lane on a groove: the groove's bass pattern for the section style, straightened below its native
        syncopation level, pushed above it; the downbeat keeps the instrument tag and the rare resolving bend."""
        root_pc, qual, chord_pcs = self.chord(sym)
        root = self.bass_root(root_pc)
        pattern = self.groove["bass"].get(style) or self.groove["bass"]["eighths"]
        if qual in ("min", "m7", "m9", "madd9", "dim", "m7b5"):     # minor chords: the walk takes the minor third / seventh
            rows, semis, cut = pattern
            semis = tuple(3 if x == 4 else (10 if x == 9 else x) for x in semis)
            pattern = (rows, semis, cut)
        cells = _render_bass_pattern(pattern, root, self.sync, self.groove["sync"], self.R)
        nxt = self.bass_root(self.chord(next_sym)[0]) if next_sym and next_sym != sym else None
        if self.sync > self.groove["sync"]:                       # each level above the groove's own adds the next push
            syncopate_bass_cells(cells, self.sync - self.groove["sync"], self.R, nxt, root)
        bass_rate = BEND_RATES.get(self.bend, BEND_RATES["sparse"])[0]
        draw = self.rng.random()
        if cells[0] == ".":
            cells[0] = midi_to_note(root)
        base = cells[0].split("!")[0]
        cut = ("!" + cells[0].split("!")[1]) if "!" in cells[0] else ""
        if bend_bar and bar % 2 == 0 and draw < bass_rate * 0.6:
            cells[0] = f"{base}@bass/-2,6"
        else:
            cells[0] = f"{base}@bass{cut}"
        for r, c in enumerate(cells):
            self.sc.put(bar, 2, r, c)

    def put_groove_drums(self, bar: int, style: str, fill: bool, crash: bool) -> None:
        """Noise lane on a groove: the groove's kit pattern for the section style (kick / snare straightened below
        the native level, hats untouched), the groove's fill on the last beat, a crash on the downbeat."""
        g = self.groove
        R = self.R
        cells = _render_kit_pattern(g["kit"].get(style) or g["kit"]["backbeat"], self.sync, g["sync"], R)
        if self.sync > g["sync"]:
            syncopate_kit_cells(cells, self.sync - g["sync"], R)
        if fill and style != "build":
            tail = g["kit"]["fill"].split()
            for i, c in enumerate(tail):
                r = R - len(tail) + i
                if 0 <= r < R:
                    cells[r] = c
        elif fill:                                                # the pre-chorus lift: snares on every row of the last half
            for r in range(R // 2, R):
                cells[r] = "S" if r % self.beat == 0 else "s"
        if crash:
            cells[0] = "KC"
        for r, c in enumerate(cells):
            self.sc.put(bar, 3, r, c)

    def put_bass(self, bar: int, sym: str, style: str, next_sym: str | None, bend_bar: bool) -> None:
        """Wave lane per bar: 'eighths' root pulse, 'bounce' root/octave, 'riff', 'walk' (pre-chorus climb),
        'hold' (bridge), 'boogie' (blues). The downbeat may bend into the root on a few even bars.
        With the fusion texture every moving style becomes the fusion slap bass (walk / bounce / slap / pedal)."""
        root_pc, qual, chord_pcs = self.chord(sym)
        if self.groove_name != "straight" and not (self.texture == "fusion" and style in ("eighths", "bounce", "walk", "riff", "quarters")):
            self.put_groove_bass(bar, sym, style, next_sym, bend_bar)
            return
        if self.texture == "fusion" and style in ("eighths", "bounce", "walk", "riff", "quarters"):
            nxt_pc = self.chord(next_sym)[0] if next_sym else root_pc
            _fusion_bass(self.sc, self.rng, bar, root_pc, chord_pcs, self.lead_scale_pcs(sym), next_root_pc=nxt_pc,
                         last=bool(next_sym and next_sym != sym), accent_inst="bass" if style != "walk" else "bassr",
                         bend=self.bend if bend_bar else "none")
            return
        root = self.bass_root(root_pc)
        fifth = root + 7 if root + 7 <= 47 else root - 5
        cells = ["."] * 16
        if style == "eighths":
            for r in range(0, 16, 2):
                cells[r] = f"{midi_to_note(root)}!5"
            cells[6] = f"{midi_to_note(fifth)}!5"
            cells[14] = f"{midi_to_note(fifth)}!5"
        elif style == "bounce":
            for r in range(0, 16, 2):
                cells[r] = midi_to_note(root) if r % 4 == 0 else f"{midi_to_note(root + 12)}!3"
            cells[11] = f"{midi_to_note(root + 12)}!2"
            cells[15] = f"{midi_to_note(fifth)}!3"
        elif style == "walk":
            steps = [root, root, fifth, fifth, root + 12, root + 12, fifth, root]
            for i, n in enumerate(steps):
                cells[i * 2] = f"{midi_to_note(n)}!5"
        elif style == "hold":
            cells[0] = midi_to_note(root)
            cells[8] = f"{midi_to_note(fifth)}"
        elif style in ("riff", "boogie"):
            rows, semis = RIFFS[self.riff if style == "riff" else "boogie"]
            for r, s in zip(rows, semis):
                n = root + s
                n = max(WAVE_RANGE[0] + 8, min(60, n))
                cells[r] = f"{midi_to_note(n)}!4" if r else midi_to_note(n)
        else:                                                    # "quarters": root on the beats (intro)
            for r in (0, 4, 8, 12):
                cells[r] = f"{midi_to_note(root)}!6"
        # the downbeat: instrument tag, and (rarely, --bend) a bend from a tone below that lands on the root
        bass_rate = BEND_RATES.get(self.bend, BEND_RATES["sparse"])[0]
        draw = self.rng.random()
        base = cells[0].split("!")[0] if cells[0] != "." else midi_to_note(root)
        cut = ("!" + cells[0].split("!")[1]) if "!" in cells[0] else ""
        if bend_bar and bar % 2 == 0 and draw < bass_rate * 0.6:
            cells[0] = f"{base}@bass/-2,6"
        else:
            cells[0] = f"{base}@bass{cut}"
        if next_sym and next_sym != sym and style in ("eighths", "bounce", "walk") and self.rng.random() < 0.5:
            nxt = self.bass_root(self.chord(next_sym)[0])
            approach = nxt + self.rng.choice((-1, -2, 1))
            if 33 <= approach <= 50:
                cells[15] = f"{midi_to_note(approach)}!6"
        if self.sync > 0:                                        # --syncopation on the straight groove: generic pushes
            nxt = self.bass_root(self.chord(next_sym)[0]) if next_sym and next_sym != sym else None
            syncopate_bass_cells(cells, self.sync, 16, nxt, root)
        for r, c in enumerate(cells):
            self.sc.put(bar, 2, r, c)

    def put_drums(self, bar: int, style: str, fill: bool = False, crash: bool = False) -> None:
        """Noise lane: 'hats' (intro), 'backbeat' (verse: kick/snare, closed hats on 8ths), 'build' (pre-chorus
        snare lift), 'full' (chorus: open hats, syncopated kick), 'half' (bridge: half-time), 'shuffle' (blues).
        With the fusion texture 'full' and 'shuffle' become the fusion kit (16th hats, ghost snares, stacks)."""
        if self.texture == "fusion" and style in ("full", "shuffle") and self.R == 16:
            _fusion_drums(self.sc, self.rng, bar, fill=fill)
            if crash:
                self.sc.put(bar, 3, 0, "KC")
            return
        if self.groove_name != "straight":
            self.put_groove_drums(bar, style, fill, crash)
            return
        c = ["."] * 16
        if style == "hats":
            for r in range(0, 16, 2):
                c[r] = "H" if r % 4 == 0 else "h"
        elif style == "backbeat":
            for r in range(0, 16, 2):
                c[r] = "h"
            c[0], c[8], c[4], c[12] = "KH", "KH", "SH", "SH"
        elif style == "build":
            for r in range(16):
                c[r] = "h"
            c[0], c[8], c[4], c[12] = "KH", "KH", "SH", "SH"
            if fill:                                             # the lift: snare on every 8th, then every 16th
                for r in range(0, 8, 2):
                    c[r] = "S" if r % 4 == 0 else "s"
                for r in range(8, 16):
                    c[r] = "S" if r % 2 == 0 else "s"
                c[0] = "KS"
        elif style == "full":
            for r in range(0, 16, 2):
                c[r] = "H" if r % 4 == 0 else "h"
            c[0], c[8], c[4], c[12] = "KH", "KH", "SH", "SH"
            c[6], c[14] = "O", "O"
            c[10] = "Kh"
        elif style == "half":
            c[0], c[8] = "K", "S"
            c[4], c[12] = "h", "h"
        elif style == "shuffle":
            for r in (0, 3, 4, 7, 8, 11, 12, 15):
                c[r] = "H" if r % 4 == 0 else "h"
            c[0], c[8], c[4], c[12] = "KH", "KH", "SH", "SH"
        if fill and style != "build":
            c[12], c[13], c[14], c[15] = "S", "s", "S", "T" if style != "half" else "S"
            if style in ("full", "shuffle"):
                c[10], c[11] = "T", "s"
        if crash:
            c[0] = "KC"
        if self.sync > 0:
            syncopate_kit_cells(c, self.sync, 16)
        for r, x in enumerate(c):
            self.sc.put(bar, 3, r, x)

    # ---- sections
    def write(self, sections: list[Section]) -> None:
        rng = self.rng
        n_sections = len(sections)
        for si, sec in enumerate(sections):
            b0 = sec.start
            nxt = sections[si + 1] if si + 1 < n_sections else None
            role = sec.role
            final = si == n_sections - 1 or (nxt is not None and nxt.role == "outro")
            self.meta.append(f"{sec.label}: bars {b0 + 1}-{b0 + sec.bars}, " + " ".join(sec.syms) +
                             " = " + numerals_to_names(sec.syms, self.key))
            for i in range(sec.bars):
                bar = b0 + i
                sym = sec.syms[i]
                next_sym = sec.syms[i + 1] if i + 1 < sec.bars else (nxt.syms[0] if nxt else None)
                last = i == sec.bars - 1
                if role == "intro":
                    self.put_chord(bar, sym, "pad" if i < 2 else "full")
                    self.put_bass(bar, sym, "quarters" if i < 2 else "eighths", next_sym, False)
                    self.put_drums(bar, "hats" if i < 2 else "backbeat", fill=last)
                elif role == "verse":
                    if self.flavour == "rock":
                        self.put_chord(bar, sym, "riff")
                        self.put_bass(bar, sym, "riff", next_sym, False)
                    else:
                        self.put_chord(bar, sym, "pad")
                        self.put_bass(bar, sym, "eighths", next_sym, False)
                    self.put_drums(bar, "backbeat", fill=(i % 4 == 3))
                elif role == "prechorus":
                    self.put_chord(bar, sym, "pad" if i < 2 else "full")
                    self.put_bass(bar, sym, "walk", next_sym, False)
                    self.put_drums(bar, "build", fill=last)
                elif role == "chorus" or role.startswith("A"):
                    full = role == "chorus" or role == "A3"
                    self.put_chord(bar, sym, "full" if full else "pad", centre=76 if full else 72)
                    self.put_bass(bar, sym, "bounce" if full else "eighths", next_sym, bend_bar=True)
                    self.put_drums(bar, "full" if full else "backbeat", fill=(i % 4 == 3), crash=(i == 0 and full))
                elif role in ("bridge", "B"):
                    if self.texture == "fusion":                 # the fusion middle eight: the chord drops, the echo answers the lead
                        self.put_chord(bar, sym, "echo" if i == 0 else ("echo-off" if last else "rest"))
                    else:
                        self.put_chord(bar, sym, "pad", centre=68)
                    self.put_bass(bar, sym, "hold", next_sym, False)
                    self.put_drums(bar, "half", fill=last)
                elif role in ("S1", "S2", "S3"):                 # the stage-corpus loop
                    if role == "S1":
                        self.put_chord(bar, sym, "riff" if self.flavour == "rock" and self.texture != "fusion" else "full")
                        self.put_bass(bar, sym, "riff" if self.flavour == "rock" else "bounce", next_sym, False)
                        self.put_drums(bar, "full", fill=(i % 4 == 3))
                    elif role == "S2":
                        if self.texture == "fusion":
                            self.put_chord(bar, sym, "echo" if i == 0 else ("echo-off" if last else "rest"))
                        else:
                            self.put_chord(bar, sym, "pad")
                        self.put_bass(bar, sym, "walk", next_sym, False)
                        self.put_drums(bar, "build", fill=last)
                    else:
                        self.put_chord(bar, sym, "full", centre=76)
                        self.put_bass(bar, sym, "bounce", next_sym, bend_bar=True)
                        self.put_drums(bar, "full", fill=(i % 4 == 3), crash=(i == 0))
                elif role == "outro":
                    self.put_chord(bar, sym, "full" if not last else "pad", centre=76)
                    self.put_bass(bar, sym, "bounce" if not last else "hold", next_sym, False)
                    self.put_drums(bar, "full" if not last else "half", fill=(i == sec.bars - 2), crash=last)
                elif role in ("head", "head2", "head3", "solo"):
                    self.put_chord(bar, sym, "stab", centre=70)
                    self.put_bass(bar, sym, "boogie", next_sym, False)
                    self.put_drums(bar, "shuffle", fill=(i % 4 == 3), crash=(i == 0 and role != "head"))
            if role == "intro" and sec.bars >= 4:
                self.sc.put(b0 + 2, 0, 0, "." )
                if self.hook_level >= 2:                         # the chord voice plays the hook's rhythm first (--hook 2)
                    self.put_hook_rhythm_chord(b0, sec.syms[0:2])
                self.put_lead(b0 + sec.bars - 2, self.hook, self.chorus_centre if self.hook_level else self.verse_centre,
                              sec.syms[-2:], "lead", rest_row=30)          # --hook: the hook is heard at pitch inside the first seconds
            elif role == "verse":
                self.write_verse(sec, second=any(s.role == "verse" and s.start < sec.start for s in sections))
            elif role == "prechorus":
                self.prechorus_count = getattr(self, "prechorus_count", 0) + 1
                frag = fragment(self.hook, self.R)
                if self.phrases >= 2 and self.prechorus_count == 2:   # the second pre-chorus climbs on the hook's answer
                    frag = fragment(self.bank("hook", "chorus")["a"], self.R)
                    if not motif_notes(frag):
                        frag = fragment(self.hook, self.R)
                for k in range(sec.bars):                       # a one-bar fragment, sequenced up a step each bar
                    one = [(r, None if d is None else d + k) for r, d in frag]
                    self.put_lead(b0 + k, one, self.verse_centre + 2, [sec.syms[k], sec.syms[k]], "lead", hold_vib=False, rest_row=None)
                    if k == sec.bars - 1:
                        self.sc.put(b0 + k, 0, self.q(14), "-")       # a breath before the chorus downbeat
            elif role == "chorus":
                self.write_hook(sec, self.chorus_centre, "hook", final=final)
            elif role.startswith("A"):
                centre = self.verse_centre + (self.mel.octave if role == "A3" else 0)
                self.write_phrase_srdc(sec, self.verse_motif, centre, "hook" if role == "A3" else "lead",
                                       vary=(role == "A2"))
            elif role in ("bridge", "B"):
                self.write_bridge(sec)
                if self.hook_level >= 3:                         # the bass quotes the hook under the bridge (--hook 3)
                    self.put_bass_quote(b0, sec.syms[0:2])
            elif role in ("S1", "S2", "S3"):
                k = int(role[1]) - 1
                centre = self.chorus_centre if role == "S3" else self.verse_centre
                self.write_stage_section(sec, self.stage_motifs[k], centre, "hook" if role == "S3" else "lead")
                if self.hook_level >= 3 and role == "S2":
                    self.put_bass_quote(b0, sec.syms[0:2])
            elif role == "outro":
                if self.hook_level:                              # the post-chorus figure: the hook's tail twice, then the cadence
                    self.put_lead(b0, tail_twice(self.hook), self.chorus_centre, sec.syms[0:2], "hook", rest_row=None)
                else:
                    self.put_lead(b0, self.hook, self.chorus_centre, sec.syms[0:2], "hook", rest_row=None)
                tag = cadence(self.hook, self.mel, self.chorus_centre)
                self.put_lead(b0 + 2, tag, self.chorus_centre, sec.syms[2:4], "hook", rest_row=None)
            elif role in ("head", "head2", "head3"):
                self.write_blues_head(sec, self.verse_centre + (self.mel.octave if role != "head" else 0),
                                      "hook" if role != "head" else "lead")
            elif role == "solo":
                self.write_blues_solo(sec)
        self.sc.loop = sections[0].bars if sections[0].role == "intro" else 0
        self.sc.sections = [(s.role, s.start, s.bars) for s in sections]
        if self.hook_level >= 2:
            self.enforce_peak(sections)

    # ---- hooks (--hook)
    def put_hook_rhythm_chord(self, bar0: int, syms: list[str]) -> None:
        """Pulse 2 states the hook's rhythm on chord tones (root and third alternating) over two bars: the hook is
        in the listener's ear before the lead sings it."""
        for b in (bar0, bar0 + 1):
            for r in range(16):
                self.sc.put(b, 1, r, ".")
        k = 0
        for row, deg in self.hook:
            b = bar0 + row // 16
            if deg is None:
                self.sc.put(b, 1, row % 16, "-")
                continue
            root_pc, qual, _ = self.chord(syms[min(row // 16, len(syms) - 1)])
            low, ivs = voice(root_pc, CHORDS[qual], 72, None)
            n = low + (ivs[1] if k % 2 else 0)
            self.sc.put(b, 1, row % 16, midi_to_note(n) + ("@pad" if k == 0 else ""))
            k += 1
        self.pad_bars.discard(bar0)
        self.pad_bars.discard(bar0 + 1)

    def put_bass_quote(self, bar0: int, syms: list[str]) -> None:
        """The wave channel quotes the hook two octaves down in the first two bars of the bridge: notes, not a
        pattern; the root returns on the hook's rest."""
        centre = self.mel.index_near(self.mel.notes[self.verse_centre] - 24)
        for b in (bar0, bar0 + 1):
            for r in range(16):
                self.sc.put(b, 2, r, ".")
        first = True
        for row, deg in self.hook:
            b = bar0 + row // 16
            if deg is None:
                root = self.bass_root(self.chord(syms[min(row // 16, len(syms) - 1)])[0])
                self.sc.put(b, 2, row % 16, midi_to_note(root))
                continue
            n = max(WAVE_RANGE[0] + 8, min(60, self.mel.note(centre, deg)))
            self.sc.put(b, 2, row % 16, midi_to_note(n) + ("@bass" if first else ""))
            first = False

    def enforce_peak(self, sections: list[Section]) -> None:
        """The chorus (stage C, the final A) is the registral peak: any lead note elsewhere that reaches the
        peak section's top note is lowered a scale step until it does not."""
        peak_roles = {"chorus", "S3", "A3"}
        peak_bars = {b for s in sections if s.role in peak_roles for b in range(s.start, s.start + s.bars)}
        if not peak_bars:
            return
        def notes_in(bars):
            for b in bars:
                for r, c in enumerate(self.sc.bars[b][0]):
                    m = LEAD_CELL_RE.match(c) if c not in (".", "-") else None
                    if m and m.group(1):
                        yield b, r, m
        top = max((note_to_midi(m.group(1)) for _, _, m in notes_in(peak_bars)), default=None)
        if top is None:
            return
        for b, r, m in list(notes_in(b for b in range(len(self.sc.bars)) if b not in peak_bars)):
            n = note_to_midi(m.group(1))
            if n < top:
                continue
            i = self.mel.index_near(n)
            while i > 0 and self.mel.notes[i] >= top:
                i -= 1
            self.sc.bars[b][0][r] = midi_to_note(self.mel.notes[i]) + (m.group(2) or "") + m.group(3)
            self.peak_fixes += 1

    def hook_info(self) -> dict:
        """What the hook engine designed (the measured metrics are added after the organic layer)."""
        if not self.hook_level:
            return {}
        d = self.design
        centre = self.chorus_centre if self.form == "verse-chorus" else self.verse_centre
        names = [midi_to_note(self.mel.note(centre, deg)) for _, deg in motif_notes(self.hook)]
        return {"level": self.hook_level, "bars": 2, "contour": d["contour"], "rhythm": d["cells"], "onsets": d["onsets"],
                "range": d["range"], "leap_at": d["leap_at"], "surprise": d["surprise"], "hearings": self.hook_hearings,
                "names": names, "peak_fixes": self.peak_fixes,
                "derived": {"verse": "the hook's rhythm skeleton on half the compass, a register lower",
                            "prechorus": "the hook's first bar sequenced up a step per bar",
                            "outro": "the hook's second bar twice, then the hook cadencing",
                            **({"answers": "mirror the statement (same rhythm and count)", "intro": "pulse 2 plays the hook's rhythm on chord tones"} if self.hook_level >= 2 else {}),
                            **({"bridge": "the wave bass quotes the hook", "final_chorus": "the last statement's final note arrives an 8th late"} if self.hook_level >= 3 else {})}}

    def write_verse(self, sec: Section, second: bool) -> None:
        """srdc: statement (bars 1-2), restatement with the last note changed (3-4), departure a step higher
        with the second rhythm (5-6), conclusion that cadences on the tonic (7-8). A rock verse is call and
        response: the riff speaks in bar 1, the lead answers in bar 2."""
        b0 = sec.start
        if self.phrases:
            self.write_verse_phrases(sec, second)
            return
        m = self.verse_motif if self.flavour != "rock" else self.answer
        rng = random.Random(self.key * 131 + 7)                  # the verse's own stream: verse 2 == verse 1 ...
        r = vary_last(m, rng)
        d = transpose(m, 2)
        c = cadence(m, self.mel, self.verse_centre)
        phrases = [m, r, d, c]
        if self.hook_level >= 2:                                 # melodic math: a line, its mirror, the line changed, the mirror cadencing
            a = mirror_motif(m)
            phrases = [m, a, third_time(m, 1), cadence(a, self.mel, self.verse_centre)]
        if second:                                               # ... except for one note in bar 4 and the ending
            phrases[1] = vary_last(r, random.Random(self.key * 131 + 8))
            phrases[3] = transpose(c, self.mel.octave) if self.flavour != "rock" else vary_last(c, rng)
        for k, ph in enumerate(phrases):
            bar = b0 + k * 2
            if bar + 1 >= b0 + sec.bars:
                break
            self.put_lead(bar, ph, self.verse_centre, sec.syms[k * 2:k * 2 + 2], "lead", bend_ok=(k == 3))

    def write_verse_phrases(self, sec: Section, second: bool) -> None:
        """The verse from its motif bank: statement, restatement with the last note changed, the answer (on the
        second lead colour), the departure cadencing. Verse 2 thins the restatement and ends an octave up; at
        level 2 it re-orders the bank (s a d' s-cadence) so its phrases are new against verse 1. A rock verse
        keeps the call and response with the riff: the lead speaks in bar 2 only."""
        b0 = sec.start
        bk = self.bank("verse", "verse", span=5)
        s, a, d = bk["s"], bk["a"], bk["d"]
        if self.flavour == "rock":
            s, a, d = second_bar_only(s), second_bar_only(a), second_bar_only(d)
        rng = random.Random(self.key * 131 + 7)
        c = self.verse_centre
        if not second:
            phrases = [s, vary_last(s, rng), a, cadence(d, self.mel, c)]
            insts = ["lead", "lead", "lead2", "lead"]
        elif self.phrases >= 2:
            phrases = [s, a, vary_last(d, rng), cadence(s, self.mel, c)]
            insts = ["lead", "lead2", "lead", "lead"]
        else:
            cad = cadence(d, self.mel, c)
            phrases = [s, thin(vary_last(s, random.Random(self.key * 131 + 8)), rng), a,
                       transpose(cad, self.mel.octave) if self.flavour != "rock" else vary_last(cad, rng)]
            insts = ["lead", "lead", "lead2", "lead"]
        for k, ph in enumerate(phrases):
            bar = b0 + k * 2
            if bar + 1 >= b0 + sec.bars:
                break
            self.put_lead(bar, ph, c, sec.syms[k * 2:k * 2 + 2], insts[k], bend_ok=(k == 3))
            self.put_response(bar, ph, c, sec.syms[k * 2:k * 2 + 2])

    def write_hook(self, sec: Section, centre: int, inst: str, final: bool) -> None:
        """AAAB: the hook three times, then the hook with a cadence; the last chorus repeats it exactly (the hook
        is the hook), only the kit opens up. With --phrases the third statement is the hook's answer (bar 1
        quotes the verse's statement a step up, bar 2 is the bank's answer) on the other lead colour; at level 2
        the second chorus answers with the bank's departure instead."""
        b0 = sec.start
        h = self.hook
        phrases = [h, h, h, cadence(h, self.mel, centre)]
        insts = [inst] * 4
        if self.hook_level:                                      # the third time changes; the last time the final note comes late
            self.hooks_written += 1
            third = third_time(h, self.hook_level)
            if self.hook_level >= 3 and final:
                third = delay_last(third)
            phrases = [h, h, third, cadence(h, self.mel, centre)]
        elif self.phrases:
            bk = self.bank("hook", "chorus")
            self.hooks_written += 1
            second = self.phrases >= 2 and self.hooks_written == 2
            ans = bk["d"] if second else bk["a"]
            if "verse" in self.banks:
                ans = quote_then_new(self.banks["verse"]["s"], ans, 1)
            phrases = [h, h, ans, cadence(bk["d"] if second else h, self.mel, centre)]   # the second chorus ends on a new idea
            insts = [inst, inst, self.alt_inst(inst), inst]
        for k, ph in enumerate(phrases):
            bar = b0 + k * 2
            if bar + 1 >= b0 + sec.bars:
                break
            self.put_lead(bar, ph, centre, sec.syms[k * 2:k * 2 + 2], insts[k], bend_ok=(k == 3), rest_row=31 if k < 3 else None)
            self.put_response(bar, ph, centre, sec.syms[k * 2:k * 2 + 2])
        if final:
            self.sc.put(b0 + sec.bars - 1, 0, self.q(14), "-")

    def write_phrase_srdc(self, sec: Section, motif: list[tuple[int, int]], centre: int, inst: str, vary: bool) -> None:
        rng = random.Random(self.key * 97 + 3)
        insts = [inst] * 4
        if self.phrases:                                          # from the A bank: s s' a d-cadence; A' re-orders at level 2
            bk = self.bank("A", "A", span=5)
            s, a, d = bk["s"], bk["a"], bk["d"]
            if s is self.hook:                                    # --hook: the A theme is the hook twice, the third changed, the cadence
                phrases = [s, s, third_time(s, self.hook_level), cadence(s, self.mel, centre)]
                if vary:
                    phrases[3] = vary_last(cadence(s, self.mel, centre), random.Random(self.key * 97 + 4))
            elif vary and self.phrases >= 2:
                phrases = [s, a, vary_last(d, rng), cadence(s, self.mel, centre)]
                insts = [inst, self.alt_inst(inst), inst, inst]
            else:
                phrases = [s, thin(vary_last(s, rng), rng) if vary else vary_last(s, rng), a, cadence(d, self.mel, centre)]
                insts = [inst, inst, self.alt_inst(inst), inst]
        elif self.hook_level:                                     # the A theme is the hook: twice, the third changed, cadence
            phrases = [motif, motif, third_time(motif, self.hook_level), cadence(motif, self.mel, centre)]
            if vary:
                phrases[3] = vary_last(cadence(motif, self.mel, centre), random.Random(self.key * 97 + 4))
        else:
            r = vary_last(motif, rng)
            phrases = [motif, r, transpose(motif, 2), cadence(motif, self.mel, centre)]
            if vary:
                phrases[3] = vary_last(cadence(motif, self.mel, centre), random.Random(self.key * 97 + 4))
        for k, ph in enumerate(phrases):
            bar = sec.start + k * 2
            self.put_lead(bar, ph, centre, sec.syms[k * 2:k * 2 + 2], insts[k], bend_ok=(k == 3))
            self.put_response(bar, ph, centre, sec.syms[k * 2:k * 2 + 2])

    def write_stage_section(self, sec: Section, motif: list[tuple[int, int]], centre: int, inst: str) -> None:
        """The stage corpus's section grammar (A A' B B' C C'): a 4-bar phrase = the motif and the motif with
        its last note changed; the repeat keeps the motif and cadences. Each section has its own motif; C sits an
        octave up."""
        b0 = sec.start
        rng = random.Random(self.key * 173 + b0)
        p1 = [motif, vary_last(motif, rng)]
        p2 = [motif, cadence(motif, self.mel, centre)]
        insts = [inst] * 4
        if self.hook_level and not self.phrases:
            if motif is self.hook:                                # A and C state the hook: twice, the third changed, cadence
                p1 = [motif, motif]
                p2 = [third_time(motif, self.hook_level), cadence(motif, self.mel, centre)]
            elif self.hook_level >= 2:                            # B: the preview and its mirror, paired
                a = mirror_motif(motif)
                p1 = [motif, a]
                p2 = [third_time(motif, 1), cadence(a, self.mel, centre)]
        if self.phrases:                                          # A A' B B' from the section's bank; B answers A
            k = int(sec.role[1]) - 1
            bk = self.bank(sec.role, sec.role)
            s, a = bk["s"], bk["a"]
            if k > 0 and f"S{k}" in self.banks and s is not self.hook:   # bar 1 quotes the previous section's answer a step away
                s = quote_then_new(self.banks[f"S{k}"]["a"], s, 1 if k == 2 else -1)
            p1 = [s, thin(vary_last(s, rng), rng) if self.phrases >= 2 else vary_last(s, rng)]
            p2 = [a, cadence(bk["d"] if self.phrases >= 2 else a, self.mel, centre)]
            insts = [inst, inst, self.alt_inst(inst), inst]
            if s is self.hook:                                    # --hook: the hook section is the hook twice, the third changed, the cadence
                p1 = [s, s]
                p2 = [third_time(s, self.hook_level), cadence(s, self.mel, centre)]
                insts = [inst] * 4
        for k, ph in enumerate(p1 + p2):
            bar = b0 + k * 2
            if bar + 1 >= b0 + sec.bars:
                break
            self.put_lead(bar, ph, centre, sec.syms[k * 2:k * 2 + 2], insts[k], bend_ok=(k == 3))
            self.put_response(bar, ph, centre, sec.syms[k * 2:k * 2 + 2])

    def write_bridge(self, sec: Section) -> None:
        """New register (lower), long notes, new chords: a departure, not a second song."""
        b0 = sec.start
        m = self.bridge_motif
        phrases = [m, vary_last(m, random.Random(self.key * 59 + 1)), transpose(m, -2), cadence(m, self.mel, self.bridge_centre)]
        insts = ["lead"] * 4
        if self.phrases:                                          # sparse bank, the statement on the second colour
            bk = self.bank("bridge", "bridge", span=4)
            rng = random.Random(self.key * 59 + 1)
            phrases = [bk["s"], bk["a"], thin(bk["s"], rng), cadence(bk["d"], self.mel, self.bridge_centre)]
            insts = ["lead2", "lead", "lead2", "lead"]
        for k in range(sec.bars // 2):
            self.put_lead(b0 + k * 2, phrases[k % 4], self.bridge_centre, sec.syms[k * 2:k * 2 + 2], insts[k % 4])
            self.put_response(b0 + k * 2, phrases[k % 4], self.bridge_centre, sec.syms[k * 2:k * 2 + 2])

    def write_blues_head(self, sec: Section, centre: int, inst: str) -> None:
        """aab: the call over I (bars 1-2), the bass answers (3-4), the same call over IV (5-8), the answer
        line over V-IV that lands on the tonic (9-10), a turnaround lick (11-12)."""
        b0 = sec.start
        a = self.head
        b = cadence(transpose(a, -2), self.mel, centre)
        lick = [(self.q(r), d) for r, d in ((0, 2), (2, 1), (4, 0), (8, -1), (12, 0))]
        self.put_lead(b0, a, centre, sec.syms[0:2], inst, bend_ok=True)
        self.put_lead(b0 + 4, a, centre, sec.syms[4:6], inst, bend_ok=True)
        self.put_lead(b0 + 8, b, centre, sec.syms[8:10], inst, bend_ok=True)
        self.put_lead(b0 + 10, cadence(lick, self.mel, centre), centre, sec.syms[10:12], inst, rest_row=28)

    def write_blues_solo(self, sec: Section) -> None:
        """Twelve bars of fresh one-bar runs in the blue scale, busiest lane of the song."""
        b0 = sec.start
        rng = random.Random(self.key * 211 + 5)
        centre = self.chorus_centre
        for k in range(0, sec.bars, 2):
            run = make_motif(rng, rng.choice(("quick", "sync", "pickup")), span=7)
            self.put_lead(b0 + k, run, centre, sec.syms[k:k + 2], "hook", bend_ok=True, rest_row=None)


def gen_form(rng: random.Random, key: int, bpm: float, bars: int, name: str, bend: str, brng: random.Random,
             style: str, form: str, progression: str | None, texture: str = "plain", lift: str = "fifth",
             phrases: int = 0, prng: random.Random | None = None, hook: int = 0, hrng: random.Random | None = None,
             groove: str = "straight", syncopation: int | None = None) -> tuple[Score, list[str], dict]:
    """The song-form generator behind --style pop|rock|chip|ska with --form stage|verse-chorus|aaba|blues12,
    --texture plain|fusion, --lift fifth|sixth|octave, --phrases 0|1|2 (the motif banks), --hook 0..3 (the hook
    designed first, the melodies derived from it), --groove and --syncopation (the rhythm of a genre)."""
    flavour = "blues" if form == "blues12" else style
    if style == "ska" and groove == "straight":
        groove = "ska"
    if progression is None:
        progression = {"pop": "axis", "chip": "axis", "rock": "threechord", "ska": "skank"}[style]
        if form == "blues12":
            progression = "blues12q" if rng.random() < 0.5 else "blues12"
        elif form == "stage":                                    # the stage-corpus defaults
            progression = "stage_a | stage_b | stage_c" if style == "rock" or rng.random() < 0.5 else "town | cadential | stage_c"
        elif style == "rock" and rng.random() < 0.5:
            progression = "mixolydian"
        elif style == "ska" and rng.random() < 0.5:
            progression = "doowop"
    progs = resolve_progressions(progression)
    prog_name, syms = progs[0]
    extra = [p[1] for p in progs[1:]]
    if form == "blues12" and len(syms) != 12:
        raise ScoreError(f"--form blues12 needs a twelve-chord progression (blues12 or blues12q), got {len(syms)} chords")
    mode = _mode_scale(syms)
    plan = build_plan(form, bars, syms, mode, rng, extra)
    fc = FormComposer(rng, brng, key, bpm, name, flavour, form, syms, bend, prog_name, texture, lift, phrases, prng, hook, hrng, groove, syncopation)
    fc.write(plan)
    if fc.phrases:
        fc.meta.append(f"phrases {fc.phrases}: motif banks " + ", ".join(f"{k} (s a d)" for k in fc.banks)
                       + f"; {fc.responses} pulse-2 answers; the answer phrases on lead2")
    if fc.hook_level:
        d = fc.design
        fc.meta.append(f"hook {fc.hook_level}: {d['contour']} contour, {d['range']} semitones, rhythm " + " ".join(d["cells"])
                       + f", leap at note {d['leap_at']}, heard {fc.hook_hearings} times note for note, third time changed"
                       + (f"; surprise {d['surprise']}" if d["surprise"] else "")
                       + (f"; {fc.peak_fixes} notes lowered so the chorus holds the top note" if fc.peak_fixes else ""))
    elif hook:
        fc.meta.append("hook: ignored (the twelve-bar blues keeps its aab head and solo)")
    prog_label = " | ".join(f"{n}: {' '.join(s)}" for n, s in progs) if len(progs) > 1 else f"{prog_name}: {' '.join(syms)}"
    meta = [f"form {form}, {sum(s.bars for s in plan)} bars, loop -> bar {fc.sc.loop + 1}, texture {texture}"
            + (f", groove {groove} (syncopation {fc.sync}, {fc.R} rows per bar)" if groove != "straight" or fc.sync else "") + f"; progression {prog_label}"
            f" ({PROGRESSIONS[prog_name][1] if prog_name in PROGRESSIONS else 'custom'})",
            "plan: " + " | ".join(f"{s.label} {s.start + 1}-{s.start + s.bars}" for s in plan),
            f"lead scale: {PC_NAME[key]} " + [k for k, v in SCALES.items() if [(key + x) % 12 for x in v] == fc.mel.pcs][0]
            + f"; verse centre {midi_to_note(fc.mel.notes[fc.verse_centre])}, chorus centre {midi_to_note(fc.mel.notes[min(len(fc.mel.notes) - 1, fc.chorus_centre)])}",
            *fc.meta]
    info = {"form": form, "texture": texture, "lift": lift, "groove": groove, "syncopation_level": fc.sync, "rows_per_bar": fc.R,
            "progression": prog_name, "numerals": syms, "chords": numerals_to_names(syms, key),
            "progressions": [{"name": n, "numerals": s, "chords": numerals_to_names(s, key)} for n, s in progs],
            "mode": mode, "loop_bar": fc.sc.loop, "phrases": fc.phrases,
            "hook": fc.hook_info() if fc.hook_level else ({"ignored": "the twelve-bar blues keeps its aab head and solo"} if hook else {}),
            "banks": {k: {"s": v["cells"]["s"], "a": v["cells"]["a"], "d": v["cells"]["d"]} for k, v in fc.banks.items()},
            "pulse2_answers": fc.responses,
            "plan": [{"section": s.label, "role": s.role, "start_bar": s.start + 1, "bars": s.bars,
                      "numerals": s.syms, "chords": numerals_to_names(s.syms, key)} for s in plan]}
    return fc.sc, meta, info


def gen_pop(rng, key, bpm, bars, name, bend="sparse", brng=None, form="verse-chorus", progression=None):
    return gen_form(rng, key, bpm, bars, name, bend, brng or random.Random(0), "pop", form, progression)


def gen_rock(rng, key, bpm, bars, name, bend="sparse", brng=None, form="verse-chorus", progression=None):
    return gen_form(rng, key, bpm, bars, name, bend, brng or random.Random(0), "rock", form, progression)


def gen_ska(rng, key, bpm, bars, name, bend="sparse", brng=None, form="verse-chorus", progression=None):
    return gen_form(rng, key, bpm, bars, name, bend, brng or random.Random(0), "ska", form, progression, groove="ska")


# ----------------------------------------------------------------------------------------------- fusion with a form

def gen_fusion_form(rng: random.Random, key: int, bpm: float, bars: int, name: str, bend: str, brng: random.Random,
                    form: str) -> tuple[Score, list[str], dict]:
    """fusion idioms poured into a song form. Sections are 8 bars; a repeated section is regenerated from the
    same seed so it comes back note for note, then its last two-bar lead phrase is varied. The B / bridge section
    modulates down a major third (the fusion reference's move) and trades the chord for the echo; the final A returns
    home with the second lead and arp instruments (the second time through, the timbre is different)."""
    sc = Score(name, f"Fusion theme ({form})", bpm, rows=16, arp=3 if bpm >= 95 else 4)
    sc.insts = [
        "inst lead pulse duty=50 env=C2 vib=2:3", "inst lead2 pulse duty=25 env=B2 vib=3:2",
        "inst arp pulse duty=25 env=90", "inst arp2 pulse duty=12 env=A0",
        "inst bass wave vol=13 shape=saw", "inst bassr wave vol=11 shape=tri",
    ]
    prog_a = rng.choice(FUSION_PROGRESSIONS)
    prog_b = rng.choice([p for p in FUSION_PROGRESSIONS if p != prog_a])
    seed_a, seed_b = rng.randrange(1 << 30), rng.randrange(1 << 30)
    if form == "aaba":
        roles = ["A", "A2", "B", "A3"]
    else:                                                        # verse-chorus: A = verse, B = chorus (lifted)
        roles = ["A", "B", "A2", "B", "C", "B2"] if bars >= 48 else ["A", "B", "A2", "B2"]
    key_b = (key + MODULATIONS[1]) % 12
    key_c = (key + MODULATIONS[2]) % 12
    meta: list[str] = []
    plan = []
    prev_top = None
    for si, role in enumerate(roles):
        b0 = si * 8
        if role.startswith("A"):
            sec_key, prog, srng = key, prog_a, random.Random(seed_a)
        elif role.startswith("B"):
            sec_key, prog, srng = (key if form != "aaba" else key_b), prog_b, random.Random(seed_b)
        else:
            sec_key, prog, srng = key_c, prog_b, random.Random(seed_b ^ 0x5A5A)
        echo = role == "B" and form == "aaba" or role == "C"
        lift = role in ("B", "B2") and form != "aaba"
        lead_inst = "lead2" if role in ("A3", "B2", "C") else "lead"
        arp_inst = "arp2" if role in ("A3", "B2", "C") else "arp"
        label = {"A": "A", "A2": "A'", "A3": "A (final)", "B": "B (middle eight)" if form == "aaba" else "chorus",
                 "B2": "chorus (final)", "C": "bridge (echo)"}[role]
        meta.append(f"{label}: bars {b0 + 1}-{b0 + 8}, key {PC_NAME[sec_key]}, "
                    + " ".join(f"{PC_NAME[(sec_key + d) % 12]}{q}" for d, q, _ in prog) + (" (echo section)" if echo else ""))
        plan.append({"section": label, "role": role, "start_bar": b0 + 1, "bars": 8, "key": PC_NAME[sec_key],
                     "chords": " ".join(f"{PC_NAME[(sec_key + d) % 12]}{q}" for d, q, _ in prog)})
        sec_prev_top = prev_top
        for ci, (deg, qual, scale_name) in enumerate(prog):
            root_pc = (sec_key + deg) % 12
            low, ivs = voice(root_pc, CHORDS[qual], 80 if lift else 72, sec_prev_top)
            sec_prev_top = low + ivs[-1]
            cname = sc.chord_name(ivs)
            scale = [(root_pc + x) % 12 for x in SCALES[scale_name]]
            chord_pcs = [(root_pc + iv) % 12 for iv in CHORDS[qual]]
            for half in range(2):
                bar = b0 + ci * 2 + half
                if echo:
                    if half == 0 and ci == 0:
                        sc.put(bar, 1, 0, f"echo:{srng.choice([4, 5, 6])},{srng.choice([3, 4])}")
                else:
                    if half == 0:
                        sc.put(bar, 1, 0, f"{midi_to_note(low)}:{cname}@{arp_inst}")
                    elif srng.random() < 0.5:
                        sc.put(bar, 1, 8, f"{midi_to_note(low + 12 if low + 12 + ivs[-1] <= 100 else low)}:{cname}")
                        sc.put(bar, 1, 15 if srng.random() < 0.3 else 12, f"{midi_to_note(low)}:{cname}")
                _fusion_bass(sc, srng, bar, root_pc, chord_pcs, scale, next_root_pc=(sec_key + prog[(ci + 1) % 4][0]) % 12,
                             last=(half == 1), accent_inst="bass" if not lift else "bassr", bend=bend)
                _fusion_drums(sc, srng, bar, fill=(bar % 8 == 7))
            lrng = random.Random(srng.randrange(1 << 30))
            if role in ("A2", "B2") and ci == 3:                 # the repeat: the last two-bar phrase is new
                lrng = random.Random(seed_a * 3 + si)
            _fusion_lead(sc, lrng, b0 + ci * 2, scale, chord_pcs, lead_inst, busy=echo or lift, bend=bend, brng=brng)
        if role == "A":
            prev_top = sec_prev_top
    sc.loop = 0
    sc.sections = [(r, i * 8, 8) for i, r in enumerate(roles)]
    info = {"form": form, "progression": "fusion", "loop_bar": 0, "plan": plan}
    return sc, [f"form {form}, {len(roles) * 8} bars; A in {PC_NAME[key]}, B in {PC_NAME[key_b if form == 'aaba' else key]}"
                + (f", bridge in {PC_NAME[key_c]}" if "C" in roles else ""), *meta], info


# ----------------------------------------------------------------------------------------------- organic layer
# What the reference corpora do that a straight generator does not (measured; docs/DESIGN_NOTES.md):
# repeats come back changed, phrases breathe, the kit fills and drops hats, a voice sits out, accents follow the
# phrase, ornaments move between repeats, density ebbs inside a section, the bass anticipates a downbeat now and
# then. `--organic 0..3` applies these moves to any generated score, deterministically; 0 leaves it byte-identical.

ARP_CELL_RE = re.compile(r"^([A-Ga-g][#b]?-?\d):([A-Za-z0-9#_]+)")
LEAD_CELL_RE = re.compile(r"^([A-Ga-g][#b]?-?\d)(@[A-Za-z_]\w*)?(.*)$")


def _bar_chord_pcs(sc: Score, bar: int) -> list[int] | None:
    """Pitch classes of the chord pulse 2 holds in `bar` (or the last one struck before it)."""
    for b in range(bar, -1, -1):
        for cell in sc.bars[b][1]:
            m = ARP_CELL_RE.match(cell)
            if m:
                ivs = CHORDS.get(m.group(2)) or sc.chords.get(m.group(2))
                if ivs:
                    root = note_to_midi(m.group(1))
                    return [(root + iv) % 12 for iv in ivs]
    return None


def _inst_volumes(sc: Score) -> dict[str, int]:
    vols = {}
    for line in sc.insts:
        m = re.match(r"inst (\w+) pulse .*?env=([0-9A-Fa-f]{2})", line)
        if m:
            vols[m.group(1)] = int(m.group(2)[0], 16)
    return vols


def apply_organic(sc: Score, level: int, rng: random.Random) -> dict[str, int]:
    """Mutate the score in place; returns a count of each move. Harmony, tempo, form and bends are untouched."""
    moves: dict[str, int] = collections.Counter()
    if level <= 0 or not sc.bars:
        return dict(moves)
    n = len(sc.bars)
    L = sc.loop
    R = sc.rows                                                   # 16, or 12 on the swing grid
    beat = R // 4
    vols = _inst_volumes(sc)
    lead_lane = lambda b: sc.bars[b][0]  # noqa: E731
    first_seen: dict[tuple, int] = {}
    repeats: dict[int, int] = {}
    for b in range(n):
        sig = tuple(lead_lane(b))
        if any(c not in (".", "-") for c in sig):
            if sig in first_seen:
                repeats[b] = first_seen[sig]
            else:
                first_seen[sig] = b
    echo_bars = {b for b in range(n) if any(c.startswith("echo:") for c in sc.bars[b][1])}

    def note_rows(cells):
        return [r for r, c in enumerate(cells) if LEAD_CELL_RE.match(c) and c not in (".", "-")]

    # 1. repeats come back changed: on the last bar of a repeated 4-bar phrase (level 1), on half of all repeated
    #    bars (level 2+): the last note moves to another chord tone, or shifts by a 16th, or trades its ornament
    for b, src in sorted(repeats.items()):
        if b < L or b in sc.protected:
            continue
        in_phrase_end = (b - L) % 4 == 3
        if not (in_phrase_end or (level >= 2 and rng.random() < 0.5)):
            continue
        cells = lead_lane(b)
        rows = note_rows(cells)
        if len(rows) < 2:
            continue
        r = rows[-1]
        m = LEAD_CELL_RE.match(cells[r])
        note, inst, mods = note_to_midi(m.group(1)), m.group(2) or "", m.group(3)
        choice = rng.random()
        pcs = _bar_chord_pcs(sc, b)
        if choice < 0.5 and pcs and "/" not in mods:
            cands = [p for d in (-4, -3, -2, -1, 1, 2, 3, 4) for p in [note + d] if p % 12 in pcs and PULSE_RANGE[0] <= p <= PULSE_RANGE[1]]
            if cands:
                cells[r] = midi_to_note(rng.choice(cands)) + inst + mods
                moves["repeat_note_changed"] += 1
                continue
        if level >= 2 and pcs and len(rows) >= 3 and rng.random() < 0.5:   # and an inner note moves too
            r2 = rows[-2]
            m2 = LEAD_CELL_RE.match(cells[r2])
            n2 = note_to_midi(m2.group(1))
            if "/" not in m2.group(3):
                c2 = [p for d in (-3, -2, -1, 1, 2, 3) for p in [n2 + d] if p % 12 in pcs and PULSE_RANGE[0] <= p <= PULSE_RANGE[1]]
                if c2:
                    cells[r2] = midi_to_note(rng.choice(c2)) + (m2.group(2) or "") + m2.group(3)
                    moves["repeat_inner_note_changed"] += 1
        if choice < 0.8 and r + 1 < R and cells[r + 1] == "." and "/" not in mods:
            cells[r + 1], cells[r] = cells[r], "."
            moves["repeat_note_shifted"] += 1
        elif "/" not in mods:
            if mods in ("", "~"):
                cells[r] = m.group(1) + inst + ("^2" if mods == "~" else "~")
            elif mods == "^2":
                cells[r] = m.group(1) + inst + "~"
            else:
                continue
            moves["repeat_ornament_swapped"] += 1
    # 2. phrase-end breaths: the last bar of a 4-bar phrase ends with air, if the phrase has already spoken; at
    #    level 2+ the second bar of a phrase breathes too (the held arrival note is released a beat early)
    breath_bars = [min(n - 1, p0 + 3) for p0 in range(L, n, 4)]
    if level >= 2:
        breath_bars += [p0 + 1 for p0 in range(L, n, 4) if p0 + 1 < n]
    for b in breath_bars:
        if b in sc.protected:
            continue
        cells = lead_lane(b)
        rows = note_rows(cells)
        if not rows or rows[-1] < R - 5 or rows[0] > R - 6:
            continue
        if rows[-1] >= R - 3:
            for r in range(R - 3, R):
                if LEAD_CELL_RE.match(cells[r]) and cells[r] not in (".", "-") and r != rows[0]:
                    cells[r] = "."
            if cells[R - 3] == ".":
                cells[R - 3] = "-"
                moves["phrase_end_breath"] += 1
        elif "-" not in cells[rows[-1] + 1:] or cells.index("-", rows[-1] + 1) >= R - 1:
            for r in range(rows[-1] + 1, R):
                if cells[r] == "-":
                    cells[r] = "."
            cells[min(R - 1, rows[-1] + 2)] = "-"
            moves["phrase_end_breath"] += 1
    # 3. the kit: a fill closes every 8-bar section; at level 2+ one bar in eight drops its off-beat hats
    fills = (["S", "s", "S", "T"], ["S", "S", "s", "S"], ["T", "T", "S", "S"], ["s", "S", "s", "S"])
    for s0 in range(L, n, 8):
        b = min(n - 1, s0 + 7)
        d = sc.bars[b][3]
        if any(c in ("T", "KT", "SC", "TT") for c in d[R - beat:R]) or sum(1 for c in d[R - beat:R] if c.startswith("S")) >= 3:
            continue
        if all(c == "." for c in d):
            continue
        for r, c in zip(range(R - beat, R), rng.choice(fills)):
            d[r] = c
        moves["section_fill"] += 1
        if level >= 2 and s0 + 2 < b:
            hb = rng.randrange(s0 + 1, b)
            dd = sc.bars[hb][3]
            dropped = 0
            for r in range(1, R, 2):
                if dd[r] in ("h", "H"):
                    dd[r] = "."
                    dropped += 1
            if dropped:
                moves["hats_dropped_bar"] += 1
    # 4. a voice sits out: level 2+, one bar in sixteen, pulse 2 rests (never the first bar of a section, never in an echo section)
    if level >= 2:
        starts = {s for _, s, _ in _section_roles(sc)} | {s + nb - 1 for _, s, nb in _section_roles(sc)}
        for s0 in range(L, n, 16):
            cands = [b for b in range(s0 + 2, min(n, s0 + 16) - 1) if b not in echo_bars and b not in starts and (b - L) % 8 not in (0, 7)]
            if not cands:
                continue
            b = rng.choice(cands)
            arp = sc.bars[b][1]
            nxt = sc.bars[b + 1][1] if b + 1 < n else None
            last_chord = None
            for bb in range(b, -1, -1):
                for c in sc.bars[bb][1]:
                    if ARP_CELL_RE.match(c):
                        last_chord = c
                        break
                if last_chord:
                    break
            if not last_chord:
                continue
            for r in range(R):
                arp[r] = "."
            arp[0] = "-"
            if nxt is not None and not any(ARP_CELL_RE.match(c) for c in nxt):
                nxt[0] = last_chord
            moves["pulse2_sits_out"] += 1
    # 5. accents follow the phrase: off-beat 8th notes two steps quieter, the phrase's first note left full
    for b in range(L, n):
        cells = lead_lane(b)
        cur = "lead"
        rows = note_rows(cells)
        for r in rows:
            m = LEAD_CELL_RE.match(cells[r])
            if m.group(2):
                cur = m.group(2)[1:]
            vol = vols.get(cur)
            if vol is None or vol < 6 or m.group(3) or m.group(2) or r % beat != beat // 2:
                continue
            if rng.random() < (0.5 if level == 1 else 0.8):
                cells[r] = m.group(1) + f"v{vol - 2}"
                moves["accent"] += 1
    # 6. density ebbs inside a section (level 3): in bars 3 and 7 of each 8 the lead drops its last short note
    if level >= 3:
        for s0 in range(L, n, 8):
            for b in (s0 + 2, s0 + 6):
                if b >= n or b in sc.protected:
                    continue
                cells = lead_lane(b)
                rows = note_rows(cells)
                if len(rows) >= 4 and (rows[-1] - rows[-2]) <= 2:
                    cells[rows[-1]] = "."
                    moves["density_ebb"] += 1
    # 7. the bass anticipates a downbeat (level 2+): one bar in sixteen, the root arrives a 16th early, as a pluck
    anticipations = []
    if level >= 2:
        for s0 in range(L, n, 16):
            cands = [b for b in range(s0 + 1, min(n, s0 + 16)) if (b - L) % 4 != 0]
            rng.shuffle(cands)
            for b in cands:
                bass, prev = sc.bars[b][2], sc.bars[b - 1][2]
                if prev[R - 1] == "." and LEAD_CELL_RE.match(bass[0]) and bass[0] not in (".", "-") and "/" not in bass[0]:
                    prev[R - 1] = bass[0]
                    bass[0] = "."
                    anticipations.append(b)
                    moves["bass_anticipation"] += 1
                    break
    # 8. timbre: a plan per lane and section, articulation pairs on one channel (the cartridges' habit, §8)
    for k, v in apply_timbre_plan(sc, level, rng, anticipations).items():
        moves[k] += v
    return dict(moves)


# instrument recipes the timbre plan can add to a score (gbc-music §8); added only when used, 15 per song at most
TIMBRE_INSTS = {
    "lead_round": "inst lead_round pulse duty=50 env=C7 vib=2:3",
    "lead_bright": "inst lead_bright pulse duty=25 env=C7 vib=2:3",
    "lead_shimmer": "inst lead_shimmer pulse duty=50,25 rate=2 env=C7 vib=2:3",
    "lead_stab": "inst lead_stab pulse duty=50 env=F3",
    "bass_b": "inst bass_b wave vol=12 shape=organ2",
    "bass_pluck": "inst bass_pluck wave vol=15 shape=tri decay=4 penv=12,1",
    "bass_alt": "inst bass_alt wave vol=12 shape=pwm50",
}
RPG_KIT = {"K": "B", "S": "Q", "s": "N", "T": "t", "C": "c"}


def _section_roles(sc: Score) -> list[tuple[str, int, int]]:
    if sc.sections:
        return list(sc.sections)
    n, L = len(sc.bars), sc.loop
    out = [("intro", 0, L)] if L else []
    roles = ("A", "B")
    for i, s0 in enumerate(range(L, n, 8)):
        out.append((roles[i % 2], s0, min(8, n - s0)))
    return out


def _lane_tag(cell: str) -> str | None:
    m = re.search(r"@([A-Za-z_]\w*)", cell)
    return m.group(1) if m else None


def _retag(cell: str, inst: str) -> str:
    m = LEAD_CELL_RE.match(cell)
    if not m or cell in (".", "-"):
        return cell
    mods = m.group(3)
    if mods.startswith("v"):          # `@name` would swallow a following `v10` (the grammar has no separator): the tag wins
        mods = re.sub(r"^v\d+", "", mods)
    return m.group(1) + "@" + inst + mods


def apply_timbre_plan(sc: Score, level: int, rng: random.Random, anticipations: list[int]) -> dict[str, int]:
    """Level 1: the lead changes colour by section (25% bright in the pre-chorus / bridge / B, the shimmer in a
    solo), the bass changes table in B-type sections (plain texture). Level 2: articulation pairs on one channel
    (a repeated lead note becomes a stab, the bass anticipation a pluck) and the RPG kit in B-type sections
    (plain texture). Switches happen on a section's first note, as the cartridges do."""
    moves: dict[str, int] = collections.Counter()
    if level <= 0:
        return dict(moves)
    n = len(sc.bars)
    have = {line.split()[1] for line in sc.insts if line.startswith("inst ")}
    fusion = any("shape=saw" in line and "vol=13" in line for line in sc.insts)   # the fusion texture's slap bass
    sections = _section_roles(sc)
    B_ROLES = {"prechorus", "bridge", "B", "S2", "C", "A2"}
    SOLO_ROLES = {"solo"}

    def ensure(inst: str) -> bool:
        if inst in have:
            return True
        if len(have) >= 15:
            return False
        sc.insts.append(TIMBRE_INSTS[inst])
        have.add(inst)
        return True

    # lead and bass by section
    cur_lead = "lead"
    for role, s0, nb in sections:
        want = "lead_bright" if role in B_ROLES else ("lead_shimmer" if role in SOLO_ROLES else None)
        bars = range(s0, min(n, s0 + nb))
        if want and ensure(want):
            first_done = False
            for b in bars:
                cells = sc.bars[b][0]
                for r, c in enumerate(cells):
                    if c in (".", "-") or not LEAD_CELL_RE.match(c):
                        continue
                    tag = _lane_tag(c)
                    if tag in ("lead", "hook", "lead2") or (not first_done and tag is None):
                        cells[r] = _retag(c, want)
                        if not first_done:
                            moves["lead_timbre_by_section"] += 1
                        first_done = True
            cur_lead = want
        else:
            # the next section must re-state its own lead: tag its first untagged note with the generator's lead
            for b in bars:
                cells = sc.bars[b][0]
                hit = False
                for r, c in enumerate(cells):
                    if c in (".", "-") or not LEAD_CELL_RE.match(c):
                        continue
                    if _lane_tag(c) is None and cur_lead not in ("lead", "hook", "lead2"):
                        cells[r] = _retag(c, "hook" if "hook" in have and role in ("chorus", "S3", "A3", "head2", "head3", "outro") else "lead")
                    hit = True
                    break
                if hit:
                    break
            cur_lead = "lead"
        if role in B_ROLES and not fusion and ensure("bass_b"):
            for b in bars:
                cells = sc.bars[b][2]
                for r, c in enumerate(cells):
                    if _lane_tag(c) in ("bass", "bassr"):
                        cells[r] = _retag(c, "bass_b")
                        moves["bass_table_by_section"] += 1
                        break
        if level >= 2 and role in B_ROLES and not fusion:
            swapped = 0
            for b in bars:
                d = sc.bars[b][3]
                for r, c in enumerate(d):
                    if c in (".", "-") or c.startswith("v"):
                        continue
                    nc = "".join(RPG_KIT.get(ch, ch) for ch in c)
                    if nc != c:
                        d[r] = nc
                        swapped += 1
            if swapped:
                moves["kit_by_section"] += 1
    # articulation pairs (level 2): a repeated lead note within a bar becomes a stab, the next note restores the lead
    if level >= 2 and ensure("lead_stab"):
        cur = "lead"
        for b in range(sc.loop, n):
            cells = sc.bars[b][0]
            idx = [r for r, c in enumerate(cells) if c not in (".", "-") and LEAD_CELL_RE.match(c)]
            for i in range(1, len(idx)):
                r0, r1 = idx[i - 1], idx[i]
                t0 = _lane_tag(cells[r0])
                if t0:
                    cur = t0
                m0, m1 = LEAD_CELL_RE.match(cells[r0]), LEAD_CELL_RE.match(cells[r1])
                if m0.group(1) == m1.group(1) and not m1.group(3) and not m0.group(3) and _lane_tag(cells[r1]) is None and rng.random() < 0.6:
                    cells[r1] = _retag(cells[r1], "lead_stab")
                    # restore on the next note (this bar or the next)
                    nxt = idx[i + 1] if i + 1 < len(idx) else None
                    if nxt is not None:
                        if _lane_tag(cells[nxt]) is None:
                            cells[nxt] = _retag(cells[nxt], cur)
                    elif b + 1 < n:
                        nc = sc.bars[b + 1][0]
                        for rr, c in enumerate(nc):
                            if c not in (".", "-") and LEAD_CELL_RE.match(c):
                                if _lane_tag(c) is None:
                                    nc[rr] = _retag(c, cur)
                                break
                    moves["lead_stab_pair"] += 1
                    cur_tag = _lane_tag(cells[r1])
                    if cur_tag:
                        pass
    # bass table alternation (level 2): the octave-bounce notes take a second table and the root restores the
    # first, the way the measured action-adventure cartridge alternates two square-in-wave widths note to note
    alt = "bassr" if (fusion and "bassr" in have) else ("bass_alt" if ensure("bass_alt") else None)
    if level >= 2 and alt:
        for b in range(sc.loop, n):
            cells = sc.bars[b][2]
            idx = [r for r, c in enumerate(cells) if c not in (".", "-") and LEAD_CELL_RE.match(c)]
            if len(idx) < 3:
                continue
            root = note_to_midi(LEAD_CELL_RE.match(cells[idx[0]]).group(1))
            cur = _lane_tag(cells[idx[0]]) or "bass"
            if cur in ("bass_pluck", alt):
                continue
            changed = 0
            for i in range(1, len(idx)):
                r = idx[i]
                m = LEAD_CELL_RE.match(cells[r])
                p = note_to_midi(m.group(1))
                tag = _lane_tag(cells[r])
                if tag and tag != alt:
                    cur = tag
                if p == root + 12 and tag is None:
                    cells[r] = _retag(cells[r], alt)
                    nxt = idx[i + 1] if i + 1 < len(idx) else None
                    if nxt is not None and _lane_tag(cells[nxt]) is None and note_to_midi(LEAD_CELL_RE.match(cells[nxt]).group(1)) != root + 12:
                        cells[nxt] = _retag(cells[nxt], cur)
                    changed += 1
            if changed:
                moves["bass_table_alternation_bars"] += 1
    # the anticipation plucks (level 2): the early root is a pluck, the bar's next bass note restores the bass
    if level >= 2 and anticipations and ensure("bass_pluck"):
        for b in anticipations:
            prev, bass = sc.bars[b - 1][2], sc.bars[b][2]
            tag = _lane_tag(prev[sc.rows - 1]) or "bass"
            prev[sc.rows - 1] = _retag(prev[sc.rows - 1], "bass_pluck")
            for r, c in enumerate(bass):
                if c not in (".", "-") and LEAD_CELL_RE.match(c):
                    if _lane_tag(c) is None:
                        bass[r] = _retag(c, tag)
                    break
            moves["bass_pluck_anticipation"] += 1
    return dict(moves)



# ----------------------------------------------------------------------------------------------- panning layer
# NR51 pans a channel hard left / right / both; mono on the handheld speaker, audible on headphones, in the WAV and
# in a two-core duet. Measured cartridges keep it static, so pans are a special effect here, opt-in (`--pan`), and
# they belong to echoes, answers and pads: never the wave bass, never the kit, everything else stays centre.
#   echo  the echo voice (pulse 2) on the right for the echo's duration, the lead on the left meanwhile (ping-pong)
#   call  call and response: the rock verse's answer bars alternate sides per phrase; the blues aab call left and
#         its answer right; a pop / chip / AABA / stage phrase group keeps the statement centre and pans the
#         restatement right and the conclusion left
#   wide  echo + call + an auto-pan (`pan=LR:10`) on the verse pad instrument only
# Applied after the organic layer on the finished score, so `--pan none` (the default) leaves every byte alone.

PAN_MODES = {
    "none": "no pans (the default; every channel centre)",
    "echo": "the echo voice right for the echo's duration, the lead left meanwhile (ping-pong echo)",
    "call": "call and response: answers / restatements on a side (rock verse alternating, blues call L answer R, pop restatement R conclusion L)",
    "wide": "echo + call + an LR auto-pan on the verse pad",
}
PAN_AUTO_PAD = 10   # frames per side for the wide mode's verse pad


def _pan_first_note(flat: list[str], start: int, end: int) -> int | None:
    for r in range(start, min(end, len(flat))):
        c = flat[r]
        if c not in (".", "-") and LEAD_CELL_RE.match(c):
            return r
    return None


def _pan_mark(flat: list[str], r: int, marker: str) -> str:
    """Put a pan marker at (or just before) the note at row r of a flattened lane. Returns how it was placed:
    on the note itself when it carries no effect; on the row before when that row is empty (the switch lands one
    16th early); on the next effect-free note of the phrase; or on the note with its ornament dropped."""
    m = LEAD_CELL_RE.match(flat[r])
    if m and not m.group(3):
        flat[r] = flat[r] + marker
        return "on_note"
    if r > 0 and flat[r - 1] == ".":
        flat[r - 1] = marker
        return "row_before"
    for r2 in range(r + 1, min(len(flat), r + 4)):
        m2 = LEAD_CELL_RE.match(flat[r2])
        if m2 and flat[r2] not in (".", "-") and not m2.group(3):
            flat[r2] = flat[r2] + marker
            return "later_note"
    if m:
        flat[r] = m.group(1) + (m.group(2) or "") + marker
        return "ornament_dropped"
    return "skipped"


def apply_pan(sc: Score, mode: str, style: str) -> dict:
    """Mutate the score in place per PAN_MODES; returns a report. Notes, rhythm, harmony and timing are untouched:
    the layer only appends `<` `>` `^` markers, echo sides and (wide) a second pad instrument."""
    rep: dict = {"mode": mode, "events": 0, "marks": collections.Counter(), "echo_sides": 0, "pad_auto": False}
    if mode == "none" or not sc.bars:
        return rep
    if mode not in PAN_MODES:
        raise ScoreError(f"unknown pan mode {mode!r}; modes: {', '.join(PAN_MODES)}")
    rows, n = sc.rows, len(sc.bars)
    want_echo, want_call, want_wide = mode in ("echo", "wide"), mode in ("call", "wide"), mode == "wide"
    targets: dict[int, str] = {}                 # lead row -> side marker, applied in row order, no-ops dropped
    echo_spans: list[tuple[int, int]] = []       # lead rows inside an echo (the lead stays left there)

    def phrase_target(bar: int, marker: str) -> None:
        r = _pan_first_note(flat, bar * rows, min(n, bar + 2) * rows)
        if r is not None and not any(a <= r < b for a, b in echo_spans):
            targets.setdefault(r, marker)

    flat = [c for b in sc.bars for c in b[0]]
    sections = _section_roles(sc) if sc.sections else []
    # ---- echo: the echo voice right, the lead left, for the echo's duration
    if want_echo:
        for b in range(n):
            arp = sc.bars[b][1]
            for r, c in enumerate(arp):
                if c.startswith("echo:") and c != "echo:off" and not re.search(r",[LRClrc]$", c):
                    arp[r] = c + ",R"
                    rep["echo_sides"] += 1
                    # the lead goes left from this row until the echo ends (echo:off or a real pulse-2 note)
                    start = b * rows + r
                    end = n * rows
                    for b2 in range(b, n):
                        for r2, c2 in enumerate(sc.bars[b2][1]):
                            if b2 * rows + r2 <= start:
                                continue
                            if c2 == "echo:off" or ARP_CELL_RE.match(c2) or (c2 not in (".", "-") and LEAD_CELL_RE.match(c2)):
                                end = b2 * rows + r2
                                break
                        if end < n * rows:
                            break
                    echo_spans.append((start, end))
                    r_on = _pan_first_note(flat, start, end)
                    if r_on is not None:
                        targets.setdefault(r_on, "<")
                    r_off = _pan_first_note(flat, end, n * rows)
                    if r_off is not None:
                        targets.setdefault(r_off, "^")
    # ---- call and response, by section role
    if want_call and sections:
        for role, s0, nb in sections:
            if role == "verse" and style == "rock":          # the riff speaks (centre), the lead answers in bar 2 of each phrase: sides alternate
                for k in range(nb // 2):
                    phrase_target(s0 + 2 * k, ">" if k % 2 == 0 else "<")
            elif role in ("verse", "A", "A2", "A3", "S1", "S2", "S3"):   # statement C, restatement R, departure C, conclusion L
                for k, marker in enumerate(("^", ">", "^", "<")):
                    if 2 * k < nb:
                        phrase_target(s0 + 2 * k, marker)
            elif role in ("head", "head2", "head3"):          # aab: the call left (bars 1-2, 5-6), the answer right (9-10), the lick centre
                phrase_target(s0, "<")
                phrase_target(s0 + 8, ">")
                phrase_target(s0 + 10, "^")
            else:                                             # every other section starts centre
                phrase_target(s0, "^")
    # ---- apply the lead targets in row order; a marker that repeats the current side is dropped
    cur = "^"
    for r in sorted(targets):
        marker = targets[r]
        if marker == cur:
            continue
        how = _pan_mark(flat, r, marker)
        rep["marks"][how] += 1
        if how != "skipped":
            cur = marker
            rep["events"] += 1
    for b in range(n):
        sc.bars[b][0] = flat[b * rows:(b + 1) * rows]
    rep["events"] += rep["echo_sides"]
    # ---- wide: the verse pad alternates sides every PAN_AUTO_PAD frames (a texture, pads only)
    if want_wide and sections:
        pad_line = next((ln for ln in sc.insts if ln.startswith("inst pad ")), None)
        verse_bars = [b for role, s0, nb in sections if role == "verse" for b in range(s0, min(n, s0 + nb))]
        if pad_line and verse_bars and len(sc.insts) < 15:
            sc.insts.append(pad_line.replace("inst pad ", "inst padlr ", 1) + f" pan=LR:{PAN_AUTO_PAD}")
            for b in verse_bars:
                arp = sc.bars[b][1]
                for r, c in enumerate(arp):
                    if "@pad" in c and "@padlr" not in c:
                        arp[r] = c.replace("@pad", "@padlr")
                        rep["pad_auto"] = True
    rep["marks"] = dict(rep["marks"])
    return rep

# ----------------------------------------------------------------------------------------------- grooves and syncopation
# Rhythm as a knob of its own: a groove supplies the kit, the bass rhythm, the pulse-2 stab rhythm and the hook
# rhythm bank for every section style the form composer asks for; --syncopation sets how many anticipations,
# off-beat pushes and strong-beat rests the hook, the bass and the kick/snare get. `straight` at level 0 is the
# generator as it was (byte-identical). The syncopation index below is the Longuet-Higgins & Lee (1984) measure
# on the row grid (a note on a weak position followed by a rest or a tie on a stronger one scores the weight
# difference); the groove research (medium syncopation in the kit and bass gives the strongest urge to move) and
# the reference-corpus bands are in docs/DESIGN_NOTES.md. Research notes: research_notes/syncopation/.
#
# Patterns are given on the groove's own grid: 16 rows per bar (sixteenths) or 12 (triplet eighths: swing and
# shuffle; `rows: 12` + `beats: 4` in the score header). Kit cells are drum letters, bass patterns are
# (rows, semitones from the chord root, cut frames), stab patterns are rows for the chord voice. A groove's
# patterns are written at its native syncopation level; `_level_rows` straightens them for a lower level and the
# generic pushes of `syncopate_*` add to them for a higher one.

GROOVES = {
    "straight": {
        "desc": "the kit, bass and hook rhythms as before: kick 1 and 3, snare 2 and 4, 8th hats (every form and texture)",
        "rows": 16, "bpm": (90, 160), "bpm_default": 100, "sync": 0, "stab_inst": None,
    },
    "swing": {
        "desc": "jazz swing on a triplet grid (rows: 12): ride on the beat and the late 8th, snare 2 and 4, walking quarter bass, chord comping on 2 and 4 or the Charleston figure",
        "rows": 12, "bpm": (100, 200), "bpm_default": 140, "sync": 1, "stab_inst": "inst comp pulse duty=25 env=A2",
        "kit": {
            "hats":     "H . h H . h H . h H . h",
            "backbeat": "KH . h SH . h kH . h SH . h",
            "build":    "KH h h SH h h KH h h SH h h",
            "full":     "KH . h SH . O KH . h SH . O",
            "half":     "K . . S . . . . . S . .",
            "shuffle":  "KH . h SH . h KH . h SH . h",
            "fill":     "S s T",
        },
        "bass": {
            "quarters": ((0, 3, 6, 9), (0, 7, 12, 7), 6),
            "eighths":  ((0, 3, 6, 9), (0, 4, 7, 9), 6),
            "bounce":   ((0, 3, 6, 9), (0, 7, 12, 10), 6),
            "walk":     ((0, 3, 6, 9), (0, 2, 4, 5), 6),
            "hold":     ((0, 6), (0, 7), 0),
            "riff":     ((0, 3, 6, 9), (0, 4, 7, 9), 6),
            "boogie":   ((0, 2, 3, 5, 6, 8, 9, 11), (0, 0, 4, 4, 7, 7, 9, 9), 4),
        },
        "stab": {"pad": (3, 9), "full": (0, 5, 9), "stab": (3, 9)},
        "hooks": ("swing_a", "swing_b", "swing_c"), "verse_hooks": ("swing_a", "swing_c"),
    },
    "shuffle": {
        "desc": "blues / boogie shuffle on the triplet grid (rows: 12): kick 1 and 3, snare 2 and 4, hats on the beat and the late 8th, boogie bass, 7th stabs on the late 8ths",
        "rows": 12, "bpm": (80, 140), "bpm_default": 112, "sync": 1, "stab_inst": "inst comp pulse duty=25 env=A2",
        "kit": {
            "hats":     "H . h H . h H . h H . h",
            "backbeat": "KH . h SH . h KH . h SH . h",
            "build":    "KH h h SH h h KH h h SH h h",
            "full":     "KH . h SH . h KH . O SH . h",
            "half":     "K . . S . . K . . S . .",
            "shuffle":  "KH . h SH . h KH . h SH . h",
            "fill":     "S s T",
        },
        "bass": {
            "quarters": ((0, 3, 6, 9), (0, 0, 7, 7), 6),
            "eighths":  ((0, 2, 3, 5, 6, 8, 9, 11), (0, 0, 4, 4, 7, 7, 9, 9), 4),
            "bounce":   ((0, 2, 3, 5, 6, 8, 9, 11), (0, 12, 0, 12, 7, 12, 7, 12), 3),
            "walk":     ((0, 3, 6, 9), (0, 4, 7, 10), 6),
            "hold":     ((0, 6), (0, 7), 0),
            "riff":     ((0, 2, 3, 5, 6, 8, 9, 11), (0, 0, 4, 4, 7, 7, 10, 10), 4),
            "boogie":   ((0, 2, 3, 5, 6, 8, 9, 11), (0, 0, 4, 4, 7, 7, 9, 9), 4),
        },
        "stab": {"pad": (2, 8), "full": (2, 5, 8, 11), "stab": (3, 9)},
        "hooks": ("shuffle_a", "shuffle_b", "swing_c"), "verse_hooks": ("shuffle_a", "swing_c"),
    },
    "ska": {
        "desc": "ska: fast 4/4 with the skank (chord chops on every off-8th), walking bass, kick 1 and 3, cross-stick snare 2 and 4 (full snare and open hats in the chorus), one-drop bridge, stop-time fill",
        "rows": 16, "bpm": (150, 185), "bpm_default": 168, "sync": 2, "stab_inst": "inst skank pulse duty=25 env=B1",
        "kit": {
            "hats":     "K . h . . . h . K . h . . . h .",
            "backbeat": "K . h . s . h . K . h . s . h .",
            "build":    "KH h h h SH h h h KH h h h SH h h h",
            "full":     "KH . O . KS . O . KH . O . KS . O s",
            "half":     ". . h . . . h . KS . h . . . h .",
            "shuffle":  "KH . O . KS . O . KH . O . KS . O s",
            "fill":     "S . S T",
        },
        "bass": {
            "quarters": ((0, 4, 8, 12), (0, 4, 7, 9), 8),
            "eighths":  ((0, 4, 8, 12, 14), (0, 4, 7, 9, 12), 7),
            "bounce":   ((0, 2, 4, 6, 8, 10, 12, 14), (0, 12, 4, 12, 7, 12, 9, 7), 4),
            "walk":     ((0, 4, 8, 12), (0, 2, 4, 5), 8),
            "hold":     ((0, 8), (0, 7), 0),
            "riff":     ((0, 4, 8, 12, 14), (0, 4, 7, 9, 12), 7),
            "boogie":   ((0, 2, 4, 6, 8, 10, 12, 14), (0, 0, 4, 4, 7, 7, 9, 9), 4),
        },
        "stab": {"pad": (2, 6, 10, 14), "full": (2, 6, 10, 14), "stab": (2, 6, 10, 14)},
        "hooks": ("ska_horn", "ska_push", "ska_stop"), "verse_hooks": ("ska_horn", "ska_stop"),
    },
    "onedrop": {
        "desc": "reggae one-drop: beat 1 empty, kick and rim-click together on beat 3, the skank on 2 and 4, a sparse bass that leans on the and-of-2, slow",
        "rows": 16, "bpm": (65, 90), "bpm_default": 76, "sync": 2, "stab_inst": "inst skank pulse duty=25 env=A1",
        "kit": {
            "hats":     ". . h . . . h . . . h . . . h .",
            "backbeat": ". . h . . . h . KS . h . . . h .",
            "build":    ". h h h S h h h KS h h h S h h h",
            "full":     ". . h . . . O . KS . h . . . O s",
            "half":     ". . . . . . . . KS . . . . . . .",
            "shuffle":  ". . h . . . h . KS . h . . . h .",
            "fill":     "S . s S",
        },
        "bass": {
            "quarters": ((0, 8), (0, 0), 0),
            "eighths":  ((0, 6, 10), (0, 7, 0), 0),
            "bounce":   ((0, 3, 6, 10, 12), (0, 12, 7, 0, 5), 0),
            "walk":     ((0, 6, 8, 12), (0, 4, 7, 9), 0),
            "hold":     ((0, 8), (0, 7), 0),
            "riff":     ((0, 6, 10), (0, 7, 0), 0),
            "boogie":   ((0, 6, 10), (0, 7, 0), 0),
        },
        "stab": {"pad": (4, 12), "full": (4, 12), "stab": (4, 12)},
        "hooks": ("drop_lazy", "drop_a", "drop_b"), "verse_hooks": ("drop_lazy",),
    },
    "funk": {
        "desc": "funk: hit the one, sixteenth-note kicks and ghost snares, hats on every 16th, a 16th-syncopated bass with octave pops, chord chanks on the off-beats",
        "rows": 16, "bpm": (90, 115), "bpm_default": 104, "sync": 2, "stab_inst": "inst chank pulse duty=25 env=B1",
        "kit": {
            "hats":     "H h H h H h H h H h H h H h H h",
            "backbeat": "KH h H sh SH h Kh h H h Kh sh SH h H sh",
            "build":    "KH h h h SH h h h KH h h h SH h h h",
            "full":     "KH h H sh SH h Kh h KH h Kh sh SH h H sh",
            "half":     "K . . . . . . s S . . . . . . .",
            "shuffle":  "KH h H sh SH h Kh h KH h Kh sh SH h H sh",
            "fill":     "S s S s",
        },
        "bass": {
            "quarters": ((0, 8), (0, 0), 6),
            "eighths":  ((0, 3, 6, 7, 10, 12, 14), (0, 0, 12, 10, 7, 0, 12), 3),
            "bounce":   ((0, 3, 6, 7, 10, 11, 14), (0, 12, 0, 12, 10, 12, 7), 3),
            "walk":     ((0, 3, 6, 10, 12, 14), (0, 0, 10, 7, 0, 10), 3),
            "hold":     ((0, 6), (0, 0), 0),
            "riff":     ((0, 3, 6, 7, 10, 12, 14), (0, 0, 12, 10, 7, 0, 12), 3),
            "boogie":   ((0, 3, 6, 7, 10, 12, 14), (0, 0, 12, 10, 7, 0, 12), 3),
        },
        "stab": {"pad": (2, 12), "full": (2, 6, 11, 14), "stab": (2, 12)},
        "hooks": ("funk_a", "funk_b", "funk_c"), "verse_hooks": ("funk_a", "funk_c"),
    },
    "dance": {
        "desc": "four-on-the-floor dance pop: kick on every beat, clap on 2 and 4, open hat on every off-8th, octave bass on the 8ths, chord stabs on the off-beats",
        "rows": 16, "bpm": (118, 130), "bpm_default": 124, "sync": 1, "stab_inst": "inst stab pulse duty=25 env=A1",
        "kit": {
            "hats":     "K . O . K . O . K . O . K . O .",
            "backbeat": "K . O . KS . O . K . O . KS . O .",
            "build":    "KH h h h KS h h h KH h h h KS h h h",
            "full":     "K . O . KS . O . K . O . KS . O s",
            "half":     "K . . . S . . . K . . . S . . .",
            "shuffle":  "K . O . KS . O . K . O . KS . O s",
            "fill":     "S S S S",
        },
        "bass": {
            "quarters": ((0, 4, 8, 12), (0, 0, 0, 0), 6),
            "eighths":  ((0, 2, 4, 6, 8, 10, 12, 14), (0, 12, 0, 12, 0, 12, 0, 12), 4),
            "bounce":   ((0, 2, 4, 6, 8, 10, 12, 14), (0, 12, 0, 12, 7, 12, 0, 12), 4),
            "walk":     ((0, 2, 4, 6, 8, 10, 12, 14), (0, 12, 0, 12, 0, 12, 0, 12), 4),
            "hold":     ((0, 8), (0, 0), 0),
            "riff":     ((0, 2, 4, 6, 8, 10, 12, 14), (0, 12, 0, 12, 0, 12, 0, 12), 4),
            "boogie":   ((0, 2, 4, 6, 8, 10, 12, 14), (0, 12, 0, 12, 0, 12, 0, 12), 4),
        },
        "stab": {"pad": (2, 10), "full": (2, 6, 10, 14), "stab": (2, 6, 10, 14)},
        "hooks": ("dance_a", "dance_b", "straight"), "verse_hooks": ("dance_a", "long"),
    },
    "tropical": {
        "desc": "a 2010s pop hit single (tropical-house / dancehall-pop): ~100 bpm, the dembow kick and snare (kick 1 and 3, snare on the and-of-2 and 4), a tresillo bass, a sparse verse that hints the hook's rhythm, a pre-chorus build, the chorus carried by an off-beat plucked hook",
        "rows": 16, "bpm": (95, 110), "bpm_default": 100, "sync": 2, "stab_inst": "inst pluck2 pulse duty=12 env=B2",
        "kit": {
            "hats":     ". . h . . . h . . . h . . . h .",
            "backbeat": "K . h . . . h . . . h . S . h .",
            "build":    "K h h h S h h h K h h h S h h h",
            "full":     "KH . h . . . SH . KH . h . SH . h s",
            "half":     "K . . . . . . . . . . . S . . .",
            "shuffle":  "KH . h . . . SH . KH . h . SH . h s",
            "fill":     "S . S s",
        },
        "bass": {
            "quarters": ((0,), (0,), 0),
            "eighths":  ((0, 12), (0, 0), 0),
            "bounce":   ((0, 6, 12), (0, 0, 7), 0),
            "walk":     ((0, 6, 12), (0, 7, 12), 0),
            "hold":     ((0,), (0,), 0),
            "riff":     ((0, 6, 12), (0, 0, 7), 0),
            "boogie":   ((0, 6, 12), (0, 0, 7), 0),
        },
        "stab": {"pad": "hook", "full": "hook", "stab": "hook"},
        "hooks": ("trop_hook", "trop_pluck", "trop_late"), "verse_hooks": ("trop_late", "long"),
    },
    "latin": {
        "desc": "latin / flamenco tresillo (a desert-stage theme from a 1998 console adventure): a straight kit, bass on the beats, chord strums on the 3-3-2 cell (rows 0, 6, 12), hook rhythms built on the tresillo",
        "rows": 16, "bpm": (100, 140), "bpm_default": 120, "sync": 2, "stab_inst": "inst strum pulse duty=25 env=B2",
        "kit": {
            "hats":     ". . h . . . h . . . h . . . h .",
            "backbeat": "K . h . S . h . K . h . S . h .",
            "build":    "K h h h S h h h K h h h S h h h",
            "full":     "KH . h . SH . Kh . KH . h . SH . h s",
            "half":     "K . . . . . . . S . . . . . . .",
            "shuffle":  "KH . h . SH . Kh . KH . h . SH . h s",
            "fill":     "S s T T",
        },
        "bass": {
            "quarters": ((0, 4, 8, 12), (0, 0, 7, 7), 6),
            "eighths":  ((0, 4, 8, 12, 14), (0, 0, 7, 7, 12), 6),
            "bounce":   ((0, 6, 8, 12, 14), (0, 12, 0, 7, 12), 4),
            "walk":     ((0, 4, 8, 12), (0, 2, 4, 5), 6),
            "hold":     ((0, 8), (0, 7), 0),
            "riff":     ((0, 6, 8, 12, 14), (0, 12, 0, 7, 12), 4),
            "boogie":   ((0, 4, 8, 12, 14), (0, 0, 7, 7, 12), 6),
        },
        "stab": {"pad": (0, 6, 12), "full": (0, 6, 12, 14), "stab": (0, 6, 12)},
        "hooks": ("latin_a", "latin_b", "latin_c"), "verse_hooks": ("latin_b", "long"),
    },
    "halftime": {
        "desc": "half-time riff rock (a late-1960s rock single): the snare on 3 only, kick on 1 with a push, 8th hats, a one-bar blues riff on the bass doubled as chord hits on pulse 2, the riff transposed with the chord",
        "rows": 16, "bpm": (100, 125), "bpm_default": 112, "sync": 1, "stab_inst": "inst riffhit pulse duty=50 env=A1",
        "kit": {
            "hats":     "H . h . H . h . H . h . H . h .",
            "backbeat": "KH . h . h . h . SH . h . h . h .",
            "build":    "KH h h h SH h h h KH h h h SH h h h",
            "full":     "KH . h . h . Kh . SH . h . h . h O",
            "half":     "K . . . . . . . S . . . . . . .",
            "shuffle":  "KH . h . h . Kh . SH . h . h . h O",
            "fill":     "T T S S",
        },
        "bass": {
            "quarters": ((0, 8), (0, 0), 0),
            "eighths":  ((0, 3, 6, 8, 11, 12, 14), (0, 0, 10, 0, 7, 5, 3), 4),
            "bounce":   ((0, 3, 6, 8, 11, 12, 14), (0, 12, 10, 0, 7, 5, 3), 4),
            "walk":     ((0, 4, 8, 12), (0, 3, 5, 6), 6),
            "hold":     ((0, 8), (0, 7), 0),
            "riff":     ((0, 3, 6, 8, 11, 12, 14), (0, 0, 10, 0, 7, 5, 3), 4),
            "boogie":   ((0, 3, 6, 8, 11, 12, 14), (0, 0, 10, 0, 7, 5, 3), 4),
        },
        "stab": {"pad": (0, 8), "full": (0, 3, 6, 8, 11, 12), "stab": (0, 8)},
        "hooks": ("half_a", "half_b", "long"), "verse_hooks": ("long", "half_a"),
    },
}
# hook rhythm banks the grooves draw from (two-bar motifs on the groove's grid; the 16-row ones join RHYTHMS)
GROOVE_RHYTHMS = {
    # ska horn lines: punchy, on the beat with pushes on the and-of-4 (stop-time at the end of the second bar)
    "ska_horn":  (0, 2, 4, 8, 12, 14, 18, 20, 24, 28),
    "ska_push":  (0, 2, 4, 8, 10, 15, 18, 22, 24, 26, 31),
    "ska_stop":  (0, 4, 6, 8, 12, 14, 20, 22, 24),
    # one-drop: lazy entries after the beat
    "drop_lazy": (2, 6, 8, 12, 18, 22, 24),
    "drop_a":    (2, 4, 6, 10, 12, 18, 20, 22, 26, 28),
    "drop_b":    (0, 6, 8, 10, 14, 16, 22, 24, 26),
    # funk: the one, then 16th pushes
    "funk_a":    (0, 3, 6, 10, 12, 15, 19, 22, 26, 28),
    "funk_b":    (0, 3, 6, 8, 11, 14, 16, 19, 22, 24, 27, 30),
    "funk_c":    (0, 6, 7, 10, 12, 16, 22, 23, 26, 28),
    # dance pop: on the beat with off-8th pushes
    "dance_a":   (0, 4, 6, 8, 12, 14, 16, 20, 22, 24, 28),
    "dance_b":   (0, 2, 4, 8, 10, 12, 16, 18, 20, 24, 26, 28),
    # tropical / dancehall pop: off-beat plucks, the tresillo (3-3-2) cell, anticipations of the downbeat
    "trop_hook": (2, 4, 6, 10, 12, 15, 18, 20, 22, 26, 28, 31),
    "trop_pluck": (0, 3, 6, 8, 11, 14, 16, 19, 22, 24, 28),
    "trop_late": (2, 6, 8, 12, 15, 18, 22, 24, 28, 31),
    # latin: the tresillo cell (0 3 6 in 8ths = rows 0, 6, 12) and dotted-8th figures; halftime: the riff's answer
    "latin_a":   (0, 3, 6, 8, 12, 14, 16, 19, 22, 24, 28, 30),
    "latin_b":   (0, 6, 8, 12, 15, 18, 22, 24, 28, 31),
    "latin_c":   (2, 6, 8, 11, 14, 16, 22, 24, 27, 30),
    "half_a":    (0, 2, 4, 8, 10, 12, 16, 20, 24, 28),
    "half_b":    (0, 3, 6, 8, 12, 16, 19, 22, 24, 28),
    # 12-row grid (swing / shuffle): rows 0..23, three rows per beat, row % 3 == 2 is the late (swung) 8th
    "swing_a":   (0, 2, 3, 5, 6, 9, 12, 14, 15, 18, 21),
    "swing_b":   (0, 3, 5, 6, 8, 9, 12, 15, 17, 18, 20),
    "swing_c":   (0, 2, 5, 6, 12, 14, 17, 18),
    "long12":    (0, 3, 6, 10, 12, 15, 18),
    "call12":    (0, 2, 3, 6, 8, 9),
    "answer12":  (12, 14, 15, 18, 20, 21),
    "shuffle_a": (0, 2, 3, 6, 8, 9, 12, 14, 15, 18),
    "shuffle_b": (0, 3, 5, 6, 9, 11, 12, 15, 17, 18, 21),
}
RHYTHMS.update(GROOVE_RHYTHMS)
# extra instruments a groove adds to the form composer's set (flavour-independent)
GROOVE_INSTS = {
    "tropical": ["inst pluck pulse duty=25 env=E3 penv=12,1"],   # the marimba / steel-pan-like pluck the chorus hook plays on
}
SYNCOPATION_LEVELS = {
    0: "straight: kick, snare, bass and hook on the beats (a groove's patterns are straightened to the beat grid), no anticipation",
    1: "the 8th grid: the kick on the and-of-3, the bass pushes the next chord's root an 8th early, the hook anticipates its second-bar downbeat by a 16th",
    2: "medium (the groove research's sweet spot; the native level of ska, one-drop, funk, latin and the pop-hit groove): the groove's 16th pushes, a ghost snare before beat 3, the bass leans on the and-of-2, the hook pushes beat 3 to the and-of-2 and takes a pickup before bar 1",
    3: "funk: + ghost snares on the off-16ths, bass pops on the off-16ths, the hook's beats 2 and 4 move to off-16ths. A groove starts from its own level: each step above it adds the next push, each step below straightens its patterns",
}


def groove_rows(groove: str) -> int:
    return GROOVES[groove]["rows"]


def metric_weights(rows: int, beats: int = 4) -> list[int]:
    """Longuet-Higgins & Lee metric weights for one bar: 0 on the downbeat, -1 at the half bar, -2 on the other
    beats, -3 on the 8ths (or the triplet subdivisions of a 12-row bar), -4 on the 16ths."""
    rpb = max(1, rows // max(1, beats))
    out = []
    for r in range(rows):
        if r == 0:
            out.append(0)
        elif beats % 2 == 0 and r == rows // 2:
            out.append(-1)
        elif r % rpb == 0:
            out.append(-2)
        elif rpb % 2 == 0 and r % (rpb // 2) == 0:
            out.append(-3)
        else:
            out.append(-4 if rpb % 2 == 0 and rpb > 2 else -3)
    return out


def syncopation_index(onsets: list[int], n_bars: int, rows: int, beats: int = 4) -> float:
    """LHL syncopation per bar over a loop: for every onset, the strongest rest or tied position before the next
    onset (circular) that outweighs it scores the weight difference; the sum is divided by the number of bars.
    `onsets` are absolute rows (bar * rows + row) inside the loop."""
    if not onsets or n_bars <= 0:
        return 0.0
    w = metric_weights(rows, beats)
    total_rows = n_bars * rows
    ons = sorted(set(o % total_rows for o in onsets))
    on_set = set(ons)
    score = 0
    for i, o in enumerate(ons):
        nxt = ons[(i + 1) % len(ons)]
        gap = (nxt - o) % total_rows
        if gap <= 1:
            continue
        best = None
        for k in range(1, gap):
            p = (o + k) % total_rows
            if p in on_set:
                break
            wp = w[p % rows]
            if best is None or wp > best:
                best = wp
        if best is not None and best > w[o % rows]:
            score += best - w[o % rows]
    return round(score / n_bars, 2)


_KICK_SNARE = set("KSksBQPND")
_ONSET_RE = re.compile(r"^[A-Ga-g][#b]?-?\d")


def score_syncopation(sc: "Score") -> dict:
    """{lead, chords, bass, drums, offbeat_*} of a generated score over its loop region: the LHL index per bar per
    lane (chords = pulse 2's strikes: the skank lives there; drums = kick and snare letters only, hats are texture,
    not syncopation) and the share of each lane's onsets off the beat."""
    R, L, n = sc.rows, sc.loop, len(sc.bars)
    beats = getattr(sc, "beats", 4)
    rpb = max(1, R // beats)
    bars = range(L, n)
    nb = max(1, n - L)
    out = {}
    for lane, key in ((0, "lead"), (1, "chords"), (2, "bass")):
        ons = [(b - L) * R + r for b in bars for r, c in enumerate(sc.bars[b][lane]) if _ONSET_RE.match(c)]
        out[key] = syncopation_index(ons, nb, R, beats)
        out["offbeat_" + key] = round(sum(1 for o in ons if (o % R) % rpb != 0) / len(ons), 2) if ons else 0.0
    ons = [(b - L) * R + r for b in bars for r, c in enumerate(sc.bars[b][3]) if c not in (".", "-") and not c.startswith("v") and any(ch in _KICK_SNARE for ch in c)]
    out["drums"] = syncopation_index(ons, nb, R, beats)
    out["offbeat_drums"] = round(sum(1 for o in ons if (o % R) % rpb != 0) / len(ons), 2) if ons else 0.0
    return out


def song_syncopation(song: "Song") -> dict:
    """The same measure on a parsed score (compile / events side)."""
    sc = Score(song.name, song.title, song.bpm, rows=song.rows, loop=song.loop)
    sc.beats = getattr(song, "beats", 4)
    n = max(song.bars) + 1
    for b in range(n):
        lanes = song.bars.get(b, {})
        for lane in range(4):
            sc.bar(b)[lane] = list(lanes.get(lane) or ["."] * song.rows)
    return score_syncopation(sc)


def _level_rows(rows: tuple[int, ...], grid: int, R: int) -> list[int]:
    """Straighten a pattern's rows onto a grid (the beat, or the 8th): an onset off the grid moves to the next
    grid position (a push becomes the beat it pushed into); one that lands on an occupied cell or past the
    pattern is dropped."""
    out: list[int] = []
    for r in rows:
        t = r if r % grid == 0 else (r // grid + 1) * grid
        if t not in out and t < 2 * R:
            out.append(t)
    return sorted(out)


def level_grid(level: int, R: int, kit: bool = False) -> int | None:
    """The grid a groove's pattern is straightened to when the asked level is below the groove's own: the beats
    at level 0, the 8ths at level 1, untouched from 2 (the groove's 16th pushes belong to level 2 and up). On the
    12-row grid the 8th grid is the beat: the late triplet row is the swing itself."""
    beat = max(1, R // 4)
    eighth = beat // 2 if beat % 2 == 0 else beat
    if level >= 2:
        return None
    return beat if level <= 0 else eighth


def syncopate_motif(motif: list[tuple[int, int]], level: int, rng: random.Random, R: int = 16) -> list[tuple[int, int]]:
    """Generic pushes for the lead (hook) motif, on top of the bank rhythm. Level 1: the second-bar downbeat is
    anticipated by a 16th (one row). Level 2: + a pickup before bar 1 (row -1, written into the previous bar) and
    beat 3 of each bar pushed to the and-of-2. Level 3: + beats 2 and 4 move to the off-16th before or after.
    Rows stay unique and sorted; degrees are untouched, so the melody is the same, only its placement moves."""
    if level <= 0 or not motif:
        return list(motif)
    beat = max(1, R // 4)
    half = beat // 2 if beat % 2 == 0 else beat - 1          # an 8th on the 16-grid, the late triplet row on the 12-grid
    rows = {r: d for r, d in motif}

    def move(src: int, dst: int) -> None:
        if src in rows and dst not in rows and -1 <= dst < 2 * R:
            rows[dst] = rows.pop(src)

    move(R, R - 1)
    if level >= 2:
        move(0, -1)
        for bar0 in (0, R):
            move(bar0 + R // 2, bar0 + R // 2 - half)
    if level >= 3:
        for r in (beat, 3 * beat, R + beat, R + 3 * beat):
            move(r, r + 1 if rng.random() < 0.5 else r - 1)
    return sorted(rows.items())


def syncopate_bass_cells(cells: list[str], level: int, R: int, next_root: int | None, root: int) -> None:
    """Generic pushes on a rendered bass bar (in place): level 1 pushes the next chord's root an 8th early when
    the chord changes; level 2 moves the beat-3 note to the and-of-2 when that cell is free; level 3 adds
    staccato octave pops on the off-16ths after beats 2 and 4."""
    if level <= 0:
        return
    beat = max(1, R // 4)
    half = beat // 2 if beat % 2 == 0 else beat - 1
    if next_root is not None and next_root != root and cells[R - half] == "." and WAVE_RANGE[0] <= next_root <= WAVE_RANGE[1]:
        cells[R - half] = f"{midi_to_note(next_root)}!{max(3, 2 * half)}"
        if cells[R - 1] not in (".", "-"):
            cells[R - 1] = "."
    if level >= 2:
        r = R // 2
        if cells[r] not in (".", "-") and cells[r - half] == "." and all(c == "." for c in cells[r - half + 1:r]):
            cells[r - half], cells[r] = cells[r], "."
    if level >= 3 and beat >= 4:
        for r in (beat + 1, 3 * beat + 1):
            if r < R and cells[r] == "." and cells[r - 1] != "." and cells[r + 1 if r + 1 < R else r] == ".":
                pop = root + 12
                if pop <= WAVE_RANGE[1]:
                    cells[r] = f"{midi_to_note(pop)}!3"


def syncopate_kit_cells(cells: list[str], level: int, R: int) -> None:
    """Generic pushes on a rendered drum bar (in place, 16-row grid only): level 1 adds the and-of-3 kick, level 2
    a ghost snare on the 16th before beat 3, level 3 ghost snares on the off-16ths after beats 2 and 4."""
    if level < 1 or R != 16:
        return
    if cells[10] in (".", "h", "H"):
        cells[10] = "Kh" if cells[10] != "." else "K"
    if level >= 2 and cells[7] in (".", "h"):
        cells[7] = "sh" if cells[7] == "h" else "s"
    if level >= 3:
        for r in (5, 13):
            if cells[r] in (".", "h"):
                cells[r] = "sh" if cells[r] == "h" else "s"


def _render_bass_pattern(pattern: tuple, root: int, level: int, native: int, R: int) -> list[str]:
    """(rows, semitones, cut) -> cells, straightened when the asked level is below the groove's native level."""
    rows, semis, cut = pattern
    place = dict(zip(rows, semis))
    grid = level_grid(level, R) if level < native else None
    if grid:
        kept = _level_rows(tuple(rows), grid, R)
        place = {r: place.get(r, place[min(rows, key=lambda x: abs(x - r))]) for r in kept}
    cells = ["."] * R
    for r in sorted(place):
        if r >= R:
            continue
        n = root + place[r]
        n = max(WAVE_RANGE[0] + 8, min(60, n))
        cells[r] = midi_to_note(n) + (f"!{cut}" if cut and r else "")
    return cells


def _render_kit_pattern(pattern: str, level: int, native: int, R: int) -> list[str]:
    """A kit pattern string -> cells; below the native level the kick/snare letters move to the beat (0) or 8th
    (1) grid and the hats stay where they are (hats are texture, kick and snare are the groove)."""
    cells = pattern.split()
    cells += ["."] * (R - len(cells))
    cells = cells[:R]
    grid = level_grid(level, R, kit=True) if level < native else None
    if not grid:
        return cells
    out = list(cells)
    for r, c in enumerate(cells):
        if c in (".", "-") or c.startswith("v") or r % grid == 0:
            continue
        ks = "".join(ch for ch in c if ch in _KICK_SNARE)
        if not ks:
            continue
        rest = "".join(ch for ch in c if ch not in _KICK_SNARE)
        out[r] = rest or "."
        t = (r // grid + 1) * grid
        if t >= R:                       # a push into the next bar's downbeat is dropped (the downbeat has its kick)
            continue
        out[t] = _merge_hits(out[t], ks)
    return out


def _merge_hits(cell: str, letters: str) -> str:
    """Two drum cells into one two-letter stack: kick first, then snare, then whatever else fits."""
    have = (cell if cell != "." else "") + letters
    order = "KBkSQPNDsHhOTtCcXMZ"
    picked = []
    for ch in order:
        if ch in have and ch not in picked:
            picked.append(ch)
    return "".join(picked[:2]) or "."


STYLES = {"fusion": gen_fusion, "ambient": gen_ambient, "chip": gen_chip, "pop": gen_pop, "rock": gen_rock, "ska": gen_ska}
# rock defaults to the stage-corpus loop (the reference corpus: 24-bar A B C loops, no intro, minor);
# pop and ska to the verse-chorus song; the three loop styles stay as they were
STYLE_DEFAULT_FORM = {"fusion": "loop", "ambient": "loop", "chip": "loop", "pop": "verse-chorus", "rock": "stage", "ska": "verse-chorus"}


# ----------------------------------------------------------------------------------------------- CLI


def cmd_compile(args: argparse.Namespace) -> int:
    compiled, names = [], []
    for f in args.scores:
        p = Path(f)
        if not p.is_file():
            sys.exit(f"compose.py: score not found: {p}")
        default = "song_" + re.sub(r"\W+", "_", p.stem).strip("_").lower()
        try:
            song = parse_score(p.read_text(encoding="utf-8"), default)
            compiled.append(compile_song(song))
        except ScoreError as exc:
            sys.exit(f"compose.py: {p}: {exc}")
        names.append(p.name)
    if len({c.song.name for c in compiled}) != len(compiled):
        sys.exit("compose.py: two scores share a song name (set `name:` in one of them)")
    c_text, h_text, reports = emit_c(compiled, names)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(c_text, encoding="utf-8")
    header = Path(args.header) if args.header else out.with_suffix(".h")
    header.write_text(h_text, encoding="utf-8")
    rep = {"ok": True, "out": str(out), "header": str(header), "songs": reports,
           "warnings": [w for r in reports for w in r["warnings"]]}
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep))
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    gen = STYLES.get(args.style)
    if gen is None:
        sys.exit(f"compose.py: unknown style {args.style!r}; styles: {', '.join(STYLES)}")
    try:
        key = key_pc(args.key)
    except ScoreError as exc:
        sys.exit(f"compose.py: {exc}")
    groove = args.groove
    if groove not in GROOVES:
        sys.exit(f"compose.py: unknown groove {groove!r}; grooves: {', '.join(GROOVES)}")
    if args.style == "ska" and groove == "straight":
        groove = "ska"
    if args.bpm is None:
        args.bpm = float(GROOVES[groove]["bpm_default"])
    if not 40 <= args.bpm <= 240:
        sys.exit("compose.py: --bpm 40..240")
    groove_warnings: list[str] = []
    lo, hi = GROOVES[groove]["bpm"]
    if groove != "straight" and not lo <= args.bpm <= hi:
        groove_warnings.append(f"--bpm {args.bpm:g} is outside the {groove} groove's band {lo}-{hi}; the groove is kept, the feel will not be")
    if args.syncopation is not None and not 0 <= args.syncopation <= 3:
        sys.exit("compose.py: --syncopation 0..3")
    rng = random.Random(args.seed)
    brng = random.Random(args.seed * 7919 + 1)   # bend decisions on their own stream: --bend never changes the tune
    name = args.name or "song_main"
    form = STYLE_DEFAULT_FORM[args.style] if args.form == "auto" else args.form
    if form not in FORMS:
        sys.exit(f"compose.py: unknown form {form!r}; forms: auto, {', '.join(FORMS)}")
    info: dict = {"form": form, "texture": args.texture}
    if args.texture not in TEXTURES:
        sys.exit(f"compose.py: unknown texture {args.texture!r}; textures: {', '.join(TEXTURES)}")
    prng = random.Random(args.seed * 48611 + 3)   # the phrase grammar's stream: --phrases 0 leaves every other draw untouched
    hrng = random.Random(args.seed * 7001 + 11)   # the hook engine's stream: --hook 0 leaves every other draw untouched
    hook = getattr(args, "hook", 0)
    uses_groove = groove != "straight" or args.syncopation
    if uses_groove and (args.style in ("fusion", "ambient") or (args.style == "chip" and form == "loop")):
        sys.exit(f"compose.py: --groove / --syncopation apply to the song forms (pop, rock, ska, chip with --form); --style {args.style} --form {form} carries its own rhythm")
    if GROOVES[groove]["rows"] != 16 and args.texture == "fusion":
        sys.exit(f"compose.py: --texture fusion is written on the 16-row grid; the {groove} groove uses 12 rows per bar (take --texture plain)")
    if hook and GROOVES[groove]["rows"] != 16:
        sys.exit(f"compose.py: --hook writes on the 16-row grid; the {groove} groove uses 12 rows per bar (take --hook 0 or a 16-row groove)")
    try:
        if form == "loop":
            if args.progression:
                sys.exit("compose.py: --progression needs a song form (--form stage|verse-chorus|aaba|blues12); the loop styles carry their own harmony")
            if args.style in ("pop", "rock", "ska"):
                sc, meta, info = gen_form(rng, key, float(args.bpm), args.bars, name, args.bend, brng, args.style, STYLE_DEFAULT_FORM[args.style], None, args.texture, args.lift, args.phrases, prng, hook, hrng, groove, args.syncopation)
            else:
                if args.texture != "plain":
                    sys.exit(f"compose.py: --texture applies to the song forms (pop, rock, chip with --form); --style {args.style} --form loop is already its own texture")
                if args.phrases:
                    sys.exit(f"compose.py: --phrases applies to the song forms (pop, rock, chip with --form); --style {args.style} --form loop has its own phrase grammar")
                sc, meta = gen(rng, key, float(args.bpm), args.bars, name, args.bend, brng)
                if hook:
                    info["hook"] = {"ignored": f"--style {args.style} --form loop has no song form to hang a hook on; use --form stage|verse-chorus|aaba"}
                    print(f"compose.py: note: --hook ignored for --style {args.style} --form loop", file=sys.stderr)
        elif args.style == "fusion":
            if form in ("blues12", "stage"):
                sys.exit("compose.py: --style fusion takes --form loop|aaba|verse-chorus; for the fusion idioms on a stage loop or a blues use --style rock --form stage|blues12 --texture fusion")
            if args.phrases:
                sys.exit("compose.py: --phrases applies to the pop/rock/chip forms; for the fusion idioms with motif banks use --style rock|pop --texture fusion --form aaba|verse-chorus|stage --phrases N")
            sc, meta, info = gen_fusion_form(rng, key, float(args.bpm), args.bars, name, args.bend, brng, form)
            if hook:
                info["hook"] = {"ignored": "the fusion forms keep their own lead grammar; for a hook use --style rock|pop --texture fusion --hook N"}
                print("compose.py: note: --hook ignored for --style fusion (use --style rock|pop --texture fusion --hook N)", file=sys.stderr)
        elif args.style == "ambient":
            sys.exit("compose.py: --style ambient has no song form (it is a bed); use --form loop")
        else:
            sc, meta, info = gen_form(rng, key, float(args.bpm), args.bars, name, args.bend, brng, args.style, form, args.progression, args.texture, args.lift, args.phrases, prng, hook, hrng, groove, args.syncopation)
    except ScoreError as exc:
        sys.exit(f"compose.py: {exc}")
    info.setdefault("groove", groove)
    info.setdefault("syncopation_level", args.syncopation or 0)
    info["bpm_band"] = list(GROOVES[groove]["bpm"])
    organic_moves: dict = {}
    if args.organic:
        organic_moves = apply_organic(sc, args.organic, random.Random(args.seed * 104729 + args.organic))
        info["organic"] = args.organic
        info["organic_moves"] = organic_moves
        meta = [*meta, "organic " + str(args.organic) + ": " + ", ".join(f"{k} {v}" for k, v in sorted(organic_moves.items()))]
    if args.pan != "none":
        try:
            pan_rep = apply_pan(sc, args.pan, args.style)
        except ScoreError as exc:
            sys.exit(f"compose.py: {exc}")
        info["pan"] = pan_rep
        meta = [*meta, f"pan {args.pan}: {pan_rep['events']} pan events ({', '.join(f'{k} {v}' for k, v in sorted(pan_rep['marks'].items()))}"
                + (f"; echo voice right x{pan_rep['echo_sides']}" if pan_rep["echo_sides"] else "") + ("; verse pad auto-pan" if pan_rep["pad_auto"] else "")
                + "); centre by default, never the bass or the kit, mono on the handheld speaker"]
    if hook and "level" in info.get("hook", {}):               # the measured hook metrics against the corpus bands
        m = hook_metrics(sc)
        info["hook"]["metrics"] = m
        info["hook"]["climax_bar"] = m.get("song_climax_bar")
        info["hook"]["step_leap"] = [m.get("step_ratio"), m.get("leap_ratio")]
        info["hook"]["repeats"] = m.get("hook_repeats", 0)
        meta = [*meta, f"hook metrics: {m.get('hook_bars', 0)}-bar cell heard {m.get('hook_repeats', 0)} times ({m.get('hook_per_minute', 0)} a minute), "
                f"range {m.get('range')}, {m.get('contour')}, steps {m.get('step_ratio')}, climax bar {m.get('song_climax_bar')}, "
                f"{m.get('in_band', 0)} metrics in the corpus band, {m.get('near_band', 0)} near, {m.get('out_of_band', 0)} out"]
    text = sc.text([f"style {args.style}, key {PC_NAME[key]}, {args.bpm:g} bpm, seed {args.seed}, bends {args.bend}"
                    + (f", form {form}" if form != "loop" else "") + (f", phrases {args.phrases}" if args.phrases else "")
                    + (f", hook {hook}" if hook else "")
                    + (f", organic {args.organic}" if args.organic else "")
                    + (f", pan {args.pan}" if args.pan != "none" else ""), *meta])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    # self-check: the generated score must compile
    try:
        song = parse_score(text, name)
        c = compile_song(song)
        _, _, reports = emit_c([c], [out.name])
    except ScoreError as exc:
        sys.exit(f"compose.py: generated score does not compile ({exc}); report this seed")
    rep = {"ok": True, "out": str(out), "style": args.style, "key": PC_NAME[key], "bpm": args.bpm, "bars": len(sc.bars),
           "seed": args.seed, "bend": args.bend, "name": name, **info, "syncopation": score_syncopation(sc),
           "sections": meta, "compiled": reports[0], "warnings": groove_warnings + reports[0]["warnings"]}
    for w in groove_warnings:
        print(f"compose.py: warning: {w}", file=sys.stderr)
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep))
    return 0


def cmd_styles(_: argparse.Namespace) -> int:
    print("styles: " + ", ".join(f"{k} (default form {STYLE_DEFAULT_FORM[k]})" for k in STYLES))
    print("forms: " + "; ".join(f"{k}: {v}" for k, v in FORMS.items()))
    print("textures: " + "; ".join(f"{k}: {v}" for k, v in TEXTURES.items()))
    print("pan modes (--pan): " + "; ".join(f"{k}: {v}" for k, v in PAN_MODES.items()))
    print("grooves (--groove; tempo band in bpm, default syncopation level, rows per bar):")
    for k, g in GROOVES.items():
        print(f"  {k:<9} {g['bpm'][0]}-{g['bpm'][1]} bpm (default {g['bpm_default']}), syncopation {g['sync']}, {g['rows']} rows: {g['desc']}")
    print("syncopation levels (--syncopation): " + "; ".join(f"{k} = {v}" for k, v in SYNCOPATION_LEVELS.items()))
    print("progressions (Roman numerals, resolved against --key; or pass your own, e.g. --progression \"I bVII IV I\"):")
    for k, (nums, mood) in PROGRESSIONS.items():
        print(f"  {k:<11} {nums:<32} {mood}")
    print("chords: " + ", ".join(f"{k}=({','.join(map(str, v))})" for k, v in CHORDS.items()))
    print("waves: " + ", ".join(WAVES))
    print("drums: " + ", ".join(f"{k}=env {d[0]:02X} poly {d[1]:02X}" + (f" then {d[2]:02X}/{d[3]:02X}" if len(d) > 2 else "") for k, d in DRUMS.items()))
    print(json.dumps({"ok": True, "styles": list(STYLES), "forms": list(FORMS), "textures": list(TEXTURES), "pan_modes": list(PAN_MODES),
                      "grooves": {k: {"bpm": list(g["bpm"]), "bpm_default": g["bpm_default"], "syncopation": g["sync"], "rows": g["rows"]} for k, g in GROOVES.items()},
                      "syncopation_levels": SYNCOPATION_LEVELS,
                      "progressions": {k: v[0] for k, v in PROGRESSIONS.items()},
                      "chords": list(CHORDS), "waves": list(WAVES), "drums": list(DRUMS)}))
    return 0


PART_RE = re.compile(r"^([A-Za-z_]\w*)=(.+)$")
PART_PAN_RE = re.compile(r"^(?i:([LR])(\d{1,3})|(C))$")   # L30, R45, C


def song_text(song: Song, meta: list[str]) -> str:
    """Serialise a parsed Song back to score text (header, non-default library entries, every bar)."""
    out = [*[f"# {m}" for m in meta], f"name: {song.name}"]
    if song.title:
        out.append(f"title: {song.title}")
    out += [f"tempo: {song.fpr}", f"rows: {song.rows}", *([f"beats: {song.beats}"] if song.rows != 4 * song.beats else []), f"arp: {song.arp}", f"loop: {song.loop}", ""]
    for name, typ, params in song.insts:
        out.append(f"inst {name} {typ} " + " ".join(f"{k}={v}" for k, v in params.items()))
    out += [f"wave {k} {v}" for k, v in song.waves.items() if WAVES.get(k) != v]
    out += [f"chord {k} " + " ".join(str(i) for i in v) for k, v in song.chords.items() if CHORDS.get(k) != v]
    for k, d in song.drums.items():   # (NR42, NR43) or (NR42, NR43, then NR42, then NR43)
        if DRUMS.get(k) != d:
            out.append(f"drum {k} env={d[0]:02X} poly={d[1]:02X}" + (f" then={d[2]:02X},{d[3]:02X}" if len(d) > 2 else ""))
    names = {0: "lead", 1: "arp", 2: "bass", 3: "drum"}
    for i in range(max(song.bars) + 1):
        lanes = song.bars.get(i, {})
        out += ["", f"bar {i + 1}"]
        for lane in range(4):
            out.append(f"{names[lane]}:".ljust(6) + " ".join(lanes.get(lane) or ["."] * song.rows))
    return "\n".join(out) + "\n"


def split_song(song: Song, keep: dict[int, str | None], part: str) -> Song:
    """A copy of `song` with only the lanes in `keep` (lane -> drum-letter filter or None); the rest is silent."""
    out = Song()
    out.name, out.title, out.fpr, out.bpm, out.rows, out.arp, out.loop = f"{song.name}_{part}", song.title, song.fpr, song.bpm, song.rows, song.arp, song.loop
    out.beats = song.beats
    out.insts, out.waves, out.chords, out.drums = list(song.insts), dict(song.waves), dict(song.chords), dict(song.drums)
    for bar, lanes in song.bars.items():
        out.bars[bar] = {}
        for lane, cells in lanes.items():
            if lane not in keep:
                continue
            letters = keep[lane]
            if lane == 3 and letters:
                cells = [c if c in (".", "-") or c.startswith("v") else ("".join(ch for ch in c if ch in letters) or ".") for c in cells]
            out.bars[bar][lane] = list(cells)
    return out


def cmd_split(args: argparse.Namespace) -> int:
    p = Path(args.score)
    if not p.is_file():
        sys.exit(f"compose.py: score not found: {p}")
    default = "song_" + re.sub(r"\W+", "_", p.stem).strip("_").lower()
    try:
        song = parse_score(p.read_text(encoding="utf-8"), default)
    except ScoreError as exc:
        sys.exit(f"compose.py: {p}: {exc}")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    part_pans: dict[str, str] = {}
    if args.pan:
        for item in args.pan.split(","):
            name, _, val = item.partition("=")
            m = PART_PAN_RE.match(val.strip())
            if not name.strip() or not m or (m.group(2) and int(m.group(2)) > 100):
                sys.exit(f"compose.py: --pan wants <part>=L<0..100>|R<0..100>|C, comma separated (e.g. a=L30,b=R30), got {item!r}")
            part_pans[name.strip()] = "C" if m.group(3) else f"{m.group(1).upper()}{int(m.group(2))}"
    parts = []
    for spec in args.part:
        m = PART_RE.match(spec)
        if not m:
            sys.exit(f"compose.py: --part wants <name>=<lane>[,<lane>...][:<drum letters>], got {spec!r}")
        part, keep = m.group(1), {}
        for item in m.group(2).split(","):
            lane_name, _, letters = item.partition(":")
            if lane_name.lower() not in LANES:
                sys.exit(f"compose.py: --part {part}: unknown lane {lane_name!r} (lead, arp, bass, drum)")
            keep[LANES[lane_name.lower()]] = letters or None
        sub = split_song(song, keep, part)
        out = out_dir / f"{p.stem}_{part}.txt"
        meta = [f"part {part} of {p.name}: lanes " + ", ".join(sorted(k.split(":")[0] for k in m.group(2).split(","))),
                "the parts share tempo, bars and loop: run one ROM per part in lockstep"]
        if part in part_pans:
            meta.append(f"pan: {part_pans[part]}")          # a mixer hint for a page that plays the parts together
        text = song_text(sub, meta)
        try:
            rep = emit_c([compile_song(parse_score(text, sub.name))], [out.name])[2][0]
        except ScoreError as exc:
            sys.exit(f"compose.py: part {part} does not compile ({exc})")
        out.write_text(text, encoding="utf-8")
        parts.append({"part": part, "name": sub.name, "out": str(out), "lanes": sorted(keep), "drums": {str(k): v for k, v in keep.items() if v},
                      "bars": rep["bars"], "notes": rep["notes"], "rom_bytes": rep["rom_bytes"], **({"pan": part_pans[part]} if part in part_pans else {})})
    unknown = sorted(set(part_pans) - {q["part"] for q in parts})
    if unknown:
        sys.exit(f"compose.py: --pan names parts that do not exist: {', '.join(unknown)}")
    rep = {"ok": True, "score": str(p), "song": song.name, "bars": max(song.bars) + 1, "frames_per_row": song.fpr, "parts": parts}
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep))
    return 0


# ----------------------------------------------------------------------------------------------- note events (piano rolls)

GB_FPS = 4194304 / 70224          # 59.7275 frames per second
EVENT_CHANNELS = ["pulse 1", "pulse 2", "wave", "noise"]
_FX_NAME = {v: k for k, v in FX.items()}


def _noise_midi(poly: int) -> int:
    """A pseudo pitch for a noise setting (NR43): the LFSR clock as a MIDI number, so kicks sit low and hats high."""
    import math
    s, r = poly >> 4, poly & 0x07
    freq = 524288.0 / (r if r else 0.5) / (2 ** (s + 1))
    return max(0, min(127, round(69 + 12 * math.log2(max(1.0, freq) / 440.0))))


def _env_seconds(env: int, vol: int, fps: float) -> float | None:
    """Lifetime of a pulse/noise NRx2 envelope that decays (None = holds): vol steps of n/64 s each."""
    n = env & 0x07
    if n == 0 or env & 0x08 or vol == 0:
        return None
    return vol * n / 64.0


def song_events(song: Song, c: Compiled, *, fps: float = GB_FPS, offset_s: float = 0.0, frame0: int = 0, bar0: int = 0) -> list[dict]:
    """Replay the compiled patterns the way src/music.c reads them and return one dict per sounding note.

    Each note: ch 0..3, t (seconds, = offset_s + f / fps), d (seconds the gate is held: until the lane's next
    note, key-off or cut), f / fd (the same in frames from music_init), bar / row (0-based, bar counted from bar0),
    midi (noise: a pseudo pitch from NR43), vol 0..15, inst (instrument name; noise: the drum letter in `drum`).
    Optional keys name what the driver does to the pitch while the note sounds: arp [intervals] + arp_f (frames
    per chord step; the cycle is not expanded), trill / mordent (interval), split (the second note of a 32nd
    pair), bend [semitones, frames], porta (frames) + porta_from (the previous note), slide (period units per frame), vib [depth, rate],
    trem [depth, rate], penv [semitones, frames], cut (frames), echo (a pulse-2 copy of a pulse-1 note made by
    FX_ECHO: delayed, quieter), dec (seconds until the envelope reaches silence, when it decays)."""
    fpr, rows = song.fpr, song.rows
    inst_rows = c.inst_rows  # type: ignore[attr-defined]
    notes: list[dict] = []
    chan = [{"inst": 0, "vol": 15, "open": None, "prev_midi": None, "cut": 0} for _ in range(4)]
    arp_speed = song.arp
    echo = 0
    echo_side = False
    pulse1_echoes: list[dict] = []   # ch0 notes to mirror on ch1 while echo is on
    pan_state = [3, 3]               # pulse channels' sides (1 right, 2 left, 3 both), as the driver tracks them
    pan_changes: list[dict] = []     # every side change: {"ch", "f", "pan": -1 | 0 | 1}
    PAN_VAL = {1: 1, 2: -1, 3: 0}

    def set_pan(chn: int, side: int, frame: int) -> None:
        if pan_state[chn] != side:
            pan_state[chn] = side
            pan_changes.append({"ch": chn, "f": frame, "pan": PAN_VAL[side]})

    def close(ch: int, frame: int) -> None:
        k = chan[ch]
        n = k["open"]
        if n is None:
            return
        n["fd"] = max(1, min(n["fd"], frame - n["f"]))
        k["open"] = None

    def inst_kind(i: int) -> str:
        return song.insts[i][1] if i < len(song.insts) else "pulse"

    n_bars = len(c.orders[0])
    for bar in range(n_bars):
        for row in range(rows):
            frame = frame0 + (bar * rows + row) * fpr
            for ch in range(4):
                cell = c.patterns[c.orders[ch][bar]][row * 3:row * 3 + 3]
                note, inst, fx, param = cell[0], cell[1] >> 4, cell[1] & 0x0F, cell[2]
                k = chan[ch]
                pan = 0
                if ch < 2 and note & PAN_NOTE and note != MUSIC_OFF:   # pan pseudo-note (a drum stack also uses bit 7)
                    pan, note = note & 0x03, 0
                if fx == FX["pan"]:
                    pan = param & 0x03
                if inst:
                    k["inst"] = inst - 1
                    k["vol"] = inst_rows[k["inst"]][1] >> 4
                if fx == FX["vol"]:
                    k["vol"] = param & 0x0F
                if fx == FX["arpspeed"] and param:
                    arp_speed = param
                if fx == FX["echo"] and ch == 1:
                    echo = param
                    close(ch, frame)
                    if echo_side and not param:
                        set_pan(1, 3, frame)
                        echo_side = False
                    if param and pan:
                        echo_side = True
                if fx == FX["cut"]:
                    k["cut"] = param or 1
                if pan and ch < 2:
                    set_pan(ch, pan, frame)
                if note == MUSIC_OFF:
                    close(ch, frame)
                    continue
                if not note:
                    if fx == FX["cut"] and k["open"] is not None:
                        k["open"]["cut"] = k["cut"]
                        close(ch, frame + k["cut"])
                    continue
                if ch == 3:
                    hits = [(note & 0x0F, 0)] + ([(note >> 4, 3)] if note >> 4 else [])
                    for d_id, late in hits:
                        env, poly = c.drum_list[d_id - 1][0], c.drum_list[d_id - 1][1]
                        letter = next((L for L, dd in song.drums.items() if tuple(dd) + ((0, 0) if len(dd) == 2 else ()) == c.drum_list[d_id - 1]), "?")
                        close(3, frame + late)
                        ev = {"ch": 3, "f": frame + late, "fd": fpr, "bar": bar0 + bar, "row": row, "midi": _noise_midi(poly),
                              "vol": env >> 4, "inst": "drum", "drum": letter}
                        dec = _env_seconds(env, env >> 4, fps)
                        if dec is not None:
                            ev["dec"] = round(dec, 4)
                        notes.append(ev)
                        k["open"] = ev
                        ev["fd"] = 10 ** 6
                    continue
                # tonal note
                close(ch, frame)
                if ch == 1 and echo:
                    echo = 0
                    if echo_side:
                        set_pan(1, 3, frame)
                        echo_side = False
                iname, ityp, ikv = song.insts[k["inst"]] if k["inst"] < len(song.insts) else ("?", "pulse", {})
                irow = inst_rows[k["inst"]]
                ev = {"ch": ch, "f": frame, "fd": 10 ** 6, "bar": bar0 + bar, "row": row, "midi": note, "vol": k["vol"], "inst": iname}
                if ch < 2 and ityp == "pulse" and irow[2]:        # instrument pan: a side per note, or an auto-pan
                    if irow[2] & 0x03:
                        set_pan(ch, irow[2] & 0x03, frame)
                    if irow[2] >> 2:
                        set_pan(ch, 2, frame)
                        ev["pan"] = "LR"
                        ev["pan_f"] = irow[2] >> 2
                if pan and ch < 2:
                    set_pan(ch, pan, frame)                        # the cell's own pan wins over the instrument's
                if ch < 2 and "pan" not in ev and pan_state[ch] != 3:
                    ev["pan"] = PAN_VAL[pan_state[ch]]
                if ityp == "pulse":
                    dec = _env_seconds(irow[1], k["vol"], fps)
                    if dec is not None:
                        ev["dec"] = round(dec, 4)
                else:
                    wenv = irow[7]
                    if wenv and not wenv & 0x80:
                        ev["dec"] = round(3 * (wenv & 0x7F) / fps, 4)
                if irow[6]:
                    ev["penv"] = [irow[6] >> 4, irow[6] & 0x0F]
                if irow[3]:
                    ev["autovib"] = [irow[3] >> 4, (irow[3] & 0x0F) << 2]
                if fx == FX["arp"]:
                    ev["arp"] = list(c.chord_list[param])
                    ev["arp_f"] = arp_speed
                elif fx == FX["trill"]:
                    ev["mordent" if param >> 4 else "trill"] = param & 0x0F
                elif fx == FX["bend"]:
                    so = param & 0x0F
                    ev["bend"] = [so - 16 if so > 7 else so, param >> 4]
                elif fx == FX["porta"]:
                    if k["prev_midi"] is not None:
                        ev["porta"] = param
                        ev["porta_from"] = k["prev_midi"]
                elif fx == FX["slide"]:
                    ev["slide"] = param - 256 if param > 127 else param
                elif fx == FX["vib"]:
                    ev["vib"] = [param >> 4, param & 0x0F]
                elif fx == FX["trem"]:
                    ev["trem"] = [param >> 4, param & 0x0F]
                elif fx == FX["cut"]:
                    ev["cut"] = k["cut"]
                notes.append(ev)
                k["open"] = ev
                k["prev_midi"] = note
                if fx == FX["cut"]:
                    close(ch, frame + k["cut"])
                if fx == FX["split"]:
                    half = fpr >> 1
                    close(ch, frame + half)
                    ev2 = dict(ev)
                    ev2.pop("arp", None); ev2.pop("arp_f", None); ev2.pop("cut", None)
                    ev2.update({"f": frame + half, "fd": 10 ** 6, "midi": param, "split": True})
                    notes.append(ev2)
                    k["open"] = ev2
                    k["prev_midi"] = param
                if ch == 0 and echo:
                    pulse1_echoes.append((ev, echo))
    end = frame0 + n_bars * rows * fpr
    for ch in range(4):
        close(ch, end)
    for ev, e in pulse1_echoes:
        delay, drop = e >> 4, e & 0x0F
        cp = dict(ev)
        cp.update({"ch": 1, "f": ev["f"] + delay, "vol": max(0, ev["vol"] - drop), "echo": True})
        cp.pop("cut", None)
        cp.pop("pan", None)
        cp.pop("pan_f", None)
        side = 0
        for chg in pan_changes:                                   # pulse 2's side when the copy sounds
            if chg["ch"] == 1 and chg["f"] <= cp["f"]:
                side = chg["pan"]
        if side:
            cp["pan"] = side
        notes.append(cp)
    notes.sort(key=lambda n: (n["f"], n["ch"]))
    for n in notes:
        n["t"] = round(offset_s + n["f"] / fps, 4)
        n["d"] = round(n["fd"] / fps, 4)
    for chg in pan_changes:
        chg["t"] = round(offset_s + chg["f"] / fps, 4)
    if pan_changes:
        notes.append({"_pan_changes": pan_changes})           # popped by cmd_events into the top-level `pan_changes`
    return notes


def cmd_events(args: argparse.Namespace) -> int:
    fps = float(args.fps)
    songs_meta, all_notes, insts = [], [], []
    pan_changes: list[dict] = []
    frame0 = bar0 = 0
    first = None
    for f in args.scores:
        p = Path(f)
        if not p.is_file():
            sys.exit(f"compose.py: score not found: {p}")
        default = "song_" + re.sub(r"\W+", "_", p.stem).strip("_").lower()
        try:
            song = parse_score(p.read_text(encoding="utf-8"), default)
            c = compile_song(song)
        except ScoreError as exc:
            sys.exit(f"compose.py: {p}: {exc}")
        if first is None:
            first = song
        elif (song.fpr, song.rows) != (first.fpr, first.rows):
            sys.exit(f"compose.py: {p}: chained scores must share tempo and rows per bar ({song.fpr}x{song.rows} vs {first.fpr}x{first.rows})")
        n_bars = len(c.orders[0])
        evs = song_events(song, c, fps=fps, offset_s=float(args.offset), frame0=frame0, bar0=bar0)
        if evs and "_pan_changes" in evs[-1]:
            pan_changes += evs.pop()["_pan_changes"]
        all_notes += evs
        songs_meta.append({"name": song.name, "title": song.title, "source": p.name, "start_bar": bar0, "bars": n_bars,
                           "loop_bar": bar0 + song.loop, "start_s": round(float(args.offset) + frame0 / fps, 4), "notes": sum(1 for n in all_notes if bar0 <= n["bar"] < bar0 + n_bars)})
        for name, typ, kv in song.insts:
            insts.append({"song": song.name, "name": name, "type": typ, **kv})
        frame0 += n_bars * song.rows * song.fpr
        bar0 += n_bars
    assert first is not None
    rep = {"ok": True, "out": args.out, "song": first.name, "title": first.title, "fps": fps, "frames_per_row": first.fpr, "rows_per_bar": first.rows,
           "beats_per_bar": first.beats, "rows_per_beat": first.rows // first.beats,
           "bpm": round(first.bpm, 3), "bars": bar0, "loop_bar": songs_meta[0]["loop_bar"] if len(songs_meta) == 1 else 0, "arp_speed": first.arp,
           "offset_s": float(args.offset), "seconds_per_bar": round(first.rows * first.fpr / fps, 5), "length_s": round(frame0 / fps, 4),
           "channels": EVENT_CHANNELS, "songs": songs_meta, "instruments": insts, "notes": all_notes}
    if pan_changes:                                               # only when the song pans: old output stays byte-identical
        rep["pan_changes"] = pan_changes
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, separators=(",", ":")), encoding="utf-8")
    print(json.dumps({k: v for k, v in rep.items() if k not in ("notes", "instruments")} | {"notes": len(all_notes)}))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="\n".join(__doc__.splitlines()[1:]))
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compile", help="score file(s) -> src/music_data.c (+ .h)")
    c.add_argument("scores", nargs="+", help="score text files (one song each)")
    c.add_argument("--out", default="output/game/src/music_data.c", help="C file to write (default output/game/src/music_data.c)")
    c.add_argument("--header", default=None, help="header to write (default: next to --out, .h)")
    c.add_argument("--report", default=None, help="also write the JSON report here")
    c.set_defaults(func=cmd_compile)
    g = sub.add_parser("generate", help="write a score in a style")
    g.add_argument("--style", default="fusion", help="fusion | ambient | chip | pop | rock | ska")
    g.add_argument("--key", default="F#", help="key, e.g. F#, Bb, C (default F#)")
    g.add_argument("--bpm", type=float, default=None, help="tempo in beats per minute (default: the groove's centre, 100 for straight; rows are 16ths: 3600/bpm/4 frames, triplet 8ths on the 12-row grooves: 3600/bpm/3)")
    g.add_argument("--bars", type=int, default=32, help="length in bars (rounded to the style's section size or the form's plan: 32/48/64, 32/40, 28/40/52)")
    g.add_argument("--seed", type=int, default=1, help="random seed; the same arguments always give the same score")
    g.add_argument("--bend", default="sparse", choices=sorted(BEND_RATES), help="how often the bass/lead bend into a note (every bend resolves onto the written tone); default sparse")
    g.add_argument("--form", default="auto", help="song form: auto (loop for fusion/ambient/chip, stage for rock, verse-chorus for pop) | loop | stage | verse-chorus | aaba | blues12")
    g.add_argument("--progression", default=None, metavar="NAME|NUMERALS",
                   help="progression(s) for pop/rock/chip forms: a library name (`compose.py styles`) or Roman numerals like \"I V vi IV\"; "
                        "several separated by ' | ' go to the sections (stage: A | B | C; verse-chorus/aaba: chorus | verse | bridge); "
                        "defaults: stage stage_a | stage_b | stage_c (rock) or town | cadential | stage_c, verse-chorus axis (pop, chip) / threechord or mixolydian (rock), blues12 or blues12q")
    g.add_argument("--texture", default="plain", help="plain (default) | fusion: layer the fusion idioms (colour-tone chord cycle, mordents and trills, slap bass, fusion kit, echo B section) on any form; form and texture are independent knobs")
    g.add_argument("--lift", default="fifth", choices=sorted(LIFTS),
                   help="how far the chorus / C section / final A / second head lead sits above the verse: fifth (default; the reference corpora lift 1-8 semitones) | sixth | octave")
    g.add_argument("--phrases", type=int, default=0, choices=(0, 1, 2),
                   help="phrase-level composition for the pop/rock/chip forms (default 0 = the one-motif grammar, byte-identical): "
                        "1 = each section composes from a bank of three ideas (statement, answer, departure) whose rhythms carry rests as cells, "
                        "B sections quote the previous section's answer a step away, pulse 2 answers a phrase that ends early, the answer phrases take a second lead colour; "
                        "2 = + repeated sections re-order their bank, restatements thin by a note, more rests")
    g.add_argument("--hook", type=int, default=0, choices=(0, 1, 2, 3),
                   help="hook and melody engine for the pop/rock/chip forms (default 0 = today's melodies, byte-identical): "
                        "1 = the chorus / stage-A hook is designed first (a corpus contour class, 7-10 semitones, one leap at a fixed place, "
                        "a rhythm with one anticipation landing on beat 3 with a breath), repeats note for note with the third statement changed, "
                        "and the verse (its rhythm on fewer notes, lower), pre-chorus (its first bar sequenced up) and outro (its tail twice) derive from it; "
                        "2 = + melodic-math symmetry: answer phrases mirror their statement with the same rhythm and note count, the chorus holds the song's "
                        "top note (heard once per chorus), the intro's chord voice plays the hook's rhythm first; "
                        "3 = + the earworm surprise: one unusual interval (a sixth or a tritone, resolved by step) in the hook, the final note delayed an 8th "
                        "the last time, the bass quotes the hook under the bridge / B section. fusion, ambient and blues12 ignore it (and say so); "
                        "the report's `hook` block carries the design and the measured metrics against the corpus bands")
    g.add_argument("--groove", default="straight", help="straight (default: as before) | swing | shuffle | ska | onedrop | funk | dance | tropical | latin | halftime: the kit, bass rhythm, pulse-2 stab rhythm and hook rhythm bank of a genre, with a tempo band (`compose.py styles`); swing / shuffle write 12-row bars (a triplet grid)")
    g.add_argument("--syncopation", type=int, default=None, choices=(0, 1, 2, 3),
                   help="anticipations, off-beat pushes and strong-beat rests on the hook, bass and kick/snare (default: the groove's own level, straight = 0 = as before): 0 kick/snare on the beats and the hook on the 8th grid; 1 the groove's pattern + the hook anticipates its second-bar downbeat and the bass pushes chord changes; 2 medium (the groove research's sweet spot): + the and-of-3 kick, the and-of-2 lean, a pickup before the hook; 3 funk: + off-16th ghosts and pops")
    g.add_argument("--organic", type=int, default=0, choices=(0, 1, 2, 3),
                   help="organic layer (default 0 = untouched): 1 = repeats vary on phrase ends, phrase-end breaths, section fills, off-beat accents; 2 = + half of all repeats vary, dropped hats, pulse 2 sits out a bar, bass anticipations; 3 = + density ebbs inside sections")
    g.add_argument("--pan", default="none", choices=sorted(PAN_MODES),
                   help="stereo pans (NR51, hard left / right; mono on the handheld speaker): none (default; byte-identical to before) | "
                        "echo (the echo voice right, the lead left for the echo's duration) | call (call and response: the rock verse's answers alternate sides, "
                        "the blues call left and answer right, a pop / stage phrase's restatement right and conclusion left) | wide (echo + call + an LR auto-pan on the verse pad). "
                        "Never the bass or the kit")
    g.add_argument("--name", default=None, help="C symbol for the song (default song_main)")
    g.add_argument("--out", required=True, help="score file to write, e.g. output/music/main.txt")
    g.add_argument("--report", default=None, help="also write the JSON report here")
    g.set_defaults(func=cmd_generate)
    s = sub.add_parser("styles", help="list styles, chord qualities, waves and drums")
    s.set_defaults(func=cmd_styles)
    sp = sub.add_parser("split", help="one score -> one score per part, each keeping only the named lanes (multi-ROM lockstep pieces)")
    sp.add_argument("score", help="the score to split")
    sp.add_argument("--part", action="append", required=True, metavar="NAME=LANES",
                    help="e.g. a=lead,arp or b=bass,drum:KSks (repeatable; lanes lead/arp/bass/drum, optional drum-letter filter)")
    sp.add_argument("--out-dir", required=True, help="directory for <stem>_<part>.txt")
    sp.add_argument("--pan", default=None, metavar="PART=L30,PART=R30",
                    help="mixer hint per part for a page that plays the parts together: L<percent> / R<percent> / C, written as `# pan: L30` in the part's header (a comment: the ROM is unchanged)")
    sp.add_argument("--report", default=None, help="also write the JSON report here")
    sp.set_defaults(func=cmd_split)
    ev = sub.add_parser("events", help="score(s) -> note events with frame times (JSON) for the piano-roll component")
    ev.add_argument("scores", nargs="+", help="score text files; several are chained back to back (the timbre demo)")
    ev.add_argument("--out", required=True, help="events JSON to write")
    ev.add_argument("--offset", type=float, default=0.0, help="seconds into the bound audio clip at which music_init fired (added to every t; default 0)")
    ev.add_argument("--fps", type=float, default=GB_FPS, help="frames per second (default 59.7275, the Game Boy)")
    ev.set_defaults(func=cmd_events)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
