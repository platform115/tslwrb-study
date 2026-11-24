#!/usr/bin/env python3
"""
a2_3_labels_story.py — A2.3: his-labels + level-story families
(T-IM42/T-IM43). Spec: A2_3_SPEC.md (frozen). Appends columns to the
T-IM41 table rows. Harness: truncation recompute on the new columns.
RUN: python3 Tests/A2_measurement/a2_3_labels_story.py          (repo root)
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
for d in ("P6_imitation_study", "P4_entry_determination"):
    sys.path.insert(0, os.path.join(T, d))
from p6_22_s6_1_presence import Resolver                     # noqa: E402
from p6_23_s6_2_interaction import edges_at                  # noqa: E402
from p4_66_context_ablation import prep                      # noqa: E402

MONTHS = {"2025-10": "2025-11-01", "2022-02": "2022-03-01"}
FAMS = ("REA", "SQZ", "GAP", "SHD")
TICK = 0.25
RNG = np.random.default_rng(113)


def load_mentions(repo, month):
    """His references (ts, edge prices via links->objects, tier)."""
    zr = pd.read_parquet(os.path.join(repo, "Data/inputs/his_zone_refs.parquet"))
    zr = zr[~zr.is_boilerplate].reset_index()  # 'index' = original row id
    sl = pd.read_parquet(os.path.join(repo, "Data/inputs/s4_ref_links.parquet"))
    so = pd.read_parquet(os.path.join(repo, "Data/inputs/s4_objects.parquet"),
                         columns=["object_id", "band_lo", "band_hi",
                                  "knowable_ts"])
    sl = sl[pd.to_datetime(sl.ts).dt.strftime("%Y-%m") == month]
    m = sl.merge(so, on="object_id", how="left").merge(
        zr[["index", "tier"]], left_on="ref_idx", right_on="index",
        how="left")
    m["t_s"] = pd.to_datetime(m.ts).astype("datetime64[ns]").astype(
        "int64") // 10**9
    m["know_s"] = pd.to_datetime(m.knowable_ts).astype(
        "datetime64[ns]").astype("int64") // 10**9
    m = m.dropna(subset=["band_lo"]).sort_values("t_s")
    return (m.t_s.to_numpy(np.int64), m.know_s.to_numpy(np.int64),
            m.band_lo.to_numpy(float), m.band_hi.to_numpy(float),
            (m.tier == "key").to_numpy())


def mention_feats(M, t, px, day0):
    """Family A at moment t (refs strictly before t, same session day)."""
    mt, mk, lo, hi, key = M
    j = int(np.searchsorted(mt, t))          # refs with ts < t
    i0 = int(np.searchsorted(mt, day0))
    out = dict(mention_near_1pt=0, mention_near_3pt=0,
               mins_since_mention=np.nan, key_mention_near=False)
    best = None
    seen = set()
    for i in range(i0, j):
        if mk[i] > t:
            continue
        d = min(abs(px - lo[i]), abs(px - hi[i]))
        if d <= 3.0:
            kk = (round(lo[i], 2), round(hi[i], 2))
            if kk not in seen:
                seen.add(kk)
                out["mention_near_3pt"] += 1
                if d <= 1.0:
                    out["mention_near_1pt"] += 1
            if key[i] and d <= 3.0:
                out["key_mention_near"] = True
            if best is None or mt[i] > best:
                best = mt[i]
    if best is not None:
        out["mins_since_mention"] = (t - best) / 60.0
    return out


def story_feats(R, sd, t64, t, px, side, secs, mids, bo, bh2, bl, bc, bv,
                bts_close):
    """Family B: level story (nearest edge) + recent completed bars."""
    out = {}
    # nearest certified edge within 5 pts
    cand = []
    for fam in FAMS:
        for e in edges_at(R, sd, t64, fam):
            cand.append(e)
    edge = min(cand, key=lambda e: abs(px - e)) if cand else None
    if edge is not None and abs(px - edge) <= 5.0:
        out["edge_dist"] = abs(px - edge)
        j2 = int(np.searchsorted(secs, t, "right")) - 1
        j0 = int(np.searchsorted(secs, t - 12 * 3600))
        w, ws = mids[j0:j2 + 1], secs[j0:j2 + 1]
        near = np.abs(w - edge) <= 1.0
        tests, last = [], -10**12
        for i in np.flatnonzero(near):
            if ws[i] - last >= 300:
                tests.append(ws[i])
            last = ws[i]
        # exclude a touch happening right now from "prior tests"
        prior = [x for x in tests if t - x >= 60]
        out["n_tests_today"] = len(prior)
        out["mins_since_test"] = ((t - prior[-1]) / 60.0) if prior else np.nan
        if prior:
            a = int(np.searchsorted(secs, prior[-1]))
            b2 = int(np.searchsorted(secs, min(prior[-1] + 300, t), "right"))
            if b2 > a:
                out["last_bounce_ticks"] = float(
                    np.max(np.abs(mids[a:b2] - edge)) / TICK)
        j120 = int(np.searchsorted(secs, t - 120))
        seg = mids[j120:j2 + 1]
        if len(seg) > 10:
            out["dwell120"] = float((np.abs(seg - edge) <= 1.0).mean())
            out["approach120"] = float(
                (abs(seg[0] - edge) - abs(px - edge)) / TICK)
    # recent completed 1m bars (close time <= t)
    k = int(np.searchsorted(bts_close, t, "right")) - 1
    if k >= 4:
        o_, h_, l_, c_, v_ = (bo[k - 4:k + 1], bh2[k - 4:k + 1],
                              bl[k - 4:k + 1], bc[k - 4:k + 1],
                              bv[k - 4:k + 1])
        d = np.sign(c_ - o_)
        run = 1
        for i in range(len(d) - 2, -1, -1):
            if d[i] == d[-1] and d[-1] != 0:
                run += 1
            else:
                break
        out["consec_1m"] = float(run * d[-1] * side)
        rng_ = h_ - l_
        with np.errstate(invalid="ignore", divide="ignore"):
            out["body_share3"] = float(np.nanmean(
                np.abs(c_[-3:] - o_[-3:]) / np.where(rng_[-3:] > 0,
                                                     rng_[-3:], np.nan)))
            wick = (h_[-1] - max(o_[-1], c_[-1])) if side > 0 else \
                (min(o_[-1], c_[-1]) - l_[-1])
            out["wick_opp_last"] = float(wick / rng_[-1]) \
                if rng_[-1] > 0 else np.nan
        out["inside_last"] = float(h_[-1] <= h_[-2] and l_[-1] >= l_[-2])
        base = v_[-4:-1].mean()
        out["volt3"] = float(v_[-1] / base) if base > 0 else np.nan
    # 10-second step run from per-second mids
    j2 = int(np.searchsorted(secs, t, "right")) - 1
    steps = []
    for i in range(12):
        a = int(np.searchsorted(secs, t - (i + 1) * 10))
        b2 = int(np.searchsorted(secs, t - i * 10))
        if b2 - 1 >= a >= 0 and b2 - 1 <= j2:
            steps.append(np.sign(mids[min(b2 - 1, j2)] - mids[a]))
    if steps:
        run = 1
        for i in range(1, len(steps)):
            if steps[i] == steps[0] and steps[0] != 0:
                run += 1
            else:
                break
        out["consec_10s"] = float(run * steps[0] * side)
    return out


NEWCOLS = ["mention_near_1pt", "mention_near_3pt", "mins_since_mention",
           "key_mention_near", "edge_dist", "n_tests_today",
           "mins_since_test", "last_bounce_ticks", "dwell120",
           "approach120", "consec_1m", "consec_10s", "body_share3",
           "wick_opp_last", "inside_last", "volt3"]


def run(repo="."):
    F = pd.read_parquet(os.path.join(repo, "Data/inputs/a2_features.parquet"))
    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["sd"] = b.session_date.astype(str)
    allnew = {}
    for month, nxt in MONTHS.items():
        bm = b[(b.ts_event >= f"{month}-01") & (b.ts_event < nxt)
               ].reset_index(drop=True)
        zr_all = pd.read_parquet(os.path.join(repo,
                                 "Data/inputs/his_zone_refs.parquet"))
        R = Resolver(bm, zr_all)
        P = prep(repo, month)
        secs, mids = P["secs"], P["mids"]
        M = load_mentions(repo, month)
        bts_open = bm.ts_event.dt.tz_convert(None).astype(
            "int64").to_numpy() // 10**9
        bts_close = bts_open + 60
        bo, bh2 = bm.open.to_numpy(), bm.high.to_numpy()
        bl, bc, bv = (bm.low.to_numpy(), bm.close.to_numpy(),
                      bm.volume.to_numpy(float))
        sd_by_bar = bm.sd.to_numpy()

        def day_start(t):
            # first second of this session day in the per-second data
            j = int(np.searchsorted(bts_open, t, "right")) - 1
            sd0 = sd_by_bar[j] if j >= 0 else None
            k = int(np.searchsorted(bts_open, 0))
            first = bts_open[sd_by_bar == sd0]
            return (int(first[0]) if len(first) else t - 12 * 3600), sd0

        def feats(t, px, side):
            d0, sd0 = day_start(t)
            o = mention_feats(M, t, px, d0)
            t64 = np.datetime64(int(t), "s")
            o.update(story_feats(R, sd0, t64, t, px, side, secs, mids,
                                 bo, bh2, bl, bc, bv, bts_close))
            return o

        rows = F[(F.month == month) & F.data_fresh]
        # ---- harness: truncation recompute on new columns ----
        his = rows[rows.who == "his"]
        idx = RNG.choice(len(his), size=min(40, len(his)), replace=False)
        fails = 0
        for i in idx:
            r = his.iloc[i]
            t, side = int(r.sec), int(r.side)
            j2 = int(np.searchsorted(secs, t, "right"))
            kb = int(np.searchsorted(bts_close, t, "right"))
            jm = int(np.searchsorted(M[0], t))
            full = feats(t, float(mids[j2 - 1]), side)
            # truncated copies
            secs2, mids2 = secs[:j2], mids[:j2]
            M2 = tuple(x[:jm] for x in M)
            bo2, bh22, bl2, bc2, bv2 = (bo[:kb], bh2[:kb], bl[:kb],
                                        bc[:kb], bv[:kb])
            d0, sd0 = day_start(t)
            o2 = mention_feats(M2, t, float(mids2[-1]), d0)
            o2.update(story_feats(R, sd0, np.datetime64(int(t), "s"), t,
                                  float(mids2[-1]), side, secs2, mids2,
                                  bo2, bh22, bl2, bc2, bv2,
                                  bts_close[:kb]))
            for c in NEWCOLS:
                x, y = full.get(c, np.nan), o2.get(c, np.nan)
                xn = isinstance(x, float) and np.isnan(x)
                yn = isinstance(y, float) and np.isnan(y)
                if not (xn and yn) and x != y:
                    fails += 1
                    break
        print(f"{month} HARNESS new-columns recompute: {fails} mismatches "
              f"(need 0) -> {'PASS' if fails == 0 else 'FAIL'}")
        if fails:
            return
        for ridx, r in rows.iterrows():
            j2 = int(np.searchsorted(secs, int(r.sec), "right")) - 1
            allnew[ridx] = feats(int(r.sec), float(mids[j2]), int(r.side))
        print(f"{month}: {len(rows)} rows measured")
    N = pd.DataFrame.from_dict(allnew, orient="index")
    for c in NEWCOLS:
        F[c] = N[c] if c in N else np.nan
    out = os.path.join(repo, "Data/inputs/a2_features.parquet")
    F.to_parquet(out, index=False)
    h = F[(F.who == "his") & F.data_fresh]
    print(f"\nwrote {out} (+{len(NEWCOLS)} columns)")
    print(f"his trades at a spot he had already named today (within 3 pts): "
          f"{(h.mention_near_3pt > 0).mean():.0%}; within 1 pt: "
          f"{(h.mention_near_1pt > 0).mean():.0%}")
    n = F[(F.who == "null") & F.data_fresh]
    print(f"nulls at such a spot: 3pt {(n.mention_near_3pt > 0).mean():.0%}, "
          f"1pt {(n.mention_near_1pt > 0).mean():.0%}")


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
