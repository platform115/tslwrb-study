#!/usr/bin/env python3
"""
p6_23_s6_2_interaction.py — S6.2: STRUCTURE INTERACTION BEFORE ENTRY +
EXIT LOCATION + DAY MAP. (T-IM30.)
===============================================================================
S6.1 was negative on price-AT-structure. Reframe (user-approved):
A. ENTRY INTERACTION: within M minutes before the entry second (M in
   {5, 15, 30}, pre-registered), did price CROSS a selected structure edge
   (path moved from one side to the other, entry direction on the
   break side) or REJECT one (touched within 1 pt, entry price >= 2 pts
   away on the entry-direction side)? Families: GAP, SHD, REA, SQZ (BRD
   reported separately - dense). Selection = S6.1's (objects knowable <=
   the entry second; selection taken at t, held for the window - noted).
B. EXIT LOCATION: his actual exit FILL prices (episode exit_prices; time
   anchor = last_exit_utc per episode - per-exit times unavailable, noted)
   vs nearest selected structure edge: share within 1 / 2 / 3 pts, per
   family and any-family, vs matched null.
C. DAY MAP: the 3 busiest sessions printed as a timeline - his entries and
   exits with nearest edges and interaction annotations, for human review.
Null design throughout: 20 time-of-day-matched seconds per real event,
other sessions, same side. Anchors: per-second mids (1-second mandate).

RUN: python3 Tests/P6_imitation_study/p6_23_s6_2_interaction.py       (repo root)
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(T, "P4_entry_determination"))
from p6_22_s6_1_presence import Resolver, MONTH, COLS      # noqa: E402
from p4_66_context_ablation import prep                    # noqa: E402
from p4_2_entry_context import month_bounds                # noqa: E402

RNG = np.random.default_rng(109)
MS = (5, 15, 30)


def edges_at(R, sd, t, fam):
    """Selected structure edges at second t for one family."""
    out = []
    if fam == "GAP":
        objs = [z for z in R._objs(sd, "gap") if z["comp"] <= t]
        best = {}
        for z in objs:
            k = (z["tf"], z["dir"])
            if k not in best or z["comp"] > best[k]["comp"]:
                best[k] = z
        for z in best.values():
            out += [z["lo"], z["hi"]]
    elif fam == "SHD":
        objs = [z for z in R._objs(sd, "shd") if z["comp"] <= t]
        best = {}
        for z in objs:
            k = (z["tf"], z["dir"])
            if k not in best or z["comp"] > best[k]["comp"]:
                best[k] = z
        for z in best.values():
            out += [z["lo"], z["hi"]]
    elif fam == "REA":
        for f2 in ("rea_sw", "rea_zz"):
            best = {}
            for z in R._objs(sd, f2):
                if z["comp"] <= t:
                    k = z["side"]
                    if k not in best or z["comp"] > best[k]["comp"]:
                        best[k] = z
            out += [z["px"] for z in best.values()]
    elif fam == "SQZ":
        for f2 in ("sqz10", "sqz30"):
            eps = [z for z in R._objs(sd, f2) if z["comp"] <= t]
            if eps:
                z = max(eps, key=lambda q: q["comp"])
                out += [z["lo"], z["hi"]]
    return sorted(set(round(e, 2) for e in out))


def interaction(R, sd, t, side, secs, mids, M):
    """Per family: cross/reject of a selected edge within [t-M min, t)."""
    t_ns = t.astype("datetime64[s]").astype(np.int64)
    j1 = int(np.searchsorted(secs, t_ns - M * 60))
    j2 = int(np.searchsorted(secs, t_ns, "right")) - 1
    if j2 - j1 < 5:
        return {}
    w = mids[j1:j2 + 1]
    px_t = mids[j2]
    out = {}
    for fam in ("GAP", "SHD", "REA", "SQZ"):
        hit = False
        for e in edges_at(R, sd, t, fam):
            if w.min() - 1 <= e <= w.max() + 1:          # edge inside window path
                crossed = (w[0] - e) * (px_t - e) < 0 or ((w < e).any() and (w > e).any())
                on_break_side = (px_t - e) * side > 0
                if crossed and on_break_side:
                    hit = True; break
                touched = np.min(np.abs(w - e)) <= 1.0
                away = (px_t - e) * side >= 2.0
                if touched and away:
                    hit = True; break
        out[fam] = hit
    out["ANY"] = any(out.values())
    return out


def run(repo="."):
    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["sd"] = b.session_date.astype(str)
    bm = b[(b.ts_event >= f"{MONTH}-01") & (b.ts_event < "2025-11-01")].reset_index(drop=True)
    zr = pd.read_parquet(os.path.join(repo, "Data/inputs/his_zone_refs.parquet"))
    R = Resolver(bm, zr)
    P = prep(repo, MONTH)
    secs, mids = P["secs"], P["mids"]
    sd1 = bm.sd.to_numpy(); bt1 = bm.ts_event.dt.tz_convert(None).to_numpy()

    def sec_sd(t):
        j = np.searchsorted(bt1, t, "right") - 1
        return sd1[j] if j >= 0 else None

    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")
                         ).dropna(subset=["first_entry_utc"])
    lo, hi = month_bounds(MONTH)
    em = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
    sds = sorted(set(sd1))
    sdm = {s: g for s, g in bm.groupby("sd")}
    print(f"{len(em)} entries", flush=True)

    # ---------- A. entry interaction ----------
    for M in MS:
        him, nul = [], []
        for _, r in em.iterrows():
            t = np.datetime64(pd.Timestamp(r.first_entry_utc).tz_convert(None))
            side = 1 if r.side == "long" else -1
            sd0 = sec_sd(t)
            if sd0 is None:
                continue
            f = interaction(R, sd0, t, side, secs, mids, M)
            if f:
                him.append(f)
            for _ in range(20):
                s2 = sds[RNG.integers(len(sds))]
                base = pd.Timestamp(str(s2)) + pd.Timedelta(
                    hours=pd.Timestamp(t).hour, minutes=pd.Timestamp(t).minute)
                t2 = np.datetime64(base + pd.Timedelta(minutes=int(RNG.integers(-30, 31))))
                if sec_sd(t2) != s2:
                    continue
                f2 = interaction(R, s2, t2, side, secs, mids, M)
                if f2:
                    nul.append(f2)
        H, N = pd.DataFrame(him), pd.DataFrame(nul)
        print(f"\n## A. ENTRY INTERACTION window M={M} min  ({len(H)} entries, {len(N)} nulls)")
        print("| family | his | null | gap |")
        for c in ("GAP", "SHD", "REA", "SQZ", "ANY"):
            print(f"| {c} | {H[c].mean():.0%} | {N[c].mean():.0%} | {H[c].mean()-N[c].mean():+.0%} |")

    # ---------- B. exit location ----------
    him_d, nul_d = [], []
    for _, r in em.iterrows():
        t = np.datetime64(pd.Timestamp(r.last_exit_utc).tz_convert(None))
        sd0 = sec_sd(t)
        if sd0 is None:
            continue
        xs = r.exit_prices if isinstance(r.exit_prices, (list, np.ndarray)) else [r.exit_prices]
        for xp in np.atleast_1d(xs):
            if not np.isfinite(xp):
                continue
            ds = {}
            for fam in ("GAP", "SHD", "REA", "SQZ"):
                E = edges_at(R, sd0, t, fam)
                ds[fam] = min((abs(float(xp) - e) for e in E), default=np.inf)
            him_d.append(ds)
        for _ in range(10):
            s2 = sds[RNG.integers(len(sds))]
            base = pd.Timestamp(str(s2)) + pd.Timedelta(
                hours=pd.Timestamp(t).hour, minutes=pd.Timestamp(t).minute)
            t2 = np.datetime64(base + pd.Timedelta(minutes=int(RNG.integers(-30, 31))))
            if sec_sd(t2) != s2:
                continue
            j2 = int(np.searchsorted(secs, t2.astype("datetime64[s]").astype(np.int64), "right")) - 1
            if j2 < 10:
                continue
            px2 = float(mids[j2])
            ds = {}
            for fam in ("GAP", "SHD", "REA", "SQZ"):
                E = edges_at(R, s2, t2, fam)
                ds[fam] = min((abs(px2 - e) for e in E), default=np.inf)
            nul_d.append(ds)
    H, N = pd.DataFrame(him_d), pd.DataFrame(nul_d)
    print(f"\n## B. EXIT LOCATION  ({len(H)} exit fills, {len(N)} nulls; time anchor = episode last exit)")
    print("| family | his <=1 / <=2 / <=3 | null <=1 / <=2 / <=3 |")
    for c in ("GAP", "SHD", "REA", "SQZ"):
        hs = " / ".join(f"{(H[c] <= k).mean():.0%}" for k in (1, 2, 3))
        ns = " / ".join(f"{(N[c] <= k).mean():.0%}" for k in (1, 2, 3))
        print(f"| {c} | {hs} | {ns} |")
    anyH = H.min(axis=1); anyN = N.min(axis=1)
    print(f"| ANY | " + " / ".join(f"{(anyH <= k).mean():.0%}" for k in (1, 2, 3)) +
          " | " + " / ".join(f"{(anyN <= k).mean():.0%}" for k in (1, 2, 3)) + " |")

    # ---------- C. day map (3 busiest sessions) ----------
    em2 = em.copy()
    em2["sd"] = [sec_sd(np.datetime64(pd.Timestamp(x).tz_convert(None))) for x in em2.first_entry_utc]
    busy = em2.sd.value_counts().head(3).index
    print("\n## C. DAY MAP (3 busiest sessions)")
    for s in busy:
        print(f"\n=== {s} ===")
        for _, r in em2[em2.sd == s].sort_values("first_entry_utc").iterrows():
            t = np.datetime64(pd.Timestamp(r.first_entry_utc).tz_convert(None))
            side = 1 if r.side == "long" else -1
            j = int(np.searchsorted(secs, t.astype("datetime64[s]").astype(np.int64), "right")) - 1
            px = float(mids[j]) if j > 0 else np.nan
            ia = interaction(R, s, t, side, secs, mids, 15)
            fams = [k for k, v in ia.items() if v and k != "ANY"]
            near = {}
            for fam in ("GAP", "SHD", "REA", "SQZ"):
                E = edges_at(R, s, t, fam)
                near[fam] = min((abs(px - e) for e in E), default=np.inf)
            nn = ", ".join(f"{k}:{v:.1f}" for k, v in sorted(near.items(), key=lambda x: x[1])[:2])
            xs = np.atleast_1d(r.exit_prices)
            print(f"  {str(pd.Timestamp(r.first_entry_utc))[11:19]} {r.side:5s} @~{px:.2f} "
                  f"| interacted[15m]: {fams or '-'} | nearest edges: {nn} "
                  f"| exits: {[float(x) for x in xs if np.isfinite(x)]} pnl {r.realized_pnl}")


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
