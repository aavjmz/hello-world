"""
BLF File Parser for CAN Messages

Supports parsing Vector Binary Logging Format (BLF) files
using python-can library
"""

from typing import List, Dict, Optional
from parsers.asc_parser import CANMessage


class BLFParser:
    """Parser for BLF format CAN message files"""

    def __init__(self):
        self.messages: List[CANMessage] = []
        self._can_available = False
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if python-can is available"""
        try:
            import can
            self._can_available = True
        except ImportError:
            self._can_available = False

    def parse_file(self, file_path: str) -> List[CANMessage]:
        """
        Parse a BLF file and return list of CAN messages

        Args:
            file_path: Path to the BLF file

        Returns:
            List of CANMessage objects
        """
        if not self._can_available:
            raise ImportError(
                "python-can library is required for BLF parsing. "
                "Install it with: pip install python-can"
            )

        self.messages.clear()

        try:
            import can

            # Open BLF file using python-can
            with can.BLFReader(file_path) as reader:
                start_time = None

                for msg in reader:
                    # Get relative timestamp
                    if start_time is None:
                        start_time = msg.timestamp

                    relative_timestamp = msg.timestamp - start_time

                    # Determine direction (default to Rx if not specified)
                    # Note: python-can uses is_rx attribute, not is_tx
                    if hasattr(msg, 'is_rx'):
                        direction = 'Rx' if msg.is_rx else 'Tx'
                    else:
                        # Fallback if attribute doesn't exist
                        direction = 'Rx'

                    # Create CANMessage object
                    can_message = CANMessage(
                        timestamp=relative_timestamp,
                        can_id=msg.arbitration_id,
                        direction=direction,
                        data=bytes(msg.data),
                        channel=msg.channel if hasattr(msg, 'channel') else 1
                    )

                    self.messages.append(can_message)

        except FileNotFoundError:
            raise FileNotFoundError(f"BLF file not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error parsing BLF file: {str(e)}")

        return self.messages

    def get_messages(self) -> List[CANMessage]:
        """Get parsed messages"""
        return self.messages

    def get_message_count(self) -> int:
        """Get total message count"""
        return len(self.messages)

    def get_time_range(self) -> tuple:
        """Get time range (start, end) of messages"""
        if not self.messages:
            return (0.0, 0.0)
        timestamps = [msg.timestamp for msg in self.messages]
        return (min(timestamps), max(timestamps))

    def get_unique_can_ids(self) -> List[int]:
        """Get list of unique CAN IDs"""
        can_ids = set(msg.can_id for msg in self.messages)
        return sorted(list(can_ids))

    def filter_by_can_id(self, can_id: int) -> List[CANMessage]:
        """Filter messages by CAN ID"""
        return [msg for msg in self.messages if msg.can_id == can_id]

    def get_statistics(self) -> Dict:
        """Get parsing statistics"""
        if not self.messages:
            return {
                'total_messages': 0,
                'time_range': (0.0, 0.0),
                'duration': 0.0,
                'unique_ids': 0,
                'rx_count': 0,
                'tx_count': 0
            }

        time_range = self.get_time_range()
        rx_count = sum(1 for msg in self.messages if msg.direction == 'Rx')
        tx_count = sum(1 for msg in self.messages if msg.direction == 'Tx')

        return {
            'total_messages': len(self.messages),
            'time_range': time_range,
            'duration': time_range[1] - time_range[0],
            'unique_ids': len(self.get_unique_can_ids()),
            'rx_count': rx_count,
            'tx_count': tx_count
        }

    @staticmethod
    def is_available() -> bool:
        """Check if BLF parsing is available"""
        try:
            import can
            return True
        except ImportError:
            return False
