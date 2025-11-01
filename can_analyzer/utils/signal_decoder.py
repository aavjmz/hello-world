"""
Signal Decoder for CAN Messages

Decodes CAN messages using DBC definitions and extracts signal values
"""

from typing import Dict, List, Optional, Any
from parsers.asc_parser import CANMessage
from utils.dbc_manager import DBCManager


class SignalValue:
    """Represents a decoded signal value"""

    def __init__(self, name: str, value: Any, unit: str = "", raw_value: Any = None):
        self.name = name
        self.value = value
        self.unit = unit
        self.raw_value = raw_value if raw_value is not None else value

    def __repr__(self):
        if self.unit:
            return f"{self.name}: {self.value} {self.unit}"
        else:
            return f"{self.name}: {self.value}"

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'value': self.value,
            'unit': self.unit,
            'raw_value': self.raw_value
        }

    def format_short(self) -> str:
        """Format as short string (value + unit)"""
        if self.unit:
            return f"{self.value}{self.unit}"
        return str(self.value)

    def format_full(self) -> str:
        """Format as full string (name: value unit)"""
        return repr(self)


class DecodedMessage:
    """Represents a decoded CAN message with all signals"""

    def __init__(self, can_id: int, message_name: str = ""):
        self.can_id = can_id
        self.message_name = message_name
        self.signals: Dict[str, SignalValue] = {}

    def add_signal(self, signal: SignalValue):
        """Add a signal to the decoded message"""
        self.signals[signal.name] = signal

    def get_signal(self, name: str) -> Optional[SignalValue]:
        """Get signal by name"""
        return self.signals.get(name)

    def get_signal_count(self) -> int:
        """Get number of signals"""
        return len(self.signals)

    def format_all_signals(self, separator: str = ", ") -> str:
        """Format all signals as a string"""
        if not self.signals:
            return ""
        return separator.join(s.format_full() for s in self.signals.values())

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'can_id': self.can_id,
            'message_name': self.message_name,
            'signal_count': len(self.signals),
            'signals': {name: sig.to_dict() for name, sig in self.signals.items()}
        }


class SignalDecoder:
    """Decoder for CAN message signals using DBC"""

    def __init__(self, dbc_manager: DBCManager):
        self.dbc_manager = dbc_manager

    def decode_message(self, message: CANMessage,
                      db_name: Optional[str] = None) -> Optional[DecodedMessage]:
        """
        Decode a CAN message using DBC

        Args:
            message: CANMessage object
            db_name: Optional DBC database name (uses active if not specified)

        Returns:
            DecodedMessage object or None if cannot decode
        """
        # Get DBC database
        if db_name is not None:
            db = self.dbc_manager.get_dbc(db_name)
        else:
            db = self.dbc_manager.get_active()

        if db is None or not db.is_loaded():
            return None

        # Try to decode
        try:
            # Get message definition
            msg_def = db.get_message_by_id(message.can_id)
            if msg_def is None:
                return None

            # Decode signals
            signal_values = db.decode_message(message.can_id, message.data)
            if not signal_values:
                return None

            # Create decoded message
            decoded = DecodedMessage(message.can_id, msg_def.name)

            # Add all signals
            for signal_name, value in signal_values.items():
                # Get signal definition to extract unit
                signal_def = None
                for sig in msg_def.signals:
                    if sig.name == signal_name:
                        signal_def = sig
                        break

                unit = signal_def.unit if signal_def else ""

                # Format value based on type
                formatted_value = self._format_signal_value(value)

                signal = SignalValue(
                    name=signal_name,
                    value=formatted_value,
                    unit=unit,
                    raw_value=value
                )
                decoded.add_signal(signal)

            return decoded

        except Exception as e:
            # Failed to decode
            return None

    def decode_messages(self, messages: List[CANMessage],
                       db_name: Optional[str] = None) -> List[Optional[DecodedMessage]]:
        """
        Decode multiple messages

        Args:
            messages: List of CANMessage objects
            db_name: Optional DBC database name

        Returns:
            List of DecodedMessage objects (None for messages that can't be decoded)
        """
        return [self.decode_message(msg, db_name) for msg in messages]

    def _format_signal_value(self, value: Any) -> Any:
        """Format signal value for display"""
        if isinstance(value, float):
            # Round to 2 decimal places for floats
            if value == int(value):
                return int(value)
            else:
                return round(value, 2)
        return value

    def get_signal_summary(self, decoded: DecodedMessage,
                          max_signals: int = 3) -> str:
        """
        Get a summary of signals for display

        Args:
            decoded: DecodedMessage object
            max_signals: Maximum number of signals to include

        Returns:
            Formatted string
        """
        if not decoded or not decoded.signals:
            return ""

        signal_list = list(decoded.signals.values())

        # Take first N signals
        signals_to_show = signal_list[:max_signals]

        # Format
        parts = [sig.format_full() for sig in signals_to_show]

        # Add ellipsis if there are more signals
        if len(signal_list) > max_signals:
            remaining = len(signal_list) - max_signals
            parts.append(f"... (+{remaining} more)")

        return ", ".join(parts)

    def get_all_signals_text(self, decoded: DecodedMessage) -> str:
        """
        Get all signals as formatted text

        Args:
            decoded: DecodedMessage object

        Returns:
            Formatted multi-line string
        """
        if not decoded or not decoded.signals:
            return ""

        lines = []
        lines.append(f"Message: {decoded.message_name} (0x{decoded.can_id:03X})")
        lines.append(f"Signals: {len(decoded.signals)}")
        lines.append("─" * 40)

        for signal in decoded.signals.values():
            lines.append(f"  {signal.format_full()}")

        return "\n".join(lines)

    def get_signal_names(self, can_id: int,
                        db_name: Optional[str] = None) -> List[str]:
        """
        Get list of signal names for a CAN ID

        Args:
            can_id: CAN ID
            db_name: Optional DBC database name

        Returns:
            List of signal names
        """
        # Get DBC database
        if db_name is not None:
            db = self.dbc_manager.get_dbc(db_name)
        else:
            db = self.dbc_manager.get_active()

        if db is None or not db.is_loaded():
            return []

        try:
            msg_def = db.get_message_by_id(can_id)
            if msg_def is None:
                return []

            return [sig.name for sig in msg_def.signals]
        except:
            return []

    def can_decode(self, can_id: int, db_name: Optional[str] = None) -> bool:
        """
        Check if a CAN ID can be decoded

        Args:
            can_id: CAN ID
            db_name: Optional DBC database name

        Returns:
            True if can decode
        """
        if db_name is not None:
            db = self.dbc_manager.get_dbc(db_name)
        else:
            db = self.dbc_manager.get_active()

        if db is None or not db.is_loaded():
            return False

        return db.get_message_by_id(can_id) is not None
