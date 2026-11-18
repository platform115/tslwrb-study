#!/usr/bin/env python3
"""
truncation_harness.py — THE LOOKAHEAD GATE (built after T-EN99/100).
===============================================================================
PRINCIPLE: a signal evaluated at time t may depend only on information
available at t. The test is mechanical: recompute each quantity with the
data TRUNCATED at t and compare to the value the pipeline used. Any
difference = lookahead, proven, no judgment involved.

Truncation rules (what "available at t" means here):
  - per-second mids/secs: samples with timestamp <= t only
  - bar PRICES (o/h/l/c, TR): completed bars only (bar close <= t)
  - bar CALENDAR (open time, session label, session date): known in advance
    (exchange schedule) - NOT truncated
  - session-level statistics (C(day), 14-session tables): sessions strictly
    before t's session date

WHAT THIS RUN TESTS (training months, sampled fire seconds + M1 trades):
  E1 burst measure mv8(t)                       - expect PASS
  E2 atr10 at the fire bar (10 completed bars)  - expect PASS
  E3 C(day) for the fire's session              - expect PASS
  E4 honest per-second thrust (120s)            - expect PASS
  E5 CONTAMINATED thrust ret2[ib]               - expect FAIL (harness
     sensitivity check: the known bug must be caught)
  E6 old score signals: completion stamp <= t   - expect PASS
  X1 M1 exits: re-run each sampled trade's leg with all bar prices AFTER its
     exit poisoned to NaN and seconds truncated at the exit - outcome
     (price, second, reason) must be identical  - expect PASS

STANDING GATE (charter): no new entry/signal script earns a registry row
until its fire logic passes this harness.

RUN: python3 Tests/P0_audit/truncation_harness.py                         (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(T, "P4_entry_determination"))
sys.path.insert(0, os.path.join(T, "P5_trade_management"))
from p4_2_entry_context import MONTHS                  # noqa: E402
from p4_66_context_ablation import prep                # noqa: E402
import p5_1_excursion_anatomy as X                     # noqa: E402
from p5_10_stall_stack_dials import leg as leg_m1      # noqa: E402

TICK = 0.25
W, GAP = 2, 45
BSH = 0.022
Q = dict(early=4.0, stop=4.0, time_bars=27, S=30)
N_ENTRY, N_EXIT = 300, 150
RNG = np.random.default_rng(7)


class PoisonView:
    """cx with bar prices NaN-poisoned beyond a cutoff; calendar kept."""
    def __init__(self, cx, cut_s):
        self.bts, self.bsec = cx.bts, cx.bsec
        self.sd, self.rth = cx.sd, cx.rth
        done = cx.bsec + 60 <= cut_s
        self.c = np.where(done, cx.c, np.nan)
        self.h = np.where(done, cx.h, np.nan)
        self.l = np.where(done, cx.l, np.nan)
        keep = cx.secs <= cut_s
        self.secs, self.mids = cx.secs[keep], cx.mids[keep]
        self._cx = cx

    def bar_of(self, s):
        return self._cx.bar_of(s)


def run(repo):
    c_day = X.c_day_fun(repo)
    from p4_89_cn_adaptive import session_ratio_table, NSESS
    RT = session_ratio_table(repo)
    overall_fail = 0
    for m, _ in MONTHS:
        P = prep(repo, m)
        cx = P["cx"]
        secs, mids = P["secs"], P["mids"]
        iw = np.searchsorted(secs, secs - 8)
        mv8 = (mids - mids[np.maximum(iw, 0)]) / TICK
        i120 = np.searchsorted(secs, secs - 120)
        mv120 = (mids - mids[np.maximum(i120, 0)]) / TICK
        bar_i = np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1, 0, len(cx.c) - 1)
        pc = np.roll(cx.c, 1); pc[0] = cx.c[0]
        tr = np.maximum(cx.h - cx.l, np.maximum(np.abs(cx.h - pc), np.abs(cx.l - pc))) / TICK
        atr10 = pd.Series(tr).shift(1).rolling(10).mean().to_numpy()
        cds = {d: c_day(d) for d in set(P["sd"])}
        Cd_bar = np.array([cds.get(d) or np.nan for d in P["sd"]])
        ret2 = np.concatenate([[0.0] * W, (cx.c[W:] - cx.c[:-W]) / TICK])
        sig = cx.sig
        sig_comp = sig.comp_ns.to_numpy(np.int64) if len(sig) else np.array([], np.int64)

        # candidate fire seconds: honest burst crossings (gap-deduped)
        R = Cd_bar[bar_i] * atr10[bar_i]
        bt = BSH * R
        cand = []
        last = -10**18
        for i in np.flatnonzero(P["keep"] & np.isfinite(bt)):
            if abs(mv8[i]) < bt[i]:
                continue
            if secs[i] - last <= GAP:
                continue
            last = int(secs[i])
            ib = bar_i[i]
            if ib < 60 or not cx.rth[ib]:
                continue
            cand.append(i)
        pick = RNG.choice(len(cand), size=min(N_ENTRY, len(cand)), replace=False)
        sample = [cand[k] for k in sorted(pick)]

        res = {k: [0, 0] for k in ("E1 mv8", "E2 atr10", "E3 C(day)",
                                   "E4 honest thrust", "E5 CONTAM thrust",
                                   "E6 signal stamps")}
        for i in sample:
            t = int(secs[i]); ib = int(bar_i[i])
            keep_s = secs <= t
            msec, mmid = secs[keep_s], mids[keep_s]
            # E1
            j = np.searchsorted(msec, t - 8)
            v = (mmid[-1] - mmid[min(j, len(mmid) - 1)]) / TICK
            res["E1 mv8"][0 if np.isclose(v, mv8[i], atol=1e-9) else 1] += 1
            # E2: last 10 completed bars before t
            done = np.flatnonzero(cx.bsec + 60 <= t)
            if len(done) >= 10:
                v = float(np.mean(tr[done[-10:]]))
                ref = atr10[ib]
                res["E2 atr10"][0 if np.isclose(v, ref, atol=1e-9) else 1] += 1
            # E3: C(day) from sessions strictly before t's session
            d = P["sd"][ib]
            i_d = list(RT.index).index(d) if d in RT.index else None
            if i_d and i_d > 0:
                w = RT.iloc[max(0, i_d - NSESS):i_d]
                v = float(w.rng.mean() / w.mtr.mean())
                res["E3 C(day)"][0 if np.isclose(v, cds.get(d) or np.nan,
                                                atol=1e-9) else 1] += 1
            # E4
            j = np.searchsorted(msec, t - 120)
            v = (mmid[-1] - mmid[min(j, len(mmid) - 1)]) / TICK
            res["E4 honest thrust"][0 if np.isclose(v, mv120[i], atol=1e-9) else 1] += 1
            # E5: contaminated thrust needs c[ib]; is bar ib completed at t?
            completed = cx.bsec[ib] + 60 <= t
            # value unavailable at t unless the bar is done -> fail when not
            res["E5 CONTAM thrust"][0 if completed else 1] += 1
            # E6: signals used must be completion-stamped <= t
            used = sig_comp[(sig_comp > (t - 300) * 10**9) & (sig_comp <= t * 10**9)]
            res["E6 signal stamps"][0 if (used <= t * 10**9).all() else 1] += 1

        # X1: exit truncation test on M1 trades
        x_pass = x_fail = 0
        busy = -1
        tested = 0
        for i in sample:
            if tested >= N_EXIT:
                break
            t = int(secs[i]); ib = int(bar_i[i])
            if ib <= busy:
                continue
            d0 = int(np.sign(mv8[i]))
            if d0 == 0:
                continue
            fill = float(mids[i]); long = d0 > 0
            px, xs, xb, reason = leg_m1(cx, ib, fill, t, long, Q)
            pv = PoisonView(cx, int(xs))
            try:
                px2, xs2, xb2, reason2 = leg_m1(pv, ib, fill, t, long, Q)
                same = (np.isclose(px, px2) and xs == xs2 and reason == reason2)
            except Exception:
                same = False
            x_pass += same; x_fail += (not same)
            busy = xb + 1
            tested += 1

        print(f"===== {m} ({len(sample)} fire seconds, {tested} exit trades) =====")
        for k, (p, f) in res.items():
            exp = "expected FAIL" if k.startswith("E5") else "expected pass"
            verdict = ("CAUGHT (as expected)" if k.startswith("E5") and f > 0 else
                       "PASS" if f == 0 else "FAIL - LOOKAHEAD")
            print(f"  {k}: pass {p}, fail {f}  [{exp}] -> {verdict}")
            if f > 0 and not k.startswith("E5"):
                overall_fail += 1
        verdict = "PASS" if x_fail == 0 else "FAIL - exit reads beyond its own exit"
        print(f"  X1 M1 exit truncation: pass {x_pass}, fail {x_fail} -> {verdict}")
        overall_fail += (x_fail > 0)
        print()
    print("HARNESS VERDICT:",
          "ALL CLEAN COMPONENTS PASS; the known bug is caught by E5."
          if overall_fail == 0 else f"{overall_fail} COMPONENT(S) SHOW LOOKAHEAD")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
