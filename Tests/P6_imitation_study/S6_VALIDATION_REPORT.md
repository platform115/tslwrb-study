# SELECTOR OUT-OF-SAMPLE VALIDATION (T-IM36)
> Frozen V1/U, zero refitting; signals recomputed via the frozen
> out-of-sample scoring path. Script: p6_29_selector_validation.py.

| metric | training 2025-10 | 2022-02 | 2021-09 |
|---|---|---|---|
| his entries | 92 | 223 | 176 |
| V1 catch | 38% | 26% | 19% |
| V1 fires/day | 18.6 | 18.0 | 13.0 |
| U catch | 49% | 44% | 32% |
| U fires/day | 48.4 | 49.7 | 34.0 |
| displacement median (V1 fills) | +3.0 | +2.4 | +2.3 |

## Reading (two-sided, per reporting rule)
HOLDS: fire rates transfer almost exactly (18.6 -> 18.0; 48.4 -> 49.7 on
2022-02) and the displacement distribution is stable (+2.3 to +3.0
median) - the MECHANISM (edge interaction + signal, entry past the edge)
is not month-fitted.
DEGRADES: catch drops out of sample - V1 38 -> 26 -> 19%, U 49 -> 44 ->
32%. Part era drift (his 2021-09/2022-02 months have 2x the entry count -
a more scalp-heavy mode with a lower structure-trigger share), part the
expected give-back from 13 selection cells on 92 entries.
CONSERVATIVE NUMBERS TO QUOTE: 2021-09 is the cleanest month (2022-02
touched the old signal-era tuning): V1 ~19% catch at 13 fires/day,
U ~32% at 34/day. Realistic bracket: V1 19-38%, U 32-49%.

## Program state
The imitation-selection cycle is complete: harness-certified structures,
the trigger-site entry model with a transferable displacement rule, two
frozen selectors with out-of-sample brackets, and a characterized
remainder (momentum trades; his Key-zone system unmodeled for lack of
stated prices in training).
