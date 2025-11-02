"""
Message Table Widget for displaying CAN messages
"""

from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QAction
from typing import List, Optional
from parsers.asc_parser import CANMessage
from utils.timestamp_formatter import TimestampFormatter, TimestampFormat
from utils.signal_decoder import SignalDecoder


class MessageTableWidget(QTableWidget):
    """Table widget for displaying CAN messages"""

    # Signals
    message_selected = pyqtSignal(int)  # Emits row index when message is selected
    message_double_clicked = pyqtSignal(CANMessage)  # Emits message when double-clicked

    def __init__(self, parent=None):
        super().__init__(parent)

        # Data storage
        self.messages: List[CANMessage] = []
        self.timestamp_formatter = TimestampFormatter(TimestampFormat.RAW)
        self.signal_decoder: Optional[SignalDecoder] = None
        self.message_filter: Optional['MessageFilter'] = None  # Import will be added

        # Setup table
        self.setup_table()

        # Connect signals
        self.itemSelectionChanged.connect(self.on_selection_changed)
        self.cellDoubleClicked.connect(self.on_cell_double_clicked)

    def setup_table(self):
        """Setup table properties and headers"""
        # Set column count and headers
        self.setColumnCount(8)
        self.setHorizontalHeaderLabels([
            "序号", "时间戳", "通道", "CAN ID", "方向", "DLC", "数据", "信号值"
        ])

        # Set table properties
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSortingEnabled(False)

        # Set column widths
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 序号
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 时间戳
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 通道
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # CAN ID
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # 方向
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # DLC
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)       # 数据
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)            # 信号值

        # Enable context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def set_timestamp_format(self, format_type: TimestampFormat):
        """Set timestamp display format"""
        self.timestamp_formatter.set_format(format_type)
        # Refresh display
        self.refresh_display()

    def set_messages(self, messages: List[CANMessage]):
        """
        Set messages to display

        Args:
            messages: List of CANMessage objects
        """
        self.messages = messages
        self.refresh_display()

    def add_message(self, message: CANMessage):
        """
        Add a single message to the table

        Args:
            message: CANMessage object
        """
        self.messages.append(message)
        self.add_message_row(len(self.messages) - 1, message)

    def add_messages(self, messages: List[CANMessage]):
        """
        Add multiple messages to the table

        Args:
            messages: List of CANMessage objects
        """
        self.messages.extend(messages)
        self.refresh_display()

    def clear_messages(self):
        """Clear all messages"""
        self.messages.clear()
        self.setRowCount(0)

    def refresh_display(self):
        """Refresh the entire table display"""
        # Clear existing rows
        self.setRowCount(0)

        # Add all messages (with optional filtering)
        for idx, message in enumerate(self.messages):
            # Apply filter if active
            if self.message_filter and not self.message_filter.matches(message):
                continue
            self.add_message_row(idx, message)

    def add_message_row(self, index: int, message: CANMessage):
        """
        Add a message row to the table

        Args:
            index: Message index
            message: CANMessage object
        """
        row = self.rowCount()
        self.insertRow(row)

        # Column 0: Index
        item = QTableWidgetItem(str(index + 1))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row, 0, item)

        # Column 1: Timestamp
        timestamp_str = self.timestamp_formatter.format(message.timestamp)
        item = QTableWidgetItem(timestamp_str)
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.setItem(row, 1, item)

        # Column 2: Channel
        item = QTableWidgetItem(str(message.channel))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row, 2, item)

        # Column 3: CAN ID
        can_id_str = f"0x{message.can_id:03X}"
        item = QTableWidgetItem(can_id_str)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row, 3, item)

        # Column 4: Direction
        item = QTableWidgetItem(message.direction)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        # Color code direction
        if message.direction == 'Rx':
            item.setForeground(QColor(0, 128, 0))  # Green
        else:
            item.setForeground(QColor(0, 0, 255))  # Blue
        self.setItem(row, 4, item)

        # Column 5: DLC
        item = QTableWidgetItem(str(message.dlc))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row, 5, item)

        # Column 6: Data
        data_str = ' '.join(f'{b:02X}' for b in message.data)
        item = QTableWidgetItem(data_str)
        item.setFont(self.font())  # Use monospace would be better
        self.setItem(row, 6, item)

        # Column 7: Signal values
        signal_str = ""
        if self.signal_decoder:
            decoded = self.signal_decoder.decode_message(message)
            if decoded:
                signal_str = self.signal_decoder.get_signal_summary(decoded, max_signals=3)

        item = QTableWidgetItem(signal_str)
        if signal_str:
            item.setForeground(QColor(0, 100, 150))  # Dark cyan for signals
        self.setItem(row, 7, item)

    def get_selected_message(self) -> Optional[CANMessage]:
        """Get the currently selected message"""
        current_row = self.currentRow()
        if 0 <= current_row < len(self.messages):
            return self.messages[current_row]
        return None

    def get_message_at(self, row: int) -> Optional[CANMessage]:
        """Get message at specific row"""
        if 0 <= row < len(self.messages):
            return self.messages[row]
        return None

    def on_selection_changed(self):
        """Handle selection change"""
        current_row = self.currentRow()
        if current_row >= 0:
            self.message_selected.emit(current_row)

    def on_cell_double_clicked(self, row: int, column: int):
        """Handle cell double click"""
        message = self.get_message_at(row)
        if message:
            self.message_double_clicked.emit(message)

    def show_context_menu(self, pos):
        """Show context menu"""
        menu = QMenu(self)

        # Copy action
        copy_action = QAction("复制", self)
        copy_action.triggered.connect(self.copy_selected)
        menu.addAction(copy_action)

        menu.addSeparator()

        # Timestamp format submenu
        ts_menu = menu.addMenu("时间戳格式")

        formats = [
            (TimestampFormat.RAW, "原始格式"),
            (TimestampFormat.SECONDS, "秒"),
            (TimestampFormat.MILLISECONDS, "毫秒"),
            (TimestampFormat.MICROSECONDS, "微秒"),
        ]

        for fmt, name in formats:
            action = QAction(name, self)
            action.triggered.connect(lambda checked, f=fmt: self.set_timestamp_format(f))
            ts_menu.addAction(action)

        # Show menu
        menu.exec(self.mapToGlobal(pos))

    def copy_selected(self):
        """Copy selected row to clipboard"""
        message = self.get_selected_message()
        if message:
            # Format message data
            text = f"Time: {self.timestamp_formatter.format(message.timestamp)}, "
            text += f"ID: 0x{message.can_id:03X}, "
            text += f"Dir: {message.direction}, "
            text += f"DLC: {message.dlc}, "
            text += f"Data: {' '.join(f'{b:02X}' for b in message.data)}"

            # Copy to clipboard
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(text)

    def filter_by_id(self, can_id: int):
        """
        Filter messages by CAN ID

        Args:
            can_id: CAN ID to filter (0 = show all)
        """
        if can_id == 0:
            # Show all messages
            self.refresh_display()
        else:
            # Filter messages
            self.setRowCount(0)
            for idx, message in enumerate(self.messages):
                if message.can_id == can_id:
                    self.add_message_row(idx, message)

    def get_message_count(self) -> int:
        """Get total message count"""
        return len(self.messages)

    def scroll_to_message(self, index: int):
        """Scroll to specific message index"""
        if 0 <= index < self.rowCount():
            self.scrollToItem(self.item(index, 0))
            self.selectRow(index)

    def set_signal_decoder(self, decoder: Optional[SignalDecoder]):
        """
        Set the signal decoder for decoding messages

        Args:
            decoder: SignalDecoder instance or None to disable decoding
        """
        self.signal_decoder = decoder
        # Refresh display to show/hide signal values
        self.refresh_display()

    def set_filter(self, message_filter: Optional['MessageFilter']):
        """
        Set message filter

        Args:
            message_filter: MessageFilter instance or None to clear filter
        """
        self.message_filter = message_filter
        # Refresh display to apply filter
        self.refresh_display()

    def get_filtered_count(self) -> int:
        """
        Get count of messages that pass the current filter

        Returns:
            Number of messages that pass filter (or total if no filter)
        """
        if not self.message_filter:
            return len(self.messages)

        count = 0
        for message in self.messages:
            if self.message_filter.matches(message):
                count += 1

        return count

    def clear_filter(self):
        """Clear the current filter"""
        self.message_filter = None
        self.refresh_display()
