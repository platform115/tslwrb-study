# M8G2 REPORT — M8 ON THE G2 LINE (T-MG28)
STATUS: CLOSED | 2026-11-27 | Spec: Tests/D29_m8/M8_SPEC.md (frozen first) | controls exact (2126/+565.9; 6252/+1659.0) | mechanism-primary | six months

| strategy | cell | trades | per-trade | pooled | by month (21-09/22-02/23-05/24-05/24-11/25-10) |
|---|---|---|---|---|---|
| G2-4 | M7 baseline | 2126 | +0.27 | +565.9 | +59/+138/+119/+39/+24/+188 |
| G2-4 | M8 D=2.0 FROZEN | 2400 | +0.34 | +824.8 | +71/+285/+101/+106/+75/+188 |
| G2-4 | M8 D=1.0 | 2673 | +0.32 | +842.6 | +100/+286/+124/+74/+89/+169 |
| G2-4 | M8 D=3.0 | 2258 | +0.36 | +823.9 | +68/+286/+138/+86/+64/+182 |
| G2-4 | M8 D=0.25 | 2723 | +0.31 | +833.1 | +94/+247/+134/+88/+91/+179 |
| G2-6 | M7 baseline | 6252 | +0.27 | +1659.0 | +173/+324/+372/+219/+231/+340 |
| G2-6 | M8 D=2.0 FROZEN | 8383 | +0.32 | +2670.0 | +271/+707/+399/+386/+305/+601 |

## MECHANISM (twin-matched; busy-freed separate)
| strategy | D_min | changed | twin delta pooled | months delta>=0 | busy add/drop (net) |
|---|---|---|---|---|---|
| G2-4 | 2.0 | 575 | +143.6 | 5/6 | 331/57 (+115.2) |
| G2-4 | 1.0 | 1016 | +46.0 | 4/6 | 624/77 (+230.8) |
| G2-4 | 3.0 | 299 | +188.2 | 6/6 | 169/37 (+69.8) |
| G2-4 | 0.25 | 1095 | +40.2 | 3/6 | 678/81 (+227.0) |
| G2-6 | 2.0 | 1375 | +165.2 | 4/6 | 3027/896 (+845.8) |

## VERDICT vs THE FROZEN LINES (G2 line: G2-4xM8, D=2.0)
- controls exact: PASS
- twin delta > 0 pooled AND >= 0 in >= 4/6 months: PASS (+143.6; 5/6)
- full cell > +565.9: PASS (+824.8)
- worst month > -10: PASS (+71.0)
G2-LINE VERDICT: ADOPT-AS-CANDIDATE - J gates

Registry: T-MG28 (G2 arm).
