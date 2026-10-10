import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import blog_tools  # noqa: E402
import lambda_function  # noqa: E402
import mcp_http  # noqa: E402

BASE = "https://example.test/blog/"
POSTS = [
    {"title": "Cedar policies for MCP tools", "slug": "cedar-mcp", "date": "2026-10-12", "tags": ["cedar", "mcp"],
     "summary": "Authorizing tool calls.", "url": BASE + "cedar-mcp/", "markdown_url": BASE + "posts/cedar-mcp.md"},
    {"title": "Writing in Claude Docs", "slug": "docs", "date": "2026-10-10", "tags": ["claude"],
     "summary": "How the blog is built.", "url": BASE + "docs/", "markdown_url": BASE + "posts/docs.md"},
]
PAGES = {
    BASE + "posts.json": json.dumps({"posts": POSTS}),
    BASE + "posts/cedar-mcp.md": "# Cedar policies for MCP tools\n\nA gateway checks each tool call against a Cedar policy.\n",
    BASE + "posts/docs.md": "# Writing in Claude Docs\n\nThe converter adds front matter. A pull request gates the deploy.\n",
}


def rpc(method, params=None, message_id=1):
    body = {"jsonrpc": "2.0", "id": message_id, "method": method, "params": params or {}}
    status, _, text = mcp_http.handle_http("POST", json.dumps(body))
    return status, json.loads(text)


def call(name, arguments):
    return rpc("tools/call", {"name": name, "arguments": arguments})[1]["result"]


class ServerTest(unittest.TestCase):
    def setUp(self):
        blog_tools.BASE_URL = BASE
        blog_tools.fetch = PAGES.__getitem__

    def test_initialize_echoes_a_supported_version(self):
        _, answer = rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}})
        self.assertEqual(answer["result"]["protocolVersion"], "2025-06-18")
        self.assertIn("tools", answer["result"]["capabilities"])

    def test_initialize_offers_its_latest_for_an_unknown_version(self):
        _, answer = rpc("initialize", {"protocolVersion": "1999-01-01"})
        self.assertEqual(answer["result"]["protocolVersion"], mcp_http.SUPPORTED_VERSIONS[0])

    def test_notification_gets_202_and_no_body(self):
        body = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})
        self.assertEqual(mcp_http.handle_http("POST", body), (202, {}, ""))

    def test_tools_list_has_three_read_only_tools(self):
        tools = rpc("tools/list")[1]["result"]["tools"]
        self.assertEqual([t["name"] for t in tools], ["list_posts", "search_posts", "get_post"])
        self.assertTrue(all(t["annotations"]["readOnlyHint"] and "call" not in t for t in tools))

    def test_list_posts_filters_by_tag(self):
        result = json.loads(call("list_posts", {"tag": "MCP"})["content"][0]["text"])
        self.assertEqual([p["slug"] for p in result["posts"]], ["cedar-mcp"])

    def test_search_ranks_the_matching_post_first(self):
        result = json.loads(call("search_posts", {"query": "pull request deploy"})["content"][0]["text"])
        self.assertEqual(result["results"][0]["slug"], "docs")
        self.assertIn("pull request", result["results"][0]["excerpt"])

    def test_search_with_no_match_returns_nothing(self):
        result = json.loads(call("search_posts", {"query": "kubernetes"})["content"][0]["text"])
        self.assertEqual(result, {"results": [], "total": 0})

    def test_get_post_returns_markdown_and_source(self):
        text = call("get_post", {"slug": "docs"})["content"][0]["text"]
        self.assertTrue(text.startswith("# Writing in Claude Docs"))
        self.assertIn(BASE + "docs/", text)

    def test_bad_input_is_a_tool_error(self):
        self.assertTrue(call("get_post", {"slug": "nope"})["isError"])
        self.assertTrue(call("get_post", {})["isError"])
        self.assertTrue(call("list_posts", {"bogus": 1})["isError"])

    def test_unknown_tool_and_method_are_protocol_errors(self):
        self.assertEqual(rpc("tools/call", {"name": "nope"})[1]["error"]["code"], -32602)
        self.assertEqual(rpc("resources/list")[1]["error"]["code"], -32601)

    def test_get_is_not_allowed_and_bad_json_is_400(self):
        self.assertEqual(mcp_http.handle_http("GET", "")[0], 405)
        self.assertEqual(mcp_http.handle_http("POST", "{nope")[0], 400)

    def test_lambda_adapter_handles_a_base64_body(self):
        import base64
        body = base64.b64encode(json.dumps({"jsonrpc": "2.0", "id": 7, "method": "ping"}).encode()).decode()
        event = {"requestContext": {"http": {"method": "POST"}}, "body": body, "isBase64Encoded": True}
        answer = lambda_function.handler(event, None)
        self.assertEqual(answer["statusCode"], 200)
        self.assertEqual(json.loads(answer["body"]), {"jsonrpc": "2.0", "id": 7, "result": {}})


if __name__ == "__main__":
    unittest.main()
