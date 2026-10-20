#!/usr/bin/env python3
"""mkdocs hook: 构建结束后做两件事。

1. 修复中文搜索: mkdocs 1.6.1 自带的 lunr.zh.js 依赖 @node-rs/jieba(Node 端 Rust
   模块),浏览器里 nodejieba 是 undefined,搜索时 nodejieba.cut() 抛错,导致中文
   搜索失效。本 hook 在 search 插件复制完 lunr.zh.js 之后,用 docs/_static/js/lunr.zh.js 覆盖它。
2. 设置 favicon: readthedocs 主题默认引用 img/favicon.ico(mkdocs 无顶层
   site_favicon 配置项),这里把用户放到 _static/favicon.ico 的图标铺到该位置。
"""
import shutil
from pathlib import Path


def on_post_build(config, **kwargs):
    site_dir = Path(config["site_dir"])
    here = Path(__file__).resolve().parent.parent

    # 1) 中文搜索分词器
    src = here / "docs" / "_static" / "js" / "lunr.zh.js"
    dst = site_dir / "search" / "lunr.zh.js"
    if src.exists() and dst.exists():
        shutil.copyfile(src, dst)

    # 2) favicon
    favicon_src = site_dir / "_static" / "favicon.ico"
    favicon_dst = site_dir / "img" / "favicon.ico"
    if favicon_src.exists():
        favicon_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(favicon_src, favicon_dst)

    # 3) 首页别名: 首页源文件是 简介.md,构建为 简介.html,
    #    而站点根路径 / 需要 index.html。这里补一份 index.html 指向首页。
    home = site_dir / "简介.html"
    index = site_dir / "index.html"
    if home.exists() and not index.exists():
        shutil.copyfile(home, index)
