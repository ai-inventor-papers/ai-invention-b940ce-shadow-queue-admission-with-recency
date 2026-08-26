"""Two admission policies plugged into the same SLRU eviction backbone.

BaselineAdmission: faithful W-TinyLFU (arXiv:1512.00727v2 Sec. 3) — global Count-Min
sketch + doorkeeper, reset every W operations.

PerKeyDecayAdmission (proposed): replaces the single global reset period with a
per-key decay rate chosen from that key's own shadow-queue inter-arrival
coefficient-of-variation (CoV) — a key with regular (low-CoV) arrivals decays slowly
("stable"), a bursty/irregular (high-CoV) key decays fast ("volatile"), so frequency
estimates track drift where it happens instead of resetting everything on a fixed
global clock.
"""

from __future__ import annotations

from collections import OrderedDict, deque

import numpy as np

from sim.countmin import CountMinSketch, DoorkeeperBloom
from sim.slru import SLRU

HIT = True
MISS = False


class BaselineAdmission:
    """W-TinyLFU: shadow-queue frequency test + global periodic halving at period W."""

    def __init__(self, cache_capacity: int, w_over_c_ratio: float = 8.0) -> None:
        width = max(64, cache_capacity * 8)
        self.sketch = CountMinSketch(width=width, depth=4)
        self.doorkeeper = DoorkeeperBloom(size=max(64, cache_capacity * 8))
        self.W = max(1, int(w_over_c_ratio * cache_capacity))
        self.op_count = 0

    def on_access(self, key: int, cache: SLRU) -> bool:
        if cache.contains(key):
            cache.access(key)
            return HIT

        seen_before = self.doorkeeper.maybe_add(key)
        if seen_before:
            self.sketch.increment(key)
        self.op_count += 1
        if self.op_count >= self.W:
            self.sketch.halve_all()
            self.doorkeeper.clear()
            self.op_count = 0

        victim = cache.peek_victim()
        if victim is None or self.sketch.estimate(key) > self.sketch.estimate(victim):
            cache.admit(key, victim)
        return MISS

    def memory_bytes(self) -> int:
        return self.sketch.theoretical_bytes() + self.doorkeeper.theoretical_bytes()


class _KeyState:
    __slots__ = ("last_seen", "gaps", "decayed_freq", "bucket")

    def __init__(self, gap_window: int) -> None:
        self.last_seen: int | None = None
        self.gaps: deque[float] = deque(maxlen=gap_window)
        self.decayed_freq: float = 0.0
        self.bucket: str = "mixed"


DECAY_HALFLIVES = {"stable": 20000.0, "mixed": 4000.0, "volatile": 800.0}
GAP_WINDOW = 6
COV_STABLE_MAX = 0.5
COV_VOLATILE_MIN = 1.5


class PerKeyDecayAdmission:
    """Same shadow-queue/admission-test skeleton as BaselineAdmission, but with a
    per-key decay rate bucketed from the CoV of that key's recent inter-arrival gaps.
    Tracked keys are bounded to `max_tracked` via an LRU-eviction dict so bookkeeping
    memory does not grow without limit as the key space grows.
    """

    def __init__(self, cache_capacity: int, max_tracked: int | None = None) -> None:
        self.max_tracked = max_tracked or 4 * cache_capacity
        self.tracked: OrderedDict[int, _KeyState] = OrderedDict()
        self.global_clock = 0

    def _get_or_create(self, key: int) -> _KeyState:
        st = self.tracked.get(key)
        if st is not None:
            self.tracked.move_to_end(key)
            return st
        st = _KeyState(GAP_WINDOW)
        self.tracked[key] = st
        if len(self.tracked) > self.max_tracked:
            self.tracked.popitem(last=False)
        return st

    @staticmethod
    def _classify(gaps: deque[float]) -> str:
        if len(gaps) < 3:
            return "mixed"
        arr = np.fromiter(gaps, dtype=np.float64)
        mean = arr.mean()
        cov = arr.std() / (mean + 1e-9)
        if cov < COV_STABLE_MAX:
            return "stable"
        if cov < COV_VOLATILE_MIN:
            return "mixed"
        return "volatile"

    def _decayed_estimate(self, st: _KeyState) -> float:
        if st.last_seen is None:
            return 0.0
        gap = self.global_clock - st.last_seen
        halflife = DECAY_HALFLIVES[st.bucket]
        return st.decayed_freq * (0.5 ** (gap / halflife))

    def on_access(self, key: int, cache: SLRU) -> bool:
        self.global_clock += 1
        if cache.contains(key):
            cache.access(key)
            # Still update frequency bookkeeping on hits so decay tracks true popularity.
            self._touch(key)
            return HIT

        self._touch(key)
        st = self.tracked[key]
        victim = cache.peek_victim()
        if victim is None:
            cache.admit(key, victim)
        else:
            v_est = self._decayed_estimate(self.tracked.get(victim, _KeyState(GAP_WINDOW)))
            if st.decayed_freq > v_est:
                cache.admit(key, victim)
        return MISS

    def _touch(self, key: int) -> None:
        st = self._get_or_create(key)
        gap = None
        if st.last_seen is not None:
            gap = self.global_clock - st.last_seen
            st.gaps.append(float(gap))
        st.last_seen = self.global_clock
        st.bucket = self._classify(st.gaps)
        if gap is not None:
            decay_factor = 0.5 ** (gap / DECAY_HALFLIVES[st.bucket])
            st.decayed_freq *= decay_factor
        st.decayed_freq += 1.0

    def memory_bytes(self) -> int:
        """Exact per-key accounting: 8B key hash + 4B float freq + GAP_WINDOW*4B ring
        buffer + 1B bucket + 8B last_seen, times the number of currently tracked keys."""
        per_key = 8 + 4 + GAP_WINDOW * 4 + 1 + 8
        return len(self.tracked) * per_key

    def bucket_histogram(self) -> dict[str, int]:
        hist = {"stable": 0, "mixed": 0, "volatile": 0}
        for st in self.tracked.values():
            hist[st.bucket] += 1
        return hist
