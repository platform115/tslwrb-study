# B4 REPORT — STRATEGY 4 x M3 JOINT UNIT TEST (T-BS05)
STATUS: CLOSED | 2026-11-25 | Spec: B4_SPEC.md (committed first) | harness: fills from the certified B2 scan; exits forward walks

HIS G2, same periods: 62 trades | 74% win | +262.8 / -31.5 | net +231.2 | +5.71 / -1.97 | worst -3.75 | (per month: 22-02 +85.5 on 40; 25-10 +145.8 on 22)

## SUMMARY — ALL 12 COMBOS (pooled over both months)
| combo | trades | win | net (22-02 / 25-10) | avg win/loss | worst | max MAE | max DD | caught /62 | extras | extras net |
|---|---|---|---|---|---|---|---|---|---|---|
| 4A d1.25 x M3A | 473 | 44% | +135.8 (+55.1 / +80.6) | +2.72 / -1.65 | -3.75 | 5.62 | 35.1 | 39 | 406 | +47.0 |
| 4A d2.5 x M3C | 381 | 43% | +125.5 (+34.0 / +91.5) | +3.95 / -2.38 | -3.75 | 7.88 | 48.8 | 47 | 301 | +105.5 |
| 4A d1.25 x M3C | 434 | 41% | +94.4 (+69.8 / +24.6) | +3.92 / -2.38 | -3.75 | 5.88 | 47.9 | 37 | 361 | +88.4 |
| 4B d1.25 x M3A | 287 | 44% | +61.8 (+9.9 / +51.9) | +2.78 / -1.76 | -3.75 | 5.62 | 34.6 | 38 | 237 | +1.2 |
| 4A d1.25 x M3B | 421 | 41% | +52.8 (+17.4 / +35.4) | +3.22 / -2.01 | -3.75 | 5.62 | 61.4 | 37 | 360 | +9.0 |
| 4A d2.5 x M3A | 396 | 42% | +44.4 (-8.5 / +52.9) | +2.84 / -1.83 | -3.75 | 7.88 | 56.8 | 47 | 319 | -15.2 |
| 4B d1.25 x M3C | 258 | 42% | +43.6 (+29.2 / +14.4) | +3.87 / -2.49 | -3.75 | 5.62 | 51.8 | 35 | 209 | +46.6 |
| 4B d2.5 x M3C | 214 | 42% | +38.4 (+28.8 / +9.6) | +3.85 / -2.43 | -3.75 | 7.88 | 51.8 | 38 | 166 | +29.6 |
| 4B d2.5 x M3A | 215 | 41% | +28.8 (+14.5 / +14.2) | +3.04 / -1.92 | -3.75 | 7.88 | 37.2 | 38 | 169 | -21.9 |
| 4B d1.25 x M3B | 272 | 42% | +14.0 (-9.1 / +23.1) | +3.09 / -2.10 | -3.75 | 5.62 | 46.8 | 36 | 227 | -33.0 |
| 4B d2.5 x M3B | 208 | 41% | -12.8 (+8.0 / -20.8) | +3.37 / -2.43 | -3.75 | 7.88 | 41.4 | 37 | 164 | -45.6 |
| 4A d2.5 x M3B | 368 | 41% | -17.2 (-3.0 / -14.2) | +3.17 / -2.31 | -3.75 | 7.88 | 56.5 | 46 | 298 | -51.9 |

## WINNER RULE (pre-stated: positive BOTH months AND extras net >= 0; highest pooled net)
WINNER: 4A d1.25 x M3A - pooled +135.8, months +55.1 / +80.6, caught 39/62, extras net +47.0.
Qualifying combos: 7 of 12.

Footer: fills = certified B2 scan (mid-cross stop orders); single position; fees ~0 per J; regime = training months only; 2024-11 untouched. Registry: T-BS05.
