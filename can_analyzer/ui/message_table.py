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

        # Sliding window mode for large datasets (better than virtual scrolling)
        self._use_sliding_window = False
        self._sliding_window_threshold = 10000  # Use sliding window for >10k messages
        self._window_size = 15000  # Fixed window size: always show 15000 rows
        self._window_start_index = 0  # Current window start position in all messages
        self._append_batch_size = 2000  # Append 2000 rows when reaching bottom
        self._bottom_trigger_rows = 100  # Trigger when within 100 rows of bottom
        self._is_loading_more = False  # Flag to prevent concurrent loading

        # Legacy virtual scrolling state (kept for compatibility)
        self._use_virtual_scrolling = False
        self._visible_buffer_size = 100  # Increased buffer: 100 rows above and below (was 30)
        self._visible_rows_start = 0  # First visible row index in data
        self._visible_rows_end = 0    # Last visible row index in data
        self._row_height_estimate = 25  # Estimated row height in pixels
        self._updating_virtual_view = False  # Flag to prevent recursive updates

        # Data cache for prepared rows
        self._row_data_cache = {}  # Dict[int, TableRowData]
        self._cache_max_size = 1000  # Maximum cached rows

        # Background worker for data preparation
        self._data_worker = None
        self._preload_threshold = 0.7  # Start preloading when 70% through buffer

        # Scroll throttle timer for smooth scrolling
        self._scroll_update_timer = QTimer()
        self._scroll_update_timer.setSingleShot(True)
        self._scroll_update_timer.timeout.connect(self._delayed_scroll_update)
        self._scroll_update_pending = False
        self._last_scroll_value = 0
        self._scroll_throttle_ms = 50  # Reduced for sliding window (no heavy updates)

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

        # Stop and cleanup old worker
        if self._data_worker:
            self._data_worker.stop()
            self._data_worker.wait(1000)  # Wait up to 1 second
            self._data_worker = None

        # Clear cache
        self._row_data_cache.clear()

        # Store messages
        self.messages = messages

        # Clear table
        self.setRowCount(0)

        # Apply filter to get messages to display
        if self.message_filter:
            self._pending_messages = [msg for msg in messages if self.message_filter.matches(msg)]
        else:
            self._pending_messages = messages.copy()

        # Determine whether to use sliding window based on message count
        total_to_display = len(self._pending_messages)

        if total_to_display >= self._sliding_window_threshold:
            # Use sliding window for large datasets (smooth continuous scrolling)
            self._use_sliding_window = True
            self._use_virtual_scrolling = False
            self._init_sliding_window()
        else:
            # Use batch loading for smaller datasets
            self._use_sliding_window = False
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
                signal_str = self.signal_decoder.get_signal_summary(decoded, max_signals=2)
                # Add expand indicator if there are signals
                if decoded.get_signal_count() > 0:
                    signal_str += " [...]"

        item = QTableWidgetItem(signal_str)
        if signal_str:
            item.setForeground(QColor(0, 100, 150))  # Dark cyan for signals
            # Add tooltip to indicate it's clickable
            item.setToolTip("双击查看详细信号信息")
        self.setItem(row, 7, item)

    def _add_message_row_fast(self, row: int, index: int, message: CANMessage):
        """
        Optimized version of add_message_row for virtual scrolling
        Assumes row already exists (pre-allocated with setRowCount)

        Args:
            row: Row index in table
            index: Message index in original messages list
            message: CANMessage object
        """
        # Column 0: Index
        item = QTableWidgetItem(str(index + 1))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setData(Qt.ItemDataRole.UserRole, index)
        self.setItem(row, 0, item)

        # Column 1: Timestamp
        item = QTableWidgetItem(self.timestamp_formatter.format(message.timestamp))
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.setItem(row, 1, item)

        # Column 2: Channel
        item = QTableWidgetItem(str(message.channel))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row, 2, item)

        # Column 3: CAN ID
        item = QTableWidgetItem(f"0x{message.can_id:03X}")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row, 3, item)

        # Column 4: Direction
        item = QTableWidgetItem(message.direction)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if message.direction == 'Rx':
            item.setForeground(QColor(0, 128, 0))
        else:
            item.setForeground(QColor(0, 0, 255))
        self.setItem(row, 4, item)

        # Column 5: DLC
        item = QTableWidgetItem(str(message.dlc))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row, 5, item)

        # Column 6: Data
        item = QTableWidgetItem(' '.join(f'{b:02X}' for b in message.data))
        self.setItem(row, 6, item)

        # Column 7: Signal values (simplified - skip decoding during fast scrolling)
        item = QTableWidgetItem("")
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
        if not message:
            return

        # If signal column (column 7) is double-clicked and has decoder, show signal details
        if column == 7 and self.signal_decoder:
            # Check if message has signals
            decoded = self.signal_decoder.decode_message(message)
            if decoded and decoded.get_signal_count() > 0:
                self.show_signal_details(message)
                return

        # Otherwise, emit normal double-click signal
        self.message_double_clicked.emit(message)

    def show_signal_details(self, message: CANMessage):
        """
        Show detailed signal information dialog

        Args:
            message: CANMessage to show details for
        """
        if not self.signal_decoder:
            return

        from ui.signal_details_dialog import SignalDetailsDialog

        dialog = SignalDetailsDialog(message, self.signal_decoder, self)
        dialog.exec()

    def show_context_menu(self, pos):
        """Show context menu"""
        menu = QMenu(self)

        # Get selected message
        message = self.get_selected_message()

        # Signal details action (if signal decoder is available and message has signals)
        if message and self.signal_decoder:
            decoded = self.signal_decoder.decode_message(message)
            if decoded and decoded.get_signal_count() > 0:
                signal_details_action = QAction("查看信号详情", self)
                signal_details_action.triggered.connect(lambda: self.show_signal_details(message))
                menu.addAction(signal_details_action)
                menu.addSeparator()

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
        Handle scroll event

        For sliding window mode: Only check for bottom reach
        For legacy virtual scrolling: Use throttling

        Args:
            value: Scroll position value
        """
        if self._use_sliding_window:
            # Sliding window mode: check if near bottom
            self._check_bottom_and_load_more()
            return

        if not self._use_virtual_scrolling or self._updating_virtual_view:
            return

        # Store the scroll value
        self._last_scroll_value = value

        # Mark that an update is needed
        self._scroll_update_pending = True

        # Restart timer - this delays update until scrolling stops
        self._scroll_update_timer.stop()
        self._scroll_update_timer.start(self._scroll_throttle_ms)

    def _delayed_scroll_update(self):
        """
        Delayed scroll update callback - called after scrolling stops
        """
        if self._scroll_update_pending:
            self._scroll_update_pending = False
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
            # Increased threshold to 80 rows for much smoother scrolling
            # With 100-row buffer on each side, this gives good tolerance
            threshold = min(80, self._visible_buffer_size // 2)
            if abs(new_start - self._visible_rows_start) > threshold or abs(new_end - self._visible_rows_end) > threshold:
                self._load_virtual_window(new_start, new_end)

        finally:
            self._updating_virtual_view = False

    def _load_virtual_window(self, start_index: int, end_index: int):
        """
        Load a specific window of rows into the table (optimized for smooth scrolling)

        Args:
            start_index: Start index in the message list
            end_index: End index in the message list
        """
        # Disable updates and sorting during batch operation for maximum performance
        self.setUpdatesEnabled(False)
        self.setSortingEnabled(False)

        try:
            # Clear current table rows
            self.setRowCount(0)

            # Pre-allocate rows for better performance
            row_count = min(end_index - start_index, len(self._pending_messages) - start_index)
            self.setRowCount(row_count)

            # Load rows in the window
            for row_idx, i in enumerate(range(start_index, end_index)):
                if i >= len(self._pending_messages):
                    break

                message = self._pending_messages[i]
                # Use i directly as original index - much faster than list.index()
                # which would be O(n) for each message
                original_index = i

                # Inline message row creation for better performance
                self._add_message_row_fast(row_idx, original_index, message)

            # Update visible range
            self._visible_rows_start = start_index
            self._visible_rows_end = end_index

        finally:
            # Re-enable updates
            self.setUpdatesEnabled(True)

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

    def _init_sliding_window(self):
        """
        Initialize sliding window mode for large datasets

        This mode provides smooth continuous scrolling by:
        1. Loading a fixed window of rows (e.g., 15000)
        2. Only appending new data when scrolling reaches bottom
        3. Removing old data from top to maintain fixed window size
        """
        if not self._pending_messages:
            return

        # Reset window position
        self._window_start_index = 0

        # Calculate initial window size
        total_messages = len(self._pending_messages)
        initial_window_end = min(self._window_size, total_messages)

        # Load initial window
        self.setUpdatesEnabled(False)
        self.setSortingEnabled(False)

        try:
            self.setRowCount(0)
            row_count = initial_window_end - self._window_start_index
            self.setRowCount(row_count)

            # Load rows in the window
            for row_idx in range(row_count):
                message_idx = self._window_start_index + row_idx
                message = self._pending_messages[message_idx]
                self._add_message_row_fast(row_idx, message_idx, message)

            # Update visible range
            self._visible_rows_start = self._window_start_index
            self._visible_rows_end = initial_window_end

        finally:
            self.setUpdatesEnabled(True)

        # Initial scroll position at top to show first messages
        # (scroll position will be adjusted to middle after window sliding)

        print(f"[Sliding Window] Initialized: loaded {row_count} rows (window {self._window_start_index}-{initial_window_end} of {total_messages} total)")

    def _check_bottom_and_load_more(self):
        """
        Check if scrolled near top or bottom and load more data if needed
        Supports bidirectional scrolling for continuous data viewing
        """
        if self._is_loading_more:
            return

        # Get current scroll position
        current_row = self.rowCount()
        if current_row == 0:
            return

        # Calculate scroll position
        scrollbar = self.verticalScrollBar()
        scroll_value = scrollbar.value()
        scroll_max = scrollbar.maximum()

        if scroll_max <= 0:
            return

        scroll_percentage = scroll_value / scroll_max

        # Check if near top (for backward scrolling)
        if scroll_percentage <= 0.05:  # Top 5%
            self._slide_window_backward()
        # Check if near bottom (for forward scrolling)
        elif scroll_percentage >= 0.95:  # Bottom 5%
            self._slide_window_forward()

    def _slide_window_forward(self):
        """
        Slide the window forward: append new data at bottom, remove old data from top
        This maintains a fixed window size while allowing continuous scrolling
        """
        if self._is_loading_more:
            return

        total_messages = len(self._pending_messages)
        current_window_end = self._window_start_index + self.rowCount()

        # Check if we have more data to load
        if current_window_end >= total_messages:
            print(f"[Sliding Window] Already at end of data ({current_window_end}/{total_messages})")
            return

        # Mark as loading
        self._is_loading_more = True

        try:
            # Calculate how many rows to append
            rows_to_append = min(self._append_batch_size, total_messages - current_window_end)

            # Calculate current visible row to maintain visual continuity
            scrollbar = self.verticalScrollBar()
            old_scroll_value = scrollbar.value()
            old_scroll_max = scrollbar.maximum()

            # Estimate which row user is currently viewing
            if old_scroll_max > 0:
                scroll_percentage = old_scroll_value / old_scroll_max
                current_viewing_row = int(scroll_percentage * self.rowCount())
            else:
                current_viewing_row = 0

            # Calculate the message index user is viewing
            viewing_message_index = self._window_start_index + current_viewing_row

            self.setUpdatesEnabled(False)
            self.setSortingEnabled(False)

            try:
                # Calculate new window boundaries
                new_window_start = self._window_start_index + rows_to_append
                new_window_end = current_window_end + rows_to_append

                # Remove rows from top
                for _ in range(rows_to_append):
                    self.removeRow(0)

                # Append new rows at bottom
                current_row_count = self.rowCount()
                self.setRowCount(current_row_count + rows_to_append)

                for i in range(rows_to_append):
                    message_idx = current_window_end + i
                    row_idx = current_row_count + i
                    message = self._pending_messages[message_idx]
                    self._add_message_row_fast(row_idx, message_idx, message)

                # Update window position
                self._window_start_index = new_window_start
                self._visible_rows_start = new_window_start
                self._visible_rows_end = new_window_end

                print(f"[Sliding Window] Slid forward: removed {rows_to_append} from top, added {rows_to_append} at bottom (window now {new_window_start}-{new_window_end} of {total_messages})")

            finally:
                self.setUpdatesEnabled(True)

                # Maintain visual continuity: keep user viewing the same message
                new_viewing_row = viewing_message_index - new_window_start

                # Ensure the new position is valid and allows further scrolling
                new_row_count = self.rowCount()
                if new_viewing_row < 0:
                    # User was viewing messages that got removed, position near top
                    new_viewing_row = new_row_count // 4  # 25% position
                elif new_viewing_row >= new_row_count:
                    # Should not happen, but handle it
                    new_viewing_row = new_row_count * 3 // 4  # 75% position

                # Set scroll position to maintain visual continuity
                new_scroll_max = scrollbar.maximum()
                if new_scroll_max > 0 and new_row_count > 0:
                    target_percentage = new_viewing_row / new_row_count
                    target_scroll_value = int(target_percentage * new_scroll_max)
                    scrollbar.setValue(target_scroll_value)
                    print(f"[Sliding Window] Maintaining scroll position: message {viewing_message_index} at row {new_viewing_row} ({target_percentage*100:.1f}%)")

        finally:
            self._is_loading_more = False

    def _slide_window_backward(self):
        """
        Slide the window backward: prepend old data at top, remove recent data from bottom
        This allows scrolling back to view earlier messages
        """
        if self._is_loading_more:
            return

        # Check if we have earlier data to load
        if self._window_start_index <= 0:
            print(f"[Sliding Window] Already at start of data (window starts at 0)")
            return

        # Mark as loading
        self._is_loading_more = True

        try:
            # Calculate how many rows to prepend
            rows_to_prepend = min(self._append_batch_size, self._window_start_index)

            # Calculate current visible row to maintain visual continuity
            scrollbar = self.verticalScrollBar()
            old_scroll_value = scrollbar.value()
            old_scroll_max = scrollbar.maximum()

            # Estimate which row user is currently viewing
            if old_scroll_max > 0:
                scroll_percentage = old_scroll_value / old_scroll_max
                current_viewing_row = int(scroll_percentage * self.rowCount())
            else:
                current_viewing_row = 0

            # Calculate the message index user is viewing
            viewing_message_index = self._window_start_index + current_viewing_row

            self.setUpdatesEnabled(False)
            self.setSortingEnabled(False)

            try:
                total_messages = len(self._pending_messages)
                current_window_end = self._window_start_index + self.rowCount()

                # Calculate new window boundaries
                new_window_start = self._window_start_index - rows_to_prepend
                new_window_end = current_window_end - rows_to_prepend

                # Remove rows from bottom
                current_row_count = self.rowCount()
                for _ in range(rows_to_prepend):
                    self.removeRow(current_row_count - 1)
                    current_row_count -= 1

                # Prepend new rows at top
                # We need to insert rows at the beginning
                for i in range(rows_to_prepend):
                    self.insertRow(0)

                # Fill the prepended rows with data
                for i in range(rows_to_prepend):
                    message_idx = new_window_start + i
                    row_idx = i
                    message = self._pending_messages[message_idx]
                    self._add_message_row_fast(row_idx, message_idx, message)

                # Update window position
                self._window_start_index = new_window_start
                self._visible_rows_start = new_window_start
                self._visible_rows_end = new_window_end

                print(f"[Sliding Window] Slid backward: removed {rows_to_prepend} from bottom, added {rows_to_prepend} at top (window now {new_window_start}-{new_window_end} of {total_messages})")

            finally:
                self.setUpdatesEnabled(True)

                # Maintain visual continuity: keep user viewing the same message
                # Since we prepended rows, the viewing position shifts down
                new_viewing_row = viewing_message_index - new_window_start

                # Ensure the new position is valid
                new_row_count = self.rowCount()
                if new_viewing_row < 0:
                    # Should not happen, but handle it
                    new_viewing_row = new_row_count // 4  # 25% position
                elif new_viewing_row >= new_row_count:
                    # User was viewing messages that got removed, position near bottom
                    new_viewing_row = new_row_count * 3 // 4  # 75% position

                # Set scroll position to maintain visual continuity
                new_scroll_max = scrollbar.maximum()
                if new_scroll_max > 0 and new_row_count > 0:
                    target_percentage = new_viewing_row / new_row_count
                    target_scroll_value = int(target_percentage * new_scroll_max)
                    scrollbar.setValue(target_scroll_value)
                    print(f"[Sliding Window] Maintaining scroll position: message {viewing_message_index} at row {new_viewing_row} ({target_percentage*100:.1f}%)")

        finally:
            self._is_loading_more = False

    def _init_virtual_scrolling_with_worker(self):
        """
        Initialize virtual scrolling with background worker thread for better performance
        """
        if not self._pending_messages:
            return

        # Create and start background worker
        from ui.virtual_scroll_worker import VirtualScrollDataWorker

        self._data_worker = VirtualScrollDataWorker(self)
        self._data_worker.set_data(
            self._pending_messages,
            self.timestamp_formatter,
            self.signal_decoder
        )
        self._data_worker.data_ready.connect(self._on_worker_data_ready)
        self._data_worker.start()

        # Calculate initial visible window size (larger than before)
        viewport_height = self.viewport().height()
        rows_visible = max(50, int(viewport_height / self._row_height_estimate))
        initial_rows = rows_visible + self._visible_buffer_size * 2  # 50 + 200 = 250 rows

        # Load initial window
        end_index = min(initial_rows, len(self._pending_messages))
        self._load_virtual_window_async(0, end_index)

        # Preload next chunk
        if end_index < len(self._pending_messages):
            preload_end = min(end_index + self._visible_buffer_size, len(self._pending_messages))
            self._data_worker.request_data_range(end_index, preload_end)

        # Configure scrollbar
        total_messages = len(self._pending_messages)
        self.verticalScrollBar().setMaximum(total_messages - 1)

    def _load_virtual_window_async(self, start_index: int, end_index: int):
        """
        Load virtual window using cached data or request from worker

        Args:
            start_index: Start index
            end_index: End index
        """
        # For initial load (empty cache), load synchronously for immediate display
        if not self._row_data_cache:
            # First time load - use synchronous loading for initial batch
            # This ensures user sees data immediately
            initial_batch = min(100, end_index - start_index)
            self._load_virtual_window(start_index, start_index + initial_batch)

            # Request rest asynchronously
            if start_index + initial_batch < end_index:
                self._data_worker.request_data_range(
                    start_index + initial_batch,
                    end_index
                )
            return

        # Check if we need to preload next chunk
        self._check_preload(start_index, end_index)

        # Try to load from cache first
        cached_rows = []
        missing_ranges = []

        for i in range(start_index, end_index):
            if i in self._row_data_cache:
                cached_rows.append(self._row_data_cache[i])
            else:
                # Mark as missing
                if not missing_ranges or missing_ranges[-1][1] != i:
                    missing_ranges.append([i, i + 1])
                else:
                    missing_ranges[-1][1] = i + 1

        # Display cached data if we have enough (>50%)
        cache_ratio = len(cached_rows) / max(1, end_index - start_index)
        if cache_ratio > 0.5:
            self._display_cached_rows(start_index, end_index, cached_rows)

        # Request missing data from worker
        for missing_start, missing_end in missing_ranges:
            self._data_worker.request_data_range(missing_start, missing_end)

    def _check_preload(self, current_start: int, current_end: int):
        """
        Check if we should preload next/previous chunks

        Args:
            current_start: Current window start
            current_end: Current window end
        """
        if not self._data_worker:
            return

        total_messages = len(self._pending_messages)
        window_size = current_end - current_start
        preload_trigger = int(window_size * self._preload_threshold)

        # Calculate scroll direction and position
        scroll_pos = (current_start + current_end) / 2
        prev_scroll_pos = (self._visible_rows_start + self._visible_rows_end) / 2

        # Scrolling down - preload next chunk
        if scroll_pos > prev_scroll_pos:
            distance_to_end = current_end - current_start
            if distance_to_end < preload_trigger:
                # Near end of current window, preload next
                preload_start = current_end
                preload_end = min(preload_start + self._visible_buffer_size, total_messages)
                if preload_start < total_messages:
                    self._data_worker.request_data_range(preload_start, preload_end)

        # Scrolling up - preload previous chunk
        elif scroll_pos < prev_scroll_pos:
            distance_to_start = current_start
            if distance_to_start < preload_trigger:
                # Near start of current window, preload previous
                preload_end = current_start
                preload_start = max(0, preload_end - self._visible_buffer_size)
                if preload_start >= 0:
                    self._data_worker.request_data_range(preload_start, preload_end)

    def _on_worker_data_ready(self, start_index: int, end_index: int, row_data_list):
        """
        Callback when worker has prepared data

        Args:
            start_index: Start index
            end_index: End index
            row_data_list: List of TableRowData objects
        """
        # Store in cache
        for i, row_data in enumerate(row_data_list):
            cache_index = start_index + i
            self._row_data_cache[cache_index] = row_data

            # Limit cache size
            if len(self._row_data_cache) > self._cache_max_size:
                # Remove oldest entries (simple FIFO)
                oldest_key = min(self._row_data_cache.keys())
                del self._row_data_cache[oldest_key]

        # If this data is in current visible window, update display
        if (start_index >= self._visible_rows_start and start_index < self._visible_rows_end) or \
           (end_index > self._visible_rows_start and end_index <= self._visible_rows_end):
            self._refresh_visible_window_from_cache()

    def _display_cached_rows(self, start_index: int, end_index: int, cached_rows):
        """
        Display rows from cache

        Args:
            start_index: Start index
            end_index: End index
            cached_rows: List of cached TableRowData (may not be complete range)
        """
        if not cached_rows:
            return

        self.setUpdatesEnabled(False)
        try:
            self.setRowCount(0)

            # Display all cached rows in order
            for i in range(start_index, end_index):
                if i in self._row_data_cache:
                    row_data = self._row_data_cache[i]
                    row = self.rowCount()
                    self.insertRow(row)

                    # Set all items
                    for col, item in enumerate(row_data.row_items):
                        self.setItem(row, col, item)

            self._visible_rows_start = start_index
            self._visible_rows_end = end_index

        finally:
            self.setUpdatesEnabled(True)

    def _refresh_visible_window_from_cache(self):
        """Refresh current visible window from cache"""
        if not self._use_virtual_scrolling:
            return

        # Get current window range
        start = self._visible_rows_start
        end = self._visible_rows_end

        # Collect cached rows in range
        cached_rows = []
        for i in range(start, end):
            if i in self._row_data_cache:
                cached_rows.append(self._row_data_cache[i])

        if cached_rows:
            self._display_cached_rows(start, end, cached_rows)
