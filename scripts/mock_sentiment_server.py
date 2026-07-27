#!/usr/bin/env python3
"""
Mock sentiment API server for demonstrating the 'api' provider_type.

Run:
    python scripts/mock_sentiment_server.py

Serves on http://localhost:5001/sentiment

Accepts POST with:
    { "envelope": { "current_text": "...", ... } }

Returns:
    { "sentiment": { "label": "positive", "score": 0.87 }, "score": 0.87 }

Uses the same keyword analyzer as the built-in code module so the
demo is consistent regardless of provider_type.
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from http.server import HTTPServer, BaseHTTPRequestHandler

from modules.sentiment_analyzer import analyze


class SentimentHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        if self.path != "/sentiment":
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            payload = json.loads(body)
            text = payload.get("envelope", {}).get("current_text", "")
            result = analyze(text)
            response = {
                "sentiment": result,
                "score": result["score"],
                "label": result["label"],
            }
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            response = {"error": str(e)}

        response_bytes = json.dumps(response, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def log_message(self, fmt, *args):
        print(f"[mock-api] {args[0]}")


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
    server = HTTPServer(("localhost", port), SentimentHandler)
    print(f"Mock sentiment API running on http://localhost:{port}/sentiment")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
