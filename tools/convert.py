#!/usr/bin/env python3
"""Turn Markdown exported from Claude Docs into Docusaurus blog posts.

    python3 tools/convert.py <export dir>   # convert an export, then regenerate indexes
    python3 tools/convert.py --check        # verify the generated files match blog/*.md
    python3 tools/convert.py --regenerate   # rebuild the generated files without an export

Export dir layout (written by the publish skill, never by hand):

    index.md             Markdown export of the "Blog: 00 Index" Doc
    posts/<slug>.md      Markdown export of each post Doc's Post tab
    meta.json            optional: {"<slug>": {"doc": "<Doc url>", "rev": <n>}}

The Index table decides what is published. A row whose Status is Ready or
Published is written to blog/<date>-<slug>.md. Every other row is skipped.

Generated from blog/*.md on every run, for machine readers:

    static/posts.json        one entry per post
    static/posts/<slug>.md   the post body as plain Markdown
    static/llms.txt          a plain-text listing of the posts

The script only moves and wraps text. It never rewrites post content.
"""
import datetime
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"
STATIC = ROOT / "static"
PUBLISHED = ROOT / "tools" / "published.json"
PUBLISH_STATUSES = {"ready", "published"}
COLUMNS = ["post", "slug", "date", "tags", "summary", "status"]
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
BYLINE = re.compile(r"^\w{3} \d{1,2}, \d{4} · @")
LINK = re.compile(r"^\[(.*)\]\((\S+)\)$")
# Leftover authoring markers. "[" is exported from Docs as "&#91;".
MARKERS = re.compile(r"(?:\[|&#91;)\s*To (?:write|confirm)", re.I)
TRUNCATE = "<!-- truncate -->"


def split_row(line):
    cells = re.split(r"(?<!\\)\|", line.strip())
    return [c.strip().replace("\\|", "|") for c in cells[1:-1]]


def parse_index(text):
    """Return the rows of the first table whose header has every expected column."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.lstrip().startswith("|"):
            continue
        header = [h.lower() for h in split_row(line)]
        if not all(c in header for c in COLUMNS):
            continue
        rows = []
        for body in lines[i + 2:]:
            if not body.lstrip().startswith("|"):
                break
            cells = split_row(body)
            cells += [""] * (len(header) - len(cells))
            rows.append(dict(zip(header, cells)))
        return rows
    sys.exit("convert: no table with columns " + ", ".join(COLUMNS) + " found in index.md")


def parse_date(value):
    for fmt in ("%Y-%m-%d", "%b %d, %Y"):
        try:
            return datetime.datetime.strptime(value.strip(), fmt).date().isoformat()
        except ValueError:
            pass
    return None


def post_body(text):
    """Drop the title heading and the date/author line Docs puts under it."""
    lines = text.replace("\r\n", "\n").split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and lines[0].startswith("# "):
        lines.pop(0)
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and BYLINE.match(lines[0]):
        lines.pop(0)
    return "\n".join(lines).strip() + "\n"


def with_truncate(body):
    """Mark the end of the first paragraph as the excerpt shown on list pages."""
    if TRUNCATE in body:
        return body
    blocks = body.split("\n\n")
    if len(blocks) < 2:
        return body
    return "\n\n".join([blocks[0], TRUNCATE] + blocks[1:])


def front_matter(meta):
    out = ["---"]
    for key in ("title", "date", "slug", "description"):
        out.append(f"{key}: {json.dumps(meta[key], ensure_ascii=False)}")
    out.append("tags: " + json.dumps(meta["tags"], ensure_ascii=False))
    out.append("authors: [sam]")
    out.append("---")
    return "\n".join(out) + "\n\n"


def read_post(path):
    """Split a blog/*.md file into its front matter values and its body."""
    text = path.read_text(encoding="utf-8")
    _, fm, body = text.split("---\n", 2)
    meta = {}
    for line in fm.splitlines():
        key, _, value = line.partition(": ")
        if key in ("title", "date", "slug", "description", "tags"):
            meta[key] = json.loads(value)
    return meta, body.lstrip("\n").replace(TRUNCATE + "\n\n", "")


def convert(export):
    export = pathlib.Path(export)
    rows = parse_index((export / "index.md").read_text(encoding="utf-8"))
    meta_path = export / "meta.json"
    source = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    published = json.loads(PUBLISHED.read_text()) if PUBLISHED.exists() else {}
    errors, written, skipped = [], [], []

    for row in rows:
        link = LINK.match(row["post"])
        title = link.group(1) if link else row["post"]
        slug, status = row["slug"], row["status"].lower()
        if status not in PUBLISH_STATUSES:
            skipped.append(f"{title} ({row['status'] or 'no status'})")
            continue
        date = parse_date(row["date"])
        tags = [t.strip().lower() for t in row["tags"].split(",") if t.strip()]
        src = export / "posts" / f"{slug}.md"
        problems = []
        if not SLUG.match(slug):
            problems.append(f"slug {slug!r} must be lowercase words joined by hyphens")
        if not date:
            problems.append(f"date {row['date']!r} is not YYYY-MM-DD")
        if not row["summary"]:
            problems.append("summary is empty")
        if not src.exists():
            problems.append(f"no export found at posts/{slug}.md")
        if problems:
            errors += [f"{title}: {p}" for p in problems]
            continue
        raw = src.read_text(encoding="utf-8")
        body = post_body(raw)
        if MARKERS.search(body):
            errors.append(f"{title}: still contains a [To write] or [To confirm] marker")
        if re.search(r"\]\(blob/", body):
            errors.append(f"{title}: contains an image stored in the Doc, which this converter cannot export yet")
        if not body.strip():
            errors.append(f"{title}: the Post tab is empty")
        meta = {"title": title, "date": date, "slug": slug, "description": row["summary"], "tags": tags}
        for old in BLOG.glob(f"*-{slug}.md"):
            if old.name != f"{date}-{slug}.md":
                old.unlink()  # the publish date changed
        out = BLOG / f"{date}-{slug}.md"
        out.write_text(front_matter(meta) + with_truncate(body), encoding="utf-8")
        written.append(out.name)
        published[slug] = {
            "doc": (link.group(2) if link else None) or source.get(slug, {}).get("doc"),
            "rev": source.get(slug, {}).get("rev"),
            "source_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        }

    if errors:
        sys.exit("convert: nothing should be committed until these are fixed:\n  " + "\n  ".join(errors))
    PUBLISHED.write_text(json.dumps(published, indent=2, sort_keys=True) + "\n")
    print(f"convert: wrote {len(written)} post(s): " + (", ".join(written) or "none"))
    if skipped:
        print("convert: skipped " + "; ".join(skipped))
    live = {m["slug"] for m, _ in map(read_post, BLOG.glob("*.md"))}
    listed = {r["slug"] for r in rows if r["status"].lower() in PUBLISH_STATUSES}
    for slug in sorted(live - listed):
        print(f"convert: note: blog/ has a post {slug!r} that the Index does not list as Ready or Published")


def generated():
    """Build the machine-readable files from blog/*.md. Returns {path: text}."""
    site = json.loads((ROOT / "site.json").read_text())
    base = site["url"].rstrip("/") + site["baseUrl"]
    posts = []
    files = {}
    for path in sorted(BLOG.glob("*.md")):
        meta, body = read_post(path)
        files[STATIC / "posts" / f"{meta['slug']}.md"] = f"# {meta['title']}\n\n{body}"
        posts.append({
            "title": meta["title"],
            "slug": meta["slug"],
            "date": meta["date"],
            "tags": meta["tags"],
            "summary": meta["description"],
            "url": f"{base}{meta['slug']}/",
            "markdown_url": f"{base}posts/{meta['slug']}.md",
        })
    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
    files[STATIC / "posts.json"] = json.dumps(
        {"site": base, "title": site["title"], "posts": posts}, indent=2, ensure_ascii=False) + "\n"
    lines = [f"# {site['title']}", "", f"> {site['tagline']}", "",
             f"Machine-readable index: {base}posts.json", "", "## Posts", ""]
    lines += [f"- [{p['title']}]({p['markdown_url']}): {p['summary']} ({p['date']})" for p in posts]
    files[STATIC / "llms.txt"] = "\n".join(lines) + "\n"
    return files


def write_generated():
    files = generated()
    (STATIC / "posts").mkdir(parents=True, exist_ok=True)
    for stale in set((STATIC / "posts").glob("*.md")) - set(files):
        stale.unlink()
    for path, text in files.items():
        path.write_text(text, encoding="utf-8")
    print(f"convert: regenerated posts.json, llms.txt, and {len(files) - 2} Markdown file(s) under static/")


def check():
    files = generated()
    bad = [str(p.relative_to(ROOT)) for p, text in files.items()
           if not p.exists() or p.read_text(encoding="utf-8") != text]
    bad += [str(p.relative_to(ROOT)) for p in set((STATIC / "posts").glob("*.md")) - set(files)]
    if bad:
        sys.exit("convert: generated files are out of date (run tools/convert.py):\n  " + "\n  ".join(sorted(bad)))
    print("convert: generated files are current")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    BLOG.mkdir(exist_ok=True)
    if sys.argv[1] == "--check":
        check()
    elif sys.argv[1] == "--regenerate":
        write_generated()
    else:
        convert(sys.argv[1])
        write_generated()
