"""Count-Min sketch with 4-bit saturating counters and a 1-bit doorkeeper Bloom filter.

Faithful to the W-TinyLFU admission scheme (arXiv:1512.00727v2 Sec. 3): the sketch
tracks approximate access frequency, the doorkeeper avoids polluting the sketch with
one-hit-wonders, and both are reset periodically (every W operations) via halving /
clearing rather than a full re-allocation.
"""

from __future__ import annotations

import numpy as np


def _hash_i(key: int, i: int, mod: int) -> int:
    """Deterministic per-row hash: mixes key with row index via a large odd multiplier."""
    h = (key * (2654435761 + i * 40503)) ^ (i * 2246822519)
    return (h & 0xFFFFFFFF) % mod


class CountMinSketch:
    """d hash rows x w columns, 4-bit saturating counters (max 15).

    Counters are stored one-per-byte (numpy uint8) rather than packed 2-per-byte for
    simplicity and vectorized halving; the memory-accounting comparison against the
    per-key-decay variant uses the theoretical 4-bit width, not this array's actual
    footprint (see `theoretical_bytes`).
    """

    MAX_COUNT = 15

    def __init__(self, width: int, depth: int = 4, seed: int = 0) -> None:
        self.width = width
        self.depth = depth
        self.counters = np.zeros((depth, width), dtype=np.uint8)
        self._seed = seed

    def _indices(self, key: int) -> list[int]:
        return [_hash_i(key ^ self._seed, i, self.width) for i in range(self.depth)]

    def increment(self, key: int) -> None:
        for row, col in enumerate(self._indices(key)):
            c = self.counters[row, col]
            if c < self.MAX_COUNT:
                self.counters[row, col] = c + 1

    def estimate(self, key: int) -> int:
        idx = self._indices(key)
        return int(min(self.counters[row, col] for row, col in enumerate(idx)))

    def halve_all(self) -> None:
        """Vectorized floor-division-by-2 reset, as prescribed by the TinyLFU paper."""
        self.counters >>= 1

    def theoretical_bytes(self) -> int:
        """4 bits/counter, matching the paper's storage claim (not this array's uint8 layout)."""
        return (self.depth * self.width * 4 + 7) // 8


class DoorkeeperBloom:
    """1-bit-per-slot Bloom filter cleared alongside the sketch's periodic reset."""

    def __init__(self, size: int, num_hashes: int = 1, seed: int = 1) -> None:
        self.size = size
        self.num_hashes = num_hashes
        self.bits = np.zeros(size, dtype=bool)
        self._seed = seed

    def _indices(self, key: int) -> list[int]:
        return [_hash_i(key ^ self._seed, i, self.size) for i in range(self.num_hashes)]

    def maybe_add(self, key: int) -> bool:
        """Sets the key's bits; returns True if ALL were already set (i.e. seen before)."""
        idx = self._indices(key)
        already = all(self.bits[i] for i in idx)
        for i in idx:
            self.bits[i] = True
        return already

    def clear(self) -> None:
        self.bits[:] = False

    def theoretical_bytes(self) -> int:
        return (self.size + 7) // 8
