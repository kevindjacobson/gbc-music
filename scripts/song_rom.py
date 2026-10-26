"""Build a standalone Game Boy Color player ROM from one or more music scores.

  python song_rom.py <score.txt>... --out song.gbc [--title "MUSIC PLAYER"] [--project <dir>] [--report <json>]

Assembles a minimal GBDK-2020 project from the files next to this script (player__Makefile, player__src__main.c, the
driver music.c / music.h), compiles the scores with compose.py (imported as a library: the same tables a game
ships), generates src/songs.h (song table, titles, bar / bpm info) and runs make. The ROM boots straight into song 1
and shows a text screen with the song title, song N/M and a live BAR / ROW counter; START / SELECT cycle songs, A
restarts, B ducks. It plays on hardware, in any emulator and through audio_probe.py (`--pre wait:60`).

Toolchain: $GBDK_HOME (the directory that contains bin/lcc), else `lcc` on PATH, else the usual install locations
(/opt/gbdk, /usr/local/gbdk, ~/gbdk, ~/gbdk-2020). The project is built in a temporary
directory unless --project keeps it (handy for inspecting src/music_data.c or hacking the player).

Prints a final JSON line {"ok": true, "out", "rom_bytes", "songs": [{"name", "title", "bars", "bpm", "seconds_per_loop",
"rom_bytes"}], "project", "gbdk"}; exits non-zero with a one-line reason (compile errors are listed) on failure.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE_FILES = {                      # flat skill-script name -> project path
    "player__Makefile": "Makefile",
    "player__src__main.c": "src/main.c",
}
DRIVER_FILES = {"music.c": "src/music.c", "music.h": "src/music.h"}
MAKE_TIMEOUT_S = 300


def _load(name: str, extra: list[Path] | None = None):
    """Import a sibling module by file: this directory, $GBC_MUSIC_DIR (or its scripts/), ./scripts/ in the cwd."""
    env = os.environ.get("GBC_MUSIC_DIR")
    env_paths = [Path(env) / name, Path(env) / "scripts" / name] if env else []
    candidates = [HERE / name, *env_paths, Path.cwd() / "scripts" / name, *(extra or [])]
    for c in candidates:
        if c.is_file():
            spec = importlib.util.spec_from_file_location(name[:-3], c)
            mod = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(mod)
            return mod
    return None


def load_compose():
    mod = _load("compose.py")
    if mod is None:
        sys.exit("song_rom.py: compose.py not found (expected next to this script, under $GBC_MUSIC_DIR, or in ./scripts/)")
    return mod


def find_gbdk() -> Path:
    """GBDK_HOME, lcc on PATH, or the usual install locations."""
    env = os.environ.get("GBDK_HOME")
    if env and (Path(env) / "bin" / "lcc").is_file():
        return Path(env)
    lcc = shutil.which("lcc")
    if lcc:
        return Path(lcc).resolve().parents[1]
    for home in (Path("/opt/gbdk"), Path("/usr/local/gbdk"), Path.home() / "gbdk", Path.home() / "gbdk-2020"):
        if (home / "bin" / "lcc").is_file():
            return home
    sys.exit("song_rom.py: GBDK not found: set GBDK_HOME to the GBDK-2020 directory that contains bin/lcc")


def template_file(flat: str) -> Path:
    """A player template file (next to this script)."""
    p = HERE / flat
    if p.is_file():
        return p
    sys.exit(f"song_rom.py: template file {flat} not found next to {HERE}")


def rom_title(title: str) -> str:
    t = re.sub(r"[^A-Z0-9 ]", "", title.upper())
    t = re.sub(r" +", " ", t).strip()[:15].strip()
    return t or "MUSIC"


def screen_text(text: str, width: int = 20) -> str:
    """Upper-case, the player font's character set, at most `width` characters, C-string safe."""
    t = re.sub(r"[^A-Za-z0-9 .!:\->?,/'+*]", "", text).strip().upper()
    t = re.sub(r" +", " ", t)[:width].strip()
    return t or "UNTITLED"


def build_rom(scores: list[Path], out: Path, title: str = "MUSIC PLAYER", project: Path | None = None) -> dict:
    compose = load_compose()
    compiled, names = [], []
    for f in scores:
        if not f.is_file():
            sys.exit(f"song_rom.py: score not found: {f}")
        default = "song_" + re.sub(r"\W+", "_", f.stem).strip("_").lower()
        try:
            song = compose.parse_score(f.read_text(encoding="utf-8"), default)
            taken = {c.song.name for c in compiled}
            if song.name in taken:                      # two `name: song_main` scores: the player keeps both
                k = 2
                while f"{song.name}_{k}" in taken:
                    k += 1
                song.name = f"{song.name}_{k}"
            compiled.append(compose.compile_song(song))
        except compose.ScoreError as exc:
            sys.exit(f"song_rom.py: {f}: {exc}")
        names.append(f.name)
    if len(compiled) > 9:
        sys.exit("song_rom.py: at most 9 songs per player ROM")
    c_text, h_text, reports = compose.emit_c(compiled, names)

    tmp = None
    if project is None:
        tmp = Path(tempfile.mkdtemp(prefix="song_rom-"))
        project = tmp
    project.mkdir(parents=True, exist_ok=True)
    (project / "src").mkdir(exist_ok=True)
    slug = re.sub(r"[^a-z0-9_-]", "", out.stem.lower()) or "song"
    tokens = {"SLUG": slug, "TITLE": screen_text(title), "ROM_TITLE": rom_title(title)}
    for flat, rel in TEMPLATE_FILES.items():
        text = template_file(flat).read_text(encoding="utf-8")
        for k, v in tokens.items():
            text = text.replace("{{" + k + "}}", v)
        (project / rel).write_text(text, encoding="utf-8")
    for flat, rel in DRIVER_FILES.items():
        shutil.copy(template_file(flat), project / rel)
    (project / "src" / "music_data.c").write_text(c_text, encoding="utf-8")
    (project / "src" / "music_data.h").write_text(h_text, encoding="utf-8")
    songs_h = ["/* songs.h -- generated by song_rom.py: the player's song table. */", "#ifndef SONGS_H", "#define SONGS_H",
               '#include "music.h"', '#include "music_data.h"', f"#define SONG_COUNT {len(compiled)}",
               f'#define PLAYER_TITLE "{tokens["TITLE"]}"',
               "static const Song *const song_table[SONG_COUNT] = { " + ", ".join(f"&{c.song.name}" for c in compiled) + " };",
               "static const char *const song_titles[SONG_COUNT] = { " + ", ".join(f'"{screen_text(c.song.title or c.song.name)}"' for c in compiled) + " };",
               "static const char *const song_infos[SONG_COUNT] = { " + ", ".join(f'"{r["bars"]} BARS {round(r["bpm"])} BPM {r["seconds_per_loop"]:.0f}S"' for r in reports) + " };",
               "#endif", ""]
    (project / "src" / "songs.h").write_text("\n".join(songs_h), encoding="utf-8")

    gbdk = find_gbdk()
    env = dict(os.environ, GBDK_HOME=str(gbdk))
    try:
        res = subprocess.run(["make"], cwd=project, env=env, capture_output=True, text=True, timeout=MAKE_TIMEOUT_S)
    except FileNotFoundError:
        sys.exit("song_rom.py: `make` is not installed or not on PATH")
    except subprocess.TimeoutExpired:
        sys.exit(f"song_rom.py: make timed out after {MAKE_TIMEOUT_S}s")
    log = res.stdout + res.stderr
    (project / "build.log").write_text(log, encoding="utf-8")
    rom = project / "build" / f"{slug}.gbc"
    if res.returncode or not rom.is_file():
        errs = [l for l in log.splitlines() if re.search(r"error|Error|ERROR|Undefined", l)]
        print(f"song_rom.py: build failed (project kept at {project})", file=sys.stderr)
        for e in errs[:5]:
            print("  " + e, file=sys.stderr)
        sys.exit(1)
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(rom, out)
    rep = {"ok": True, "out": str(out), "rom_bytes": out.stat().st_size, "title": tokens["TITLE"], "rom_title": tokens["ROM_TITLE"],
           "songs": [{"name": r["name"], "title": r["title"], "bars": r["bars"], "bpm": r["bpm"], "frames_per_row": r["frames_per_row"],
                      "seconds_per_loop": r["seconds_per_loop"], "loop_bar": r["loop_bar"], "notes": r["notes"], "rom_bytes": r["rom_bytes"],
                      "warnings": r["warnings"]} for r in reports],
           "project": str(project), "gbdk": str(gbdk)}
    if tmp is not None:
        shutil.rmtree(tmp, ignore_errors=True)
        rep["project"] = None
    return rep


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="\n".join(__doc__.splitlines()[1:]))
    ap.add_argument("scores", nargs="+", help="score text files (one song each, at most 9)")
    ap.add_argument("--out", required=True, help="ROM to write, e.g. song.gbc")
    ap.add_argument("--title", default="MUSIC PLAYER", help="player name on the screen and the cart header (default MUSIC PLAYER)")
    ap.add_argument("--project", default=None, help="keep the generated GBDK project in this directory (default: a temporary dir, deleted)")
    ap.add_argument("--report", default=None, help="also write the JSON report here")
    args = ap.parse_args()
    rep = build_rom([Path(s) for s in args.scores], Path(args.out), args.title, Path(args.project) if args.project else None)
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
