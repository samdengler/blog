---
name: publish-blog
description: Publish Sam's blog from Claude Docs to the samdengler/blog repo. Use when the user says "publish the blog", "publish my post", or asks to push Ready posts to the site.
---

# Publish the blog

The blog is written in Claude Docs. The Doc titled "Blog: 00 Index" lists every post. A post is
published when its Status in the Index is Ready or Published. This skill exports those posts,
converts them, and opens a pull request. The user merges it, and GitHub Actions deploys the site.

Post content moves as files. Never retype, summarize, or reword a post, and never paste export
text into a file by hand. The converter in the repo (`tools/convert.py`) does all text handling.

## Steps

1. **Find the Index.** List the user's artifacts, open "Blog: 00 Index" with the docs tools, and
   read its Posts table. Each row's Post cell links to the post Doc.
2. **Get the repo.** Attach `samdengler/blog` to the session with push access if it is not
   attached, clone it, and create a branch named `publish/<yyyy-mm-dd>-<first new slug>`.
3. **Export to an `export/` folder in the scratchpad** (never inside the repo):
   - **Index.** Create a stored Markdown export of the Index tab with the docs `create` tool:
     object `blob`, engine `blob`, payload `{"from": {"object": "file", "id": "<tab id>"}, "format": "markdown"}`.
     The result gives an asset id. Save that asset to disk with the Artifact tool's `read` action
     (`url` = the Doc link, `path` = the asset id, one asset per call). Copy it to `export/index.md`.
   - **Posts.** For each row with Status Ready or Published: open the post Doc, find the tab
     named "Post", export it the same way, and copy the file to `export/posts/<slug>.md`.
     Never export the Research tab.
   - **Images and diagrams.** The Markdown export leaves a text placeholder for each one, so
     their files travel separately. Read the Post tab's contents in full and note, in document
     order, every `<media blob='blob/<id>'>` (an uploaded image) and every
     `<embed ref='node/<id>'>` (a drawn diagram or chart). If there are none, skip this.
     - Image: `read` the blob (`ref` object `blob`) to get its asset id, then save the asset
       with the Artifact tool's `read` action.
     - Diagram: `read` the widget node with engine `widget` and payload `{"kind": "screenshot"}`.
       The result names a PNG saved on disk.
     - Copy each file to `export/media/<slug>/NN.<ext>` (01, 02, ... in document order) and write
       `export/media/<slug>/media.json` as a list with one entry per file:
       `{"kind": "image", "file": "01.png"}` or
       `{"kind": "diagram", "file": "02.png", "alt": "<the diagram's title words>"}`.
   - **Source record.** Write `export/meta.json` as
     `{"<slug>": {"doc": "<Doc url>", "rev": <rev from the export result>}}`.
4. **Convert.** From the repo root run `python3 tools/convert.py <export dir>`. If it lists
   problems, stop, tell the user what to fix in the Docs, and do not commit.
5. **Build.** Run `npm ci` (first time in a clone) and `npm run build`. Stop on any error.
   Open the built page for each new post and look at it before going on.
6. **Open the pull request.** Commit `blog/`, `static/`, and `tools/published.json`, push the
   branch, and open a pull request titled `Publish: <post titles>` whose body lists new and
   changed posts. Give the user the link.
7. **After the user merges.** Confirm the deploy run succeeded, then set each newly published
   post's Status in the Index from Ready to Published.

## Rules

- The Docs are the source of truth. Never edit files under `blog/`, `static/posts/`, or
  `static/img/posts/` by hand.
- A post whose Status is Idea or Draft is never exported.
- Do not change a slug after its post is Published. The slug is the URL.
- If no post is Ready and no Published post changed, say so and open no pull request.
- To unpublish a post, set its Status back to Draft, delete its file under `blog/` and its
  folder under `static/img/posts/`, run `python3 tools/convert.py --regenerate`, and open a
  pull request.
- Diagrams are published as light-theme PNG screenshots of the drawing in the Doc.

## New posts

When the user asks to start a post: create a Doc titled "Blog: <Post Title>" with a tab named
"Post" (the writing) and a tab named "Research" (notes and sources, never published), then add
a row to the Index with a slug, the planned date as YYYY-MM-DD, tags, a one-sentence summary,
and Status Idea or Draft.
