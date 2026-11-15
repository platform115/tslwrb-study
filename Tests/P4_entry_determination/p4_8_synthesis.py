#!/usr/bin/env python3
"""
p4_8_synthesis.py — P4.8: combine the cleared components into a draft entry rule.
==================================================================================
GOAL (user, 2026-11-15): find something that WORKS. This step is CONSTRUCTIVE, not
a hypothesis test: the rule is built on the discovery months and gets its real test
on the reserved years. Recorded as such (registry row T-EN10).

INPUTS (all previously computed, per signal): the locked signal table (p4_3b),
trailing-tape features (p4_6), trailing flow (p4_7), template minutes (p4_6).

SIX CONDITIONS, one per cleared component — thresholds are deterministic
(pooled-all-signal medians or zero), chosen BEFORE seeing combined results:
  C1 kme_born15   signal completed within 15 min of a scheduled event (T-EN01)
  C2 htf_overlap  signal's zone overlaps direction-matched zones on >=3 of the
                  3/5/10/15m charts (T-EN02)
  C3 big_body     signal WRB body >= pooled median (T-EN03)
  C4 fast_tape    trailing 5-min path >= pooled median (T-EN08)
  C5 flow_with    trailing 5-min oriented flow > 0 (T-EN09; NaN -> False,
                  i.e. unknown flow never helps the score)
  C6 template     the completion minute is a template minute: event -> reaction
                  WRB -> price at/inside its body (T-EN06)
SCORE = number of conditions true (0..6). Outputs: redundancy matrix (Spearman),
take rate by score, and for each cutoff k the rule "score >= k": how many of his
entries it captures, the take rate among flagged signals, and lift vs base rate.

RUN: python3 Tests/P4_entry_determination/p4_8_synthesis.py            (repo root)
     python3 Tests/P4_entry_determination/p4_8_synthesis.py --selftest
OUT: p4_8_synthesis.csv (per-signal conditions + score).
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

COND_COLS = ["c1_kme_born15", "c2_htf_overlap", "c3_big_body",
             "c4_fast_tape", "c5_flow_with", "c6_template"]


def build_table():
    sig = pd.read_csv(os.path.join(HERE, "p4_3b_signal_table.csv"))
    sig["comp_ns"] = pd.DatetimeIndex(pd.to_datetime(sig.comp, utc=True)).as_unit("ns").asi8
    f6 = pd.read_csv(os.path.join(HERE, "p4_6_signal_features.csv"))
    f7 = pd.read_csv(os.path.join(HERE, "p4_7_trailing_flow.csv"))
    tm = pd.read_csv(os.path.join(HERE, "p4_6_template_minutes.csv"))

    # join p4_6 by comp_ns (it carries the key); p4_7 positionally within month
    # (built by iterating the same CSV in the same order) with hard checks.
    df = sig.merge(f6[["comp_ns", "en08_path_5m_tk"]], on="comp_ns", how="left")
    assert len(df) == len(sig)
    parts = []
    for month in sig.month.unique():
        a = sig[sig.month == month].reset_index(drop=True)
        b = f7[f7.month == month].reset_index(drop=True)
        assert len(a) == len(b) and (a.taken.to_numpy() == b.taken.to_numpy()).all(), \
            f"[join] p4_7 row order mismatch for {month}"
        parts.append(pd.DataFrame({"comp_ns": a.comp_ns, "flow_5m": b.flow_5m}))
    df = df.merge(pd.concat(parts), on="comp_ns", how="left")
    t = tm[tm.template][["t_ns"]].drop_duplicates().rename(columns={"t_ns": "comp_ns"})
    t["c6_template"] = True
    df = df.merge(t, on="comp_ns", how="left")
    df["c6_template"] = df.c6_template.fillna(False).astype(bool)

    med_body = float(df.body_tk.median()); med_path = float(df.en08_path_5m_tk.median())
    df["c1_kme_born15"] = df.kme_born_15_all.astype(bool)
    df["c2_htf_overlap"] = df.n_htf_overlap_dir >= 3
    df["c3_big_body"] = df.body_tk >= med_body
    df["c4_fast_tape"] = df.en08_path_5m_tk >= med_path
    df["c5_flow_with"] = df.flow_5m.fillna(-1) > 0
    df["score"] = df[COND_COLS].sum(axis=1)
    return df, med_body, med_path


def run(repo):
    df, med_body, med_path = build_table()
    df.to_csv(os.path.join(HERE, "p4_8_synthesis.csv"), index=False)
    base = df.taken.mean()
    print(f"signals={len(df)} taken={int(df.taken.sum())} base take rate={base:.1%}"
          f" | thresholds: body>={med_body:.0f} tk, 5m path>={med_path:.0f} tk")

    print("\n===== redundancy: Spearman correlation between the six conditions =====")
    c = df[COND_COLS].astype(int).corr(method="spearman").round(2)
    print(c.to_string())
    print("(anything >= ~0.5 is close to the same thing measured twice)")

    print("\n===== take rate by score (how many conditions are true at once) =====")
    g = df.groupby("score").agg(n=("taken", "size"), taken=("taken", "sum"))
    g["take_rate"] = (g.taken / g.n)
    for s, r in g.iterrows():
        print(f"  score {s}: {int(r.n):5d} signals, {int(r.taken):3d} taken, take rate {r.take_rate:6.1%}")

    print("\n===== rule candidates: flag signals with score >= k =====")
    print(f"{'k':>2} {'flagged':>8} {'of his entries captured':>24} {'take rate on flagged':>21} {'lift':>6}")
    for k in range(1, 7):
        f = df[df.score >= k]
        rec = f.taken.sum() / df.taken.sum()
        prec = f.taken.mean() if len(f) else np.nan
        print(f"{k:>2} {len(f):>8} {rec:>23.1%} {prec:>20.1%} {prec/base:>5.1f}x")
    print("\nper-month check of the middle cutoffs:")
    for month in df.month.unique():
        d = df[df.month == month]; b = d.taken.mean()
        for k in (3, 4):
            f = d[d.score >= k]
            print(f"  {month} k={k}: flagged {len(f)}, captures {f.taken.sum()/d.taken.sum():.0%}"
                  f" of entries, take rate {f.taken.mean():.1%} ({f.taken.mean()/b:.1f}x base)")

    print("\n===== what each condition adds on top of the other five =====")
    for col in COND_COLS:
        others = [c2 for c2 in COND_COLS if c2 != col]
        s5 = df[others].sum(axis=1)
        hi = df[s5 >= 3]          # among already-promising signals
        if hi[col].nunique() == 2:
            a = hi[hi[col]].taken.mean(); b2 = hi[~hi[col]].taken.mean()
            print(f"  {col:16s}: among signals with >=3 of the others, take rate "
                  f"{a:.1%} with it vs {b2:.1%} without")
    print("\nREAD: constructed on the discovery months - the reserved years are the test.")


def selftest():
    print("=== SELF-TEST ===")
    d = pd.DataFrame({c: [True, False] for c in COND_COLS})
    assert d[COND_COLS].sum(axis=1).tolist() == [6, 0]
    print("  score counting OK")
    df, mb, mp = build_table()
    assert len(df) == 1865 and df.taken.sum() == 179, (len(df), df.taken.sum())
    assert df.c6_template.sum() > 0 and df.c5_flow_with.notna().all()
    print(f"  table build OK: {len(df)} signals, template-flagged={int(df.c6_template.sum())}")
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
