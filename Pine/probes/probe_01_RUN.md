# Running Probe 01

Steps marked [doc] were checked against TradingView's help pages on 2026-11-18.
Steps marked [memory] were not found on a help page; the label or location may differ slightly.

## Before you start

- Any time of day works. The script only reads loaded history.
- Expect under a minute per run once the code is pasted.

## A. Set up the chart

1. Open a chart and load the ES symbol you normally use. Note what the top-left shows: `ES1!` is the continuous contract; something like `ESZ2026` is a single contract.
2. If it is `ES1!`: look at the bottom of the chart for the **B-ADJ** button. Leave it off (off is the default). [doc: help article 43000685266]
3. Click the interval menu in the top toolbar and pick **1 second** from the Seconds group. [doc: help article 43000747934]
4. Set the session to **Electronic trading hours**: chart Settings (gear icon) → Symbol → Session, or the ETH/RTH button at the bottom of the chart. [memory]

## B. Load the script

5. Click the **Pine** icon on the right toolbar. [doc: help article 43000763320]
6. Click the script name at the top of the editor → create new → **Indicator**. [doc]
7. Select everything in the editor, delete it, and paste the full contents of `probe_01_history_rth_gaps_v1.pine`.
8. Click the script name → **Save script**. [doc]
9. Click **Add to the chart**. [doc]
10. If an error appears instead of a table: copy the error text exactly, with its line number, and send it. Stop here.

## C. Run 1 — Electronic hours

11. A black table appears in the top-right corner of the chart. Take a screenshot of it.

## D. Run 2 — Regular hours

12. Switch the session to **Regular trading hours** (same place as step 4). The table recalculates by itself.
13. Take a second screenshot.

## E. Hand check for Q2

14. Read the row "Q2: last completed RTH session (CT date)" and the range under it.
15. Switch the chart to 1 minute and set the chart timezone to Chicago (clock at the bottom-right of the chart). [memory]
16. On that date, find the highest high and lowest low between 08:30 and 15:00. Subtract. Note whether it equals the table's range.

## F. Send back

17. Both screenshots, the hand-check number, and whether the B-ADJ button was present and off.

## G. Clean up

18. Remove the indicator from the chart (hover its name at the top-left of the chart → X). [memory]

## Reading the table

| Row | What it means |
|---|---|
| Q1: RTH sessions done at first chart bar | 15 or more = the 1-minute request has enough history. Fewer = it is capped. |
| Q2 range | Should equal the hand check. If it equals the 08:30–15:15 range or the full-day range instead, the filter is not working inside the request. |
| Q3 rows | How many seconds had no bar, and the longest run. On the Electronic run these may read 0 if the loaded bars do not reach back into regular hours; the Regular run is the one that counts for Q3. |
