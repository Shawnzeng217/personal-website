# Shawn's Personal Website

使用 Markdown + Python 构建的静态个人网站。

## 目录结构

```
personal-website/
├── content/           # Markdown 内容
│   ├── tech/         # 技术文章
│   ├── life/         # 生活随笔
│   └── projects/     # 项目展示
├── templates/        # HTML 模板
│   ├── page.html     # 页面骨架
│   └── post.html     # 文章模板
├── scripts/          # 构建脚本
│   └── build.py      # 主构建脚本
├── public/           # 静态资源
│   ├── css/
│   ├── js/
│   └── images/
├── index.html        # 生成的网站
├── requirements.txt
└── README.md
```

## 使用方法

### 1. 添加新文章

在 `content/{category}/` 下创建 `.md` 文件：

```markdown
---
title: 文章标题
date: 2026-01-01
tags: 标签1,标签2
description: 简短描述
---

# 文章内容

使用 Markdown 编写...
```

### 2. 构建网站

```bash
python3 scripts/build.py
```

### 3. 本地预览

```bash
# 方法 1: 使用 Python
cd public && python3 -m http.server 8080

# 方法 2: VS Code Live Server
# 右键 index.html -> Open with Live Server
```

### 4. 发布

```bash
# 推送到 GitHub
git add .
git commit -m "Add new post: xxx"
git push

# GitHub Pages 会自动部署
```

## 支持的 Markdown

- 标题 `# ## ###`
- 加粗 `**text**`
- 斜体 `*text*`
- 代码 `` `code` ``
- 代码块 ` ``` `
- 链接 `[text](url)`
- 图片 `![alt](url)`
- 列表 `- item`

## 部署

网站使用 GitHub Pages 自动部署：

1. Push 到 GitHub
2. Settings → Pages → Source: main branch
3. 访问 `https://yourname.github.io/repo-name/`
