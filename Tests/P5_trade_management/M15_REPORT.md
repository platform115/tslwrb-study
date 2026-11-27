# M15 REPORT — FLOW-STATE CONDITIONED STALL (T-MG27)
STATUS: CLOSED | 2026-11-27 | Spec: M15_SPEC.md (committed first) | R-9 CONTROL exact | depth months only (2022-02 + 2025-10) | Tier-R | verdict: MECHANISM-PRIMARY, both months required

| cell | trades | pooled net | by month | checks/extended/no-book | twin delta (changed) | months delta>0 | earners harmed | verdict |
|---|---|---|---|---|---|---|---|---|
| CONTROL | 757 | +325.1 | +138/+188 | 0 | - | - | - | (reproduced) |
| th0 | 676 | +225.9 | +78/+148 | 669/289/259 | -50.5 on 94 changed | 0/4 | 9 | FAIL |
| th125 | 685 | +222.8 | +80/+143 | 665/276/259 | -56.5 on 91 changed | 0/4 | 10 | FAIL |

Registry: T-MG27.

## READING — HIS SEPARATORS DO NOT TRANSFER AS RULES ONTO OUR TRADES
Decisive FAIL: the ~90 changed trades lost -50/-57 vs their M7
twins, negative in BOTH months; the extensions also lengthened
holds, crowding out later entries (676 vs 757 trades, cell net
-100). The no-book fallback hit 259 of ~670 checks (windowed
coverage) - but the covered majority is where the losses happened,
so coverage is not the excuse.
THE PATTERN, NOW THREE INSTANCES (register-bound): signals that
genuinely separate HIS behavior fail as rules on OUR fills -
imb10 (F-8 -> M12 rejected), entry flow (F-10 -> null for our
earners, F-5), and now OFI10 (F-17 -> M15 rejected). His
hold-while-flow-supports behavior pays ON THE TRADES HE SELECTED;
our population is ~8x broader, and on it, flow persistence at stall
moments carries no continuation premium. His exit skill is
ENTANGLED WITH his entry selection - the two cannot be split and
transplanted separately.
WHERE F-17 STILL PAYS (unchanged): as track-1 knowledge of HIM, and
as the management-design input for D-25 - a strategy whose entries
are HIS-LIKE BY DESIGN is the one place his exit rule has its
preconditions. M7 survives challenger #12 and remains Tier-P
deployable; the depth feed remains justified by D-25's path, not by
retrofitting G2-4.
