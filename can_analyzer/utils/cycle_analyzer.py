"""
CAN message cycle (period) analysis

Groups messages by (CAN ID, channel, direction) and computes the actual transmit interval
statistics, optionally compared with a user supplied expected period.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import numpy as np


# (can_id, channel, direction)
GroupKey = Tuple[int, int, str]


@dataclass
class CycleStats:
    """Cycle statistics of one CAN ID (all intervals in milliseconds)"""
    can_id: int
    channel: int
    direction: str
    count: int
    times: np.ndarray = field(repr=False)      # timestamps (s) of each interval's end
    intervals: np.ndarray = field(repr=False)  # interval to previous message (ms)
    mean: float = 0.0
    median: float = 0.0
    min: float = 0.0
    max: float = 0.0
    std: float = 0.0

    def deviation_pct(self, expected_ms: float) -> float:
        """Mean interval deviation from expected period, in percent"""
        return (self.mean - expected_ms) / expected_ms * 100.0

    def out_of_tolerance(self, expected_ms: float, tolerance_pct: float) -> int:
        """Number of intervals outside expected * (1 +/- tolerance)"""
        return int(np.count_nonzero(self.violation_mask(expected_ms, tolerance_pct)))

    def violation_mask(self, expected_ms: float, tolerance_pct: float) -> np.ndarray:
        limit = expected_ms * tolerance_pct / 100.0
        return np.abs(self.intervals - expected_ms) > limit


class CycleAnalyzer:
    """Computes per-CAN-ID cycle statistics from a message list"""

    @staticmethod
    def analyze(messages) -> Dict[GroupKey, CycleStats]:
        timestamps: Dict[GroupKey, List[float]] = {}
        for msg in messages:
            key = (msg.can_id, msg.channel, msg.direction)
            timestamps.setdefault(key, []).append(msg.timestamp)

        result: Dict[GroupKey, CycleStats] = {}
        for key, ts in timestamps.items():
            can_id, channel, direction = key
            arr = np.sort(np.asarray(ts, dtype=float))
            intervals = np.diff(arr) * 1000.0
            stats = CycleStats(can_id=can_id, channel=channel,
                               direction=direction, count=len(arr),
                               times=arr[1:], intervals=intervals)
            if intervals.size:
                stats.mean = float(intervals.mean())
                stats.median = float(np.median(intervals))
                stats.min = float(intervals.min())
                stats.max = float(intervals.max())
                stats.std = float(intervals.std())
            result[key] = stats
        return result
