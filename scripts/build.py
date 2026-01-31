#!/usr/bin/env python3
"""
Markdown Static Site Generator
Usage: python3 build.py
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path

# Config
SITE_ROOT = Path(__file__).parent.parent
CONTENT_DIR = SITE_ROOT / "content"
OUTPUT_DIR = SITE_ROOT
PUBLIC_DIR = SITE_ROOT / "public"

# Categories
CATEGORIES = {
    "技术": {"name": "技术", "icon": "💻"},
    "生活": {"name": "生活", "icon": "🌱"},
    "项目": {"name": "项目", "icon": "🚀"}
}

# Navigation HTML template
NAV_TEMPLATE = '''
    <nav class="sidebar">
        <div class="nav-header">
            <a href="/" class="nav-avatar">👤</a>
            <a href="/" class="nav-name">Shawn</a>
        </div>
        <ul class="nav-menu">
            <li><a href="/" class="{home}">首页</a></li>
            <li><a href="/技术/" class="{技术}">技术</a></li>
            <li><a href="/生活/" class="{生活}">生活</a></li>
            <li><a href="/项目/" class="{项目}">项目</a></li>
        </ul>
    </nav>
'''

FOOTER = '''
    <script src="/js/main.js"></script>
</body>
</html>
'''


def parse_frontmatter(content):
    """Parse YAML frontmatter from markdown"""
    pattern = r'^---\n(.*?)\n---\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)
    if match:
        frontmatter = parse_yaml(match.group(1))
        markdown = match.group(2)
        return frontmatter, markdown
    return {}, content


def parse_yaml(yaml_str):
    """Simple YAML parser for frontmatter"""
    result = {}
    for line in yaml_str.strip().split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            result[key] = value
    return result


def markdown_to_html(markdown):
    """Convert markdown to HTML"""
    html = markdown

    # Code blocks
    html = re.sub(r'```(\w*)\n(.*?)```', r'<pre><code>\2</code></pre>', html, flags=re.DOTALL)

    # Inline code
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)

    # Headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # Bold
    html = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', html)

    # Italic
    html = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', html)

    # Links - convert internal links to relative paths
    def fix_link(match):
        text = match.group(1)
        url = match.group(2)
        # Skip external links
        if url.startswith('http'):
            return f'<a href="{url}">{text}</a>'
        
        # Map English to Chinese categories
        url = url.replace('tech/', '技术/')
        url = url.replace('life/', '生活/')
        url = url.replace('projects/', '项目/')
        url = url.replace('/tech/', '/技术/')
        url = url.replace('/life/', '/生活/')
        url = url.replace('/projects/', '/项目/')
        
        # Ensure absolute paths
        if not url.startswith('/') and not url.startswith('./') and not url.startswith('../'):
            url = '/' + url
        
        # Remove .md extension
        url = re.sub(r'\.md$', '', url)
        # Add index.html for category/article roots
        if url.endswith('/') and not url.endswith('index.html'):
            url = url + 'index.html'
        elif not url.endswith('.html') and not url.endswith('/'):
            url = url + '/index.html'
        
        return f'<a href="{url}">{text}</a>'

    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', fix_link, html)

    # Images
    html = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', html)

    # Lists
    html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'(<li>.*</li>\n?)+', r'<ul>\g<0></ul>', html)

    # Paragraphs
    html = re.sub(r'\n\n+', r'</p><p>', html)
    html = f'<p>{html}</p>'

    # Clean up
    html = html.replace('</p><p></p>', '')
    html = html.replace('<p></p>', '')

    return html


def generate_nav(current_page):
    """Generate navigation with active state"""
    pages = {
        "home": "",
        "技术": "",
        "生活": "",
        "项目": ""
    }
    if current_page in pages:
        pages[current_page] = "active"
    
    return NAV_TEMPLATE.format(**pages)


def wrap_page(title, content, current_page="home"):
    """Wrap content in full HTML page"""
    nav = generate_nav(current_page)
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | Shawn</title>
    <link rel="stylesheet" href="/css/style.css">
</head>
<body>
{nav}
    <main class="main-content">
        {content}
    </main>
{FOOTER}'''


def get_all_posts():
    """Get all posts from all categories"""
    posts = []
    for cat_key, cat_info in CATEGORIES.items():
        cat_dir = CONTENT_DIR / cat_key
        if not cat_dir.exists():
            continue

        for md_file in cat_dir.glob('*.md'):
            with open(md_file) as f:
                content = f.read()

            frontmatter, markdown = parse_frontmatter(content)
            slug = md_file.stem

            posts.append({
                "slug": slug,
                "category": cat_key,
                "category_name": cat_info["name"],
                "title": frontmatter.get("title", slug),
                "date": frontmatter.get("date", ""),
                "tags": frontmatter.get("tags", ""),
                "description": frontmatter.get("description", ""),
                "content": markdown_to_html(markdown),
                "filename": md_file.name
            })

    # Sort by date
    posts.sort(key=lambda x: x["date"], reverse=True)
    return posts


def generate_index(posts):
    """Generate index.html"""
    # Get latest posts per category
    技术_posts = [p for p in posts if p["category"] == "技术"][:3]
    生活_posts = [p for p in posts if p["category"] == "生活"][:3]
    项目_posts = [p for p in posts if p["category"] == "项目"][:3]

    html = f'''
    <div class="hero">
        <h1>你好，我是 Shawn</h1>
        <p>探索技术 · 创造价值 · 持续学习<br>在这里记录我的学习笔记、技术分享和生活思考</p>
    </div>

    <section class="section">
        <div class="section-header">
            <h2 class="section-title">💻 技术文章</h2>
            <a href="/技术/" class="section-more">查看更多 →</a>
        </div>
        <div class="post-list">
            {generate_post_cards(技术_posts)}
        </div>
    </section>

    <section class="section">
        <div class="section-header">
            <h2 class="section-title">🌱 生活随笔</h2>
            <a href="/生活/" class="section-more">查看更多 →</a>
        </div>
        <div class="post-list">
            {generate_post_cards(生活_posts)}
        </div>
    </section>

    <section class="section">
        <div class="section-header">
            <h2 class="section-title">🚀 项目展示</h2>
            <a href="/项目/" class="section-more">查看更多 →</a>
        </div>
        <div class="post-list">
            {generate_post_cards(项目_posts)}
        </div>
    </section>
    '''

    return wrap_page("首页", html, "home")


def generate_post_cards(posts):
    """Generate HTML for post cards"""
    if not posts:
        return '<p style="color: var(--text-secondary);">暂无内容</p>'

    cards = []
    for post in posts:
        cards.append(f'''
        <a href="/{post['category']}/{post['slug']}/" class="post-card">
            <h3>{post['title']}</h3>
            <p>{post['description']}</p>
            <div class="meta">
                <span>📅 {post['date']}</span>
                <span>🏷️ {post['tags']}</span>
            </div>
        </a>
        ''')
    return '\n'.join(cards)


def generate_category_page(posts, category):
    """Generate category listing page"""
    cat_info = CATEGORIES[category]

    cat_posts = [p for p in posts if p["category"] == category]

    html = f'''
    <div class="section">
        <h2 class="section-title" style="font-size: 28px; margin-bottom: 30px;">
            {cat_info['icon']} {cat_info['name']}
        </h2>
        <div class="post-list">
            {generate_post_cards(cat_posts)}
        </div>
    </div>
    '''

    return wrap_page(cat_info["name"], html, category)


def generate_post_page(post):
    """Generate single post page"""
    html = f'''
    <article class="post">
        <header class="post-header">
            <span class="post-category">{post['category_name']}</span>
            <h1 class="post-title">{post['title']}</h1>
            <div class="post-meta">
                <span>📅 {post['date']}</span>
                <span>🏷️ {post['tags']}</span>
            </div>
        </header>
        <div class="post-content">
            {post['content']}
        </div>
        <footer class="post-footer">
            <a href="/{post['category']}/">← 返回{post['category_name']}</a>
        </footer>
    </article>
    '''

    return wrap_page(post["title"], html, post["category"])


def build():
    """Build the site"""
    print("🚀 Building site...")

    # Get all posts
    posts = get_all_posts()
    print(f"📄 Found {len(posts)} posts")

    # Generate index
    print("📝 Generating index.html...")
    with open(OUTPUT_DIR / "index.html", "w") as f:
        f.write(generate_index(posts))

    # Generate category pages
    for cat_key in CATEGORIES:
        print(f"📝 Generating {cat_key}/index.html...")
        cat_dir = OUTPUT_DIR / cat_key
        cat_dir.mkdir(exist_ok=True)

        with open(cat_dir / "index.html", "w") as f:
            f.write(generate_category_page(posts, cat_key))

    # Generate individual posts
    for post in posts:
        print(f"📝 Generating {post['category']}/{post['slug']}/index.html...")
        post_dir = OUTPUT_DIR / post["category"] / post["slug"]
        post_dir.mkdir(parents=True, exist_ok=True)

        with open(post_dir / "index.html", "w") as f:
            f.write(generate_post_page(post))

    # Copy public files
    print("📦 Copying public assets...")
    for item in PUBLIC_DIR.rglob("*"):
        if item.is_file():
            rel_path = item.relative_to(PUBLIC_DIR)
            dest = OUTPUT_DIR / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            with open(item, 'rb') as src:
                with open(dest, 'wb') as dst:
                    dst.write(src.read())

    print("✅ Build complete!")
    print(f"📁 Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    build()
