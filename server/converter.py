#!/usr/bin/env python3
"""
Vitals Station — Converter
--------------------------
Processing pipeline:

  1. inbox/pending/*.json   → parse, write health-data/events/*.md,
                               prepend YAML provenance header,
                               move to inbox/processed/
  2. inbox/processed/*.json → load all (strips YAML header), dedupe
  3. Rebuild three projections from unified deduplicated store

No model involvement. Purely deterministic.
"""

import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE_DIR  = Path(__file__).parent.parent
PENDING    = BASE_DIR / "inbox" / "pending"
PROCESSED  = BASE_DIR / "inbox" / "processed"
EVENT_DIR  = BASE_DIR / "health-data" / "events"
PROJ_DIR   = BASE_DIR / "health-data"

# Load 8 days of files to build a 7-day projection.
# The extra day catches boundary bleed — exports often carry a few records
# from the prior day at the seam (e.g. 23:58 on day N appears in day N+1 file).
LOAD_DAYS  = 8

PENDING.mkdir(parents=True, exist_ok=True)
PROCESSED.mkdir(parents=True, exist_ok=True)
EVENT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Timestamp parsing
# ---------------------------------------------------------------------------

def parse_ts(s: str) -> datetime:
    """Parse '2026-06-09 14:31:00 -0600' → aware datetime."""
    s = s.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M:%S%z"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise ValueError(f"Cannot parse timestamp: {s!r}")

def to_utc(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc)

def fmt_local(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S%z")

def fmt_hm(hours: float) -> str:
    total_minutes = round(hours * 60)
    h = total_minutes // 60
    m = total_minutes % 60
    return f"{h}h {m:02d}m"

# ---------------------------------------------------------------------------
# Inbox processing — pending → events → processed
# ---------------------------------------------------------------------------

def _parse_with_frontmatter(path: Path) -> dict:
    """Read a file that may have YAML frontmatter. Returns parsed JSON."""
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            text = parts[2].strip()
    return json.loads(text)


def _ingest_pending() -> list:
    """
    For each file in inbox/pending/:
      - Parse JSON payload
      - Write health-data/events/<stem>.md (immutable event record)
      - Prepend YAML provenance header, move to inbox/processed/
      - Remove from pending
    Returns list of processed filenames.
    """
    done = []
    for src in sorted(PENDING.glob("*.json")):
        if src.name == ".keep":
            continue
        try:
            payload = json.loads(src.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  [warn] cannot parse {src.name}: {e}", flush=True)
            continue

        now_utc    = datetime.now(timezone.utc)
        metrics    = payload.get("data", {}).get("metrics", [])
        names      = [m["name"] for m in metrics]
        rec_count  = sum(len(m.get("data", [])) for m in metrics)

        # data_date from filename prefix e.g. 20260609_received-...
        stem           = src.stem
        data_date_raw  = stem.split("_")[0]           # "20260609"
        data_date_fmt  = (f"{data_date_raw[:4]}-"
                          f"{data_date_raw[4:6]}-"
                          f"{data_date_raw[6:]}")      # "2026-06-09"

        received_raw = ""
        if "received-" in stem:
            received_raw = stem.split("received-")[1]  # "20260610T182039Z"

        # --- Write event file ---
        event_name = stem + ".md"
        event_path = EVENT_DIR / event_name
        event_path.write_text(
            f"---\n"
            f"event_type: health-ingest\n"
            f"data_date: {data_date_fmt}\n"
            f"received_at: {now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
            f"source_file: inbox/processed/{src.name}\n"
            f"metrics_count: {len(names)}\n"
            f"records_count: {rec_count}\n"
            f"metrics: [{', '.join(names)}]\n"
            f"---\n\n"
            f"Raw payload archived at: inbox/processed/{src.name}\n",
            encoding="utf-8"
        )
        print(f"  event: {event_name}", flush=True)

        # --- Move to processed with YAML provenance header prepended ---
        header = (
            f"---\n"
            f"processed_at: {now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
            f"data_date: {data_date_fmt}\n"
            f"received_at: {received_raw}\n"
            f"event_written: health-data/events/{event_name}\n"
            f"projections_rebuilt: [projection-micro.md, projection-meso.md, projection-macro.md]\n"
            f"metrics_count: {len(names)}\n"
            f"records_count: {rec_count}\n"
            f"---\n\n"
        )
        dest = PROCESSED / src.name
        dest.write_text(
            header + json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        src.unlink()
        done.append(src.name)
        print(f"  processed: {src.name}", flush=True)

    return done


# ---------------------------------------------------------------------------
# Load all processed exports into unified deduplicated store
# ---------------------------------------------------------------------------

def _window_files(directory: Path, days: int) -> list:
    """
    Return files from directory whose filename date prefix falls within
    the last `days` days (inclusive of today UTC). Filename format:
    YYYYMMDD_received-*.json — the date prefix is the data date.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y%m%d")
    files = []
    for f in sorted(directory.glob("*.json")):
        if f.name == ".keep":
            continue
        date_prefix = f.name[:8]
        if date_prefix.isdigit() and date_prefix >= cutoff:
            files.append(f)
    return files


def load_all_exports() -> dict:
    """
    Reads the last LOAD_DAYS days of files from inbox/processed/.
    Also reads any still in inbox/pending/ (always include — just arrived).
    Dedupes on (metric_name, date_utc_str).
    Returns: { metric_name: [records sorted by date_utc] }
    """
    seen  = set()
    store = defaultdict(list)

    sources = _window_files(PROCESSED, LOAD_DAYS) + sorted(PENDING.glob("*.json"))
    for f in sources:
        if f.name == ".keep":
            continue
        try:
            data = _parse_with_frontmatter(f)
        except Exception as e:
            print(f"  [warn] skipping {f.name}: {e}", flush=True)
            continue

        for metric in data.get("data", {}).get("metrics", []):
            name = metric["name"]
            for pt in metric.get("data", []):
                raw_date = pt.get("date", "")
                if not raw_date:
                    continue
                try:
                    dt_local = parse_ts(raw_date)
                except ValueError:
                    continue
                dt_utc = to_utc(dt_local)
                key    = (name, dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"))
                if key in seen:
                    continue
                seen.add(key)

                store[name].append({
                    "date_utc":    dt_utc,
                    "date_local":  dt_local,
                    "start_local": parse_ts(pt["start"]) if "start" in pt else dt_local,
                    "end_local":   parse_ts(pt["end"])   if "end"   in pt else dt_local,
                    "qty":         pt.get("qty"),
                    "source":      pt.get("source", ""),
                    "extra":       {k: v for k, v in pt.items()
                                    if k not in ("date","start","end","qty",
                                                 "source","startDate","endDate")},
                })

    for name in store:
        store[name].sort(key=lambda r: r["date_utc"])
    return dict(store)


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

def day_str(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")

def records_for_day(records: list, day: str) -> list:
    return [r for r in records if day_str(r["date_local"]) == day]

def qty_values(records: list) -> list:
    return [r["qty"] for r in records if r["qty"] is not None]

# Anomaly detection restricted to physiological signals only.
# Accumulator metrics (steps, distance, active energy) arrive at per-second
# granularity with near-identical micro-values — statistical deviation is
# meaningless on them and produces pure noise.
ANOMALY_METRICS = {
    "heart_rate", "resting_heart_rate", "heart_rate_variability",
    "blood_oxygen_saturation", "respiratory_rate", "body_temperature",
    "wrist_temperature", "walking_heart_rate_average",
}

def detect_anomalies(records: list, day: str) -> list:
    """
    Returns readings >2 std dev from day mean.
    Physiological signals only. Deduped to one per minute (most extreme wins).
    Requires >=3 points.
    """
    day_recs = records_for_day(records, day)
    vals = qty_values(day_recs)
    if len(vals) < 3:
        return []
    mean  = statistics.mean(vals)
    stdev = statistics.stdev(vals)
    if stdev == 0:
        return []
    flagged = [r for r in day_recs
               if r["qty"] is not None and abs(r["qty"] - mean) > 2 * stdev]
    by_minute = {}
    for r in flagged:
        key = r["date_local"].strftime("%Y-%m-%d %H:%M")
        if key not in by_minute or abs(r["qty"]-mean) > abs(by_minute[key]["qty"]-mean):
            by_minute[key] = r
    return list(by_minute.values())

def sleep_summary(records: list, day: str) -> dict:
    stages = defaultdict(float)
    for r in records_for_day(records, day):
        stage = r["extra"].get("value", "Unknown")
        if r["qty"] is not None:
            stages[stage] += r["qty"]
    return {"stages": dict(stages), "total": sum(stages.values())}

def hr_summary(records: list, day: str) -> dict:
    day_recs  = records_for_day(records, day)
    sedentary = [r for r in day_recs if r["extra"].get("context") == "Sedentary"]
    all_avgs  = [r["extra"].get("Avg") for r in day_recs if r["extra"].get("Avg") is not None]
    all_mins  = [r["extra"].get("Min") for r in day_recs if r["extra"].get("Min") is not None]
    all_maxs  = [r["extra"].get("Max") for r in day_recs if r["extra"].get("Max") is not None]
    rest_vals = [r["extra"].get("Avg") for r in sedentary if r["extra"].get("Avg") is not None]
    return {
        "resting_avg": round(statistics.mean(rest_vals), 1) if rest_vals else None,
        "day_min":     min(all_mins) if all_mins else None,
        "day_max":     max(all_maxs) if all_maxs else None,
        "day_avg":     round(statistics.mean(all_avgs), 1) if all_avgs else None,
    }

def daily_total(records: list, day: str) -> float | None:
    vals = qty_values(records_for_day(records, day))
    return round(sum(vals), 1) if vals else None

def daily_avg(records: list, day: str) -> float | None:
    vals = qty_values(records_for_day(records, day))
    return round(statistics.mean(vals), 1) if vals else None

def current_read(store: dict) -> dict:
    return {name: records[-1] for name, records in store.items() if records}


# ---------------------------------------------------------------------------
# Projection builders
# ---------------------------------------------------------------------------

def build_micro(store: dict, today: str, now_local: datetime) -> str:
    lines = [
        "# Vitals Station — Micro Projection",
        "",
        f"Last sync: {fmt_local(now_local)}",
        f"Today: {today}",
        "",
        "---",
        "",
        "## Current Read  (most recent value per metric)",
        "",
    ]
    cr = current_read(store)
    order = [
        ("heart_rate",             "Heart Rate",
         lambda r: f"{r['extra'].get('Avg','?')} bpm  (min {r['extra'].get('Min','?')} / max {r['extra'].get('Max','?')}) [{r['extra'].get('context','?')}]"),
        ("resting_heart_rate",     "Resting HR",        lambda r: f"{r['qty']} bpm"),
        ("heart_rate_variability", "HRV",               lambda r: f"{round(r['qty'],1)} ms"),
        ("blood_oxygen_saturation","Blood Oxygen",      lambda r: f"{round(r['qty'],1)}%"),
        ("respiratory_rate",       "Respiratory Rate",  lambda r: f"{round(r['qty'],1)} /min"),
        ("step_count",             "Steps (today so far)", lambda r: f"{int(r['qty']):,}"),
        ("active_energy",          "Active Energy",     lambda r: f"{round(r['qty'],1)} kcal"),
        ("walking_running_distance","Distance",         lambda r: f"{round(r['qty'],2)} mi"),
        ("physical_effort",        "Physical Effort",   lambda r: f"{round(r['qty'],2)} kcal/hr·kg"),
    ]
    for key, label, fmt in order:
        if key in cr:
            r  = cr[key]
            ts = r["date_local"].strftime("%I:%M%p").lstrip("0").lower()
            try:    val = fmt(r)
            except: val = str(r.get("qty","?"))
            lines.append(f"  {label:<22s} {val}  (as of {ts})")

    lines += ["", "---", "", f"## Today  ({today}, running)", ""]

    if "sleep_analysis" in store:
        sleep_days = sorted(set(day_str(r["date_local"]) for r in store["sleep_analysis"]), reverse=True)
        if sleep_days:
            s = sleep_summary(store["sleep_analysis"], sleep_days[0])
            if s["total"] > 0:
                lines.append(f"  Sleep ({sleep_days[0]}):     {fmt_hm(s['total'])} total")
                for stage in ("Deep","REM","Core","Awake"):
                    if stage in s["stages"]:
                        lines.append(f"    {stage:<8s} {fmt_hm(s['stages'][stage])}")
                lines.append("")

    for key, label, fmt in [
        ("step_count",             "Steps",         lambda v: f"{int(v):,}"),
        ("walking_running_distance","Distance",     lambda v: f"{v} mi"),
        ("active_energy",          "Active Energy", lambda v: f"{v} kcal"),
        ("flights_climbed",        "Flights",       lambda v: str(int(v))),
        ("apple_stand_time",       "Stand Time",    lambda v: f"{int(v)} min"),
    ]:
        if key in store:
            val = daily_total(store[key], today)
            if val is not None:
                lines.append(f"  {label:<22s} {fmt(val)}")

    anomaly_lines = []
    for name, records in store.items():
        if name not in ANOMALY_METRICS:
            continue
        for r in detect_anomalies(records, today):
            ts  = r["date_local"].strftime("%I:%M%p").lstrip("0").lower()
            lines_a = f"  {name:<35s} {r['qty']}  at {ts}"
            anomaly_lines.append(lines_a)
    if anomaly_lines:
        lines += ["", "### Anomalies Today  (>2σ from day mean)", ""]
        lines += anomaly_lines

    lines.append("")
    return "\n".join(lines)


def build_meso(store: dict, today: str, yesterday: str, day_before: str) -> str:
    lines = [
        "# Vitals Station — Meso Projection",
        "",
        f"Generated: {today}",
        f"Covers: {day_before} / {yesterday} / {today} (partial)",
        "",
        "---",
    ]
    for day, label in [(yesterday, "Yesterday"), (day_before, "Day Before Yesterday")]:
        lines += ["", f"## {label}  ({day})", ""]
        if "sleep_analysis" in store:
            s = sleep_summary(store["sleep_analysis"], day)
            if s["total"] > 0:
                lines.append(f"  Sleep:       {fmt_hm(s['total'])} total")
                for stage in ("Deep","REM","Core","Awake"):
                    if stage in s["stages"]:
                        lines.append(f"    {stage:<8s} {fmt_hm(s['stages'][stage])}")
                lines.append("")
        if "heart_rate" in store:
            hr = hr_summary(store["heart_rate"], day)
            if hr["day_avg"] is not None:
                rest = f"Resting avg: {hr['resting_avg']} bpm  |  " if hr["resting_avg"] else ""
                lines.append(f"  Heart Rate:  {rest}Range: {hr['day_min']}–{hr['day_max']} bpm  |  Avg: {hr['day_avg']} bpm")
        if "heart_rate_variability" in store:
            val = daily_avg(store["heart_rate_variability"], day)
            if val: lines.append(f"  HRV:         {val} ms (avg)")
        lines.append("")
        for key, label2, fmt in [
            ("step_count",             "Steps",    lambda v: f"{int(v):,}"),
            ("walking_running_distance","Distance",lambda v: f"{v} mi"),
            ("active_energy",          "Active",   lambda v: f"{v} kcal"),
            ("flights_climbed",        "Flights",  lambda v: str(int(v))),
        ]:
            if key in store:
                val = daily_total(store[key], day)
                if val is not None: lines.append(f"  {label2:<14s} {fmt(val)}")
        lines.append("")
        for key, label2, fmt in [
            ("blood_oxygen_saturation","Blood O2",  lambda v: f"{v}%"),
            ("respiratory_rate",       "Resp Rate", lambda v: f"{v} /min"),
            ("resting_heart_rate",     "Resting HR",lambda v: f"{v} bpm"),
        ]:
            if key in store:
                val = daily_avg(store[key], day)
                if val: lines.append(f"  {label2:<14s} {val}")
        anomaly_lines = []
        for name, records in store.items():
            if name not in ANOMALY_METRICS:
                continue
            for r in detect_anomalies(records, day):
                ts = r["date_local"].strftime("%H:%M MDT")
                anomaly_lines.append(f"  {ts}  {name:<35s} {r['qty']}")
        if anomaly_lines:
            lines += ["", "### Anomalies  (>2σ from day mean)", ""]
            lines += sorted(anomaly_lines)
    lines.append("")
    return "\n".join(lines)


def build_macro(store: dict, today: str) -> str:
    today_dt = datetime.strptime(today, "%Y-%m-%d")
    days = [(today_dt - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    days.reverse()
    lines = [
        "# Vitals Station — Macro Projection",
        "",
        f"Generated: {today}",
        f"Window: {days[0]} → {days[-1]} (7 days)",
        "",
        "---",
        "",
        "## Daily Totals",
        "",
        f"  {'Date':<12} {'Steps':>8} {'Distance':>10} {'Active':>10} {'Flights':>8}",
        f"  {'-'*12} {'-'*8} {'-'*10} {'-'*10} {'-'*8}",
    ]
    for day in days:
        steps   = daily_total(store.get("step_count",[]), day)
        dist    = daily_total(store.get("walking_running_distance",[]), day)
        active  = daily_total(store.get("active_energy",[]), day)
        flights = daily_total(store.get("flights_climbed",[]), day)
        lines.append(
            f"  {day:<12} "
            f"{(str(int(steps))+' ') if steps else '—':>9}"
            f"{(str(dist)+' mi') if dist else '—':>11}"
            f"{(str(active)+' kcal') if active else '—':>11}"
            f"{(str(int(flights))) if flights else '—':>9}"
        )
    lines += ["", "## Sleep (total per night)", ""]
    for day in days:
        if "sleep_analysis" in store:
            s = sleep_summary(store["sleep_analysis"], day)
            if s["total"] > 0:
                lines.append(f"  {day}  {fmt_hm(s['total'])}")
    lines += ["", "## Resting Heart Rate", ""]
    for day in days:
        if "resting_heart_rate" in store:
            val = daily_avg(store["resting_heart_rate"], day)
            if val: lines.append(f"  {day}  {val} bpm")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _notify_telegram(store: dict, today: str, started: datetime):
    """Send a concise ingest summary to Karma B-Side via Hermes send_message."""
    import subprocess, sys, json as _json, statistics as _stats

    elapsed = round((datetime.now(timezone.utc) - started).total_seconds(), 1)
    total   = sum(len(v) for v in store.values())
    processed_count = len([f for f in PROCESSED.glob("*.json") if f.name != ".keep"])

    # Anomalies for yesterday (most recent complete day)
    mdt       = timezone(timedelta(hours=-6))
    yesterday = day_str(datetime.now(timezone.utc).astimezone(mdt) - timedelta(days=1))
    anom_lines = []
    for name, records in store.items():
        if name not in ANOMALY_METRICS:
            continue
        for r in detect_anomalies(records, yesterday):
            ts  = r["date_local"].strftime("%I:%M%p").lstrip("0").lower()
            anom_lines.append(f"  {name}: {r['qty']} at {ts}")

    lines = [
        f"✓ Vitals Station — ingest complete",
        f"Date: {today}  |  {elapsed}s  |  {total:,} records  |  {processed_count} exports on file",
    ]
    if anom_lines:
        lines.append(f"Anomalies yesterday ({yesterday}):")
        lines += anom_lines[:5]  # cap at 5 so it doesn't flood
    else:
        lines.append(f"No anomalies detected for {yesterday}")

    msg = "\n".join(lines)

    try:
        hermes_bin = subprocess.run(
            ["which", "hermes"], capture_output=True, text=True
        ).stdout.strip() or "/home/jeremy/.local/bin/hermes"

        result = subprocess.run(
            [hermes_bin, "send",
             "-t", "telegram:Karma B-Side (group)",
             msg],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            print(f"  [warn] telegram notify failed: {result.stderr[:200]}", flush=True)
        else:
            print(f"  telegram: notified B-Side", flush=True)
    except Exception as e:
        print(f"  [warn] telegram notify error: {e}", flush=True)


def run():
    elapsed_start = datetime.now(timezone.utc)

    # Step 1: process pending imports
    pending = [p for p in PENDING.glob("*.json") if p.name != ".keep"]
    if pending:
        print(f"Processing {len(pending)} pending export(s)...", flush=True)
        _ingest_pending()
    else:
        print("No pending exports.", flush=True)

    # Step 2: load all processed data
    print("Loading all exports...", flush=True)
    store = load_all_exports()
    total = sum(len(v) for v in store.values())
    print(f"  {len(store)} metrics, {total} records (deduped)", flush=True)

    # Step 3: rebuild projections
    mdt       = timezone(timedelta(hours=-6))
    now_local = datetime.now(timezone.utc).astimezone(mdt)
    today     = day_str(now_local)
    yesterday = day_str(now_local - timedelta(days=1))
    day_before= day_str(now_local - timedelta(days=2))

    print(f"  today={today}  yesterday={yesterday}", flush=True)

    (PROJ_DIR / "projection-micro.md").write_text(build_micro(store, today, now_local))
    (PROJ_DIR / "projection-meso.md").write_text(build_meso(store, today, yesterday, day_before))
    (PROJ_DIR / "projection-macro.md").write_text(build_macro(store, today))

    print("  wrote projection-micro.md", flush=True)
    print("  wrote projection-meso.md",  flush=True)
    print("  wrote projection-macro.md", flush=True)
    print("Done.", flush=True)

    # Telegram notification — send summary to Karma B-Side
    _notify_telegram(store, today, elapsed_start)


if __name__ == "__main__":
    run()
