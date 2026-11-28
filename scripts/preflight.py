#!/usr/bin/env python3
"""preflight.py — THE one command before any registry-affecting
commit or presentation (R-8 mechanical pass). Runs every audit;
hard-fails on structural defects.
RUN: python3 scripts/preflight.py
"""
import subprocess, sys
fail = False
print("== taxonomy_audit (hard) ==")
r = subprocess.run([sys.executable, "scripts/taxonomy_audit.py"])
if r.returncode != 0:
    fail = True
print("== overview-systems sync (hard) ==")
r = subprocess.run([sys.executable, "scripts/gen_overview_systems.py"])
if r.returncode != 0:
    fail = True
# COUNT CROSS-CHECK (added 2026-11-28 after the empty-table escape:
# sync-vs-file passed on a section with ZERO rows). The autogen
# section's data rows must equal the matrix's SYSTEMS rows, and
# neither may be zero.
mx = open("SYSTEMS_MATRIX.md").read()
sec = mx[mx.index("## SYSTEMS"):].split("\n## ")[0]
n_mx = sum(1 for ln in sec.splitlines()
           if ln.startswith("| ") and not ln.startswith("| system"))
ov = open("OVERVIEW_TREE.md").read()
gen = ov.split("<!-- AUTOGEN:SYSTEMS")[1].split("<!-- AUTOGEN:END")[0]
n_ov = sum(1 for ln in gen.splitlines()
           if ln.startswith("| ") and not ln.startswith("| status"))
if n_mx == 0 or n_ov != n_mx:
    print(f"overview-systems COUNT FAIL: matrix {n_mx} vs tree {n_ov}")
    fail = True
else:
    print(f"overview-systems count ok: {n_mx} systems both sides")
print("== roadmap_audit (advisory) ==")
subprocess.run([sys.executable, "scripts/roadmap_audit.py"])
print("== assets inventory (advisory) ==")
subprocess.run([sys.executable, "scripts/gen_assets_inventory.py"])
if fail:
    print("PREFLIGHT: FAIL — fix before presenting or committing.")
    sys.exit(1)
print("PREFLIGHT: PASS")
