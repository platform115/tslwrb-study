# G31 REPORT — G3-1: THE QUIET-MARKET CYCLE (T-EN116)
STATUS: CLOSED | 2026-11-27 | Spec: G31_SPEC.md (frozen first) | R-9 dual controls exact (engine set-equal on 2022-02; G2-6 sim 6252/+1659.0) | six months | TRAINING-ONLY

| cell | trades | per-trade | pooled | by month (21-09/22-02/23-05/24-05/24-11/25-10) | catch-G3 | extras |
|---|---|---|---|---|---|---|
| G2-6 (news windows, ref) | 6252 | +0.27 | +1659.0 | +173/+324/+372/+219/+231/+340 | 5/151 | +1638.8 |
| G3-1 x M7 | 19008 | +0.19 | +3689.4 | +357/+952/+593/+432/+528/+827 | 150/151 | +3262.4 |
| G3-1 x M9 (secondary) | 23941 | +0.24 | +5727.8 | +470/+1720/+833/+628/+768/+1308 | 150/151 | +5241.1 |

## PER-FAMILY (G3-1 x M7; first-family tag, shared busy)
| family | trades | net | per-trade | months net<0 |
|---|---|---|---|---|
| GAP | 7124 | +1129.8 | +0.16 | 0/6 |
| PDY | 108 | -25.6 | -0.24 | 4/6 TOXIC-FLAG |
| REA | 299 | +81.6 | +0.27 | 1/6 |
| SHD | 5738 | +1357.0 | +0.24 | 0/6 |
| SQZ | 1508 | +141.5 | +0.09 | 1/6 |
| W20 | 677 | +58.8 | +0.09 | 2/6 |
| WRB | 3554 | +946.4 | +0.27 | 0/6 |

## VERDICT vs THE FROZEN LINES (G3-1 x M7)
- controls exact: PASS
- catch >= 60% of his G3 set: PASS (150/151)
- pooled > 0, no month < -10: PASS (+3689.4; worst +356.6)
- extras >= 0: PASS (+3262.4)
- per-trade >= +0.20: FAIL (+0.19)
- no unflagged toxic family: FLAGGED
OVERALL: PARTIAL - facts to J

Registry: T-EN116.
