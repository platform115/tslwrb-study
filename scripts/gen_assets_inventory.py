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
    # R-8 doc-coverage check: every .md must appear in DOCUMENT_MAP.md
    if os.path.exists("DOCUMENT_MAP.md"):
        dm = open("DOCUMENT_MAP.md").read()
        covered_groups = ["Tests/01", "Tests/02", "Tests/03", "Tests/04",
                          "Tests/05", "Tests/06", "Tests/07",
                          "STRATEGY_SPEC_v", "_spec", "_REPORT", "PLAN",
                          "SPEC", "CHARTER", "HANDOFF", "BACKLOG",
                          "CANDIDATES", "GROUPS", "DESIGN", "CHECK",
                          "USAGE", "SUMMARY", "VALIDATION"]
        missing = []
        for md in glob.glob("*.md") + glob.glob("Tests/*/*.md"):
            base = os.path.basename(md)
            if base in dm or any(k in md for k in covered_groups):
                continue
            missing.append(md)
        if missing:
            print("DOC-COVERAGE FAIL - not in DOCUMENT_MAP.md:")
            for x in missing:
                print("  ", x)
        else:
            print("doc-coverage: all .md files placed")


if __name__ == "__main__":
    main()
