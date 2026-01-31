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
TEMPLATES_DIR = SITE_ROOT / "templates"
OUTPUT_DIR = SITE_ROOT
PUBLIC_DIR = SITE_ROOT / "public"

# Categories
CATEGORIES = {
    "tech": {"name": "技术", "icon": "💻"},
    "life": {"name": "生活", "icon": "🌱"},
    "projects": {"name": "项目", "icon": "🚀"}
}


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

    # Links
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)

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


def load_template(name):
    """Load template file"""
    with open(TEMPLATES_DIR / name) as f:
        return f.read()


def render_template(template, **kwargs):
    """Simple template renderer"""
    result = template
    for key, value in kwargs.items():
        result = result.replace(f'{{{{{key}}}}}', str(value))
    return result


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
    template = load_template("page.html")

    # Get latest posts per category
    tech_posts = [p for p in posts if p["category"] == "tech"][:3]
    life_posts = [p for p in posts if p["category"] == "life"][:3]
    projects_posts = [p for p in posts if p["category"] == "projects"][:3]

    html = f"""
    <div class="hero">
        <h1>你好，我是 Shawn</h1>
        <p>探索技术 · 创造价值 · 持续学习<br>在这里记录我的学习笔记、技术分享和生活思考</p>
    </div>

    <section class="section">
        <div class="section-header">
            <h2 class="section-title">💻 技术文章</h2>
            <a href="/tech/" class="section-more">查看更多 →</a>
        </div>
        <div class="post-list">
            {generate_post_cards(tech_posts)}
        </div>
    </section>

    <section class="section">
        <div class="section-header">
            <h2 class="section-title">🌱 生活随笔</h2>
            <a href="/life/" class="section-more">查看更多 →</a>
        </div>
        <div class="post-list">
            {generate_post_cards(life_posts)}
        </div>
    </section>

    <section class="section">
        <div class="section-header">
            <h2 class="section-title">🚀 项目展示</h2>
            <a href="/projects/" class="section-more">查看更多 →</a>
        </div>
        <div class="post-list">
            {generate_post_cards(projects_posts)}
        </div>
    </section>
    """

    return render_template(template,
        title="首页",
        content=html,
        is_home=True
    )


def generate_post_cards(posts):
    """Generate HTML for post cards"""
    if not posts:
        return '<p style="color: var(--text-secondary);">暂无内容</p>'

    cards = []
    for post in posts:
        cards.append(f'''
        <a href="{post['category']}/{post['slug']}/index.html" class="post-card">
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
    template = load_template("page.html")
    cat_info = CATEGORIES[category]

    cat_posts = [p for p in posts if p["category"] == category]

    html = f"""
    <div class="section">
        <h2 class="section-title" style="font-size: 28px; margin-bottom: 30px;">
            {cat_info['icon']} {cat_info['name']}
        </h2>
        <div class="post-list">
            {generate_post_cards(cat_posts)}
        </div>
    </div>
    """

    is_tech = category == "tech"
    is_life = category == "life"
    is_projects = category == "projects"

    return render_template(template,
        title=cat_info["name"],
        content=html,
        **{"is_tech": is_tech, "is_life": is_life, "is_projects": is_projects}
    )


def generate_post_page(post):
    """Generate single post page"""
    template = load_template("page.html")
    post_template = load_template("post.html")

    html = render_template(post_template,
        category=post["category_name"],
        title=post["title"],
        date=post["date"],
        tags=post["tags"],
        content=post["content"]
    )

    is_tech = post["category"] == "tech"
    is_life = post["category"] == "life"
    is_projects = post["category"] == "projects"

    return render_template(template,
        title=post["title"],
        content=html,
        **{"is_tech": is_tech, "is_life": is_life, "is_projects": is_projects}
    )


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
        print(f"📝 Generating {post['category']}/{post['slug']}.html...")
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
