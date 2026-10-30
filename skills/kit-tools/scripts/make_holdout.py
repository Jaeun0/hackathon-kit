#!/usr/bin/env python3
"""data를 복사해 날짜를 옮기고 함정 변형을 넣은 '자가 홀드아웃'을 만든다. 원본은 건드리지 않는다.
표준 라이브러리만 사용.

사용법:
    python make_holdout.py data holdout/data --config holdout.json
    python make_holdout.py data holdout/data --shift-days 7          # 날짜만 이동

설정(JSON) 예:
{
  "shift_days": 7,
  "skip_columns": {"equipment.csv": ["installed_at"]},
  "mutations": [
    {"file": "events.csv", "type": "duplicate", "where": {"equip_id": "E07"}, "limit": 2},
    {"file": "events.csv", "type": "set", "where": {"severity": "MAJOR"}, "set": {"severity": "major "}, "limit": 1},
    {"file": "events.csv", "type": "blank", "where": {"equip_id": "E03"}, "columns": ["cleared_at"], "limit": 1},
    {"file": "equipment.csv", "type": "append", "rows": [{"equip_id": "E99", "zone": "LAB"}]}
  ]
}
  - where: 값이 정확히 같은 행만 고른다 (생략하면 전체)
  - limit: 바꿀 최대 행 수 (생략하면 전부)
  - 날짜 이동은 날짜·일시 형식(YYYY-MM-DD, T/공백, Z/+09:00)을 그대로 유지한다.
결과 폴더에 HOLDOUT_LOG.md를 남긴다: 어떤 변형을 몇 행에 넣었는지.
기대값은 이 로그와 규정으로 손계산한다. 본 코드 출력을 기대값으로 복사하지 않는다.
"""
import argparse
import csv
import json
import re
import shutil
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

try:  # Windows에서도 한글 출력이 깨지지 않게
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DT_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})([ T]\d{2}:\d{2}(:\d{2}(\.\d+)?)?)?(Z|[+-]\d{2}:?\d{2})?$")


def shift_value(v, days):
    m = DT_RE.match(v.strip())
    if not m or days == 0:
        return v
    d = date.fromisoformat(m.group(1)) + timedelta(days=days)
    return d.isoformat() + v.strip()[10:]


def read_csv(p):
    with p.open(encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        return r.fieldnames or [], list(r)


def write_csv(p, cols, rows):
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def match(row, where):
    return all(str(row.get(k, "")) == str(v) for k, v in (where or {}).items())


def main():
    ap = argparse.ArgumentParser(description="자가 홀드아웃 만들기 (원본 불변)")
    ap.add_argument("src", help="원본 data 폴더")
    ap.add_argument("dst", help="만들 폴더 (이미 있으면 지우고 새로 만듦)")
    ap.add_argument("--config", help="변형 설정 JSON")
    ap.add_argument("--shift-days", type=int, help="날짜 이동 일수 (설정보다 우선)")
    a = ap.parse_args()
    src, dst = Path(a.src).resolve(), Path(a.dst).resolve()
    if dst == src or src in dst.parents or dst in src.parents or dst == Path.cwd():
        print("원본 폴더나 그 안에는 만들 수 없음. 다른 위치를 지정할 것")
        return 1
    cfg = json.loads(Path(a.config).read_text(encoding="utf-8")) if a.config else {}
    days = a.shift_days if a.shift_days is not None else int(cfg.get("shift_days", 0))
    skip = cfg.get("skip_columns", {})
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    log = [f"# 자가 홀드아웃 기록", f"- 원본: {src}", f"- 날짜 이동: {days}일", ""]
    tables = {}
    for p in sorted(dst.rglob("*.csv")):
        cols, rows = read_csv(p)
        shifted = 0
        for row in rows:
            for c in cols:
                if c in skip.get(p.name, []):
                    continue
                v = row.get(c) or ""
                nv = shift_value(v, days)
                if nv != v:
                    row[c] = nv
                    shifted += 1
        tables[p] = [cols, rows]
        log.append(f"- {p.relative_to(dst)}: {len(rows)}행, 날짜 값 {shifted}개 이동")
    log.append("\n## 변형")
    for i, m in enumerate(cfg.get("mutations", []), 1):
        p = next((q for q in tables if q.name == m["file"]), None)
        if p is None:
            log.append(f"{i}. {m['file']}: 파일 없음, 건너뜀")
            continue
        cols, rows = tables[p]
        limit = m.get("limit")
        hits = [r for r in rows if match(r, m.get("where"))]
        if limit is not None:
            hits = hits[:limit]
        t = m["type"]
        if t == "duplicate":
            rows.extend(dict(r) for r in hits)
        elif t == "set":
            for r in hits:
                r.update({k: str(v) for k, v in m["set"].items()})
        elif t == "blank":
            for r in hits:
                for c in m["columns"]:
                    r[c] = ""
        elif t == "append":
            new = [{c: str(r.get(c, "")) for c in cols} for r in m["rows"]]
            rows.extend(new)
            hits = new
        else:
            log.append(f"{i}. 알 수 없는 type: {t}")
            continue
        log.append(f"{i}. {m['file']} · {t} · 조건 {m.get('where', {})} · {len(hits)}행")
    for p, (cols, rows) in tables.items():
        write_csv(p, cols, rows)
    (dst / "HOLDOUT_LOG.md").write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log))
    return 0


if __name__ == "__main__":
    sys.exit(main())
