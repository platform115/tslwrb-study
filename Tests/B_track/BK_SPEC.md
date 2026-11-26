# BK_SPEC — BOOK LENS ON THE WHICH-SIGNAL QUESTION (T-EN111)
STATUS: FROZEN BEFORE RUN | 2026-11-26 | Rule 2 pre-registration
Trigger: J's external drive reconnected (standing trigger item (d),
added by T-EN109) and J's directive: "He's using data and facts
everyone has access to, we need to figure out the decision tree."
The order book IS data everyone has access to (any depth feed).
STUDY ONLY — no strategy change from this round.

## DATA (new to the repo)
book_per_sec_{2022-02,2025-10}.parquet from J's drive
(tslwrb_windowed): last-in-second top-of-book sizes (bid0, ask0) and
10-level depth sums (bid10, ask10), built by reduce_book.py from the
windowed MBP-10. Copied into Data/inputs with checksums; provenance
= drive, Databento GLBX.MDP3 MBP-10, instrument-filtered
(ESH2 / ESZ5).

## DESIGN
IDENTICAL to T-EN109 (ws_round.py episode machinery, with its
dedupe fixes): the 21 multi-cross episodes; taken cross vs passed
siblings; 10,000 within-episode permutations. Book state is
market-state (not cumulative), so every feature below is VALID in
the paired design — none is monotone-in-time by construction.

## FEATURES at the cross second (direction d known at the cross)
1. opp0   — top-of-book size on the side being broken (ask0 for
            longs, bid0 for shorts): the immediate resistance
2. opp10  — 10-level depth on the broken side
3. own0   — top size on the supporting side
4. imb0   — (own0 - opp0) / (own0 + opp0)
5. imb10  — 10-level imbalance, same construction
6. d30_opp0 — change in opp0 over the last 30s (pulling = negative)
7. depth_tot — bid10 + ask10 (two-sided; thin tape vs thick)
Missing seconds: nearest prior book second within 5s, else the
cross is reported as uncovered (no silent fills).

## ANALYSIS & OUTCOME LINES (frozen; as T-EN109)
Pooled within-episode rank statistic per feature; permutation p;
7 features -> Bonferroni alpha .0071 for FINDING, .05 suggestive,
else null. Coverage line (crosses with book data) printed first.
FINDING -> candidate rule spec'd to J; suggestive -> BACKLOG
(validation-months retest only); all null -> the which-signal
question is also book-closed at this resolution, remaining lane =
event-level MBP-10 (queue shape / pulling dynamics inside the
second) and cross-market.
Registry: T-EN111.
