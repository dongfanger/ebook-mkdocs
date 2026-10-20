#!/usr/bin/env python3
"""部署到 GitHub Pages: 清空目标仓库 → 复制 site → git add/commit/push。

先本地预览(生成 site 产物)确认无误后再运行本脚本。
双击运行,或终端执行: ./.venv/bin/python deploy.py

前置条件:
  1. 平级目录下已 clone 你的 GitHub Pages 仓库(SSH key 或 HTTPS 凭据配好)
  2. 该目录当前分支即 GitHub Pages 展示分支(origin 已配好上游)

流程:
  1. 清空目标仓库内所有文件(保留 .git)
  2. 复制 site/ 全部内容到目标仓库
  3. git add -A → git commit → git push
"""
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent            # 本项目根目录
SITE = ROOT / "site"                              # 构建产物
MK = ROOT / ".venv" / "bin" / "mkdocs"            # mkdocs 可执行文件

# ⚠️ 改成你自己的 GitHub Pages 仓库名(与本项目平级,已 clone 且配好推送)
TARGET = ROOT.parent / "yourname.github.io"

COMMIT_MSG = f"deploy: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"


def run(cmd, cwd):
    print(f"  $ {' '.join(cmd)}")
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr.strip())
        sys.exit(r.returncode)
    return r


def clear_target():
    """清空目标目录内所有条目,保留 .git。"""
    for item in TARGET.iterdir():
        if item.name == ".git":
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
        print(f"  🗑️  删除 {item.relative_to(TARGET)}")


def copy_site():
    shutil.copytree(SITE, TARGET, dirs_exist_ok=True)
    # 放一个空的 .nojekyll,明确禁用 GitHub Pages 的 Jekyll 处理
    (TARGET / ".nojekyll").write_text("", encoding="utf-8")
    print(f"  📦 复制 {SITE} → {TARGET}")
    print("  🚫 写入 .nojekyll")


def build():
    """部署前强制重新构建 site,确保推送的是当前源码的最新产物。"""
    print("  $ mkdocs build --clean")
    r = subprocess.run([str(MK), "build", "--clean"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr.strip())
        sys.exit(r.returncode)


def main():
    if not (TARGET / ".git").is_dir():
        print(f"❌ 未找到 git 仓库: {TARGET}")
        sys.exit(1)

    print("== 1/4 构建 site ==")
    build()
    print("== 2/4 清空目标仓库 ==")
    clear_target()
    print("== 3/4 复制 site 产物 ==")
    copy_site()

    print("== 4/4 git 提交并推送 ==")
    run(["git", "add", "-A"], cwd=TARGET)
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=TARGET, capture_output=True, text=True,
    )
    if not status.stdout.strip():
        print("  ℹ️  无变更,跳过提交")
        return
    run(["git", "commit", "-m", COMMIT_MSG], cwd=TARGET)
    run(["git", "push"], cwd=TARGET)
    print("\n✅ 部署完成")


if __name__ == "__main__":
    main()
