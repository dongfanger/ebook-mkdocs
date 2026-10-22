# ebook-mkdocs

基于 mkdocs 的电子书空壳模板，克隆后几分钟就能搭起自己的技术电子书。

## 特性

- **自动生成导航**：按 `docs/` 下的「分类/子分类」目录结构自动生成 `mkdocs.yml`，无需手写 nav
- **中文搜索**：内置纯 JS 分词器，修复 mkdocs 默认 `nodejieba` 依赖导致的搜索失效
- **一键预览/发布**：`serve.py` 本地预览，`deploy.py` 发布到 GitHub Pages

## 快速开始

```bash
# 1. 创建虚拟环境并安装依赖
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt

# 2. 写文章：放到 docs/分类/子分类/000001-标题.md

# 3. 本地预览
./.venv/bin/python serve.py
```

## 发布到 GitHub Pages

1. clone 你的 `yourname.github.io` 仓库到本项目**平级**目录
2. 编辑 `deploy.py`，把 `TARGET` 改成你的仓库名
3. 运行 `./.venv/bin/python deploy.py`

## 目录结构

```
├── docs/                 # 内容目录(mkdocs 默认,按分类/子分类组织)
│   ├── 简介.md            # 首页
│   ├── 关于本书.md        # 关于页
│   └── _static/          # 静态资源(extra.css / lunr.zh.js / favicon.ico)
├── scripts/
│   ├── gen_nav.py        # 扫描 docs 生成 mkdocs.yml
│   └── post_build.py     # 构建后 hook(中文搜索 + favicon)
├── serve.py              # 本地预览入口
├── deploy.py             # 部署入口
└── requirements.txt
```

## 文章命名约定

- 用 `000001-标题.md` 这种 6 位数字前缀，导航按文件名自然排序
- 无前缀的文件（如 `简介.md`）不会进入分类目录的导航

## 目录顺序

默认按目录名自动排序。想固定顺序，编辑 `scripts/gen_nav.py` 顶部的
`TOP_ORDER` 和 `SUB_ORDER` 两个变量即可。
