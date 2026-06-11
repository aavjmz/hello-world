"""
Vehicle Log Parser for CAN Messages

Parses *.264.can_vecihle.txt files produced by vehicle recorders.
These files contain CAN bus messages timestamped with video frame PTS values.

Format:
    pts             index       chn frameid     rx  flag    len data
    1778870865718   1           0   18f62621x   Rx  d       8   94 05 f8 42 d8 35 ff 9c
"""

from typing import List, Dict, Optional
from parsers.asc_parser import CANMessage


class VehicleLogParser:
    """Parser for vehicle recorder CAN log files (*.264.can_vecihle.txt)"""

    def __init__(self):
        self.messages: List[CANMessage] = []

    @staticmethod
    def is_vehicle_log(file_path: str) -> bool:
        """
        Detect vehicle log format by checking the header line for the 'pts' token.

        Args:
            file_path: Path to the file

        Returns:
            True if the file is a vehicle log format
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    tokens = line.split()
                    return tokens[0].lower() == 'pts'
        except Exception:
            pass
        return False

    def parse_file(self, file_path: str) -> List[CANMessage]:
        """
        Parse a vehicle log file and return a list of CAN messages.

        The 'pts' column is an absolute Unix timestamp in milliseconds.
        It is converted to seconds to match the CANMessage.timestamp contract.

        Args:
            file_path: Path to the vehicle log file

        Returns:
            List of CANMessage objects
        """
        self.messages = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    tokens = line.split()
                    if len(tokens) < 7:
                        continue
                    # Skip header line
                    if tokens[0].lower() == 'pts':
                        continue
                    msg = self._parse_line(tokens)
                    if msg is not None:
                        self.messages.append(msg)
        except FileNotFoundError:
            raise FileNotFoundError(f"Vehicle log file not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error parsing vehicle log file: {str(e)}")

        return self.messages

    def _parse_line(self, tokens: list) -> Optional[CANMessage]:
        """Parse a single data line into a CANMessage."""
        try:
            # flag must be 'd' (data frame); skip remote frames etc.
            flag = tokens[5].lower()
            if flag != 'd':
                return None

            pts_ms = int(tokens[0])
            timestamp = pts_ms / 1000.0
            channel = int(tokens[2])
            can_id = int(tokens[3].rstrip('xX'), 16)
            direction = tokens[4]  # 'Rx' or 'Tx'
            dlc = int(tokens[6])

            hex_tokens = tokens[7:7 + dlc]
            data = bytes(int(h, 16) for h in hex_tokens)

            return CANMessage(
                timestamp=timestamp,
                can_id=can_id,
                direction=direction,
                data=data,
                channel=channel,
            )
        except (ValueError, IndexError):
            return None

    def get_statistics(self) -> Dict:
        """Get parsing statistics (same schema as ASCParser)."""
        if not self.messages:
            return {
                'total_messages': 0,
                'time_range': (0.0, 0.0),
                'duration': 0.0,
                'unique_ids': 0,
                'rx_count': 0,
                'tx_count': 0,
            }

        timestamps = [msg.timestamp for msg in self.messages]
        time_range = (min(timestamps), max(timestamps))
        rx_count = sum(1 for msg in self.messages if msg.direction == 'Rx')
        tx_count = sum(1 for msg in self.messages if msg.direction == 'Tx')

        return {
            'total_messages': len(self.messages),
            'time_range': time_range,
            'duration': time_range[1] - time_range[0],
            'unique_ids': len(set(msg.can_id for msg in self.messages)),
            'rx_count': rx_count,
            'tx_count': tx_count,
        }
