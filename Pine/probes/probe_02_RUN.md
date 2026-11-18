# Running Probe 02

Same procedure as Probe 01 (`probe_01_RUN.md`), with these differences.

## Conditions

- Timeframe: **1 minute**, not 1 second.
- Symbol: ES1!, B-ADJ off, real-time data (no "10 min delayed" badge).
- The market must be open so live ticks arrive. ES is closed 16:00–17:00 CT daily and from Friday 16:00 CT to Sunday 17:00 CT.

## Steps

1. Set the chart to 1 minute and the session to **Regular trading hours**.
2. Pine icon (right toolbar) → script name → create new → Indicator. Replace everything with the contents of `probe_02_ltf_seconds_v1.pine`. Save script. Add to the chart.
3. If an error appears: copy it exactly, with the line number, send it, stop.
4. The table is on the right edge, vertically centred. Screenshot it. Outside 08:30–15:15 CT the Regular-hours chart gets no live ticks, so the four "Live" rows will read 0 / n/a on this run. That is expected.
5. Switch the session to **Electronic trading hours**.
6. Wait about two minutes without touching the chart, so the script sees live ticks.
7. Screenshot the table twice, about 20 seconds apart within the same minute. The two "Live" rows for the forming bar should differ between the screenshots.
8. Remove the indicator.

## Reading the table

| Row | What a good result looks like |
|---|---|
| B3: RTH sessions on chart's own bars | 15 or more on at least one of the two runs |
| B1: bars WITH 1S data / first bar with 1S data / RTH days | Any non-zero amount. This sets how far back fires can be drawn, not whether live detection works |
| B2: RTH seconds that had a bar, % | Close to the 99.5% Probe 01 measured |
| Live: script updates seen | Climbs steadily |
| Live: 1S intrabars in the forming bar now | Grows through the minute, towards ~60 |
| Live: clock minus newest 1S bar open | A second or two. A value near 60 means seconds only arrive when the minute closes, which kills option (b) for live use |
