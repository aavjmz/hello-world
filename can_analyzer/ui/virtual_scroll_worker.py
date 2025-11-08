"""
Virtual Scrolling Data Worker - Background thread for preparing table data
"""

from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker
from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from typing import List, Optional, Tuple
from parsers.asc_parser import CANMessage
from utils.timestamp_formatter import TimestampFormatter
from utils.signal_decoder import SignalDecoder


class TableRowData:
    """Represents prepared data for a single table row"""

    def __init__(self, row_items: List[QTableWidgetItem], message_index: int):
        self.row_items = row_items
        self.message_index = message_index


class VirtualScrollDataWorker(QThread):
    """
    Worker thread for preparing table row data in background

    This separates data preparation from UI updates for better performance
    """

    # Signal emitted when data chunk is ready
    data_ready = pyqtSignal(int, int, list)  # start_index, end_index, row_data_list

    def __init__(self, parent=None):
        super().__init__(parent)

        self._mutex = QMutex()
        self._messages: List[CANMessage] = []
        self._timestamp_formatter: Optional[TimestampFormatter] = None
        self._signal_decoder: Optional[SignalDecoder] = None

        self._requested_ranges: List[Tuple[int, int]] = []  # Queue of (start, end) ranges
        self._should_stop = False

    def set_data(self, messages: List[CANMessage],
                 timestamp_formatter: TimestampFormatter,
                 signal_decoder: Optional[SignalDecoder]):
        """
        Set data for the worker

        Args:
            messages: List of messages
            timestamp_formatter: Formatter for timestamps
            signal_decoder: Optional signal decoder
        """
        with QMutexLocker(self._mutex):
            self._messages = messages
            self._timestamp_formatter = timestamp_formatter
            self._signal_decoder = signal_decoder

    def request_data_range(self, start_index: int, end_index: int):
        """
        Request data for a specific range

        Args:
            start_index: Start index
            end_index: End index
        """
        with QMutexLocker(self._mutex):
            # Add to queue if not already processing this range
            request = (start_index, end_index)
            if request not in self._requested_ranges:
                self._requested_ranges.append(request)

    def clear_queue(self):
        """Clear the request queue"""
        with QMutexLocker(self._mutex):
            self._requested_ranges.clear()

    def stop(self):
        """Stop the worker thread"""
        with QMutexLocker(self._mutex):
            self._should_stop = True

    def run(self):
        """Main worker loop"""
        while True:
            # Check for stop signal
            with QMutexLocker(self._mutex):
                if self._should_stop:
                    break

                # Get next request
                if not self._requested_ranges:
                    pass  # No requests, continue loop
                else:
                    request = self._requested_ranges.pop(0)

            if request:
                start_index, end_index = request

                # Prepare data for this range
                row_data_list = self._prepare_data_range(start_index, end_index)

                # Emit signal with prepared data
                if row_data_list:
                    self.data_ready.emit(start_index, end_index, row_data_list)

                request = None

            # Small sleep to avoid busy waiting
            self.msleep(10)

    def _prepare_data_range(self, start_index: int, end_index: int) -> List[TableRowData]:
        """
        Prepare data for a range of messages

        Args:
            start_index: Start index
            end_index: End index

        Returns:
            List of TableRowData objects
        """
        with QMutexLocker(self._mutex):
            messages = self._messages
            timestamp_formatter = self._timestamp_formatter
            signal_decoder = self._signal_decoder

        if not messages or not timestamp_formatter:
            return []

        row_data_list = []

        for i in range(start_index, min(end_index, len(messages))):
            message = messages[i]

            # Prepare all items for this row
            row_items = []

            # Column 0: Index
            item = QTableWidgetItem(str(i + 1))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setData(Qt.ItemDataRole.UserRole, i)
            row_items.append(item)

            # Column 1: Timestamp
            timestamp_str = timestamp_formatter.format(message.timestamp)
            item = QTableWidgetItem(timestamp_str)
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row_items.append(item)

            # Column 2: Channel
            item = QTableWidgetItem(str(message.channel))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            row_items.append(item)

            # Column 3: CAN ID
            can_id_str = f"0x{message.can_id:03X}"
            item = QTableWidgetItem(can_id_str)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            row_items.append(item)

            # Column 4: Direction
            item = QTableWidgetItem(message.direction)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if message.direction == 'Rx':
                item.setForeground(QColor(0, 128, 0))  # Green
            else:
                item.setForeground(QColor(0, 0, 255))  # Blue
            row_items.append(item)

            # Column 5: DLC
            item = QTableWidgetItem(str(message.dlc))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            row_items.append(item)

            # Column 6: Data
            data_str = ' '.join(f'{b:02X}' for b in message.data)
            item = QTableWidgetItem(data_str)
            row_items.append(item)

            # Column 7: Signal values
            signal_str = ""
            if signal_decoder:
                decoded = signal_decoder.decode_message(message)
                if decoded:
                    signal_str = signal_decoder.get_signal_summary(decoded, max_signals=2)
                    if decoded.get_signal_count() > 0:
                        signal_str += " [...]"

            item = QTableWidgetItem(signal_str)
            if signal_str:
                item.setForeground(QColor(0, 100, 150))
                item.setToolTip("双击查看详细信号信息")
            row_items.append(item)

            # Create row data object
            row_data = TableRowData(row_items, i)
            row_data_list.append(row_data)

        return row_data_list
