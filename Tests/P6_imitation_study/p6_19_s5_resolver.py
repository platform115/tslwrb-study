#!/usr/bin/env python3
"""
p6_19_s5_resolver.py — S5: RESOLVER + HIT-RATE DASHBOARD. (T-IM26.)
===============================================================================
A. TOLERANCE SCHEDULE DASHBOARD - per kind (its adopted generator +
   selection), per year: hit rate at tolerance 3 / 2 / 1.5 / 1 pts.
   The narrowing schedule the charter requires, measured not assumed.
B. KEY-ZONE MAINTAINED-LIST RECONSTRUCTION - forward prediction test:
   the zone list at time t = prices he STATED in Key-zone messages BEFORE t
   (each stated price opens a +/-3 band, refreshed on re-statement, expiry
   E days after last statement). Test: his later UNPRICED relational
   Key-zone references - does market price sit on a list zone? Null: the
   same test at random RTH times in the same sessions. E in {30, 90, 9999}.
   <=t throughout: only messages strictly before t enter the list.

RUN: python3 Tests/P6_imitation_study/p6_19_s5_resolver.py            (repo root)
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

K_SESS = 5
TOLS = (3.0, 2.0, 1.5, 1.0)
RNG = np.random.default_rng(89)
KIND2GEN = {"hidden_gap": ("g1_whg", None), "shadow_interval": ("g2_shadow_d2", None),
            "reaction_hl": ("g3_swing", "N2"), "contraction": ("g4_c2", "W15"),
            "tight_range": ("g4_c2", "W30"), "trading_range": ("g4_c2", "W30")}
DIRMAP = {"up": "up", "down": "down", "upper": "upper", "lower": "lower",
          "high": "high", "low": "low"}


def load_env(repo):
    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"),
                        columns=["ts_event", "close", "session_date", "session"])
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["sd"] = b.session_date.astype(str)
    O = pd.read_parquet(os.path.join(repo, "Data/inputs/s4_objects.parquet"))
    O["kts"] = pd.to_datetime(O.knowable_ts).to_numpy()
    zr = pd.read_parquet(os.path.join(repo, "Data/inputs/his_zone_refs.parquet"))
    return b, O, zr


def dashboard(repo):
    b, O, zr = load_env(repo)
    ts1 = b.ts_event.dt.tz_convert(None).to_numpy()
    c1 = b.close.to_numpy()
    sd_arr = b.sd.to_numpy()
    sess_list = list(dict.fromkeys(sd_arr))
    sess_idx = {s: i for i, s in enumerate(sess_list)}
    by_sess = {s: g for s, g in O.groupby("session_date")}
    R = zr[(zr.instrument == "ES")
           & (zr.ref_type.isin(["relational", "explicit_price", "event"]))
           & (zr.kind.isin(KIND2GEN))].copy()
    print(f"A. DASHBOARD refs: {len(R)}", flush=True)

    def min_dist(r):
        t = np.datetime64(pd.Timestamp(r.ts_utc).tz_convert(None))
        j = np.searchsorted(ts1, t, "right") - 1
        if j < 0:
            return None
        sd0 = sd_arr[j]; si = sess_idx.get(sd0)
        if si is None:
            return None
        px = float(r.price_1) if np.isfinite(r.price_1) else float(c1[max(0, j - 1)])
        gen, param = KIND2GEN[r.kind]
        frames = [by_sess[sess_list[si - k]] for k in range(K_SESS)
                  if si - k >= 0 and sess_list[si - k] in by_sess]
        if not frames:
            return None
        g = pd.concat(frames)
        g = g[(g.generator == gen) & (g.kts.to_numpy() <= t)]
        if param:
            g = g[g.param == param]
        want = DIRMAP.get(str(r.direction))
        if want:
            g = g[(g.dir_side == want) | (g.dir_side == "")]
        if not len(g):
            return None
        g = g.sort_values("kts").groupby(["tf", "dir_side"]).tail(1)
        lo = g.band_lo.to_numpy(); hi = g.band_hi.to_numpy()
        d = np.where((lo <= px) & (px <= hi), 0.0,
                     np.minimum(np.abs(px - lo), np.abs(px - hi)))
        return float(d.min())

    R["year"] = pd.to_datetime(R.ts_utc, utc=True).dt.year
    rows = []
    for _, r in R.iterrows():
        d = min_dist(r)
        if d is not None:
            rows.append((r.kind, r.year, d))
    D = pd.DataFrame(rows, columns=["kind", "year", "d"])
    print("\n## A. HIT RATE by kind x tolerance (all years pooled)")
    print("| kind | n | <=3 | <=2 | <=1.5 | <=1 |")
    print("|---|---|---|---|---|---|")
    for kind, g in D.groupby("kind"):
        cells = " | ".join(f"{(g.d <= tol).mean():.0%}" for tol in TOLS)
        print(f"| {kind} | {len(g)} | {cells} |")
    print("\n## A2. HIT RATE <=3 by kind x year (stability over time)")
    piv = D.assign(hit=D.d <= 3).pivot_table(index="kind", columns="year",
                                             values="hit", aggfunc="mean")
    cnt = D.pivot_table(index="kind", columns="year", values="d", aggfunc="size")
    with pd.option_context("display.float_format", "{:.0%}".format, "display.width", 200):
        print(piv.to_string())
    print("(counts)"); print(cnt.fillna(0).astype(int).to_string())
    return b, zr, ts1, c1, sd_arr, sess_list


def keyzone_reconstruction(repo, env):
    b, zr, ts1, c1, sd_arr, sess_list = env
    k = zr[(zr.kind == "key_kme_wrb") & (zr.instrument == "ES")].copy()
    k["t"] = pd.to_datetime(k.ts_utc, utc=True).dt.tz_convert(None)
    priced = k[k.price_1.notna()].sort_values("t")
    unpriced = k[k.price_1.isna() & k.relation.isin(
        ["back_to", "broken", "testing", "hugging", "reached", "inside",
         "approaching", "failed_held", "at_near", "above", "below"])].sort_values("t")
    print(f"\nB. KEY-ZONE RECONSTRUCTION: list events {len(priced)} | unpriced relational refs {len(unpriced)}")
    pts = priced.t.to_numpy()
    pps = priced.price_1.to_numpy(float)

    def on_list(t, px, E_days, tol=3.0):
        a = np.searchsorted(pts, t)
        if a == 0:
            return None
        sel = pps[:a]
        age = (t - pts[:a]) / np.timedelta64(1, "D")
        sel = sel[age <= E_days]
        if not len(sel):
            return None
        return bool(np.min(np.abs(sel - px)) <= tol)

    for E in (30, 90, 9999):
        hits = []
        for _, r in unpriced.iterrows():
            t = np.datetime64(r.t)
            j = np.searchsorted(ts1, t, "right") - 1
            if j < 1:
                continue
            x = on_list(t, float(c1[j - 1]), E)
            if x is not None:
                hits.append(x)
        nulls = []
        for perm in range(20):
            u = m = 0
            for _, r in unpriced.iterrows():
                t = np.datetime64(r.t)
                j = np.searchsorted(ts1, t, "right") - 1
                if j < 1:
                    continue
                sd0 = sd_arr[j]
                idx = np.flatnonzero(sd_arr == sd0)
                jj = int(idx[RNG.integers(30, len(idx))]) if len(idx) > 40 else j
                x = on_list(ts1[jj], float(c1[jj]), E)
                if x is not None:
                    u += x; m += 1
            nulls.append(u / max(1, m))
        nulls = np.array(nulls)
        hr = np.mean(hits)
        print(f"  expiry {E:>4}d: his unpriced refs on-list {hr:.0%} (n={len(hits)}) "
              f"| null {nulls.mean():.0%} +/- {nulls.std():.0%} | gap {hr-nulls.mean():+.0%}")


if __name__ == "__main__":
    repo = "." if len(sys.argv) < 2 else sys.argv[1]
    env = dashboard(repo)
    keyzone_reconstruction(repo, env)
