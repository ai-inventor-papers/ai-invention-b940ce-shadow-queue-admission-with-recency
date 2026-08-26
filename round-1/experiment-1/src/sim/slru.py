"""Segmented LRU: protected + probationary segments, standard promotion/demotion/eviction.

This is the eviction backbone shared by both admission policies (baseline and
per-key-decay) so any hit-ratio difference between them is attributable purely to the
admission test, not to a different cache replacement discipline.
"""

from __future__ import annotations

from collections import OrderedDict


class SLRU:
    """Fixed total capacity C, split protected_ratio/1-protected_ratio between segments.

    - `protected`: OrderedDict acting as an LRU (most-recently-used at the end).
    - `probationary`: OrderedDict acting as an LRU; the probationary TAIL (oldest) is
      the eviction/admission-test candidate (`peek_victim`).
    - A HIT on a probationary key promotes it to protected, possibly demoting the
      protected segment's own LRU tail back down to probationary (standard SLRU).
    """

    def __init__(self, capacity: int, protected_ratio: float = 0.8) -> None:
        if capacity < 1:
            raise ValueError("SLRU capacity must be >= 1")
        self.capacity = capacity
        self.protected_cap = max(1, int(round(capacity * protected_ratio)))
        self.probationary_cap = capacity - self.protected_cap
        if self.probationary_cap < 1:
            self.probationary_cap = 1
            self.protected_cap = capacity - 1
        self.protected: OrderedDict[int, None] = OrderedDict()
        self.probationary: OrderedDict[int, None] = OrderedDict()

    def contains(self, key: int) -> bool:
        return key in self.protected or key in self.probationary

    def size(self) -> int:
        return len(self.protected) + len(self.probationary)

    def access(self, key: int) -> bool:
        """Registers an access to a key already in the cache. Returns True (always a hit)."""
        if key in self.protected:
            self.protected.move_to_end(key)
            return True
        if key in self.probationary:
            del self.probationary[key]
            self.protected[key] = None
            self.protected.move_to_end(key)
            if len(self.protected) > self.protected_cap:
                demoted, _ = self.protected.popitem(last=False)
                self.probationary[demoted] = None
                self.probationary.move_to_end(demoted)
                self._evict_probationary_overflow()
            return True
        raise KeyError(f"access() called on key not in cache: {key}")

    def peek_victim(self) -> int | None:
        """LRU tail of probationary segment: the admission-test candidate. None if there
        is free capacity (no eviction needed to admit a new key)."""
        if self.size() < self.capacity:
            return None
        if self.probationary:
            return next(iter(self.probationary))
        # Degenerate case: probationary empty but cache is full (protected == capacity).
        return next(iter(self.protected))

    def admit(self, key: int, victim_key: int | None) -> None:
        """Evicts victim_key (if given) and inserts key at the probationary MRU end."""
        if victim_key is not None:
            if victim_key in self.probationary:
                del self.probationary[victim_key]
            elif victim_key in self.protected:
                del self.protected[victim_key]
        self.probationary[key] = None
        self.probationary.move_to_end(key)
        self._evict_probationary_overflow()

    def _evict_probationary_overflow(self) -> None:
        while len(self.probationary) > self.probationary_cap and self.size() > self.capacity:
            self.probationary.popitem(last=False)
