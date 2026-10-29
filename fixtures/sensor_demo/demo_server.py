#!/usr/bin/env python3
"""키트 스크립트 시험용 가짜 웹 서버. 실제 과제와 무관하다.
    python demo_server.py --port 8765 --data data [--bad-date 2030-03-04]
  /              → HTML
  /api/dates     → 날짜 목록 JSON
  /api/day?date= → 그 날짜 요약 JSON. --bad-date와 같으면 409 (run_e2e가 잡아내는지 시험)
"""
import argparse
import csv
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, default=8765)
ap.add_argument("--data", default="data")
ap.add_argument("--bad-date", default="")
a = ap.parse_args()
rows = list(csv.DictReader((Path(a.data) / "readings.csv").open(encoding="utf-8-sig")))
dates = sorted({r["ts"][:10] for r in rows})


class H(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, code, body, ctype="application/json"):
        b = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/":
            return self.send(200, "<h1>demo</h1>", "text/html")
        if u.path == "/api/dates":
            return self.send(200, json.dumps(dates))
        if u.path == "/api/day":
            d = parse_qs(u.query).get("date", [""])[0]
            if d == a.bad_date:
                return self.send(409, json.dumps({"error": "undecided group"}))
            n = sum(1 for r in rows if r["ts"].startswith(d))
            return self.send(200, json.dumps({"date": d, "readings": n}))
        self.send(404, "{}")


ThreadingHTTPServer(("0.0.0.0", a.port), H).serve_forever()
