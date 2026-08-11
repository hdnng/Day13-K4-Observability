"""Aggregate data/logs.jsonl into the 6 dashboard panels defined in
config/dashboard.yaml, and emit a single JSON file the HTML dashboard
artifact reads. Read-only against logs; does not touch app/ or config/.
"""
from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"
OUT_PATH = REPO_ROOT / "submission" / "evidence" / "dashboard_data.json"

THRESHOLDS = {
    "latency_p95_ms": 3000,
    "error_rate_pct": 2,
    "cost_usd_total": 2.5,
    "tokens_total": 50000,
    "quality_avg": 0.75,
    "traffic_rate_per_min": 1,
}


def percentile(values: list[float], p: int) -> float:
    if not values:
        return 0.0
    items = sorted(values)
    idx = max(0, min(len(items) - 1, round((p / 100) * len(items) + 0.5) - 1))
    return float(items[idx])


def minute_bucket(ts: str) -> str:
    return ts[:16]  # "YYYY-MM-DDTHH:MM"


def main() -> None:
    records = []
    with LOG_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))

    received = [r for r in records if r.get("event") == "request_received"]
    sent = [r for r in records if r.get("event") == "response_sent"]
    failed = [r for r in records if r.get("event") == "request_failed"]

    # Incident windows, derived from the app's own incident_enabled/disabled
    # log events (app/main.py), so the dashboard can annotate what caused an
    # anomaly instead of showing an unexplained spike or gap.
    incident_events = [
        r for r in records if r.get("event") in ("incident_enabled", "incident_disabled")
    ]
    open_incidents: dict[str, str] = {}
    incident_windows: list[dict[str, str]] = []
    for r in sorted(incident_events, key=lambda r: r["ts"]):
        name = (r.get("payload") or {}).get("name", "unknown")
        if r["event"] == "incident_enabled":
            open_incidents[name] = r["ts"]
        elif r["event"] == "incident_disabled" and name in open_incidents:
            incident_windows.append(
                {"scenario": name, "start": open_incidents.pop(name), "end": r["ts"]}
            )
    for name, start in open_incidents.items():
        incident_windows.append({"scenario": name, "start": start, "end": None})

    latencies = [r["latency_ms"] for r in sent if r.get("latency_ms") is not None]
    costs = [r["cost_usd"] for r in sent if r.get("cost_usd") is not None]
    tokens_in = [r["tokens_in"] for r in sent if r.get("tokens_in") is not None]
    tokens_out = [r["tokens_out"] for r in sent if r.get("tokens_out") is not None]
    quality = [r["quality_score"] for r in sent if r.get("quality_score") is not None]

    total_requests = len(received)
    total_failed = len(failed)
    error_rate_pct = round((total_failed / total_requests * 100) if total_requests else 0.0, 2)
    error_breakdown = Counter(r.get("error_type", "unknown") for r in failed)

    traffic_by_minute: dict[str, int] = defaultdict(int)
    for r in received:
        traffic_by_minute[minute_bucket(r["ts"])] += 1

    cost_by_minute: dict[str, float] = defaultdict(float)
    for r in sent:
        cost_by_minute[minute_bucket(r["ts"])] += r.get("cost_usd", 0.0)

    latency_by_minute: dict[str, list[float]] = defaultdict(list)
    for r in sent:
        if r.get("latency_ms") is not None:
            latency_by_minute[minute_bucket(r["ts"])].append(r["latency_ms"])

    minutes_sorted = sorted(
        set(traffic_by_minute) | set(cost_by_minute) | set(latency_by_minute)
    )

    timeline = []
    for m in minutes_sorted:
        vals = latency_by_minute.get(m, [])
        timeline.append(
            {
                "minute": m,
                "traffic": traffic_by_minute.get(m, 0),
                "cost_usd": round(cost_by_minute.get(m, 0.0), 4),
                "latency_p50": percentile(vals, 50) if vals else None,
                "latency_p95": percentile(vals, 95) if vals else None,
            }
        )

    feature_breakdown = Counter(r.get("feature", "unknown") for r in received)

    incident_annotations = [
        {
            "scenario": w["scenario"],
            "start_minute": minute_bucket(w["start"]),
            "end_minute": minute_bucket(w["end"]) if w["end"] else None,
        }
        for w in incident_windows
    ]

    data = {
        "generated_from": str(LOG_PATH.relative_to(REPO_ROOT)),
        "time_range_minutes": 60,
        "totals": {
            "requests_received": total_requests,
            "responses_sent": len(sent),
            "requests_failed": total_failed,
        },
        "panels": {
            "latency": {
                "unit": "ms",
                "p50": percentile(latencies, 50),
                "p95": percentile(latencies, 95),
                "p99": percentile(latencies, 99),
                "threshold_p95": THRESHOLDS["latency_p95_ms"],
            },
            "traffic": {
                "unit": "requests_per_minute",
                "total": total_requests,
                "by_feature": dict(feature_breakdown),
                "threshold_min_rate": THRESHOLDS["traffic_rate_per_min"],
            },
            "errors": {
                "unit": "percent",
                "error_rate_pct": error_rate_pct,
                "total_failed": total_failed,
                "total_requests": total_requests,
                "breakdown": dict(error_breakdown),
                "threshold": THRESHOLDS["error_rate_pct"],
            },
            "cost": {
                "unit": "usd",
                "total": round(sum(costs), 4),
                "avg": round(statistics.fmean(costs), 6) if costs else 0.0,
                "threshold_total": THRESHOLDS["cost_usd_total"],
            },
            "tokens": {
                "unit": "tokens",
                "tokens_in_total": sum(tokens_in),
                "tokens_out_total": sum(tokens_out),
                "total": sum(tokens_in) + sum(tokens_out),
                "threshold_total": THRESHOLDS["tokens_total"],
            },
            "quality": {
                "unit": "score_0_to_1",
                "avg": round(statistics.fmean(quality), 4) if quality else 0.0,
                "min": round(min(quality), 4) if quality else 0.0,
                "max": round(max(quality), 4) if quality else 0.0,
                "threshold_min": THRESHOLDS["quality_avg"],
            },
        },
        "timeline": timeline,
        "incidents": incident_annotations,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT_PATH.relative_to(REPO_ROOT)}")
    print(json.dumps(data["panels"], indent=2))


if __name__ == "__main__":
    main()
