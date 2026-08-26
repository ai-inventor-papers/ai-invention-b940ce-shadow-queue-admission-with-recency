"""Steady-state hit ratio and drift-recovery-time scoring.

Recovery time is measured against a "post-drift optimal" hit rate computed FAR after
the drift event (window past `end`), so a slow, correct convergence is scored fairly
rather than penalized for not being instantaneous.
"""

from __future__ import annotations

import numpy as np


def _rolling_mean(x: np.ndarray, window: int) -> np.ndarray:
    if len(x) < window:
        return np.array([x.mean()]) if len(x) else np.array([np.nan])
    c = np.cumsum(np.insert(x.astype(np.float64), 0, 0.0))
    return (c[window:] - c[:-window]) / window


def compute_metrics(
    hits: np.ndarray,
    drift_events: list[tuple[int, int, str]],
    window: int = 2000,
    recovery_frac: float = 0.9,
) -> dict:
    n = len(hits)
    tail = hits[-window:] if n >= window else hits
    steady_state_hr = float(tail.mean()) if len(tail) else float("nan")

    recovery_times = []
    for start, end, ev_type in drift_events:
        post_start = min(end, n - 1)
        post_end = min(n, post_start + window)
        if post_end - post_start < window // 4:
            recovery_times.append({"event": ev_type, "start": start, "end": end, "recovery_steps": None, "reason": "insufficient_post_window"})
            continue
        post_optimal = float(hits[post_end:min(n, post_end + window)].mean()) if post_end + 1 < n else float(hits[post_start:post_end].mean())
        target = recovery_frac * post_optimal
        tail_hits = hits[end:]
        if len(tail_hits) < 500:
            recovery_times.append({"event": ev_type, "start": start, "end": end, "recovery_steps": None, "reason": "trace_too_short_after_event"})
            continue
        rolling = _rolling_mean(tail_hits, min(500, len(tail_hits)))
        above = np.where(rolling >= target)[0]
        t_recover = int(above[0]) if len(above) else None
        recovery_times.append({
            "event": ev_type,
            "start": start,
            "end": end,
            "post_optimal_hr": post_optimal,
            "target_hr": target,
            "recovery_steps": t_recover,
        })
    return {"steady_state_hit_ratio": steady_state_hr, "recovery_events": recovery_times}
