"""Run every fenced shell command in README.md and EXAMPLES.md in a scratch directory, so the documentation stays
true of the code.

    python docs/check_examples.py [--scratch DIR] [--alias <new>=<legacy>,...] [--only README|EXAMPLES] [--keep]

Builds a "skill view" directory with symlinks to the scripts, exports SKILL, and runs each ```-fenced block whose lines
start with `python $SKILL/`, `export SKILL=`, `mkdir`, `cd` or `cat >` through `sh -e`. Lines starting with `#` are
skipped. `--alias` rewrites identifiers before running (the map is applied to the command text only). The python used is this interpreter (needs numpy,
pyboy and Pillow for the WAV and probe examples). Prints PASS / FAIL per block and exits 1 on any failure.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
RUNNABLE = ("python $SKILL/", "export SKILL=", "mkdir ", "cd ", "cat >", "ls ", "cp ")


def make_view(root: Path) -> Path:
    view = root / "skill"
    if view.exists():
        shutil.rmtree(view)
    (view / "scripts").mkdir(parents=True, exist_ok=True)
    for p in (SKILL / "scripts").iterdir():
        if p.is_file():
            os.symlink(p, view / "scripts" / p.name)
    if (SKILL / "docs").is_dir():
        os.symlink(SKILL / "docs", view / "docs")
    return view


def blocks(md: Path) -> list[tuple[int, list[str]]]:
    out = []
    lines = md.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        if lines[i].startswith("```"):
            start = i + 1
            j = start
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            body = lines[start:j]
            cmds = [l for l in body if l.strip() and not l.lstrip().startswith("#")]
            if cmds and cmds[0].startswith("export SKILL=") and any(l.startswith("python $SKILL/") for l in cmds):
                out.append((start + 1, body))
            i = j + 1
        else:
            i += 1
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scratch", default=None, help="scratch directory (default: a temporary one)")
    ap.add_argument("--alias", default="", help="comma-separated old=new rewrites applied to the command text (new=legacy identifier)")
    ap.add_argument("--only", default=None, help="README or EXAMPLES")
    ap.add_argument("--keep", action="store_true", help="keep the scratch directory")
    args = ap.parse_args()
    root = Path(args.scratch) if args.scratch else Path(tempfile.mkdtemp(prefix="gbc-music-examples-"))
    root.mkdir(parents=True, exist_ok=True)
    view = make_view(root)
    aliases = [a.split("=", 1) for a in args.alias.split(",") if "=" in a]
    docs = [SKILL / "docs" / "README.md", SKILL / "docs" / "EXAMPLES.md"]
    if args.only:
        docs = [d for d in docs if d.stem.upper() == args.only.upper()]
    env = dict(os.environ, SKILL=str(view), PATH=str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", ""))
    failures = 0
    n = 0
    for doc in docs:
        for line_no, body in blocks(doc):
            n += 1
            work = root / f"{doc.stem.lower()}_{line_no}"
            if work.exists():
                shutil.rmtree(work)
            work.mkdir()
            script = "\n".join(body)
            for old, new in aliases:
                script = re.sub(rf"(?<=[\s=|\"'])({re.escape(old)})(?=[\s\"'|]|$)", new, script)
            script = re.sub(r"^\s*export SKILL=.*$", "", script, flags=re.M)
            script = re.sub(r"^\s*mkdir (\S+) && cd \1\s*$", "", script, flags=re.M)
            script = script.replace("python $SKILL/", f"{sys.executable} -I $SKILL/")
            res = subprocess.run(["sh", "-e"], input=script, cwd=work, env=env, capture_output=True, text=True, timeout=900)
            ok = res.returncode == 0
            failures += 0 if ok else 1
            print(f"{'PASS' if ok else 'FAIL'} {doc.name}:{line_no} ({len(body)} lines) -> {work}")
            if not ok:
                print("  " + (res.stderr.strip().splitlines() or ["(no stderr)"])[-1][:300])
    print(f"{n - failures}/{n} blocks passed; scratch {root}")
    if not args.keep and not args.scratch and failures == 0:
        shutil.rmtree(root, ignore_errors=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
