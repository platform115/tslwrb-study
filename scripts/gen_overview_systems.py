#!/usr/bin/env python3
"""gen_overview_systems.py — OVERVIEW_TREE's systems section is
GENERATED from SYSTEMS_MATRIX (single source; no hand drift).
Modes: --write (regenerate in place) | --check (fail if stale).
The generated block lives between AUTOGEN markers.
"""
import re, sys

BEGIN = "<!-- AUTOGEN:SYSTEMS (gen_overview_systems.py) -->"
END = "<!-- AUTOGEN:END -->"

def matrix_systems():
    mx = open("SYSTEMS_MATRIX.md").read()
    ix = mx.index("## SYSTEMS")
    rows = []
    lines = mx[ix:].splitlines()[1:]
    while lines and not lines[0].startswith("|"):
        lines.pop(0)
    for ln in lines:
        if ln.startswith("|---"):
            continue
        if not ln.startswith("| "):
            break
        c = [x.strip() for x in ln.strip("|").split("|")]
        if c[0] in ("system",):
            continue
        rows.append(c)   # system, formula, tier, status, headline, judge
    # SAFETY (added after the empty-table escape 2026-11-28): a
    # parse that returns no rows is a defect, never valid output.
    assert rows, "matrix_systems parsed ZERO rows - parser broken"
    return rows

def render(rows):
    order = {"VALIDATED": 0, "TRAINING-ONLY": 1, "DORMANT": 2,
             "DEAD": 3}
    out = [BEGIN,
           "### Combo line (Tier-P, Pine-portable)",
           "| status | system | formula | headline | judge |",
           "|---|---|---|---|---|"]
    for tier, title in (("P", None), ("R", "### Surgical line "
                                      "(Tier-R, depth feed)")):
        sel = sorted([r for r in rows if r[2] == tier],
                     key=lambda r: (order.get(r[3], 9), r[0]))
        if title:
            out += [title,
                    "| status | system | formula | headline | judge |",
                    "|---|---|---|---|---|"]
        for r in sel:
            out.append(f"| {r[3]} | {r[0]} | {r[1]} | {r[4]} | "
                       f"{r[5]} |")
    out.append(END)
    return "\n".join(out)

ot = open("OVERVIEW_TREE.md").read()
if BEGIN not in ot:
    print("FAIL: AUTOGEN markers missing from OVERVIEW_TREE.md")
    sys.exit(1)
block = render(matrix_systems())
new = ot[:ot.index(BEGIN)] + block + ot[ot.index(END) + len(END):]
if "--write" in sys.argv:
    open("OVERVIEW_TREE.md", "w").write(new)
    print("OVERVIEW_TREE systems section regenerated")
elif new != ot:
    print("FAIL: OVERVIEW_TREE systems section is STALE - run: "
          "python3 scripts/gen_overview_systems.py --write")
    sys.exit(1)
else:
    print("overview-systems: in sync with SYSTEMS_MATRIX")
