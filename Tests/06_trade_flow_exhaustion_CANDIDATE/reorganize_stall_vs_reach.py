#!/usr/bin/env python3
"""
reorganize_stall_vs_reach.py — declutter the phase root WITHOUT breaking the import web
========================================================================================
The stall-vs-reach scripts are import-coupled (velocity_* -> range_expansion -> ... -> forward_battery,
and all -> trade_flow_exhaustion + horse_race_spine). Scattering them one-folder-per-probe (the older
pattern) would break `import range_expansion` etc. So:

  * SHARED SPINE stays at root (imported across the whole 06 tree): trade_flow_exhaustion.py,
    trade_flow_exhaustion_round2.py, horse_race_spine.py, config.toml, wrb_1m.parquet, *_results.csv.
  * ENTIRE stall-vs-reach phase -> ONE folder (PHASE_DIR), so every intra-phase import still resolves
    (they all sit together; the spine is found via PYTHONPATH=. at run time).
  * Per-FAMILY recreation SPECs written into PHASE_DIR (matching the existing one-SPEC-per-few-scripts
    granularity). Umbrella findings doc moved alongside.
  * __pycache__ removed (regenerated on next run).

POST-MOVE RUN COMMAND (from the phase root):
    PYTHONPATH=. python3 PHASE_DIR/velocity_ratio_sweep.py --config config.toml --wrb wrb_1m.parquet
  (Python auto-adds the script's own dir to sys.path -> intra-phase imports resolve; PYTHONPATH=. adds
   root -> spine resolves; cwd=root -> config.toml/SSD paths resolve exactly as before.)

SAFE BY DEFAULT: prints the plan and changes nothing. Re-run with --apply to execute. Uses `git mv`
when inside a git work tree (preserves history), else shutil.move. Never overwrites an existing dest;
never moves the spine; only removes __pycache__ when --clean-pycache is passed.

    python3 reorganize_stall_vs_reach.py                 # dry-run (plan only)
    python3 reorganize_stall_vs_reach.py --apply --clean-pycache
"""

import argparse
import os
import shutil
import subprocess

PHASE_DIR = "06-13_stall_vs_reach"   # rename here if 06-13 collides with loser_submodes in your tree

# phase scripts -> PHASE_DIR (kept together so intra-phase imports resolve)
PHASE_SCRIPTS = [
    "forward_battery.py", "forward_sweep.py", "structure_family.py",
    "continuous_outcome.py", "speed_leads_robustness.py",
    "sign_persistence.py", "sign_persistence_dfa.py", "intensity.py", "impact.py", "efficiency_ratio.py",
    "range_expansion.py", "velocity_acceleration.py", "velocity_ratio_confirm.py",
    "velocity_ratio_sweep.py", "variance_ratio.py",
    "exit_velocity.py", "give_back.py", "stagnation.py", "exit_reversal.py",
]
PHASE_DOCS = ["STALL_VS_REACH_FINDINGS.md"]            # umbrella findings -> PHASE_DIR
OTHER_MOVES = {"SPEC_06-12_combined_rule.md": "06-12_combined_rule"}   # loose root spec -> its folder

# never move these (shared spine / data / config / candidate specs the whole tree depends on)
SPINE_KEEP = {
    "trade_flow_exhaustion.py", "trade_flow_exhaustion_round2.py", "horse_race_spine.py",
    "config.toml", "wrb_1m.parquet",
    "trade_flow_exhaustion_results.csv", "trade_flow_exhaustion_round2_results.csv",
    "FROZEN_in_trade_flow_exhaustion_HOLDOUT_spec.md",
    "reorganize_06.py", "reorganize_stall_vs_reach.py",
}

# ---- per-family recreation specs (written into PHASE_DIR) ----
SPECS = {
"SPEC_SR-A_exit_microstructure.md": """# SPEC SR-A — exit-anchored microstructure (stall vs reach)  [STATUS: NULL]
Population: 47 target_reached vs 29 below_target_win (non-losers; 16 losers excluded incl 5 reached-then-lost).
Design: (b) exit-anchored, matched-elapsed; per-cut AUC + cluster bootstrap over 29 stall cuts; W=60s.
Question: does the trade's order-flow character near the EXIT separate stalls from reaches?

Scripts & features:
  sign_persistence.py      rho1 (lag-1 oriented trade-sign autocorrelation)
  sign_persistence_dfa.py  Hurst of sign series via DFA-1 (Lillo & Farmer long-memory)
  intensity.py             trades/sec LEVEL and within-window arrival-rate SLOPE
  impact.py                |net mid move|/trade (Amihud illiquidity, Kyle lambda)
  efficiency_ratio.py      Kaufman efficiency ratio on per-second mid (path shape)

Result (all NULL): rho1 0.542 · hurst 0.562 · flow_level 0.522 · intensity_slope 0.545 ·
  impact 0.529 · efficiency_ratio 0.477. intensity_LEVEL separated (0.244 / two-sided 0.756) but is
  PEEKED (direction taken from a diagnostic) + time-of-day/volatility-regime confounded (stalls cluster
  at the open) and is NOT absorption (stalls have ~2x trades AND ~2x net move) -> NOT a candidate.
Disposition: exit-anchored microstructure is the wrong frame for EARLY prediction; retired.
Run: PYTHONPATH=. python3 %s/sign_persistence.py --config config.toml --wrb wrb_1m.parquet
""" % PHASE_DIR,

"SPEC_SR-B_forward_structure.md": """# SPEC SR-B — entry-forward & structure family  [STATUS: NULL / one marginal-and-inverting lead]
Population: 47 reach / 29 stall. Design: (c) entry-anchored FORWARD, SURVIVORS-only (hold>=tau), pooled
two-sample bootstrap (seed 0, 10000). 120s-survivors = pre-registered primary (stall n=13).

Scripts:
  forward_battery.py   entry-forward tau=30s pooled battery (also the shared lib: build_arms,
                       read_trade_full, window_features, two_sample_boot_ci) -> all straddle 0.5
  forward_sweep.py     window sweep 60/120/180/300, capped vs survivors-only control. hurst CLEARS only
                       at 120s survivors (0.657 [0.507,0.795]); capped-pooled clears at W>=120 are the
                       whole-life-capping ARTIFACT (collapse in survivors), not signal.
  structure_family.py  flow_consistency (NEW: Kaufman ER on cumulative signed flow) 0.612 [0.435,0.782]
                       leaner, no clear; hurst 0.657 clears; impact 0.531 FLAT -> magnitude family CLOSED.

Disposition: hurst is the only leakage-free clear (weak: LB 0.507, n=13) and is reach>stall across all
8 reads (mean 0.600) BUT inverts vs MFE later (SR-C) -> treated as weak, not carried. flow_consistency
corroborates the persistence axis, not independent. Magnitude family closed.
Run: PYTHONPATH=. python3 %s/structure_family.py --config config.toml --wrb wrb_1m.parquet
""" % PHASE_DIR,

"SPEC_SR-C_continuous_outcome.md": """# SPEC SR-C — continuous-outcome reframe  [STATUS: apparent lead WITHDRAWN as artifact]
Population: 47 reach / 29 stall. Idea: the binary pt1 threshold may hide GRADED signal. Outcomes:
MFE (ticks, how far) all 76; time_to_pt1 (how fast) reaches only. Spearman + bootstrap CI (seed 0).

Scripts:
  continuous_outcome.py     early-30s features vs MFE and vs time_to_pt1. APPARENT find: flow_level
                            -0.46 [-0.64,-0.23], ER_abs -0.36 [-0.58,-0.09] vs time_to_pt1 (stronger
                            early flow -> faster to pt1). Also rho1 -0.27 vs MFE (WRONG sign vs pre-reg),
                            intensity +0.27 vs MFE (volatility confound), hurst -0.18 (inverts).
  speed_leads_robustness.py tau-robustness + distance partial. KILLED the flow_level/ER lead: pt1 lands
                            AT/BEFORE entry for ~half of reaches (pt1_open_el median 49s, p25 -14s), so
                            the tau=30 window overlapped/post-dated pt1 -> LOOK-AHEAD. On the clean
                            subset (pt1_open_el>=tau) the effect vanishes (flow_level +0.26/+0.40/+0.12,
                            all CIs straddle 0). Distance was NOT the confound (rho time_to_pt1,distance
                            = -0.06). Partial(flow_level,time_to_pt1|distance) +0.24, null.

Disposition: the speed-to-pt1 lead is a window-contamination ARTIFACT and is WITHDRAWN. time_to_pt1 is
not a trustworthy outcome (pt1 timing relative to entry). Use the BINARY label downstream (SR-D).
Run: PYTHONPATH=. python3 %s/continuous_outcome.py --config config.toml --wrb wrb_1m.parquet
""" % PHASE_DIR,

"SPEC_SR-D_price_movement.md": """# SPEC SR-D — price-movement vein  [STATUS: ONE surviving candidate = velocity_ratio @ tau=60]
Motivation: the trader's own account is that MOVEMENT/SPEED of price action drives cut/hold. Order-flow
was null; this vein tests PRICE-domain movement. Outcome: BINARY reach (47) vs stall (29), survivors-only,
two-sample bootstrap (seed 0). tau=60 primary.

Scripts:
  range_expansion.py        expansion_ratio = range[entry,entry+tau]/range[entry-tau,entry]; within_accel.
                            expansion_ratio 0.594/0.598 LEANS reach>stall, CI through 0.5 (no clear).
  velocity_acceleration.py  velocity_ratio = per-second path-length(fwd)/path-length(pre), UNSIGNED (not
                            pt1-circular). *** CLEARS: tau=60 AUC 0.660 [0.522,0.788], reach>stall.***
                            acceleration null. tau=30 0.627 (CI grazes 0.5).
  velocity_ratio_confirm.py decomposition (stall frac<1.0 = 0.62 vs reach 0.44 -> stalls DECELERATE vs
                            own pre-entry pace) + jackknife (min 0.645, robust) + permutation (p=0.014).
  variance_ratio.py         Lo-MacKinlay VR (trend vs chop) as INDEPENDENT check. NULL/wrong-way (0.353
                            at 60, 0.540 at 30). Signal is SPEED, not trend-SHAPE; velocity_ratio stands
                            alone (uncorroborated).
  velocity_ratio_sweep.py   forward-window sweep keeping fixed-60s pre-norm: norm_ratio 0.660/0.660/0.629
                            at 60/90/120 -> STABLE, not growing (a ~60s onset effect). raw (un-normalised)
                            fwd 0.42/0.46/0.49 -> wrong-way/null: the signal lives ENTIRELY in the
                            pre-entry normalization (volatility control essential).

Disposition: velocity_ratio @ tau=60 is the study's ONE surviving candidate: AUC 0.660, jackknife-robust,
permutation-real, mechanism = stallers decelerate vs their pre-entry pace. Caveats: single feature,
NORMALIZATION-dependent (no raw effect), UNCORROBORATED by shape, n=47/24, one trader / one month,
in-sample. Freeze as the tau=60 candidate for any future out-of-sample work.
Run: PYTHONPATH=. python3 %s/velocity_ratio_sweep.py --config config.toml --wrb wrb_1m.parquet
""" % PHASE_DIR,

"SPEC_SR-E_exit_window.md": """# SPEC SR-E — exit-window sweep (stall-bail trigger)  [STATUS: NO mechanical trigger -> DISCRETIONARY]
Population: 47 reach / 29 stall. Question: is there a consistent, mechanically-measurable price event
before a stall-bail (vs a target-exit)? Reframe: exit is the trader's own decision (endogenous) -> judge
on STALL-ARM TIGHTNESS (a consistent band = candidate rule), not group-separation AUC. Binary label,
per-second mid, rank AUC + two-sample bootstrap (seed 0).

Probes (B -> A -> D -> C):
  exit_velocity.py (B)  velocity death into exit. exit_decel NULL (0.514/0.535); exit_vel_norm clears
                        W30 0.637 but = the ENTRY velocity_ratio re-expressed, not an exit trigger.
  give_back.py (A)      give-back from MFE peak (Sweeney 1996). give_back_frac AUC 0.287 (stall>reach) but
                        CONSTRUCTION; stall band WIDE (IQR 0.60) -> no rule. time_since_mfe NULL 0.466.
  stagnation.py (D)     time-stop / deadweight time. no_progress_frac NULL 0.553; both arms ~0.93 (tight
                        at the SHARED value = trap, not a trigger). The least label-coupled probe -> clean null.
  exit_reversal.py (C)  adverse reversal. adverse_move 0.555/0.590, retrace_ticks 0.506/0.511 NULL; stall
                        retrace band WIDE (~6tk) -> no soft-stop.

Disposition: four hypotheses, four NO-trigger. The cut/hold of a stalling winner is NOT a univariate
threshold in the trade's own tape -> DISCRETIONARY (consistent with the trader never documenting a rule).
Pivot: the cause is CONTEXT the instrument's tape lacks -> (1) entry-determination [test first; builds on
velocity_ratio], (2) higher-TF/WRB structure (es_5m_front), (3) conditional/PRIM. Pre-commit a stop if
entry-context separates no better than this sweep did. Full detail: SPEC_SR-E_exit_window.md (standalone).
Run: PYTHONPATH=. python3 %s/exit_velocity.py --config config.toml --wrb wrb_1m.parquet
""" % PHASE_DIR,

"README_stall_vs_reach.md": """# Stall-vs-Reach phase — operational README
Question: among NON-losers, predict EARLY which trades REACH WRB pt1 (47) vs STALL short (29).
Population settled deterministically (build_groups): 92 Oct-2025 ESZ5 episodes = 47 reach + 29 stall +
16 losers (excluded; incl 5 reached-pt1-then-lost -> reach is 47 not 52). Forward/movement probes use
SURVIVORS-only (hold>=tau): tau=60 -> 45 reach / 24 stall.

IMPORT NOTE (why this is one folder, not many): the scripts are import-coupled and all import the shared
spine (trade_flow_exhaustion, horse_race_spine) which stays at the phase ROOT. Run from the root:
    PYTHONPATH=. python3 %s/<script>.py --config config.toml --wrb wrb_1m.parquet

Families (recreation specs): SR-A exit microstructure (null) · SR-B forward/structure (null + weak
hurst) · SR-C continuous-outcome (lead withdrawn as artifact) · SR-D price-movement (velocity_ratio
candidate) · SR-E exit-window sweep (B/A/D/C — no mechanical exit trigger). Full record:
STALL_VS_REACH_FINDINGS.md.

FINAL DISPOSITION: one surviving candidate, velocity_ratio @ tau=60 (AUC 0.660, robust, modest,
normalization-dependent, uncorroborated by shape). The exit-window sweep (SR-E) found NO consistent
mechanical trigger for the stall-bail across four trader's-eye hypotheses -> the cut/hold-a-winner
decision is DISCRETIONARY. Next vein: the discretionary cause is context the instrument's own tape lacks
(entry-determination / higher-TF & WRB structure / conditional gating), with a pre-committed stop rule.
The reach-vs-stall boundary is, at this n and resolution, only weakly recoverable from the tape itself.
""" % PHASE_DIR,
}


def in_git():
    try:
        return subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                              capture_output=True, text=True).stdout.strip() == "true"
    except FileNotFoundError:
        return False


def do_move(src, dest_dir, apply, git):
    if not os.path.exists(src):
        print(f"  SKIP (missing): {src}"); return
    os.path.join(dest_dir, os.path.basename(src))
    dest = os.path.join(dest_dir, os.path.basename(src))
    if os.path.exists(dest):
        print(f"  SKIP (dest exists): {dest}"); return
    print(f"  MOVE {src}  ->  {dest}")
    if apply:
        os.makedirs(dest_dir, exist_ok=True)
        if git and subprocess.run(["git", "mv", src, dest], capture_output=True).returncode == 0:
            return
        shutil.move(src, dest)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="execute (default: dry-run)")
    ap.add_argument("--clean-pycache", action="store_true", help="also remove __pycache__")
    a = ap.parse_args()
    git = in_git()
    mode = "APPLY" if a.apply else "DRY-RUN (nothing will change; re-run with --apply)"
    print(f"=== reorganize stall-vs-reach :: {mode} :: git={'yes' if git else 'no'} ===\n")

    print(f"[1] phase scripts -> {PHASE_DIR}/")
    for f in PHASE_SCRIPTS + PHASE_DOCS:
        do_move(f, PHASE_DIR, a.apply, git)

    print(f"\n[2] loose specs -> their folders")
    for f, d in OTHER_MOVES.items():
        do_move(f, d, a.apply, git)

    print(f"\n[3] write recreation specs into {PHASE_DIR}/")
    for name, body in SPECS.items():
        dest = os.path.join(PHASE_DIR, name)
        if os.path.exists(dest):
            print(f"  SKIP (exists): {dest}")
        else:
            print(f"  WRITE {dest}")
            if a.apply:
                os.makedirs(PHASE_DIR, exist_ok=True)
                open(dest, "w").write(body)

    print(f"\n[4] kept at root (shared spine / data / candidate specs): {', '.join(sorted(SPINE_KEEP))}")

    if a.clean_pycache:
        print("\n[5] remove __pycache__")
        if os.path.isdir("__pycache__"):
            print("  RM __pycache__/")
            if a.apply:
                shutil.rmtree("__pycache__")
    else:
        print("\n[5] __pycache__ left in place (pass --clean-pycache to remove)")

    print(f"\nPOST-MOVE RUN:  PYTHONPATH=. python3 {PHASE_DIR}/<script>.py --config config.toml --wrb wrb_1m.parquet")
    if not a.apply:
        print("\nDRY-RUN complete. Review the plan, then re-run with --apply (and --clean-pycache).")


if __name__ == "__main__":
    main()
