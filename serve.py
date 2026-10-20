#!/usr/bin/env python3
"""本地预览: 校验 → 生成导航 → mkdocs serve。

双击运行,或终端执行: ./.venv/bin/python serve.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
VENV = ROOT / ".venv" / "bin"
PY = VENV / "python"
MK = VENV / "mkdocs"


def main():
    print("== 1/3 校验 markdown ==")
    r = subprocess.run([str(PY), "verify.py"], cwd=SCRIPTS)
    if r.returncode != 0:
        sys.exit(r.returncode)

    print("== 2/3 生成导航 ==")
    nav = subprocess.run([str(PY), "gen_nav.py"], cwd=SCRIPTS, capture_output=True, text=True)
    if nav.returncode != 0:
        print(nav.stderr)
        sys.exit(nav.returncode)
    (ROOT / "mkdocs.yml").write_text(nav.stdout, encoding="utf-8")

    print("== 3/3 启动预览 (Ctrl+C 退出) ==")
    subprocess.run([str(MK), "serve", "--clean"], cwd=ROOT)


if __name__ == "__main__":
    main()
