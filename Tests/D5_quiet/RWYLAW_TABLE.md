# RWYLAW_TABLE — THE RUNWAY LAW, BY MONTH (T-EN117 appendix)
STATUS: CLOSED | 2026-11-27 | every pair: baseline vs the
frozen [2,8] gate; n / net / per-trade per month. Sources:
T-SR05 (5W pair, banked parquets) + T-EN117 cells (re-run,
controls previously exact).

## 5W full-RTH (surgical, depth months) — T-SR05
| month | base n | base net | base pt | RWY n | RWY net | RWY pt | pt ratio |
|---|---|---|---|---|---|---|---|
| 2022-02 | 385 | +194.6 | +0.51 | 49 | +78.9 | +1.61 | 3.2x |
| 2025-10 | 365 | +277.5 | +0.76 | 53 | +78.2 | +1.48 | 1.9x |
| POOLED | 750 | +472.1 | +0.63 | 102 | +157.1 | +1.54 | 2.4x |

## G3-2 (quiet x M9) — T-EN117
| month | base n | base net | base pt | RWY n | RWY net | RWY pt | pt ratio |
|---|---|---|---|---|---|---|---|
| 2021-09 | 2822 | +470.1 | +0.17 | 404 | +60.0 | +0.15 | 0.9x |
| 2022-02 | 5332 | +1720.5 | +0.32 | 1076 | +750.4 | +0.70 | 2.2x |
| 2023-05 | 3763 | +833.4 | +0.22 | 460 | +174.0 | +0.38 | 1.7x |
| 2024-05 | 3442 | +628.2 | +0.18 | 356 | +209.0 | +0.59 | 3.2x |
| 2024-11 | 3528 | +767.9 | +0.22 | 527 | +151.9 | +0.29 | 1.3x |
| 2025-10 | 5054 | +1307.6 | +0.26 | 1020 | +599.1 | +0.59 | 2.3x |
| POOLED | 23941 | +5727.8 | +0.24 | 3843 | +1944.4 | +0.51 | 2.1x |

## G3-1 (quiet x M7) — T-EN117
| month | base n | base net | base pt | RWY n | RWY net | RWY pt | pt ratio |
|---|---|---|---|---|---|---|---|
| 2021-09 | 2320 | +356.6 | +0.15 | 363 | -5.8 | -0.02 | -0.1x |
| 2022-02 | 3567 | +951.9 | +0.27 | 817 | +486.5 | +0.60 | 2.2x |
| 2023-05 | 3337 | +593.0 | +0.18 | 427 | +149.4 | +0.35 | 2.0x |
| 2024-05 | 3108 | +432.5 | +0.14 | 326 | +112.8 | +0.35 | 2.5x |
| 2024-11 | 2931 | +528.2 | +0.18 | 470 | +122.2 | +0.26 | 1.4x |
| 2025-10 | 3745 | +827.1 | +0.22 | 756 | +321.2 | +0.42 | 1.9x |
| POOLED | 19008 | +3689.4 | +0.19 | 3159 | +1186.4 | +0.38 | 1.9x |

## G2-6 (news x M7) — T-EN117
| month | base n | base net | base pt | RWY n | RWY net | RWY pt | pt ratio |
|---|---|---|---|---|---|---|---|
| 2021-09 | 808 | +172.9 | +0.21 | 156 | +79.4 | +0.51 | 2.4x |
| 2022-02 | 959 | +324.2 | +0.34 | 257 | +112.1 | +0.44 | 1.3x |
| 2023-05 | 986 | +372.1 | +0.38 | 131 | +73.8 | +0.56 | 1.5x |
| 2024-05 | 1142 | +219.0 | +0.19 | 151 | +101.2 | +0.67 | 3.5x |
| 2024-11 | 1006 | +230.8 | +0.23 | 199 | +66.4 | +0.33 | 1.5x |
| 2025-10 | 1351 | +340.0 | +0.25 | 318 | +194.4 | +0.61 | 2.4x |
| POOLED | 6252 | +1659.0 | +0.27 | 1212 | +627.2 | +0.52 | 2.0x |

NOTE (fill-vs-cross gating, quantified): cross-to-fill delay
on certified G2-4 trades is median 99s, q90 367s - 61% of
fills are >60s after the cross, so edge sets CAN change in
between. The tested gate evaluates runway AT THE FILL SECOND,
which a live Python runner replicates exactly (re-evaluate
each second, pull the pending order when out of band). Pine
can only approximate at bar granularity. No lookahead either
way; the stated limitation is Pine fidelity, not causality.
