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
print("== roadmap_audit (advisory) ==")
subprocess.run([sys.executable, "scripts/roadmap_audit.py"])
print("== assets inventory (advisory) ==")
subprocess.run([sys.executable, "scripts/gen_assets_inventory.py"])
if fail:
    print("PREFLIGHT: FAIL — fix before presenting or committing.")
    sys.exit(1)
print("PREFLIGHT: PASS")
