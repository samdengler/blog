"""AWS Lambda entry point for an API Gateway HTTP API or a Lambda function URL."""
import base64

import mcp_http


def handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "POST")
    body = event.get("body") or ""
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")
    status, headers, text = mcp_http.handle_http(method, body)
    return {"statusCode": status, "headers": headers, "body": text}
