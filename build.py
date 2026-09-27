#!/usr/bin/env python3
"""Builds clyon.dev from Markdown. Standard library only, so it runs anywhere.

    python3 build.py                      build the site
    python3 build.py new blogs "Title"    start a blog post dated today
    python3 build.py new life "Title"     start a life post dated today

Posts live in posts/blogs/ and posts/life/ as YYYY-MM-DD-slug.md, with a small
header between --- lines (title, dek, kind, photo, draft). Images go in
posts/<section>/images/ and are referenced as images/name.jpg.

Generated (never edit by hand): index.html, blogs/, life/, projects/,
feed.xml, 404.html. loose-ends/ is its own site and is never touched.
"""
import datetime
import html
import json
import math
import os
import re
import shutil
import sys
from email.utils import format_datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
POSTS = os.path.join(ROOT, "posts")
SITE = "https://clyon.dev"
AUTHOR = "Clyon Jackson"
SECTIONS = ["blogs", "projects", "life"]
GENERATED_DIRS = ["blogs", "life", "projects"]
DESCRIPTION = "Clyon Jackson. Writing about what I'm building, and about life in between."


# ---------- Markdown (the subset posts need) ----------

def _ext(url):
    return ' target="_blank" rel="noopener"' if url.startswith("http") and "clyon.dev" not in url else ""


def inline(s, section):
    out = []
    for part in re.split(r"(`[^`]+`)", s):
        if len(part) > 1 and part.startswith("`") and part.endswith("`"):
            out.append("<code>" + html.escape(part[1:-1]) + "</code>")
            continue
        p = html.escape(part, quote=False)

        def img(m):
            src = m.group(2)
            if not src.startswith(("http", "/")):
                src = "/%s/%s" % (section, src)
            return '<img src="%s" alt="%s" loading="lazy">' % (src, m.group(1))

        p = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", img, p)
        p = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: '<a href="%s"%s>%s</a>' % (m.group(2), _ext(m.group(2)), m.group(1)), p)
        p = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", p)
        p = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", p)
        p = re.sub(r"(?<![\w])_(?!\s)(.+?)(?<!\s)_(?![\w])", r"<em>\1</em>", p)
        out.append(p)
    return "".join(out)


LIST = re.compile(r"^\s*([-*+]|\d+\.)\s+")
BLOCK_START = re.compile(r"^(#{1,4}\s|```|>|\s*([-*+]|\d+\.)\s)")


def render(md, section):
    lines = md.strip("\n").split("\n")
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):
            buf, i = [], i + 1
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            out.append("<pre><code>" + html.escape("\n".join(buf)) + "</code></pre>")
            i += 1
            continue
        m = re.match(r"(#{1,4})\s+(.*)", line)
        if m:
            n = min(len(m.group(1)) + 1, 5)  # the post title is the page's h1
            out.append("<h%d>%s</h%d>" % (n, inline(m.group(2), section), n))
            i += 1
            continue
        if re.match(r"^(-{3,}|\*{3,})\s*$", line):
            out.append("<hr>")
            i += 1
            continue
        if line.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i][1:].lstrip())
                i += 1
            out.append("<blockquote>" + render("\n".join(buf), section) + "</blockquote>")
            continue
        if LIST.match(line):
            ordered = bool(re.match(r"^\s*\d+\.", line))
            items = []
            while i < len(lines) and LIST.match(lines[i]):
                items.append(LIST.sub("", lines[i]))
                i += 1
                while i < len(lines) and lines[i].startswith("  ") and lines[i].strip() and not LIST.match(lines[i]):
                    items[-1] += " " + lines[i].strip()
                    i += 1
            tag = "ol" if ordered else "ul"
            out.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % inline(x, section) for x in items), tag))
            continue
        if line.lstrip().startswith("<"):
            buf = []
            while i < len(lines) and lines[i].strip():
                buf.append(lines[i])
                i += 1
            out.append("\n".join(buf))
            continue
        buf = []
        while i < len(lines) and lines[i].strip() and not BLOCK_START.match(lines[i]):
            buf.append(lines[i].strip())
            i += 1
        out.append("<p>%s</p>" % inline(" ".join(buf), section))
    return "\n".join(out)


def plain(fragment):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


# ---------- posts ----------

def read_posts(section):
    folder = os.path.join(POSTS, section)
    posts = []
    if not os.path.isdir(folder):
        return posts
    for name in sorted(os.listdir(folder)):
        m = re.match(r"(\d{4}-\d{2}-\d{2})-(.+)\.md$", name)
        if not m:
            continue
        raw = open(os.path.join(folder, name), encoding="utf-8").read()
        meta, body = {}, raw
        fm = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", raw, re.S)
        if fm:
            body = fm.group(2)
            for line in fm.group(1).splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip().lower()] = v.strip().strip('"').strip("'")
        if meta.get("draft", "").lower() in ("true", "yes"):
            continue
        date = datetime.date.fromisoformat(meta.get("date", m.group(1)))
        body_html = render(body, section)
        text = plain(body_html)
        slug = m.group(2)
        posts.append({
            "section": section,
            "slug": slug,
            "date": date,
            "title": meta.get("title", ""),
            "dek": meta.get("dek", ""),
            "kind": meta.get("kind", "Note" if section == "life" else ""),
            "photo": meta.get("photo", ""),
            "html": body_html,
            "text": text,
            "mins": max(1, math.ceil(len(text.split()) / 230)),
            "url": "/blogs/%s/" % slug if section == "blogs" else "/life/#%s" % slug,
        })
    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
    return posts


# ---------- markup ----------

E = html.escape
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def md_date(d):
    return "%s %d" % (MON[d.month - 1], d.day)


def long_date(d):
    return "%s %d, %d" % (MON[d.month - 1], d.day, d.year)


ICONS = {
    "blogs": '<path d="M7 3h7l5 5v11a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/><path d="M14 3v5h5"/><path d="M8.5 12.5h7M8.5 16h5"/>',
    "projects": '<path d="M9 3h6M10 3v6.2L4.6 18.4A1.7 1.7 0 0 0 6.1 21h11.8a1.7 1.7 0 0 0 1.5-2.6L14 9.2V3"/><path d="M7.2 14.5h9.6"/>',
    "life": '<path d="M3 8.5A1.5 1.5 0 0 1 4.5 7h2.8l1.5-2.2h6.4L16.7 7h2.8A1.5 1.5 0 0 1 21 8.5v9a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 17.5z"/><circle cx="12" cy="12.8" r="3.6"/>',
}


def menu(active):
    items = []
    for i, sec in enumerate(SECTIONS):
        on = ' class="on" aria-current="page"' if sec == active else ""
        items.append(
            '<li style="--i:%d"><a href="/%s/" data-sec="%s"%s><svg class="ic" viewBox="0 0 24 24" aria-hidden="true" fill="none" '
            'stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">%s</svg><span>%s</span></a></li>'
            % (i, sec, sec, on, ICONS[sec], sec.capitalize()))
    return "\n        ".join(items)


def blogs_section(blogs):
    rows = "".join(
        '<a class="row" href="%s" style="--i:%d"><time datetime="%s">%s</time><div><h2>%s</h2>%s<small>%d min read</small></div></a>'
        % (p["url"], i + 1, p["date"].isoformat(), md_date(p["date"]), E(p["title"]),
           "<p>%s</p>" % E(p["dek"]) if p["dek"] else "", p["mins"])
        for i, p in enumerate(blogs))
    return "<h1>Blogs</h1>" + (rows or '<p class="empty" style="--i:1">First post soon.</p>')


def life_section(life):
    rows = []
    for i, p in enumerate(life):
        photo = ""
        if p["photo"]:
            src = p["photo"] if p["photo"].startswith(("http", "/")) else "/life/" + p["photo"]
            photo = '<img class="photo" src="%s" alt="%s" loading="lazy">' % (E(src), E(p["title"] or p["kind"]))
        title = "<h2>%s</h2>" % E(p["title"]) if p["title"] else ""
        rows.append('<article class="row" id="%s" style="--i:%d"><time datetime="%s">%s</time><div>%s%s<div class="prose small">%s</div><small>%s</small></div></article>'
                    % (p["slug"], i + 1, p["date"].isoformat(), md_date(p["date"]), photo, title, p["html"], E(p["kind"])))
    return "<h1>Life</h1>" + ("".join(rows) or '<p class="empty" style="--i:1">First post soon.</p>')


SPIRAL = ('<svg viewBox="31.5 26.5 44 44" aria-hidden="true"><path class="t" pathLength="1" d="M52 52C57 52 57 45 51 45C42 45 42 57 52 57C65 57 65 41 51 41C34 41 34 67 53 67C74 67 74 33 51 33"/>'
          '<circle class="d" cx="51" cy="33" r="5.5"/></svg>')
FACE = ('<svg class="face" viewBox="0 0 107 98" aria-hidden="true"><g fill="none" stroke="#00E5A0" stroke-linecap="round"><line x1="18.35" y1="22.44" x2="38.07" y2="42.16" stroke-width="10.79"/>'
        '<line x1="38.07" y1="22.44" x2="18.35" y2="42.16" stroke-width="10.79"/><path d="M 81.88 62.36 A 32.02 23.71 0 0 1 20.99 62.36" stroke-width="12.44"/></g>'
        '<g fill="none" stroke="#00E5A0" stroke-linecap="round" stroke-width="10.79"><g class="wink"><line x1="60.71" y1="32.30" x2="88.60" y2="32.30"/><line x1="74.66" y1="18.35" x2="74.66" y2="46.24"/></g></g></svg>')


def projects_section():
    return """<h1>Projects</h1>
<a class="pcard le" href="/loose-ends/" style="--i:1"><div class="plogo">%s<span class="pname" aria-label="Loose Ends" data-name="Loose Ends">Loose Ends</span></div><span class="go">clyon.dev/loose-ends →</span><p>Stop holding it all in your head. For Mac and iPhone. Coming soon.</p></a>
<a class="pcard mb" href="https://mathblitz.app/" target="_blank" rel="noopener" style="--i:2"><div class="plogo">%s<span class="pname" aria-label="Math Blitz" data-name="Math Blitz">Math Blitz</span></div><span class="go">mathblitz.app →</span><p>Times tables in your head, a minute a day. A lane for kids, a lane for adults.</p></a>""" % (SPIRAL, FACE)


def latest_block(latest):
    if not latest:
        return ""
    label = "Blogs" if latest["section"] == "blogs" else "Life"
    data = ' data-sec="life"' if latest["section"] == "life" else ""
    text = latest["title"] or latest["text"]
    if len(text) > 160:
        text = text[:157].rsplit(" ", 1)[0] + "…"
    return ('<a class="latest" id="latest" href="%s"%s><div class="label"><b>Latest</b><span>%s · %s</span></div><p>%s</p></a>'
            % (latest["url"], data, label, md_date(latest["date"]), E(text)))


def article(p, older, newer):
    nav = ""
    if older or newer:
        nav = '<nav class="pn">%s%s</nav>' % (
            '<a href="%s"><small>← Older</small><span>%s</span></a>' % (older["url"], E(older["title"])) if older else "<span></span>",
            '<a class="nx" href="%s"><small>Newer →</small><span>%s</span></a>' % (newer["url"], E(newer["title"])) if newer else "")
    return ('<article class="article"><a class="back" href="/blogs/" data-sec="blogs">← All blogs</a>'
            '<div class="meta"><time datetime="%s">%s</time><span>%d min read</span></div><h1>%s</h1>%s<div class="prose">%s</div>%s</article>'
            % (p["date"].isoformat(), long_date(p["date"]), p["mins"], E(p["title"]),
               '<p class="dek">%s</p>' % E(p["dek"]) if p["dek"] else "", p["html"], nav))


def page(kind, sec, title, desc, url, main, templates, latest):
    home = kind == "home"
    return """<!doctype html>
<html lang="en" data-page="%(kind)s" data-sec="%(sec)s">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<link rel="canonical" href="%(url)s">
<meta property="og:type" content="%(ogtype)s">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(url)s">
<meta name="twitter:card" content="summary">
<meta name="theme-color" content="#F6F6F4" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0E0E0E" media="(prefers-color-scheme: dark)">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="alternate" type="application/rss+xml" title="clyon.dev" href="/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Poppins:wght@800&display=swap">
<link rel="stylesheet" href="/assets/site.css">
<script>(function(d){d.classList.add("js");if(d.dataset.page==="home"&&!/^#(blogs|life|projects)$/.test(location.hash))d.classList.add("intro")})(document.documentElement)</script>
</head>
<body>
<div class="site%(docked)s" id="site">
  <div class="hero">
    <header class="head">
      <a class="stage" id="stage" href="/" aria-label="clyon.dev, home">
        <span class="ghost" aria-hidden="true">clyon.dev</span>
        <span class="typed" aria-hidden="true"><span id="out">clyon<span class="dev">.dev</span></span><span id="path">%(path)s</span></span>
      </a>
      <nav aria-label="Sections"><ul class="menu%(shown)s" id="menu">
        %(menu)s
      </ul></nav>
    </header>
    %(latest)s
  </div>
  <main class="content" id="content"%(hidden)s>%(main)s</main>
  <footer class="foot"><span>© %(year)d %(author)s</span><a href="/feed.xml">RSS</a></footer>
</div>
<div id="caret" aria-hidden="true"></div>
%(templates)s
<script src="/assets/site.js" defer></script>
</body>
</html>
""" % {
        "kind": kind, "sec": sec or "", "title": E(title), "desc": E(desc), "url": url,
        "ogtype": "article" if kind == "post" else "website",
        "docked": "" if home else " docked", "path": "" if home else "/" + sec,
        "shown": "" if home else " shown", "menu": menu(None if home else sec),
        "latest": latest, "hidden": " hidden" if home else "", "main": main,
        "year": datetime.date.today().year, "author": AUTHOR, "templates": templates,
    }


def feed(posts):
    items = []
    for p in posts[:30]:
        title = p["title"] or (p["text"][:80] + ("…" if len(p["text"]) > 80 else ""))
        pub = datetime.datetime(p["date"].year, p["date"].month, p["date"].day, 12, tzinfo=datetime.timezone.utc)
        items.append("<item><title>%s</title><link>%s%s</link><guid>%s%s</guid><pubDate>%s</pubDate><description>%s</description></item>"
                     % (E(title), SITE, p["url"], SITE, p["url"], format_datetime(pub), E(p["html"])))
    return ('<?xml version="1.0" encoding="utf-8"?>\n<rss version="2.0"><channel><title>clyon.dev</title><link>%s/</link>'
            "<description>%s</description><language>en</language>%s</channel></rss>\n" % (SITE, E(DESCRIPTION), "".join(items)))


def write(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def build():
    blogs, life = read_posts("blogs"), read_posts("life")
    everything = sorted(blogs + life, key=lambda p: (p["date"], p["section"] == "blogs"), reverse=True)
    latest = latest_block(everything[0] if everything else None)
    sections = {"blogs": blogs_section(blogs), "life": life_section(life), "projects": projects_section()}
    templates = "\n".join('<template id="t-%s">%s</template>' % (k, v) for k, v in sections.items())

    for d in GENERATED_DIRS:
        shutil.rmtree(os.path.join(ROOT, d), ignore_errors=True)

    write("index.html", page("home", None, "clyon.dev", DESCRIPTION, SITE + "/", "", templates, latest))
    blurbs = {"blogs": "Writing about what I'm building.",
              "life": "Updates, photos and notes from life in between.",
              "projects": "Loose Ends and Math Blitz."}
    for sec in SECTIONS:
        write("%s/index.html" % sec, page("section", sec, "%s · clyon.dev" % sec.capitalize(), blurbs[sec],
                                          "%s/%s/" % (SITE, sec), sections[sec], templates, latest))
    for i, p in enumerate(blogs):
        newer = blogs[i - 1] if i > 0 else None
        older = blogs[i + 1] if i + 1 < len(blogs) else None
        write("blogs/%s/index.html" % p["slug"],
              page("post", "blogs", "%s · clyon.dev" % p["title"], p["dek"] or p["text"][:160],
                   SITE + p["url"], article(p, older, newer), templates, latest))
    for sec in ("blogs", "life"):
        src = os.path.join(POSTS, sec, "images")
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(ROOT, sec, "images"))
    write("feed.xml", feed(everything))
    write("404.html", page("section", "blogs", "Not found · clyon.dev", DESCRIPTION, SITE + "/404.html",
                           '<h1>Not found</h1><p class="empty">Nothing typed here yet. <a href="/">Go home</a>.</p>', templates, latest)
          .replace('data-page="section" data-sec="blogs"', 'data-page="404" data-sec=""')
          .replace('<span id="path">/blogs</span>', '<span id="path">/404</span>')
          .replace(' class="on" aria-current="page"', ""))
    print("built: %d blogs, %d life posts" % (len(blogs), len(life)))


def new(section, title):
    if section not in ("blogs", "life"):
        sys.exit("section must be blogs or life")
    today = datetime.date.today().isoformat()
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60] or "post"
    path = os.path.join(POSTS, section, "%s-%s.md" % (today, slug))
    if os.path.exists(path):
        sys.exit("already exists: " + path)
    head = "---\ntitle: %s\n" % title
    head += "dek: \n" if section == "blogs" else "kind: Note\n"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(head + "---\n\n")
    print(path)


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "new":
        new(sys.argv[2], " ".join(sys.argv[3:]))
    else:
        build()
