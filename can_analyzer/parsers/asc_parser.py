"""
ASC File Parser for CAN Messages

Supports parsing Vector CANalyzer/CANoe ASCII format files
"""

import re
from datetime import datetime
from typing import List, Dict, Optional


class CANMessage:
    """CAN message data structure"""

    def __init__(self, timestamp: float, can_id: int, direction: str,
                 data: bytes, channel: int = 1):
        self.timestamp = timestamp
        self.can_id = can_id
        self.direction = direction  # 'Rx' or 'Tx'
        self.data = data
        self.channel = channel
        self.dlc = len(data)

    def __repr__(self):
        data_str = ' '.join(f'{b:02X}' for b in self.data)
        return (f"CANMessage(t={self.timestamp:.6f}, "
                f"ID=0x{self.can_id:03X}, {self.direction}, "
                f"DLC={self.dlc}, Data=[{data_str}])")

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'can_id': self.can_id,
            'can_id_hex': f'0x{self.can_id:03X}',
            'direction': self.direction,
            'data': self.data,
            'data_hex': ' '.join(f'{b:02X}' for b in self.data),
            'dlc': self.dlc,
            'channel': self.channel
        }


class ASCParser:
    """Parser for ASC format CAN message files"""

    # Regular expression patterns
    # Pattern for CAN message line:
    # timestamp channel can_id direction dlc data_bytes
    # Example: 0.010000 1  123  Rx   d 8  00 01 02 03 04 05 06 07
    CAN_MSG_PATTERN = re.compile(
        r'^\s*'
        r'(?P<timestamp>[\d.]+)\s+'           # timestamp
        r'(?P<channel>\d+)\s+'                # channel
        r'(?P<can_id>[0-9A-Fa-f]+)\s+'       # CAN ID (hex)
        r'(?P<direction>Rx|Tx)\s+'            # direction
        r'd\s+'                                # 'd' for data frame
        r'(?P<dlc>\d+)'                       # DLC
        r'(?:\s+(?P<data>[0-9A-Fa-f\s]+))?'  # data bytes (optional)
    )

    def __init__(self):
        self.messages: List[CANMessage] = []
        self.start_date: Optional[datetime] = None
        self.base_format: str = 'hex'
        self.timestamp_format: str = 'absolute'

    def parse_file(self, file_path: str) -> List[CANMessage]:
        """
        Parse an ASC file and return list of CAN messages

        Args:
            file_path: Path to the ASC file

        Returns:
            List of CANMessage objects
        """
        self.messages.clear()

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Parse header information
                    if line.startswith('date'):
                        self._parse_date(line)
                    elif line.startswith('base'):
                        self._parse_base(line)
                    elif line.startswith('timestamps'):
                        self._parse_timestamps(line)
                    # Parse CAN message
                    else:
                        msg = self._parse_message_line(line)
                        if msg:
                            self.messages.append(msg)

        except FileNotFoundError:
            raise FileNotFoundError(f"ASC file not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error parsing ASC file: {str(e)}")

        return self.messages

    def _parse_date(self, line: str):
        """Parse date line"""
        # Example: date Mon Nov 1 10:30:00.000 2021
        try:
            # Simple extraction, can be improved
            parts = line.split()
            if len(parts) >= 2:
                # Just store the raw date string for now
                self.start_date = ' '.join(parts[1:])
        except:
            pass

    def _parse_base(self, line: str):
        """Parse base format line"""
        # Example: base hex  timestamps absolute
        if 'hex' in line.lower():
            self.base_format = 'hex'
        elif 'dec' in line.lower():
            self.base_format = 'dec'

    def _parse_timestamps(self, line: str):
        """Parse timestamp format line"""
        # Example: timestamps absolute
        if 'absolute' in line.lower():
            self.timestamp_format = 'absolute'
        elif 'relative' in line.lower():
            self.timestamp_format = 'relative'

    def _parse_message_line(self, line: str) -> Optional[CANMessage]:
        """Parse a single CAN message line"""
        if not line or line.startswith('Begin') or line.startswith('End'):
            return None

        match = self.CAN_MSG_PATTERN.match(line)
        if not match:
            return None

        try:
            timestamp = float(match.group('timestamp'))
            channel = int(match.group('channel'))
            can_id = int(match.group('can_id'), 16)  # CAN ID is in hex
            direction = match.group('direction')
            dlc = int(match.group('dlc'))

            # Parse data bytes
            data_str = match.group('data')
            if data_str:
                # Remove extra spaces and split
                data_bytes = bytes.fromhex(data_str.replace(' ', ''))
            else:
                data_bytes = b''

            return CANMessage(
                timestamp=timestamp,
                can_id=can_id,
                direction=direction,
                data=data_bytes,
                channel=channel
            )

        except (ValueError, AttributeError) as e:
            # Skip malformed lines
            return None

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
