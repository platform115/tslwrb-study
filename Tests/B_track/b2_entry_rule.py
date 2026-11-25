#!/usr/bin/env python3
"""
b2_entry_rule.py — B2: the G2 entry rule (T-EN103). Spec: B2_SPEC.md
(committed first). Entries only; management = B3.
RUN: python3 Tests/B_track/b2_entry_rule.py > Tests/B_track/B2_REPORT.md
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
for d in ("P6_imitation_study", "P4_entry_determination",
          "P5_trade_management"):
    sys.path.insert(0, os.path.join(T, d))
from p6_0_feature_battery import build_ctx, battery          # noqa: E402
from p6_22_s6_1_presence import Resolver                     # noqa: E402
from p6_23_s6_2_interaction import edges_at                  # noqa: E402
from p4_3_confluence_news import news_sets                   # noqa: E402

MONTHS = {"2025-10": "2025-11-01", "2022-02": "2022-03-01"}
DISPS = [1.25, 2.50]
ORDER_TTL = 300
DEDUP = 300
P_C, S_C, T_C = 4.50, 2.50, 240          # center barrier cell
SENS = [("profit 2.25", 2.25, S_C, T_C), ("profit 7.25", 7.25, S_C, T_C),
        ("stop 0.75", P_C, 0.75, T_C), ("stop 3.75", P_C, 3.75, T_C),
        ("time 120", P_C, S_C, 120), ("time 660", P_C, S_C, 660)]
OIL = "Crude Oil Inventories"

# ---- his G2 trades (targets) ----
F = pd.read_parquet("Data/inputs/a2_features.parquet")
F = F[(F.who == "his") & F.data_fresh].copy()
m = F.kme_mins_since
F["np_"] = np.where(np.isfinite(m) & (m <= 5), "burst",
                    np.where(np.isfinite(m) & (m <= 45), "window", "none"))
def ctx_row(r):
    for f in ("SQZ", "REA", "GAP", "SHD"):
        if r[f"{f}_interact"]:
            return {"SQZ": "squeeze", "REA": "reaction"}.get(f, "other")
    return "other"
F["ctx"] = F.apply(ctx_row, axis=1)
HIS = F[(F.ctx == "squeeze") & (F.np_ == "window")][
    ["month", "sec", "side", "kme_event"]].copy()

cal = pd.read_parquet("Data/inputs/kme_calendar.parquet").dropna(
    subset=["ts_utc"]).sort_values("ts_utc")
cts = (pd.to_datetime(cal.ts_utc, utc=True).dt.as_unit("ns")
       .astype("int64").to_numpy() // 10**9)
cev = cal.event.astype(str).to_numpy()


def ev_name(es):
    j = int(np.searchsorted(cts, es, "right")) - 1
    return cev[j] if j >= 0 and abs(int(cts[j]) - int(es)) <= 1 else "?"


def run(repo="."):
    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["sd"] = b.session_date.astype(str)
    zr = pd.read_parquet(os.path.join(repo, "Data/inputs/his_zone_refs.parquet"))
    ev_all = np.asarray(news_sets(repo)["all"], dtype=np.int64) // 10**9
    cands = []
    nd = 0
    for month, nxt in MONTHS.items():
        bm = b[(b.ts_event >= f"{month}-01") & (b.ts_event < nxt)
               ].reset_index(drop=True)
        R = Resolver(bm, zr)
        C = build_ctx(repo, month)
        secs, mids = C["secs"], C["mids"]
        null_p50_mv15 = 0.0  # ambient median of signed mv15 is 0 (A2.2)
        sd1 = bm.sd.to_numpy()
        bt1 = bm.ts_event.dt.tz_convert(None).astype("int64").to_numpy() // 10**9
        rth = bm.session.eq("RTH").to_numpy() if "session" in bm else None
        nd += bm.sd.nunique()
        evm = ev_all[(ev_all >= secs[0]) & (ev_all <= secs[-1])]
        for es in evm:
            w0, w1 = es + 300, es + 2700
            j0 = int(np.searchsorted(secs, w0))
            j1 = int(np.searchsorted(secs, w1, "right"))
            if j1 - j0 < 60:
                continue
            kb = int(np.searchsorted(bt1, secs[j0], "right")) - 1
            if kb < 0 or (rth is not None and not rth[kb]):
                # window start outside RTH -> skip (spec: RTH windows)
                continue
            sd0 = sd1[kb]
            last_fire = {}
            jj = j0
            while jj < j1:
                t = int(secs[jj])
                t64 = np.datetime64(t, "s")
                E = edges_at(R, sd0, t64, "SQZ")
                px, prev = mids[jj], mids[jj - 1]
                for e in E:
                    d = 0
                    if prev <= e < px:
                        d = 1
                    elif prev >= e > px:
                        d = -1
                    if d == 0:
                        continue
                    key = (round(e, 2), d)
                    if t - last_fire.get(key, -10**9) <= DEDUP:
                        continue
                    last_fire[key] = t
                    for disp in DISPS:
                        lvl = e + disp * d
                        j2 = int(np.searchsorted(secs, t + ORDER_TTL,
                                                 "right"))
                        seg = mids[jj:j2]
                        hit = np.flatnonzero((seg >= lvl) if d > 0
                                             else (seg <= lvl))
                        if not len(hit):
                            continue
                        jf = jj + int(hit[0])
                        tf = int(secs[jf])
                        f = battery(C, t, d)
                        if f is None:
                            continue
                        # barrier labels from the FILL second
                        def lab(P, S, TT):
                            j3 = int(np.searchsorted(secs, tf + TT,
                                                     "right"))
                            exc = (mids[jf:j3] - lvl) * d
                            up = np.flatnonzero(exc >= P)
                            dn = np.flatnonzero(exc <= -S)
                            iu = up[0] if len(up) else 10**9
                            idn = dn[0] if len(dn) else 10**9
                            if iu == idn == 10**9:
                                return float(exc[-1]) if len(exc) else 0.0
                            return P if iu < idn else -S
                        cands.append(dict(
                            month=month, t=t, tf=tf, d=d, edge=e,
                            disp=disp, event=ev_name(es),
                            mv15=f["mv15"], persist=f.get("consec_10s",
                                                          np.nan),
                            flow1=f["flow1"],
                            sig=f.get("sig_samedir_5m", 0.0),
                            pnl_c=lab(P_C, S_C, T_C),
                            **{f"pnl_s{i}": lab(P, S, TT) for
                               i, (_, P, S, TT) in enumerate(SENS)}))
                jj += 1
        print(f"# scanned {month}: {len([c for c in cands if c['month']==month])} fills", file=sys.stderr)
    D = pd.DataFrame(cands)
    # persistence from battery? consec_10s not in battery -> approx via mv10>0
    if D.persist.isna().all():
        D["persist"] = (D.mv15 > 0).astype(float)  # disclosed fallback
    his_t = {mo: HIS[HIS.month == mo] for mo in MONTHS}

    def caught(sub):
        got = set()
        for _, h in HIS.iterrows():
            hh = sub[(sub.month == h.month) & (sub.d == h.side)
                     & (abs(sub.tf - h.sec) <= 300)]
            if len(hh):
                got.add((h.month, h.sec))
        return len(got)

    FILTERS = {
        "none": lambda d: np.ones(len(d), bool),
        "move": lambda d: (d.mv15 > 0).to_numpy(),
        "flow": lambda d: (d.flow1 > 0).to_numpy(),
        "signal": lambda d: (d.sig > 0).to_numpy(),
        "move+flow": lambda d: ((d.mv15 > 0) & (d.flow1 > 0)).to_numpy(),
        "move+signal": lambda d: ((d.mv15 > 0) & (d.sig > 0)).to_numpy(),
        "flow+signal": lambda d: ((d.flow1 > 0) & (d.sig > 0)).to_numpy(),
        "all": lambda d: ((d.mv15 > 0) & (d.flow1 > 0)
                          & (d.sig > 0)).to_numpy(),
    }
    print("# B2 REPORT — THE G2 ENTRY RULE (T-EN103)")
    print("STATUS: CLOSED | 2026-11-25 | Spec: B2_SPEC.md (committed "
          "first) | entries only; management = B3")
    print()
    print(f"Candidate fills scanned: {len(D)} across {nd} sessions; "
          f"his G2 targets: {len(HIS)}.")
    print()
    for disp in DISPS:
        print(f"## DISPLACEMENT {disp} pts")
        print("| filter | fills | fills/day | his caught (of 62) | "
              "extras | extras barrier win | extras avg barrier P&L |")
        print("|---|---|---|---|---|---|---|")
        Dd = D[D.disp == disp]
        for fname, ffun in FILTERS.items():
            sub = Dd[ffun(Dd)]
            c = caught(sub)
            near = np.zeros(len(sub), bool)
            for _, h in HIS.iterrows():
                near |= ((sub.month == h.month).to_numpy()
                         & (np.abs(sub.tf - h.sec) <= 300).to_numpy())
            ex = sub[~near]
            wr = (ex.pnl_c > 0).mean() if len(ex) else np.nan
            ap = ex.pnl_c.mean() if len(ex) else np.nan
            print(f"| {fname} | {len(sub)} | {len(sub)/nd:.1f} | {c} | "
                  f"{len(ex)} | {wr:.0%} | {ap:+.2f} |")
        print()
    # per-event split (center cell, disp grid pooled, filter=move+flow)
    print("## PER-EVENT SPLIT (J's check: oil vs the rest; "
          "filter move+flow, both displacements)")
    sub = D[(D.mv15 > 0) & (D.flow1 > 0)]
    for name, msk in (("Crude Oil Inventories", sub.event == OIL),
                      ("all other events", sub.event != OIL)):
        g = sub[msk]
        wr = (g.pnl_c > 0).mean() if len(g) else np.nan
        print(f"- {name}: {len(g)} fills, barrier win {wr:.0%}, "
              f"avg {g.pnl_c.mean():+.2f} pts")
    print()
    print("## BARRIER SENSITIVITY (filter move+flow, disp 1.25)")
    g = D[(D.disp == 1.25) & (D.mv15 > 0) & (D.flow1 > 0)]
    print(f"- center (P {P_C} / S {S_C} / T {T_C}s): win "
          f"{(g.pnl_c>0).mean():.0%}, avg {g.pnl_c.mean():+.2f}")
    for i, (nm, *_rest) in enumerate(SENS):
        col = g[f"pnl_s{i}"]
        print(f"- {nm}: win {(col>0).mean():.0%}, avg {col.mean():+.2f}")
    print()
    D.to_parquet("Data/inputs/b2_candidates.parquet", index=False)
    print("Candidates saved to Data/inputs/b2_candidates.parquet. "
          "Registry: T-EN103.")


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
