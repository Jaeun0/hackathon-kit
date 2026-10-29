#!/usr/bin/env python3
"""제출 직전 점검. 표준 라이브러리만 사용. 과제 폴더(git 저장소)에서 실행한다.

사용법:
    python check_submit.py                       # 현재 폴더
    python check_submit.py --workspace . --data-dir data --require README.md REPORT.md DECISIONS.md

검사 항목
  [실패] 미커밋 파일이 있음 / data 원본이 첫 커밋 이후 바뀜 / 필수 파일 없음
  [확인] 문서 속 "미실시·TODO·TBD·작성 예정" / 예외 발생을 기대하는 테스트 / "미확인"·"잠정" 위치
종료 코드: 실패 0건이면 0.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

try:  # Windows에서도 한글 출력이 깨지지 않게
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DOCS = ["PLAN.md", "REPORT.md", "DECISIONS.md", "HANDOFF.md", "AGENTS.md"]
STALE = re.compile(r"미실시|TODO|TBD|작성 예정|추후 작성|\(채울 것\)")
SOFT = re.compile(r"미확인|잠정|미정")
RAISES = re.compile(r"pytest\.raises|assertRaises|with raises\(")


def git(ws, *args):
    p = subprocess.run(["git", *args], cwd=ws, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, p.stdout.rstrip("\n")


def main():
    ap = argparse.ArgumentParser(description="제출 직전 점검")
    ap.add_argument("--workspace", default=".")
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--require", nargs="*", default=[], help="반드시 있어야 하는 파일")
    a = ap.parse_args()
    ws = Path(a.workspace).resolve()
    fails, notes = [], []

    code, out = git(ws, "status", "--porcelain")
    if code != 0:
        fails.append("git 저장소가 아니거나 git 실행 실패")
    else:
        changed = [l for l in out.splitlines() if l.strip()]
        print(f"- 미커밋 파일 {len(changed)}개")
        if changed:
            fails.append("미커밋: " + ", ".join(l[3:] for l in changed[:10]))

    code, root = git(ws, "rev-list", "--max-parents=0", "HEAD")
    if code == 0 and root:
        first = root.splitlines()[0]
        _, diff = git(ws, "diff", "--name-only", first, "HEAD", "--", a.data_dir)
        _, wdiff = git(ws, "diff", "--name-only", "--", a.data_dir)
        touched = sorted(set(diff.splitlines()) | set(wdiff.splitlines()))
        print(f"- 첫 커밋 이후 {a.data_dir}/ 변경 {len(touched)}개")
        if touched:
            fails.append(f"{a.data_dir}/ 원본 변경: " + ", ".join(touched[:10]))
        _, n = git(ws, "rev-list", "--count", "HEAD")
        print(f"- 커밋 수 {n}")

    for r in a.require:
        if not (ws / r).exists():
            fails.append(f"필수 파일 없음: {r}")

    for d in DOCS:
        f = ws / d
        if not f.exists():
            continue
        for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if STALE.search(line):
                notes.append(f"[문서 상태] {d}:{i} {line.strip()[:70]}")
            elif SOFT.search(line):
                notes.append(f"[미확인·잠정] {d}:{i} {line.strip()[:70]}")

    for f in ws.rglob("test*.py"):
        if any(part.startswith(".") for part in f.relative_to(ws).parts):
            continue
        for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if RAISES.search(line):
                notes.append(f"[예외 기대 테스트] {f.relative_to(ws)}:{i} — 명세에 있는 오류인지 확인")

    print()
    if notes:
        print("확인할 것 (실패는 아님):")
        for n in notes[:40]:
            print(f"- {n}")
        if len(notes) > 40:
            print(f"- … 외 {len(notes) - 40}건")
        print()
    if fails:
        print(f"결과: 실패 {len(fails)}건")
        for f in fails:
            print(f"- {f}")
        return 1
    print("결과: 실패 0건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
