# S5 — RESOLVER + HIT-RATE DASHBOARD (T-IM26)
> Status: AWAITING REVIEW. Script: `p6_19_s5_resolver.py`.

## A. Tolerance schedule (356 price-anchored refs, adopted selections)
| kind | n | ≤3 | ≤2 | ≤1.5 | ≤1 |
|---|---|---|---|---|---|
| shadow_interval | 70 | 97% | 96% | 96% | 96% |
| hidden_gap | 65 | 94% | 89% | 89% | 86% |
| reaction_hl | 59 | 64% | 51% | 42% | 32% |
| contraction | 104 | 60% | 53% | 51% | 49% |
| tight_range | 26 | 54% | 54% | 46% | 42% |
| trading_range | 19 | 47% | 47% | 42% | 37% |

TOLERANCE RECOMMENDATION (the charter's narrowing schedule, measured):
- hidden gaps and shadows: NARROW TO 1 PT now (86–96% hold).
- reaction levels: STAY AT 3 (precise levels degrade with tolerance —
  64% → 32%; narrowing waits for the S6 behavioral evidence).
- contraction family: STAY AT 3 (weakest kind; ~half resolve).
Caveat: band kinds count inside-band as distance 0, which is cheap for
wide bands — the S3 fair nulls remain the honesty reference; this table is
the RESOLUTION schedule, not fresh evidence of edge.

## A2. Stability across years
No era collapse: shadows 97–100% every year (83% in 2026, n=6), gaps
85–100% (one n=2 cell at 50%), reaction 62–75% except an n=2 2023 cell.
Contraction family swings 38–75% with small yearly n — consistent with it
being the weakest generator, not a regime artifact.

## B. Key-zone maintained-list reconstruction (forward prediction)
List built ONLY from prices he stated earlier (53 events, ±3 band,
expiry grid): his later UNPRICED relational Key-zone refs land on-list
7–10% vs null 3–5% (gap +4–5 pts; ~2x ratio).
HONEST READING: the quoted levels ARE disproportionately where his later
zone talk lands (2x null), but 53 stated prices over 5 years cannot cover
743 references — he rarely quotes numbers, so reconstruction from stated
prices alone is INSUFFICIENT. The Key-zone list must be GENERATED from
data (which generator + KME anchoring + his tier semantics) — this is the
single biggest open problem the structure program hands to S6, and the
stated-price clusters remain the validation set for whatever generates it.

## Resolver state handed to S6
resolve(t) per kind = adopted generator + selection at its recommended
tolerance; Key-zone channel = stated-price list (partial, validation-grade)
until a generated list passes against it.
