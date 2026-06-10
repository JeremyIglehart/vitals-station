---
event_type: schema-discovery
recording_mode: live
date_time: 2026-06-10T12:22:42-06:00
---

## First Export Landed — Wire Format Known

The first real test export from Health Auto Export arrived at
`https://karma-01.tail3cae5f.ts.net:8080/ingest`. 9.9MB. 19 metrics.
The wire format is now a first-class known quantity, not a documentation assumption.

---

## TLS Decision (resolved before this export)

**Fork considered:**
- Plain HTTP — rejected. Health Auto Export requires HTTPS. Non-negotiable.
- Self-signed cert — viable, but requires manual trust-profile install on iOS.
  Extra friction every cert rotation. Rejected.
- Tailscale-issued Let's Encrypt cert (`tailscale cert`) — chosen.

**Why:** Free on the Personal plan. iOS trusts Let's Encrypt automatically — no
profile install, no manual trust step on the phone. Cert scoped to the Tailscale
hostname (`karma-01.tail3cae5f.ts.net`), which is only reachable inside the
tailnet. The one tradeoff: machine name published to Certificate Transparency
ledger (public record, not public access). Jeremy reviewed and accepted.

**How it works:** Server binds to `100.95.70.33:8080` (Tailscale interface only —
never 0.0.0.0). `ssl.SSLContext` wraps the stdlib TCP server with the provisioned
cert and key. Key excluded from git via `.gitignore`. Cert committed.

---

## Wire Format — Confirmed Schema

Top-level structure:
```json
{ "data": { "metrics": [ ... ] } }
```

Each metric:
```json
{
  "name": "<field_name>",
  "units": "<unit_string>",
  "data": [ ... ]
}
```

**Three distinct data-point shapes (not one):**

Shape A — standard interval metric (11 metrics):
  `date`, `start`, `end`, `qty`, `source`
  Metrics: walking_heart_rate_average, walking_step_length, walking_speed,
  resting_heart_rate, walking_double_support_percentage, physical_effort,
  walking_asymmetry_percentage, respiratory_rate, heart_rate_variability,
  environmental_audio_exposure, blood_oxygen_saturation

Shape B — sleep analysis (1 metric):
  `date`, `start`, `end`, `startDate`, `endDate`, `qty`, `source`, `value`
  The `value` field carries the sleep stage name (e.g. "HKCategoryValueSleepAnalysisAsleepREM").
  startDate/endDate appear to duplicate start/end — provenance TBD.

Shape C — heart rate (1 metric):
  `date`, `start`, `end`, `Avg`, `Min`, `Max`, `context`, `source`
  No single `qty` — it's a range. `context` unknown until inspected.

Shape D — point-in-time metric (6 metrics):
  `date`, `qty`, `source`
  No interval. Metrics: time_in_daylight, flights_climbed, apple_stand_time,
  active_energy, walking_running_distance, step_count

**Timezone:** All timestamps carry `-0600` (MDT). Deterministic parse — the offset
is embedded in the string. No inference needed.

---

## Design Decision Surfaced by Real Data

**High-frequency granulation problem:** Several metrics arrive at watch-sample
granularity for a single day:
  - step_count: 21,252 data points
  - walking_running_distance: 20,859 data points
  - active_energy: 8,523 data points
  - apple_stand_time: 3,900 data points

Storing every raw data point in the projection would produce a wall of noise
unusable by Atmos or any other consumer. The events layer stores the raw payload
faithfully (immutable, complete). The projection layer must aggregate.

**Aggregation strategy decision (open — next event):**
  - Daily summary per metric (sum/avg/min/max depending on type)?
  - Hourly buckets?
  - Both (hourly detail + daily summary)?
  This gets decided when the converter is written. Deferred deliberately — the
  schema-discovery event closes here; the converter design opens as the next event.

---

## 19 Metrics Confirmed Active in This Export

walking_heart_rate_average, walking_step_length, walking_speed, sleep_analysis,
resting_heart_rate, walking_double_support_percentage, physical_effort, heart_rate,
walking_asymmetry_percentage, respiratory_rate, heart_rate_variability,
environmental_audio_exposure, time_in_daylight, blood_oxygen_saturation,
flights_climbed, apple_stand_time, active_energy, walking_running_distance, step_count

Note: This set differs from the documented "Active by default" list — actual
active metrics are determined by Jeremy's Health Auto Export configuration,
not the documentation defaults. The wire format is authoritative.

---

## Raw File

`test-exports/raw/20260610_182039_001.json` — 9.9MB, committed to git.
