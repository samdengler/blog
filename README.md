# blog

Source for https://samdengler.github.io/blog/.

Posts are written in Claude Docs and published here as Markdown. The files under `blog/` and
`static/posts/` are generated. Edit the Doc and publish again; do not edit them by hand.

## Publishing flow

1. Each post is one Claude Doc with a Post tab and a Research tab.
2. The "Blog: 00 Index" Doc lists every post with its slug, date, tags, summary, and status.
3. Posts marked Ready or Published are exported to Markdown.
4. `tools/convert.py` adds front matter and writes `blog/<date>-<slug>.md`.
5. A pull request shows the diff. Merging it deploys the site through GitHub Actions.

The steps Claude follows are in `tools/publish-blog/SKILL.md`.

## Machine-readable output

Every publish regenerates these from `blog/*.md`:

| File | Content |
| --- | --- |
| `/posts.json` | One entry per post: title, slug, date, tags, summary, page URL, Markdown URL |
| `/posts/<slug>.md` | The post as plain Markdown |
| `/llms.txt` | Plain-text listing of the posts |

## Local commands

```
npm ci
npm start                              # local preview
npm run build                          # production build
python3 tools/convert.py <export dir>  # convert an export from Claude Docs
python3 tools/convert.py --check       # confirm generated files are current
```

## Site address

`site.json` holds the site URL and base path. Both the Docusaurus config and the converter read it.
To move to a custom domain, change `url` and `baseUrl` there, add `static/CNAME`, and run
`python3 tools/convert.py --regenerate`.
