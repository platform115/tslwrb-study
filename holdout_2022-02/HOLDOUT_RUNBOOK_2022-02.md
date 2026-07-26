# HOLDOUT RUNBOOK — Feb-2022 data prep (GLBX-20260607-UDES9FRSPK)
**Place at:** `tslwrb-study/holdout_2022-02/HOLDOUT_RUNBOOK_2022-02.md`
Step-by-step, in order. Every step is a gate: do not proceed past a FAIL.
All paths are RELATIVE TO THE REPO ROOT (`tslwrb-study/`) — start every session with
`cd` to the repo root. The Databento batch is assumed at
`/Volumes/2TB-Lexar/GLBX-20260607-UDES9FRSPK` — adjust once in `holdout_2022-02/config.toml` if not.

Repo facts this runbook is written against (from the actual tree):
- Stage-0 scripts live in `Old/` (`Old/02_reduce_to_windows.py`, `Old/03_align_verify.py`) —
  the only copies in the repo; these are the ones that produced the October windowed parquet.
- TWO config.toml files exist: repo root `./config.toml` and the probe config
  `Tests/06_trade_flow_exhaustion_CANDIDATE/config.toml`. NEITHER is touched by this runbook.
  The holdout gets a third: `holdout_2022-02/config.toml`.
- The probe root ("06_ root") is `Tests/06_trade_flow_exhaustion_CANDIDATE/`;
  `wrb_1m.parquet` lives there.

---

## PRE-REGISTERED EXCLUSION (locked before any data is touched)
**Feb 28, 2022 is EXCLUDED from the holdout.** The Databento batch ends at
2022-02-28 00:00 UTC, so that trading day has no MBP-10 coverage (wrb_1m has bars
through Feb 28 20:58 UTC; the tape does not). Decision made blind — before any
Feb-28 episode was counted or any feature computed. Consequences:
- Any episode with `first_entry_utc` on 2022-02-28 is out of every arm.
- Step 2 prints the count of affected episodes FOR THE RECORD; the count does not
  change the decision.
- The exclusion is enforced mechanically by data absence (02 reduces per-file and
  there is no 20220228 file — that day is silently never reduced). This paragraph is
  what makes the silence auditable.
- Every Feb result carries "Feb-2022 ex-28" in its registry notes.

Commit this file to git BEFORE running Step 1.

---

## Step 0 — folder setup (no code edits; pipeline stays byte-identical)
02/03 have no `--config` flag — each reads the `config.toml` sitting NEXT TO the script.
So the holdout folder gets verbatim copies of both, plus the Feb config renamed:

All commands from the repo root. The config and verify script are created IN PLACE
(self-contained paste blocks — they do not exist anywhere else on disk); the Stage-0
scripts and manifest are copied from where they already live.

**0.1 — create the holdout config** (skip if `holdout_2022-02/config.toml` already
exists and `python3 -c "import tomllib; print(tomllib.load(open('holdout_2022-02/config.toml','rb'))['run']['month'])"` prints `2022-02`):
```bash
cat > holdout_2022-02/config.toml <<'EOF'
# tslwrb-study — Feb-2022 HOLDOUT config (sibling of the October configs; both untouched)
# [run.resolved] is INTENTIONALLY ABSENT until 02/03 gates pass (02 prints the block to paste).
# Front-month hypothesis on record: ESH2 — DO NOT ASSUME; 02 resolves by volume.

[paths]
mbp10_dir   = "/Volumes/2TB-Lexar/GLBX-20260607-UDES9FRSPK"
episodes    = "/Users/joshhall/Developer/Projects/es-trading-agent-v3/Data/processed/chatlogs/tsl_episodes_clean.parquet"
es_1m_front = "/Users/joshhall/Developer/Projects/es-trading-agent-v3/Data/processed/es/es_1m_front.parquet"
es_5m_front = "/Users/joshhall/Developer/Projects/es-trading-agent-v3/Data/processed/es/es_5m_front.parquet"
out_dir     = "/Volumes/2TB-Lexar/tslwrb_windowed"

[run]
month               = "2022-02"
pre_entry_min       = 60
post_exit_min       = 5
chunk_rows          = 1000000
resolve_sample_rows = 5000000
tick                = 0.25
recon_tol_ticks     = 1
EOF
```

**0.2 — create the manifest verifier** (skip if `holdout_2022-02/verify_manifest.py` exists; it does after the 2026-07-26 session):
```bash
cat > holdout_2022-02/verify_manifest.py <<'EOF'
#!/usr/bin/env python3
# verify_manifest.py — checks every file in manifest.json exists, byte-size and sha256 match.
# Deterministic; no network. Exit 0 = all pass, 1 = any failure.
import argparse, hashlib, json, os, sys

def sha256(path, buf=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(buf):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--dir", required=True)
    a = ap.parse_args()
    files = json.load(open(a.manifest))["files"]
    fail = 0
    for f in files:
        path = os.path.join(a.dir, f["filename"])
        tag = f["filename"]
        if not os.path.exists(path):
            print(f"MISSING  {tag}"); fail += 1; continue
        size = os.path.getsize(path)
        if size != f["size"]:
            print(f"SIZE     {tag}  got {size} want {f['size']}"); fail += 1; continue
        want = f["hash"].split(":", 1)[1]
        got = sha256(path)
        if got != want:
            print(f"HASH     {tag}  MISMATCH"); fail += 1
        else:
            print(f"OK       {tag}  {size:>11,} bytes")
    n = len(files)
    print(f"\n{n - fail}/{n} pass")
    sys.exit(1 if fail else 0)

if __name__ == "__main__":
    main()
EOF
```

**0.3 — copy the Stage-0 scripts and manifest** (these DO exist on disk already):
```bash
cp Old/02_reduce_to_windows.py  holdout_2022-02/
cp Old/03_align_verify.py       holdout_2022-02/
cp /Volumes/2TB-Lexar/GLBX-20260607-UDES9FRSPK/manifest.json holdout_2022-02/
```

Provenance record (hashes of the exact scripts used for the holdout reduction):
```bash
shasum -a 256 Old/02_reduce_to_windows.py Old/03_align_verify.py \
              holdout_2022-02/02_reduce_to_windows.py holdout_2022-02/03_align_verify.py
```
GATE: each copied file's hash matches its `Old/` original (trivially true for a clean
`cp`; the record is what matters — paste the four lines into "Recorded counts" below).

One caveat to confirm once, then move on: `Old/` implies archived. If there is ANY doubt
that these are the scripts that produced October's windowed parquet (e.g. a later edit
that lived only in a chat), the check is: the October sidecar
`/Volumes/2TB-Lexar/tslwrb_windowed/02_resolved_2025-10.json` must exist and its keys
must match what `Old/02_reduce_to_windows.py` writes (month, front_contract,
windowed_parquet, rows_written, per_file). If it does, these are the scripts. 

Housekeeping (observed in the tree, fix or ignore consciously): the repo has a file named
`gitignore` — without the leading dot it does nothing; `.venv/`, `__pycache__/`, parquets
and the SSD outputs should be ignored via a real `.gitignore` before the commits below.

Then:
```bash
git add holdout_2022-02/ && git commit -m "holdout 2022-02: stage-0 setup + feb28 pre-registration"
```

---

## Step 1 — download integrity
```bash
cd holdout_2022-02
python3 verify_manifest.py --manifest manifest.json \
    --dir /Volumes/2TB-Lexar/GLBX-20260607-UDES9FRSPK
```
GATE: `25/25 pass`, exit code 0. Any MISSING/SIZE/HASH line → re-download that file, rerun.

---

## Step 2 — episode-side pre-count (before reduction, so the numbers are on record first)
Run from `holdout_2022-02/` (reads the episode path out of the Feb config):
```bash
python3 - <<'EOF'
import pandas as pd, tomllib
cfg = tomllib.load(open("config.toml","rb"))
ep = pd.read_parquet(cfg["paths"]["episodes"])
lo, hi = pd.Timestamp("2022-02-01", tz="UTC"), pd.Timestamp("2022-03-01", tz="UTC")
m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
feb28 = m[m.first_entry_utc >= pd.Timestamp("2022-02-28", tz="UTC")]
print(f"Feb-2022 episodes: {len(m)}  | on Feb 28 (PRE-REGISTERED EXCLUDED): {len(feb28)}")
print(f"usable: {len(m) - len(feb28)}")
print("per-day:"); print(m.trading_date.value_counts().sort_index().to_string())
EOF
```
GATE: Feb-2022 episode count > 0. If 0, the episode table doesn't cover the holdout
month — stop; nothing downstream is runnable. Record all three numbers below.

## Step 2b — es_1m_front coverage (03's reference; fail fast, not inside 03)
```bash
python3 - <<'EOF'
import pandas as pd, tomllib
cfg = tomllib.load(open("config.toml","rb"))
es = pd.read_parquet(cfg["paths"]["es_1m_front"], columns=["ts_event","symbol"])
m = es[(es.ts_event >= "2022-02-01") & (es.ts_event < "2022-03-01")]
print("es_1m_front Feb-2022 rows:", len(m)); print(m.symbol.value_counts())
EOF
```
GATE: nonzero rows, dominant symbol a plausible front month (hypothesis ESH2 —
02 makes the actual call by volume). If empty: es_1m_front was built for the October
study and must be extended to Feb-2022 BEFORE 03 can gate anything.
(wrb_1m.parquet Feb-2022 coverage is already verified: 1,714 ESH2 RTH rows, 20 days.)

---

## Step 3 — reduce (02): resolve front month by volume + write windowed parquet
```bash
cd holdout_2022-02
python3 02_reduce_to_windows.py
```
Watch for:
- `[resolve] ... front=` per file — EXPECT ESH2 on every file; the script hard-fails
  on any disagreement (unexpected mid-month roll).
- `[reduce] glbx-mdp3-202202XX ...: kept N rows` on active days; Sundays / Presidents'
  Day (Feb 21) / no-episode days print "no episodes this day, skipping" — normal.
- Final: `[done] wrote N rows -> /Volumes/2TB-Lexar/tslwrb_windowed/mbp10_ESH2_2022-02_windowed.parquet`
  plus the `02_resolved_2022-02.json` sidecar (both land in `out_dir`, NOT in the repo).
GATE: exit 0; front month consistent; rows_written > 0.
Feb 24 is the heaviest file (671 MB compressed — invasion day); slowest to reduce.
Expected, not a hang.

## Step 4 — verify (03): OHLCV reconciliation gate
```bash
python3 03_align_verify.py
```
GATE: `[GATE] PASS` (OHLC ≥99% within 1 tick, no constant offset, volume exact ≥99%).
Interpreting a FAIL (from the script's own key): constant OHLC offset = wrong contract;
scattered mismatches = clock/session bug; volume gap = incomplete trades.
Caution: Feb-2022 is a far higher-volatility regime than Oct-2025. If borderline
failures cluster ON Feb 24 specifically, report the by-day pattern before touching
`recon_tol_ticks` — do not silently raise the tolerance.

## Step 5 — freeze the resolution into the holdout config
02 prints the exact block; copy it from `02_resolved_2022-02.json` into
`holdout_2022-02/config.toml` (contract per the sidecar — copy, don't assume):
```toml
[run.resolved]
contract = "ESH2"
windowed_parquet = "/Volumes/2TB-Lexar/tslwrb_windowed/mbp10_ESH2_2022-02_windowed.parquet"
```
Then commit together: `git add holdout_2022-02/config.toml` + the sidecar copy + the
`03_align_ESH2_2022-02.md` report (copy both from the SSD into `holdout_2022-02/` so the
repo carries the gate evidence).

---

## Step 6 — toolkit hardcode audit, THEN arms gate
**6a. Hardcode grep (the single most likely silent-failure point).** The probe toolkit
was written against October and carries at least these module-level constants in
`Tests/06_trade_flow_exhaustion_CANDIDATE/trade_flow_exhaustion.py`:
`INSTRUMENT_ID = 294973` (ESZ5's id — ESH2's is DIFFERENT; `read_per_second` /
`read_trade_full` filter on it and would return ZERO Feb rows), and
`MONTH, SYMBOL = "2025-10", "ESZ5"` (build_groups filters episodes and WRBs on them).
Find every instance:
```bash
grep -rn "2025-10\|ESZ5\|294973" Tests/06_trade_flow_exhaustion_CANDIDATE \
     Tests/06b_trade_flow_confirmation_CANDIDATE --include="*.py"
```
Every hit must be parameterized ADDITIVELY (read from config with the old value as
default, so October runs still reproduce bit-for-bit) before any holdout run.
ESH2's instrument_id is not known in advance — resolve it from the Feb windowed parquet
(`instrument_id` column of rows where `symbol=="ESH2"`), print it, and record it below.
This is its own build-and-test pass with selftests; do it as a separate chat/turn with
the grep output pasted, not ad hoc.

**6b. Arms gate.** From the 06_ root, pointing at the holdout config
(`build_arms(config_path, wrb_path)` — both probe-toolkit args):
```bash
cd Tests/06_trade_flow_exhaustion_CANDIDATE
PYTHONPATH=.:06-13_stall_vs_reach python3 - <<'EOF'
from forward_battery import build_arms
stall, reach, windowed = build_arms("../../holdout_2022-02/config.toml", "wrb_1m.parquet")
print(f"HOLDOUT ARMS: reach={len(reach)} stall={len(stall)} | windowed={windowed}")
print("reach holds:", reach.hold.describe().round(1).to_dict())
print("stall holds:", stall.hold.describe().round(1).to_dict())
EOF
```
GATE (recorded, not judged): arm counts printed and written below. Do NOT interpret
them against October's 47/29 — February is a different sample by construction.
This is also where the 47-vs-52 definitional reconciliation must be settled BEFORE any
stall-boundary test runs: the boundary definition frozen in each October spec is the one
that applies; if any spec is ambiguous, resolve from the October spec text — never from
looking at February data.

---

## Step 7 — run the 16 index rows (only after 1–6 all pass)
Each test exactly per its linked .md spec in `holdout_index.html`: frozen windows,
thresholds, seeds, pre-registered pass bars. One registry row per run;
`labels_basis=behavioral`, notes carry "Feb-2022 ex-28". No re-fitting, no new grids,
no post-hoc variants. Pass bar met → `confirmed`/`confirmed-weak`; not met → `rejected`.
Discovery vocabulary does not apply here.

Derived inputs that are MONTH-STAMPED and must be rebuilt for Feb before their tests run
(they are inputs, not results — rebuilding them is prep, not fitting):
- `whg_1m_2022-02.parquet` / `whg_5m_2022-02.parquet` via
  `Tests/06_.../06-10_whg_fill/build_whg_series.py` (needed by whg_gap_capture).
- Any other `*_2025-10.*` artifact a spec references — the grep in 6a plus
  `grep -rln "2025-10" Tests --include="*.md"` over the 16 specs flags them.
Spec-readiness check first: the candidate-chip rows were "config not yet locked" per the
dashboard legend — any spec missing a frozen parameter gets locked from OCTOBER results
only, in a logged pass, before its Feb run.

---

## Recorded counts (fill in as gates pass)
- Step 0 script hashes: DONE 2026-07-26 — 02: be73cde6…09f8b9 · 03: 46fa50df…4a8c17f (Old/ == holdout copies, both pairs match)
- Step 1 manifest: 25/25 pass — DONE 2026-07-26
- Step 2 episodes Feb-2022 total: 223 · on Feb 28 (excluded): 8 · usable: 215 → 213 after NaT-exit exclusion (2, data-integrity pre-registration, guard patched into holdout 02 copy)
- Step 2b es_1m_front Feb rows: 27,360 · symbol: ESH2 (100%)
- Step 3 front month: ESH2 (consistent all files) · rows written: 117,429,046
- Step 4 gate: PASS · minutes compared: 5,550 (OHLC 99.98–100% within 1 tick, offsets +0.0000, volume 99.19% exact)
- Step 6a hardcode hits fixed: 17 files env-patched + spine + forward_battery + 06b assert month-gated; Oct smoke test reproduced 0.660 bit-for-bit · ESH2 instrument_id resolved: 5782
- Step 6b arms: reach 91 / stall 72 / losers 60 (boundary: settled 06-13 behavioral labels via build_arms, as frozen)
- Step 7: 15/16 rows adjudicated T-DF10–24 (loser_submodes on hold — no committed code) · 7 confirmed / 2 confirmed-weak / 4 rejected / 2 replicated-null · see HOLDOUT_FINDINGS_2022-02.md
- Note: repo initialized after Steps 0–1; Feb-28 pre-registration was documented before any reduction ran.
