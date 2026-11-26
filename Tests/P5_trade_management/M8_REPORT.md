# M8 DISCOVERY — HOLD-OR-SELL STATES (T-MG15)
STATUS: CLOSED | 2026-11-26 | Spec: M8_SPEC.md (committed first)

State-seconds: 325,580 (every 5th second) from 775 trades (18,526 from his 62 trades).
Base rates: mean fut120 = -0.017, mean fut300 = -0.020 (the drift a policy must beat).

## RANKING for fut120 (held-out, session-grouped; 60k subsample)
- mins_since_ev: 0.0155
- slope30: 0.0038
- give_back: 0.0035
- slope10: 0.0003
- t: -0.0024

## RANKING for fut300 (held-out, session-grouped; 60k subsample)
- mins_since_ev: 0.0518
- t: 0.0049
- peak: 0.0028
- slope30: 0.0009
- slope10: -0.0007

## PLAIN EVIDENCE — continuation by state (mean fut120 per-second | per-trade-averaged)
- give_back < 0.5 (at/near peak): n=32,989 | per-sec -0.293 | per-trade -1.331
- give_back 0.5-1.5: n=43,068 | per-sec -0.079 | per-trade -0.897
- give_back >= 1.5 (deep off peak): n=249,523 | per-sec +0.031 | per-trade +0.151
- slope30 > +1 (accelerating): n=69,014 | per-sec -0.167 | per-trade -0.300
- slope30 < -1 (fading): n=69,724 | per-sec +0.110 | per-trade +0.237
- room_ahead < 1 (at a level): n=22,677 | per-sec -0.188 | per-trade -0.173
- room_ahead 1-4: n=93,722 | per-sec -0.098 | per-trade -0.122
- room_ahead >= 4 (open air): n=209,181 | per-sec +0.038 | per-trade +0.025
- exc >= 2 & give_back < 0.5 (winning, at peak): n=23,788 | per-sec -0.363 | per-trade -1.550
- exc >= 2 & give_back >= 1.5 (winning, fading): n=71,818 | per-sec -0.004 | per-trade -0.862
- exc <= -1.5 (losing): n=125,218 | per-sec +0.034 | per-trade +1.356
- t > 300s (old trade): n=261,244 | per-sec -0.015 | per-trade -0.015

REVIEW GATE: J sees this before any policy extraction (step 4).
Registry: T-MG15. m8_states.parquet saved.
