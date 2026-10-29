#!/usr/bin/env python3
"""지정 실행 명령으로 처음부터 끝까지 돌려 보고 실패 수를 센다. 표준 라이브러리만 사용.

CLI 과제:
    python run_e2e.py cli --cmd "python pipeline/run.py --input {data} --output {out}" \
        --data data --out out/result.csv

웹 서비스 과제 (서버를 띄우고 키마다 URL을 호출):
    python run_e2e.py server --cmd "python app.py --port {port} --data {data}" --data data \
        --port 8765 --path "/" --path "/api/summary?date={key}" --keys 2026-01-05,2026-01-06

    키 목록을 API에서 받기: --keys-url "/api/dates" (JSON 배열을 돌려주는 경로)

종료 코드: 실패 0건이면 0, 하나라도 실패하면 1.
서버 기동·대기·정리 부분은 anthropics/skills webapp-testing의 with_server.py(Apache-2.0)를 바탕으로 고쳐 썼다.
"""
import argparse
import json
import shlex
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

try:  # Windows에서도 한글 출력이 깨지지 않게
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def quote_arg(v):
    """경로에 띄어쓰기 등이 있으면 셸이 한 덩어리로 읽도록 따옴표로 감싼다."""
    v = str(v)
    if v and not any(c in v for c in ' \t"\'&|<>()^%!;$`'):
        return v
    if sys.platform == "win32":
        return '"' + v.replace('"', '\\"') + '"'
    return shlex.quote(v)


def fill(template, **kw):
    """{data} {out} {port} {key} 자리표시자를 채운다.
    템플릿에서 이미 따옴표로 감싼 자리("{data}")는 그대로 넣고, 아니면 필요할 때 따옴표를 붙인다."""
    out = template
    for k, v in kw.items():
        ph = "{" + k + "}"
        for q in ('"', "'"):
            out = out.replace(q + ph + q, q + str(v) + q)
        out = out.replace(ph, quote_arg(v))
    return out


def wait_port(port, timeout):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False


def http_get(url, timeout=15):
    t0 = time.time()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            body = r.read()
            return r.status, len(body), round(time.time() - t0, 2), body[:200].decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        body = e.read()
        return e.code, len(body), round(time.time() - t0, 2), body[:200].decode("utf-8", "replace")
    except Exception as e:  # 연결 실패 등
        return None, 0, round(time.time() - t0, 2), str(e)[:200]


def run_cli(a):
    out = Path(a.out) if a.out else None
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            out.unlink()
    cmd = fill(a.cmd, data=a.data, out=a.out or "")
    print(f"실행: {cmd}")
    t0 = time.time()
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    dt = round(time.time() - t0, 1)
    fails = []
    print(f"- 종료 코드 {p.returncode} · {dt}초")
    if p.returncode != 0:
        fails.append(f"종료 코드 {p.returncode}")
    if out:
        if not out.exists() or out.stat().st_size == 0:
            fails.append(f"출력 파일 없음/비어 있음: {out}")
        else:
            n = sum(1 for _ in out.open(encoding="utf-8-sig", errors="replace"))
            print(f"- 출력 파일 {out} · {n}줄")
    if p.stderr.strip():
        print("- stderr 끝부분:\n" + "\n".join(p.stderr.strip().splitlines()[-8:]))
    return fails


def run_server(a):
    cmd = fill(a.cmd, data=a.data, port=a.port)
    print(f"서버 실행: {cmd}")
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    fails = []
    try:
        if not wait_port(a.port, a.timeout):
            proc.poll()
            err = proc.stderr.read().decode("utf-8", "replace")[-800:] if proc.returncode is not None else ""
            return [f"서버가 {a.timeout}초 안에 포트 {a.port}를 열지 않음. {err}"]
        base = f"http://127.0.0.1:{a.port}"
        keys = [k for k in (a.keys or "").split(",") if k]
        if a.keys_url:
            try:
                with urllib.request.urlopen(base + a.keys_url, timeout=15) as r:
                    data = json.loads(r.read())
                if isinstance(data, dict):
                    data = next((v for v in data.values() if isinstance(v, list)), [])
                keys += [str(k) for k in data]
            except Exception as e:
                fails.append(f"키 목록 경로 실패 {a.keys_url}: {e}")
        print(f"- 서버 준비됨 · 키 {len(keys)}개\n")
        print("| 경로 | 상태 | 바이트 | 초 |")
        print("| --- | --- | --- | --- |")
        paths = []
        for p in a.path:
            if "{key}" in p:
                paths += [p.replace("{key}", k) for k in keys]
            else:
                paths.append(p)
        for p in paths:
            st, size, sec, head = http_get(base + p)
            ok = st is not None and 200 <= st < 300 and size > 0
            print(f"| {p} | {st} | {size} | {sec} |")
            if not ok:
                fails.append(f"{p} → {st} {head[:80]}")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    return fails


def main():
    ap = argparse.ArgumentParser(description="지정 명령으로 끝까지 돌려 실패 수를 센다")
    sub = ap.add_subparsers(dest="mode", required=True)
    c = sub.add_parser("cli", help="CLI 과제")
    c.add_argument("--cmd", required=True, help="실행 명령. {data} {out} 자리표시자 사용 가능")
    c.add_argument("--data", default="data")
    c.add_argument("--out", help="확인할 출력 파일 경로 (실행 전에 지움)")
    s = sub.add_parser("server", help="웹 서비스 과제")
    s.add_argument("--cmd", required=True, help="서버 실행 명령. {port} {data} 자리표시자 사용 가능")
    s.add_argument("--data", default="data")
    s.add_argument("--port", type=int, default=8765)
    s.add_argument("--path", action="append", default=[], help="호출할 경로. 여러 번 지정 가능. {key} 사용 가능")
    s.add_argument("--keys", help="쉼표로 구분한 키 목록 (예: 날짜)")
    s.add_argument("--keys-url", help="키 목록(JSON 배열)을 돌려주는 경로")
    s.add_argument("--timeout", type=int, default=30)
    a = ap.parse_args()
    if a.mode == "server" and not a.path:
        a.path = ["/"]
    fails = run_cli(a) if a.mode == "cli" else run_server(a)
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