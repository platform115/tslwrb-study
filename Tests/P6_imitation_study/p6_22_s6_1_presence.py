#!/usr/bin/env python3
"""
p6_22_s6_1_presence.py — S6.1: STRUCTURE PRESENCE AT HIS ENTRIES. (T-IM29.)
===============================================================================
For each of his first entries in 2025-10: the resolver state at the ENTRY
SECOND (anchor = per-second mid, 1-second mandate; structures from bars
completed by that second — harness-passed in S6.0; STAMP FIX 2026-11-28
(T-RH01): rea_zz and sqz comps moved from closing-bar OPEN to CLOSE,
removing a bounded <=59s early-visibility defect). Null: for each entry,
20 ambient seconds drawn from OTHER sessions of the month within +/-30 min
of the entry's time of day (session type matched).

Structures checked (kind -> adopted selection, tolerance):
  GAP   g1 hidden gaps, most-recent per (TF, dir), unfilled/partial, 1 pt
        (both any-direction and trade-direction-matched reported)
  SHD   g2 shadows D2, most-recent per (TF, side), range edge within 1 pt
  REA   reaction union (5m N=2 swing OR 0.08% zigzag), level within 3 pts;
        side-matched variant: long at a LOW level, short at a HIGH level
  SQZ   contraction band W=10 q=0.67 + tight W=30 q=0.67, edge within 3 pts
  KEY   stated-price Key-zone list (statements before entry), within 3 pts
  BRD   WRB body borders (p6_1 object): current-session or virgin older
        border on TFs 1/3/5, within 1 pt
Report: presence % at his entries vs null, overall + long/short split +
KME-window split. Counts shown; no thresholds fitted.

RUN: python3 Tests/P6_imitation_study/p6_22_s6_1_presence.py          (repo root)
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(T, "P4_entry_determination"))
from p6_12_g1_hidden_gap import resample_tf, whg_zones, fill_state   # noqa: E402
from p6_14_g2_shadow import shadow_intervals                          # noqa: E402
from p6_15_g3_reaction import swings                                  # noqa: E402
from p6_16_g4_contraction import episodes_c2                          # noqa: E402
from p6_1_entry_typology import border_catalog, nearest_border        # noqa: E402
from p4_66_context_ablation import prep                               # noqa: E402
from p4_2_entry_context import month_bounds                           # noqa: E402
from p4_3_confluence_news import news_sets                            # noqa: E402

MONTH = "2025-10"
TFS = (1, 2, 3, 5, 15)
RNG = np.random.default_rng(107)
COLS = ["ts_event", "open", "high", "low", "close", "is_roll_day", "session_date"]


class Resolver:
    def __init__(self, b, zr):
        self.groups = {s: g.reset_index(drop=True) for s, g in b.groupby("sd")}
        self.cache = {}
        k = zr[(zr.kind == "key_kme_wrb") & (zr.instrument == "ES") & zr.price_1.notna()]
        kt = pd.to_datetime(k.ts_utc, utc=True).dt.tz_convert(None).to_numpy()
        o = np.argsort(kt)
        self.key_ts, self.key_px = kt[o], k.price_1.to_numpy(float)[o]

    def _objs(self, sd, fam):
        key = (sd, fam)
        if key in self.cache:
            return self.cache[key]
        g = self.groups[sd]
        out = []
        if fam == "gap":
            for tf in TFS:
                rb = resample_tf(g[COLS], tf); rb["ts_event"] = rb.ts_event.dt.tz_convert(None)
                out += [dict(z, tf=tf) for z in whg_zones(rb, tf)]
        elif fam == "shd":
            for tf in TFS:
                rb = resample_tf(g[COLS], tf); rb["ts_event"] = rb.ts_event.dt.tz_convert(None)
                out += shadow_intervals(rb, tf, "D2", 0)
        elif fam == "rea_sw":
            rb = resample_tf(g[COLS], 5); rb["ts_event"] = rb.ts_event.dt.tz_convert(None)
            out = swings(rb, 5, 2)
        elif fam == "rea_zz":
            gts = g.ts_event.dt.tz_convert(None).to_numpy()
            hh, ll = g.high.to_numpy(), g.low.to_numpy()
            mode = 0; ext = hh[0]; ext_l = ll[0]
            for i in range(1, len(hh)):
                rev = hh[i] * 0.08 / 100
                if mode >= 0:
                    if hh[i] > ext: ext = hh[i]
                    if ext - ll[i] >= rev:
                        out.append(dict(side="high", px=ext, comp=gts[i] + np.timedelta64(60, "s"))); mode = -1; ext_l = ll[i]
                if mode <= 0:
                    if ll[i] < ext_l: ext_l = ll[i]
                    if hh[i] - ext_l >= rev:
                        out.append(dict(side="low", px=ext_l, comp=gts[i] + np.timedelta64(60, "s"))); mode = 1; ext = hh[i]
        elif fam.startswith("sqz"):
            W = 10 if fam == "sqz10" else 30
            eps, hh, ll = episodes_c2(g, W, 0.67)
            gts = g.ts_event.dt.tz_convert(None).to_numpy()
            for (a, e) in eps:
                if e + 1 >= len(gts): continue
                a0 = max(0, a - W + 1)
                out.append(dict(lo=float(ll[a0:e+1].min()), hi=float(hh[a0:e+1].max()),
                                comp=gts[e + 1] + np.timedelta64(60, "s")))
        self.cache[key] = out
        return out

    def presence(self, sd, t, px, side, cx=None, bcat=None, sd_str=None):
        """Returns dict of flags for one (second, price, trade-side)."""
        f = {}
        # GAP: most-recent per (tf,dir) non-filled, edge/band within 1 pt
        g1 = [z for z in self._objs(sd, "gap") if z["comp"] <= t]
        best = {}
        for z in g1:
            k = (z["tf"], z["dir"])
            if k not in best or z["comp"] > best[k]["comp"]:
                best[k] = z
        hit_any = hit_dir = False
        want = "up" if side > 0 else "down"
        for (tf, d), z in best.items():
            near = (z["lo"] - 1 <= px <= z["hi"] + 1)
            if near:
                hit_any = True
                if d == want:
                    hit_dir = True
        f["GAP any-dir"] = hit_any; f["GAP dir-match"] = hit_dir
        # SHD: most-recent per (tf,side), range edge within 1 pt
        g2 = [z for z in self._objs(sd, "shd") if z["comp"] <= t]
        best = {}
        for z in g2:
            k = (z["tf"], z["dir"])
            if k not in best or z["comp"] > best[k]["comp"]:
                best[k] = z
        f["SHD edge"] = any(min(abs(px - z["lo"]), abs(px - z["hi"])) <= 1
                            for z in best.values())
        # REA union: nearest level within 3; side-matched: long near LOW level
        lows, highs = [], []
        for fam in ("rea_sw", "rea_zz"):
            best = {}
            for z in self._objs(sd, fam):
                if z["comp"] <= t and (z["side"], ) and True:
                    k = z["side"]
                    if k not in best or z["comp"] > best[k]["comp"]:
                        best[k] = z
            if "low" in best: lows.append(best["low"]["px"])
            if "high" in best: highs.append(best["high"]["px"])
        near_low = any(abs(px - p) <= 3 for p in lows)
        near_high = any(abs(px - p) <= 3 for p in highs)
        f["REA any"] = near_low or near_high
        f["REA side-match"] = near_low if side > 0 else near_high
        # SQZ: most recent episode band edge within 3
        hit = False
        for fam in ("sqz10", "sqz30"):
            eps = [z for z in self._objs(sd, fam) if z["comp"] <= t]
            if eps:
                z = max(eps, key=lambda q: q["comp"])
                if min(abs(px - z["lo"]), abs(px - z["hi"])) <= 3:
                    hit = True
        f["SQZ edge"] = hit
        # KEY: stated zone within 3 (statements before t)
        cut = np.searchsorted(self.key_ts, t)
        f["KEY stated"] = bool(cut and np.min(np.abs(self.key_px[:cut] - px)) <= 3) if cut else False
        # BRD: p6_1 border (1/3/5m current-session or virgin), within 1 pt (4 ticks)
        if cx is not None:
            d, _ = nearest_border(bcat, cx, int(t.astype("datetime64[ns]").astype(np.int64)),
                                  px, sd_str, 3)
            f["BRD border"] = (d * 0.25) <= 1.0
        return f


def run(repo="."):
    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["sd"] = b.session_date.astype(str)
    bm = b[(b.ts_event >= f"{MONTH}-01") & (b.ts_event < "2025-11-01")].reset_index(drop=True)
    zr = pd.read_parquet(os.path.join(repo, "Data/inputs/his_zone_refs.parquet"))
    R = Resolver(bm, zr)
    P = prep(repo, MONTH)
    cx = P["cx"]; secs, mids = P["secs"], P["mids"]
    bcat = border_catalog(cx.bars)
    ev = np.asarray(news_sets(repo)["all"], dtype=np.int64)
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")
                         ).dropna(subset=["first_entry_utc"])
    lo, hi = month_bounds(MONTH)
    em = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
    print(f"his {MONTH} first entries: {len(em)}", flush=True)
    sdm = {s: g for s, g in bm.groupby("sd")}
    sds = list(sdm)
    sd1 = bm.sd.to_numpy(); bt1 = bm.ts_event.dt.tz_convert(None).to_numpy()

    def sec_sd(t):
        j = np.searchsorted(bt1, t, "right") - 1
        return sd1[j] if j >= 0 else None

    rows = []
    for _, r in em.iterrows():
        t = np.datetime64(pd.Timestamp(r.first_entry_utc).tz_convert(None))
        side = 1 if r.side == "long" else -1
        j = np.searchsorted(secs, t.astype("datetime64[s]").astype(np.int64), "right") - 1
        if j < 10:
            continue
        px = float(mids[j])                       # per-second anchor (mandate)
        sd0 = sec_sd(t)
        if sd0 is None:
            continue
        s0ns = int(t.astype("datetime64[ns]").astype(np.int64))
        kk = np.searchsorted(ev, s0ns, "right") - 1
        kme = bool(kk >= 0 and (s0ns - ev[kk]) <= 45 * 60 * 10**9)
        f = R.presence(sd0, t, px, side, cx=cx, bcat=bcat, sd_str=str(P["sd"][
            int(np.clip(np.searchsorted(cx.bts, s0ns, "right") - 1, 0, len(cx.c) - 1))]))
        f.update(dict(who="HIM", side=side, kme=kme, tod=pd.Timestamp(t).time()))
        rows.append(f)
        # 20 matched nulls: other sessions, +/-30 min of same time of day
        for _ in range(20):
            s2 = sds[RNG.integers(len(sds))]
            g2 = sdm[s2]
            base = pd.Timestamp(str(g2.sd.iloc[0])) + pd.Timedelta(
                hours=pd.Timestamp(t).hour, minutes=pd.Timestamp(t).minute)
            t2 = np.datetime64(base + pd.Timedelta(minutes=int(RNG.integers(-30, 31))))
            j2 = np.searchsorted(secs, t2.astype("datetime64[s]").astype(np.int64), "right") - 1
            if j2 < 10 or sec_sd(t2) != s2:
                continue
            px2 = float(mids[j2])
            f2 = R.presence(s2, t2, px2, side, cx=cx, bcat=bcat, sd_str=str(P["sd"][
                int(np.clip(np.searchsorted(cx.bts, int(t2.astype("datetime64[ns]").astype(np.int64)), "right") - 1, 0, len(cx.c) - 1))]))
            f2.update(dict(who="NULL", side=side, kme=False, tod=None))
            rows.append(f2)
        print(".", end="", flush=True)
    D = pd.DataFrame(rows)
    him = D[D.who == "HIM"]; nul = D[D.who == "NULL"]
    feats = [c for c in D.columns if c not in ("who", "side", "kme", "tod")]
    print(f"\n\n===== S6.1 PRESENCE: {len(him)} entries vs {len(nul)} matched nulls =====")
    print("| structure | his | null | gap |")
    print("|---|---|---|---|")
    for c in feats:
        print(f"| {c} | {him[c].mean():.0%} | {nul[c].mean():.0%} | {him[c].mean()-nul[c].mean():+.0%} |")
    print("\n## split: long vs short (his entries)")
    for c in feats:
        L = him[him.side > 0]; S = him[him.side < 0]
        print(f"  {c}: long {L[c].mean():.0%} (n={len(L)}) | short {S[c].mean():.0%} (n={len(S)})")
    print("\n## split: KME window vs not (his entries)")
    for c in feats:
        K = him[him.kme]; N = him[~him.kme]
        print(f"  {c}: KME-window {K[c].mean():.0%} (n={len(K)}) | outside {N[c].mean():.0%} (n={len(N)})")
    D.to_parquet(os.path.join(repo, "Data/inputs/s6_presence.parquet"))


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
