# CR REPORT — S5-LINE CONSTANTS RANGES (T-SA02, D-33 R4)
STATUS: CLOSED | 2026-11-28 | Spec: CR_SPEC.md (frozen first) | center controls exact (1541/1264 builder; 750/+472.1 sim) | NOTHING adopted (T-SA01 law)

Baseline: 750 trades, +472.1 (+195.3 / +276.8).

| cell | touches | trades | net | per-trade | 22-02 | 25-10 |
|---|---|---|---|---|---|---|
| CENTER | 1264 | 750 | +472.1 | +0.63 | +194.6 | +277.5 |
| offset-0.50 | 1264 | 836 | +488.8 | +0.58 | +213.9 | +274.9 |
| offset-1.00 | 1264 | 708 | +388.4 | +0.55 | +150.6 | +237.8 |
| ttl-90 | 1264 | 717 | +482.5 | +0.67 | +198.9 | +283.6 |
| ttl-180 | 1264 | 808 | +486.9 | +0.60 | +203.6 | +283.2 |
| stop-1.00 | 1264 | 755 | +463.8 | +0.61 | +187.5 | +276.2 |
| stop-1.50 | 1264 | 747 | +454.4 | +0.61 | +183.0 | +271.4 |
| arm-0.75 | 1264 | 740 | +443.1 | +0.60 | +185.5 | +257.6 |
| arm-1.50 | 1264 | 772 | +429.5 | +0.56 | +190.8 | +238.8 |
| giveback-0.50 | 1264 | 770 | +487.9 | +0.63 | +215.9 | +272.0 |
| giveback-1.00 | 1264 | 738 | +484.0 | +0.66 | +203.2 | +280.8 |
| fadestart-45 | 1264 | 752 | +465.5 | +0.62 | +203.0 | +262.5 |
| fadestart-90 | 1264 | 746 | +465.8 | +0.62 | +192.6 | +273.1 |
| fadestep-15 | 1264 | 751 | +474.9 | +0.63 | +199.5 | +275.4 |
| fadestep-45 | 1264 | 748 | +462.5 | +0.62 | +185.9 | +276.6 |
| cap-600 | 1264 | 750 | +468.1 | +0.62 | +199.4 | +268.8 |
| cap-1200 | 1264 | 749 | +476.6 | +0.64 | +194.5 | +282.1 |
| approach-1.5 | 1282 | 768 | +477.1 | +0.62 | +181.2 | +295.9 |
| approach-2.5 | 1240 | 738 | +433.2 | +0.59 | +175.6 | +257.6 |
| touch-0.25 | 1198 | 790 | +483.9 | +0.61 | +186.8 | +297.1 |
| touch-0.75 | 1314 | 707 | +518.4 | +0.73 | +213.1 | +305.2 |
| spacing-300 | 1892 | 1027 | +613.8 | +0.60 | +257.2 | +356.5 |
| spacing-900 | 1005 | 624 | +360.2 | +0.58 | +112.6 | +247.6 |
| lvl-tol-1.5 | 1722 | 1009 | +538.0 | +0.53 | +279.6 | +258.4 |
| lvl-tol-2.5 | 1039 | 682 | +388.2 | +0.57 | +165.5 | +222.8 |
| lvl-score-3 | 1336 | 794 | +484.0 | +0.61 | +201.1 | +282.9 |
| lvl-score-5 | 1129 | 679 | +444.0 | +0.65 | +192.6 | +251.4 |
| lvl-window-45 | 1255 | 783 | +349.9 | +0.45 | +160.5 | +189.4 |
| lvl-window-75 | 1301 | 820 | +375.0 | +0.46 | +132.2 | +242.8 |
| lvl-kill-3.75 | 1264 | 750 | +472.1 | +0.63 | +194.6 | +277.5 |
| lvl-kill-6.25 | 1264 | 750 | +472.1 | +0.63 | +194.6 | +277.5 |

## LABELS (T-SA01 convention: ROBUST within +-15% pooled net AND months same-direction; SENSITIVE beyond; KNIFE-EDGE = sign flip)
| dial | low cell | high cell | label |
|---|---|---|---|
| offset | +488.8 | +388.4 | SENSITIVE |
| ttl | +482.5 | +486.9 | ROBUST |
| stop | +463.8 | +454.4 | ROBUST |
| arm | +443.1 | +429.5 | ROBUST |
| giveback | +487.9 | +484.0 | ROBUST |
| fade-start | +465.5 | +465.8 | ROBUST |
| fade-step | +474.9 | +462.5 | ROBUST |
| cap | +468.1 | +476.6 | ROBUST |
| approach-zone | +477.1 | +433.2 | ROBUST |
| touch-distance | +483.9 | +518.4 | ROBUST |
| level-spacing | +613.8 | +360.2 | SENSITIVE |
| lvl-tolerance | +538.0 | +388.2 | SENSITIVE |
| lvl-score | +484.0 | +444.0 | ROBUST |
| lvl-window | +349.9 | +375.0 | SENSITIVE |
| lvl-kill | +472.1 | +472.1 | ROBUST |

## SUMMARY
- offset: SENSITIVE
- level-spacing: SENSITIVE
- lvl-tolerance: SENSITIVE
- lvl-window: SENSITIVE

Registry: T-SA02.
