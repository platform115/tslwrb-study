#!/usr/bin/env python3
"""
Part 1 diagnostic — loss-cutting / failed-setup recognition (wrbtrader, ES, Oct 2025).

DESIGN (settled in chat; supersedes Stage 0's "within-window random null" as primary):
  Question tested: what order-flow signature separates "cut this loser" from
  "hold through comparable pain and it works out"?
    CASES    = the Oct-2025 loss-cuts (realized_pnl < 0).  Decision instant = his EXIT.
    CONTROLS = winners (realized_pnl > 0) MATCHED ON ADVERSE EXCURSION (MAE).
               Decision instant = the winner's MAE instant (its max-pain hold point).
    FLOOR    = random pre-exit timestamps within the same losers (dead-on-arrival check).

  WHY matched-on-MAE: unmatched, winners' median MAE (~1.0pt) vs losers' (~3.0pt) means an
  unmatched test just relearns "losers go further underwater" — a price fact needing no flow.

  KNOWN STRUCTURAL ASYMMETRY (documented, not hidden): a CUT is a timestamped action;
  a HOLD is not. The loser's exit is on the bounce AFTER its MAE; the control instant is AT
  the trough. So this contrasts "flow at his cut" vs "flow at a held trough of similar depth."
  A null here is INFORMATIVE (he could not read it pre-outcome), not a failure.
  Set CASE_INSTANT='mae' to instead align BOTH at the trough (the alternative framing).

  LOOKAHEAD: every feature uses ONLY records strictly before the decision instant.

  This script computes; it does not decide. All thresholds are config, recorded in output.
  Operational feature formulas are marked [PROJECT CONVENTION] — the *concepts*
  (delta, absorption, tape intensity, book depletion) are standard order-flow; the exact
  scalars are our choices and must be reported as such.

USAGE:
  1) python p1_cut_vs_hold_diagnostic.py inspect   # schema + scaling + DELTA-SIGN gate. Run FIRST.
  2) python p1_cut_vs_hold_diagnostic.py run        # full diagnostic -> two CSVs + printed table

Paste back: the printed summary table, the delta-sign gate line, and the matched-MAE overlap line.
"""

from __future__ import annotations
import sys, os, json, hashlib
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.compute as pc

# ======================================================================================
# CONFIG  (edit paths / column names here; everything that affects a result is recorded)
# ======================================================================================
WINDOWED_MBP10 = "/Volumes/2TB-Lexar/tslwrb_windowed/mbp10_ESZ5_2025-10_windowed.parquet"
EPISODES       = "/Users/joshhall/Developer/Projects/es-trading-agent-v3/Data/processed/chatlogs/tsl_episodes_clean.parquet"
ES_1M_FRONT    = "/Users/joshhall/Developer/Projects/es-trading-agent-v3/Data/processed/es/es_1m_front.parquet"
WRB_1M         = "/Users/joshhall/Developer/Projects/es-trading-agent-v3/Data/processed/wrb_1m.parquet"  # optional, not yet wired
MONTH_PREFIX   = "2025-10"
CONTRACT_ID    = None      # set to the resolved ESZ5 instrument_id (int) to hard-filter; None = trust pre-reduced file

# MBP-10 column names (Databento .to_df() layout assumed; adjust to YOUR writer's names)
TS_COL     = "ts_event"
ACTION_COL = "action"; TRADE_ACTION = "T"
SIDE_COL   = "side"                              # expect 'B'/'A'/'N' (aggressor). Sign INFERRED below.
PRICE_COL  = "price"; SIZE_COL = "size"
IID_COL    = "instrument_id"
TOP_N      = 5     # book depth to load (>= OFI_LEVELS; QI uses level 0 only)
BID_PX = [f"bid_px_{i:02d}" for i in range(TOP_N)]
ASK_PX = [f"ask_px_{i:02d}" for i in range(TOP_N)]
BID_SZ = [f"bid_sz_{i:02d}" for i in range(TOP_N)]
ASK_SZ = [f"ask_sz_{i:02d}" for i in range(TOP_N)]

# Validated book-feature params
OFI_LEVELS    = 5     # MLOFI depth: best-level OFI (lvl 0) is primary; sum over [0, OFI_LEVELS) is the multi-level variant
LARGE_LOT_MIN = 10    # [PROJECT CONVENTION] contracts; a single ES trade >= this counts as a "large lot"

# Path-asymmetry params (your velocity observation)
PATH_SOURCE   = "trade"   # 'trade' = trade-price path | 'mid' = book mid path
VEL_MIN_STEPS = 3         # need at least this many price changes in a window or velocity feats = NaN

# Good-cut / bad-cut labelling (within-loser, forward outcome from es_1m_front)
FWD_HORIZON_S = 120       # forward window after his exit; "bad cut" = price recovered to his entry within this

# Adverse-dynamics lenses (your "deep/fast against him" hypothesis)
RUN_WINDOW_S  = 5         # "recent" sub-window for speed/depth right before the instant
N_SLICES      = 3         # split the feature window into this many slices to measure acceleration (S_last - S_first)
GRID_S        = 5         # time-to-exit lens: sample each loser's hold every GRID_S seconds
MIN_GRID_PTS  = 4         # need this many grid points in a loser to compute its time-to-exit correlation
TICK          = 0.25      # ES tick, for depth-in-ticks

# Exploration (Oct discovery only -- NOT the frozen Feb params): window/slice sensitivity on the lead
EXPLORE_W_GRID = [15, 30, 45, 60]
EXPLORE_SLICES = [2, 3]

# Cut-type clustering + held-through-stall (block G/H). Window is a knob -- not married to 30.
CLUSTER_W       = 30
CLUSTER_SLICES  = 3
CLUSTER_FEATURES = ["accel_adverse_speed", "favorable_velocity", "accel_cum_delta", "accel_ofi", "adverse_depth_ticks"]

# Whole-hold STATE (block I): the confluence over the entire entry->exit window, not a pre-exit slice.
EARLY_S = 45      # "early window" = first EARLY_S seconds after entry (predictive / non-tautological view)
STATE_FEATURES = ["spread_mean_ticks", "spread_frac_wide", "adverse_qi_frac", "favorable_progress_rate",
                  "time_to_first_fav_frac", "time_underwater_frac", "adverse_slope_permin", "adverse_persistence"]
STATE_TAUTOLOGICAL = {"time_underwater_frac", "adverse_slope_permin", "adverse_persistence", "favorable_progress_rate"}

# Failed-rally / give-back (block J): favorable-side EVENT (Sweeney 1996 MFE + bounce-then-fail). Tilt, not trigger.
FR_W_GRID = [30, 60, 90]   # pre-exit window (s) for the failed-bounce measure; a rally needs room to form and fail

# Bounce-behavior tilt (block K): the decision (cut vs hold) on the one surviving axis, as a threshold FILTER with coverage.
KW_GRID = [30, 45, 60]     # window (s) for favorable_velocity; swept, not married to one value

# Decision-instant alignment
CASE_INSTANT    = "exit"   # 'exit' (his cut) | 'mae' (trough, for the alternative both-at-trough framing)
CONTROL_INSTANT = "mae"    # winners have no cut; 'mae' is the held trough

# Feature / null windows (seconds). Sized per-trade off hold length so short trades don't self-contaminate.
W_MIN, W_MAX   = 10.0, 30.0
def feat_window(hold_s): return float(np.clip(hold_s / 3.0, W_MIN, W_MAX))
LAG_GUARD_S    = 0.0       # recorded exit may trail the decision; shift instant earlier by this many s if needed

# Control matching on MAE (points)
MAE_BAND       = (2.0, 6.0)   # controls must have MAE in this band; report overlap vs cases
PREFILTER_PAD  = 0.75         # loosen 1m pre-filter before precise MBP-10 MAE

# Random-null floor
N_NULL         = 100
def null_guard(hold_s): return max(15.0, hold_s * 0.25)

# Stats
N_PERM         = 10000
SEED           = 20251007
DELTA_CORR_MIN = 0.30      # |corr(signed_vol, price_change)| must exceed this or delta features are flagged unreliable

OUT_FEATURES   = "p1_features_per_episode.csv"
OUT_SUMMARY    = "p1_summary.csv"
RNG = np.random.default_rng(SEED)

# ======================================================================================
# IO helpers (RAM-safe: push ts filters down, read only needed columns)
# ======================================================================================
def _dataset():
    return ds.dataset(WINDOWED_MBP10, format="parquet")

def _detect_scaling(dset):
    """Return (price_div, ts_is_int) by sampling one batch."""
    sample = dset.head(2000).to_pandas()
    if PRICE_COL not in sample.columns:
        return 1.0, None
    pmed = pd.to_numeric(sample[PRICE_COL], errors="coerce").abs().median()
    price_div = 1e9 if (pmed is not None and pmed > 1e6) else 1.0
    ts_is_int = pd.api.types.is_integer_dtype(sample[TS_COL])
    return price_div, ts_is_int

def _ts_bound(t, ts_is_int):
    t = pd.Timestamp(t)
    if t.tzinfo is None: t = t.tz_localize("UTC")
    if ts_is_int: return int(t.value)
    return pa.scalar(t.value, type=pa.timestamp("ns", tz="UTC"))  # full ns, no pydatetime truncation

def read_window(dset, start, end, cols, price_div, ts_is_int):
    f = (pc.field(TS_COL) >= _ts_bound(start, ts_is_int)) & (pc.field(TS_COL) < _ts_bound(end, ts_is_int))
    if CONTRACT_ID is not None:
        f = f & (pc.field(IID_COL) == CONTRACT_ID)
    present = [c for c in cols if c in dset.schema.names]
    df = dset.to_table(columns=present, filter=f).to_pandas()
    if df.empty: return df
    if ts_is_int:
        df[TS_COL] = pd.to_datetime(df[TS_COL], utc=True)
    elif df[TS_COL].dt.tz is None:
        df[TS_COL] = df[TS_COL].dt.tz_localize("UTC")
    if PRICE_COL in df.columns: df[PRICE_COL] = df[PRICE_COL] / price_div
    for c in BID_PX + ASK_PX:
        if c in df.columns: df[c] = df[c] / price_div
    # DBN sizes are UNSIGNED -> cast to signed int64 so negation (delta) / subtraction (book-pull) don't wrap
    for c in [SIZE_COL] + BID_SZ + ASK_SZ:
        if c in df.columns: df[c] = df[c].astype("int64")
    return df.sort_values(TS_COL)

def trades_only(df):
    return df[df[ACTION_COL] == TRADE_ACTION] if ACTION_COL in df.columns else df

# ======================================================================================
# Schema gate + delta-sign gate
# ======================================================================================
REQUIRED = [TS_COL, ACTION_COL, SIDE_COL, PRICE_COL, SIZE_COL]

def schema_gate(dset):
    missing = [c for c in REQUIRED if c not in dset.schema.names]
    if missing:
        print("SCHEMA GATE FAILED. Missing columns:", missing)
        print("Available:", list(dset.schema.names))
        print("-> Edit the *_COL / level-name constants at the top to match your windowed parquet.")
        sys.exit(1)
    book_missing = [c for c in (BID_SZ+ASK_SZ+BID_PX+ASK_PX) if c not in dset.schema.names]
    if book_missing:
        print("WARNING: book columns absent ->", book_missing[:4], "...")
        print("         absorption / book-pull features will be NaN. Delta + tape still run.")
    return not book_missing

def infer_delta_sign(dset, price_div, ts_is_int):
    """Empirically resolve the aggressor convention (the contract-offset-trap analogue).
    Returns (sign_mult, corr). signed_vol = sign_mult * (size if side=='B' else -size)."""
    # read a generous slab of trades from the first available day
    sample = dset.head(500000).to_pandas()
    if ts_is_int: sample[TS_COL] = pd.to_datetime(sample[TS_COL], utc=True)
    sample = trades_only(sample)
    if sample.empty: return 1.0, np.nan
    sample[PRICE_COL] = sample[PRICE_COL] / price_div
    sz = sample[SIZE_COL].astype("int64")            # avoid unsigned wraparound on negation
    s = sample[SIDE_COL].astype(str).str.upper().str[0]
    raw_signed = np.where(s == "B", sz, np.where(s == "A", -sz, 0.0))
    g = pd.DataFrame({"ts": sample[TS_COL].dt.floor("1min"),
                      "sv": raw_signed, "px": sample[PRICE_COL]})
    per = g.groupby("ts").agg(sv=("sv","sum"), o=("px","first"), c=("px","last"))
    per["dpx"] = per["c"] - per["o"]
    per = per[per["dpx"].abs() > 0]
    corr = float(np.corrcoef(per["sv"], per["dpx"])[0,1]) if len(per) > 5 else np.nan
    sign_mult = 1.0 if (np.isnan(corr) or corr >= 0) else -1.0
    return sign_mult, corr

# ======================================================================================
# Episode selection + MAE (from MBP-10 trades; es_1m_front only pre-filters winners)
# ======================================================================================
def load_episodes():
    ep = pd.read_parquet(EPISODES)
    ep = ep[(ep.trading_date.str.startswith(MONTH_PREFIX)) & (ep.n_entries==1) & (ep.n_exits==1)].copy()
    ep["entry"] = ep.entry_prices.apply(lambda x: float(x[0]))
    ep["hold_s"] = (ep.last_exit_utc - ep.first_entry_utc).dt.total_seconds()
    return ep

def mae_from_trades(dset, row, price_div, ts_is_int):
    tr = trades_only(read_window(dset, row.first_entry_utc, row.last_exit_utc,
                                 [TS_COL, ACTION_COL, PRICE_COL, SIZE_COL], price_div, ts_is_int))
    if tr.empty: return np.nan, pd.NaT
    if row.side == "long":
        i = tr[PRICE_COL].idxmin(); mae = row.entry - tr.loc[i, PRICE_COL]
    else:
        i = tr[PRICE_COL].idxmax(); mae = tr.loc[i, PRICE_COL] - row.entry
    return float(mae), tr.loc[i, TS_COL]

def winner_mae_prefilter(ep):
    """Cheap 1m MAE to shortlist winner controls before precise MBP-10 MAE."""
    b = pd.read_parquet(ES_1M_FRONT).sort_values("ts_event")
    out = []
    for _, r in ep[ep.realized_pnl > 0].iterrows():
        w = b[(b.ts_event >= r.first_entry_utc.floor("min")) & (b.ts_event <= r.last_exit_utc)]
        if w.empty: continue
        m = (r.entry - w.low.min()) if r.side == "long" else (w.high.max() - r.entry)
        if m >= MAE_BAND[0] - PREFILTER_PAD:
            out.append(r.episode_id)
    return set(out)

# ======================================================================================
# Features (all over [instant - w - LAG_GUARD_S, instant - LAG_GUARD_S); strictly pre-instant)
# ======================================================================================
@dataclass
class Feat:
    cum_delta_adverse: float    # signed TRADE vol against his position (+ = pressure on him). Trades only.
    ofi_best_adverse: float     # Cont-Kukanov-Stoikov 2014 best-level OFI, oriented against him (+ = pressure on him)
    ofi_multi_adverse: float    # MLOFI: sum of per-level OFI over [0,OFI_LEVELS), oriented against him
    queue_imb_adverse: float    # Gould-Bonart 2016 touch queue imbalance, mean over window, oriented against him
    max_trade_size: float       # largest single trade (contracts) in window  [trade-size]
    large_lot_adverse_vol: float# [PROJECT CONVENTION] volume from aggressor-against-him trades >= LARGE_LOT_MIN
    tape_intensity_ratio: float # [PROJECT CONVENTION] sum size [t-w,t) / sum size [t-2w,t-w)  (>1 intensifying)
    price_adverse_pts: float    # [PROJECT CONVENTION] adverse price extent within window vs window-start
    favorable_velocity: float   # [PROJECT CONVENTION] favorable-leg speed (pts/sec); LOW = weak/unconvincing bounce
    velocity_asym: float        # [PROJECT CONVENTION] adverse_vel/(adverse_vel+fav_vel); >0.5 = moves AGAINST him are faster
    semivar_ratio: float        # Barndorff-Nielsen-Kinnebrock-Shephard 2010 downside/total realized semivariance, oriented adverse
    reversal_rate: float        # [PROJECT CONVENTION] fraction of price-change steps that flip sign (choppiness / "up and down")
    adverse_speed_recent: float # [PROJECT CONVENTION] adverse price extent over last RUN_WINDOW_S / RUN_WINDOW_S (pts/sec) -- "fast against him"
    adverse_depth_ticks: float  # [PROJECT CONVENTION] adverse book-mid push over last RUN_WINDOW_S, in ticks -- "deep against him"
    adverse_new_extremes: float # [PROJECT CONVENTION] count of new adverse price extremes in last RUN_WINDOW_S (level-clearing / sweeps)
    accel_cum_delta: float      # [PROJECT CONVENTION] cum_delta_adverse(last slice) - (first slice): is against-him flow ramping in
    accel_ofi: float            # [PROJECT CONVENTION] ofi_best_adverse(last slice) - (first slice)
    accel_adverse_speed: float  # [PROJECT CONVENTION] adverse extent(last slice) - (first slice): is the move accelerating

def _signed_vol(df, sign_mult):
    s = df[SIDE_COL].astype(str).str.upper().str[0]
    sz = df[SIZE_COL].astype("int64")
    return float(sign_mult * np.where(s=="B", sz, np.where(s=="A", -sz, 0.0)).sum())

def _ofi_level(df, lvl):
    """Cont-Kukanov-Stoikov (2014) OFI at one book level over the rows of df (book updates).
    e_n = 1{Pb>=Pb_}qb - 1{Pb<=Pb_}qb_  -  (1{Pa<=Pa_}qa - 1{Pa>=Pa_}qa_).  Returns sum(e_n)."""
    bpx, ask = f"bid_px_{lvl:02d}", f"ask_px_{lvl:02d}"
    bsz, asz = f"bid_sz_{lvl:02d}", f"ask_sz_{lvl:02d}"
    if any(c not in df.columns for c in (bpx, ask, bsz, asz)) or len(df) < 2:
        return np.nan
    Pb, Qb = df[bpx].to_numpy(float), df[bsz].to_numpy("int64")
    Pa, Qa = df[ask].to_numpy(float), df[asz].to_numpy("int64")
    Pb0, Pb1, Qb0, Qb1 = Pb[:-1], Pb[1:], Qb[:-1], Qb[1:]
    Pa0, Pa1, Qa0, Qa1 = Pa[:-1], Pa[1:], Qa[:-1], Qa[1:]
    e_bid = np.where(Pb1 >= Pb0, Qb1, 0) - np.where(Pb1 <= Pb0, Qb0, 0)
    e_ask = np.where(Pa1 <= Pa0, Qa1, 0) - np.where(Pa1 >= Pa0, Qa0, 0)
    return float((e_bid - e_ask).sum())

def _secs(ts_series):
    return ts_series.to_numpy(dtype="datetime64[ns]").astype("int64") / 1e9

def _path_asymmetry(prices, times, pos):
    """Velocity/variance asymmetry of a price path, oriented to his position.
    adverse step = price moves against him (pos*r<0). Returns
    (favorable_velocity, velocity_asym, semivar_ratio, reversal_rate)."""
    p = np.asarray(prices, float); t = np.asarray(times, float)
    if len(p) < VEL_MIN_STEPS + 1: return (np.nan, np.nan, np.nan, np.nan)
    r, dt = np.diff(p), np.diff(t)
    ok = dt > 0; r, dt = r[ok], dt[ok]
    if len(r) < VEL_MIN_STEPS: return (np.nan, np.nan, np.nan, np.nan)
    adv, fav = (pos * r < 0), (pos * r > 0)
    def vel(m):
        tt = dt[m].sum()
        return (np.abs(r[m]).sum() / tt) if tt > 0 else np.nan
    av, fv = vel(adv), vel(fav)
    velocity_asym = (av / (av + fv)) if (np.isfinite(av) and np.isfinite(fv) and (av + fv) > 0) else np.nan
    rs_a, rs_f = float((r[adv] ** 2).sum()), float((r[fav] ** 2).sum())
    semivar_ratio = (rs_a / (rs_a + rs_f)) if (rs_a + rs_f) > 0 else np.nan
    s = np.sign(r); s = s[s != 0]
    reversal_rate = float((np.diff(s) != 0).mean()) if len(s) >= 2 else np.nan
    return (fv, velocity_asym, semivar_ratio, reversal_rate)

def label_good_cut(es1m, side, entry, exit_ts, H):
    """good cut = price did NOT recover to his entry within H after exit (bailing was right).
    bad cut  = price recovered to entry (holding would have got him back). Forward price from es_1m_front
    (full RTH series, never truncated). Returns (good:1/0/None, n_fwd_bars)."""
    w = es1m[(es1m.ts_event > exit_ts) & (es1m.ts_event <= exit_ts + pd.Timedelta(seconds=H))]
    if w.empty: return (np.nan, 0)
    recovered = (w.high.max() >= entry) if side == "long" else (w.low.min() <= entry)
    return (0 if recovered else 1, len(w))

def _cum_delta_adv(trdf, pos, sign_mult):
    return (-pos * _signed_vol(trdf, sign_mult)) if len(trdf) else np.nan

def _ofi_adv(df, pos):
    o = _ofi_level(df, 0)
    return (-pos * o) if not np.isnan(o) else np.nan

def _adv_extent(trdf, pos):
    """Adverse price extent (pts) within a trade slice: how far it moved against him from the slice's first print."""
    if len(trdf) < 2: return np.nan
    p = trdf[PRICE_COL].to_numpy(float); p0 = p[0]
    return float(max(0.0, (p0 - p.min()) if pos > 0 else (p.max() - p0)))

def _accel_fav_at(full, instant, side, w, n_slices, sign_mult):
    """Lightweight: (accel_adverse_speed, favorable_velocity) at one instant for a given window/slices.
    Used by the sensitivity sweep; trades-only, no book needed."""
    pos = 1.0 if side == "long" else -1.0
    t = pd.Timestamp(instant); t0 = t - pd.Timedelta(seconds=w)
    cur = full[(full[TS_COL] >= t0) & (full[TS_COL] < t)]
    if len(cur) < 2: return (np.nan, np.nan)
    edges = [t0 + pd.Timedelta(seconds=w * k / n_slices) for k in range(n_slices + 1)]
    s1 = trades_only(cur[(cur[TS_COL] >= edges[0])  & (cur[TS_COL] < edges[1])])
    s3 = trades_only(cur[(cur[TS_COL] >= edges[-2]) & (cur[TS_COL] < edges[-1])])
    av1, av3 = _adv_extent(s1, pos), _adv_extent(s3, pos)
    accel = (av3 - av1) if (np.isfinite(av1) and np.isfinite(av3)) else np.nan
    tr = trades_only(cur)
    fv = _path_asymmetry(tr[PRICE_COL].to_numpy(float), _secs(tr[TS_COL]), pos)[0] if len(tr) >= VEL_MIN_STEPS + 1 else np.nan
    return (accel, fv)

def _cluster_feats_at(full, instant, side, w, n_slices, sign_mult, has_book):
    """Fixed-window candidate-mechanism vector at one instant (accel + favorable stall + depth)."""
    pos = 1.0 if side == "long" else -1.0
    t = pd.Timestamp(instant); t0 = t - pd.Timedelta(seconds=w)
    cur = full[(full[TS_COL] >= t0) & (full[TS_COL] < t)]
    out = dict.fromkeys(CLUSTER_FEATURES, np.nan)
    if len(cur) < 2: return out
    edges = [t0 + pd.Timedelta(seconds=w * k / n_slices) for k in range(n_slices + 1)]
    s1 = cur[(cur[TS_COL] >= edges[0])  & (cur[TS_COL] < edges[1])]
    s3 = cur[(cur[TS_COL] >= edges[-2]) & (cur[TS_COL] < edges[-1])]
    av1, av3 = _adv_extent(trades_only(s1), pos), _adv_extent(trades_only(s3), pos)
    if np.isfinite(av1) and np.isfinite(av3): out["accel_adverse_speed"] = av3 - av1
    cd1, cd3 = _cum_delta_adv(trades_only(s1), pos, sign_mult), _cum_delta_adv(trades_only(s3), pos, sign_mult)
    if np.isfinite(cd1) and np.isfinite(cd3): out["accel_cum_delta"] = cd3 - cd1
    of1, of3 = _ofi_adv(s1, pos), _ofi_adv(s3, pos)
    if np.isfinite(of1) and np.isfinite(of3): out["accel_ofi"] = of3 - of1
    tr = trades_only(cur)
    if len(tr) >= VEL_MIN_STEPS + 1:
        out["favorable_velocity"] = _path_asymmetry(tr[PRICE_COL].to_numpy(float), _secs(tr[TS_COL]), pos)[0]
    if has_book and {"bid_px_00", "ask_px_00"} <= set(cur.columns):
        mid = ((cur["bid_px_00"] + cur["ask_px_00"]) / 2).to_numpy(float)
        push = (mid[0] - mid.min()) if pos > 0 else (mid.max() - mid[0])
        out["adverse_depth_ticks"] = float(max(0.0, push) / TICK)
    return out

def _kmeans2(X, iters=100):
    """Deterministic 2-means: farthest-point init, no RNG. Returns (labels, centroids)."""
    c0 = X[np.argmax(((X - X.mean(0)) ** 2).sum(1))]
    c1 = X[np.argmax(((X - c0) ** 2).sum(1))]
    C = np.vstack([c0, c1])
    for _ in range(iters):
        lab = (((X[:, None, :] - C[None, :, :]) ** 2).sum(2)).argmin(1)
        newC = np.vstack([X[lab == k].mean(0) if (lab == k).any() else C[k] for k in range(2)])
        if np.allclose(newC, C): break
        C = newC
    return lab, C

def _hold_state(win, entry_px, side):
    """Whole-hold (or early-window) state: spread/cost, book hostility, favorable-progress failure, slope/persistence.
    Oriented to position; 'adverse' = bad for the trade."""
    pos = 1.0 if side == "long" else -1.0
    out = dict.fromkeys(STATE_FEATURES, np.nan)
    if len(win) < 5: return out
    ts = _secs(win[TS_COL]); dur = ts[-1] - ts[0]
    if dur <= 0: return out
    has_b = {"bid_px_00", "ask_px_00", "bid_sz_00", "ask_sz_00"} <= set(win.columns)
    if has_b:
        bid = win["bid_px_00"].to_numpy(float); ask = win["ask_px_00"].to_numpy(float)
        mid = (bid + ask) / 2.0; spread = ask - bid
        out["spread_mean_ticks"] = float(np.nanmean(spread) / TICK)
        out["spread_frac_wide"]  = float(np.nanmean(spread > 1.5 * TICK))
        bs = win["bid_sz_00"].to_numpy(float); az = win["ask_sz_00"].to_numpy(float)
        den = bs + az; qi = np.where(den > 0, (bs - az) / np.where(den == 0, 1, den), np.nan)
        out["adverse_qi_frac"] = float(np.nanmean((-pos * qi) > 0))   # book leaning against his exit side
    else:
        mid = win[PRICE_COL].to_numpy(float)
    sgn = pos * (mid - entry_px)                 # >0 = favorable
    out["time_underwater_frac"] = float(np.mean(sgn < 0))
    favmax = max(0.0, float(np.max(sgn)))
    out["favorable_progress_rate"] = favmax / (dur / 60.0)            # max favorable reach per minute (low = slow to go his way)
    fav = np.where(sgn > 0)[0]
    out["time_to_first_fav_frac"] = float((ts[fav[0]] - ts[0]) / dur) if len(fav) else 1.0
    if len(mid) >= 3:
        b = np.polyfit(ts - ts[0], mid, 1)[0]
        out["adverse_slope_permin"] = float(-pos * b * 60.0)          # >0 = drifting against him
    adv = (sgn < 0).astype(int); best = cur = 0
    for v in adv:
        cur = cur + 1 if v else 0; best = max(best, cur)
    out["adverse_persistence"] = float(best / len(adv))
    return out

def _failed_rally(win, entry_px, side, w_exit, exit_ts):
    """Favorable-side EVENT features: whole-hold MFE (Sweeney 1996) + pre-exit bounce-then-fail give-back."""
    pos = 1.0 if side == "long" else -1.0
    out = dict(mfe_hold_pts=np.nan, rally_size_w=np.nan, giveback_w=np.nan)
    if len(win) < 5: return out
    has_b = {"bid_px_00", "ask_px_00"} <= set(win.columns)
    mid = ((win["bid_px_00"] + win["ask_px_00"]) / 2.0).to_numpy(float) if has_b else win[PRICE_COL].to_numpy(float)
    g = pos * (mid - entry_px)
    out["mfe_hold_pts"] = float(max(0.0, np.max(g)))                       # how far it ever went his way (Sweeney MFE)
    sub = win[win[TS_COL] >= pd.Timestamp(exit_ts) - pd.Timedelta(seconds=w_exit)]
    if len(sub) >= 3:
        m2 = ((sub["bid_px_00"] + sub["ask_px_00"]) / 2.0).to_numpy(float) if has_b else sub[PRICE_COL].to_numpy(float)
        gg = pos * m2; runmin = np.minimum.accumulate(gg)
        out["rally_size_w"] = float(np.max(gg - runmin))                   # largest favorable up-swing within window (a bounce formed)
        out["giveback_w"]   = float(np.max(gg) - gg[-1])                   # surrendered from in-window high to exit (it failed)
    return out

def _spearman(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b); a, b = a[m], b[m]
    if len(a) < 4: return np.nan
    ra = pd.Series(a).rank().to_numpy(); rb = pd.Series(b).rank().to_numpy()
    if ra.std() == 0 or rb.std() == 0: return np.nan
    return float(np.corrcoef(ra, rb)[0, 1])

def _youden(scores, labels):
    """Best in-sample threshold for 'hold if score>t'. labels: 1=hold (high score), 0=cut. Returns (J, thr, sens, spec)."""
    s = np.asarray(scores, float); y = np.asarray(labels, int)
    m = np.isfinite(s); s, y = s[m], y[m]
    best = (-1.0, np.nan, np.nan, np.nan)
    for t in np.unique(s):
        ph = s > t
        tp = int(np.sum(ph & (y == 1))); fn = int(np.sum(~ph & (y == 1)))
        tn = int(np.sum(~ph & (y == 0))); fp = int(np.sum(ph & (y == 0)))
        sens = tp / (tp + fn) if (tp + fn) else np.nan      # holds correctly kept
        spec = tn / (tn + fp) if (tn + fp) else np.nan      # cuts correctly cut
        if np.isfinite(sens) and np.isfinite(spec):
            j = sens + spec - 1
            if j > best[0]: best = (j, float(t), sens, spec)
    return best

def compute_features(dset, instant, side, hold_s, price_div, ts_is_int, sign_mult, has_book, pre_df=None):
    w = feat_window(hold_s)
    t  = pd.Timestamp(instant) - pd.Timedelta(seconds=LAG_GUARD_S)
    t0, t00 = t - pd.Timedelta(seconds=w), t - pd.Timedelta(seconds=2*w)
    pos = 1.0 if side == "long" else -1.0
    cols = [TS_COL, ACTION_COL, SIDE_COL, PRICE_COL, SIZE_COL] + (BID_PX+ASK_PX+BID_SZ+ASK_SZ if has_book else [])
    if pre_df is None:
        df = read_window(dset, t00, t, cols, price_div, ts_is_int)
    else:
        df = pre_df[(pre_df[TS_COL] >= t00) & (pre_df[TS_COL] < t)]
    if df.empty: return Feat(*([np.nan]*18)), w
    cur = df[df[TS_COL] >= t0]; prev = df[(df[TS_COL] >= t00) & (df[TS_COL] < t0)]
    tr_cur, tr_prev = trades_only(cur), trades_only(prev)

    # --- trade-flow ---
    signed = _signed_vol(tr_cur, sign_mult) if not tr_cur.empty else 0.0
    cum_delta_adverse = -pos * signed

    if not tr_cur.empty:
        p0 = tr_cur[PRICE_COL].iloc[0]
        adverse = (p0 - tr_cur[PRICE_COL].min()) if side=="long" else (tr_cur[PRICE_COL].max() - p0)
        price_adverse_pts = float(max(0.0, adverse))
    else:
        price_adverse_pts = np.nan

    sz_cur  = float(tr_cur[SIZE_COL].sum()) if not tr_cur.empty else 0.0
    sz_prev = float(tr_prev[SIZE_COL].sum()) if not tr_prev.empty else 0.0
    tape_intensity_ratio = (sz_cur / sz_prev) if sz_prev > 0 else np.nan

    max_trade_size = float(tr_cur[SIZE_COL].max()) if not tr_cur.empty else np.nan
    adverse_side = "A" if side == "long" else "B"   # aggressor side that pushes against him
    if not tr_cur.empty:
        s = tr_cur[SIDE_COL].astype(str).str.upper().str[0]
        big = tr_cur[(s == adverse_side) & (tr_cur[SIZE_COL] >= LARGE_LOT_MIN)]
        large_lot_adverse_vol = float(big[SIZE_COL].sum())
    else:
        large_lot_adverse_vol = np.nan

    # --- book features (use ALL events in cur, not just trades) ---
    ofi_best_adverse = ofi_multi_adverse = queue_imb_adverse = np.nan
    if has_book and len(cur) >= 2:
        ofi0 = _ofi_level(cur, 0)
        ofi_best_adverse = (-pos * ofi0) if not np.isnan(ofi0) else np.nan
        per = [_ofi_level(cur, m) for m in range(OFI_LEVELS)]
        per = [x for x in per if not np.isnan(x)]
        ofi_multi_adverse = (-pos * float(np.sum(per))) if per else np.nan
        b0, a0 = cur[f"bid_sz_00"].to_numpy("int64"), cur[f"ask_sz_00"].to_numpy("int64")
        denom = (b0 + a0)
        qi = np.where(denom > 0, (b0 - a0) / np.where(denom == 0, 1, denom), np.nan)
        if np.isfinite(qi).any():
            queue_imb_adverse = float(-pos * np.nanmean(qi))

    # --- path asymmetry (your velocity observation) ---
    if PATH_SOURCE == "trade":
        pp, tt = (tr_cur[PRICE_COL].to_numpy(float), _secs(tr_cur[TS_COL])) if not tr_cur.empty else (np.array([]), np.array([]))
    else:  # 'mid' = book mid path
        if has_book and {"bid_px_00", "ask_px_00"} <= set(cur.columns) and not cur.empty:
            pp = ((cur["bid_px_00"] + cur["ask_px_00"]) / 2).to_numpy(float); tt = _secs(cur[TS_COL])
        else:
            pp, tt = np.array([]), np.array([])
    favorable_velocity, velocity_asym, semivar_ratio, reversal_rate = _path_asymmetry(pp, tt, pos)

    # --- adverse dynamics: "deep/fast against him" right before the instant ---
    rec = cur[cur[TS_COL] >= (t - pd.Timedelta(seconds=RUN_WINDOW_S))]
    tr_rec = trades_only(rec)
    adverse_speed_recent = (_adv_extent(tr_rec, pos) / RUN_WINDOW_S) if len(tr_rec) >= 2 else np.nan
    adverse_depth_ticks = adverse_new_extremes = np.nan
    if len(tr_rec) >= 2:
        p = tr_rec[PRICE_COL].to_numpy(float); p0 = p[0]
        run = np.maximum.accumulate(p0 - p) if pos > 0 else np.maximum.accumulate(p - p0)  # running adverse extreme
        adverse_new_extremes = float((np.diff(run) > 0).sum())
    if has_book and len(rec) >= 2 and {"bid_px_00", "ask_px_00"} <= set(rec.columns):
        mid = ((rec["bid_px_00"] + rec["ask_px_00"]) / 2).to_numpy(float)
        adv_push = (mid[0] - mid.min()) if pos > 0 else (mid.max() - mid[0])
        adverse_depth_ticks = float(max(0.0, adv_push) / TICK)

    # --- acceleration across N_SLICES of the feature window [t0, t) ---
    accel_cum_delta = accel_ofi = accel_adverse_speed = np.nan
    if len(cur) >= 2:
        edges = [t0 + pd.Timedelta(seconds=w * k / N_SLICES) for k in range(N_SLICES + 1)]
        s_first = cur[(cur[TS_COL] >= edges[0]) & (cur[TS_COL] < edges[1])]
        s_last  = cur[(cur[TS_COL] >= edges[-2]) & (cur[TS_COL] < edges[-1])]
        cd1, cd3 = _cum_delta_adv(trades_only(s_first), pos, sign_mult), _cum_delta_adv(trades_only(s_last), pos, sign_mult)
        of1, of3 = _ofi_adv(s_first, pos), _ofi_adv(s_last, pos)
        av1, av3 = _adv_extent(trades_only(s_first), pos), _adv_extent(trades_only(s_last), pos)
        accel_cum_delta     = (cd3 - cd1) if (np.isfinite(cd1) and np.isfinite(cd3)) else np.nan
        accel_ofi           = (of3 - of1) if (np.isfinite(of1) and np.isfinite(of3)) else np.nan
        accel_adverse_speed = (av3 - av1) if (np.isfinite(av1) and np.isfinite(av3)) else np.nan

    return Feat(cum_delta_adverse, ofi_best_adverse, ofi_multi_adverse, queue_imb_adverse,
                max_trade_size, large_lot_adverse_vol, tape_intensity_ratio, price_adverse_pts,
                favorable_velocity, velocity_asym, semivar_ratio, reversal_rate,
                adverse_speed_recent, adverse_depth_ticks, adverse_new_extremes,
                accel_cum_delta, accel_ofi, accel_adverse_speed), w

# ======================================================================================
# Stats: Cliff's delta + permutation p (deterministic, seeded; no scipy)
# ======================================================================================
def cliffs_delta(x, y):
    x, y = np.asarray(x,float), np.asarray(y,float)
    x, y = x[~np.isnan(x)], y[~np.isnan(y)]
    if len(x)==0 or len(y)==0: return np.nan
    gt = sum((xi > y).sum() for xi in x); lt = sum((xi < y).sum() for xi in x)
    return (gt - lt) / (len(x)*len(y))

def perm_p(x, y, n=N_PERM):
    x, y = np.asarray(x,float), np.asarray(y,float)
    x, y = x[~np.isnan(x)], y[~np.isnan(y)]
    if len(x)==0 or len(y)==0: return np.nan
    obs = np.median(x) - np.median(y); pooled = np.concatenate([x,y]); k = len(x); hits = 0
    for _ in range(n):
        RNG.shuffle(pooled)
        if abs(np.median(pooled[:k]) - np.median(pooled[k:])) >= abs(obs) - 1e-12: hits += 1
    return (hits + 1) / (n + 1)

def _energy_stat(X, Y):
    """Szekely-Rizzo energy distance between two multivariate samples (rows=obs)."""
    def md(A, B):
        d = np.sqrt(((A[:,None,:]-B[None,:,:])**2).sum(-1))
        return d.mean()
    return 2*md(X, Y) - md(X, X) - md(Y, Y)

def energy_omnibus(cut_df, hold_df, feat_names, n=N_PERM):
    """One multivariate test: do cut and hold differ JOINTLY? Standardize features (pooled),
    median-impute NaNs, permutation null on the energy statistic. Returns (stat, p, n_used_features)."""
    use = [f for f in feat_names if (cut_df[f].notna().any() and hold_df[f].notna().any())]
    pooled = pd.concat([cut_df[use], hold_df[use]], axis=0)
    mu, sd = pooled.mean(), pooled.std(ddof=0).replace(0, 1.0)
    def Z(d): return ((d[use] - mu) / sd).fillna(0.0).to_numpy(float)
    X, Y = Z(cut_df), Z(hold_df)
    obs = _energy_stat(X, Y); pooledZ = np.vstack([X, Y]); k = len(X); hits = 0
    for _ in range(n):
        RNG.shuffle(pooledZ)
        if _energy_stat(pooledZ[:k], pooledZ[k:]) >= obs - 1e-12: hits += 1
    return float(obs), (hits + 1) / (n + 1), len(use)

FEATURE_NAMES = list(Feat.__dataclass_fields__.keys())
VELOCITY_FEATURES = ["favorable_velocity", "velocity_asym", "semivar_ratio", "reversal_rate"]
DYNAMICS_FEATURES = ["adverse_speed_recent", "adverse_depth_ticks", "adverse_new_extremes",
                     "accel_cum_delta", "accel_ofi", "accel_adverse_speed"]

def spearman(x, y):
    s = pd.DataFrame({"x": x, "y": y}).replace([np.inf, -np.inf], np.nan).dropna()
    if len(s) < MIN_GRID_PTS or s.x.nunique() < 2 or s.y.nunique() < 2: return np.nan
    return float(np.corrcoef(s.x.rank().values, s.y.rank().values)[0, 1])

def sign_flip_p(d, n=N_PERM):
    """Paired test: are the per-loser (exit - baseline) deltas systematically non-zero?"""
    d = np.asarray(d, float); d = d[~np.isnan(d)]
    if len(d) == 0: return np.nan
    obs = abs(np.median(d)); hits = 0
    for _ in range(n):
        if abs(np.median(d * RNG.choice([-1.0, 1.0], size=len(d)))) >= obs - 1e-12: hits += 1
    return (hits + 1) / (n + 1)

# ======================================================================================
def run_inspect():
    dset = _dataset()
    print("=== SCHEMA ==="); print(list(dset.schema.names))
    has_book = schema_gate(dset)
    price_div, ts_is_int = _detect_scaling(dset)
    print(f"price_div={price_div}  ts_is_int={ts_is_int}  book_features={'ON' if has_book else 'OFF'}")
    sign_mult, corr = infer_delta_sign(dset, price_div, ts_is_int)
    print(f"DELTA-SIGN GATE: corr(signed_vol, price_change)={corr:.3f}  -> sign_mult={sign_mult:+.0f}")
    if np.isnan(corr) or abs(corr) < DELTA_CORR_MIN:
        print(f"  *** WARNING: |corr| < {DELTA_CORR_MIN}: delta-sign ambiguous. Treat delta features as UNRELIABLE. ***")
    else:
        print(f"  OK: convention resolved. Buyer-aggressor = side {'B' if sign_mult>0 else 'A'}.")
    print("Sample rows:"); print(dset.head(3).to_pandas().to_string())

def run_full():
    dset = _dataset(); has_book = schema_gate(dset)
    price_div, ts_is_int = _detect_scaling(dset)
    sign_mult, corr = infer_delta_sign(dset, price_div, ts_is_int)
    ep = load_episodes()

    losers  = ep[ep.realized_pnl < 0].copy()
    cand_ids = winner_mae_prefilter(ep)
    winners = ep[(ep.realized_pnl > 0) & (ep.episode_id.isin(cand_ids))].copy()

    # precise MAE (+instant) from MBP-10 for losers and matched-winner candidates
    for d in (losers, winners):
        mm = d.apply(lambda r: mae_from_trades(dset, r, price_div, ts_is_int), axis=1, result_type="expand")
        d["mae"], d["mae_instant"] = mm[0], mm[1]
    winners_hold = winners[(winners.mae >= MAE_BAND[0]) & (winners.mae <= MAE_BAND[1])].copy()
    winners_all  = ep[ep.realized_pnl > 0].copy()      # all winners, for the winner-EXIT contrast (timestamped)

    feat_cols = [TS_COL, ACTION_COL, SIDE_COL, PRICE_COL, SIZE_COL] + (BID_PX+ASK_PX+BID_SZ+ASK_SZ if has_book else [])

    def feats_at(rows, instant_col):
        out = []
        for _, r in rows.iterrows():
            inst = r[instant_col]
            if pd.isna(inst): continue
            f, _w = compute_features(dset, inst, r.side, r.hold_s, price_div, ts_is_int, sign_mult, has_book)
            out.append(asdict(f))
        return pd.DataFrame(out)

    # losers: read each window ONCE -> exit features + within-trade baseline + null pool + paired delta + time-to-exit grid
    loser_exit_rows, paired_deltas, null_rows, grid_corrs = [], [], [], []
    for _, r in losers.iterrows():
        full = read_window(dset, r.first_entry_utc - pd.Timedelta(seconds=2*W_MAX),
                           r.last_exit_utc + pd.Timedelta(seconds=1), feat_cols, price_div, ts_is_int)
        if full.empty: continue
        fe, _w = compute_features(dset, r.last_exit_utc, r.side, r.hold_s, price_div, ts_is_int, sign_mult, has_book, pre_df=full)
        rec = asdict(fe); rec.update(episode_id=r.episode_id, side=r.side, entry=r.entry, exit_ts=r.last_exit_utc)
        loser_exit_rows.append(rec)
        g = null_guard(r.hold_s); lo = r.first_entry_utc + pd.Timedelta(seconds=g); hi = r.last_exit_utc - pd.Timedelta(seconds=g)
        if hi <= lo: continue
        span = (hi - lo).total_seconds(); bf = []
        for _ in range(N_NULL):
            tau = lo + pd.Timedelta(seconds=float(RNG.uniform(0, span)))
            ff, _w = compute_features(dset, tau, r.side, r.hold_s, price_div, ts_is_int, sign_mult, has_book, pre_df=full)
            dd = asdict(ff); null_rows.append(dd); bf.append(dd)
        base = pd.DataFrame(bf).median(numeric_only=True)
        paired_deltas.append({k: asdict(fe)[k] - base.get(k, np.nan) for k in FEATURE_NAMES})
        # time-to-exit grid: features on a fixed cadence across the hold; per-loser Spearman(feature, seconds-to-exit)
        gpts = np.arange(0, span, GRID_S)
        if len(gpts) >= MIN_GRID_PTS:
            grows, tte = [], []
            for s_ in gpts:
                gp = lo + pd.Timedelta(seconds=float(s_))
                gf, _w = compute_features(dset, gp, r.side, r.hold_s, price_div, ts_is_int, sign_mult, has_book, pre_df=full)
                grows.append(asdict(gf)); tte.append((r.last_exit_utc - gp).total_seconds())
            gdf = pd.DataFrame(grows); tte = np.array(tte)
            grid_corrs.append({fn: spearman(gdf[fn].values, tte) for fn in FEATURE_NAMES})
    loser_exit = pd.DataFrame(loser_exit_rows)
    nulldf     = pd.DataFrame(null_rows)
    paired     = pd.DataFrame(paired_deltas)
    grid_corr  = pd.DataFrame(grid_corrs)   # one row per loser, columns = features, values = Spearman(feat, time-to-exit)
    winner_hold = feats_at(winners_hold, "mae_instant")
    winner_exit = feats_at(winners_all,  "last_exit_utc")

    pd.set_option("display.width", 220); pd.set_option("display.max_columns", 24)
    print(f"\nMATCHED-MAE OVERLAP  loser-exit n={len(losers)} median_MAE={losers.mae.median():.2f} | "
          f"hold(winner trough) n={len(winners_hold)} median_MAE={winners_hold.mae.median():.2f}  (want CLOSE)")
    print(f"DELTA-SIGN GATE: corr={corr:.3f} sign_mult={sign_mult:+.0f}  PATH_SOURCE={PATH_SOURCE}"
          + ("  [DELTA UNRELIABLE]" if (np.isnan(corr) or abs(corr)<DELTA_CORR_MIN) else ""))

    def two_sample_block(title, A, B, na, nb):
        eP = vP = dP = np.nan
        if len(A) and len(B):
            _, eP, ek = energy_omnibus(A, B, FEATURE_NAMES)
            _, vP, vk = energy_omnibus(A, B, VELOCITY_FEATURES)
            _, dP, dk = energy_omnibus(A, B, DYNAMICS_FEATURES)
            print(f"\n=== {title} ===  ({na} n={len(A)} vs {nb} n={len(B)})")
            print(f"OMNIBUS  all {ek}f: p={eP:.4f}   |   velocity {vk}f: p={vP:.4f}   |   dynamics {dk}f: p={dP:.4f}   (p<0.05 = joint diff)")
            rows = [dict(feature=fn, med_a=np.nanmedian(A[fn]), med_b=np.nanmedian(B[fn]),
                         cliffs=cliffs_delta(A[fn].values, B[fn].values),
                         perm_p=perm_p(A[fn].values, B[fn].values)) for fn in FEATURE_NAMES]
            print(pd.DataFrame(rows).round(3).to_string(index=False))
        return eP, vP, dP

    # D. WITHIN-LOSER GOOD-CUT vs BAD-CUT (actionable, confound-free of profit-take): label from forward es_1m_front
    es1m = pd.read_parquet(ES_1M_FRONT).sort_values("ts_event")
    labs, cov = [], []
    for _, row in loser_exit.iterrows():
        g, n = label_good_cut(es1m, row.side, row.entry, row.exit_ts, FWD_HORIZON_S)
        labs.append(g); cov.append(n)
    loser_exit["good_cut"] = labs
    good = loser_exit[loser_exit.good_cut == 1]; bad = loser_exit[loser_exit.good_cut == 0]
    print(f"\n=== D. GOOD-CUT vs BAD-CUT  (within losers; H={FWD_HORIZON_S}s; bad=recovered to entry) ===  [actionable]")
    print(f"   good(no recovery) n={len(good)} | bad(recovered) n={len(bad)} | min_fwd_bars={min(cov) if cov else 0}")
    dA, dV, dD = two_sample_block("   D detail", good, bad, "good_cut", "bad_cut")

    # E. TIME-TO-EXIT (within-loser): per-loser Spearman(feature, seconds-to-exit), then sign-flip across losers (autocorr-safe)
    print(f"\n=== E. TIME-TO-EXIT  (n={len(grid_corr)} losers; GRID={GRID_S}s; per-loser rank-corr, sign-flip across losers) ===  [highest-power]")
    print("   negative median_rho = feature RISES as his exit approaches; watch the dynamics rows")
    erows = []
    for fn in FEATURE_NAMES:
        c = grid_corr[fn].values if len(grid_corr) else np.array([])
        erows.append(dict(feature=fn, median_rho=np.nanmedian(c) if len(c) else np.nan,
                          frac_neg=float(np.nanmean(np.asarray(c, float) < 0)) if len(c) else np.nan,
                          p=sign_flip_p(c) if len(c) else np.nan))
    print(pd.DataFrame(erows).round(3).to_string(index=False))

    # C. WITHIN-TRADE PAIRED (alignment-immune): each loser's exit vs its own within-trade baseline
    print(f"\n=== C. WITHIN-TRADE PAIRED  (n={len(paired)} losers; delta = exit - own baseline) ===  [alignment-immune]")
    prows = [dict(feature=fn, median_delta=np.nanmedian(paired[fn]) if len(paired) else np.nan,
                  frac_pos=float(np.nanmean(paired[fn].to_numpy(float) > 0)) if len(paired) else np.nan,
                  paired_p=sign_flip_p(paired[fn].values) if len(paired) else np.nan) for fn in FEATURE_NAMES]
    print(pd.DataFrame(prows).round(3).to_string(index=False))

    # B. WINNER-EXIT vs LOSER-EXIT (both real timestamped exits, no imputation)
    bA, bV, bD = two_sample_block("B. WINNER-EXIT vs LOSER-EXIT  [both timestamped]", winner_exit, loser_exit, "win_exit", "lose_exit")
    aA, aV, aD = two_sample_block("A. LOSER-EXIT vs HOLD(trough)  [as before]", loser_exit, winner_hold, "cut", "hold")

    # F. WINDOW/SLICE SENSITIVITY (exploratory; Oct only): does the lead strengthen/weaken with the observation window?
    # Tests accel_adverse_speed, favorable_velocity (stall), and a combined z-score on the good-cut/bad-cut split.
    tcols = [TS_COL, ACTION_COL, SIDE_COL, PRICE_COL, SIZE_COL]
    acc = {}
    maxw = max(EXPLORE_W_GRID)
    for _, row in loser_exit.iterrows():
        if pd.isna(row.good_cut): continue
        full = read_window(dset, row.exit_ts - pd.Timedelta(seconds=maxw + 5),
                           row.exit_ts + pd.Timedelta(seconds=1), tcols, price_div, ts_is_int)
        if full.empty: continue
        grp = "good" if row.good_cut == 1 else "bad"
        for w_ in EXPLORE_W_GRID:
            for ns in EXPLORE_SLICES:
                a, fv = _accel_fav_at(full, row.exit_ts, row.side, w_, ns, sign_mult)
                d = acc.setdefault((w_, ns), {"good": {"a": [], "fv": []}, "bad": {"a": [], "fv": []}})
                d[grp]["a"].append(a); d[grp]["fv"].append(fv)
    def _z(x, ref):
        m, s = np.nanmean(ref), np.nanstd(ref)
        return (np.asarray(x, float) - m) / s if s > 0 else np.full(len(x), np.nan)
    frows = []
    for (w_, ns), d in sorted(acc.items()):
        ga, ba = np.array(d["good"]["a"], float), np.array(d["bad"]["a"], float)
        gf, bf = np.array(d["good"]["fv"], float), np.array(d["bad"]["fv"], float)
        allA, allF = np.concatenate([ga, ba]), np.concatenate([gf, bf])
        gC = _z(ga, allA) - _z(gf, allF); bC = _z(ba, allA) - _z(bf, allF)   # good = high accel + low fav (stall)
        frows.append(dict(w=w_, slices=ns,
                          accel_cliffs=cliffs_delta(ga, ba), accel_p=perm_p(ga, ba),
                          favstall_cliffs=cliffs_delta(gf, bf), favstall_p=perm_p(gf, bf),
                          combined_cliffs=cliffs_delta(gC, bC), combined_p=perm_p(gC, bC)))
    print(f"\n=== F. WINDOW/SLICE SENSITIVITY  (good vs bad cut; exploratory, Oct only) ===")
    print("   accel: good>bad expected (+cliffs). favstall: good<bad expected (-cliffs, slow favorable=good cut).")
    print("   combined = z(accel) - z(fav): good>bad expected (+cliffs).")
    print(pd.DataFrame(frows).round(3).to_string(index=False))

    # G. CUT-TYPE CLUSTERING (exploratory): are the 16 cuts one signal or two types (accel vs stall)?
    crows = []
    for _, row in loser_exit.iterrows():
        if pd.isna(row.good_cut): continue
        full = read_window(dset, row.exit_ts - pd.Timedelta(seconds=CLUSTER_W + 5),
                           row.exit_ts + pd.Timedelta(seconds=1), feat_cols, price_div, ts_is_int)
        if full.empty: continue
        cf = _cluster_feats_at(full, row.exit_ts, row.side, CLUSTER_W, CLUSTER_SLICES, sign_mult, has_book)
        cf.update(episode_id=int(row.episode_id), good_cut=int(row.good_cut)); crows.append(cf)
    cl = pd.DataFrame(crows)
    print(f"\n=== G. CUT-TYPE CLUSTERING  (k=2 on {CLUSTER_FEATURES}; window={CLUSTER_W}s/{CLUSTER_SLICES}) ===  [exploratory]")
    if len(cl) >= 4:
        X = cl[CLUSTER_FEATURES].copy()
        X = X.fillna(X.median())
        Z = ((X - X.mean()) / X.std(ddof=0).replace(0, 1.0)).to_numpy(float)
        lab, _C = _kmeans2(Z); cl["cluster"] = lab
        print(cl[["episode_id", "good_cut", "cluster"] + CLUSTER_FEATURES].round(3).to_string(index=False))
        print("\n  cluster medians (original units):")
        print(cl.groupby("cluster")[CLUSTER_FEATURES].median().round(3).to_string())
        print("\n  cluster x good_cut (rows=cluster, cols=good_cut 0=bad/1=good):")
        print(pd.crosstab(cl.cluster, cl.good_cut).to_string())
    else:
        print("  too few labelled cuts to cluster")

    # H. HELD-THROUGH-STALL (exploratory): did he HOLD (winner trough) when favorable was alive vs CUT when it stalled?
    hrows = []
    for _, row in winners_hold.iterrows():
        if pd.isna(row.mae_instant): continue
        full = read_window(dset, row.mae_instant - pd.Timedelta(seconds=CLUSTER_W + 5),
                           row.mae_instant + pd.Timedelta(seconds=1), feat_cols, price_div, ts_is_int)
        if full.empty: continue
        hrows.append(_cluster_feats_at(full, row.mae_instant, row.side, CLUSTER_W, CLUSTER_SLICES, sign_mult, has_book))
    hold_cf = pd.DataFrame(hrows)
    print(f"\n=== H. HELD-THROUGH-STALL  (good-cut vs winner-hold; window={CLUSTER_W}s) ===  [exploratory]")
    if len(cl) and len(hold_cf):
        good_cf = cl[cl.good_cut == 1]; allcut_cf = cl
        hh = []
        for feat in ["favorable_velocity", "accel_adverse_speed", "accel_cum_delta"]:
            g, a, h = good_cf[feat].values, allcut_cf[feat].values, hold_cf[feat].values
            hh.append(dict(feature=feat, med_goodcut=np.nanmedian(g), med_allcut=np.nanmedian(a), med_hold=np.nanmedian(h),
                           cliffs_good_vs_hold=cliffs_delta(g, h), perm_p_good_vs_hold=perm_p(g, h)))
        print("   hypothesis: holds keep favorable alive (high fav_vel); good-cuts have it stalled (low). Want gradient good < all < hold.")
        print(pd.DataFrame(hh).round(3).to_string(index=False))
    else:
        print("  insufficient data")

    # I. WHOLE-HOLD STATE (exploratory): the confluence over the ENTIRE entry->exit window, losers (cut) vs held winners.
    #    Also an EARLY window (first EARLY_S s) = predictive / non-tautological view. (*) marks outcome-tautological features.
    state_cols = [TS_COL, ACTION_COL, PRICE_COL, SIZE_COL, "bid_px_00", "ask_px_00", "bid_sz_00", "ask_sz_00"]
    def hold_states(rows):
        whole, early = [], []
        for _, r in rows.iterrows():
            win = read_window(dset, r.first_entry_utc, r.last_exit_utc + pd.Timedelta(seconds=1),
                              state_cols, price_div, ts_is_int)
            if win.empty: continue
            whole.append(_hold_state(win, r.entry, r.side))
            ew = win[win[TS_COL] <= r.first_entry_utc + pd.Timedelta(seconds=EARLY_S)]
            early.append(_hold_state(ew, r.entry, r.side))
        return pd.DataFrame(whole), pd.DataFrame(early)
    print(f"\n=== I. WHOLE-HOLD STATE  (loser/cut vs held-winner; reads full holds, may be slow) ===  [exploratory]")
    Lw, Le = hold_states(losers)
    Ww, We = hold_states(winners_all)
    def state_table(LA, WA, tag):
        rows = []
        for fn in STATE_FEATURES:
            a, b = LA[fn].values, WA[fn].values
            rows.append(dict(feature=fn + (" (*)" if fn in STATE_TAUTOLOGICAL else ""),
                             med_loser=np.nanmedian(a), med_winner=np.nanmedian(b),
                             cliffs=cliffs_delta(a, b), perm_p=perm_p(a, b)))
        print(f"\n  [{tag}]  loser n={len(LA)} vs winner n={len(WA)}   (*) = outcome-tautological, read with caution")
        print(pd.DataFrame(rows).round(3).to_string(index=False))
    if len(Lw) and len(Ww): state_table(Lw, Ww, "WHOLE HOLD")
    if len(Le) and len(We): state_table(Le, We, f"EARLY {EARLY_S}s (predictive)")
    # coverage (4): for the cleanest favorable-failure feature, how many losers vs winners show the unfavorable state
    if len(Le) and len(We):
        thr = np.nanmedian(np.concatenate([Le["time_to_first_fav_frac"].values, We["time_to_first_fav_frac"].values]))
        lo_cov = float(np.nanmean(Le["time_to_first_fav_frac"].values >= thr))
        wi_cov = float(np.nanmean(We["time_to_first_fav_frac"].values >= thr))
        print(f"\n  COVERAGE (early time_to_first_fav >= {thr:.2f}): losers {lo_cov:.0%} vs winners {wi_cov:.0%}  "
              f"(want losers high = slow to go his way early)")

    # J. FAILED RALLY / GIVE-BACK (exploratory): favorable-side event, tilt for discretionary exit (good vs bad cut).
    print(f"\n=== J. FAILED RALLY / GIVE-BACK  (good vs bad cut; MFE + pre-exit bounce-then-fail) ===  [exploratory; tilt]")
    gc = loser_exit["good_cut"].to_numpy()
    fv = loser_exit["favorable_velocity"].to_numpy()
    jrows = []
    losL = losers.reset_index(drop=True)
    for i, r in enumerate(losL.itertuples()):
        win = read_window(dset, r.first_entry_utc, r.last_exit_utc + pd.Timedelta(seconds=1),
                          state_cols, price_div, ts_is_int)
        rec = dict(episode_id=int(getattr(r, "episode_id", i)), good_cut=gc[i],
                   loss_pts=float(getattr(r, "realized_pnl", np.nan)), fav_vel=float(fv[i]))
        for w in FR_W_GRID:
            fr = _failed_rally(win, r.entry, r.side, w, r.last_exit_utc)
            if w == FR_W_GRID[0]: rec["mfe_hold_pts"] = fr["mfe_hold_pts"]
            rec[f"giveback_{w}"] = fr["giveback_w"]; rec[f"rally_{w}"] = fr["rally_size_w"]
        jrows.append(rec)
    J = pd.DataFrame(jrows)
    show = ["episode_id", "good_cut", "mfe_hold_pts", f"rally_{FR_W_GRID[1]}", f"giveback_{FR_W_GRID[1]}", "fav_vel"]
    print(J[show].round(3).to_string(index=False))
    g_, b_ = J[J.good_cut == 1], J[J.good_cut == 0]
    print(f"\n  good-cut n={len(g_)} vs bad-cut n={len(b_)}   (MFE hypothesis: good=lower MFE=never worked; bad=higher=gave back a live trade)")
    srows = [dict(feature="mfe_hold_pts", med_good=np.nanmedian(g_.mfe_hold_pts), med_bad=np.nanmedian(b_.mfe_hold_pts),
                  cliffs=cliffs_delta(g_.mfe_hold_pts.values, b_.mfe_hold_pts.values),
                  perm_p=perm_p(g_.mfe_hold_pts.values, b_.mfe_hold_pts.values))]
    for w in FR_W_GRID:
        for base in ("rally", "giveback"):
            col = f"{base}_{w}"
            srows.append(dict(feature=col, med_good=np.nanmedian(g_[col]), med_bad=np.nanmedian(b_[col]),
                              cliffs=cliffs_delta(g_[col].values, b_[col].values),
                              perm_p=perm_p(g_[col].values, b_[col].values)))
    print(pd.DataFrame(srows).round(3).to_string(index=False))
    print(f"\n  CONFLUENCE with favorable-stall (Spearman across {len(J)} losers; are these the SAME signal or additive?):")
    print(f"    mfe_hold_pts   vs fav_vel : rho={_spearman(J.mfe_hold_pts, J.fav_vel):+.3f}")
    print(f"    giveback_{FR_W_GRID[1]} vs fav_vel : rho={_spearman(J[f'giveback_{FR_W_GRID[1]}'], J.fav_vel):+.3f}")

    # K. BOUNCE-BEHAVIOR TILT (exploratory): cut vs hold on favorable_velocity, as a threshold FILTER (winner-hold = positive class).
    print(f"\n=== K. BOUNCE-BEHAVIOR TILT  (cut vs hold; favorable_velocity as a filter) ===  [exploratory; tilt; IN-SAMPLE]")
    maxw = max(KW_GRID) + 5
    def fv_at_windows(instant, side):
        full = read_window(dset, pd.Timestamp(instant) - pd.Timedelta(seconds=maxw),
                           pd.Timestamp(instant) + pd.Timedelta(seconds=1), feat_cols, price_div, ts_is_int)
        return {w: _cluster_feats_at(full, instant, side, w, CLUSTER_SLICES, sign_mult, has_book)["favorable_velocity"]
                for w in KW_GRID} if not full.empty else {w: np.nan for w in KW_GRID}
    cut_fv  = [fv_at_windows(r.exit_ts, r.side) for _, r in loser_exit.iterrows()]
    gc_mask = loser_exit["good_cut"].to_numpy()
    hold_fv = [fv_at_windows(r.mae_instant, r.side) for _, r in winners_hold.iterrows() if pd.notna(r.mae_instant)]
    krows = []
    for w in KW_GRID:
        cut = np.array([d[w] for d in cut_fv], float)
        hold = np.array([d[w] for d in hold_fv], float)
        good = np.array([d[w] for d, g in zip(cut_fv, gc_mask) if g == 1], float)
        for cuts, ctag in [(cut, "all-cut"), (good, "good-cut")]:
            cl = cliffs_delta(hold, cuts)                       # +cliffs = holds rank higher (bounce more alive)
            sc = np.concatenate([cuts, hold]); lb = np.concatenate([np.zeros(len(cuts)), np.ones(len(hold))])
            jstat, thr, sens, spec = _youden(sc, lb)
            krows.append(dict(w=w, contrast=f"hold_vs_{ctag}", n_cut=len(cuts), n_hold=len(hold),
                              cliffs=cl, auc=(cl + 1) / 2, perm_p=perm_p(hold, cuts),
                              best_thr=thr, sens_hold=sens, spec_cut=spec, bal_acc=(sens + spec) / 2 if np.isfinite(sens) else np.nan))
    print("   +cliffs/auc>0.5 = holds have livelier bounce than cuts. filter: HOLD if favorable_velocity > best_thr, else lean CUT.")
    print("   (best_thr/sens/spec are IN-SAMPLE upper bounds -- optimistic; Feb adjudicates.)")
    print(pd.DataFrame(krows).round(3).to_string(index=False))

    for df_, tag in [(loser_exit,"loser_exit"), (winner_exit,"winner_exit"), (winner_hold,"winner_hold")]:
        if len(df_): df_["group"] = tag
    pd.concat([d for d in (loser_exit, winner_exit, winner_hold) if len(d)], ignore_index=True).to_csv(OUT_FEATURES, index=False)
    paired.to_csv("p1_paired_deltas.csv", index=False)
    grid_corr.to_csv("p1_time_to_exit_corrs.csv", index=False)

    git = "n/a"
    try:
        import subprocess
        git = subprocess.check_output(["git","rev-parse","--short","HEAD"], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        pass
    prov = dict(seed=SEED, n_perm=N_PERM, path_source=PATH_SOURCE, w_min=W_MIN, w_max=W_MAX,
                lag_guard_s=LAG_GUARD_S, mae_band=MAE_BAND, n_null=N_NULL, ofi_levels=OFI_LEVELS,
                large_lot_min=LARGE_LOT_MIN, fwd_horizon_s=FWD_HORIZON_S, delta_corr=corr, sign_mult=sign_mult,
                contract_id=CONTRACT_ID, omni_D_all_p=dA, omni_D_vel_p=dV, omni_D_dyn_p=dD,
                omni_A_all_p=aA, omni_A_vel_p=aV, omni_A_dyn_p=aD,
                omni_B_all_p=bA, omni_B_vel_p=bV, omni_B_dyn_p=bD, git_commit=git,
                config_hash=hashlib.sha256(json.dumps({k:str(v) for k,v in globals().items()
                    if k.isupper()}, sort_keys=True).encode()).hexdigest()[:12])
    print("\nPROVENANCE:", json.dumps(prov, default=str))
    print("READING:")
    print(" - E (time-to-exit) is the highest-power lens for 'deep/fast against him drives the exit': does a feature")
    print("   RISE as his exit nears, within his own trades? Negative median_rho + small p on a dynamics feature = your signal.")
    print(" - DYNAMICS omnibus isolates the new depth/speed/acceleration features from the old level features.")
    print(" - D = cut quality, C = within-trade shift, B = exit-by-outcome, A = cut-vs-hold.")
    print(" - n tiny -> SIGNAL-SPOTTING. Carry only pre-specified survivors to Feb-2022; nothing here is confirmed.")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "inspect"
    (run_inspect if mode == "inspect" else run_full)()
