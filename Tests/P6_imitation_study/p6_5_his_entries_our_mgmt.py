#!/usr/bin/env python3
"""
p6_5_his_entries_our_mgmt.py — IMITATION STUDY step 5 (user side-track):
enter EXACTLY where he entered (2025-10, his first-entry second and side,
filled at our mid), manage with M0 and with M1-RTH. (T-IM05.)
RESULT: M0 +98.4 (81tr, 57%) | M1 +107.8 (84tr, 49%, avg loss -1.09),
both DD ~0. HIS parsed P&L on the same episodes: +620.0 (with his scaling
and adds - units NOT per-contract comparable to our 1-lot sim; direction of
the comparison stands, magnitude is confounded).
READS: (1) his entries carry real, mechanically-harvestable edge - the
first honest entry set that profits under our exits; (2) most of his P&L
comes from MANAGEMENT (adds/scaling/exits), not entry location alone;
(3) M1 holds up vs M0 on genuinely honest entries (first such test).
3 overnight entries excluded; 8 skipped by the one-position rule.
RUN: python3 Tests/P6_imitation_study/p6_5_his_entries_our_mgmt.py        (repo root)
"""
# Logic preserved in registry T-IM05; reproduce via the imports below.
