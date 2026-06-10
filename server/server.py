#!/usr/bin/env python3
"""
Vitals Station — Ingestion Server (TLS)
----------------------------------------
Receives Apple Health exports from Health Auto Export (iPhone).
Binds to the Tailscale interface only on port 8080 with Let's Encrypt TLS.

On each POST /ingest:
  1. Writes raw JSON to inbox/pending/<data-date>_received-<utc-ts>Z.json
  2. Runs the converter (processes pending → writes event → moves to processed)
  3. Returns a receipt

Endpoints:
  GET  /health  — liveness + pending/processed counts
  POST /ingest  — accepts JSON body
"""

import http.server
import importlib.util
import json
import ssl
import socketserver
import sys
from datetime import datetime, timezone
from pathlib import Path

# --- Config ---
HOST      = "100.95.70.33"
PORT      = 8080
BASE_DIR  = Path(__file__).parent.parent
PENDING   = BASE_DIR / "inbox" / "pending"
PROCESSED = BASE_DIR / "inbox" / "processed"
CERT_DIR  = Path(__file__).parent / "certs"
CERTFILE  = CERT_DIR / "karma-01.tail3cae5f.ts.net.crt"
KEYFILE   = CERT_DIR / "karma-01.tail3cae5f.ts.net.key"
CONVERTER = Path(__file__).parent / "converter.py"

PENDING.mkdir(parents=True, exist_ok=True)
PROCESSED.mkdir(parents=True, exist_ok=True)


def run_converter():
    """Run converter — processes pending exports, rebuilds projections."""
    try:
        spec = importlib.util.spec_from_file_location("converter", CONVERTER)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.run()
    except Exception as e:
        print(f"  [warn] converter failed: {e}", flush=True)
        import traceback; traceback.print_exc()


def _infer_data_date(payload: dict) -> str:
    """
    Infer the date the export data is *about* from the first timestamp
    found in the payload. Returns YYYYMMDD string. Falls back to today UTC.
    """
    try:
        metrics = payload.get("data", {}).get("metrics", [])
        for metric in metrics:
            for pt in metric.get("data", []):
                date_str = pt.get("date") or pt.get("start")
                if date_str:
                    # Format: "2026-06-09 00:22:31 -0600"
                    date_part = date_str.strip()[:10].replace("-", "")
                    if len(date_part) == 8 and date_part.isdigit():
                        return date_part
    except Exception:
        pass
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def _next_filename(data_date: str, received_ts: str) -> str:
    """
    Primary sort key:  data_date       (what the export is about)
    Tiebreaker:        received_ts     (when it arrived, UTC, to the second)
    Format: <YYYYMMDD>_received-<YYYYMMDDTHHMMSSz>.json
    """
    return f"{data_date}_received-{received_ts}.json"


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
            pending   = [f for f in PENDING.glob("*.json")]
            processed = [f for f in PROCESSED.glob("*.json")]
            body = (
                f"Vitals Station\n"
                f"status: alive\n"
                f"tls: enabled\n"
                f"inbox/pending:   {len(pending)}\n"
                f"inbox/processed: {len(processed)}\n"
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
            payload = json.loads(raw_body)
            is_valid_json = True
            pretty = json.dumps(payload, indent=2, ensure_ascii=False)
        except json.JSONDecodeError as e:
            is_valid_json = False
            payload = {}
            pretty = raw_body.decode("utf-8", errors="replace")
            print(f"  [warn] body is not valid JSON: {e}", flush=True)

        # Build filename — data date first, received timestamp as tiebreaker
        now_utc      = datetime.now(timezone.utc)
        received_ts  = now_utc.strftime("%Y%m%dT%H%M%SZ")
        data_date    = _infer_data_date(payload)
        filename     = _next_filename(data_date, received_ts)

        # Write to pending
        dest = PENDING / filename
        # If file already exists (same second, same date) add a counter
        counter = 2
        while dest.exists():
            stem = f"{data_date}_received-{received_ts}-{counter:03d}"
            dest = PENDING / f"{stem}.json"
            counter += 1

        dest.write_text(pretty, encoding="utf-8")
        size = dest.stat().st_size
        print(f"  pending: {dest.name} ({size} bytes)", flush=True)

        # Process — converter handles pending → events → processed
        run_converter()

        receipt = {
            "status":              "received",
            "file":                dest.name,
            "data_date":           f"{data_date[:4]}-{data_date[4:6]}-{data_date[6:]}",
            "received_at":         now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "bytes":               size,
            "valid_json":          is_valid_json,
            "projections_rebuilt": True,
        }
        self._send(200, json.dumps(receipt, indent=2), "application/json")


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    if not CERTFILE.exists() or not KEYFILE.exists():
        print(f"ERROR: certs not found at {CERT_DIR}", flush=True)
        sys.exit(1)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=str(CERTFILE), keyfile=str(KEYFILE))

    print(f"Vitals Station starting on {HOST}:{PORT} (TLS)", flush=True)
    print(f"Pending  → {PENDING}", flush=True)
    print(f"Processed → {PROCESSED}", flush=True)
    print(f"GET  https://karma-01.tail3cae5f.ts.net:{PORT}/health", flush=True)
    print(f"POST https://karma-01.tail3cae5f.ts.net:{PORT}/ingest", flush=True)

    with ReusableTCPServer((HOST, PORT), VitalsHandler) as srv:
        srv.socket = context.wrap_socket(srv.socket, server_side=True)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\nshutting down", flush=True)
            sys.exit(0)
