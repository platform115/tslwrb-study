#!/usr/bin/env python3
"""
horse_race_spine.py  — shared machinery for the 07/08 paired horse race
-------------------------------------------------------------------------------
Single source of truth for everything the four tests share, so the grouping,
windows, AUC, CI, and coherence diagnostic CANNOT drift between 07a / 07b /
08-bar / 08-tick. The four test scripts import from here and supply ONLY their
own feature function. This module computes NO feature itself and freezes NO
estimator — it is plumbing.

Reuses the FROZEN machinery from trade_flow_exhaustion.py (grouping / per-second
reader / constants). Does NOT modify that file. Place this beside it.

POPULATION (this chat): 52 target_reached vs 40 failed_trades (Reading B, frozen pt1).
DIRECTION: every AUC here is reported TWO-SIDED (per pre-registration). The read is
"does the 95% CI exclude 0.5" and "in which direction", NOT "lower bound > 0.5".
On discovery we REPORT; we do not declare a winner or freeze a primary estimator.

A feature_fn has signature:
    feature_fn(side: str, ws: Timestamp, we: Timestamp) -> dict | None
returning at minimum {"value": float}.  It SHOULD also return the coherence
ingredients when the feature is a ratio:
    {"value": ratio, "num": numerator_total, "den": denominator_total, "n": usable_count}
Return None (or value=nan) for a window that cannot be scored (caller handles it).
The feature_fn closes over whatever data it needs (per-second arrays, or bars).
"""

import numpy as np
import pandas as pd

# --- frozen machinery: imported, never re-implemented ---
from trade_flow_exhaustion import build_groups, S


# =============================================================================
# 1. GROUPING (52/40) — frozen pt1 / Reading B, via the frozen build_groups
# =============================================================================
def load_and_group(config_path, wrb_path):
    """Returns (failed_df, reached_df, g_full). 52 reached / 40 failed expected (Oct ESZ5)."""
    import tomllib
    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)
    ep_path = cfg["paths"]["episodes"]
    windowed = cfg.get("run", {}).get("resolved", {}).get("windowed_parquet")
    g = build_groups(ep_path, wrb_path)
    failed = g[g.group == "failed_trades"].copy().reset_index(drop=True)
    reached = g[g.group == "target_reached"].copy().reset_index(drop=True)
    return failed, reached, g, ep_path, windowed


# =============================================================================
# 2. DESIGN A WINDOW ENUMERATION (re-armed for 52/40)
#    failed cut-window  : [max(entry, exit - W), exit)
#    reached peer-window: per failed tau=hold, each reached peer with pt1_open_el > tau
#                         -> [max(entry, entry+tau - W), entry+tau)
#    Mirrors the descriptive pass exactly (already validated on Oct: 40 cuts / 627 peers).
# =============================================================================
def designA_cut_windows(failed, W):
    out = []
    for _, f in failed.iterrows():
        we = f.exit; ws = max(f.entry, f.exit - W)
        out.append(dict(uid=f.uid, side=f.side, ws=ws, we=we, tau=float(f.hold)))
    return out


def designA_peer_windows_for(f_row, reached, W):
    """Eligible reached peers for one failed cut at tau = f_row.hold."""
    tau = float(f_row.hold)
    elig = reached[reached.pt1_open_el > tau]
    out = []
    for _, r in elig.iterrows():
        anc = r.entry + S(tau); ws = max(r.entry, anc - W); we = anc
        out.append(dict(uid=r.uid, side=r.side, ws=ws, we=we, tau=tau))
    return out


# =============================================================================
# 3. TWO-SIDED RANK AUC  (pure numpy; identical engine to the frozen auc_pair)
# =============================================================================
def rank_auc(a, b):
    """Directional AUC = P(a > b) with 0.5 ties. a,b array-like; NaNs dropped."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    a = a[~np.isnan(a)]; b = b[~np.isnan(b)]
    if len(a) == 0 or len(b) == 0:
        return np.nan, len(a), len(b)
    gt = (a[:, None] > b[None, :]).sum() + 0.5 * (a[:, None] == b[None, :]).sum()
    return gt / (len(a) * len(b)), len(a), len(b)


def two_sided(auc):
    """Return (strength, direction): strength = |auc-0.5|+0.5 in [0.5,1]; direction str."""
    if np.isnan(auc):
        return np.nan, "n/a"
    if auc >= 0.5:
        return auc, "reached>failed"
    return 1.0 - auc, "failed>reached"


# =============================================================================
# 4. CLUSTER-BOOTSTRAP CI over Design-A per-cut AUCs  (seed-fixed, deterministic)
#    Two-sided read: report point + CI; flag whether CI excludes 0.5.
# =============================================================================
def cluster_boot_ci(per_cut, seed=0, B=10000):
    pc = np.asarray(per_cut, float); pc = pc[~np.isnan(pc)]
    if len(pc) < 5:
        return dict(mean=np.nan, lo=np.nan, hi=np.nan, n=len(pc), excludes_half=False)
    rng = np.random.default_rng(seed)
    boot = np.array([rng.choice(pc, len(pc), True).mean() for _ in range(B)])
    lo, hi = float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))
    return dict(mean=float(pc.mean()), lo=lo, hi=hi, n=len(pc),
                excludes_half=(lo > 0.5 or hi < 0.5))


# =============================================================================
# 5. DESIGN A per-cut scorer (the PRIMARY decision window)
#    For each failed cut: value_cut vs eligible reached-peer values -> per-cut AUC
#    P(peer > cut). Bootstrap over the failed cuts. feature_fn supplies values.
#    Also accumulates coherence ingredients (num/den) per arm if provided.
# =============================================================================
def designA_perCut(failed, reached, feature_fn, W, seed=0, B=10000):
    per_cut = []
    coh_cut = {"num": [], "den": [], "n": []}
    coh_peer = {"num": [], "den": [], "n": []}
    n_cut_scored = 0
    for _, f in failed.iterrows():
        we = f.exit; ws = max(f.entry, f.exit - W)
        fc = feature_fn(f.side, ws, we)
        if fc is None or np.isnan(fc.get("value", np.nan)):
            continue
        _accum(coh_cut, fc)
        n_cut_scored += 1
        peers = designA_peer_windows_for(f, reached, W)
        pv = []
        for pw in peers:
            fp = feature_fn(pw["side"], pw["ws"], pw["we"])
            if fp is None or np.isnan(fp.get("value", np.nan)):
                continue
            _accum(coh_peer, fp)
            pv.append(fp["value"])
        if pv:
            pv = np.asarray(pv, float)
            cv = fc["value"]
            per_cut.append((np.sum(pv > cv) + 0.5 * np.sum(pv == cv)) / len(pv))
    ci = cluster_boot_ci(per_cut, seed=seed, B=B)
    return dict(ci=ci, n_cut_scored=n_cut_scored, coh_cut=coh_cut, coh_peer=coh_peer)


def _accum(store, fdict):
    for k in ("num", "den", "n"):
        if k in fdict and fdict[k] is not None and not (isinstance(fdict[k], float) and np.isnan(fdict[k])):
            store[k].append(fdict[k])


# =============================================================================
# 6. POPULATION-LEVEL two-sided AUC on a window set (used for A1/A2/B context,
#    and as a simpler cross-check beside Design A). feature_fn over each trade's
#    own window via (side, ws, we) columns the caller passes in.
# =============================================================================
def population_auc(failed, reached, feature_fn, ws_col, we_col):
    def vals(df):
        out = []
        for _, r in df.iterrows():
            fr = feature_fn(r.side, r[ws_col], r[we_col])
            out.append(np.nan if (fr is None) else fr.get("value", np.nan))
        return np.asarray(out, float)
    rv, fv = vals(reached), vals(failed)
    auc, nr, nf = rank_auc(rv, fv)
    strength, direction = two_sided(auc)
    return dict(auc=auc, strength=strength, direction=direction, n_reached=nr, n_failed=nf,
                med_reached=float(np.nanmedian(rv)) if np.isfinite(rv).any() else np.nan,
                med_failed=float(np.nanmedian(fv)) if np.isfinite(fv).any() else np.nan)


# =============================================================================
# 7. COHERENCE DIAGNOSTIC — print the two ingredients of a ratio separately,
#    per arm, so a separating ratio can be attributed to genuine impact vs to
#    the known price-move asymmetry (failed windows move more: 46 vs 31 ticks).
#    num = total |Δmid| (ticks); den = total volume; ratio summary = sum/sum.
# =============================================================================
def report_coherence(label, coh_cut, coh_peer):
    def block(name, c):
        if not c["num"]:
            print(f"    {name}: (no scored windows)")
            return
        num = np.array(c["num"], float); den = np.array(c["den"], float); nn = np.array(c["n"], float)
        sum_ratio = num.sum() / den.sum() if den.sum() > 0 else np.nan
        print(f"    {name:14s} windows={len(num):4d}  Σnum(|Δmid|tk)={num.sum():10.1f}  "
              f"Σden(vol)={den.sum():12.0f}  Σnum/Σden={sum_ratio:.5f}  "
              f"med usable-sec={np.nanmedian(nn):.0f}")
    print(f"  [coherence] {label}  (is a separating ratio driven by numerator or denominator?)")
    block("failed cut", coh_cut)
    block("reached peer", coh_peer)


# =============================================================================
# 8. REPORTERS
# =============================================================================
def report_designA(title, res):
    ci = res["ci"]
    print(f"\n===== {title} — Design A (PRIMARY, two-sided) =====")
    print(f"  per-cut AUC = P(reached-peer value > failed-cut value)")
    if np.isnan(ci["mean"]):
        print(f"  n cuts scored = {res['n_cut_scored']} (<5 valid cuts: uninformative)")
    else:
        flag = "CI EXCLUDES 0.5 (separates)" if ci["excludes_half"] else "CI includes 0.5 (no separation)"
        print(f"  point = {ci['mean']:.3f}   95% CI [{ci['lo']:.3f}, {ci['hi']:.3f}]   "
              f"cuts={ci['n']}   -> {flag}")
        if ci["n"] < 8:
            print(f"  NOTE: {ci['n']} valid cuts < floor 8 -> treat as uninformative, not a result.")


def report_population(title, res):
    print(f"  {title:26s} AUC={res['auc']:.3f}  two-sided={res['strength']:.3f} "
          f"({res['direction']})  medR={res['med_reached']:+.3f} medF={res['med_failed']:+.3f} "
          f"(nR={res['n_reached']}, nF={res['n_failed']})")


if __name__ == "__main__":
    # Self-test only: confirm the spine imports, groups resolve 52/40, and Design-A
    # window counts match the validated descriptive pass (40 cuts / 627 peers).
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--W", type=int, default=60)
    a = ap.parse_args()
    failed, reached, g, ep, win = load_and_group(a.config, a.wrb)
    print(f"[spine] target_reached={len(reached)}  failed_trades={len(failed)}  (expect 52 / 40)")
    W = S(a.W)
    cuts = designA_cut_windows(failed, W)
    npeers = sum(len(designA_peer_windows_for(f, reached, W)) for _, f in failed.iterrows())
    print(f"[spine] Design A: cut-windows={len(cuts)}  peer-windows={npeers}  (expect 40 / 627 at W=60)")
    print(f"[spine] windowed_parquet from config: {win}")
    print("[spine] OK — import clean, grouping + window enumeration match the descriptive pass.")
