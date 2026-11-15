#!/usr/bin/env python3
"""
p4_17_chat_alignment.py — P4.17: his own words, aligned to his trading.
========================================================================
Data: Data/inputs/wrb_messages.parquet (31,838 wrbtrader messages 2021-05..2026-06,
trade calls tagged) and chat_activity.parquet (per-minute room counts), exported
from the user's scraped forum-chat corpus (es-trading-agent-v3 chatlog-scraper).
The room is effectively HIS narration log (median 30 msgs/day, 24 his).

QUESTIONS (methods fixed before running):
 1. COVERAGE: how many episode days have chat coverage?
 2. PRESENCE: the standing "passed on may include absent" caveat, finally measured.
    Feature per signal (discovery months): minutes since his previous message of
    any kind. Binary read: message within the prior 30 min ("verifiably at the
    keyboard"). Compare take rates; AUC on minutes-since (taken = more recent).
 3. WORDS BEFORE ENTRIES: his NON-trade messages in the 15 min before an entry
    vs his other desk-window non-trade messages (both months). Token frequency
    ratio (lowercase, >=5 occurrences, short stopword list) - which words are
    over-represented right before he pulls the trigger. Descriptive.
 4. INVENTORY for future measurement: corpus-wide counts of absence markers,
    scheduled-news words, chart-timeframe words, zone/WRB vocabulary.

RUN: python3 Tests/P4_entry_determination/p4_17_chat_alignment.py            (repo root)
     python3 Tests/P4_entry_determination/p4_17_chat_alignment.py --selftest
"""
import argparse, os, re, sys
from collections import Counter
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds, MONTHS   # noqa: E402
from p4_4_probes import rank_auc, boot_ci             # noqa: E402

STOP = set("the a an and or of to in on at for is are was were be been it this that "
           "i you he she we they my your his its with as by from into out up down "
           "not no yes if then than so just now will would can could do did done "
           "have has had get got going go gets me him them us our their there here "
           "about after before again too very s t m re ve ll don isn didn".split())
PRE_MIN = 15
PRESENT_MIN = 30


def tokens(s):
    return [w for w in re.findall(r"[a-z]{2,}", str(s).lower()) if w not in STOP]


def mins_since_prev(msg_ns, t_ns):
    i = np.searchsorted(msg_ns, t_ns) - 1
    return (t_ns - msg_ns[i]) / 60e9 if i >= 0 else np.nan


def run(repo):
    msg = pd.read_parquet(os.path.join(repo, "Data/inputs/wrb_messages.parquet"))
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc"])
    sig = pd.read_csv(os.path.join(HERE, "p4_3b_signal_table.csv"))
    sig["comp_ns"] = pd.DatetimeIndex(pd.to_datetime(sig.comp, utc=True)).as_unit("ns").asi8
    msg_ns = np.sort(pd.DatetimeIndex(msg.datetime_utc).as_unit("ns").asi8)

    # 1. coverage
    mdays = set(pd.DatetimeIndex(msg.datetime_utc).date)
    edays = set(pd.DatetimeIndex(ep.first_entry_utc).date)
    print(f"1. COVERAGE: chat on {len(mdays)} days; trading on {len(edays)} days; "
          f"overlap {len(mdays & edays)} ({len(mdays & edays)/len(edays):.0%} of trading days)")

    # 2. presence at the 1,865 signals
    s = sig.copy()
    s["mins_since_msg"] = [mins_since_prev(msg_ns, int(t)) for t in s.comp_ns]
    s["present30"] = s.mins_since_msg <= PRESENT_MIN
    T, K = s[s.taken], s[~s.taken]
    print(f"\n2. PRESENCE (discovery signals): message within prior {PRESENT_MIN} min:")
    print(f"   taken {T.present30.mean():.0%} vs skipped {K.present30.mean():.0%}")
    for pres in (True, False):
        d = s[s.present30 == pres]
        print(f"   take rate when {'PRESENT' if pres else 'quiet>30min'}: "
              f"{d.taken.mean():.1%} (n={len(d)})")
    ci = boot_ci(-T.mins_since_msg, -K.mins_since_msg)
    print(f"   minutes-since-message AUC (taken more recent): {ci['auc']:.3f} "
          f"[{ci['lo']:.3f},{ci['hi']:.3f}] {'CLEARS' if ci['clears'] else 'no'}")

    # 3. words before entries (non-trade messages, both discovery months)
    m = msg[~(msg.trade_action.fillna("") != "")].copy()
    m["ns"] = pd.DatetimeIndex(m.datetime_utc).as_unit("ns").asi8
    en_ns = np.sort(pd.DatetimeIndex(ep.first_entry_utc).as_unit("ns").asi8)
    pre, rest = Counter(), Counter()
    n_pre = n_rest = 0
    for month, _ in MONTHS:
        lo, hi = month_bounds(month)
        mm = m[(m.datetime_utc >= lo) & (m.datetime_utc < hi)]
        for _, r in mm.iterrows():
            j = np.searchsorted(en_ns, r.ns)
            is_pre = j < len(en_ns) and (en_ns[j] - r.ns) <= PRE_MIN * 60e9
            tk = tokens(r.message)
            if is_pre:
                pre.update(tk); n_pre += 1
            else:
                rest.update(tk); n_rest += 1
    print(f"\n3. WORDS IN THE {PRE_MIN} MIN BEFORE AN ENTRY vs his other messages "
          f"(discovery months; {n_pre} vs {n_rest} messages)")
    tot_p, tot_r = sum(pre.values()), sum(rest.values())
    scored = []
    for w, c in pre.items():
        if c >= 5:
            rr = (c / tot_p) / ((rest[w] + 1) / tot_r)
            scored.append((rr, w, c, rest[w]))
    scored.sort(reverse=True)
    print("   over-represented before entries (word, pre-count, elsewhere-count, ratio):")
    for rr, w, c, cr in scored[:15]:
        print(f"     {w:14s} {c:4d} vs {cr:4d}   {rr:4.1f}x")

    # 4. vocabulary inventory, corpus-wide
    print("\n4. INVENTORY (all 31,838 messages; counts of messages containing the word)")
    groups = {
        "absence markers": ["brb", "back", "lunch", "break", "afk", "leaving", "done for"],
        "scheduled news": ["cpi", "fomc", "fed", "nfp", "powell", "news", "report", "pmi",
                           "claims", "gdp", "ism"],
        "chart timeframes": ["1min", "3min", "5min", "10min", "15min", "1m", "3m", "5m"],
        "method vocabulary": ["wrb", "zone", "gap", "contracting", "expanding", "volatility",
                              "interval", "hidden"],
    }
    low = msg.message.astype(str).str.lower()
    for g, words in groups.items():
        counts = {w: int(low.str.contains(rf"\b{re.escape(w)}\b", regex=True).sum()) for w in words}
        top = sorted(counts.items(), key=lambda kv: -kv[1])
        print(f"   {g:17s}: " + "  ".join(f"{w}:{c}" for w, c in top if c > 0))
    print("\nREAD: presence is the measurable version of the standing 'possibly away'")
    print("caveat; words are descriptive leads. Anything promising becomes a condition.")


def selftest():
    assert tokens("The CPI report is BIG today") == ["cpi", "report", "big", "today"]
    ms = np.array([pd.Timestamp("2025-10-06 13:00", tz="UTC").value], dtype=np.int64)
    assert mins_since_prev(ms, pd.Timestamp("2025-10-06 13:07", tz="UTC").value) == 7.0
    assert np.isnan(mins_since_prev(ms, pd.Timestamp("2025-10-06 12:00", tz="UTC").value))
    print("=== SELF-TEST ===\n  tokens + minutes-since OK\nSELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
