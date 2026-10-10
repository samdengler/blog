# Blog MCP server

Read-only MCP tools over the blog's published files.

| Tool | Does |
| --- | --- |
| `list_posts` | Lists posts newest first, optionally by tag |
| `search_posts` | Keyword search over titles, summaries, tags, and bodies, with excerpts |
| `get_post` | Returns one post's full Markdown by slug |

The server reads `posts.json` and `posts/<slug>.md` from the blog over HTTPS and caches them in
memory for five minutes. It stores nothing, needs no credentials, and has no dependencies beyond
the Python standard library.

## Files

| File | Role |
| --- | --- |
| `blog_tools.py` | The three tools and their schemas |
| `mcp_http.py` | Stateless MCP over Streamable HTTP (JSON-RPC in, JSON out) |
| `lambda_function.py` | AWS Lambda entry point for an API Gateway HTTP API |
| `local_server.py` | Local runner for testing |
| `template.yaml` | AWS SAM template: Lambda, HTTP API, optional custom domain |

## Run locally

```
python3 mcp/local_server.py 8787        # serves http://localhost:8787/mcp
python3 -m unittest discover -s mcp/tests
```

## Deploy

Requires the AWS SAM CLI and credentials for the target account.

```
cd mcp
sam deploy --guided --stack-name blog-mcp
```

The `Endpoint` output is the MCP URL. Add it to Claude as a custom connector.

### Custom domain (mcp.dengler.io)

1. Request an ACM certificate for `mcp.dengler.io` in the deploy region and validate it with
   the DNS record ACM gives you.
2. Deploy with `--parameter-overrides DomainName=mcp.dengler.io CertificateArn=<arn>`.
3. Add a CNAME record for `mcp.dengler.io` pointing at the `DnsTarget` output.

When the blog moves to its own domain, redeploy with `BlogBaseUrl` set to the new address.

## Behind an AgentCore Gateway

The tools in `blog_tools.py` are plain functions with JSON schemas, separate from the HTTP
layer. To put them behind a gateway, register this server's endpoint as an MCP target, or add
a second Lambda entry point that maps the gateway's tool event to `blog_tools.TOOLS`.
