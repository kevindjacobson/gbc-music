"""Render a music score to WAV (and optionally MP3) through the real Game Boy sound chip emulation.

  python song_wav.py <score.txt>... --out song.wav [--seconds N] [--loops 1] [--mp3] [--rate 32768] [--rom <keep.gbc>] [--report <json>]

Builds the standalone player ROM with song_rom.py (so the sound is the driver and the chip, not a synthesizer
approximation), boots it in headless PyBoy with sound emulation through audio_probe.py's capture code, trims the
emulator's boot chime and the silence after it (the clip starts on the song's first sounding sample; the report's
`trimmed_s` says how much was cut) and writes 16-bit stereo PCM at --rate Hz (32768 = the APU's native rate in PyBoy). The default length
is the first score played --loops times (from its bar count and tempo) plus half a second; --seconds overrides it.
With several scores only the first one is rendered (the ROM starts on song 1); pass one score per WAV.
--mp3 also writes <out>.mp3 with lame (192 kb/s), or ffmpeg's libmp3lame when lame is not installed.

Requires PyBoy + numpy in the running python (`pip install pyboy numpy`). Prints a final JSON line
{"ok": true, "out", "seconds", "samples", "rate", "rom", "mp3", "song"}.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FPS = 4194304 / 70224


def _load(name: str):
    env = os.environ.get("GBC_MUSIC_DIR")
    extra = [Path(env) / name, Path(env) / "scripts" / name] if env else []
    for c in [HERE / name, *extra, Path.cwd() / "scripts" / name]:
        if c.is_file():
            spec = importlib.util.spec_from_file_location(name[:-3], c)
            mod = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(mod)
            return mod
    sys.exit(f"song_wav.py: {name} not found next to this script or in scripts/")


def render(rom: Path, out: Path, seconds: float, rate: int) -> dict:
    import numpy as np
    probe = _load("audio_probe.py")
    run = probe.Run(rom, rate, None)
    try:
        if not run.samples_ok:
            sys.exit("song_wav.py: this PyBoy cannot sample sound (needs sound_emulated=True support)")
        frames, _ = run.measure(int(round(seconds * FPS)) + 90)      # + boot margin, trimmed below
    finally:
        run.stop()
    data = np.concatenate([f for f in frames if f.shape[0]]) if any(f.shape[0] for f in frames) else np.zeros((0, 2), dtype=np.int16)
    nz = np.flatnonzero(np.abs(data).max(axis=1)) if data.shape[0] else np.zeros(0, dtype=int)
    start = int(nz[0]) if nz.size else 0
    # The emulator's boot ROM plays its chime before the cartridge runs (about 0.2 s of sound, then 0.4 s of silence
    # before the song's first frame). Cut at the end of the first silence gap of >= 100 ms after the first sound, so
    # the clip starts on the song's first sounding sample; a ROM without a chime keeps its first sound.
    if nz.size:
        gaps = np.flatnonzero(np.diff(nz) > rate // 10)
        if gaps.size and nz[gaps[0]] < start + 2 * rate:
            start = int(nz[gaps[0] + 1])
    want = int(round(seconds * rate))
    data = data[start:start + want]
    n = probe.write_wav(out, [data], rate)
    return {"samples": n, "seconds": round(n / rate, 2), "silent": not nz.size, "music_offset_s": 0.0,
            "trimmed_s": round(start / rate, 3)}


def encode_mp3(wav: Path, mp3: Path) -> str:
    if shutil.which("lame"):
        cmd = ["lame", "--quiet", "-b", "192", str(wav), str(mp3)]
    elif shutil.which("ffmpeg"):
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-codec:a", "libmp3lame", "-b:a", "192k", str(mp3)]
    else:
        sys.exit("song_wav.py: --mp3 needs lame or ffmpeg on PATH")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode or not mp3.is_file():
        sys.exit(f"song_wav.py: mp3 encoding failed: {(res.stderr or res.stdout).strip()[:200]}")
    return cmd[0]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="\n".join(__doc__.splitlines()[1:]))
    ap.add_argument("scores", nargs="+", help="score text file(s); the first one is rendered")
    ap.add_argument("--out", required=True, help="WAV file to write, e.g. song.wav")
    ap.add_argument("--seconds", type=float, default=None, help="length to render (default: the song's length x --loops + 0.5 s, at most 600)")
    ap.add_argument("--loops", type=int, default=1, help="how many times the song plays when --seconds is not given (default 1)")
    ap.add_argument("--rate", type=int, default=32768, help="sample rate (default 32768)")
    ap.add_argument("--mp3", action="store_true", help="also write <out>.mp3 (lame, or ffmpeg)")
    ap.add_argument("--rom", default=None, help="keep the player ROM at this path (default: a temporary file)")
    ap.add_argument("--report", default=None, help="also write the JSON report here")
    args = ap.parse_args()
    try:
        import pyboy  # noqa: F401
        import numpy  # noqa: F401
    except ImportError:
        sys.exit("song_wav.py: pyboy and numpy are required (pip install pyboy numpy)")
    song_rom = _load("song_rom.py")
    tmp = None
    rom = Path(args.rom) if args.rom else None
    if rom is None:
        tmp = Path(tempfile.mkdtemp(prefix="song_wav-"))
        rom = tmp / "song.gbc"
    built = song_rom.build_rom([Path(s) for s in args.scores], rom, "MUSIC PLAYER", None)
    first = built["songs"][0]
    seconds = args.seconds
    if seconds is None:
        full = first["seconds_per_loop"]
        loop_len = full - first["loop_bar"] * 16 * first["frames_per_row"] / FPS
        seconds = min(600.0, full + max(0, args.loops - 1) * loop_len + 0.5)
    if seconds <= 0:
        sys.exit("song_wav.py: --seconds must be > 0")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    info = render(rom, out, seconds, args.rate)
    rep = {"ok": True, "out": str(out), "rate": args.rate, "rom": str(rom) if args.rom else None, "rom_bytes": built["rom_bytes"],
           "song": first["name"], "title": first["title"], "bars": first["bars"], "bpm": first["bpm"], "mp3": None, **info}
    if args.mp3:
        mp3 = out.with_suffix(".mp3")
        rep["mp3_encoder"] = encode_mp3(out, mp3)
        rep["mp3"] = str(mp3)
        rep["mp3_bytes"] = mp3.stat().st_size
    if tmp is not None:
        shutil.rmtree(tmp, ignore_errors=True)
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
