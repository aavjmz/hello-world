"""
ASC File Parser for CAN Messages

Supports parsing Vector CANalyzer/CANoe ASCII format files.
Uses python-can's ASCReader as the primary parser for robust format support,
with a regex-based fallback for environments without python-can.
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

    # --- Regex patterns used as fallback when python-can is unavailable ---

    # Pattern 1: Standard format with explicit direction (Rx/Tx) and data frame marker (d)
    # Example: 0.010000 1  123  Rx   d 8  00 01 02 03 04 05 06 07
    # Also matches extended IDs: 0.010000 1  123X  Rx   d 8  00 01 02 03 04 05 06 07
    #                         or: 0.010000 1  123x  Rx   d 8  00 01 02 03 04 05 06 07
    _PATTERN_WITH_DIR = re.compile(
        r'^\s*'
        r'(?P<timestamp>[\d.]+)\s+'            # timestamp
        r'(?P<channel>\d+)\s+'                 # channel number
        r'(?P<can_id>[0-9A-Fa-f]+)[Xx]?\s+'   # CAN ID (hex), optional X/x for extended frame
        r'(?P<direction>Rx|Tx)\s+'             # direction
        r'd\s+'                                 # 'd' = data frame
        r'(?P<dlc>\d+)'                        # DLC
        r'(?:\s+(?P<data>[0-9A-Fa-f\s]*))?'   # data bytes (optional)
    )

    # Pattern 2: Format without explicit direction (only data frame marker)
    # Example: 0.010000 1  123  d 8  00 01 02 03 04 05 06 07
    #       or: 0.010000 1  123x  d 8  00 01 02 03 04 05 06 07
    _PATTERN_NO_DIR = re.compile(
        r'^\s*'
        r'(?P<timestamp>[\d.]+)\s+'            # timestamp
        r'(?P<channel>\d+)\s+'                 # channel number
        r'(?P<can_id>[0-9A-Fa-f]+)[Xx]?\s+'   # CAN ID (hex), optional X/x for extended frame
        r'd\s+'                                 # 'd' = data frame (no direction field)
        r'(?P<dlc>\d+)'                        # DLC
        r'(?:\s+(?P<data>[0-9A-Fa-f\s]*))?'   # data bytes (optional)
    )

    def __init__(self):
        self.messages: List[CANMessage] = []
        self.start_date: Optional[str] = None
        self.base_format: str = 'hex'
        self.timestamp_format: str = 'absolute'

    def parse_file(self, file_path: str) -> List[CANMessage]:
        """
        Parse an ASC file and return list of CAN messages.

        Uses python-can's ASCReader when available (handles extended IDs,
        remote frames, various format variants). Falls back to regex-based
        parsing otherwise.

        Args:
            file_path: Path to the ASC file

        Returns:
            List of CANMessage objects
        """
        # Try python-can's ASCReader first (more robust)
        try:
            import can  # noqa: F401
            return self._parse_with_python_can(file_path)
        except ImportError:
            pass
        except Exception:
            # python-can failed; fall through to regex approach
            pass

        return self._parse_with_regex(file_path)

    # ------------------------------------------------------------------
    # Primary parser: python-can ASCReader
    # ------------------------------------------------------------------

    def _parse_with_python_can(self, file_path: str) -> List[CANMessage]:
        """
        Parse ASC file using python-can's ASCReader.

        Handles:
        - Standard and extended (29-bit) CAN IDs
        - Rx / Tx direction from the ASC direction field
        - Channel names like "1", "CAN1", "Vector__XXX 1"
        - Error frames and remote frames are skipped

        Args:
            file_path: Path to the ASC file

        Returns:
            List of CANMessage objects
        """
        import can

        self.messages.clear()

        try:
            with can.ASCReader(file_path) as reader:
                for msg in reader:
                    # Skip error frames and remote frames
                    if msg.is_error_frame or msg.is_remote_frame:
                        continue

                    # Determine direction
                    if hasattr(msg, 'is_rx') and msg.is_rx is not None:
                        direction = 'Rx' if msg.is_rx else 'Tx'
                    else:
                        direction = 'Rx'

                    # Resolve channel to an integer
                    channel = self._resolve_channel(msg)

                    can_message = CANMessage(
                        timestamp=msg.timestamp,
                        can_id=msg.arbitration_id,
                        direction=direction,
                        data=bytes(msg.data) if msg.data else b'',
                        channel=channel,
                    )
                    self.messages.append(can_message)

        except FileNotFoundError:
            raise FileNotFoundError(f"ASC file not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error parsing ASC file: {str(e)}")

        return self.messages

    def _resolve_channel(self, msg) -> int:
        """Extract an integer channel number from a python-can Message."""
        if not hasattr(msg, 'channel') or msg.channel is None:
            return 1
        ch = msg.channel
        if isinstance(ch, int):
            return ch
        # Handle strings like "1", "CAN1", "Vector__XXX 1"
        m = re.search(r'\d+', str(ch))
        return int(m.group()) if m else 1

    # ------------------------------------------------------------------
    # Fallback parser: regex-based
    # ------------------------------------------------------------------

    def _parse_with_regex(self, file_path: str) -> List[CANMessage]:
        """
        Parse ASC file using regex patterns.

        Handles the two most common line formats. Comments (`;`) and
        header lines (date / base / timestamps) are processed correctly.

        Args:
            file_path: Path to the ASC file

        Returns:
            List of CANMessage objects
        """
        self.messages.clear()

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith(';'):
                        continue
                    if line.startswith('date'):
                        self._parse_date(line)
                    elif line.startswith('base'):
                        self._parse_base(line)
                    elif line.startswith('timestamps'):
                        self._parse_timestamps(line)
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
        """Parse date header line."""
        parts = line.split()
        if len(parts) >= 2:
            self.start_date = ' '.join(parts[1:])

    def _parse_base(self, line: str):
        """Parse base format header line."""
        lower = line.lower()
        if 'hex' in lower:
            self.base_format = 'hex'
        elif 'dec' in lower:
            self.base_format = 'dec'

    def _parse_timestamps(self, line: str):
        """Parse timestamps header line."""
        lower = line.lower()
        if 'absolute' in lower:
            self.timestamp_format = 'absolute'
        elif 'relative' in lower:
            self.timestamp_format = 'relative'

    def _parse_message_line(self, line: str) -> Optional[CANMessage]:
        """Try to parse a single data-frame line using both regex patterns."""
        if line.startswith('Begin') or line.startswith('End'):
            return None

        # Try pattern with explicit direction first
        match = self._PATTERN_WITH_DIR.match(line)
        if match:
            return self._build_message(match, has_direction=True)

        # Try pattern without direction field
        match = self._PATTERN_NO_DIR.match(line)
        if match:
            return self._build_message(match, has_direction=False)

        return None

    def _build_message(self, match, has_direction: bool) -> Optional[CANMessage]:
        """Build a CANMessage from a successful regex match."""
        try:
            timestamp = float(match.group('timestamp'))
            channel = int(match.group('channel'))
            can_id = int(match.group('can_id'), 16)
            direction = match.group('direction') if has_direction else 'Rx'
            dlc = int(match.group('dlc'))

            data_str = match.group('data') or ''
            # Split on whitespace, take only valid 2-char hex tokens up to DLC
            hex_tokens = [t for t in data_str.split() if len(t) == 2][:dlc]
            data_bytes = bytes(int(h, 16) for h in hex_tokens)

            return CANMessage(
                timestamp=timestamp,
                can_id=can_id,
                direction=direction,
                data=data_bytes,
                channel=channel,
            )
        except (ValueError, AttributeError):
            return None

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------

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
        return sorted(set(msg.can_id for msg in self.messages))

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
