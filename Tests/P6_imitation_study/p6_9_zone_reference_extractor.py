#!/usr/bin/env python3
"""
p6_9_zone_reference_extractor.py — IMITATION STUDY: HIS STRUCTURE REFERENCES
extracted to a database. (T-IM10.) USER RULE: nothing ignored - every message
touching his structural vocabulary becomes a row; what cannot be parsed is
kept with needs_review=True, never dropped.

Output: Data/inputs/his_zone_refs.parquet, one row per reference:
  ts_utc, month, ref_type  explicit_price | relational | event | mention
  kind      key_kme_wrb | kme | wrb_zone | wrb | zone_area | level_sr | range
  relation  above | below | at_near | reached | testing | approaching |
            failed_held | none
  price_1, price_2   parsed prices (NaN if none); side_label S/R if stated
  confidence  high (explicit price + kind) | med (relational + kind) |
              low (mention only / ambiguous)
  needs_review, raw (trimmed text)
Relational rows get resolved_price later by chart anchoring (price at
message time + relation + structure), calibrated on the explicit-price rows.

RUN: python3 Tests/P6_imitation_study/p6_9_zone_reference_extractor.py    (repo root)
"""
import os, re, sys
import numpy as np
import pandas as pd

KINDS = [
    ("key_kme_wrb", r"key\s+kme\s+wrb|kme\s+wrb\s+zone"),
    ("kme", r"\bkme\b"),
    ("wrb_zone", r"wrb\s+(?:zone|area)"),
    ("wrb", r"\bwrb\b"),
    ("zone_area", r"\bzone\b|\barea\b"),
    ("level_sr", r"\blevel\b|\bsupport\b|\bresistance\b|\b[SR]\s+area\b"),
    ("range", r"trading\s+range|\brange\b"),
]
RELS = [
    ("reached", r"reach|tagged|\bhit\b|touch"),
    ("testing", r"\btest|prob(?:e|ing)|attack|challeng"),
    ("approaching", r"approach|coming\s+(?:up|down)|heading|push(?:ing)?\s+(?:up|down|toward)"),
    ("failed_held", r"\bfail|reject|\bheld\b|\bhold(?:ing)?\b|defend|bounc"),
    ("above", r"\babove\b"),
    ("below", r"\bbelow\b"),
    ("at_near", r"\b(?:at|near|around)\b|@"),
]
PRICE = re.compile(r"\b([1-9]\d{3}(?:\.(?:25|50|5|75|00|0))?)\b")
SIDE = re.compile(r"\b([SR])\s+area\b", re.I)
EVENT = re.compile(r"wrb\s+(reached|pt\d|formed|completed)|pt\d\s+reached", re.I)


def extract(repo="."):
    wm = pd.read_parquet(os.path.join(repo, "Data/inputs/wrb_messages.parquet"))
    wm["dtm"] = pd.to_datetime(wm.datetime_utc, utc=True)
    rows = []
    any_kind = re.compile("|".join(p for _, p in KINDS), re.I)
    for _, r in wm.iterrows():
        t = str(r.message).replace("\n", " ").strip()
        tl = t.lower()
        if not any_kind.search(tl):
            continue
        kind = next((k for k, p in KINDS if re.search(p, tl)), "zone_area")
        rel = next((k for k, p in RELS if re.search(p, tl)), "none")
        prices = [float(x) for x in PRICE.findall(t)][:2]
        side = (SIDE.search(t) or [None, None])[1] if SIDE.search(t) else None
        is_event = bool(EVENT.search(tl))
        if prices:
            ref_type, conf = "explicit_price", ("high" if kind != "zone_area" else "med")
        elif is_event:
            ref_type, conf = "event", "med"
        elif rel != "none":
            ref_type, conf = "relational", ("med" if kind in ("key_kme_wrb", "kme", "wrb_zone", "wrb") else "low")
        else:
            ref_type, conf = "mention", "low"
        rows.append(dict(
            ts_utc=r["dtm"], month=str(r["dtm"])[:7], ref_type=ref_type,
            kind=kind, relation=rel,
            price_1=prices[0] if prices else np.nan,
            price_2=prices[1] if len(prices) > 1 else np.nan,
            side_label=side.upper() if side else None,
            confidence=conf, needs_review=(conf == "low"), raw=t[:200]))
    df = pd.DataFrame(rows)
    out = os.path.join(repo, "Data/inputs/his_zone_refs.parquet")
    df.to_parquet(out)
    print(f"extracted {len(df)} structure references -> {out}")
    print("\nby ref_type:"); print(df.ref_type.value_counts().to_string())
    print("\nby kind (top):"); print(df.kind.value_counts().head(7).to_string())
    print("\nconfidence:"); print(df.confidence.value_counts().to_string())
    print("\nper data month:")
    for m in ("2025-10", "2022-02", "2021-09", "2024-11"):
        g = df[df.month == m]
        print(f"  {m}: {len(g)} refs | explicit {len(g[g.ref_type=='explicit_price'])} "
              f"| relational {len(g[g.ref_type=='relational'])} | events "
              f"{len(g[g.ref_type=='event'])} | mention {len(g[g.ref_type=='mention'])}")
    return df


if __name__ == "__main__":
    extract("." if len(sys.argv) < 2 else sys.argv[1])
