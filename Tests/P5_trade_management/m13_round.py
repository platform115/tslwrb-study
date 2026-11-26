#!/usr/bin/env python3
"""
m13_round.py — T-MG22: M13 clock extension (hold past 480s while the
book supports). Spec: M13_SPEC.md (committed first). Derived from
m12_round.py; only the exit function and verdicts change.
RUN: python3 Tests/P5_trade_management/m13_round.py > Tests/P5_trade_management/M13_REPORT.md
"""
import sys
import numpy as np
import pandas as pd

for d in ("Tests/P6_imitation_study", "Tests/P4_entry_determination"):
    sys.path.insert(0, d)
from p6_22_s6_1_presence import Resolver                     # noqa: E402
from p6_23_s6_2_interaction import edges_at                  # noqa: E402
from p4_66_context_ablation import prep                      # noqa: E402
from p4_3_confluence_news import news_sets                   # noqa: E402

MONTHS = {"2025-10": "2025-11-01", "2022-02": "2022-03-01"}
DISP, TTL, DEDUP, STOP, GRID = 1.25, 300, 300, 3.75, 0.25
CELLS = {"CONTROL": None, "M13 th0.00": 0.00, "M13 th-0.02": -0.02}
EXPECT = dict(n=607, pooled=276.1, caught=47, extras=185.6)

b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b.sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
days_all = sorted(b[~b.is_roll_day].sd.unique())
day_ix = {d: i for i, d in enumerate(days_all)}
closes = b[~b.is_roll_day].groupby("sd").close.last(
    ).reindex(days_all).to_numpy()
ev_all = np.asarray(news_sets(".")["all"], dtype=np.int64) // 10**9
zr = pd.read_parquet("Data/inputs/his_zone_refs.parquet")

BOOK = {}
for mo in MONTHS:
    bk = pd.read_parquet(f"Data/inputs/book_per_sec_{mo}.parquet")
    BOOK[mo] = (bk.sec.to_numpy(), bk.bid10.to_numpy().astype(float),
                bk.ask10.to_numpy().astype(float))

def imb10_at(mo, t, sdn):
    bsec, b10, a10 = BOOK[mo]
    k = int(np.searchsorted(bsec, t, "right")) - 1
    if k < 0 or t - bsec[k] > 5:
        return None
    sup = b10[k] if sdn > 0 else a10[k]
    opp = a10[k] if sdn > 0 else b10[k]
    return (sup - opp) / max(sup + opp, 1.0)

def band_arrays(g, W, q):
    h = g.high.to_numpy(); l = g.low.to_numpy(); n = len(h)
    hs = pd.Series(h).rolling(W).max().to_numpy()
    ls = pd.Series(l).rolling(W).min().to_numpy()
    rng_w = hs - ls
    med = pd.Series(rng_w).shift(1).rolling(60, min_periods=10
                                            ).median().to_numpy()
    active = np.isfinite(rng_w) & np.isfinite(med) & (rng_w <= q * med)
    blo = np.full(n, np.nan); bhi = np.full(n, np.nan)
    run_lo = run_hi = np.nan; in_run = False
    cur_lo = cur_hi = np.nan
    for i in range(n):
        if active[i]:
            s0 = max(0, i - W + 1)
            if not in_run:
                run_lo, run_hi = l[s0:i + 1].min(), h[s0:i + 1].max()
                in_run = True
            else:
                run_lo = min(run_lo, l[i]); run_hi = max(run_hi, h[i])
            cur_lo, cur_hi = run_lo, run_hi
        else:
            in_run = False
        blo[i], bhi[i] = cur_lo, cur_hi
    return blo, bhi

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

def m13(exc, ts, best, mo, tf, sdn, theta, acct):
    """theta None -> pure M7. Clock extension at 480s per M13_SPEC.
    Returns (pnl, ix, extended)."""
    peak, tp, armed = 0.0, 0, False
    extended = False
    next_check = 480
    arm = max(best - 0.75, 0.5) if (best is not None and best <= 8.0) \
        else None
    for i in range(len(exc)):
        if exc[i] > peak:
            peak, tp = exc[i], ts[i]
        if arm is not None and exc[i] >= arm:
            armed = True
        if exc[i] <= -STOP:
            return -STOP, i, extended
        if armed and exc[i] <= peak - 0.75:
            return peak - 0.75, i, extended
        if ts[i] - tp >= 60:
            return exc[i], i, extended
        if ts[i] >= 900:
            acct["hardcap"] += 1
            return exc[i], i, extended
        if ts[i] >= next_check:
            if theta is None:
                return exc[i], i, extended
            imb = imb10_at(mo, tf + int(ts[i]), sdn)
            if imb is None:
                if not extended:
                    acct["nobook"] += 1
                return exc[i], i, extended
            if imb < theta:
                acct["recheck_exit" if extended
                     else "exit480"] += 1
                return exc[i], i, extended
            if not extended:
                acct["extended"] += 1
                extended = True
            next_check += 60
    return ((exc[-1], len(exc) - 1, extended) if len(exc)
            else (0.0, 0, extended))

F = pd.read_parquet("Data/inputs/a2_features.parquet")
F = F[(F.who == "his") & F.data_fresh].copy()
mm = F.kme_mins_since
F["np_"] = np.where(np.isfinite(mm) & (mm <= 5), "burst",
                    np.where(np.isfinite(mm) & (mm <= 45), "window",
                             "none"))
def ctx_row(r):
    for f in ("SQZ", "REA", "GAP", "SHD"):
        if r[f"{f}_interact"]:
            return {"SQZ": "squeeze", "REA": "reaction"}.get(f, "other")
    return "other"
F["ctx"] = F.apply(ctx_row, axis=1)
HIS62 = F[(F.ctx == "squeeze") & (F.np_ == "window")][["month", "sec",
                                                      "side"]]

# lane-1 candidates (identical generation to cd_round/tl_round)
cands = []
month_arrays = {}
for mo, nxt in MONTHS.items():
    bm = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)
           ].reset_index(drop=True)
    R = Resolver(bm, zr)
    P = prep(".", mo)
    secs, mids = P["secs"], P["mids"]
    month_arrays[mo] = (secs, mids)
    bt = bm.ts_event.dt.tz_convert(None).astype("int64"
                                                ).to_numpy() // 10**9
    rth = bm.session.eq("RTH").to_numpy()
    sd1 = bm.sd.to_numpy()
    evm = ev_all[(ev_all >= secs[0]) & (ev_all <= secs[-1])]
    band_cache = {}
    for es in evm:
        j0 = int(np.searchsorted(secs, es + 300))
        j1 = int(np.searchsorted(secs, es + 2700, "right"))
        if j1 - j0 < 60:
            continue
        kb = int(np.searchsorted(bt, secs[j0], "right")) - 1
        if kb < 0 or not rth[kb]:
            continue
        sd0 = sd1[kb]
        if sd0 not in band_cache:
            g = bm[bm.sd == sd0].reset_index(drop=True)
            band_cache[sd0] = (band_arrays(g, 20, 0.8),
                               (g.ts_event.dt.tz_convert(None)
                                .astype("int64").to_numpy() // 10**9))
        (blo, bhi), g_bt = band_cache[sd0]
        last_fire = {}
        for jj in range(max(j0, 1), j1):
            t = int(secs[jj])
            t64 = np.datetime64(t, "s")
            E = list(edges_at(R, sd0, t64, "SQZ"))
            ki = int(np.searchsorted(g_bt + 60, t, "right")) - 1
            if ki >= 0 and np.isfinite(blo[ki]):
                E += [blo[ki], bhi[ki]]
            px, prev = mids[jj], mids[jj - 1]
            for e in E:
                ddir = 1 if (prev <= e < px) else \
                    (-1 if (prev >= e > px) else 0)
                if ddir == 0:
                    continue
                key = (round(e, 2), ddir)
                if t - last_fire.get(key, -10**9) <= DEDUP:
                    continue
                last_fire[key] = t
                lvl = e + DISP * ddir
                j3 = int(np.searchsorted(secs, t + TTL, "right"))
                seg2 = mids[jj:j3]
                hit = np.flatnonzero((seg2 >= lvl) if ddir > 0
                                     else (seg2 <= lvl))
                if len(hit):
                    jf = jj + int(hit[0])
                    cands.append((mo, sd0, int(secs[jf]), ddir, key,
                                  jf))

cell_tr = {}
cell_acct = {}
for cname, theta in CELLS.items():
    out = []
    acct = dict(exit480=0, extended=0, recheck_exit=0, hardcap=0,
                nobook=0)
    for mo in MONTHS:
        secs, mids = month_arrays[mo]
        cl = sorted([x for x in cands if x[0] == mo],
                    key=lambda x: x[2])
        seen = set()
        busy = -10**12
        for (mo_, sd0, tf, ddir, key, jf) in cl:
            dk = (tf, key)
            if dk in seen:
                continue
            seen.add(dk)
            if tf < busy:
                continue
            lvl = key[0] + DISP * ddir
            j4 = int(np.searchsorted(secs, tf + 1800, "right"))
            exc = (mids[jf:j4] - lvl) * ddir
            ts_ = (secs[jf:j4] - tf).astype(int)
            di = day_ix.get(sd0)
            lv = lf(di) if di is not None else []
            ahead = sorted([(p - lvl) * ddir for p in lv
                            if (p - lvl) * ddir > 0.25])
            pnl, ix, was_ext = m13(exc, ts_,
                                   ahead[0] if ahead else None,
                                   mo, tf, ddir, theta, acct)
            busy = int(secs[jf + ix])
            out.append((mo, tf, ddir, pnl, key, int(was_ext)))
    cell_tr[cname] = pd.DataFrame(
        out, columns=["month", "tf", "d", "pnl", "key", "ext"])
    cell_acct[cname] = acct

def score(tr):
    nets = tr.groupby("month").pnl.sum()
    caught = 0
    for _, h in HIS62.iterrows():
        if len(tr[(tr.month == h.month) & (tr.d == h.side)
                  & (abs(tr.tf - h.sec) <= 300)]):
            caught += 1
    near = np.zeros(len(tr), bool)
    for _, h in HIS62.iterrows():
        near |= ((tr.month == h.month).to_numpy()
                 & (np.abs(tr.tf - h.sec) <= 300).to_numpy())
    exn = float(tr.pnl[~near].sum())
    return nets, caught, exn, float(tr.pnl.sum())

fails = []
cn, cc, ce, cp = score(cell_tr["CONTROL"])
if not (len(cell_tr["CONTROL"]) == EXPECT["n"]
        and abs(cp - EXPECT["pooled"]) < 0.1
        and cc == EXPECT["caught"] and abs(ce - EXPECT["extras"]) < 0.1):
    fails.append(f"CONTROL mismatch: n={len(cell_tr['CONTROL'])} "
                 f"pooled={cp:+.1f} caught={cc} extras={ce:+.1f}")
ctrl_entries = set(map(tuple, cell_tr["CONTROL"][["month", "tf",
                                                  "key"]].itertuples(
                                                      index=False)))
shifted = {}
for cname in list(CELLS)[1:]:
    s_ = set(map(tuple, cell_tr[cname][["month", "tf", "key"]
                                       ].itertuples(index=False)))
    shifted[cname] = (len(s_ - ctrl_entries), len(ctrl_entries - s_))
if fails:
    print("# M13 RUN ABORTED — MANDATORY CHECKS FAILED")
    for f_ in fails:
        print("-", f_)
    sys.exit(1)

print("# M13 REPORT — CLOCK EXTENSION: HOLD PAST 480s WHILE THE "
      "BOOK SUPPORTS (T-MG22)")
print("STATUS: CLOSED | 2026-11-26 | Spec: M13_SPEC.md (committed "
      "first) | engine: fill-time | CONTROL reproduced exactly | "
      "verdict: MECHANISM-PRIMARY (T-MG21 lesson)")
print()
print("| cell | trades | net (22-02/25-10) | caught/62 | extras net "
      "| worst | stall exits / extended / forced / no-book | "
      "busy-shifted entries (+/-) | verdict |")
print("|---|---|---|---|---|---|---|---|---|")
for cname, theta in CELLS.items():
    tr = cell_tr[cname]
    nets, caught, exn, pooled = score(tr)
    both = (len(nets) == 2 and all(x > 0 for x in nets.to_numpy()))
    worst = tr.pnl.min()
    a = cell_acct[cname]
    if cname == "CONTROL":
        v = "(incumbent reproduced)"
        sh = "-"
    else:
        v = ("secondary PASS" if (pooled > 276.1 and both
                                  and worst >= -STOP - 1e-9)
             else "secondary fail")
        sh = f"+{shifted[cname][0]}/-{shifted[cname][1]}"
    extnet = tr.pnl[tr.ext == 1].sum() if "ext" in tr else 0.0
    extn = int(tr.ext.sum()) if "ext" in tr else 0
    print(f"| {cname} | {len(tr)} | {pooled:+.1f} "
          f"({nets.get('2022-02', 0):+.1f}/"
          f"{nets.get('2025-10', 0):+.1f}) | {caught} | {exn:+.1f} | "
          f"{worst:+.2f} | {a['exit480']}/{a['extended']}/"
          f"{a['recheck_exit']}/{a['hardcap']}/{a['nobook']} | "
          f"{sh} | {v} |")
    if cname != "CONTROL":
        print(f"|  ^ extended-trade detail: {extn} trades, net "
              f"{extnet:+.1f} ({extnet / max(extn, 1):+.2f}/trade) "
              f"| | | | | | | | |")
print()
print("## PRIMARY VERDICT — EXTENDED TRADES vs THEIR M7 TWINS")
ctl = cell_tr["CONTROL"].set_index(["month", "tf", "key"]).pnl
for cname in list(CELLS)[1:]:
    tr = cell_tr[cname]
    ext = tr[tr.ext == 1]
    j = ext.set_index(["month", "tf", "key"]).pnl
    common = j.index.intersection(ctl.index)
    de = (j.loc[common] - ctl.loc[common])
    mo_ok = all(de[de.index.get_level_values("month") == mo].sum() > 0
                for mo in MONTHS)
    prim = "PASS" if (de.sum() > 0 and mo_ok) else "FAIL"
    per_mo = {mo: round(float(de[de.index.get_level_values(
        "month") == mo].sum()), 1) for mo in MONTHS}
    print(f"- {cname}: {len(common)} of {len(ext)} extended trades "
          f"have an identical-entry M7 twin; twin delta "
          f"{de.sum():+.1f} total ({de.mean():+.2f}/trade; "
          f"{(de > 0).mean():.0%} improved; worst {de.min():+.2f}; "
          f"per month {per_mo}) -> PRIMARY {prim}")
print()
print("Registry: T-MG22.")
