#!/usr/bin/env python3
"""
reorganize_06.py — split the Test/06 folder into 06-1..06-5 subtest subfolders.
-------------------------------------------------------------------------------
SAFE BY DEFAULT: dry-run unless --apply. Only the files in the explicit manifest move;
everything else is LEFT AT ROOT and listed so nothing moves by surprise.

WHY IT EDITS SCRIPTS: every test script imports horse_race_spine + trade_flow_exhaustion,
which only resolve when run from the same dir. Those two stay at the folder ROOT (shared);
each MOVED script gets a 4-line path bootstrap (ast-inserted before its first import) so it
still finds the root modules from one level down. Idempotent (marker-guarded).

trade_flow_exhaustion.py STAYS at root: it is both the original Test-06 script AND a hard
dependency (build_groups / read_per_second / constants) of the spine and all subtests. If you
later relocate the original 06/06b work, you must keep a copy here OR refactor build_groups /
read_per_second into horse_race_spine first — moving it now breaks every subtest.

RUN
  python3 reorganize_06.py                 # dry-run: prints the full plan, changes nothing
  python3 reorganize_06.py --apply         # execute
  (run from inside the 06 folder; or pass --root /path/to/06_folder)
"""

import argparse, ast, os, shutil, sys

MOVES = {
    "06-1_sparsity":            ["describe_window_sparsity.py", "window_sparsity.csv"],
    "06-2_impact":              ["test_07a_impact.py", "test_07b_impact.py"],
    "06-3_compression":         ["test_08_bar_compression.py"],
    "06-4_relabel":             ["build_behavioral_relabel.py",
                                 "behavioral_relabel_2025-10.parquet",
                                 "behavioral_relabel_2025-10.csv"],
    "06-5_behavioral_baseline": ["test_behavioral_baseline.py"],
}
# scripts that import the shared root modules -> need the path bootstrap after moving
NEEDS_BOOTSTRAP = {
    "describe_window_sparsity.py", "test_07a_impact.py", "test_07b_impact.py",
    "test_08_bar_compression.py", "build_behavioral_relabel.py", "test_behavioral_baseline.py",
}
STAYS_AT_ROOT = [
    "horse_race_spine.py", "trade_flow_exhaustion.py",          # shared / dependency
    "config.toml", "CURRENT_STATE.md",
    "FROZEN_in_trade_flow_exhaustion_HOLDOUT_spec.md",
    "trade_flow_exhaustion_results.csv",                        # original 06 Round 1
    "trade_flow_exhaustion_round2.py", "trade_flow_exhaustion_round2_results.csv",  # original 06 R2
]

BOOT_MARKER = "# --- path bootstrap (subtest dir -> shared root modules) ---"
BOOTSTRAP = (
    BOOT_MARKER + "\n"
    "import sys as _sys, os as _os\n"
    "_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))\n"
    "# --- end path bootstrap ---\n"
)


def insert_bootstrap(path, apply):
    src = open(path, "r").read()
    if BOOT_MARKER in src:
        return "already bootstrapped"
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return f"SKIP (parse error: {e})"
    first_import = next((n.lineno for n in tree.body
                         if isinstance(n, (ast.Import, ast.ImportFrom))), None)
    if first_import is None:
        return "SKIP (no imports found)"
    lines = src.splitlines(keepends=True)
    new = "".join(lines[:first_import - 1]) + BOOTSTRAP + "".join(lines[first_import - 1:])
    if apply:
        open(path, "w").write(new)
    return f"insert bootstrap before line {first_import}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="the 06 folder (default: CWD)")
    ap.add_argument("--apply", action="store_true", help="execute (default: dry-run)")
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    mode = "APPLY" if args.apply else "DRY-RUN (nothing changes)"
    print(f"[{mode}] root = {root}\n")

    # validate manifest files exist
    missing = []
    for files in MOVES.values():
        for f in files:
            if not os.path.exists(os.path.join(root, f)):
                missing.append(f)
    if missing:
        print(f"[warn] manifest files not found at root (skipping these): {missing}\n")

    # plan: moves
    print("PLAN — moves:")
    for sub, files in MOVES.items():
        for f in files:
            src = os.path.join(root, f)
            if not os.path.exists(src):
                continue
            print(f"  {f:38s} ->  {sub}/{f}")
    print("\nPLAN — bootstrap edits (so moved scripts still import root modules):")
    for sub, files in MOVES.items():
        for f in files:
            if f in NEEDS_BOOTSTRAP and os.path.exists(os.path.join(root, f)):
                print(f"  {sub}/{f}")
    print("\nLEFT AT ROOT (untouched):")
    present = set(os.listdir(root))
    moved = {f for files in MOVES.values() for f in files}
    for f in sorted(present - moved):
        if f == "__pycache__":
            print(f"  {f}   (will be DELETED — stale bytecode)")
        elif f == os.path.basename(__file__):
            print(f"  {f}   (this script)")
        else:
            tag = "" if f in STAYS_AT_ROOT else "   (not in manifest — leaving as-is)"
            print(f"  {f}{tag}")

    if not args.apply:
        print("\nDry-run only. Re-run with --apply to execute. "
              "Then: git add -A && git commit (git detects the renames).")
        return

    # execute
    print("\nEXECUTING:")
    for sub, files in MOVES.items():
        d = os.path.join(root, sub)
        os.makedirs(d, exist_ok=True)
        for f in files:
            src = os.path.join(root, f)
            if not os.path.exists(src):
                continue
            dst = os.path.join(d, f)
            shutil.move(src, dst)
            print(f"  moved {f} -> {sub}/")
            if f in NEEDS_BOOTSTRAP:
                print(f"    bootstrap: {insert_bootstrap(dst, apply=True)}")
    pyc = os.path.join(root, "__pycache__")
    if os.path.isdir(pyc):
        shutil.rmtree(pyc); print("  deleted __pycache__")

    print("\nDONE. New run commands (from a subfolder, config/wrb at PROJECT ROOT = ../../../):")
    print("  cd 06-2_impact && python3 test_07a_impact.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet")
    print("  (horse_race_spine + trade_flow_exhaustion import from ../ via the bootstrap.)")
    print("\nPLACE the SPEC docs into their folders: SPEC_06-2 -> 06-2_impact/, etc.")
    print("Then: git add -A && git commit.")


if __name__ == "__main__":
    main()
