---
name: publish-blog
description: Publish the blog from Claude Docs to the samdengler/blog repo. Use when the user says "publish the blog", "publish my post", or asks to push Ready posts to the site.
---

# Publish the blog

The blog is written in Claude Docs. The Doc titled "Blog: 00 Index" lists every post. A post is
published when its Status in the Index is Ready or Published. This skill exports those posts,
converts them, and opens a pull request. The user merges it, and GitHub Actions deploys the site.

Post content moves as files. Never retype, summarize, or reword a post, and never paste export
text into a file by hand.

## Steps

1. **Find the Index.** List the user's artifacts and open "Blog: 00 Index" with the docs tools.
   Read its Posts table. Each row's Post cell links to the post Doc.
2. **Get the repo.** Clone `samdengler/blog` (attach it to the session first if needed) and
   create a branch named `publish/<yyyy-mm-dd>-<first slug>`.
3. **Export to `export/` in the scratchpad** (not inside the repo):
   - Index: create a stored Markdown export of the Index tab
     (`create` a `blob` with `{"from": {"object": "file", "id": "<tab id>"}, "format": "markdown"}`),
     then save that asset to disk with the Artifact tool's `read` action (`path` = the asset id).
     Copy it to `export/index.md`.
   - For each row with Status Ready or Published: open the post Doc, find the tab named "Post",
     export it the same way, and copy it to `export/posts/<slug>.md`. Never export the Research tab.
   - Write `export/meta.json` as `{"<slug>": {"doc": "<Doc url>", "rev": <rev from the export result>}}`.
4. **Convert.** Run `python3 tools/convert.py <export dir>` from the repo root. If it lists
   problems, stop, tell the user what to fix in the Docs, and do not commit.
5. **Build.** Run `npm ci` (first time) and `npm run build`. Stop on any error.
6. **Open the pull request.** Commit `blog/`, `static/`, and `tools/published.json`, push the
   branch, and open a pull request titled `Publish: <post titles>`. The body lists new and
   changed posts.
7. **After the user merges.** In the Index, set each Ready post that was published to Published.

## Rules

- The Docs are the source of truth. Never edit files under `blog/` or `static/posts/` by hand.
- A post whose Status is Idea or Draft is never exported.
- Do not change a slug after its post is Published. The slug is the URL.
- To unpublish a post, set its Status back to Draft, delete its file under `blog/`, run
  `python3 tools/convert.py --regenerate`, and open a pull request.
- Images stored in a Doc are not supported yet. The converter stops when it finds one.
