#!/usr/bin/env python3
"""
a2_1_ground_truth.py — A2.1: ground truth table + label audit (T-IM40).
Spec: A2_1_SPEC.md (frozen). Months: training only (2025-10, 2022-02).
RUN: python3 Tests/A2_measurement/a2_1_ground_truth.py          (repo root)
OUT: Data/inputs/a2_ground_truth.parquet + printed report.
"""
import os
import sys

import numpy as np
import pandas as pd

TOL = 0.5          # pt tolerance for a "touch" of a reported price
BACK = 600         # seconds searched before the message
FWD = 120          # seconds searched after the message
MONTHS = ["2025-10", "2022-02"]


def month_flow(repo, month):
    f = pd.read_parquet(
        os.path.join(repo, f"Data/inputs/flow_per_sec_{month}_full.parquet"))
    return f.sec.to_numpy(), f.mid.to_numpy()


def touch_audit(secs, mids, msg_s, price):
    """Returns (verified, lag_s, flag, min_dist) for one reported price."""
    j1 = int(np.searchsorted(secs, msg_s - BACK))
    j2 = int(np.searchsorted(secs, msg_s + FWD, "right"))
    if j2 <= j1:
        return False, np.nan, "no_data_window", np.nan
    w = mids[j1:j2]
    ws = secs[j1:j2]
    d = np.abs(w - price)
    md = float(d.min())
    hit = d <= TOL
    if not hit.any():
        return False, np.nan, "unverified", md
    before = hit & (ws <= msg_s)
    if before.any():
        lag = float(msg_s - ws[np.flatnonzero(before)[-1]])
        return True, lag, "", md
    return True, np.nan, "touch_only_after", md


def run(repo="."):
    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"),
                        columns=["ts_event", "session_date", "is_roll_day"])
    b = b.sort_values("ts_event").reset_index(drop=True)
    bt = b.ts_event.dt.tz_convert(None).to_numpy()
    bsd = b.session_date.astype(str).to_numpy()
    broll = b.is_roll_day.to_numpy()

    ep = pd.read_parquet(
        os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet"))
    ep["m"] = pd.to_datetime(ep.first_entry_utc, utc=True).dt.strftime("%Y-%m")
    rows = []
    for month in MONTHS:
        secs, mids = month_flow(repo, month)
        em = ep[ep.m == month]
        for _, r in em.iterrows():
            t_in = pd.Timestamp(r.first_entry_utc).tz_convert("UTC")
            t_out = pd.Timestamp(r.last_exit_utc).tz_convert("UTC") \
                if pd.notna(r.last_exit_utc) else pd.NaT
            s_in = int(t_in.timestamp())
            s_out = int(t_out.timestamp()) if pd.notna(t_out) else None
            fills = np.atleast_1d(r.entry_prices).astype(float)
            exits = np.atleast_1d(r.exit_prices).astype(float) \
                if r.exit_prices is not None else np.array([])
            side = 1 if r.side == "long" else -1

            ev, elag, eflag, edist = touch_audit(secs, mids, s_in, fills[0]) \
                if np.isfinite(fills[0]) else (False, np.nan, "no_price", np.nan)
            if len(exits) and np.isfinite(exits[-1]) and s_out:
                xv, xlag, xflag, xdist = touch_audit(secs, mids, s_out, exits[-1])
            else:
                xv, xlag, xflag, xdist = False, np.nan, "no_exit_price", np.nan

            # P&L reconciliation (stated limitation: sizes unknowable)
            if len(exits) and np.isfinite(fills).all() and np.isfinite(exits).all():
                calc = (np.mean(exits) - np.mean(fills)) * side
                recon = abs(calc - float(r.realized_pnl)) <= 0.5 \
                    if pd.notna(r.realized_pnl) else False
            else:
                calc, recon = np.nan, False

            # outcomes (y): MAE/MFE over the reported hold, 1s mids
            mae = mfe = np.nan
            hold = np.nan
            if s_out and s_out > s_in:
                j1 = int(np.searchsorted(secs, s_in))
                j2 = int(np.searchsorted(secs, s_out, "right"))
                if j2 > j1 and np.isfinite(fills[0]):
                    exc = (mids[j1:j2] - fills[0]) * side
                    mae, mfe = float(-exc.min()), float(exc.max())
                hold = s_out - s_in
            # context tags
            j = int(np.searchsorted(bt, np.datetime64(t_in.tz_convert(None)),
                                    "right")) - 1
            sd = bsd[j] if j >= 0 else None
            roll = bool(broll[j]) if j >= 0 else False
            ct = t_in.tz_convert("America/Chicago")
            rth = (ct.hour, ct.minute) >= (8, 30) and ct.hour < 15

            rows.append(dict(
                episode_id=int(r.episode_id), month=month, session_date=sd,
                side=r.side, n_entries=int(r.n_entries),
                n_exits=int(r.n_exits), scaled=bool(r.scaled),
                entry_msg_s=s_in, exit_msg_s=s_out,
                entry_price=fills[0] if len(fills) else np.nan,
                exit_price=exits[-1] if len(exits) else np.nan,
                entry_verified=ev, posting_lag_s=elag, entry_flag=eflag,
                entry_min_dist=edist,
                exit_verified=xv, exit_lag_s=xlag, exit_flag=xflag,
                exit_min_dist=xdist,
                pnl_stated=float(r.realized_pnl) if pd.notna(r.realized_pnl)
                else np.nan,
                pnl_calc=calc, pnl_recon=recon, pnl_ok_src=bool(r.pnl_ok),
                mae_pts=mae, mfe_pts=mfe, hold_s=hold,
                is_roll_day=roll, rth=rth, src=r.source_file))
    g = pd.DataFrame(rows)
    out = os.path.join(repo, "Data/inputs/a2_ground_truth.parquet")
    g.to_parquet(out, index=False)

    print(f"===== A2.1 GROUND TRUTH + LABEL AUDIT ({len(g)} episodes) =====")
    for month, gm in g.groupby("month"):
        lag = gm.posting_lag_s.dropna()
        print(f"\n-- {month} ({len(gm)} trades) --")
        print(f"entry verified: {gm.entry_verified.mean():.0%} | "
              f"exit verified: {gm.exit_verified.mean():.0%} | "
              f"P&L reconciled: {gm.pnl_recon.mean():.0%} "
              f"(single-entry only: "
              f"{gm[gm.n_entries == 1].pnl_recon.mean():.0%})")
        if len(lag):
            q = np.percentile(lag, [50, 75, 90, 99])
            print(f"posting lag s q50/75/90/99: "
                  f"{q[0]:.0f} / {q[1]:.0f} / {q[2]:.0f} / {q[3]:.0f} | "
                  f">120s: {(lag > 120).mean():.0%}")
        print(f"roll-day trades: {gm.is_roll_day.sum()} | "
              f"ETH entries: {(~gm.rth).sum()}")
    print("\n## AMBIGUITY LEDGER (flagged, for J - nothing dropped)")
    bad = g[(~g.entry_verified) | (g.entry_flag == "touch_only_after") |
            (g.posting_lag_s > 120)]
    for _, r in bad.iterrows():
        print(f"  ep{r.episode_id} {r.month} {r.side:5s} "
              f"entry {r.entry_price} flag={r.entry_flag or 'lag>120'} "
              f"lag={r.posting_lag_s} min_dist={r.entry_min_dist:.2f}")
    if not len(bad):
        print("  none")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
