#!/usr/bin/env python3
"""
p6_12_g1_hidden_gap.py — S3 GENERATOR 1: WRB HIDDEN GAP ZONES + CALIBRATION
vs HIS references. (T-IM17.)
===============================================================================
DEFINITION: WRB Definition.txt (Perry-sourced, S2-approved, unchanged):
  WRB: body strictly > each of prior 3 bodies, same session_date, no doji.
  WHG (bullish): [prior 3 bars' body-high, close] if close above it;
  bearish mirror. Fill: a later bar's H/L covering the whole zone = FILLED;
  entered-but-not-covered = PARTIAL (project convention).
TFs: the S0-decided set 1m, 2m, 3m, 5m, 15m (60m is zones-only, S4+).
ROLL DAYS: bars with is_roll_day=True are EXCLUDED from WRB qualification
  (CLAUDE.md: roll gaps are contract transitions, not market moves).

<=t DISCIPLINE: for a reference at time t, only WRBs whose bar COMPLETED
(open_ts + tf <= t) are candidates, and fill state uses only bars completed
by t. Anchor price = close of the last completed 1m bar at t.

CALIBRATION (his 119 hidden-gap references; ZERO explicit prices, so all
relational): for each reference, distance in POINTS from the anchor price
to the nearest qualifying zone (inside = 0), computed per TF and pooled,
with lookback K sessions (zone created same session or up to K-1 before).
Direction honored when his message states up/down. Reported for ALL zones
and UNFILLED-only.
AMBIENT NULL: same measurement at N random session-matched times -> if his
references are no closer to zones than random moments, the zones explain
nothing (anti-saturation check, user rule).

RUN: python3 Tests/P6_imitation_study/p6_12_g1_hidden_gap.py          (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

TFS = (1, 2, 3, 5, 15)
K_SESS = 5          # zone lookback: same session + up to 4 before (reported split)
TOL_GRID = (0.0, 1.0, 2.0, 3.0)   # points beyond the band edge
N_NULL = 400
RNG = np.random.default_rng(17)


def resample_tf(b, tf):
    """b: contiguous 1m bars one session; label = OPEN time of the window."""
    if tf == 1:
        return b
    g = b.set_index("ts_event").resample(f"{tf}min")
    out = pd.DataFrame(dict(
        open=g.open.first(), high=g.high.max(), low=g.low.min(),
        close=g.close.last(), is_roll_day=g.is_roll_day.max())).dropna()
    out["session_date"] = str(b.session_date.iloc[0])
    return out.reset_index()


def whg_zones(bars, tf):
    """S2-approved definition. Returns list of dicts with completion ts."""
    o = bars.open.to_numpy(); c = bars.close.to_numpy()
    h = bars.high.to_numpy(); l = bars.low.to_numpy()
    roll = bars.is_roll_day.to_numpy()
    ts = bars.ts_event.to_numpy()
    body = np.abs(c - o)
    zones = []
    for i in range(3, len(bars)):
        if roll[i] or body[i] <= 0:
            continue
        if not (body[i] > body[i-1] and body[i] > body[i-2] and body[i] > body[i-3]):
            continue
        if c[i] > o[i]:
            pbh = max(o[i-1], c[i-1], o[i-2], c[i-2], o[i-3], c[i-3])
            if c[i] > pbh:
                zones.append(dict(tf=tf, dir="up", lo=pbh, hi=c[i],
                                  comp=ts[i] + np.timedelta64(tf, "m"), bar_i=i))
        elif c[i] < o[i]:
            pbl = min(o[i-1], c[i-1], o[i-2], c[i-2], o[i-3], c[i-3])
            if c[i] < pbl:
                zones.append(dict(tf=tf, dir="down", lo=c[i], hi=pbl,
                                  comp=ts[i] + np.timedelta64(tf, "m"), bar_i=i))
    return zones


def fill_state(z, h1, l1, ts1, t):
    """Zone state at time t from COMPLETED 1m bars in (comp, t]."""
    a = np.searchsorted(ts1, z["comp"])
    b = np.searchsorted(ts1, t - np.timedelta64(60, "s"), "right")
    if b <= a:
        return "UNFILLED"
    hh, ll = h1[a:b], l1[a:b]
    if ((hh >= z["hi"]) & (ll <= z["lo"])).any():
        return "FILLED"
    if ((ll <= z["hi"]) & (hh >= z["lo"])).any():
        return "PARTIAL"
    return "UNFILLED"


def measure(t, px, want_dir, sess_bars_by_tf, ts1, h1, l1, sess_list, sd_of_t):
    """Distances (pts) to nearest zone: (any_state, unfilled_only) per sess-back."""
    best_any = {k: np.inf for k in range(K_SESS)}
    best_unf = {k: np.inf for k in range(K_SESS)}
    si = sess_list.index(sd_of_t)
    for k in range(K_SESS):
        if si - k < 0:
            break
        sd = sess_list[si - k]
        for tf in TFS:
            for z in sess_bars_by_tf[(sd, tf)]:
                if z["comp"] > t - np.timedelta64(0, "s"):
                    continue
                if want_dir in ("up", "down") and z["dir"] != want_dir:
                    continue
                d = 0.0 if z["lo"] <= px <= z["hi"] else min(abs(px - z["lo"]), abs(px - z["hi"]))
                if d < best_any[k]:
                    best_any[k] = d
                if d < best_unf[k]:
                    st = fill_state(z, h1, l1, ts1, t)
                    if st != "FILLED":
                        best_unf[k] = d
    # cumulative over lookback
    ca, cu = [], []
    m1 = m2 = np.inf
    for k in range(K_SESS):
        m1 = min(m1, best_any[k]); m2 = min(m2, best_unf[k])
        ca.append(m1); cu.append(m2)
    return ca, cu


def run(repo):
    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["sd"] = b.session_date.astype(str)
    z = pd.read_parquet(os.path.join(repo, "Data/inputs/his_zone_refs.parquet"))
    hg = z[z.kind == "hidden_gap"].copy()
    hg["t"] = pd.to_datetime(hg.ts_utc, utc=True).dt.tz_convert(None).to_numpy()
    ts1 = b.ts_event.dt.tz_convert(None).to_numpy()
    h1, l1, c1 = b.high.to_numpy(), b.low.to_numpy(), b.close.to_numpy()
    sd_arr = b.sd.to_numpy()
    sess_list = list(dict.fromkeys(sd_arr))        # ordered unique sessions
    sd_first = {s: i for i, s in enumerate(sess_list)}

    # map each needed time -> session date via bar lookup
    def sd_at(t):
        t = np.datetime64(t)
        j = np.searchsorted(ts1, t, "right") - 1
        return sd_arr[j] if j >= 0 else None

    # which sessions need zones? refs' sessions + K before (and null times share them)
    needed = set()
    for t in hg["t"]:
        s = sd_at(np.datetime64(t))
        if s is None:
            continue
        si = sess_list.index(s)
        for k in range(K_SESS):
            if si - k >= 0:
                needed.add(sess_list[si - k])
    print(f"{len(hg)} hidden-gap refs -> computing zones for {len(needed)} sessions x {len(TFS)} TFs")

    groups = {s: g.reset_index(drop=True) for s, g in b.groupby("sd") if s in needed}
    Z = {}
    for s, g in groups.items():
        for tf in TFS:
            rb = resample_tf(g[["ts_event", "open", "high", "low", "close",
                                "is_roll_day", "session_date"]], tf)
            rb["ts_event"] = rb.ts_event.dt.tz_convert(None)
            Z[(s, tf)] = whg_zones(rb.assign(ts_event=rb.ts_event), tf)
    nz = sum(len(v) for v in Z.values())
    print(f"zones generated: {nz} (mean {nz/max(1,len(needed)):.0f}/session over {len(TFS)} TFs)")

    # --- his references ---
    A, U, used = [], [], 0
    for _, r in hg.iterrows():
        t = np.datetime64(r["t"]); s = sd_at(t)
        if s is None or s not in groups:
            continue
        j = np.searchsorted(ts1, t - np.timedelta64(60, "s"), "right") - 1
        if j < 0:
            continue
        px = c1[j]
        ca, cu = measure(t, px, r["direction"], Z, ts1, h1, l1, sess_list, s)
        A.append(ca); U.append(cu); used += 1
    A, U = np.array(A), np.array(U)

    # --- ambient null: random times in the SAME sessions, same session period ---
    nullA, nullU = [], []
    ref_sess = [sd_at(t) for t in hg["t"] if sd_at(t) in groups]
    for i in range(N_NULL):
        s = ref_sess[RNG.integers(len(ref_sess))]
        g = groups[s]
        jj = RNG.integers(20, len(g))
        t = np.datetime64(g.ts_event.iloc[jj].tz_convert(None)) + np.timedelta64(60, "s")
        j = np.searchsorted(ts1, t - np.timedelta64(60, "s"), "right") - 1
        px = c1[j]
        dirs = ["up", "down", "none"][RNG.integers(3)]
        ca, cu = measure(t, px, dirs, Z, ts1, h1, l1, sess_list, s)
        nullA.append(ca); nullU.append(cu)
    nullA, nullU = np.array(nullA), np.array(nullU)

    print(f"\n===== CALIBRATION: his {used} hidden-gap refs vs {N_NULL} session-matched random times =====")
    print("(distance in POINTS from anchor price to nearest zone; inside = 0)")
    for name, X, NX in (("ALL zones", A, nullA), ("UNFILLED/PARTIAL only", U, nullU)):
        print(f"\n## {name}")
        print("| lookback | his: med dist | within 0 / 1 / 2 / 3 pts | null: med | within 0 / 1 / 2 / 3 pts |")
        print("|---|---|---|---|---|")
        for k in (0, 1, 2, 4):
            x, nx = X[:, k], NX[:, k]
            hs = " / ".join(f"{(x <= tol).mean():.0%}" for tol in TOL_GRID)
            ns = " / ".join(f"{(nx <= tol).mean():.0%}" for tol in TOL_GRID)
            print(f"| same-sess+{k} | {np.median(x[np.isfinite(x)]):.2f} | {hs} "
                  f"| {np.median(nx[np.isfinite(nx)]):.2f} | {ns} |")
    # ---- SELECTIVITY PASS: his language says "most recent" (57/119) and
    # "Big" (47/119); raw per-definition zones saturate (the result above).
    # Variants measured identically, lookback = same-sess+4 (cumulative):
    #   R  = most-recent unfilled/partial zone per (TF, dir) at t
    #   Bx = zone size >= x points
    #   R&Bx, and R per single TF
    def measure_sel(t, px, want_dir, s, mode, tf_only=None, bmin=0.0):
        si = sess_list.index(s)
        cands = []
        for k in range(K_SESS):
            if si - k < 0:
                break
            sd = sess_list[si - k]
            for tf in TFS:
                if tf_only and tf != tf_only:
                    continue
                for z in Z[(sd, tf)]:
                    if z["comp"] > t:
                        continue
                    if want_dir in ("up", "down") and z["dir"] != want_dir:
                        continue
                    if (z["hi"] - z["lo"]) < bmin:
                        continue
                    cands.append(z)
        if mode == "recent":
            # keep only the most recent per (tf, dir) that is not FILLED
            best = {}
            for z in cands:
                key = (z["tf"], z["dir"])
                if key not in best or z["comp"] > best[key]["comp"]:
                    best[key] = z
            # walk back if the latest is filled: sort per key by comp desc
            byk = {}
            for z in cands:
                byk.setdefault((z["tf"], z["dir"]), []).append(z)
            sel = []
            for key, zs in byk.items():
                for z in sorted(zs, key=lambda q: q["comp"], reverse=True):
                    if fill_state(z, h1, l1, ts1, t) != "FILLED":
                        sel.append(z); break
            cands = sel
        else:
            cands = [z for z in cands if fill_state(z, h1, l1, ts1, t) != "FILLED"]
        d = np.inf
        for z in cands:
            dd = 0.0 if z["lo"] <= px <= z["hi"] else min(abs(px - z["lo"]), abs(px - z["hi"]))
            d = min(d, dd)
        return d

    variants = [("R all-TF", dict(mode="recent")),
                ("B>=2", dict(mode="all", bmin=2.0)),
                ("B>=4", dict(mode="all", bmin=4.0)),
                ("B>=6", dict(mode="all", bmin=6.0)),
                ("R & B>=2", dict(mode="recent", bmin=2.0)),
                ("R & B>=4", dict(mode="recent", bmin=4.0))] +                [(f"R tf={tf}m", dict(mode="recent", tf_only=tf)) for tf in TFS]
    his_pts = []
    for _, r in hg.iterrows():
        t = np.datetime64(r["t"]); ss = sd_at(t)
        if ss is None or ss not in groups:
            continue
        j = np.searchsorted(ts1, t - np.timedelta64(60, "s"), "right") - 1
        his_pts.append((t, c1[j], r["direction"], ss))
    null_pts = []
    for i in range(N_NULL):
        ss = ref_sess[RNG.integers(len(ref_sess))]
        g = groups[ss]
        jj = RNG.integers(20, len(g))
        t = np.datetime64(g.ts_event.iloc[jj].tz_convert(None)) + np.timedelta64(60, "s")
        j = np.searchsorted(ts1, t - np.timedelta64(60, "s"), "right") - 1
        null_pts.append((t, c1[j], ["up", "down", "none"][RNG.integers(3)], ss))
    print("\n===== SELECTIVITY (unfilled/partial, lookback same-sess+4) =====")
    print("| variant | his med | his within 0/1/2/3 | null med | null within 0/1/2/3 | edge@1pt |")
    print("|---|---|---|---|---|---|")
    for name, kw in variants:
        dh = np.array([measure_sel(t, px, d_, ss, **kw) for (t, px, d_, ss) in his_pts])
        dn = np.array([measure_sel(t, px, d_, ss, **kw) for (t, px, d_, ss) in null_pts])
        hs = "/".join(f"{(dh <= tol).mean():.0%}" for tol in TOL_GRID)
        ns = "/".join(f"{(dn <= tol).mean():.0%}" for tol in TOL_GRID)
        edge = (dh <= 1.0).mean() - (dn <= 1.0).mean()
        print(f"| {name} | {np.median(dh[np.isfinite(dh)]):.2f} | {hs} "
              f"| {np.median(dn[np.isfinite(dn)]):.2f} | {ns} | {edge:+.0%} |")
    return A, U, nullA, nullU


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
