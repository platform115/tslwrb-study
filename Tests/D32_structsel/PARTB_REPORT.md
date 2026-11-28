# PARTB REPORT — THE 3s BOOK READ, FULL UNIVERSE + RWY STACK (T-SR06)
STATUS: CLOSED | 2026-11-28 | Spec: PARTB_SPEC.md (frozen first) | extraction cert bit-exact (691 x 4 features, 0 mismatch) | controls exact (750/+472.1; 109/+101.6 post-F-36) | T2 frozen from T-SR01 universe | coverage 1264/1264

| cell | touches | trades | win | per-trade | pooled | by month (22-02/25-10) | stops |
|---|---|---|---|---|---|---|---|
| 5W-ANY (baseline) | 1264 | 750 | 47% | +0.63 | +472.1 | +195/+278 | 47% |
| 5W-ACTIVE | 538 | 365 | 44% | +0.58 | +213.4 | +70/+144 | 53% |
| RWY-ANY (baseline) | 179 | 109 | 51% | +0.93 | +101.6 | +49/+52 | 42% |
| RWY-ACTIVE | 86 | 58 | 50% | +1.38 | +79.9 | +39/+40 | 43% |

## VERDICT vs THE FROZEN LINES
- 5W-ACTIVE per-trade > +0.63 AND both months positive: FAIL (+0.58; months +70/+144)
- RWY-ACTIVE per-trade > +1.54 (FROZEN, pre-F-36) AND n >= 40 AND both months positive: FAIL (+1.38, n=58)
- RWY-ACTIVE vs the CORRECTED baseline +0.93 (post-F-36 reference, not a frozen line): ABOVE
OVERALL: facts to J (the RWY-ACTIVE frozen line predates F-36; registration shape is J's gate).

Registry: T-SR06.
