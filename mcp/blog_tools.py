"""Read-only tools over the blog's published files.

The blog publishes posts.json (an index) and one plain Markdown file per post.
Everything here reads those two things over HTTPS. Nothing is stored or written.
"""
import json
import os
import re
import time
import urllib.request

BASE_URL = os.environ.get("BLOG_BASE_URL", "https://samdengler.github.io/blog/").rstrip("/") + "/"
CACHE_SECONDS = int(os.environ.get("BLOG_CACHE_SECONDS", "300"))
_cache = {}


def fetch(url):
    """GET a URL as text, cached in memory for a few minutes."""
    hit = _cache.get(url)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1]
    request = urllib.request.Request(url, headers={"User-Agent": "blog-mcp/1.0"})
    with urllib.request.urlopen(request, timeout=10) as response:
        text = response.read().decode("utf-8")
    _cache[url] = (time.time(), text)
    return text


def _posts():
    return json.loads(fetch(BASE_URL + "posts.json"))["posts"]


def _limit(value, default=20):
    try:
        return max(1, min(int(value), 50))
    except (TypeError, ValueError):
        return default


def list_posts(tag=None, limit=None):
    """Posts newest first, optionally only those carrying a tag."""
    posts = _posts()
    if tag:
        posts = [p for p in posts if tag.lower() in p["tags"]]
    return {"posts": posts[:_limit(limit)], "total": len(posts)}


def get_post(slug):
    """One post: its index entry plus the full Markdown."""
    for post in _posts():
        if post["slug"] == slug:
            return {**post, "markdown": fetch(post["markdown_url"])}
    raise ValueError(f"No post with slug {slug!r}. Use list_posts to see the slugs.")


def search_posts(query, limit=None):
    """Rank posts by how often the query's words appear, with a matching excerpt."""
    words = [w for w in re.findall(r"[a-z0-9]+", (query or "").lower()) if len(w) > 1]
    if not words:
        raise ValueError("query must contain at least one word")
    results = []
    for post in _posts():
        body = fetch(post["markdown_url"])
        heading = " ".join([post["title"], post["summary"], " ".join(post["tags"])]).lower()
        lowered = body.lower()
        matched = [w for w in words if w in heading or w in lowered]
        if not matched:
            continue
        score = sum(5 * heading.count(w) + lowered.count(w) for w in words)
        at = min((lowered.find(w) for w in matched if w in lowered), default=0)
        start = max(at - 120, 0)
        excerpt = " ".join(body[start:at + 240].split())
        results.append({
            "title": post["title"], "slug": post["slug"], "date": post["date"],
            "url": post["url"], "summary": post["summary"],
            "matched_words": len(matched), "score": score,
            "excerpt": ("... " if start else "") + excerpt + " ...",
        })
    results.sort(key=lambda r: (r["matched_words"], r["score"], r["date"]), reverse=True)
    return {"results": results[:_limit(limit, 10)], "total": len(results)}


READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}

TOOLS = [
    {
        "name": "list_posts",
        "title": "List blog posts",
        "description": "List the posts on Sam Dengler's blog, newest first, with title, slug, date, "
                       "tags, summary, and URL. Optionally filter by one tag.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tag": {"type": "string", "description": "Only posts with this tag (lowercase)."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "description": "Most posts to return. Default 20."},
            },
            "additionalProperties": False,
        },
        "annotations": READ_ONLY,
        "call": list_posts,
    },
    {
        "name": "search_posts",
        "title": "Search blog posts",
        "description": "Full-text keyword search across the titles, summaries, tags, and bodies of the "
                       "blog's posts. Returns the best matches with an excerpt. Use get_post for the full text.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Words to look for."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "description": "Most results to return. Default 10."},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        "annotations": READ_ONLY,
        "call": search_posts,
    },
    {
        "name": "get_post",
        "title": "Get a blog post",
        "description": "Get one post by slug: its title, date, tags, summary, URL, and full Markdown text.",
        "inputSchema": {
            "type": "object",
            "properties": {"slug": {"type": "string", "description": "The post's slug, from list_posts or search_posts."}},
            "required": ["slug"],
            "additionalProperties": False,
        },
        "annotations": READ_ONLY,
        "call": get_post,
    },
]
