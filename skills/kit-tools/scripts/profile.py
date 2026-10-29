#!/usr/bin/env python3
"""data 폴더(또는 파일)를 행 출력 없이 요약한다. 표준 라이브러리만 사용.

사용법:
    python profile.py data/
    python profile.py data/events.csv --max-cat 40

출력: 파일별 행 수, 완전 중복 행 수, 컬럼별 유형 추정과 요약
  - 범주형: 값별 건수 전부 (값이 "대상 아님"을 뜻할 수 있으니 전부 본다)
  - ID형: 고유 개수, 두 번 이상 나온 값 수
  - 숫자형: 최소·최대, 가장 자주 나온 값 3개 (기준값에 몰린 값 확인용)
  - 시간형: 최소·최대, 시간대 표기 종류, 시(hour)별 건수
"""
import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

try:  # Windows에서도 한글 출력이 깨지지 않게
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MISSING = {"", "na", "n/a", "nan", "null", "none", "-"}
DT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2}(\.\d+)?)?)?(Z|[+-]\d{2}:?\d{2})?$")


def read_table(path):
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, list):
                    data = v
                    break
        if not isinstance(data, list) or not data or not isinstance(data[0], dict):
            return None, None
        cols = list(dict.fromkeys(k for row in data for k in row))
        rows = [[("" if r.get(c) is None else str(r.get(c))) for c in cols] for r in data]
        return cols, rows
    delim = "\t" if path.suffix.lower() == ".tsv" else ","
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=delim)
        try:
            cols = next(reader)
        except StopIteration:
            return [], []
        rows = [r for r in reader]
    return cols, rows


def is_num(v):
    try:
        float(v.replace(",", ""))
        return True
    except ValueError:
        return False


def tz_kind(v):
    if v.endswith("Z"):
        return "Z(UTC)"
    m = re.search(r"([+-]\d{2}:?\d{2})$", v)
    if m and ("T" in v or " " in v):
        return m.group(1)
    return "없음"


def parse_dt(v):
    s = v.replace("Z", "+00:00")
    if re.search(r"[+-]\d{4}$", s):
        s = s[:-2] + ":" + s[-2:]
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def summarize_column(name, values, n_rows, max_cat):
    present = [v.strip() for v in values if v.strip().lower() not in MISSING]
    missing = len(values) - len(present)
    distinct = Counter(present)
    out = {"column": name, "missing": missing, "distinct": len(distinct)}
    if not present:
        out["type"] = "비어 있음"
        return out
    if all(DT_RE.match(v) for v in present):
        out["type"] = "시간"
        dts = [d for d in (parse_dt(v) for v in present) if d]
        out["min"], out["max"] = min(present), max(present)
        out["tz"] = dict(Counter(tz_kind(v) for v in present))
        hours = Counter(d.hour for d in dts if len(present[0]) > 10)
        if hours:
            out["by_hour"] = {h: hours[h] for h in sorted(hours)}
        return out
    if all(is_num(v) for v in present):
        nums = [float(v.replace(",", "")) for v in present]
        out["type"] = "숫자"
        out["min"], out["max"] = min(nums), max(nums)
        out["top_values"] = distinct.most_common(3)
        if len(distinct) <= max_cat and len(distinct) < max(3, n_rows // 2):
            out["type"] = "숫자(범주처럼 쓰임)"
            out["counts"] = dict(sorted(distinct.items(), key=lambda kv: -kv[1]))
        return out
    all_unique = len(distinct) == len(present) and len(present) > 5
    if len(distinct) <= max_cat and not all_unique:
        out["type"] = "범주"
        out["counts"] = dict(sorted(distinct.items(), key=lambda kv: -kv[1]))
        return out
    out["type"] = "ID/텍스트"
    out["repeated_values"] = sum(1 for c in distinct.values() if c > 1)
    out["examples"] = [v for v, _ in distinct.most_common(3)]
    return out


def profile_file(path, max_cat):
    cols, rows = read_table(path)
    if cols is None:
        return {"file": path.name, "error": "표 형태가 아님"}
    dup = sum(c - 1 for c in Counter(tuple(r) for r in rows).values() if c > 1)
    width_bad = sum(1 for r in rows if len(r) != len(cols))
    columns = []
    for i, c in enumerate(cols):
        vals = [r[i] if i < len(r) else "" for r in rows]
        columns.append(summarize_column(c, vals, len(rows), max_cat))
    return {"file": path.name, "rows": len(rows), "exact_duplicate_rows": dup,
            "rows_with_wrong_width": width_bad, "columns": columns}


def render(prof):
    lines = [f"## {prof['file']}"]
    if "error" in prof:
        return "\n".join(lines + [f"- {prof['error']}", ""])
    lines.append(f"- 행 {prof['rows']} · 완전 중복 행 {prof['exact_duplicate_rows']}"
                 f" · 컬럼 수 불일치 행 {prof['rows_with_wrong_width']}")
    lines.append("")
    lines.append("| 컬럼 | 유형 | 결측 | 고유 | 요약 |")
    lines.append("| --- | --- | --- | --- | --- |")
    for c in prof["columns"]:
        t = c["type"]
        if "counts" in c:
            summ = ", ".join(f"{k}:{v}" for k, v in c["counts"].items())
        elif t == "시간":
            summ = f"{c['min']} ~ {c['max']} · 시간대 {c['tz']}"
            if "by_hour" in c:
                summ += " · 시별 " + " ".join(f"{h}h:{n}" for h, n in c["by_hour"].items())
        elif t == "숫자":
            summ = f"{c['min']} ~ {c['max']} · 최빈 {c['top_values']}"
        elif t == "ID/텍스트":
            summ = f"반복된 값 {c['repeated_values']}개 · 예 {c['examples']}"
        else:
            summ = ""
        lines.append(f"| {c['column']} | {t} | {c['missing']} | {c['distinct']} | {summ} |")
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="data 폴더를 행 출력 없이 요약")
    ap.add_argument("path", help="data 폴더 또는 CSV/TSV/JSON 파일")
    ap.add_argument("--max-cat", type=int, default=30, help="값 종류가 이 수 이하이면 범주로 보고 전부 셈 (기본 30)")
    ap.add_argument("--json", action="store_true", help="마크다운 대신 JSON으로 출력")
    a = ap.parse_args()
    p = Path(a.path)
    files = [p] if p.is_file() else sorted(
        f for f in p.rglob("*") if f.suffix.lower() in {".csv", ".tsv", ".json"})
    if not files:
        print(f"요약할 CSV/TSV/JSON 파일이 없음: {p}")
        return 1
    profs = [profile_file(f, a.max_cat) for f in files]
    if a.json:
        print(json.dumps(profs, ensure_ascii=False, indent=1, default=str))
    else:
        print(f"# 데이터 프로파일 ({len(files)}개 파일)\n")
        for pr in profs:
            print(render(pr))
        print("범주형 값 중 '대상 아님'(테스트·시험·폐기·예비 등)을 뜻할 수 있는 값은 담당자 질문 후보다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
