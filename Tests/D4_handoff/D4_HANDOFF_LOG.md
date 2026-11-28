# D4_HANDOFF_LOG — THE PINE-AGENT HANDOFF TRACKER
STATUS: LIVING | opened 2026-11-28 (J requested at the S2 stop) |
Owner: research side. One row per gate event; one entry per issue;
lessons at the bottom feed the next handoff (G2-6 addendum).

## STAGE TRACKER
| stage | what | gate result | date |
|---|---|---|---|
| S1 | scaffolding, inputs, session logic | PASSED (echo exact; 3 independent cross-checks) | 2026-11-28 |
| S2 | W20 bands | PASSED (4,140/4,140 exact; TV 1m bars = research bars on all 3 sessions) | 2026-11-28 |
| S3 | squeeze edges | next - J paused here | - |
| S4 | signals + orders | waits on S3; sliver purchase decided AT this gate | - |
| S5 | fills | on the fresh 1s vectors | - |
| S6 | exits (M7) | on the fresh 1s vectors | - |
| S7 | full replay + divergence report | - | - |

## DECISIONS OF RECORD
- Strategy mode (simulated), 1-second chart, G2-4 only, paste-in
  inputs (J, pre-build).
- HYBRID verification after the history discoveries (J): S2/S3 on
  1m overlap vectors; S4-S6 on fresh 1s-window vectors bought at
  the S4 gate (~3 recent weekdays, bbo-1s + tbbo); forward-parallel
  stays as the ongoing health check.
- Symbol: ESZ2025 or ES1! back-adjustment OFF for the vector
  sessions (identical there); front-contract chart for forward
  paper. J still to state which he compiled on.

## ISSUE LOG (every one found, by whom, and the fix)
| # | issue | found by | fix |
|---|---|---|---|
| 1 | Spec said window gate ends 15:15; engine's RTH label ends 15:00 (15:00-16:00 = overlap hour, never eligible) | Pine agent (S1 probe Q3) | spec v1.1; S1 v02 |
| 2 | Session-end rules unwritten (15:00-16:00 behavior, halt handling, no force-close) | Pine agent (Q4) | spec v1.1 |
| 3 | Retest carry-over past window end unwritten (cross in-window; clocks run on) | Pine agent (Q5, from vector rows) | spec v1.1 |
| 4 | Same-second event dedupe unwritten (108 rows -> 94 seconds -> 65 windows vs their 73) | both (count reconciliation) | spec v1.1; S1 v03 |
| 5 | v_structure column semantics unwritten (w20 unlagged vs sqz lagged; bar_ct = open) | Pine agent (Q6) | spec v1.1 section 10 |
| 6 | Constants file status line stale (v1.0 on v1.1 content) | Pine agent | bumped |
| 7 | TV 1-second history ~1 month - October vectors unreachable at 1s | J's Bar Replay test | hybrid plan |
| 8 | TV 1-minute history ~1 year - October vectors unreachable at ANY TF | J's chart test | overlap vectors minted (Apr-May 2026), October control byte-identical |
| 9 | Raw sparsest overlap session was Good Friday (short holiday session) | research side | swapped for sparsest full session |
| 10 | Export quirk: last chart bar row empty | Pine agent (twice, consistent) | accepted as artifact; replay point set after session |
| 11 | Chart timezone must be America/Chicago before export | research side (preempted) | J instruction |

## LESSONS FOR THE NEXT HANDOFF (G2-6 addendum and beyond)
1. CHECK THE CONSUMER'S DATA REACH FIRST. Both history limits (1s
   ~1 month, 1m ~1 year) were discoverable in five minutes before
   any vectors were minted; instead the October vectors were built
   unreachable. Rule: the first question of any handoff is "what
   can the target platform actually load?" - vectors are minted
   inside that window from the start.
2. SPECS DRIFT FROM CONVENTION WORDS, NOT NUMBERS. All three
   silent-convention escapes (15:00 gate, retest carry-over,
   dedupe) were behaviors the engine HAD that the house vocabulary
   papered over. Rule: port specs are transcribed from code, then
   DIFFED against code behavior on edge cases, never written from
   the project's own shorthand.
3. THE ECHO/GATE DESIGN WORKS - KEEP IT. Every issue above was
   caught at a gate before any signal logic existed; three
   independent cross-checks (echo sums, count reconciliation,
   their Python band re-implementation) each caught something or
   confirmed something. Cost: a few extra turns. Worth it.
4. THE CONSUMER IS A VERIFIER, NOT A TYPIST. The Pine agent's
   independent re-implementations and probes found 6 of the 11
   issues. Future handoff prompts should explicitly require the
   pre-check habit (re-derive the rule independently, compare,
   then build).
5. SESSION PICKS NEED A CALENDAR CHECK. Holiday/short sessions
   masquerade as "sparse" days (issue 9). Rule: candidate vector
   sessions are screened for full bar counts and exchange
   holidays before selection.
6. VERSION EVERY ARTIFACT, DIFF EVERY REPLACEMENT. Their
   mechanical diff of replacement docs caught the status-line
   miss instantly; the practice goes both ways and stays.

## NEXT ACTIONS
- J: state the compile symbol; S3 go (paste-back block delivered
  2026-11-28 16:48 MYT, ready to send).
- Research side: nothing owed until the S4 gate (sliver purchase
  proposal with exact days + schemas).
- D-8 walk resumes at step 3 (G2-7) when J returns to it.
