# D27 REPORT — SENSITIVITY AUDIT (T-SA01)
STATUS: CLOSED | 2026-11-27 | Spec: D27_SPEC.md (frozen first) |
BASELINE reproduced exactly (757 / +325.1) | robustness check only -
nothing adopted, nothing changed.

## PARTS A+B — ENGINE CONSTANTS (band: +-15% of +325.1)
| constant | baseline | variants -> pooled | verdict |
|---|---|---|---|
| give-back | 0.75 | 0.5 -> +327.1; 1.0 -> +329.0 | ROBUST (flat) |
| arm floor | 0.5 | 0.25 -> +322.0; 0.75 -> +315.2 | ROBUST |
| stop | 3.75 | 3.0 -> +319.9; 4.5 -> +313.5; 5.25 -> +310.8 | ROBUST (remarkably flat - F-15 reinforced: the stop level barely matters across 3.0-5.25) |
| time cap | 480 | 360 -> +328.0; 720 -> +322.0 | ROBUST (vestigial, as T-MG22 showed) |
| entry TTL | 300 | 150 -> +312.9; 450 -> +325.9 | ROBUST |
| lane-2 window | 600 | 300 -> +320.4; 900 -> +333.1 | ROBUST (mildly better at 900 - noted, NOT adopted) |
| cross dedupe | 300 | 150 -> +304.5 (-6%); 450 -> +260.9 (-20%) | SENSITIVE - the one flagged constant. Direction: longer dedupe suppresses re-cross entries, which carry real value (consistent with the retest findings). No sign flip (not a knife-edge). Context: 300 was set pre-grid in the B2 era; the validated OOS results already price it in implicitly, but it is now ON RECORD as the constant whose value matters most. |

## PART C — ANALYSIS CONSTANTS
- F-17's OFI window (15/30/60s): the exit-vs-hold separation
  survives at EVERY window, both months, and GROWS with the window
  (15s: -280/-97; 30s: -702/-155; 60s: -1058/-624). ROBUST - and a
  character refinement: his exit-fade is a SUSTAINED flow change
  over ~a minute, not a sub-second blip.
- T-BK03 outcome thresholds: the base rate moves 41-62% hold with
  the labels (definitional, expected) but the book-null survives at
  every labeling (OFI10 p = 0.42-0.83). The null is ROBUST.

## VERDICT
No knife-edges anywhere. One SENSITIVE constant (dedupe 300),
flagged and recorded; everything else flat. The engine's
conclusions do not sit on arbitrary numbers. Registry: T-SA01.
