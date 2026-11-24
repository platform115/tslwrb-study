#!/usr/bin/env python3
"""gen_assets_inventory.py — regenerate ASSETS.md deterministically.
Lists every data asset with columns, row count, size, and the scripts that
read it (grep). Run from repo root after any data change. R-8 depends on
this file being current: completeness passes diff deliverables against it.
"""
import glob
import os
import subprocess

import pandas as pd

OUT = "ASSETS.md"


def readers(stem):
    try:
        r = subprocess.run(
            ["grep", "-rl", stem, "Tests/", "scripts/"],
            capture_output=True, text=True)
        return sorted(os.path.basename(x) for x in r.stdout.split()
                      if x.endswith(".py"))
    except Exception:
        return []


def main():
    lines = [
        "# ASSETS.md — DATA ASSET INVENTORY (generated; do not hand-edit)",
        "Regenerate: `python3 scripts/gen_assets_inventory.py` (repo root).",
        "Purpose (R-8): every deliverable's completeness pass is a diff",
        "against THIS list, never against memory.", "",
        "| asset | rows | cols | read by |", "|---|---|---|---|"]
    for f in sorted(glob.glob("Data/inputs/*.parquet")):
        name = os.path.basename(f)
        try:
            df = pd.read_parquet(f)
            cols = ", ".join(df.columns)
            n = len(df)
        except Exception as e:
            cols, n = f"UNREADABLE: {e}", -1
        rd = readers(name.replace(".parquet", ""))
        lines.append(f"| {name} | {n:,} | {cols} | "
                     f"{', '.join(rd) if rd else 'NONE'} |")
    for f in sorted(glob.glob("Data/inputs/*.txt")) + sorted(
            glob.glob("Data/inputs/*.csv")):
        name = os.path.basename(f)
        rd = readers(os.path.splitext(name)[0])
        lines.append(f"| {name} | - | (text) | "
                     f"{', '.join(rd) if rd else 'NONE'} |")
    lines += ["", "Assets read by NONE are either freshly built or "
              "candidates nobody has used — both deserve a look.", ""]
    with open(OUT, "w") as fh:
        fh.write("\n".join(lines))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
