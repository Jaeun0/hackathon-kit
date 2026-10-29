#!/usr/bin/env python3
"""hackathon-kit 설치. Windows·macOS·Linux 공용, 표준 라이브러리만 사용.
반드시 codex를 실행하기 전에 돌린다 (AGENTS.md는 세션 시작 때만 읽힌다).

    python install.py --workspace <과제 폴더>
    python install.py --workspace . --dry-run            # 무엇을 할지 보기만
    python install.py --workspace . --also-codex-home    # /skills에 안 보이면 ~/.codex/skills에도 복사

하는 일
  1. skills/kit-* 를 ~/.agents/skills/ 에 복사 (기존 kit-* 만 덮어씀)
  2. 과제 폴더에 AGENTS.md 배치 (이미 있으면 키트 규칙을 덧붙임, 두 번 붙이지 않음)
  3. 과제 폴더에 templates/*.md 복사 (같은 이름 파일이 있으면 건드리지 않음)
  4. git 저장소면 verify/holdout/ 을 로컬 제외(.git/info/exclude)에 추가
"""
import argparse
import shutil
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

KIT = Path(__file__).resolve().parent
MARK = "<!-- hackathon-kit rules -->"


def log(msg):
    print(msg)


def copy_skills(dst_root, dry):
    dst_root = Path(dst_root).expanduser()
    names = []
    for src in sorted((KIT / "skills").iterdir()):
        if not (src / "SKILL.md").exists():
            continue
        dst = dst_root / src.name
        names.append(src.name)
        if not dry:
            if dst.exists():
                shutil.rmtree(dst)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
    log(f"- 스킬 {len(names)}개 → {dst_root}  ({', '.join(names)})")
    return dst_root


def kit_rules(skills_root):
    text = (KIT / "AGENTS.md").read_text(encoding="utf-8")
    rules, _, _ = text.partition("## 담당자 확인 사항")
    tools = Path(skills_root) / "kit-tools" / "scripts"
    rules = rules.rstrip() + f"\n13. 키트 스크립트 위치: {tools} (본문을 읽지 말고 --help로 사용법 확인)\n"
    return rules


def place_agents(ws, skills_root, dry):
    target = ws / "AGENTS.md"
    rules = kit_rules(skills_root)
    if not target.exists():
        body = rules + "## 담당자 확인 사항\n"
        if not dry:
            target.write_text(body, encoding="utf-8")
        log(f"- AGENTS.md 새로 만듦 → {target}")
        return
    cur = target.read_text(encoding="utf-8")
    if MARK in cur or "1. 나는 결정, 너는 실행·확인" in cur:
        log("- AGENTS.md에 키트 규칙이 이미 있음, 그대로 둠")
        return
    block = "\n\n" + MARK + "\n" + rules.replace("# AGENTS.md\n", "", 1)
    if "## 담당자 확인 사항" not in cur:
        block += "\n## 담당자 확인 사항\n"
    if not dry:
        target.write_text(cur.rstrip() + block, encoding="utf-8")
    log("- 기존 AGENTS.md 끝에 키트 규칙을 덧붙임 (원래 내용은 그대로)")


def place_templates(ws, dry):
    done, kept = [], []
    for t in sorted((KIT / "templates").glob("*.md")):
        dst = ws / t.name
        if dst.exists():
            kept.append(t.name)
            continue
        done.append(t.name)
        if not dry:
            shutil.copy2(t, dst)
    log(f"- 템플릿 복사: {', '.join(done) or '없음'}" + (f" · 이미 있어 둠: {', '.join(kept)}" if kept else ""))


def exclude_holdout(ws, dry):
    ex = ws / ".git" / "info" / "exclude"
    if not ex.parent.exists():
        log("- git 저장소가 아님: 제외 설정 건너뜀")
        return
    cur = ex.read_text(encoding="utf-8") if ex.exists() else ""
    if "verify/holdout/" in cur:
        return
    if not dry:
        ex.write_text(cur.rstrip("\n") + "\nverify/holdout/\n", encoding="utf-8")
    log("- verify/holdout/ 을 git 로컬 제외에 추가")


def main():
    ap = argparse.ArgumentParser(description="hackathon-kit 설치 (codex 실행 전에)")
    ap.add_argument("--workspace", default=".", help="과제 폴더 (기본: 현재 폴더)")
    ap.add_argument("--skills-dir", default=str(Path.home() / ".agents" / "skills"))
    ap.add_argument("--also-codex-home", action="store_true", help="~/.codex/skills 에도 복사")
    ap.add_argument("--dry-run", action="store_true", help="실제로 바꾸지 않고 할 일만 출력")
    a = ap.parse_args()
    ws = Path(a.workspace).resolve()
    if not ws.is_dir():
        log(f"과제 폴더가 없음: {ws}")
        return 1
    if ws == KIT or KIT in ws.parents:
        log("키트 폴더 안에는 설치하지 않는다. 과제 폴더를 --workspace로 지정할 것")
        return 1
    log(f"# hackathon-kit 설치{' (dry-run)' if a.dry_run else ''}\n- 과제 폴더: {ws}")
    root = copy_skills(a.skills_dir, a.dry_run)
    if a.also_codex_home:
        copy_skills(Path.home() / ".codex" / "skills", a.dry_run)
    place_agents(ws, root, a.dry_run)
    place_templates(ws, a.dry_run)
    exclude_holdout(ws, a.dry_run)
    log("\n다음: 과제 폴더에서 codex 실행 → /skills 에 kit-* 가 보이는지 확인.")
    log(f"안 보이면: python \"{KIT / 'install.py'}\" --workspace \"{ws}\" --also-codex-home 후 codex 재시작.")
    log(f"그래도 안 보이면 스킬 없이 {KIT / 'PROMPTS.md'} 의 긴 프롬프트를 복사해 쓴다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
