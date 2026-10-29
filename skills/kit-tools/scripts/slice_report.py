#!/usr/bin/env python3
"""결과 CSV를 범주 컬럼별로 나눠 튀는 그룹을 찾는다. 표준 라이브러리만 사용.

사용법:
    python slice_report.py out/result.csv --by line --by date
    python slice_report.py out/result.csv --by line --metric yield --weight wafers

표시 기준(★): 그룹 지표가 그룹 평균에서 표준편차 2배 넘게 벗어남, 또는 건수 비중이 3% 미만·50% 초과.
★는 '틀렸다'가 아니라 '설명할 수 있어야 하는 그룹'이다. 설명이 안 되면 담당자 질문 후보다.
"""
import argparse
import csv
import statistics
import sys
from collections import defaultdict

try:  # Windows에서도 한글 출력이 깨지지 않게
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def to_num(v):
    try:
        return float(str(v).replace(",", "").replace("%", ""))
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser(description="범주별로 나눠 튀는 그룹 찾기")
    ap.add_argument("csv")
    ap.add_argument("--by", action="append", required=True, help="나눌 컬럼. 여러 번 지정 가능")
    ap.add_argument("--metric", help="비교할 숫자 컬럼 (생략하면 건수만)")
    ap.add_argument("--weight", help="가중 평균에 쓸 숫자 컬럼 (예: wafer 수)")
    ap.add_argument("--k", type=float, default=2.0, help="표준편차 배수 기준 (기본 2)")
    a = ap.parse_args()
    with open(a.csv, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print("행이 없음")
        return 1
    print(f"# 범주별 분할 ({a.csv}, {len(rows)}행)\n")
    for col in a.by:
        if col not in rows[0]:
            print(f"## {col}: 컬럼 없음\n")
            continue
        groups = defaultdict(list)
        for r in rows:
            groups[r[col]].append(r)
        stats = {}
        for g, rs in groups.items():
            m = None
            if a.metric:
                vals = [(to_num(r.get(a.metric)), to_num(r.get(a.weight)) if a.weight else 1.0) for r in rs]
                vals = [(v, w) for v, w in vals if v is not None and w]
                if vals:
                    m = sum(v * w for v, w in vals) / sum(w for _, w in vals)
            stats[g] = (len(rs), m)
        means = [m for _, m in stats.values() if m is not None]
        mu = statistics.mean(means) if means else None
        sd = statistics.pstdev(means) if len(means) > 1 else 0.0
        print(f"## {col} ({len(groups)}개 그룹)\n")
        head = "| 값 | 행 | 비중 |" + (f" {a.metric} |" if a.metric else "") + " 표시 |"
        print(head)
        print("| --- | --- | --- |" + (" --- |" if a.metric else "") + " --- |")
        for g, (n, m) in sorted(stats.items(), key=lambda kv: -kv[1][0]):
            share = n / len(rows)
            flag = []
            if share < 0.03:
                flag.append("소수")
            if share > 0.5 and len(groups) > 2:
                flag.append("쏠림")
            if m is not None and sd and abs(m - mu) > a.k * sd:
                flag.append("지표 이탈")
            mtxt = f" {m:.4g} |" if a.metric and m is not None else (" - |" if a.metric else "")
            print(f"| {g} | {n} | {share:.1%} |{mtxt} {'★ ' + ','.join(flag) if flag else ''} |")
        if mu is not None:
            print(f"\n그룹 평균 {mu:.4g}, 표준편차 {sd:.4g}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
