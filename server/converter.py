#!/usr/bin/env python3
"""
Vitals Station — Converter
--------------------------
Converts raw JSON exports (test-exports/raw/*.json) into:
  1. health-data/events/<date>_ingest-<seq>.md  — immutable event per export
  2. health-data/projection-micro.md            — Current Read + Today + anomalies
  3. health-data/projection-meso.md             — Yesterday arc + 3-day rolling
  4. health-data/projection-macro.md            — 7-day rolling window + trends

Run manually or called by the ingest server after each POST.
No model involvement. Purely deterministic.
"""

import json
import math
import statistics
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE     = Path(__file__).parent.parent
RAW_DIR  = BASE / "test-exports" / "raw"
EVENT_DIR = BASE / "health-data" / "events"
PROJ_DIR  = BASE / "health-data"

EVENT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Timestamp parsing
# ---------------------------------------------------------------------------

def parse_ts(s: str) -> datetime:
    """Parse '2026-06-09 14:31:00 -0600' → aware datetime."""
    s = s.strip()
    # Format: YYYY-MM-DD HH:MM:SS ±HHMM
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
# Load all raw exports, dedupe, and build a unified metric store
# ---------------------------------------------------------------------------

def load_all_exports() -> dict:
    """
    Returns: {
      metric_name: [
        { date_utc, date_local, start_local, end_local, qty, source,
          extra: {context, value, Avg, Min, Max, ...} }
      ]
    }
    Deduped on (metric_name, date_utc_str).
    """
    seen = set()
    store = defaultdict(list)

    for f in sorted(RAW_DIR.glob("*.json")):
        data = json.loads(f.read_text())
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
                key = (name, dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"))
                if key in seen:
                    continue
                seen.add(key)

                record = {
                    "date_utc":    dt_utc,
                    "date_local":  dt_local,
                    "start_local": parse_ts(pt["start"]) if "start" in pt else dt_local,
                    "end_local":   parse_ts(pt["end"])   if "end"   in pt else dt_local,
                    "qty":         pt.get("qty"),
                    "source":      pt.get("source", ""),
                    "extra":       {k: v for k, v in pt.items()
                                    if k not in ("date","start","end","qty","source",
                                                 "startDate","endDate")},
                }
                store[name].append(record)

    # Sort each metric by date_utc
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

# Metrics eligible for anomaly detection — physiological signals only.
# Accumulator metrics (steps, distance, active energy) are excluded:
# they sample thousands of times/day at near-identical micro-values,
# making statistical deviation meaningless and producing pure noise.
ANOMALY_METRICS = {
    "heart_rate", "resting_heart_rate", "heart_rate_variability",
    "blood_oxygen_saturation", "respiratory_rate", "body_temperature",
    "wrist_temperature", "walking_heart_rate_average",
}

def detect_anomalies(records: list, day: str) -> list:
    """Return records >2 std dev from day mean. Physiological signals only.
    Deduped to one anomaly per minute (most extreme value wins).
    Requires >=3 points."""
    day_recs = records_for_day(records, day)
    vals = qty_values(day_recs)
    if len(vals) < 3:
        return []
    mean = statistics.mean(vals)
    stdev = statistics.stdev(vals)
    if stdev == 0:
        return []
    flagged = [
        r for r in day_recs
        if r["qty"] is not None and abs(r["qty"] - mean) > 2 * stdev
    ]
    # Dedupe to one per minute — keep the most extreme
    by_minute = {}
    for r in flagged:
        minute_key = r["date_local"].strftime("%Y-%m-%d %H:%M")
        if minute_key not in by_minute:
            by_minute[minute_key] = r
        else:
            existing = by_minute[minute_key]
            if abs(r["qty"] - mean) > abs(existing["qty"] - mean):
                by_minute[minute_key] = r
    return list(by_minute.values())

def sleep_summary(records: list, day: str) -> dict:
    """Aggregate sleep stages for a day. Returns {stage: hours, total: hours}."""
    stages = defaultdict(float)
    for r in records_for_day(records, day):
        stage = r["extra"].get("value", "Unknown")
        if r["qty"] is not None:
            stages[stage] += r["qty"]
    total = sum(stages.values())
    return {"stages": dict(stages), "total": total}

def hr_summary(records: list, day: str) -> dict:
    """Heart rate summary: resting (Sedentary), active range, HRV."""
    day_recs = records_for_day(records, day)
    sedentary = [r for r in day_recs if r["extra"].get("context") == "Sedentary"]
    all_avgs = [r["extra"].get("Avg") for r in day_recs
                if r["extra"].get("Avg") is not None]
    all_mins = [r["extra"].get("Min") for r in day_recs
                if r["extra"].get("Min") is not None]
    all_maxs = [r["extra"].get("Max") for r in day_recs
                if r["extra"].get("Max") is not None]
    resting_vals = [r["extra"].get("Avg") for r in sedentary
                    if r["extra"].get("Avg") is not None]
    return {
        "resting_avg": round(statistics.mean(resting_vals), 1) if resting_vals else None,
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

def daily_last(records: list, day: str):
    """Most recent reading for the day."""
    day_recs = records_for_day(records, day)
    if not day_recs:
        return None
    return day_recs[-1]

def current_read(store: dict) -> dict:
    """Most recent record per metric across all data."""
    result = {}
    for name, records in store.items():
        if records:
            result[name] = records[-1]
    return result

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
        ("heart_rate",             "Heart Rate",        lambda r: f"{r['extra'].get('Avg','?')} bpm  (min {r['extra'].get('Min','?')} / max {r['extra'].get('Max','?')}) [{r['extra'].get('context','?')}]"),
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
            r = cr[key]
            ts = r["date_local"].strftime("%I:%M%p").lstrip("0").lower()
            try:
                val = fmt(r)
            except Exception:
                val = str(r.get("qty","?"))
            lines.append(f"  {label:<22s} {val}  (as of {ts})")

    # Today summary
    lines += ["", "---", "", f"## Today  ({today}, running)", ""]

    # Sleep — always from most recent sleep, not today's date
    if "sleep_analysis" in store:
        # find most recent day with sleep data
        sleep_days = sorted(set(day_str(r["date_local"])
                                for r in store["sleep_analysis"]), reverse=True)
        if sleep_days:
            sleep_day = sleep_days[0]
            s = sleep_summary(store["sleep_analysis"], sleep_day)
            if s["total"] > 0:
                stgs = s["stages"]
                lines.append(f"  Sleep ({sleep_day}):     {fmt_hm(s['total'])} total")
                for stage in ("Deep","REM","Core","Awake"):
                    if stage in stgs:
                        lines.append(f"    {stage:<8s} {fmt_hm(stgs[stage])}")
                lines.append("")

    summable = [
        ("step_count",             "Steps",          lambda v: f"{int(v):,}"),
        ("walking_running_distance","Distance",      lambda v: f"{v} mi"),
        ("active_energy",          "Active Energy",  lambda v: f"{v} kcal"),
        ("flights_climbed",        "Flights",        lambda v: str(int(v))),
        ("apple_stand_time",       "Stand Time",     lambda v: f"{int(v)} min"),
    ]
    for key, label, fmt in summable:
        if key in store:
            val = daily_total(store[key], today)
            if val is not None:
                lines.append(f"  {label:<22s} {fmt(val)}")

    # Anomalies today — physiological signals only
    anomaly_lines = []
    for name, records in store.items():
        if name not in ANOMALY_METRICS:
            continue
        anoms = detect_anomalies(records, today)
        for r in anoms:
            ts = r["date_local"].strftime("%I:%M%p").lstrip("0").lower()
            qty = r["qty"]
            anomaly_lines.append(f"  {name:<35s} {qty}  at {ts}")

    if anomaly_lines:
        lines += ["", "### Anomalies Today  (>2σ from day mean)", ""]
        lines += anomaly_lines

    lines += [""]
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

        # Sleep
        if "sleep_analysis" in store:
            s = sleep_summary(store["sleep_analysis"], day)
            if s["total"] > 0:
                stgs = s["stages"]
                lines.append(f"  Sleep:       {fmt_hm(s['total'])} total")
                for stage in ("Deep","REM","Core","Awake"):
                    if stage in stgs:
                        lines.append(f"    {stage:<8s} {fmt_hm(stgs[stage])}")
                lines.append("")

        # Heart rate
        if "heart_rate" in store:
            hr = hr_summary(store["heart_rate"], day)
            if hr["day_avg"] is not None:
                resting = f"Resting avg: {hr['resting_avg']} bpm  |  " if hr["resting_avg"] else ""
                lines.append(f"  Heart Rate:  {resting}Range: {hr['day_min']}–{hr['day_max']} bpm  |  Avg: {hr['day_avg']} bpm")

        # HRV
        if "heart_rate_variability" in store:
            val = daily_avg(store["heart_rate_variability"], day)
            if val:
                lines.append(f"  HRV:         {val} ms (avg)")

        # Activity
        lines.append("")
        for key, label2, fmt in [
            ("step_count",             "Steps",     lambda v: f"{int(v):,}"),
            ("walking_running_distance","Distance", lambda v: f"{v} mi"),
            ("active_energy",          "Active",    lambda v: f"{v} kcal"),
            ("flights_climbed",        "Flights",   lambda v: str(int(v))),
        ]:
            if key in store:
                val = daily_total(store[key], day)
                if val is not None:
                    lines.append(f"  {label2:<14s} {fmt(val)}")

        # Vitals
        lines.append("")
        for key, label2, fmt in [
            ("blood_oxygen_saturation","Blood O2",  lambda v: f"{v}%"),
            ("respiratory_rate",       "Resp Rate", lambda v: f"{v} /min"),
            ("resting_heart_rate",     "Resting HR",lambda v: f"{v} bpm"),
        ]:
            if key in store:
                val = daily_avg(store[key], day)
                if val:
                    lines.append(f"  {label2:<14s} {val}")

        # Anomalies — physiological signals only
        anomaly_lines = []
        for name, records in store.items():
            if name not in ANOMALY_METRICS:
                continue
            anoms = detect_anomalies(records, day)
            for r in anoms:
                ts = r["date_local"].strftime("%H:%M MDT")
                qty = r["qty"]
                anomaly_lines.append(f"  {ts}  {name:<35s} {qty}")

        if anomaly_lines:
            lines += ["", "### Anomalies  (>2σ from day mean)", ""]
            lines += sorted(anomaly_lines)

    lines += [""]
    return "\n".join(lines)


def build_macro(store: dict, today: str) -> str:
    today_dt = datetime.strptime(today, "%Y-%m-%d")
    days = [(today_dt - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    days.reverse()  # oldest first

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
        steps    = daily_total(store.get("step_count",[]), day)
        dist     = daily_total(store.get("walking_running_distance",[]), day)
        active   = daily_total(store.get("active_energy",[]), day)
        flights  = daily_total(store.get("flights_climbed",[]), day)
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
            if val:
                lines.append(f"  {day}  {val} bpm")

    lines += [""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run():
    print("Loading all exports...", flush=True)
    store = load_all_exports()
    total = sum(len(v) for v in store.values())
    print(f"  {len(store)} metrics, {total} records (deduped)", flush=True)

    now_utc   = datetime.now(timezone.utc)
    # Use MDT (UTC-6) as local
    mdt       = timezone(timedelta(hours=-6))
    now_local = now_utc.astimezone(mdt)
    today     = day_str(now_local)
    yesterday = day_str(now_local - timedelta(days=1))
    day_before= day_str(now_local - timedelta(days=2))

    print(f"  today={today}  yesterday={yesterday}", flush=True)

    micro = build_micro(store, today, now_local)
    meso  = build_meso(store, today, yesterday, day_before)
    macro = build_macro(store, today)

    (PROJ_DIR / "projection-micro.md").write_text(micro)
    (PROJ_DIR / "projection-meso.md").write_text(meso)
    (PROJ_DIR / "projection-macro.md").write_text(macro)

    print("  wrote projection-micro.md", flush=True)
    print("  wrote projection-meso.md",  flush=True)
    print("  wrote projection-macro.md", flush=True)
    print("Done.", flush=True)


if __name__ == "__main__":
    run()
