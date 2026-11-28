#!/usr/bin/env python3
"""
d8_report.py — shared D-8 reporting shapes (J amendments 2026-11-28):
report card + HIS reference rows + daily breakdown report.
Import-only module; no data is computed at import.
"""
import numpy as np
import pandas as pd


def card_stats(t):
    """t: trades frame with sd, tf, pnl (one month or pooled)."""
    if not len(t):
        return dict(n=0)
    t = t.sort_values("tf")
    eq = t.pnl.cumsum()
    dd = float((eq.cummax() - eq).max())
    loss = (t.pnl < 0).to_numpy()
    streak = best = 0
    for x in loss:
        streak = streak + 1 if x else 0
        best = max(best, streak)
    bd = t.groupby("sd").pnl.sum().sort_values(ascending=False)
    gw = t.pnl[t.pnl > 0].sum(); gl = -t.pnl[t.pnl < 0].sum()
    return dict(n=len(t), net=float(t.pnl.sum()),
                pt=float(t.pnl.mean()), win=float((t.pnl > 0).mean()),
                pf=float(gw / gl) if gl > 0 else np.inf, dd=dd,
                streak=best, top3=float(bd.head(3).sum()),
                days=t.sd.nunique())


def catch_count(t, H):
    c = 0
    for _, h in H.iterrows():
        if len(t[(t.month == h.month) & (t.d == h.side)
                 & (abs(t.tf - h.sec) <= 300)]):
            c += 1
    return c


def card_table(P, tn, months, HGRP, ref_line):
    """Print the report card. HGRP: his group frame (month, sec,
    side) for the catch column, or None."""
    P(ref_line)
    P()
    P("| scope | n | net | per-trade | win% | PF | maxDD | streak |"
      " top3-day share | catch |")
    P("|---|---|---|---|---|---|---|---|---|---|")
    for mo in list(months) + ["POOLED"]:
        t = tn if mo == "POOLED" else tn[tn.month == mo]
        c = card_stats(t)
        if not c["n"]:
            P(f"| {mo} | 0 | - | - | - | - | - | - | - | - |")
            continue
        if HGRP is not None:
            H = HGRP if mo == "POOLED" else HGRP[HGRP.month == mo]
            cstr = f"{catch_count(t, H)}/{len(H)}"
        else:
            cstr = "-"
        sh = (f"{c['top3']/c['net']:+.0%}" if abs(c["net"]) > 1e-9
              else "-")
        P(f"| {mo} | {c['n']} | {c['net']:+.1f} | {c['pt']:+.2f} | "
          f"{c['win']:.0%} | {c['pf']:.2f} | {c['dd']:.1f} | "
          f"{c['streak']} | {sh} ({c['days']} days) | {cstr} |")
    P()


def his_rows(P, months, group_name, HGRP):
    """HIS reference rows from the D-8 ground truth. Context, not
    like-for-like: his P&L is per HIS scaling and holds."""
    gt = pd.read_parquet("Tests/D8_judgment/d8_ground_truth.parquet")
    gt = gt[gt.month.isin(months)].copy()
    gt["pl"] = np.where(gt.pnl_stated.notna(), gt.pnl_stated,
                        gt.pnl_calc)
    P("HIS reference (verified trades; HIS scaling and holds - "
      "context, not like-for-like):")
    P()
    P(f"| scope | HIS n (all) | HIS net | HIS per-trade | "
      f"HIS n ({group_name}) | net | per-trade |")
    P("|---|---|---|---|---|---|---|")
    for mo in list(months) + ["POOLED"]:
        g = gt if mo == "POOLED" else gt[gt.month == mo]
        if HGRP is not None:
            Hm = HGRP if mo == "POOLED" else HGRP[HGRP.month == mo]
            sub = g.merge(Hm[["month", "sec"]], left_on=["month",
                          "entry_msg_s"], right_on=["month", "sec"])
            s = (f"{len(sub)} | {sub.pl.sum():+.1f} | "
                 f"{sub.pl.mean():+.2f}" if len(sub) else "0 | - | -")
        else:
            s = "- | - | -"
        P(f"| {mo} | {len(g)} | {g.pl.sum():+.1f} | "
          f"{g.pl.mean():+.2f} | {s} |")
    P()


def daily_breakdown(P, tn, months, stop_val=3.75):
    """The daily breakdown report (J, 2026-11-28)."""
    for mo in months:
        t = tn[tn.month == mo]
        if not len(t):
            continue
        P(f"DAILY BREAKDOWN — {mo}:")
        P()
        P("| day | trades | day P/L | wins | full stops | "
          "running P/L |")
        P("|---|---|---|---|---|---|")
        d = t.groupby("sd").agg(
            n=("pnl", "size"), pl=("pnl", "sum"),
            w=("pnl", lambda x: int((x > 0).sum())),
            st=("pnl", lambda x: int((x <= -(stop_val - 0.01)).sum())))
        run = 0.0
        for sd, r in d.iterrows():
            run += r.pl
            P(f"| {sd} | {int(r.n)} | {r.pl:+.1f} | {int(r.w)} | "
              f"{int(r.st)} | {run:+.1f} |")
        P()
