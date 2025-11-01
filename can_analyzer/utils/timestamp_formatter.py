"""
Timestamp Formatter

Provides various timestamp formatting options for CAN messages
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Union


class TimestampFormat(Enum):
    """Timestamp format options"""
    RAW = "raw"              # Raw timestamp value (seconds with decimals)
    SECONDS = "seconds"      # Seconds (integer)
    MILLISECONDS = "ms"      # Milliseconds
    MICROSECONDS = "us"      # Microseconds
    TIME_OF_DAY = "time"     # Time of day (HH:MM:SS.mmm)
    RELATIVE = "relative"    # Relative to start (s)


class TimestampFormatter:
    """Formatter for timestamp values"""

    def __init__(self, format_type: TimestampFormat = TimestampFormat.RAW):
        self.format_type = format_type
        self.start_time = None
        self.base_datetime = None

    def set_format(self, format_type: TimestampFormat):
        """Set the timestamp format"""
        self.format_type = format_type

    def set_start_time(self, start_time: float):
        """Set the start time for relative timestamps"""
        self.start_time = start_time

    def set_base_datetime(self, base_datetime: datetime):
        """Set the base datetime for absolute time formatting"""
        self.base_datetime = base_datetime

    def format(self, timestamp: float) -> str:
        """
        Format a timestamp value

        Args:
            timestamp: Raw timestamp value in seconds

        Returns:
            Formatted timestamp string
        """
        if self.format_type == TimestampFormat.RAW:
            return self._format_raw(timestamp)
        elif self.format_type == TimestampFormat.SECONDS:
            return self._format_seconds(timestamp)
        elif self.format_type == TimestampFormat.MILLISECONDS:
            return self._format_milliseconds(timestamp)
        elif self.format_type == TimestampFormat.MICROSECONDS:
            return self._format_microseconds(timestamp)
        elif self.format_type == TimestampFormat.TIME_OF_DAY:
            return self._format_time_of_day(timestamp)
        elif self.format_type == TimestampFormat.RELATIVE:
            return self._format_relative(timestamp)
        else:
            return self._format_raw(timestamp)

    def _format_raw(self, timestamp: float) -> str:
        """Format as raw value with 6 decimal places"""
        return f"{timestamp:.6f}"

    def _format_seconds(self, timestamp: float) -> str:
        """Format as seconds (integer)"""
        return f"{int(timestamp)}s"

    def _format_milliseconds(self, timestamp: float) -> str:
        """Format as milliseconds"""
        ms = timestamp * 1000
        return f"{ms:.3f}ms"

    def _format_microseconds(self, timestamp: float) -> str:
        """Format as microseconds"""
        us = timestamp * 1000000
        return f"{us:.0f}us"

    def _format_time_of_day(self, timestamp: float) -> str:
        """Format as time of day (HH:MM:SS.mmm)"""
        if self.base_datetime is None:
            # If no base datetime, just format as duration
            return self._format_duration(timestamp)

        # Calculate absolute time
        absolute_time = self.base_datetime + timedelta(seconds=timestamp)
        return absolute_time.strftime("%H:%M:%S.%f")[:-3]  # Remove last 3 digits

    def _format_relative(self, timestamp: float) -> str:
        """Format as relative time from start"""
        if self.start_time is None:
            relative = timestamp
        else:
            relative = timestamp - self.start_time

        return f"{relative:.6f}s"

    def _format_duration(self, seconds: float) -> str:
        """Format seconds as HH:MM:SS.mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60

        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

    @staticmethod
    def parse_timestamp(timestamp_str: str) -> float:
        """
        Parse a timestamp string back to float value

        Args:
            timestamp_str: Formatted timestamp string

        Returns:
            Timestamp value in seconds
        """
        # Remove units and convert
        timestamp_str = timestamp_str.strip()

        if timestamp_str.endswith('ms'):
            # Milliseconds
            value = float(timestamp_str[:-2])
            return value / 1000.0
        elif timestamp_str.endswith('us'):
            # Microseconds
            value = float(timestamp_str[:-2])
            return value / 1000000.0
        elif timestamp_str.endswith('s'):
            # Seconds
            value = float(timestamp_str[:-1])
            return value
        else:
            # Try to parse as raw float
            try:
                return float(timestamp_str)
            except ValueError:
                # Try to parse as time format (HH:MM:SS.mmm)
                if ':' in timestamp_str:
                    parts = timestamp_str.split(':')
                    if len(parts) == 3:
                        hours = float(parts[0])
                        minutes = float(parts[1])
                        seconds = float(parts[2])
                        return hours * 3600 + minutes * 60 + seconds

                raise ValueError(f"Cannot parse timestamp: {timestamp_str}")

    def format_range(self, start: float, end: float) -> str:
        """
        Format a time range

        Args:
            start: Start timestamp
            end: End timestamp

        Returns:
            Formatted range string
        """
        duration = end - start
        return f"{self.format(start)} - {self.format(end)} (Δ{duration:.6f}s)"


class TimestampConverter:
    """Helper class for timestamp conversions"""

    @staticmethod
    def to_milliseconds(seconds: float) -> float:
        """Convert seconds to milliseconds"""
        return seconds * 1000.0

    @staticmethod
    def to_microseconds(seconds: float) -> float:
        """Convert seconds to microseconds"""
        return seconds * 1000000.0

    @staticmethod
    def from_milliseconds(milliseconds: float) -> float:
        """Convert milliseconds to seconds"""
        return milliseconds / 1000.0

    @staticmethod
    def from_microseconds(microseconds: float) -> float:
        """Convert microseconds to seconds"""
        return microseconds / 1000000.0

    @staticmethod
    def get_relative(timestamp: float, base: float) -> float:
        """Get relative timestamp"""
        return timestamp - base

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in human-readable form"""
        if seconds < 1.0:
            return f"{seconds * 1000:.3f}ms"
        elif seconds < 60.0:
            return f"{seconds:.3f}s"
        elif seconds < 3600.0:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.3f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours}h {minutes}m {secs:.3f}s"
