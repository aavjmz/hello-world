"""
Message Filter

Provides filtering functionality for CAN messages
"""

from typing import Set


class MessageFilter:
    """Represents a message filter configuration"""

    def __init__(self):
        # CAN ID filter
        self.filter_by_can_id = False
        self.can_id_list: Set[int] = set()
        self.can_id_mode = "include"  # "include" or "exclude"

        # Direction filter
        self.filter_by_direction = False
        self.show_rx = True
        self.show_tx = True

        # Time range filter
        self.filter_by_time = False
        self.time_start = 0.0
        self.time_end = 999999.0

        # DLC filter
        self.filter_by_dlc = False
        self.dlc_min = 0
        self.dlc_max = 8

    def matches(self, message) -> bool:
        """
        Check if a message matches this filter

        Args:
            message: CANMessage object

        Returns:
            True if message passes all active filters
        """
        # CAN ID filter
        if self.filter_by_can_id:
            id_in_list = message.can_id in self.can_id_list
            if self.can_id_mode == "include":
                if not id_in_list:
                    return False
            else:  # exclude
                if id_in_list:
                    return False

        # Direction filter
        if self.filter_by_direction:
            if message.direction == "Rx" and not self.show_rx:
                return False
            if message.direction == "Tx" and not self.show_tx:
                return False

        # Time filter
        if self.filter_by_time:
            if message.timestamp < self.time_start or message.timestamp > self.time_end:
                return False

        # DLC filter
        if self.filter_by_dlc:
            if message.dlc < self.dlc_min or message.dlc > self.dlc_max:
                return False

        return True

    def is_active(self) -> bool:
        """Check if any filter is active"""
        return (self.filter_by_can_id or
                self.filter_by_direction or
                self.filter_by_time or
                self.filter_by_dlc)

    def get_description(self) -> str:
        """Get a human-readable description of active filters"""
        if not self.is_active():
            return "无过滤条件"

        parts = []

        if self.filter_by_can_id:
            id_count = len(self.can_id_list)
            mode_text = "包含" if self.can_id_mode == "include" else "排除"
            parts.append(f"CAN ID {mode_text}: {id_count}个")

        if self.filter_by_direction:
            dirs = []
            if self.show_rx:
                dirs.append("Rx")
            if self.show_tx:
                dirs.append("Tx")
            parts.append(f"方向: {'/'.join(dirs)}")

        if self.filter_by_time:
            parts.append(f"时间: {self.time_start:.3f}s - {self.time_end:.3f}s")

        if self.filter_by_dlc:
            parts.append(f"DLC: {self.dlc_min}-{self.dlc_max}")

        return " | ".join(parts)
