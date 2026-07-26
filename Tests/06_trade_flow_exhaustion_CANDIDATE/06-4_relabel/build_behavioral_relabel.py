#!/usr/bin/env python3
"""
build_behavioral_relabel.py  — deterministic failure_tag per episode (single source)
-------------------------------------------------------------------------------
WHY
  The 52 target_reached vs 40 failed_trades contrast is muddy: most failed_trades are
  PROFITABLE early-exits, not losses, which dilutes any exit signal toward null. This
  relabel separates the three behaviors so exit research runs on a clean contrast.

CLASSES (option 1, three clean classes — see note on dropped 'scratch')
  Priority order (losers take precedence over pt1, matching the FROZEN exhaustion-candidate
  de-dupe so a give-back trade is a loss, not a "reached"):
    losing_trade      : realized_pnl < 0
    reached_target    : NOT losing AND pt1 reached
    below_target_win  : NOT losing AND pt1 NOT reached   (the profitable early-exits)
  October resolves to 16 / 47 / 29. The clean EXIT contrast = losing_trade (16) vs
  reached_target (47) == the exhaustion candidate's loser spine (verified identical:
  16 losers, 5 overlap with pt1, 47 non-loser reached).

  'scratch_trade' DROPPED: October realized_pnl (points, tick-granular) has NO cluster at
  zero (1 trade exactly 0; near-continuous from -3 up). Any scratch band would be an
  arbitrary cut manufacturing an arm that is not in the data. A scratch class can be
  RE-INTRODUCED later as a BEHAVIORAL definition (fast exit + near-zero excursion), which
  needs the MAE/time features — not a pnl band. Recorded as a deferred decision, not a
  silent omission. (pt1 def: WRB_Definition.txt sec 5.)

OUTPUT (reusable label, attach in all downstream exit tests):
  <out>.parquet / .csv with: uid, episode_id, source_file, side, trading_date,
  first_entry_utc, last_exit_utc, realized_pnl, group(pt1), is_loser, failure_tag.
  uid = source_file::episode_id  (episode_id alone is non-unique across files).

Deterministic. Read-only on source. Reuses frozen build_groups (pt1 / Reading-B grouping).

RUN
  python3 build_behavioral_relabel.py --config ../../config.toml --wrb ../../wrb_1m.parquet \
      --out behavioral_relabel_2025-10
"""

# --- path bootstrap (subtest dir -> shared root modules) ---
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
# --- end path bootstrap ---
import argparse
import pandas as pd

from trade_flow_exhaustion import build_groups


def load_episode_path(config_path):
    import tomllib
    with open(config_path, "rb") as f:
        return tomllib.load(f)["paths"]["episodes"]


def assign_failure_tag(g):
    """Three-class partition; losers take priority over pt1. Returns g with failure_tag."""
    g = g.copy()
    g["is_loser"] = g["realized_pnl"] < 0
    def tag(r):
        if r["is_loser"]:
            return "losing_trade"
        if r["group"] == "target_reached":
            return "reached_target"
        return "below_target_win"
    g["failure_tag"] = g.apply(tag, axis=1)
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--wrb", required=True)
    ap.add_argument("--out", default="behavioral_relabel_2025-10")
    args = ap.parse_args()

    ep_path = load_episode_path(args.config)
    g = build_groups(ep_path, args.wrb)          # frozen pt1 grouping; uid built inside
    g = assign_failure_tag(g)

    counts = g["failure_tag"].value_counts()
    print(f"[relabel] episodes={len(g)}")
    for k in ["losing_trade", "below_target_win", "reached_target"]:
        print(f"  {k:18s} {int(counts.get(k, 0))}")
    # integrity reconciliation against the frozen exhaustion spec
    overlap = int(((g.group == "target_reached") & g.is_loser).sum())
    assert int(g.is_loser.sum()) == 16, "loser count drift vs frozen 16"
    assert overlap == 5, "pt1-loser overlap drift vs frozen 5"
    assert int(((g.group == "target_reached") & ~g.is_loser).sum()) == 47, "non-loser reached drift vs 47"
    print(f"[relabel] reconciled with exhaustion spec: 16 losers, {overlap} overlap, 47 non-loser reached.")
    print(f"[relabel] clean EXIT contrast = losing_trade(16) vs reached_target(47) "
          f"(below_target_win(29) = profitable early-exits, held out of the contrast).")

    keep = ["uid", "side", "entry", "exit", "group", "realized_pnl", "is_loser", "failure_tag",
            "hold", "pt1_open_el"]
    out = g[keep].rename(columns={"entry": "first_entry_utc", "exit": "last_exit_utc"})
    out.to_parquet(f"{args.out}.parquet", index=False)
    out.to_csv(f"{args.out}.csv", index=False)
    print(f"[relabel] wrote {args.out}.parquet and .csv ({len(out)} rows). "
          f"Attach as the single-source exit label.")


if __name__ == "__main__":
    main()
