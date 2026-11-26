# EX2 REPORT — EXCURSION-MATCHED ROBUSTNESS CHECK (T-MG20)
STATUS: CLOSED | 2026-11-26 | Spec: EX2_SPEC.md (committed first)

Cases with book + mid + >=1 duration-AND-excursion-matched control: 275 (dropped: 8 no book, 0 no mid, 30 no excursion-matched control).

| feature | exit med | hold med | direction | perm p | verdict (alpha .0167 / .05) |
|---|---|---|---|---|---|
| imb10 | 0.005 | -0.020 | exit HIGHER | 0.0004 | SURVIVES |
| imb0 | 0.000 | -0.035 | exit HIGHER | 0.6462 | dies |
| depth_tot | 1155.000 | 1174.000 | exit HIGHER | 0.3952 | dies (month-inconsistent) |

Registry: T-MG20.

## READING
- imb10 SURVIVES with the price path controlled (275 cases, p=0.0004,
  both months): at the same duration AND the same open profit, the
  moments he exits show the deep book tilted toward his support side;
  the moments other trades keep holding do not. The price-extreme
  explanation is ruled out as the whole story. This is now the best-
  evidenced exit-side signal in the program: exit-into-liquidity.
- Its two neighbors die under the same control (imb0, depth_tot) -
  the signal is specifically the DEEP imbalance, not top-of-book.
- PRACTICAL FLAG for validation: the purchased months are tbbo +
  bbo-1s - TOP of book only. imb10 needs 10 levels, so an imb10 rule
  CANNOT be tested on the current purchase. Options: (a) extend the
  purchase to mbp-10 for 2023-05/2024-05 (cost), (b) carry the rule
  as training-evidenced only until MBP-10 validation data exists,
  (c) test a top-of-book proxy knowing imb0 did NOT survive (weak).
- Per the frozen line, the switch-rule backtest is now spec-able.
  Two candidate shapes for J to aim between (both vs M7, traded P&L
  the verdict): (a) STALL GATE - when M7's stall-60 fires, exit only
  if imb10 is support-tilted (liquidity to exit into); otherwise
  grant one 60s extension; (b) CLOCK EXTENSION - at the 480s cap,
  keep holding while imb10 (and Analysis B's sup0) stay supportive,
  re-checked each 60s, hard cap 900s.
