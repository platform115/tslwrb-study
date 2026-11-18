# spec/

Empty until the research side delivers. Nothing in `indicators/` is built before these exist.

Expected contents:

1. `S2A_SPEC_v<N>.md` — written from the research code in `Tests/P4_entry_determination/`, every
   quantity with its exact formula and every symbol defined (answers Q5–Q10 in `../OPEN_QUESTIONS.md`).
2. Reference outputs for named days:
   - per session: C(day) and the 14-session mean day range
   - the full fire list: timestamp, direction, and the threshold values at each fire
3. Acceptance criteria: the tolerance within which TradingView fires must match the reference list.

Files here are write-once. A changed spec is a new version file.
