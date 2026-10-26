"""Listen to a GBC ROM headless in PyBoy and report what the four sound channels do.

Runs the ROM several times with identical input (PyBoy is deterministic): once with the normal
stereo mix (for the WAV) and once per channel with NR51 (0xFF25) forced to that channel alone
after every frame, so each channel can be analysed on its own. Two measurement windows:
  title  after --pre (default `wait:150`), --title-seconds of audio (default 3)
  play   after --script (default `press:start;wait:60`), --seconds of audio (default 10)
Per window and channel: active frames (RMS above a floor), distinct pitches (autocorrelation pitch
per frame, rounded to MIDI), pitch changes, note onsets, arpeggio runs (the pitch stepping every 2..6
frames through >= 3 notes: the chord-cycle idiom), drum hits on the noise channel. `music_detected`
means >= 2 channels active over >= 15% of the window and >= 8 pitch changes on the tonal channels
(not one static tone). `music_during_gameplay` is the play window's music_detected.

Writes <out>/audio_report.json, <out>/audio.wav (the play window, stereo) and <out>/pianoroll.png
(per-channel pitch over time, noise as hits) and prints the report as a final JSON line.
If this PyBoy cannot sample sound, falls back to the readable APU registers (NR52 channel flags,
envelopes): activity only, no pitch; the report then says "samples": false.

Example:
  python scripts/audio_probe.py --rom output/dist/game.gbc --out output/qa/audio --seconds 10
Steps for --pre/--script: wait:<frames> press:<btn> hold:<btn>:<frames> hold:<btn> release:<btn>, separated by ';'.
"""
from __future__ import annotations

import argparse
import json
import math
import struct
import sys
import wave
from pathlib import Path

try:
    import numpy as np
except ImportError:  # pragma: no cover
    sys.exit("audio_probe.py: numpy is required (use tools/pyenv)")

BUTTONS = ("up", "down", "left", "right", "a", "b", "start", "select")
NAMES = ("pulse1", "pulse2", "wave", "noise")
NR51 = 0xFF25
NR52 = 0xFF26
ACTIVE_RATIO = 0.15
MIN_PITCH_CHANGES = 8
MIN_CHANNELS = 2
ARP_STEP = (2, 6)      # frames per note for an arpeggio run
ARP_MIN_CHANGES = 6    # consecutive pitch changes that make a run


class ScriptError(Exception):
    pass


def parse_script(text: str) -> list[tuple[str, str | None, int | None]]:
    steps: list[tuple[str, str | None, int | None]] = []
    for raw in text.split(";"):
        step = raw.strip()
        if not step:
            continue
        parts = step.split(":")
        op = parts[0].lower()
        try:
            if op == "wait" and len(parts) == 2:
                steps.append(("wait", None, int(parts[1])))
            elif op == "press" and len(parts) == 2 and parts[1].lower() in BUTTONS:
                steps.append(("press", parts[1].lower(), 6))
            elif op == "hold" and len(parts) in (2, 3) and parts[1].lower() in BUTTONS:
                steps.append(("hold", parts[1].lower(), int(parts[2]) if len(parts) == 3 else None))
            elif op == "release" and len(parts) == 2 and parts[1].lower() in BUTTONS:
                steps.append(("release", parts[1].lower(), None))
            elif op == "shot":
                continue  # accepted for script compatibility; this probe takes no screenshots
            else:
                raise ValueError
        except ValueError:
            raise ScriptError(f"bad step {step!r}: wait:<frames> | press:<btn> | hold:<btn>[:<frames>] | release:<btn>") from None
    return steps


# ---------------------------------------------------------------- emulation


class Run:
    """One deterministic pass over the ROM; `solo` = channel index to isolate via NR51, or None."""

    def __init__(self, rom: Path, rate: int, solo: int | None) -> None:
        from pyboy import PyBoy  # type: ignore
        try:
            self.pb = PyBoy(str(rom), window="null", cgb=True, sound_emulated=True, sound_sample_rate=rate, sound_volume=100)
            self.samples_ok = True
        except TypeError:
            self.pb = PyBoy(str(rom), window="null", cgb=True)
            self.samples_ok = False
        self.pb.set_emulation_speed(0)
        self.solo = solo
        self.mask = 0x11 << solo if solo is not None else None
        self.overrides = 0
        self.frames = 0
        self.held: set[str] = set()

    def tick(self, collect: list | None, regs: list | None) -> None:
        if self.mask is not None:
            self.pb.memory[NR51] = self.mask
        self.pb.tick(1, False, True)
        self.frames += 1
        if self.mask is not None and (self.pb.memory[NR51] & 0xFF) != self.mask:
            self.overrides += 1
        if collect is not None:
            if self.samples_ok:
                try:
                    buf = self.pb.sound.ndarray
                    collect.append(np.array(buf, dtype=np.int16, copy=True))
                except Exception:
                    self.samples_ok = False
                    collect.append(np.zeros((0, 2), dtype=np.int16))
            else:
                collect.append(np.zeros((0, 2), dtype=np.int16))
        if regs is not None:
            m = self.pb.memory
            regs.append((m[NR52] & 0x0F, m[0xFF12], m[0xFF17], m[0xFF1C], m[0xFF21]))

    def run_steps(self, steps) -> None:
        for op, btn, n in steps:
            if op == "wait":
                for _ in range(n or 0):
                    self.tick(None, None)
            elif op == "press":
                self.pb.button_press(btn)
                for _ in range(6):
                    self.tick(None, None)
                self.pb.button_release(btn)
            elif op == "hold":
                self.pb.button_press(btn)
                self.held.add(btn)
                if n is not None:
                    for _ in range(n):
                        self.tick(None, None)
                    self.pb.button_release(btn)
                    self.held.discard(btn)
            elif op == "release":
                self.pb.button_release(btn)
                self.held.discard(btn)

    def measure(self, frames: int) -> tuple[list, list]:
        collect: list = []
        regs: list = []
        for _ in range(frames):
            self.tick(collect, regs)
        return collect, regs

    def stop(self) -> None:
        self.pb.stop(save=False)


# ---------------------------------------------------------------- analysis


def _pitch(x: np.ndarray, rate: int) -> tuple[float, float]:
    """(frequency Hz, periodicity 0..1) of a mono window by autocorrelation; 0 Hz when aperiodic.
    The first clear peak after the autocorrelation's first dip below zero is the period (later peaks are its
    multiples, so taking the first one avoids sub-octave errors); the value is unbiased for the shorter overlap."""
    n = len(x)
    if n < 64:
        return 0.0, 0.0
    x = x - x.mean()
    if not np.any(x):
        return 0.0, 0.0
    size = 1 << int(math.ceil(math.log2(2 * n)))
    spec = np.fft.rfft(x, size)
    r = np.fft.irfft(spec * np.conj(spec), size)[:n]
    if r[0] <= 0:
        return 0.0, 0.0
    r = r / r[0]
    lag_min = max(2, int(rate / 2200))
    lag_max = min(int(n * 0.7), int(rate / 28))
    if lag_max <= lag_min:
        return 0.0, 0.0
    neg = np.nonzero(r[lag_min:lag_max] < 0)[0]
    start = lag_min + int(neg[0]) if len(neg) else lag_min
    if start + 2 >= lag_max:
        return 0.0, 0.0
    unb = r[start:lag_max] * (n / (n - np.arange(start, lag_max)))
    best = float(unb.max())
    if best < 0.6:
        return 0.0, best
    # first local maximum that comes close to the best one
    lag = None
    for i in range(1, len(unb) - 1):
        if unb[i] >= unb[i - 1] and unb[i] >= unb[i + 1] and unb[i] >= 0.85 * best:
            lag = start + i
            break
    if lag is None:
        lag = start + int(np.argmax(unb))
    peak = float(unb[lag - start])
    if 1 <= lag < n - 1:  # parabolic refinement
        a, b, c = r[lag - 1], r[lag], r[lag + 1]
        denom = a - 2 * b + c
        if denom != 0:
            lag = lag + 0.5 * (a - c) / denom
    return rate / lag, min(1.0, peak)


def _midi(freq: float) -> int:
    return int(round(69 + 12 * math.log2(freq / 440.0))) if freq > 0 else 0


def _note_name(n: int) -> str:
    return ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"][n % 12] + str(n // 12 - 1)


def analyse_channel(frames: list[np.ndarray], rate: int, tonal: bool, wide: bool = False) -> dict:
    """Per-frame activity, pitch and onset analysis for one solo channel. `wide` widens the pitch window to
    two frames (the wave bass reaches 32 Hz; pulses change pitch every 3 frames in an arpeggio and use one)."""
    mono = [f.mean(axis=1) if f.ndim == 2 and f.shape[0] else np.zeros(0) for f in frames]
    rms = np.array([float(np.sqrt(np.mean((m - m.mean()) ** 2))) if len(m) else 0.0 for m in mono])
    peak = float(rms.max()) if len(rms) else 0.0
    floor = max(0.35, peak * 0.04)
    active = rms > floor
    notes = np.zeros(len(mono), dtype=int)
    if tonal:
        for i, m in enumerate(mono):
            if not active[i]:
                continue
            win = np.concatenate([mono[i - 1], m]) if (wide and i > 0) else m
            f, per = _pitch(win.astype(np.float64), rate)
            if f > 0 and per >= 0.6:
                notes[i] = _midi(f)
        active = active & (notes > 0)
    n_active = int(active.sum())
    out: dict = {"active_frames": n_active, "active_ratio": round(n_active / max(1, len(mono)), 3), "peak_rms": round(peak, 2)}
    onsets = 0
    prev_on = False
    prev_rms = 0.0
    last_note = 0      # last pitch heard, kept across gaps of up to 3 frames (a pitch detector miss is not a rest)
    gap = 99
    changes = 0
    change_frames: list[tuple[int, int]] = []
    for i in range(len(mono)):
        on = bool(active[i])
        if on:
            if tonal and last_note and gap <= 3 and notes[i] != last_note:
                changes += 1
                change_frames.append((i, int(notes[i])))
            if gap > 3 or rms[i] > prev_rms * 1.6 + 0.5:
                onsets += 1
            if tonal:
                last_note = int(notes[i])
            gap = 0
        else:
            gap += 1
            if gap > 3:
                last_note = 0
        prev_on, prev_rms = on, float(rms[i])
    out["onsets"] = onsets
    if tonal:
        pitches = sorted({int(n) for n in notes if n > 0})
        out["distinct_pitches"] = len(pitches)
        out["pitches"] = [_note_name(n) for n in pitches][:24]
        out["pitch_changes"] = changes
        out["arpeggio"] = _arpeggio(change_frames)
        out["notes"] = [int(n) for n in notes]   # for the piano roll; trimmed from the report later
    else:
        out["hits"] = onsets
    return out


def _arpeggio(change_frames: list[tuple[int, int]]) -> dict:
    """Runs of >= ARP_MIN_CHANGES pitch changes spaced ARP_STEP frames apart through >= 3 notes."""
    runs = []
    i = 0
    while i < len(change_frames):
        j = i
        while j + 1 < len(change_frames) and ARP_STEP[0] <= change_frames[j + 1][0] - change_frames[j][0] <= ARP_STEP[1]:
            j += 1
        if j - i + 1 >= ARP_MIN_CHANGES:
            seg = change_frames[i:j + 1]
            pcs = {n for _, n in seg}
            if len(pcs) >= 3:
                gaps = [seg[k + 1][0] - seg[k][0] for k in range(len(seg) - 1)]
                runs.append({"start_frame": seg[0][0], "frames": seg[-1][0] - seg[0][0], "changes": len(seg),
                             "step_frames": round(sum(gaps) / len(gaps), 2), "notes": [_note_name(n) for n in sorted(pcs)][:6]})
        i = j + 1
    total = sum(r["frames"] for r in runs)
    return {"detected": len(runs) >= 2 or total >= 90, "runs": len(runs), "frames": total,
            "step_frames": round(sum(r["step_frames"] for r in runs) / len(runs), 2) if runs else None,
            "example": runs[0] if runs else None}


def window_summary(chs: list[dict], frames: int, seconds: float) -> dict:
    active = [n for n, c in zip(NAMES, chs) if c["active_ratio"] >= ACTIVE_RATIO]
    pitch_changes = sum(c.get("pitch_changes", 0) for c in chs[:3])
    distinct = sum(c.get("distinct_pitches", 0) for c in chs[:3])
    onsets = sum(c.get("onsets", 0) for c in chs)
    return {
        "frames": frames, "seconds": round(seconds, 2),
        "channels_active": active, "pitch_changes": pitch_changes, "distinct_pitches": distinct,
        "onsets_per_second": round(onsets / max(0.01, seconds), 2),
        "arpeggio": any(c.get("arpeggio", {}).get("detected") for c in chs[:3]),
        "music_detected": len(active) >= MIN_CHANNELS and pitch_changes >= MIN_PITCH_CHANGES,
        "channels": {n: {k: v for k, v in c.items() if k not in ("notes", "rms_curve")} for n, c in zip(NAMES, chs)},
    }


def regs_summary(regs: list[tuple]) -> dict:
    """Fallback without samples: NR52 channel flags per frame."""
    n = len(regs)
    on = [sum(1 for r in regs if r[0] & (1 << c)) for c in range(4)]
    chs = [{"active_frames": on[c], "active_ratio": round(on[c] / max(1, n), 3)} for c in range(4)]
    active = [NAMES[c] for c in range(4) if chs[c]["active_ratio"] >= ACTIVE_RATIO]
    return {"frames": n, "channels_active": active, "pitch_changes": None, "music_detected": None,
            "channels": dict(zip(NAMES, chs)), "note": "registers only: NRx3 are write-only, so no pitch"}


# ---------------------------------------------------------------- outputs


def write_wav(path: Path, frames: list[np.ndarray], rate: int) -> int:
    data = np.concatenate([f for f in frames if f.shape[0]]) if any(f.shape[0] for f in frames) else np.zeros((0, 2), dtype=np.int16)
    pcm = (np.clip(data, -128, 127).astype(np.int16) * 256).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    return int(pcm.shape[0])


# Dark chart surface and the categorical slots stepped for it (one hue per channel, fixed order).
SURFACE = (0x1A, 0x1A, 0x19)
INK = (0xF0, 0xEF, 0xEC)
MUTED = (0x89, 0x87, 0x81)
GRID = (0x2C, 0x2C, 0x2A)
SERIES = ((0x39, 0x87, 0xE5), (0xD9, 0x59, 0x26), (0x19, 0x9E, 0x70), (0xC9, 0x85, 0x00))


def draw_pianoroll(path: Path, title: str, windows: list[tuple[str, list[dict], list[np.ndarray] | None]], fps: float) -> None:
    from PIL import Image, ImageDraw  # type: ignore
    total_frames = sum(len(w[1][0]["notes"]) for w in windows)
    px = 2 if total_frames <= 700 else 1
    left, top, lane_h, noise_h, gap = 46, 56, 120, 44, 18
    lo_note, hi_note = 30, 102
    width = left + total_frames * px + 16
    height = top + 3 * (lane_h + gap) + noise_h + 28
    im = Image.new("RGB", (width, height), SURFACE)
    d = ImageDraw.Draw(im)
    d.text((left, 8), title, fill=INK)
    d.text((left, 22), "pitch per frame per channel (autocorrelation on the solo mix); x = time", fill=MUTED)
    x0 = left
    for wname, chs, _ in windows:
        n = len(chs[0]["notes"])
        for c in range(3):
            y0 = top + c * (lane_h + gap)
            if x0 == left:
                d.text((left + 4, y0 - 12), NAMES[c], fill=SERIES[c])
                for octave in range(36, hi_note, 12):
                    y = y0 + lane_h - (octave - lo_note) * lane_h / (hi_note - lo_note)
                    d.line([(left, y), (width - 8, y)], fill=GRID)
                    d.text((4, y - 5), _note_name(octave), fill=MUTED)
            notes = chs[c]["notes"]
            i = 0
            while i < n:
                if notes[i] <= 0:
                    i += 1
                    continue
                j = i
                while j + 1 < n and notes[j + 1] == notes[i]:
                    j += 1
                nn = max(lo_note, min(hi_note, notes[i]))
                y = y0 + lane_h - (nn - lo_note) * lane_h / (hi_note - lo_note)
                d.rectangle([x0 + i * px, y - 1, x0 + (j + 1) * px - 1, y + 1], fill=SERIES[c])
                i = j + 1
        y0 = top + 3 * (lane_h + gap)
        if x0 == left:
            d.text((left + 4, y0 - 12), NAMES[3], fill=SERIES[3])
        hits = chs[3].get("rms_curve") or []
        for i, v in enumerate(hits):
            if v > 0:
                h = max(1, int(v * noise_h))
                d.line([(x0 + i * px, y0 + noise_h), (x0 + i * px, y0 + noise_h - h)], fill=SERIES[3])
        d.line([(x0, top - 6), (x0, height - 20)], fill=MUTED)
        d.text((x0 + 3, height - 18), f"{wname} window: {n / fps:.1f} s", fill=MUTED)
        x0 += n * px
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)


# ---------------------------------------------------------------- main


def probe(rom: Path, out: Path, *, pre: str, script: str, title_s: float, play_s: float, rate: int, fps: float,
          want_wav: bool, want_png: bool) -> dict:
    pre_steps, steps = parse_script(pre), parse_script(script)
    title_frames, play_frames = int(round(title_s * fps)), int(round(play_s * fps))
    report: dict = {"ok": True, "rom": str(rom), "sample_rate": rate, "pre": pre, "script": script,
                    "title_seconds": title_s, "seconds": play_s}
    passes: dict[int | None, tuple[list, list, list, list, int, int]] = {}
    samples = True
    for solo in (None, 0, 1, 2, 3):
        r = Run(rom, rate, solo)
        try:
            r.run_steps(pre_steps)
            t_audio, t_regs = r.measure(title_frames)
            r.run_steps(steps)
            p_audio, p_regs = r.measure(play_frames)
            passes[solo] = (t_audio, t_regs, p_audio, p_regs, r.overrides, r.frames)
            samples = samples and r.samples_ok
        finally:
            r.stop()
        if not samples:
            break
    report["samples"] = samples
    report["frames_emulated"] = passes[None][5]
    if samples:
        overrides = sum(passes[s][4] for s in (0, 1, 2, 3))
        report["panning_overridden_frames"] = overrides
        report["solo_reliable"] = overrides < 0.1 * (title_frames + play_frames) * 4
        windows = []
        for wname, idx, secs in (("title", 0, title_s), ("play", 2, play_s)):
            chs = [analyse_channel(passes[c][idx], rate, tonal=(c < 3), wide=(c == 2)) for c in range(4)]
            # noise RMS curve for the picture
            nz = passes[3][idx]
            rms = np.array([float(np.sqrt(np.mean((f.mean(axis=1) - f.mean()) ** 2))) if f.shape[0] else 0.0 for f in nz])
            chs[3]["rms_curve"] = [float(v / rms.max()) if rms.max() > 0 else 0.0 for v in rms]
            report[wname] = window_summary(chs, len(passes[None][idx]), secs)
            windows.append((wname, chs, passes[None][idx]))
        report["music_detected"] = bool(report["title"]["music_detected"] or report["play"]["music_detected"])
        report["music_during_gameplay"] = bool(report["play"]["music_detected"])
        if want_wav:
            n = write_wav(out / "audio.wav", passes[None][2], rate)
            report["wav"] = str(out / "audio.wav")
            report["wav_samples"] = n
        if want_png:
            try:
                draw_pianoroll(out / "pianoroll.png", f"{rom.name}: audio probe", windows, fps)
                report["png"] = str(out / "pianoroll.png")
            except Exception as exc:  # Pillow missing or odd data: the numbers still stand
                report["png_error"] = f"{type(exc).__name__}: {exc}"
    else:
        report["title"] = regs_summary(passes[None][1])
        report["play"] = regs_summary(passes[None][3])
        report["music_detected"] = None
        report["music_during_gameplay"] = None
        report["note"] = "this PyBoy cannot sample sound; activity from NR52 flags only"
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="\n".join(__doc__.splitlines()[1:]))
    ap.add_argument("--rom", required=True, help="path to the .gbc ROM")
    ap.add_argument("--out", default="output/qa/audio", help="report directory (default output/qa/audio)")
    ap.add_argument("--pre", default="wait:150", help="steps before the title window (default wait:150)")
    ap.add_argument("--script", default="press:start;wait:60", help="steps between the title and play windows (default press:start;wait:60)")
    ap.add_argument("--title-seconds", type=float, default=3.0, help="length of the title window (default 3)")
    ap.add_argument("--seconds", type=float, default=10.0, help="length of the play window (default 10)")
    ap.add_argument("--rate", type=int, default=32768, help="sample rate for the emulated APU (default 32768)")
    ap.add_argument("--no-wav", action="store_true", help="skip audio.wav")
    ap.add_argument("--no-png", action="store_true", help="skip pianoroll.png")
    args = ap.parse_args()

    rom = Path(args.rom)
    if not rom.is_file():
        sys.exit(f"audio_probe.py: ROM not found: {rom}")
    if args.seconds <= 0 or args.title_seconds < 0:
        sys.exit("audio_probe.py: --seconds must be > 0 and --title-seconds >= 0")
    try:
        from pyboy import PyBoy  # noqa: F401
    except ImportError:
        sys.exit("audio_probe.py: pyboy is not installed in this python (use tools/pyenv)")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    try:
        report = probe(rom, out, pre=args.pre, script=args.script, title_s=args.title_seconds, play_s=args.seconds,
                       rate=args.rate, fps=4194304 / 70224, want_wav=not args.no_wav, want_png=not args.no_png)
    except ScriptError as exc:
        sys.exit(f"audio_probe.py: {exc}")
    (out / "audio_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    report["report"] = str(out / "audio_report.json")
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
