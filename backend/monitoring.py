import time
import logging
from collections import defaultdict, deque
from threading import Lock

logger = logging.getLogger(__name__)

_metrics = {
    "requests_total": defaultdict(int),
    "requests_success": defaultdict(int),
    "requests_failed": defaultdict(int),
    "latency_ms": defaultdict(list),
}
_recent = deque(maxlen=100)
_lock = Lock()


def log_request(endpoint: str, input_preview: str, latency_ms: float, success: bool):
    with _lock:
        _metrics["requests_total"][endpoint] += 1
        if success:
            _metrics["requests_success"][endpoint] += 1
        else:
            _metrics["requests_failed"][endpoint] += 1
        _metrics["latency_ms"][endpoint].append(latency_ms)
        _recent.append({
            "endpoint": endpoint,
            "input_preview": input_preview,
            "latency_ms": latency_ms,
            "success": success,
            "timestamp": time.time(),
        })
    level = logging.INFO if success else logging.WARNING
    logger.log(level, f"[{endpoint}] latency={latency_ms}ms success={success} input='{input_preview}'")


def get_metrics() -> dict:
    with _lock:
        summary = {}
        for endpoint in _metrics["requests_total"]:
            latencies = _metrics["latency_ms"][endpoint]
            summary[endpoint] = {
                "total": _metrics["requests_total"][endpoint],
                "success": _metrics["requests_success"][endpoint],
                "failed": _metrics["requests_failed"][endpoint],
                "p50_latency_ms": round(sorted(latencies)[len(latencies) // 2], 2) if latencies else 0,
                "p95_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.95)], 2) if len(latencies) > 1 else 0,
                "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
            }
        return {
            "endpoints": summary,
            "recent_requests": list(_recent)[-10:],
        }
