#!/usr/bin/env python3
"""
p4_18_vocab_mining.py — P4.18: what HE says he watches — speed and other factors.
==================================================================================
USER (2026-11-15): mine his messages for what he was looking at ("speed" and other
factors) to narrow the reverse-engineering target list. Purely descriptive, his
words verbatim:
  1. For each watch-word family (speed/pace, volatility state, direction words,
     level words, patience/waiting), count messages and show the words he pairs
     them with (the two words either side - collocations).
  2. VERBATIM SAMPLES: his non-trade messages within 10 min BEFORE an entry that
     contain a speed or volatility word - printed for reading, oldest first.
  3. "Volatility X" / "X volatility": what states does he name? (contracting
     appears 295 times, expanding 3 - the asymmetry itself is information.)

RUN: python3 Tests/P4_entry_determination/p4_18_vocab_mining.py            (repo root)
"""
import argparse, os, re, sys
from collections import Counter
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_17_chat_alignment import STOP, tokens   # noqa: E402

FAMILIES = {
    "speed/pace": ["fast", "slow", "speed", "quick", "momentum", "grind", "grinding",
                   "chop", "choppy", "crawl", "racing", "moving"],
    "volatility state": ["volatility", "contracting", "contraction", "expanding",
                         "expansion", "quiet", "dead", "wild", "volatile"],
    "direction words": ["southward", "northward", "breakout", "breakdown", "through",
                        "reversal", "bounce", "rejection"],
    "level words": ["level", "levels", "zone", "zones", "gap", "hidden", "interval",
                    "support", "resistance", "top", "bottom"],
    "waiting/patience": ["waiting", "wait", "patience", "patient", "watching",
                         "stalking", "missed", "late", "early"],
}


def collocations(msgs_low, word, n=6):
    """Most common neighbors (one word either side) of `word` across messages."""
    c = Counter()
    rx = re.compile(rf"(\w+)?\W*\b{re.escape(word)}\b\W*(\w+)?")
    for s in msgs_low:
        for m in rx.finditer(s):
            for g in m.groups():
                if g and g not in STOP and g != word and len(g) > 2:
                    c[g] += 1
    return c.most_common(n)


def run(repo):
    msg = pd.read_parquet(os.path.join(repo, "Data/inputs/wrb_messages.parquet"))
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc"])
    nontrade = msg[msg.trade_action.fillna("") == ""].copy()
    low = nontrade.message.astype(str).str.lower()

    print("===== 1. watch-word families: message counts + what he pairs them with =====")
    for fam, words in FAMILIES.items():
        print(f"\n[{fam}]")
        for w in words:
            m = low.str.contains(rf"\b{re.escape(w)}\b", regex=True)
            n = int(m.sum())
            if n < 10:
                continue
            col = collocations(low[m], w)
            print(f"  {w:12s} {n:5d} msgs | with: " + ", ".join(f"{a}({b})" for a, b in col))

    print("\n===== 2. verbatim: speed/volatility messages in the 10 min before an entry =====")
    en_ns = np.sort(pd.DatetimeIndex(ep.first_entry_utc).as_unit("ns").asi8)
    nt = nontrade.assign(ns=pd.DatetimeIndex(nontrade.datetime_utc).as_unit("ns").asi8)
    speedy = nt[nt.message.astype(str).str.lower().str.contains(
        r"\b(fast|slow|speed|momentum|volatility|contracting|expanding|chop|grind)\w*\b",
        regex=True)]
    j = np.searchsorted(en_ns, speedy.ns.to_numpy())
    pre = speedy[(j < len(en_ns)) & ((en_ns[np.clip(j, 0, len(en_ns) - 1)] - speedy.ns) <= 10 * 60e9)]
    print(f"({len(pre)} such messages across the full history; first 25 shown)")
    for _, r in pre.sort_values("datetime_utc").head(25).iterrows():
        t = pd.Timestamp(r.datetime_utc).strftime("%Y-%m-%d %H:%M")
        print(f"  [{t}] {str(r.message)[:150]}")

    print("\n===== 3. 'volatility ___': the states he names =====")
    c = Counter()
    rx = re.compile(r"\bvolatility\b\W*(\w+)|(\w+)\W*\bvolatility\b")
    for s in low[low.str.contains(r"\bvolatility\b", regex=True)]:
        for m in rx.finditer(s):
            for g in m.groups():
                if g and g not in STOP and len(g) > 2:
                    c[g] += 1
    for w, n in c.most_common(20):
        print(f"  {w:16s} {n}")
    print("\nREAD: his words, counted and quoted - leads for measurement, not findings.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
