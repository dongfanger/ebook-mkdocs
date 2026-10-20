#!/usr/bin/env python3
"""扫描 docs 目录,生成 mkdocs.yml。

目录顺序在此脚本内硬编码维护(不再依赖 Sphinx 的 _index.rst / index.rst):
  - TOP_ORDER:一级目录顺序
  - SUB_ORDER:各一级目录下的二级目录顺序
文章 .md 文件按文件名排序(数字前缀天然有序)。

用法: python3 gen_nav.py > mkdocs.yml
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # 项目根目录
SRC = ROOT / "docs"

# 不参与导航的内容目录
SKIP_DIRS = {"_static", "_images", "assets", ".git", "__pycache__"}

# 一级目录顺序(留空 = 按目录名自动扫描排序;想固定顺序就填,如 ["分类A", "分类B"])
TOP_ORDER = []

# 各一级目录下的二级目录顺序(留空 = 自动扫描;如 {"分类A": ["子分类1", "子分类2"]})
SUB_ORDER = {}


def list_subdirs(dpath: Path, order: list[str]) -> list[str]:
    """按指定顺序返回子目录名,兜底补上 order 未列到但实际存在的目录(按名排序)。"""
    sub_dirs = [name for name in order if (dpath / name).is_dir()]
    for child in sorted(p for p in dpath.iterdir()
                        if p.is_dir() and p.name not in SKIP_DIRS):
        if child.name not in sub_dirs:
            sub_dirs.append(child.name)
    return sub_dirs


def emit_md_lines(lines, dpath: Path, indent: str):
    """输出一个二级目录下的文章 .md(按文件名排序)。"""
    for md in sorted(dpath.glob("*.md")):
        rel = md.relative_to(SRC).as_posix()
        lines.append(f"{indent}- {rel}")


def build_nav():
    lines = ["nav:"]
    # 首页: 优先 简介.md,回退 index.md(兼容旧命名)
    home = "简介.md" if (SRC / "简介.md").exists() else "index.md"
    lines.append(f"  - 简介: {home}")

    # 根目录下其余 .md(如 关于本书.md)作为顶层导航项,按文件名排序
    for md in sorted(SRC.glob("*.md")):
        if md.name == home:
            continue
        lines.append(f"  - {md.stem}: {md.name}")

    # 一级目录按硬编码顺序,兜底补上未列到的目录
    for top in list_subdirs(SRC, TOP_ORDER):
        top_path = SRC / top
        lines.append(f"  - {top}:")
        for sub in list_subdirs(top_path, SUB_ORDER.get(top, [])):
            lines.append(f"      - {sub}:")
            emit_md_lines(lines, top_path / sub, indent="        ")

    return "\n".join(lines)


HEADER = """site_name: My Docs
site_description: 基于 mkdocs 的技术电子书

theme:
  name: readthedocs

plugins:
  - search:
      lang: zh

markdown_extensions:
  - admonition
  - codehilite
  - attr_list

# 扁平 URL(/xxx.html 而非 /xxx/)
use_directory_urls: false

# 自定义样式:blockquote 引用块(主题默认无样式)
extra_css:
  - _static/css/extra.css

# 中文搜索:构建后用纯 JS 分词器覆盖默认 lunr.zh.js(修复 nodejieba 依赖导致的搜索失效)
hooks:
  - scripts/post_build.py

"""

if __name__ == "__main__":
    print(HEADER + build_nav())
