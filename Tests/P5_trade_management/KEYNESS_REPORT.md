# KEY-NESS STUDY (T-IM49)
STATUS: CLOSED | 2026-11-25 | Spec: KEYNESS_SPEC.md (committed first)

Objects: key-linked 3641, non-key-mentioned 3374, matched random 10923 (price-walk samples 800 each).

## PROPERTY DIFFERENCES (all price-computable live)
| property | key q50 | non-key q50 | random q50 | key-vs-random diff |
|---|---|---|---|---|
| width | 3.25 | 3.38 | 1.50 | +0.29 |
| touches6h | 5.00 | 6.00 | 15.00 | -0.39 |
| survive_h | 0.02 | 0.03 | 0.17 | -0.65 |
| formed in news window | 19% | 24% | 12% | - |
| round-number | 6% | 7% | 6% | - |
| timeframe mix | {1: np.float64(0.41), 5: np.float64(0.24), 2: np.float64(0.12), 15: np.float64(0.12), 3: np.float64(0.11)} | {1: np.float64(0.33), 5: np.float64(0.23), 3: np.float64(0.15), 15: np.float64(0.15), 2: np.float64(0.14)} | {1: np.float64(0.45), 5: np.float64(0.21), 2: np.float64(0.15), 3: np.float64(0.11), 15: np.float64(0.08)} | - |
| generator mix | {'g2_shadow_d2': np.float64(0.21), 'g1_whg': np.float64(0.21), 'g2_shadow_d1': np.float64(0.21), 'g3_swing': np.float64(0.2), 'g4_c2': np.float64(0.19)} | {'g2_shadow_d2': np.float64(0.28), 'g2_shadow_d1': np.float64(0.26), 'g1_whg': np.float64(0.18), 'g3_swing': np.float64(0.15), 'g4_c2': np.float64(0.12)} | (matched) | - |

STUDY-ONLY (barred from shipping): mentions per key object q50 = 1 vs non-key 1

## DRAFT RULE: written in the summary from the table above, for J's review before any stage-1 retest.
Registry: T-IM49.

## ANALYSIS APPENDED (same day): A SELECTION CONFOUND, CAUGHT
The striking numbers (key objects "die" in ~72s, fewer touches) are NOT
intrinsic properties - they are MENTION-TIMING artifacts: he mentions an
object when price is engaging it, so price promptly moves around it;
random objects include far-from-price ones nothing visits. Survival and
touch counts here measure WHEN HE TALKS, not what makes a level key.
These two rows are therefore DISCARDED as evidence.
What survives the confound (weak but real): key objects are WIDER
(3.25 vs 1.50 median), skew to HIGHER timeframes, are 1.6x likelier to
have FORMED inside a news window, and overweight gaps/swings vs shadows.
None of this separates strongly enough for a shippable rule.
## THE REDESIGN THIS FORCES
His "key" zones, per the closed S4 evidence, live WEEKS TO MONTHS -
they are MULTI-DAY PRICE LEVELS, not the intraday objects this study
sampled (the link table attaches his words to nearby intraday
structures - the wrong population for key-ness). The computable
candidate is therefore a MULTI-DAY LEVEL DETECTOR: prices where the
market has repeatedly halted/reversed across trailing days (daily
reaction-price clustering - deterministic, price-only, live-computable).
This is also the long-parked "Key-zone generated list" backlog item,
now with a concrete design. It awaits J's go as a detector-layer build.
