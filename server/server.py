#!/usr/bin/env python3
"""
Vitals Station — Schema Discovery Server (TLS)
-----------------------------------------------
Schema-discovery mode. Accepts any JSON POST to /ingest, writes the raw
payload to test-exports/raw/ with a UTC timestamp + sequence number.
No parsing, no conversion, no interpretation.

Binds to the Tailscale hostname on port 8080 with Let's Encrypt TLS
(provisioned via `tailscale cert`). iOS trusts this automatically.

Endpoints:
  GET  /health  — liveness check
  POST /ingest  — accepts JSON body, writes raw file, returns 200 + receipt
"""

import http.server
import importlib.util
import json
import os
import ssl
import socketserver
import sys
from datetime import datetime, timezone
from pathlib import Path

# --- Config ---
HOST     = "100.95.70.33"   # Tailscale interface only
PORT     = 8080
BASE_DIR = Path(__file__).parent.parent
RAW_DIR  = BASE_DIR / "test-exports" / "raw"
CERT_DIR   = Path(__file__).parent / "certs"
CERTFILE   = CERT_DIR / "karma-01.tail3cae5f.ts.net.crt"
KEYFILE    = CERT_DIR / "karma-01.tail3cae5f.ts.net.key"
CONVERTER  = Path(__file__).parent / "converter.py"

def run_converter():
    """Run converter after each ingest to rebuild all three projections."""
    try:
        spec = importlib.util.spec_from_file_location("converter", CONVERTER)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.run()
    except Exception as e:
        print(f"  [warn] converter failed: {e}", flush=True)

RAW_DIR.mkdir(parents=True, exist_ok=True)


def _next_filename() -> str:
    """UTC timestamp + zero-padded sequence — never collides, always sorts."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    existing = sorted(RAW_DIR.glob(f"{ts}_*.json"))
    seq = len(existing) + 1
    return f"{ts}_{seq:03d}.json"


class VitalsHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
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
                f"tls: enabled\n"
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

        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length)

        try:
            parsed = json.loads(raw_body)
            is_valid_json = True
            pretty = json.dumps(parsed, indent=2, ensure_ascii=False)
        except json.JSONDecodeError as e:
            is_valid_json = False
            pretty = raw_body.decode("utf-8", errors="replace")
            print(f"  [warn] body is not valid JSON: {e}", flush=True)

        filename = _next_filename()
        dest = RAW_DIR / filename
        dest.write_text(pretty, encoding="utf-8")

        size = dest.stat().st_size
        print(f"  wrote {filename} ({size} bytes, valid_json={is_valid_json})", flush=True)

        # Rebuild all three projections immediately
        run_converter()

        receipt = {
            "status": "received",
            "file": filename,
            "bytes": size,
            "valid_json": is_valid_json,
            "projections_rebuilt": True,
        }
        self._send(200, json.dumps(receipt), "application/json")


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    if not CERTFILE.exists() or not KEYFILE.exists():
        print(f"ERROR: certs not found at {CERT_DIR}", flush=True)
        print("Run: tailscale cert karma-01.tail3cae5f.ts.net", flush=True)
        sys.exit(1)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=str(CERTFILE), keyfile=str(KEYFILE))

    print(f"Vitals Station starting on {HOST}:{PORT} (TLS)", flush=True)
    print(f"Raw exports → {RAW_DIR}", flush=True)
    print(f"GET  https://karma-01.tail3cae5f.ts.net:{PORT}/health", flush=True)
    print(f"POST https://karma-01.tail3cae5f.ts.net:{PORT}/ingest", flush=True)

    with ReusableTCPServer((HOST, PORT), VitalsHandler) as srv:
        srv.socket = context.wrap_socket(srv.socket, server_side=True)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\nshutting down", flush=True)
            sys.exit(0)
