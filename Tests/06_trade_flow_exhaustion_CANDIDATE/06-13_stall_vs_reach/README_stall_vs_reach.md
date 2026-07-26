# Stall-vs-Reach phase — operational README
Question: among NON-losers, predict EARLY which trades REACH WRB pt1 (47) vs STALL short (29).
Population settled deterministically (build_groups): 92 Oct-2025 ESZ5 episodes = 47 reach + 29 stall +
16 losers (excluded; incl 5 reached-pt1-then-lost -> reach is 47 not 52). Forward/movement probes use
SURVIVORS-only (hold>=tau): tau=60 -> 45 reach / 24 stall.

IMPORT NOTE (why this is one folder, not many): the scripts are import-coupled and all import the shared
spine (trade_flow_exhaustion, horse_race_spine) which stays at the phase ROOT. Run from the root:
    PYTHONPATH=. python3 06-13_stall_vs_reach/<script>.py --config config.toml --wrb wrb_1m.parquet

Families (recreation specs): SR-A exit microstructure (null) · SR-B forward/structure (null + weak
hurst) · SR-C continuous-outcome (lead withdrawn as artifact) · SR-D price-movement (velocity_ratio
candidate). Full record: STALL_VS_REACH_FINDINGS.md.

FINAL DISPOSITION: one surviving candidate, velocity_ratio @ tau=60 (AUC 0.660, robust, modest,
normalization-dependent, uncorroborated by shape). Everything else null/artifact. The reach-vs-stall
boundary is, at this n and resolution, only weakly recoverable — consistent with a largely discretionary
cut/hold decision.
