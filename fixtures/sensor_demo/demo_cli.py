#!/usr/bin/env python3
"""키트 스크립트 시험용 가짜 CLI. 실제 과제와 무관하다.
zone·날짜(UTC)별 HIGH 건수와 value 평균을 CSV로 쓴다.
    python demo_cli.py --input data --output out/summary.csv [--fail]
"""
import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--input", required=True)
ap.add_argument("--output", required=True)
ap.add_argument("--fail", action="store_true", help="일부러 실패 (시험용)")
a = ap.parse_args()
if a.fail:
    print("의도된 실패", file=sys.stderr)
    sys.exit(2)
d = Path(a.input)
zone = {r["sensor_id"]: r["zone"] for r in csv.DictReader((d / "sensors.csv").open(encoding="utf-8-sig"))}
agg = defaultdict(lambda: [0, 0, 0.0])
for r in csv.DictReader((d / "readings.csv").open(encoding="utf-8-sig")):
    k = (r["ts"][:10], zone.get(r["sensor_id"], "UNKNOWN"))
    agg[k][0] += r["level"] == "HIGH"
    if r["value"]:
        agg[k][1] += 1
        agg[k][2] += float(r["value"])
out = Path(a.output)
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["date", "zone", "high", "readings", "mean_value"])
    for (dt, z), (h, n, s) in sorted(agg.items()):
        w.writerow([dt, z, h, n, round(s / n, 2) if n else ""])
