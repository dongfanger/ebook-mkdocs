#!/usr/bin/env python3
"""整理 + 校验 docs 下的 Markdown,作为部署主线硬门禁,任一步失败即中断。

整合自 tools/ 下四个脚本:
  - rewrite_md_heads.py : 重写 md 头部(标题 + 固定文本),幂等
  - reorganize.py       : 图片统一到 assets/uuid + 文件编号,幂等
  - check_fix_image.py  : 图片匹配检查(断链/孤儿/空 assets)
  - md_head_scan.py     : 头部格式 + 一级标题数量检查

只处理 6 位数字前缀的文章(000001-xxx.md);根目录 简介.md/关于本书.md
及无前缀特例文件(如「原创电子书全新重磅升级.md」)一律跳过。
"""
import os
import re
import shutil
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs"
FIXED = "> 本文版权归作者所有，未经授权请勿转载。"

PREFIX_RE = re.compile(r"^(\d{6})-(.*)\.md$")
UUID_RE = re.compile(r"^[0-9a-f]{32}\.(.+)$", re.IGNORECASE)
IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico", ".tiff"}
MD_IMG_RE = re.compile(r'!\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
HTML_IMG_RE = re.compile(r'<img[^>]*?\ssrc\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
REMOTE_RE = re.compile(r"^(https?://|//|data:)", re.IGNORECASE)
_H1 = re.compile(r"^#\s+(.+)$")

failures = []


def fail(msg):
    """记录一个致命问题;校验阶段结束后统一中断。"""
    failures.append(msg)


def is_remote(src):
    return bool(REMOTE_RE.match(src))


def article_md_files():
    """返回所有 6 位前缀文章的 Path 列表(跳过根目录与无前缀特例)。"""
    out = []
    for md in SRC.rglob("*.md"):
        if PREFIX_RE.match(md.name):
            out.append(md)
    return sorted(out)


def extract_srcs(body):
    srcs = MD_IMG_RE.findall(body) + HTML_IMG_RE.findall(body)
    return srcs


def resolve(src, md_dir):
    """把图片引用解析为本地绝对路径;远程/非法返回 None。"""
    if is_remote(src):
        return None
    clean = src.split("#", 1)[0].split("?", 1)[0]
    if os.path.isabs(clean):
        return os.path.normpath(clean)
    return os.path.normpath(os.path.join(md_dir, clean))


# ============================================================
# 步骤 1:重写头部(幂等)
# ============================================================
def rewrite_heads(files):
    changed = 0
    for md in files:
        content = md.read_text(encoding="utf-8")
        lines = content.splitlines()
        if len(lines) >= 3 and lines[2] == FIXED:
            continue
        title = PREFIX_RE.match(md.name).group(2)
        new_head = [f"# {title}", "", FIXED, ""]
        tail = lines[3:]
        md.write_text("\n".join(new_head + tail) + "\n", encoding="utf-8")
        print(f"  ✏️  重写头部: {md.relative_to(SRC)}")
        changed += 1
    if changed:
        print(f"  [头部] 重写 {changed} 个文件")
    return changed


# ============================================================
# 步骤 2:图片整理(统一到 assets/uuid,幂等)
# ============================================================
def reorganize_images(files):
    moved = 0
    for md in files:
        md_dir = md.parent
        body = md.read_text(encoding="utf-8")
        srcs = extract_srcs(body)
        replacements = {}
        for src in srcs:
            if src in replacements or is_remote(src):
                continue
            abs_path = resolve(src, str(md_dir))
            if not abs_path or not os.path.isfile(abs_path):
                # 缺失图片 → 记录,由步骤 3 统一中断
                continue
            clean = src.split("#", 1)[0].split("?", 1)[0]
            if clean.startswith("assets/"):
                if UUID_RE.match(os.path.basename(clean)):
                    continue  # 已合规
            assets_dir = md_dir / "assets"
            assets_dir.mkdir(exist_ok=True)
            ext = os.path.splitext(abs_path)[1]
            new_name = uuid.uuid4().hex + ext
            shutil.copy2(abs_path, assets_dir / new_name)
            replacements[src] = f"assets/{new_name}"
            moved += 1
        if replacements:
            for old, new in replacements.items():
                body = body.replace(old, new)
            md.write_text(body, encoding="utf-8")
            print(f"  🖼️  整理图片: {md.relative_to(SRC)}")
    if moved:
        print(f"  [图片] 整理 {moved} 张图片")
    return moved


# ============================================================
# 步骤 3:图片匹配检查(断链/孤儿/空 assets,失败即中断)
# ============================================================
def check_images(files):
    seen_dirs = {}
    for md in files:
        seen_dirs.setdefault(md.parent, []).append(md)

    for md_dir, md_list in seen_dirs.items():
        assets_dir = md_dir / "assets"
        all_imgs = set()
        if assets_dir.is_dir():
            all_imgs = {
                f for f in os.listdir(assets_dir)
                if os.path.splitext(f)[1].lower() in IMG_EXTS
                and os.path.isfile(assets_dir / f)
            }
        referenced = set()
        for md in md_list:
            body = md.read_text(encoding="utf-8")
            for src in extract_srcs(body):
                if is_remote(src):
                    continue
                abs_path = resolve(src, str(md_dir))
                if not abs_path:
                    continue
                if not os.path.isfile(abs_path):
                    fail(f"断链图片: {md.relative_to(SRC)} → {src}")
                else:
                    referenced.add(os.path.basename(abs_path))

        # 空 assets → 删除
        if assets_dir.is_dir() and not all_imgs:
            shutil.rmtree(assets_dir)
            print(f"  🗑️  删除空 assets: {assets_dir.relative_to(SRC)}")
        # 孤儿图片 → 删除
        for img in sorted(all_imgs - referenced):
            os.remove(assets_dir / img)
            print(f"  🗑️  删除孤儿图片: {assets_dir.relative_to(SRC)}/{img}")


# ============================================================
# 步骤 4:头部 + 一级标题检查(失败即中断)
# ============================================================
def check_heads(files):
    for md in files:
        title = PREFIX_RE.match(md.name).group(2)
        lines = md.read_text(encoding="utf-8").splitlines()
        if not lines or lines[0] != f"# {title}":
            fail(f"头部第1行应为 '# {title}': {md.relative_to(SRC)}")
        if len(lines) < 2 or lines[1].strip() != "":
            fail(f"头部第2行应为空行: {md.relative_to(SRC)}")
        if len(lines) < 3 or lines[2] != FIXED:
            fail(f"头部第3行应为固定文本: {md.relative_to(SRC)}")
        if len(lines) < 4 or lines[3].strip() != "":
            fail(f"头部第4行应为空行: {md.relative_to(SRC)}")
        if len(lines) < 5 or lines[4].strip() == "":
            fail(f"头部第5行应有正文: {md.relative_to(SRC)}")
        # H1 数量(跳过代码块)
        h1s, in_code = [], False
        for line in lines:
            s = line.strip()
            if s.startswith("```") or s.startswith("~~~"):
                in_code = not in_code
                continue
            if in_code:
                continue
            m = _H1.match(s)
            if m:
                h1s.append(m.group(1))
        if len(h1s) != 1:
            fail(f"一级标题应为 1 个(实际 {len(h1s)}): {md.relative_to(SRC)}")


def main():
    files = article_md_files()
    print(f"📂 扫描到 {len(files)} 篇 6 位前缀文章")

    print("\n[1/4] 重写头部...")
    rewrite_heads(files)
    print("[2/4] 整理图片...")
    reorganize_images(files)
    print("[3/4] 图片匹配检查...")
    check_images(files)
    print("[4/4] 头部 + 标题检查...")
    check_heads(files)

    if failures:
        print(f"\n❌ 发现 {len(failures)} 个问题,中断:")
        for f in failures:
            print(f"    - {f}")
        sys.exit(1)
    print("\n✅ 全部通过")


if __name__ == "__main__":
    main()
