# M10 SPEC — HIS-EXIT IMMINENCE STUDY (pre-registered)
STATUS: FROZEN | 2026-11-26 | Registry: T-MG17
J's challenge: before declaring the hold/sell switch exhausted in-data,
two untested lanes must be run: (1) in-trade VOLUME/FLOW state (never a
switch candidate in any M-round); (2) HIS exits studied directly
(supervised on his behavior, not on path value).
## DATASET
His 315 audited training trades, entry second to exit second, states
every 2s. LABEL: he exits within the next 30s (1) vs he holds at least
120s more (0); the ambiguous 30-120s band is EXCLUDED (clean classes).
## FEATURES (knowable at the state's second)
Path: t_in_trade, exc, peak, give_back, slope10, slope30.
Levels: room ahead / behind (shipped detector).
Clock: mins since release.
NEW - in-trade tape: flow10, flow30 (signed volume toward his side),
vol30 (contracts), vol_fade = vol30 now / vol30 at the last new peak
(volume dying into the move - the documented divergence concept).
## VERDICT LINES (pre-stated)
Held-out AUC (GroupKFold by session), per-trade-averaged effect cells
beside it (serial-correlation honesty):
AUC >= 0.65: his exit timing is substantially predictable -> extract a
  deterministic exit trigger (next round, gated).
0.55-0.65: weak signal - report which features carry it; J decides.
< 0.55: in-data exhaustion is EARNED - the switch waits on MBP-10
  (standing backlog trigger: the external drive's return) and/or
  cross-market data. Said plainly either way.
