# XD REPORT — D-1 EXTRAS DECOMPOSITION (T-XD01)
STATUS: CLOSED | 2026-11-27 | Spec: XD_SPEC.md (committed first) | R-9 double control: training 757/+325.1 and validation 760/+158.1 both reproduced exactly | study only

Population: 1517 G2-4 trades over 4 months ({'2022-02': 353, '2023-05': 353, '2024-05': 407, '2025-10': 404}).

## 1. CONCENTRATION — WHERE THE NET LIVES
| month | net | top 10% share | top 25% share | % trades pnl>0 |
|---|---|---|---|---|
| 2022-02 | +137.6 | 181% | 293% | 48% |
| 2025-10 | +187.5 | 133% | 201% | 51% |
| 2023-05 | +118.8 | 130% | 211% | 54% |
| 2024-05 | +39.4 | 352% | 562% | 49% |
| POOLED | +483.2 | 169% | 263% | 50% |

EARNERS = top quartile pooled (pnl >= +1.38): 381 trades holding 263% of pooled net.

## 2. ENTRY-TIME FEATURES — EARNERS vs REST
(BH-FDR q=0.10 within family; FINDING also needs >=3/4 month direction consistency)
Correlated >0.9 (reported as one signal): lane~pre_exc; room_ahead~lvl_within8

| family | feature | earner med | rest med | p | BH | months same dir | verdict |
|---|---|---|---|---|---|---|---|
| F1 entry mechanics | lane | 1.00 | 1.00 | 0.2448 | n | 4/4 | null |
| F1 entry mechanics | edge_src | 0.00 | 0.00 | 0.0973 | n | 4/4 | null |
| F1 entry mechanics | band_width | 8.00 | 6.75 | 0.0000 | Y | 2/4 | suggestive |
| F1 entry mechanics | edge_dist_rel | 0.62 | -0.12 | 0.1975 | n | 2/4 | null |
| F1 entry mechanics | pre_exc | 0.00 | 0.00 | 0.3350 | n | 4/4 | null |
| F1 entry mechanics | cross_to_fill | 80.00 | 109.00 | 0.0001 | Y | 4/4 | FINDING |
| F1 entry mechanics | sig_idx | 10.00 | 10.00 | 0.4591 | n | 0/4 | null |
| F1 entry mechanics | trades_today | 10.00 | 10.00 | 0.4814 | n | 1/4 | null |
| F2 news context | tier20 | 0.00 | 0.00 | 0.0495 | Y | 4/4 | FINDING |
| F2 news context | tier45 | 0.00 | 0.00 | 0.0270 | Y | 4/4 | FINDING |
| F2 news context | mins_since_rel | 25.30 | 27.51 | 0.1654 | n | 4/4 | null |
| F2 news context | react5 | 3.00 | 2.25 | 0.0000 | Y | 4/4 | FINDING |
| F2 news context | range5 | 7.75 | 5.50 | 0.0000 | Y | 4/4 | FINDING |
| F2 news context | vol5 | 22073.00 | 17143.00 | 0.0000 | Y | 4/4 | FINDING |
| F2 news context | hour | 9.58 | 9.58 | 0.2222 | n | 2/4 | null |
| F2 news context | dow | 2.00 | 2.00 | 0.3439 | n | 4/4 | null |
| F3 levels | room_ahead | 4.50 | 6.00 | 0.0021 | Y | 4/4 | FINDING |
| F3 levels | lvl_within8 | 1.00 | 1.00 | 0.0053 | Y | 3/4 | FINDING |
| F3 levels | n_levels_10 | 3.00 | 2.00 | 0.0000 | Y | 2/4 | suggestive |
| F3 levels | room_behind | 4.50 | 5.50 | 0.0027 | Y | 3/4 | FINDING |
| F4 flow/book | flow30 | 163.00 | 165.00 | 0.7166 | n | 2/4 | null |
| F4 flow/book | flow120 | 173.00 | 185.00 | 0.4636 | n | 2/4 | null |
| F4 flow/book | vol30 | 1892.00 | 1484.50 | 0.0000 | Y | 4/4 | FINDING |
| F4 flow/book | top_imb | -0.16 | -0.25 | 0.0059 | Y | 4/4 | FINDING |
| F4 flow/book | own0 | 28.50 | 37.00 | 0.0004 | Y | 2/4 | suggestive |
| F4 flow/book | opp0 | 42.50 | 62.00 | 0.0000 | Y | 4/4 | FINDING |
| F5 path before | mom60 | 1.50 | 1.25 | 0.0112 | Y | 2/4 | suggestive |
| F5 path before | mom300 | 1.50 | 1.25 | 0.5861 | n | 2/4 | null |
| F5 path before | in_prior_range | 1.00 | 1.00 | 0.1211 | n | 4/4 | null |
| F5 path before | dist_pd_edge | 13.88 | 13.12 | 0.0409 | Y | 2/4 | suggestive |
| F6 regime | rng_ratio | 0.91 | 0.85 | 0.0081 | Y | 4/4 | FINDING |
| F6 regime | rv30 | 47.75 | 32.62 | 0.0000 | Y | 4/4 | FINDING |

## 3. ANATOMY (path features - NOT usable for selection)
| exit type | n | net | share of pooled net | earner n | earner net |
|---|---|---|---|---|---|
| spike | 321 | +679.2 | 141% | 201 | +622.4 |
| stall | 1103 | +96.5 | 20% | 179 | +597.4 |
| timecap | 1 | +52.5 | 11% | 1 | +52.5 |
| stop | 92 | -345.0 | -71% | 0 | +0.0 |
| end | 0 | +0.0 | 0% | 0 | +0.0 |
MFE med earners 3.62 vs rest 0.88; MAE med 0.12 vs 1.12.

## FINDINGS (14) — candidate inputs for D-2/D-3 specs (J gates; nothing adopted here)
- cross_to_fill (F1 entry mechanics): earners 80.00 vs rest 109.00, p=7.0e-05, 4/4 months
- tier20 (F2 news context): earners 0.00 vs rest 0.00, p=4.9e-02, 4/4 months
- tier45 (F2 news context): earners 0.00 vs rest 0.00, p=2.7e-02, 4/4 months
- react5 (F2 news context): earners 3.00 vs rest 2.25, p=5.4e-06, 4/4 months
- range5 (F2 news context): earners 7.75 vs rest 5.50, p=2.7e-12, 4/4 months
- vol5 (F2 news context): earners 22073.00 vs rest 17143.00, p=7.6e-09, 4/4 months
- room_ahead (F3 levels): earners 4.50 vs rest 6.00, p=2.1e-03, 4/4 months
- lvl_within8 (F3 levels): earners 1.00 vs rest 1.00, p=5.3e-03, 3/4 months
- room_behind (F3 levels): earners 4.50 vs rest 5.50, p=2.7e-03, 3/4 months
- vol30 (F4 flow/book): earners 1892.00 vs rest 1484.50, p=5.5e-09, 4/4 months
- top_imb (F4 flow/book): earners -0.16 vs rest -0.25, p=5.9e-03, 4/4 months
- opp0 (F4 flow/book): earners 42.50 vs rest 62.00, p=1.8e-08, 4/4 months
- rng_ratio (F6 regime): earners 0.91 vs rest 0.85, p=8.1e-03, 4/4 months
- rv30 (F6 regime): earners 47.75 vs rest 32.62, p=1.0e-17, 4/4 months

Trade table saved: Data/inputs/xd_trades.parquet. Registry: T-XD01.

## READING — THE EARNER PROFILE IS ONE COHERENT STORY
Our money is made when: (1) the MARKET HAS ENERGY - last-30-min
movement (rv30, p=1e-17, the strongest signal in the table), busy
first-5-min (vol5/react5/range5), big-calendar days (tier20/45), and
30s volume at the entry itself; (2) the entry sits in LEVEL-DENSE
territory - nearest level ahead closer (4.5 vs 6.0 pts), level
within 8 (M7's arm condition), level behind closer too; (3) the
break meets a THINNER WALL (opp0 42.5 vs 62) and fills FAST
(80s vs 109s to fill). The anatomy closes the loop: spike-capture
exits alone are +679 of the +483 pooled net (141%) - the whole
business is "enter near levels when the tape is moving, let M7's
level-snap collect"; stalls are breakeven noise (+96 across 1,103
trades) and stops cost -345. Earners' median MAE is 0.12 vs rest
1.12: winners work almost immediately.
TWO HONEST NEGATIVES: (a) signed FLOW at entry does NOT separate our
earners (flow30/flow120 null) - the 3-sample flow thread is about
HIS choices, not our P&L, so D-2's premise is WEAKENED for the gate
use-case; (b) lane is not a finding - both lanes produce earners,
which retroactively supports the two-lane union.
CANDIDATE INPUTS handed to the next spec (J gates; correlated
cluster warning - activity features overlap heavily, a gate design
should pick 1-2 orthogonal ones): activity gate (rv30 or vol5),
proximity gate (room_ahead <= 8, already M7's arm input), thin-wall
gate (opp0), fast-fill (observational - TTL shortening candidate).
