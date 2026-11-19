#!/usr/bin/env python3
"""
p6_11_parser_v3.py — S1: STRUCTURE-REFERENCE PARSER v3. (T-IM15.)
Implements PARSER_V3_SPEC.md exactly. Acceptance (the S1 review gate):
  --samples   50 stratified sample parses, verbatim, full field assignments
  --recapture re-capture accounting on the preserved T-IM13 remainder
              (Data/inputs/remainder_820.txt) vs the hand-read classes
  (default)   full-corpus parse -> stats only; DB write ONLY with --write
              (spec: no regeneration before the review gate passes)

RUN: python3 Tests/P6_imitation_study/p6_11_parser_v3.py --samples    (repo root)
"""
import argparse, os, re, sys
import numpy as np
import pandas as pd

# ---------- KINDS (ordered; first in list wins for primary kind) ----------
KINDS = [
    ("key_kme_wrb", r"key\s+kme(?:\s+wrb)?\s+zone|kme\s+key\s+wrb\s+zone|\bkey\s+kme\b"),
    ("kme_wrb_zone", r"kme\s+wrb\s+zone"),
    ("hidden_gap", r"hidden\s+gap"),
    ("shadow_interval", r"long\s+(?:upper|lower)\s+shadow|\bshadow\s+interval"),
    ("reaction_hl", r"reaction\s+(?:high|low)"),
    ("contraction", r"contract(?:ing|ed|ion)\s+volatility|volatility\s+contract|too\s+contracted|\bcontract(?:ing|ed)\b"),
    ("tight_range", r"tight\s+(?:trading\s+)?range"),
    ("trading_range", r"trading\s+range|range\s?bound"),
    ("wrb_zone", r"wrb\s+(?:zone|area)"),
    ("wrb", r"\bwrb\b"),
    ("kme_line", r"kme\s+line"),
    ("kme_time", r"kme\s+time|\bkme\b"),
    ("level_sr", r"\b[SR]\s+area\b|\bsupport\b|\bresistance\b|\blevel\b"),
    ("zone_area", r"\bzone\b|\barea\b"),
    ("range_generic", r"\brange\b|short\s+squeeze|sticky|battle"),
    ("insync", r"\binsync\b|\bin\s+sync\b|(?:other\s+)?key\s+markets"),
    ("vtr", r"volatility\s+trading\s+re|\bvtr\b"),
    ("alert", r"price\s+alerts?|my\s+alerts?|set\s+(?:an?\s+)?alerts?"),
]
ALL_KIND = re.compile("|".join(p for _, p in KINDS), re.I)

RELS = [
    ("acting_as", r"acting\s+(?:like|as)"),
    ("back_to", r"\bback\s+(?:to|up\s+to|down\s+to)\b|retraced?\s+back"),
    ("broken", r"\bbroke(?:n)?\b|\bbreak(?:ing|s|out)?\b|\bthru\b|\bthrough\b|cross(?:ed|ing|es)?"),
    ("squeeze", r"short\s+squeeze"),
    ("battle", r"\bbattle\b|\bfight(?:ing)?\b|\bsticky\b"),
    ("hugging", r"\bhug(?:ging)?\b|\bstuck\b|\bsitting\b|\bpinned\b"),
    ("reached", r"\breach(?:ed|ing)?\b|\btagged\b|\bhit\b|\btouch(?:ed|ing)?\b"),
    ("testing", r"\btest(?:ing|ed|s)?\b|\bretest|\bprob(?:e|ing)\b|\battack|\bchalleng"),
    ("approaching", r"\bapproach|\bnear(?:ing|s)\b|coming\s+(?:up|down)|\bheading\b|push(?:ing)?\s+(?:up|down|toward)"),
    ("failed_held", r"\bfail(?:ed|ing|s)?\b|\breject|\bheld\b|\bhold(?:ing)?\b|\bdefend|\bbounc"),
    ("inside", r"\binside\b|\bwithin\b|\bin\s+the\b"),
    ("above", r"\babove\b"),
    ("below", r"\bbelow\b"),
    ("at_near", r"\b(?:at|near|around|on|off)\b|@"),
]
INSTR = [("NQ", r"\bnq\b|nasdaq"), ("VIX", r"\bvix\b"), ("YM", r"\bym\b|\bdow\b"),
         ("CL", r"\bcl\b|crude"), ("RTY", r"\brty\b|russell"),
         ("SPY", r"\bspy\b"), ("SOXL", r"\bsoxl\b"), ("QQQ", r"\bqqq\b"),
         ("DIA", r"\bdia\b"), ("breadth", r"\bbreadth\b|advancers|decliners")]
PRICE = re.compile(r"\b([1-9]\d{3}(?:\.(?:25|50|5|75|00|0))?)\b")
SIDE = re.compile(r"\b([SR])\s+area\b|\b([SR])\s*/\s*[SR]\b", re.I)
EVENT = re.compile(r"wrb\s+(?:pt\s?\d|reached|formed|completed)|pt\s?\d\s+reached", re.I)
TIER = [("small", r"\bsmall\b"), ("old", r"\bold\b"), ("regular", r"\bregular\b")]
DIRECTION = re.compile(r"\b(up|down)\b", re.I)
STATE = [("open", r"\bopen\b|\bunfilled\b"), ("filled", r"\bfilled\b")]
RECENCY = [("most_recent", r"most\s+recent"), ("prior", r"\bprior\b|\bprevious\b"),
           ("new", r"\bnew\b"), ("old", r"\bold\b"), ("today", r"\btoday'?s?\b")]
TFTOK = re.compile(r"\b(\d{1,2})\s?min\b|\b(\d{1,2})m\s+chart|\bhourly\b|\bdaily\b|\bweekly\b", re.I)
EMPH = re.compile(r"!|very\s+(?:important|careful)|\bimportant\b|\bcareful\b|\bBIG\b|\bHUGE\b")
CORR = re.compile(r"\bcorrection\b|\bmeant\b|\btypo\b", re.I)
BOILER = re.compile(r"hours?\s+later\s+by\s+an\s+average|most\s+consistent\s+results|has\s+(?:in|de)creased\s+\d|maximum\s+(?:price\s+)?(?:in|de)crease|free\s+chat\s+room|cme\s+group\s+alert|not\s+a\s+signal\s+calling|free\s+study\s+guide", re.I)
PERSONAL = re.compile(r"be\s+back\s+(?:in|at|later|for)|good\s+morning|gm\b|logged\s+in|calling\s+it\s+quits|lunch|dinner|coffee", re.I)
MIDPT = re.compile(r"mid\s?point", re.I)


def parse_text(t, ts=None):
    """One message -> list of reference dicts (possibly empty)."""
    tl = t.lower()
    found = [(k, re.search(p, tl, re.I)) for k, p in KINDS]
    found = [(k, m) for k, m in found if m]
    is_boiler = bool(BOILER.search(t))
    is_personal = bool(PERSONAL.search(tl)) and not found
    if not found:
        return []
    kind = found[0][0]
    extra_kinds = [k for k, _ in found if k in ("insync", "vtr", "alert") and k != kind]
    rel = next((k for k, p in RELS if re.search(p, tl, re.I)), "none")
    prices = [float(x) for x in PRICE.findall(t)][:2]
    sm = SIDE.search(t)
    role = (sm.group(1) or sm.group(2)).upper() if sm else None
    tier = next((k for k, p in TIER if re.search(p, tl)), "none")
    if kind == "key_kme_wrb" and tier == "none":
        tier = "key"
    dm = DIRECTION.search(tl) if kind in ("hidden_gap", "shadow_interval", "wrb") else None
    state = next((k for k, p in STATE if re.search(p, tl)), "none") if kind == "hidden_gap" else "none"
    rec = next((k for k, p in RECENCY if re.search(p, tl)), "none")
    tfm = TFTOK.search(tl)
    tf = None
    if tfm:
        g = tfm.group(1) or tfm.group(2)
        tf = f"{g}m" if g else tfm.group(0).lower()
    instr = next((k for k, p in INSTR if re.search(p, tl)), "ES")
    is_event = bool(EVENT.search(tl))
    if prices:
        ref_type = "explicit_price"
        conf = "high" if kind not in ("zone_area", "range_generic", "level_sr") else "med"
    elif is_event:
        ref_type, conf = "event", "med"
    elif rel != "none":
        ref_type = "relational"
        conf = "med" if kind not in ("zone_area", "range_generic") or role else "low"
    else:
        ref_type, conf = "mention", "low"
    base = dict(
        kind=kind, tier=tier,
        direction=(dm.group(1).lower() if dm else "none"),
        state=state, recency_cue=rec, relation=rel, role=role,
        role_flip=(rel == "acting_as"), tf=tf,
        price_1=prices[0] if prices else np.nan,
        price_2=prices[1] if len(prices) > 1 else np.nan,
        instrument=instr, midpoint=bool(MIDPT.search(tl)),
        emphasis=bool(EMPH.search(t)), ref_type=ref_type, confidence=conf,
        is_correction=bool(CORR.search(t)),
        is_boilerplate=is_boiler, is_personal=is_personal,
        needs_review=(conf == "low" or instr != "ES"),
        raw=t[:220])
    out = [base]
    for ek in extra_kinds:
        d2 = dict(base); d2["kind"] = ek; d2["confidence"] = "med"
        d2["needs_review"] = (instr != "ES")
        out.append(d2)
    return out


def full_parse(repo):
    wm = pd.read_parquet(os.path.join(repo, "Data/inputs/wrb_messages.parquet"))
    wm["dtm"] = pd.to_datetime(wm.datetime_utc, utc=True)
    wm = wm.sort_values("dtm").reset_index(drop=True)
    rows, last_ref_ts = [], None
    for _, r in wm.iterrows():
        t = str(r.message).replace("\n", " ").strip()
        for d in parse_text(t):
            d["ts_utc"] = r["dtm"]; d["month"] = str(r["dtm"])[:7]
            d["corrects_ts"] = (last_ref_ts if d["is_correction"] and last_ref_ts is not None
                                and (r["dtm"] - last_ref_ts).total_seconds() <= 900 else None)
            rows.append(d)
            if not d["is_correction"]:
                last_ref_ts = r["dtm"]
    return pd.DataFrame(rows)


def recapture(repo):
    """Run v3 over the preserved 820-row T-IM13 remainder; class accounting."""
    lines = open(os.path.join(repo, "Data/inputs/remainder_820.txt")).read().splitlines()
    cls = {"zone_area_rel": 0, "range_rel": 0, "kme": 0, "shadow": 0,
           "hidden_gap": 0, "reaction": 0, "contraction": 0, "insync": 0,
           "vtr": 0, "correction": 0, "boiler_personal": 0, "uncaptured": []}
    cap = 0
    for ln in lines:
        _, _, txt = ln.split("|", 2)
        if BOILER.search(txt):
            cls["boiler_personal"] += 1; cap += 1
            continue
        refs = parse_text(txt)
        if not refs:
            if PERSONAL.search(txt.lower()):
                cls["boiler_personal"] += 1; cap += 1
            else:
                cls["uncaptured"].append(txt[:120])
            continue
        d = refs[0]; cap += 1
        kinds_all = {x["kind"] for x in refs}
        if "insync" in kinds_all and d["kind"] != "insync":
            cls["insync"] += 1
        if "vtr" in kinds_all and d["kind"] != "vtr":
            cls["vtr"] += 1
        k = d["kind"]
        if d["is_correction"]:
            cls["correction"] += 1
        if k == "shadow_interval":
            cls["shadow"] += 1
        elif k == "hidden_gap":
            cls["hidden_gap"] += 1
        elif k == "reaction_hl":
            cls["reaction"] += 1
        elif k == "contraction":
            cls["contraction"] += 1
        elif k == "insync":
            cls["insync"] += 1
        elif k == "vtr":
            cls["vtr"] += 1
        elif k in ("kme_time", "kme_line"):
            cls["kme"] += 1
        elif k in ("tight_range", "trading_range", "range_generic"):
            cls["range_rel"] += 1
        else:
            cls["zone_area_rel"] += 1
    n = len(lines)
    print(f"===== RE-CAPTURE on the T-IM13 remainder ({n} rows) =====")
    print(f"captured (any class): {cap}/{n} = {cap/n:.0%}")
    print(f"  zone/area-family refs: {cls['zone_area_rel']}   (hand read: 194 zone/area + part of 167 new-vocab)")
    print(f"  range-family refs:     {cls['range_rel']}   (hand read: 199)")
    print(f"  KME remarks:           {cls['kme']}   (hand read: 129)")
    print(f"  shadow intervals:      {cls['shadow']}   (hand read: 68)")
    print(f"  hidden gaps:           {cls['hidden_gap']}   (hand read: 49)")
    print(f"  reaction H/L:          {cls['reaction']}   (hand read: 11)")
    print(f"  contraction:           {cls['contraction']}   (hand read: 10)")
    print(f"  insync:                {cls['insync']}   (hand read: 11)")
    print(f"  VTR:                   {cls['vtr']}   (hand read: 1)")
    print(f"  corrections flagged:   {cls['correction']}   (hand read: 12)")
    print(f"  boilerplate/personal:  {cls['boiler_personal']}   (hand read: 37+10)")
    print(f"\nUNCAPTURED ({len(cls['uncaptured'])}; hand read said 72 unresolved) — all shown:")
    for u in cls["uncaptured"]:
        print(f"  - {u}")


def samples(repo, k=50):
    df = full_parse(repo)
    print(f"full corpus: {len(df)} references (v2 baseline: 4358)\n")
    print(df.kind.value_counts().to_string())
    rng = np.random.default_rng(11)
    picks = []
    for kind, g in df.groupby("kind"):
        m = max(1, round(k * len(g) / len(df)))
        picks.append(g.iloc[sorted(rng.choice(len(g), size=min(m, len(g)), replace=False))])
    S = pd.concat(picks).sort_values("ts_utc")
    print(f"\n===== {len(S)} STRATIFIED SAMPLE PARSES (every kind represented) =====")
    for _, r in S.iterrows():
        flags = "".join([" CORR" if r.is_correction else "", " BOIL" if r.is_boilerplate else "",
                         " EMPH" if r.emphasis else "", " FLIP" if r.role_flip else "",
                         " NR" if r.needs_review else ""])
        p = "" if np.isnan(r.price_1) else f" px={r.price_1:g}" + ("" if np.isnan(r.price_2) else f"/{r.price_2:g}")
        extra = "".join([f" tier={r.tier}" if r.tier not in ("none",) else "",
                         f" dir={r.direction}" if r.direction != "none" else "",
                         f" state={r.state}" if r.state != "none" else "",
                         f" rec={r.recency_cue}" if r.recency_cue != "none" else "",
                         f" role={r.role}" if isinstance(r.role, str) else "", f" tf={r.tf}" if isinstance(r.tf, str) else "",
                         " midpt" if r.midpoint else ""])
        print(f"[{str(r.ts_utc)[:16]}] {r.kind}/{r.relation} ({r.ref_type},{r.confidence})"
              f"{extra}{p} [{r.instrument}]{flags}")
        print(f"    \"{r.raw[:180]}\"")
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--samples", action="store_true")
    ap.add_argument("--recapture", action="store_true")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    if a.recapture:
        recapture(a.repo)
    elif a.samples:
        samples(a.repo)
    else:
        df = full_parse(a.repo)
        print(f"{len(df)} references"); print(df.kind.value_counts().to_string())
        if a.write:
            out = os.path.join(a.repo, "Data/inputs/his_zone_refs.parquet")
            df.to_parquet(out); print(f"WROTE {out} (gate must have passed)")
