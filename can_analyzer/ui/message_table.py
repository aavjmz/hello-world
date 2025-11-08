"""
Message Table Widget for displaying CAN messages
"""

from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
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

        # Batch loading state
        self._pending_messages: List[CANMessage] = []
        self._batch_index = 0
        self._batch_size = 100  # Add 100 rows per batch (reduced for better responsiveness)
        self._batch_timer = QTimer()
        self._batch_timer.timeout.connect(self._process_batch)

        # Virtual scrolling state (for large datasets)
        self._use_virtual_scrolling = False
        self._virtual_scroll_threshold = 10000  # Use virtual scrolling for >10k messages
        self._visible_buffer_size = 30  # Rows above and below visible area
        self._visible_rows_start = 0  # First visible row index in data
        self._visible_rows_end = 0    # Last visible row index in data
        self._row_height_estimate = 25  # Estimated row height in pixels
        self._updating_virtual_view = False  # Flag to prevent recursive updates

        # Setup table
        self.setup_table()

        # Connect signals
        self.itemSelectionChanged.connect(self.on_selection_changed)
        self.cellDoubleClicked.connect(self.on_cell_double_clicked)

        # Connect scroll events for virtual scrolling
        self.verticalScrollBar().valueChanged.connect(self._on_scroll)

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
        Set messages to display (batch loaded or virtual scrolling based on size)

        Args:
            messages: List of CANMessage objects
        """
        # Stop any ongoing batch loading
        self._batch_timer.stop()

        # Store messages
        self.messages = messages

        # Clear table
        self.setRowCount(0)

        # Apply filter to get messages to display
        if self.message_filter:
            self._pending_messages = [msg for msg in messages if self.message_filter.matches(msg)]
        else:
            self._pending_messages = messages.copy()

        # Determine whether to use virtual scrolling based on message count
        total_to_display = len(self._pending_messages)

        if total_to_display >= self._virtual_scroll_threshold:
            # Use virtual scrolling for large datasets
            self._use_virtual_scrolling = True
            self._init_virtual_scrolling()
        else:
            # Use batch loading for smaller datasets
            self._use_virtual_scrolling = False
            self._batch_index = 0

            if self._pending_messages:
                # Start timer to process batches (50ms interval for better UI responsiveness)
                self._batch_timer.start(50)

    def _process_batch(self):
        """Process one batch of messages"""
        if self._batch_index >= len(self._pending_messages):
            # All done
            self._batch_timer.stop()
            self._pending_messages.clear()
            return

        # Process one batch
        end_index = min(self._batch_index + self._batch_size, len(self._pending_messages))

        for i in range(self._batch_index, end_index):
            message = self._pending_messages[i]
            # Find original index in self.messages
            original_index = self.messages.index(message) if message in self.messages else i
            self.add_message_row(original_index, message)

        self._batch_index = end_index

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
        """Refresh the entire table display (batch loaded)"""
        # Use set_messages for batch loading
        self.set_messages(self.messages)

    def add_message_row(self, index: int, message: CANMessage):
        """
        Add a message row to the table

        Args:
            index: Message index in the original messages list
            message: CANMessage object
        """
        row = self.rowCount()
        self.insertRow(row)

        # Column 0: Index
        item = QTableWidgetItem(str(index + 1))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        # Store original message index for virtual scrolling
        item.setData(Qt.ItemDataRole.UserRole, index)
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
        return self.get_message_at(current_row)

    def get_message_at(self, row: int) -> Optional[CANMessage]:
        """Get message at specific row"""
        if row < 0 or row >= self.rowCount():
            return None

        # Get the original message index from the first column
        item = self.item(row, 0)
        if item:
            message_index = item.data(Qt.ItemDataRole.UserRole)
            if message_index is not None and 0 <= message_index < len(self.messages):
                return self.messages[message_index]

        return None

    def on_selection_changed(self):
        """Handle selection change"""
        current_row = self.currentRow()
        if current_row >= 0:
            # Get the original message index
            item = self.item(current_row, 0)
            if item:
                message_index = item.data(Qt.ItemDataRole.UserRole)
                if message_index is not None:
                    self.message_selected.emit(message_index)
                else:
                    # Fallback for backward compatibility
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
        """
        Scroll to specific message index

        Args:
            index: Index in the messages list (not row number)
        """
        if index < 0 or index >= len(self.messages):
            return

        if self._use_virtual_scrolling:
            # For virtual scrolling, we need to update the window to include this message
            # Calculate the scroll position for this message
            total_messages = len(self._pending_messages)
            if total_messages > 0:
                # Find the index in pending_messages
                try:
                    pending_index = self._pending_messages.index(self.messages[index])
                except ValueError:
                    # Message not in pending (filtered out)
                    return

                # Calculate scroll percentage
                scroll_percentage = pending_index / max(1, total_messages - 1)

                # Update scrollbar to trigger window update
                scrollbar = self.verticalScrollBar()
                scroll_value = int(scroll_percentage * scrollbar.maximum())
                scrollbar.setValue(scroll_value)

                # Force update the virtual window
                self._update_virtual_window()

                # Now find the row in the current table
                for row in range(self.rowCount()):
                    item = self.item(row, 0)
                    if item and item.data(Qt.ItemDataRole.UserRole) == index:
                        self.scrollToItem(item)
                        self.selectRow(row)
                        break
        else:
            # For batch loading, find the row with this message index
            for row in range(self.rowCount()):
                item = self.item(row, 0)
                if item and item.data(Qt.ItemDataRole.UserRole) == index:
                    self.scrollToItem(item)
                    self.selectRow(row)
                    break

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

    def highlight_row(self, row: int):
        """
        Highlight a specific row with a distinct background color

        Args:
            row: Row index to highlight
        """
        if 0 <= row < self.rowCount():
            # Set highlight color (yellow background)
            highlight_color = QColor(255, 255, 0, 100)  # Semi-transparent yellow

            # Apply to all columns in the row
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    item.setBackground(highlight_color)

            # Scroll to and select the row
            self.scrollToItem(self.item(row, 0))
            self.selectRow(row)

    def clear_highlight(self):
        """Clear all row highlights"""
        # Reset background color for all cells
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    # Reset to default (transparent background)
                    item.setBackground(QColor(255, 255, 255, 0))

    def get_displayed_messages(self) -> List[CANMessage]:
        """
        Get the list of currently displayed messages (after filtering)

        Returns:
            List of CANMessage objects currently shown in table
        """
        if self.message_filter:
            return [msg for msg in self.messages if self.message_filter.matches(msg)]
        return self.messages

    def _on_scroll(self, value):
        """
        Handle scroll event for virtual scrolling

        Args:
            value: Scroll position value
        """
        if not self._use_virtual_scrolling or self._updating_virtual_view:
            return

        # Update the virtual window based on scroll position
        self._update_virtual_window()

    def _update_virtual_window(self):
        """
        Update the visible window of rows for virtual scrolling.
        Only loads rows that are visible or in the buffer zone.
        """
        if not self._use_virtual_scrolling or self._updating_virtual_view:
            return

        if not self._pending_messages:
            return

        # Prevent recursive updates
        self._updating_virtual_view = True

        try:
            # Calculate visible row range based on viewport
            viewport_height = self.viewport().height()
            rows_visible = max(30, int(viewport_height / self._row_height_estimate))

            # Get scroll position
            scrollbar = self.verticalScrollBar()
            scroll_value = scrollbar.value()
            scroll_max = scrollbar.maximum()

            # Calculate which message indices should be visible
            total_messages = len(self._pending_messages)

            if scroll_max > 0:
                # Calculate position as percentage
                scroll_percentage = scroll_value / scroll_max
                # Calculate center of visible window
                center_index = int(scroll_percentage * total_messages)
            else:
                center_index = 0

            # Calculate start and end indices with buffer
            new_start = max(0, center_index - rows_visible // 2 - self._visible_buffer_size)
            new_end = min(total_messages, center_index + rows_visible // 2 + self._visible_buffer_size)

            # Only update if the range has changed significantly (to avoid too many updates)
            if abs(new_start - self._visible_rows_start) > 10 or abs(new_end - self._visible_rows_end) > 10:
                self._load_virtual_window(new_start, new_end)

        finally:
            self._updating_virtual_view = False

    def _load_virtual_window(self, start_index: int, end_index: int):
        """
        Load a specific window of rows into the table

        Args:
            start_index: Start index in the message list
            end_index: End index in the message list
        """
        # Clear current table rows
        self.setRowCount(0)

        # Load rows in the window
        for i in range(start_index, end_index):
            if i >= len(self._pending_messages):
                break

            message = self._pending_messages[i]
            # Find original index in self.messages
            original_index = self.messages.index(message) if message in self.messages else i
            self.add_message_row(original_index, message)

        # Update visible range
        self._visible_rows_start = start_index
        self._visible_rows_end = end_index

    def _init_virtual_scrolling(self):
        """
        Initialize virtual scrolling for large datasets.
        Sets up the initial visible window.
        """
        if not self._pending_messages:
            return

        # Calculate initial visible window size
        viewport_height = self.viewport().height()
        initial_rows = max(60, int(viewport_height / self._row_height_estimate) + self._visible_buffer_size * 2)

        # Load initial window
        end_index = min(initial_rows, len(self._pending_messages))
        self._load_virtual_window(0, end_index)

        # Configure scrollbar to represent total data size
        # Note: We'll use a proxy approach where scrollbar maximum represents data range
        total_messages = len(self._pending_messages)
        self.verticalScrollBar().setMaximum(total_messages - 1)
