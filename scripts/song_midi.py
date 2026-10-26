"""Export a music score (compose.py's text format) as a Standard MIDI File.

  python song_midi.py <score.txt> --out song.mid [--loops 1] [--vibrato cc|bend|none] [--report <json>]

The score is parsed with compose.py (imported as a library from this directory) and replayed the way the
Game Boy driver (music.c) would play it, frame by frame at 59.7275 frames per second:
  - one MIDI track per lane: pulse 1 (lead), pulse 2 (arpeggio / echo), wave (bass), noise (drums on channel 10);
  - a General MIDI program per role: pulse 1 = 80 Lead 1 (square), pulse 2 = 81 Lead 2 (sawtooth), wave = by table
    (38 Synth Bass 1; triangle / sine tables 39 Synth Bass 2; bell 14 Tubular Bells; organ tables 16 Drawbar Organ);
  - a chord arpeggio (`F#4:maj7`) is expanded into its notes, one every `arp:` frames, exactly as the driver cycles it;
    trills and mordents alternate per frame; a 32nd pair (`C5>D5`) strikes its second note mid-row;
  - a resolving bend (`/-2,6`), a portamento (`G4=6`), an instrument pitch envelope (`penv=`) and a raw slide (`/-6`)
    become pitch-bend events (bend range set to 12 semitones with RPN 0), following the driver's period-linear glide;
  - vibrato becomes CC1 (modulation) by default, pitch bend with --vibrato bend, or nothing;
  - a pan (`C5<` / `E5>` / `G5^` markers, `echo:5,3,R`, an instrument's `pan=L|R|LR:N`) becomes CC10 (0 left, 64 centre,
    127 right) on the lane's track at the frame the side changes; an auto-pan emits CC10 per flip; a score without
    pans gets no CC10 at all (the file is byte-identical to before);
  - `v9` sets velocity (vol 0..15 -> 7..127), `!3` cuts the note, a wave `decay=` ends the note on its own,
    `echo:5,3` copies pulse 1 onto the pulse-2 track N frames late and quieter until `echo:off` or a real pulse-2 note;
  - the kit letters map to GM percussion (K 36 kick, S 38 snare, H 42 closed hat, O 46 open hat, T 45 tom, C 49 crash,
    B 36, Q 40, P 38, N 38, M 56, t 47, X 51, c 49, D 37, Z 54; ghost letters k s h keep their quieter velocity);
  - tempo = `rows / beats` rows per quarter note at `frames_per_row` frames per row (bpm 100 = 9 frames per row on
    the 16-row grid); PPQ = 8 x rows-per-beat x frames_per_row so every frame is exactly 8 ticks; the time signature
    follows `beats:` (16 rows = 4/4; a 12-row `beats: 4` swing bar is 4/4 with each row a triplet eighth).
Tremolo (`%`) is not exported (a hardware level step; MIDI has no equivalent on these channels). --loops N appends the
loop body (from `loop:`) N-1 more times.

Prints a final JSON line {"ok": true, "out", "song", "bpm", "seconds", "ppq", "cells", "midi_notes", "tracks": [...]}.
`cells` is the number of note cells in the score (the same count as compose.py's compile report `notes`);
`midi_notes` counts the notes after arpeggio / trill / echo expansion.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import re
import struct
import sys
from pathlib import Path

NOTE_START = re.compile(r"^[A-Ga-g][#b]?-?\d")

FPS = 4194304 / 70224          # Game Boy frame rate, 59.7275 Hz
TICKS_PER_FRAME = 8
BEND_RANGE = 12                # semitones, set with RPN 0 on every tonal track
MUSIC_STACK_FRAMES = 3         # second drum of a cell stack (music.h)
DRUM_FRAMES = 4                # MIDI length of a drum hit (GM percussion ignores note-off)

# music.c period table: MIDI 36..107 -> 11-bit period. The wave channel plays the same table an octave lower, so pitch
# ratios (what a bend sounds like) are identical for all three tonal channels.
PERIOD_TABLE = [
    44, 156, 262, 363, 457, 547, 631, 710, 786, 854, 923, 986,
    1046, 1102, 1155, 1205, 1253, 1297, 1339, 1379, 1417, 1452, 1486, 1517,
    1546, 1575, 1602, 1627, 1650, 1673, 1694, 1714, 1732, 1750, 1767, 1783,
    1798, 1812, 1825, 1837, 1849, 1860, 1871, 1881, 1890, 1899, 1907, 1915,
    1923, 1930, 1936, 1943, 1949, 1954, 1959, 1964, 1969, 1974, 1978, 1982,
    1985, 1989, 1992, 1995, 1998, 2001, 2004, 2006, 2009, 2011, 2013, 2015,
]
TABLE_BASE = 36

LANE_NAMES = ("pulse 1 lead", "pulse 2 arp/echo", "wave bass", "noise drums")
LANE_CHANNELS = (0, 1, 2, 9)                    # MIDI channels 1, 2, 3, 10
PULSE_PROGRAMS = {0: 80, 1: 81}                 # Lead 1 (square), Lead 2 (sawtooth)
WAVE_PROGRAMS = {"tri": 39, "tri2": 39, "tridip": 39, "sine": 39, "soft": 39, "bell": 14, "organ": 16, "organ2": 16}
WAVE_DEFAULT_PROGRAM = 38                       # Synth Bass 1
GM_DRUMS = {"K": 36, "k": 36, "S": 38, "s": 38, "H": 42, "h": 42, "O": 46, "T": 45, "C": 49,
            "B": 36, "Q": 40, "P": 38, "N": 38, "M": 56, "t": 47, "X": 51, "c": 49, "D": 37, "Z": 54}
GM_DRUM_DEFAULT = 38


# ---------------------------------------------------------------- compose.py as a library


def load_compose():
    """Import compose.py from this directory, $GBC_MUSIC_DIR (or its scripts/), or ./scripts/ in the cwd."""
    here = Path(__file__).resolve().parent
    env = os.environ.get("GBC_MUSIC_DIR")
    candidates = [
        here / "compose.py",
        Path(env) / "compose.py" if env else None,
        Path(env) / "scripts" / "compose.py" if env else None,
        Path.cwd() / "scripts" / "compose.py",                 # a project that vendored the scripts
    ]
    for c in candidates:
        if c and c.is_file():
            spec = importlib.util.spec_from_file_location("compose", c)
            mod = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(mod)
            return mod
    sys.exit("song_midi.py: compose.py not found (expected next to this script, under $GBC_MUSIC_DIR, or in ./scripts/)")


# ---------------------------------------------------------------- pitch helpers


def period_of(note: int) -> int:
    idx = max(0, min(len(PERIOD_TABLE) - 1, note - TABLE_BASE))
    return PERIOD_TABLE[idx]


def period_semis(period: float, ref_period: int) -> float:
    """Semitone offset of a period relative to the reference period (pulse formula 131072 / (2048 - p))."""
    p = max(0.0, min(2047.0, period))
    if ref_period >= 2048:
        return 0.0
    return 12.0 * math.log2((2048.0 - ref_period) / (2048.0 - p))


def glide_curve(from_p: int, to_p: int, n: int) -> list[float]:
    """The driver's period-linear glide: offsets per frame (frame 0 = full offset, frame n = 0), as semitones."""
    n = max(1, n)
    d = from_p - to_p
    step = -int(d / n) if d else 0                  # C integer division truncates towards zero
    out = []
    cur = d
    for k in range(n):
        out.append(period_semis(to_p + cur, to_p))
        cur = cur + step if k + 1 < n else 0
    return out


def tri8(phase: int) -> int:
    q = phase & 0x0F
    v = q if q < 8 else 16 - q
    return v - 4


# ---------------------------------------------------------------- the frame-level replay


PAN_CC = {1: 127, 2: 0, 3: 64}           # NR51 side (1 right, 2 left, 3 both) -> CC10


class Note:
    __slots__ = ("lane", "start", "dur", "midi", "vel", "program", "bends", "cc1")

    def __init__(self, lane: int, start: int, dur: int, midi: int, vel: int, program: int | None):
        self.lane, self.start, self.dur, self.midi, self.vel, self.program = lane, start, dur, midi, vel, program
        self.bends: list[tuple[int, float]] = []     # (frame, semitone offset) during the note
        self.cc1: int | None = None                  # modulation depth to send at note start


def velocity(vol: int) -> int:
    return max(1, min(127, 8 * max(0, min(15, vol)) + 7))


def wave_program(shape: str) -> int:
    return WAVE_PROGRAMS.get(shape.split(",")[0], WAVE_DEFAULT_PROGRAM)


class Replay:
    """Walk the score bar by bar and emit notes the way music.c plays them."""

    def __init__(self, compose, song, loops: int, vibrato: str) -> None:
        self.compose = compose
        self.song = song
        self.vibrato = vibrato
        self.fpr = song.fpr
        self.rows = song.rows
        self.arp_speed = song.arp
        n_bars = max(song.bars) + 1
        self.sequence = list(range(n_bars)) + [b for _ in range(max(0, loops - 1)) for b in range(song.loop, n_bars)]
        self.total_frames = len(self.sequence) * self.rows * self.fpr
        self.notes: list[Note] = []
        self.cells = 0
        self.lane_state = [{"inst": 0, "vol": 15, "note": None, "prev_period": None} for _ in range(4)]
        self.echo_segments: list[tuple[int, int, int, int]] = []     # (start, end, delay, drop)
        self.open_echo: tuple[int, int, int] | None = None
        self.echo_side = False
        self.pan_state = [3, 3]                                       # pulse lanes' sides, as the driver tracks them
        self.pans: list[list[tuple[int, int]]] = [[], []]             # per pulse lane: (frame, CC10 value) at each change
        self.warnings: list[str] = list(song.warnings)

    def set_pan(self, lane: int, side: int, frame: int) -> None:
        if lane < 2 and side and self.pan_state[lane] != side:
            self.pan_state[lane] = side
            self.pans[lane].append((frame, PAN_CC[side]))

    # -- instrument helpers
    def inst(self, lane: int):
        name, typ, kv = self.song.insts[self.lane_state[lane]["inst"]]
        return name, typ, kv

    def inst_program(self, lane: int) -> int | None:
        _, typ, kv = self.inst(lane)
        if lane == 3:
            return None
        if typ == "wave":
            return wave_program(kv.get("shape", "saw"))
        return PULSE_PROGRAMS.get(lane, 80)

    def inst_vol(self, lane: int) -> int:
        _, typ, kv = self.inst(lane)
        if typ == "wave":
            return max(0, min(15, int(kv.get("vol", "12"))))
        return (int(kv.get("env", "F2"), 16) >> 4) & 0x0F

    # -- the walk
    def run(self) -> None:
        song = self.song
        FX = self.compose.FX
        # First pass: collect every cell as (lane, frame, span_frames, parsed) so a note knows where it ends.
        cells: list[list[tuple[int, int, str]]] = [[] for _ in range(4)]       # per lane: (frame, row_in_bar, cell)
        for seq_i, bar in enumerate(self.sequence):
            lanes = song.bars.get(bar, {})
            for lane in range(4):
                row_cells = lanes.get(lane) or ["."] * self.rows
                for row, cell in enumerate(row_cells):
                    if cell == ".":
                        continue
                    frame = (seq_i * self.rows + row) * self.fpr
                    cells[lane].append((frame, row, cell))
        # a tonal note ends at the next cell on its lane that carries a note or a key-off (effect-only cells such as
        # `echo:5,3`, `arpspeed:4`, `~`, `v6` leave the held note sounding, as in the driver)
        for lane in range(4):
            lst = cells[lane]
            for i, (frame, row, cell) in enumerate(lst):
                end = self.total_frames
                if lane != 3:
                    for j in range(i + 1, len(lst)):
                        nxt = lst[j][2]
                        if nxt in ("-", "off") or NOTE_START.match(nxt):
                            end = lst[j][0]
                            break
                self.play_cell(lane, frame, end, cell, row)
        if self.open_echo:
            start, delay, drop = self.open_echo
            self.echo_segments.append((start, self.total_frames, delay, drop))
        self.apply_echo()

    def play_cell(self, lane: int, frame: int, end: int, cell: str, row: int) -> None:
        compose = self.compose
        FX = compose.FX
        st = self.lane_state[lane]
        if cell in ("-", "off"):
            return
        if lane == 3:
            if cell.startswith("v") and cell[1:].isdigit():
                return                                     # the driver's noise channel ignores v (drum presets carry their own volume)
            self.cells += 1
            letters = cell[:2]
            for k, letter in enumerate(letters):
                d = self.song.drums.get(letter)
                if d is None:
                    self.warnings.append(f"unknown drum letter {letter!r}")
                    continue
                vol = (d[0] >> 4) & 0x0F
                self.notes.append(Note(3, frame + k * MUSIC_STACK_FRAMES, DRUM_FRAMES, GM_DRUMS.get(letter, GM_DRUM_DEFAULT), velocity(vol), None))
            return
        # tonal cell: let compose.py parse it so the grammar lives in one place
        comp = compose.Compiled(self.song)
        try:
            note, inst_fx, param = compose.compile_cell(comp, lane, cell, 0, row)
        except compose.ScoreError as exc:
            self.warnings.append(str(exc))
            return
        inst_id, fx = inst_fx >> 4, inst_fx & 0x0F
        pan = 0
        if lane < 2 and note & compose.PAN_NOTE and note != compose.MUSIC_OFF:   # pan pseudo-note: a side change on an effect-only cell
            pan, note = note & 0x03, 0
        if fx == FX["pan"]:
            pan = param & 0x03
        if inst_id:
            st["inst"] = inst_id - 1
            st["vol"] = self.inst_vol(lane)
        if fx == FX["vol"]:
            st["vol"] = param & 0x0F
        if fx == FX["arpspeed"] and param:
            self.arp_speed = param
        if fx == FX["echo"] and lane == 1:
            if self.open_echo:
                s, d, dr = self.open_echo
                self.echo_segments.append((s, frame, d, dr))
                self.open_echo = None
            if self.echo_side and not param:
                self.set_pan(1, 3, frame)
                self.echo_side = False
            if param:
                self.open_echo = (frame, param >> 4, param & 0x0F)
                if pan:
                    self.echo_side = True
            self.set_pan(lane, pan, frame)
            return
        if not note:
            self.set_pan(lane, pan, frame)
            return
        self.cells += 1
        if lane == 1 and self.open_echo:                       # a real pulse-2 note ends echo mode (and its side)
            s, d, dr = self.open_echo
            self.echo_segments.append((s, frame, d, dr))
            self.open_echo = None
            if self.echo_side:
                self.set_pan(1, 3, frame)
                self.echo_side = False
        span = max(1, end - frame)
        if fx == FX["cut"]:
            span = min(span, max(1, param))
        name, typ, kv = self.inst(lane)
        if typ == "wave" and "decay" in kv:
            span = min(span, 3 * max(1, int(kv["decay"])))
        if lane < 2 and typ == "pulse" and "pan" in kv:        # instrument pan: a side per note, or an auto-pan (CC10 per flip)
            m = re.fullmatch(r"(?i)(C|L|R|LR)(?::(\d+))?", kv["pan"].strip())
            if m and m.group(1).upper() == "LR":
                period = int(m.group(2)) if m.group(2) else (int(kv["rate"]) if "rate" in kv and "," not in kv.get("duty", "") else compose.PAN_AUTO_DEFAULT)
                side = 2
                for k in range(0, span, max(1, period)):
                    self.set_pan(lane, side, frame + k)
                    side = 1 if side == 2 else 2
            elif m:
                self.set_pan(lane, compose.PAN[m.group(1).upper()], frame)
        self.set_pan(lane, pan, frame)                         # the cell's own pan wins over the instrument's
        # per-frame pitch (MIDI note) and bend offset (semitones)
        pitches = [note] * span
        bend = [0.0] * span
        target_p = period_of(note)
        if fx == FX["arp"]:
            ivs = comp.chord_list[param]
            slot, t = 0, self.arp_speed
            for k in range(span):
                if t == 0:
                    t = self.arp_speed
                    slot = slot + 1
                    if slot >= len(ivs):
                        slot = 0
                t -= 1
                pitches[k] = note + ivs[slot]
        elif fx == FX["trill"]:
            span_frames, interval = param >> 4, param & 0x0F
            for k in range(min(span, self.fpr)):
                if (span_frames == 0 or k < span_frames) and (k & 1):
                    pitches[k] = note + interval
        elif fx == FX["split"]:
            half = self.fpr >> 1
            for k in range(half, span):
                pitches[k] = param
        elif fx == FX["bend"]:
            n, so = param >> 4, param & 0x0F
            if so > 7:
                so -= 16
            curve = glide_curve(period_of(note + so), target_p, n)
            for k, v in enumerate(curve[:span]):
                bend[k] = v
        elif fx == FX["porta"]:
            if st["prev_period"] is not None:
                curve = glide_curve(st["prev_period"], target_p, param)
                for k, v in enumerate(curve[:span]):
                    bend[k] = v
        elif fx == FX["slide"]:
            delta = param - 256 if param > 127 else param
            acc = 0
            for k in range(span):
                acc += delta
                bend[k] = period_semis(target_p + acc, target_p)
        if fx not in (FX["bend"], FX["porta"]) and "penv" in kv:
            semis, frames_ = (int(x) for x in kv["penv"].lstrip("+").split(","))
            curve = glide_curve(period_of(note + semis), target_p, frames_)
            for k, v in enumerate(curve[:span]):
                bend[k] += v
        # vibrato: cell `~` or the instrument's delayed auto-vibrato
        depth, rate, delay = 0, 3, 0
        if fx == FX["vib"]:
            depth, rate = param >> 4, max(1, param & 0x0F)
        elif "vib" in kv:
            d, _, dl = kv["vib"].partition(":")
            depth, delay = int(d), 4 * int(dl or "2")
        cc1 = None
        if depth:
            if self.vibrato == "bend":
                phase = 0
                for k in range(delay, span):
                    if (k % rate) == 0:
                        phase += 1
                    bend[k] += period_semis(target_p + tri8(phase) * depth, target_p)
            elif self.vibrato == "cc":
                cc1 = min(127, depth * 16)
        # run-length merge equal pitches into notes
        program = self.inst_program(lane)
        vel = velocity(st["vol"])
        k = 0
        while k < span:
            j = k
            while j + 1 < span and pitches[j + 1] == pitches[k]:
                j += 1
            n = Note(lane, frame + k, j - k + 1, pitches[k], vel, program)
            n.bends = [(frame + i, bend[i]) for i in range(k, j + 1)]
            if cc1 is not None and k == 0:
                n.cc1 = cc1
            self.notes.append(n)
            k = j + 1
        st["prev_period"] = target_p

    def apply_echo(self) -> None:
        lead = [n for n in self.notes if n.lane == 0]
        for start, end, delay, drop in self.echo_segments:
            for n in lead:
                if start <= n.start < end:
                    e = Note(1, n.start + delay, n.dur, n.midi, velocity(max(0, (n.vel - 7) // 8 - drop)), PULSE_PROGRAMS[1])
                    e.bends = [(f + delay, b) for f, b in n.bends]
                    self.notes.append(e)


# ---------------------------------------------------------------- MIDI writer (format 1)


def vlq(n: int) -> bytes:
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append(0x80 | (n & 0x7F))
        n >>= 7
    return bytes(reversed(out))


def meta(kind: int, data: bytes) -> bytes:
    return bytes([0xFF, kind]) + vlq(len(data)) + data


def track_chunk(events: list[tuple[int, int, bytes]]) -> bytes:
    """events = (tick, priority, message bytes) -> one MTrk with delta times; priority orders same-tick events."""
    events.sort(key=lambda e: (e[0], e[1]))
    out = bytearray()
    last = 0
    for tick, _, msg in events:
        out += vlq(tick - last) + msg
        last = tick
    out += vlq(0) + meta(0x2F, b"")
    return b"MTrk" + struct.pack(">I", len(out)) + bytes(out)


def bend_value(semis: float) -> int:
    return max(0, min(16383, int(round(8192 + semis / BEND_RANGE * 8192))))


def build_midi(replay: Replay, title: str) -> tuple[bytes, dict]:
    fpr = replay.fpr
    rows = replay.rows
    beats = getattr(replay.song, "beats", rows // 4 if rows % 4 == 0 else rows)
    rpb = max(1, rows // max(1, beats))                           # rows per beat: 4 (sixteenths) or 3 (triplet eighths)
    ppq = rpb * fpr * TICKS_PER_FRAME                             # a quarter note = rpb rows
    tempo_us = int(round(rpb * fpr / FPS * 1_000_000))
    if rows % beats == 0 and rpb in (3, 4) or rows % 4 == 0 and rpb == 4:
        num, den_pow = beats, 2                                   # x/4
    elif rows % 4 == 0:
        num, den_pow = rows // 4, 2
    else:
        num, den_pow = rows, 4                                    # x/16
    conductor: list[tuple[int, int, bytes]] = [
        (0, 0, meta(0x03, title.encode("latin-1", "replace"))),
        (0, 0, meta(0x51, struct.pack(">I", tempo_us)[1:])),
        (0, 0, meta(0x58, bytes([num, den_pow, 24, 8]))),
    ]
    tracks = [track_chunk(conductor)]
    stats = []
    for lane in range(4):
        ch = LANE_CHANNELS[lane]
        ev: list[tuple[int, int, bytes]] = [(0, 0, meta(0x03, LANE_NAMES[lane].encode()))]
        notes = sorted((n for n in replay.notes if n.lane == lane), key=lambda n: n.start)
        program = None
        if lane != 3:
            # pitch bend range = BEND_RANGE semitones: RPN 0 (CC 101/100), data entry (CC 6), then RPN null
            for cc, val in ((101, 0), (100, 0), (6, BEND_RANGE), (38, 0), (101, 127), (100, 127)):
                ev.append((0, 0, bytes([0xB0 | ch, cc, val])))
        n_bends = 0
        last_bend = None
        if lane < 2:
            for f, v in replay.pans[lane]:                        # CC10 at each side change (none when the song has no pans)
                ev.append((f * TICKS_PER_FRAME, 1, bytes([0xB0 | ch, 10, v])))
        for n in notes:
            t0 = n.start * TICKS_PER_FRAME
            t1 = (n.start + n.dur) * TICKS_PER_FRAME
            if n.program is not None and n.program != program:
                program = n.program
                ev.append((t0, 1, bytes([0xC0 | ch, program])))
            if n.cc1 is not None:
                ev.append((t0, 1, bytes([0xB0 | ch, 1, n.cc1])))
            for f, semis in n.bends:
                v = bend_value(semis)
                if v != last_bend:
                    ev.append((f * TICKS_PER_FRAME, 1, bytes([0xE0 | ch, v & 0x7F, v >> 7])))
                    last_bend = v
                    n_bends += 1
            if n.bends and last_bend != 8192 and n.bends[-1][1] != 0.0:
                ev.append((t1, 0, bytes([0xE0 | ch, 0, 64])))      # centre the bend when the note ends
                last_bend = 8192
            ev.append((t0, 2, bytes([0x90 | ch, n.midi & 0x7F, n.vel])))
            ev.append((t1, 0, bytes([0x80 | ch, n.midi & 0x7F, 0])))
        tracks.append(track_chunk(ev))
        stats.append({"lane": LANE_NAMES[lane], "channel": ch + 1, "program": (program + 1) if program is not None else "drums",
                      "notes": len(notes), "bend_events": n_bends, "pan_events": len(replay.pans[lane]) if lane < 2 else 0})
    header = b"MThd" + struct.pack(">IHHH", 6, 1, len(tracks), ppq)
    info = {"ppq": ppq, "tempo_us_per_quarter": tempo_us, "time_signature": f"{num}/{1 << den_pow}", "tracks": stats}
    return header + b"".join(tracks), info


# ---------------------------------------------------------------- main


def export(score_path: Path, out: Path, loops: int = 1, vibrato: str = "cc") -> dict:
    compose = load_compose()
    default = "song_" + "".join(ch if ch.isalnum() else "_" for ch in score_path.stem).strip("_").lower()
    try:
        song = compose.parse_score(score_path.read_text(encoding="utf-8"), default)
    except compose.ScoreError as exc:
        sys.exit(f"song_midi.py: {score_path}: {exc}")
    replay = Replay(compose, song, loops, vibrato)
    replay.run()
    data, info = build_midi(replay, song.title or song.name)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    seconds = replay.total_frames / FPS
    rep = {"ok": True, "out": str(out), "song": song.name, "title": song.title, "bars": max(song.bars) + 1, "loops": loops,
           "bpm": round(song.bpm, 1), "frames_per_row": song.fpr, "frames": replay.total_frames, "seconds": round(seconds, 2),
           "cells": replay.cells, "midi_notes": len(replay.notes), "vibrato": vibrato, "bytes": len(data), **info,
           "warnings": replay.warnings}
    return rep


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="\n".join(__doc__.splitlines()[1:]))
    ap.add_argument("score", help="score text file (compose.py format)")
    ap.add_argument("--out", required=True, help="MIDI file to write, e.g. song.mid")
    ap.add_argument("--loops", type=int, default=1, help="how many times the song plays (the loop body from `loop:` is appended for loops > 1; default 1)")
    ap.add_argument("--vibrato", default="cc", choices=("cc", "bend", "none"), help="vibrato as CC1 modulation (default), as pitch-bend events, or dropped")
    ap.add_argument("--report", default=None, help="also write the JSON report here")
    args = ap.parse_args()
    p = Path(args.score)
    if not p.is_file():
        sys.exit(f"song_midi.py: score not found: {p}")
    if args.loops < 1:
        sys.exit("song_midi.py: --loops must be >= 1")
    rep = export(p, Path(args.out), args.loops, args.vibrato)
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
