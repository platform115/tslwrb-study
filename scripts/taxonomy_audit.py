#!/usr/bin/env python3
"""taxonomy_audit.py — mechanical check of SYSTEMS_MATRIX.md against
GLOSSARY.md (R-8 pass). Fails loudly on any wiring defect.
Checks: unique register ids; every formula token registered; every
matrix system present in GLOSSARY; every GLOSSARY system row present
in the matrix (both directions); closed status vocabulary; every
non-historical component used by >= 1 system.
RUN: python3 scripts/taxonomy_audit.py
"""
import re, sys

mx = open("SYSTEMS_MATRIX.md").read()
gl = open("GLOSSARY.md").read()
errs, warns = [], []

def table_rows(text, header_start):
    ix = text.index(header_start)
    seg = text[ix:]
    lines = seg.splitlines()[1:]
    while lines and not lines[0].startswith("|"):
        lines.pop(0)
    rows = []
    for ln in lines:
        first = ln.strip("|").split("|")[0].strip()
        if first in ("id", "system") or ln.startswith("|---"):
            continue
        if not ln.startswith("| "):
            break
        rows.append([c.strip() for c in ln.strip("|").split("|")])
    return rows

reg = {}
for sec, pref in (("## REGISTER: ENTRIES", "EN-"),
                  ("## REGISTER: FILTERS", "FL-"),
                  ("## REGISTER: TRADE MANAGEMENT PLANS", "MP-")):
    for r in table_rows(mx, sec):
        rid = r[0]
        if not rid.startswith(pref):
            errs.append(f"{sec}: id '{rid}' lacks prefix {pref}")
        if rid in reg:
            errs.append(f"duplicate register id {rid}")
        reg[rid] = r

systems = {}
STATUS_OK = {"VALIDATED", "TRAINING-ONLY", "DORMANT", "DEAD"}
for r in table_rows(mx, "## SYSTEMS"):
    name, formula, tier, status = r[0], r[1], r[2], r[3]
    if name in systems:
        errs.append(f"duplicate system row {name}")
    systems[name] = r
    toks = [t.strip() for t in formula.split("x")]
    for t in toks:
        if t not in reg:
            errs.append(f"{name}: formula token '{t}' not registered")
    if status not in STATUS_OK:
        errs.append(f"{name}: status '{status}' outside closed vocab")
    if tier not in ("P", "R"):
        errs.append(f"{name}: tier '{tier}' not P/R")

# GLOSSARY system rows (patterns = the complete system namespace)
pat = re.compile(r"^\| (G2-\d+|G3-\d+|Strategy 5W|Strategy 5|5W-RWY|"
                 r"S5-MF) ", re.M)
gl_sys = set(m.group(1) for m in pat.finditer(gl))
mx_sys = set(systems)
for s in sorted(gl_sys - mx_sys):
    errs.append(f"GLOSSARY system '{s}' missing from matrix")
for s in sorted(mx_sys - gl_sys):
    errs.append(f"matrix system '{s}' missing from GLOSSARY")

# usage: every register id appears in >= 1 formula (historical ok->warn)
used = set()
for r in systems.values():
    used |= set(t.strip() for t in r[1].split("x"))
for rid in reg:
    if rid not in used:
        warns.append(f"component {rid} used by no system")

# MP-10 must exist as M10 in GLOSSARY
if "| M10 " not in gl and "M10 " not in gl:
    errs.append("M10 (MP-10 alias) not found in GLOSSARY")

# implementation anchors: file exists and contains its anchor token
import os
for r in table_rows(mx, "## IMPLEMENTATION ANCHORS"):
    rid, src = r[0], r[1]
    if rid not in reg:
        errs.append(f"anchor row '{rid}' not a registered component")
    if "::" in src:
        fp, tok = [x.strip() for x in src.split("::", 1)]
        tok = tok.split("(")[0].strip()
        if not os.path.exists(fp):
            errs.append(f"{rid}: anchor file missing: {fp}")
        else:
            body = open(fp).read()
            probe = tok.replace("def ", "def ").split()[-1]                 if tok.startswith("def ") else tok.split()[0]
            if probe not in body:
                errs.append(f"{rid}: anchor token '{probe}' not in {fp}")
anchored = set(r[0] for r in table_rows(mx, "## IMPLEMENTATION ANCHORS"))
for rid in reg:
    if rid not in anchored:
        errs.append(f"component {rid} has no implementation anchor row")

for w in warns:
    print(f"WARN: {w}")
if errs:
    for e in errs:
        print(f"FAIL: {e}")
    sys.exit(1)
print(f"TAXONOMY AUDIT PASS: {len(reg)} components, "
      f"{len(systems)} systems, bidirectional GLOSSARY match")
