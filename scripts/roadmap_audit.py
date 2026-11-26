#!/usr/bin/env python3
"""roadmap_audit.py - mechanical open-item sweep (R-8 ritual).
Greps the governance docs, BACKLOG and the registry's notes column for
open-item language and prints every hit. A human (or agent) checks each
hit maps to a D-/Q- id in MASTER_PROGRAM's roadmap; anything unmapped
is a register bug. Append-only check: D-/Q- numbering in MASTER must be
contiguous from 1."""
import csv, glob, re, sys
KW = re.compile(r"\b(owed|pending|awaiting|parked|queued|halted|"
                r"on hold|still due|unsolved|open question|revisit|"
                r"deferred)\b", re.I)
hits = 0
for f in (["MASTER_PROGRAM.md", "BACKLOG.md", "VALIDATION_PLAN.md",
           "GLOSSARY.md", "DOCUMENT_MAP.md"]
          + sorted(glob.glob("Tests/*/REMAINDER_LEDGER.md"))):
    try:
        for i, line in enumerate(open(f), 1):
            if KW.search(line):
                print(f"{f}:{i}: {line.strip()[:110]}")
                hits += 1
    except FileNotFoundError:
        pass
with open("Tests/test_registry_rows.tsv") as fh:
    for r in csv.reader(fh, delimiter="\t"):
        if len(r) > 17 and KW.search(r[17]):
            print(f"registry {r[0]}: ...{KW.search(r[17]).group(0)}...")
            hits += 1
m = open("MASTER_PROGRAM.md").read()
dn = sorted(set(int(x) for x in re.findall(r"\| D-(\d+) \|", m)))
qn = sorted(set(int(x) for x in re.findall(r"\| Q-(\d+) \|", m)))
for nm, ns in (("D", dn), ("Q", qn)):
    missing = [i for i in range(1, max(ns) + 1) if i not in ns] if ns else []
    print(f"{nm}-numbering: {len(ns)} ids, "
          + ("contiguous OK" if not missing else f"GAPS {missing}"))
print(f"\n{hits} open-language hits. Each must map to a D-/Q- id "
      "(or be historical text in a CLOSED report).")
