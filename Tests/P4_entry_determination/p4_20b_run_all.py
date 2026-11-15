#!/usr/bin/env python3
"""Drive p4_20 over every episode month except the two discovery months."""
import sys, os, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
import p4_20_validation as V

ep = pd.read_parquet("Data/inputs/tsl_episodes_clean.parquet").dropna(subset=["first_entry_utc"])
months = sorted({str(p) for p in ep.first_entry_utc.dt.to_period("M")})
skip = {"2025-10", "2022-02"}
for m in months:
    if m in skip:
        continue
    print(f"\n{'='*70}\nMONTH {m}\n{'='*70}", flush=True)
    try:
        V.run(".", m)
    except Exception as e:
        print(f"[{m}] FAILED: {e}")
        traceback.print_exc()
