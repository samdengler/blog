# Writing in Claude Docs, publishing with Docusaurus

This blog is written in Claude Docs and published as a static Docusaurus site.  I wanted the drafting and research to happen where I already work with Claude, and I wanted the published result to be plain files in a git repo.

## How a post gets here

1. Each post is one Claude Doc with two tabs.  The Post tab holds the writing.  The Research tab holds notes and sources and is never published.
2. An index Doc lists every post with its slug, date, tags, summary, and status.
3. When I set a post to Ready, Claude exports the Post tab to Markdown and runs a converter script that adds front matter and writes the file into the repo.
4. Claude opens a pull request.  I read the diff and merge it.
5. GitHub Actions builds the site and deploys it to GitHub Pages.

## Docs as the source of truth

Edits happen in the Doc and flow one way to the site.  The repo is never edited by hand, so the two cannot drift.  The pull request is the review step.  It shows what changed since the last publish.

## Readable by machines

Every publish also writes a `posts.json` index, a plain Markdown copy of each post, and an `llms.txt` file.  An MCP server can list, search, and fetch posts from those files without scraping HTML.

## Open items

Images and diagrams are next.  The converter does not handle them yet, so this first post is text only.
