# Vitals Station — Server

Schema-discovery server. Stdlib only, no dependencies.

## Run

```bash
python3 server/server.py
```

Binds to `100.95.70.33:8080` (Tailscale interface only).

## Endpoints

- `GET  /health` — liveness check
- `POST /ingest` — accepts any JSON body, writes raw to `test-exports/raw/`

## Test exports

Each POST gets its own timestamped file:
`test-exports/raw/<utc-timestamp>_<seq>.json`

Files are never overwritten. Send 10 exports, get 10 files.

## Schema discovery

This server is intentionally dumb. It stores whatever comes in.
After the first real export lands, read the raw files to understand
the wire format, then build the converter.
