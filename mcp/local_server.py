"""Run the MCP server on localhost for testing:  python3 mcp/local_server.py [port]"""
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

import mcp_http


class Handler(BaseHTTPRequestHandler):
    def _answer(self):
        length = int(self.headers.get("Content-Length") or 0)
        status, headers, text = mcp_http.handle_http(self.command, self.rfile.read(length).decode("utf-8"))
        data = text.encode("utf-8")
        self.send_response(status)
        for key, value in headers.items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    do_POST = do_GET = do_DELETE = _answer

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8787
    print(f"MCP server on http://localhost:{port}/mcp")
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
