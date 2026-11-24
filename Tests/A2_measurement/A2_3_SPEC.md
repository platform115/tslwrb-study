# A2.3 SPEC — FIRST ABSENT FAMILIES: HIS LABELS + THE LEVEL'S STORY
STATUS: FROZEN at run | 2026-11-24 | Track A step A2.3 | Registry: T-IM42 (his labels), T-IM43 (level story / recent bars)
Rows: the same 315 trades + 3,070 nulls as T-IM41 (columns appended).

## FAMILY A — HIS OWN LABELS (build-order rank 1)
Source: his 5,155 parsed references -> the 7,533 reference-to-object
links -> the objects' edge prices. All references STRICTLY BEFORE the
moment; all objects knowable before the moment (R-1).
| column | plain meaning |
|---|---|
| mention_near_1pt / _3pt | how many distinct areas he had ALREADY named today whose edge sits within 1 / 3 pts of the current price |
| mins_since_mention | minutes since his most recent such nearby mention |
| key_mention_near | one of those areas was named as a KEY area (his tier word) |
These answer, at every entry and every ordinary moment alike: "is price
at a spot he had already talked about?" - the talk->trade question.

## FAMILY B — THE LEVEL'S STORY + RECENT BARS (build-order rank 2)
Reference level = the nearest structure edge of any certified family
within 5 pts at the moment (resolver, knowable); no edge -> fields NaN.
| column | plain meaning |
|---|---|
| edge_dist | distance from price to that edge (pts) |
| n_tests_today | prior touches of the edge today (within 1 pt, >=5 min apart) |
| mins_since_test | minutes since the last such touch |
| last_bounce_ticks | after the previous touch, how far price bounced away within 5 min (ticks; only seconds before the moment are read) |
| dwell120 | share of the last 2 minutes spent within 1 pt of the edge |
| approach120 | how much the distance to the edge SHRANK over the last 2 min (ticks; + = approaching) |
| consec_1m | consecutive same-direction 1-minute closes, signed toward his side (completed bars only: bar open + 60s <= t) |
| consec_10s | same idea on 10-second steps from per-second data |
| body_share3 | how decisive the last 3 completed 1-minute bars were (body as share of range, averaged) |
| wick_opp_last | the last completed bar's rejection wick against his direction, as share of its range |
| inside_last | last completed bar held inside the prior bar's range (0/1) |
| volt3 | last completed bar's volume vs the three before it |

## HARNESS
The T-IM41 truncation recompute extends to every new column at 40
sampled moments per month (references, objects, bars and seconds all cut
at t); any difference fails. (The planted-bug mechanism was certified in
T-IM41 and the machinery is unchanged.)

## OUTPUT
Columns appended to Data/inputs/a2_features.parquet (checksum updated),
report in the T-IM41 format (difference-sorted, units, families), two
registry rows. No verdicts; A3 grouping consumes the result.
