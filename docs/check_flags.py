"""Generate a score for every style with every generator flag switched on, and compile each: the regression check
that no flavour-keyed table or flag combination crashes (the ska second-lead KeyError of 1.1 is the case that started it).

    python docs/check_flags.py [--keep DIR]

Prints PASS / FAIL per argument set and exits 1 on any failure. Only `compose.py generate` is run (seconds, no emulator).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
COMPOSE = SKILL / "scripts" / "compose.py"
ALL_ON = "--phrases 2 --hook 3 --organic 3 --pan wide --syncopation 2"
SETS = [
    f"--style ska --key G --bpm 180 --bars 48 --seed 101 {ALL_ON}",
    f"--style ska --key C --bpm 200 --bars 64 --seed 7 --progression doowop {ALL_ON}",
    f"--style ska --key F --bpm 176 --bars 32 --seed 9 --form aaba --phrases 2 --hook 2 --organic 2 --pan call",
    f"--style ska --key A --bpm 168 --bars 28 --seed 3 --form stage --phrases 1 --hook 3 --organic 2 --pan echo --texture fusion",
    f"--style pop --key C --bpm 120 --bars 64 --seed 1 --progression axis {ALL_ON}",
    f"--style pop --key G --bpm 100 --bars 48 --seed 5 --groove tropical {ALL_ON}",
    f"--style pop --key D --bpm 128 --bars 48 --seed 2 --groove dance --texture fusion {ALL_ON}",
    f"--style pop --key A --bpm 110 --bars 40 --seed 6 --form aaba {ALL_ON}",
    f"--style rock --key E --bpm 146 --bars 28 --seed 3 --texture fusion {ALL_ON}",
    f"--style rock --key A --bpm 150 --bars 16 --seed 4 --form stage --groove halftime {ALL_ON}",
    f"--style rock --key A --bpm 112 --bars 40 --seed 5 --form blues12 {ALL_ON}",
    f"--style rock --key D --bpm 110 --bars 28 --seed 8 --groove shuffle --phrases 2 --organic 3 --pan call",
    f"--style rock --key E --bpm 120 --bars 32 --seed 12 --form verse-chorus --groove funk {ALL_ON}",
    f"--style chip --key G --bpm 140 --bars 48 --seed 4 --form verse-chorus --lift octave {ALL_ON}",
    f"--style chip --key C --bpm 92 --bars 48 --seed 2 --form verse-chorus --groove swing --phrases 2 --organic 2 --pan wide",
    f"--style pop --key B --bpm 76 --bars 48 --seed 3 --groove onedrop {ALL_ON}",
    f"--style pop --key E --bpm 96 --bars 48 --seed 8 --groove latin --bend normal {ALL_ON}",
    "--style fusion --key F# --bpm 100 --bars 32 --seed 7 --form verse-chorus --organic 2 --pan echo",
    "--style ambient --key D --bpm 70 --bars 16 --seed 2 --organic 1",
    "--style chip --key G --bpm 140 --bars 16 --seed 4 --organic 2 --pan wide",
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--keep", default=None, help="directory to keep the scores in (default: a temporary one)")
    args = ap.parse_args()
    root = Path(args.keep) if args.keep else Path(tempfile.mkdtemp(prefix="gbc-music-flags-"))
    root.mkdir(parents=True, exist_ok=True)
    failures = 0
    for i, a in enumerate(SETS, 1):
        out = root / f"set{i:02d}.txt"
        r = subprocess.run([sys.executable, "-I", str(COMPOSE), "generate", *a.split(), "--out", str(out), "--report", str(out.with_suffix(".json"))],
                           capture_output=True, text=True)
        ok = r.returncode == 0
        detail = ""
        if ok:
            rep = json.loads(out.with_suffix(".json").read_text(encoding="utf-8"))
            c = subprocess.run([sys.executable, "-I", str(COMPOSE), "compile", str(out), "--out", str(root / f"set{i:02d}.c")], capture_output=True, text=True)
            ok = c.returncode == 0
            detail = f"{rep['bars']} bars, hooks {len(rep.get('hooks', []))}, {len(rep.get('warnings', []))} warnings"
        else:
            detail = (r.stderr.strip().splitlines() or ["(no stderr)"])[-1][:200]
        failures += 0 if ok else 1
        print(f"{'PASS' if ok else 'FAIL'} {i:02d} {a}  -> {detail}")
    print(f"{len(SETS) - failures}/{len(SETS)} argument sets passed; scores in {root}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
