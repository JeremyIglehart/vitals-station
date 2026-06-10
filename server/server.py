#!/usr/bin/env python3
"""
Vitals Station — Schema Discovery Server
----------------------------------------
Schema-discovery mode only. Accepts any JSON POST to /ingest and writes
the raw payload to test-exports/raw/ with a UTC timestamp + sequence number.
No parsing, no conversion, no interpretation. That comes after the first
real export lands and we know what we're working with.

Binds exclusively to the Tailscale interface (100.95.70.33) on port 8080.
Not accessible from the public internet.

Endpoints:
  GET  /health  — liveness check, returns 200 + plain text
  POST /ingest  — accepts JSON body, writes raw file, returns 200 + receipt
"""

import http.server
import json
import os
import socketserver
import sys
from datetime import datetime, timezone
from pathlib import Path

# --- Config ---
HOST = "100.95.70.33"   # Tailscale interface only — never 0.0.0.0
PORT = 8080
BASE_DIR = Path(__file__).parent.parent  # vitals-station/
RAW_DIR  = BASE_DIR / "test-exports" / "raw"

RAW_DIR.mkdir(parents=True, exist_ok=True)


def _next_filename() -> str:
    """UTC timestamp + zero-padded sequence so files sort chronologically
    and multiple exports in the same second don't collide."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    # Count existing json files to get sequence number
    existing = sorted(RAW_DIR.glob(f"{ts}_*.json"))
    seq = len(existing) + 1
    return f"{ts}_{seq:03d}.json"


class VitalsHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # Cleaner log — timestamp + message only
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f"[{ts}] {fmt % args}", flush=True)

    def _send(self, code: int, body: str, content_type: str = "text/plain"):
        encoded = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        if self.path == "/health":
            raw_files = list(RAW_DIR.glob("*.json"))
            body = (
                f"Vitals Station — schema discovery mode\n"
                f"status: alive\n"
                f"test exports received: {len(raw_files)}\n"
                f"raw dir: {RAW_DIR}\n"
            )
            self._send(200, body)
        else:
            self._send(404, "not found")

    def do_POST(self):
        if self.path != "/ingest":
            self._send(404, "not found")
            return

        # Read body
        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length)

        # Validate it's parseable JSON — but store raw bytes regardless
        try:
            parsed = json.loads(raw_body)
            is_valid_json = True
            pretty = json.dumps(parsed, indent=2, ensure_ascii=False)
        except json.JSONDecodeError as e:
            is_valid_json = False
            pretty = raw_body.decode("utf-8", errors="replace")
            print(f"  [warn] body is not valid JSON: {e}", flush=True)

        # Write to disk
        filename = _next_filename()
        dest = RAW_DIR / filename
        dest.write_text(pretty, encoding="utf-8")

        size = dest.stat().st_size
        print(f"  wrote {filename} ({size} bytes, valid_json={is_valid_json})", flush=True)

        # Receipt back to caller
        receipt = {
            "status": "received",
            "file": filename,
            "bytes": size,
            "valid_json": is_valid_json,
        }
        self._send(200, json.dumps(receipt), "application/json")


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    print(f"Vitals Station starting on {HOST}:{PORT}", flush=True)
    print(f"Raw exports → {RAW_DIR}", flush=True)
    print(f"GET  http://{HOST}:{PORT}/health", flush=True)
    print(f"POST http://{HOST}:{PORT}/ingest", flush=True)

    with ReusableTCPServer((HOST, PORT), VitalsHandler) as srv:
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\nshutting down", flush=True)
            sys.exit(0)
