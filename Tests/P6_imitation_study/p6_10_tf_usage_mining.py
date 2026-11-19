#!/usr/bin/env python3
"""
p6_10_tf_usage_mining.py — STRUCTURE PROGRAM S0: TIMEFRAME USAGE MINING.
(T-IM14.) Verify, don't assume (user directive): extract EVERY timeframe
mention in his messages with context; test the hypothesis "mostly 1m, with
3m/5m sometimes — 1m for entries" against his own words.

Method (text mining only, no price data, no rule-building):
  1. Regex catalogue of timeframe spellings (1m / 1 min / 1-minute / 5min /
     hourly / daily / weekly / monthly / 60m ...) with word boundaries.
  2. Every hit becomes a row: ts, month, tf_label (normalized), raw text.
  3. Context classes per message (a message can carry several):
       entry     enter/entry/signal/long/short/buy/sell/trade trigger words
       exit      exit/close(d) trade/target/pt1-3/stop/trail
       structure WRB/zone/KME/S-R/level/area/range/shadow/gap
       chart     explicit "<tf> chart" phrasing (what he is LOOKING at)
       other     none of the above matched
  4. Report: counts per normalized TF; TF x context cross-tab; per-month
     presence; sample quotes per TF for human review.
NOTHING is built on this until the review gate passes (plan S0).

FINDING (v1 pass): the raw mention count is dominated by DURATIONS
("be back in 20 mins", "for the past 12 minutes", the "N hours later"
statistical boilerplate posts) - NOT chart timeframes. Pass 2 below
therefore isolates CHART-TF statements: compact tokens (2min/15min/...),
"chart"/"time frame"/"chart interval" vocabulary, and TF list messages.
Only 14 such messages exist in the whole corpus; they are printed in full.

RUN: python3 Tests/P6_imitation_study/p6_10_tf_usage_mining.py      (repo root)
"""
import os, re, sys
import numpy as np
import pandas as pd

# --- timeframe spellings -> normalized label ---------------------------------
# order matters: longer/explicit spellings first so "15 min" isn't eaten as "5 min"
TF_PATTERNS = [
    (r"\b(\d{1,3})\s*(?:-|\s)?\s*m(?:in(?:ute)?s?)?\s+charts?\b", "NUM_chart"),
    (r"\b(\d{1,3})\s*(?:-|\s)?\s*min(?:ute)?s?\b", "NUM"),
    (r"\b(\d{1,3})m\b", "NUM"),                     # 1m 3m 5m 15m 60m
    (r"\bm(\d{1,3})\b", "NUM"),                     # m1 m5 (rare)
    (r"\b(\d{1,2})\s*(?:-|\s)?\s*h(?:ou)?rs?\b", "NUM_H"),
    (r"\b(\d{1,2})h\b", "NUM_H"),
    (r"\bhourly\b", "60m"),
    (r"\bdaily\b", "daily"),
    (r"\bweekly\b", "weekly"),
    (r"\bmonthly\b", "monthly"),
    (r"\bintraday\b", "intraday"),
]
# number words occasionally used
WORDNUM = {"one": 1, "two": 2, "three": 3, "five": 5, "ten": 10, "fifteen": 15}
TF_WORD = re.compile(r"\b(one|two|three|five|ten|fifteen)\s+min(?:ute)?s?\b", re.I)

CTX = [
    ("entry", r"\bentr(?:y|ies|ered?)\b|\benter(?:ing|ed)?\b|\bsignal\b|\blong\b|\bshort\b|\bbought\b|\bsold\b|\bbuy\b|\bsell\b|\btrigger"),
    ("exit", r"\bexit|\bclosed?\s+(?:the\s+)?(?:trade|position|out)|\btarget|\bpt\s?\d|\bstop\b|\btrail"),
    ("structure", r"\bwrb\b|\bzone\b|\bkme\b|\bs\s*/\s*r\b|\b[SR]\s+area\b|\blevel\b|\bsupport\b|\bresistance\b|\barea\b|\brange\b|\bshadow\b|\bgap\b|\bcontract(?:ing|ion)\b"),
    ("chart", r"charts?\b"),
]
# exclusions: things that look like TFs but are not (money, points, contract counts)
EXCL_BEFORE = re.compile(r"[$\d.]$")                      # $5m, 1.5m
EXCL_AFTER = re.compile(r"^\s*(?:ticks?|pts?|points?|contracts?|cars?|%)", re.I)


def norm(label, g):
    if label == "NUM" or label == "NUM_chart":
        return f"{int(g)}m"
    if label == "NUM_H":
        return f"{int(g)*60}m"
    return label


def mine(repo="."):
    wm = pd.read_parquet(os.path.join(repo, "Data/inputs/wrb_messages.parquet"))
    wm["dtm"] = pd.to_datetime(wm.datetime_utc, utc=True)
    pats = [(re.compile(p, re.I), lab) for p, lab in TF_PATTERNS]
    rows = []
    for _, r in wm.iterrows():
        t = str(r.message).replace("\n", " ").strip()
        hits = {}   # span-start -> (tf, is_chart)
        for cre, lab in pats:
            for mt in cre.finditer(t):
                a = mt.start()
                if any(abs(a - b) < 3 for b in hits):   # longer pattern won
                    continue
                if a > 0 and EXCL_BEFORE.search(t[:a]):
                    continue
                if EXCL_AFTER.match(t[mt.end():]):
                    continue
                g = mt.group(1) if mt.groups() else None
                if g is not None and not (1 <= int(g) <= 240):
                    continue
                hits[a] = (norm(lab, g) if g else norm(lab, None),
                           lab == "NUM_chart")
        for mt in TF_WORD.finditer(t):
            a = mt.start()
            if not any(abs(a - b) < 3 for b in hits):
                hits[a] = (f"{WORDNUM[mt.group(1).lower()]}m", False)
        if not hits:
            continue
        tl = t.lower()
        ctx = [k for k, p in CTX if re.search(p, tl)] or ["other"]
        for a, (tf, ischart) in sorted(hits.items()):
            rows.append(dict(ts_utc=r["dtm"], month=str(r["dtm"])[:7], tf=tf,
                             chart_phrase=ischart or ("chart" in ctx),
                             ctx_entry=("entry" in ctx), ctx_exit=("exit" in ctx),
                             ctx_structure=("structure" in ctx),
                             ctx_chart=("chart" in ctx),
                             ctx_other=(ctx == ["other"]),
                             raw=t[max(0, a - 90):a + 110]))
    df = pd.DataFrame(rows)
    n = len(df)
    print(f"===== TF USAGE MINING: {n} timeframe mentions in {wm.shape[0]} messages =====\n")
    print("## Mentions per normalized timeframe")
    vc = df.tf.value_counts()
    print(vc.to_string())
    print("\n## TF x context (message-level flags; a message can carry several)")
    print("| TF | n | entry-ctx | exit-ctx | structure-ctx | chart-ctx | none |")
    print("|---|---|---|---|---|---|---|")
    for tf in vc.index:
        g = df[df.tf == tf]
        print(f"| {tf} | {len(g)} | {g.ctx_entry.mean():.0%} | {g.ctx_exit.mean():.0%} "
              f"| {g.ctx_structure.mean():.0%} | {g.ctx_chart.mean():.0%} "
              f"| {g.ctx_other.mean():.0%} |")
    print("\n## Per data month")
    for m in ("2025-10", "2022-02", "2021-09", "2024-11"):
        g = df[df.month == m]
        print(f"  {m}: {len(g)} mentions | {dict(g.tf.value_counts())}")
    print("\n## All months with any mention (top 15)")
    print(df.month.value_counts().head(15).to_string())
    print("\n## SAMPLE QUOTES per TF (for human review; up to 6 each, spread over time)")
    for tf in vc.index:
        g = df[df.tf == tf]
        k = np.linspace(0, len(g) - 1, min(6, len(g))).astype(int)
        print(f"\n--- {tf} ({len(g)}) ---")
        for _, q in g.iloc[k].iterrows():
            print(f"  [{str(q.ts_utc)[:16]}] ...{q.raw}...")
    out = os.path.join(repo, "Data/inputs/his_tf_mentions.parquet")
    df.to_parquet(out)
    print(f"\nsaved -> {out}")

    # ---- PASS 2: CHART-TF statements only (the durations trap removed) ----
    print("\n\n===== PASS 2: EXPLICIT CHART-TF STATEMENTS (full messages) =====")
    tok = re.compile(r"\b[1-9]\d?min\b|\bhourly\b", re.I)
    chartish = re.compile(r"time\s?frame|chart", re.I)
    tfnum2 = re.compile(r"\b\d{1,3}\s?-?\s?min(?:ute)?s?\b|\b\d{1,3}m\b", re.I)
    seen = set()
    for _, r in wm.iterrows():
        t = str(r.message).replace("\n", " ").strip()
        is_compact = bool(tok.search(t))
        is_chart = bool(chartish.search(t) and tfnum2.search(t))
        is_list = len(set(m.group(0).lower() for m in tfnum2.finditer(t))) >= 2
        if (is_compact or is_chart or is_list) and t not in seen:
            seen.add(t)
            print(f"[{str(r['dtm'])[:16]}] {t[:300]}")
    print(f"\n{len(seen)} chart-TF statements in {wm.shape[0]} messages")
    return df


if __name__ == "__main__":
    mine("." if len(sys.argv) < 2 else sys.argv[1])
