#!/usr/bin/env python3
"""
s1_round.py — T-SR01: Strategy S-1 backtest. Spec: S1_SPEC.md
(committed first). Container-only (all inputs banked).
RUN: python3 Tests/D25_surgical/s1_round.py > Tests/D25_surgical/S1_REPORT.md
"""
import numpy as np
import pandas as pd

MONTHS = ("2022-02", "2025-10")
GRID = 0.25

# touches with 3s features + outcomes + his tags
F = pd.read_parquet("Data/inputs/db3_features.parquet")
MB = pd.read_csv("Tests/D6_deepbook/mb_outcomes.csv")
E1 = pd.read_csv("Tests/D6_deepbook/e1_outcomes.csv")
E1["cid"] = np.arange(len(E1))
B = F[F.q == "mb"].merge(MB[["cid", "outcome"]], on="cid")
B = B.merge(E1[["cid", "level", "his", "his_side"]], on="cid")
assert len(B) == 693, f"touch universe mismatch: {len(B)}"
B["churn3"] = B.depl_opp_3 + B.repl_opp_3
T2 = B.churn3.quantile(2 / 3)
B["active"] = (B.churn3 >= T2) | (B.sweep_3 > 0)

MIDS, OFI = {}, {}
for mo in MONTHS:
    f = pd.read_parquet(f"Data/inputs/flow_per_sec_{mo}_full.parquet")
    MIDS[mo] = (f.sec.to_numpy(np.int64), f.mid.to_numpy(float))
    o = pd.read_parquet(f"Data/inputs/ofi10_per_sec_{mo}.parquet")
    OFI[mo] = (o.sec.to_numpy(np.int64),
               np.concatenate([[0.0], np.cumsum(
                   (o.ofi_b - o.ofi_a).to_numpy(float))]))

def ofi30(mo, t, sdn):
    osec, ocum = OFI[mo]
    i = int(np.searchsorted(osec, t - 30))
    j = int(np.searchsorted(osec, t, "right"))
    if j <= i:
        return None
    return float(ocum[j] - ocum[i]) * sdn

# levels-ahead needs the detector (for the capture exit)
import sys
sys.path.insert(0, "Tests/P4_entry_determination")
from p4_3_confluence_news import news_sets                   # noqa: E402
ev_all = np.asarray(news_sets(".")["all"], dtype=np.int64) // 10**9
b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b.sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
days_all = sorted(b[~b.is_roll_day].sd.unique())
day_ix = {d: i for i, d in enumerate(days_all)}
closes = b[~b.is_roll_day].groupby("sd").close.last(
    ).reindex(days_all).to_numpy()
rows = []
so = pd.read_parquet("Data/inputs/s4_objects.parquet",
                     columns=["generator", "band_lo", "band_hi",
                              "session_date", "knowable_ts"])
so = so[so.generator.isin(["g2_shadow_d2", "g1_whg", "g3_swing"])]
so["sd"] = so.session_date.astype(str)
ks = so.knowable_ts.astype("datetime64[ns]").astype("int64") // 10**9
kk2 = np.searchsorted(ev_all, ks.to_numpy(), "right") - 1
so["newsborn"] = (ks.to_numpy() - ev_all[np.maximum(kk2, 0)]) <= 2700
for col in ("band_lo", "band_hi"):
    rows.append(so[["sd", col, "newsborn"]].dropna()
                .rename(columns={col: "px"}))
bb = b[~b.is_roll_day]
for tfm in ("5min", "15min"):
    for sd, g in bb.groupby("sd"):
        r = g.set_index("ts_event").resample(tfm).agg(
            {"open": "first", "close": "last"}).dropna()
        body = (r.close - r.open).abs().to_numpy()
        pm = pd.Series(body).shift(1).rolling(3).max().to_numpy()
        w_ = body > pm
        for o, c in zip(r.open.to_numpy()[w_], r.close.to_numpy()[w_]):
            rows.append(pd.DataFrame({"sd": [sd, sd],
                                      "px": [max(o, c), min(o, c)],
                                      "newsborn": [False, False]}))
EV = pd.concat(rows, ignore_index=True)
EV["px"] = (EV.px * 4).round() / 4
EV = EV.drop_duplicates(["sd", "px"])
EV["di"] = EV.sd.map(day_ix); EV = EV.dropna(subset=["di"])
EV["di"] = EV.di.astype(int)
Vpx, Vdi, Vnb = EV.px.to_numpy(), EV.di.to_numpy(), EV.newsborn.to_numpy()

def density_levels(px, di, nb, tol, m):
    if not len(px):
        return []
    gp = np.round(px / GRID).astype(np.int64)
    lo, hi = gp.min(), gp.max()
    width = int(round(tol / GRID))
    order = np.argsort(gp)
    gs, ds, nbs = gp[order], di[order], nb[order]
    uniq = np.arange(lo, hi + 1); score = np.zeros(len(uniq))
    for k, g0 in enumerate(uniq):
        a = np.searchsorted(gs, g0 - width)
        b2 = np.searchsorted(gs, g0 + width, "right")
        if b2 > a:
            score[k] = len(set(ds[a:b2])) + (1.0 if nbs[a:b2].any()
                                             else 0.0)
    out, taken = [], np.zeros(len(uniq), bool)
    for k in np.argsort(-score):
        if score[k] < m or taken[k]:
            continue
        out.append(float(uniq[k] * GRID))
        taken[max(0, k - 2 * width):k + 2 * width + 1] = True
    return out

lv_cache = {}
def lf(di):
    if di not in lv_cache:
        msk = (Vdi >= di - 60) & (Vdi < di)
        out = []
        for p in density_levels(Vpx[msk], Vdi[msk], Vnb[msk], 2.0, 4):
            sel = np.abs(Vpx[msk] - p) <= 2.0
            last_mem = int(Vdi[msk][sel].max())
            cseg = closes[last_mem + 1:di]
            if not (len(cseg) and (np.abs(cseg - p) > 5.0).all()):
                out.append(p)
        lv_cache[di] = out
    return lv_cache[di]

sd_of = {}
bnr = b[~b.is_roll_day]
bt_all = bnr.ts_event.dt.tz_convert(None).astype("int64"
                                                ).to_numpy() // 10**9
sd_all = bnr.sd.to_numpy()

def sim(sub, label):
    out = []
    for mo in MONTHS:
        secs, mids = MIDS[mo]
        tt = sub[sub.month == mo].sort_values("t")
        busy = -10**12
        for r in tt.itertuples():
            t0 = int(r.t) + 3
            if t0 < busy:
                continue
            d = int(r.side)             # break direction = approach dir
            L = float(r.level)
            ent = L + 0.75 * d
            j0 = int(np.searchsorted(secs, t0))
            j1 = int(np.searchsorted(secs, t0 + 120, "right"))
            seg = mids[j0:j1]
            hit = np.flatnonzero((seg >= ent) if d > 0
                                 else (seg <= ent))
            if not len(hit):
                continue
            jf = j0 + int(hit[0])
            tf = int(secs[jf])
            if tf < busy:
                continue
            stop_px = L - 1.25 * d
            kb = int(np.searchsorted(bt_all, tf, "right")) - 1
            di = day_ix.get(sd_all[kb]) if kb >= 0 else None
            lv = lf(di) if di is not None else []
            ahead = sorted([(p - ent) * d for p in lv
                            if (p - ent) * d > 0.5])
            tgt = ahead[0] if ahead else None
            j4 = int(np.searchsorted(secs, tf + 900, "right"))
            exc = (mids[jf:j4] - ent) * d
            ts_ = (secs[jf:j4] - tf).astype(int)
            stop_exc = (stop_px - ent) * d        # = -2.0
            peak = 0.0
            pnl = exc[-1] if len(exc) else 0.0
            ix = len(exc) - 1
            reason = "cap"
            next_chk = 60
            for i in range(len(exc)):
                if exc[i] > peak:
                    peak = exc[i]
                if exc[i] <= stop_exc:
                    pnl, ix, reason = stop_exc, i, "stop"
                    break
                if tgt is not None and peak >= tgt - 1.0 \
                        and exc[i] <= peak - 0.75:
                    pnl, ix, reason = peak - 0.75, i, "capture"
                    break
                if ts_[i] >= next_chk:
                    v = ofi30(mo, tf + int(ts_[i]), d)
                    if v is not None and v < 0:
                        pnl, ix, reason = exc[i], i, "flowfade"
                        break
                    next_chk += 30
            busy = int(secs[jf + ix])
            out.append(dict(month=mo, tf=tf, d=d, pnl=float(pnl),
                            exit=reason, his=int(r.his)))
    return pd.DataFrame(out)

print("# S1 REPORT — STRATEGY S-1, SURGICAL LEVEL-BREAK (T-SR01)")
print("STATUS: CLOSED | 2026-11-27 | Spec: S1_SPEC.md (frozen first) "
      "| touch universe reconciled (693) | Tier-R | covered touches "
      "only (news-window skew stated)")
print()
print("## HIS-ALIGNMENT (J's question: what does HE pick?)")
for g, sub in B.groupby("active"):
    nm = "ACTIVE touches" if g else "QUIET/middle touches"
    print(f"- {nm}: he traded {int(sub.his.sum())}/{len(sub)} "
          f"({sub.his.mean():.0%})")
print()
print("| cell | trades | win | per-trade | pooled | by month | "
      "worst | exits (stop/fade/capture/cap) | his-overlap | "
      "verdict |")
print("|---|---|---|---|---|---|---|---|---|---|")
res = {}
for label, sub in (("S1-ACTIVE", B[B.active]), ("S1-ANY", B)):
    tr = sim(sub, label)
    res[label] = tr
    nets = {mo: tr[tr.month == mo].pnl.sum() for mo in MONTHS}
    pooled = tr.pnl.sum()
    pt = pooled / max(1, len(tr))
    w = (tr.pnl > 0).mean() if len(tr) else 0
    ex = tr.exit.value_counts()
    exs = (f"{ex.get('stop', 0)}/{ex.get('flowfade', 0)}/"
           f"{ex.get('capture', 0)}/{ex.get('cap', 0)}")
    bym = "/".join(f"{nets[mo]:+.0f}" for mo in MONTHS)
    res[label + "_stats"] = (pooled, pt, nets)
    print(f"| {label} | {len(tr)} | {w:.0%} | {pt:+.2f} | "
          f"{pooled:+.1f} | {bym} | {tr.pnl.min():+.2f} | {exs} | "
          f"{int(tr.his.sum())} | - |")
pa, ta, na = res["S1-ACTIVE_stats"]
pn, tn, nn = res["S1-ANY_stats"]
both = all(v > 0 for v in na.values())
ok = (pa > 0 and both and ta >= 0.60 and ta > tn)
print()
print("## VERDICT vs THE FROZEN LINES")
print(f"- pooled > 0: {'PASS' if pa > 0 else 'FAIL'} ({pa:+.1f})")
print(f"- both months > 0: {'PASS' if both else 'FAIL'}")
print(f"- per-trade >= +0.60: "
      f"{'PASS' if ta >= 0.60 else 'FAIL'} ({ta:+.2f})")
print(f"- ACTIVE beats ANY on per-trade (signal contributes): "
      f"{'PASS' if ta > tn else 'FAIL'} ({ta:+.2f} vs {tn:+.2f})")
print(f"OVERALL: "
      f"{'REGISTER S-1 TRAINING-ONLY' if ok else 'BACK TO THE BENCH'}")
print()
print("Registry: T-SR01.")
