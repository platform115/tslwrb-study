# M10 REPORT — HIS-EXIT IMMINENCE (T-MG17)
STATUS: CLOSED | 2026-11-26 | Spec: M10_SPEC.md (committed first)

States: 56,491 from 296 of his audited trades; exit-imminent (<=30s): 8% base rate.

## HELD-OUT AUC: 0.814 (verdict lines: >=0.65 predictable | 0.55-0.65 weak | <0.55 in-data exhaustion earned)

Importance (held-out):
- t: 0.1502
- vol30: 0.0314
- peak: 0.0123
- give_back: 0.0085
- vol_fade: 0.0064
- slope30: 0.0052
- mins_since_ev: 0.0046

## PLAIN CELLS (share of states that are exit-imminent | base rate = overall)
(base rate 8%)
- vol_fade < 0.5 (volume died from peak): n=13,616 | imminent 3% | per-trade 33%
- vol_fade > 1.5 (volume building): n=2,618 | imminent 6% | per-trade 29%
- flow30 < -50 (flow against): n=18,242 | imminent 10% | per-trade 60%
- flow30 > +50 (flow with): n=22,027 | imminent 8% | per-trade 50%
- at a level ahead < 1: n=3,617 | imminent 11% | per-trade 56%
- give_back < 0.5 & exc >= 2 (winning at peak): n=7,758 | imminent 13% | per-trade 50%
- slope30 < -1 (fading): n=7,547 | imminent 19% | per-trade 59%

Registry: T-MG17. m10_states.parquet saved.

## ABLATION (the checklist's selection-effect line, run before verdict)
AUC with time-in-trade alone: 0.805. All features without it: 0.766.
Full model: 0.814 - everything beyond his clock adds +0.009.
VERDICT: his exit timing is dominated by an internal duration clock,
already replicated by M7's time elements (why refinements plateau at
~63%). His residual edge = rare deviations from his own clock - not
predictable from path/clock/levels/volume/flow (fifth independent
null: A5, SEL, M8, M9, M10). IN-DATA EXHAUSTION EARNED. The switch
question waits on MBP-10 (standing trigger) and cross-market data. No
extraction round: it would rediscover time stops we already ship.
