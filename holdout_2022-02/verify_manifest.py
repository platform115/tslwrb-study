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
